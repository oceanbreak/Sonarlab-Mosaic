from lib.SonarData import SonarStripe
import lib.Utils as ut
import numpy as np
from scipy.signal import spline_filter, savgol_filter, medfilt


class TrackProcess:

    def __init__(self, sonar_stripes_array):
        self.track = []
        self.rotations = []
        for stripe in sonar_stripes_array:
            self.track.append((stripe.lon, stripe.lat))
        self.calcRotations()
        self.cable_out = [0] * len(self.track)


    def smoothRotations(self, window, order):
        self.rotations = savgol_filter(self.rotations, window, order)

    
    def filterRotations(self, window):
        self.rotations = medfilt(self.rotations, window)


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


    def updateCableOut(self):

        new_track = [None] * len(self.track)
        outlier_track_length = 0
        for i in range(len(self.track)):
            cable_out = self.cable_out[i]
            # Start from previous ping
            distance = 0.0
            j = 1
            while distance < cable_out and i-j >=0:
                distance = ut.calcDistance(self.track[i], self.track[i-j])
                j += 1

            if i-j >= 0:
                new_track[i] = self.track[i-j]
            else:
                outlier_track_length += 1
                # new_track[i] = self.calcOffsetedPoint(self.track[i], cable_out)

        # Extrapolate track
        delta_meters = cable_out / outlier_track_length
        for i in range(outlier_track_length):
            print(f'delta metres = { (outlier_track_length - i)*delta_meters}')
            new_track[i] = self.calcOffsetedPoint(self.track[0],
                                                   (outlier_track_length - i)*delta_meters)
        
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
        rot = 180 - self.rotations[0] # Back direction
        offset_x, offset_y = ut.calcDistByRot(pt1, rot, offset)
        print(f'Calculated offset {(offset_x, offset_y)} based on rotation {rot}')
        return (offset_x, offset_y)
    

    def inputCableOut(self, cableOutInfo):
        """
        Function for  manual input of cable out
        CableOut info must be array of tuples (ping, cable)
        where ping is ping number
        cable is cableout info in corresponding time
        """
        if type(cableOutInfo) == int:
            self.cable_out = [cableOutInfo] * len(self.cable_out)
            return 0
        
        start_ping_no = 0
        for cur_info in cableOutInfo:
            ping_no, cableout = cur_info
            for i in range(start_ping_no, ping_no):
                self.cable_out[i] = cableout
            start_ping_no = ping_no
        # Fill to the end
        for i in range(start_ping_no, len(self.cable_out)):
            pass


