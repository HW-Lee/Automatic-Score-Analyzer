import numpy as np
from ScoreAnalyzer.runlength.rlcodec import run_length_coding

def has_staffline(deskewed_data=np.array([]), staffline_width=0, staffline_space=0, length_thresh=.5):
    # To check if there is a staffline within the given image
    #
    # Returns:
    #     True/False

    # Check if the condition is satisfied:
    #   The mean of the first five highest projection onto y-axis is greater than a theshold
    if sum(deskewed_data.shape) > 0:
        deskewed_data = np.array(deskewed_data)
        height = 5*staffline_width + 4*staffline_space
        half_h = deskewed_data.shape[0]/2

        # only search central region
        if height < half_h:
            deskewed_data = deskewed_data[half_h-height:half_h+height, :]

        y_proj = np.sum(deskewed_data, axis=1)
        y_proj = -np.sort(-y_proj)

        return np.mean(y_proj[0:5]) > length_thresh*deskewed_data.shape[1]
    else:
        return False

def _filter_staffline_per_col(col, staffline_width):
    # Eliminate pixels which possibly are part of a staffline at a given column data
    # Note that the size of the input data is very small such that only one line is contained in the data
    #
    # Returns:
    #     an array where all possible stafflines are eliminated

    # The way checking if there is a line contained in the data:
    #   to check if there is any pattern like [0, 0, 0, ... , 0, 1, 1, 1, 1, 1, 0, 0, ... , 0]
    #   such that the number of consecutive 1's is in the range we defined

    # Clone the original data
    col = np.array(col)

    # Compute its run-length stream
    rl = run_length_coding(col)
    offset = 0

    # Remove the parts which do not belong to the pattern
    while len(rl) > 0 and rl[0][0] == 1:
        offset += rl[0][1]
        del rl[0]

    while len(rl) > 0 and rl[-1][0] == 1:
        del rl[-1]

    # Check if it is valid:
    #   1. the pattern is 3-length in run-length representation
    #   2. the leading symbol is 0
    #   3. the number of consecutive 1's is in the range of [1, 2*staffline_width-1]
    # The pattern is 3-length in run-length representation and the leading symbol is 0
    if len(rl) == 3 and rl[0][0] == 0 and abs(rl[1][1] - staffline_width) < staffline_width:
        col[offset+rl[0][1]:offset+rl[0][1]+rl[1][1]] = 0

    return col

def _filter_staffline_per_line(data, staffline_width):
    # Eliminate pixels which possibly compose a line at a given column data
    # Note that the size of the input data is very small such that only one line is contained in the data
    #
    # Returns:
    #     processed data

    # Clone the original data
    data = np.array(data)

    # Process the data columnwisely
    width_repeat = [staffline_width] * data.shape[1]
    data = map(_filter_staffline_per_col, data.transpose(), width_repeat)
    data = np.array(data).transpose()

    return data

def extract_staffline(deskewed_data=np.array([]), staffline_width=0, staffline_space=0):
    # Separate an image of score into staffline-removed part and residual part
    #
    # Returns:
    #     filterred, residual, y_idces
    #       - filterred : the image after stafflines removal
    #       - residual  : the difference between original data and filterred data
    #       - y_idces   : the positions where stafflines are located

    # To check if the input is not empty
    if sum(deskewed_data.shape) > 0:
        # Clone the original data
        deskewed_data = np.array(deskewed_data)

        # Compute the height of a staffline
        height = 5*staffline_width + 4*staffline_space

        # Find vertical center value
        half_h = deskewed_data.shape[0]/2

        # Find positions where stafflines are located
        # 1. Initial guess of staffline positions based on staffline width and space
        # 2. Adjust positions such that the positions are indicated accurately
        #

        # Initialization
        margin = int(round((staffline_width + staffline_space) / 2.))

        # Initial guess
        y_idces = np.array([-2, -1, 0, 1, 2]) * (staffline_width+staffline_space) + half_h

        # Segment lines to adjust positions
        horizlines = map(lambda y: np.array(deskewed_data[y-margin:y+margin, :]), y_idces)

        # Compute y-projection respectively
        y_projs = map(lambda line: np.sum(line, axis=1).flatten(), horizlines)

        # Find adjustment value respectively
        y_adjs = map(lambda proj: round(np.argsort(-proj)[0]), y_projs)
        y_adjs = np.array(y_adjs) - margin
        y_idces += y_adjs

        # Resegment lines to eliminate
        horizlines = map(lambda y: np.array(deskewed_data[y-margin:y+margin, :]), y_idces)

        # Filter each line segment
        width_repeat = [staffline_width] * 5
        horizlines_filterred = map(_filter_staffline_per_line, horizlines, width_repeat)

        # Initialize 
        filterred = np.array(deskewed_data)

        # Overwrite the original data with processed segments
        for x in range(5):
            y = y_idces[x]
            filterred[y-margin:y+margin, :] *= horizlines_filterred[x]

        # Do subtraction to obtain residual
        residual = np.array(deskewed_data) - filterred

        return (filterred, residual, y_idces)
    else:
        return (np.array([]), np.array([]), np.array([]))