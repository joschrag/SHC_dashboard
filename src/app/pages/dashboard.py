"""This script defines the page layout for the game page."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc

dash.register_page(
    __name__,
    path="/",
    name="Live Game Stats",
    title="Live Game Stats",
    description="Landing page.",
)

col_list = [
    "num_eco_buildings",
    "num_total_buildings",
    "total_gold",
    "weighted_troops_killed",
    "weighted_buildings_destroyed",
    "goods_received",
    "goods_sent",
    "housing",
    "units",
    "siege_engines",
    "popularity",
    "wood",
    "hops",
    "stone",
    "iron",
    "pitch",
    "wheat",
    "bread",
    "cheese",
    "meat",
    "apples",
    "ale",
    "gold",
    "flour",
    "bows",
    "crossbows",
    "spears",
    "pikes",
    "maces",
    "swords",
    "leather_armor",
    "metal_armor",
    "total_food",
    "population",
    "taxes",
    "weighted_losses",
    "weighted_units",
    "num_farms",
    "num_iron_mines",
    "num_pitchrigs",
    "num_quarries",
    "num_buildings",
    "workers_needed",
    "workers_working",
    "workers_missing",
    "snoozed",
]

layout = [
    dbc.Row(
        [
            dbc.Col(dcc.Dropdown(id="lord-select", multi=True)),
        ]
    ),
    dbc.Row(
        [
            dbc.Col([dbc.Button(col, id={"type": "col-switch", "index": col}) for col in col_list]),
        ]
    ),
    dbc.Row(dcc.Graph(id="stat-display")),
]
