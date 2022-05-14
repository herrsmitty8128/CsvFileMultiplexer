
#           Copyright Christopher Smith 2022.
# Distributed under the Boost Software License, Version 1.0.
#      (See accompanying file LICENSE.txt or copy at
#          https://www.boost.org/LICENSE_1_0.txt)

import sys
import CsvFileMultiplexer
from PyQt5 import QtWidgets, QtCore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(463, 296)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 117, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.testBtn = QtWidgets.QPushButton(self.centralwidget)
        self.testBtn.setObjectName("testBtn")
        self.horizontalLayout.addWidget(self.testBtn)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem3 = QtWidgets.QSpacerItem(20, 116, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.testBtn.clicked.connect(MainWindow.testCSVFileLoader)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Test CsvFileMultiplexer Dialog"))
        self.testBtn.setText(_translate("MainWindow", "Open CsvFileMultiplexer"))


class RowConverter(CsvFileMultiplexer.AbstractRowConverter):

    @staticmethod
    def fieldnames() -> set:
        return set([
            'name',
            'entries',
            'load_factor',
            'mem alloc',
            'ns_per_entry'
        ])

    def convert(self, csv_row: dict) -> object:
        row = {}
        row.update(csv_row)
        return row


class DataModel(CsvFileMultiplexer.AbstractDataModel):

    def __init__(self):
        self._data = []

    def add(self, data: object):
        self._data.append(data)


class MainTestWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, application):
        super().__init__()
        self.setupUi(self)
        self.application = application

    @QtCore.pyqtSlot()
    def testCSVFileLoader(self):
        dataModel = DataModel()
        result, errors = CsvFileMultiplexer.Dialog.load(self, dataModel, [RowConverter])
        print(result)
        for err in errors:
            print(err)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainTestWindow(app)
    window.show()
    sys.exit(app.exec_())
