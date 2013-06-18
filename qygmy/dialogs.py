
from PySide.QtCore import *
from PySide.QtGui import *

from .ui.details import Ui_details


class Details(QDialog):
    def __init__(self, main, formatter):
        super().__init__(main)
        self.main = main
        self.fmt = formatter
        self.ui = Ui_details()
        self.ui.setupUi(self)

    def show_details(self, metadata):
        self.ui.details_label.setText(self.fmt.details(metadata))
        self.exec_()

