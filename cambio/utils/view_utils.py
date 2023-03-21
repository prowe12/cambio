"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

"""

from django.http import HttpRequest, HttpResponse

from cambio.utils.cambio import cambio
from cambio.utils.schemas import CambioInputs
from cambio.utils.cambio_utils import CambioVar


class ManageInputs:
    """
    Manage the inputs to the cambio model and the webapp interface
    """

    def __init__(self, request, default):
        """Get the scenario inputs:
        # - Always include the default first (it can be overridden)"""
        self.default = default
        self.new_scenario_id = ""
        self.is_new = False
        self.new_scenario = None
        self.scenario_inputs: dict[str, CambioInputs] = {}

        # Always add the default
        self.include_default()

        # Add old scenarios
        self.add_old(request.COOKIES)

        # Add new scenarios if indicated
        if is_in_request(request, "add_button"):
            self.set_new(request)

    def add_old(self, cookies):
        """add old scenarios from cookies"""
        for scenario_id, scenario in cookies.items():
            if CambioInputs.is_json(scenario):
                self.scenario_inputs[scenario_id] = CambioInputs.from_json(scenario)

    def set_new(self, request):
        """Get new scenario from get parameters only if it exists"""
        new_scenario_id = request.GET.get("scenario_name", "")
        if new_scenario_id != "":
            self.new_scenario_id = new_scenario_id
            self.is_new = True
            self.new_scenario = CambioInputs.from_dict(request.GET)
            self.scenario_inputs[new_scenario_id] = self.new_scenario
        else:
            self.new_scenario_id = ""
            self.is_new = False
            self.new_scenario = None

    def new_exists(self):
        """
        Return True if new scenario exists
        @returns True if new scenario exists, else False
        """
        return self.is_new

    def get_new(self):
        """
        Get the new scenario id and new scenario
        @returns  The new scenario id
        @returns  The new scenario
        """
        if self.is_new:
            new_scenario = self.scenario_inputs[self.new_scenario_id].json()
            return self.new_scenario_id, new_scenario
        return None, None

    def delete(self, request, del_button, del_name) -> list[str]:
        """Remove scenarios that are scheduled to be deleted"""

        scenarios_ids_to_delete = []
        # Only delete scenarios if the Delete button was clicked
        if is_in_request(request, del_button):
            scenarios_ids_to_delete = get_scenarios(request, del_name)

            # Never remove the default
            if self.default in scenarios_ids_to_delete:
                scenarios_ids_to_delete.remove(self.default)

            # Remove the scenarios scheduled for deletion
            self.scenario_inputs = {
                key: value
                for key, value in self.scenario_inputs.items()
                if key not in scenarios_ids_to_delete
            }

        return scenarios_ids_to_delete

    def get(self):
        """Get the scenario inputs"""
        return self.scenario_inputs

    def get_ids_to_plot(self, request, plot_name):
        """
        Get scenario ids that will be plotted
        """
        # Always plot any checked scenarios
        scenarios_ids_to_plot = get_scenarios(request, plot_name)
        scenarios_ids_to_plot = [
            sid for sid in scenarios_ids_to_plot if sid in self.scenario_inputs
        ]
        # If nothing else is indicated for plotting, plot the default
        if len(scenarios_ids_to_plot) == 0:
            scenarios_ids_to_plot = [self.default]
        return scenarios_ids_to_plot

    def include_default(self):
        """
        Always include default scenario in the list of scenarios
        @params scenario_inputs
        @params
        """
        if self.default not in self.scenario_inputs:
            dflt_params = {
                "inv_time_constant": [""],
                "transition_year": [""],
                "transition_duration": [""],
                "long_term_emissions": [""],
                "albedo_with_no_constraint": [""],
                "albedo_feedback": [""],
                "temp_anomaly_feedback": [""],
                "stochastic_c_atm_std_dev": [""],
                "scenario_name": ["hi"],
                "F_ha": ["on"],
                "flux": ["GtC/year"],
                "C_atm": ["on"],
                "carbon": ["GtC"],
                "T_anomaly": ["on"],
                "temp": ["C"],
                "pH": ["on"],
                "albedo": ["on"],
            }
            self.scenario_inputs[self.default] = CambioInputs.from_dict(dflt_params)


def include_default(scenario_inputs, default: str):
    """
    Always include default scenario in the list of scenarios
    @params scenario_inputs
    @params
    """
    if default not in scenario_inputs:
        dflt_params = {
            "inv_time_constant": [""],
            "transition_year": [""],
            "transition_duration": [""],
            "long_term_emissions": [""],
            "albedo_with_no_constraint": [""],
            "albedo_feedback": [""],
            "temp_anomaly_feedback": [""],
            "stochastic_c_atm_std_dev": [""],
            "scenario_name": ["hi"],
            "F_ha": ["on"],
            "flux": ["GtC/year"],
            "C_atm": ["on"],
            "carbon": ["GtC"],
            "T_anomaly": ["on"],
            "temp": ["C"],
            "pH": ["on"],
            "albedo": ["on"],
        }
        scenario_inputs[default] = CambioInputs.from_dict(dflt_params)


def is_in_request(request: HttpRequest, name) -> bool:
    """
    Get the scenario ids to plot
    @params request  The HttpRequest
    @returns The scenario ids to plot
    """
    if name in request.GET.keys():
        return True
    return False


def get_scenarios(request: HttpRequest, get_prefix: str) -> list[str]:
    """
    Get the scenario ids to plot
    @params request  The HttpRequest
    @returns The scenario ids to plot
    """
    scenario_ids: list[str] = []
    for get_param in request.GET.keys():
        if not get_param.startswith(get_prefix):
            continue
        scenario_ids.append(get_param[len(get_prefix) :])
    return scenario_ids


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
