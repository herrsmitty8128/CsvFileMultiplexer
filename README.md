# CsvFileMultiplexer

CsvFileMultiplexer is a dialog box (GUI) written in Python 3 using the PyQt5 module. It was created to make it easy to simultaneously read multiple CSV files, with varying columns, into a single data model.

## Please Note

In order to use CsvFileMultiplexer in your code, you must have PyQt5 installed.

## License

CSV File Multiplexer is licensed under the Boost Software License - Version 1.0 - August 17th, 2003

## Sample Code and Usage

To use CsvFileMultiplexer in your code, simply include CsvFileMultiplexer.py in the appropriate subdirectory of your project. Then include the appropriate *import CsvFileMultiplexer* statement in your code file(s).

### Step 1: Subclass the *CsvFileMultiplexer.AbstractRowConverter* class and implement the *fieldnames* and *convert* methods.

```python
class MyRowConverter(CsvFileMultiplexer.AbstractRowConverter):

    @staticmethod
    def fieldnames() -> set:
        return set([
            'header name 1',
            'header name 2',
            'header name 3'
        ])

    def convert(self, csv_row: dict) -> object:
        # use csv_row to create a new object
        return newOject
```

### Step 2: Subclass the *CsvFileMultiplexer.AbstractDataModel* class and implement the *add* method.

```python
class MyDataModel(CsvFileMultiplexer.AbstractDataModel):

    def __init__(self):
        self._data = []

    def add(self, data: object):
        # add the object to your data model
        self._data.append(data)
```

### Step 3: Instantiate your data model and pass it to *CsvFileMultiplexer.Dialog.load()*.

```python
class MyApplication:

    # other attributes, methods, and members here...

    @QtCore.pyqtSlot()
    def testCSVFileLoader(self):

        # create an instance of your data model
        dataModel = MyDataModel()

        # open the dialog box
        # pass the instance of your data model and a list of subclasses of the CsvFileMultiplexer.AbstractRowConverter class
        success, errors = CsvFileMultiplexer.Dialog.load(self, dataModel, [MyRowConverter])
        
        if success:
            # do something with your data model
        else:
            # do something with errors
```