"""This script defines the dash app and its template layout."""

import dash
import dash_bootstrap_components as dbc
import diskcache
import numpy as np
from dash import dcc, html
from dash.long_callback import DiskcacheLongCallbackManager

from . import data_callbacks, graph_callbacks, ui_callbacks  # noqa: F401


def init_dash_app(read_interval: float = 10) -> dash.Dash:
    """Initialize the dash app with the desired read interval per second.

    Args:
        read_interval (float, optional): ticks of interval component per second. Defaults to 10.

    Returns:
        dash.Dash: dash app object
    """
    cache = diskcache.Cache("./cache")
    long_callback_manager = DiskcacheLongCallbackManager(cache)
    app = dash.Dash(
        __name__,
        use_pages=True,
        external_stylesheets=[dbc.themes.MATERIA, "assets/style.css"],
        long_callback_manager=long_callback_manager,
        update_title="",
    )
    nav_link_style = {
        "margin": "1em 1em",
        "textAlign": "center",
        "padding": "0.5em 2em",
    }

    navbar = dbc.Navbar(
        [
            # Use row and col to control vertical alignment of logo / brand
            dbc.Nav(
                [
                    dbc.NavLink("Game", href="/", active="exact", style=nav_link_style),
                    dbc.NavLink(
                        "Dashboard",
                        href="/dashboard",
                        active="exact",
                        style=nav_link_style,
                    ),
                    dbc.NavLink(
                        "Settings",
                        href="/settings",
                        active="exact",
                        style=nav_link_style,
                    ),
                ],
                vertical=False,
                pills=True,
            )
        ],
        style={
            "padding-left": "10em",
            "padding-bottom": "3em",
            "border": "none",
            "width": "auto",
            "box-shadow": "none",
            "background-color": "none",
        },
    )

    app.layout = dbc.Container(
        children=[
            navbar,
            dbc.Row(html.Div(dash.page_container)),
            dcc.Interval(id="game_read", interval=np.round(1000 * read_interval)),
            dcc.Interval(id="1_min", interval=1000 * 60),
            dcc.Interval(id="10_min", interval=1000 * 10 * 60),
            dcc.Store("cards_store_train", storage_type="session"),
            dcc.Store("cards_store_game", storage_type="session"),
            dcc.Store("settings_store", storage_type="session"),
            dcc.Store("game_store", storage_type="memory"),
            dcc.Store("col_store", storage_type="session"),
            dcc.Store("lord_store", storage_type="session"),
            dcc.Store("map_store", storage_type="session"),
        ],
        className="dbc",
        fluid=True,
    )
    return app
