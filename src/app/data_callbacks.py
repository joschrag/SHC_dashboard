"""This script contains the callbacks used in the apps data collection."""

import logging

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src import PROCESS_NAME
from src.parser.building import Building
from src.parser.lord import Lord
from src.parser.read_data import read_config
from src.parser.state_machine import StateMachine
from src.parser.unit import Unit

logger = logging.getLogger(__name__)
build_config = read_config("building", "memory")
b = Building.from_dict(build_config)
lord_config = read_config("lord", "memory")
lord = Lord.from_dict(lord_config)
unit_config = read_config("unit", "memory")
unit = Unit.from_dict(unit_config)
sm = StateMachine()


@callback(Output("game_store", "data"), Input("game_read", "n_intervals"), State("game_store", "data"))
def read_data_from_memory(n_intervals: int, data: list | None) -> list:
    """Read values from game memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): currently stored game data

    Returns:
        list: game data
    """
    data = data or []
    game_data = pd.DataFrame(data)
    state = sm.update_state(PROCESS_NAME)
    if state == "game":
        lord_glob_df = lord.get_lord_global_stats()
        lord_det_df = lord.get_lord_detailed_stats()
        buildings_df = b.calculate_all_stats()
        unit_df = unit.calculate_units()
        cur_tick_df = (
            pd.concat([lord_glob_df, lord_det_df], axis=1)
            .merge(buildings_df, how="left", on="p_ID")
            .merge(unit_df, how="left", on="p_ID")
        )
        cur_tick_df["time"] = n_intervals
        game_data = pd.concat(
            [game_data, cur_tick_df],
            ignore_index=True,
        )
        return game_data.to_dict("records")
    elif state == "lobby":
        game_data = pd.DataFrame()
    return game_data.to_dict("records")


@callback(Output("map_store", "data"), Input("game_read", "n_intervals"), State("map_store", "data"))
def read_map_data_from_memory(n_intervals: int, data: list | None) -> list:
    """Read values from game memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): currently stored game data

    Returns:
        list: game data
    """
    data = data or []
    map_data = pd.DataFrame(data)
    state = sm.update_state(PROCESS_NAME)
    if state == "game":
        lord_glob_df = lord.get_map_settings()
        lord_glob_df["end_month"] = lord_glob_df["end_month"] + 1
        lord_glob_df["start_month"] = lord_glob_df["start_month"] + 1
        lord_glob_df["year_month"] = (
            lord_glob_df["end_year"].astype(str) + "-" + lord_glob_df["end_month"].astype(str)
        ).astype("datetime64[s]")
        if ((lord_glob_df["start_year"] == 0) | (lord_glob_df["end_year"] == 0)).any():
            raise PreventUpdate()
        if not map_data.empty and map_data[lord_glob_df.columns.to_list()].tail(1).reset_index(drop=True).equals(
            lord_glob_df
        ):
            raise PreventUpdate()
        lord_glob_df["time"] = n_intervals
        map_data = pd.concat(
            [map_data, lord_glob_df],
            ignore_index=True,
        )
        return map_data.to_dict("records")
    elif state == "lobby":
        map_data = pd.DataFrame()
    return map_data.to_dict("records")


@callback(Output("lord_store", "data"), Input("game_read", "n_intervals"), State("lord_store", "data"))
def save_lord_names(n_intervals: int, data: list | None) -> list:
    """Store the lord names into app memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): last stored lord names

    Raises:
        PreventUpdate: No update needed

    Returns:
        list: lord names list
    """
    if isinstance(data, list) and any(data):
        old_df = pd.DataFrame(data)
    else:
        old_df = pd.DataFrame()
    state = sm.update_state(PROCESS_NAME)
    if state != "stats":
        lord.get_active_lords()
        lord.get_lord_names()
        lord_df = pd.DataFrame(
            {"p_ID": np.arange(1, lord.num_lords + 1), "lord_names": lord.lord_names, "teams": lord.teams}
        )
        if not lord_df.equals(old_df):
            return lord_df.to_dict("records")
    raise PreventUpdate()
