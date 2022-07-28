import glob
import os.path
from importlib.util import module_from_spec, spec_from_file_location
from itertools import chain
from types import ModuleType
from typing import Any, Dict

from setuptools import find_packages

_PROJECT_ROOT = "."
_SOURCE_ROOT = os.path.join(_PROJECT_ROOT, "src")
_PACKAGE_ROOT = os.path.join(_SOURCE_ROOT, "lightning")
_FREEZE_REQUIREMENTS = bool(int(os.environ.get("FREEZE_REQUIREMENTS", 0)))


def _load_py_module(name: str, location: str) -> ModuleType:
    spec = spec_from_file_location(name, location)
    assert spec, f"Failed to load module {name} from {location}"
    py = module_from_spec(spec)
    assert spec.loader, f"ModuleSpec.loader is None for {name} from {location}"
    spec.loader.exec_module(py)
    return py


def _adjust_manifest(**kwargs: Any) -> None:
    # todo: consider rather aggregation of particular manifest adjustments
    manifest_path = os.path.join(_PROJECT_ROOT, "MANIFEST.in")
    assert os.path.isfile(manifest_path)
    with open(manifest_path) as fp:
        lines = fp.readlines()
    if kwargs["pkg_name"] == "lightning":
        lines += [
            "recursive-include src/lightning *.md" + os.linesep,
            # fixme: this is strange, this shall work with setup find package - include
            "prune src/lightning_app" + os.linesep,
            "prune src/pytorch_lightning" + os.linesep,
        ]
    else:
        lines += [
            "recursive-include src *.md" + os.linesep,
            "recursive-include requirements *.txt" + os.linesep,
            "recursive-include src/lightning_app/cli/*-template *" + os.linesep,  # Add templates
        ]
    with open(manifest_path, "w") as fp:
        fp.writelines(lines)


def _setup_args(**kwargs: Any) -> Dict[str, Any]:
    _path_setup_tools = os.path.join(_PROJECT_ROOT, ".actions", "setup_tools.py")
    _setup_tools = _load_py_module("setup_tools", _path_setup_tools)
    _about = _load_py_module("about", os.path.join(_PACKAGE_ROOT, "__about__.py"))
    _version = _load_py_module("version", os.path.join(_PACKAGE_ROOT, "__version__.py"))
    _long_description = _setup_tools.load_readme_description(
        _PROJECT_ROOT, homepage=_about.__homepage__, version=_version.version
    )
    if kwargs["pkg_name"] == "lightning":
        _include_pkgs = ["lightning", "lightning.*"]
        # todo: generate this list automatically with parsing feature pkg versions
        _requires = ["pytorch-lightning>=1.6.5, <1.7.0", "lightning-app>=0.5.2, <0.6.0"]
    else:
        _include_pkgs = ["*"]
        _requires = [
            _setup_tools.load_requirements(d, unfreeze=not _FREEZE_REQUIREMENTS)
            for d in glob.glob(os.path.join("requirements", "*"))
            if os.path.isdir(d)
        ]
        _requires = list(chain(*_requires))
    # TODO: consider invaliding some additional arguments from packages, for example if include data or safe to zip

    # TODO: remove this once lightning-ui package is ready as a dependency
    _setup_tools._download_frontend(_PROJECT_ROOT)

    return dict(
        name="lightning",
        version=_version.version,  # todo: consider adding branch for installation from source
        description=_about.__docs__,
        author=_about.__author__,
        author_email=_about.__author_email__,
        url=_about.__homepage__,
        download_url="https://github.com/Lightning-AI/lightning",
        license=_about.__license__,
        packages=find_packages(where="src", include=_include_pkgs),
        package_dir={"": "src"},
        long_description=_long_description,
        long_description_content_type="text/markdown",
        include_package_data=True,
        zip_safe=False,
        keywords=["deep learning", "pytorch", "AI"],  # todo: aggregate tags from all packages
        python_requires=">=3.7",  # todo: take the lowes based on all packages
        entry_points={
            "console_scripts": [
                "lightning = lightning_app.cli.lightning_cli:main",
            ],
        },
        setup_requires=[],
        install_requires=_requires,
        extras_require={},  # todo: consider porting all other packages extras with prefix
        project_urls={
            "Bug Tracker": "https://github.com/Lightning-AI/lightning/issues",
            "Documentation": "https://lightning.ai/lightning-docs",
            "Source Code": "https://github.com/Lightning-AI/lightning",
        },
        classifiers=[
            "Environment :: Console",
            "Natural Language :: English",
            # How mature is this project? Common values are
            #   3 - Alpha, 4 - Beta, 5 - Production/Stable
            "Development Status :: 4 - Beta",
            # Indicate who your project is intended for
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Scientific/Engineering :: Information Analysis",
            # Pick your license as you wish
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
            # Specify the Python versions you support here.
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
        ],  # todo: consider aggregation/union of tags from particular packages
    )
