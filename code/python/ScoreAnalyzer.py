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
        # Figure out all switched indices where the value of each index is different from the next value
        # i.e. find all i where arr[i] != arr[i+1]
        switch_pts = [i for i, x in enumerate(map(lambda x, y: x != y, array_data[:-1], array_data[1:])) if x]

        # Insert values such that the difference of switched indices is equal to run-length sequence
        switch_pts.insert(0, -1)
        switch_pts.append(len(array_data)-1)

        # Get run-length sequence
        run_length_sequence = np.diff(switch_pts)

        # Find out the corresponded set of each run-length
        sequence_id = (np.arange(len(run_length_sequence)) + array_data[0]) % 2

        # Each element consists of two values: (SET, RUN_LENGTH)
        return zip(sequence_id, run_length_sequence)
    else:
        return None

def _run_length_distribution(data):
    # Aggregate RLC pairs
    hist = Counter(data)

    # Wrap unique elements and its corresponded count
    # ((SET_ID, RUN_LENGTH), COUNT)
    hist = zip(hist.keys(), hist.values())

    # Splitting by sets (0/1)
    # hist[0/1]: array of (RUN_LENGTH, COUNT) of the set 0/1
    hist = map(lambda v: filter(lambda x: x[0][0] == v, hist), [0, 1])
    hist = map(lambda v: map(lambda x: (x[0][1], x[1]), hist[v]), [0, 1])

    # Sort by count in descending order
    hist = map(lambda v: sorted(hist[v], key=lambda x: x[1], reverse=True), [0, 1])

    return hist

def _find_staffline_centers(col, width, space):
    # Check for existence of staffline
    # Simplest rule: the length must be greater than 9 (for 5 lines and 4 spaces)
    if len(col) < 9: return []

    col = np.array(col, dtype=int)
    acc_offset = np.zeros(col.shape, dtype=int)
    for x in range(1, len(acc_offset)):
        acc_offset[x] = acc_offset[x-1] + col[x-1]

    # Generatetesting frames
    #                               center
    #                                 |
    #                                 v
    # [ width, space, width, space, width, space, width, space, width ]
    # [ rl[0], rl[1], rl[2], rl[3], rl[4], rl[5], rl[6], rl[7], rl[8] ]
    # [ rl[1], rl[2], rl[3], rl[4], rl[5], rl[6], rl[7], rl[8], rl[9] ]
    # ...
    candidates = [
        col[0:-8],
        col[1:-7],
        col[2:-6],
        col[3:-5],
        col[4:-4],
        col[5:-3],
        col[6:-2],
        col[7:-1],
        col[8:]
    ]
    candidates = np.array(candidates).transpose()

    # Select the indices of possible stafflines centers
    results = map(_is_staffline, candidates, [width]*len(candidates), [space]*len(candidates))
    center_idx = np.array([i for i, x in enumerate(results) if x], dtype=int) + 4

    return acc_offset[center_idx] + width/2

def _is_staffline(arr=np.array([]), width=0, space=0, err_thresh=1.):
    if len(arr) == 9:
        height = 5*width + 4*space
        if abs(arr[0] - width) / float(width) > err_thresh: return False
        perfect_staffline = np.array([width, space, width, space, width, space, width, space, width], dtype=float)
        diff = abs(np.array(arr) - perfect_staffline)
        diff_rat = np.divide(diff, perfect_staffline)

        return reduce(lambda x, y: x and y, diff_rat < err_thresh)
    else:
        return None

def staffline_info(data):
    # RLC at each column
    rl_per_col = map(_run_length_coding, data.transpose())

    # Compute the distribution of run-lengths
    hist = _run_length_distribution(reduce(lambda x, y: x+y, rl_per_col))

    # Staffline info
    # hist[v]: array of unique sets which contains a tuple and an integer
    #   0 -> for inactive run-length
    #   1 -> for active run-length
    #
    # hist[v][0]: the set which contains the largest count (RUN_LENGTH, COUNT)
    staffline_width = hist[1][0][0]
    staffline_space = hist[0][0][0]

    # Staffline centers
    rl_per_col = map(lambda x: np.array(x)[:, 1], rl_per_col)
    staffline_centers = map(_find_staffline_centers, rl_per_col,
                            [staffline_width]*len(rl_per_col), [staffline_space]*len(rl_per_col))

    return {"width": staffline_width, "space": staffline_space, "centers": staffline_centers}
