"""ORM classes for all SQL tables."""

from sqlalchemy import DATETIME, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.schema import PrimaryKeyConstraint


class Base(DeclarativeBase):
    """Base table class."""

    pass


class Games(Base):
    """Games table class."""

    __tablename__ = "games"

    id = mapped_column(String, primary_key=True)
    created_at = mapped_column(DATETIME)


class Lord_Names(Base):
    """Lord names table class."""

    __tablename__ = "lord_names"

    lord_name = mapped_column(String(100))
    p_ID = mapped_column(Integer)
    teams = mapped_column(Integer)
    game_id = mapped_column(ForeignKey("games.id"))

    __table_args__ = (PrimaryKeyConstraint("game_id", "p_ID"),)


class Lords(Base):
    """Lords table class."""

    __tablename__ = "lords"

    time = mapped_column(Integer)
    p_ID = mapped_column(Integer)
    num_eco_buildings = mapped_column(Integer)
    num_total_buildings = mapped_column(Integer)
    num_eco_buildings = mapped_column(Integer)
    total_gold = mapped_column(Integer)
    weighted_troops_killed = mapped_column(Integer)
    weighted_buildings_destroyed = mapped_column(Integer)
    goods_received = mapped_column(Integer)
    goods_sent = mapped_column(Integer)
    housing = mapped_column(Integer)
    total_units = mapped_column(Integer)
    siege_engines = mapped_column(Integer)
    popularity = mapped_column(Integer)
    wood = mapped_column(Integer)
    hops = mapped_column(Integer)
    stone = mapped_column(Integer)
    iron = mapped_column(Integer)
    pitch = mapped_column(Integer)
    wheat = mapped_column(Integer)
    bread = mapped_column(Integer)
    cheese = mapped_column(Integer)
    meat = mapped_column(Integer)
    apples = mapped_column(Integer)
    gold = mapped_column(Integer)
    flour = mapped_column(Integer)
    bows = mapped_column(Integer)
    crossbows = mapped_column(Integer)
    spears = mapped_column(Integer)
    pikes = mapped_column(Integer)
    maces = mapped_column(Integer)
    swords = mapped_column(Integer)
    leather_armor = mapped_column(Integer)
    metal_armor = mapped_column(Integer)
    total_food = mapped_column(Integer)
    population = mapped_column(Integer)
    taxes = mapped_column(Integer)
    weighted_losses = mapped_column(Integer)
    ale_coverage = mapped_column(Integer)
    num_inns = mapped_column(Integer)
    num_bakery = mapped_column(Integer)
    weighted_units = mapped_column(Integer)
    num_farms = mapped_column(Integer)
    num_iron_mines = mapped_column(Integer)
    num_pitchrigs = mapped_column(Integer)
    num_quarries = mapped_column(Integer)
    game_id = mapped_column(ForeignKey("games.id"))

    __table_args__ = (PrimaryKeyConstraint("game_id", "p_ID", "time"),)


class Map_Data(Base):
    """Map data table class."""

    __tablename__ = "map_data"

    time = mapped_column(Integer)
    map_name = mapped_column(Integer)
    advantage_setting = mapped_column(Integer)
    start_year = mapped_column(Integer)
    start_month = mapped_column(Integer)
    end_year = mapped_column(Integer)
    end_month = mapped_column(Integer)
    year_month = mapped_column(DATETIME)
    game_id = mapped_column(ForeignKey("games.id"))

    __table_args__ = (PrimaryKeyConstraint("game_id", "time"),)


class Units(Base):
    """Units table class."""

    __tablename__ = "units"

    time = mapped_column(Integer)
    p_ID = mapped_column(Integer)
    a_archer = mapped_column(Integer)
    assassin = mapped_column(Integer)
    a_swordsman = mapped_column(Integer)
    crossbowman = mapped_column(Integer)
    h_archer = mapped_column(Integer)
    monk = mapped_column(Integer)
    pikeman = mapped_column(Integer)
    e_archer = mapped_column(Integer)
    ladderman = mapped_column(Integer)
    spearman = mapped_column(Integer)
    e_swordsman = mapped_column(Integer)
    maceman = mapped_column(Integer)
    knight = mapped_column(Integer)
    tunneler = mapped_column(Integer)
    slave = mapped_column(Integer)
    slinger = mapped_column(Integer)
    firethrower = mapped_column(Integer)
    catapult = mapped_column(Integer)
    mangonel = mapped_column(Integer)
    trebuchet = mapped_column(Integer)
    tower_ballista = mapped_column(Integer)
    shield = mapped_column(Integer)
    battering_ram = mapped_column(Integer)
    siege_tower = mapped_column(Integer)
    fireballista = mapped_column(Integer)
    melee = mapped_column(Integer)
    ranged = mapped_column(Integer)
    game_id = mapped_column(ForeignKey("games.id"))

    __table_args__ = (PrimaryKeyConstraint("game_id", "p_ID", "time"),)
