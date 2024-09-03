from io import BytesIO

import numpy as np
import requests
from PIL import Image


def normalize_array(array: np.ndarray):
    return (array - np.min(array)) / np.max(array - np.min(array))


def linear_to_srgb_array(color_array: np.ndarray):
    # Create an empty array to hold the sRGB values
    srgb_array = np.empty_like(color_array)

    # Apply the conversion for values <= 0.0031308
    mask = color_array <= 0.0031308
    srgb_array[mask] = 12.92 * color_array[mask] * 255.99

    # Apply the conversion for values > 0.0031308
    srgb_array[~mask] = (1.055 * np.power(color_array[~mask], 1 / 2.4) - 0.055) * 255.99

    # Convert the result to integers (sRGB values)
    return srgb_array.astype(np.uint8)


def reverse_color(color_array: np.ndarray):
    return 255 - color_array


def convert_to_bytes(image: Image.Image):

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
