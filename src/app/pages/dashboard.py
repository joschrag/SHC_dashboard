"""This script defines the page layout for the game page."""

import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src import APP_CATEGORIES, IMAGE_PATHS

logger = logging.getLogger("src")
dash.register_page(__name__, path_template="/dashboard/<db_id>")


def layout(db_id: str | None = None, **kwargs) -> list:
    """Create the dashboard page.

    Args:
        db_id (str | None, optional): dashboard id used in callbacks. Defaults to None.

    Returns:
        list: dashboard page layout
    """
    return [
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
