from lib.MapDrawer import MapDrawer, SonarImageGK
from lib.PictureViewer import PictureViewer
from lib.io import loadCsvGK, npToCsv
from lib.Georef import Georef
from lib.SonarData import SonarData
import numpy as np

TARGET_SCALE = 0.4

def splitTrack(track):
    for cur_pair in track:
        print(cur_pair)

if __name__ == '__main__':

    track_input = loadCsvGK('test/Sonar  2.08.2024 14-49-43-GK.csv')
    print(track_input)
    sonar = SonarData('test/Sonar  2.08.2024 14-49-43.XTF')
    sonar.gammaCorrect(2)
    sonar.loadGK(track_input)

    print(f'Size of inuts: track - {len(track_input)}, sonar - {len(sonar.sonar_packets)}')

    angle = 30
    stripe = sonar.getSonarStripeGK(10,110)
    sonar_image = SonarImageGK(stripe, TARGET_SCALE)
    print(f'Start width, height: {sonar_image.width}, {sonar_image.height}')
    sonar_image.rotate(angle)
    print(f'Width, height after rotation: {sonar_image.width}, {sonar_image.height}')
    

    viewer = PictureViewer('Image', sonar_image.image)
    viewer.show()

    # Create canvas
    canvas_tl = sonar_image.getGKcoordTopLeft()
    canvas_br = sonar_image.getGKcoordBotRight()

    canvas_tl = (canvas_tl[0] - 200, canvas_tl[1])

    mapGK = MapDrawer(TARGET_SCALE)
    mapGK.createCanvas(canvas_tl, canvas_br)
    mapGK.placeStripeOnCanvas(sonar_image)
    img_map = mapGK.getImage()

    viewer = PictureViewer('MAP', img_map)
    viewer.show()

    # viewer = PictureViewer('Alpha', image.alpha)
    # viewer.show()

    # sonar_img = SonarImageGK(sonar_stripes[-1], DIST_SCALE).image   

    exit(0)

    i = 0
    for data, ccord in zip(sonar.sonar_packets, track_input):
        print(i, data.ShipXCoordinateGK, data.ShipYCoordinateGK, " = ", ccord)
        
        stripe = sonar.getSonarStripeGK(i, i+1)
        print(stripe)
        i += 1


    # Split sonar image in stripes
    sonar_stripes = []
    ping_start = 0
    ping_no = 0
    prev_lon, prev_lat = track_input[0]
    for sonar_packet in sonar.sonar_packets[1:]:
        ping_no += 1
        print(f'Ping no {ping_no}')
        lon = sonar_packet.ShipXCoordinateGK
        lat = sonar_packet.ShipYCoordinateGK
        ping_stop = ping_no
        if prev_lon != lon or prev_lat != lat:
            stripe = sonar.getSonarStripeGK(ping_start, ping_stop)
            print(stripe)
            sonar_stripes.append(stripe)
            ping_start = ping_stop
            prev_lat = lat
            prev_lon = lon

    DIST_SCALE = 1

    drawer = MapDrawer()

    sonar_img = SonarImageGK(sonar_stripes[-1], DIST_SCALE).image
    for stripe in sonar_stripes[-2:0:-1]:
        sonar_img = np.vstack((sonar_img, SonarImageGK(stripe, DIST_SCALE).image))
        viewer = PictureViewer('Sonar', sonar_img)
        viewer.show()




    # for stripe in sonar_stripes:
    #     print(stripe)
    # print(len(sonar_stripes))

    

    # stripe = sonar.getSonarStripeGK(20,22)
    # print(stripe)

    # viewer = PictureViewer('Sonar Stripe', stripe.image)
    # viewer.show()



    # Map = MapDrawer()


    # Map.map_scale = 1
    # Map.track = track

    
    # Map.calculateTrackMargins()
    # Map.drawTrack()



    # img = Map.getImage()
    
    # margins = Map.getMarginMaps()

    # print('Margins')
    # print(margins)


    # # Save image
    # image_name = 'test/out.png'
    # ref_name = 'test/out.georef'
    # viewer = PictureViewer('Map', img)
    # viewer.show()
    # viewer.imsave(image_name)

    # g = Georef(ref_name, margins)
    # g.make()

    # Save georef
