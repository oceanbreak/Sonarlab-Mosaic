import numpy as np

class CoordinatesData:

    def __init__(self):
        return

class Navigation:

    def __init__(self):
        self.track_wgs84 = None
        self.track_GK = None

    def loadGK(self, coord_list : np.ndarray):
        # Read coordinates list in Gauss Kruger projection
        self.track_GK = coord_list