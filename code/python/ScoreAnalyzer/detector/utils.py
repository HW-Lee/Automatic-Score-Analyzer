import numpy as np
from ScoreAnalyzer.runlength.rlcodec import run_length_coding

def staff_tighten(data, staff, bound_thresh):
    # Tighten an image with its stafflines extraction results
    vertproj = np.sum(staff, axis=0)
    bound_thresh = np.minimum(np.median(vertproj), bound_thresh)
    idces = np.where(vertproj >= bound_thresh)[0]
    
    if np.sum(idces.shape) == 0: return data
    else: return data[:, idces[0]:idces[-1]+1]

def is_barline(data, region, info):
    height = info["width"]*5 + info["space"]*4
    main_region = data[:, region[0]:region[1]]
    
    return np.sum(np.sum(main_region, axis=1) > 0, axis=0) > height*.9

def find_region(array, find):
    rlc = run_length_coding(array)
    offset = np.zeros(len(rlc))
    for x in range(len(rlc)-1): offset[x+1] = offset[x] + rlc[x][1]

    regions = filter(lambda x: x[0][0] == find, zip(rlc, offset))
    regions = map(lambda x: [int(x[1]), int(x[1]+x[0][1])], regions)

    return regions

def get_barline_positions(data, info):
    c = int(np.floor(data.shape[0] / 2))
    height = info["width"]*5 + info["space"]*4
    sample = data[c-height/2:c+height/2+1, :]
    
    h = np.zeros([sample.shape[1], 1]).flatten()
    r = [0, 2*info["width"] + info["space"]]
    
    for x in range(sample.shape[1]-3):
        inf = r[0] + x
        sup = np.minimum(r[1] + x, sample.shape[1])
        feat = run_length_coding(np.sum(sample[:, inf:sup], axis=0) > info["space"])
        if len(feat) == 3 and feat[0][0] == 0: h[(inf+sup)/2] = 1
        
    regions = find_region(h, find=1)
    regions = np.array(filter(lambda region: is_barline(sample, region, info), regions))
    
    return regions

def segment_by_measures(symb, staff, info):
    symb_tight = staff_tighten(data=symb, staff=staff)
    regions = get_barline_positions(data=symb_tight, info=info)
    regions = reduce(lambda x, y: x+y, regions)
    regions = [0] + regions + [symb_tight.shape[1]]
    regions = np.array(regions)
    regions = np.reshape(regions, [len(regions)/2, 2])
    return map(lambda region: np.array(symb_tight[:, region[0]:region[1]+1]), regions)
