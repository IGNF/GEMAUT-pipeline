#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests unitaires pour le marquage NoData dans le masque GEMO."""

import os
import sys
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from gemaut.image_utils import MaskProcessor


class TestMaskNodataMarking(unittest.TestCase):
    """Vérifie le masque GEMO : bords à 11, trous intérieurs à 255."""

    NODATA_EXT = -32768
    NODATA_INT = -32767
    NODATA_MASK = 11
    SURSOL_MASK = 255

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mask_path = os.path.join(self.temp_dir, "mask.tif")
        self.mns_path = os.path.join(self.temp_dir, "mns.tif")
        self.output_path = os.path.join(self.temp_dir, "mask_nodata.tif")

        profile = {
            'driver': 'GTiff',
            'height': 3,
            'width': 3,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 3, 1, 1),
        }

        mns = np.array([
            [self.NODATA_EXT, 10.0, self.NODATA_INT],
            [20.0, 30.0, 40.0],
            [self.NODATA_INT, 50.0, self.NODATA_EXT],
        ], dtype=np.float32)

        mask = np.array([
            [0, 255, 0],
            [0, 0, 255],
            [0, 0, 0],
        ], dtype=np.uint8)

        with rasterio.open(self.mns_path, 'w', **profile) as dst:
            dst.write(mns, 1)

        mask_profile = profile.copy()
        mask_profile['dtype'] = 'uint8'
        with rasterio.open(self.mask_path, 'w', **mask_profile) as dst:
            dst.write(mask, 1)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_marks_borders_and_holes_differently(self):
        MaskProcessor.set_nodata_extern_to_nodata_intern_mask(
            self.mask_path,
            self.mns_path,
            self.output_path,
            self.NODATA_EXT,
            self.NODATA_INT,
            self.NODATA_MASK,
        )

        with rasterio.open(self.output_path) as src:
            result = src.read(1)

        expected = np.array([
            [self.NODATA_MASK, 255, self.SURSOL_MASK],
            [0, 0, 255],
            [self.SURSOL_MASK, 0, self.NODATA_MASK],
        ], dtype=np.uint8)

        np.testing.assert_array_equal(result, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
