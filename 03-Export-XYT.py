# from lib.PictureViewer import PictureViewer

# img = PictureViewer((300, 500), 'Test canvas')
# img.show()

from lib.SonarData import SonarData
import glob
from tkinter.filedialog import askdirectory
import os

path = askdirectory()
xtf_files = glob.glob(os.path.join(path, '*.xtf'))

for xtf_file in xtf_files:

    out_name = xtf_file[:-4] + '.csv'
    sonar_data = SonarData(xtf_file)
    trackout = sonar_data.getXYT()


        

    with open(out_name, 'w') as fw:
        for line in trackout:
            fw.write(';'.join(line.split(';')[1:]) + '\n')
    print('Done')

    cable_out = sonar_data.extractCableOut()
    print(f'Cable out: {cable_out}')

