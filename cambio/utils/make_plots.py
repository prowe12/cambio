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
        inputs = clean_inputs(inputs)

        conversion_funs_general = {
            "carbon": {"GtC": return_same, "atm": gtc_to_atm, "GtCO2": gtc_to_gtco2},
            "flux": {"GtC/year": return_same, "GtCO2/year": return_same},
            "temp": {"C": return_same, "K": celsius_to_kelvin, "F": celsius_to_f},
            "temp_anomaly": {"C": return_same, "K": return_same, "F": dt_c_to_dt_f},
            "none": {"": return_same},
        }

        # Set the conversions for converting from each name, default unit to unit
        self.conversion_funs = {
            "C_atm": conversion_funs_general["carbon"],
            "C_ocean": conversion_funs_general["carbon"],
            "F_ha": conversion_funs_general["flux"],
            "F_la": conversion_funs_general["flux"],
            "F_al": conversion_funs_general["flux"],
            "F_ao": conversion_funs_general["flux"],
            "F_oa": conversion_funs_general["flux"],
            "T_C": conversion_funs_general["temp"],
            "T_anomaly": conversion_funs_general["temp_anomaly"],
            "pH": conversion_funs_general["none"],
            "albedo": conversion_funs_general["none"],
        }

        self.plot_stuff = {
            "carbon": {
                "plot": [],
                "vars": {
                    "C_atm": "Atmospheric carbon",
                    "C_ocean": "Oceanic carbon",
                },
                "units": list(conversion_funs_general["carbon"].keys()),
                "selected_vars": ["C_atm"],
                "selected_unit": "GtC",
                "label": "Carbon amount",
            },
            "flux": {
                "plot": [],
                "vars": {
                    "F_ha": "Flux human->atmosphere",
                    "F_ao": "Flux atmosphere->ocean",
                    "F_oa": "Flux ocean->atmosphere",
                    "F_la": "Flux land->atmosphere",
                    "F_al": "Flux atmosphere->land",
                },
                "units": list(conversion_funs_general["flux"].keys()),
                "selected_vars": ["F_ha"],
                "selected_unit": "GtC/year",
                "label": "Flux",
            },
            "temp": {
                "plot": [],
                "vars": {
                    "T_anomaly": "Global temperature change",
                    "T_C": "Global temperature",
                },
                "units": list(conversion_funs_general["temp"].keys()),
                "selected_vars": ["T_anomaly"],
                "selected_unit": "C",
                "label": "Temperature",
            },
            "pH": {
                "plot": [],
                "vars": {"pH": "pH"},
                "units": [],
                "selected_vars": ["pH"],
                "selected_unit": "",
                "label": "pH",
            },
            "albedo": {
                "plot": [],
                "vars": {"albedo": "albedo"},
                "units": [],
                "selected_vars": ["albedo"],
                "selected_unit": "",
                "label": "albedo",
            },
        }

        for panel, values in self.plot_stuff.items():
            # Replace selected vars with get parameters, if present
            plot_vars = list(values["vars"].keys())  # [y[0] for y in values["vars"]]
            selected_vars = [x for x in inputs.keys() if x in plot_vars]
            if len(selected_vars) > 0:
                values["selected_vars"] = selected_vars

            # Replace selected units with get parameters, if present
            units = values["units"]
            selected_unit = [y for x, y in inputs.items() if x in panel]
            if len(selected_unit) > 0 and selected_unit[-1] in units:
                values["selected_unit"] = selected_unit[-1]

    def make(
        self,
        scenarios: list[dict[str, CambioVar]],
    ) -> dict:
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
            years: list[CambioVar] = []
            climvarvals: list[float | CambioVar] = []
            # Loop over variables to plot in each panel
            for name in values["selected_vars"]:
                # label = values[""]
                unit = values["selected_unit"]
                conversion_fun = self.conversion_funs[name][unit]

                label = values["vars"][name]
                if len(unit) > 0:
                    unit = f"({unit})"
                ylabel = f"{values['label']}  {unit}"

                # Loop over the scenarios and append the variables needed for the plot
                for scenario in scenarios:
                    scenario_id = scenario["scenario_id"]
                    yvals = conversion_fun(scenario[name])
                    climvarvals.append(yvals)
                    years.append(scenario["year"])
                    legend_labels.append(f"{scenario_id}: {label}")
            # Set all the plots for this panel
            values["plot"] = self.plot_panel(years, climvarvals, legend_labels, ylabel)

        return self.plot_stuff

    def plot_panel(
        self,
        years: list[npt.NDArray[np.float64]],
        climvarvals: list[npt.NDArray[np.float64]],
        names: list[str],
        ylabel: str,
    ):
        """
        Return a plot
        @param years
        @param climvarvals
        @param names
        @param ylabel
        @returns a plotly plot object
        """
        return plot(
            {
                "data": [
                    Scatter(
                        x=xvals,
                        y=yvals,
                        mode="lines",
                        name=name,
                        opacity=0.8,
                        marker_color=getcolor(i),
                    )
                    for i, (xvals, yvals, name) in enumerate(
                        zip(years, climvarvals, names)
                    )
                ],
                "layout": {
                    "xaxis": {"title": "year"},
                    "yaxis": {"title": ylabel},
                },
            },
            output_type="div",
            include_plotlyjs=False,
        )


def return_same(x: float) -> float:
    return x


def dt_c_to_dt_f(x: float) -> float:
    return x * 9 / 5


def gtc_to_gtco2(x: float) -> float:
    return x / 0.27


def gtc_to_atm(x: float) -> float:
    return x / 2.12


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
