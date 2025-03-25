from io import BytesIO

import numpy as np
from copy import deepcopy
from PIL import Image
import csv
import os
import logging
import math


logger = logging.getLogger(__name__)

# Define the path to the media folder (adjust if needed)
MEDIA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "static"))


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


def calculate_fov(sensor_width, sensor_height, focal_length):
    """
    Calculate the horizontal and vertical field of view (FOV) in degrees.

    Parameters:
    - sensor_width: Width of the sensor in millimeters.
    - sensor_height: Height of the sensor in millimeters.
    - focal_length: Focal length of the lens in millimeters.

    Returns:
    - A tuple containing horizontal FOV and vertical FOV in degrees.
    """
    # Calculate horizontal FOV
    h_fov = 2 * math.atan(sensor_width / (2 * focal_length))
    h_fov_degrees = math.degrees(h_fov)

    # Calculate vertical FOV
    v_fov = 2 * math.atan(sensor_height / (2 * focal_length))
    v_fov_degrees = math.degrees(v_fov)

    return h_fov_degrees, v_fov_degrees



def get_field_view(camera, sensor_h, sensor_w, focal_len, reso):


    if camera == "default (fov of 50x70)":
        # screen_size = 13.3
        # distance = 40  # Viewing distance in cm
        # PPI = np.sqrt(reso[0] ** 2 + reso[1] ** 2) / screen_size
        # ppcm = PPI / 2.54
        # PsysicalWidth = reso[0] / ppcm  # physical width/height of the image on the screen (cm)
        # PsysicalHeight = reso[1] / ppcm  # physical width/height of the image on the screen (cm)
        #
        # v1 = 2 * math.atan((PsysicalWidth) / (2 * distance)) * (
        #             180 / math.pi)  # horizontal visual angle of the image at the specified viewing distance
        # v2 = 2 * math.atan((PsysicalHeight) / (2 * distance)) * (
        #             180 / math.pi)  # vertival visual angle of the image at the specified viewing distance
        return 50, 70
    else: # WHEN WE KNOW THE CAMERA MODEL
        v1, v2 = calculate_fov(sensor_height=sensor_h, sensor_width=sensor_w, focal_length=focal_len)

    return v1, v2




def add_filter(img, HShift, VShift, camera, sensor_h, sensor_w, focal_len, white_balance=False):
    charIm = deepcopy(img)
    thisHShift = HShift
    thisVShift = VShift
    v, h, c = charIm.shape
    reso = (v, h)

    v1, v2 = get_field_view(camera, sensor_h, sensor_w, focal_len, reso)
    imgSize = v1 * v2
    if v > h:
        vv = max(v1, v2)
        vh = min(v1, v2)
    else:
        vv = min(v1, v2)
        vh = max(v1, v2)

    # print(f"Field of view vv: {vv}, vh: {vh}")

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
        if thisimage.size == 0:
            raise Exception("thisimage is empty")

        if meanLum is None:
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
    # start_time = time.time()
    #
    # imgName = 'architecture-apartment-room-1470945_9pYfwd0.jpg'
    # expFolder = '../media/uploads/'
    # with open(expFolder+imgName, 'rb') as f:
    #     img_bytes = f.read()
    #     img = Image.open(BytesIO(img_bytes)).convert('RGB')
    #     hor, ver = find_shift(0.57,1.37)
    #     filtered_img = add_filter(np.array(img, dtype=np.uint8), 1/hor, ver)
    #     image = Image.fromarray(filtered_img)
    #     out_path = os.path.join(expFolder, "filtered_" + imgName)
    #     image.save(out_path, format='PNG')
    #
    # end_time = time.time()
    # print("Time: ", end_time - start_time)

    h_fov_degrees, v_fov_degrees = calculate_fov(sensor_height=9.8, sensor_width=7.3, focal_length=6.86)
    print(h_fov_degrees, v_fov_degrees)
