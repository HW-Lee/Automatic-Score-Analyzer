import os
import glob
import numpy as np
from ScoreAnalyzer.detector.utils import find_region
from ScoreAnalyzer.image import imagetools as it
from scipy import misc

rootpath = os.path.dirname(os.path.abspath(__file__))

class RestClassifier(object):
    SIM_THRESH = {
        1 : .7,
        2 : .7,
        4 : .75,
        8 : .7,
        16: .7,
        32: .7,
        64: .7
    }

    def __init__(self):
        imglist = glob.glob("{}/models/rest*.png".format(rootpath))
        imgid = map(lambda x: int(x.split("/")[-1].replace("rest", "").replace(".png", "")), imglist)
        tpl_imgs = map(lambda x: it.load(x, reverse=True), imglist)
        self.templates = dict(zip(imgid, tpl_imgs))
        self.decision_thresh = RestClassifier.SIM_THRESH

    def _cos_similarity(self, img, template):
        img = np.array(img)
        template = np.array(template)

        scale = template.shape[0]*1./img.shape[0]
        template = misc.imresize(template, 1./scale) / 255.

        if template.shape[1] > img.shape[1]:
            zerospad = np.zeros([img.shape[0], template.shape[1]-img.shape[1]])
            img = np.hstack([img, zerospad])

        padlen = template.shape[1]/4
        zerospad = np.zeros([img.shape[0], padlen])
        img = np.hstack([zerospad, img, zerospad])
        dp_offset = -padlen

        num_frames = img.shape[1]-template.shape[1]+1
        regions = np.tile([0, template.shape[1]], [num_frames, 1])
        regions += np.tile(np.arange(num_frames), [2, 1]).T

        frames = map(lambda r: img[:, r[0]:r[1]], regions)
        feats = map(lambda frame: frame.flatten(), frames)
        feats = map(lambda feat: feat*1. / (np.linalg.norm(feat, ord=2)+1), feats)
        feats = np.array(feats)
        template = template.flatten()
        template /= np.linalg.norm(template, ord=2)

        starts = np.arange(num_frames)+dp_offset
        ends = starts + len(template)/img.shape[0]
        return np.vstack([np.dot(feats, template), starts, ends]).T

    def _eval_conf(self, img):
        keys, templates = zip(*self.templates.items())
        confs = map(lambda template: self._cos_similarity(img, template), templates)
        return dict(zip(keys, confs))

    def eval_conf(self, imgs):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        conflist = map(self._eval_conf, imgs)
        return conflist if len(imgs) > 1 else conflist[0]

    def _find_matched(self, img, eliminate_empty):
        confs = self._eval_conf(img)
        for key, mat in confs.items():
            rs = find_region(mat[:, 0] > self.decision_thresh[key], find=1, merge_thresh=0)
            confs[key] = np.array(map(lambda r: mat[r[0]+np.argmax(mat[r[0]:r[1]+1, 0]), :], rs))
            if eliminate_empty and np.sum(confs[key].shape) == 0: confs.pop(key, None)

        return confs

    def find_matched(self, imgs, eliminate_empty=False):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        bmtched_list = map(lambda img: self._find_matched(img, eliminate_empty), imgs)
        return bmtched_list if len(imgs) > 1 else bmtched_list[0]
