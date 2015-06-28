#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# core.prepare Prepares the game environment.
#
"""This module initializes the display and creates dictionaries of resources.
It contains all the static and dynamic variables used throughout the game such
as display resolution, scale, etc.
"""

import os
import pygame as pg

from . import tools
from .components import config
from .components import player

# Import the android module. If we can't import it, set it to None - this
# lets us test it, and check to see if we want android-specific behavior.
try:
    import android
except ImportError:
    android = None


# Read the "tuxemon.cfg" configuration file
CONFIG = config.Config()

# Set up the screen size and caption
SCREEN_SIZE = CONFIG.resolution
ORIGINAL_CAPTION = "Tuxemon"

# Set the native tile size so we know how much to scale our maps
TILE_SIZE = [16, 16]    # 1 tile = 16 pixels

# Set the status icon size so we know how much to scale our menu icons
ICON_SIZE = [7, 7]

# Set the healthbar color
HP_COLOR = (112, 248, 168)

# Set the XP bar color
XP_COLOR = (248, 245, 71)

# Set the party limit
PARTY_LIMIT = 6

# Native resolution is similar to the old gameboy resolution. This is
# used for scaling.
NATIVE_RESOLUTION = [240, 160]

# If scaling is enabled, scale the tiles based on the resolution
if CONFIG.scaling == "1":
    SCALE = int((SCREEN_SIZE[0] / NATIVE_RESOLUTION[0]))
    TILE_SIZE[0] *= SCALE
    TILE_SIZE[1] *= SCALE
else:
    SCALE = 1


# Initialization of PyGame dependent systems.
def init():
    """The init function is used to initialize all PyGame dependent
    systems. This is primarily implemented to allow sphinx-apidoc
    to autogenerate documentation without initializing a PyGame
    window.

    :param None:
    
    :rtype: None
    :returns: None

    """

    # These variables will persist throughout the module so they
    # can be called externally. E.g. "prepare.SCREEN", etc.    
    global SCREEN
    global SCREEN_RECT
    global JOYSTICKS
    global player1
    global FONTS
    global MUSIC
    global SFX
    global GFX

    # Initialize PyGame and our screen surface.
    pg.init()
    pg.display.set_caption(ORIGINAL_CAPTION)
    SCREEN = pg.display.set_mode(SCREEN_SIZE, CONFIG.fullscreen, 32)
    SCREEN_RECT = SCREEN.get_rect()

    # Disable the mouse cursor visibility
    pg.mouse.set_visible(False)

    # Set up any gamepads that we detect
    # The following event types will be generated by the joysticks:
    # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    pg.joystick.init()
    JOYSTICKS = [pg.joystick.Joystick(x) 
        for x in range(pg.joystick.get_count())]

    # Initialize the individual joysticks themselves.
    for joystick in JOYSTICKS:
        joystick.init()

    # Map the appropriate android keys if we're on android
    if android:
        android.init()
        android.map_key(android.KEYCODE_MENU, pg.K_ESCAPE)

    # Create an instance of the player and list of NPCs
    player1 = player.Player()

    # Scale the sprite and its animations
    for key, animation in player1.sprite.items():
        animation.scale(
            tuple(i * SCALE for i in animation.getMaxSize()))

    for key, image in player1.standing.items():
        player1.standing[key] = pg.transform.scale(
            image, (image.get_width() * SCALE,
                    image.get_height() * SCALE))

    # Set the player's width and height based on the size of our scaled
    # sprite.
    player1.playerWidth, player1.playerHeight = \
        player1.standing["front"].get_size()
    player1.playerWidth = TILE_SIZE[0]
    player1.playerHeight = TILE_SIZE[1]
    player1.tile_size = TILE_SIZE

    # Put the player right in the middle of our screen.
    player1.position = [
        (SCREEN_SIZE[0] / 2) - (player1.playerWidth / 2),
        (SCREEN_SIZE[1] / 2) - (player1.playerHeight / 2)]

    # Set the player's collision rectangle
    player1.rect = pg.Rect(
        player1.position[0],
        player1.position[1],
        TILE_SIZE[0],
        TILE_SIZE[1])

    # Set the walking and running pixels per second based on the scale
    player1.walkrate *= SCALE
    player1.runrate *= SCALE


    # Resource loading (Fonts and music just contain path names).
    FONTS = tools.load_all_fonts(os.path.join("resources", "font"))
    MUSIC = tools.load_all_music(os.path.join("resources", "music"))
    SFX   = tools.load_all_sfx(os.path.join("resources", "sounds"))
    GFX   = tools.load_all_gfx(os.path.join("resources", "gfx"))

