from lib.Settings import Settings
from lib.SonarData import SonarData
from lib.Georef import Georef
from lib.io import FileNaming
from lib.GausKruger import GausKruger
from tkinter.filedialog import askdirectory
from lib.MapDrawer import MapDrawer, SonarImageGK
from lib.PictureViewer import PictureViewer
from lib.io import loadCsvGK, npToCsv
from lib.TrackProcess import TrackProcess
import numpy as np
import glob
import os
import cv2
from skimage import io
from matplotlib import pyplot as plt
import rasterio
from rasterio.transform import from_origin



if __name__ == '__main__':

    
    # Initiate settings
    settings = Settings()
    print(settings)
    path = askdirectory(initialdir=settings.directory)
    settings.directory = path
    settings.writefile()


    TARGET_SCALE = settings.map_scale
    MARGIN = settings.map_margins
    CABLE_OUT = settings.cable_out
    CORRECTION_WINDOW = settings.corwindow
    GAMMA = settings.gamma
    SLANT_THRESHOLD = settings.slantthreshold
    FIRST_REFLECTION = settings.startsearchbottom

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
            GK_X, GK_Y, GK_zone = GK.transform_to_gauss_kruger(lat, lon, 12)
            for x, y in zip(GK_X, GK_Y):
                wfile.write(f'{x};{y}\n')
        print(f'Writing file {track_file} done')

# Generate maps
    for xtf_file in xtf_list:
        naming = FileNaming(xtf_file)
        track_GK_file = naming.get_track_GK_name()
        map_file = naming.get_map_name()
        geotiff_file = naming.get_geotiff_name()
        map_georef_file = naming.get_map_georef_name()

        try:
            track_input = loadCsvGK(track_GK_file)
            sonar = SonarData(xtf_file)
        except FileNotFoundError:
            print('Missed files')
            exit(1)

        
        sonar.correctSlantRange(threshold=SLANT_THRESHOLD, startrefl=FIRST_REFLECTION)
        sonar.gammaCorrect(GAMMA)
        sonar.loadGK(track_input)
        sonar_stripes = sonar.splitIntoGKStripes()

        # Get rotations
        track_proc = TrackProcess(sonar_stripes)

        # plt.plot(track_proc.getTrackRotations(), label='Raw')

        
        # Update track rotations
        track_proc.smoothRotations(CORRECTION_WINDOW, 2)
        # plt.plot(track_proc.getTrackRotations(), label='Pre-smoothed')

        # Cable out
        track_proc.inputCableOut(CABLE_OUT)
        track_proc.updateCableOut()
        track_proc.smoothRotations(CORRECTION_WINDOW, 2)
        # plt.plot(track_proc.getTrackRotations(), label='Smoothed after cableout')

        # plt.legend()
        # plt.show()
        
        offseted_track = track_proc.getTrack()
        rotations = track_proc.getTrackRotations()
        print(f'Stripes are {len(sonar_stripes)}, rotations are {len(rotations)}')

        # CALCULATE MARGINS
        print('Processing track')
        TL_coordsGK = []
        BR_coordsGK = []
        stripe_imgs = []

        for stripe, rot, trackpoint in zip(sonar_stripes, rotations, offseted_track):
            stripe_img = SonarImageGK(stripe, TARGET_SCALE)
            stripe_img.updateCenterGK(trackpoint)
            stripe_img.rotate(rot)
            TL_coordsGK.append(stripe_img.getGKcoordTopLeft())
            BR_coordsGK.append(stripe_img.getGKcoordBotRight())
            stripe_imgs.append(stripe_img)

        print('Estimating map limits')
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
        viewer.show(10)

        margins = mapGK.getMarginMaps()

        # cv2.imwrite(map_file, mapGK.getTransparent())
        # io.imsave(map_file, mapGK.getTransparent())
        # print(f'Saved image {map_file}')
        # ref = Georef()
        # ref.make(map_georef_file, margins)

        ### Save GeoTiff
        # Define the coordinates of the corners in the Pulkovo coordinate system
        # Example: (left, bottom, right, top)

        left, right, bottom, top = mapGK.getCornersGK()



        # Define the image dimensions (width, height)
        height, width = mapGK.getImgSize()


        # Calculate the transform (affine transformation matrix)
        transform = from_origin(left, top, (right - left) / width, (top - bottom) / height)
        image0 = mapGK.getTransparent()
        # MOVE CHANNEL AXES (RGB) to the beginning
        image = np.moveaxis(image0.squeeze(),-1,0)

        # Write the GeoTIFF file
        with rasterio.open(
            geotiff_file,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=4,  # Number of bands
            dtype=image.dtype,
            crs=f'EPSG:{28400 + GK_zone}',  # Pulkovo 1942 coordinate system (example, adjust as needed)
            transform=transform
        ) as dst:
            print(type(dst))
            dst.write(image)  # Write the image data to the first band

        print(f"GeoTIFF file saved as {geotiff_file}")


        

