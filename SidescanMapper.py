import pyxtf
import cv2
import numpy as np
import Utils as ut
import logging

class Xtf:

    def getPingTime(self, ping_no):
        year = self.sonar_packets[ping_no].Year
        month = self.sonar_packets[ping_no].Month + 1 # Month in XTF starts from 0
        day =  self.sonar_packets[ping_no].Day
        hour =  self.sonar_packets[ping_no].Hour
        minute =  self.sonar_packets[ping_no].Minute
        second =  self.sonar_packets[ping_no].Second
        hseconds =  self.sonar_packets[ping_no].HSeconds # Hundredths of second

        return np.array((year, month, day, hour, minute, second, hseconds), dtype=np.uint32)


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
        return cv2.resize(cur_frame, (960, 320))


    def getSonarStripe(self, ping_no):
        if 0 <= ping_no < self.pings_num:
            l_chan = self.sonar_packets[ping_no].data[0]
            r_chan = self.sonar_packets[ping_no].data[1]
            return (l_chan, r_chan)
        else:
            return None


    def generateFullImage(self):
        np_chan1 = pyxtf.concatenate_channel(self.sonar_packets,
                                             file_header=self.file_header, channel=0, weighted=True)
        np_chan2 = pyxtf.concatenate_channel(self.sonar_packets,
                                             file_header=self.file_header, channel=1, weighted=True)

        fullImage = np.concatenate((np_chan1, np_chan2), axis=1)
        self.fullImage = (fullImage - np.amin(fullImage)) / (np.amax(fullImage) - np.amin(fullImage))
        self.rawImage = np.copy(self.fullImage)


    def gammaCorrect(self, gamma):
        self.fullImage = ut.gammaCorrection(self.rawImage, gamma)


    def generateDistanceArray(self, base_distance=1.3, GK=False):
        """
        Function generates continuous velues for distance between pings
        based on GPS data in xtf file
        :return: array of distances (meters)
        """
        print('Offset calculation ...')
        y = [self.sonar_packets[i].ShipYcoordinate
                              for i in range(self.pings_num)]
        x = [self.sonar_packets[i].ShipXcoordinate
                              for i in range(self.pings_num)]

        # plt.plot(x,y)
        # plt.show()

        if GK:
            GK_coord = np.zeros((len(y), 2))
            for i in range(len(y)):
                GK_coord[i,:] = ut.GaussKruger(x[i], y[i])
            distance_raw = [0.0] + [ut.getDistance(GK_coord[i,0], GK_coord[i,1], GK_coord[i-1,0], GK_coord[i-1,1])
                            for i in range(1, len(GK_coord))]
        else:
            distance_raw = [0.0] + [ut.haversine((x[i], y[i]), (x[i-1], y[i-1]))
                            for i in range(1, len(self.sonar_packets))]

        distance = np.zeros((len(distance_raw)))
        self.offset = np.zeros((len(distance_raw)))

        # Interpolate distances between pings, where GPS data is constant
        count = 0
        i0 = 0
        for i in range(len(distance_raw)):
            if distance_raw[i] == 0.0:
                count += 1
            else:
                # Update parameter in counted group
                count += 1
                for j in range(i0, i0 + count):
                    distance[j] = distance_raw[i] / count
                count = 0
                i0 = i+1

        # Calculate distance offset for each ping
        for i in range(len(distance)):
            j = i
            dist = 0.0
            time0 = self.sonar_packets[i].Second + self.sonar_packets[i].HSeconds/100
            while dist < base_distance:
                dist += distance[j]
                if j-1 < 0:
                    break
                else:
                    j = j-1
            time1 = self.sonar_packets[j].Second + self.sonar_packets[j].HSeconds/100
            self.offset[i] = (abs(time0 - time1) % 60 )
            logging.debug('Offset array[%i] = %f sec' % (i, self.offset[i]))


    def __init__(self, xtf_file):
        (file_header, packets) = pyxtf.xtf_read(xtf_file)
        self.file_header = file_header
        self.sonar_packets = packets[pyxtf.XTFHeaderType.sonar]
        self.left_chan_width = self.sonar_packets[0].data[0].shape[0]
        self.right_chan_width = self.sonar_packets[0].data[1].shape[0]
        self.pings_num = len(self.sonar_packets)
        self.video_files_list = []

        self.left_chan_ranges = [self.sonar_packets[i].ping_chan_headers[0].SlantRange for i in range(self.pings_num)]
        self.right_chan_ranges = [self.sonar_packets[i].ping_chan_headers[1].SlantRange for i in range(self.pings_num)]


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
        t1 = self.getPingTime(self.pings_num - 156)
        t0 = ut.timeToSec(*t0)
        t1 = ut.timeToSec(*t1)
        self.pings_per_sec = self.pings_num/(t1-t0)

        self.generateDistanceArray()
        self.generateFullImage()


if __name__ == '__main__':
    pass

