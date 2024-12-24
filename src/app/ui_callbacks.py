"""This script contains the callbacks used in the app ui generation."""

import logging

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, html, no_update

from src import APP_CATEGORIES, IMAGE_PATHS

logger = logging.getLogger(__name__)


@callback(
    [
        Output("stat-icons", "children"),  # Update the category row
        Output("substat-icons", "children"),  # Update the subcategory row
    ],
    [Input({"type": "col-switch", "index": ALL}, "n_clicks")],  # Listen to clicks on categories
    [State({"type": "col-switch", "index": ALL}, "id")],
)
def toggle_subcategories(n_clicks: list, ids: list) -> tuple:
    """Toggle categories and subcategories on and off.

    Args:
        n_clicks (list): number of clicks on categories
        ids (list): ids of categories

    Returns:
        tuple: categories and subcategories lists
    """
    if not any(n_clicks):  # If no clicks, return the default layout
        return no_update, []

    # Find the clicked category
    clicked_index = next((id["index"] for n, id in zip(n_clicks, ids) if n), None)
    logger.info(clicked_index)
    # Highlight the clicked category
    categories = [
        dbc.Col(
            html.Div(
                [
                    html.Img(
                        src=dash.get_relative_path(f"/assets/img/{IMAGE_PATHS[col]['img_path']}"),
                        className="category",
                    ),
                    html.P(col, className="category"),
                ],
                className=f"cat-div {'highlight' if col == clicked_index else ''}",
                id={"type": "col-switch", "index": col},
            ),
            width=2,
        )
        for col in APP_CATEGORIES
    ]

    # Create subcategories for the clicked category
    subcategories = [
        html.Div(
            [
                html.Img(
                    src=dash.get_relative_path(f"/assets/img/{IMAGE_PATHS[sub]['img_path']}"),
                    className="subcategory",
                ),
                html.P(sub, className="subcategory"),
            ],
            className="subcat-div",
            id={"type": "graph-switch", "index": sub},
        )
        for sub in APP_CATEGORIES.get(clicked_index, [])
    ]

    return categories, subcategories
