import os
import numpy as np
from ScoreAnalyzer.detector.clefdetector import ClefClassifier
from ScoreAnalyzer.detector.nhdetector import NoteHeadDetector
from ScoreAnalyzer.detector.restdetector import RestClassifier
from ScoreAnalyzer.detector.accdtaldetector import AccidentalClassifier
from ScoreAnalyzer.detector.utils import find_region, segment_by_pitch

rootpath = os.path.dirname(os.path.abspath(__file__))

class SymbolDetector(object):
    SYMBOLS = [
        "treble",
        "bass",
        "flat",
        "sharp",
        "natural",
        "rest01",
        "rest02",
        "rest04",
        "rest08",
        "rest16",
        "rest32",
        "rest64"
    ]

    SYMB_TO_SYMBID = dict(zip(SYMBOLS, np.arange(len(SYMBOLS))+1))
    SYMBID_TO_SYMB = dict(zip(np.arange(len(SYMBOLS))+1, SYMBOLS))

    def __init__(self, stfwidth=None, stfspace=None, clefclf=None, nhdtr=None, restclf=None, accdtclf=None):
        self.stfwidth = stfwidth
        self.stfspace = stfspace
        self.clefclf = ClefClassifier() if clefclf is None else clefclf
        self.nhdtr = NoteHeadDetector() if nhdtr is None else nhdtr
        self.restclf = RestClassifier() if restclf is None else restclf
        self.accdtclf = AccidentalClassifier() if accdtclf is None else accdtclf

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

        trebles = np.array([row[:2] for row in rs if row[2]==0])
        basses = np.array([row[:2] for row in rs if row[2]==1])
        matched = {"treble": trebles, "bass": basses}
        for clefname in matched.keys():
            if matched[clefname].shape[0] == 0: matched.pop(clefname, None)

        matched["y-center"] = c
        matched["margin"] = margin

        return matched

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
        if len(matchedlist) == 0: matchedlist = np.array([])
        else: matchedlist = reduce(lambda x, y: np.vstack([x, y]), matchedlist)
        matched = {}
        for restid in self.restclf.decision_thresh.keys():
            matched["rest{:02d}".format(restid)] = np.array([row[1:] for row in matchedlist if row[0]==restid])
            if matched["rest{:02d}".format(restid)].shape[0] == 0: matched.pop("rest{:02d}".format(restid), None)

        matched["y-center"] = c
        matched["margin"] = margin

        return matched

    def find_accidentals(self, img, stfwidth=None, stfspace=None, pitch_range=8):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        positions = np.arange(-pitch_range, pitch_range+1)[::-1]
        pitch_imgs = segment_by_pitch(img, {"width": stfwidth, "space": stfspace}, pitch_range=pitch_range, overlap=1)
        pitch_matcheds = self.accdtclf.find_matched(pitch_imgs, eliminate_empty=True)
        pitch_matcheds =  dict(zip(positions, pitch_matcheds))
        for position in positions:
            if len(pitch_matcheds[position].keys()) == 0:
                pitch_matcheds.pop(position, None)

        pitch_matcheds["y-center"] = c
        pitch_matcheds["margin"] = margin

        return pitch_matcheds