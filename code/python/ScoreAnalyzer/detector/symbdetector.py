import os
import numpy as np
from ScoreAnalyzer.detector.clefdetector import ClefClassifier
from ScoreAnalyzer.detector.nhdetector import NoteHeadDetector
from ScoreAnalyzer.detector.restdetector import RestClassifier
from ScoreAnalyzer.detector.utils import find_region, segment_by_pitch

rootpath = os.path.dirname(os.path.abspath(__file__))

class SymbolDetector(object):
    def __init__(self, stfwidth=None, stfspace=None, clefclf=None, nhdtr=None, restclf=None):
        self.stfwidth = stfwidth
        self.stfspace = stfspace
        self.clefclf = ClefClassifier() if clefclf is None else clefclf
        self.nhdtr = NoteHeadDetector() if nhdtr is None else nhdtr
        self.restclf = RestClassifier() if restclf is None else restclf

    def _profile(self, img, stfwidth, stfspace):
        return img.shape[0]/2, stfwidth+stfspace

    def _onset(self, img, thresh):
        return np.sum(img, axis=0) > thresh

    def find_clefs(self, img, stfwidth=None, stfspace=None):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        h = self._onset(img, margin*.2)
        rs = find_region(h, find=1, merge_thresh=0)
        rs = filter(lambda r: self.clefclf.is_clef(img=img[c-2*margin:c+2*margin, r[0]:r[1]]), rs)
        rs = map(lambda r: np.hstack([r, self.clefclf.predict_clef(img=img[c-2*margin:c+2*margin, r[0]:r[1]])]), rs)

        return np.array(rs)

    def find_rests(self, img, stfwidth=None, stfspace=None):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        h = self._onset(img, margin*.2)
        rs = find_region(h, find=1, merge_thresh=stfwidth)
        segments = map(lambda r: img[c-3*margin:c+2*margin, r[0]:r[1]], rs)
        matchedlist = self.restclf.find_matched(imgs=segments, eliminate_empty=True)
        for i, matched in enumerate(matchedlist):
            if len(matched.values()) == 0:
                matchedlist[i] = np.array([])
                continue
            for key, mat in matched.items():
                matched[key] = np.vstack([[key]*mat.shape[0], mat.T]).T
                matched[key][:, 2:] += rs[i][0]

            matchedlist[i] = reduce(lambda x, y: np.vstack([x, y]), matched.values())

        matchedlist = filter(lambda x: np.sum(x.shape) > 0, matchedlist)
        if len(matchedlist) == 0: return np.array([])
        return reduce(lambda x, y: np.vstack([x, y]), matchedlist)
