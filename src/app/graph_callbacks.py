"""This script contains the callbacks used in the apps graph generation."""

import logging

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

from src import SHC_COLORS

logger = logging.getLogger(__name__)


@callback(
    Output("stat-display", "figure"),
    Output("col_store", "data"),
    Input("game_store", "data"),
    Input({"type": "graph-switch", "index": ALL}, "n_clicks"),
    State("col_store", "data"),
    State("lord_store", "data"),
    State("stat-display", "figure"),
)
def update_graph(game_data, _, last_column, lord_data, current_fig):
    """Update the display graph based on game and lord data."""
    column = last_column or "popularity"
    figure = go.Figure(current_fig) if current_fig else go.Figure()

    if not (game_data and lord_data and ctx.triggered_id):
        raise PreventUpdate()

    if isinstance(ctx.triggered_id, dict):
        column = ctx.triggered_id.get("index", column)

    df = pd.DataFrame(game_data).sort_values(["p_ID", "time"])
    df = df.merge(pd.DataFrame(lord_data), on="p_ID", how="left")

    # Identify and remove outliers
    tolerance = 5
    df["is_outlier"] = (
        ((df[column].shift(1) - df[column]).abs() > tolerance)
        & ((df[column].shift(-1) - df[column]).abs() > tolerance)
        & ((df[column].shift(1) - df[column].shift(-1)).abs() <= tolerance)
        & (df["p_ID"].shift(1) == df["p_ID"])
    ) | (df[column] > 10**9)
    df = df[~df["is_outlier"]]

    # Patch or add data to the figure
    if figure.data and ctx.triggered_id == "game_store":
        patched_figure = dash.Patch()

        max_x = max(max(filter(None, trace.x) or [0]) for trace in figure.data if trace.x is not None)
        df = df[df["time"] >= max_x]

        for p_id, group in df.groupby("p_ID"):
            patched_figure["data"][p_id - 1]["x"].extend(group["time"].tolist())
            patched_figure["data"][p_id - 1]["y"].extend(group[column].tolist())

        return patched_figure, column
    figure = go.Figure()
    for p_id, group in df.groupby("p_ID"):
        assert isinstance(p_id, int)
        team = group["teams"].iloc[0] if not group["teams"].isnull().all() else None
        legendgroup = f"Team {team}" if team else "No team"
        figure.add_trace(
            go.Scatter(
                x=group["time"],
                y=group[column],
                mode="lines",
                name=group["lord_names"].iloc[0],
                marker_color=SHC_COLORS[p_id - 1],
                legendgroup=legendgroup,
                legendgrouptitle_text=legendgroup,
            )
        )

    figure.update_layout(
        legend={"groupclick": "toggleitem"},
        title=f"{column} over time",
        xaxis_title="Timesteps",
        yaxis_title=column,
    )

    return figure, column
