import os
import numpy as np
from scipy import misc
from sklearn import svm
from sklearn.externals import joblib

rootpath = os.path.dirname(os.path.abspath(__file__))

class NoteHeadFeatureExtractor(object):
    @staticmethod
    def get_tiny_image(img, size):
        img = np.array(img)
        aspect_ratio = img.shape[1] * 1. / img.shape[0]
        ref_aspect_ratio = size[1] * 1. / size[0]

        return misc.imresize(img, size) * np.min([1., aspect_ratio / ref_aspect_ratio]) / 255. * 2 - 1

    @staticmethod
    def get_feat(img, width, tighten=False):
        img = np.array(img)
        feat = []
        if tighten: img = NoteHeadFeatureExtractor._binimg_tighten(img=img)
        img = misc.imresize(img, [width, width]) / 255.

        for s in range(width):
            feat += [0]
            for i, j in NoteHeadFeatureExtractor._get_positions(s):
                feat[-1] += img[i, j]
        for s in range(width-1):
            feat += [0]
            for i, j in NoteHeadFeatureExtractor._get_positions(width-2-s):
                feat[-1] += img.T[i, j]

        return feat

    @staticmethod
    def find_feat_peak(img, width, tighten=False):
        return 1 - abs(width-1-np.argmax(NoteHeadFeatureExtractor.get_feat(img, width)))*1./(width-1)

    @staticmethod
    def _binimg_tighten(img):
        img = np.array(img)
        vert = np.sum(img, axis=0) > 0
        horiz = np.sum(img, axis=1) > 0
        if np.sum(vert) == 0 or np.sum(horiz) == 0: return np.array([])
        xr = np.where(vert == 1)[0]
        yr = np.where(horiz == 1)[0]

        return img[yr[0]:yr[-1], xr[0]:xr[-1]]

    @staticmethod
    def _get_positions(num):
        n = np.arange(num+1)
        return np.array([n, num-n]).transpose()

class NoteHeadDetector(object):
    def __init__(self, model="notehead20160517-1", typemodel="notehead_clf20160528", decision_thresh=0):
        self.clf = joblib.load("/".join([rootpath, "models", model]) + ".pkl")
        self.typeclf = joblib.load("/".join([rootpath, "models", typemodel]) + ".pkl")
        self.decision_thresh = decision_thresh
        self.featwidth = 12

    def is_notehead(self, img, tighten=False):
        if img.shape[0]/1.5 > img.shape[1] or img.shape[1]/1.5 > img.shape[0]: return False
        return self.eval_conf(img=img, tighten=tighten) > self.decision_thresh

    def eval_conf(self, img, tighten=False):
        if img.shape[0]/1.5 > img.shape[1] or img.shape[1]/1.5 > img.shape[0]: return -1
        feat = NoteHeadFeatureExtractor.get_feat(img=img, width=self.featwidth, tighten=tighten)
        return self.clf.decision_function([feat])[0][0]

    def get_type(self, img, tighten=False):
        if self.typeclf.predict([NoteHeadFeatureExtractor.get_tiny_image(img, [12, 16]).flatten()])[0] == 0: return "nh-h"
        else: return "nh-s"
