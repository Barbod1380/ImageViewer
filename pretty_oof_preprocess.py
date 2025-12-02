import numpy as np
import cv2

def pretty_oof_preprocess(image: np.ndarray, save_path: str = None) -> np.ndarray:
    """
    Preprocess an image using a series of transformations to enhance its features.

    This function applies grayscale conversion, normalization, Sobel gradients,
    adaptive thresholding, and rescaling to preprocess the input image.

    Args:
        image (numpy.ndarray): The input image in BGR format (datatype: numpy.ndarray).
        save_path (bool, optional): Whether to save the processed image to a file. Defaults to False (datatype: bool).

    Returns:
        numpy.ndarray: The processed image, rescaled to the 0-255 range (datatype: numpy.ndarray).

    Steps:
    1. Convert the input image to grayscale.
    2. Normalize the grayscale image to the range [0, 255].
    3. Compute Sobel gradients in the x and y directions.
    4. Combine the gradients to calculate the gradient magnitude.
    5. Generate a mean image by blending the gradient magnitude and the original grayscale image.
    6. Compute a histogram of pixel intensities and adjust pixel values based on the most frequent interval.
    7. Clamp positive pixel values in the adjusted image to zero.
    8. Normalize the adjusted image to the range [0, 255].
    9. Apply adaptive Gaussian thresholding to the normalized image.
    10. Rescale the binary image to the 0-255 range.
    11. Optionally save the processed image as "pretty_oof_preprocess.png".

    Note:
    - The input image must be in BGR format as expected by OpenCV.
    - The processed image is returned as an 8-bit single-channel image.
    """
    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)

    grad_x = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    gradient_magnitude = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    gradient_magnitude = (1 - gradient_magnitude / gradient_magnitude.max()) * 255
    ALPHA = 0.21
    mean_image = ALPHA * gradient_magnitude + (1 - ALPHA) * image

    mean_image = cv2.normalize(
        mean_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U
    )
    bin_indices = mean_image // 16
    counts = np.bincount(bin_indices.ravel(), minlength=16)
    max_bin = np.argmax(counts[:16])  # Consider only bins 0-15
    adjustment = max_bin * 16

    adjusted_image = np.minimum(mean_image, adjustment)

    # adjusted_image_normalized = cv2.normalize(adjusted_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    # _, otsu_thresh = cv2.threshold(adjusted_image_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    adjusted_image_normalized = cv2.normalize(
        adjusted_image, None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)
    # Apply adaptive thresholding
    binary_image = cv2.adaptiveThreshold(
        adjusted_image_normalized,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        149,  # Block size 27 very important
        21,  # Constant subtracted from the mean 11
    )

    # Rescale to 0-255 using OpenCV
    rescaled_image = cv2.normalize(binary_image, None, 0, 255, cv2.NORM_MINMAX).astype(
        np.uint8
    )
    if save_path:
        cv2.imwrite(f"{save_path}/pretty_oof_preprocess.png", rescaled_image)

    return rescaled_image
