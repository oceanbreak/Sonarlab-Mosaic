
from math import radians, cos, sin, asin, sqrt, tan, pi
import numpy as np
from sys import stdout
import cv2
from skimage import img_as_float, img_as_uint
from sklearn import linear_model
from matplotlib import pyplot as plt



def timeToSec(year, month, day, hour, minute, second, hseconds):
    return year + month * 31 * 24 * 3600 \
           + day * 3600 * 24 +\
           hour * 3600 + minute * 60 + \
           second + hseconds / 100


def haversine(coord_a, coord_b):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [coord_a[1], coord_a[0], coord_b[1], coord_b[0]])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6358.827  # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000 # in meters


def GaussKruger(dLon, dLat, zone=None):
    """
    Translate geographical coordinates into 6-zone GK system (meters)
    :param dLon:
    :param dLat:
    :param zone:
    :return: Zone, Norhing, Easting
    """
    if zone == None:
        zone = int(dLon/6.0 + 1)

    a = 6378245.0  # Equator semi-axis
    b = 6356863.019  # Polar semi-axis
    e2 = (a ** 2 - b ** 2) / a ** 2  # Eccentricity
    n = (a - b) / (a + b)  # Flattening

    F = 1.0     # Scaling coefficient
    Lat0 = 0.0  # Beginning lattitude
    Lon0 = (zone*6 - 3) * pi/180    # Central longtitude
    N0 = 0.0    # Northing for beginning lat
    E0 = zone * 1e6+500000.0 # Easting for central lon

    Lat, Lon = map(radians, [dLat, dLon])

    # Variables for transformation calculation
    v = a * F * (1 - e2 * (sin(Lat)**2))**-0.5
    p = a * F * (1 - e2) * (1 - e2 * sin(Lat)**2)**-1.5
    n2 = v/p - 1
    M1 = (1 + n + 5.0 / 4.0*n**2 + 5.0/4.0*n**3) * (Lat - Lat0)
    M2 = (3*n+3*n**2+21.0/8.0*n**3)*sin(Lat-Lat0)*cos(Lat+Lat0)
    M3 = (15.0 / 8.0 * n ** 2 + 15.0 / 8.0 * n ** 3) * sin(2 * (Lat -Lat0)) * cos(2 * (Lat + Lat0))
    M4 = 35.0 / 24.0 * n ** 3 * sin(3 *(Lat - Lat0)) * cos(3 * (Lat + Lat0))
    M = b * F * (M1 - M2 + M3 - M4)
    I = M + N0
    II = v / 2 * sin(Lat) * cos(Lat)
    III = v / 24 * sin(Lat) * (cos(Lat)) ** 3 * (5 - (tan(Lat) ** 2) + 9 * n2)
    IIIA = v / 720 * sin(Lat) * (cos(Lat) ** 5) * (61 - 58 * (tan(Lat) ** 2) + (tan(Lat) ** 4))
    IV = v * cos(Lat)
    V = v / 6 * (cos(Lat) ** 3) * (v / p - (tan(Lat) ** 2))
    VI = v / 120 * (cos(Lat) ** 5) * (5 - 18 * (tan(Lat) ** 2) + (tan(Lat) ** 4) + 14 * n2 - 58 * (tan(Lat) ** 2) * n2)

    # Nortning and Easting Calculation
    N = I + II * (Lon - Lon0) ** 2 + III * (Lon - Lon0) ** 4 + IIIA * (Lon - Lon0) ** 6
    E = E0 + IV * (Lon - Lon0) + V * (Lon - Lon0) ** 3 + VI * (Lon - Lon0) ** 5

    return (N, E)


def getDistance(x0, y0, x1, y1):
    """
    Pifagorian distance between two points
    """
    return sqrt( (x0 - x1)**2 + (y0 - y1)**2 )


def gammaCorrection(image, gamma):
    image = img_as_float(image)
    result = image ** (1/gamma)
    result = result * 255
    return result.astype(np.uint8)


def normalize(image):
    image = img_as_float(image)
    result = ((image - np.amin(image)) /
              ((np.amax(image) - np.amin(image)) + 10e-9))
    result = result * 255
    return result.astype(np.uint8)


def getRegionBrightness(image, y_center, x_center, dx=8):
    """
    Returns average value of rectangular region (dx*dx) with input point X in center
    """
    value = 0.0
    total_px = 0
    for i  in range(y_center-dx, y_center+dx):
        for j in range(x_center-dx, x_center+dx):
            try:
                value += image[i,j]
                total_px += 1
            except IndexError:
                pass
    if total_px > 0:
        return value / total_px
    else:
        return None


def eqHist(image, clache=True, gray_only=False):
    """
    Equalization of image, by default based on CLACHE method
    """
    if gray_only:
        L = image
    else:
        imgHLS = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
        L = imgHLS[:,:,1]
    if clache:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equ = clahe.apply(L)
    else:
        equ = cv2.equalizeHist(L)

    if gray_only:
        return equ

    imgHLS[:,:,1] = equ
    res = cv2.cvtColor(imgHLS, cv2.COLOR_HLS2BGR)
    return res


def ratioPreservedResize(image, new_parameter):
    """
    Function resizes with preserving scale if only one parameter specified
    :param image: input image
    :param new_parameter: (width, height) - new size. If one of parameters is 0 or None, then ratio preserved resize made
    :return: resized iamge
    """
    ratio = image.shape[1] / image.shape[0]
    if len(new_parameter) != 2:
        raise ValueError('Input must have shape of (2,)')
    (width, height) = new_parameter
    if width == None or width == 0.0:
        return cv2.resize(image, (int(height * ratio), height))
    elif height == None or height == 0.0:
        return cv2.resize(image, (width, int(width / ratio)))
    else:
        return cv2.resize(image, (width, height))


def goRansac(X, y, thresh, show_plot=False, label = ("Input", "Response")):
    # Fit line using all data
    # lr = linear_model.LinearRegression()
    # lr.fit(X, y)

    # Robustly fit linear model with RANSAC algorithm
    ransac = linear_model.RANSACRegressor(residual_threshold=thresh)
    # print(X.shape)
    # print(y.shape)
    ransac.fit(X, y)
    inlier_mask = ransac.inlier_mask_
    outlier_mask = np.logical_not(inlier_mask)

    # Predict data of estimated models
    line_X = np.arange(X.min(), X.max())[:, np.newaxis]
    # line_y = lr.predict(line_X)
    line_y_ransac = ransac.predict(line_X)

    # Compare estimated coefficients
    # print("Estimated coefficients (true, linear regression, RANSAC):")
    # print(lr.coef_, ransac.estimator_.coef_)

    if show_plot:
        lw = 2
        plt.scatter(X[inlier_mask], y[inlier_mask], color='yellowgreen', marker='.',
                    label='Inliers')
        plt.scatter(X[outlier_mask], y[outlier_mask], color='gold', marker='.',
                    label='Outliers')
        # plt.plot(line_X, line_y, color='navy', linewidth=lw, label='Linear fit')
        plt.plot(line_X, line_y_ransac, color='cornflowerblue', linewidth=lw,
                 label='RANSAC')
        plt.legend(loc='lower right')
        plt.xlabel(label[0])
        plt.ylabel(label[1])
        plt.show()
        plt.savefig('output/outliers_detection.png')
        plt.pause(0.1)

    return inlier_mask


def degrToLatLon(y, x):
    lat_deg = int(y)
    lon_deg = int(x)
    lat_min = (y - lat_deg) * 60
    lon_min = (x - lon_deg) * 60
    lat = 'N' if y > 0 else 'S'
    lon = 'E' if x > 0 else 'W'
    return '{} {:.4f} {} {:0>3} {:.4f} {}'.format(lat_deg, lat_min, lat, lon_deg, lon_min, lon)


def MSE(im_train, im_query, ty):
    """
    Mean squared error between two shifted images
    :param im_train:
    :param im_query:
    :param ty:
    :return:
    """

    im_height, im_width = im_train.shape[:2]
    H = np.identity(3)[:-1, :]
    H[1,-1] = ty

    im1 = cv2.cvtColor(im_train, cv2.COLOR_RGB2GRAY)
    im2 = cv2.cvtColor(im_query, cv2.COLOR_RGB2GRAY)
    im2 =  cv2.warpAffine(im2, H, (im_width, im_height))

    im1 = img_as_float(im1)
    im2 = img_as_float(im2)

    top_margin = int(im_height/2 - ty/2)
    bot_margin = int(im_height/2 + ty/2)

    im1 = im1[top_margin:bot_margin, :]
    im2 = im2[top_margin:bot_margin, :]


    # cv2.imshow('1', im1)
    # cv2.imshow('2', im2)
    # cv2.waitKey(2)

    return np.mean(((im1 - im2)**2))


if __name__ == '__main__':
    # print(GaussKruger(72.432, 34.563))
    PATH = 'data/panorama_test_03'
    from os import listdir
    from os.path import isfile, join
    images = [join(PATH, f) for f in listdir(PATH) if isfile(join(PATH, f)) and f.split('.')[-1]=='png'][:10]
    images = [cv2.imread(im) for im in images]
    images = [cv2.resize(im, (800, 450)) for im in images]
    im = images[0]
    cv2.imshow('', im)
    eqHist(im)
    cv2.waitKey()