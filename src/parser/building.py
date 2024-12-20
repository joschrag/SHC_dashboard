"""Script containing code to manage building related tasks and calculations."""

import numpy as np
import pandas as pd

from src import PROCESS_NAME
from src.stats.read_data import D_Types, read_config, read_memory, read_memory_chunk


class Building:
    """Class to read buildings from memory and compute stats."""

    def __init__(self, base: int, offsets: dict, total_buildings: int) -> None:
        """Initialize the Building class.

        Args:
            base (int): base address of the buildings array in memory
            offsets (dict): offset to next building in memory
            total_buildings (int): address where number of total buildings is stored
        """
        self.building_names = read_config("names")["Buildings"]
        self.base = base
        self.offset = offsets["offset"]
        self.owner = offsets["owneroffset"]
        self.workers_needed = offsets["workersneededoffset"]
        self.workers = offsets["workersworkingoffset"]
        self.workers_missing = offsets["workersmissingoffset"]
        self.snoozed = offsets["snoozedoffset"]
        self.total_buildings = total_buildings

    @staticmethod
    def from_dict(config: dict) -> "Building":
        """Initialize Building from a dictionary.

        Args:
            config (dict): configuration dictionary

        Returns:
            Building: instantiated class
        """
        return Building(config["address"], config["offsets"], config["total"])

    def list_buildings(self, player_id: int = 0) -> pd.DataFrame:
        """List all buildings present in the game.

        Args:
            player_id (int, optional): player id to filter buildings. Defaults to 0 and not filtering.

        Returns:
            pd.DataFrame: buildings data
        """
        num_buildings = int(read_memory(PROCESS_NAME, self.total_buildings, D_Types.INT))
        offset_list = [0, self.owner, self.workers_needed, self.workers, self.workers_missing, self.snoozed]
        buildings_list = read_memory_chunk(
            PROCESS_NAME,
            self.base,
            [i * self.offset + extra_off for i in range(num_buildings) for extra_off in offset_list],
        )
        buildings_array = np.array(buildings_list).reshape((num_buildings, len(offset_list)))
        if player_id != 0:
            mask = buildings_array[:, 2] == player_id
        else:
            mask = (buildings_array[:, 2] >= 0) & (buildings_array[:, 2] <= 8)

        filtered_buildings = buildings_array[mask]

        building_names_array = np.vectorize(self.building_names.get)(filtered_buildings[:, 0])
        address_array = (self.base + np.arange(buildings_array.shape[0]) * self.offset).reshape(-1, 1)
        buildings_array = np.column_stack((address_array, building_names_array, filtered_buildings))
        return pd.DataFrame(
            buildings_array,
            columns=[
                "address",
                "b_name",
                "ID",
                "owner",
                "workers_needed",
                "workers_working",
                "workers_missing",
                "snoozed",
            ],
        ).astype(
            {
                "address": pd.Int64Dtype(),
                "b_name": pd.StringDtype(),
                "ID": pd.Int64Dtype(),
                "owner": pd.Int16Dtype(),
                "workers_needed": pd.Int16Dtype(),
                "workers_working": pd.Int16Dtype(),
                "workers_missing": pd.Int16Dtype(),
                "snoozed": pd.Int16Dtype(),
            }
        )

    def calculate_all_stats(self) -> pd.DataFrame:
        """Calculate all building and worker related stats into a dataframe.

        Returns:
            pd.DataFrame: All building stats.
        """
        false_worker_ids = [1, 2, 8, 9, 21, 29]
        ground_ids = [53, 55, 56, 57, 58, 59]
        keep_ids = [71, 72, 73]
        siege_engines = [80, 81, 82, 83, 84, 86, 87]
        building_info_df = pd.DataFrame(
            columns=["num_buildings", "workers_needed", "workers_working", "workers_missing", "snoozed"]
        )
        building_mem_df = self.list_buildings()
        building_mem_df = building_mem_df.loc[
            ~(building_mem_df["ID"].isin(ground_ids + keep_ids + siege_engines)),
            :,
        ]
        building_info_df["num_buildings"] = (
            building_mem_df.loc[:, ["owner"]]
            .groupby("owner")
            .size()
            .to_frame()
            .rename(columns={"size": "num_buildings"})
        )
        building_info_df["snoozed"] = (
            building_mem_df.loc[building_mem_df["snoozed"] == 1, ["owner"]]
            .groupby("owner")
            .size()
            .to_frame()
            .rename(columns={"size": "snoozed"})
        )
        building_info_df["snoozed"] = building_info_df["snoozed"].fillna(0).astype(pd.Int32Dtype())
        building_mem_df = building_mem_df.loc[
            ~(building_mem_df["ID"].isin(false_worker_ids)) & (building_mem_df["snoozed"] == 0),
            :,
        ]
        building_info_df[["workers_needed", "workers_working", "workers_missing"]] = (
            building_mem_df.loc[:, ["owner", "workers_needed", "workers_working", "workers_missing"]]
            .groupby("owner")
            .sum()
        )
        return building_info_df.reset_index(names=["p_ID"])
