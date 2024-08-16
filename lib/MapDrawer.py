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
        if new_size_y < 3: new_size_y = 3
        if new_size_x < 3: new_size_y = 3
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
        self.canvas[TL_corner[1] : TL_corner[1] + stripe.height,
                    TL_corner[0] : TL_corner[0] + stripe.width, :] = stripe.image




    def PtGKtoImg(self, pt : GKpoint):
        lon, lat = pt
        x = (lon - self.XminGK) * self.map_scale
        y = self.canvas.shape[0] - (lat - self.YminGK) * self.map_scale
        return MapPoint((int(x), int(y)))


    def DekartToImg(self, pt):
        x, y = pt
        return (x, -y)
    

    def ImgToDekart(self, pt):
        x, y = pt
        return (x, -y)


    def loadSonarImg(self, sonar_image):
        self.sonar_images.append(SonarImageGK(sonar_image))


    def calculateTrackMargins(self):

        print('Calculating margins')
        Xmin = np.min(self.track.data[:,0]) 
        Xmax = np.max(self.track.data[:,0]) 
        Ymin = np.min(self.track.data[:,1]) 
        Ymax = np.max(self.track.data[:,1]) 

        # Save margins
        self.margin_navi = (Xmin, Ymin, Xmax, Ymax)

        self.canvas = 255*np.ones((int((Ymax - Ymin) * (1/self.map_scale)) , 
                                   int((Xmax - Xmin) * (1/self.map_scale)), 3)).astype(np.uint8)

        self.x_offset = Xmin * (1/self.map_scale)
        self.y_offset = Ymin * (1/self.map_scale)

        offseted_track_x = self.track.data[:,0] *  (1/self.map_scale) - Xmin * (1/self.map_scale)
        offseted_track_y = int((Ymax - Ymin) * (1/self.map_scale)) -  \
            (self.track.data[:,1] *  (1/self.map_scale) - Ymin * (1/self.map_scale)) # Reverse Y axis
        self.offseted_track = np.vstack((offseted_track_x, offseted_track_y)).transpose()

        print(f'X offset = {self.x_offset}, Y offset = {self.y_offset}')
        print(f'Canvas size ({self.canvas.shape})')


    def drawTrack(self):
        radius = int(1 / self.map_scale) if self.map_scale < 1 else 1
        thickness = int(1 / self.map_scale) if self.map_scale < 1 else 1
        self.drawPoints(self.offseted_track, radius=radius, color=(0,0,255), thickness=thickness)


    def getImage(self):
        return self.canvas
    

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

    
    def addWeighted(self, center_point : tuple, stripe : np.ndarray, rotation : float = 0.0):
        pass

    def rotateStripe(self):
        pass


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