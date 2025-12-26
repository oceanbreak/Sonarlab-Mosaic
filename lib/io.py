import numpy as np
import os

class FileNaming:

    proc_name = 'proc'
    out_name = 'mosaic'

    def __init__(self, xtf_file):
        self.xtf_file_name = xtf_file
        path, fname = os.path.split(xtf_file)
        self.base_path = path
        self.base_name = fname

        # add folders
        self.proc_folder = os.path.join(self.base_path, 'proc')
        self.output_folder = os.path.join(self.base_path, 'mosaic')

        self.createFolders()

    def get_xtf_name(self):
        return self.xtf_file_name
    
    def get_track_WGS_name(self):
        outputfile =  '.'.join(self.base_name.split('.')[:-1]) + '.csv'
        return os.path.join(self.proc_folder, outputfile)
    
    def get_bottom_file_name(self):
        outputfile =  '.'.join(self.base_name.split('.')[:-1]) + '_Bottom_data.csv'
        return os.path.join(self.proc_folder, outputfile)
    
    def get_track_GK_name(self):
        outputfile =  '.'.join(self.base_name.split('.')[:-1]) + '-GK.csv'
        return os.path.join(self.proc_folder, outputfile)
    
    def get_track_georef_name(self):
        return self.get_track_WGS_name() + '.gsr2'
    
    def get_map_name(self):
        outputfile =  '.'.join(self.base_name.split('.')[:-1]) + '_mosaic.png'
        return os.path.join(self.output_folder, outputfile)
    
    def get_geotiff_name(self):
        outputfile =  '.'.join(self.base_name.split('.')[:-1]) + '_mosaic.tif'
        return os.path.join(self.output_folder, outputfile)
    
    def get_map_georef_name(self):
        return self.get_map_name() + '.georef'
    

    def createFolders(self):
        if not os.path.exists(self.proc_folder):
            os.mkdir(self.proc_folder)
        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)
    


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


