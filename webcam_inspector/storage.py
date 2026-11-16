import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from webcam_inspector.inspection import InspectionResult


Image = NDArray[np.uint8]
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def ensure_data_dirs(data_dir: Path = DEFAULT_DATA_DIR) -> None:
    (data_dir / "master_sample").mkdir(parents=True, exist_ok=True)
    (data_dir / "inspections").mkdir(parents=True, exist_ok=True)


def master_image_path(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return data_dir / "master_sample" / "master.jpg"


def load_master(data_dir: Path = DEFAULT_DATA_DIR) -> Image | None:
    path = master_image_path(data_dir)
    if not path.exists():
        return None
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise OSError(f"Could not read the master image at {path}")
    return image


def save_master(image: Image, data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    ensure_data_dirs(data_dir)
    path = master_image_path(data_dir)
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not save the master image at {path}")
    return path


def save_inspection(
    current: Image,
    result: InspectionResult,
    tolerance: int,
    max_difference_percent: float,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> Path:
    ensure_data_dirs(data_dir)
    timestamp = datetime.now().astimezone()
    stem = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    output_dir = data_dir / "inspections"
    current_path = output_dir / f"{stem}_current.jpg"
    overlay_path = output_dir / f"{stem}_overlay.jpg"
    if not cv2.imwrite(str(current_path), current):
        raise OSError(f"Could not save the inspection image at {current_path}")
    if not cv2.imwrite(str(overlay_path), result.overlay):
        current_path.unlink(missing_ok=True)
        raise OSError(f"Could not save the inspection overlay at {overlay_path}")

    record = {
        "timestamp": timestamp.isoformat(timespec="milliseconds"),
        "result": "OK" if result.ok else "NG",
        "difference_percent": round(result.difference_percent, 4),
        "tolerance": tolerance,
        "max_difference_percent": max_difference_percent,
        "current_image": current_path.name,
        "overlay_image": overlay_path.name,
    }
    record_path = output_dir / f"{stem}.json"
    try:
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    except OSError:
        current_path.unlink(missing_ok=True)
        overlay_path.unlink(missing_ok=True)
        raise
    return record_path
