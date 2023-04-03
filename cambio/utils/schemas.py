"""
By Daniel Neshyba-Rowe and Penny Rowe
2022/12/21
"""

import json
from django.http import QueryDict
from pydantic import BaseModel


class BaseInputs(BaseModel):
    """Class for default inputs to CAMBIO that the user can change"""

    transition_year: float = 2040
    transition_duration: float = 20
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
