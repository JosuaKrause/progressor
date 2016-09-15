# -*- coding: utf-8 -*-
"""
Created on 2016-09-14

@author: joschi <josua.krause@gmail.com>

A visually appealing progress bar for long lasting computations.
"""
from setuptools import setup

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='progress_bar',
    version='0.1.0',
    description='A visually appealing progress bar for long lasting '
                'computations.',
    long_description=long_description,
    url='https://github.com/JosuaKrause/progress_bar',
    author='Josua Krause',
    author_email='josua.krause@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='visual progress bar time estimation',
    py_modules=['progress_bar'],
    install_requires=[
        'numpy',
        'scikit-learn',
    ],
)
