""""
Module to generate Surfer Georeference file 
for output image
"""

import numpy as np

class Georef:

    header = f'Surfer Georeference Control Point File\n' \
                'Version=1\n' \
                'Method=3\n' \
                'Name,Raster X,Raster Y,Longitude,Latitude,Active\n'

    def __init__(self, out_file : str, image_coord_margins : np.ndarray):
        self.image_coord_margins = image_coord_margins
        self.out_file_name = out_file

    def make(self):
        with open(self.out_file_name, 'w') as fw:
            fw.write(self.header)
            for line in self.image_coord_margins:
                fw.write(f',{int(line[0])},{int(line[1])},{line[2]},{line[3]},1\n')
        print('Reference file created')


