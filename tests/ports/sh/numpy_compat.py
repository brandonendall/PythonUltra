"""Host smoke tests for PythonUltra's calculator-sized NumPy layer."""

import os
import sys
import unittest


MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ports/sh/modules"))
sys.path.insert(0, MODULE_DIR)

import numpy as np


class NumpyCompatTests(unittest.TestCase):
    def test_array_basics(self):
        values = np.arange(6).reshape((2, 3))
        self.assertEqual(values.shape, (2, 3))
        self.assertEqual(values.tolist(), [[0, 1, 2], [3, 4, 5]])
        self.assertEqual((values + 2).tolist(), [[2, 3, 4], [5, 6, 7]])

    def test_matrix_constructor_and_multiply(self):
        left = np.matrix([[1, 2], [3, 4]])
        right = np.matrix([[5, 6], [7, 8]])
        self.assertIsInstance(left, np.matrix)
        self.assertEqual(left.shape, (2, 2))
        self.assertEqual((left * right).tolist(), [[19, 22], [43, 50]])
        self.assertEqual((2 * left).tolist(), [[2, 4], [6, 8]])

    def test_matrix_transpose_and_aliases(self):
        value = np.mat([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(value.T.tolist(), [[1, 4], [2, 5], [3, 6]])
        self.assertEqual(np.asmatrix([1, 2, 3]).shape, (1, 3))
        self.assertEqual(value.A.tolist(), [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(value.A1.tolist(), [1, 2, 3, 4, 5, 6])

    def test_matrix_inverse(self):
        value = np.matrix([[4.0, 7.0], [2.0, 6.0]])
        inverse = value.I
        product = value * inverse
        self.assertAlmostEqual(product[0, 0], 1.0, places=5)
        self.assertAlmostEqual(product[0, 1], 0.0, places=5)
        self.assertAlmostEqual(product[1, 0], 0.0, places=5)
        self.assertAlmostEqual(product[1, 1], 1.0, places=5)

    def test_matmul_remains_separate_api(self):
        left = np.array([[1, 2], [3, 4]])
        right = np.array([[2], [1]])
        self.assertEqual(np.matmul(left, right).tolist(), [[4], [10]])
        self.assertEqual(np.identity(2).tolist(), [[1.0, 0.0], [0.0, 1.0]])


if __name__ == "__main__":
    unittest.main()
