"""This script contains the callbacks used in the apps data collection."""

import logging

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src import PROCESS_NAME
from src.stats.building import Building
from src.stats.lord import Lord
from src.stats.read_data import read_config
from src.stats.state_machine import StateMachine
from src.stats.unit import Unit

logger = logging.getLogger(__name__)
build_config = read_config("building")
b = Building.from_dict(build_config)
lord_config = read_config("lord")
lord = Lord.from_dict(lord_config)
unit_config = read_config("unit")
unit = Unit.from_dict(unit_config)
sm = StateMachine()


@callback(Output("game_store", "data"), Input("game_read", "n_intervals"), State("game_store", "data"))
def read_data_from_memory(n_intervals: int, data: list | None) -> list:
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


@callback(Output("lord_store", "data"), Input("game_read", "n_intervals"), State("lord_store", "data"))
def save_lord_names(n_intervals: int, data: list | None) -> list:
    if any((s > 0 for s in np.array(data).shape)):
        array = np.array(data)
    else:
        array = np.array([])
    state = sm.update_state(PROCESS_NAME)
    if state != "stats":
        lord.get_active_lords()
        lord.get_lord_names()
        if not np.array_equal(lord.lord_names, array):
            return lord.lord_names.tolist()
    raise PreventUpdate()
