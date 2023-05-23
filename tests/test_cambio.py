from django.test import TestCase
from django.urls import reverse
from pydantic import BaseModel

from cambio.utils.schemas import CambioInputs
from cambio.utils.cambio import cambio


class Test(BaseModel):
    """Pydantic class for default inputs to CAMBIO"""

    transition_year: float = 2040.0
    transition_duration: float = 20.0
    long_term_emissions: float = 2.0
    albedo_transition_temp: float = 4.0
    temp_anomaly_feedback: bool = True
    stochastic_c_atm_std_dev: float = 0.0
    start_year: float = 1750.0
    stop_year: float = 2200.0
    dtime: float = 1.0
    inv_time_constant: float = 0.025
    albedo_with_no_constraint: bool = False
    albedo_feedback: bool = True
    flux_al_transition_temp: float = 3.9

    preindust_c_atm: float = 615.0
    preindust_c_ocean: float = 350.0
    preindust_albedo: float = 0.3
    preindust_ph: float = 8.2
    climate_sensitivity: float = 3.0 / preindust_c_atm
    k_la: float = 120
    k_al0: float = 113
    k_al1: float = 0.0114
    k_oa: float = 0.2
    k_ao: float = 0.114
    ocean_degas_flux_feedback: float = 0.034
    albedo_sensitivity: float = -100
    albedo_transition_interval: float = 1
    max_albedo_change_rate: float = 0.0006
    fractional_albedo_floor: float = 0.9
    flux_al_transition_temp_interval: float = 1.0
    fractional_flux_al_floor: float = 0.9


class cambioTestSample(TestCase):
    """
    A sample class for trying out testing
    """

    def setUp(self):
        """
        Run test using the test inputs
        """
        self.inputs = Test()

    def test_default(self):
        """Run the cambio model and check the outputs for the default scenario"""
        climatestate = cambio(self.inputs)

        # Test outputs at the starting year (1750)
        self.assertEqual(climatestate["year"][0], 1750)
        self.assertAlmostEqual(climatestate["c_atm"][0], 614.8923685)
        self.assertAlmostEqual(climatestate["c_ocean"][0], 350.11)
        self.assertAlmostEqual(climatestate["albedo"][0], 0.2999998)
        self.assertAlmostEqual(climatestate["temp_anomaly"][0], 1.843252e-5)
        self.assertAlmostEqual(climatestate["ph"][0], 8.200076)
        self.assertAlmostEqual(climatestate["flux_ha"][0], 0.0133627)
        self.assertAlmostEqual(climatestate["flux_ao"][0], 70.11)
        self.assertAlmostEqual(climatestate["flux_oa"][0], 70.0)
        self.assertAlmostEqual(climatestate["flux_la"][0], 120.0)
        self.assertAlmostEqual(climatestate["flux_al"][0], 120.0109942)
        # self.assertAlmostEqual(climatestate["T_C"][0],)

        # Test outputs at the ending year (2200)
        self.assertEqual(climatestate["year"][-1], 2199)
        self.assertAlmostEqual(climatestate["c_atm"][-1], 898.384488, places=5)
        self.assertAlmostEqual(climatestate["c_ocean"][-1], 491.024656, places=5)
        self.assertAlmostEqual(climatestate["albedo"][-1], 0.2999882, places=5)
        self.assertAlmostEqual(climatestate["temp_anomaly"][-1], 1.38765, places=5)
        self.assertAlmostEqual(climatestate["ph"][-1], 8.035413, places=5)
        self.assertAlmostEqual(climatestate["flux_ha"][-1], 2.0, places=5)
        self.assertAlmostEqual(climatestate["flux_ao"][-1], 102.5119139, places=5)
        self.assertAlmostEqual(climatestate["flux_oa"][-1], 102.919734, places=5)
        self.assertAlmostEqual(climatestate["flux_la"][-1], 120.0, places=5)
        self.assertAlmostEqual(climatestate["flux_al"][-1], 123.250647, places=5)
        # self.assertAlmostEqual(climatestate["T_C"][-1],, places=5)


class cambioTestDefault:
    """
    A sample class for trying out testing
    """

    def setUp(self):
        """
        Run test using the default inputs
        """
        self.inputs = CambioInputs()

    def test_default(self):
        """Run the cambio model and check the outputs for the default scenario"""
        climatestate = cambio(self.inputs)

        # Test outputs at the starting year (1750)
        self.assertEqual(climatestate["year"][0], 1750)
        self.assertAlmostEqual(climatestate["c_atm"][0], 614.8923685)
        self.assertAlmostEqual(climatestate["c_ocean"][0], 350.11)
        self.assertAlmostEqual(climatestate["albedo"][0], 0.2999998)
        self.assertAlmostEqual(climatestate["temp_anomaly"][0], 1.843252e-5)
        self.assertAlmostEqual(climatestate["ph"][0], 8.200076)
        self.assertAlmostEqual(climatestate["flux_ha"][0], 0.0133627)
        self.assertAlmostEqual(climatestate["flux_ao"][0], 70.11)
        self.assertAlmostEqual(climatestate["flux_oa"][0], 70.0)
        self.assertAlmostEqual(climatestate["flux_la"][0], 120.0)
        self.assertAlmostEqual(climatestate["flux_al"][0], 120.0109942)
        # self.assertAlmostEqual(climatestate["T_C"][0],)

        # Test outputs at the ending year (2200)
        self.assertEqual(climatestate["year"][-1], 2199)
        self.assertAlmostEqual(climatestate["c_atm"][-1], 898.384488, places=5)
        self.assertAlmostEqual(climatestate["c_ocean"][-1], 491.024656, places=5)
        self.assertAlmostEqual(climatestate["albedo"][-1], 0.2999882, places=5)
        self.assertAlmostEqual(climatestate["temp_anomaly"][-1], 1.38765, places=5)
        self.assertAlmostEqual(climatestate["ph"][-1], 8.035413, places=5)
        self.assertAlmostEqual(climatestate["flux_ha"][-1], 2.0, places=5)
        self.assertAlmostEqual(climatestate["flux_ao"][-1], 102.5119139, places=5)
        self.assertAlmostEqual(climatestate["flux_oa"][-1], 102.919734, places=5)
        self.assertAlmostEqual(climatestate["flux_la"][-1], 120.0, places=5)
        self.assertAlmostEqual(climatestate["flux_al"][-1], 123.250647, places=5)
        # self.assertAlmostEqual(climatestate["T_C"][-1],, places=5)
