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
Aspect (drishti) related functions for Vedic astrology charts.

Contains graha drishti (planetary aspects), raasi drishti (sign aspects),
argala calculations, and various functions for determining aspected planets,
houses, and signs.
"""
from jhora import const, utils
from jhora.horoscope.chart.house_relationships import (
    planet_list, rasi_names_en,
    quadrants_of_the_raasi, trines_of_the_raasi,
)


def _get_raasi_drishti_movable():
    """Compute raasi drishti for movable signs.

    Returns:
        Dict mapping each movable sign index to list of fixed sign indices it aspects
    """
    raasi_drishti = {}
    for ms in const.movable_signs:
        rd = []
        for fs in const.fixed_signs:
            if fs != ms + 1 and fs != ms - 1:
                rd.append(fs)
        raasi_drishti[ms] = rd
    return raasi_drishti


def _get_raasi_drishti_fixed():
    """Compute raasi drishti for fixed signs.

    Returns:
        Dict mapping each fixed sign index to list of movable sign indices it aspects
    """
    raasi_drishti = {}
    for fs in const.fixed_signs:
        rd = []
        for ms in const.movable_signs:
            if ms != fs + 1 and ms != fs - 1:
                rd.append(ms)
        raasi_drishti[fs] = rd
    return raasi_drishti


def _get_raasi_drishti_dual():
    """Compute raasi drishti for dual signs.

    Returns:
        Dict mapping each dual sign index to list of other dual sign indices it aspects
    """
    raasi_drishti = {}
    for fs in const.dual_signs:
        rd = []
        for ms in const.dual_signs:
            if fs != ms:
                rd.append(ms)
        raasi_drishti[fs] = rd
    return raasi_drishti


def _get_raasi_drishti():
    """Compute the complete raasi drishti mapping for all 12 signs.

    Combines movable, fixed, and dual sign drishti into a single sorted dict.

    Returns:
        Dict mapping each sign index (0-11) to list of sign indices it aspects
    """
    _raasi_drishti = {**_get_raasi_drishti_movable(), **_get_raasi_drishti_fixed(), **_get_raasi_drishti_dual()}
    _raasi_drishti = dict(sorted(_raasi_drishti.items()))
    return _raasi_drishti


def aspected_kendras_of_raasi(raasi, reverse_direction=False):
    """Get aspected kendra house numbers from a given raasi.

    Args:
        raasi: Sign index (0-11)
        reverse_direction: If True, reverse the direction (used for some dhasa-bukthi
            such as drig dhasa). Default is False.

    Returns:
        List of aspected house numbers [1,4,7,10] with respect to the raasi.
        NOTE: Kendras are returned as 1..12 instead of 0..11.
    """
    rd = _get_raasi_drishti()[raasi]
    rd = [r for r in rd if r > raasi] + [r for r in rd if r < raasi]
    rdr = rd[:]
    if reverse_direction:
        rdr.reverse()
        rdr = [r for r in rdr if r < raasi] + [r for r in rdr if r > raasi]
    return rdr


def graha_drishti_from_chart(house_to_planet_dict, separator='/'):
    """Get graha drishti from the chart positions of the planets.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them.
            Example: ['','','','','2','7','1/5','0','3/4','L','','6/8']
            1st element is Aries and last is Pisces.
        separator: Separator character used to separate planets in a house

    Returns:
        Tuple of (arp, ahp, app) where:
            arp = planets' graha drishti on raasis. Example: [[0,1],...]] Sun has graha drishti in Aries and Taurus
            ahp = planets' graha drishti on houses. Example: [[0,1],...]] Sun has graha drishti in 1st and 2nd houses
            app = planets' graha drishti on planets. Example: [[1,2],...]] Sun has graha drishti on Moon and Mars
    """
    h_to_p = house_to_planet_dict[:]
    # Remove uranus neptune and pluto from h_to_p
    h_to_p = utils.remove_tropical_planets_from_chart(h_to_p)
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    asc_house = p_to_h[const._ascendant_symbol]
    arp = {}
    ahp = {}
    app = {}
    for p, _ in enumerate(planet_list):
        house_of_the_planet = p_to_h[p]
        arp[p] = [(h + house_of_the_planet - 1) % 12 for h in const.graha_drishti[p]]
        ahp[p] = [(h - asc_house) % 12 for h in arp[p]]
        app[p] = sum([h_to_p[ar].replace(const._ascendant_symbol, '').split(separator) for ar in arp[p] if h_to_p[ar] != ''], [])
        app[p] = [int(pp) for pp in app[p] if pp != '']
    return arp, ahp, app


def graha_drishti_of_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get graha drishti of a planet on other planets.

    Returns list of planets on which the given planet has graha drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them.
            Example: ['','','','','2','7','1/5','0','3/4','L','','6/8']
        planet: The index of the planet for which graha drishti is sought
            (0=Sun, 9=Ketu, 'L'=Lagnam)
        separator: Separator character used to separate planets in a house

    Returns:
        List of planet indices on which the given planet has graha drishti
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(house_to_planet_dict)
    _, _, app = graha_drishti_from_chart(house_to_planet_dict, separator)
    arp, _, app1 = raasi_drishti_from_chart(house_to_planet_dict)
    app[planet] += app1[planet]
    ppd = {}
    hl = arp[planet]
    hp = p_to_h[planet]
    pp = []
    for h in hl:
        pp = planets_in_the_house((h + hp - 1) % 12, p_to_h, exclude_lagna=True)
    ppd[planet] = pp + app[planet]
    return list(set(ppd[planet]))


def raasi_drishti_from_chart(house_to_planet_dict, separator='/'):
    """Get raasi drishti from the chart positions of the planets.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them.
            Example: ['','','','','2','7','1/5','0','3/4','L','','6/8']
        separator: Separator character used to separate planets in a house

    Returns:
        Tuple of (arp, ahp, app) where:
            arp = raasis' graha drishti on raasis. Example: [[1,2],...]] Aries has raasi drishti in Taurus and Gemini
            ahp = raasis' graha drishti on houses. Example: [[1,2],...]] 1st house/Lagnam has raasi drishti in 2nd and 3rd houses
            app = raasis' graha drishti on planets. Example: [[1,2],...]] Aries has graha raasi on Moon and Mars
    """
    h_to_p = house_to_planet_dict[:]
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    asc_house = p_to_h[const._ascendant_symbol]
    rd = _get_raasi_drishti()
    arp = {}
    ahp = {}
    app = {}
    for p, _ in enumerate(planet_list[:9]):
        ph = p_to_h[p]
        arp[p] = rd[ph]
        ahp[p] = [(h - asc_house) % 12 for h in arp[p]]
        app[p] = sum([h_to_p[ar].split(separator) for ar in arp[p] if h_to_p[ar] != ''], [])
        app[p] = [int(pp) for pp in app[p] if pp != '' and pp != const._ascendant_symbol]
    return arp, ahp, app


def raasi_drishti_of_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get raasi drishti of a given raasi.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of sign indices aspected by the given raasi
    """
    return _get_raasi_drishti()[raasi]


def aspected_planets_of_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get planets aspected by the given planet using Graha Drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of planet indices aspected by the input planet
    """
    _, _, app = graha_drishti_from_chart(house_to_planet_dict, separator)
    aspected_planets = utils.flatten_list([map(int, value) for key, value in app.items() if planet == key])
    return aspected_planets


def aspected_rasis_of_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get raasis aspected by the given planet using Graha Drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of raasi indices aspected by the input planet
    """
    arp, _, _ = graha_drishti_from_chart(house_to_planet_dict, separator)
    aspected_rasis = utils.flatten_list([map(int, value) for key, value in arp.items() if planet == key])
    return aspected_rasis


def aspected_houses_of_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get houses aspected by the given planet using Graha Drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of house indices aspected by the input planet
    """
    _, ahp, _ = graha_drishti_from_chart(house_to_planet_dict, separator)
    aspected_houses = utils.flatten_list([map(int, value) for key, value in ahp.items() if planet == key])
    return aspected_houses


def aspected_planets_of_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get planets that have raasi drishti on the given raasi.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of planet indices that have raasi drishti on the given raasi
    """
    arp, _, _ = raasi_drishti_from_chart(house_to_planet_dict, separator=separator)
    aspected_planets = [key for key, value in arp.items() if raasi in value]
    return aspected_planets


def aspected_houses_of_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get aspected houses of the given raasi from the chart.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of house indices aspected by the given raasi
    """
    _, ahp, _ = raasi_drishti_from_chart(house_to_planet_dict, separator=separator)
    aspected_houses = [key for key, value in ahp.items() if str(raasi) in value]
    return aspected_houses


def aspected_raasis_of_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get aspected raasis of the given raasi from the chart.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of raasi indices that have drishti on the given raasi
    """
    arr, _, _ = raasi_drishti_from_chart(house_to_planet_dict, separator=separator)
    aspected_raasis = [key for key, value in arr.items() if raasi in value]
    return aspected_raasis


def get_argala(house_to_planet_dict, separator='\n'):
    """Get argala and Virodhargala from the chart.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them.
            Example: ['','','','','2','7','1/5','0','3/4','L','','6/8']
        separator: Separator character used to separate planets in a house

    Returns:
        Tuple of (argala, virodhargala) where:
            argala = list of houses each planet causing argala - 2D List [[0,2]..]] Sun causing argala in Ar and Ge
            virodhargala = list of houses each planet causing virodhargala - 2D List [[0,2]..]]
    """
    h_to_p = house_to_planet_dict[:]
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    asc_house = p_to_h[const._ascendant_symbol]
    argala = [[h_to_p[(r + asc_house + a - 1) % 12].replace(const._ascendant_symbol, '').replace(separator, '/').replace('//', '/') for a in const.argala_houses] for r in range(12)]
    virodhargala = [[h_to_p[(r + asc_house + a - 1) % 12].replace(const._ascendant_symbol, '').replace(separator, '/').replace('//', '/') for a in const.virodhargala_houses] for r in range(12)]
    return argala, virodhargala


def planets_aspecting_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get planets that aspect the given planet using graha drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of planet indices that aspect the given planet
    """
    _, _, app = graha_drishti_from_chart(house_to_planet_dict)
    aspecting_planets = [k for k, v in app.items() if planet in v]
    return aspecting_planets


def raasis_aspecting_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get raasis that aspect the given planet using graha drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of sign indices that aspect the given planet
    """
    arp, _, _ = graha_drishti_from_chart(house_to_planet_dict)
    aspecting_raasis = [k for k, v in arp.items() if planet in v]
    return aspecting_raasis


def houses_aspecting_the_planet(house_to_planet_dict, planet, separator='/'):
    """Get houses that aspect the given planet using graha drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        planet: Planet index
        separator: Separator character used to separate planets in a house

    Returns:
        List of house indices that aspect the given planet
    """
    _, ahp, _ = graha_drishti_from_chart(house_to_planet_dict)
    aspecting_houses = [k for k, v in ahp.items() if planet in v]
    return aspecting_houses


def planets_aspecting_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get planets that aspect the given raasi using raasi drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of planet indices that aspect the given raasi
    """
    _, _, app = raasi_drishti_from_chart(house_to_planet_dict)
    aspecting_planets = [k for k, v in app.items() if raasi in v]
    return aspecting_planets


def raasis_aspecting_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get raasis that aspect the given raasi using raasi drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of sign indices that aspect the given raasi
    """
    arp, _, _ = raasi_drishti_from_chart(house_to_planet_dict)
    aspecting_raasis = [k for k, v in arp.items() if raasi in v]
    return aspecting_raasis


def houses_aspecting_the_raasi(house_to_planet_dict, raasi, separator='/'):
    """Get houses that aspect the given raasi using raasi drishti.

    Args:
        house_to_planet_dict: List of raasi with planet ids in them
        raasi: Sign index (0-11)
        separator: Separator character used to separate planets in a house

    Returns:
        List of house indices that aspect the given raasi
    """
    _, ahp, _ = raasi_drishti_from_chart(house_to_planet_dict)
    aspecting_houses = [k for k, v in ahp.items() if raasi in v]
    return aspecting_houses


def planets_in_the_house(raasi, planet_to_house_dict=None, chart_1d=None,
                         planet_positions=None, exclude_lagna=False,
                         exclude_western_planets=True):
    """Get the list of planets in the given raasi/zodiac/house.

    Args:
        raasi: Sign/house index (0-11)
        planet_to_house_dict: Planet-to-house dictionary
        chart_1d: 1D chart list (house-to-planet)
        planet_positions: Planet positions list
        exclude_lagna: If True, exclude lagna from the result
        exclude_western_planets: If True, exclude western planets from the result

    Returns:
        List of planet indices in the given house

    Raises:
        ValueError: If raasi and one of (planet_to_house_dict, chart_1d, planet_positions) are not provided
    """
    if planet_positions is not None:
        planet_to_house_dict = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    if chart_1d is not None:
        planet_to_house_dict = utils.get_planet_to_house_dict_from_chart(chart_1d)
    if planet_to_house_dict is None or raasi is None:
        raise ValueError("raasi and one of (planet_to_house_dict,chart_1d,planet_positions) should be provided")
    _pir = [p for p, h in planet_to_house_dict.items() if h == raasi]
    if exclude_lagna and const._ascendant_symbol in _pir:
        _pir.remove(const._ascendant_symbol)
    if exclude_western_planets:
        [_pir.remove(op) for op in const.western_planets if op in _pir]
    return _pir
