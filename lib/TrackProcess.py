from lib.SonarData import SonarStripe
import lib.Utils as ut
import numpy as np
from scipy.signal import spline_filter, savgol_filter


class TrackProcess:

    def __init__(self, sonar_stripes_array):
        self.track = []
        self.rotations = []
        for stripe in sonar_stripes_array:
            self.track.append((stripe.lon, stripe.lat))
        self.calcRotations()


    def smoothRotations(self, window, order):
        self.rotations = savgol_filter(self.rotations, window, order)


    def getTrack(self):
        return self.track

    def getTrackRotations(self):
        return self.rotations
    
    
    def calcRotations(self):
        rotations = []
        for i in range(1,len(self.track)):
            j = 0
            while self.track[i-j] == self.track[i]:
                j += 1
            pt1 = self.track[i-j]
            pt2 = self.track[i]
            # print(type(pt1), type(pt2))
            rot = ut.calcRotBtwPoints(pt1, pt2)
            rotations.append(rot)
        # Make size equal by doubling last value
        rotations.append(rotations[-1])

        self.rotations = rotations


    def updateCableOut(self, cable_out):
        new_track = [None] * len(self.track)
        for i in range(len(self.track)):
            # Start from previous ping
            distance = 0.0
            j = 1
            while distance < cable_out and i-j >=0:
                distance = ut.calcDistance(self.track[i], self.track[i-j])
                j += 1

            if i-j >= 0:
                new_track[i] = self.track[i-j]
            else:
                new_track[i] = self.calcOffsetedPoint(self.track[i], cable_out)
        self.track = new_track
        print(f'Track updated based on cable offset {cable_out} m')
        print('Test for pairs')
        for i in range(1, len(self.track)):
            if self.track[i-1] == self.track[i]:
                print(f'Repeated {self.track[i]}')
        # Update rotataions
        self.calcRotations()


    def calcOffsetedPoint(self, pt1, offset):
        # Calculate offset from beginning of track
        pt0 = ((self.track[0][0] - 0.001), (self.track[0][1] - 0.001))
        dist1 = ut.calcDistance(pt0, pt1)
        proportion = dist1 / offset
        offset_x = (pt1[0] - pt0[0])/proportion + pt0[0]
        offset_y = (pt1[1] - pt0[1])/proportion + pt0[1]
        return (offset_x, offset_y)