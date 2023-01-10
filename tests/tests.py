from django.test import TestCase

# Trying out an import (not used yet)
from cambio.views import index


class SampleTestCase(TestCase):
    """
    A sample class for trying out testing
    """

    def setUp(self):
        print("In setUp")

    def test_sample(self):
        """Sample test"""
        print("In test")
        my_var = 3
        self.assertEqual(my_var, 3)
