"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21
"""

from django.test import TestCase
from django.urls import reverse
import requests

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


class IndexViewTest(TestCase):
    """
    Testing the index function in the views
    Several tests here were adapted from
    https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Testing
    Run them via:
    $ poetry run python manage.py test
    """

    @classmethod
    def setUpTestData(cls):
        """Setup to run tests by deleting all cookies"""
        reqs = requests.session()
        reqs.cookies.clear()

    def test_view_url_exists_at_desired_location(self):
        """Check that the cambio url from index exists"""
        response = self.client.get("/cambio/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        """generates the URL from its name in the URL configuration"""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """query the response for its status code"""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cambio/index.html")

    def test_context_keys_all_there(self):
        """Check the context is as expected for no user input"""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("plot_divs" in response.context)
        self.assertTrue("old_scenario_inputs" in response.context)
        self.assertTrue("plot_scenario_choices" in response.context)
        self.assertTrue("plot_scenario_ids" in response.context)
        self.assertTrue("inputs" in response.context)

    def test_with_no_user_input(self):
        """
        Test that the context vars are as expected with no user input or cookies
        """
        # expected_plot_divs = {
        #     "carbon": {
        #         "plot": [],
        #         "vars": {"C_atm": "Atmospheric carbon", "C_ocean": "Oceanic carbon"},
        #         "units": ["GtC", "atm", "GtCO2"],
        #         "selected_vars": ["C_atm"],
        #         "selected_unit": "GtC",
        #         "label": "Carbon amount",
        #     },
        #     "flux": {
        #         "plot": [],
        #         "vars": {
        #             "F_ha": "Flux human->atmosphere",
        #             "F_ao": "Flux atmosphere->ocean",
        #             "F_oa": "Flux ocean->atmosphere",
        #             "F_la": "Flux land->atmosphere",
        #             "F_al": "Flux atmosphere->land",
        #         },
        #         "units": ["GtC/year", "GtCO2/year"],
        #         "selected_vars": ["F_ha"],
        #         "selected_unit": "GtC/year",
        #         "label": "Flux",
        #     },
        #     "temp": {
        #         "plot": [],
        #         "vars": {
        #             "T_anomaly": "Global temperature change",
        #             "T_C": "Global temperature",
        #         },
        #         "units": ["C", "K", "F"],
        #         "selected_vars": ["T_anomaly"],
        #         "selected_unit": "C",
        #         "label": "Temperature",
        #     },
        #     "pH": {
        #         "plot": [],
        #         "vars": {"pH": "pH"},
        #         "units": [],
        #         "selected_vars": ["pH"],
        #         "selected_unit": "",
        #         "label": "pH",
        #     },
        #     "albedo": {
        #         "plot": [],
        #         "vars": {"albedo": "albedo"},
        #         "units": [],
        #         "selected_vars": ["albedo"],
        #         "selected_unit": "",
        #         "label": "albedo",
        #     },
        # }
        expected_inputs = {
            "transition_year": 2040,
            "transition_duration": 20,
            "long_term_emissions": 2.0,
            "albedo_transition_temp": 4.0,
            "flux_al_transition_temp": 3.9,
            "stochastic_c_atm_std_dev": 0.0,
            "preindust_c_atm": 615,
            "preindust_c_ocean": 350,
            "preindust_ph": 8.2,
            "scenario_name": "Default",
            "albedo_sensitivity": -100,
            "albedo_transition_interval": 1,
            "climate_sensitivity": 0.004878048780487805,
            "flux_al_transition_temp_interval": 1.0,
            "fractional_albedo_floor": 0.9,
            "fractional_flux_al_floor": 0.9,
            "k_al0": 113,
            "k_al1": 0.0114,
            "k_ao": 0.114,
            "k_la": 120,
            "k_oa": 0.2,
            "max_albedo_change_rate": 0.0006,
            "ocean_degas_flux_feedback": 0.034,
            "preindust_albedo": 0.3,
        }

        old_scenario_inputs = {
            "Default": {
                "transition_year": 2040,
                "transition_duration": 20,
                "long_term_emissions": 2.0,
                "albedo_feedback": True,
                "albedo_transition_temp": 4.0,
                "albedo_with_no_constraint": False,
                "temp_anomaly_feedback": True,
                "stochastic_c_atm_std_dev": 0.0,
                "flux_al_transition_temp": 3.9,
                "start_year": 1750.0,
                "stop_year": 2200.0,
                "dtime": 1.0,
                "inv_time_constant": 0.025,
                "albedo_sensitivity": -100,
                "albedo_transition_interval": 1,
                "climate_sensitivity": 0.004878048780487805,
                "flux_al_transition_temp_interval": 1.0,
                "fractional_albedo_floor": 0.9,
                "fractional_flux_al_floor": 0.9,
                "k_al0": 113,
                "k_al1": 0.0114,
                "k_ao": 0.114,
                "k_la": 120,
                "k_oa": 0.2,
                "max_albedo_change_rate": 0.0006,
                "ocean_degas_flux_feedback": 0.034,
                "preindust_albedo": 0.3,
                "preindust_c_atm": 615,
                "preindust_c_ocean": 350,
                "preindust_ph": 8.2,
            }
        }
        # "albedo_with_no_constraint": False,

        plot_scen_choices = [["Default", "plot_scenario_Default"]]

        # Get the request and response
        response = self.client.get("cambio")

        # Make sure cookies are empty
        self.assertFalse(bool(response.client.cookies.items()))

        # Make sure proper status code returned
        response = self.client.get("http://127.0.0.1:8000/cambio/?")
        self.assertEqual(response.status_code, 200)

        # Test for expected results
        self.maxDiff = None
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["transition_year"],
        #     old_scenario_inputs["Default"]["transition_year"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["transition_duration"],
        #     old_scenario_inputs["Default"]["transition_duration"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["long_term_emissions"],
        #     old_scenario_inputs["Default"]["long_term_emissions"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["albedo_feedback"],
        #     old_scenario_inputs["Default"]["albedo_feedback"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"][
        #         "albedo_transition_temperature"
        #     ],
        #     old_scenario_inputs["Default"]["albedo_transition_temperature"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["temp_anomaly_feedback"],
        #     old_scenario_inputs["Default"]["temp_anomaly_feedback"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"][
        #         "stochastic_c_atm_std_dev"
        #     ],
        #     old_scenario_inputs["Default"]["stochastic_c_atm_std_dev"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["start_year"],
        #     old_scenario_inputs["Default"]["start_year"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["stop_year"],
        #     old_scenario_inputs["Default"]["stop_year"],
        # )
        # self.assertEqual(
        #     response.context["old_scenario_inputs"]["Default"]["dtime"],
        #     old_scenario_inputs["Default"]["dtime"],
        # )

        self.assertEqual(response.context["old_scenario_inputs"], old_scenario_inputs)
        self.assertEqual(response.context["inputs"], expected_inputs)
        self.assertEqual(response.context["plot_scenario_choices"], plot_scen_choices)
        self.assertEqual(response.context["plot_scenario_ids"], ["Default"])
