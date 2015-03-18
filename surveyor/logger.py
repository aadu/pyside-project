import sys
from queue import Queue
from PySide import QtCore, QtGui


class WriteStream(object):
    """Replaces the default stream associated with sys.stdout."""
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


class MyReceiver(QtCore.QObject):
    """Stream receiver
    A QObject (to be run in a QThread) which sits waiting for
    data to come through a Queue.Queue(). It blocks until
    data is available, and one it has got something from the
    queue, it sends it to the "MainThread" by emitting a
    Qt Signal."""
    mysignal = QtCore.Signal(str)

    def __init__(self, queue, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.queue = queue

    @QtCore.Slot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class LongRunningThing(QtCore.QObject):
    """An example QObject (to be run in a QThread)
    which outputs information with print."""
    @QtCore.Slot()
    def run(self):
        for i in range(1000):
            print(i)


class LogWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(LogWidget, self).__init__()
        self.layout = QtGui.QVBoxLayout(self)
        self.textedit = QtGui.QTextEdit()
        self.textedit.setTextColor("#119E11")
        self.layout.addWidget(self.textedit)

    @QtCore.Slot()
    def append_text(self, text):
        self.textedit.moveCursor(QtGui.QTextCursor.End)
        self.textedit.insertPlainText(text)

    @QtCore.Slot()
    def start_thread(self):
        self.thread = QtCore.QThread()
        self.long_running_thing = LongRunningThing()
        self.long_running_thing.moveToThread(self.thread)
        self.thread.started.connect(self.long_running_thing.run)
        self.thread.start()


if __name__ == '__main__':
    # Create Queue and redirect sys.stdout to this queue
    queue = Queue()
    sys.stdout = WriteStream(queue)
    # Create QApplication and QWidget
    qapp = QtGui.QApplication(sys.argv)
    app = LogWidget()
    app.show()
    # Create thread that will listen on the other end of the
    # queue, and send the text to the textedit in our application
    thread = QtCore.QThread()
    my_receiver = MyReceiver(queue)
    my_receiver.mysignal.connect(app.append_text)
    my_receiver.moveToThread(thread)
    thread.started.connect(my_receiver.run)
    thread.start()
    qapp.exec_()
