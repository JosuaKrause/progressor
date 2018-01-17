#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import io
import sys
import time
import math
import random

__version__ = "0.1.14"


times = [
    (1000, "s"),
    (1000*60, "m"),
    (1000*60*60, "h"),
    (1000*60*60*24, "d"),
]
def convert_time_ms(value):
    if value is None:
        return "  ??????"
    cur = ""
    prev_u = ""
    prev_c = 1
    for (conv, unit) in times:
        cur_v = value / conv
        if cur_v >= 1 or not len(cur):
            if prev_u:
                cur_h = math.floor(cur_v)
                cur_l = math.floor((cur_v - cur_h) * conv / prev_c)
                cur = "{0:3.0f}{1} {2:2.0f}{3}".format(cur_h, unit,
                                                       cur_l, prev_u)
            else:
                cur = "{0:7.3f}{1}".format(cur_v, unit)
        else:
            break
        prev_u = unit
        prev_c = conv
    return cur


if hasattr(time, "monotonic"):
    _get_time_ms = lambda: time.monotonic() * 1000.0
else:
    _get_time_ms = lambda: time.clock() * 1000.0
def get_time_ms():
    return _get_time_ms()


max_time_list = 1000
def add_time_point(time_points, count, p):
    if len(time_points) < max_time_list:
        time_points.append(p)
    else:
        pos = random.randrange(count)
        if pos < len(time_points):
            time_points[pos] = p


def compute_eta(time_points, before):
    if len(time_points) < 2:
        return None
    total = 0.0
    number = 0.0
    prev_x = None
    prev_y = None
    # x is fraction of work done
    # y is time elapsed
    for (x, y) in time_points:
        if prev_x is not None:
            total += float(y - prev_y) / float(x - prev_x)
            number += 1
        prev_x = x
        prev_y = y
    return max(float(total) / float(number) - before, 0)

BLOCKS = [
    " ",
    "▏",
    "▎",
    "▍",
    "▌",
    "▋",
    "▊",
    "▉",
    "█", # "\x1b[7m \x1b[0m" would fake a full block for bad terminals but then it's too large :(
]
def compute_bar(br, width):
    if br < 1.0:
        r = br * width
        ri = int(math.floor(r))
        return "{0}{1}{2}".format(
            BLOCKS[-1] * ri,
            BLOCKS[int(math.floor((r - ri) * len(BLOCKS)))],
            BLOCKS[0] * (width - ri - 1))
    return "{0}".format(BLOCKS[-1] * width)

def method_blocks(out, prefix, ix, length, width,
                  elapsed_ms, time_points, count):
    br = float(ix) / float(length)
    if time_points is not None:
        add_time_point(time_points, count, (br, elapsed_ms))
        eta = compute_eta(time_points, elapsed_ms)
    else:
        eta = 0
    if width > 0:
        bar = compute_bar(br, width)
        out.write("{0}|{1}| {2:6.2f}% (T {3} ETA {4})".format(
            prefix, bar,
            br * 100.0,
            convert_time_ms(elapsed_ms), convert_time_ms(eta)))
    else:
        out.write("{0}{1:6.2f}% (T {2} ETA {3})".format(
            prefix, br * 100.0, convert_time_ms(elapsed_ms), convert_time_ms(eta)))
    return count + 1


INDEF = [
    "-",
    "\\",
    "|",
    "/",
]
def method_indef(out, prefix, rot, elapsed_ms):
    if rot < 0:
        out.write("{0}took {1}".format(prefix, convert_time_ms(elapsed_ms)))
    else:
        out.write("{0}{1}".format(prefix, INDEF[rot % len(INDEF)]))


def _get_prefix(prefix, isatty):
    if isatty:
        return "\r{0}: ".format(prefix) if prefix is not None else "\r"
    return "{0}: ".format(prefix) if prefix is not None else ""


class SafePrinter(object):
    def __init__(self, writer):
        self._w = writer
        self._reset = False
        self._cur_width = 0
        self._last_width = 0
        self._system = []
        if writer == sys.stdout:
            self._system.append("out")
            sys.stdout = self
        if writer == sys.stderr:
            self._system.append("err")
            sys.stderr = self
        self._update_configuration()
        self._finished = False

    def _update_configuration(self):
        self.closed = self._w.closed
        self.encoding = self._w.encoding

    def _finish(self):
        if self._finished:
            return
        for s in self._system:
            if s == "out":
                sys.stdout = self._w
            if s == "err":
                sys.stderr = self._w
        self._finished = True
        if self._reset:
            self._w.write("\n")

    def flush(self):
        self._w.flush()

    def isatty(self):
        return self._w.isatty()

    def close(self):
        self._w.close()
        self._update_configuration()

    def writelines(self, lines):
        for l in lines:
            self.write(l)

    def write(self, text):
        if self._finished:
            return self._w.write(text)
        count = 0
        firstLF = True
        for l in text.split("\n"):
            if self._reset:
                count += self._w.write("\r{0}\r".format(" " * max(self._cur_width, self._last_width)))
                self._cur_width = 0
                self._last_width = 0
                self._reset = False
            if not firstLF:
                count += self._w.write("\n")
                self._cur_width = 0
                self._last_width = 0
                self._reset = False
            firstLF = False
            firstCR = True
            for chunk in l.split("\r"):
                if not firstCR:
                    count += self._w.write("\r")
                    self._last_width = max(self._last_width, self._cur_width)
                    self._cur_width = 0
                    self._reset = True
                firstCR = False
                count += self._w.write(chunk)
                self._cur_width += len(chunk)
        self._w.flush()
        return count


class IOWrapper(io.RawIOBase):
    def __init__(self, f, out=sys.stderr, prefix=None,
            method=method_blocks, width=20, delay=100, fallback=method_indef):
        self._f = f
        self._out = SafePrinter(out)
        self._isatty = out.isatty()
        self._prefix = _get_prefix(prefix, self._isatty)
        self._method = method
        self._width = width
        self._delay = delay
        self._start_time = get_time_ms()
        self._last_progress = self._start_time
        self._points = []
        self._count = 0
        self._orig = 0
        if self.seekable():
            self._orig = self.tell()
            self.seek(0, io.SEEK_END)
            self._length = self.tell() - self._orig
            self.seek(self._orig, io.SEEK_SET)
            if self._length > 0:
                self._callmethod(0, self._last_progress)
        else:
            self._method = fallback
            self._length = None
            self._rot = 0
            self._callmethod(self._rot, self._last_progress)

    def _callmethod(self, cur, cur_time):
        do_print = self._isatty
        if self._length is not None:
            if cur >= self._length:
                if self._points is not None:
                    do_print = True
                self._points = None
                cur = self._length
            self._count = self._method(self._out,
                self._prefix, cur, self._length, self._width,
                cur_time - self._start_time, self._points, self._count)
        else:
            if self._rot < 0:
                do_print = True
            self._method(self._out, self._prefix, cur, cur_time - self._start_time)

    def _progress(self):
        cur_progress = get_time_ms()
        if cur_progress - self._last_progress >= self._delay:
            if self._length is not None:
                cur = self.tell() - self._orig
                self._callmethod(cur, cur_progress)
            else:
                self._rot += 1
                self._callmethod(self._rot, cur_progress)
            self._last_progress = cur_progress

    def seek(self, pos, whence=0):
        return self._f.seek(pos, whence)

    def tell(self):
        return self._f.tell()

    def seekable(self):
        return self._f.seekable()

    def readable(self):
        return self._f.readable()

    def fileno(self):
        return self._f.fileno()

    def isatty(self):
        return self._f.isatty()

    def flush(self):
        self._f.flush()

    def close(self):
        if not self._out._finished:
            self._last_progress = get_time_ms()
            if self._length is not None:
                self._callmethod(self._length, self._last_progress)
            else:
                self._rot = -1
                self._callmethod(self._rot, self._last_progress)
        self._out._finish()
        self._f.close()

    @property
    def closed(self):
        return self._f.closed

    @property
    def __closed(self):
        return self._f.closed

    def readline(self, size=-1):
        res = self._f.readline(size)
        self._progress()
        return res

    def read(self, size=-1):
        res = self._f.read(size)
        self._progress()
        return res

    def readall(self):
        res = self._f.readall()
        self._progress()
        return res

    def readinto(self, b):
        res = self._f.readinto(b)
        self._progress()
        return res


def progress_wrap(f, out=sys.stderr, prefix=None,
            method=method_blocks, width=20, delay=100, fallback=method_indef):
    return IOWrapper(f, out, prefix, method, width, delay, fallback)


def progress(from_ix, to_ix, job, out=sys.stderr, prefix=None,
             method=method_blocks, width=20, delay=100):
    out = SafePrinter(out)
    isatty = out.isatty()
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = _get_prefix(prefix, isatty)
    length = to_ix - from_ix
    if length == 0:
        return
    cur_ix = 0
    try:
        if isatty:
            count = method(out, prefix, cur_ix, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for ix in range(from_ix, to_ix):
            cur_ix = ix
            if isatty and cur_progress - last_progress >= delay:
                count = method(out, prefix, cur_ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            job(ix, length)
            cur_progress = get_time_ms()
        cur_ix = length
    finally:
        count = method(out, prefix, cur_ix, length, width,
                       cur_progress - start_time, None, count)
        out._finish()


def progress_list(iterator, job, out=sys.stderr, prefix=None,
                  method=method_blocks, width=20, delay=100):
    out = SafePrinter(out)
    isatty = out.isatty()
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = _get_prefix(prefix, isatty)
    length = len(iterator)
    if length == 0:
        return
    cur_ix = 0
    try:
        if isatty:
            count = method(out, prefix, cur_ix, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for (ix, elem) in enumerate(iterator):
            cur_ix = ix
            if isatty and cur_progress - last_progress >= delay:
                count = method(out, prefix, cur_ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            job(elem)
            cur_progress = get_time_ms()
        cur_ix = length
    finally:
        count = method(out, prefix, cur_ix, length, width,
                       cur_progress - start_time, None, count)
        out._finish()


def progress_map(iterator, job, out=sys.stderr, prefix=None,
                 method=method_blocks, width=20, delay=100):
    out = SafePrinter(out)
    isatty = out.isatty()
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = _get_prefix(prefix, isatty)
    length = len(iterator)
    res = []
    if length == 0:
        return res
    cur_ix = 0
    try:
        if isatty:
            count = method(out, prefix, cur_ix, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for (ix, elem) in enumerate(iterator):
            cur_ix = ix
            if isatty and cur_progress - last_progress >= delay:
                count = method(out, prefix, cur_ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            res.append(job(elem))
            cur_progress = get_time_ms()
        cur_ix = length
    finally:
        count = method(out, prefix, cur_ix, length, width,
                       cur_progress - start_time, None, count)
        out._finish()
    return res


def progress_indef(iterator, job, out=sys.stderr, prefix=None,
                   method=method_indef, delay=100):
    out = SafePrinter(out)
    isatty = out.isatty()
    start_time = get_time_ms()
    last_progress = start_time
    cur_progress = last_progress
    prefix = _get_prefix(prefix, isatty)
    rot = 0
    try:
        if isatty:
            method(out, prefix, rot, cur_progress - start_time)
        for elem in iterator:
            cur_progress = get_time_ms()
            if isatty and cur_progress - last_progress >= delay:
                rot += 1
                method(out, prefix, rot, cur_progress - start_time)
                last_progress = cur_progress
            job(elem)
        rot = -1
    finally:
        method(out, prefix, rot, cur_progress - start_time)
        out._finish()


def histogram(items, width=50, out=sys.stderr):
    max_value = None
    max_len = 0
    for (prefix, v) in items:
        prefix = "{0}".format(prefix)
        max_len = max(len(prefix), max_len)
        if max_value is None:
            max_value = v
        else:
            max_value = max(max_value, v)
    if max_value is None:
        return
    for (prefix, v) in items:
        prefix = "{0}".format(prefix)
        padding = " " * (max_len - len(prefix))
        out.write("{0}{1} |{2}| {3}\n".format(padding, prefix,
            compute_bar(float(v) / float(max_value), width), v))
