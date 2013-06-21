
from PySide.QtCore import *
from PySide.QtGui import *

from .ui.infodialog import Ui_infodialog
from .ui.settings import Ui_settings


class Info(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.ui = Ui_infodialog()
        self.ui.setupUi(self)

    def show_dialog(self, name, info):
        while self.ui.layout.count() > 0:
            w = self.ui.layout.takeAt(0)
            w.widget().hide()
            w.widget().deleteLater()
        d = self.main.fmt.info_dialog(name, info)
        for a, b in d:
            self.ui.layout.addRow(a, QLabel(b))
        self.adjustSize()
        self.exec_()


class Settings(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.ui = Ui_settings()
        self.ui.setupUi(self)

