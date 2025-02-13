# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/CsvFileMultiplexerDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(888, 461)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.fileTableView = TableView(Dialog)
        self.fileTableView.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.fileTableView.setAlternatingRowColors(True)
        self.fileTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.fileTableView.setSortingEnabled(True)
        self.fileTableView.setWordWrap(False)
        self.fileTableView.setObjectName("fileTableView")
        self.fileTableView.verticalHeader().setSortIndicatorShown(True)
        self.verticalLayout.addWidget(self.fileTableView)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.addFileBtn = QtWidgets.QPushButton(Dialog)
        self.addFileBtn.setObjectName("addFileBtn")
        self.horizontalLayout.addWidget(self.addFileBtn)
        self.removeFileBtn = QtWidgets.QPushButton(Dialog)
        self.removeFileBtn.setObjectName("removeFileBtn")
        self.horizontalLayout.addWidget(self.removeFileBtn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.startLoadingBtn = QtWidgets.QPushButton(Dialog)
        self.startLoadingBtn.setEnabled(False)
        self.startLoadingBtn.setObjectName("startLoadingBtn")
        self.horizontalLayout.addWidget(self.startLoadingBtn)
        self.stopLoadingBtn = QtWidgets.QPushButton(Dialog)
        self.stopLoadingBtn.setEnabled(False)
        self.stopLoadingBtn.setObjectName("stopLoadingBtn")
        self.horizontalLayout.addWidget(self.stopLoadingBtn)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        self.addFileBtn.clicked.connect(Dialog.addFile) # type: ignore
        self.removeFileBtn.clicked.connect(Dialog.removeFile) # type: ignore
        self.startLoadingBtn.clicked.connect(Dialog.startLoading) # type: ignore
        self.stopLoadingBtn.clicked.connect(Dialog.stopLoading) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Load Data from CSV Files"))
        self.addFileBtn.setToolTip(_translate("Dialog", "Add a new file to the list above."))
        self.addFileBtn.setText(_translate("Dialog", "Add"))
        self.removeFileBtn.setToolTip(_translate("Dialog", "Remove selected files from the list above."))
        self.removeFileBtn.setText(_translate("Dialog", "Remove"))
        self.startLoadingBtn.setToolTip(_translate("Dialog", "Start loading the files above."))
        self.startLoadingBtn.setText(_translate("Dialog", "Start"))
        self.stopLoadingBtn.setToolTip(_translate("Dialog", "Stop loading files."))
        self.stopLoadingBtn.setText(_translate("Dialog", "Stop"))
from CsvFileLoader import TableView
