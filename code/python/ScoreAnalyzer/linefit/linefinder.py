import numpy as np

def get_pts_set(centers):
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

def find_lines_by_RANSAC(data_pts, Niter=1000, in_thresh=.5):
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

        samples += [[a, b, len(idces), line_range]]

    return np.array(samples)

def find_lines_by_centers_RANSAC(centers, min_margin=0.5, max_iter=10, ang_thresh=0.01, NRANSAC=200):
    # Find lines by Randomly Sampled Consensus
    #
    # Returns:
    #     a d-by-2 matrix where each row refers to a line with the format [slope, intercept]

    # Initialization
    iter_count = 0
    NRANSAC = int(NRANSAC)
    pts = get_pts_set(centers)

    results = []

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
        lines = find_lines_by_RANSAC(pts, Niter=NRANSAC)
        lines = sorted(lines, key=lambda x: x[2], reverse=True)

        lines = lines[:NRANSAC/10]

        if len(lines) > 0:
            # If there is no staffline has been detected yet, choose the first element of RANSAC results
            # otherwise choose the first element of detected results
            if len(results) > 0: a, _ = results[0]
            else: a, _, _, _ = lines[0]


            # Note:
            # tan(t1 - t2) = (tan(t1) - tan(t2)) / (1 + tan(t1)tan(t2))
            # |t1 - t2| = |(r1 - r2) / (1 + r1r2)| at small |t1 - t2|
            # 1 degree = 0.017 rad
            lines = filter(lambda line: abs((line[0] - a) / (1 + line[0]*a)) < ang_thresh, lines)

            for line in lines:
                a, b, _, _ = line

                intercepts = np.array(map(lambda x: x[1], results))

                # Note:
                # to check if there is any overlapped region of some pair of lines
                if sum(np.abs(intercepts - b) < min_margin) == 0:
                    dist = np.abs(pts.dot(np.array([a, -1])) + b)
                    results += [[a, b]]
                    pts = pts[dist > min_margin, :]

        else:
            break


    return results