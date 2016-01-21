import numpy as np
from scipy import misc

def load(path, thresh=.5):
    image = misc.imread(name=path, flatten=True)
    image_rev = abs(image - 255.)
    return binarize_image(raw_image=image_rev, thresh=thresh, dtype=float)

def binarize(v=0, thresh=.5):
    return v > 255.0*thresh

def binarize_image(raw_image=np.array([]), thresh=.5, dtype=float):
    if sum(raw_image.shape) > 0:
        bin_image = map(binarize, raw_image, thresh*np.ones(raw_image.shape))
        bin_image = np.array(bin_image, dtype=dtype)

        return bin_image
    else:
        return None

def segment_by_line(data, line_params, margin, bin_thresh=.5):
    # Segment a sub-matrix from a matrix with a specific line equation and margin
    # 1. find the y-value of the line corresponded to horizontally center point
    # 2. segment the data with two horizontal lines where the y-values are y += margin, respectively
    # 3. rotate the data such that the cut line is horizontally flat

    # Get the line parameters
    #     a: slope
    #     b: intercept
    a, b = line_params

    # Find the horizontally center x-value
    half_w = int(np.floor(data.shape[1] / 2.))

    # Compute the corresponding y-value at the cut line
    seg_y = int(round(a*half_w + b))

    # Compute the angle between cut line and x-axis
    theta = np.arctan(a)

    # Segment the data and rotate with the angle
    # Note that:
    #     the y-axis goes downward in images manner, rotating images counter-clockwisely
    #     is equivallent to rotating matrices clockwisely. Therefore, the ratation angle must not
    #     be added by negative sign.
    data_seg = misc.imrotate(data[seg_y-margin : seg_y+margin, :], theta/np.pi * 180., interp="bilinear")

    # After interpolation step, the image should be binarized again with a specific threshold
    data_seg = binarize_image(data_seg, thresh=bin_thresh)

    return data_seg

def segment_data(data, lines_params, margin, bin_thresh=.5):
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

    # Do segment operations with each line parameters
    segments = map(segment_by_line, data_repeat, lines_params, margin_repeat, bin_thresh_repeat)

    return segments
