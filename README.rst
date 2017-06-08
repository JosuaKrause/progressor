progressor
=============

A visually appealing progress bar for long lasting computations. It also
computes the remaining estimated time for the task by ad-hoc learning of
the completion so far. For this reason ``scikit-learn`` and ``numpy``
are required.

You can install *progressor* via

.. code:: bash

    pip install progressor

and import it in python using:

.. code:: python

    import progressor

Compute a task as follows:

.. code:: python

    from __future__ import print_function
    import time

    res = [ 0 ]

    def task(elem):
        time.sleep(0.01)
        res[0] += elem

    progressor.progress_list(range(1000), task, prefix="sleep list")
    print(res[0])

or in a range:

.. code:: python

    def task_range(cur_ix, length):
        task(cur_ix)

    progressor.progress(0, 1000, task_range, prefix="sleep range")
    print(res[0])

The output looks roughly like this:

::

    sleep list: |████████████▌       |  62.30% (T   7.492s ETA   6.791s)

If no estimate of the progress towards completion can be made use:

.. code:: python

    def repeat(num):
        while True:
            yield num

    progressor.progress_indef(repeat(1), task, prefix="sleep indefinitely")

which produces output like this:

::

    sleep indefinitely: /
