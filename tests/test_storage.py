import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from webcam_inspector.inspection import compare_images
from webcam_inspector.storage import load_master, save_inspection, save_master


class StorageTests(unittest.TestCase):
    def test_master_and_inspection_are_written_under_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory)
            image = np.zeros((8, 8, 3), dtype=np.uint8)
            master_path = save_master(image, data_dir)
            result = compare_images(image, image)
            record_path = save_inspection(image, result, 35, 2.0, data_dir)

            self.assertTrue(master_path.exists())
            self.assertIsNotNone(load_master(data_dir))
            self.assertTrue(record_path.exists())
            self.assertEqual(
                len(list((data_dir / "inspections").glob("*_overlay.jpg"))), 1
            )
            self.assertEqual(json.loads(record_path.read_text())["result"], "OK")


if __name__ == "__main__":
    unittest.main()
