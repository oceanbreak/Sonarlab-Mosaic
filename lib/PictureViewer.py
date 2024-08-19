""""
Module for showing pictures
with ability to change scale
"""

import cv2
import numpy as np
from lib.SonarData import SonarData


class PictureViewer:

    def __init__(self, image_name : str, image : np.ndarray):
        self._image_name = image_name
        self._image_width = image.shape[1]
        self._image_height = image.shape[0]
        self._image = image
        self._is_showed = False

        # Scaling properties
        self.scale = 1.0

    def reduceScale(self):
        if self.scale > 0.2:
            self.scale -= 0.1

    def plusScale(self):
        self.scale += 0.1

    def updateScale(self):
        return cv2.resize(self._image, (int(self._image_width * self.scale), 
                                         int(self._image_height * self.scale)))

    def show(self, delay=0):
        self._is_showed = True
        while self._is_showed:
            show_canvas = self.updateScale()
            cv2.imshow(self._image_name, show_canvas)
            self.keyHandler(delay)

    def keyHandler(self, delay):
        if delay != 0:
            cv2.waitKey(delay)
            self._is_showed = False
            return
        resp = cv2.waitKey()
        if resp & 0xFF == 27:
            self._is_showed = False
        try:
            if chr(resp) in ('w', 'W'):
                self.plusScale()
            if chr(resp) in ('s', 'S'):
                self.reduceScale()
        except:
            pass


    def imsave(self, output_file):
        cv2.imwrite(output_file, self._image)
        