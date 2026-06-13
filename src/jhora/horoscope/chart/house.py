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
    Release History:
    V4.8.6 - Error in rudra(planet_positions) fixed.

    Refactored: Split into three focused modules for maintainability.
    - house_relationships.py: Pure house relationship calculations
    - house_aspects.py: Aspect/drishti related functions
    - house_karakas.py: Karaka (significator) functions

    This module re-exports everything from the three sub-modules for
    backward compatibility. All existing imports like
    `from jhora.horoscope.chart import house` will continue to work.
"""
from jhora import const, utils
from jhora.panchanga import drik

# Re-export everything from the three sub-modules for backward compatibility
from jhora.horoscope.chart.house_relationships import *  # noqa: F401,F403
from jhora.horoscope.chart.house_aspects import *  # noqa: F401,F403
from jhora.horoscope.chart.house_karakas import *  # noqa: F401,F403

# Explicit re-exports of key names to make them available via house.X
from jhora.horoscope.chart.house_relationships import (  # noqa: F811
    chara_karaka_names, planet_list, rasi_names_en,
    get_relative_house_of_planet, strong_signs_of_planet,
    trines_of_the_raasi, trikona_aspects_of_the_raasi,
    functional_benefic_lord_houses, functional_malefic_lord_houses,
    functional_neutral_lord_houses,
    lords_of_quadrants, lords_of_trines,
    lords_of_quadrants_from_planet_positions, lords_of_trines_from_planet_positions,
    is_yoga_kaaraka,
    trikonas,
    dushthanas_of_the_raasi, dushthana_aspects_of_the_raasi,
    dushthanas,
    chathusras_of_the_raasi, chathusra_aspects_of_the_raasi,
    chathusras,
    quadrants_of_the_raasi, kendra_aspects_of_the_raasi,
    panapharas_of_the_raasi, apoklimas_of_the_raasi,
    upachayas_of_the_raasi, upachaya_aspects_of_the_raasi,
    are_planets_in_quadrants, get_planets_in_quadrants,
    are_planets_in_trines, get_planets_in_trines,
    are_planets_in_panapharas, get_planets_in_panapharas,
    are_planets_in_apoklimas, get_planets_in_apklimas,
    are_planets_in_upachayas, get_planets_in_upachayas,
    are_planets_in_chathusras, get_planets_in_chathusras,
    are_planets_in_dushthanas, get_planets_in_dushthanas,
    quadrants, kendras, upachayas,
)
from jhora.horoscope.chart.house_aspects import (  # noqa: F811
    _get_raasi_drishti_movable, _get_raasi_drishti_fixed, _get_raasi_drishti_dual,
    _get_raasi_drishti,
    aspected_kendras_of_raasi,
    graha_drishti_from_chart, graha_drishti_of_the_planet,
    raasi_drishti_from_chart, raasi_drishti_of_the_raasi,
    aspected_planets_of_the_planet, aspected_rasis_of_the_planet,
    aspected_houses_of_the_planet,
    aspected_planets_of_the_raasi, aspected_houses_of_the_raasi,
    aspected_raasis_of_the_raasi,
    get_argala,
    planets_aspecting_the_planet, raasis_aspecting_the_planet,
    houses_aspecting_the_planet,
    planets_aspecting_the_raasi, raasis_aspecting_the_raasi,
    houses_aspecting_the_raasi,
    planets_in_the_house,
)
from jhora.horoscope.chart.house_karakas import (  # noqa: F811
    chara_karakas, sthira_karakas, naisargika_karakas,
    longevity_of_pair,
)


# =============================================================================
# Functions that remain in house.py — they depend on multiple sub-modules
# and don't fit neatly into any single category.
# =============================================================================


def stronger_planet_from_planet_positions(planet_positions, planet1=None, planet2=None, check_during_dhasa=False):
    """
        To find stronger planet between Rahu/Saturn/Aquarius or Ketu/Mars/Scorpio 
        @param planet_positions list in the format [[planet,(raasi,planet_longitude)],...]] 
            First element is that of Lagnam. Example: [ ['L',(0,123.4)],[0,(11,32.7)],...]]
            Lagnam in Aries 123.4 degrees, Sun in Taurus 32.7 degrees
        @param planet1 and planet2 has to be either Rahu/Saturn 7 and 6 or Ketu/Mars 8 and 3
          Default: planet1=6 (Saturn) and planet2=7 (Rahu)
        @param check_during_dhasa True/False. Set this to True if checking for dhasa-bhukthi
        @return stronger of planet1 and planet2
            Stronger of Rahu/Saturn or Ketu/Mars is returned
    """
    if planet1 is None: planet1 = const.SATURN_ID
    if planet2 is None: planet2 = const.RAHU_ID
    ### V4.6.5 Following checks added to force Saturn or Mars to be strong owner if configured
    if {planet1, planet2} == {const.RAHU_ID,const.SATURN_ID} and const.aquarius_owner_for_dhasa_calculations in [const.RAHU_ID,const.SATURN_ID]:
        return const.aquarius_owner_for_dhasa_calculations
    if {planet1, planet2} == {const.MARS_ID,const.KETU_ID} and const.scorpio_owner_for_dhasa_calculations in [const.MARS_ID,const.KETU_ID]:
        return const.scorpio_owner_for_dhasa_calculations
    _debug_print = False
    if planet1==planet2:
        return planet1
    if planet1==const._ascendant_symbol:
        planet1_rasi = planet_positions[0][1][0]; planet2_rasi = planet_positions[planet2+1][1][0]
        sr = stronger_rasi_from_planet_positions(planet_positions, planet1_rasi, planet2_rasi)
        if sr == planet1_rasi:
            return planet1
        else:
            return planet2
    if planet2==const._ascendant_symbol:
        planet2_rasi = planet_positions[0][1][0]; planet1_rasi = planet_positions[planet1+1][1][0]
        sr = stronger_rasi_from_planet_positions(planet_positions, planet1_rasi, planet2_rasi)
        if sr == planet1_rasi:
            return planet1
        else:
            return planet2
    house_to_planet_dict = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    stronger_planet = _stronger_planet_new(house_to_planet_dict,planet1,planet2)
    if stronger_planet is not None:
        return stronger_planet
    if _debug_print: print("Rule-4: Both planets are in same type of rasi Dual/fixed/movable - and are equally stronger")
    planet1_house = p_to_h[planet1]
    planet1_longitude = planet_positions[planet1+1][1][1] # +1 to inlcude first element 'L'
    planet2_house = p_to_h[planet2]
    planet2_longitude = planet_positions[planet2+1][1][1]
    if check_during_dhasa:
        """ Rule-5-a, planet giving a larger length for narayana dhasa"""
        from jhora.horoscope.dhasa.raasi import narayana 
        planet1_narayana_dhasa_duration = narayana._dhasa_duration(planet_positions,planet1_house)
        if _debug_print: print('planet1_narayana_dhasa_duration',planet1_narayana_dhasa_duration)
        planet2_narayana_dhasa_duration = narayana._dhasa_duration(planet_positions,planet2_house)
        if _debug_print: print('planet2_narayana_dhasa_duration',planet2_narayana_dhasa_duration)
        if planet1_narayana_dhasa_duration > planet2_narayana_dhasa_duration:
            if _debug_print: print('Rule-5(a): Planet1/Saturn/Mars is stronger')
            return planet1
        elif planet2_narayana_dhasa_duration > planet1_narayana_dhasa_duration:
            if _debug_print: print('Rule-5(a): Planet2/Rahu/Ketu is stronger')
            return planet2
    #else: # Check during Arudhas
    """ Rule 5(b) the planet that is more advanced in its rasi. """
    if planet1_longitude is not None and planet2_longitude is not None:
        if planet1_longitude > planet2_longitude:
            if _debug_print: print('Rule 5(b)',planet_list[planet1],' is stronger than',planet_list[planet2],planet1_longitude,'>',planet2_longitude)
            return planet1
        else:
            if _debug_print: print('Rule 5(b)',planet_list[planet2],' is stronger than',planet_list[planet1],planet2_longitude,'>',planet1_longitude)
            return planet2
def _stronger_planet_new(house_to_planet_dict,planet1=None,planet2=None):
    if planet1 is None: planet1 = const.SATURN_ID
    if planet2 is None: planet2 = const.RAHU_ID
    _debug_print = False
    if _debug_print: print('stronger_planet_new: finding stronger co lords ',planet_list[planet1],planet_list[planet2])
    if planet1==planet2:
        return planet1
    p_to_h = utils.get_planet_to_house_dict_from_chart(house_to_planet_dict)
    if _debug_print: print('p_to_h',p_to_h)
    """
    ### Validate planet inputs
    valid_input = (planet1 == 6 and planet2 == 7) or (planet1 == 2 and planet2 == 8)
    if not valid_input:
        print('Only accepted planet combinations are Saturn/Rahu or Mar/Ketu')
        return None  
    """
    RAHU_OR_KETU = [const.RAHU_ID,const.KETU_ID]
    planet1_house = p_to_h[planet1]
    if _debug_print: print('planet1',planet1,planet_list[planet1],'in house',planet1_house,rasi_names_en[planet1_house])
    planet2_house = p_to_h[planet2]
    if _debug_print: print('planet2',planet2,planet_list[planet2],'in house',planet2_house,rasi_names_en[planet2_house])
    if planet1 in RAHU_OR_KETU:
        lord_house_of_planets = const.houses_of_rahu_kethu[planet1] #const.house_lords_dict#
    elif planet2 in RAHU_OR_KETU:
        lord_house_of_planets = const.houses_of_rahu_kethu[planet2] #const.house_lords_dict#
    #if _debug_print: print('lord_house_of_planets',lord_house_of_planets)
    """ Basic Rule - If Planet1/Saturn/Mars in Aq/Sc and Planet2/Rahu/Ketu elsewhere then Planet2/Rahu/Ketu is stronger """
    if ((planet2 in RAHU_OR_KETU  or planet1 in RAHU_OR_KETU) and planet1_house==lord_house_of_planets and planet2_house != lord_house_of_planets):
        if _debug_print: print('Basic Rule','Planet2/Rahu/Ketu is stronger')
        return planet2
    if ((planet2 in RAHU_OR_KETU  or planet1 in RAHU_OR_KETU) and planet2_house==lord_house_of_planets and planet1_house != lord_house_of_planets):
        if _debug_print: print('Basic Rule','Planet1/Saturn/Mars is stronger')
        return planet1
    #if _debug_print: print('Basic Rule: Neither',planet_list[planet1],' nor ',planet_list[planet2],'in',lord_house_of_planets)
    """ Rule-1: If one planet is joined by more planets than the other, it is stronger. """
    planet1_co_planet_count = sum(value==planet1_house for value in p_to_h.values()) - 1 # Exclude planet itsef
    if _debug_print: print('Rule-1','planet1_co_planet_count',planet1_co_planet_count)
    planet2_co_planet_count = sum(value==planet2_house for value in p_to_h.values()) - 1 # Exclude planet itself
    if _debug_print: print('Rule-1','planet2_co_planet_count',planet2_co_planet_count)
    if planet1_co_planet_count > planet2_co_planet_count:
        if _debug_print: print('Rule-1','Planet1/Saturn/Mars is stronger')
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        if _debug_print: print('Rule-1','Planet2/Rahu/Ketu is stronger')
        return planet2
    if _debug_print: print('Rule-1: Both planets have same co planet count',planet1_co_planet_count,planet2_co_planet_count)
    """ Rule-2: how many of the following planets conjoin/aspect a planet: (1) Jupiter,(2) Mercury, and, (3) dispositor. """
    # Dispositor of a planet = lord of the house where the planet is
    dispositor_of_planet1_house = const.house_owners[planet1_house]
    if _debug_print: print('dispositor_of_planet1_house',planet_list[dispositor_of_planet1_house])
    planet1_co_planet_count = 0
    planet1_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet1_house].count(planet1_house)
    #if _debug_print: print('Planet1',planet_list[planet1],' cojoin count',planet1_co_planet_count)
    planet1_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet1_house)
    if _debug_print: print('Aspects of',planet_list[planet1],[planet_list[p] for p in planet1_aspects])
    planet1_co_planet_count += sum(p1 in planet1_aspects for p1 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet1_house])
    if _debug_print: print('Planet1',planet_list[planet1],' aspect count',planet1_co_planet_count)
    if _debug_print: print('Rule-2','Planet1',planet_list[planet1],'Aspect/Cojoin count',planet1_co_planet_count)

    planet2_co_planet_count = 0
    dispositor_of_planet2_house = const.house_owners[planet2_house]
    if _debug_print: print('dispositor_of_planet2_house',planet_list[dispositor_of_planet2_house])
    planet2_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet2_house].count(planet2_house)
    if _debug_print: print('Planet2',planet_list[planet2],' cojoin count',planet2_co_planet_count)
    planet2_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet2_house)
    if _debug_print: print('Aspects of',planet_list[planet2],[planet_list[p] for p in planet2_aspects])
    planet2_co_planet_count += sum(p2 in planet2_aspects for p2 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet2_house])
    if _debug_print: print('Planet2',planet_list[planet2],' aspect count',planet2_co_planet_count)
    if _debug_print: print('Rule-2','Planet2',planet_list[planet2],'Aspect/Cojoin count',planet2_co_planet_count)
    """
    planet1_co_planet_count = sum( ((value==planet1_house) and (value==p_to_h[3]) and (value==p_to_h[4]) \
                                   and (value==dispositor_of_planet1_house)) for value in p_to_h.values())
    print('Rule-2','planet1_house',planet1_house,'dispositor_of_planet1_house',dispositor_of_planet1_house,'planet1_co_planet_count',planet1_co_planet_count)
    dispositor_of_planet2_house = const.house_owners[planet2_house]
    print('dispositor_of_planet2_house',planet_list[dispositor_of_planet2_house])
    planet2_co_planet_count = sum( ((value==planet2_house) and (value==p_to_h[3]) and (value==p_to_h[4]) \
                                   and (value==dispositor_of_planet2_house)) for value in p_to_h.values())
    """
    if planet1_co_planet_count > planet2_co_planet_count:
        if _debug_print: print('Rule-2','Planet1/Saturn/Mars is stronger')
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        if _debug_print: print('Rule-2','Planet2/Rahu/Ketu is stronger')
        return planet2
    if _debug_print: print("Rule-2 Both planets have same Cojoin/Aspects count",planet1_co_planet_count,planet2_co_planet_count)
    """ Rule-3: If one planet is exalted and the other not, then the exalted planet is stronger. """
    if _debug_print: print('house_strengths_of_planet1',const.house_strengths_of_planets[planet1][planet1_house], 'house_strengths_of_planet2',const.house_strengths_of_planets[planet2][planet2_house])
    if const.house_strengths_of_planets[planet1][planet1_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet1][planet1_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        if _debug_print: print('Rule-3','Planet1/Saturn/Mars is exhalted and thus stronger')
        return planet1
    if const.house_strengths_of_planets[planet2][planet2_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet2][planet2_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        if _debug_print: print('Rule-3','Planet2/Rahu/Ketu is exhalted and thus stronger')
        return planet2
    if _debug_print: print("Rule-3:None of the planets are exhalted and thus stronger")
    """ Rule - 4: natural strength of the rasi containing the planet. 
        Dual rasis are stronger than fixed rasis and fixed rasis are stronger than movable rasis.
    """
    # Rule - 4: natural strength of the rasi containing the planet.
    # Dual rasis are stronger than fixed rasis and fixed rasis are stronger than movable rasis.
    
    def _mod_rank(sign_idx):
        if sign_idx in const.dual_signs:
            return 3  # Dual
        elif sign_idx in const.fixed_signs:
            return 2  # Fixed
        else:
            return 1  # Movable
    
    m1 = _mod_rank(planet1_house)
    m2 = _mod_rank(planet2_house)
    
    if m1 > m2:
        if _debug_print: print("Rule-4: Planet1 stronger (Dual>Fixed>Movable)")
        return planet1
    elif m2 > m1:
        if _debug_print: print("Rule-4: Planet2 stronger (Dual>Fixed>Movable)")
        return planet2
    else:
        # SAME modality → Rule-4 cannot decide; let Rule-5 handle it.
        if _debug_print: print("Rule-4: tie on modality — defer to Rule-5")
    return None
def stronger_planet(house_to_planet_dict,planet1=None,planet2=None,check_during_dhasa=False,
                    planet1_longitude=None,planet2_longitude=None):
    """
        NOTE: To check all rules of strength use stronger_planet_from_planet_positions()
        To find stronger planet between Rahu/Saturn/Aquarius or Ketu/Mars/Scorpio 
        @param house_to_planet_dict: list of raasi with planet ids in them
          Example: ['','','','','2','7','1/5','0','3/4','L','','6/8'] 1st element is Aries and last is Pisces
        @param planet1 and planet2 has to be either Rahu/Saturn 7 and 6 or Ketu/Mars 8 and 3
          Default: planet1=6 (Saturn) and planet2=7 (Rahu)
        @return stronger of planet1 and planet2
            Stronger of Rahu/Saturn or Ketu/Mars is returned
    """
    if planet1 is None: planet1 = const.SATURN_ID
    if planet2 is None: planet2 = const.RAHU_ID
    ### V4.6.5 Following checks added to force Saturn or Mars to be strong owner if configured
    if {planet1, planet2} == {const.RAHU_ID,const.SATURN_ID} and const.aquarius_owner_for_dhasa_calculations in [const.SATURN_ID,const.RAHU_ID]:
        return const.aquarius_owner_for_dhasa_calculations
    if {planet1, planet2} == {const.MARS_ID,const.KETU_ID} and const.scorpio_owner_for_dhasa_calculations in [const.MARS_ID,const.KETU_ID]:
        return const.scorpio_owner_for_dhasa_calculations
    if planet1==planet2:
        return planet1
    p_to_h = utils.get_planet_to_house_dict_from_chart(house_to_planet_dict)
    """
    ### Validate planet inputs
    valid_input = (planet1 == 6 and planet2 == 7) or (planet1 == 2 and planet2 == 8)
    if not valid_input:
        print('Only accepted planet combinations are Saturn/Rahu or Mar/Ketu')
        return None  
    """
    planet1_house = p_to_h[planet1]
    #print('planet1',planet1,planet_list[planet1],'in house',planet1_house,rasi_names_en[planet1_house])
    planet2_house = p_to_h[planet2]
    #print('planet2',planet2,planet_list[planet2],'in house',planet2_house,rasi_names_en[planet2_house])
    lord_house_of_planets = const.house_lords_dict#const.houses_of_rahu_kethu[planet2]
    #print('lord_house_of_planets',lord_house_of_planets,[rasi_names_en[p] for p in lord_house_of_planets])
    """ Basic Rule - If Planet1/Saturn/Mars in Aq/Sc and Planet2/Rahu/Ketu elsewhere then Planet2/Rahu/Ketu is stronger """
    if (planet1_house==lord_house_of_planets and planet2_house != lord_house_of_planets):
        #print('Basic Rule','Planet2/Rahu/Ketu is stronger')
        return planet2
    if (planet2_house==lord_house_of_planets and planet1_house != lord_house_of_planets):
        #print('Basic Rule','Planet1/Saturn/Mars is stronger')
        return planet1
    #print('Basic Rule: Neither',planet1,' nor ',planet2,'in',lord_house_of_planets)
    """ Rule-1: If one planet is joined by more planets than the other, it is stronger. """
    planet1_co_planet_count = sum(value==planet1_house for value in p_to_h.values()) - 1 # Exclude planet itsef
    #print('Rule-1','planet1_co_planet_count',planet1_co_planet_count)
    planet2_co_planet_count = sum(value==planet2_house for value in p_to_h.values()) - 1 # Exclude planet itself
    #print('Rule-1','planet2_co_planet_count',planet2_co_planet_count)
    if planet1_co_planet_count > planet2_co_planet_count:
        #print('Rule-1','Planet1/Saturn/Mars is stronger')
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        #print('Rule-1','Planet2/Rahu/Ketu is stronger')
        return planet2
    #print('Rule-1: Both planets have same co planet count',planet1_co_planet_count,planet2_co_planet_count)
    """ Rule-2: how many of the following planets conjoin/aspect a planet: (1) Jupiter,(2) Mercury, and, (3) dispositor. """
    # Dispositor of a planet = lord of the house where the planet is
    dispositor_of_planet1_house = const.house_owners[planet1_house]
    #print('dispositor_of_planet1_house',planet_list[dispositor_of_planet1_house])
    planet1_co_planet_count = 0
    planet1_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet1_house].count(planet1_house)
    #print('Planet1',planet_list[planet1],' cojoin count',planet1_co_planet_count)
    planet1_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet1_house)
    #print('Aspects of',planet_list[planet1],[planet_list[p] for p in planet1_aspects])
    planet1_co_planet_count += sum(planet1_aspects.count(p1) for p1 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet1_house])
    #print('Planet1',planet_list[planet1],' aspect count',planet1_co_planet_count)
    #print('Rule-2','Planet1',planet_list[planet1],'Aspect/Cojoin count',planet1_co_planet_count)

    planet2_co_planet_count = 0
    dispositor_of_planet2_house = const.house_owners[planet2_house]
    #print('dispositor_of_planet2_house',planet_list[dispositor_of_planet2_house])
    planet2_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet2_house].count(planet2_house)
    #print('Planet2',planet_list[planet2],' cojoin count',planet2_co_planet_count)
    planet2_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet2_house)
    #print('Aspects of',planet_list[planet2],[planet_list[p] for p in planet2_aspects])
    planet2_co_planet_count += sum(planet2_aspects.count(p2) for p2 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet2_house])
    #print('Planet2',planet_list[planet2],' aspect count',planet2_co_planet_count)
    #print('Rule-2','Planet2',planet_list[planet2],'Aspect/Cojoin count',planet2_co_planet_count)
    """
    planet1_co_planet_count = sum( ((value==planet1_house) and (value==p_to_h[3]) and (value==p_to_h[4]) \
                                   and (value==dispositor_of_planet1_house)) for value in p_to_h.values())
    print('Rule-2','planet1_house',planet1_house,'dispositor_of_planet1_house',dispositor_of_planet1_house,'planet1_co_planet_count',planet1_co_planet_count)
    dispositor_of_planet2_house = const.house_owners[planet2_house]
    print('dispositor_of_planet2_house',planet_list[dispositor_of_planet2_house])
    planet2_co_planet_count = sum( ((value==planet2_house) and (value==p_to_h[3]) and (value==p_to_h[4]) \
                                   and (value==dispositor_of_planet2_house)) for value in p_to_h.values())
    """
    if planet1_co_planet_count > planet2_co_planet_count:
        #print('Rule-2','Planet1/Saturn/Mars is stronger')
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        #print('Rule-2','Planet2/Rahu/Ketu is stronger')
        return planet2
    #print("Rule-2 Both planets have same Cojoin/Aspects count",planet1_co_planet_count,planet2_co_planet_count)
    """ Rule-3: If one planet is exalted and the other not, then the exalted planet is stronger. """
    #print('house_strengths_of_planet1',const.house_strengths_of_planets[planet1][planet1_house], 'house_strengths_of_planet2',const.house_strengths_of_planets[planet2][planet2_house])
    if const.house_strengths_of_planets[planet1][planet1_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet1][planet1_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        #print('Rule-3','Planet1/Saturn/Mars is exhalted and thus stronger')
        return planet1
    if const.house_strengths_of_planets[planet2][planet2_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet2][planet2_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        #print('Rule-3','Planet2/Rahu/Ketu is exhalted and thus stronger')
        return planet2
    #print("Rule-3:None of the planers are exhalted and thus stronger")
    """ Rule - 4: natural strength of the rasi containing the planet. 
        Dual rasis are stronger than fixed rasis and fixed rasis are stronger than movable rasis.
    """
    if planet1_house in const.dual_signs and planet2_house not in const.dual_signs:
            #print('Rule-4','Planet1/Saturn/Mars is stronger')
            return planet1
    elif planet1_house in const.fixed_signs:
        if planet2_house in const.dual_signs:
            #print('Rule-4','Planet2/Rahu/Ketu is stronger')
            return planet2
        elif planet2_house in const.movable_signs: 
            #print('Rule-4','Planet1/Saturn/Mars is stronger')
            return planet1
    else: # Saturn/Mars in movable
        if planet2_house not in const.movable_signs:
            #print('Rule-4','Planet2/Rahu/Ketu is stronger')
            return planet2
    #print("Rule-4: Both planets are in same type of rasi Dual/fixed/movable - and are equally stronger")
    if check_during_dhasa:
        """ Rule-5-a, planet giving a larger length for narayana dhasa"""
        from jhora.horoscope.dhasa.raasi import narayana 
        planet1_narayana_dhasa_duration = narayana._dhasa_duration(p_to_h,planet1_house)
        #print('planet1_narayana_dhasa_duration',planet1_narayana_dhasa_duration)
        planet2_narayana_dhasa_duration = narayana._dhasa_duration(p_to_h,planet2_house)
        #print('planet2_narayana_dhasa_duration',planet2_narayana_dhasa_duration)
        if planet1_narayana_dhasa_duration > planet2_narayana_dhasa_duration:
            #print('Rule-5(a): Planet1/Saturn/Mars is stronger')
            return planet1
        elif planet2_narayana_dhasa_duration > planet1_narayana_dhasa_duration:
            #print('Rule-5(a): Planet2/Rahu/Ketu is stronger')
            return planet2
    #else: # Check during Arudhas
    """ Rule 5(b) the planet that is more advanced in its rasi. """
    if planet1_longitude is not None and planet2_longitude is not None:
        if planet1_longitude > planet2_longitude:
            #print('Rule 5(b)',planet_list[planet1],' is stronger than',planet_list[planet2])
            return planet1
        else:
            #print('Rule 5(b)',planet_list[planet2],' is stronger than',planet_list[planet2])
            return planet2
def stronger_rasi_from_planet_positions(planet_positions,rasi1,rasi2):
    house_to_planet_dict = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    _stronger_rasi = stronger_rasi(house_to_planet_dict,rasi1,rasi2)
    if _stronger_rasi is not None:
        return _stronger_rasi
    """ Rule-6: The rasi owned by the planet with the higher advancement of longitude is stronger. """
    #print("Upto Rule 5 - not met. Stronger Rasi to be found from stronger_co_lords",rasi1,rasi2)
    lord_of_rasi1 = house_owner_from_planet_positions(planet_positions, rasi1) # const.house_owners[rasi1]
    lord_of_rasi2 = house_owner_from_planet_positions(planet_positions, rasi2) #const.house_owners[rasi2]
    #sp = stronger_planet_from_planet_positions(planet_positions, lord_of_rasi1, lord_of_rasi1)
    #if sp is None:
    #    print('could not find stronger co lord',lord_of_rasi1,lord_of_rasi2)
    #    exit()
    if planet_positions[lord_of_rasi1+1][1][1] > planet_positions[lord_of_rasi2+1][1][1]:#sp == lord_of_rasi1:
        #print("Rule-6:",rasi1,'is stronger by higher advancement of longitude',planet_positions[lord_of_rasi1+1][1][1],'>',planet_positions[lord_of_rasi2+1][1][1])
        return rasi1
    else:
        #print("Rule-6:",rasi2,'is stronger by higher advancement of longitude',planet_positions[lord_of_rasi2+1][1][1],'>',planet_positions[lord_of_rasi1+1][1][1])
        return rasi2
     
def stronger_rasi(house_to_planet_dict,rasi1,rasi2):
    """
        To find stronger rasi between rasi1 and rasi2 
        @param house_to_planet_dict: list of raasi with planet ids in them
          Example: ['','','','','2','7','1/5','0','3/4','L','','6/8'] 1st element is Aries and last is Pisces
        @param rasi1: [ 0,,11] 0 = Ar and 11 = Pi 
        @param rasi2: [ 0,,11] 0 = Ar and 11 = Pi
        @return  return stronger raasi (raasi index 0 to 11, 0 = Ar, 11=Pi) 
    """
    _DEBUG_ = False
    p_to_h = utils.get_planet_to_house_dict_from_chart(house_to_planet_dict)
    if _DEBUG_: print(p_to_h)
    """ Rule-1 rasi contains more planets than the other rasi, then it is stronger. """
    rasi1_planet_count = sum(value==rasi1 for key,value in p_to_h.items() if key != const._ascendant_symbol)
    if _DEBUG_: print('Rule-1',rasi1,'rasi1_planet_count',rasi1_planet_count)
    rasi2_planet_count = sum(value==rasi2 for key,value in p_to_h.items() if key != const._ascendant_symbol)
    if _DEBUG_: print('Rule-1',rasi2,'rasi2_planet_count',rasi2_planet_count)
    if rasi1_planet_count > rasi2_planet_count:
        if _DEBUG_: print('Rule-1 Rasi1',rasi1,'is stronger')
        return rasi1
    if rasi2_planet_count > rasi1_planet_count:
        if _DEBUG_: print('Rule-1 Rasi2',rasi2,'is stronger')
        return rasi2
    if _DEBUG_: print('Rule-1: Both rasis have same count of planets')
    """ Rule-2: how many of the following planets in/aspecting the rasi: (1) Jupiter,(2) Mercury, and, (3) dispositor. """
    # Dispositor of a planet = lord of the house where the planet is
    lord_of_rasi1 = const.house_owners[rasi1]
    rasi1_co_planet_count = 0
    rasi1_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],lord_of_rasi1].count(rasi1)
    if _DEBUG_: print('rasi1',rasi_names_en[rasi1],' cojoin count',rasi1_co_planet_count)
    rasi1_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, rasi1)
    if _DEBUG_: print('Aspects of',rasi_names_en[rasi1],[planet_list[p] for p in rasi1_aspects])
    rasi1_co_planet_count += sum(rasi1_aspects.count(p1) for p1 in [const.MERCURY_ID,const.JUPITER_ID,lord_of_rasi1])
    
    lord_of_rasi2 = const.house_owners[rasi2]
    rasi2_co_planet_count = 0
    rasi2_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],lord_of_rasi2].count(rasi2)
    if _DEBUG_: print('rasi2',rasi_names_en[rasi2],' cojoin count',rasi2_co_planet_count)
    rasi2_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, rasi2)
    if _DEBUG_: print('Aspects of',rasi_names_en[rasi2],[planet_list[p] for p in rasi2_aspects])
    rasi2_co_planet_count += sum(rasi2_aspects.count(p1) for p1 in [const.MERCURY_ID,const.JUPITER_ID,lord_of_rasi2])
    if rasi1_co_planet_count > rasi2_co_planet_count:
        if _DEBUG_: print('Rule-2 Rasi1',rasi1,'is stronger')
        return rasi1
    elif rasi2_co_planet_count > rasi1_co_planet_count:
        if _DEBUG_: print('Rule-2 Rasi2',rasi2,'is stronger')
        return rasi2
    if _DEBUG_: print('Rule-2: Both rasis have same aspect/cojoin count',rasi1)
    """ Rule-3: If one rasi contains an exalted planet and the other does not, then the former rasi is stronger."""
    rasi1_exhalted_planet_count = sum([const.house_strengths_of_planets[int(p)][rasi1] == const._EXALTED_UCCHAM for p in p_to_h if p!= const._ascendant_symbol and p_to_h[p]==rasi1])
    if _DEBUG_: print('Rule-3','rasi1_exhalted_planet_count',rasi1_exhalted_planet_count)
    rasi2_exhalted_planet_count = sum([const.house_strengths_of_planets[int(p)][rasi2] == const._EXALTED_UCCHAM for p in p_to_h if p!= const._ascendant_symbol and p_to_h[p]==rasi2])
    if _DEBUG_: print('Rule-3','rasi2_exhalted_planet_count',rasi2_exhalted_planet_count)
    if rasi1_exhalted_planet_count > 0 and rasi2_exhalted_planet_count ==0:
        if _DEBUG_: print('rasi1',rasi1,'contains exhalted planet and rasi2',rasi2,'does not')
        return rasi1
    if rasi2_exhalted_planet_count > 0 and rasi1_exhalted_planet_count ==0:
        if _DEBUG_: print('rasi2',rasi2,'contains exhalted planet and rasi1',rasi1,'does not')
        return rasi2
    """ Rule - 4: A rasi whose lord is in a rasi with a different oddity (odd/even) is stronger than a
                    rasi whose lord is in a rasi with the same oddity. """
    if _DEBUG_: print(rasi1,lord_of_rasi1,p_to_h[lord_of_rasi1])
    rasi1_has_oddity = (rasi1 in const.odd_signs and p_to_h[lord_of_rasi1] in const.even_signs) or (rasi1 in const.even_signs and p_to_h[lord_of_rasi1] in const.odd_signs)
    if _DEBUG_: print(rasi2,lord_of_rasi2,p_to_h[lord_of_rasi2])
    rasi2_has_oddity = (rasi2 in const.odd_signs and p_to_h[lord_of_rasi2] in const.even_signs) or (rasi2 in const.even_signs and p_to_h[lord_of_rasi2] in const.odd_signs)
    if _DEBUG_: print('Rule-4','rasi1_has_oddity',rasi1_has_oddity,'rasi2_has_oddity',rasi2_has_oddity)
    if rasi1_has_oddity and not rasi2_has_oddity:
        if _DEBUG_: print('Rule-4:rasi1',rasi1,'has oddity and thus stronger')
        return rasi1
    if rasi2_has_oddity and not rasi1_has_oddity:
        if _DEBUG_: print('Rule-4:rasi2',rasi2,'has oddity and thus stronger')
        return rasi2
    if _DEBUG_: print('Rule-4: Both Rasis have same oddity')
    """ Rule - 5: natural strength of the rasi. 
        Dual rasis are stronger than fixed rasis and fixed rasis are stronger than movable rasis.
    """
    def _mod_rank(sign_idx):
        if sign_idx in const.dual_signs:
            return 3  # Dual
        elif sign_idx in const.fixed_signs:
            return 2  # Fixed
        else:
            return 1  # Movable
    
    m1 = _mod_rank(rasi1)
    m2 = _mod_rank(rasi2)
    
    if m1 > m2:
        if _DEBUG_: print("Rule-5: rasi1 stronger (Dual>Fixed>Movable)")
        return rasi1
    elif m2 > m1:
        if _DEBUG_: print("Rule-5: rasi2 stronger (Dual>Fixed>Movable)")
        return rasi2
    else:
        # SAME modality → Rule-4 cannot decide; let Rule-5 handle it.
        if _DEBUG_: print("Rule-5: tie on modality — defer to Rule-5")
    return None

    return None
    #import sys
    #sys.exit('No Stronger Rasi found. Use stronger_rasi_from_planet_positions instead.')
def natural_friends_of_planets(h_to_p=None):
    """
        Take the moolatrikona of the planet. Lord of the rasi where it is exalted is its friend. 
        Lords of 2nd, 4th, 5th, 8th, 9th and 12th rasis from it are also its natural friends.
    """
    if h_to_p==None:
        return const.friendly_planets
    nf = {p:[] for p in const.SUN_TO_KETU}
    for p in const.SUN_TO_KETU:
        mtr = const.moola_trikona_of_planets[p]
        if p < const.RAHU_ID:
            er = [house_owner(h_to_p,r) for r in range(12) if const.house_strengths_of_planets[p][r]==const._EXALTED_UCCHAM]
            #ler = house_owner(h_to_p, er)
            nf[p].append(er)
        fr = [house_owner(h_to_p,r) for r in range(12) if const.house_strengths_of_planets[p][r]==const._FRIEND]
        nf[p].append(fr)
        nf[p] = utils.flatten_list(nf[p])
        #print(p,mtr,er,nf[p])
        nf[p] = list(set(nf[p]))
    return nf # const.friendly_planets
def natural_neutral_of_planets(h_to_p=None):
    return const.neutral_planets
def natural_enemies_of_planets(h_to_p=None):
    return const.enemy_planets
def _get_temporary_friends_of_planets(h_to_p):
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    p_temp_friends = {}
    for p in const.SUN_TO_KETU:
        p_raasi = p_to_h[p]
        _temp_friends = utils.flatten_list([h_to_p[(p_raasi+h)%12].split('/') for h in const.temporary_friend_raasi_positions if h_to_p[(p_raasi+h)%12] !=''])
        [_temp_friends.remove(rp) for rp in [str(p),'L'] if rp in _temp_friends]
        _temp_friends = list(set(map(int,_temp_friends)))
        p_temp_friends[p] = _temp_friends
    return p_temp_friends
def _get_temporary_enemies_of_planets(h_to_p):
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    p_temp_enemies = {}
    for p in const.SUN_TO_KETU:
        p_raasi = p_to_h[p]
        _temp_enemies = utils.flatten_list([h_to_p[(p_raasi+h)%12].split('/') for h in const.temporary_enemy_raasi_positions if h_to_p[(p_raasi+h)%12] !=''])
        [_temp_enemies.remove(rp) for rp in [str(p),'L'] if rp in _temp_enemies]
        _temp_enemies = list(set(map(int,_temp_enemies)))
        p_temp_enemies[p] = _temp_enemies
    return p_temp_enemies
def _get_compound_relationships_of_planets(h_to_p):
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    tf = _get_temporary_friends_of_planets(h_to_p)
    #print('_get_temporary_friends_of_planets',tf)
    te = _get_temporary_enemies_of_planets(h_to_p)
    #print('_get_temporary_enemies_of_planets',te)
    nf = const.friendly_planets
    #print('friendly_planets',nf)
    nn = const.neutral_planets
    #print('neutral_planets',nn)
    ne = const.enemy_planets
    #print('enemy_planets',ne)
    p_compound = [[0 for _ in const.SUN_TO_KETU] for _ in const.SUN_TO_KETU]
    for p in const.SUN_TO_KETU:
        tfp = tf[p]; tep = te[p]; nfp = nf[p]; nnp = nn[p]; nep = ne[p]
        #print('tfp',tfp,'tep',tep,'nfp',nfp,'nnp',nnp,'nep',nep)
        #am=[];m=[];n=[];e=[];ae=[]
        for p1 in const.SUN_TO_KETU:
            if p==p1:
                continue
            if p1 in nfp and p1 in tfp: # Adhimitras
                p_compound[p][p1] = 4
                #am.append(p1)
            elif (p1 in nfp and p1 in tep) or (p1 in nep and p1 in tfp): # Neutral
                p_compound[p][p1] = 2
                #n.append(p1)
            elif (p1 in nnp and p1 in tfp):
                p_compound[p][p1] = 3
                #m.append(p1)
            elif (p1 in nnp and p1 in tep):
                p_compound[p][p1] = 1
                #e.append(p1)
            elif (p1 in nep and p1 in tep):
                p_compound[p][p1] = 0
                #ae.append(p1)
        #p_compound[p] = [am,m,n,e,ae]
    return p_compound
def _get_varga_viswa_of_planets(h_to_p):
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    cs = _get_compound_relationships_of_planets(h_to_p)
    scores = const.varga_viswa_scores
    #print('compound releations',cs)
    vv = [0 for _ in const.SUN_TO_KETU]
    for p in const.SUN_TO_KETU:
        if const.house_strengths_of_planets[p][ p_to_h[p]]==const._OWNER_RULER:
            #print('planet',p,'is a ruler/owner of',p_to_h[p],'score=20')
            vv[p] = 20
        else:
            d = const.house_owners[p_to_h[p]]
            vv[p] = scores[cs[p][d]]
    return vv    
def house_owner_from_planet_positions(planet_positions,sign,check_during_dhasa=False):
    """ If house owner for Sc/Aq is forced - use that """ 
    if sign==const.SCORPIO and const.scorpio_owner_for_dhasa_calculations in [const.MARS_ID,const.KETU_ID]:
        return const.scorpio_owner_for_dhasa_calculations
    elif sign==const.AQUARIUS and const.aquarius_owner_for_dhasa_calculations in [const.SATURN_ID,const.RAHU_ID]: 
        return const.aquarius_owner_for_dhasa_calculations
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    lord_of_sign = house_owner(h_to_p, sign)
    if sign == const.SCORPIO:
        lord_of_sign = stronger_planet_from_planet_positions(planet_positions, const.MARS_ID, const.KETU_ID, check_during_dhasa=check_during_dhasa)
    elif sign == const.AQUARIUS:
        lord_of_sign = stronger_planet_from_planet_positions(planet_positions, const.SATURN_ID, const.RAHU_ID, check_during_dhasa=check_during_dhasa)
    return lord_of_sign
def house_owner(h_to_p,sign):
    lord_of_sign = const.house_owners[sign]
    l_o_s = lord_of_sign
    #print('sign',sign,'lord_of_sign',lord_of_sign)
    if sign==const.SCORPIO:
        lord_of_sign = stronger_planet(h_to_p,const.MARS_ID,const.KETU_ID) \
            if const.scorpio_owner_for_dhasa_calculations is None else const.scorpio_owner_for_dhasa_calculations
        #print('Stronger in Scorpio',lord_of_sign)
    elif sign==const.AQUARIUS:
        lord_of_sign = stronger_planet(h_to_p,const.SATURN_ID,const.RAHU_ID) \
            if const.aquarius_owner_for_dhasa_calculations is None else const.aquarius_owner_for_dhasa_calculations
    if lord_of_sign==None:
        #print('Rule (5) Requires longitudes of planets which are not provided, hence house.house_owner returning None')
        #print('h_to_p',h_to_p,'sign',sign,'lord_of_sign',lord_of_sign)
        #print('Warning: Returning lord of sign as owner of house',l_o_s,' without checking Sc/Aq stronger lord')
        return l_o_s #None # 
        #exit()
    return lord_of_sign
def marakas_from_planet_positions(planet_positions):
    """
        If a malefic planet powerfully conjoins or aspects, using graha drishti, 
        the 2nd and 7th houses or their lords, then it qualifies as a maraka graha.
        @param planet_positions list in the format [[planet,(raasi,planet_longitude)],...]] 
            First element is that of Lagnam. Example: [ ['L',(0,123.4)],[0,(11,32.7)],...]]
            Lagnam in Aries 123.4 degrees, Sun in Taurus 32.7 degrees
        @return: maraka graha/planets as a list
    """
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    print(p_to_h)
    maraka_sthanas = [(h+p_to_h[const._ascendant_symbol])%12 for h in [const.HOUSE_2,const.HOUSE_7]]
    maraka_planets = [house_owner_from_planet_positions(planet_positions, sign) for sign in maraka_sthanas] ## 2 and 7th houses are maraka sthanas
    print(maraka_sthanas,'maraka_sthana_owners',maraka_planets)
    mpls = [mp for mp in const.SUN_TO_KETU if p_to_h[mp] in maraka_sthanas or p_to_h[mp] in [p_to_h[p] for p in maraka_planets]]
    print('mpls',mpls)
    if mpls:
        maraka_planets += mpls
    maraka_planets = list(set(maraka_planets))
    return maraka_planets    
def marakas(h_to_p):
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    """
        If a malefic planet powerfully conjoins or aspects, using graha drishti, 
        the 2nd and 7th houses or their lords, then it qualifies as a maraka graha.
    """
    #print(p_to_h)
    maraka_sthanas = [(h+p_to_h[const._ascendant_symbol])%12 for h in [const.HOUSE_2,const.HOUSE_7]]
    maraka_planets = [house_owner(h_to_p, sign) for sign in maraka_sthanas] ## 2 and 7th houses are maraka sthanas
    #print(maraka_sthanas,'maraka_sthana_owners',maraka_planets)
    mpls = [mp for mp in const.SUN_TO_KETU if p_to_h[mp] in maraka_sthanas or p_to_h[mp] in [p_to_h[p] for p in maraka_planets]]
    #print('mpls',mpls)
    if mpls:
        maraka_planets += mpls
    maraka_planets = list(set(maraka_planets))
    return maraka_planets
def rudra_from_jd_place(jd,place,divisional_chart_factor=1):
    """ 
        Stronger of lord of the 8th house from (i) lagna and (ii) the 7th house - is Rudra
        8th house calculated not the usual way but using const.rudra_eighth_house
        Ref: Table-32 of PVR's Book.
    """
    planet_positions = drik.dhasavarga(jd, place, divisional_chart_factor=divisional_chart_factor)
    ascendant_constellation, ascendant_longitude, _, _ = drik.ascendant(jd,place)
    planet_positions = [[const._ascendant_symbol,(ascendant_constellation, ascendant_longitude)]] + planet_positions
    return rudra(planet_positions)
def brahma(planet_positions):
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    asc_house = planet_positions[0][1][0]
    seventh_house = (asc_house+const.HOUSE_7) %12
    sp = stronger_rasi_from_planet_positions(planet_positions, asc_house, seventh_house)
    #print('asc_house',asc_house,'seventh_house',seventh_house,'stronger rasi',sp)
    lords = [house_owner_from_planet_positions(planet_positions, (sp+h)%12) for h in [const.HOUSE_6,const.HOUSE_8,const.HOUSE_12]]
    #print('lords',lords)
    lords = [l for l in lords if l not in [const.RAHU_ID,const.KETU_ID]] # Remove Rahu and Kethu
    #print('lords',lords)
    lords_scores = {l:0 for l in lords}
    for l in lords:
        h = p_to_h[l]
        if const.house_strengths_of_planets[l][h] >= const._FRIEND:
            lords_scores[l] += 1
        if h in const.odd_signs:
            lords_scores[l] += 1
        if h in [(sp+j)%12 for j in const.SUN_TO_SATURN]:
            lords_scores[l] += 1
    #print(lords_scores)
    lords_scores = dict(sorted(lords_scores.items(), key = lambda x: x[1], reverse = True)[:2])
    #print(lords_scores)
    if len(lords_scores)==1:
        brahma = list(lords_scores.keys())[0]
    elif len(lords_scores)==2:
        brahma = stronger_planet_from_planet_positions(planet_positions, list(lords_scores.keys())[0], list(lords_scores.keys())[1])
    else:
        b1 = stronger_planet_from_planet_positions(planet_positions, list(lords_scores.keys())[0], list(lords_scores.keys())[1])
        brahma = stronger_planet_from_planet_positions(planet_positions, b1, list(lords_scores.keys())[2])
    return brahma
def rudra(planet_positions):
    """ 
        Stronger of lord of the 8th house from (i) lagna and (ii) the 7th house - is Rudra
        8th house calculated not the usual way but using const.rudra_eighth_house
        Ref: Table-32 of PVR's Book.
    """
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    lagna_house = p_to_h['L']
    eighth_house_lord = house_owner_from_planet_positions(planet_positions, const.rudra_eighth_house[lagna_house])
    seventh_house = (lagna_house+const.HOUSE_7)%12
    seventh_house_lord = house_owner_from_planet_positions(planet_positions, const.rudra_eighth_house[seventh_house])
    _rudra = stronger_planet_from_planet_positions(planet_positions, eighth_house_lord, seventh_house_lord, check_during_dhasa=False)
    _rudra_sign = p_to_h[_rudra]
    trishoola_rasis = trines_of_the_raasi(_rudra_sign)
    return _rudra, _rudra_sign,trishoola_rasis
def trishoola_rasis(planet_positions):
    return trines_of_the_raasi(rudra(planet_positions)[1])
def maheshwara_from_planet_positions(planet_positions):
    pp = planet_positions
    _chara_karakas = chara_karakas(pp) #jd, place, divisional_chart_factor)
    atma_karaka = _chara_karakas[0]
    #print('_maheshwara',atma_karaka)
    #print(pp)
    h_to_p = utils.get_house_planet_list_from_planet_positions(pp)
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(pp)
    #print(h_to_p)
    atma_karaka_house = pp[atma_karaka+1][1][0]
    _maheshwara = house_owner_from_planet_positions(planet_positions, (atma_karaka_house+const.HOUSE_8)%12) # V4.6.0
    #print('atma_karaka_house',atma_karaka_house,'atma_8th_lord',_maheshwara)
    #print(p_to_h[_maheshwara],'==?',const.house_owners[_maheshwara])
    if p_to_h[_maheshwara] == const.house_owners[_maheshwara]:
        atma_karaka_house = p_to_h[_maheshwara]
        atma_8th_lord = house_owner_from_planet_positions(planet_positions,(atma_karaka_house+const.HOUSE_8)%12) # V4.6.0
        atma_12th_lord = house_owner_from_planet_positions(planet_positions,(atma_karaka_house+const.HOUSE_12)%12) # V4.6.0
        _maheshwara = stronger_planet_from_planet_positions(planet_positions, atma_8th_lord, atma_12th_lord) # V4.6.0
    #print(p_to_h[_maheshwara],'==',p_to_h[7],'or',p_to_h[_maheshwara],'==',p_to_h[8])
    #print(p_to_h[7],'==',(p_to_h[_maheshwara]+7)%12,'or', p_to_h[8],'==',(p_to_h[_maheshwara]+7)%12)
    if p_to_h[_maheshwara]==p_to_h[const.RAHU_ID] or p_to_h[_maheshwara]==p_to_h[const.KETU_ID]:
        _maheshwara = house_owner_from_planet_positions(planet_positions, (atma_karaka_house+const.HOUSE_6)%12) # V4.6.0
    elif p_to_h[const.RAHU_ID]==(p_to_h[_maheshwara]+const.HOUSE_8)%12 or p_to_h[const.KETU_ID]==(p_to_h[_maheshwara]+const.HOUSE_8)%12:
        _maheshwara = house_owner_from_planet_positions(planet_positions, (atma_karaka_house+const.HOUSE_6)%12) # V4.6.0
    if _maheshwara == const.RAHU_ID:
        _maheshwara = const.MERCURY_ID
    elif _maheshwara == const.KETU_ID:
        _maheshwara = const.JUPITER_ID
    return _maheshwara
def maheshwara(dob,tob,place,divisional_chart_factor=1):
    """
        Get Maheshwara Planet
    """
    jd = utils.julian_day_number(dob, tob)
    from jhora.horoscope.chart import charts
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)
    return maheshwara_from_planet_positions(pp)
def longevity(dob,tob,place,divisional_chart_factor=1):
    jd = utils.julian_day_number(dob, tob)
    planet_positions = drik.dhasavarga(jd, place, divisional_chart_factor=divisional_chart_factor)
    ascendant_constellation, ascendant_longitude, _, _ = drik.ascendant(jd,place)
    planet_positions = [[const._ascendant_symbol,(ascendant_constellation, ascendant_longitude)]] + planet_positions
    rasi_type = lambda rasi:[index for index,r_type in enumerate([const.fixed_signs,const.movable_signs,const.dual_signs]) if rasi in r_type][0]
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    #print('p_to_h',p_to_h)
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    #print('h_to_p',h_to_p)
    lagna_house = p_to_h['L']
    # first pair houses of Lagna Lord and 8th lord 
    lagna_lord_house = p_to_h[house_owner(h_to_p, lagna_house)]
    #print('lagna_house',lagna_house,'lagna lord',house_owner(h_to_p, lagna_house),'lagna_lord_house',lagna_lord_house)
    eighth_lord_house = p_to_h[house_owner(h_to_p, const.rudra_eighth_house[lagna_house])]
    #print('eighth_lord',house_owner(h_to_p, const.rudra_eighth_house[lagna_house]),'eighth_lord_house',eighth_lord_house)
    #print('lagna_lord_house rasi_type',rasi_type(lagna_lord_house),'eighth_lord rasi type',rasi_type(eighth_lord_house))
    pair1_longevity = longevity_of_pair(rasi_type(lagna_lord_house),rasi_type(eighth_lord_house))
    #print('pair1_longevity',pair1_longevity)
    
    # Second pair - houses of moon and Saturn
    pair2_longevity = longevity_of_pair(rasi_type(p_to_h[const.MOON_ID]),rasi_type(p_to_h[const.SATURN_ID]))
    #print('pair2_longevity',pair2_longevity)
    
    # Third pair Houses of Lagna and Hora Lagna
    time_of_birth_in_hours = utils.from_dms(tob[0],tob[1],tob[2])
    hora_lagna_house = drik.hora_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)[0]  # V3.1.9
    #print('hora_lagna_house',hora_lagna_house)
    pair3_longevity = longevity_of_pair(rasi_type(lagna_house),rasi_type(hora_lagna_house))
    #print('pair3_longevity',pair3_longevity)
    def _longevity_pair_check(pair1_longevity,pair2_longevity,pair3_longevity):
        if pair1_longevity==pair2_longevity and pair2_longevity == pair3_longevity:
            #print('all pairs equal')
            return const.longevity_years[pair1_longevity][pair2_longevity]
        elif pair1_longevity==pair2_longevity and pair2_longevity != pair3_longevity:
            #print('Pair 1 and 2 equal')
            return const.longevity_years[pair1_longevity][pair3_longevity]
        elif pair2_longevity==pair3_longevity and pair2_longevity != pair1_longevity:
            #print('Pair 2 and 3 equal')
            return const.longevity_years[pair2_longevity][pair1_longevity]
        elif pair1_longevity==pair3_longevity and pair1_longevity != pair2_longevity:
            #print('Pair 1 and 3 equal')
            return const.longevity_years[pair1_longevity][pair2_longevity]
        elif pair1_longevity!=pair2_longevity and pair1_longevity != pair3_longevity and pair2_longevity != pair3_longevity:
            #print('All are not equal')
            if p_to_h[const.MOON_ID]==p_to_h[const._ascendant_symbol] or p_to_h[const.MOON_ID] == p_to_h[(lagna_house+const.HOUSE_7)%12]:
                #print('Order Pair 3 and 2')
                return const.longevity_years[pair2_longevity][pair2_longevity]
            else:
                #print('Order Pair 3 and 1')
                return const.longevity_years[pair2_longevity][pair1_longevity]
    return _longevity_pair_check(pair1_longevity,pair2_longevity,pair3_longevity)


def _associations_of_the_planet(planet_positions, planet, restrict_to_kendra_trikona=True,
                                exclude_rahu_ketu=True):
    """
    Associations of a planet:
      (1) Conjunction, (2) Mutual graha drishti (exclude Rahu/Ketu), (3) Parivartana.
    If restrict_to_kendra_trikona=True, only consider planets that are lords of kendra/trikona.
    Returns a sorted list of associated planets (IDs).
    TODO: This should match get_raja_yoga_pairs of raja yoga module
    """
    excluded_planets = [const.RAHU_ID, const.KETU_ID] if exclude_rahu_ketu else []
    if planet == 'L':
        return []

    planet = int(planet)

    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)

    # Build domain
    if restrict_to_kendra_trikona:
        asc_house = p_to_h[const._ascendant_symbol]
        lq = set(lords_of_quadrants_from_planet_positions(planet_positions, asc_house))
        lt = set(lords_of_trines_from_planet_positions(planet_positions, asc_house))
        domain = sorted(map(int, (lq | lt)))
        # If the requested planet isn't a kendra/trikona lord, return empty
        if planet not in domain:
            return []
    else:
        # Generic planet domain: Sun..Saturn (exclude Rahu/Ketu) if you want RY-like behavior
        domain = list(const.SUN_TO_SATURN)
    print('domain',domain)
    associated = set()

    # (1) Conjunction
    house_of_planet = p_to_h[planet]
    for p in domain:
        if p != planet and p_to_h[p] == house_of_planet:
            associated.add(p)

    # (2) Mutual graha drishti (exclude Rahu/Ketu)
    RAHU, KETU = const.RAHU_ID, const.KETU_ID
    if planet not in (RAHU, KETU):
        drishti_of_planet = set(map(int, graha_drishti_of_the_planet(h_to_p, planet)))
        for p in domain:
            if p == planet or p in (RAHU, KETU):
                continue
            drishti_of_p = set(map(int, graha_drishti_of_the_planet(h_to_p, p)))
            if (p in drishti_of_planet) and (planet in drishti_of_p):
                associated.add(p)

    # (3) Parivartana (exchange)
    owner_house_planet = house_owner_from_planet_positions(planet_positions, p_to_h[planet])
    for p in domain:
        if p == planet:
            continue
        owner_house_p = house_owner_from_planet_positions(planet_positions, p_to_h[p])
        if owner_house_p == planet and owner_house_planet == p:
            associated.add(p)

    return sorted(associated)

def associations_of_the_planet(house_to_planet_list=None,planet_positions=None,planet=None):
    """ There are 3 important associations:
        (1) The two planets are conjoined,
        (2) The two planets aspect each other with graha drishti, or,
        (3) The two planets have a parivartana (exchange). For example, if the 4th lord is in
            the 5th house and the 5th lord is in the 4th house, then we say that there is a
            parivartana between the 4th and 5th lords. This is an association.
    """
    if planet_positions is not None:
        house_to_planet_list = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if house_to_planet_list is None: return []
    planet_to_house_dict = utils.get_planet_to_house_dict_from_chart(house_to_planet_list)
    ap = []
    """ (1) The two planets are conjoined,"""
    pl = [int(p) for p in const.SUN_TO_KETU if planet_to_house_dict[p]==planet_to_house_dict[planet] and p!=planet]
    #print('conjoin of planet',planet,pl)
    ap += pl
    """ (2) The two planets aspect each other with graha drishti """
    pl = list(map(int,graha_drishti_of_the_planet(house_to_planet_list, planet)))
    """ Remove uranus neptune and pluto """
    pl = [p for p in pl if p not in const.western_planets]
    pl1 = []
    """ Check other planet has drishti on the planet  V4.6.0 """
    for gp in pl:
        gp1 = list(map(int,graha_drishti_of_the_planet(house_to_planet_list, gp)))
        if planet in gp1:
            pl1.append(gp)
    if planet in pl1:
        pl1.remove(planet)
    #print('graha drishti aspects of planet',planet,pl,pl1)
    ap += pl1
    """ (3) The two planets have a parivartana (exchange) """
    if planet_positions is not None:
        pl = [int(p) for p in const.SUN_TO_KETU if int(planet)!=int(p) and \
              house_owner_from_planet_positions(planet_positions, planet_to_house_dict[p])==planet and \
              house_owner_from_planet_positions(planet_positions, planet_to_house_dict[planet])==p]
    else:
        pl = [int(p) for p in const.SUN_TO_KETU if int(planet)!=int(p) and \
              house_owner(planet_to_house_dict, planet_to_house_dict[p])==planet and \
              house_owner(planet_to_house_dict, planet_to_house_dict[planet])==p]
    #print('parivarthana of planet',planet,pl)
    ap += pl
    """ remove duplicates """
    ap = list(set(ap))
    #print("Associations of planet",planet,ap)
    return ap
def _are_planets_associated(planet_positions,planet1,planet2):
    planet1_association = _associations_of_the_planet(planet_positions=planet_positions, planet=planet1)
    return planet2 in planet1_association
def _get_associated_planet_pairs(planet_positions):
    """Return unique unordered associated planet pairs for integer items 0..8."""
    unique_pairs = set()

    for planet1 in const.SUN_TO_KETU:
        associations = _associations_of_the_planet(planet_positions=planet_positions, planet=planet1)
        # Debug (optional)
        # print('planet1 associations', planet1, associations)

        for planet2 in associations:
            if planet2 is None:
                continue
            # Exclude self-pairs; remove this check if you want (x, x) included
            if planet1 == planet2:
                continue

            # Normalize order so (a, b) == (b, a)
            pair = (min(planet1, planet2), max(planet1, planet2))
            unique_pairs.add(pair)

    # Return as a sorted list of tuples for stable output
    return sorted(unique_pairs)

def baadhakas_of_raasi(raasi):
    """ return [Baadhaka Sthaana/rasi, [baadhaka planets]]  of the given raasi"""
    return const.baadhakas[raasi]
def order_of_planets_by_strength(planet_positions):
    from functools import cmp_to_key
    planets = const.SUN_TO_KETU
    def compare(planet1,planet2):
        sp = stronger_planet_from_planet_positions(planet_positions, planet1,planet2)
        #Left stronger = -1 ; right stronger = +1
        if sp==planet1: return -1 # Planet1 stronger
        elif sp==planet2: return 1 #Planet2 stronger
        else: return 0 # Both equal
    return sorted(planets, key=cmp_to_key(compare))
def order_of_raasis_by_strength(planet_positions):
    pp = planet_positions[:const._pp_count_upto_ketu]
    from functools import cmp_to_key
    rasis = [*range(12)]
    def compare(rasi1,rasi2):
        sp = stronger_rasi_from_planet_positions(pp, rasi1,rasi2)
        if sp==rasi1: return -1 # rasi1 stronger
        elif sp==rasi2: return 1 # rasi2 stronger
        else: return 0 # both equal
    return sorted(rasis, key=cmp_to_key(compare))
def stronger_planet_from_list_of_planets(planet_positions,planet_list_arg):
    def _compare(planet1,planet2):
        return -1 if stronger_planet_from_planet_positions(planet_positions, planet1, planet2)==planet1 else 1 
    from functools import cmp_to_key
    return sorted(planet_list_arg, key=cmp_to_key(_compare))[0]

def stronger_raasi_from_list_of_raasis(planet_positions, raasi_list):
    # Build a rank map: lower index = stronger
    full_order = order_of_raasis_by_strength(planet_positions)
    rank = {r: i for i, r in enumerate(full_order)}
    # Return strongest in the subset
    return min(raasi_list, key=lambda r: rank[r])
if __name__ == "__main__":
    utils.set_language('en')
    dob = (2026,5,23); tob = (8,34,0);place_as_tuple = drik.Place('Chennai, India',13.0878,80.2785,5.5)
    dcf = 1
    jd_at_dob = utils.julian_day_number(dob, tob)
    from jhora.horoscope.chart.charts import divisional_chart
    for d in range(365):
        planet_positions = divisional_chart(jd_at_dob, place_as_tuple, divisional_chart_factor=dcf,chart_method=dcf)
        print(utils.jd_to_gregorian(jd_at_dob),rudra(planet_positions))
        jd_at_dob += 1
    exit()
    _quads = [quadrants_of_the_raasi((planet_positions[0][1][0]+h)%12) for h in range(3)]
    _quads1 = _quads[0]+sorted(_quads[1])+sorted(_quads[2])
    print(_quads1)
    print(planet_positions)
    print('rasi chart',utils.get_house_planet_list_from_planet_positions(planet_positions))
    print('1. stronger of Ke/Sa',stronger_planet_from_planet_positions(planet_positions,const.KETU_ID, const.SATURN_ID))
    print(order_of_planets_by_strength(planet_positions))
    #print('2. stronger of Ju/Me',stronger_planet_from_planet_positions(planet_positions,const.JUPITER_ID, const.MERCURY_ID))
    #print('3. stronger of Ra/Ke',stronger_planet_from_planet_positions(planet_positions,const.RAHU_ID, const.KETU_ID))
    #print('4. stronger of Ra/Sa',stronger_planet_from_planet_positions(planet_positions,const.RAHU_ID, const.SATURN_ID))
    #print('5. stronger of Ra/Ju',stronger_planet_from_planet_positions(planet_positions,const.RAHU_ID, const.JUPITER_ID))
    #print('6. stronger of Ra/Me',stronger_planet_from_planet_positions(planet_positions,const.RAHU_ID, const.MERCURY_ID))
    
    