"""
The module serves to open folder with XTF files
and to generate images (png default) from them
with specified vertical scale, which is stored in their name.
"""


from lib.SonarData import SonarData
from tkinter.filedialog import askdirectory
import glob
import os
import numpy as np
import cv2
from skimage import io
from matplotlib import pyplot as plt

VERTICAL_SCALE = 2.8
GAMMA_CORRECT = 1.7
EXTENSION = '.png'


if  __name__ == "__main__":

    user_dir = askdirectory()
    process_files = glob.glob(os.path.join(user_dir, '*.xtf'))
    print(f"Found files:\n{process_files}")

    ending_suffix = f"_vscale{str(VERTICAL_SCALE)}"

    for process_file in process_files:

        # Splits into root and extension
        root, ext = os.path.splitext(process_file)

        # If you need just the file name without the directory path
        file_name = os.path.basename(root)

        sonarfile = SonarData(process_file)
        sonarfile.gammaCorrect(GAMMA_CORRECT)
        

        image = sonarfile.fullImage
        h, w = image.shape[:2]

        # Resize
        new_size = (w, int(h*VERTICAL_SCALE))
        image = cv2.resize(image, new_size)

        print(f'{process_file} info:')
        print(type(image), np.max(image), image.shape)

        cv2.imwrite(os.path.join(user_dir, file_name + ending_suffix + EXTENSION), image)
        print(f'File {file_name + ending_suffix + EXTENSION} saved')

    print('Finished')

