"""This script contains the callbacks used in the apps data collection."""

import logging
import pathlib

import numpy as np
import pandas as pd
import sqlalchemy as sa
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src import PROCESS_NAME, engine
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


@callback(Output("game_state", "data"), Input("game_read", "n_intervals"))
def update_game_state(_: int) -> str:
    """Update the game state and store state in app.

    Args:
        _ (int): number of intervals.

    Returns:
        str: One of "game", "lobby" or "stats".
    """
    return sm.update_state(PROCESS_NAME)


def read_data_from_memory(n_intervals: int, game_state: str, pathname: str) -> None:
    """Read values from game memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): currently stored game data

    Returns:
        list: game data
    """
    path_name = pathlib.Path(pathname)
    game_uid = path_name.name
    logger.info(game_uid)
    if game_state == "game" and path_name.parent == pathlib.Path("/dashboard"):
        lord_glob_df = lord.get_lord_global_stats()
        lord_det_df = lord.get_lord_detailed_stats()
        buildings_df = b.calculate_all_stats()
        unit_df = unit.calculate_units()
        cur_tick_df = pd.concat([lord_glob_df, lord_det_df], axis=1).merge(buildings_df, on=["p_ID"])
        cur_tick_df["game_id"] = unit_df["game_id"] = game_uid
        cur_tick_df["time"] = unit_df["time"] = n_intervals
        with engine.begin() as conn:
            cur_tick_df.to_sql("lords", conn, if_exists="append", index=False)
            unit_df.to_sql("units", conn, if_exists="append", index_label="p_ID")
        logger.info("Uploaded game data for tick %i", n_intervals)


def save_lord_names(n_intervals: int, game_state: str, pathname: str) -> None:
    """Store the lord names into app memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): last stored lord names

    Raises:
        PreventUpdate: No update needed

    Returns:
        list: lord names list
    """
    path_name = pathlib.Path(pathname)
    game_uid = path_name.name
    logger.info([game_uid, path_name.parent])
    with engine.begin() as conn:
        table = sa.Table("lord_names", sa.MetaData(), autoload_with=engine)
        query = sa.Select(table).where(table.c.game_id == game_uid)
        old_df = pd.read_sql(query, conn)
    if n_intervals and game_state != "stats" and path_name.parent == pathlib.Path("/dashboard"):
        lord.get_active_lords()
        if lord.num_lords == 0:
            raise PreventUpdate()
        lord.get_lord_names()
        lord_df = pd.DataFrame(
            {
                "lord_names": lord.lord_names,
                "p_ID": np.arange(1, lord.num_lords + 1),
                "teams": lord.teams,
                "game_id": [game_uid] * lord.num_lords,
            }
        )
        if not lord_df.equals(old_df):
            with engine.begin() as conn:
                lord_df.to_sql("lord_names", conn, if_exists="append", index=False)


@callback(
    Input("game_read", "n_intervals"),
    State("map_store", "data"),
    State("game_state", "data"),
    State("loc", "pathname"),
)
def read_map_data_from_memory(n_intervals: int, map_data: list | None, game_state: str, pathname: str) -> None:
    """Read values from game memory.

    Args:
        n_intervals (int): number of intervals passed
        data (list | None): currently stored game data

    Returns:
        list: game data
    """
    map_data = map_data or []
    map_df = pd.DataFrame(map_data)
    path_name = pathlib.Path(pathname)
    game_uid = path_name.name
    if game_state == "game" and n_intervals is not None and path_name.parent == pathlib.Path("/dashboard"):
        read_data_from_memory(n_intervals, game_state, pathname)
        save_lord_names(n_intervals, game_state, pathname)
        lord_glob_df = lord.get_map_settings()
        lord_glob_df["end_month"] = lord_glob_df["end_month"] + 1
        lord_glob_df["start_month"] = lord_glob_df["start_month"] + 1
        if not ((lord_glob_df["start_year"] == 0) | (lord_glob_df["end_year"] == 0)).any():
            lord_glob_df["year_month"] = (
                (lord_glob_df["end_year"].astype(str) + "-" + lord_glob_df["end_month"].astype(str))
                .astype("datetime64[s]")
                .dt.strftime("%Y-%m-%dT%H:%M:%S")
            )

            if map_df.empty or not map_df[lord_glob_df.columns.to_list()].tail(1).reset_index(drop=True).equals(
                lord_glob_df
            ):
                lord_glob_df["time"] = n_intervals
                lord_glob_df["game_id"] = game_uid
                with engine.begin() as conn:
                    lord_glob_df.to_sql("map_data", conn, if_exists="append", index=False)


@callback(
    Output("map_store", "data"),
    Input("game_read", "n_intervals"),
    State("loc", "pathname"),
)
def read_map_data_from_sql(n_intervals: int, pathname: str) -> list:
    """Read the map_data table from sql and save data to store.

    Args:
        n_intervals (int): number of intervals
        pathname (str): current app browser path

    Raises:
        PreventUpdate: No new data to update store

    Returns:
        list: map data
    """
    game_uid = pathlib.Path(pathname).name
    if n_intervals and game_uid:
        table = sa.Table("map_data", sa.MetaData(), autoload_with=engine)
        query = sa.Select(table).where(table.c.game_id == game_uid)
        with engine.begin() as conn:
            dataframe = pd.read_sql(query, conn)
        return dataframe.to_dict("records")
    raise PreventUpdate()


@callback(
    Output("lord_store", "data"),
    Input("game_read", "n_intervals"),
    State("loc", "pathname"),
)
def read_lord_data_from_sql(n_intervals: int, pathname: str) -> list:
    """Read the lord_data table from sql and save data to store.

    Args:
        n_intervals (int): number of intervals
        pathname (str): current app browser path

    Raises:
        PreventUpdate: No new data to update store

    Returns:
        list: lord data
    """
    game_uid = pathlib.Path(pathname).name
    if n_intervals and game_uid:
        table = sa.Table("lords", sa.MetaData(), autoload_with=engine)
        query = sa.Select(table).where(table.c.game_id == game_uid)
        with engine.begin() as conn:
            dataframe = pd.read_sql(query, conn)
        return dataframe.to_dict("records")
    raise PreventUpdate()


@callback(
    Output("unit_store", "data"),
    Input("game_read", "n_intervals"),
    State("loc", "pathname"),
)
def read_unit_data_from_sql(n_intervals: int, pathname: str) -> list:
    """Read the unit_data table from sql and save data to store.

    Args:
        n_intervals (int): number of intervals
        pathname (str): current app browser path

    Raises:
        PreventUpdate: No new data to update store

    Returns:
        list: unit data
    """
    game_uid = pathlib.Path(pathname).name
    if n_intervals and game_uid:
        table = sa.Table("units", sa.MetaData(), autoload_with=engine)
        query = sa.Select(table).where(table.c.game_id == game_uid)
        with engine.begin() as conn:
            dataframe = pd.read_sql(query, conn)
        return dataframe.to_dict("records")
    raise PreventUpdate()


@callback(
    Output("lord_names", "data"),
    Input("game_read", "n_intervals"),
    State("loc", "pathname"),
)
def read_lord_names_data_from_sql(n_intervals: int, pathname: str) -> list:
    """Read the lord_names_data table from sql and save data to store.

    Args:
        n_intervals (int): number of intervals
        pathname (str): current app browser path

    Raises:
        PreventUpdate: No new data to update store

    Returns:
        list: lord names data
    """
    game_uid = pathlib.Path(pathname).name
    if n_intervals and game_uid:
        table = sa.Table("lord_names", sa.MetaData(), autoload_with=engine)
        query = sa.Select(table).where(table.c.game_id == game_uid)
        with engine.begin() as conn:
            dataframe = pd.read_sql(query, conn)
        return dataframe.to_dict("records")
    raise PreventUpdate()
