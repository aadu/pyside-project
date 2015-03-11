import sys
from PySide import QtGui
import gc1


class GC1Dialog(QtGui.QDialog):
    def __init__(self):
        super(GC1Dialog, self).__init__()

    def processGC1(self):
        df, cpt = gc1.macro(
                            self.returns_widget.raw_returns,
                            self.editor.config, True)
        df.to_csv('output.csv', index=False)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = GC1Dialog()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
