"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Inspired by Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from cambio.utils.view_utils import (
    run_model_for_dict,
)

#    make_plots,
from cambio.utils.make_plots import MakePlots
from cambio.utils.schemas import CambioInputs, ScenarioInputs


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

    # Get cambio inputs from cookies
    scenario_inputs: dict[str, CambioInputs] = {
        scenario_id: CambioInputs.from_json(scenario)
        for scenario_id, scenario in request.COOKIES.items()
    }

    # Get new scenario from get parameters for model run and for saving to cookies
    # *only* if it exists
    new_scenario_id = request.GET.get("scenario_name", "")
    if new_scenario_id != "":
        scenario_inputs[new_scenario_id] = CambioInputs.from_dict(request.GET)

    # Remove all scenarios that are scheduled to be deleted
    scenario_inputs = {
        key: value
        for key, value in scenario_inputs.items()
        if key not in scenarios_ids_to_delete
    }

    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    scenarios = run_model_for_dict(scenario_inputs)
    scenarios_to_plot = [
        scenarios[scenario_id]
        for scenario_id in scenarios_ids_to_plot
        if scenario_id in scenarios
    ]

    # Create the plots
    makePlots = MakePlots(inputs)
    plot_divs = makePlots.make(scenarios_to_plot)

    scenario_ids = list(scenarios.keys())
    plot_scenarios = [
        [scenario_id, f"plot_scenario_{scenario_id}"] for scenario_id in scenario_ids
    ]
    old_scenario_inputs = {
        scenario_id: scenario.dict()
        for scenario_id, scenario in scenario_inputs.items()
    }

    # Variables to pass to html
    context = {
        "plot_divs": plot_divs,
        "old_scenario_inputs": old_scenario_inputs,
        "scenarios": scenario_ids,
        "plot_scenarios": plot_scenarios,
        "inputs": ScenarioInputs().dict(),
    }
    response = render(request, "cambio/index.html", context)

    # If there is a new scenario in the get parameters, save it to cookies
    if new_scenario_id != "":
        scenario = scenario_inputs[new_scenario_id].json()
        response.set_cookie(new_scenario_id, scenario)

    # delete all unwanted scenarios:
    for cookie_name in scenarios_ids_to_delete:
        response.delete_cookie(cookie_name)

    return response
