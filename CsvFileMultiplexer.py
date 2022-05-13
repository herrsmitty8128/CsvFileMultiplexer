
#           Copyright Christopher Smith 2022.
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          https://www.boost.org/LICENSE_1_0.txt)

from typing import Iterable
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
import abc
import os
import csv
import uuid
import io
import queue
import enum


class AbstractRowConverter(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def fieldnames() -> set:
        '''
        This static method should return a set of the csv file headers that the self.convert()
        method will need to construct an object from a row in a csv file.
        '''
        raise NotImplementedError('CsvFileLoader.AbstractRowConverter.fieldnames()->set has not been implemented.')

    @abc.abstractmethod
    def convert(csv_row: dict) -> object | None:
        '''
        It is this method's job to convert the data in a csv row into a more useful format for
        inclusion in a data model. Return None if you do not want the object to be included in
        the data model.
        '''
        raise NotImplementedError('CsvFileLoader.AbstractRowConverter.convert(csv_row:dict)->object has not been implemented.')


class AbstractDataModel(abc.ABC):

    @abc.abstractmethod
    def add(self, data: object) -> None:
        '''
        This static method adds data to the data model.
        '''
        raise NotImplementedError('CsvFileLoader.AbstractDatModel.add(data:object)->set has not been implemented.')


class DataModelWorker(QtCore.QRunnable):

    def __init__(self, dataModel: AbstractDataModel):
        super().__init__()
        self.dataModel = dataModel
        self.objectQueue = queue.Queue()
        self.running = True

    @QtCore.pyqtSlot()
    def run(self):
        while self.running:
            while not self.objectQueue.empty():
                self.dataModel.add(self.objectQueue.get())
        while not self.objectQueue.empty():
            self.dataModel.add(self.objectQueue.get())

    def stop(self):
        self.running = False


class RowConverterFactory:

    def __init__(self, converterClasses: Iterable):
        '''
        converterClasses: An iterable collection of classes that implement the AbstractRowConverter class.
        '''
        self.converterClasses = set()
        for converterClass in converterClasses:
            if not issubclass(converterClass, AbstractRowConverter):
                raise TypeError('converterClasses arg contains an object that is not a subclass of AbstractRowConverter')
            self.converterClasses.add(converterClass)

    def makeRowConverter(self, columnHeaders: Iterable) -> AbstractRowConverter:
        '''
        Returns an instance of the AbstractRowConverter object in the converterClasses collection that cooresponds to csvColumnHeaders.
        columnHeaders: Typically a list or set of str objects that represent the column headers in a csv file.
        '''
        # if fieldnames is not a set object, then try to convert it to one
        headers = columnHeaders if isinstance(columnHeaders, set) else set(x for x in columnHeaders)
        for converterClass in self.converterClasses:
            fields = converterClass.fieldnames()
            # if fields is not a set object, then try to convert it to one
            if not isinstance(fields, set):
                fields = set(x for x in fields)
            if fields.issubset(headers):
                return converterClass()
        return None


class MessageTypes(enum.Enum):
    UPDATE = 1
    FINISHED = 2
    ERROR = 3


class InputFileWorker(QtCore.QRunnable):

    def __init__(self, file: io.TextIOWrapper, converterClasses: Iterable, objectQueue: queue.Queue, progressQueue: queue.Queue, fileSize: int):
        super().__init__()
        self.file = file
        self.running = True
        self.workerID = uuid.uuid4()
        self.factory = RowConverterFactory(converterClasses)
        self.objectQueue = objectQueue
        self.progressQueue = progressQueue
        self.fileSize = fileSize

    @QtCore.pyqtSlot()
    def run(self):
        position = 0
        progress = 0
        prevProgress = 0
        try:
            reader = csv.DictReader(self.file)
            converter = self.factory.makeRowConverter(reader.fieldnames)
            if converter is None:
                raise ValueError('Unable to create a RowConverter object with the given RowConverterFactory object.')
            for row in reader:
                if not self.running:
                    break
                obj = converter.convert(row)
                if obj:
                    self.objectQueue.put(obj)
                self.file.flush()
                position = self.file.tell()
                progress = round(position / self.fileSize * 100)
                if progress > prevProgress:
                    self.progressQueue.put((self.workerID, MessageTypes.UPDATE, progress))
                prevProgress = progress
        except Exception as err:
            self.progressQueue.put((self.workerID, MessageTypes.ERROR, str(err)))
        finally:
            self.progressQueue.put((self.workerID, MessageTypes.FINISHED, progress))

    def stop(self):
        self.running = False


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.headerNames = ['File Name', 'Last Modified', 'File Size', 'Progress']

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return 0 if self._data is None else len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return len(self.headerNames)

    def headerData(self, index: int, orient: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> QtCore.QVariant:
        if role == QtCore.Qt.DisplayRole:
            if orient == QtCore.Qt.Horizontal:
                return self.headerNames[index]
            if orient == QtCore.Qt.Vertical:
                return index + 1
        return QtCore.QVariant()

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> QtCore.QVariant:
        if index.isValid():
            row = self._data[index.row()]
            header = self.headerNames[index.column()]
            if role == QtCore.Qt.TextAlignmentRole and (header == 'File Size' or header == 'Last Modified'):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            if role == QtCore.Qt.DisplayRole:
                if header == 'Progress':
                    widget = self.parent().indexWidget(index)
                    if not widget:
                        self.parent().setIndexWidget(index, row['Progress'])
                elif header == 'File Size':
                    size = row[header]
                    if size > 1000000000000:
                        return str(round(size / 1000000000000, 1)) + ' TB'
                    if size > 1000000000:
                        return str(round(size / 1000000000, 1)) + ' GB'
                    if size > 1000000:
                        return str(round(size / 1000000, 1)) + ' MB'
                    if size > 1000:
                        return str(round(size / 1000, 1)) + ' KB'
                    return str(round(size, 1)) + ' B'
                else:
                    return row[header]
        return QtCore.QVariant()

    def setData(self, index: QtCore.QModelIndex, value: QtCore.QVariant, role: int = QtCore.Qt.EditRole) -> bool:
        if index.isValid():
            row = self._data[index.row()]
            header = self.headerNames[index.column()]
            if role == QtCore.Qt.EditRole:
                row[header] = value
                return True
        return False

    def insertRow(self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        self.beginInsertRows(parent, row, row)
        progressBar = QtWidgets.QProgressBar(self.parent())
        progressBar.setValue(0)
        progressBar.setTextVisible(True)
        self._data.insert(row, {'File Name': '', 'Last Modified': '', 'File Size': 0.0, 'Progress': progressBar})
        self.endInsertRows()
        return True

    def appendFile(self, fileName: str, lastModified: object, fileSize: int) -> None:
        if self.insertRow(self.rowCount()):
            index = self.index(self.rowCount() - 1, 0)
            self.setData(index, fileName)
            index = self.index(self.rowCount() - 1, 1)
            self.setData(index, lastModified)
            index = self.index(self.rowCount() - 1, 2)
            self.setData(index, fileSize)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def sort(self, col: int, order: QtCore.Qt.SortOrder = QtCore.Qt.AscendingOrder) -> None:
        if col < len(self.headerNames) - 1:
            self.layoutAboutToBeChanged.emit()
            field = self.headerNames[col]
            self._data.sort(key=lambda x: x[field], reverse=order)
            self.layoutChanged.emit()

    def removeRow(self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        return True


class TableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel(TableModel(parent=self))
        self.setColumnWidth(0, 550)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 100)
        self.horizontalHeader().setStretchLastSection(True)

    @QtCore.pyqtSlot()
    def removeSelectedRows(self):
        rows = set(x.row() for x in self.selectionModel().selectedIndexes())
        for row in sorted(rows, reverse=True):
            self.model().removeRow(row)

    def appendFiles(self, fileNames: list):
        for fileName in fileNames:
            fileSize = round(os.stat(fileName).st_size, 1)
            lastModified = round(os.stat(fileName).st_mtime, 1)
            lastModified = datetime.fromtimestamp(lastModified).strftime('%Y-%m-%d %H:%M')
            self.model().appendFile(fileName, lastModified, fileSize)


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1000, 500)
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
        self.addFileBtn.clicked.connect(Dialog.addFile)  # type: ignore
        self.removeFileBtn.clicked.connect(Dialog.removeFile)  # type: ignore
        self.startLoadingBtn.clicked.connect(Dialog.startLoading)  # type: ignore
        self.stopLoadingBtn.clicked.connect(Dialog.stopLoading)  # type: ignore
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


class Dialog(QtWidgets.QDialog, Ui_Dialog):

    @staticmethod
    def load(parent, dataModel: AbstractDataModel, converterClasses: Iterable) -> tuple[int, list]:
        return Dialog(parent, dataModel, converterClasses).exec_()

    def exec_(self) -> tuple[int, list]:
        return (super().exec_(), self.errorLog)

    def __init__(self, parent, dataModel: AbstractDataModel, converterClasses: Iterable, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent, flags)
        self.setupUi(self)
        self.didNotComplete = False
        self.errorLog = []
        self.fileWorkers = {}
        self.dataWorker = None
        self.dataModel = dataModel
        self.converterClasses = converterClasses
        self.threadPool = QtCore.QThreadPool()
        self.progressQueue = queue.Queue()
        self.timer = self.startTimer(10)

    def closeEvent(self, event) -> None:
        if len(self.fileWorkers) > 0:
            event.ignore()  # if there are active InputFileWorker classes, then ignore the close event
        else:
            event.accept()  # accept the close event

    @QtCore.pyqtSlot()
    def addFile(self) -> None:
        try:
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Select one or more CSV files to load', '*.csv', '*.csv')
            self.findChild(QtWidgets.QTableView, 'fileTableView').appendFiles(files)
            self.findChild(QtWidgets.QPushButton, 'startLoadingBtn').setEnabled(True)
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Error', str(err))

    @QtCore.pyqtSlot()
    def removeFile(self) -> None:
        try:
            response = QtWidgets.QMessageBox.question(self, 'Confirm Deletion', 'Are you sure you want to delete the selected rows?')
            if response == QtWidgets.QMessageBox.Yes:
                tableView = self.findChild(QtWidgets.QTableView, 'fileTableView')
                tableView.removeSelectedRows()
                if tableView.model().rowCount() == 0:
                    self.findChild(QtWidgets.QPushButton, 'startLoadingBtn').setEnabled(False)
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Error', str(err))

    @QtCore.pyqtSlot()
    def startLoading(self) -> None:
        try:
            self.findChild(QtWidgets.QPushButton, 'startLoadingBtn').setEnabled(False)
            self.findChild(QtWidgets.QPushButton, 'stopLoadingBtn').setEnabled(True)
            self.findChild(QtWidgets.QPushButton, 'addFileBtn').setEnabled(False)
            self.findChild(QtWidgets.QPushButton, 'removeFileBtn').setEnabled(False)
            self.didNotComplete = False
            self.errorLog = []
            self.fileWorkers = {}
            self.dataWorker = DataModelWorker(self.dataModel)
            self.threadPool.start(self.dataWorker)
            model = self.findChild(QtWidgets.QTableView, 'fileTableView').model()
            for row in model._data:
                fileHandle = open(row['File Name'], 'r', newline='')
                worker = InputFileWorker(fileHandle, self.converterClasses, self.dataWorker.objectQueue, self.progressQueue, row['File Size'])
                self.fileWorkers[worker.workerID] = {
                    'Progress Bar': row['Progress'],
                    'File Handle': fileHandle,
                    'Worker': worker
                }
                self.threadPool.start(worker)
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Error', str(err))

    def timerEvent(self, event: QtCore.QTimerEvent) -> None:
        try:
            while not self.progressQueue.empty():
                workerID, messageType, value = self.progressQueue.get()
                if messageType == MessageTypes.UPDATE:
                    self.fileWorkers[workerID]['Progress Bar'].setValue(value)
                elif messageType == MessageTypes.ERROR:
                    self.errorLog.append(value)
                elif messageType == MessageTypes.FINISHED:
                    if value < 100:
                        self.didNotComplete = True
                        fileName = self.fileWorkers[workerID]['File Handle'].name
                        self.errorLog.append(f'Did not finish loading data from {fileName}')
                    self.fileWorkers[workerID]['File Handle'].close()
                    self.fileWorkers[workerID]['Progress Bar'].setValue(value)
                    del self.fileWorkers[workerID]
                    if len(self.fileWorkers) == 0:
                        self.dataWorker.stop()
                        if self.didNotComplete:
                            QtWidgets.QMessageBox.warning(self, 'Load incomplete', 'Not all csv files were successfully loaded.')
                            self.done(QtWidgets.QDialog.Rejected)
                        else:
                            QtWidgets.QMessageBox.information(self, 'Load complete', 'Successfully loaded all csv files.')
                            self.done(QtWidgets.QDialog.Accepted)
                else:
                    raise ValueError('Unrecognized message type received.')
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Error', str(err))

    @QtCore.pyqtSlot()
    def stopLoading(self) -> None:
        try:
            for workerInfo in self.fileWorkers.values():
                workerInfo['Worker'].stop()
            self.dataWorker.stop()
            self.findChild(QtWidgets.QPushButton, 'startLoadingBtn').setEnabled(True)
            self.findChild(QtWidgets.QPushButton, 'addFileBtn').setEnabled(True)
            self.findChild(QtWidgets.QPushButton, 'removeFileBtn').setEnabled(True)
            self.findChild(QtWidgets.QPushButton, 'stopLoadingBtn').setEnabled(False)
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Error', str(err))
