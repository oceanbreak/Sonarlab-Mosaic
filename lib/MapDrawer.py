""""
Module to take xtf bits sonar data, separate metric navigation data (in GK projection)
and plots sonar bits along the track.
Each sonar bit should correspond to one navigation point.
"""

from lib.SonarData import SonarStripe
from lib.dtypes import GKpoint, MapPoint
from lib.Utils import getSizeFromRotation, formTranslationRotationMtx
import numpy as np
import cv2
from matplotlib import pyplot as plt

class SonarImageGK:
    """
    Class that holds image with precalculated parameters
    """

    def __init__(self, img : SonarStripe, dst_scale : float):

        # Calc new size
        self.scale = dst_scale
        new_size = self.equalScale(img.widthM, img.heightM, dst_scale)
        self.image = cv2.resize(img.image, new_size)
        # Convert to BGR
        self.image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
        self.alpha = np.ones(self.image.shape).astype(np.uint8)*255

        # Store attributes
        self.shape = self.image.shape # Height First, width second, as in numpy
        self.size_cv = [self.image.shape[1], self.image.shape[0]] # Width first, height second, as in cv2
        self.center_cv = [self.image.shape[1]//2, self.image.shape[0]//2]
        self.width = new_size[0]
        self.height = new_size[1]
        self.center_coordinate_GK = GKpoint((img.lon, img.lat))
        self.rotation = 0.0


    def updateCenterGK(self, new_point_GK):
        self.center_coordinate_GK = GKpoint(new_point_GK)


    def getGKcoordTopLeft(self):
        TLx = self.center_coordinate_GK[0] - self.width / (2 * self.scale)
        TLy = self.center_coordinate_GK[1] + self.height / (2 * self.scale)
        return (TLx, TLy)


    def getGKcoordBotRight(self):
        BRx = self.center_coordinate_GK[0] + self.width / (2 * self.scale)
        BRy = self.center_coordinate_GK[1] - self.height / (2 * self.scale)
        return (BRx, BRy)


    def equalScale(self, sizeXM, sizeYM, dst_scale):
        new_size_x = sizeXM * dst_scale
        new_size_y = sizeYM * dst_scale
        # Add thickness to avoid white
        if new_size_y < dst_scale * 4: new_size_y = int(dst_scale * 4) + 5 
        if new_size_x < dst_scale * 4: new_size_y = int(dst_scale * 4) + 5
        return (int(new_size_x), int(new_size_y))


    def rotate(self, degrees):
        # Calculate new paramters
        new_size = getSizeFromRotation((self.width, self.height), degrees)
        translation = (new_size[0] // 2 - self.center_cv[0],
                    new_size[1]//2 - self.center_cv[1])
        transform_mtx = formTranslationRotationMtx(self.center_cv, translation, degrees, 1.0)

        # Update parameters
        self.rotation = degrees
        self.width, self.height = new_size
        self.center_cv = (new_size[0]//2, new_size[1]//2)

        # Warp image
        self.image = cv2.warpPerspective(self.image, transform_mtx, new_size)
        self.alpha = cv2.warpPerspective(self.alpha, transform_mtx, new_size)

        
        
class MapDrawer:
    """
    Central class of the program.
    Generates map with track and sonar data in Gauss Kruger coordinates.
    """

    def __init__(self, scale):
        self.track = None
        self.sonar_images = []
        self.map_scale = scale # Pixel per meter
        print('Created MapDrawer object')


    def createCanvas(self, coord_TL, coord_BR):
        """
        Creates canvas based on coordinates of corners
        first Top-Left, second Bottom-Right
        """
        lonTL, latTL = coord_TL
        lonBR, latBR = coord_BR
        width = int((lonBR - lonTL) * self.map_scale) 
        height = int((latTL - latBR) * self.map_scale)

        # Store canvas and limits
        self.canvas = 255*np.ones((height, width, 3)).astype(np.uint8)
        self.alpha = 255*np.zeros((height, width, 3)).astype(np.uint8)
        self.XminGK = lonTL
        self.XmaxGK = lonBR
        self.YmaxGK = latTL
        self.YminGK = latBR


    def placeStripeOnCanvas(self, stripe : SonarImageGK):
        """
        Place one stripe on canvas using alpha channel
        """
        stripe_center = self.PtGKtoImg(stripe.center_coordinate_GK)
        TL_corner = (stripe_center[0] - stripe.width // 2,
                    stripe_center[1] - stripe.height // 2)
        
        # Calculate alpha
        background = self.canvas[TL_corner[1] : TL_corner[1] + stripe.height,
                    TL_corner[0] : TL_corner[0] + stripe.width, :]
        

        inv_alpha = 255 - stripe.alpha

        bg = background.astype(np.float32) / 255
        al = stripe.alpha.astype(np.float32) / 255

        # inv_alpha = cv2.dilate(1.0 - al, kernel)
        inv_alpha = 1.0 - al
        msk = bg * (inv_alpha)

        new = msk + stripe.image.astype(np.float32) / 255

        # Return on canvas
        self.canvas[TL_corner[1] : TL_corner[1] + stripe.height,
                    TL_corner[0] : TL_corner[0] + stripe.width, :] = (255.0 * new).astype(np.uint8)
        
        # Update canvas alpha
        raw_alpha = self.alpha[TL_corner[1] : TL_corner[1] + stripe.height,
                    TL_corner[0] : TL_corner[0] + stripe.width]

        res_alpha = cv2.add(raw_alpha, stripe.alpha)

        self.alpha[TL_corner[1] : TL_corner[1] + stripe.height,
                    TL_corner[0] : TL_corner[0] + stripe.width] = res_alpha


    def PtGKtoImg(self, pt : GKpoint):
        lon, lat = pt
        x = (lon - self.XminGK) * self.map_scale
        y = self.canvas.shape[0] - (lat - self.YminGK) * self.map_scale
        return MapPoint((int(x), int(y)))


    def loadSonarImg(self, sonar_image):
        self.sonar_images.append(SonarImageGK(sonar_image))


    def getImage(self):
        return self.canvas
    
    def getAlpha(self):
        return self.alpha[:,:,0]
    
    def getTransparent(self):
        out = np.zeros((self.canvas.shape[0], self.canvas.shape[1], 4))
        out[:,:,:3] = self.canvas
        out[:,:,3] = self.alpha[:,:,0]
        return out

    def getMarginMaps(self):
        # Order: TopLeft, BotLeft, BotRight, TopRight
        # As in surfer: Y on the top

        corners = np.array(((0,self.canvas.shape[0]),
                            (0, 0),
                            (self.canvas.shape[1], 0),
                            (self.canvas.shape[1],self.canvas.shape[0])))
        navi_pts = np.array(((self.XminGK, self.YmaxGK),
                             (self.XminGK, self.YminGK),
                             (self.XmaxGK, self.YminGK),
                             (self.XmaxGK, self.YmaxGK)))
        
        return np.hstack((corners, navi_pts))
        

    def drawPoints(self, points, radius=1, color=(0,0,255), thickness=1, scaler=1):
        """
        Draw points on image preserving scale
        """
        for pt in points:
            pt = tuple([int(x*scaler) for x in pt])
            cv2.circle(self.canvas, pt, radius, color, thickness)


    def drawMapPoint(self, pt : MapPoint, radius=1, color=(0,0,0), thickness=1):
        cv2.circle(self.canvas, pt, radius, color, thickness)


    def translationAfterResize(self, image : SonarImageGK, new_size):
        img_center = image.center_cv
        return (new_size[0] // 2 - img_center[0],
                        new_size[1]//2 - img_center[1])


    def formTranslationRotationMtx(self, center, translation, rotation, scale):
        R = np.identity(3)
        R[:2,:] = cv2.getRotationMatrix2D(center, rotation, scale)
        
        # Estimate scale-preserved-translation
        new_center = np.array(center) + np.array(translation)
        T = np.identity(3)
        T[:-1,-1] = np.array(translation) + (new_center*scale - new_center)
        return T @ R


    def getSizeFromRotation(self, input_size, rotation):
        rot_rad = np.radians(rotation)
        width, height = input_size

        width_new = np.abs(width * np.cos(rot_rad)) + np.abs(height * np.sin(rot_rad))
        height_new = np.abs(height * np.cos(rot_rad)) + np.abs(width * np.sin(rot_rad))

        return (int(width_new), int(height_new))
    

    def rotateImage(self, img : SonarImageGK):
        pass


if __name__ == '__main__':
    pass