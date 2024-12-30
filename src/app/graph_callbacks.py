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
    Output("last_tick_store", "data"),
    Input("lord_store", "data"),
    Input({"type": "graph-switch", "index": ALL}, "n_clicks"),
    State("last_tick_store", "data"),
    State("lord_names", "data"),
    State("map_store", "data"),
    State("unit_store", "data"),
    State("stat-display", "figure"),
    prevent_initial_call=True,
)
def update_graph(
    lord_data, _, last_tick_store, lord_names_data, map_data, unit_data, current_fig
) -> tuple[go.Figure | dash.Patch, tuple[str, int]]:
    """Update the display graph based on game and lord data."""
    last_tick_store = last_tick_store or ("popularity", None)
    column, last_tick = last_tick_store
    figure = go.Figure(current_fig) if current_fig else go.Figure()

    if not (lord_data and lord_names_data and ctx.triggered_id and map_data and unit_data):
        raise PreventUpdate()

    if isinstance(ctx.triggered_id, dict):
        column = ctx.triggered_id.get("index", column)
    map_df = pd.DataFrame(map_data).drop(columns=["map_name", "advantage_setting", "start_year", "start_month"])
    unit_data = pd.DataFrame(unit_data)
    df: pd.DataFrame = (
        pd.DataFrame(lord_data).merge(unit_data, on=["p_ID", "game_id", "time"]).sort_values(["p_ID", "time"])
    )
    df = df.merge(pd.DataFrame(lord_names_data), on="p_ID", how="left")

    # Identify and remove outliers
    tolerance = 5
    df["is_outlier"] = (
        ((df[column].shift(1) - df[column]).abs() > tolerance)
        & ((df[column].shift(-1) - df[column]).abs() > tolerance)
        & ((df[column].shift(1) - df[column].shift(-1)).abs() <= tolerance)
        & (df["p_ID"].shift(1) == df["p_ID"])
    ) | (df[column] > 10**9)
    df = df[~df["is_outlier"]].merge(map_df, "left", on="time").dropna(subset=["end_year", "end_month"])
    if df.empty:
        raise PreventUpdate()
    # Patch or add data to the figure
    if current_fig is not None and ctx.triggered_id == "game_store":
        patched_figure = dash.Patch()
        if last_tick:
            last_timestamp = pd.Series(
                [
                    *(
                        (map_df.loc[(map_df["time"] == last_tick), "year_month"]).astype("datetime64[s]")
                        - pd.DateOffset(months=1)
                    ).values,
                    map_df.year_month.astype("datetime64[s]").min(),
                ]
            ).max()

        for p_id, group in df.groupby("p_ID"):
            assert isinstance(p_id, int)
            first_row = group.loc[group.year_month.astype("datetime64[s]") <= last_timestamp]
            # get size of first row for plot trimming
            group = group.loc[first_row.iloc[-1].name :]
            df_first = group["year_month"].drop_duplicates(keep="first")
            df_last = group["year_month"].drop_duplicates(keep="last")
            df_dates = pd.concat([df_first.iloc[:1].to_frame(), df_last.iloc[1:].to_frame()]).astype("datetime64[s]")
            group.loc[:, "year_month"] = group.year_month.drop_duplicates(keep=False)
            group.loc[df_dates.index, "year_month"] = df_dates
            group.loc[:, "year_month"] = group["year_month"].astype("datetime64[s]").interpolate("linear")
            patched_figure["data"][p_id - 1]["x"] = figure["data"][p_id - 1]["x"][0 : first_row.shape[0]]
            patched_figure["data"][p_id - 1]["y"] = figure["data"][p_id - 1]["y"][0 : first_row.shape[0]]
            patched_figure["data"][p_id - 1]["x"].extend(group["year_month"].tolist())
            patched_figure["data"][p_id - 1]["y"].extend(group[column].tolist())

        return patched_figure, (column, df["time"].max())
    figure = go.Figure()
    for p_id, group in df.groupby("p_ID"):
        assert isinstance(p_id, int)
        team = group["teams"].iloc[0] if not group["teams"].isnull().all() else None
        legendgroup = f"Team {team}" if team else "No team"
        df_first = group["year_month"].drop_duplicates(keep="first")
        df_last = group["year_month"].drop_duplicates(keep="last")
        group["year_month"] = pd.concat([df_first.iloc[:-1].to_frame(), df_last.iloc[-1:].to_frame()]).astype(
            "datetime64[s]"
        )
        group["year_month"] = group["year_month"].interpolate()
        figure.add_trace(
            go.Scatter(
                x=group["year_month"],
                y=group[column],
                mode="lines",
                name=group["lord_names"].iloc[0],
                marker_color=SHC_COLORS[p_id - 1],
                legendgroup=legendgroup,
                legendgrouptitle_text=legendgroup,
                # line={"shape": "spline"},
            )
        )

    figure.update_layout(
        legend={"groupclick": "toggleitem"},
        title=f"{column} over time",
        xaxis_title="Timesteps",
        yaxis_title=column,
        hovermode="x unified",
    )
    figure.update_xaxes(
        tickmode="auto",  # Automatically adjust tick frequency
        tickvals=df["time"],  # Use numeric values for tick positions
        ticktext=df["year_month"],  # Map numeric values to 'year-month' labels
        tickformatstops=[
            # Show the year-month format for larger time intervals (e.g., months or years)
            dict(dtickrange=["M1", "M12"], value="%b-%Y"),
            dict(dtickrange=["M12", None], value="%Y"),  # Show only year for longer time periods
        ],
    )

    return figure, (column, df["time"].max())
