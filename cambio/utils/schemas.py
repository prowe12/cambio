"""
By Daniel Neshyba-Rowe and Penny Rowe
2022/12/21
"""

import json
from django.http import QueryDict
from pydantic import BaseModel


class BaseInputs(BaseModel):
    """Class for default inputs to CAMBIO that the user can change"""

    transition_year: float = 2040.0
    transition_duration: float = 20.0
    long_term_emissions: float = 2.0
    albedo_transition_temp: float = 4.0
    stochastic_c_atm_std_dev: float = 0.0
    flux_al_transition_temp: float = 3.9

    @classmethod
    def from_dict(cls, input_dict: dict[str, str] | QueryDict):
        """
        Replace default inputs to CAMBIO with user-defined values
        """

        input_dict_cleaned = clean_dict(input_dict)
        try:
            return cls.parse_obj(input_dict_cleaned)
        except ValueError:
            return cls()

    @classmethod
    def from_json(cls, input_json: str):
        """
        Replace default inputs to CAMBIO with user-defined values
        """
        # TODO: investigate possibilities of malicious code injection via json deserialization
        input_dict = json.loads(input_json)

        return cls.from_dict(input_dict)

    @classmethod
    def is_json(cls, possible_json: str) -> bool:
        """
        Determine if a string is valid json
        @param possible_json  The input to test
        @returns  True if json, else false
        """
        try:
            json.loads(possible_json)
        except ValueError as e:
            return False
        return True


class CambioInputs(BaseInputs):
    """
    Set additional default values for inputs to CAMBIO that the user does not specify
    """

    # Default values
    # albedo_with_no_constraint = True says that the albedo can change by more than
    #   a specified amount (hard-wired into cambio) per year
    start_year: float = 1750.0
    stop_year: float = 2200.0
    dtime: float = 1.0
    inv_time_constant: float = 0.025
    albedo_with_no_constraint: bool = False
    albedo_feedback: bool = True
    temp_anomaly_feedback: bool = True

    preindust_c_atm: float = 615.0
    preindust_c_ocean: float = 350.0
    preindust_albedo: float = 0.3
    preindust_ph: float = 8.2

    # Parameter for the basic sensitivity of the climate to increasing CO2
    # IPCC: 3 degrees for doubled CO2
    climate_sensitivity: float = 3.0 / preindust_c_atm

    # Carbon flux constants
    k_la: float = 120
    k_al0: float = 113
    k_al1: float = 0.0114
    k_oa: float = 0.2
    k_ao: float = 0.114

    # Parameter for ocean degassing flux feedback (pretty well known from physical chemistry)
    ocean_degas_flux_feedback: float = 0.034

    # Parameters for albedo feedback
    albedo_sensitivity: float = -100

    # T at which significant albedo reduction kicks in (a guess)
    albedo_transition_interval: float = 1
    # Temperature range over which albedo reduction kicks in (a guess)
    max_albedo_change_rate: float = 0.0006
    # Amount albedo can change in a year (based on measurements)
    fractional_albedo_floor: float = 0.9
    # Maximum of 10% reduction in albedo (a guess)

    # Parameters for the atmosphere->land flux feedback
    # T anomaly at which photosynthesis will become impaired (a guess)
    flux_al_transition_temp_interval: float = 1.0
    # Temperature range over which photosynthesis impairment kicks in (guess)
    fractional_flux_al_floor: float = 0.9
    # Maximum of 10% reduction in F_al (a guess)


class ScenarioInputs(BaseInputs):
    """
    Model listing attributes users need to specify for each scenario.
    """

    scenario_name: str = "Default"


def clean_dict(input_dict: dict[str, str] | QueryDict) -> dict[str, str]:
    """
    Return the dictionary after removing all key/value pairs that are
    not variables of the class
    @param input_dict  The dictionary with input variable names and values
    @returns  A dictionary of input variable names and values
    """
    return {key: value for key, value in input_dict.items() if value != ""}
