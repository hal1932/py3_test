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
    def pixmap(self):
        # type: () -> QPixmap
        if self.__pixmap is None:
            self.__pixmap = QPixmap(self.__image)
        return self.__pixmap

    def __init__(self, path):
        # type: (str) -> NoReturn
        super(ImageItem, self).__init__()
        self.__name = os.path.basename(path)
        self.__path = path
        self.__image = QImage(path).scaled(100, 100)
        self.__pixmap = None


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
        self.__items.clear()

    def rowCount(self, parent=QModelIndex()):
        return len(self.__items)

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, Qt.ItemDataRole) -> object

        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__items):
            return None

        item = self.__items[index.row()]

        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.DecorationRole:
            return item.pixmap
        elif role == Qt.ItemDataRole:
            return item
        elif role == Qt.UserRole:
            return item.path

        return None


class ImageLoader(QObject):

    loaded = Signal(ImageItem)
    completed = Signal()

    def __init__(self, directory):
        # type: (str) -> NoReturn
        super(ImageLoader, self).__init__()
        self.__tasks_lock = threading.Lock()
        self.__tasks = {}
        self.__pool = multiprocessing.pool.ThreadPool(processes=20)
        self.__directory = directory

    def run(self):
        for path in glob.iglob(os.path.join(self.__directory, '*.png')):
            task = self.__pool.apply_async(self.task_func, [path])
            self.__tasks[path] = task

    def task_func(self, path):
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

        self.view = ImageListView()
        self.model = ImageListModel()
        self.view.setModel(self.model)
        area.setWidget(self.view)

        filter_text = QLineEdit()
        filter_text.textChanged.connect(lambda: self.view.set_filter(filter_text.text()))

        button = QPushButton('run')
        button.clicked.connect(self.start)

        self.setLayout(vbox(
            button,
            filter_text,
            area
        ))

    def start(self):
        self.items = []

        loader = ImageLoader('C:/tmp/test_images')
        loader.loaded.connect(self.update)
        loader.completed.connect(self.complete)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        loader.run()

    def update(self, item):
        # type: (ImageItem) -> NoReturn
        # self.model.append(item)
        self.items.append(item)

    def complete(self):
        QApplication.restoreOverrideCursor()
        self.model.clear()
        self.model.extend(self.items)
        self.items.clear()


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
