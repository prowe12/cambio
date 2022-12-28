"""
By Penny Rowe and Daniel Neshyba
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter

from cambio.utils.cambio import cambio
from cambio.utils.cambio_utils import celsius_to_f, celsius_to_kelvin


def getcolor(i) -> str:
    """
    Return a a color
    @returns  A string representing a color
    """
    colors = [
        'red',
        'orange',
        'green',
        'cyan',
        'blue',
        'magenta',
        'black',
        'gray',
        'cornflowerblue',
        'olive',
        'tomato',
        'rosybrown',
        'cadetblue',
        'orchid',
        'purple',
    ]
    j = i%len(colors)
    return colors[j]

def get_scenario_units(request):
    """
    Get the units from the request
    """
    inputs = parse_cambio_inputs_for_units(request.GET)
    units = {}
    units["temp_units"] = inputs["temp_units"]
    return units


def parse_cambio_inputs_for_cookies(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """
    
    # Default values
    inputs = {
        "start_year": 1750.0,  #<!-- start_year"><br> -->
        "stop_year": 2200.0,  #stop_year"><br> -->
        "dtime": 1.,  #dtime"><br> time resolution (years) -->
        "inv_time_constant": 0.025,  #inv_time_constant"><br> -->
        "transition_year": 2040.0,  #transition_year"><br> # year to start decreasing CO2 -->
        "transition_duration": 20.0,  #transition_duration"><br> years over which to decrease co2  -->
        "long_term_emissions": 2.0,  #long_term_emissions"><br> # ongoing carbon emissions after decarbonization  -->
        "albedo_with_no_constraint": False,  #albedo_with_no_constraint"><br> -->
        "albedo_feedback": False,  #albedo_feedback"><br> -->
        "temp_anomaly_feedback": False,  #temp_anomaly_feedback"><br> -->
        "stochastic_C_atm": False,  #stochastic_C_atm"><br> -->
        "stochastic_c_atm_std_dev": 0.1,  #stochastic_c_atm_std_dev"> <br> -->
    }
    varnames = {
        'start_year': float,
        'stop_year': float,
        'dtime': float,
        'inv_time_constant': float,
        'transition_year': float,
        'transition_duration': float,
        'long_term_emissions': float,
        'albedo_with_no_constraint': bool,
        'albedo_feedback': bool,
        'temp_anomaly_feedback': bool,
        'stochastic_C_atm': bool,
        'stochastic_c_atm_std_dev': float,
    }

    for varname,vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == '':
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs

def parse_cambio_inputs(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """
    
    # Default values
    inputs = {
        "start_year": 1750.0,  #<!-- start_year"><br> -->
        "stop_year": 2200.0,  #stop_year"><br> -->
        "dtime": 1.,  #dtime"><br> time resolution (years) -->
        "inv_time_constant": 0.025,  #inv_time_constant"><br> -->
        "transition_year": 2040.0,  #transition_year"><br> # year to start decreasing CO2 -->
        "transition_duration": 20.0,  #transition_duration"><br> years over which to decrease co2  -->
        "long_term_emissions": 2.0,  #long_term_emissions"><br> # ongoing carbon emissions after decarbonization  -->
        "albedo_with_no_constraint": False,  #albedo_with_no_constraint"><br> -->
        "albedo_feedback": False,  #albedo_feedback"><br> -->
        "temp_anomaly_feedback": False,  #temp_anomaly_feedback"><br> -->
        "stochastic_C_atm": False,  #stochastic_C_atm"><br> -->
        "stochastic_c_atm_std_dev": 0.1,  #stochastic_c_atm_std_dev"> <br> -->
        "temp_units": "F",  #temp_units"><br> # F, C, or K -->
        "c_units": "GtC",  #c_units"><br> GtC, GtCO2, atm  -->
        "flux_type": "/year",  #flux_type"><br> # total, per year-->
        "plot_flux_diffs": True,  #plot_flux_diffs"><br> -->
    }
    varnames = {
        'start_year': float,
        'stop_year': float,
        'dtime': float,
        'inv_time_constant': float,
        'transition_year': float,
        'transition_duration': float,
        'long_term_emissions': float,
        'albedo_with_no_constraint': bool,
        'albedo_feedback': bool,
        'temp_anomaly_feedback': bool,
        'stochastic_C_atm': bool,
        'stochastic_c_atm_std_dev': float,
        'temp_units':str,
        'c_units':str,
        'flux_type':str,
        'plot_flux_diffs':bool,
    }

    for varname,vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == '':
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs

def parse_cambio_inputs_for_units(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """
    
    # Default values
    inputs = {
        "temp_units": "F",  #temp_units"><br> # F, C, or K -->
        "c_units": "GtC",  #c_units"><br> GtC, GtCO2, atm  -->
        "flux_type": "/year",  #flux_type"><br> # total, per year-->
        "plot_flux_diffs": True,  #plot_flux_diffs"><br> -->
    }
    varnames = {
        'temp_units':str,
        'c_units':str,
        'flux_type':str,
        'plot_flux_diffs':bool,
    }

    for varname,vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == '':
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs

def run_model(scenario_inputs, request) -> list[dict]:
    """
    Run the model for the inputs
    @param scenario_inputs
    @param request
    @returns Climate model run outputs
    """
    
    # Get cambio inputs from GET params for saving to cookies
    # and if the new scenario is different from all old scenarios, add it
    inputs = parse_cambio_inputs_for_cookies(request.GET)
    new_hash = str(hash(json.dumps(inputs)))
    if new_hash not in request.COOKIES.keys():
        scenario_inputs.append(inputs)

    # Run the model
    scenarios = []
    for scenario_input in scenario_inputs:
        climate, _ = cambio(
            scenario_input['start_year'],
            scenario_input['stop_year'],
            scenario_input['dtime'],
            scenario_input['inv_time_constant'],
            scenario_input['transition_year'],
            scenario_input['transition_duration'],
            scenario_input['long_term_emissions'],
            scenario_input['stochastic_c_atm_std_dev'],
            scenario_input['albedo_with_no_constraint'],
            scenario_input['albedo_feedback'],
            scenario_input['stochastic_C_atm'],
            scenario_input['temp_anomaly_feedback'],
        )
        scenarios.append(climate)
    return scenarios

def make_plots(scenarios, scenario_inputs):
    """
    Return the plots that will be displayed
    @param scenarios  The climate model run results
    @param scenario_inputs The climate model run inputs (only units currently used)
    @returns  The plots
    """


    # if scenario_inputs["c_units"] == "GtC":
    #     carbon = "F_ha"
    # else:
    #     raise ValueError("units not found")
    
    # if scenario_inputs["flux_type"] == "/year":
    #     pass
    # else:
    #     raise ValueError("units not found")

    climvarval_selected_names = ["F_ha", "T_C", "pH", "albedo"]
    climvarvals = [[] for i in range(len(climvarval_selected_names))]
    labels = [[] for i in range(len(climvarval_selected_names))]

    # get all scenarios
    years = []
    for scenario in scenarios:
        for i,name in enumerate(climvarval_selected_names):
            unit_name = ""
            label = name
            if name == "T_C":
                unit_name = scenario_inputs["temp_units"]
                label = "temperature" + " (" + unit_name + ")"
                if unit_name == "F":
                    yvals = celsius_to_f(scenario[name])
                    print("\n yvals:")
                    print(yvals)
                elif unit_name == "K":
                    yvals = celsius_to_kelvin(scenario[name])
                else:
                    yvals = scenario[name]
            else:
                yvals = scenario[name]
            climvarvals[i].append(yvals)
            labels[i] = label
            
        years.append(scenario["year"])

    # print("climvarvals is:", climvarvals)

    # The plots
    plot_divs = []
    if len(scenarios)>0:
        for climvar_name, climvarval, label in zip(climvarval_selected_names, climvarvals, labels):
            print(f'plotting {climvar_name}, there should be {len(climvarval)} simulations')
            plot_divs.append(plot({'data':
            [
                Scatter(x=xvals, y=yvals,
                        mode='lines', name=f'Scenario {i}',
                        opacity=0.8, marker_color=getcolor(i)) \
                for i,(xvals,yvals) in enumerate(zip(years,climvarval))
            ],
                    'layout': {'xaxis': {'title': 'year'},
                    'yaxis': {'title': label}}},
            output_type='div', include_plotlyjs=False))
            
    return plot_divs

def index(request):
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # Get cambio inputs from cookies
    cookie_scenarios = [json.loads(value) for input, value in request.COOKIES.items()]
    cookie_scenarios = list(filter(lambda x: isinstance(x, dict), cookie_scenarios))
    scenario_inputs = [parse_cambio_inputs(scenario) for scenario in cookie_scenarios]
    scenario_units = get_scenario_units(request)
    # scenario_units = get_scenario_units(request.GET)


    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    scenarios = run_model(scenario_inputs, request)

    # Make the plots
    plot_divs = make_plots(scenarios, scenario_units)

    # Buttons to select what to plot
    climateinputs = [] # "C_atm", "C_ocean"]
#         climatestate["C_atm"] = c_atm
#     climatestate["C_ocean"] = c_ocean
#     climatestate["albedo"] = albedo
#     climatestate["T_anomaly"] = t_anom
#     climatestate["pH"] = pH
#     climatestate["T_C"] = T_C
#     # climatestate["T_F"] = T_F
#     climatestate["F_ha"] = F_ha
#     climatestate["F_ao"] = F_ao
#     climatestate["F_oa"] = F_oa
#     climatestate["F_la"] = F_la
#     climatestate["F_al"] = F_al
# ]
    
    # Variables to pass to html
    context = {
        'plot_divs': plot_divs,
        'climateinputs': climateinputs,
    }
    response = render(request, 'cambio/index.html', context)

    # save latest run in cookies
    scenario = json.dumps(scenario_inputs[-1])
    scenario_hash = str(hash(scenario))
    # don't add the new scenario to cookies if it already exists
    if scenario_hash not in request.COOKIES.keys():
        response.set_cookie(scenario_hash, scenario)

    return response


# Names for displaying climate variables
# climvar_names = {
#                  'f_ha': 'CO2 flux from humans (GTC)',
#                  'atmos_co2': 'Atmospheric CO2 (GTC)',
#                  'ocean_co2': 'Ocean CO2 (GTC)',
#                  'ocean_ph': 'Ocean pH (GTC)',
#                  't_C': 'temperature (C)',
#                  't_F': 'temperature (F)',
#                  't_anomaly': 'temp. anomaly (C)',
#                  'albedo': 'albedo',
#                  'f_oa': 'CO2 flux from ocean (GTC)',
#                  'f_la': 'CO2 flux from land (GTC)',
#                  'tot_ha': 'total CO2 from humans (GTC)',
#                 }
