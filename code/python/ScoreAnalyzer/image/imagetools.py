import numpy as np
from scipy import misc

def load(path, thresh=.5, reverse=True):
    # Load an image with binarization
    # reverse:
    #   - T, blackset refers to active set
    #   - F, whiteset refers to active set

    image = misc.imread(name=path, flatten=True)
    if reverse: image = abs(image - 255.)
    return binarize_image(raw_image=image, thresh=thresh, dtype=float)

def binarize(v=0, thresh=.5, max_value=255.):
    return v > max_value*thresh

def binarize_image(raw_image=np.array([]), thresh=.5, max_value=255., dtype=float):
    if sum(raw_image.shape) > 0:
        bin_image = map(lambda row: binarize(row, thresh=thresh, max_value=max_value), raw_image)
        bin_image = np.array(bin_image, dtype=dtype)

        return bin_image
    else:
        return np.array([])

def segment_by_line(data, line_params, margin, bin_thresh=None, derotate=True, interp="bilinear"):
    # Segment a sub-matrix from a matrix with a specific line equation and margin
    # 1. find the y-value of the line corresponded to horizontally center point
    # 2. segment the data with two horizontal lines where the y-values are y += margin, respectively
    # 3. rotate the data such that the cut line is horizontally flat

    # Get the line parameters
    #     a: slope
    #     b: intercept
    a, b = line_params

    # Compute the corresponding y-value at the cut line
    min_y, max_y = np.sort([ b, int(round(a*(data.shape[1]-1) + b)) ])
    min_y = np.max([min_y-margin, 0])
    max_y = np.min([max_y+margin, data.shape[0]-1])

    # Compute the angle between cut line and x-axis
    theta = np.arctan(a)

    # Segment the data and rotate with the angle
    # Note that:
    #     the y-axis goes downward in images manner, rotating images counter-clockwisely
    #     is equivallent to rotating matrices clockwisely. Therefore, the ratation angle must not
    #     be added by negative sign.
    data_seg = data[min_y:max_y, :]
    if derotate:
        data_seg = misc.imrotate(data_seg, theta/np.pi * 180., interp=interp)

        # Segment the data again
        half_h = int(np.floor(data_seg.shape[0] / 2.))
        data_seg = data_seg[half_h-margin : half_h+margin, :]

        # After interpolation step, the image should be binarized again with a specific threshold
        if bin_thresh != None: data_seg = binarize_image(data_seg, thresh=bin_thresh, max_value=np.max(data_seg.flatten()))

    return data_seg

def segment_data(data, lines_params, margin, bin_thresh=None, derotate=True, interp="bilinear"):
    # Segment the image into a couple of sub-images where each image only contains one de-skewed staffline
    #
    # Returns:
    #     an array where each element is an image that contains only one staffline

    # Convert to matrix such that the var elements can be accessed like a matrix
    data = np.array(data)
    lines_params = np.array(lines_params)

    # Getting parameters
    margin = int(round(margin))
    Nstafflines = len(lines_params)

    # Generating parameters to sub-function
    data_repeat = [data] * Nstafflines
    margin_repeat = [margin] * Nstafflines
    bin_thresh_repeat = [bin_thresh] * Nstafflines
    derotate_repeat = [derotate] * Nstafflines
    interp_repeat = [interp] * Nstafflines

    # Do segment operations with each line parameters
    segments = map(segment_by_line, data_repeat, lines_params, margin_repeat, bin_thresh_repeat, derotate_repeat, interp_repeat)

    return segments
