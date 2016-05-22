import os
import glob
import numpy as np
from ScoreAnalyzer.detector.utils import find_region, cos_similarity
from ScoreAnalyzer.image import imagetools as it
from scipy import misc

rootpath = os.path.dirname(os.path.abspath(__file__))

class AccidentalClassifier(object):
    SIM_THRESH = {
        "flat"   : .7,
        "sharp"  : .7,
        "natural": .75
    }

    def __init__(self):
        imglist = glob.glob("{}/models/accidental-*.png".format(rootpath))
        imgid = map(lambda x: x.split("/")[-1].replace("accidental-", "").replace(".png", ""), imglist)
        tpl_imgs = map(lambda x: it.load(x, reverse=True), imglist)
        self.templates = dict(zip(imgid, tpl_imgs))
        self.decision_thresh = AccidentalClassifier.SIM_THRESH

    def _eval_conf(self, img):
        keys, templates = zip(*self.templates.items())
        confs = map(lambda template: cos_similarity(img, template), templates)
        return dict(zip(keys, confs))

    def eval_conf(self, imgs):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        conflist = map(self._eval_conf, imgs)
        return conflist

    def _find_matched(self, img, eliminate_empty):
        confs = self._eval_conf(img)
        for key, mat in confs.items():
            rs = find_region(mat[:, 0] > self.decision_thresh[key], find=1, merge_thresh=0)
            confs[key] = np.array(map(lambda r: mat[r[0]+np.argmax(mat[r[0]:r[1], 0]), :], rs))
            if eliminate_empty and np.sum(confs[key].shape) == 0: confs.pop(key, None)

        return confs

    def find_matched(self, imgs, eliminate_empty=False):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        bmtched_list = map(lambda img: self._find_matched(img, eliminate_empty), imgs)
        return bmtched_list
