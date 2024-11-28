import numpy as np
import os

class FileNaming:

    def __init__(self, xtf_file):
        self.xtf_file_name = xtf_file

    def get_xtf_name(self):
        return self.xtf_file_name
    
    def get_track_WGS_name(self):
        return '.'.join(self.xtf_file_name.split('.')[:-1]) + '.csv'
    
    def get_track_GK_name(self):
        return '.'.join(self.xtf_file_name.split('.')[:-1]) + '-GK.csv'
    
    def get_track_georef_name(self):
        return self.get_track_WGS_name() + '.gsr2'
    
    def get_map_name(self):
        return '.'.join(self.xtf_file_name.split('.')[:-1]) + '_mosaic.png'
    
    def get_map_georef_name(self):
        return self.get_map_name() + '.georef'
    




def npToCsv(out_name : str, array : np.ndarray):
    """
    Write np array to csv
    """
    if len(array.shape) != 2:
        print('Dimensions must be 2')
    with open(out_name, 'w') as f_write:
        for i in range(array.shape[0]):
            line_list = [str(array[i,j]) for j in range(array.shape[1])]
            f_write.write(';'.join(line_list) + '\n')
    print(f'{out_name} write successfully')


def loadCsvGK(in_name : str, delimeter=';') -> np.ndarray:
    """
    Loading Csv for pair of coordinates in Gauss Kruger
    """
    x = []
    y = []
    with open(in_name, 'r') as f_read:
        for line in f_read:
            line = line.strip()
            # Replace , with .
            line = '.'.join(line.split(','))
            in_x, in_y = line.split(delimeter)
            x.append(float(in_x))
            y.append(float(in_y))

    return np.array([x,y]).transpose()

def loadCsvWGS(in_name : str, delimeter=';') -> np.ndarray:
    """
    Loading Csv for pair of coordinates in Gauss Kruger
    """
    x = []
    y = []
    with open(in_name, 'r') as f_read:
        for line in f_read:
            line = line.strip()
            in_x, in_y = line.split(delimeter)
            x.append(float(in_x))
            y.append(float(in_y))

    return np.array([x,y]).transpose()


