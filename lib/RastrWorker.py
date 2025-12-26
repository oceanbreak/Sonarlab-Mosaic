import numpy as np
from PySide6.QtCore import QObject, Signal, Slot
# import time
import numpy as np
import glob
from skimage import io
from matplotlib import pyplot as plt
from lib.RASTR_Reader import *
from tkinter.filedialog import askopenfile
from lib.RASTR_Struct import DataStructure
import ctypes
import os
import pyxtf
import builtins
from tkinter.filedialog import askdirectory
import traceback
from lib.Settings import Settings


class RastrWorker(QObject):
    status = Signal(str)
    # image = Signal(np.ndarray)
    finished = Signal()
    cancelled = Signal()

    def __init__(self, settings : Settings):
        super().__init__()
        self._abort = False

        self.settings = settings


    def abort(self):
        self._abort = True
        # raise RuntimeError

    def process(self):
        self._abort = False
        try:
            self._process()
            self.finished.emit()
        except BaseException as e:
            # This block catches the exception
            self.status.emit(f"An exception occurred: {e}\nException type: {type(e).__name__}") # Prints a user-friendly message and the error message
            traceback.print_exc()
            self.cancelled.emit()


    @Slot(str)
    def _process(self):
        file_path = self.settings.directory
        RASTR_files = glob.glob(os.path.join(file_path, "*.lft")) 
        for rastr_file_index, RASTR_file in enumerate(RASTR_files):
            base_string = f'Processing {rastr_file_index + 1} of {len(RASTR_files)} files - {RASTR_file}:\n'
            self.status.emit(f'{base_string}')
            if self._abort:
                self.cancelled.emit()
                return
            data_struct = DataStructure(RASTR_file)
            nv = NV_Reader(data_struct.n_v)

            # Работаем с левым каналом
            rastr_lft = RASTR_Reader(data_struct.lft)
            rastr_lft.readFile()
            data_lft = rastr_lft.getFileData()
            block_times = rastr_lft.getBlockTimes()
            block_sizes = rastr_lft.getBlockSizes()

            # Работаем с правым каналом
            rastr_rgt = RASTR_Reader(data_struct.rgt)
            rastr_rgt.readFile()
            data_rgt = rastr_rgt.getFileData()
            
            nv_reader = NV_Reader(data_struct.n_v)
            nv_reader.readFile()
            nv_data = nv_reader.getData()
            n_v_length = len(nv_data)
            repeated_coordinates_list = nv_reader.process_coordinates(block_times, block_sizes)

            output_file_name = data_struct.base_name + '.xtf'

            # Initialize file header
            fh = pyxtf.XTFFileHeader()
            fh.SonarName = b'RastrtoXTF'
            fh.SonarType = pyxtf.XTFSonarType.unknown1
            fh.NavUnits = pyxtf.XTFNavUnits.latlon.value
            fh.NumberOfSonarChannels = 2

            # Port chaninfo
            fh.ChanInfo[0].TypeOfChannel = pyxtf.XTFChannelType.port.value
            fh.ChanInfo[0].SubChannelNumber = 0
            fh.ChanInfo[0].BytesPerSample = 1
            fh.ChanInfo[0].SampleFormat = pyxtf.XTFSampleFormat.byte.value

            # Stbd chaninfo
            fh.ChanInfo[1].TypeOfChannel = pyxtf.XTFChannelType.stbd.value
            fh.ChanInfo[1].SubChannelNumber = 1
            fh.ChanInfo[1].BytesPerSample = 1
            fh.ChanInfo[1].SampleFormat = pyxtf.XTFSampleFormat.byte.value
            
            pings = []
            f = zip(data_lft, data_rgt)
            repeated_coordinates = [coord for block in repeated_coordinates_list for coord in block]
            glob_pos_index = 0

            for dat__block_lft, dat_block_rgt in f:
                head_lft = dat__block_lft[0]
                strings_lft = dat__block_lft[1]
                head_rgt = dat_block_rgt[0]
                strings_rgt = dat_block_rgt[1]

                # Получаем параметры из заголовка
                sec = head_lft.getItem('sec')
                min = head_lft.getItem('min')
                hour = head_lft.getItem('hour')
                day = head_lft.getItem('day')
                month = head_lft.getItem('month')
                year = head_lft.getItem('year')
                string_size = head_lft.getItem('string_size')
                string_number = head_lft.getItem('string_number')
                frequency = head_lft.getItem('frequency')
                
                for j in range(string_number):
                    p = pyxtf.XTFPingHeader()
                    s_r = (1500 * string_size) / (2 * frequency)
                    p.HeaderType = pyxtf.XTFHeaderType.sonar.value
                    p.NumChansToFollow = 2
                    p.Year = year
                    p.Month = month
                    p.Day = day 
                    p.Hour = hour
                    p.Minute = min
                    p.Second = sec
                    p.PingNumber = j
                    p.SoundVelocity = 1500
                    p.WaterTemperature = 8
                    p.FixTimeHour = hour
                    p.FixTimeMinute = min
                    p.FixTimeSecond = sec
                    p.SensorSpeed = 1.5
                    if repeated_coordinates:  
                        p.ShipXcoordinate = repeated_coordinates[glob_pos_index][1]  # Долгота
                        p.ShipYcoordinate = repeated_coordinates[glob_pos_index][0]  # Широта
                        p.SensorXcoordinate = repeated_coordinates[glob_pos_index][1] 
                        p.SensorYcoordinate = repeated_coordinates[glob_pos_index][0]
                        glob_pos_index += 1
                    else:
                        self.status.emit(f'{base_string}No coordinate available for string {j}.')
                    
                    p.SensorPrimaryAltitude = 10
                    p.SensorPitch = 15
                    p.SensorRoll = 0
                    p.SensorHeading = 45
                    # Setup ping chan headers
                    c = (pyxtf.XTFPingChanHeader(), pyxtf.XTFPingChanHeader())
                    c[0].ChannelNumber = 0
                    c[0].SlantRange = s_r
                    c[0].Frequency = 80
                    c[0].NumSamples = string_size
                    c[1].ChannelNumber = 1
                    c[1].SlantRange = s_r
                    c[1].Frequency = 80
                    c[1].NumSamples = string_size

                    p.ping_chan_headers = c
                    mirrored_lft_string = np.flip(strings_lft[j])
                    p.data = [mirrored_lft_string, strings_rgt[j]]
                    # Set packet size
                    sz = ctypes.sizeof(pyxtf.XTFPingHeader)                            
                    sz += ctypes.sizeof(pyxtf.XTFPingChanHeader) * 2
                    sz += len(strings_lft[j]) + len(strings_rgt[j])
                    p.NumBytesThisRecord = sz
                    pings.append(p)
                    
                # Запись в файл
                with open(output_file_name, 'wb') as f:
                    f.write(fh.to_bytes())
                    for p in pings:
                        f.write(p.to_bytes())
        self.status.emit("RASTR to XTF converting finished")
