from pyproj import Transformer

class GausKruger:

    def __init__(self):
        pass

    def gauss_kruger_zone(self, longitude):
        """Determine the Gauss-Kruger zone based on longitude."""
        return int((longitude + 6) / 6)

    def transform_to_gauss_kruger(self, latitude, longitude, zone=None):
        """Transform geographical coordinates to Gauss-Kruger (Pulkovo) projection."""
        if zone is None:
            zone = self.gauss_kruger_zone(longitude[0])
        # Define the EPSG code for the Gauss-Kruger zone
        epsg_code = 28400 + zone
        # Create a transformer object
        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_code}", always_xy=True)
        # Perform the transformation
        x, y = transformer.transform(longitude, latitude)
        return x, y, zone
    


# x, y, zone = transform_to_gauss_kruger(latitude, longitude)
# print(f"Gauss-Kruger Coordinates (Zone {zone}): X = {x:.2f}, Y = {y:.2f}")