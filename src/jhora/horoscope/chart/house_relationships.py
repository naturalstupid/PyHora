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
Pure house relationship calculation functions.

Contains functions for computing house relationships such as trines, quadrants,
dushthanas, chathusras, upachayas, panapharas, and apoklimas. Also includes
aggregate functions and planet-in-house queries.

All lambda assignments from the original monolithic house.py have been converted
to proper def statements with docstrings. Duplicate alias functions
(*_aspects_of_the_raasi vs *_of_the_raasi) have been consolidated, keeping only
the conventional Vedic astrology name (*_of_the_raasi) with inlined logic.
"""
from jhora import const, utils

# Module-level constants shared across the package
chara_karaka_names = const.chara_karaka_names
planet_list = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
rasi_names_en = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']


def get_relative_house_of_planet(from_house, planet_house):
    """Get the relative house number of a planet from a given house.

    Args:
        from_house: The reference house/sign index (0=Aries to 11=Pisces)
        planet_house: The house/sign index of the planet (0=Aries to 11=Pisces)

    Returns:
        Relative house number (1-12). E.g., if from_house=0 and planet_house=4,
        returns 5 meaning the planet is in the 5th house from the reference.
    """
    return (planet_house + 12 - from_house) % 12 + 1


def strong_signs_of_planet(planet, strength=const._FRIEND):
    """Get all signs where a planet has the specified strength level.

    Args:
        planet: Planet index (0=Sun to 8=Ketu)
        strength: Strength level constant (default: const._FRIEND)

    Returns:
        List of sign indices (0-11) where the planet has the given strength
    """
    return [h for h in range(12) if const.house_strengths_of_planets[planet][h] == strength]


def trines_of_the_raasi(raasi):
    """Get trikona (1st/5th/9th) house indices from a given raasi.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for trikona houses relative to the given raasi
    """
    return [(raasi + const.HOUSE_1) % 12, (raasi + const.HOUSE_5) % 12, (raasi + const.HOUSE_9) % 12]


# Backward-compatible alias
trikona_aspects_of_the_raasi = trines_of_the_raasi


def functional_benefic_lord_houses(asc_house):
    """Get functional benefic lord houses (trines from the ascendant).

    Args:
        asc_house: Ascendant sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for functional benefic houses
    """
    return trines_of_the_raasi(asc_house)


def functional_malefic_lord_houses(asc_house):
    """Get functional malefic lord houses (3rd/6th/11th from the ascendant).

    Args:
        asc_house: Ascendant sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for functional malefic houses
    """
    return [(asc_house + const.HOUSE_3) % 12, (asc_house + const.HOUSE_6) % 12, (asc_house + const.HOUSE_11) % 12]


def functional_neutral_lord_houses(asc_house):
    """Get functional neutral lord houses (2nd/8th/12th from the ascendant).

    Args:
        asc_house: Ascendant sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for functional neutral houses
    """
    return [(asc_house + const.HOUSE_2) % 12, (asc_house + const.HOUSE_8) % 12, (asc_house + const.HOUSE_12) % 12]


def lords_of_quadrants(h_to_p, raasi):
    """Get lords of quadrant houses from a given raasi.

    Args:
        h_to_p: House-to-planet list
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of planet indices that are lords of quadrant houses
    """
    from jhora.horoscope.chart.house import house_owner
    return [house_owner(h_to_p, h) for h in quadrants_of_the_raasi(raasi)]


def lords_of_trines(h_to_p, raasi):
    """Get lords of trine houses from a given raasi.

    Args:
        h_to_p: House-to-planet list
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of planet indices that are lords of trine houses
    """
    from jhora.horoscope.chart.house import house_owner
    return [house_owner(h_to_p, h) for h in trines_of_the_raasi(raasi)]


def lords_of_quadrants_from_planet_positions(planet_positions, raasi):
    """Get lords of quadrant houses from planet positions.

    Args:
        planet_positions: Planet positions list
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of planet indices that are lords of quadrant houses
    """
    from jhora.horoscope.chart.house import house_owner_from_planet_positions
    return [house_owner_from_planet_positions(planet_positions, int(h)) for h in quadrants_of_the_raasi(raasi)]


def lords_of_trines_from_planet_positions(planet_positions, raasi):
    """Get lords of trine houses from planet positions.

    Args:
        planet_positions: Planet positions list
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of planet indices that are lords of trine houses
    """
    from jhora.horoscope.chart.house import house_owner_from_planet_positions
    return [house_owner_from_planet_positions(planet_positions, int(h)) for h in trines_of_the_raasi(raasi)]


def is_yoga_kaaraka(asc_house, planet, planet_house):
    """Check if a planet is yoga kaaraka.

    A yoga kaaraka is a planet that owns both a kendra and a trikona from the
    ascendant and is the ruler/owner of the sign it occupies.

    Args:
        asc_house: Raasi index of Lagnam (0=Aries, 11=Pisces)
        planet: Index of Planet (0=Sun, 8=Ketu)
        planet_house: Raasi index of where planet is (0=Aries, 11=Pisces)

    Returns:
        True/False whether planet is yoga kaaraka or not
    """
    return (planet_house in quadrants_of_the_raasi(asc_house)
            and planet_house in trines_of_the_raasi(asc_house)
            and const.house_strengths_of_planets[planet][planet_house] == const._OWNER_RULER)


def trikonas():
    """Get all trikonas of all houses.

    Returns:
        List of 12 lists, each containing the trikona house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    trikonas_list = []
    for house in range(12):
        trik = [house, trines_of_the_raasi(house)]
        trik = [x + 1 for x in trik[1]]
        trikonas_list.append(trik)
    return trikonas_list


def dushthanas_of_the_raasi(raasi):
    """Get dushthana (6th/8th/12th) house indices from a given raasi.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for dushthana houses relative to the given raasi
    """
    return [int(raasi + const.HOUSE_6) % 12, int(raasi + const.HOUSE_8) % 12, int(raasi + const.HOUSE_12) % 12]


# Backward-compatible alias
dushthana_aspects_of_the_raasi = dushthanas_of_the_raasi


def dushthanas():
    """Get all dushthanas of all houses.

    Returns:
        List of 12 lists, each containing the dushthana house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    dushthanas_list = []
    for house in range(12):
        dust = [house, dushthanas_of_the_raasi(house)]
        dust = [x + 1 for x in dust[1]]
        dushthanas_list.append(dust)
    return dushthanas_list


def chathusras_of_the_raasi(raasi):
    """Get chathusra (4th/8th) house indices from a given raasi.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for chathusra houses relative to the given raasi
    """
    return [(raasi + const.HOUSE_4) % 12, (raasi + const.HOUSE_8) % 12]


# Backward-compatible alias
chathusra_aspects_of_the_raasi = chathusras_of_the_raasi


def chathusras():
    """Get all chathusras of all houses.

    Returns:
        List of 12 lists, each containing the chathusra house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    chathusras_list = []
    for house in range(12):
        chat = [house, chathusras_of_the_raasi(house)]
        chat = [x + 1 for x in chat[1]]
        chathusras_list.append(chat)
    return chathusras_list


def quadrants_of_the_raasi(raasi):
    """Get kendra (1st/4th/7th/10th) house indices from a given raasi.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for kendra houses relative to the given raasi
    """
    return [(raasi + const.HOUSE_1) % 12, (raasi + const.HOUSE_4) % 12,
            (raasi + const.HOUSE_7) % 12, (raasi + const.HOUSE_10) % 12]


# Backward-compatible alias
kendra_aspects_of_the_raasi = quadrants_of_the_raasi


def panapharas_of_the_raasi(raasi):
    """Get panaphara (2nd/5th/8th/11th) house indices from a given raasi.

    Panapharas are the kendras counted from the next sign.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for panaphara houses relative to the given raasi
    """
    return quadrants_of_the_raasi((raasi + 1) % 12)


def apoklimas_of_the_raasi(raasi):
    """Get apoklima (3rd/6th/9th/12th) house indices from a given raasi.

    Apoklimas are the kendras counted from the second next sign.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for apoklima houses relative to the given raasi
    """
    return quadrants_of_the_raasi((raasi + 2) % 12)


def upachayas_of_the_raasi(raasi):
    """Get upachaya (3rd/6th/10th/11th) house indices from a given raasi.

    Args:
        raasi: Sign index (0=Aries to 11=Pisces)

    Returns:
        List of sign indices for upachaya houses relative to the given raasi
    """
    return [(raasi + const.HOUSE_3) % 12, (raasi + const.HOUSE_6) % 12,
            (raasi + const.HOUSE_10) % 12, (raasi + const.HOUSE_11) % 12]


# Backward-compatible alias
upachaya_aspects_of_the_raasi = upachayas_of_the_raasi


def are_planets_in_quadrants(p_to_h, planet_list_arg):
    """Check if all specified planets are in quadrant houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in quadrants, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in quadrants_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_quadrants(p_to_h):
    """Get all planets in quadrant houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in quadrant houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in quadrants_of_the_raasi(asc_house)]


def are_planets_in_trines(p_to_h, planet_list_arg):
    """Check if all specified planets are in trine houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in trines, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in trines_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_trines(p_to_h):
    """Get all planets in trine houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in trine houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in trines_of_the_raasi(asc_house)]


def are_planets_in_panapharas(p_to_h, planet_list_arg):
    """Check if all specified planets are in panaphara houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in panapharas, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in panapharas_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_panapharas(p_to_h):
    """Get all planets in panaphara houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in panaphara houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in panapharas_of_the_raasi(asc_house)]


def are_planets_in_apoklimas(p_to_h, planet_list_arg):
    """Check if all specified planets are in apoklima houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in apoklimas, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in apoklimas_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_apklimas(p_to_h):
    """Get all planets in apoklima houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in apoklima houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in apoklimas_of_the_raasi(asc_house)]


def are_planets_in_upachayas(p_to_h, planet_list_arg):
    """Check if all specified planets are in upachaya houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in upachayas, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in upachayas_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_upachayas(p_to_h):
    """Get all planets in upachaya houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in upachaya houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in upachayas_of_the_raasi(asc_house)]


def are_planets_in_chathusras(p_to_h, planet_list_arg):
    """Check if all specified planets are in chathusra houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in chathusras, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in chathusras_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_chathusras(p_to_h):
    """Get all planets in chathusra houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in chathusra houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in chathusras_of_the_raasi(asc_house)]


def are_planets_in_dushthanas(p_to_h, planet_list_arg):
    """Check if all specified planets are in dushthana houses.

    Args:
        p_to_h: Planet-to-house dictionary
        planet_list_arg: List of planet indices to check

    Returns:
        True if all specified planets are in dushthanas, False otherwise
    """
    asc_house = p_to_h[const._ascendant_symbol]
    planet_houses = [(p_to_h[p] - asc_house) % 12 for p in planet_list_arg]
    return all(house in dushthanas_of_the_raasi(asc_house) for house in planet_houses)


def get_planets_in_dushthanas(p_to_h):
    """Get all planets in dushthana houses.

    Args:
        p_to_h: Planet-to-house dictionary

    Returns:
        List of planet indices that are in dushthana houses
    """
    asc_house = p_to_h[const._ascendant_symbol]
    return [p for p, _ in p_to_h.items() if p_to_h[p] in dushthanas_of_the_raasi(asc_house)]


def quadrants():
    """Get all quadrants of all houses. Alias for kendras().

    Returns:
        List of 12 lists, each containing the kendra house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    return kendras()


def kendras():
    """Get all kendras of all houses.

    Returns:
        List of 12 lists, each containing the kendra house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    kendras_list = []
    for house in range(12):
        ken = [house, quadrants_of_the_raasi(house)]
        ken = [x + 1 for x in ken[1]]
        kendras_list.append(ken)
    return kendras_list


def upachayas():
    """Get all upachayas of all houses.

    Returns:
        List of 12 lists, each containing the upachaya house numbers (1-12)
        relative to each house (0=Aries to 11=Pisces)
    """
    upachayas_list = []
    for house in range(12):
        upa = [house, [(house) % 12, (house + 3) % 12, (house + 7) % 12, (house + 8) % 12]]
        upa = [x + 1 for x in upa[1]]
        upachayas_list.append(upa)
    return upachayas_list
