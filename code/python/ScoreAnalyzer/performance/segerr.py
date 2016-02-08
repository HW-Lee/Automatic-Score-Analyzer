import numpy as np
from ScoreAnalyzer.runlength.rlcodec import run_length_coding

#---------------------------------------------#
#             Deprecated function             #
#            because it is too slow           #
#---------------------------------------------#
def segment_by_diffusion(avail_set, periph_que, prop_set=[]):
    if len(periph_que) == 0: return np.array(prop_set), avail_set
    
    avail_set = np.array(avail_set)
    buff = []
    dirs = np.array([[-1, 0], [0, -1], [1, 0], [0, 1]])
    
    for ppt in periph_que:
        p = np.array(ppt)
        new_pts = np.matlib.repmat(p, 4, 1) + dirs
        
        avail_set_found = map(lambda pt: [i for i, x in enumerate(avail_set) if sum(np.abs(x - pt)) == 0], new_pts)
        is_valid = np.array(map(lambda found: len(found) > 0, avail_set_found))
        
        avail_set_found = map(lambda x: x[0], filter(lambda found: len(found) > 0, avail_set_found))
        avail_set = np.delete(avail_set, avail_set_found, axis=0)
        buff += list(new_pts[is_valid])
        prop_set += buff
        
    return segment_by_diffusion(avail_set, buff, prop_set)

def get_segment(array):
    # Find segments of interest with an array
    #
    # Returns:
    #     an Npt-by-2 matrix where each row stands for (idx_min, idx_max)
    #     (idx_min, idx_max) implies that the (idx_min-1)^th and (idx_max+1)^th element is 0 and
    #     the region in [idx_min, idx_max] is a vector with consecutive 1's

    # Convert into binary array
    arrb = np.array(array, dtype=bool)

    # Represent with run-lengths
    rls = run_length_coding(arrb)

    # Initialize the results
    results = []

    # Append target regions
    offset = 0
    for symb, rl in rls:
        if symb == 1: results += [[offset, offset+rl-1]]
        offset += rl

    return np.array(results)

def segments_set(data):
    # Cluster the points in a 2-D plane into a set of segments
    #
    # Returns:
    #     an array where each element is a N[i]-by-2 matrix which indicates the segments of the i^th row.
    #
    # Reference:
    #     M. Thulke et al: A general approach to quality evaluation of document segmentation results.
    #     Lecture Notes in Computer Science, vol. 1655, pp. 43-57, Springer (1999)

    # Convert into binary matrix, note that the rule of binarization depends on if the element is equal to 0
    data = np.array(data, dtype=bool)

    return map(get_segment, data)

