from io import BytesIO

import numpy as np
from copy import deepcopy

from PIL import Image
import csv
import os
import logging


logger = logging.getLogger(__name__)

# Define the path to the media folder (adjust if needed)
MEDIA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media/csv"))


def read_csv(file_path):
    """ Reads a CSV file and returns the parsed rows as a list of dictionaries. """
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except FileNotFoundError:
        print("File not found:", file_path)
        return []


def find_shift(va: float, cs: float) -> tuple[float, float]:
    """ Finds and returns the shift values (a, b) based on va and cs. """
    file_path = os.path.join(MEDIA_FOLDER, "va_cs_matrix.csv")  # CSV file path

    rows = read_csv(file_path)  # Read CSV content

    for row in rows:
        if float(row['VA']) == va and float(row['CS']) == cs:
            return float(row['a']), float(row['b'])  # Return (hor, ver)

    return 0.0, 0.0  # Default return value if no match is found


## iPhone 15 pro max: 6.7 inch, 2796 x 1290 pixels, 460 ppi
## iPhone 15 pro : 6.1 inch, 2556 x 1179 pixels, 460 ppi
def add_filter(img, HShift, VShift, screen_size=13.3, camera=True, white_balance=False, ppi=None):
    charIm = deepcopy(img)
    thisHShift = HShift
    thisVShift = VShift
    v, h, c = charIm.shape
    reso = (v, h)
    # if image not taken by a camera therefore viewing angle depend on the viewing distance
    if not camera:
        logger.info(f"Not Camera")
        # Calculate Viewing Angle
        # PPI = sqrt((horizontal reso/width in inches)^2 + (vertical reso/height in inches)^2)
        # PPcm = PPI/2.54
        PPI = np.sqrt(reso[0] ** 2 + reso[1] ** 2) / screen_size
        ppcm = PPI / 2.54
        PsysicalWidth = charIm.shape[0] / ppcm  # physical width/height of the image on the screen (cm)
        PsysicalHeight = charIm.shape[1] / ppcm  # physical width/height of the image on the screen (cm)
        distance = 40  # Viewing distance in cm
        vh = 2 * math.atan((PsysicalWidth) / (2 * distance)) * (
                    180 / math.pi)  # horizontal visual angle of the image at the specified viewing distance
        vv = 2 * math.atan((PsysicalHeight) / (2 * distance)) * (
                    180 / math.pi)  # vertival visual angle of the image at the specified viewing distance
        imgSize = vh * vv  # visual angle of the entire image at the specified viewing distance

        # % hsize=PsysicalWidth/h; % height of a pixel in cm (cm/pixel)
        # % vsize=PsysicalHeight/v; % width of a pixel in cm (cm/pixel)

    else: # WHEN WE KNOW THE CAMERA MODEL
        logger.info(f"Camera")
        if v > h:
            vv = 71
            vh = 56
        else:
            vh = 71  # iPhone main camera horizontal field of view in degrees
            vv = 56  # iPhone main camera vertical field of view in degrees
        imgSize = vh * vv  # visual angle of the entire image

    h = charIm.shape[1]  # horizontal pixel number of the image
    v = charIm.shape[0]  # vertical pixel number of the image
    fx = np.arange(start=-h / 2, stop=h / 2, step=1)
    fx = fx / vh
    fy = np.arange(start=-v / 2, stop=v / 2, step=1)
    fy = fy / vv
    [ux, uy] = np.meshgrid(fx, fy)
    finalImg = np.zeros_like(charIm)
    for j in range(3):  # three color channels or only luminance channel

        thisimage = charIm[:, :, j].astype(np.float64)
        meanLum = np.mean(thisimage)
        if thisimage.size == 0:  # ✅ Correct way to check if a NumPy array is empty
            raise Exception("thisimage is empty")

        if meanLum is None:  # ✅ Correct way to check if meanLum is missing
            raise Exception("meanLum is None")

        # If you want to check if meanLum is zero (which might be problematic)
        if meanLum == 0:
            raise Exception("meanLum is zero")

        ## Generate blur

        ## Horizontal shift
        sSF0 = np.sqrt(ux ** 2 + uy ** 2 + .0001)
        CSF0 = (5200 * np.exp(-.0016 * (100 / meanLum + 1) ** .08 * sSF0 ** 2)) / np.sqrt(
            (0.64 * sSF0 ** 2 + 144 / imgSize + 1) * (1. / (1 - np.exp(-.02 * sSF0 ** 2)) + 63 / (meanLum ** .83)))
        sSF = thisHShift * np.sqrt(ux ** 2 + uy ** 2 + .0001)
        if white_balance:
            # Vertical Shift
            for ii in range(thisimage.shape[0]):
                for jj in range(thisimage.shape[1]):
                    if thisimage[ii, jj] != 255:
                        thisimage[ii, jj] = np.round(255 - np.round((255 - thisimage[ii, jj]) * thisVShift))
            CSF = (5200 * np.exp(-.0016 * (100 / meanLum + 1) ** .08 * sSF ** 2)) / np.sqrt(
                (0.64 * sSF ** 2 + 144 / imgSize + 1) * (1. / (1 - np.exp(-.02 * sSF ** 2)) + 63 / (meanLum ** .83)))
        else:
            CSF = thisVShift * (5200 * np.exp(-.0016 * (100 / meanLum + 1) ** .08 * sSF ** 2)) / np.sqrt(
                (0.64 * sSF ** 2 + 144 / imgSize + 1) * (1. / (1 - np.exp(-.02 * sSF ** 2)) + 63 / (meanLum ** .83)))

        nCSF = np.fft.fftshift(CSF / CSF0)
        maxValue = 1
        nCSF = np.clip(nCSF, None, maxValue)  # replace maximun to 1
        nCSF[0, 0] = 1

        Y = np.fft.fft2(thisimage)

        # spectrum = np.abs(Y)

        filtImg = np.real(np.fft.ifft2(nCSF * Y))

        ## put the three channels together
        finalImg[:, :, j] = np.clip(np.round(filtImg), 0, 255)

    return finalImg


import time
if __name__ == '__main__':
    start_time = time.time()

    imgName = 'architecture-apartment-room-1470945_9pYfwd0.jpg'
    # imgName = 'IMG_9151.JPG'
    expFolder = '../media/uploads/'

    with open(expFolder+imgName, 'rb') as f:
        img_bytes = f.read()
        img = Image.open(BytesIO(img_bytes)).convert('RGB')


        hor, ver = find_shift(0.57,1.37)
        filtered_img = add_filter(np.array(img, dtype=np.uint8), 1/hor, ver)
        image = Image.fromarray(filtered_img)

        out_path = os.path.join(expFolder, "filtered_" + imgName)
        image.save(out_path, format='PNG')


    end_time = time.time()

    print("Time: ", end_time - start_time)
