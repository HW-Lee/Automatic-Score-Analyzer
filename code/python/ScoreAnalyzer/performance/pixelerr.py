import numpy as np

def evaluate_staff_removal_efficiency(result, gt, image, detail=False):
    result = np.array(result)
    gt = np.array(gt)
    image = np.array(image)

    compare_tuple = np.sum(result.flatten() != gt.flatten()), np.sum(image.flatten() == 1.)

    if detail: return compare_tuple
    return float(compare_tuple[0]) / compare_tuple[1]
