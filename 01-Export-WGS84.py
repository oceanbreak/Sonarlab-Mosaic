from lib.Settings import Settings
from lib.SonarData import SonarData
from lib.Georef import Georef
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
    xtf_list = glob.glob(os.path.join(settings.directory, '*.xtf')) + \
                glob.glob(os.path.join(settings.directory, '*.XTF'))
    print(xtf_list)

    # Process data
    for xtf_file in xtf_list:
        track_file = '.'.join(xtf_file.split('.')[:-1]) + '.csv'
        georef = track_file + '.gsr2'
        sonar_data = SonarData(xtf_file)
        track = sonar_data.extractTrackWGS84()
        with open(track_file, 'w') as wfile:
            for line in track:
                wfile.write(f'{line[0]};{line[1]}\n')
        print(f'Writing file {track_file} done')
        gr = Georef()
        gr.makeSurferGeorefWGS84(georef)

    