#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) Open Astro Technologies, USA.
# Modified by Sundar Sundaresan, USA. carnaticmusicguru2015@comcast.net
# Downloaded from https://github.com/naturalstupid/PyJHora

# This file is part of the "PyJHora" Python library
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Karaka (significator) related functions for Vedic astrology charts.

Contains the three types of karakas:
- Chara Karakas: Significators based on planetary degrees
- Sthira Karakas: Fixed significators
- Naisargika Karakas: Natural significators

Also includes the longevity_of_pair helper used in longevity calculations.
"""
from jhora import const


def chara_karakas(planet_positions):
    """Get chara karakas for a dasa varga chart.

    Chara karakas are determined by ranking planets (Sun through Rahu) by their
    longitudinal advancement in their respective signs. The planet with the
    highest advancement becomes Atma Karaka, and so on.

    Args:
        planet_positions: Planet positions list in the format
            [[planet,(raasi,planet_longitude)],...]]
            First element is that of Lagnam. Example: [['L',(0,123.4)],[0,(11,32.7)],...]]
            Lagnam in Aries 123.4 degrees, Sun in Taurus 32.7 degrees

    Returns:
        List of planet indices as chara karakas. First element is the planet_index
        that is Atma Karaka, then Amatya Karaka, etc.
        ['atma_karaka','amatya_karaka','bhratri_karaka','maitri_karaka',
         'pitri_karaka','putra_karaka','jnaati_karaka','dara_karaka']
    """
    pp = [[i, row[-1][1]] for i, row in enumerate(planet_positions[const.SUN_ID + 1:const.KETU_ID + 1])]
    one_rasi = 360.0 / 12
    pp[-1][-1] = one_rasi - pp[-1][-1]
    pp1 = sorted(pp, key=lambda x: x[1], reverse=True)
    pp2 = [pi[0] for _, pi in enumerate(pp1)]
    return pp2


def sthira_karakas(planet_positions):
    """Get sthira karakas from dhasa varga chart positions.

    Sthira karakas are fixed significators. The first two are determined by
    comparing strength of specific planet pairs, while the rest are fixed.

    Args:
        planet_positions: Planet positions of the charts

    Returns:
        List of sthira karakas:
        [stronger of Sun or Venus, stronger of Moon or Mars, Mars, Mercury,
         Jupiter, Venus, Saturn]
    """
    from jhora.horoscope.chart.house import stronger_planet_from_planet_positions
    sk = [const.MARS_ID, const.MERCURY_ID, const.JUPITER_ID, const.VENUS_ID, const.SATURN_ID]
    sk1 = stronger_planet_from_planet_positions(planet_positions, const.SUN_ID, const.VENUS_ID)
    sk2 = stronger_planet_from_planet_positions(planet_positions, const.MOON_ID, const.MARS_ID)
    return [sk1, sk2] + sk


def naisargika_karakas():
    """Get the natural (naisargika) karakas.

    Returns:
        List of naisargika karakas from const module
    """
    return const.naisargika_karakas


def longevity_of_pair(rasi1, rasi2):
    """Get the longevity category for a pair of rasi types.

    Args:
        rasi1: First rasi type index (0=fixed, 1=movable, 2=dual)
        rasi2: Second rasi type index (0=fixed, 1=movable, 2=dual)

    Returns:
        Longevity category key from const.longevity
    """
    return [key for key, value in const.longevity.items() if (rasi1, rasi2) in value][0]
