"""Script containing code to manage building related tasks and calculations."""

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
        buildings_info = [
            read_memory_chunk(
                PROCESS_NAME,
                self.base + i * self.offset,
                [0, self.owner, self.workers_needed, self.workers, self.workers_missing, self.snoozed],
            )
            for i in range(num_buildings)
        ]
        if player_id != 0:
            buildings_info = [
                [self.building_names.get(sublist[0])] + sublist
                for sublist in filter(lambda x: x[1] == player_id, buildings_info)
            ]
        else:
            buildings_info = [[self.building_names.get(sublist[0])] + sublist for sublist in buildings_info]
        return pd.DataFrame(
            buildings_info,
            columns=[
                "b_name",
                "address",
                "ID",
                "owner",
                "workers_needed",
                "workers_working",
                "workers_missing",
                "snoozed",
            ],
        )

    def calc_worker_stats(self, player_id: int = 0) -> pd.Series:
        """Calculate the worker stats through the buildings.

        Args:
            player_id (int, optional): player id to filter. Defaults to 0 and calculating global stats.

        Returns:
            pd.Series: series containing workers_needed, workers_working and workers_missing
        """
        buildings_df = self.list_buildings(player_id)
        # filter hovels, houses, quarrypiles and snoozed building to obtain correct results
        sums = buildings_df.loc[
            ~(buildings_df["ID"].isin([1, 2, 21])) | (buildings_df["snoozed"] == 1),
            ["workers_needed", "workers_working", "workers_missing"],
        ].sum()
        return sums
