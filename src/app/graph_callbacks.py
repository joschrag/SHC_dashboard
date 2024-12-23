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
    Input({"type": "graph-switch", "index": ALL}, "n_clicks"),
    State("col_store", "data"),
    State("lord_store", "data"),
)
def update_graph(data: list, _: dict[str, int], last_column: str | None, lord_names: list | None) -> tuple:
    """Update the display graph.

    Args:
        data (list): stored game data
        _ (dict[str, int]): number of clicks on the subcategories
        last_column (str | None): last selected subcategory
        lord_names (list | None): list of lord names

    Returns:
        tuple: updated graph, selected subcategory
    """
    column = last_column or "popularity"
    fig = go.Figure()
    logger.info(ctx.triggered_id)
    if data and lord_names and ctx.triggered_id is not None:
        if isinstance(ctx.triggered_id, dict):
            column = ctx.triggered_id.get("index", "")
        df = pd.DataFrame(data)
        tolerance = 5
        df = df.sort_values(["p_ID", "time"])
        df["lord_name"] = df["p_ID"].map({p_id: lord_names[p_id - 1] for p_id in df["p_ID"].unique()})
        # Identify outliers where the value is far from both its neighbors
        df["is_outlier"] = (
            ((df[column].shift(1) - df[column]).abs() > tolerance)
            & ((df[column].shift(-1) - df[column]).abs() > tolerance)
            & ((df[column].shift(1) - df[column].shift(-1)).abs() <= tolerance)
            & (df["p_ID"].shift(1) == df["p_ID"])
        ) | (df[column] > 10**9)

        # Filter out the outliers
        df = df.loc[~df["is_outlier"], :].drop(columns=["is_outlier"])
        for p_id, group in df.groupby("p_ID"):
            assert isinstance(p_id, int)
            fig.add_trace(
                go.Scatter(
                    x=group["time"],
                    y=group[column],
                    mode="lines",
                    name=lord_names[p_id - 1],
                    marker_color=SHC_COLORS[p_id - 1],
                )
            )

        # Customize layout (optional)
        fig.update_layout(title=f"{column} over time", xaxis_title="Timesteps", yaxis_title=column)
        # image_data = {
        #     "source": dash.get_relative_path("/assets/img/open_book.png"),
        #     "xref": "paper",
        #     "yref": "paper",
        #     "x": 0,
        #     "y": 0,
        #     "xanchor": "left",
        #     "yanchor": "bottom",
        #     "sizex": 1,
        #     "sizey": 1,  # abs(full_fig.layout.yaxis.range[1] - full_fig.layout.yaxis.range[0]),
        #     "sizing": "stretch",
        #     "opacity": 0.6,
        #     "layer": "below",
        # }
        # logger.info(fig.layout.images)
        # if len(fig.layout.images) == 0:
        #     fig.add_layout_image(image_data)
        # else:
        #     fig.update_layout_images(image_data)
    return fig, column
