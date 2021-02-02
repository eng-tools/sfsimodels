import numpy as np


def remove_close_items(y, tol, del_prev=True):
    diffs = np.diff(y)
    pairs = []
    inds = np.where(diffs < tol)
    while len(inds[0]):  # progressively delete coordinate below until tolerance is reached
        pairs.append((y[inds[0][0]], y[inds[0][0] + 1]))
        if del_prev:
            y = np.delete(y, inds[0][0])
        else:
            y = np.delete(y, inds[0][0] + 1)

        diffs = np.diff(y)
        inds = np.where(diffs < tol)
    return y, pairs
