"""This script defines the page layout for the game page."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src import APP_CATEGORIES, IMAGE_PATHS

dash.register_page(
    __name__,
    path="/",
    name="Live Game Stats",
    title="Live Game Stats",
    description="Landing page.",
)


layout = [
    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    [
                        html.Img(
                            src=dash.get_relative_path(f"/assets/img/{IMAGE_PATHS[col]['img_path']}"),
                            className="category",
                        ),
                        html.P(col, className="category"),
                    ],
                    id={"type": "col-switch", "index": col},
                    className="cat-div",
                ),
                width=2,
            )
            for col in APP_CATEGORIES
        ],
        id="stat-icons",
    ),
    dbc.Row(id="substat-icons"),
    dbc.Row(dcc.Graph(id="stat-display")),
]
