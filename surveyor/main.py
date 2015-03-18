import sys
import config
import returns
import gc1
import logger
import queue
from PySide import QtGui, QtCore


class RunGC1Macro(QtCore.QObject):
    processed = QtCore.Signal(list)

    def __init__(self, returns, config):
        QtCore.QObject.__init__(self)
        self.returns = returns
        self.config = config

    @QtCore.Slot()
    def run(self):
        df, cpt = gc1.macro(self.returns, self.config, True)
        self.processed_returns = df
        self.processed.emit([df])


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.errorMessageDialog = QtGui.QErrorMessage(self)
        self.raw_returns = {}
        self.editor = config.ConfigEditor(self)
        self.returns_widget = returns.ReturnsDialog(self)
        self.setCentralWidget(self.createLogo())
        self.createMenus()
        self.createDockWindows()
        self.createToolBars()
        self.createStatusBar()
        self.config = {}
        self.processed_returns = {}
        self.setGeometry(500, 200, 850, 550)
        self.setWindowTitle('Read-o-matic')
        self.show()
        self.readSettings()

    def start_thread(self):
        log_queue = queue.Queue()
        sys.stdout = logger.WriteStream(log_queue)
        self.thread = QtCore.QThread()
        self.my_receiver = logger.MyReceiver(log_queue)
        self.my_receiver.mysignal.connect(self.log_widget.append_text)
        self.my_receiver.moveToThread(self.thread)
        self.thread.started.connect(self.my_receiver.run)
        self.thread.start()

    def createLogo(self):
        logo = QtGui.QPixmap('static/0ptimusLogo_Charcoal.png')
        logo = logo.scaled(200, 200, QtCore.Qt.KeepAspectRatio)
        optimus_logo = QtGui.QLabel(self)
        optimus_logo.setPixmap(logo)
        optimus_logo.setMargin(30)
        size = optimus_logo.sizePolicy()
        size.setHorizontalStretch(1)
        optimus_logo.setSizePolicy(size)
        return(optimus_logo)

    def openReturnsDialog(self):
        returns_dialog = returns.ReturnsDialog(self)
        returns_dialog.resize(1000, 650)
        if returns_dialog.exec_():
            self.raw_returns = returns_dialog.raw_returns
            print("{}".format(len(self.raw_returns)))
        else:
            print("Canceled")

    def processReturns(self):
        self.returns_widget.process.trigger()
        if not len(self.returns_widget.raw_returns):
            QtGui.QMessageBox.warning(self,
                                      "Warning", "No return files to process.")
        elif not len(self.editor.config):
            QtGui.QMessageBox.warning(self, "Warning",
                                      "Question configuration missing.")
        else:
            self.start_thread()
            self.gc1_thread = QtCore.QThread()
            self.gc1_macro = RunGC1Macro(
                                         self.returns_widget.raw_returns,
                                         self.editor.config)
            self.gc1_macro.moveToThread(self.gc1_thread)
            self.gc1_thread.started.connect(self.gc1_macro.run)
            self.gc1_macro.processed.connect(self.setSaveFileName)
            self.gc1_thread.start()

    def setSaveFileName(self, results):
        self.processed_returns = results[0]
        options = QtGui.QFileDialog.Options()
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(
                                        self,
                                        "Save Processed Returns",
                                        "returns.csv",
                                        "All Files (*);;Text Files (*.csv)",
                                        "", options)
        if fileName:
            self.processed_returns.to_csv(fileName, index=False)

    def writeSettings(self):
        settings = QtCore.QSettings("Read-o-matic", "0ptimus")
        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.setValue("pos", self.pos())
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.endGroup()

    def readSettings(self):
        settings = QtCore.QSettings("Read-o-matic", "0ptimus")
        settings.beginGroup("MainWindow")
        size = settings.value("size", QtCore.QSize(400, 400))
        pos = settings.value("pos", QtCore.QPoint(200, 200))
        geometry = settings.value("geometry")
        state = settings.value("windowState")
        settings.endGroup()
        self.resize(size)
        self.move(pos)
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def createToolBars(self):
        self.toolbar = self.addToolBar('Returns')
        self.toolbar.setObjectName("returns_toolbar")
        processReturns = QtGui.QAction(
                                       QtGui.QIcon('static/circleright32.png'),
                                       'Process Returns', self)
        processReturns.setShortcut('Ctrl+p')
        self.toolbar.addAction(processReturns)
        processReturns.triggered.connect(self.processReturns)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def createDockWindows(self):
        self.setDockNestingEnabled(True)
        dock = QtGui.QDockWidget("Questions", self)
        dock.setWidget(self.editor.config_tree)
        dock.setObjectName("qtree_dock")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        dock = QtGui.QDockWidget("Config Editor", self)
        dock.setWidget(self.editor)
        dock.setObjectName("config_dock")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        dock = QtGui.QDockWidget("Returns", self)
        dock.setWidget(self.returns_widget)
        dock.setObjectName("returns_dock")
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        self.log_widget = logger.LogWidget()
        dock = QtGui.QDockWidget("Processing", self)
        dock.setWidget(self.log_widget)
        dock.setObjectName("processing_window")
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

    def createMenus(self):
        self.viewMenu = self.menuBar().addMenu("&View")

    def closeEvent(self, event):
        if True:
            self.writeSettings()
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
