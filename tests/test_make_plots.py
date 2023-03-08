from django.test import TestCase
import numpy as np

from cambio.utils.make_plots import get_years_to_plot


class GetYearsToPlotTestCase(TestCase):
    """
    A sample class for trying out testing
    """

    def setUp(self):
        self.year = np.arange(1700.0, 2201.0, 1.0)

    def test_in_range(self):
        """Test for returning indices to year(s) in the middle of the range"""
        # 1st year
        iyear = get_years_to_plot(self.year, (1700.0, 1700.0))
        self.assertTrue(np.array_equal(iyear, np.array([0])))

        # 2nd year
        iyear = get_years_to_plot(self.year, (1701.0, 1701.0))
        self.assertTrue(np.array_equal(iyear, np.array([1])))

        # 2nd 2 years
        iyear = get_years_to_plot(self.year, (1701.0, 1702.0))
        self.assertTrue(np.array_equal(iyear, np.array([1, 2])))

        # 10 years
        iyear = get_years_to_plot(self.year, (1701.0, 1710.0))
        expected = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertTrue(np.array_equal(iyear, expected))

        # Last year
        iyear = get_years_to_plot(self.year, (2200.0, 2200.0))
        self.assertTrue(np.array_equal(iyear, np.array([500])))

        # Last two years
        iyear = get_years_to_plot(self.year, (2199.0, 2200.0))
        self.assertTrue(np.array_equal(iyear, np.array([499, 500])))

    def test_outside_range(self):
        """Test for selecting year(s) outside the range"""

        # outside low end
        iyear = get_years_to_plot(self.year, (1600.0, 1650.0))
        self.assertTrue(np.array_equal(iyear, np.array([])))

        # outside high end
        iyear = get_years_to_plot(self.year, (2201.0, 2210.0))
        self.assertTrue(np.allclose(iyear, np.array([])))

        # overlapping low end
        iyear = get_years_to_plot(self.year, (1600.0, 1703.0))
        self.assertTrue(np.allclose(iyear, np.array([0, 1, 2, 3])))
