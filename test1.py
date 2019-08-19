# coding: utf-8
from __future__ import absolute_import
from typing import *
from six.moves import *

import sys
import glob
import threading
import time
import random

import multiprocessing.pool
import threading

from libs.gui.pyside_modules import *
from libs.gui.layouts import *


class ImageItem(object):

    def __init__(self, path):
        super(ImageItem, self).__init__()
        self.path = path
        self.image = QImage(path)


class ImageLabel(QLabel):

    def __init__(self, item):
        super(ImageLabel, self).__init__()
        pix = QPixmap(item.image).scaled(100, 100)
        # pix = QPixmap(item.path).scaled(100, 100)
        self.setPixmap(pix)
        self.item = item

    def mouseDoubleClickEvent(self, *args, **kwargs):
        QMessageBox.information(self, 'image', self.item.path)


class ImageLoader(QObject):

    loaded = Signal(ImageItem)
    completed = Signal()

    def __init__(self, directory):
        super(ImageLoader, self).__init__()
        self.is_stopped = False
        self.lock = threading.Lock()
        self.tasks = {}
        self.pool = multiprocessing.pool.ThreadPool(processes=20)
        self.directory = directory

    def run(self):
        self.start = time.time()
        for path in glob.glob(self.directory + '/*.png'):
            task = self.pool.apply_async(self.task_func, [path])
            self.tasks[path] = task

    def task_func(self, path):
        # time.sleep(random.random())
        item = ImageItem(path)
        time.sleep(0.1)
        self.loaded.emit(item)
        with self.lock:
            self.tasks.pop(path)
        if len(self.tasks) == 0:
            self.completed.emit()
            print(time.time() - self.start)


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setMinimumSize(QSize(1000, 1000))

        self.layout = FlowLayout()
        w = QWidget()
        w.setLayout(self.layout)

        area = QScrollArea()
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setWidgetResizable(True)
        area.setWidget(w)

        button = QPushButton('run')
        button.clicked.connect(self.start)

        self.setLayout(vbox(
            button,
            area
        ))

    def start(self):
        for _ in range(self.layout.count()):
            w = self.layout.takeAt(0)
            w.widget().deleteLater()

        task = ImageLoader('C:/tmp/test_images')
        task.loaded.connect(self.update)
        task.completed.connect(self.complete)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        task.run()

    def update(self, item):
        label = ImageLabel(item)
        self.layout.addWidget(label)

    def complete(self):
        QApplication.restoreOverrideCursor()


if __name__ == '__main__':
    # from PIL import Image, ImageDraw, ImageFont
    #
    # font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 500)
    # for i in range(1000):
    #     index = str(i).zfill(4)
    #     img = Image.new('RGB', (1024, 1024))
    #     draw = ImageDraw.Draw(img)
    #     draw.text((0, 0), index, font=font)
    #     img.save('C:/tmp/test_images/test_{}.png'.format(index))

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec_()
