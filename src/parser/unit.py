import numpy as np
import pandas as pd

from src import PROCESS_NAME
from src.stats.read_data import D_Types, read_config, read_memory, read_memory_chunk


class MemoryAddress:
    def __init__(self, base, offset, val_offset):
        self.base = base
        self.offset = offset
        self.val_offset = val_offset

    def calculate_address(self, multiplier):
        return self.base + multiplier * self.offset + self.val_offset


class Unit:
    def __init__(self, base: int, offsets: dict, total_units: int) -> None:
        self.unit_names = read_config("names")["Units"]
        self.base = base
        self.offset = offsets["offset"]
        self.color = offsets["coloroffset"]
        self.owner = offsets["owneroffset"]
        self.moving = offsets["moving"]
        self.selected = offsets["selected"]
        self.hp_bar = offsets["hp_bar_percent"]
        self.cur_hp = offsets["cur_hp"]
        self.max_hp = offsets["max_hp"]
        self.x = offsets["x_coord_cam"]
        self.y = offsets["y_coord_cam"]
        self.unknown = [MemoryAddress(self.base, self.offset, unknown_offset) for unknown_offset in offsets["unknown"]]

        self.total_units = total_units

    @staticmethod
    def from_dict(config: dict) -> "Unit":
        return Unit(config["address"], config["offsets"], config["total"])

    def list_units(self, player_id: int | None = None) -> pd.DataFrame:
        num_units = int(read_memory(PROCESS_NAME, self.total_units, D_Types.INT))
        offset_list = [
            0,
            self.color,
            self.moving,
            self.selected,
            self.hp_bar,
            self.owner,
            self.cur_hp,
            self.max_hp,
            self.x,
            self.y,
        ]
        unit_info = read_memory_chunk(
            PROCESS_NAME,
            self.base,
            [i * self.offset + extra_off for i in range(num_units) for extra_off in offset_list],
            D_Types.WORD,
        )
        unit_info = np.array(unit_info).reshape((num_units, len(offset_list)))
        if player_id is not None:
            mask = unit_info[:, 2] == player_id
        else:
            mask = (unit_info[:, 2] >= 0) & (unit_info[:, 2] <= 8)

        filtered_units = unit_info[mask]

        unit_names_array = np.vectorize(self.unit_names.get)(filtered_units[:, 0])
        address_array = (self.base + np.arange(unit_info.shape[0]) * self.offset)[mask].reshape(-1, 1)
        unit_info = np.column_stack((address_array, unit_names_array, filtered_units))
        return pd.DataFrame(
            unit_info,
            columns=[
                "address",
                "unit_name",
                "ID",
                "color",
                "moving",
                "selected",
                "hp_percent",
                "p_ID",
                "cur_hp",
                "max_hp",
                "x",
                "y",
            ],
        ).astype(
            {
                "address": pd.Int64Dtype(),
                "unit_name": pd.StringDtype(),
                "ID": pd.Int64Dtype(),
                "color": pd.Int64Dtype(),
                "moving": pd.Int32Dtype(),
                "selected": pd.Int32Dtype(),
                "hp_percent": pd.Int32Dtype(),
                "p_ID": pd.Int32Dtype(),
                "cur_hp": pd.Int64Dtype(),
                "max_hp": pd.Int64Dtype(),
                "x": pd.Int64Dtype(),
                "y": pd.Int64Dtype(),
            }
        )

    def list_units_exp(self, player_id: int | None = None) -> pd.DataFrame:
        num_units = int(read_memory(PROCESS_NAME, self.total_units, D_Types.INT))
        offset_list = [0, *[obj.val_offset for obj in self.unknown]]
        unit_info = read_memory_chunk(
            PROCESS_NAME,
            self.base,
            [i * self.offset + extra_off for i in range(num_units) for extra_off in offset_list],
            D_Types.WORD,
        )
        unit_info = np.array(unit_info).reshape((num_units, len(offset_list)))
        if player_id is not None:
            mask = unit_info[:, 2] == player_id
        else:
            mask = (unit_info[:, 2] >= 0) & (unit_info[:, 2] <= 8)

        filtered_units = unit_info[mask]

        unit_names_array = np.vectorize(self.unit_names.get)(filtered_units[:, 0])
        address_array = (self.base + np.arange(unit_info.shape[0]) * self.offset).reshape(-1, 1)
        unit_info = np.column_stack((address_array, unit_names_array, filtered_units))
        return pd.DataFrame(
            unit_info,
            columns=[
                "address",
                "unit_name",
                "ID",
                *[hex(off.val_offset) for off in self.unknown],
            ],
        )

    def calculate_units(self, player_id: int | None = None) -> pd.DataFrame:
        units = self.list_units(player_id)
        unit_stats_df = units.groupby(["p_ID", "unit_name"]).size().unstack(fill_value=0)
        return unit_stats_df
