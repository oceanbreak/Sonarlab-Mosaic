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
    
    WGS_gsr_header = f'Golden Software Cartographic Reference Information : Version 2.00\n' + \
                        'System Type : GCS\n' + \
                        'System Identification : World Geodetic System 1984\n' + \
                        '  Comment : System Identification strings are subject to change at any time.\n' + \
                        'System GCS Token : GEOGCS_DATUM_WGS84\n' + \
                        'System POSC/EPSG Code : 4326\n' + \
                        'Projection Method : Unprojected Lat/Long\n' + \
                        'Datum Name : World Geodetic System 1984\n' + \
                        'Datum GCS Token : DATUM_WGS84\n' + \
                        'Datum Method : None\n' + \
                        'Datum Ellipsoid Type : WGS 84\n' + \
                        'Datum Ellipsoid GCS Token : ELLIPSOID_WGS_84\n' + \
                        'Datum Ellipsoid Radius (meters) : 6378137\n' + \
                        'Datum Ellipsoid Flattening : 0.00335281066474748\n'


    def __init__(self,):
        pass


    def make(self,  out_file : str, image_coord_margins : np.ndarray):
        with open(out_file, 'w') as fw:
            fw.write(self.header)
            for line in image_coord_margins:
                fw.write(f',{int(line[0])},{int(line[1])},{line[2]},{line[3]},1\n')
        print('Reference file created')


    def makeSurferGeorefWGS84(self, out_file):
        with open(out_file, 'w') as fw:
            fw.write(self.WGS_gsr_header)


if __name__ == '__main__':
    g = Georef('out', (2,3))
    print(g.WGS_gsr_header)