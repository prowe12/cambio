"""
By Penny Rowe and Daniel Neshyba
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from plotly.offline import plot
from plotly.graph_objs import Scatter
import numpy as np
from django.db.models import Min, Max

from cambio.utils.cambio import cambio

def index(request):
    # Values that must be in the database
    defaultyear = 2100

    # Need to remove this
    climvar = request.GET.get('climvar', 'f_ha')
    disp_scenario = "3"
    year = 2022
    
    # Default values
    inputs = {
        "start_year": 1750,  #<!-- start_year"><br> -->
        "stop_year": 2200,  #stop_year"><br> -->
        "dtime": 1.,  #dtime"><br> time resolution (years) -->
        "inv_time_constant": 0.025,  #inv_time_constant"><br> -->
        "transition_year": 2040.,  #transition_year"><br> # year to start decreasing CO2 -->
        "transition_duration": 20.,  #transition_duration"><br> years over which to decrease co2  -->
        "long_term_emissions": 2.,  #long_term_emissions"><br> # ongoing carbon emissions after decarbonization  -->
        "albedo_with_no_constraint": "False",  #albedo_with_no_constraint"><br> -->
        "albedo_feedback": "False",  #albedo_feedback"><br> -->
        "temp_anomaly_feedback": "False",  #temp_anomaly_feedback"><br> -->
        "stochastic_C_atm": "False",  #stochastic_C_atm"><br> -->
        "stochastic_c_atm_std_dev": 0.1,  #stochastic_c_atm_std_dev"> <br> -->
        "temp_units": "F",  #temp_units"><br> # F, C, or K -->
        "c_units": "GtC",  #c_units"><br> GtC, GtCO2, atm  -->
        "flux_type": "/year",  #flux_type"><br> # total, per year-->
        "plot_flux_diffs": "True",  #plot_flux_diffs"><br> -->
    }


    # Get variables from GET params
    varnames = {
        'start_year': 'float',
        'stop_year': 'float',
        'dtime': 'float',
        'inv_time_constant': 'float',
        'transition_year': 'float',
        'transition_duration': 'float',
        'long_term_emissions': 'float',
        'albedo_with_no_constraint': 'bool', #albedo_with_no_constraint"><br> -->
        'albedo_feedback': 'bool', #albedo_feedback"><br> -->
        'temp_anomaly_feedback': 'bool', #temp_anomaly_feedback"><br> -->
        'stochastic_C_atm': 'bool', #stochastic_C_atm"><br> -->
        'stochastic_c_atm_std_dev': 'float', #stochastic_c_atm_std_dev"> <br> -->
        'temp_units':'str', #temp_units"><br> # F, C, or K -->
        'c_units':'str', #c_units"><br> GtC, GtCO2, atm  -->
        'flux_type':'str', #flux_type"><br> # total, per year-->
        'plot_flux_diffs':'str', #plot_flux_diffs"><br> -->
    }
    for varname,vartype in varnames.items():
        try:
            valstr = request.GET.get(varname, 'nan')
            if valstr != '':
                if vartype == 'float':
                    inputs[varname] = float(valstr)
                elif vartype == 'bool':
                    inputs[varname] = bool(valstr)
        except:
            print(varname)

    # Run the model
    climate, climate_params = cambio(
    inputs['start_year'],
    inputs['stop_year'],
    inputs['dtime'],
    inputs['inv_time_constant'],
    inputs['transition_year'],
    inputs['transition_duration'],
    inputs['long_term_emissions'],
    inputs['stochastic_c_atm_std_dev'],
    inputs['albedo_with_no_constraint'],
    inputs['albedo_feedback'],
    inputs['stochastic_C_atm'],
    inputs['temp_anomaly_feedback'],
    inputs['temp_units'],
    inputs['flux_type'],
    inputs['plot_flux_diffs'],
    )



    # TODO: The possible number of scenarios is hard-wired here. Fix this.
    # scenarios = [i for i in range(1,17) if request.GET.get(f'scenario{i}', None) is not None]
    

    # query database
    scenarios = [0]
    climvarval_selected_names = ["F_ha", "T_anomaly", "pH","albedo"]
    climvarvals = [[] for i in range(len(climvarval_selected_names))]


    # get the new scenario
    for i,name in enumerate(climvarval_selected_names):
        climvarvals[i].append(climate[name])


    years = []
    years.append(climate["year"])



    colors = [
        'red',
        'orange',
        'yellow',
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

    # The plot
    if len(scenarios)==0:
        plot_div=''
    else:
        plot_divs = []
        for climvar_name, climvarval in zip(climvarval_selected_names, climvarvals):
            plot_divs.append(plot({'data':
            [
                Scatter(x=xvals, y=yvals,
                        mode='lines', name=f'Scenario {scenarios[i]}',
                        opacity=0.8, marker_color=colors[i%len(colors)]) \
                for i,(xvals,yvals) in enumerate(zip(years,climvarval))
            ],
                    'layout': {'xaxis': {'title': 'year'},
                    'yaxis': {'title': climvar_name}}},
            output_type='div', include_plotlyjs=False))
        print("plot divs len:", len(plot_divs))

    # Names for displaying climate variables
    climvar_names = {
                     'f_ha': 'CO2 flux from humans (GTC)',
                     'atmos_co2': 'Atmospheric CO2 (GTC)',
                     'ocean_co2': 'Ocean CO2 (GTC)',
                     'ocean_ph': 'Ocean pH (GTC)',
                     't_C': 'temperature (C)',
                     't_F': 'temperature (F)',
                     't_anomaly': 'temp. anomaly (C)',
                     'albedo': 'albedo',
                     'f_oa': 'CO2 flux from ocean (GTC)',
                     'f_la': 'CO2 flux from land (GTC)',
                     'tot_ha': 'total CO2 from humans (GTC)',
                    }

    climvar_names_bot = dict(climvar_names) # {key:value for key,value in climvar_names}
    climvar_names_bot['year'] = 'year'

    disp_outyear = {}
    # SQL: disp_inp <-- select * from ClimInputs where scenario=disp_scenario
    #disp_inp = get_object_or_404(ClimInputs, scenario=disp_scenario)

    # TODO: add elif for when year is in the database, so no need to interpolate
    # disp_outyear = disp_inp.climoutputs_set.get(year=year)

    # disp_out = {}
    # if year == '' or year is None:
    #     disp_outyear['year'] = ''
    #     disp_yearbef = (disp_inp.climoutputs_set.get(year=defaultyear)).get_fields()
    #     for i,(name, value) in enumerate(disp_yearbef):
    #         if name != 'id' and name != 'scenario':
    #             disp_outyear[name] = ''
    #             disp_out[climvar_names_bot[name]] = ''
    # else:
    #     # SQL: select [atts of climoutputs] from disp_inp natural_join climoutputs
    #     disp_all = disp_inp.climoutputs_set.all()

    #     year = float(year)
    #     yearmin = disp_all.all().aggregate(Min('year'))['year__min']
    #     yearmax = disp_all.all().aggregate(Max('year'))['year__max']
    #     if year < yearmin:
    #         year = yearmin
    #     elif year > yearmax:
    #         year = yearmax

    #     # Get the indices to the year before and after the years of interest
    #     # Product.objects.all().aggregate(Min('price'))
    #     iyear = [i for i,disp_year in enumerate(disp_all) if disp_year.year>=int(year)][0]
    #     if iyear <= 0:
    #         iyear = 1

    #     # Interpolate everything to the selected year
    #     yearbef = disp_all[iyear-1].year
    #     yearaft = disp_all[iyear].year
    #     wtaft = (year-yearbef)/(yearaft-yearbef)
    #     wtbef = (yearaft-year)/(yearaft-yearbef)
    #     disp_yearbef = (disp_inp.climoutputs_set.get(year=yearbef)).get_fields()
    #     disp_yearaft = (disp_inp.climoutputs_set.get(year=yearaft)).get_fields()
    #     for i,(name, value) in enumerate(disp_yearbef):
    #         if name != 'id' and name != 'scenario':
    #             res = round(wtbef * float(value) + wtaft * float(disp_yearaft[i][1]), 2)
    #             disp_outyear[name] = res
    #             disp_out[climvar_names_bot[name]] = str(res)

    climateinputs = []
    disp_out = []
    
    context = {
        'climateinputs': climateinputs,
        'years': years,
        'scenario': scenarios,
        'climvar': climvar,
        'disp_scenario': disp_scenario,
        'year': year,
        'plot_divs': plot_divs,
        'climvar_names': climvar_names,
        'disp_out': disp_out,
    }
    return render(request, 'cambio/index.html', context)
