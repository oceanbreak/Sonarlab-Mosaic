from lib.MapDrawer import MapDrawer, SonarImageGK
from lib.PictureViewer import PictureViewer
from lib.io import loadCsvGK, npToCsv
from lib.Georef import Georef
from lib.SonarData import SonarData
from lib.TrackSmoother import TrackSmoother
import numpy as np
import cv2

TARGET_SCALE = 1.4
MARGIN = 10 # for map canvas, meters

if __name__ == '__main__':

    track_input = loadCsvGK('test/Sonar  2.08.2024 14-49-43-GK.csv')
    sonar = SonarData('test/Sonar  2.08.2024 14-49-43.XTF')
    sonar.gammaCorrect(2)
    sonar.loadGK(track_input)



    sonar_stripes = sonar.splitIntoGKStripes()

    # Get rotations
    smoother = TrackSmoother(sonar_stripes)
    # smoother.smoothTrack(3)
    smoother.getTrackRotations()
    rotations = smoother.smoothRotations(33, 2)
    
    print(f'Stripes are {len(sonar_stripes)}, rotations are {len(rotations)}')



    # CALCULATE MARGINS

    # sonar_img = SonarImageGK(sonar_stripes[-1], DIST_SCALE).image
    TL_coordsGK = []
    BR_coordsGK = []
    stripe_imgs = []
    for stripe, rot in zip(sonar_stripes, rotations):
        # print(stripe)
        stripe_img = SonarImageGK(stripe, TARGET_SCALE)
        stripe_img.rotate(rot)
        TL_coordsGK.append(stripe_img.getGKcoordTopLeft())
        BR_coordsGK.append(stripe_img.getGKcoordBotRight())
        stripe_imgs.append(stripe_img)

    print(np.array(TL_coordsGK).shape)
    TL_np = np.array(TL_coordsGK)
    BR_np = np.array(BR_coordsGK)

    Map_topY = np.max(TL_np[:,1]) + MARGIN
    Map_leftX = np.min(TL_np[:,0]) - MARGIN
    Map_rgtX = np.max(BR_np[:,0]) + MARGIN
    Map_botY = np.min(BR_np[:,1]) - MARGIN

    print(f"TL corner: {Map_leftX}, {Map_topY}, BR corner: {Map_rgtX}, {Map_botY}")

    mapGK = MapDrawer(TARGET_SCALE)
    mapGK.createCanvas((Map_leftX, Map_topY), (Map_rgtX, Map_botY))

    for i, stripe in enumerate(stripe_imgs):
        mapGK.placeStripeOnCanvas(stripe)

    viewer = PictureViewer('Map', mapGK.getImage())
    viewer.show()

    margins = mapGK.getMarginMaps()

    cv2.imwrite('test/test_GK_sonar.png', mapGK.getTransparent())
    ref = Georef('test/test_GK_sonar.georef', margins)
    ref.make()

    

