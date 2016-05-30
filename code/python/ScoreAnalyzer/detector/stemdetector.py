import numpy as np
from ScoreAnalyzer.detector.nhdetector import NoteHeadDetector
from ScoreAnalyzer.detector.utils import find_region, ypos_to_pitch_number

class StemDetector(object):
    def __init__(self, stfwidth=None, stfspace=None, info=None):
        if info is not None:
            self.stfwidth, self.stfspace = info["width"], info["space"]
        else:
            self.stfwidth, self.stfspace = stfwidth, stfspace

    def _in_staff(self, ypos, yc):
        margin = self.stfwidth + self.stfspace
        return ypos >= yc-margin*3 and ypos <= yc+margin*3

    def _find_stems(self, img):
        img = np.array(img)
        c = img.shape[0]/2
        margin = self.stfwidth + self.stfspace

        stems = []
        for i, col in enumerate(img.T):
            rs = find_region(col, find=1, merge_thresh=self.stfwidth)
            rs = filter(lambda r: r[1]-r[0] >= 2*margin and (self._in_staff(r[0], c) or self._in_staff(r[1], c)), rs)
            for miny, maxy in rs:
                if len(stems) > 0 and i-stems[-1][1] == 1: stems[-1] = [stems[-1][0], i, np.min([miny, stems[-1][2]]), np.max([maxy, stems[-1][3]])]
                else: stems.append([i, i, miny, maxy])

        stems = np.array([row for row in stems if row[1]-row[0] <= margin*.2])

        return stems

    def find_stems(self, imgs):
        if not isinstance(imgs, list): imgs = [imgs]
        return map(self._find_stems, imgs)
