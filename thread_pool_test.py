# coding: utf-8
from __future__ import absolute_import
from typing import *
from six.moves import *

import sys
import os
import glob
import time

import multiprocessing.pool
import threading

from libs.gui.pyside_modules import *
from libs.gui.layouts import *


class ImageItem(object):

    @property
    def name(self):
        # type: () -> str
        return self.__name

    @property
    def path(self):
        # type: () -> str
        return self.__path

    @property
    def image(self):
        # type: () -> QImage
        return self.__image

    @property
    def pixmap(self):
        # type: () -> QPixmap
        return self.__pixmap

    def __init__(self, path):
        # type: (str) -> NoReturn
        super(ImageItem, self).__init__()
        self.__name = os.path.basename(path)
        self.__path = path
        self.__image = QImage(path).scaled(100, 100)
        self.__pixmap = None

    def convert_to_pixmap(self):
        # type: () -> NoReturn
        self.__pixmap = QPixmap(self.__image)
        self.__image = None


class ImageListView(QListView):

    def __init__(self):
        super(ImageListView, self).__init__()
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)

        self.__proxy_model = QSortFilterProxyModel()
        self.__proxy_model.setSortRole(Qt.DisplayRole)
        super(ImageListView, self).setModel(self.__proxy_model)

    def setModel(self, model):
        # type: (QAbstractItemModel) -> NoReturn
        self.__proxy_model.setSourceModel(model)

    def mouseDoubleClickEvent(self, e):
        # type: (QMouseEvent) -> NoReturn
        index = self.indexAt(e.pos())
        index = self.__proxy_model.mapToSource(index)
        item = self.__proxy_model.sourceModel().data(index, Qt.ItemDataRole)
        if item is not None:
            QMessageBox.information(self, 'image', item.path)

    def set_filter(self, pattern):
        # type: (str) -> NoReturn
        self.__proxy_model.setFilterWildcard(pattern)


class ImageListModel(QAbstractListModel):

    def __init__(self):
        super(ImageListModel, self).__init__()
        self.__items = []  # type: List[ImageItem]

    def append(self, item):
        # type: (ImageItem) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        self.__items.append(item)
        self.__items.sort(key=lambda x: x.name)
        self.endInsertRows()

    def extend(self, items):
        # type: (Iterable[ImageItem]) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(items))
        self.__items.extend(items)
        self.__items.sort(key=lambda x: x.name)
        self.endInsertRows()

    def clear(self):
        self.__items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.__items)

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, Qt.ItemDataRole) -> object

        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__items):
            return None

        item = self.__items[index.row()]

        if role == Qt.ItemDataRole:
            return item

        if role == Qt.DisplayRole:
            return item.name

        if role == Qt.DecorationRole:
            return item.image

        return None


class ImageLoader(QObject):

    loaded = Signal(ImageItem)
    completed = Signal()

    def __init__(self, directory, thread_count=multiprocessing.cpu_count()):
        # type: (str, int) -> NoReturn
        super(ImageLoader, self).__init__()
        self.__tasks_lock = threading.Lock()
        self.__tasks = {}  # type: Dict[str, multiprocessing.pool.AsyncResult]
        self.__pool = multiprocessing.pool.ThreadPool(processes=thread_count)
        self.__directory = directory

    def load_async(self):
        for path in glob.iglob(os.path.join(self.__directory, '*.png')):
            task = self.__pool.apply_async(self.__task_func, [path])
            self.__tasks[path] = task

    def join(self):
        tasks = list(self.__tasks.values())[:]
        for task in tasks:
            task.wait()

    def __task_func(self, path):
        # type: (str) -> NoReturn
        item = ImageItem(path)
        self.loaded.emit(item)

        with self.__tasks_lock:
            self.__tasks.pop(path)

        if len(self.__tasks) == 0:
            self.completed.emit()


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setMinimumSize(QSize(1000, 1000))

        area = QScrollArea()
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setWidgetResizable(True)

        self.__view = ImageListView()
        self.__model = ImageListModel()
        self.__view.setModel(self.__model)
        area.setWidget(self.__view)

        filter_text = QLineEdit()
        filter_text.textChanged.connect(lambda: self.__view.set_filter(filter_text.text()))

        button = QPushButton('run')
        button.clicked.connect(self.start)

        self.setLayout(vbox(
            button,
            filter_text,
            area
        ))

        self.__items = None  # type: List[ImageItem]

    def start(self):
        self.__items = []

        loader = ImageLoader('C:/tmp/test_images')
        loader.loaded.connect(self.update)
        loader.completed.connect(self.complete)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        loader.load_async()

    def update(self, item):
        # type: (ImageItem) -> NoReturn
        # self.model.append(item)
        self.__items.append(item)

    def complete(self):
        self.__model.clear()
        self.__model.extend(self.__items)
        QApplication.restoreOverrideCursor()
        self.__items = None


def main():
    # from PIL import Image, ImageDraw, ImageFont
    #
    # font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 500)
    # for i in range(1000):
    #     index = str(i).zfill(4)
    #     img = Image.new('RGB', (1024, 1024))
    #     draw = ImageDraw.Draw(img)
    #     draw.text((0, 0), index, font=font)
    #     img.save('C:/tmp/test_images/test_{}.png'.format(index))

    # import time
    # import gc
    # for i in [1, 2, 4, 8, 12, 16, 20, 24, 28, 32]:
    #     # print(i)
    #     times = []
    #     for _ in range(10):
    #         loader = ImageLoader('C:/tmp/test_images', i)
    #
    #         gc.collect()
    #         start = time.time()
    #         loader.load_async()
    #         loader.join()
    #         times.append(time.time() - start)
    #
    #         del loader
    #
    #     print(sum(times) / 10)

    # app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec_()


if __name__ == '__main__':
    main()
