from lib.Settings import Settings
from lib.SonarData import SonarData
from lib.Georef import Georef
from lib.io import FileNaming
from lib.GausKruger import GausKruger
import os
from tkinter.filedialog import askdirectory
import glob



if __name__ == '__main__':

    
    # Initiate settings
    settings = Settings()
    print(settings)
    path = askdirectory(initialdir=settings.directory)
    settings.directory = path
    settings.writefile()
    print(settings)

    # Load XTF files
    xtf_list = glob.glob(os.path.join(settings.directory, '*.xtf'))
    print(xtf_list)

    # Process data
    for xtf_file in xtf_list:
        naming = FileNaming(xtf_file)
        # track_file = '.'.join(xtf_file.split('.')[:-1]) + '.csv'
        # georef = track_file + '.gsr2'
        track_file = naming.get_track_WGS_name()
        track_GK_file = naming.get_track_GK_name()
        georef = naming.get_track_georef_name()

        sonar_data = SonarData(xtf_file)
        track = sonar_data.extractTrackWGS84()
        with open(track_file, 'w') as wfile:
            for line in track:
                wfile.write(f'{line[0]};{line[1]}\n')
        print(f'Writing file {track_file} done')
        gr = Georef()
        gr.makeSurferGeorefWGS84(georef)

        # Gauss Kruger
        GK = GausKruger()
        with open(track_GK_file, 'w') as wfile:
            lon = track[:,0]
            lat = track[:,1]
            GK_X, GK_Y, zone = GK.transform_to_gauss_kruger(lat, lon, 12)
            for x, y in zip(GK_X, GK_Y):
                wfile.write(f'{x};{y}\n')
        print(f'Writing file {track_file} done')

    