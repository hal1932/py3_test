# coding: utf-8
from __future__ import absolute_import
from typing import *
from six.moves import *

from concurrent import futures
from multiprocessing.pool import ThreadPool
import time
import threading

from libs.gui.app import *
from libs.gui.layouts import *
from libs.gui.scopes import *


class TestObject(QObject):

    def __init__(self, layout, index):
        super(TestObject, self).__init__()
        self.layout = layout
        self.index = index

    @Slot()
    def add_label(self):
        print('slot {}: {}'.format(self.index, threading.current_thread().name))
        self.layout.addWidget(QLabel(str(self.index)))


class Model_Executer(QObject):

    def __init__(self):
        super(Model_Executer, self).__init__()
        self.__executer = futures.ThreadPoolExecutor(max_workers=4)
        self.__futures = {}
        self.__futures_lock = threading.Lock()

    def execute(self, layout):
        self.__set_wait_cursor()
        self.start = time.time()
        self.__futures = {i: self.__executer.submit(self.test, TestObject(layout, i)) for i in range(10)}

    def test(self, obj):
        QMetaObject.invokeMethod(obj, 'add_label', Qt.BlockingQueuedConnection)

        with self.__futures_lock:
            self.__futures.pop(obj.index)
            print(len(self.__futures))

        if len(self.__futures) == 0:
            print(time.time() - self.start)
            QMetaObject.invokeMethod(self, '__reset_cursor', Qt.QueuedConnection)

    def __set_wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    @Slot()
    def __reset_cursor(self):
        QApplication.restoreOverrideCursor()


class Model_ThreadPool_Invoke(QObject):

    def __init__(self):
        super(Model_ThreadPool_Invoke, self).__init__()
        self.__pool = ThreadPool(processes=4)
        self.__tasks = {}
        self.__tasks_lock = threading.Lock()

    def execute(self, layout):
        self.__set_wait_cursor()
        self.start = time.time()
        self.__tasks = {i: self.__pool.apply_async(self.test, [TestObject(layout, i)]) for i in range(10)}

    def test(self, obj):
        # print('invoke {}: {}'.format(obj.index, threading.current_thread().name))
        QMetaObject.invokeMethod(obj, 'add_label', Qt.BlockingQueuedConnection)

        with self.__tasks_lock:
            self.__tasks.pop(obj.index)

        if len(self.__tasks) == 0:
            print(time.time() - self.start)
            QMetaObject.invokeMethod(self, '__reset_cursor', Qt.QueuedConnection)

    def __set_wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    @Slot()
    def __reset_cursor(self):
        QApplication.restoreOverrideCursor()


class Model_ThreadPool_Signal(QObject):

    add_label = Signal(TestObject, QWaitCondition)

    def __init__(self):
        super(Model_ThreadPool_Signal, self).__init__()
        self.__pool = ThreadPool(processes=4)
        self.__tasks = {}
        self.__tasks_lock = threading.Lock()
        self.add_label.connect(self.on_add_label)

    def execute(self, layout):
        self.__set_wait_cursor()
        self.start = time.time()
        self.__tasks = {i: self.__pool.apply_async(self.test, [TestObject(layout, i)]) for i in range(10)}

    def test(self, obj):
        cond = QWaitCondition()
        mutex = QMutex()
        with QMutexLocker(mutex):
            self.add_label.emit(obj, cond)
            cond.wait(mutex)

        with self.__tasks_lock:
            self.__tasks.pop(obj.index)

        if len(self.__tasks) == 0:
            print(time.time() - self.start)
            QMetaObject.invokeMethod(self, '__reset_cursor', Qt.QueuedConnection)

    def __set_wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    @Slot()
    def __reset_cursor(self):
        QApplication.restoreOverrideCursor()

    def on_add_label(self, obj, cond):
        obj.add_label()
        cond.wakeOne()


class MainWindow(MainWindowBase):

    def __init__(self):
        super(MainWindowBase, self).__init__()
        self.__model = Model_ThreadPool_Signal()

    def _setup_ui(self, central_widget):
        # type: (QWidget) -> NoReturn
        self.setWindowTitle('title')
        button = QPushButton('execute')
        button.clicked.connect(self.__execute)
        self.test_layout = vbox()
        central_widget.setLayout(vbox(
            button,
            self.test_layout
        ))

    @wait_cursor_scope
    def __execute(self):
        self.__model.execute(self.test_layout)


class App(AppBase):

    def __init__(self):
        super(App, self).__init__()

    def _create_window(self):
        # type: () -> MainWindowBase
        return MainWindow()


def main():
    app = App()
    app.execute()


if __name__ == '__main__':
    main()
