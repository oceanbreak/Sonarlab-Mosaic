""""
Module for plotting sonar data
based in rectangular coordinates
"""

import cv2
import numpy as np
from lib.Xtf import Xtf
from lib.Navigation import Navigation

class PictureViewer:

    def __init__(self, canvas_size : tuple, canvas_name : str):
        self._canvas_name = canvas_name
        self._canvas_width = canvas_size[0]
        self._canvas_height = canvas_size[1]
        self._canvas = np.zeros((self._canvas_height, self._canvas_width)).astype(np.uint8)
        self._is_showed = False

        # Scaling properties
        self.scale = 1.0

    def reduceScale(self):
        if self.scale > 0.2:
            self.scale -= 0.1

    def plusScale(self):
        self.scale += 0.1

    def updateScale(self):
        return cv2.resize(self._canvas, (int(self._canvas_width * self.scale), 
                                         int(self._canvas_height * self.scale)))

    def show(self):
        self._is_showed = True
        while self._is_showed:
            show_canvas = self.updateScale()
            cv2.imshow(self._canvas_name, show_canvas)
            self.keyHandler()

    def keyHandler(self):
        resp = cv2.waitKey()
        if resp & 0xFF == 27:
            self._is_showed = False
        if chr(resp) in ('w', 'W'):
            self.plusScale()
        if chr(resp) in ('s', 'S'):
            self.reduceScale()
