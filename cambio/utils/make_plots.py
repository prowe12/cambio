"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

"""

from typing import Any
from plotly.offline import plot
from plotly.graph_objs import Scatter
from django.http import QueryDict
import numpy.typing as npt
import numpy as np

from cambio.utils.cambio_utils import CambioVar, celsius_to_f, celsius_to_kelvin


class MakePlots:
    """
    Make the plots, depending on user-specified variables and units.
    Use defaults when not specified
    """

    def __init__(self, inputs: dict[str, str] | QueryDict):
        """
        Replace default inputs to CAMBIO with user-defined values
        """
        self.year_range = (1900.0, 2201.0)  # Year range to plot

        conversion_funs_general = {
            "carbon": {"GtC": return_same, "ppm": gtc_to_ppm, "GtCO2": gtc_to_gtco2},
            "flux": {"GtC/year": return_same, "GtCO2/year": gtc_to_gtco2},
            "temp": {"C": return_same, "K": celsius_to_kelvin, "F": celsius_to_f},
            "temp_anomaly": {"C": return_same, "K": return_same, "F": dt_c_to_dt_f},
            "none": {"": return_same},
        }

        # Set the conversions for converting from each name, default unit to unit
        self.conversion_funs = {
            "c_atm": conversion_funs_general["carbon"],
            "c_ocean": conversion_funs_general["carbon"],
            "flux_ha": conversion_funs_general["flux"],
            "flux_la": conversion_funs_general["flux"],
            "flux_al": conversion_funs_general["flux"],
            "flux_ao": conversion_funs_general["flux"],
            "flux_oa": conversion_funs_general["flux"],
            "netflux_oa": conversion_funs_general["flux"],
            "netflux_la": conversion_funs_general["flux"],
            "temp_c": conversion_funs_general["temp"],
            "temp_anomaly": conversion_funs_general["temp_anomaly"],
            "albedo_trans_temp": conversion_funs_general["temp_anomaly"],
            "flux_al_trans_temp": conversion_funs_general["temp_anomaly"],
            "ph": conversion_funs_general["none"],
            "albedo": conversion_funs_general["none"],
        }
        # "temp_anomaly_feedback": conversion_funs_general["temp_anomaly"],

        self.plot_stuff = {
            "flux": {
                "plot": [],
                "vars": {
                    "flux_ha": ["Human&rarr;Atmos", "solid"],
                    "flux_ao": ["Atmos&rarr;Ocean", "20px"],
                    "flux_oa": ["Ocean&rarr;Atmos", "longdashdot"],
                    "flux_la": ["Land&rarr;Atmos", "longdash"],
                    "flux_al": ["Atmos&rarr;Land", "dashdot"],
                    "netflux_oa": ["Net, Ocean&harr;Atmos", "dot"],
                    "netflux_la": ["Net, Land&harr;Atmos ", "dash"],
                },
                "units": list(conversion_funs_general["flux"].keys()),
                "selected_vars": ["flux_ha"],
                "selected_unit": "GtC/year",
                "label": "Flux",
            },
            "carbon": {
                "plot": [],
                "vars": {
                    "c_atm": ["Atmospheric", "solid"],
                    "c_ocean": ["Oceanic", "dash"],
                },
                "units": list(conversion_funs_general["carbon"].keys()),
                "selected_vars": ["c_atm"],
                "selected_unit": "GtC",
                "label": "Carbon amount",
            },
            "temp": {
                "plot": [],
                "vars": {
                    "temp_anomaly": ["Temperature change", "solid"],
                    "temp_c": ["Temperature", "longdash"],
                    "albedo_trans_temp": ["Tipping Pt: albedo", "dashdot"],
                    "flux_al_trans_temp": ["Tipping Pt: forest", "dot"],
                },
                "units": list(conversion_funs_general["temp"].keys()),
                "selected_vars": ["temp_anomaly"],
                "selected_unit": "C",
                "label": "Temperature",
            },
            "pH": {
                "plot": [],
                "vars": {"ph": ["pH", "solid"]},
                "units": [],
                "selected_vars": ["ph"],
                "selected_unit": "",
                "label": "pH",
            },
            "albedo": {
                "plot": [],
                "vars": {"albedo": ["albedo", "solid"]},
                "units": [],
                "selected_vars": ["albedo"],
                "selected_unit": "",
                "label": "albedo",
            },
        }

        self.derived_inputs = {
            "netflux_oa": get_netflux_oa,
            "netflux_la": get_netflux_la,
        }

        inputs = clean_inputs(inputs)

        for panel, values in self.plot_stuff.items():
            # Replace selected vars with get parameters, if present
            plot_vars = list(values["vars"].keys())
            selected_vars = [x for x in inputs.keys() if x in plot_vars]

            if len(selected_vars) > 0:
                values["selected_vars"] = selected_vars

            # Replace selected units with get parameters, if present
            units = values["units"]
            selected_unit = [y for x, y in inputs.items() if x in panel]
            if len(selected_unit) > 0 and selected_unit[-1] in units:
                values["selected_unit"] = selected_unit[-1]

    def make(self, scenarios: list[dict[str, CambioVar]]) -> dict:
        """
        Return the plots that will be displayed.
        @param scenarios  The climate model run results
        @returns  The plots and associated data
        """

        if len(scenarios) == 0:
            return self.plot_stuff

        # Loop over plots (aka panels)
        # For each variable to plot
        for values in self.plot_stuff.values():
            legend_labels: list[str] = []
            line_colors: list[str] = []
            line_styles: list[str] = []
            years: list[CambioVar] = []
            climvarvals: list[float | CambioVar] = []

            # Loop over variables to plot in each panel
            # These correspond to the instance variables defined in the constructor
            for name in values["selected_vars"]:
                # Get units, conversion functions, labels, and line styles from the
                # instance variables defined in the constructor
                unit = values["selected_unit"]
                conversion_fun = self.conversion_funs[name][unit]

                label = values["vars"][name][0]
                line_style = values["vars"][name][1]
                if len(unit) > 0:
                    unit = f"({unit})"
                ylabel = f"{values['label']}  {unit}"

                # Loop over the scenarios input to this method, which represent the climate
                # model results, and append the variables that will be plotted
                for iscen, scenario in enumerate(scenarios):
                    scenario_id = scenario["scenario_id"]
                    year = scenario["year"]

                    # Get variables derived from other variables
                    if name not in scenario:
                        # Set input variables that will be plotted
                        if name in self.derived_inputs:
                            myfun = self.derived_inputs[name]
                            scenario[name] = myfun(scenario)
                        else:
                            raise ValueError("Variable cannot be plotted")

                    yvals = conversion_fun(scenario[name])
                    inds = get_years_to_plot(year, self.year_range)

                    if len(yvals) == len(year):
                        years.append(year[inds])
                        climvarvals.append(yvals[inds])
                    elif len(yvals) == 1:
                        # Constant values
                        years.append(np.array([year[inds[0]], year[inds[-1]]]))
                        climvarvals.append(np.array([yvals[0], yvals[0]]))
                    else:
                        raise ValueError("Bad length for variable to plot")

                    # Unique legend label and line color for each scenario
                    legend_labels.append(f"{label}: {scenario_id}")
                    line_colors.append(getcolor(iscen))

                    # Unique line style for each variable plotted (e.g. name)
                    line_styles.append(line_style)

            # Set all the plots for this panel
            values["plot"] = self.plot_panel(
                years,
                climvarvals,
                legend_labels,
                ylabel,
                line_colors,
                line_styles,
            )

        return self.plot_stuff

    def plot_panel(
        self,
        years: list[npt.NDArray[np.float64]],
        climvarvals: list[npt.NDArray[np.float64]],
        names_in: list[str],
        ylabel: str,
        line_colors: list[str],
        line_styles: list[str],
    ):
        """
        Return a plot
        @param years
        @param climvarvals
        @param names
        @param ylabel
        @returns a plotly plot object
        """

        names = []
        # Replace arrows with better symbols
        for name in names_in:
            if "&rarr;" in name:
                name = name.replace("&rarr;", "\u2192")
            if "&harr;" in name:
                name = name.replace("&harr;", "\u2194")
            names.append(name)

        return plot(
            {
                "data": [
                    Scatter(
                        x=xvals,
                        y=yvals,
                        mode="lines",
                        name=name,
                        opacity=0.8,
                        marker_color=line_color,
                        line_dash=line_style,
                        showlegend=True,
                    )
                    for i, (xvals, yvals, name, line_color, line_style) in enumerate(
                        zip(years, climvarvals, names, line_colors, line_styles)
                    )
                ],
                "layout": {
                    "xaxis": {"title": "year"},
                    "yaxis": {"title": ylabel},
                    "legend": {
                        "orientation": "h",
                        "entrywidth": 70,
                        "yanchor": "bottom",
                        "y": 1.02,
                        "xanchor": "right",
                        "x": 1,
                    },
                },
            },
            output_type="div",
            include_plotlyjs=False,
        )


def get_display_names() -> dict[str:str]:
    """
    Retrun the display names for the plot
    @returns  A dictionary of names for model and names for display
    """
    return {
        "transition_year": "Year CO2 emission peaks",
        "transition_duration": "Years to decarbonize",
        "long_term_emissions": "Long-term CO2 emissions",
        "albedo_transition_temp": "Albedo tipping point",
        "flux_al_transition_temp": "Forest tipping point",
        "stochastic_c_atm_std_dev": "Noise level",
        "scenario_name": "Scenario name",
    }
    # "temp_anomaly_feedback": "Forest fire feedback",


def get_netflux_oa(scenario: dict[float]):
    """
    Compute the net flux from ocean to atmosphere
    @param scenario  The climate model outputs
    @returns  The net flux from ocean to atmosphere
    """
    return scenario["F_oa"] - scenario["F_ao"]


def get_netflux_la(scenario):
    """
    Compute the net flux from land to atmosphere
    @param scenario  The climate model outputs
    @returns  The net flux from land to atmosphere
    """
    return scenario["F_la"] - scenario["F_al"]


def return_same(inp: float) -> float:
    """
    return same value
    @param inp value to return
    @returns  input value
    """
    return inp


def dt_c_to_dt_f(dtemp: np.ndarray[float]) -> np.ndarray[float]:
    """
    Convert temperature change in Celsius to temperature change
    in Fahrenheit
    @param dtemp  Temperature change in Celsius
    @returns  Temperature in Fahrenheit
    """
    return dtemp * 9 / 5


def gtc_to_gtco2(carbon: float) -> float:
    """
    Convert GTC to GTCO2
    @param  carbon  Carbon amount in GTC
    @returns  Carbon amount in GTCO2
    """
    return carbon / 0.27


def gtc_to_ppm(carbon: float) -> float:
    """
    Convert from GTC to ppm
    @param carbon  Carbon amount in GTC
    @returns  Carbon amount in ppm
    """
    return carbon / 2.12


def get_years_to_plot(
    year: npt.NDArray[np.float64], year_range: tuple[float, float]
) -> npt.NDArray[np.float64]:
    """
    Get indices to the years that will be plotted
    @param year  Original years
    @param year_range  First and last year of range to plot
    @returns  Indices to years that will be plotted
    """
    return np.where((year >= year_range[0]) & (year <= year_range[1]))[0]


def getcolor(i: int) -> str:
    """
    Return a a color
    @returns  A string representing a color
    """
    colors = [
        "red",
        "orange",
        "green",
        "cyan",
        "blue",
        "magenta",
        "black",
        "gray",
        "cornflowerblue",
        "olive",
        "tomato",
        "rosybrown",
        "cadetblue",
        "orchid",
        "purple",
    ]
    j = i % len(colors)
    return colors[j]


def clean_inputs(input_dict: dict[str, str] | QueryDict) -> dict[str, str]:
    """
    Return the dictionary after removing all key/value pairs that are
    not variables of the class
    @param input_dict  The dictionary with input variable names and values
    @returns  A dictionary of input variable names and values
    """
    return {key: value for key, value in input_dict.items() if value != ""}
