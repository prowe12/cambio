from django.test import TestCase

# Trying out an import (not used yet)
from cambio.views import index


class SampleTestCase(TestCase):
    """
    A sample class for trying out testing
    """

    def setUp(self):
        self.myvar = 3

    def test_sample(self):
        """Sample test"""
        self.assertEqual(self.myvar, 3)
