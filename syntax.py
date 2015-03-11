from PySide import QtCore, QtGui
import formencode
import yaml
import gc1
from hilight import Highlighter


class TreeWidgetItem(QtGui.QTreeWidgetItem):
        def __init__(self, parent=None):
            QtGui.QTreeWidgetItem.__init__(self, parent)

        def __lt__(self, otherItem):
            column = self.treeWidget().sortColumn()
            try:
                return(float(self.text(column)) <
                       float(otherItem.text(column)))
            except ValueError:
                return self.text(column) < otherItem.text(column)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupFileMenu()
        self.setupHelpMenu()
        self.setupEditor()
        self.label1 = QtGui.QLabel("A Label")
        self.label1.setWordWrap(True)
        self.label2 = QtGui.QLabel("Another one")
        self.label2.setWordWrap(True)
        self.config_tree = QtGui.QTreeWidget()
        self.config_tree.setColumnCount(4)
        self.config_tree.setSortingEnabled(True)
        self.config_tree.setAnimated(True)
        self.config_tree.setHeaderLabels(
                                         ['Label', 'Q#/Value',
                                          'Version', 'Only If'])
        self.config_tree.setColumnWidth(0, 200)
        self.config_tree.setColumnWidth(1, 100)
        self.config_tree.setColumnWidth(2, 80)
        self.config_tree.setColumnWidth(3, 100)
        self.errorMessageDialog = QtGui.QErrorMessage(self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.label2)
        display = QtGui.QWidget()
        display.setLayout(layout)
        splitter = QtGui.QSplitter()
        splitter.addWidget(self.editor)
        splitter.addWidget(self.config_tree)
        splitter.addWidget(display)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 5)
        self.setCentralWidget(splitter)
        self.setWindowTitle("Config Testing")
        self.setMinimumWidth(400)
        self.editor.textChanged.connect(self.update_tree)

    def update_tree(self):
        text = self.editor.toPlainText()
        validator = gc1.ValidConfig()
        try:
            config_string = yaml.load(text)
            self.label1.setText("")
        except yaml.YAMLError as exc:
            self.label1.setText(str(exc))
            print(exc)
        try:
            config = validator.to_python(config_string)
            self.label2.setText("")
            questions = config['questions']
            for q in questions:
                parent = TreeWidgetItem(self.config_tree)
                parent.setText(0, str(q['name']))
                parent.setText(1, '{}'.format(q['order']))
                if q['version']:
                    parent.setText(2, '{}'.format(q['version']))
                if q['onlyif']:
                    parent.setText(3, 'Q{}=={}'.format(
                        q.get('onlyif').get('question'),
                        q.get('onlyif').get('equals')))
                items = q.get('responses')
                for key in sorted(items, key=items.get):
                    i = TreeWidgetItem(parent)
                    i.setText(0, str(key))
                    i.setText(1, str(items[key]))
                    i_font = i.font(0)
                    i_font.setItalic(True)
                    i.setFont(0, i_font)
                    i.setFont(1, i_font)
                    i.setTextAlignment(1, QtCore.Qt.AlignHCenter)
        except formencode.Invalid as exc:
            self.label2.setText(str(exc))
            print(exc)

    def about(self):
        QtGui.QMessageBox.about(self, "About Syntax Highlighter",
                                ("<p>The <b>Syntax Highlighter</b> "
                                 "example shows how to perform simple "
                                 "syntax highlighting by subclassing the "
                                 "QSyntaxHighlighter class and describing "
                                 "highlighting rules using regular "
                                 "expressions.</p>"))

    def newFile(self):
        self.editor.clear()

    def openFile(self, path=None):
        if not path:
            path = QtGui.QFileDialog.getOpenFileName(
                                                self, "Open File",
                                                "",
                                                "YAML files (*.yaml *.yml)")
        if path:
            inFile = QtCore.QFile(path[0])
            if inFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                text = inFile.readAll()
                try:
                    # Python v3.
                    text = str(text, encoding='ascii')
                except TypeError:
                    # Python v2.
                    text = str(text)
                self.editor.setPlainText(text)

    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.KeyPress and
                widget is self.editor):
            key = event.key()
            if key == QtCore.Qt.Key_Tab:
                self.editor.insertPlainText("   ")
                return(True)
        return(QtGui.QWidget.eventFilter(self, widget, event))

    def setupEditor(self):
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(14)
        self.editor = QtGui.QTextEdit()
        self.editor.setFont(font)
        self.editor.setTextColor("#75715e")
        self.editor.setTabStopWidth(30)
        self.editor.setStyleSheet(
                                  ("QTextEdit {background-color:#272822;"
                                   " margin: 6px;padding: 5px;}"))
        self.editor.installEventFilter(self)
        self.highlighter = Highlighter(self.editor.document())
        self.editor.setFrameStyle(QtGui.QFrame.Panel)

    def setupFileMenu(self):
        fileMenu = QtGui.QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)
        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("E&xit", QtGui.qApp.quit, "Ctrl+Q")

    def setupHelpMenu(self):
        helpMenu = QtGui.QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)
        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QtGui.qApp.aboutQt)


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.resize(1600, 1200)
    window.show()
    sys.exit(app.exec_())
