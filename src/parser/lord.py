import numpy as np
import pandas as pd

from src import PROCESS_NAME

from .read_data import D_Types, read_memory_chunk


class Lord:
    def __init__(self, map: dict, lord_basic: dict, lord_global: dict, lord_name: dict, lord_stat: dict) -> None:
        self.map = map
        self.lord_basic = lord_basic["memory"]
        self.lord_basic_off = lord_basic["offset"]
        self.lord_name = lord_name["memory"]
        self.lord_name_off = lord_name["offset"]
        self.lord_global = lord_global["memory"]
        self.lord_global_off = lord_global["offset"]
        self.lord_stat = lord_stat["memory"]
        self.lord_stat_off = lord_stat["offset"]
        self.active_lords = np.empty(8)
        self.num_lords = 8
        self.teams = np.empty(1)
        self.lord_names = np.empty(1)

    @staticmethod
    def from_dict(config: dict) -> "Lord":
        return Lord(
            config["map_offsets"],
            config["lord_basic_offsets"],
            config["lord_global_offsets"],
            config["lord_name_offsets"],
            config["lord_stat_offsets"],
        )

    def get_active_lords(self) -> None:
        lord_basic = self.lord_basic[0]
        basic_offsets = [
            i * self.lord_basic_off + extra_off["offset"] for extra_off in lord_basic["stat_offsets"] for i in range(8)
        ]
        dtypes = [D_Types[extra_off["type"].upper()] for extra_off in lord_basic["stat_offsets"] for i in range(8)]
        lord_basic_mem = read_memory_chunk(
            PROCESS_NAME,
            lord_basic["address"],
            basic_offsets,
            dtypes,
        )
        lord_basic_arr = np.reshape(np.array(lord_basic_mem), (2, 8))
        self.active_lords = lord_basic_arr[0, :]
        self.num_lords = np.max([lord_basic_arr[0, :].sum(), (lord_basic_arr[1, :] >= 0).sum()])
        self.teams = lord_basic_arr[1, 0 : self.num_lords]  # noqa: E203

    def get_lord_names(self) -> None:
        lord_name = self.lord_name[0]
        names_offsets = [
            i * self.lord_name_off + extra_off["offset"]
            for extra_off in lord_name["stat_offsets"]
            for i in range(self.num_lords)
        ]
        dtypes = [
            D_Types[extra_off["type"].upper()]
            for extra_off in lord_name["stat_offsets"]
            for i in range(self.num_lords)
        ]
        lord_names_mem = read_memory_chunk(
            PROCESS_NAME,
            lord_name["address"],
            names_offsets,
            dtypes,
        )
        self.lord_names = np.reshape(np.array(lord_names_mem), (self.num_lords, 1))

    def get_lord_global_stats(self) -> pd.DataFrame:
        cols = ["p_ID"] + [
            extra_off["name"] for lord_global in self.lord_global for extra_off in lord_global["stat_offsets"]
        ]
        total_arr = np.arange(1, self.num_lords + 1).reshape(-1, 1)
        for lord_global in self.lord_global:
            global_offsets = [
                i * self.lord_global_off + extra_off["offset"]
                for extra_off in lord_global["stat_offsets"]
                for i in range(self.num_lords)
            ]
            dtypes = [
                D_Types[extra_off["type"].upper()]
                for extra_off in lord_global["stat_offsets"]
                for _ in range(self.num_lords)
            ]
            lord_global_mem = read_memory_chunk(
                PROCESS_NAME,
                lord_global["address"],
                global_offsets,
                dtypes,
            )
            lord_global_arr = np.reshape(
                np.array(lord_global_mem),
                (
                    len(lord_global["stat_offsets"]),
                    self.num_lords,
                ),
            ).T
            total_arr = np.concat((total_arr, lord_global_arr), axis=1)
        return pd.DataFrame(total_arr, columns=cols)

    def get_lord_detailed_stats(self) -> pd.DataFrame:
        cols = [extra_off["name"] for lord_stat in self.lord_stat for extra_off in lord_stat["stat_offsets"]]
        total_arr = np.empty((self.num_lords, 0))
        for lord_stat in self.lord_stat:
            stat_offsets = [
                i * self.lord_stat_off + extra_off["offset"]
                for i in range(self.num_lords)
                for extra_off in lord_stat["stat_offsets"]
            ]
            dtypes = [
                D_Types[extra_off["type"].upper()]
                for extra_off in lord_stat["stat_offsets"]
                for _ in range(self.num_lords)
            ]
            lord_stat_mem = read_memory_chunk(
                PROCESS_NAME,
                lord_stat["address"],
                stat_offsets,
                dtypes,
            )
            lord_stat_arr = np.reshape(
                np.array(lord_stat_mem),
                (self.num_lords, -1),
            )
            total_arr = np.concat((total_arr, lord_stat_arr), axis=1)
        return pd.DataFrame(total_arr, columns=cols)
