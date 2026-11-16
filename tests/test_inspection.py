import unittest

import numpy as np

from webcam_inspector.inspection import compare_images


class CompareImagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.master = np.zeros((10, 10, 3), dtype=np.uint8)

    def test_identical_images_are_ok(self) -> None:
        result = compare_images(self.master, self.master.copy())

        self.assertTrue(result.ok)
        self.assertEqual(result.difference_percent, 0.0)
        self.assertFalse(result.mask.any())

    def test_changed_region_is_highlighted_and_can_be_ng(self) -> None:
        current = self.master.copy()
        current[2:4, 3:6] = 255

        result = compare_images(
            self.master, current, tolerance=20, max_difference_percent=1.0
        )

        self.assertFalse(result.ok)
        self.assertAlmostEqual(result.difference_percent, 6.0)
        self.assertTrue(result.mask[2:4, 3:6].all())
        self.assertTrue((result.overlay[2, 3] == [0, 0, 255]).all())

    def test_tolerance_ignores_small_pixel_changes(self) -> None:
        current = np.full_like(self.master, 15)

        result = compare_images(self.master, current, tolerance=20)

        self.assertTrue(result.ok)
        self.assertEqual(result.difference_percent, 0.0)

    def test_rejects_mismatched_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            compare_images(self.master, np.zeros((8, 10, 3), dtype=np.uint8))

    def test_rejects_invalid_tolerance(self) -> None:
        with self.assertRaises(ValueError):
            compare_images(self.master, self.master, tolerance=256)


if __name__ == "__main__":
    unittest.main()
