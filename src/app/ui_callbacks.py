"""This script contains the callbacks used in the app ui generation."""

from dash import Input, Output, callback
from dash.exceptions import PreventUpdate


@callback(Output("lord-select", "options"), Input("lord_store", "data"))
def display_lord_dd(lord_names):
    if lord_names:
        return [{"label": "No owner", "value": 0}] + [
            {"label": lord_name, "value": i + 1} for i, lord_name in enumerate(lord_names)
        ]
    raise PreventUpdate()
