import sys
import os
import numpy as np
from scipy import misc
from collections import Counter

def load(path, thresh=.5):
    image = misc.imread(name=path, flatten=True)
    image_rev = abs(image - 255.)
    return _binarize_image(raw_image=image_rev, thresh=thresh, dtype=float)

def _binarize(v=0, thresh=.5):
    return v > 255.0*thresh

def _binarize_image(raw_image=np.array([]), thresh=.5, dtype=float):
    if sum(raw_image.shape) > 0:
        bin_image = map(_binarize, raw_image, thresh*np.ones(raw_image.shape))
        bin_image = np.array(bin_image, dtype=dtype)

        return bin_image
    else:
        return None

def _run_length_coding(array_data=np.array([])):
    if sum(array_data.shape) > 0:
        switch_pts = [i for i, x in enumerate(map(lambda x, y: x != y, array_data[:-1], array_data[1:])) if x]
        switch_pts.insert(0, -1)
        switch_pts.append(len(array_data)-1)

        run_length_sequence = np.diff(switch_pts)
        sequence_id = (np.arange(len(run_length_sequence)) + array_data[0]) % 2

        return zip(sequence_id, run_length_sequence)
    else:
        return None

def staffline_info(data):
    # RLC at each column
    rl_per_col = map(_run_length_coding, data.transpose())

    # Concatenating all pairs at every column
    hist = reduce(lambda x, y: x + y, rl_per_col)

    # Aggregate RLC pairs
    hist = Counter(hist)

    # Transform to key-value pairs
    hist = zip(hist.keys(), hist.values())

    # Splitting by RLC IDs
    hist = map(lambda v: filter(lambda x: x[0][0] == v, hist), [0, 1])

    # Sorting by count
    hist = map(lambda v: sorted(hist[v], key=lambda x: x[1], reverse=True), [0, 1])

    # Staffline info
    # hist[v]: array of unique sets which contains a tuple and an integer
    #   0 -> for inactive run-length
    #   1 -> for active run-length
    #
    # hist[v][0]: the set which contains the largest count
    # hist[v][0][0]: the RLC pair of the set
    # hist[v][0][0][1]: the RL-value of the RLC pair
    staffline_width = hist[1][0][0][1]
    staffline_space = hist[0][0][0][1]

    return {"width": staffline_width, "space": staffline_space}
