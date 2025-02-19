# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, List

"""This module initializes the display and creates dictionaries of resources.
It contains all the static and dynamic variables used throughout the game such
as display resolution, scale, etc.
"""

import logging
import os.path
import re

from tuxemon import config
from tuxemon.constants import paths

if TYPE_CHECKING:
    import pygame as pg

    SCREEN: pg.surface.Surface
    SCREEN_RECT: pg.rect.Rect
    JOYSTICKS: List[pg.joystick.Joystick]

logger = logging.getLogger(__name__)

# TODO: refact this out when other platforms supported (such as headless)
PLATFORM = "pygame"

# list of regular expressions to blacklist devices
joystick_blacklist = [
    re.compile(r"Microsoft.*Transceiver.*"),
    re.compile(r".*Synaptics.*", re.I),
    re.compile(r"Wacom*.", re.I),
]

# Create game dir if missing
if not os.path.isdir(paths.USER_STORAGE_DIR):
    os.makedirs(paths.USER_STORAGE_DIR)

# Create game data dir if missing
if not os.path.isdir(paths.USER_GAME_DATA_DIR):
    os.makedirs(paths.USER_GAME_DATA_DIR)

# Create game savegame dir if missing
if not os.path.isdir(paths.USER_GAME_SAVE_DIR):
    os.makedirs(paths.USER_GAME_SAVE_DIR)

# Generate default config
config.generate_default_config()

# Read "tuxemon.cfg" config from disk, update and write back
CONFIG = config.TuxemonConfig(paths.USER_CONFIG_PATH)

with open(paths.USER_CONFIG_PATH, "w") as fp:
    CONFIG.cfg.write(fp)

# Set up the screen size and caption
SCREEN_SIZE = CONFIG.resolution

# Set the native tile size so we know how much to scale our maps
# 1 tile = 16 pixels
TILE_SIZE = (16, 16)

# Set the status icon size so we know how much to scale our menu icons
ICON_SIZE = [7, 7]

# Set the healthbar _color
HP_COLOR = (112, 248, 168)

# Set the XP bar _color
XP_COLOR = (248, 245, 71)

# Native resolution is similar to the old gameboy resolution. This is
# used for scaling.
NATIVE_RESOLUTION = [240, 160]

# Set the character limit for setting a player name.
PLAYER_NAME_LIMIT = 30

# Fonts
FONT_BASIC = "PressStart2P.ttf"
FONT_CHINESE = "SourceHanSerifCN-Bold.otf"
FONT_JAPANESE = "SourceHanSerifJP-Bold.otf"

# If scaling is enabled, scale the tiles based on the resolution
if CONFIG.large_gui:
    SCALE = 2
    TILE_SIZE = (TILE_SIZE[0] * SCALE, TILE_SIZE[1] * SCALE)
elif CONFIG.scaling:
    SCALE = int(SCREEN_SIZE[0] / NATIVE_RESOLUTION[0])
    TILE_SIZE = (TILE_SIZE[0] * SCALE, TILE_SIZE[1] * SCALE)
else:
    SCALE = 1

# Reference user save dir
SAVE_PATH = os.path.join(paths.USER_GAME_SAVE_DIR, "slot")
SAVE_METHOD = "JSON"
# SAVE_METHOD = "CBOR"

DEV_TOOLS = CONFIG.dev_tools


def pygame_init() -> None:
    """Eventually refactor out of prepare."""
    global JOYSTICKS
    global FONTS
    global MUSIC
    global SFX
    global GFX
    global SCREEN
    global SCREEN_RECT

    import pygame as pg

    # Configure databases and locale
    from tuxemon.locale import T

    T.collect_languages(CONFIG.recompile_translations)
    from tuxemon.db import db

    db.load()

    logger.debug("pygame init")
    pg.init()
    pg.display.set_caption(CONFIG.window_caption)

    from tuxemon import platform

    if platform.android:
        fullscreen = pg.FULLSCREEN
    else:
        fullscreen = pg.FULLSCREEN if CONFIG.fullscreen else 0
    flags = pg.HWSURFACE | pg.DOUBLEBUF | fullscreen

    SCREEN = pg.display.set_mode(SCREEN_SIZE, flags)
    SCREEN_RECT = SCREEN.get_rect()

    # Disable the mouse cursor visibility
    pg.mouse.set_visible(not CONFIG.hide_mouse)

    # Set up any gamepads that we detect
    # The following event types will be generated by the joysticks:
    # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    JOYSTICKS = list()
    pg.joystick.init()
    devices = [pg.joystick.Joystick(x) for x in range(pg.joystick.get_count())]

    # Initialize the individual joysticks themselves.
    for joystick in devices:
        name = joystick.get_name()
        print(f'Found joystick: "{name}"')
        blacklisted = any(i.match(name) for i in joystick_blacklist)
        if blacklisted:
            print(f'Ignoring joystick: "{name}"')
        else:
            print(f'Configuring joystick: "{name}"')
            joystick.init()
            JOYSTICKS.append(joystick)


# Initialize the game framework
def init() -> None:
    from tuxemon import platform

    platform.init()
    if PLATFORM == "pygame":
        pygame_init()


# Fetches a resource file
# note: this has the potential of being a bottle neck doing to all the checking of paths
# eventually, this should be configured at game launch, or in a config file instead
# of looking all over creation for the required files.
def fetch(*args: str) -> str:
    relative_path = os.path.join(*args)

    for mod_name in CONFIG.mods:
        # when assets are in folder with the source
        path = os.path.join(paths.mods_folder, mod_name, relative_path)
        logger.debug("searching asset: %s", path)
        if os.path.exists(path):
            return path

        # when assets are in a system path (like for os packages and android)
        for root_path in paths.system_installed_folders:
            path = os.path.join(root_path, "mods", mod_name, relative_path)
            logger.debug("searching asset: %s", path)
            if os.path.exists(path):
                return path

        # mods folder is in same folder as the launch script
        path = os.path.join(paths.BASEDIR, "mods", mod_name, relative_path)
        logger.debug("searching asset: %s", path)
        if os.path.exists(path):
            return path

    raise OSError(f"cannot load file {relative_path}")
