"""
By Daniel Neshyba-Rowe
2022/12/21
"""

import json
from django.http import QueryDict
from pydantic import BaseModel


class BaseInputs(BaseModel):
    """Class for default inputs to CAMBIO"""

    inv_time_constant: float = 0.025
    transition_year: float = 2040.0
    transition_duration: float = 20.0
    long_term_emissions: float = 2.0
    albedo_with_no_constraint: bool = False
    albedo_feedback: bool = False
    temp_anomaly_feedback: bool = False
    stochastic_C_atm: bool = False
    stochastic_c_atm_std_dev: float = 5.0

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


class CambioInputs(BaseInputs):
    """
    Set additional inputs to CAMBIO that the user does not specify
    """

    start_year: float = 1750.0
    stop_year: float = 2200.0
    dtime: float = 1.0


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
