"""This script contains the callbacks used in the apps graph generation."""

import logging

import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx

from src import SHC_COLORS

logger = logging.getLogger(__name__)


@callback(
    Output("stat-display", "figure"),
    Output("col_store", "data"),
    Input("game_store", "data"),
    Input({"type": "col-switch", "index": ALL}, "n_clicks"),
    State("col_store", "data"),
)
def update_graph(data: list, _: dict[str, int], last_column: str | None):
    column = last_column or "num_buildings"
    fig = go.Figure()
    logger.info(ctx.triggered_id)
    if data and ctx.triggered_id is not None:
        if isinstance(ctx.triggered_id, dict):
            column = ctx.triggered_id.get("index", "")
        df = pd.DataFrame(data)
        tolerance = 5
        df = df.sort_values(["p_ID", "time"])
        # Identify outliers where the value is far from both its neighbors
        df["is_outlier"] = (
            ((df["num_buildings"].shift(1) - df["num_buildings"]).abs() > tolerance)
            & ((df["num_buildings"].shift(-1) - df["num_buildings"]).abs() > tolerance)
            & ((df["num_buildings"].shift(1) - df["num_buildings"].shift(-1)).abs() <= tolerance)
            & (df["p_ID"].shift(1) == df["p_ID"])
        )

        # Filter out the outliers
        df = df.loc[~df["is_outlier"], :].drop(columns=["is_outlier"])
        for p_id, group in df.groupby("p_ID"):
            assert isinstance(p_id, int)
            fig.add_trace(
                go.Scatter(
                    x=group["time"],
                    y=group[column],
                    mode="lines",
                    name=f"p_ID {p_id}",
                    marker_color=SHC_COLORS[p_id - 1],
                )
            )

        # Customize layout (optional)
        fig.update_layout(title=f"{column} over time", xaxis_title="Timesteps", yaxis_title=column)
    return fig, column
