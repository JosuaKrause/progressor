# progress_bar
A visually appealing progress bar for long lasting computations.
It also computes the remaining estimated time for the task by ad-hoc learning
of the completion so far. For this reason `scikit-learn` and `numpy` are
required.

Compute a task as follows:
```python
from __future__ import print_function
import time

def task(elem):
    print("sleep: " + str(elem))
    time.sleep(elem)
    print("done")

progress_bar.progress_list([ 1, 3, 2 ], task, prefix="sleep list")
```
or in a range:
```python
progress_bar.progress(0, 5, task, prefix="sleep range")
```

If no estimate of the progress towards completion can be made use:
```python
def repeat(num):
    while True:
        yield num

progress_bar.progress_indef(repeat(1), task, prefix="sleep indefinitely")
```

You can install *progress_bar* via
```bash
pip install --user git+https://github.com/JosuaKrause/progress_bar.git
```

and import it in python using:
```python
import progress_bar
```
