#!/usr/bin/env python
 
"""PyQt4 port of the richtext/syntaxhighlighter example from Qt v4.x"""  
import sys
import os
import re
from PySide import QtGui, QtCore
import pandas as pd

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
                #self.itemChanged.emit(item, 0)
            self.itemDeleted.emit()
           

class LoadReturnsDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(LoadReturnsDialog, self).__init__(parent)
 
        self.setupTreeWidget()
        self.returns_tree.fileDropped.connect(self.returnsDropped)
        self.returns_tree.itemChanged.connect(self.printTreeContents)
        self.returns_tree.itemDeleted.connect(self.removeReturn)
        self.returns_tree.itemChanged.connect(self.updateInfo)
        self.returns_tree.itemDeleted.connect(self.updateInfo)
        self.load_count = 0
        self.returns = {}
    
        #self.update_return_count = QtCore.Signal(str)
        self.info = QtGui.QGroupBox()
        self.return_count = QtGui.QLabel(self)
        self.version_count = QtGui.QLabel(self)
        self.process_button = QtGui.QPushButton("&Process Returns", self)
        self.process_button.clicked.connect(self.processReturns)
        info_layout = QtGui.QVBoxLayout()
        info_layout.addWidget(QtGui.QLabel("Return files:"))
        info_layout.addWidget(self.return_count)
        info_layout.addWidget(QtGui.QLabel("Unique versions:"))
        info_layout.addWidget(self.version_count)
        info_layout.addWidget(self.process_button)
        self.info.setLayout(info_layout)
       
         
        layout = QtGui.QGridLayout()
        layout.addWidget(self.returns_tree, 0, 0, 5, 1)
        layout.addWidget(self.info, 0, 1)
        self.errorMessageDialog = QtGui.QErrorMessage(self)
        self.setLayout(layout)
        self.setWindowTitle("Load Returns")
        self.setMinimumWidth(400)
        
        
    def processReturns(self):
        print("Activated")
        
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
        
        
        
    def returnsDropped(self, l):
        for url in l:
            if os.path.exists(url):
                print(url)
                item = QtGui.QTreeWidgetItem(self.returns_tree)
                filename = os.path.basename(url)
                item.setText(0, filename)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                #item.setCheckState(3, QtCore.Qt.Unchecked)
                item.setToolTip(0, url) # Important for loading performance 
                date = re.sub(r'.*(\d{2})_(\d{2})_(\d{4}).*', r'\3-\1-\2', filename)
                if date:
                    item.setText(1, date)
                version = re.search(r'[Vv]ersion[-_. ]?[A-Z]', filename)
                if version:
                    v = re.sub(r'.*[Vv]ersion[-_. ]?([A-Z]).*', r'\1', version.group())
                    item.setText(2, v)
                                               

    def updateInfo(self):
         # Versions
        self.return_count.setText('<p style=font-size:20pt>{}</p>'.format(
                len(self.returns)))
        self.version_count.setText(
                '<p style=font-size:20pt>{}</p>'.format(len(self.versions())))
    def printTreeContents(self, widget, col):
        #for i in range(self.returns_tree.topLevelItemCount()):
            #item = self.returns_tree.topLevelItem(i)
            #print(",".join([item.text(ix) for ix in range(5)]))
        QtCore.QTextCodec.setCodecForLocale(QtCore.QTextCodec.codecForName('UTF-8'))
        path = '{}'.format(widget.toolTip(0))
        filename = os.path.basename(path)
        # Load if it hasn't been loaded yet
        if filename and filename not in self.returns:
            self.returns[filename] = pd.read_table('{}'.format(path))
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
           
    #all_files = pd.Series(os.listdir(returns_path))
    # Filter out files using a regex to include only valid gc1 returns
    #dates = ['-'.join([str(d)[-4:],str(d)[0:2],str(d)[3:5]]) for d in raw_dates]
    
   # raw = pd.DataFrame() # container for combined files
    def setupTreeWidget(self):
        self.returns_tree = ReturnsTreeView(self)
        self.returns_tree.setColumnCount(5)
        self.returns_tree.setSortingEnabled(True)
        self.returns_tree.setAnimated(True)
        self.returns_tree.setHeaderLabels(['File', 'Date', 'Version', 'Flag1', 'Flag2'])
        self.returns_tree.setColumnWidth(0, 400)
        self.returns_tree.setColumnWidth(1, 100)
        self.returns_tree.setColumnWidth(2, 100)
        self.returns_tree.setColumnWidth(3, 100)
        self.returns_tree.setColumnWidth(4, 100)
        
    def versions(self):
        unique_versions = []
        for i in range(self.returns_tree.topLevelItemCount()):
            v = self.returns_tree.topLevelItem(i).text(2)
            if v and v not in unique_versions: 
                unique_versions.append(v)
        return(unique_versions)
 
if __name__ == '__main__':
 
    app = QtGui.QApplication(sys.argv)
    window = LoadReturnsDialog()
    window.resize(1600, 1200)
    window.show()
    sys.exit(app.exec_())