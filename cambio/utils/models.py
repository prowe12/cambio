import json
from django.http import QueryDict
from pydantic import BaseModel


class BaseInputs(BaseModel):
    inv_time_constant: float = 0.025
    transition_year: float = 2040.0
    transition_duration: float = 20.0
    long_term_emissions: float = 2.0
    albedo_with_no_constraint: bool = False
    albedo_feedback: bool = False
    temp_anomaly_feedback: bool = False
    stochastic_C_atm: bool = False
    stochastic_c_atm_std_dev: float = 0.1

    @classmethod
    def from_dict(cls, input_dict: dict[str, str] | QueryDict):
        input_dict_cleaned = clean_dict(input_dict)
        try:
            return cls.parse_obj(input_dict_cleaned)
        except ValueError:
            return cls()

    @classmethod
    def from_json(cls, input_json: str):
        # TODO: investigate possibilities of malicious code injection via json deserialization
        input_dict = json.loads(input_json)
        return cls.from_dict(input_dict)


class CambioInputs(BaseInputs):
    start_year: float = 1750.0
    stop_year: float = 2200.0
    dtime: float = 1.0


class ScenarioInputs(BaseInputs):
    """
    Model listing attributes users need to specify for each scenario.
    """

    id: str = "0"


def clean_dict(input_dict: dict[str, str] | QueryDict) -> dict[str, str]:
    return {key: value for key, value in input_dict.items() if value != ""}
