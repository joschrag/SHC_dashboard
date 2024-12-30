"""This script defines the page layout for the game page."""

import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/",
    name="Recorded games",
    title="Recorded games",
    description="Landing page.",
)


layout = [
    dbc.Row(dbc.Button("Record stats", id="record_game")),
]
