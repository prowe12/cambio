"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

"""


from cambio.utils.cambio import cambio
from cambio.utils.scenarios import CambioInputs
from cambio.utils.cambio_utils import CambioVar


def run_model_for_dict(
    scenario_inputs: dict[str, CambioInputs]
) -> dict[str, dict[str, CambioVar]]:
    """
    Run the model for the inputs
    @param scenario_inputs
    @param request
    @returns Climate model run outputs
    """
    # Run the model
    # scenarios: dict[dict[str, CambioVar]] = {}
    scenarios: dict[str, dict[str, CambioVar]] = {}
    for scenario_id, scenario_input in scenario_inputs.items():
        climate, _ = cambio(scenario_input)
        climate["scenario_id"] = scenario_id
        scenarios[scenario_id] = climate
    return scenarios
