from PySide import QtCore, QtGui
import formencode
import yaml
import gc1
from highlight import Highlighter


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


class ConfigEditor(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigEditor, self).__init__(parent)
        self.config = {}
        self.setupEditor()
        self.setupTree()
        self.setupInfo()
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.editor)
        self.setLayout(self.layout)
        self.setMinimumWidth(200)
        self.editor.textChanged.connect(self.update_tree)

    def setupInfo(self):
        self.label1 = QtGui.QLabel("A Label")
        self.label1.setWordWrap(True)
        self.label2 = QtGui.QLabel("Another one")
        self.label2.setWordWrap(True)
        self.save_button = QtGui.QPushButton("&Save Config", self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.label2)
        layout.addWidget(self.save_button)
        self.display = QtGui.QWidget()
        self.display.setLayout(layout)

    def setupTree(self):
        self.config_tree = QtGui.QTreeWidget()
        self.config_tree.setColumnCount(4)
        self.config_tree.setSortingEnabled(True)
        self.config_tree.setAnimated(True)
        self.config_tree.setHeaderLabels(['Label',
                                          'Q#/Value', 'Version', 'Only If'])
        self.config_tree.setColumnWidth(0, 200)
        self.config_tree.setColumnWidth(1, 100)
        self.config_tree.setColumnWidth(2, 80)
        self.config_tree.setColumnWidth(3, 100)
        self.validator = gc1.ValidConfig()

    def update_tree(self):
        text = self.editor.toPlainText()
        validator = self.validator
        config_string = ""
        try:
            config_string = yaml.load(text)
            self.label1.setText("")
        except yaml.YAMLError as exc:
            self.label1.setText(str(exc))
            print(exc)
        try:
            config = validator.to_python(config_string)
            self.config = config
            self.label2.setText("")
            self.config_tree.clear()
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

    # Capture Tabs and Replace with three spaces
    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.KeyPress and
                widget is self.editor):
            key = event.key()
            if key == QtCore.Qt.Key_Tab:
                self.editor.insertPlainText("   ")
                return(True)
        return QtGui.QWidget.eventFilter(self, widget, event)

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
            "QTextEdit {background-color:#272822; margin: 6px;padding: 5px;}")
        self.editor.installEventFilter(self)
        self.highlighter = Highlighter(self.editor.document())
        self.editor.setFrameStyle(QtGui.QFrame.Panel)


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = ConfigEditor()
    window.resize(1600, 1200)
    window.show()
    sys.exit(app.exec_())
