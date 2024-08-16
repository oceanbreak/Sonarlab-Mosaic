from lib.SonarData import SonarData
import lib.Utils as ut
from lib.io import npToCsv, loadCsvGK
import glob
from skimage import io
from matplotlib import pyplot as plt
import cv2


if __name__ == '__main__':
    xtf_files = glob.glob('test/*.xtf')
    navi_files = glob.glob('test/*GK.csv')
    for xtf_file in xtf_files:
        gps_file = '.'.join(xtf_file.split('.')[:-1]) + '.csv'
        sonar_data = SonarData(xtf_file)
        gps = sonar_data.extractTrackWGS84()
        print(gps.shape)
        npToCsv(gps_file, gps)
        sonar_data.generateFullImage()

        sonar_data.gammaCorrect(2)
        image = cv2.resize(sonar_data.fullImage, (300, 600))
        cv2.imshow(xtf_file, image)
        cv2.waitKey()

        # Load GK
        GK_file = '.'.join(gps_file.split('.')[:-1]) + '-GK.csv'
        GK_coords = loadCsvGK(GK_file)
        sonar_data.loadGK(GK_coords)

        # print(GK_coords.shape)
        # a, b = GK_coords.transpose()
        # print(a)
        # print(b)
        
