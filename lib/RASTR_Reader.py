import numpy as np
from lib.RASTR_Struct import *
import re
from datetime import datetime

class RASTR_Reader:

    def __init__(self, filename, byteorder='little'):
        self.__filename = filename
        self.__current_position = 0
        self.__file = open(filename, 'rb')
        self.__byteorder = byteorder
        self.__rastr_header = None
        self.__rastr_data = []
        self.__rastr_image = None
        self.block_count = 0
        self.block_times = []
        self.block_sizes = []

    def readFile(self):
        self.__jumpTo(0)
        file_data = []
        fheader = self.__readFileHeader()
        self.__rastr_header = fheader
        cur_pos = self.__tellCurPos()
        
        while True:
            self.__jumpTo(cur_pos)
            block_header = self.__readBlockHeader()
            str_size = block_header.getItem('string_size')
            str_num = block_header.getItem('string_number')
            cur_block_size = block_header.getItem('current_data_size')
            cur_pos = cur_pos + cur_block_size
            
            if cur_block_size == 0:
                break

            self.block_sizes.append(str_num)

            time_stamp = self.__getBlockTime(block_header)
            self.block_times.append(time_stamp)

            data = self.__readDataBLock(str_num, str_size)

            if self.__rastr_image is None:
                self.__rastr_image = data
            else:
                self.__rastr_image = np.vstack((self.__rastr_image, data))

            file_data.append([block_header, data])

        self.__rastr_data = file_data
        self.__closeFile()
    
    def getImage(self):
        return self.__rastr_image
    
    def getFileHeader(self):
        return self.__rastr_header

    def getBlockSizes(self):
        return self.block_sizes

    def getFileData(self):
        return self.__rastr_data

    def getBlockTimes(self):
        return self.block_times 

    def __getBlockTime(self, block_header):
        year = block_header.getItem('year')
        month = block_header.getItem('month')
        day = block_header.getItem('day')
        hour = block_header.getItem('hour')
        minute = block_header.getItem('min')
        second = block_header.getItem('sec')
        return f"{hour:02d}:{minute:02d}:{second:02d}"

    def __readFileHeader(self):
        RFH = RastrFileHeader()
        RFH.writeItem('password', self.__readInt(2))
        RFH.writeItem('version', self.__readChars(4))
        RFH.writeItem('coding_mode', self.__readInt(2))
        RFH.writeItem('FILE_TITLE_size', self.__readInt(2))
        RFH.writeItem('BLOCK_TITLE_size', self.__readInt(2))
        if RFH.items['FILE_TITLE_size'] == 126:
            RFH.writeItem('begin_time', self.__readChars(16))
        elif RFH.items['FILE_TITLE_size'] == 130:
            RFH.writeItem('begin_time', self.__readChars(20)) 
        RFH.writeItem('device', self.__readChars(6))
        RFH.writeItem('report', self.__readChars(92))
        return RFH
    
    def __readBlockHeader(self):
        RBH = RastrBlockHeader()
        RBH.writeItem('device', self.__readInt(2))
        RBH.writeItem('current_data_size', self.__readInt(4))
        RBH.writeItem('previous_data_size', self.__readInt(4))
        RBH.writeItem('sec', self.__readInt(2))
        RBH.writeItem('min', self.__readInt(2))
        RBH.writeItem('hour', self.__readInt(2))
        RBH.writeItem('day', self.__readInt(2))
        RBH.writeItem('month', self.__readInt(2))
        RBH.writeItem('year', self.__readInt(2))
        RBH.writeItem('delta_time', self.__readInt(2))
        RBH.writeItem('string_size', self.__readInt(2))
        RBH.writeItem('string_number', self.__readInt(2))
        RBH.writeItem('frequency', self.__readInt(2))
        # Read Buffer
        _ = self.__readDummy(100)
        self.block_count += 1

        return RBH
    
    def __readDataBLock(self, string_num, string_size):
        buffer = self.__file.read(string_num * string_size)
        DB = np.frombuffer(buffer, dtype=np.uint8).reshape(string_num, string_size)
        self.__current_position += string_num * string_size
        return DB

    def __readInt(self, numbytes):
        val = self.__file.read(numbytes)
        self.__current_position += numbytes
        return int.from_bytes(val, self.__byteorder)
    
    def __readChars(self, numbytes):
        val = self.__file.read(numbytes)
        self.__current_position += numbytes
        return val.decode('ASCII')
    
    def __readDummy(self, numbytes):
        val = self.__file.read(numbytes)
        self.__current_position += numbytes

    def __jumpTo(self, byte_index):
        self.__file.seek(byte_index)
        self.__current_position = byte_index

    def __tellCurPos(self):
        return self.__file.tell()
    
    def getBlockCount(self):
        return self.block_count

    def __closeFile(self):
        self.__file.close()

class NV_Reader:
    def __init__(self, filename, ):
        self.__filename = filename
        self.__n_v_data = []

    def readFile(self):
        with open(self.__filename, 'rt') as fread:
            for line in fread:
                data = self.__splitData(line)
                self.__n_v_data.append(self.__readNavLine(data))
    
    def getData(self):
        return self.__n_v_data
    
    def __readNavLine(self, data):
        n_v_line = RastrNavLine()
        n_v_line.writeItem('lattitude',
                           self.__convertCoordStringToDegree(data[13]))
        n_v_line.writeItem('longtitude',
                           self.__convertCoordStringToDegree(data[15]))
        n_v_line.writeItem('sec', data[19])
        n_v_line.writeItem('min', data[18])
        n_v_line.writeItem('hour', data[17])
        n_v_line.writeItem('day', data[22])
        n_v_line.writeItem('month', data[21])
        n_v_line.writeItem('year', data[20])
        return n_v_line

    def __splitData(self, line):
        return re.split(":|,|/| |\n", line)
    
    def __convertCoordStringToDegree(self, coord_string):
        if len(coord_string.split('.')[0]) == 4:
            floats = np.array([coord_string[0:2], coord_string[2:11]], dtype=float)
            x = floats[1] / float(60)
            return floats[0] + x
        elif len(coord_string.split('.')[0]) == 5:
            floats = np.array([coord_string[0:3], coord_string[3:12]], dtype=float)
            x = floats[1] / float(60)
            return floats[0] + x
            
        else:
            print(f'Unknown coord type: {coord_string}')
            raise ValueError
    
    def convert_time_to_seconds(self, time_str):
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60 + seconds
    
    def interpolate_coordinates(self, latitudes, longitudes, num_points):
        latitudes_interp = np.interp(np.linspace(0, len(latitudes) - 1, num_points), 
                                    np.arange(len(latitudes)), latitudes)
        longitudes_interp = np.interp(np.linspace(0, len(longitudes) - 1, num_points), 
                                    np.arange(len(longitudes)), longitudes)
        
        latitudes_interp = np.round(latitudes_interp, 6)
        longitudes_interp = np.round(longitudes_interp, 6)

        return list(zip(latitudes_interp, longitudes_interp))
        
    def process_coordinates(self, block_times, block_sizes):
        repeated_coordinates_list = []
        all_coordinates = []
        n_v_length = len(self.__n_v_data)

        for nv_index in range(n_v_length):
            current_time = f"{self.__n_v_data[nv_index].getItem('hour')}:{self.__n_v_data[nv_index].getItem('min')}:{self.__n_v_data[nv_index].getItem('sec')[:-3]}"            
            coord = (self.__n_v_data[nv_index].getItem('lattitude'), self.__n_v_data[nv_index].getItem('longtitude'))
            all_coordinates.append((current_time, coord))

        previous_block_end_coord = None 

        for index in range(len(block_sizes)):
            block_size = block_sizes[index]
            block_time = block_times[index]
            next_block_time = block_times[index + 1] if index + 1 < len(block_times) else None
            
            block_time_seconds = self.convert_time_to_seconds(block_time)
            next_block_time_seconds = self.convert_time_to_seconds(next_block_time) if next_block_time else float('inf')
            
            coordinates_block = []
            for time, coord in all_coordinates:
                current_time_seconds = self.convert_time_to_seconds(time)
                if block_time_seconds <= current_time_seconds < next_block_time_seconds:
                    coordinates_block.append(coord)

            if coordinates_block:
                coords_to_interpolate = []
                
                if previous_block_end_coord is not None:
                    coords_to_interpolate.append(previous_block_end_coord)
                coords_to_interpolate.append(coordinates_block[0])  

                for i in range(len(coordinates_block)):
                    coords_to_interpolate.append(coordinates_block[i])
                coords_to_interpolate.append(coordinates_block[-1])  

                latitudes = [c[0] for c in coords_to_interpolate]
                longitudes = [c[1] for c in coords_to_interpolate]

                repeated_coordinates = self.interpolate_coordinates(latitudes, longitudes, block_size)
                repeated_coordinates_list.append(repeated_coordinates)
                
                previous_block_end_coord = coordinates_block[-1]

        return repeated_coordinates_list
