import numpy as np
from PySide6.QtCore import QObject, Signal, Slot
# import time
import gc
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
import glob
import os
import cv2
from skimage import io
from matplotlib import pyplot as plt
import rasterio
from rasterio.transform import from_origin
import traceback


class MosaicWorker(QObject):
    status = Signal(str)
    image = Signal(np.ndarray)
    finished = Signal()
    cancelled = Signal()

    def __init__(self, settings : Settings):
        super().__init__()
        self._abort = False

        self.settings = settings

    # @Slot(str)
    # def process(self):
    #     self._abort = False
    #     self.status.emit("Reading XTF files...")

    #     for i in range(5):
    #         if self._abort:
    #             self.status.emit("Processing cancelled")
    #             self.cancelled.emit()
    #             return

    #         time.sleep(1)  # simulate heavy work

    #         img = np.random.randint(0, 255, (200, 400), dtype=np.uint8)
    #         self.image.emit(img)
    #         self.status.emit(f"Processing step {i + 1}/5")

    #     self.status.emit("Processing finished")
    #     self.finished.emit()

    def abort(self):
        self._abort = True
        # raise RuntimeError

    def process(self):
        self._abort = False
        try:
            self._process()
            self.finished.emit()
        except BaseException as e:
            # This block catches the exception
            self.status.emit(f"An exception occurred: {e}\nException type: {type(e).__name__}") # Prints a user-friendly message and the error message
            traceback.print_exc()
            self.cancelled.emit()


    @Slot(str)
    def _process(self):
        self.image.emit(None)

        # Load XTF files
        xtf_list = glob.glob(os.path.join(self.settings.directory, '*.xtf'))
        # print(xtf_list)
        self.status.emit('\n'.join(xtf_list))

        # Process data
        for xtf_file in xtf_list:
            if self._abort:
                self.status.emit("Processing cancelled")
                self.cancelled.emit()
                return

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
            self.status.emit(f'Writing file {track_file} done')
            gr = Georef()
            gr.makeSurferGeorefWGS84(georef)

            # Gauss Kruger
            GK = GausKruger()
            with open(track_GK_file, 'w') as wfile:
                lon = track[:,0]
                lat = track[:,1]
                GK_X, GK_Y, GK_zone = GK.transform_to_gauss_kruger(lat, lon)
                for x, y in zip(GK_X, GK_Y):
                    wfile.write(f'{x};{y}\n')
            self.status.emit(f'Writing file {track_file} done')

    # Generate maps
        for xtf_index, xtf_file in enumerate(xtf_list):
            status_head = f'File {xtf_index + 1} of {len(xtf_list)} - {xtf_file}:\n'
            if self._abort:
                self.status.emit("Processing cancelled")
                self.cancelled.emit()
                return
            naming = FileNaming(xtf_file)
            track_GK_file = naming.get_track_GK_name()
            map_file = naming.get_map_name()
            geotiff_file = naming.get_geotiff_name()
            map_georef_file = naming.get_map_georef_name()

            try:

                track_input = loadCsvGK(track_GK_file)
                sonar = SonarData(xtf_file)
            except FileNotFoundError:
                self.status.emit(f'{status_head}Missed files')
                self.cancelled.emit()
                return

            if self.settings.correct_slantrange:
                self.status.emit(f'{status_head}Applying slant range correction')
                sonar.correctSlantRange(self.settings.startsearchbottom,
                                        self.settings.debug,
                                        self.settings.corsltrng_searchwindow,
                                        self.settings.corsltrng_frst_refl_bias)
            sonar.gammaCorrect(self.settings.gamma)
            sonar.loadGK(track_input)
            sonar_stripes = sonar.splitIntoGKStripes()

            # Get rotations
            track_proc = TrackProcess(sonar_stripes)

            # plt.plot(track_proc.getTrackRotations(), label='Raw')

            
            # Update track rotations
            track_proc.smoothRotations(self.settings.corwindow, 2)
            # plt.plot(track_proc.getTrackRotations(), label='Pre-smoothed')

            # Cable out
            track_proc.inputCableOut(self.settings.cable_out)
            track_proc.updateCableOut()
            track_proc.smoothRotations(self.settings.corwindow, 2)

            
            offseted_track = track_proc.getTrack()
            rotations = track_proc.getTrackRotations()
            self.status.emit(f'{status_head}Stripes are {len(sonar_stripes)}, rotations are {len(rotations)}')

            # CALCULATE MARGINS
            self.status.emit(f'{status_head}Processing track')
            TL_coordsGK = []
            BR_coordsGK = []

            for stripe, rot, trackpoint in zip(sonar_stripes, rotations, offseted_track):
                stripe_img = SonarImageGK(stripe, self.settings.map_scale, self.settings.stripescale)
                stripe_img.updateCenterGK(trackpoint)
                stripe_img.rotate(rot)
                TL_coordsGK.append(stripe_img.getGKcoordTopLeft())
                BR_coordsGK.append(stripe_img.getGKcoordBotRight())
                # stripe_imgs.append(stripe_img)
                # del stripe_img
                # gc.collect()

            # print('Estimating map limits')
            TL_np = np.array(TL_coordsGK)
            BR_np = np.array(BR_coordsGK)

            Map_topY = np.max(TL_np[:,1]) + self.settings.map_margins
            Map_leftX = np.min(TL_np[:,0]) - self.settings.map_margins
            Map_rgtX = np.max(BR_np[:,0]) + self.settings.map_margins
            Map_botY = np.min(BR_np[:,1]) - self.settings.map_margins

            self.status.emit(f"{status_head}TL corner: {Map_leftX}, {Map_topY}, BR corner: {Map_rgtX}, {Map_botY}")

            mapGK = MapDrawer(self.settings.map_scale)
            mapGK.createCanvas((Map_leftX, Map_topY), (Map_rgtX, Map_botY))

            self.status.emit(f"{status_head}Building mosaic...")

            for stripe, rot, trackpoint in zip(sonar_stripes, rotations, offseted_track):
                stripe_img = SonarImageGK(stripe, self.settings.map_scale, self.settings.stripescale)
                stripe_img.updateCenterGK(trackpoint)
                stripe_img.rotate(rot)
                mapGK.placeStripeOnCanvas(stripe_img)

            # viewer = PictureViewer('Map', mapGK.getImage())
            self.image.emit(mapGK.getImage())
            # viewer.show(10)

            margins = mapGK.getMarginMaps()

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
                self.status.emit(type(dst))
                dst.write(image)  # Write the image data to the first band

            self.status.emit(f"GeoTIFF file saved as {geotiff_file}")
            del sonar
            del image
            del sonar_stripes
            del mapGK
            # del stripe_imgs
            # del viewer
            gc.collect()
        self.status.emit("Processing finished")
        return