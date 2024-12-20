import ctypes
import logging
import pathlib
from ctypes import Array, c_bool, c_byte, c_char, c_uint16, c_uint32, wintypes
from enum import Enum

import psutil
import yaml

logger = logging.getLogger(__name__)

# Constants for permissions
PROCESS_ALL_ACCESS = 0x1F0FFF


def read_config(filename: str) -> dict:
    path = pathlib.Path().cwd() / "memory" / f"{filename}.yaml"
    with open(path, "r", encoding="utf8") as file:
        if path.suffix == ".yaml":
            data = yaml.safe_load(file)
    return data


# Helper function to find a process by name
def get_process_by_name(name):
    for proc in psutil.process_iter(["name"]):
        # print(proc.info["name"])
        if proc.info["name"] == name:
            return proc
    return None


class D_Types(Enum):
    INT = 0
    STRING = 1
    BYTE = 2
    BOOL = 3
    WORD = 4


d_types: dict[D_Types, c_uint32 | c_byte | c_bool | c_uint16 | Array[c_char]] = {
    D_Types.INT: ctypes.c_uint32(),
    D_Types.STRING: ctypes.create_string_buffer(256),
    D_Types.BYTE: ctypes.c_byte(),
    D_Types.BOOL: ctypes.c_bool(),
    D_Types.WORD: ctypes.c_uint16(),
}


class MemoryReadError(Exception):
    """Custom exception for memory read errors."""

    def __init__(self, message, process_name=None, address=None):
        self.message = message
        self.process_name = process_name
        self.address = address
        super().__init__(self._build_message())

    def _build_message(self):
        details = []
        if self.process_name:
            details.append(f"Process: '{self.process_name}'")
        if self.address is not None:
            details.append(f"Address: {hex(self.address) if isinstance(self.address, int) else self.address}")
        details.append(self.message)
        return "; ".join(details)


def read_memory(process_name: str, address: int, dtype: D_Types) -> int | bool | str:
    """Read the memory value from an address within a process.

    Args:
        process_name (str): name of the target process
        address (int): target address
        dtype (D_Types): address value data type

    Raises:
        MemoryReadError: Can't find target process.
        MemoryReadError: Can't open target process.
        ValueError: Invalid data type.
        MemoryReadError: Can't read target address.
        e: General exception.

    Returns:
        int | bool | str: value of memory address
    """
    try:
        # Locate the process
        proc = get_process_by_name(process_name)
        if not proc:
            raise MemoryReadError("Process not found.", process_name=process_name)

        # Open the process with the necessary access
        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.pid)
        if not process_handle:
            raise MemoryReadError("Failed to open process.", process_name=process_name)

        try:
            # Prepare a buffer to store the read value
            if dtype not in d_types:
                raise ValueError(f"Unsupported dtype '{dtype}'. Supported types: {list(d_types.keys())}")

            buffer = d_types[dtype]
            bytes_read = wintypes.SIZE()

            # Perform the read
            success = ctypes.windll.kernel32.ReadProcessMemory(
                process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                ctypes.sizeof(buffer),
                ctypes.byref(bytes_read),
            )

            if not success:
                raise MemoryReadError("Failed to read memory.", process_name=process_name, address=address)

            # Return the read value
            if isinstance(buffer, ctypes.Array):
                return buffer.value.decode("utf-8", errors="ignore")

            return buffer.value

        finally:
            # Ensure the process handle is always closed
            ctypes.windll.kernel32.CloseHandle(process_handle)

    except Exception as e:
        raise e


def read_memory_chunk(process_name: str, base_address: int, offsets: list[int]) -> list[int]:
    """Read a chunk of memory at different offsets.

    Args:
        process_name (str): name of the target process
        base_address (int): target address
        offsets (list[int]): offsets from target address to be read

    Raises:
        ValueError: Offsets must be nonempty
        MemoryReadError: Can't find target process.
        MemoryReadError: Can't open target process.
        MemoryReadError: Can't read target address.
        e: General exception.

    Returns:
        list[int]: list of memory values at offsets.
    """
    try:
        if not offsets:
            raise ValueError("Offsets list cannot be empty.")

        # Locate the process
        proc = get_process_by_name(process_name)
        if not proc:
            raise MemoryReadError("Process not found.", process_name=process_name)

        # Open the process
        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.pid)
        if not process_handle:
            raise MemoryReadError("Failed to open process.", process_name=process_name)

        try:
            # Calculate the range of memory to read
            size = max(offsets) + 4  # Adjust for last type size

            # Read the contiguous memory block
            buffer = (ctypes.c_ubyte * size)()
            bytes_read = wintypes.SIZE()

            success = ctypes.windll.kernel32.ReadProcessMemory(
                process_handle,
                ctypes.c_void_p(base_address),
                buffer,
                size,
                ctypes.byref(bytes_read),
            )

            if not success:
                raise MemoryReadError("Failed to read memory.", process_name=process_name, address=base_address)

            # Extract the values dynamically
            results = []
            for offset in offsets:
                # Assuming 2-byte word data; adjust for other types if needed
                value = buffer[offset] | (buffer[offset + 1] << 8)
                results.append(value)

            return results

        finally:
            # Ensure the process handle is always closed
            ctypes.windll.kernel32.CloseHandle(process_handle)

    except Exception as e:
        raise e
