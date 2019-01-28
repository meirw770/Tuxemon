# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
from __future__ import unicode_literals

from tuxemon.core.components.event.eventaction import EventAction
from tuxemon.core.components.event import get_npc


class OpenShopAction(EventAction):
    name = "open_shop"
    valid_parameters = [
        (str, "npc_slug"),
    ]

    def start(self):
        npc = get_npc(self.game, self.parameters.npc_slug)

        def buy_menu():
            self.game.pop_state()
            self.game.push_state(
                "ShopMenuState",
                buyer=self.game.player1,
                seller=npc,
            )

        def sell_menu():
            self.game.pop_state()
            self.game.push_state(
                "ShopMenuState",
                buyer=None,
                seller=self.game.player1,
            )

        var_menu = [
            ("Buy", "Buy", buy_menu),
            ("Sell", "Sell", sell_menu),
        ]

        return self.game.push_state("ChoiceState", menu=var_menu)
