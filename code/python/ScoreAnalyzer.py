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

def _is_staffline(arr=np.array([]), width=0, space=0, err_thresh=.9):
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

def _get_pts_set(centers):
    # centers is an array where each element is an array of y indices which indicates possible staffline centers
    # e.g.
    # [
    #     [ c[1][1], c[1][2], c[1][3] ],
    #     [ c[2][1], c[2][2], c[2][3], c[2][4], c[2][5] ],
    #                             .
    #                             .
    #                             .
    #     [ c[k][1], ... , c[k][N_k] ],
    #                             .
    #                             .
    #                             .
    #     [ c[X][1], ... , c[X][N_X] ]
    # ]
    #
    # Returns:
    #     an array where each element is a 2-D points indicates the position of a possible staffline center

    pts = []
    for i, center in enumerate(centers):
        pts += map(lambda c: [i, c], center)

    return np.array(pts)

def _find_lines_by_RANSAC(data_pts, Niter=1000, in_thresh=.5):
    # Find lines by Randomly Sampled Consensus (private subfunction)
    #
    # Returns:
    #     a Niter-by-4 matrix where each row refers to a line candidate
    #     and each row contains [slope, intercept, inset_cnt, x_range]

    # Initialization
    data_pts = np.array(data_pts)
    samples = []
    xlist = np.unique(data_pts[:, 0])

    # The number of unique x's must be at least 2
    if len(xlist) < 2:
        return np.array([])

    # Separate data into a couple of segmentations which are clustered by its x-index
    centers = map(lambda x: np.array(filter(lambda pt: pt[0] == x, data_pts))[:, 1], xlist)

    # Repeat the operation Niter times:
    # 1. randomly select two points with different x-indices
    # 2. compute slope and intercept with chosen points (difference between different x's must be safe to be a divisor)
    # 3. compute vertical distance of all points from the selected line
    # 4. compute the number of in-set and its corresponding x-range
    # 5. append to output array with row [slope, intercept, in-set size, x-range]
    for _ in range(Niter):
        rs_idces = np.random.choice(range(len(xlist)), 2, replace=False)
        rs_x = xlist[rs_idces]
        rs_y = np.array(map(lambda v: np.random.choice(centers[rs_idces[v]], 1)[0], [0, 1]))

        a = 1. * np.diff(rs_y)[0] / np.diff(rs_x)[0]
        b = np.mean(rs_y - rs_x * a)

        dist = abs( data_pts.dot(np.array([a, -1])) + b )
        idces = [i for i, d in enumerate(dist) if d < in_thresh]
        line_range = data_pts[idces[-1], 0] - data_pts[idces[0], 0]

        samples += [[a, b, len(filter(lambda x: x < .5, dist)), line_range]]

    return np.array(samples)

def find_lines_RANSAC(centers, img_width, staffline_height, max_iter=10, ang_thresh=0.01, NRANSAC=200):
    # Find lines by Randomly Sampled Consensus
    #
    # Returns:
    #     a d-by-2 matrix where each row refers to a line with the format [slope, intercept]

    # Initialization
    iter_count = 0
    NRANSAC = int(NRANSAC)
    pts = _get_pts_set(centers)

    stafflines = []

    # Avoid unstable time consumption, the loop cannot be executed infinitely
    # Repeat the operation at most max_iter times:
    # 1. get RANSAC results and sort by in-set size
    # 2. select first 10% data (prevent from processing bad models)
    # 3. select results where x-range is greater than half of image width
    # 4. filter duplicated lines (with difference between intercepts) and unparallel lines (with a threshold angle)
    # 5. append to output array and eliminate unneeded points, which are located inside the staffline
    # 6. terminate if there is no result to process
    while iter_count < max_iter:
        iter_count += 1
        lines = _find_lines_by_RANSAC(pts, Niter=NRANSAC)
        lines = sorted(lines, key=lambda x: x[2], reverse=True)

        lines = lines[:NRANSAC/10]
        lines = filter(lambda line: line[3] > img_width * .3, lines)

        if len(lines) > 0:
            # If there is no staffline has been detected yet, choose the first element of RANSAC results
            # otherwise choose the first element of detected stafflines
            if len(stafflines) > 0: a, _ = stafflines[0]
            else: a, _, _, _ = lines[0]


            # Note:
            # tan(t1 - t2) = (tan(t1) - tan(t2)) / (1 + tan(t1)tan(t2))
            # |t1 - t2| = |(r1 - r2) / (1 + r1r2)| at small |t1 - t2|
            # 1 degree = 0.017 rad
            lines = filter(lambda line: abs((line[0] - a) / (1 + line[0]*a)) < ang_thresh, lines)

            for line in lines:
                a, b, _, _ = line

                intercepts = np.array(map(lambda x: x[1], stafflines))

                # Note:
                # to check if there is any overlapped region of some pair of lines
                if sum(np.abs(intercepts - b) < staffline_height*1.5) == 0:
                    dist = np.abs(pts.dot(np.array([a, -1])) + b)
                    stafflines += [[a, b]]
                    pts = pts[dist > staffline_height*1.5, :]

        else:
            break


    return stafflines

