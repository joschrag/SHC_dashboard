import ctypes
import logging
import pathlib
from ctypes import Array, c_bool, c_byte, c_char, c_uint16, c_uint32, wintypes
from enum import Enum

import numpy as np
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
    BOOLEAN = 3
    WORD = 4


d_types: dict[D_Types, c_uint32 | c_byte | c_bool | c_uint16 | Array[c_char]] = {
    D_Types.INT: ctypes.c_uint32(),
    D_Types.STRING: ctypes.create_string_buffer(256),
    D_Types.BYTE: ctypes.c_byte(),
    D_Types.BOOLEAN: ctypes.c_bool(),
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


def slice_ctypes_array(ctypes_array: Array, offset: int, length: int) -> Array:
    array_type = ctypes.c_byte * length
    return array_type(*ctypes_array[offset : offset + length])  # noqa: E203


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


def read_memory_chunk(
    process_name: str, base_address: int, offsets: list[int], dtype: D_Types | list[D_Types]
) -> list[int | str | bool]:
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

        if not isinstance(dtype, list):
            dtype = [dtype] * len(offsets)

        if len(dtype) != len(offsets):
            raise ValueError("The length of dtype list must match the length of offsets.")

        if offsets != sorted(offsets):
            offsets, dtype = map(list, zip(*sorted(zip(offsets, dtype))))

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
            type_sizes = {
                D_Types.INT: ctypes.sizeof(c_uint32()),
                D_Types.STRING: 256,  # Assuming a fixed size for strings
                D_Types.BYTE: ctypes.sizeof(c_byte()),
                D_Types.BOOLEAN: ctypes.sizeof(c_bool()),
                D_Types.WORD: ctypes.sizeof(c_uint16()),
            }
            size = offsets[-1] + type_sizes[dtype[-1]]

            # Read the contiguous memory block
            buffer: Array[c_byte] = (ctypes.c_byte * size)()
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
            for offset, d in zip(offsets, dtype):
                slice = slice_ctypes_array(buffer, offset, type_sizes[d])
                if d == D_Types.INT:
                    value: int | str | bool = ctypes.c_uint32.from_buffer_copy(slice).value
                elif d == D_Types.STRING:
                    # print(chardet.detect(bytes(np.mod(buffer[offset : offset + type_sizes[d]], 256).tolist())))
                    value = ctypes.create_string_buffer(
                        bytes(np.mod(buffer[offset : offset + type_sizes[d]], 256))  # noqa: E203
                    ).value.decode("ISO-8859-1")
                elif d == D_Types.BYTE:
                    value = ctypes.c_byte.from_buffer_copy(slice).value
                elif d == D_Types.BOOLEAN:
                    value = ctypes.c_bool.from_buffer_copy(slice).value
                elif d == D_Types.WORD:
                    value = ctypes.c_uint16.from_buffer_copy(slice).value
                else:
                    raise ValueError(
                        (
                            "ctypes.c_uint32.from_buffer_copy(buffer[offset : offset + type_sizes[d]])"
                            f".valueUnsupported data type: {d}"
                        )
                    )
                results.append(value)

            return results

        finally:
            # Ensure the process handle is always closed
            ctypes.windll.kernel32.CloseHandle(process_handle)

    except Exception as e:
        raise e
