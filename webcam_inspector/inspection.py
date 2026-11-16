from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


Image = NDArray[np.uint8]


@dataclass(frozen=True)
class InspectionResult:
    ok: bool
    difference_percent: float
    overlay: Image
    mask: NDArray[np.bool_]


def compare_images(
    master: Image,
    current: Image,
    tolerance: int = 35,
    max_difference_percent: float = 2.0,
) -> InspectionResult:
    """Compare aligned BGR images and mark pixels that exceed the color tolerance."""
    if master.shape != current.shape:
        raise ValueError(
            f"Images must have the same dimensions; got {master.shape} and {current.shape}"
        )
    if master.ndim != 3 or master.shape[2] != 3:
        raise ValueError("Images must be three-channel BGR images")
    if not 0 <= tolerance <= 255:
        raise ValueError("tolerance must be between 0 and 255")
    if not 0 <= max_difference_percent <= 100:
        raise ValueError("max_difference_percent must be between 0 and 100")

    channel_difference = cv2.absdiff(master, current)
    mask = np.max(channel_difference, axis=2) > tolerance
    difference_percent = float(np.count_nonzero(mask) * 100.0 / mask.size)
    overlay = current.copy()
    overlay[mask] = (0, 0, 255)

    return InspectionResult(
        ok=difference_percent <= max_difference_percent,
        difference_percent=difference_percent,
        overlay=overlay,
        mask=mask,
    )
