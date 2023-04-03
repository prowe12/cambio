from django.test import TestCase
from django.urls import reverse

from cambio.utils.schemas import CambioInputs
from cambio.utils.cambio import cambio


class Test:
    """Class for default inputs to CAMBIO"""

    transition_year: float = 2040
    transition_duration: float = 20
    long_term_emissions: float = 2
    albedo_transition_temp: float = 4.0
    temp_anomaly_feedback: bool = True
    stochastic_c_atm_std_dev: float = 0
    start_year: float = 1750.0
    stop_year: float = 2200.0
    dtime: float = 1.0
    inv_time_constant: float = 0.025
    albedo_with_no_constraint: bool = False
    albedo_feedback: bool = True
    flux_al_transition_temp: float = 3.9


class cambioTestSample(TestCase):
    """
    A sample class for trying out testing
    """

    def setUp(self):
        # self.inputs = CambioInputs()
        self.inputs = Test()

    def test_default(self):
        """Run the cambio model and check the outputs for the default scenario"""
        climatestate = cambio(self.inputs)[0]

        # Test outputs at the starting year (1750)
        self.assertEqual(climatestate["year"][0], 1750)
        self.assertAlmostEqual(climatestate["C_atm"][0], 614.8923685)
        self.assertAlmostEqual(climatestate["C_ocean"][0], 350.11)
        self.assertAlmostEqual(climatestate["albedo"][0], 0.2999998)
        self.assertAlmostEqual(climatestate["T_anomaly"][0], 1.843252e-5)
        self.assertAlmostEqual(climatestate["pH"][0], 8.200076)
        self.assertAlmostEqual(climatestate["F_ha"][0], 0.0133627)
        self.assertAlmostEqual(climatestate["F_ao"][0], 70.11)
        self.assertAlmostEqual(climatestate["F_oa"][0], 70.0)
        self.assertAlmostEqual(climatestate["F_la"][0], 120.0)
        self.assertAlmostEqual(climatestate["F_al"][0], 120.0109942)
        # self.assertAlmostEqual(climatestate["T_C"][0],)

        # Test outputs at the ending year (2200)
        self.assertEqual(climatestate["year"][-1], 2199)
        self.assertAlmostEqual(climatestate["C_atm"][-1], 898.384488, places=5)
        self.assertAlmostEqual(climatestate["C_ocean"][-1], 491.024656, places=5)
        self.assertAlmostEqual(climatestate["albedo"][-1], 0.2999882, places=5)
        self.assertAlmostEqual(climatestate["T_anomaly"][-1], 1.38765, places=5)
        self.assertAlmostEqual(climatestate["pH"][-1], 8.035413, places=5)
        self.assertAlmostEqual(climatestate["F_ha"][-1], 2.0, places=5)
        self.assertAlmostEqual(climatestate["F_ao"][-1], 102.5119139, places=5)
        self.assertAlmostEqual(climatestate["F_oa"][-1], 102.919734, places=5)
        self.assertAlmostEqual(climatestate["F_la"][-1], 120.0, places=5)
        self.assertAlmostEqual(climatestate["F_al"][-1], 123.250647, places=5)
        # self.assertAlmostEqual(climatestate["T_C"][-1],, places=5)


# class cambioTest(TestCase):
#     """
#     Testing the cambio climate model
#     Run tests via:
#     $ poetry run python manage.py test
#     """

#     @classmethod
#     def setUpTestData(cls):
#         """Setup to run tests by getting default inputs"""
#         cambioInputs = CambioInputs()

#     def test_view_url_exists_at_desired_location(self):
#         """Check that the cambio url from index exists"""
#         response = self.client.get("/cambio/")
#         self.assertEqual(response.status_code, 200)
