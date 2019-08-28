# coding: utf-8
from __future__ import absolute_import
from typing import *
from six.moves import *

import time
import math
import multiprocessing.pool as pool


def main():

    def f():
        r = 0
        for x in range(50000):
            r *= x
        return r

    for i in [1, 2, 4, 8, 12, 16, 20, 24, 28, 32]:
        p = pool.ThreadPool(processes=i)

        start = time.time()
        tasks = []
        for _ in range(1000):
            task = p.apply_async(f)
            tasks.append(task)

        for t in tasks:
            t.wait()

        print(i, time.time() - start)

main()

