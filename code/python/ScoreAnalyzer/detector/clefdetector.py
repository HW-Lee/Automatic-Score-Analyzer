import os
import numpy as np
from scipy import misc
from sklearn import svm
from sklearn.externals import joblib

rootpath = os.path.dirname(os.path.abspath(__file__))

class ClefFeatureExtractor(object):
    @staticmethod
    def get_feat(img):
        aspect_ratio = img.shape[1] * 1. / img.shape[0]
        img = ClefFeatureExtractor.get_tiny_image(img, [20, 15])
        horiz_proj = np.mean(img, axis=0).tolist()
        vert_proj = np.mean(img, axis=1).tolist()
        horiz_centroid = (np.dot(img.T, np.arange(img.shape[0])) / (np.sum(img, axis=0) + 1/255.) / img.shape[0]).tolist()
        vert_centroid = (np.dot(img, np.arange(img.shape[1])) / (np.sum(img, axis=1) + 1/255.) / img.shape[1]).tolist()
        
        return [aspect_ratio] + horiz_proj + vert_proj + horiz_centroid + vert_centroid

    @staticmethod
    def get_tiny_image(img, size):
        img = np.array(img)
        aspect_ratio = img.shape[1] * 1. / img.shape[0]
        ref_aspect_ratio = size[1] * 1. / size[0]

        return misc.imresize(img, size) * np.min([1., aspect_ratio / ref_aspect_ratio]) / 255. * 2 - 1

class ClefClassifier(object):
    def __init__(self, model=["clef_clf20160430-1", "clef_dtr20160430-1"]):
        self.clf = joblib.load("{}/models/{}.pkl".format(rootpath, model[0]))
        self.dtr = joblib.load("{}/models/{}.pkl".format(rootpath, model[1]))

    def predict_clef(self, img):
        return int(self.clf.predict(ClefFeatureExtractor.get_feat(img)))

    def predict_clefs(self, imgs):
        return np.array(map(self.predict_clef, imgs))

    def decision_function(self, imgs):
        return map(self.clf.decision_function, map(ClefFeatureExtractor.get_feat, imgs))

    def is_clef(self, imgs=None, img=None, decision_thresh=0):
        if img != None:
            imgs = [np.array(img)]

        if imgs != None:
            results = np.array(map(lambda x: abs(x.shape[1]*1./x.shape[0] - .6) < .3, imgs)).flatten()
            feats = np.array(map(lambda x: ClefFeatureExtractor.get_tiny_image(x, [20, 15]).flatten(), imgs))
            results &= np.array(self.dtr.decision_function(feats) > decision_thresh).flatten()

        if img: return results[0]
        return results