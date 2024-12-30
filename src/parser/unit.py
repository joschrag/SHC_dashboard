"""Script containing code to manage unit related tasks and calculations."""

import numpy as np
import pandas as pd

from src import PROCESS_NAME
from src.parser.read_data import D_Types, read_config, read_memory, read_memory_chunk


class MemoryAddress:
    """Class to represent a memory address."""

    def __init__(self, base: int, offset: int, val_offset: int):
        """Initialize the memory.

        Args:
            base (int): memory base address
            offset (int): offset for each player
            val_offset (int): value offset from base address
        """
        self.base = base
        self.offset = offset
        self.val_offset = val_offset

    def calculate_address(self, multiplier: int) -> int:
        """Calculate the memory address for a given multiplier.

        Args:
            multiplier (int): player id to calculate address for

        Returns:
            int: address of the object
        """
        return self.base + multiplier * self.offset + self.val_offset


class Unit:
    """Class to read unit values and calculate statistics."""

    def __init__(self, base: int, offsets: dict, total_units: int) -> None:
        """Initialize the unit class with memory address and offsets.

        Args:
            base (int): base memory address
            offsets (dict): dictionary with offset values
            total_units (int): address with total unit value
        """
        self.unit_names = read_config("names", "memory")["Units"]
        self.base = base
        self.offset = offsets.pop("offset", 0)
        self.value_offsets = offsets
        self.unknown = [
            MemoryAddress(self.base, self.offset, unknown_offset) for unknown_offset in offsets.pop("unknown", [])
        ]

        self.total_units = total_units

    @staticmethod
    def from_dict(config: dict) -> "Unit":
        """Instantiate the class from a config dicionary.

        Args:
            config (dict): configuration dict

        Returns:
            Unit: instantiated class object
        """
        return Unit(config["address"], config["offsets"], config["total"])

    def list_units(self, player_id: int | None = None) -> pd.DataFrame:
        """Read unit data from memory into a dataframe.

        Args:
            player_id (int | None, optional): Player id to filter. Defaults to None.

        Returns:
            pd.DataFrame: dataframe with memory values
        """
        num_units = int(read_memory(PROCESS_NAME, self.total_units, D_Types.INT))
        if num_units == 0:
            return pd.DataFrame(
                columns=[
                    "address",
                    "unit_name",
                    "ID",
                    *self.value_offsets.keys(),
                ],
            )
        offset_list = [0, *self.value_offsets.values()]
        unit_info = read_memory_chunk(
            PROCESS_NAME,
            self.base,
            [i * self.offset + extra_off for i in range(num_units) for extra_off in offset_list],
            D_Types.WORD,
        )
        unit_arr = np.array(unit_info).reshape((num_units, len(offset_list)))
        if player_id is not None:
            mask = unit_arr[:, 2] == player_id
        else:
            mask = (unit_arr[:, 2] >= 0) & (unit_arr[:, 2] <= 8)

        filtered_units = unit_arr[mask]

        unit_names_array = np.vectorize(self.unit_names.get)(filtered_units[:, 0])
        address_array = (self.base + np.arange(unit_arr.shape[0]) * self.offset)[mask].reshape(-1, 1)
        unit_arr = np.column_stack((address_array, unit_names_array, filtered_units))
        return pd.DataFrame(
            unit_arr,
            columns=[
                "address",
                "unit_name",
                "ID",
                *self.value_offsets.keys(),
            ],
        ).astype(
            {
                "address": pd.Int64Dtype(),
                "unit_name": pd.StringDtype(),
                "ID": pd.Int64Dtype(),
                **{key: pd.Int64Dtype() for key in self.value_offsets.keys()},
            }
        )

    def list_units_exp(self, player_id: int | None = None) -> pd.DataFrame:
        """List the unknown flags data into a dataframe.

        Args:
            player_id (int | None, optional): Player id to filter. Defaults to None.

        Returns:
            pd.DataFrame: dataframe with memory values
        """
        num_units = int(read_memory(PROCESS_NAME, self.total_units, D_Types.INT))
        offset_list = [0, *[obj.val_offset for obj in self.unknown]]
        unit_info = read_memory_chunk(
            PROCESS_NAME,
            self.base,
            [i * self.offset + extra_off for i in range(num_units) for extra_off in offset_list],
            D_Types.WORD,
        )
        unit_arr = np.array(unit_info).reshape((num_units, len(offset_list)))
        if player_id is not None:
            mask = unit_arr[:, 2] == player_id
        else:
            mask = (unit_arr[:, 2] >= 0) & (unit_arr[:, 2] <= 8)

        filtered_units = unit_arr[mask]

        unit_names_array = np.vectorize(self.unit_names.get)(filtered_units[:, 0])
        address_array = (self.base + np.arange(unit_arr.shape[0]) * self.offset).reshape(-1, 1)
        unit_arr = np.column_stack((address_array, unit_names_array, filtered_units))
        return pd.DataFrame(
            unit_arr,
            columns=[
                "address",
                "unit_name",
                "ID",
                *[hex(off.val_offset) for off in self.unknown],
            ],
        )

    def calculate_units(self, player_id: int | None = None) -> pd.DataFrame:
        """Calculate unit stats from data.

        Args:
            player_id (int | None, optional): player to filter. Defaults to None.

        Returns:
            pd.DataFrame: dataframe with the unit stats
        """
        units = self.list_units(player_id)
        unit_list = [18, 35, 39, 40, 41, 42, 43, 44, 106, 109, 190, 191, 192, 193, 195, 196, 199]
        siege_engines = [62, 83, 84, 120, 121, 123, 124, 197]
        army = units.loc[units.ID.isin(unit_list)]
        se_army = units.loc[units.ID.isin(siege_engines)]
        se_stats_df = se_army.groupby(["p_ID", "unit_name"]).size().unstack(fill_value=0)
        unit_stats_df = army.groupby(["p_ID", "unit_name"]).size().unstack(fill_value=0)
        unit_stats_df = pd.concat([unit_stats_df, se_stats_df], axis=1)
        tmp_result = army.groupby(["p_ID", "is_ranged"]).size().unstack(fill_value=0)
        missing_units = np.vectorize(self.unit_names.get)(
            np.array([x for x in unit_list + siege_engines if x not in units["ID"].unique()])
        )
        unit_stats_df.loc[:, missing_units] = 0
        unit_stats_df[["melee", "ranged"]] = tmp_result.reindex(columns=[0, 1], fill_value=0)
        return unit_stats_df.fillna(0)
