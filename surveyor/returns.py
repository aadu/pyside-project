import sys
import os
import re
import pandas as pd
import numpy as np
from PySide import QtGui, QtCore


class ReturnsTreeView(QtGui.QTreeWidget):
    fileDropped = QtCore.Signal(list)
    itemDeleted = QtCore.Signal()

    def __init__(self, type, parent=None):
        super(ReturnsTreeView, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.fileDropped.emit(links)
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Delete:
            root = self.invisibleRootItem()
            for item in self.selectedItems():
                (item.parent() or root).removeChild(item)
            self.itemDeleted.emit()


class ReturnsDialog(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ReturnsDialog, self).__init__(parent)
        self.load_count = 0
        self.returns = {}
        self.raw_returns = []
        self.createTreeWidget()
        self.createInfo()
        # SIGNALS
        self.returns_tree.fileDropped.connect(self.returnsDropped)
        self.returns_tree.itemChanged.connect(self.printTreeContents)
        self.returns_tree.itemDeleted.connect(self.removeReturn)
        self.returns_tree.itemChanged.connect(self.updateInfo)
        self.returns_tree.itemDeleted.connect(self.updateInfo)
        self.process.triggered.connect(self.processReturns)
        # setup UI
        layout = QtGui.QGridLayout()
        layout.addWidget(self.returns_tree, 0, 0, 5, 1)
        layout.addWidget(self.info, 0, 1)
        self.setLayout(layout)
        self.setWindowTitle("Load Returns")
        self.setMinimumWidth(400)

    def createTreeWidget(self):
        self.returns_tree = ReturnsTreeView(self)
        self.returns_tree.setColumnCount(5)
        self.returns_tree.setSortingEnabled(True)
        self.returns_tree.setAnimated(True)
        self.returns_tree.setHeaderLabels(['File', 'Date', 'Version', 'Flag1',
                                           'Flag2'])
        self.returns_tree.setColumnWidth(0, 400)
        self.returns_tree.setColumnWidth(1, 100)
        self.returns_tree.setColumnWidth(2, 100)
        self.returns_tree.setColumnWidth(3, 100)
        self.returns_tree.setColumnWidth(4, 100)

    def createInfo(self):
        self.info = QtGui.QGroupBox()
        self.return_count = QtGui.QLabel(self)
        self.version_count = QtGui.QLabel(self)
        self.process = QtGui.QAction(self)
        self.process.setText("Prep Returns")
        info_layout = QtGui.QVBoxLayout()
        info_layout.addWidget(QtGui.QLabel("Return files:"))
        info_layout.addWidget(self.return_count)
        info_layout.addWidget(QtGui.QLabel("Unique versions:"))
        info_layout.addWidget(self.version_count)
        self.info.setLayout(info_layout)

    def returnsDropped(self, l):
        for url in l:
            if os.path.exists(url):
                print(url)
                item = QtGui.QTreeWidgetItem(self.returns_tree)
                filename = os.path.basename(url)
                item.setText(0, filename)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                # Important for loading performance
                item.setToolTip(0, url)
                date = re.sub(r'.*(\d{2})_(\d{2})_(\d{4}).*',
                              r'\3-\1-\2', filename)
                if date:
                    item.setText(1, date)
                version = re.search(r'[Vv]ersion[-_. ]?[A-Z]', filename)
                if version:
                    v = re.sub(r'.*[Vv]ersion[-_. ]?([A-Z]).*',
                               r'\1', version.group())
                    item.setText(2, v)

    def removeReturn(self):
        tree_returns = []
        for i in range(self.returns_tree.topLevelItemCount()):
            item = self.returns_tree.topLevelItem(i)
            path = '{}'.format(item.toolTip(0))
            filename = os.path.basename(path)
            tree_returns.append(filename)
        delete = []
        for r in self.returns:
            if r not in tree_returns:
                delete.append(r)
        for r in delete:
            del self.returns[r]
            print("Deleted {}".format(r))

    def updateInfo(self):
        self.return_count.setText('<p style=font-size:20pt>{}</p>'.format(
                len(self.returns)))
        self.version_count.setText(
                '<p style=font-size:20pt>{}</p>'.format(len(self.versions())))

    def printTreeContents(self, widget, col):
        path = '{}'.format(widget.toolTip(0))
        filename = os.path.basename(path)
        # Load if it hasn't been loaded yet
        if filename and filename not in self.returns:
            self.returns[filename] = pd.read_table('{}'.format(path),
                                                   dtype=np.unicode_)
            self.load_count += 1
            print('Load Count: {}'.format(self.load_count))
            print('{} rows'.format(len(self.returns[filename])))
        if filename:
            date = widget.text(1)
            version = widget.text(2)
            flag1 = widget.text(3)
            flag2 = widget.text(4)
            if col == 1:
                self.returns[filename]['date'] = date
                print('date set to {}'.format(date))
            if col == 2:
                self.returns[filename]['version'] = version
                print('version set to {}'.format(version))
            if col == 3:
                self.returns[filename]['flag1'] = flag1
                print('"flag1" set to {}'.format(flag1))
            if col == 4:
                self.returns[filename]['flag2'] = flag2
                print('"flag2" set to {}'.format(flag2))
            print('{} columns'.format(len(self.returns[filename].columns)))

    def versions(self):
        unique_versions = []
        for i in range(self.returns_tree.topLevelItemCount()):
            v = self.returns_tree.topLevelItem(i).text(2)
            if v and v not in unique_versions:
                unique_versions.append(v)
        return(unique_versions)

    def processReturns(self):
        # Container for combined files
        raw = pd.DataFrame()
        for f in self.returns:
            if not len(raw):
                raw = self.returns[f]
            else:
                raw = pd.concat([raw, self.returns[f]])
        ts = raw['date'] + ' ' + raw['Time']
        raw['timestamp'] = pd.to_datetime(ts,
                                          format="%Y-%m-%d %H:%M:%S %p")
        if 'flag1' in raw:
            print("{}".format(raw['flag1'].unique()))
        if 'flag2' in raw:
            print("{}".format(raw['flag2'].unique()))
        raw.reset_index(drop=True, inplace=True)
        self.raw_returns = raw


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = ReturnsDialog()
    window.resize(1600, 1200)
    window.show()
    sys.exit(app.exec_())
