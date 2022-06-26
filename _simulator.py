import pandas as pd

from _env._env import Environment
from _env._msc import initalizeMSC
from _viewer import MSC_Viewer
from _util import AppManager


class Simulator():
    def __init__(self):
        """
            Source = -1
            End = -2
            Conveyor : 1
            MSC_L : 2
            MSC_R : 3
        """
        # print("initalize... MSC...")
        # print("initalize... Environmnet...")
        self.env = Environment(msc=initalizeMSC())
        # print("initalize... Background...")
        self.viewer = MSC_Viewer()
        self.viewer.setBackground(self.env)
        # print("Start...")

    def run(self):
        AppManager.updateTime()

        if not self.viewer.render(self.env):
            return -1

        return self.env.update()