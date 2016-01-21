import numpy as np
from ScoreAnalyzer.runlength.rlcodec import run_length_coding, run_length_distribution

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

def _is_staffline(arr=np.array([]), width=0, space=0, err_thresh=.7):
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
    rl_per_col = map(run_length_coding, data.transpose())

    # Compute the distribution of run-lengths
    hist = run_length_distribution(reduce(lambda x, y: x+y, rl_per_col))

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
