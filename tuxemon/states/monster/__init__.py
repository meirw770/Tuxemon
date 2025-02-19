# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Generator, Optional

import pygame
from pygame.rect import Rect

from tuxemon import graphics, prepare, tools
from tuxemon.menu.interface import ExpBar, HpBar, MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea, draw_text


class MonsterMenuState(Menu[Optional[Monster]]):
    """
    A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """

    background_filename = "gfx/ui/monster/monster_menu_bg.png"
    draw_borders = False

    def __init__(self) -> None:
        super().__init__()

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.rect = Rect(tools.scale_sequence((20, 80, 80, 100)))
        self.sprites.add(self.text_area, layer=100)

        # Set up the border images used for the monster slots
        self.monster_slot_border = {}
        self.monster_portrait = pygame.sprite.Sprite()
        self.hp_bar = HpBar()
        self.exp_bar = ExpBar()

        # load and scale the monster slot borders
        root = "gfx/ui/monster/"
        border_types = ["empty", "filled", "active"]
        for border_type in border_types:
            filename = root + border_type + "_monster_slot_border.png"
            border = graphics.load_and_scale(filename)

            filename = root + border_type + "_monster_slot_bg.png"
            background = graphics.load_image(filename)

            window = GraphicBox(border, background, None)
            self.monster_slot_border[border_type] = window

        # TODO: something better than this global, load_sprites stuff
        for monster in local_session.player.monsters:
            monster.load_sprites()

    def animate_monster_down(self) -> None:
        ani = self.animate(
            self.monster_portrait.rect,
            y=-tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_monster_up

    def animate_monster_up(self) -> None:
        ani = self.animate(
            self.monster_portrait.rect,
            y=tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_monster_down

    def calc_menu_items_rect(self) -> Rect:
        width, height = self.rect.size
        left = width // 2.25
        top = height // 12
        width //= 2
        return Rect(left, top, width, height - top * 2)

    def initialize_items(
        self,
    ) -> Generator[MenuItem[Optional[Monster]], None, None]:
        # position the monster portrait
        try:
            monster = local_session.player.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)

        # position and animate the monster portrait
        width, height = prepare.SCREEN_SIZE
        self.monster_portrait.rect = image.get_rect(
            centerx=width // 4,
            top=height // 12,
        )
        self.sprites.add(self.monster_portrait)
        self.animations.empty()
        self.animate_monster_down()

        width = prepare.SCREEN_SIZE[0] // 2
        height = prepare.SCREEN_SIZE[1] // int(
            local_session.player.party_limit * 1.5,
        )

        # make 6 slots
        for _ in range(local_session.player.party_limit):
            rect = Rect(0, 0, width, height)
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            item = MenuItem(surface, None, None, None)
            yield item

        self.refresh_menu_items()

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        pass

    def render_monster_slot(
        self,
        surface: pygame.surface.Surface,
        rect: Rect,
        monster: Optional[Monster],
        in_focus: bool,
    ) -> pygame.surface.Surface:
        filled = monster is not None
        border = self.determine_border(in_focus, filled)
        border.draw(surface)
        if monster is not None:
            self.draw_monster_info(surface, monster, rect)
        return surface

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        """
        Used to determine if a given monster should be selectable.

        When other code creates a MonsterMenu, it should overwrite this method
        to suit it's needs.

        Parameters:
            monster: The monster corresponding to the menu item, if any.

        """
        return monster is not None

    def refresh_menu_items(self) -> None:
        """Used to render slots after their 'focus' flags change."""

        for index, item in enumerate(self.menu_items):

            monster: Optional[Monster]
            try:
                monster = local_session.player.monsters[index]
            except IndexError:
                monster = None
            item.game_object = monster

            item.enabled = (monster is not None) and self.is_valid_entry(
                item.game_object
            )
            item.image.fill((0, 0, 0, 0))
            item.in_focus = (index == self.selected_index) and item.enabled
            self.render_monster_slot(
                item.image,
                item.image.get_rect(),
                item.game_object,
                item.in_focus,
            )

    def draw_monster_info(
        self,
        surface: pygame.surface.Surface,
        monster: Monster,
        rect: Rect,
    ) -> None:
        # position and draw hp bar
        hp_rect = rect.copy()
        left = int(rect.width * 0.6)
        right = rect.right - tools.scale(4)
        hp_rect.width = right - left
        hp_rect.left = left
        hp_rect.height = tools.scale(8)
        hp_rect.centery = rect.centery

        # draw the hp bar
        self.hp_bar.value = monster.current_hp / monster.hp
        self.hp_bar.draw(surface, hp_rect)

        # draw the name + gender
        if monster.gender == "male":
            icon = "♂"
        elif monster.gender == "female":
            icon = "♀"
        else:
            icon = ""
        text_rect = rect.inflate(-tools.scale(6), -tools.scale(6))
        draw_text(surface, monster.name + icon, text_rect, font=self.font)

        # draw the level info
        text_rect.top = rect.bottom - tools.scale(7)
        draw_text(
            surface,
            "  Lv " + str(monster.level),
            text_rect,
            font=self.font,
        )

        # draw any status icons
        # TODO: caching or something, idk
        # TODO: not hardcode icon sizes
        for index, status in enumerate(monster.status):
            if status.icon:
                image = graphics.load_and_scale(status.icon)
                pos = (
                    (rect.width * 0.45) + (index * tools.scale(6.5)),
                    rect.y + tools.scale(0),
                )
                surface.blit(image, pos)

    def determine_border(self, selected: bool, filled: bool) -> GraphicBox:
        if selected:
            return self.monster_slot_border["active"]
        elif filled:
            return self.monster_slot_border["filled"]
        else:
            return self.monster_slot_border["empty"]

    def on_menu_selection_change(self) -> None:
        try:
            monster = local_session.player.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.monster_portrait.image = image
        self.refresh_menu_items()
