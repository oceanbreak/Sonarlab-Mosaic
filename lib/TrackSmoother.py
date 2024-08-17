from lib.SonarData import SonarStripe
import lib.Utils as ut
import numpy as np
from scipy.signal import spline_filter, savgol_filter


class TrackSmoother:

    def __init__(self, sonar_stripes_array):
        self.track = []
        self.rotations = []
        for stripe in sonar_stripes_array:
            self.track.append((stripe.lon, stripe.lat))

    def smoothRotations(self, window, order):
        self.rotations = savgol_filter(self.rotations, window, order)
        return self.rotations

    def getTrackRotations(self):
        for i in range(1,len(self.track)):
            pt1 = self.track[i-1]
            pt2 = self.track[i]
            # print(type(pt1), type(pt2))
            rot = ut.calcRotBtwPoints(pt1, pt2)
            self.rotations.append(rot)
        # Make size equal
        self.rotations.append(self.rotations[-1])
        return self.rotations