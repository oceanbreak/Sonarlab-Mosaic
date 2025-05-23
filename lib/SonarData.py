import pyxtf
import cv2
import numpy as np
import lib.Utils as ut
import logging
import glob
from matplotlib import pyplot as plt
import sys


class SonarStripe:

    def __init__(self, image : np.ndarray, coordinatesGK : tuple, size_meters : tuple):
        self.image = image
        self.lon = coordinatesGK[0]
        self.lat = coordinatesGK[1]
        self.widthM = size_meters[0]
        self.heightM = size_meters[1]

        # Calculate scale in pixels / meters
        self.scaleX = self.image.shape[1] / self.widthM
        self.scaleY = self.image.shape[0] / self.heightM

    def __str__(self):
        return f'Sonar Stripe with begin coord: {self.lon}, {self.lat}\n' + \
                f"Width: {self.widthM} m, Height: {self.heightM} m\n" + \
                f"Scale X: {self.scaleX} px/m, Scale Y: {self.scaleY} px/m"

class SonarData:

    def getPingTime(self, ping_no):
        year = self.sonar_packets[ping_no].Year
        month = self.sonar_packets[ping_no].Month + 1 # Month in XTF starts from 0
        day =  self.sonar_packets[ping_no].Day
        hour =  self.sonar_packets[ping_no].Hour
        minute =  self.sonar_packets[ping_no].Minute
        second =  self.sonar_packets[ping_no].Second
        hseconds =  self.sonar_packets[ping_no].HSeconds # Hundredths of second
        return np.array((year, month, day, hour, minute, second, hseconds), dtype=np.uint32)
    
    
    def getSonarLine(self, ping_no):
        if 0 <= ping_no < self.pings_num:
            l_chan = self.sonar_packets[ping_no].data[0]
            r_chan = self.sonar_packets[ping_no].data[1]
            return (l_chan, r_chan)
        else:
            return None
        

    def writeSonarLine(self, ping_no, rgt, lft):
        if 0 <= ping_no < self.pings_num:
            self.sonar_packets[ping_no].data[0] = lft
            self.sonar_packets[ping_no].data[1] = rgt 


    def getPingCoordinates(self, ping_no):
        lon = self.sonar_packets[ping_no].ShipXcoordinate
        lat = self.sonar_packets[ping_no].ShipYcoordinate
        return (lon, lat)


    def getPingCoordinatesGK(self, ping_no):
        lon = self.sonar_packets[ping_no].ShipXcoordinateGK
        lat = self.sonar_packets[ping_no].ShipYcoordinateGK
        return (lon, lat)


    def getPingNoByTime(self, input_time, start_no=0, reversed = False):
        if reversed:
            for packet_no in range(start_no, 0, -1):
                cur_packet_time = self.getPingTime(packet_no)
                if ut.timeToSec(*cur_packet_time) < ut.timeToSec(*input_time):
                    break
            return packet_no

        for packet_no in range(start_no, self.pings_num):
            cur_packet_time = self.getPingTime(packet_no)
            if ut.timeToSec(*cur_packet_time) > ut.timeToSec(*input_time):
                break
        return packet_no


    def createFrame(self, ping_no, vertical_scale):
        ping_no = self.pings_num - ping_no # Because full picture starts with end
        # Check if frame doesn't exceed beginning and ending of data
        if vertical_scale >= len(self.sonar_packets):
            begin = 0
            end = self.pings_num
        else:
            if ping_no > vertical_scale//2:
                if ping_no > len(self.sonar_packets) - vertical_scale/2:
                    begin = ping_no - vertical_scale//2
                    end = len(self.sonar_packets) - 1
                else:
                    begin = ping_no - vertical_scale//2
                    end = ping_no + vertical_scale//2
            else:
                begin = 0
                end = ping_no + vertical_scale//2

        # Draw a line on current ping
        line_begin = (0, ping_no-begin)
        line_end = (self.fullImage.shape[1], ping_no - begin)

        cur_frame = np.zeros( (end-begin, self.fullImage.shape[1]) )
        cur_frame[:, :] = self.fullImage[begin:end, :]
        cur_frame = cv2.line(cur_frame, line_begin, line_end, (255,0,0), 1)
        return cur_frame


    def getSonarStripeGK(self, ping_start, ping_stop) -> SonarStripe:
        """ 
        Return SonarStripe object with
        """
        if ping_start < 0 or ping_stop >= self.pings_num :
            return None
        if ping_start == ping_stop:
            return None
        # Reverse, because image Y 0 starts from top
        img = self.fullImage[-ping_start-1:-ping_stop-1:-1, :]
        
        lon1, lat1 = self.getPingCoordinatesGK(ping_start)
        lon2, lat2 = self.getPingCoordinatesGK(ping_stop)

        # Calculate size in meters

        Xsize = self.sonar_packets[ping_start].ping_chan_headers[0].SlantRange + \
                 self.sonar_packets[ping_start].ping_chan_headers[1].SlantRange 
        Ysize = ut.calcDistance((lon1, lat1), (lon2, lat2))

        return SonarStripe(img, (lon1, lat1), (Xsize, Ysize))
    

    def splitIntoGKStripes(self):
        # Split sonar image in stripes with equal coordinates 
        # Also form filtered track
        sonar_stripes = []
        ping_start = 0
        ping_no = 0
        prev_lon = self.sonar_packets[0].ShipXcoordinateGK
        prev_lat = self.sonar_packets[0].ShipYcoordinateGK
        for sonar_packet in self.sonar_packets[1:]:
            ping_no += 1
            lon = sonar_packet.ShipXcoordinateGK
            lat = sonar_packet.ShipYcoordinateGK
            ping_stop = ping_no
            if prev_lon != lon or prev_lat != lat:
                stripe = self.getSonarStripeGK(ping_start, ping_stop)
                sonar_stripes.append(stripe)
                ping_start = ping_stop
                prev_lat = lat
                prev_lon = lon
        print(f'Created {len(sonar_stripes)} sonar stripes')
        return sonar_stripes
    
    
    def estimateFirstReflection(self, rgt, threshold, start_refl):
        # Estimate dirst reflection by right channel
        refl_start_refl = rgt[start_refl:]
        refl_arr = refl_start_refl[refl_start_refl < threshold]
        return len(refl_arr) + start_refl
    
    
    def calculateNewDistances(self, rgt, slant_range, fish_height, first_reflection):
        x0 = np.arange(len(rgt))
        L = x0[first_reflection:] * slant_range / len(rgt) # array of slant ranges for each reflection
        H = fish_height
        return np.sqrt(L*L - H*H)
    
    
    def remapChannel(self, rgt_corrected, new_range):
        x0 = new_range
        x1 = np.linspace(0, new_range[-1], len(new_range))
        y_new = np.interp(x1, x0, rgt_corrected)
        return y_new
    

    def correctSlantRange(self, threshold = 10, startrefl=0):
        for ping_no in range(len(self.sonar_packets)):
            sys.stdout.write(f'\rAnalysing {ping_no} of {len(self.sonar_packets)} pings')
            lft, rgt = self.getSonarLine(ping_no)
            slant_range = self.sonar_packets[ping_no].ping_chan_headers[0].SlantRange
            lft = lft[::-1] # Inverse to work nice
            startrefl_pixels = int(startrefl * len(rgt) / slant_range )
            # print(f'start reflection: {startrefl_pixels}')
            first_reflection = self.estimateFirstReflection(rgt, threshold, startrefl_pixels)
            fish_height = slant_range * first_reflection / len(rgt)

            new_ranges = self.calculateNewDistances(rgt, slant_range, fish_height, first_reflection)
            if len(new_ranges) > 100:
                new_rgt = self.remapChannel(rgt[first_reflection:], new_ranges)
                new_lft = self.remapChannel(lft[first_reflection:], new_ranges)
                new_lft = new_lft[::-1] # Inverse back
                new_slant_range = new_ranges[-1]
                # plt.plot(old_ranges, rgt, label='Raw')
                # plt.plot(new_ranges, rgt[first_reflection:], label='Corrected')
                # plt.show()
                # new_slant_range = new_ranges[-1]
                # plt.plot(new_ranges)
                # plt.plot(np.arange(len(rgt)) * slant_range  / len(rgt))

                # Update slant ranges
                self.sonar_packets[ping_no].ping_chan_headers[0].NumSamples = len(new_ranges)
                self.sonar_packets[ping_no].ping_chan_headers[1].NumSamples = len(new_ranges)

                self.sonar_packets[ping_no].ping_chan_headers[0].SlantRange = new_slant_range
                self.sonar_packets[ping_no].ping_chan_headers[1].SlantRange = new_slant_range
                self.writeSonarLine(ping_no, new_rgt, new_lft)
        self.generateFullImage()

            


    def generateFullImage(self):
        np_chan1 = pyxtf.concatenate_channel(self.sonar_packets,
                                             file_header=self.file_header, channel=0, weighted=True)
        np_chan2 = pyxtf.concatenate_channel(self.sonar_packets,
                                             file_header=self.file_header, channel=1, weighted=True)

        fullImage = np.concatenate((np_chan1, np_chan2), axis=1)
        self.fullImage = (fullImage - np.amin(fullImage)) / (np.amax(fullImage) - np.amin(fullImage))
        # self.rawImage = np.copy(self.fullImage)

        return self.fullImage


    def gammaCorrect(self, gamma):
        self.fullImage = ut.gammaCorrection(self.fullImage, gamma)


    def extractCableOut(self):
        return [self.sonar_packets[i].CableOut
                              for i in range(self.pings_num)]


    def extractTrackWGS84(self) -> np.ndarray:
        """
        Extracts track coordinates for each ping as np array
        """
        y = [self.sonar_packets[i].ShipYcoordinate
                              for i in range(self.pings_num)]
        x = [self.sonar_packets[i].ShipXcoordinate
                              for i in range(self.pings_num)]
        return np.array((x,y)).transpose()
    

    def loadGK(self, coord_array : np.ndarray):
        """
        Load numpy array of GK coordinates
        that must be generated separately with Surfer or smth like that
        """
        x_arr, y_arr = coord_array.transpose()
        if len(x_arr) + len(y_arr) != self.pings_num * 2:
            logging.log('Dimension of GK data is wrong')
            return 0
        for i, x, y in zip(range(len(x_arr)), x_arr, y_arr):
            self.sonar_packets[i].ShipYcoordinateGK = y
            self.sonar_packets[i].ShipXcoordinateGK = x

    def getXYT(self):
        """
        Return array of X Y and time as text
        """
        out_array = []
        for ping_no in range(self.pings_num):
            x = self.sonar_packets[ping_no].ShipXcoordinate
            y = self.sonar_packets[ping_no].ShipYcoordinate
            year = self.sonar_packets[ping_no].Year
            month = self.sonar_packets[ping_no].Month # Month in XTF starts from 0
            day =  self.sonar_packets[ping_no].Day
            hour =  self.sonar_packets[ping_no].Hour
            minute =  self.sonar_packets[ping_no].Minute
            second =  self.sonar_packets[ping_no].Second
            out_array.append(f'{year}/{month}/{day} {hour}:{minute}:{second};{x},{y}')
        return out_array



    def __init__(self, xtf_file):
        (file_header, packets) = pyxtf.xtf_read(xtf_file)
        self.file_header = file_header
        self.sonar_packets = packets[pyxtf.XTFHeaderType.sonar]
        self.left_chan_width = self.sonar_packets[0].data[0].shape[0]
        self.right_chan_width = self.sonar_packets[0].data[1].shape[0]
        self.pings_num = len(self.sonar_packets)
        self.video_files_list = []

        # self.left_chan_ranges = [self.sonar_packets[i].ping_chan_headers[0].SlantRange for i in range(self.pings_num)]
        # self.right_chan_ranges = [self.sonar_packets[i].ping_chan_headers[1].SlantRange for i in range(self.pings_num)]


        # Update HSeconds parameter (hundredths of second) (because it's always zero in our Videomodule XTF files)
        count = 1
        i0 = 0
        for i in range(1, len(self.sonar_packets)):
            if self.sonar_packets[i].Second == self.sonar_packets[i-1].Second:
                count += 1
            else:
                # Update parameter in counted group
                for j in range(i0, i0 + count):
                    self.sonar_packets[j].HSeconds = int((j - i0)*(100/count))
                count = 1
                i0 = i

        # Calculate pings per sec
        t0 = self.getPingTime(0)
        t1 = self.getPingTime(self.pings_num-1)
        t0 = ut.timeToSec(*t0)
        t1 = ut.timeToSec(*t1)
        self.pings_per_sec = self.pings_num/(t1-t0)

        self.generateFullImage()


if __name__ == '__main__':
    xtf_files = glob.glob('test/*.xtf')
    for xtf_file in xtf_files:
        gps_file = '.'.join(xtf_file.split('.')[:-1]) + '.csv'
        sonar_data = SonarData(xtf_file)
        gps = sonar_data.extractTrackWGS84()
        print(gps.shape)
        ut.npToCsv(gps_file, gps)
        # sonar_data.generateFullImage()
        # sonar_data.gammaCorrect(2)
        # image = cv2.resize(sonar_data.fullImage, (300, 600))
        # cv2.imshow(xtf_file, image)
        # cv2.waitKey()
