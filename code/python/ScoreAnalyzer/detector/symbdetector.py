import numpy as np
from copy import deepcopy
from ScoreAnalyzer.detector.clefdetector import ClefClassifier
from ScoreAnalyzer.detector.nhdetector import NoteHeadDetector, NoteHeadFeatureExtractor
from ScoreAnalyzer.detector.restdetector import RestClassifier
from ScoreAnalyzer.detector.accdtaldetector import AccidentalClassifier
from ScoreAnalyzer.detector.stemdetector import StemDetector
from ScoreAnalyzer.detector.beamgrouper import BeamGrouper
from ScoreAnalyzer.detector.utils import find_region, segment_by_pitch, ypos_to_pitch_number

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
        "rest64",
        "nh-b",
        "nh-w"
    ]

    SYMB_TO_SYMBID = dict(zip(SYMBOLS, np.arange(len(SYMBOLS))+1))
    SYMBID_TO_SYMB = dict(zip(np.arange(len(SYMBOLS))+1, SYMBOLS))

    SYMB_YRANGE = {
        "clef": [-3.5, 3.5],
        "rest": [-3, 2],
        "accidental": [-1.5, 1.5],
        "notehead": [-.75, .75]
    }

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

    @staticmethod
    def _pitch_expansion(pitch_matched):
        if len(pitch_matched.keys()) == 2: return []
        c, margin = pitch_matched["y-center"], pitch_matched["margin"]
        pitches, matcheds = zip(*[(pitch, matched) for pitch, matched in pitch_matched.items() if isinstance(pitch, int)])
        for pitch, matched in zip(pitches, matcheds):
            matched.update({"y-center": c - pitch*margin/2, "margin": margin})

        return matcheds

    @staticmethod
    def _matched_mat(matched, yrange):
        matched = deepcopy(matched)
        c, margin = matched.pop("y-center"), matched.pop("margin")
        if len(matched.keys()) == 0: return np.array([])
        miny, maxy = np.round([c + y*margin for y in yrange])
        matched_mat = [np.vstack([ [SymbolDetector.SYMB_TO_SYMBID[symbname]]*match.shape[0], match.T,
                                   [miny]*match.shape[0], [maxy]*match.shape[0] ]).T 
                        for symbname, match in matched.items()]

        if len(matched_mat) == 0: return np.array([[]])
        matched_mat = reduce(lambda x, y: np.vstack([x, y]), matched_mat)
        return matched_mat

    @staticmethod
    def to_matrix(clef_matched=None, rest_matched=None, acc_matched=None, notehead_matched=None):
        mat = []
        if clef_matched != None: mat.append((clef_matched, SymbolDetector.SYMB_YRANGE["clef"]))
        if rest_matched != None: mat.append((rest_matched, SymbolDetector.SYMB_YRANGE["rest"]))
        if acc_matched != None:
            for pitch_matched in SymbolDetector._pitch_expansion(acc_matched):
                mat.append((pitch_matched, SymbolDetector.SYMB_YRANGE["accidental"]))
        if notehead_matched != None:
            for pitch_matched in SymbolDetector._pitch_expansion(notehead_matched):
                mat.append((pitch_matched, SymbolDetector.SYMB_YRANGE["notehead"]))

        mat = map(lambda x: SymbolDetector._matched_mat(matched=x[0], yrange=x[1]), mat)
        mat = filter(lambda x: x.shape[0] > 0, mat)
        mat = reduce(lambda x, y: np.vstack([x, y]), mat) if len(mat) > 0 else np.array([])
        if mat.shape[0] > 0: mat = mat[np.argsort(mat[:, 2]), :]

        return mat

    def detect(self, img, stfwidth=None, stfspace=None, detect_clef=True, detect_rest=True, detect_acc=True, detect_nh=True, filterfunc=None):
        img = np.array(img)
        clef_matched = self.find_clefs(img, stfwidth, stfspace) if detect_clef else None
        rest_matched = self.find_rests(img, stfwidth, stfspace) if detect_rest else None
        acc_matched = self.find_accidentals(img, stfwidth, stfspace) if detect_acc else None
        notehead_matched = self.find_noteheads(img, clef_matched, None, acc_matched) if detect_nh else None
        tags = SymbolDetector.to_matrix(clef_matched=clef_matched, rest_matched=rest_matched, 
                                        acc_matched=acc_matched, notehead_matched=notehead_matched)
        if filterfunc != None: tags = filterfunc(tags)
        return tags

    def find_clefs(self, img, stfwidth=None, stfspace=None):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        h = self._onset(img[c-2*margin:c+2*margin, :], margin*.2)
        rs = find_region(h, find=1, merge_thresh=0)
        rs = filter(lambda r: self.clefclf.is_clef(img=img[c-2*margin:c+2*margin, r[0]:r[1]]), rs)
        rs = map(lambda r: np.hstack([r, self.clefclf.predict_clef(img=img[c-2*margin:c+2*margin, r[0]:r[1]])]), rs)

        trebles = np.array([np.hstack([float("nan"), row[:2]]) for row in rs if row[2]==0])
        basses = np.array([np.hstack([float("nan"), row[:2]]) for row in rs if row[2]==1])
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

        h = self._onset(img[c-3*margin:c+2*margin, :], margin*.2)
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

    def find_accidentals(self, img, stfwidth=None, stfspace=None, pitch_range=10):
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

    def find_noteheads(self, img, clef_matched=None, rest_matched=None, acc_matched=None, stfwidth=None, stfspace=None, pitch_range=10, matched_mat=np.array([])):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        matched_mat = SymbolDetector.to_matrix(clef_matched=clef_matched, rest_matched=rest_matched, acc_matched=acc_matched)
        if matched_mat.shape[0] > 0:
            for symbid, conf, minx, maxx, miny, maxy in matched_mat: img[miny:maxy, minx:maxx] = 0

        positions = np.arange(-pitch_range, pitch_range+1)[::-1]
        pitch_imgs = segment_by_pitch(img, {"width": stfwidth, "space": stfspace}, pitch_range=pitch_range, overlap=.25)
        pitch_matcheds = {"y-center": c, "margin": margin}
            
        for position, pitch_img in zip(positions, pitch_imgs):
            pitch_c, _ = self._profile(pitch_img, 0, 0)
            h = self._onset(pitch_img[pitch_c-margin/2:pitch_c+margin/2, :], thresh=margin*.2)
            rs = find_region(h, find=1, merge_thresh=margin*.5)
            confs = map(lambda r: self.nhdtr.eval_conf(pitch_img[:, r[0]:r[1]]), rs)
            matched = filter(lambda conf: conf[0] > 0, np.vstack([confs, np.array(rs).T]).T)
            if len(matched) == 0: continue

            pitch_matcheds[position] = {
                "nh-b": np.array([r for r in np.array(matched) if self.nhdtr.get_type(pitch_img[:, r[1]:r[2]]) == "nh-b"]),
                "nh-w": np.array([r for r in np.array(matched) if self.nhdtr.get_type(pitch_img[:, r[1]:r[2]]) == "nh-w"])
            }
            for nhname in pitch_matcheds[position].keys():
                if pitch_matcheds[position][nhname].shape[0] == 0: pitch_matcheds[position].pop(nhname, None)

        return pitch_matcheds

    def find_stems(self, img, clef_matched=None, stfwidth=None, stfspace=None):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        c, margin = self._profile(img, stfwidth, stfspace)

        if clef_matched != None:
            matched_mat = SymbolDetector.to_matrix(clef_matched=clef_matched)
            if matched_mat.shape[0] > 0:
                for symbid, conf, minx, maxx, miny, maxy in matched_mat: img[miny:maxy, minx:maxx] = 0

        stems = StemDetector(stfwidth=stfwidth, stfspace=stfspace).find_stems(img)[0]
        return BeamGrouper(img=img, stems=stems, stfwidth=stfwidth, stfspace=stfspace)

    def find_noteheads_stem_guided(self, img, beamgroup=None, clef_matched=None, stfwidth=None, stfspace=None):
        img = np.array(img)
        if stfwidth is None: stfwidth = self.stfwidth
        if stfspace is None: stfspace = self.stfspace
        if beamgroup is None: beamgroup = self.find_stems(img, clef_matched, stfwidth, stfspace)
        c, margin = self._profile(img, stfwidth, stfspace)
        bg = beamgroup

        for minid, maxid, updown in bg.beams:
            xx = np.arange(bg.stems[minid][0], bg.stems[maxid][0]+1)
            yy = np.array(np.round(np.linspace(bg.stems[minid][updown+2], bg.stems[maxid][updown+2], len(xx))), dtype=int)
            for x, y in zip(xx, yy):
                img[y-margin:y+margin, x] = 0

        def get_rect(minx, maxx, pn):
            rect = np.array([[minx, c-pn*margin/2-margin*.75], [maxx, c-pn*margin/2+margin*.75]])
            return img[rect[0, 1]:rect[1, 1], rect[0, 0]:rect[1, 0]], rect

        pitch_matcheds = {}
        for i, stem in enumerate(bg.stems):
            minx, maxx, miny, maxy = stem
            pu = ypos_to_pitch_number(miny, c, margin)
            pd = ypos_to_pitch_number(maxy, c, margin)
            
            if bg.beamtype_list[i] != 0:
                nhimgs = [nhimg for nhimg, rect in map(lambda x: get_rect(minx, maxx+margin*1.2, x), range(pu-1, pu+2))]
                pu += np.argmax(map(lambda x: self.nhdtr.eval_conf(x), nhimgs))-1
                nhimg, rect = get_rect(minx, maxx+margin*1.2, pu)
                xr = rect[:, 0]
                if self.nhdtr.is_notehead(nhimg):
                    bg.stemnote_founded[i] = True
                    t = self.nhdtr.get_type(nhimg)
                    if not pu in pitch_matcheds.keys():
                        pitch_matcheds[pu] = {t: np.array([[self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])}
                    else:
                        if not t in pitch_matcheds[pu]:
                            pitch_matcheds[pu][t] = np.array([[self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])
                        else:
                            mat = pitch_matcheds[pu][t]
                            pitch_matcheds[pu][t] = np.vstack([mat, [self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])

            if bg.beamtype_list[i] != 1:
                nhimgs = [nhimg for nhimg, rect in map(lambda x: get_rect(minx-margin*1.2, maxx, x), range(pd-1, pd+2))]
                pd += np.argmax(map(lambda x: self.nhdtr.eval_conf(x), nhimgs))-1
                nhimg, rect = get_rect(minx-margin*1.2, maxx, pd)
                xr = rect[:, 0]
                if self.nhdtr.is_notehead(nhimg):
                    bg.stemnote_founded[i] = True
                    t = self.nhdtr.get_type(nhimg)
                    if not pd in pitch_matcheds.keys():
                        pitch_matcheds[pd] = {t: np.array([[self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])}
                    else:
                        if not t in pitch_matcheds[pd]:
                            pitch_matcheds[pd][t] = np.array([[self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])
                        else:
                            mat = pitch_matcheds[pd][t]
                            pitch_matcheds[pd][t] = np.vstack([mat, [self.nhdtr.eval_conf(nhimg), xr[0], xr[1]]])

        pitch_matcheds["y-center"] = c
        pitch_matcheds["margin"] = margin

        return pitch_matcheds

