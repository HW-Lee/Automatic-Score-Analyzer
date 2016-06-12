import numpy as np
from ScoreAnalyzer.detector.utils import find_region, line_integral

class BeamGrouper(object):
    def __init__(self, img, stems, stfwidth=None, stfspace=None, info=None):
        if info is not None:
            self.stfwidth, self.stfspace = info["width"], info["space"]
        else:
            self.stfwidth, self.stfspace = stfwidth, stfspace

        self.stems = stems
        margin = self.stfwidth + self.stfspace
        img = np.array(img)
                    
        beams_segments = self._find_segments(img, margin)
        beams = self._aggregate_segments(beams_segments)
        self.beams = self._eliminate_false_positives(beams)
        self.beamtype_list = -np.ones(self.stems.shape[0])
        self.stemnote_founded = [False]*self.stems.shape[0]
        for minid, maxid, updown in self.beams:
            self.beamtype_list[minid:maxid+1] = updown

    def _find_segments(self, img, margin):
        beams_segments = []
        for i in range(0, self.stems.shape[0]):
            for j in range(i, self.stems.shape[0]):
                added = False
                for k in [0, 1]:
                    if self.stems[j][0] - self.stems[i][0] < 2*margin: continue
                    pt1 = [self.stems[i][0], self.stems[i][k+2]]
                    pt2 = [self.stems[j][0], self.stems[j][k+2]]
                    proj = line_integral(img, [pt1, pt2], yrange=margin*2)
                    onset_regions = find_region(proj > (pt2[0]-pt1[0]+1)*.9, find=1, merge_thresh=0)
                    if len(onset_regions) > 0 and reduce(lambda x, y: x | y, map(lambda r: r[1]-r[0] > margin*.2, onset_regions)):
                        beams_segments.append([i, j, k])
                        added = True
                        break
                if added: break

        return sorted(beams_segments, key=lambda x: x[2])

    def _aggregate_segments(self, segments):
        beams = []
        for segment in segments:
            if len(beams) == 0: 
                beams.append(segment)
                continue
            if segment[0] == beams[-1][1] and segment[2] == beams[-1][2]:
                beams[-1][1] = segment[1]
            else:
                beams.append(segment)

        return sorted(beams, key=lambda x: x[0])

    def _eliminate_false_positives(self, beams):
        beams_filt = []
        for beam in beams:
            if len(beams_filt) == 0:
                beams_filt.append(beam)
                continue
            if beam[0] <= beams_filt[-1][1]:
                new_i, new_j, _ = beam
                old_i, old_j, _ = beams_filt[-1]
                if self.stems[new_j][0] - self.stems[new_i][0] > self.stems[old_j][0] - self.stems[old_i][0]:
                    beams_filt[-1] = beam
            else:
                beams_filt.append(beam)

        return np.array(beams_filt)
