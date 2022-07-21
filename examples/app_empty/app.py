# v0_app.py

import lightning as L


class EmptyApp(L.LightningFlow):
    def __init__(self):
        super().__init__()


    def run(self):
        pass


app = L.LightningApp(EmptyApp())
