"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Inspired by Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from cambio.utils.view_utils import ManageInputs, run_model_for_dict, get_scenarios
from cambio.utils.make_plots import MakePlots
from cambio.utils.schemas import CambioInputs, ScenarioInputs


def index(request: HttpRequest) -> HttpResponse:
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # Get variables from request:
    scenarios_ids_to_plot = get_scenarios(request, "plot_scenario_")
    scenarios_ids_to_delete = get_scenarios(request, "del_scenario")

    # Get variables from request for use in plots
    inputs = request.GET

    # Name of default scenario
    default = "Default"

    # Get the scenario inputs from the request
    manageInputs = ManageInputs(request, default)

    # Remove scenarios that are scheduled to be deleted
    manageInputs.remove_deleted(scenarios_ids_to_delete, default)

    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    scenario_inputs = manageInputs.get()
    scenarios = run_model_for_dict(scenario_inputs)
    scenarios_ids_to_plot = [sid for sid in scenarios_ids_to_plot if sid in scenarios]

    # If nothing else is indicated for plotting, plot the default
    if len(scenarios_ids_to_plot) == 0:
        scenarios_ids_to_plot = [default]

    scenarios_to_plot = [scenarios[sid] for sid in scenarios_ids_to_plot]

    # Create the plots (for passing to the html)
    makePlots = MakePlots(inputs)
    plot_divs = makePlots.make(scenarios_to_plot)

    # Get the other variables to pass to the html
    scenario_ids = list(scenarios.keys())
    old_display_inputs = {sid: inp.dict() for sid, inp in scenario_inputs.items()}
    plot_scenario_choices = [[sid, f"plot_scenario_{sid}"] for sid in scenario_ids]
    plot_scenario_ids = [sid for sid in scenarios_ids_to_plot if sid in scenarios]

    display_names: dict = {
        "transition_year": "Year CO2 emission peaks",
        "transition_duration": "Years to decarbonize",
        "long_term_emissions": "Long-term CO2 emissions",
        "albedo_feedback": "Albedo feedback",
        "temp_anomaly_feedback": "Forest fire feedback",
        "stochastic_c_atm_std_dev": "Noise level",
        "scenario_name": "Scenario name",
    }

    # Variables to pass to html
    context = {
        "plot_divs": plot_divs,
        "old_scenario_inputs": old_display_inputs,
        "plot_scenario_choices": plot_scenario_choices,
        "plot_scenario_ids": plot_scenario_ids,
        "inputs": ScenarioInputs().dict(),  # display_inputs,  #
        "display_names": display_names,
    }
    response = render(request, "cambio/index.html", context)

    # If there is a new scenario in the get parameters, save it to cookies
    # if new_scenario_id != "":
    #     scenario = scenario_inputs[new_scenario_id].json()
    #     response.set_cookie(new_scenario_id, scenario)

    if manageInputs.new_exists():
        new_id, new_scenario = manageInputs.get_new()
        response.set_cookie(new_id, new_scenario)
        # new_scenario = scenario_inputs[new_scenario_id].json()
        # print()
        # print(new_scenario_id)
        # print(new_scenario)
        # response.set_cookie(new_scenario_id, new_scenario)

    # delete all unwanted scenarios:
    for cookie_name in scenarios_ids_to_delete:
        response.delete_cookie(cookie_name)

    return response
