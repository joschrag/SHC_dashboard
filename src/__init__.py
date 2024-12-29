"""This module initializes the database and contains the other submodules."""

import logging
import pathlib

import sqlalchemy as sa

from .parser.read_data import read_config, read_memory, read_memory_chunk  # noqa: F401
from .setup_logging import NonErrorFilter, setup_logging  # noqa: F401
from .tables import Base, Games, Lord_Names, Lords, Map_Data, Units  # noqa: F401

db_file = pathlib.Path.cwd() / "db" / "db.sqlite"
if not db_file.exists():
    db_file.touch()
engine = sa.create_engine("sqlite:///db/db.sqlite")

setup_logging()
Base.metadata.create_all(engine)
PROCESS_NAME = "Stronghold_Crusader_Extreme.exe"
SHC_COLORS = ["#ef0008", "#d67300", "#e7c600", "#0084e7", "#6b6b6b", "#9c21b5", "#31a5bd", "#18bd10"]
IMAGE_PATHS = read_config("images", "app")

APP_CATEGORIES = read_config("stat_categories", "app")
logger = logging.getLogger(__name__)
