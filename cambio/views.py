"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Inspired by Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from cambio.utils.view_utils import ManageInputs, run_model_for_dict
from cambio.utils.view_utils import get_scenarios, is_in_request
from cambio.utils.make_plots import MakePlots, get_display_names
from cambio.utils.schemas import CambioInputs, ScenarioInputs


def index(request: HttpRequest) -> HttpResponse:
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # Get the scenario inputs from the default, the cookies, and new scenarios
    manageInputs = ManageInputs(request, "Default")

    # Remove scenarios set for deletion
    ids_to_delete = manageInputs.delete(request, "delete_button", "del_scenario")

    # Run the model on old and new inputs to get the climate model results
    scenario_inputs = manageInputs.get()
    scenarios = run_model_for_dict(scenario_inputs)

    # Always plot any checked scenarios
    ids_to_plot = manageInputs.get_ids_to_plot(request, "plot_scenario_")

    # Create the plots (for passing to the html)
    makePlots = MakePlots(request.GET)
    plot_divs = makePlots.make([scenarios[sid] for sid in ids_to_plot])

    # Get the other variables to pass to the html
    old_display_inputs = {sid: inp.dict() for sid, inp in scenario_inputs.items()}
    plot_scenario_choices = [[sid, f"plot_scenario_{sid}"] for sid in scenarios]
    plot_scenario_ids = [sid for sid in ids_to_plot if sid in scenarios]

    # Variables to pass to html
    context = {
        "plot_divs": plot_divs,
        "old_scenario_inputs": old_display_inputs,
        "plot_scenario_choices": plot_scenario_choices,
        "plot_scenario_ids": plot_scenario_ids,
        "inputs": ScenarioInputs().dict(),
        "display_names": get_display_names(),
    }
    response = render(request, "cambio/index.html", context)

    # If there is a new scenario in the get parameters, save it to cookies
    if manageInputs.new_exists():
        new_id, new_scenario = manageInputs.get_new()
        response.set_cookie(new_id, new_scenario)

    # Delete all unwanted scenarios:
    for cookie_name in ids_to_delete:
        response.delete_cookie(cookie_name)

    return response
