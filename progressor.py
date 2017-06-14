#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import sys
import time
import math
import random

import numpy as np
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures

__version__ = "0.1.3"


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


def get_time_ms():
    return time.clock() * 1000.0


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
    if len(time_points) < 3:
        x1, y1 = time_points[0]
        x2, y2 = time_points[1]
        if x2 == x1:
            return None
        return float(y2 * (1.0 - x1) - y1 * (1.0 - x2)) / float(x2 - x1)
    x, y = zip(*time_points)
    poly = PolynomialFeatures(degree=8)
    x = poly.fit_transform(np.sqrt(x).reshape((len(x), 1)))
    clf = linear_model.Ridge(alpha=0.5)
    clf.fit(x, y)
    return max(0, clf.predict(poly.transform(np.array([[1.0]])))[0] - before)


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
        out.write("\r{0}|{1}| {2:6.2f}% (T {3} ETA {4})".format(
            prefix, bar,
            br * 100.0,
            convert_time_ms(elapsed_ms), convert_time_ms(eta)))
    else:
        out.write("\r{0}{1:6.2f}% (T {2} ETA {3})".format(
            prefix, br * 100.0, convert_time_ms(elapsed_ms), convert_time_ms(eta)))
    return count + 1


def progress(from_ix, to_ix, job, out=sys.stderr, prefix=None,
             method=method_blocks, width=20, delay=100):
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = str(prefix) + ": " if prefix is not None else ""
    length = to_ix - from_ix
    if length == 0:
        return
    try:
        count = method(out, prefix, 0, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for ix in range(from_ix, to_ix):
            if cur_progress - last_progress >= delay:
                count = method(out, prefix, ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            job(ix, length)
            cur_progress = get_time_ms()
        count = method(out, prefix, length, length, width,
                       cur_progress - start_time, None, count)
    finally:
        out.write("\n")


def progress_list(iterator, job, out=sys.stderr, prefix=None,
                  method=method_blocks, width=20, delay=100):
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = str(prefix) + ": " if prefix is not None else ""
    length = len(iterator)
    if length == 0:
        return
    try:
        count = method(out, prefix, 0, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for (ix, elem) in enumerate(iterator):
            if cur_progress - last_progress >= delay:
                count = method(out, prefix, ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            job(elem)
            cur_progress = get_time_ms()
        count = method(out, prefix, length, length, width,
                       cur_progress - start_time, None, count)
    finally:
        out.write("\n")


def progress_map(iterator, job, out=sys.stderr, prefix=None,
                 method=method_blocks, width=20, delay=100):
    start_time = get_time_ms()
    last_progress = start_time
    points = []
    count = 0
    prefix = str(prefix) + ": " if prefix is not None else ""
    length = len(iterator)
    res = []
    if length == 0:
        return res
    try:
        count = method(out, prefix, 0, length, width, 0, points, count)
        cur_progress = get_time_ms()
        for (ix, elem) in enumerate(iterator):
            if cur_progress - last_progress >= delay:
                count = method(out, prefix, ix, length, width,
                               cur_progress - start_time, points, count)
                last_progress = cur_progress
            res.append(job(elem))
            cur_progress = get_time_ms()
        count = method(out, prefix, length, length, width,
                       cur_progress - start_time, None, count)
    finally:
        out.write("\n")
    return res


INDEF = [
    "-",
    "\\",
    "|",
    "/",
]
def method_indef(out, prefix, rot):
    out.write("\r{0}{1}".format(prefix, INDEF[rot % len(INDEF)]))


def progress_indef(iterator, job, out=sys.stderr, prefix=None,
                   method=method_indef, delay=100):
    last_progress = get_time_ms()
    prefix = str(prefix) + ": " if prefix is not None else ""
    rot = 0
    try:
        method(out, prefix, rot)
        for elem in iterator:
            cur_progress = get_time_ms()
            if cur_progress - last_progress >= delay:
                rot += 1
                method(out, prefix, rot)
                last_progress = cur_progress
            job(elem)
    finally:
        out.write("\n")


def histogram(items, width=50, out=sys.stderr):
    max_value = None
    for (_, v) in items:
        if max_value is None:
            max_value = v
        else:
            max_value = max(max_value, v)
    if max_value is None:
        return
    for (prefix, v) in items:
        out.write("{0} |{1}| {2}\n".format(prefix, compute_bar(float(v) / float(max_value), width), v))
