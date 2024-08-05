from lib.Xtf import Xtf
import lib.Utils as ut
from lib.io import npToCsv
import glob


if __name__ == '__main__':
    xtf_files = glob.glob('test/*.xtf')
    navi_files = glob.glob('test/*GK.csv')
    for xtf_file in xtf_files:
        gps_file = '.'.join(xtf_file.split('.')[:-1]) + '.csv'
        sonar_data = Xtf(xtf_file)
        gps = sonar_data.extractTrackWGS84()
        print(gps.shape)
        npToCsv(gps_file, gps)
        # sonar_data.generateFullImage()
        # sonar_data.gammaCorrect(2)
        # image = cv2.resize(sonar_data.fullImage, (300, 600))
        # cv2.imshow(xtf_file, image)
        # cv2.waitKey()
