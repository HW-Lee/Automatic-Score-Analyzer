import os
import glob
import numpy as np
from ScoreAnalyzer.image import imagetools as it
from scipy import misc

rootpath = os.path.dirname(os.path.abspath(__file__))
SIM_THRESH = {
    1 : .75,
    2 : .75,
    4 : .75,
    8 : .65,
    16: .7,
    32: .7,
    64: .7
}

class RestClassifier(object):
    def __init__(self):
        imglist = glob.glob("{}/models/rest*.png".format(rootpath))
        imgid = map(lambda x: int(x.split("/")[-1].replace("rest", "").replace(".png", "")), imglist)
        tpl_imgs = map(lambda x: it.load(x, reverse=True), imglist)
        self.templates = dict(zip(imgid, tpl_imgs))
        self.decision_thresh = SIM_THRESH

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
        feats = map(lambda feat: feat*1. / np.linalg.norm(feat, ord=2), feats)
        feats = np.array(feats)
        template = template.flatten()
        template /= np.linalg.norm(template, ord=2)
        return np.vstack([np.dot(feats, template), np.arange(num_frames)+dp_offset]).T

    def _eval_conf(self, img):
        keys, templates = zip(*self.templates.items())
        confs = map(lambda template: self._cos_similarity(img, template), templates)
        return dict(zip(keys, confs))

    def eval_conf(self, imgs):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        conflist = map(self._eval_conf, imgs)
        return conflist if len(imgs) > 1 else conflist[0]

    def _find_best_matched(self, img):
        confs = self._eval_conf(img)
        for key, mat in confs.items():
            confs[key] = mat[np.argmax(mat[:, 0]), :]

        return np.array(map(lambda k: np.hstack([k, confs[k]]), sorted(confs.keys())))

    def find_best_matched(self, imgs):
        if not isinstance(imgs, list): imgs = [imgs]
        if len(imgs) == 0: return []

        bmtched_list = map(self._find_best_matched, imgs)
        return bmtched_list if len(imgs) > 1 else bmtched_list[0]
