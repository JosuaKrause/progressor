# progress_bar
A visually appealing progress bar for long lasting computations.
It also computes the remaining estimated time for the task by ad-hoc learning
of the completion so far. For this reason `scikit-learn` and `numpy` are
required.

You can install *progress_bar* via
```bash
pip install --user git+https://github.com/JosuaKrause/progress_bar.git
```

and import it in python using:
```python
import progress_bar
```

Compute a task as follows:
```python
from __future__ import print_function
import time

res = [ 0 ]

def task(elem):
    time.sleep(0.01)
    res[0] += elem

progress_bar.progress_list(range(1000), task, prefix="sleep list")
print(res[0])
```
or in a range:
```python
def task_range(cur_ix, length):
    task(cur_ix)

progress_bar.progress(0, 1000, task_range, prefix="sleep range")
print(res[0])
```

The output looks roughly like this:
```
sleep list: |████████████▌       |  62.30% (T   7.492s ETA   6.791s)
```

If no estimate of the progress towards completion can be made use:
```python
def repeat(num):
    while True:
        yield num

progress_bar.progress_indef(repeat(1), task, prefix="sleep indefinitely")
```

which produces output like this:
```
sleep indefinitely: /
```
