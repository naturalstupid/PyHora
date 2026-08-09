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
    V4.8.5: All Planet Positions are restricted to [:const._pp_count_upto_ketu]
    V4.8.6 - Fixed data validation and house_owner calculations from planet positions and some errors fixed.
    V4.8.7 - removed 'L' from planets in the house
    V4.8.9 - calls to upagraha now use charts module instead of drik module
"""
import json
from jhora import const,utils
from jhora.panchanga import drik
from jhora.horoscope.chart import house, charts
from jhora.horoscope.chart.house import planets_in_the_house as planets_in_raasi
_lang_path = const._LANGUAGE_PATH
movable_signs = const.movable_signs
fixed_signs = const.fixed_signs
dual_signs = const.dual_signs
SUN_TO_SATURN = const.SUN_TO_SATURN
SUN_TO_KETU = const.SUN_TO_KETU

division_chart_factors = const.division_chart_factors
quadrants_of_the_house = lambda raasi: house.quadrants_of_the_raasi(raasi)
trines_of_the_house = lambda raasi: house.trines_of_the_raasi(raasi)
dushthanas_of_the_house = lambda raasi: house.dushthana_aspects_of_the_raasi(raasi)
def _get_natural_benefics(chart_1d,natural_benefics=None):
    if natural_benefics is None:
        _natural_benefics = [const.JUPITER_ID, const.VENUS_ID]
        if _is_mercury_benefic(chart_1d):
            _natural_benefics.append(const.MERCURY_ID)
    else:
        _natural_benefics = list(natural_benefics)
    return _natural_benefics
def _is_mercury_benefic(chart_1d):
    """ mercury is benefic if alone or with jupiter/venus"""
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    imb1 = p_to_h[const.MERCURY_ID] == p_to_h[const.JUPITER_ID]
    imb2 = p_to_h[const.MERCURY_ID] == p_to_h[const.VENUS_ID]
    imb3 = (len(planets_in_raasi(p_to_h[const.MERCURY_ID],p_to_h,exclude_lagna=True))==1) #V4.8.0
    return imb1 or imb2 or imb3
def get_yoga_resources(language='en'):
    """
        get yoga names from yoga_msgs_<lang>.txt
        @param language: Two letter language code. en, hi, ka, ta, te
        @return json strings from the resource file as dictionary 
    """
    json_file = _lang_path + const._DEFAULT_YOGA_JSON_FILE_PREFIX+language+'.json'
    f = open(json_file,"r",encoding="utf-8")
    msgs = json.load(f)
    f.close()
    return msgs
def get_yoga_details_for_all_charts(jd,place,language='en',divisional_chart_factor=None,**kwargs):
    """
        Get all the yoga information that are present in the divisional charts for a given julian day and place
        @param jd: Julian day number
        @param place: struct (plave name, latitude, longitude, timezone)
        @param language: two letter language code (en, hi, ka, ta, te)
        @param divisional_chart_factor: None => Get for all varga charts. Or specify divisional chart number 
        @return: returns a 2D List of yoga_name, yoga_details
            yoga_name in language
            yoga_details: [chart_ID, yoga_name, yoga_desription, yoga_benfits] 
    """
    msgs = get_yoga_resources(language=language)
    yoga_results_combined = {}
    if divisional_chart_factor==None:
        for dv in division_chart_factors:
            yoga_results,_,_ = get_yoga_details(jd,place,divisional_chart_factor=dv,
                                                language=language,**kwargs)
            yoga_results.update(yoga_results_combined)
            yoga_results_combined = yoga_results
    else:
        yoga_results,_,_ = get_yoga_details(jd,place,divisional_chart_factor=divisional_chart_factor,
                                            language=language,**kwargs)
        yoga_results.update(yoga_results_combined)
        yoga_results_combined = yoga_results
        
    #print('Found',len(yoga_results_combined),'out of',len(msgs)*len(division_chart_factors),'yogas')
    return yoga_results_combined,len(yoga_results_combined),len(msgs)*len(division_chart_factors)
def get_yoga_details(jd,place,divisional_chart_factor=1,language='en',**kwargs):
    """
        Get all the yoga information that are present in the requested divisional charts for a given julian day and place
        @param jd: Julian day number
        @param place: struct (plave name, latitude, longitude, timezone)
        @param divisional_chart_factor: integer of divisional chart 1=Rasi, 2=D2, 9=D9 etc 
        @param language: two letter language code (en, hi, ka, ta, te)
        @return: returns a 2D List of yoga_name, yoga_details
            yoga_name in language
            yoga_details: [chart_ID, yoga_name, yoga_desription, yoga_benfits] 
    """
    msgs = get_yoga_resources(language=language)
    """
    global p_to_h, h_to_p, asc_house, planet_positions
    ascendant_index = const._ascendant_symbol
    planet_positions = drik.dhasavarga(jd,place,divisional_chart_factor)
    ascendant_longitude = drik.ascendant(jd,place)[1]
    asc_house,asc_long = drik.dasavarga_from_long(ascendant_longitude,divisional_chart_factor)
    planet_positions = [[ascendant_index,(asc_house,asc_long)]] + planet_positions
    planet_positions = planet_positions[:const._pp_count_upto_ketu]
    p_to_h = { p:h for p,(h,_) in planet_positions}
    h_to_p = ['' for h in range(12)] 
    for sublist in planet_positions:
        p = sublist[0]
        h = sublist[1][0]
        h_to_p[h] += str(p) + '/'
    """
    yoga_results = {}
    yoga_with_special_arguments = {
        'mahabhagya_yoga':['gender'], 'sara_yoga':['method'],'ishu_yoga':['method'],
        'matsya':['method'],'koorma':['method'],'brahma':['method'],'yukthi':['method'],
        'dharidhra':['method'],'amsaavatara':['method'],
        'subha_yoga':['use_affliction_check', 'include_rahu_ketu_aspecting'],
        'asubha_yoga':['use_affliction_check', 'include_rahu_ketu_aspecting'],
    }
    for yoga_function,details in msgs.items():
        """ TODO: yoga functions have only one argument h_to_p. Here we call 3 args - need to synch"""
        eval_str = yoga_function+'_from_jd_place'#'_from_planet_positions'
        #print(eval_str)
        try:
            call_kwargs = {}
            if yoga_function in yoga_with_special_arguments:
                for arg_name in yoga_with_special_arguments[yoga_function]:
                    if arg_name in kwargs:
                        call_kwargs[arg_name] = kwargs[arg_name]
            yoga_exists = eval(eval_str)(jd=jd, place=place,
                                         divisional_chart_factor=divisional_chart_factor,
                                         **call_kwargs)
            if yoga_exists:
                details.insert(0,'D'+str(divisional_chart_factor))
                yoga_results[yoga_function] = details
        except Exception as e:
            utils.show_exception(e)
            print("Error executing",eval_str,"for divisional_chart_factor=",divisional_chart_factor,e)
    #print('Found',len(yoga_results),'out of',len(msgs),'yogas in D'+str(divisional_chart_factor),'chart')
    return yoga_results,len(yoga_results),len(msgs)
""" Sun/Ravi Yogas """
def vesi_yoga_from_planet_positions(planet_positions):
    """  BVR-16 If there is a planet other than Moon in the 2nd house from Sun, then this yoga is present. """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return vesi_yoga(h_to_p)
def vesi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """  BVR-16 If there is a planet other than Moon in the 2nd house from Sun, then this yoga is present. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return vesi_yoga_from_planet_positions(pp)
def vesi_yoga(chart_1d):
    """  BVR-16 If there is a planet other than Moon in the 2nd house from Sun, then this yoga is present. """
    yoga_planet = const.SUN_ID; excluded_planet = const.MOON_ID
    house_from_yoga_planet = const.HOUSE_2
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_house = (p_to_h[yoga_planet] + house_from_yoga_planet) % 12
    planet_ids = planets_in_raasi(yoga_house,p_to_h)# V4.8.0
    return (len(planet_ids) >= 1) and (excluded_planet not in planet_ids)
def vosi_yoga_from_planet_positions(planet_positions):
    """ BVR-17 (Vasi Yoga) If there is a planet other than Moon in the 12th house from Sun, then this yoga is present. """ 
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return vosi_yoga(h_to_p)
def vosi_yoga(chart_1d):
    """ BVR-17 (Vasi Yoga) If there is a planet other than Moon in the 12th house from Sun, then this yoga is present. """ 
    yoga_planet = const.SUN_ID; excluded_planet = const.MOON_ID
    house_from_yoga_planet = const.HOUSE_12
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_house = (p_to_h[yoga_planet] + house_from_yoga_planet) % 12
    planet_ids = planets_in_raasi(yoga_house,p_to_h)# V4.8.0
    return (len(planet_ids) >= 1) and (excluded_planet not in planet_ids)
def vosi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-17 (Vasi Yoga) If there is a planet other than Moon in the 12th house from Sun, then this yoga is present. """ 
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return vosi_yoga_from_planet_positions(planet_positions)
def ubhayachara_yoga_from_planet_positions(planet_positions):
    """ BVR-18 Obhayachari / Ubhayachara  Yoga - There is a planet other than Moon in the 2nd and 12th house from Sun. """
    yp = vesi_yoga_from_planet_positions(planet_positions) and vosi_yoga_from_planet_positions(planet_positions)
    return yp
def ubhayachara_yoga(chart_1d):
    """ BVR-18 Obhayachari / Ubhayachara  Yoga - There is a planet other than Moon in the 2nd and 12th house from Sun. """
    yp = vesi_yoga(chart_1d) and vosi_yoga(chart_1d)
    return yp
def ubhayachara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-18 Obhayachari / Ubhayachara  Yoga - There is a planet other than Moon in the 2nd and 12th house from Sun. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return ubhayachara_yoga_from_planet_positions(planet_positions)
def nipuna_yoga_from_planet_positions(planet_positions):
    """ BVR-26 Budha-Aaditya Yoga (Nipuna Yoga)- If Sun and Mercury are together (in one sign), this yoga is present."""
    """
        TODO: Note: If Mercury is too close to Sun, he is combust (asta or astangata). Yogas 
                    formed by combust planets lose some of their power to do good. 
    """
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    return p_to_h[const.SUN_ID]==p_to_h[const.MERCURY_ID]
def nipuna_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-26 Budha-Aaditya Yoga (Nipuna Yoga)- If Sun and Mercury are together (in one sign), this yoga is present."""
    """
        TODO: Note: If Mercury is too close to Sun, he is combust (asta or astangata). Yogas 
                    formed by combust planets lose some of their power to do good. 
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    #is_mercury_combust =  const.MERCURY_ID in charts.planets_in_combustion(planet_positions, use_absolute_longitude=True)
    return nipuna_yoga_from_planet_positions(planet_positions)
budha_aaditya_yoga_from_planet_positions = lambda planet_positions:nipuna_yoga_from_planet_positions(planet_positions)
def nipuna_yoga(chart_1d):
    """ BVR-26 Budha-Aaditya Yoga (Nipuna Yoga)- If Sun and Mercury are together (in one sign), this yoga is present."""
    """
        TODO: Note: If Mercury is too close to Sun, he is combust (asta or astangata). Yogas 
                    formed by combust planets lose some of their power to do good. 
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return p_to_h[const.SUN_ID]==p_to_h[const.MERCURY_ID]
budha_aaditya_yoga = lambda chart_1d:nipuna_yoga(chart_1d)
""" Moon/Chandra yogas """
def sunaphaa_yoga_from_planet_positions(planet_positions):
    """ BVR-2 If there are planets other than Sun in the 2nd house from Moon, this yoga is present. """ 
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sunaphaa_yoga(h_to_p)
def sunaphaa_yoga(chart_1d):
    """ BVR-2 If there are planets other than Sun in the 2nd house from Moon, this yoga is present. """ 
    yoga_planet = const.MOON_ID; excluded_planet = const.SUN_ID
    house_from_yoga_planet = const.HOUSE_2
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_house = (p_to_h[yoga_planet] + house_from_yoga_planet) % 12
    yoga_house_planets = planets_in_raasi(yoga_house,p_to_h) # V4.8.0
    planet_ids = [int(p) for p in yoga_house_planets if p!='' and p != const._ascendant_symbol]
    return (len(planet_ids) >= 1) and (excluded_planet not in planet_ids)
def sunaphaa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-2 If there are planets other than Sun in the 2nd house from Moon, this yoga is present. """ 
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return sunaphaa_yoga_from_planet_positions(pp)
def anaphaa_yoga_from_planet_positions(planet_positions):
    """ BVR-3 If there are planets other than Sun in the 12th house from Moon, this yoga is present. """ 
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return anaphaa_yoga(h_to_p)
def anaphaa_yoga(chart_1d):
    """ BVR-3 If there are planets other than Sun in the 12th house from Moon, this yoga is present. """ 
    yoga_planet = const.MOON_ID; excluded_planet = const.SUN_ID
    house_from_yoga_planet = const.HOUSE_12
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_house = (p_to_h[yoga_planet] + house_from_yoga_planet) % 12
    yoga_house_planets = planets_in_raasi(yoga_house,p_to_h) # V4.8.0
    planet_ids = [int(p) for p in yoga_house_planets if p!='' and p != const._ascendant_symbol]
    return (len(planet_ids) >= 1) and (excluded_planet not in planet_ids)
def anaphaa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-3 If there are planets other than Sun in the 12th house from Moon, this yoga is present. """ 
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return anaphaa_yoga_from_planet_positions(pp)
def duradhara_yoga(chart_1d):
    """ BVR-4 Sunaphaa/Duradhara/Dhuradhara Yoga - There is a planet other than Sun in the 2nd and 12th house from Moon. """
    return sunaphaa_yoga(chart_1d) and anaphaa_yoga(chart_1d)
def duradhara_yoga_from_planet_positions(planet_positions):
    """ BVR-4 Sunaphaa/Duradhara/Dhuradhara Yoga - There is a planet other than Sun in the 2nd and 12th house from Moon. """
    _sunaphaa = sunaphaa_yoga_from_planet_positions(planet_positions)
    _anaphaa = anaphaa_yoga_from_planet_positions(planet_positions)
    return _sunaphaa and _anaphaa
def duradhara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-4 Sunaphaa/Duradhara/Dhuradhara Yoga - There is a planet other than Sun in the 2nd and 12th house from Moon. """
    _sunaphaa = sunaphaa_yoga_from_jd_place(jd, place, divisional_chart_factor)
    _anaphaa = anaphaa_yoga_from_jd_place(jd, place, divisional_chart_factor)
    return _sunaphaa and _anaphaa
def kemadruma_yoga_from_planet_positions(planet_positions):
    """ BVR-5 Kemadruma Yoga - there are no planets other than Sun in the 1st, 2nd and 12th houses from
        Moon and if there are no planets other than Moon in the quadrants from lagna"""
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return kemadruma_yoga(h_to_p)
def kemadruma_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-5 Kemadruma Yoga - there are no planets other than Sun in the 1st, 2nd and 12th houses from
        Moon and if there are no planets other than Moon in the quadrants from lagna"""
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return kemadruma_yoga_from_planet_positions(planet_positions)
def kemadruma_yoga(chart_1d):
    """
    BVR-5 Kemadruma Yoga:
    - No planets other than Sun in the 1st, 2nd, and 12th houses from Moon
      (i.e., in those three houses, allowed occupants among planets are Moon and Sun only; emptiness is also fine).
    - No planets other than Moon in the quadrants (1, 4, 7, 10) from lagna
      (i.e., in those four houses, allowed among planets is Moon only; emptiness is also fine).
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    # Read key anchors
    moon_house = p_to_h[const.MOON_ID]
    lagna_house = p_to_h[const._ascendant_symbol]
    # --- Condition 1: 1st, 2nd, 12th from Moon ---
    houses_from_moon = [(moon_house + off) % 12 for off in (const.HOUSE_1, const.HOUSE_2, const.HOUSE_12)]
    # Collect *planets only* (exclude ascendant symbol)
    planets_in_moon_zone = [p for p, h in p_to_h.items() if p in SUN_TO_KETU and h in houses_from_moon]
    # Allowed: Moon and Sun only
    ky1 = all(p in (const.MOON_ID, const.SUN_ID) for p in planets_in_moon_zone)
    # --- Condition 2: Quadrants from Lagna ---
    quadrants = house.quadrants_of_the_raasi(lagna_house)  # [lagna, lagna+3, lagna+6, lagna+9] % 12
    planets_in_quadrants = [p for p, h in p_to_h.items() if p in SUN_TO_KETU and h in quadrants]
    # Allowed: Moon only
    ky2 = all(p == const.MOON_ID for p in planets_in_quadrants)
    return ky1 and ky2
def chandra_mangala_yoga_from_planet_positions(planet_positions):
    """ BVR-6 Chandra-Mangala Yoga - Moon and Mars are together (in one sign). """
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    return p_to_h[const.MARS_ID]==p_to_h[const.MOON_ID]
def chandra_mangala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-6 Chandra-Mangala Yoga - Moon and Mars are together (in one sign). """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return chandra_mangala_yoga_from_planet_positions(planet_positions)
def chandra_mangala_yoga(chart_1d):
    """ BVR-6 Chandra-Mangala Yoga - Moon and Mars are together (in one sign). """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return p_to_h[const.MARS_ID]==p_to_h[const.MOON_ID]
def adhi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-7 Adhi Yoga - natural benefics occupy 6th, 7th and 8th from Moon, """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    _natural_benefics = charts.benefics(jd, place,divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    yoga_houses = [const.HOUSE_6,const.HOUSE_7,const.HOUSE_8]
    houses_from_moon = [(p_to_h[const.MOON_ID]+mh)%12 for mh in yoga_houses]
    return any(p_to_h[pid] in houses_from_moon for pid in _natural_benefics)
def adhi_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-7 Adhi Yoga - natural benefics occupy 6th, 7th and 8th from Moon, """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return adhi_yoga(h_to_p,natural_benefics=natural_benefics)
def adhi_yoga(chart_1d,natural_benefics=None):
    """ BVR-7 Adhi Yoga - natural benefics occupy 6th, 7th and 8th from Moon, """
    """ 
        NOTE: Mercury is treated as natural benefics if alone or with Jupiter and/or Venus
        Moon is not considered here because tithi information is not passed
        If moon is to be considered use adhi_yoga(jd,place)
    """
    # AND is used to check ALL NATURAL BENEFICS are in 6 or 7 or 8 from moon
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_houses = [const.HOUSE_6,const.HOUSE_7,const.HOUSE_8]
    houses_from_moon = [(p_to_h[const.MOON_ID]+mh)%12 for mh in yoga_houses]
    if natural_benefics is not None:
        _natural_benefics = natural_benefics
    else:
        _natural_benefics = const.natural_benefics
    if _is_mercury_benefic(chart_1d):
        _natural_benefics += [const.MERCURY_ID] 
    return any(p_to_h[pid] in houses_from_moon for pid in _natural_benefics)
""" Pancha Mahapurusha Yogas """
def ruchaka_yoga_from_planet_positions(planet_positions):
    """  BVR-22 Ruchaka Yoga - Mars should be in 0 or 7 or 9th rasi and he should be in 1, 4, 7 or 10th from lagna """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return ruchaka_yoga(h_to_p)
def ruchaka_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """  BVR-22 Ruchaka Yoga - Mars should be in 0 or 7 or 9th rasi and he should be in 1, 4, 7 or 10th from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return ruchaka_yoga_from_planet_positions(planet_positions)
def ruchaka_yoga(chart_1d):
    """  BVR-22 Ruchaka Yoga - Mars should be in 0 or 7 or 9th rasi and he should be in 1, 4, 7 or 10th from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_planet = const.MARS_ID
    yoga_planet_zodiac = p_to_h[yoga_planet]
    yoga_zodiacs = [const.ARIES, const.SCORPIO, const.CAPRICORN]
    _yoga_houses = [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]
    yoga_houses =[(p_to_h[const._ascendant_symbol]+mh)%12 for mh in _yoga_houses]
    return yoga_planet_zodiac in yoga_zodiacs and yoga_planet_zodiac in yoga_houses
def bhadra_yoga_from_planet_positions(planet_positions):
    """ BVR-23 Bhadra Yoga - Mercury should be in Ge or Vi and he should be in 1st, 4th, 7th or 10th from lagna. """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return bhadra_yoga(h_to_p)
def bhadra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-23 Bhadra Yoga - Mercury should be in Ge or Vi and he should be in 1st, 4th, 7th or 10th from lagna. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return bhadra_yoga_from_planet_positions(planet_positions)
def bhadra_yoga(chart_1d):
    """ BVR-23 Bhadra Yoga - Mercury should be in Ge or Vi and he should be in 1st, 4th, 7th or 10th from lagna. """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_planet = const.MERCURY_ID
    yoga_planet_zodiac = p_to_h[yoga_planet]
    yoga_zodiacs = [const.GEMINI, const.VIRGO]
    _yoga_houses = [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]
    yoga_houses =[(p_to_h[const._ascendant_symbol]+mh)%12 for mh in _yoga_houses]
    return yoga_planet_zodiac in yoga_zodiacs and yoga_planet_zodiac in yoga_houses
def sasa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-21 Saturn should be in Cp, Aq or Li and he should be in 1st, 4th, 7th or 10th from lagna. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return sasa_yoga_from_planet_positions(planet_positions)
def sasa_yoga_from_planet_positions(planet_positions):
    """ BVR-21 Saturn should be in Cp, Aq or Li and he should be in 1st, 4th, 7th or 10th from lagna. """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sasa_yoga(h_to_p)
def sasa_yoga(chart_1d):
    """ BVR-21 Saturn should be in Cp, Aq or Li and he should be in 1st, 4th, 7th or 10th from lagna. """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_planet = const.SATURN_ID
    yoga_planet_zodiac = p_to_h[yoga_planet]
    yoga_zodiacs = [const.CAPRICORN, const.AQUARIUS, const.LIBRA]
    _yoga_houses = [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]
    yoga_houses =[(p_to_h[const._ascendant_symbol]+mh)%12 for mh in _yoga_houses]
    return yoga_planet_zodiac in yoga_zodiacs and yoga_planet_zodiac in yoga_houses
def maalavya_yoga_from_planet_positions(planet_positions):
    """ BVR-20 Maalavya Yoga - Venus should be in Ta, Li or Pi and he should be in 1st, 4th, 7th or 10th from lagna. """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return maalavya_yoga(chart_1d)
def maalavya_yoga(chart_1d):
    """ BVR-20 Maalavya Yoga - Venus should be in Ta, Li or Pi and he should be in 1st, 4th, 7th or 10th from lagna. """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_planet = const.VENUS_ID
    yoga_planet_zodiac = p_to_h[yoga_planet]
    yoga_zodiacs = [const.TAURUS, const.PISCES, const.LIBRA]
    _yoga_houses = [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]
    yoga_houses =[(p_to_h[const._ascendant_symbol]+mh)%12 for mh in _yoga_houses]
    return yoga_planet_zodiac in yoga_zodiacs and yoga_planet_zodiac in yoga_houses
def maalavya_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-20 Maalavya Yoga - Venus should be in Ta, Li or Pi and he should be in 1st, 4th, 7th or 10th from lagna. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return maalavya_yoga_from_planet_positions(planet_positions)
def hamsa_yoga_from_planet_positions(planet_positions):
    """ BVR-19 Hamsa Yoga - Jupiter should be in Sg, Pi or Cn and he should be in 1st, 4th, 7th or 10th from lagna. """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return hamsa_yoga(chart_1d)
def hamsa_yoga(chart_1d):
    """ BVR-19 Hamsa Yoga - Jupiter should be in Sg, Pi or Cn and he should be in 1st, 4th, 7th or 10th from lagna. """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    yoga_planet = const.JUPITER_ID
    yoga_planet_zodiac = p_to_h[yoga_planet]
    yoga_zodiacs = [const.SAGITTARIUS, const.PISCES, const.CANCER]
    _yoga_houses = [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]
    yoga_houses =[(p_to_h[const._ascendant_symbol]+mh)%12 for mh in _yoga_houses]
    return yoga_planet_zodiac in yoga_zodiacs and yoga_planet_zodiac in yoga_houses
def hamsa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-19 Hamsa Yoga - Jupiter should be in Sg, Pi or Cn and he should be in 1st, 4th, 7th or 10th from lagna. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return hamsa_yoga_from_planet_positions(planet_positions)
""" Naabasa / Aasraya yogas """
def rajju_yoga_from_planet_positions(planet_positions):
    """ BVR-98 Rajju Yoga: all the planets are exclusively in movable signs """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return rajju_yoga(chart_1d)
def rajju_yoga(chart_1d):
    """ BVR-98 Rajju Yoga: all the planets are exclusively in movable signs """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _rajju_yoga = all(p_to_h[p] in movable_signs for p in SUN_TO_KETU)
    return _rajju_yoga
def rajju_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-98 Rajju Yoga: all the planets are exclusively in movable signs """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return rajju_yoga_from_planet_positions(planet_positions)
def musala_yoga_from_planet_positions(planet_positions):
    """ BVR-99 Musala Yoga: all the planets are exclusively in fixed signs """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return musala_yoga(chart_1d)
def musala_yoga(chart_1d):
    """ BVR-99 Musala Yoga: all the planets are exclusively in fixed signs """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _musala_yoga = all(p_to_h[p] in fixed_signs for p in SUN_TO_KETU)
    return _musala_yoga
def musala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-99 Musala Yoga: all the planets are exclusively in fixed signs """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return musala_yoga_from_planet_positions(planet_positions)
def nala_yoga_from_planet_positions(planet_positions):
    """ BVR-100 Nala Yoga: all the planets are exclusively in dual signs, """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return nala_yoga(chart_1d)
def nala_yoga(chart_1d):
    """ BVR-100 Nala Yoga: all the planets are exclusively in dual signs, """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _nala_yoga = all(p_to_h[p] in dual_signs for p in SUN_TO_KETU)
    return _nala_yoga
def nala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-100 Nala Yoga: all the planets are exclusively in dual signs, """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return nala_yoga_from_planet_positions(planet_positions)
""" Naabhasa Dala Yogas """
def srik_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    return maalaa_yoga_from_jd_place(jd, place, divisional_chart_factor)
def maalaa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    lagna_house = p_to_h[const._ascendant_symbol]
    kendra_houses = quadrants_of_the_house(lagna_house)
    occupied_benefic_kendras = 0
    for house_index in kendra_houses:
        planets_in_house = planets_in_raasi(house_index,p_to_h)#V4.8.0
        if any(str(nb) in planets_in_house for nb in _natural_benefics):
            occupied_benefic_kendras += 1
    return occupied_benefic_kendras == 3
def srik_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    return maalaa_yoga_from_planet_positions(planet_positions,natural_benefics=natural_benefics)
def maalaa_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return maalaa_yoga(chart_1d,natural_benefics=natural_benefics) 
def srik_yoga(chart_1d,natural_benefics=None):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    return maalaa_yoga(chart_1d,natural_benefics=natural_benefics)
def maalaa_yoga(chart_1d,natural_benefics=None):
    """ BVR-101 Srik/maalaa Yoga -  all the benefics occupy kendras, Srik Yoga is caused."""
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    if natural_benefics is not None:
        _natural_benefics = natural_benefics
    else:
        _natural_benefics = const.natural_benefics
    if _is_mercury_benefic(chart_1d):
        _natural_benefics += [const.MERCURY_ID] 
    lagna_house = p_to_h[const._ascendant_symbol]
    kendra_houses = quadrants_of_the_house(lagna_house)
    occupied_benefic_kendras = 0
    for house_index in kendra_houses:
        planets_in_house = planets_in_raasi(house_index,p_to_h) # V4.8.0
        if any(nb in planets_in_house for nb in _natural_benefics):
            occupied_benefic_kendras += 1
    return occupied_benefic_kendras == 3
def sarpa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-102 Sarpa Yoga: If three quadrants from lagna are occupied by natural malefics, """
    _natural_malefics = charts.malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    lagna_house = p_to_h[const._ascendant_symbol]
    kendra_houses = quadrants_of_the_house(lagna_house)
    occupied_benefic_kendras = 0
    for house_index in kendra_houses:
        planets_in_house = planets_in_raasi(house_index,p_to_h) # V4.8.0
        if any(nb in planets_in_house for nb in _natural_malefics):
            occupied_benefic_kendras += 1
    return occupied_benefic_kendras == 3
def sarpa_yoga(chart_1d):
    """ BVR-102 Sarpa Yoga: If three quadrants from lagna are occupied by natural malefics, """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_malefics = const.natural_malefics
    lagna_house = p_to_h[const._ascendant_symbol]
    kendra_houses = quadrants_of_the_house(lagna_house)
    occupied_benefic_kendras = 0
    for house_index in kendra_houses:
        planets_in_house = planets_in_raasi(house_index,p_to_h) # V4.8.0
        if any(nb in planets_in_house for nb in _natural_malefics):
            occupied_benefic_kendras += 1
    return occupied_benefic_kendras == 3        
def sarpa_yoga_from_planet_positions(planet_positions):
    """ BVR-102 Sarpa Yoga: If three quadrants from lagna are occupied by natural malefics, """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sarpa_yoga(chart_1d)
""" Aakriti yogas """
def gadaa_yoga_from_planet_positions(planet_positions):
    """ BVR-81 Gadaa Yoga: all the planets occupy two successive quadrants from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return gadaa_yoga(chart_1d)
def gadaa_yoga(chart_1d):
    """ BVR-81 Gadaa Yoga: all the planets occupy two successive quadrants from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    quadrant_houses = [const.HOUSE_1, const.HOUSE_4, const.HOUSE_7, const.HOUSE_10]
    quadrant_pairs = [tuple(sorted(((asc_house+a)%12,(asc_house+b)%12))) for a,b in zip(quadrant_houses, quadrant_houses[1:]+quadrant_houses[:1])]
    sph = tuple(sorted({p_to_h[p_id] for p_id in SUN_TO_SATURN}))
    gadaa_yoga = sph in quadrant_pairs
    return gadaa_yoga
def gadaa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-81 Gadaa Yoga: all the planets occupy two successive quadrants from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return gadaa_yoga_from_planet_positions(planet_positions)
def sakata_yoga_from_planet_positions(planet_positions):
    """ BVR-82 Sakata Yoga: If all the planets occupy 1st and 7th houses from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sakata_yoga(chart_1d)
def sakata_yoga(chart_1d):
    """ BVR-82 Sakata Yoga: If all the planets occupy 1st and 7th houses from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    slq = [tuple(sorted(((asc_house+const.HOUSE_1)%12, (asc_house+const.HOUSE_7)%12)))]
    sph = tuple(sorted({p_to_h[p_id] for p_id in SUN_TO_SATURN}))
    sakata_yoga = sph in slq
    return sakata_yoga
def sakata_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-82 Sakata Yoga: If all the planets occupy 1st and 7th houses from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    return sakata_yoga_from_planet_positions(planet_positions)
def vihaga_yoga_from_planet_positions(planet_positions):
    return vihanga_yoga_from_planet_positions(planet_positions)
def vihanga_yoga_from_planet_positions(planet_positions):
    """ BVR-83 Vihanga/Vihaga Yoga: If all the planets occupy 4th and 10th houses from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return vihanga_yoga(chart_1d)
def vihanga_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-83 Vihanga/Vihaga Yoga: If all the planets occupy 4th and 10th houses from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return vihanga_yoga_from_planet_positions(planet_positions)
def vihaga_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ BVR-83 Vihanga/Vihaga Yoga: If all the planets occupy 4th and 10th houses from lagna """
    return vihanga_yoga_from_jd_place(jd, place, divisional_chart_factor)
def vihaga_yoga(chart_1d):
    """ BVR-83 Vihanga/Vihaga Yoga: If all the planets occupy 4th and 10th houses from lagna """
    return vihanga_yoga(chart_1d)
def vihanga_yoga(chart_1d):
    """ BVR-83 Vihanga/Vihaga Yoga: If all the planets occupy 4th and 10th houses from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    slq = [tuple(sorted(((asc_house+const.HOUSE_4)%12, (asc_house+const.HOUSE_10)%12)))]
    sph = tuple(sorted({p_to_h[p_id] for p_id in SUN_TO_SATURN}))
    vihanga_yoga = sph in slq
    return vihanga_yoga
def sringaataka_yoga_from_planet_positions(planet_positions):
    """ BVR-86 Sringaataka Yoga: If all the planets occupy trines (1st, 5th and 9th) from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sringaataka_yoga(chart_1d)
def sringaataka_yoga(chart_1d):
    """ BVR-86 Sringaataka Yoga: If all the planets occupy trines (1st, 5th and 9th) from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    slq = [tuple(sorted(((asc_house+const.HOUSE_1)%12, (asc_house+const.HOUSE_5)%12, (asc_house+const.HOUSE_9)%12)))]
    sph = tuple(sorted({p_to_h[p_id] for p_id in SUN_TO_SATURN}))
    sringaataka_yoga = sph in slq
    return sringaataka_yoga
def sringaataka_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-86 Sringaataka Yoga: If all the planets occupy trines (1st, 5th and 9th) from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return sringaataka_yoga_from_planet_positions(planet_positions)
def hala_yoga_from_planet_positions(planet_positions):
    """ BVR-87 Hala Yoga: If all the planets occupy mutual trines but not trines from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return hala_yoga(chart_1d)
def hala_yoga(chart_1d):
    """ BVR-87 Hala Yoga: If all the planets occupy mutual trines but not trines from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    slq = [tuple(sorted(((asc_house+const.HOUSE_2)%12, (asc_house+const.HOUSE_6)%12, (asc_house+const.HOUSE_10)%12))),
        tuple(sorted(((asc_house+const.HOUSE_3)%12, (asc_house+const.HOUSE_7)%12, (asc_house+const.HOUSE_11)%12))),
        tuple(sorted(((asc_house+const.HOUSE_4)%12, (asc_house+const.HOUSE_8)%12, (asc_house+const.HOUSE_12)%12)))
        ]
    sph = tuple(sorted({p_to_h[p_id] for p_id in SUN_TO_SATURN}))
    hala_yoga = sph in slq
    return hala_yoga
def hala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-87 Hala Yoga: If all the planets occupy mutual trines but not trines from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return hala_yoga_from_planet_positions(planet_positions)
def vajra_yoga_from_planet_positions(planet_positions):
    """
    BVR-84 Vajra Yoga (presence-based):
    - Lagna and 7th houses have at least one natural benefic present.
    - 4th and 10th houses have at least one natural malefic present.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return vajra_yoga(chart_1d)
def vajra_yoga(chart_1d):
    """
    BVR-84 Vajra Yoga (presence-based):
    - Lagna and 7th houses have at least one natural benefic present.
    - 4th and 10th houses have at least one natural malefic present.
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)

    asc_house = p_to_h[const._ascendant_symbol]  # 0..11

    lagna   = (asc_house + const.HOUSE_1)  % 12
    seventh = (asc_house + const.HOUSE_7)  % 12
    fourth  = (asc_house + const.HOUSE_4)  % 12
    tenth   = (asc_house + const.HOUSE_10) % 12

    def any_in_house(planet_ids, target_house):
        return any(p_to_h.get(pid) == target_house for pid in planet_ids)

    benefic_ok = any_in_house(const.natural_benefics, lagna) and \
                 any_in_house(const.natural_benefics, seventh)

    malefic_ok = any_in_house(const.natural_malefics, fourth) and \
                 any_in_house(const.natural_malefics, tenth)

    return benefic_ok and malefic_ok
def vajra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-84 Vajra Yoga (presence-based):
    - Lagna and 7th houses have at least one natural benefic present.
    - 4th and 10th houses have at least one natural malefic present.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return vajra_yoga_from_planet_positions(planet_positions)
def yava_yoga_from_planet_positions(planet_positions):
    """ BVR-85 Yava Yoga: If lagna and the 7th houses are occupied by natural malefics and the 4th
        and 10th houses are occupied by natural benefics, """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return yava_yoga(chart_1d)
def yava_yoga(chart_1d):
    """ BVR-85 Yava Yoga: If lagna and the 7th houses are occupied by natural malefics and the 4th
        and 10th houses are occupied by natural benefics, """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)

    asc_house = p_to_h[const._ascendant_symbol]  # 0..11

    lagna   = (asc_house + const.HOUSE_1)  % 12
    seventh = (asc_house + const.HOUSE_7)  % 12
    fourth  = (asc_house + const.HOUSE_4)  % 12
    tenth   = (asc_house + const.HOUSE_10) % 12

    def any_in_house(planet_ids, target_house):
        return any(p_to_h.get(pid) == target_house for pid in planet_ids)

    malefic_ok = any_in_house(const.natural_malefics, lagna) and \
                 any_in_house(const.natural_malefics, seventh)

    benefic_ok = any_in_house(const.natural_benefics, fourth) and \
                 any_in_house(const.natural_benefics, tenth)

    return benefic_ok and malefic_ok
def yava_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-85 Vajra Yoga (presence-based):
    - Lagna and 7th houses have at least one natural benefic present.
    - 4th and 10th houses have at least one natural malefic present.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return yava_yoga_from_planet_positions(planet_positions)
def kamala_yoga_from_planet_positions(planet_positions):
    """
    BVR-88 Kamala Yoga: If all the planets are in quadrants (kendras) from lagna, this yoga is formed.
    Subset interpretation: every considered planet lies in one of {1,4,7,10} from Lagna.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return kamala_yoga(chart_1d)
def kamala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-88 Kamala Yoga: If all the planets are in quadrants (kendras) from lagna, this yoga is formed.
    Subset interpretation: every considered planet lies in one of {1,4,7,10} from Lagna.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return kamala_yoga_from_planet_positions(planet_positions)
def kamala_yoga(chart_1d):
    """
    BVR-88 Kamala Yoga: If all the planets are in quadrants (kendras) from lagna, this yoga is formed.
    Subset interpretation: every considered planet lies in one of {1,4,7,10} from Lagna.
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # Kendras (quadrants) from Lagna: 1, 4, 7, 10 (mod 12)
    kendras = {
        (asc_house + const.HOUSE_1)  % 12,
        (asc_house + const.HOUSE_4)  % 12,
        (asc_house + const.HOUSE_7)  % 12,
        (asc_house + const.HOUSE_10) % 12,
    }
    # All considered planets must lie within kendras
    return all(p_to_h.get(pid) in kendras for pid in SUN_TO_SATURN)
def vaapi_yoga_from_planet_positions(planet_positions):
    """
    BVR-89 Vaapi Yoga: If all the planets are in Panaparas (2,5,8,11) or in Apoklimas (3,6,9,12) from Lagna.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return vaapi_yoga(chart_1d)
def vaapi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-89 Vaapi Yoga: If all the planets are in Panaparas (2,5,8,11) or in Apoklimas (3,6,9,12) from Lagna.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return vaapi_yoga_from_planet_positions(planet_positions)
def vaapi_yoga(chart_1d):
    """
    BVR-89 Vaapi Yoga: If all the planets are in Panaparas (2,5,8,11) or in Apoklimas (3,6,9,12) from Lagna.
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    panaparas = {(asc_house + const.HOUSE_2) % 12,
                 (asc_house + const.HOUSE_5) % 12,
                 (asc_house + const.HOUSE_8) % 12,
                 (asc_house + const.HOUSE_11) % 12}
    apoklimas = {(asc_house + const.HOUSE_3) % 12,
                 (asc_house + const.HOUSE_6) % 12,
                 (asc_house + const.HOUSE_9) % 12,
                 (asc_house + const.HOUSE_12) % 12}
    # Check if all planets are in panaparas OR all in apoklimas
    all_in_panaparas = all(p_to_h.get(pid) in panaparas for pid in SUN_TO_SATURN)
    all_in_apoklimas = all(p_to_h.get(pid) in apoklimas for pid in SUN_TO_SATURN)
    return all_in_panaparas or all_in_apoklimas
def yoopa_yoga_from_planet_positions(planet_positions):
    """ BVR-71 Yoopa Yoga: all the planets are in 1st, 2nd, 3rd and 4th houses from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return yoopa_yoga(chart_1d)
def yoopa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-71 Yoopa Yoga: all the planets are in 1st, 2nd, 3rd and 4th houses from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return yoopa_yoga_from_planet_positions(planet_positions)
def yoopa_yoga(chart_1d):
    """ BVR-71 Yoopa Yoga: all the planets are in 1st, 2nd, 3rd and 4th houses from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    yoga_houses = {
        (asc_house + const.HOUSE_1)  % 12,
        (asc_house + const.HOUSE_2)  % 12,
        (asc_house + const.HOUSE_3)  % 12,
        (asc_house + const.HOUSE_4) % 12,
    }
    return all(p_to_h.get(pid) in yoga_houses for pid in SUN_TO_SATURN)
def sara_yoga_from_planet_positions(planet_positions,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sara_yoga(chart_1d,method=method)
def sara_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return sara_yoga_from_planet_positions(planet_positions,method=method)
def sara_yoga(chart_1d,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    yoga_houses = {
        (asc_house + const.HOUSE_4)  % 12,
        (asc_house + const.HOUSE_5)  % 12,
        (asc_house + const.HOUSE_6)  % 12 if method==1 else (asc_house + const.HOUSE_9)  % 12,
        (asc_house + const.HOUSE_7) % 12,
    }
    return all(p_to_h.get(pid) in yoga_houses for pid in SUN_TO_SATURN)
def ishu_yoga_from_planet_positions(planet_positions,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    return sara_yoga_from_planet_positions(planet_positions,method=method)
def ishu_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    return sara_yoga_from_jd_place(jd, place, divisional_chart_factor,method=method)
def ishu_yoga(chart_1d,method=None):
    """ 
        BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
        NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
        In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
        In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
        seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
        Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
    """
    if method is None: method = const.sara_yoga_method
    return sara_yoga(chart_1d,method=method)

def sakti_yoga_from_planet_positions(planet_positions):
    """ BVR-73 Sakti Yoga: If all the planets are in 7th, 8th, 9th and 10th houses from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return sakti_yoga(chart_1d)
def sakti_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-73 Sakti Yoga: If all the planets are in 7th, 8th, 9th and 10th houses from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return sakti_yoga_from_planet_positions(planet_positions)
def sakti_yoga(chart_1d):
    """ BVR-73 Sakti Yoga: If all the planets are in 7th, 8th, 9th and 10th houses from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    yoga_houses = {
        (asc_house + const.HOUSE_7)  % 12,
        (asc_house + const.HOUSE_8)  % 12,
        (asc_house + const.HOUSE_9)  % 12,
        (asc_house + const.HOUSE_10) % 12,
    }
    return all(p_to_h.get(pid) in yoga_houses for pid in SUN_TO_SATURN)
def danda_yoga_from_planet_positions(planet_positions):
    """ BVR-74 Danda Yoga: If all the planets are in 10th, 11th, 12th and 1st houses from lagna """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return danda_yoga(chart_1d)
def danda_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-74 Sakti Yoga: If all the planets are in 7th, 8th, 9th and 10th houses from lagna """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return danda_yoga_from_planet_positions(planet_positions)
def danda_yoga(chart_1d):
    """ BVR-74 Danda Yoga: If all the planets are in 10th, 11th, 12th and 1st houses from lagna """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    yoga_houses = {
        (asc_house + const.HOUSE_10)  % 12,
        (asc_house + const.HOUSE_11)  % 12,
        (asc_house + const.HOUSE_12)  % 12,
        (asc_house + const.HOUSE_1) % 12,
    }
    return all(p_to_h.get(pid) in yoga_houses for pid in SUN_TO_SATURN)
def nav_yoga_from_planet_positions(planet_positions):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    return naukaa_yoga_from_planet_positions(planet_positions)
def nav_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    return naukaa_yoga_from_jd_place(jd,place,divisional_chart_factor)
def naukaa_yoga_from_planet_positions(planet_positions):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return naukaa_yoga(chart_1d)
def naukaa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return naukaa_yoga_from_planet_positions(planet_positions)
def nav_yoga(chart_1d):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    return naukaa_yoga(chart_1d)
def naukaa_yoga(chart_1d):
    """
    BVR-75 Naukaa (Nauka)/Nav Yoga: All seven visible planets (Sun..Saturn) occupy the seven
    consecutive houses commencing from Lagna (1st through 7th), with none of those
    houses empty and no visible planet outside this span.
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    base_house = p_to_h[const._ascendant_symbol]  # 0..11
    # Seven consecutive houses from Base House
    span7 = [(base_house + offset) % 12 for offset in const.SUN_TO_SATURN]
    span7_set = set(span7)
    # 1) Every visible planet must lie within the 7-house span.
    all_in_span = all(p_to_h.get(pid) in span7_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the seven houses in the span must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in span7)
    return all_occupied
def koota_yoga_from_planet_positions(planet_positions):
    """ BVR-76 Koota Yoga: If all the planets occupy the 7 signs from the 4th house """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return koota_yoga(chart_1d)
def koota_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-76 Koota Yoga: If all the planets occupy the 7 signs from the 4th house """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return koota_yoga_from_planet_positions(planet_positions)
def koota_yoga(chart_1d):
    """ BVR-76 Koota Yoga: If all the planets occupy the 7 signs from the 4th house """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    base_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_4)%12
    # Seven consecutive houses from Base House
    span7 = [(base_house + offset) % 12 for offset in const.SUN_TO_SATURN]
    span7_set = set(span7)
    # 1) Every visible planet must lie within the 7-house span.
    all_in_span = all(p_to_h.get(pid) in span7_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the seven houses in the span must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in span7)
    return all_occupied
def chatra_yoga_from_planet_positions(planet_positions):
    """ BVR-77 Chatra Yoga: If all the planets occupy the 7 signs from the 7th house, """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return chatra_yoga(chart_1d)
def chatra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-77 Chatra Yoga: If all the planets occupy the 7 signs from the 7th house, """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return chatra_yoga_from_planet_positions(planet_positions)
def chatra_yoga(chart_1d):
    """ BVR-77 Chatra Yoga: If all the planets occupy the 7 signs from the 7th house, """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    base_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_7)%12
    # Seven consecutive houses from Base House
    span7 = [(base_house + offset) % 12 for offset in const.SUN_TO_SATURN]
    span7_set = set(span7)
    # 1) Every visible planet must lie within the 7-house span.
    all_in_span = all(p_to_h.get(pid) in span7_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the seven houses in the span must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in span7)
    return all_occupied
def chaapa_yoga_from_planet_positions(planet_positions): # V4.6.0
    """ BVR-78 Chaapa Yoga: If all the planets occupy the 7 signs from the 10th house, """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return chaapa_yoga(chart_1d)
def chaapa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-78 Chaapa Yoga: If all the planets occupy the 7 signs from the 10th house, """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return chaapa_yoga_from_planet_positions(planet_positions)
def chaapa_yoga(chart_1d): # V4.6.0
    """ BVR-78 Chaapa Yoga: If all the planets occupy the 7 signs from the 10th house, """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    base_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_10)%12
    # Seven consecutive houses from Base House
    valid_houses = [(base_house + offset) % 12 for offset in const.SUN_TO_SATURN]
    valid_houses_set = set(valid_houses)
    # 1) Every visible planet must lie within the 7-house span.
    all_in_span = all(p_to_h.get(pid) in valid_houses_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the seven houses in the span must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in valid_houses)
    return all_occupied
def ardha_chandra_yoga_from_planet_positions(planet_positions):
    """
    BVR-79 Ardha Chandra Yoga (strict):
      - All seven visible planets (Sun..Saturn) are confined to a span of
        seven consecutive houses that STARTS from a non-Kendra (Panapara or Apoklima),
      - AND each of those seven houses is occupied (none empty).
    Returns:
      True if Ardha Chandra Yoga is present per strict definition, else False.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return ardha_chandra_yoga(chart_1d)
def ardha_chandra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-79 Ardha Chandra Yoga (strict):
      - All seven visible planets (Sun..Saturn) are confined to a span of
        seven consecutive houses that STARTS from a non-Kendra (Panapara or Apoklima),
      - AND each of those seven houses is occupied (none empty).
    Returns:
      True if Ardha Chandra Yoga is present per strict definition, else False.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return ardha_chandra_yoga_from_planet_positions(planet_positions)
def ardha_chandra_yoga(chart_1d):
    """
    BVR-79 Ardha Chandra Yoga (strict):
      - All seven visible planets (Sun..Saturn) are confined to a span of
        seven consecutive houses that STARTS from a non-Kendra (Panapara or Apoklima),
      - AND each of those seven houses is occupied (none empty).
    Returns:
      True if Ardha Chandra Yoga is present per strict definition, else False.
    """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]  # 0..11
    # Panaparas (succedents): 2, 5, 8, 11
    # Apoklimas (cadents): 3, 6, 9, 12 (=> 0 in 0-index system)
    starting_offsets = [
        const.HOUSE_2, const.HOUSE_5, const.HOUSE_8, const.HOUSE_11,  # panaparas
        const.HOUSE_3, const.HOUSE_6, const.HOUSE_9, const.HOUSE_12   # apoklimas
    ]
    # Precompute house -> visible planets for occupancy checks
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    # Try each allowed starting offset
    for offset in starting_offsets:
        start_house = (asc_house + offset) % 12
        span7_list = [(start_house + i) % 12 for i in const.SUN_TO_SATURN]
        span7_set = set(span7_list)
        # 1) Confinement: every visible planet must lie within this span
        all_in_span = all(p_to_h.get(pid) in span7_set for pid in SUN_TO_SATURN)
        if not all_in_span:
            continue
        # 2) Occupancy: each house in the span must have at least one visible planet
        all_occupied = all(len(house_to_visible[h]) > 0 for h in span7_list)
        if all_occupied:
            return True
    return False
def chakra_yoga_from_planet_positions(planet_positions):
    """ BVR-80 Chakra/Chandra Yoga: If all the planets occupy 1st, 3rd, 5th, 7th, 9th and 11th houses """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return chakra_yoga(chart_1d)
def chakra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-80 Chakra/Chandra Yoga: If all the planets occupy 1st, 3rd, 5th, 7th, 9th and 11th houses """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return chakra_yoga_from_planet_positions(planet_positions)
def chakra_yoga(chart_1d):
    """ BVR-80 Chakra/Chandra Yoga: If all the planets occupy 1st, 3rd, 5th, 7th, 9th and 11th houses """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    _valid_houses = [const.HOUSE_1,const.HOUSE_3,const.HOUSE_5,const.HOUSE_7,const.HOUSE_9,const.HOUSE_11]
    valid_houses = [(asc_house + offset) % 12 for offset in _valid_houses]
    valid_houses_set = set(valid_houses)
    # 1) Every visible planet must lie within valid houses
    all_in_span = all(p_to_h.get(pid) in valid_houses_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the valid houses must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in valid_houses)
    return all_occupied
def samudra_yoga_from_planet_positions(planet_positions):
    """ BVR-90 Samudra Yoga: If all the planets occupy 2nd, 4th, 6th, 8th, 10th and 12th houses """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return samudra_yoga(chart_1d)
def samudra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-90 Samudra Yoga: If all the planets occupy 2nd, 4th, 6th, 8th, 10th and 12th houses """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return samudra_yoga_from_planet_positions(planet_positions)
def samudra_yoga(chart_1d):
    """ BVR-90 Samudra Yoga: If all the planets occupy 2nd, 4th, 6th, 8th, 10th and 12th houses """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    _valid_houses = [const.HOUSE_2,const.HOUSE_4,const.HOUSE_6,const.HOUSE_8,const.HOUSE_10,const.HOUSE_12]
    valid_houses = [(asc_house + offset) % 12 for offset in _valid_houses]
    valid_houses_set = set(valid_houses)
    # 1) Every visible planet must lie within valid houses
    all_in_span = all(p_to_h.get(pid) in valid_houses_set for pid in SUN_TO_SATURN)
    if not all_in_span:
        return False
    # 2) Each of the valid houses must be occupied by at least one visible planet.
    house_to_visible = {h: set() for h in range(12)}
    for pid in SUN_TO_SATURN:
        h = p_to_h.get(pid)
        if h is not None:
            house_to_visible[h].add(pid)
    all_occupied = all(len(house_to_visible[h]) > 0 for h in valid_houses)
    return all_occupied
def veenaa_yoga_from_planet_positions(planet_positions):
    """ BVR-91 Veenaa/Vallaki Yoga: If the seven planets occupy exactly 7 distinct signs among them """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return veenaa_yoga(chart_1d)
def veenaa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-91 Veenaa/Vallaki Yoga: If the seven planets occupy exactly 7 distinct signs among them """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return veenaa_yoga_from_planet_positions(planet_positions)
def veenaa_yoga(chart_1d):
    """ BVR-91 Veenaa/Vallaki Yoga: If the seven planets occupy exactly 7 distinct signs among them """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    chk = set([p_to_h[p] for p in SUN_TO_SATURN])
    return (None not in chk) and (len(chk) == 7)
def daama_yoga_from_planet_positions(planet_positions):
    """ BVR-92 Daama/Damni Yoga: If the seven planets occupy exactly 6 distinct signs among them """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return daama_yoga(chart_1d)
def daama_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-92 Daama/Damni Yoga: If the seven planets occupy exactly 6 distinct signs among them """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return daama_yoga_from_planet_positions(planet_positions)
def daama_yoga(chart_1d):
    """ BVR-92 Daama/Damni Yoga: If the seven planets occupy exactly 6 distinct signs among them """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    chk = set([p_to_h[p] for p in SUN_TO_SATURN])
    return len(chk) == 6
def paasa_yoga_from_planet_positions(planet_positions):
    """ BVR-93 Paasa Yoga: If the seven planets occupy exactly 5 distinct signs among them """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return paasa_yoga(chart_1d)
def paasa_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-93 Paasa Yoga: If the seven planets occupy exactly 5 distinct signs among them """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return paasa_yoga_from_planet_positions(planet_positions)
def paasa_yoga(chart_1d):
    """ BVR-93 Paasa Yoga: If the seven planets occupy exactly 5 distinct signs among them """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    chk = set([p_to_h[p] for p in SUN_TO_SATURN])
    return len(chk) == 5
def kedaara_yoga_from_planet_positions(planet_positions):
    """ BVR-94 Kedaara Yoga: If the seven planets occupy exactly 4 distinct signs among them """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return kedaara_yoga(chart_1d)
def kedaara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-94 Kedaara Yoga: If the seven planets occupy exactly 4 distinct signs among them """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return kedaara_yoga_from_planet_positions(planet_positions)
def kedaara_yoga(chart_1d):
    """ BVR-94 Kedaara Yoga: If the seven planets occupy exactly 4 distinct signs among them """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    chk = set([p_to_h[p] for p in SUN_TO_SATURN])
    return len(chk) == 4
def soola_yoga_from_planet_positions(planet_positions):
    """ BVR-95 Soola Yoga: If the seven planets occupy exactly 3 distinct signs among them """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return soola_yoga(chart_1d)
def soola_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-95 Soola Yoga: If the seven planets occupy exactly 3 distinct signs among them """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return soola_yoga_from_planet_positions(planet_positions)
def soola_yoga(chart_1d):
    """ BVR-95 Soola Yoga: If the seven planets occupy exactly 3 distinct signs among them """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    chk = set([p_to_h[p] for p in SUN_TO_SATURN])
    return len(chk) == 3
def subha_yoga_from_jd_place(jd,place,divisional_chart_factor=1, use_affliction_check=False, include_rahu_ketu_aspecting=True):
    """
    Subha Yoga
      Present if either:
        (1) Lagna has benefics and is NOT affected by malefics, OR
        (2) Lagna is surrounded by benefics (benefics in BOTH 12th and 2nd) and lagna is NOT affected by malefics.
      Note: In your simplified version, "not affected" can be enforced via "only benefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by malefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only benefics" conditions in the tested houses.
      - include_rahu_ketu_aspecting (bool): If True, consider Rahu/Ketu aspects (5th, 9th, and 7th).
    TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Subha Yoga is present, False otherwise.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    _natural_benefics,_natural_malefics = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return __subha_yoga_calculation(chart_1d, _natural_benefics, _natural_malefics, use_affliction_check, include_rahu_ketu_aspecting)
def __subha_yoga_calculation(chart_1d,_natural_benefics,_natural_malefics,use_affliction_check,include_rahu_ketu_aspecting):
    """
    Subha Yoga
      Present if either:
        (1) Lagna has benefics and is NOT affected by malefics, OR
        (2) Lagna is surrounded by benefics (benefics in BOTH 12th and 2nd) and lagna is NOT affected by malefics.
      Note: In your simplified version, "not affected" can be enforced via "only benefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by malefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only benefics" conditions in the tested houses.
      - include_rahu_ketu_aspecting (bool): If True, consider Rahu/Ketu aspects (5th, 9th, and 7th).
    TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Subha Yoga is present, False otherwise.
    """
    # Build p->h mapping
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L = p_to_h[const._ascendant_symbol]
    def planets_in_house(h):
        return planets_in_raasi(h,p_to_h,exclude_lagna=True)
    # --- Aspect model: Graha Drishti (sign-based; no degrees needed) ---
    # All planets aspect 7th (opposition).
    # Mars: +4th, +8th; Jupiter: +5th, +9th; Saturn: +3rd, +10th.
    # Rahu/Ketu: many traditions accept 5th/9th + 7th; controlled via flag.
    def malefic_aspect_targets(p, h):
        targets = {(h + const.HOUSE_7) % 12}  # 7th
        if p == const.MARS_ID:  # Mars
            targets |= {(h + const.HOUSE_4) % 12, (h + const.HOUSE_8) % 12}
        elif p == const.SATURN_ID:  # Saturn
            targets |= {(h + const.HOUSE_3) % 12, (h + const.HOUSE_10) % 12}
        elif p in (const.RAHU_ID, const.KETU_ID) and include_rahu_ketu_aspecting:  # Rahu/Ketu aspects
            targets |= {(h + const.HOUSE_5) % 12, (h + const.HOUSE_9) % 12}  # 5th, 9th
        return targets

    def house_afflicted_by_malefics(target_h):
        # Occupancy by malefics
        if planets_in_house(target_h) & _natural_malefics:
            return True
        # Graha drishti onto target
        for p, h in p_to_h.items():
            if p in _natural_malefics:
                if target_h in malefic_aspect_targets(p, h):
                    return True
        # Pāpa-kartari hemming (malefics in BOTH 12th and 2nd from target)
        h12 = (target_h - 1) % 12
        h2 = (target_h + 1) % 12
        if (planets_in_house(h12) & _natural_malefics) and (planets_in_house(h2) & _natural_malefics):
            return True
        return False

    # --- “Only benefics” helpers (your simplified enforcement) ---
    def house_has_only_benefics(h):
        ps = set(planets_in_house(h))
        return len(ps) > 0 and ps.issubset(_natural_benefics)

    def house_is_strictly_unafflicted(h):
        # Unafflicted means: no malefics *occupying*, no malefic *aspects*, and not *hemmed* by malefics.
        return not house_afflicted_by_malefics(h)

    # Condition (1): Lagna has ONLY benefics AND lagna is NOT afflicted
    cond1_only_benefics = house_has_only_benefics(L)
    cond1_unafflicted = house_is_strictly_unafflicted(L) if use_affliction_check else True
    cond1 = cond1_only_benefics and cond1_unafflicted

    # Condition (2): Lagna SURROUNDED by ONLY benefics (both flanks) AND lagna is NOT afflicted
    h12 = (L - 1) % 12
    h2 = (L + 1) % 12

    left_only_benefics = house_has_only_benefics(h12)
    right_only_benefics = house_has_only_benefics(h2)
    cond2_unafflicted = house_is_strictly_unafflicted(L) if use_affliction_check else True
    cond2 = left_only_benefics and right_only_benefics and cond2_unafflicted
    return cond1 or cond2
        
def subha_yoga_from_planet_positions(planet_positions, use_affliction_check=False, include_rahu_ketu_aspecting=True):
    """
    Subha Yoga
      Present if either:
        (1) Lagna has benefics and is NOT affected by malefics, OR
        (2) Lagna is surrounded by benefics (benefics in BOTH 12th and 2nd) and lagna is NOT affected by malefics.
      Note: In your simplified version, "not affected" can be enforced via "only benefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by malefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only benefics" conditions in the tested houses.
      - include_rahu_ketu_aspecting (bool): If True, consider Rahu/Ketu aspects (5th, 9th, and 7th).
    TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Subha Yoga is present, False otherwise.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return subha_yoga(chart_1d, use_affliction_check=use_affliction_check, include_rahu_ketu_aspecting=include_rahu_ketu_aspecting)
def subha_yoga(chart_1d, use_affliction_check=False, include_rahu_ketu_aspecting=True):
    """
    Subha Yoga
      Present if either:
        (1) Lagna has benefics and is NOT affected by malefics, OR
        (2) Lagna is surrounded by benefics (benefics in BOTH 12th and 2nd) and lagna is NOT affected by malefics.
      Note: In your simplified version, "not affected" can be enforced via "only benefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by malefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only benefics" conditions in the tested houses.
      - include_rahu_ketu_aspecting (bool): If True, consider Rahu/Ketu aspects (5th, 9th, and 7th).
    TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Subha Yoga is present, False otherwise.
    """
    _natural_benefics = {3, 4, 5}
    # Malefics: Sun(0), Mars(2), Saturn(6), Rahu(7), Ketu(8)
    _natural_malefics = {0, 2, 6, 7, 8}
    return __subha_yoga_calculation(chart_1d, _natural_benefics, _natural_malefics, use_affliction_check, include_rahu_ketu_aspecting)
def _asubha_yoga_calculation(chart_1d,_natural_benefics,_natural_malefics, use_affliction_check=False):
    """
        TODO: Need to check use_affliction_check algorithm=True
    """
    # Build p->h mapping
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L = p_to_h[const._ascendant_symbol]
    def planets_in_house(h):
        return planets_in_raasi(h,p_to_h,exclude_lagna=True)
    # --- Aspect model: Graha Drishti (sign-based; no degrees needed) ---
    # All planets aspect 7th (opposition).
    # Mars: +4th, +8th; Jupiter: +5th, +9th; Saturn: +3rd, +10th.
    # Rahu/Ketu: many traditions accept 5th/9th + 7th; controlled via flag.
    def benefic_aspect_targets(p, h):
        targets = {(h + const.HOUSE_7) % 12}  # 7th
        if p == const.JUPITER_ID:  # Jupiter (benefic; here for completeness if you want to use later)
            targets |= {(h + const.HOUSE_5) % 12, (h + const.HOUSE_9) % 12}
        return targets

    def house_afflicted_by_benefics(target_h):
        # Occupancy by benefics
        if planets_in_house(target_h) & _natural_benefics:
            return True
        # Graha drishti onto target
        for p, h in p_to_h.items():
            if p in _natural_benefics:
                if target_h in benefic_aspect_targets(p, h):
                    return True
        # subha-kartari hemming (benefics in BOTH 12th and 2nd from target)
        h12 = (target_h - 1) % 12
        h2 = (target_h + 1) % 12
        if (planets_in_house(h12) & _natural_benefics) and (planets_in_house(h2) & _natural_benefics):
            return True
        return False

    # --- “Only malefics” helpers (your simplified enforcement) ---
    def house_has_only_malefics(h):
        ps = set(planets_in_house(h))
        return len(ps) > 0 and ps.issubset(_natural_malefics)

    def house_is_strictly_unafflicted(h):
        # Unafflicted means: no malefics *occupying*, no benefic *aspects*, and not *hemmed* by benefics.
        return not house_afflicted_by_benefics(h)

    # Condition (1): Lagna has ONLY benefics AND lagna is NOT afflicted
    cond1_only_malefics = house_has_only_malefics(L)
    cond1_unafflicted = house_is_strictly_unafflicted(L) if use_affliction_check else True
    cond1 = cond1_only_malefics and cond1_unafflicted

    # Condition (2): Lagna SURROUNDED by ONLY malefics (both flanks) AND lagna is NOT afflicted
    h12 = (L - 1) % 12
    h2 = (L + 1) % 12

    left_only_malefics = house_has_only_malefics(h12)
    right_only_malefics = house_has_only_malefics(h2)
    cond2_unafflicted = house_is_strictly_unafflicted(L) if use_affliction_check else True
    cond2 = left_only_malefics and right_only_malefics and cond2_unafflicted
    return cond1 or cond2
    
def asubha_yoga(chart_1d, use_affliction_check=False):
    """
    Asubha Yoga
      Present if either:
        (1) Lagna has malenefics and is NOT affected by benefics, OR
        (2) Lagna is surrounded by malefics (malefics in BOTH 12th and 2nd) and lagna is NOT affected by benefics.
      Note: In your simplified version, "not affected" can be enforced via "only malefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by benefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only malefics" conditions in the tested houses.
        TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Asubha Yoga is present, False otherwise.
    """
    _natural_benefics = {3, 4, 5}
    # Malefics: Sun(0), Mars(2), Saturn(6), Rahu(7), Ketu(8)
    _natural_malefics = {0, 2, 6, 7, 8}
    return _asubha_yoga_calculation(chart_1d, _natural_benefics, _natural_malefics,use_affliction_check=use_affliction_check)
def asubha_yoga_from_planet_positions(planet_positions,use_affliction_check=False):
    """ Asubha Yoga: If lagna has malefics or has “paapa kartari” – malefics in 12th and 2nd """
    """
        TODO: Need to check use_affliction_check algorithm=True
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return asubha_yoga(chart_1d, use_affliction_check=use_affliction_check)
def asubha_yoga_from_jd_place(jd,place,divisional_chart_factor=1, use_affliction_check=False, include_rahu_ketu_aspecting=True):
    """
    Subha Yoga
      Present if either:
        (1) Lagna has benefics and is NOT affected by malefics, OR
        (2) Lagna is surrounded by benefics (benefics in BOTH 12th and 2nd) and lagna is NOT affected by malefics.
      Note: In your simplified version, "not affected" can be enforced via "only benefics" in the tested houses.
    Parameters:
      - use_affliction_check (bool): If True, compute "not affected by malefics" using occupancy, aspects, and hemming.
        If False, rely solely on "only benefics" conditions in the tested houses.
      - include_rahu_ketu_aspecting (bool): If True, consider Rahu/Ketu aspects (5th, 9th, and 7th).
    TODO: Need to check use_affliction_check algorithm=True
    Returns:
      - bool: True if Subha Yoga is present, False otherwise.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    _natural_benefics,_natural_malefics = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _asubha_yoga_calculation(chart_1d, _natural_benefics, _natural_malefics, use_affliction_check=False)
def gaja_kesari_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ 
        BVR1 - Gaja-Kesari Yoga: If (1) Jupiter is in a quadrant from Moon, (2) a benefic planet
        conjoins or aspects Jupiter, and, (3) Jupiter is not debilitated or combust or in an
        enemy’s house
        NOTE: Since only chart is given:
            2. benefic is assumed to only mercury,jupiter,venus. Mercury if alone or jupiter/venus
            3. combustion if Jupiter and Sun in same house.
        
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _gaja_kesari_yoga_calculation(planet_positions=planet_positions,natural_benefics=_natural_benefics)
def gaja_kesari_yoga(chart_1d):
    """ 
        BVR1 - Gaja-Kesari Yoga: If (1) Jupiter is in a quadrant from Moon, (2) a benefic planet
        conjoins or aspects Jupiter, and, (3) Jupiter is not debilitated or combust or in an
        enemy’s house
        NOTE: Since only chart is given:
            2. benefic is assumed to only mercury,jupiter,venus. Mercury if alone or jupiter/venus
            3. combustion if Jupiter and Sun in same house.
        
    """
    return _gaja_kesari_yoga_calculation(chart_1d)    
def _gaja_kesari_yoga_calculation(chart_1d=None,planet_positions=None,natural_benefics=None):
    """ 
        BVR1 - Gaja-Kesari Yoga: If (1) Jupiter is in a quadrant from Moon, (2) a benefic planet
        conjoins or aspects Jupiter, and, (3) Jupiter is not debilitated or combust or in an
        enemy’s house
        NOTE: Since only chart is given:
            2. benefic is assumed to only mercury,jupiter,venus. Mercury if alone or jupiter/venus
            3. combustion if Jupiter and Sun in same house.
        
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # Condition 1 - Jupiter is in a quadrant from Moon
    jupiter_house = p_to_h[const.JUPITER_ID]
    chk1 = jupiter_house in quadrants_of_the_house(p_to_h[const.MOON_ID])
    if not chk1:
        return False
    # Condition 2 - a benefic planet conjoins or aspects Jupiter
    # Check 2.1 - benefic planet conjoins jupiter
    chk21 = any([p_to_h[p]==p_to_h[const.JUPITER_ID] for p in _natural_benefics])
    bpj = house.aspected_planets_of_the_planet(chart_1d, const.JUPITER_ID)
    # Check 2.2 benefics aspecting jupiter
    chk22 = [nb for nb in _natural_benefics if nb in bpj]
    chk2 = chk21 or chk22
    if not chk2:
        return False
    # Condition 3 - Jupiter is not debilitated or combust or in an enemy’s house
    # Condition 3.1 Jupiter is not debilitated or in an enemy's house
    chk31 = utils.is_planet_strong(const.JUPITER_ID, jupiter_house, include_neutral_samam=True)
    #Condition 3.2" - Jupiter is not combust
    # If provided only chart_1d - use if Jupiter and Sun in same house
    # If provided planet_positions then use charts.planets_in_combustion(planet_positions)
    if planet_positions is not None:
        combustion_planets = charts.planets_in_combustion(planet_positions)
    else:
        combustion_planets = [const.JUPITER_ID] if p_to_h[const.JUPITER_ID]==p_to_h[const.SUN_ID] else []
    chk32 = const.JUPITER_ID not in combustion_planets
    chk3 = chk31 and chk32
    chk = chk1 and chk2 and chk3
    return chk    
def gaja_kesari_yoga_from_planet_positions(planet_positions):
    """ 
        BVR1 - Gaja-Kesari Yoga: If (1) Jupiter is in a quadrant from Moon, (2) a benefic planet
        conjoins or aspects Jupiter, and, (3) Jupiter is not debilitated or combust or in an
        enemy’s house
        NOTE: Since only chart is given:
            2. benefic is assumed to only mercury,jupiter,venus. Mercury if alone or jupiter/venus
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return gaja_kesari_yoga(chart_1d)
def guru_mangala_yoga_from_planet_positions(planet_positions):
    """ Guru-Mangala Yoga: If Jupiter and Mars are together or in the 7th house from each other """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return guru_mangala_yoga(chart_1d)
def guru_mangala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ Guru-Mangala Yoga: If Jupiter and Mars are together or in the 7th house from each other """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return guru_mangala_yoga_from_planet_positions(planet_positions)
def guru_mangala_yoga(chart_1d):
    """ Guru-Mangala Yoga: If Jupiter and Mars are together or in the 7th house from each other """
    #p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    gmy1 = p_to_h[const.MARS_ID]==p_to_h[const.JUPITER_ID]
    gmy2 = p_to_h[const.MARS_ID]==(p_to_h[const.JUPITER_ID]+const.HOUSE_7)%12
    gmy3 = p_to_h[const.JUPITER_ID]==(p_to_h[const.MARS_ID]+const.HOUSE_7)%12
    return  gmy1 or gmy2 or gmy3
def amala_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-13 Amala Yoga: If there are only natural benefics in the 10th house from lagna or Moon """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return _amala_yoga_calculation(chart_1d, natural_benefics=natural_benefics)
def _amala_yoga_calculation(chart_1d,natural_benefics=None):
    """ BVR-13 Amala Yoga: If there are only natural benefics in the 10th house from lagna or Moon """
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    lagna_tenth_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_10)%12
    moon_tenth_house = (p_to_h[const.MOON_ID]+const.HOUSE_10)%12
    ay = any([p_to_h[p1]==h for p1 in _natural_benefics for h in [lagna_tenth_house,moon_tenth_house]]) #V4.8.0
    return ay
def amala_yoga(chart_1d):
    """ BVR-13 Amala Yoga: If there are only natural benefics in the 10th house from lagna or Moon """
    return _amala_yoga_calculation(chart_1d)
def amala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-13 Amala Yoga: If there are only natural benefics in the 10th house from lagna or Moon """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return amala_yoga_from_planet_positions(planet_positions, natural_benefics=_natural_benefics)
def parvata_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-14 Parvata Yoga: If (1) quadrants are occupied only by benefics and (2) the 7th and 8th houses 
        are either vacant or occupied only by benefics """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    _natural_benefics = charts.benefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _parvata_yoga_calculation(chart_1d, natural_benefics=_natural_benefics)
def parvata_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-14 Parvata Yoga: If (1) quadrants are occupied only by benefics and (2) the 7th and 8th houses 
        are either vacant or occupied only by benefics """
    return _parvata_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def _parvata_yoga_calculation(chart_1d=None,planet_positions=None,natural_benefics=None):
    """ BVR-14 Parvata Yoga: If (1) quadrants are occupied only by benefics and (2) the 7th and 8th houses 
        are either vacant or occupied only by benefics """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    asc_house = p_to_h[const._ascendant_symbol]

    quadrants = [(asc_house + i) % 12 for i in [const.HOUSE_1,const.HOUSE_4,const.HOUSE_7,const.HOUSE_10]]
    houses_7_8 = [(asc_house + const.HOUSE_7) % 12, (asc_house + const.HOUSE_8) % 12]

    # Helper function to check if a house contains ONLY benefics or is empty
    def house_has_only_benefics_or_empty(house_index):
        p_ids = planets_in_raasi(house_index,p_to_h,exclude_lagna=True) # V4.8.0
        if not p_ids:return True
        _is_clean = all(pid in _natural_benefics for pid in p_ids)
        return _is_clean
    # --- CHK1: Quadrants occupied ONLY by benefics ---
    # Note: Traditional Parvata Yoga usually implies quadrants must not be empty 
    # AND must only have benefics. If they can be empty, use is_clean.
    py1 = all(house_has_only_benefics_or_empty(q) for q in quadrants)
    py2 = all(house_has_only_benefics_or_empty(h) for h in houses_7_8)
    return py1 and py2
def parvata_yoga(chart_1d):
    """ BVR-14 Parvata Yoga: If (1) quadrants are occupied only by benefics and (2) the 7th and 8th houses 
        are either vacant or occupied only by benefics """
    return _parvata_yoga_calculation(chart_1d)
def kaahala_yoga_from_planet_positions(planet_positions):
    """ BVR-15 Kaahala Yoga: If (1) the 4th lord and Jupiter are in mutual quadrants and (2) lagna lord is strong """
    return kaahala_yoga(planet_positions=planet_positions)
def kaahala_yoga(chart_1d=None,planet_positions=None):
    """ BVR-15 Kaahala Yoga: If (1) the 4th lord and Jupiter are in mutual quadrants and (2) lagna lord is strong """
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    if planet_positions_available:
        fourth_lord = house.house_owner_from_planet_positions(planet_positions,(asc_house+const.HOUSE_4)%12)
        lagna_lord = house.house_owner_from_planet_positions(planet_positions,asc_house)
    else:
        fourth_lord = house.house_owner(chart_1d,(asc_house+const.HOUSE_4)%12)
        lagna_lord = house.house_owner(chart_1d,asc_house)
    ky1 = ( p_to_h[fourth_lord] in quadrants_of_the_house(p_to_h[const.JUPITER_ID]) or 
            p_to_h[const.JUPITER_ID] in quadrants_of_the_house(p_to_h[fourth_lord]) )
    if not ky1:
        return False
    ky2 = utils.is_planet_strong(lagna_lord,asc_house,include_neutral_samam=True)
    return ky1 and ky2
def kaahala_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-15 Kaahala Yoga: If (1) the 4th lord and Jupiter are in mutual quadrants and (2) lagna lord is strong """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return kaahala_yoga(planet_positions=planet_positions)
def _chaamara_yoga_calculation(chart_1d=None,planet_positions=None,natural_benefics=None):
    """ Chaamara Yoga: If the lagna lord is exalted in a quadrant with Jupiter’s aspect or
        two benefics join in 7th, 9th or 10th """
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    targets = ((asc_house + const.HOUSE_7) % 12, (asc_house + const.HOUSE_9) % 12, (asc_house + const.HOUSE_10) % 12)    
    two_benefics_join = any(
        sum((p in _natural_benefics) for p, h in p_to_h.items() if isinstance(p, int) and h == t) >= 2
        for t in targets
    )
    if two_benefics_join:
        return True
    if planet_positions_available:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions,asc_house)
    else:
        lagna_lord = house.house_owner(chart_1d,asc_house)
    lagna_lord_house = p_to_h[lagna_lord]
    lagna_lord_in_kendra = lagna_lord_house in quadrants_of_the_house(asc_house)
    lagna_lord_is_exalted = utils.is_planet_in_exalation(lagna_lord, lagna_lord_house, planet_positions)
    jupiter_aspected_houses = [h%12 for h in house.graha_drishti_from_chart(chart_1d)[1][const.JUPITER_ID]]
    jupiter_aspects_lagna_lord_house = lagna_lord_house in jupiter_aspected_houses
    """ If Lagna Lord is in the below common house of 3 lists then yoga condition will be satisfied"""
    return two_benefics_join or (lagna_lord_in_kendra and jupiter_aspects_lagna_lord_house and lagna_lord_is_exalted)
def chaamara_yoga(chart_1d,natural_benefics=None):
    """ Chaamara Yoga: If the lagna lord is exalted in a quadrant with Jupiter’s aspect or
        two benefics join in 7th, 9th or 10th """
    return _chaamara_yoga_calculation(chart_1d,natural_benefics=natural_benefics)
def chaamara_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ Chaamara Yoga: If the lagna lord is exalted in a quadrant with Jupiter’s aspect or
        two benefics join in 7th, 9th or 10th """
    return _chaamara_yoga_calculation(planet_positions=planet_positions,natural_benefics=natural_benefics)
def chaamara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ Chaamara Yoga: If the lagna lord is exalted in a quadrant with Jupiter’s aspect or
        two benefics join in 7th, 9th or 10th """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _chaamara_yoga_calculation(planet_positions=planet_positions, natural_benefics=_natural_benefics)
def _sankha_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-12 Sankha Yoga:
       (1.1) Lagna lord is strong AND (1.2) 5th & 6th lords are in mutual quadrants
       OR
       (2.1) Lagna lord & 10th lord are together in a movable sign AND (2.2) 9th lord is strong
    """
    # If planet_positions are provided, prefer them to derive chart_1d
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]  # house index (0..11) where Lagna falls
    # Resolve house lords (owners) of relevant houses
    if planet_positions_available:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
        fifth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_5) % 12)
        sixth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_6) % 12)
        ninth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_9) % 12)
        tenth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_10) % 12)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
        fifth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_5) % 12)
        sixth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_6) % 12)
        ninth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_9) % 12)
        tenth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_10) % 12)
    # --- (1.1) Lagna lord strong ---
    # Evaluate strength at the lagna lord's CURRENT placement (not necessarily asc_house)
    lagna_lord_house = p_to_h[lagna_lord]
    ky3 = utils.is_planet_strong(lagna_lord, lagna_lord_house, include_neutral_samam=False)
    # --- (1.2) 5th & 6th lords in mutual quadrants ---
    fifth_lord_house  = p_to_h[fifth_lord]
    sixth_lord_house  = p_to_h[sixth_lord]
    # Mutual kendra: each is in the other's quadrant. Using your helper for clarity.
    ky1 = fifth_lord_house in quadrants_of_the_house(sixth_lord_house)
    ky2 = sixth_lord_house in quadrants_of_the_house(fifth_lord_house)
    
    # --- (2.2) 9th lord strong ---
    ninth_lord_house = p_to_h[ninth_lord]
    ky4 = utils.is_planet_strong(ninth_lord, ninth_lord_house, include_neutral_samam=False)
    # --- (2.1) Lagna lord & 10th lord together in a MOVABLE SIGN ---
    tenth_lord_house = p_to_h[tenth_lord]
    conj_house = lagna_lord_house
    ky5_conj = (lagna_lord_house == tenth_lord_house)
    conj_sign_index = (asc_house + conj_house) % 12
    ky5_mov = (conj_sign_index in const.movable_signs)  # e.g., {0,3,6,9} = Aries,Cancer,Libra,Capricorn
    ky5 = ky5_conj and ky5_mov
    # Final decision: (1.1 & 1.2) OR (2.1 & 2.2)
    return (ky1 and ky2 and ky3) or (ky4 and ky5)
def sankha_yoga_from_planet_positions(planet_positions):
    """ BVR-12 Sankha Yoga: If (1) lagna lord is strong and (2) 5th and 6th lords are in mutual
        quadrants, then this yoga is present. Alternately, this yoga is present if (1) lagna lord
        and 10th lord are together in a movable sign and (2) the 9th lord is strong. """
    return _sankha_yoga_calculation(planet_positions=planet_positions)
def sankha_yoga(chart_1d):
    """ BVR-12 Sankha Yoga: If (1) lagna lord is strong and (2) 5th and 6th lords are in mutual
        quadrants, then this yoga is present. Alternately, this yoga is present if (1) lagna lord
        and 10th lord are together in a movable sign and (2) the 9th lord is strong. """
    return _sankha_yoga_calculation(chart_1d=chart_1d)
def sankha_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-12 Sankha Yoga: If (1) lagna lord is strong and (2) 5th and 6th lords are in mutual
        quadrants, then this yoga is present. Alternately, this yoga is present if (1) lagna lord
        and 10th lord are together in a movable sign and (2) the 9th lord is strong. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankha_yoga_calculation(planet_positions=planet_positions)
def _bheri_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-45 Bheri Yoga:
       Path A: (1) 9th lord is strong AND (2) 1st, 2nd, 7th, and 12th houses are occupied by planets
       OR
       Path B: (1) 9th lord is strong AND (2) Jupiter, Venus, and Lagna lord are in mutual quadrants
    """
    # If planet_positions are provided, prefer them to derive chart_1d
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]  # house index (0..11) where Lagna falls
    # Resolve house lords
    if planet_positions_available:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
        ninth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_9) % 12)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
        ninth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_9) % 12)
    # planet_ids for Sun to Ketu (skipping lagna.
    planet_ids = [p for p in p_to_h.keys() if isinstance(p, int)]  # exclude 'L'
    # --- Strength checks ---
    ninth_lord_house = p_to_h[ninth_lord]
    """ BV Raman data passes only with >= NEUTRAL_SAMAM is considered strong """
    is_ninth_strong = utils.is_planet_strong(ninth_lord, ninth_lord_house, include_neutral_samam=True)
    # --- Path A: 1st, 2nd, 7th, 12th houses occupied by planets ---
    def house_has_planet(h_idx):
        return any(p_to_h[p] == h_idx for p in planet_ids)
    # 1st, 2nd, 7th, 12th relative to Lagna
    required_houses = [(asc_house+h)%12 for h in [const.HOUSE_1, const.HOUSE_2, const.HOUSE_7, const.HOUSE_12]]
    are_houses_occupied = all(house_has_planet(h) for h in required_houses)
    # --- Path B: Jupiter, Venus, and Lagna lord are in mutual quadrants (pairwise mutual) ---
    jup_house = p_to_h[const.JUPITER_ID]
    ven_house = p_to_h[const.VENUS_ID]
    lagna_lord_house = p_to_h[lagna_lord]
    def are_mutual_kendras(h1, h2):
        return (h1 in quadrants_of_the_house(h2)) and (h2 in quadrants_of_the_house(h1))
    by_mutual_quadrants = (
        are_mutual_kendras(jup_house, ven_house) and
        are_mutual_kendras(jup_house, lagna_lord_house) and
        are_mutual_kendras(ven_house, lagna_lord_house)
    )
    # Final decision: Path A OR Path B
    return (is_ninth_strong and are_houses_occupied) or (is_ninth_strong and by_mutual_quadrants)
def bheri_yoga_from_planet_positions(planet_positions):
    """ BVR-45 Bheri Yoga:
       Path A: (1) 9th lord is strong AND (2) 1st, 2nd, 7th, and 12th houses are occupied by planets
       OR
       Path B: (1) 9th lord is strong AND (2) Jupiter, Venus, and Lagna lord are in mutual quadrants
    """
    return _bheri_yoga_calculation(planet_positions=planet_positions)
def bheri_yoga(chart_1d):
    """ BVR-45 Bheri Yoga:
       Path A: (1) 9th lord is strong AND (2) 1st, 2nd, 7th, and 12th houses are occupied by planets
       OR
       Path B: (1) 9th lord is strong AND (2) Jupiter, Venus, and Lagna lord are in mutual quadrants
    """
    return _bheri_yoga_calculation(chart_1d=chart_1d)
def bheri_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """Bheri Yoga:
       Path A: (1) 9th lord is strong AND (2) 1st, 2nd, 7th, and 12th houses are occupied by planets
       OR
       Path B: (1) 9th lord is strong AND (2) Jupiter, Venus, and Lagna lord are in mutual quadrants
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bheri_yoga_calculation(planet_positions=planet_positions)
def _mridanga_yoga_calculation(chart_1d=None,planet_positions=None):
    """ BVR-46 Mridanga Yoga: If (1) there are planets in own and exaltation signs in quadrants
        and trines and (2) lagna lord is strong. """
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    quadrants = house.quadrants_of_the_raasi(asc_house)
    trines = house.trines_of_the_raasi(asc_house)
    own_exalted_quadrant = any((p_to_h[p] in quadrants) and const.house_strengths_of_planets[p][p_to_h[p]] > const._FRIEND for p in SUN_TO_KETU)
    own_exalted_trine = any((p_to_h[p] in trines) and const.house_strengths_of_planets[p][p_to_h[p]] > const._FRIEND for p in SUN_TO_KETU)
    if planet_positions_available:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions,asc_house)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
    lagna_lord_is_strong = const.house_strengths_of_planets[lagna_lord][p_to_h[lagna_lord]] > const._FRIEND
    return own_exalted_quadrant and own_exalted_trine and lagna_lord_is_strong
def mridanga_yoga(chart_1d):
    """ BVR-46 Mridanga Yoga: If (1) there are planets in own and exaltation signs in quadrants
        and trines and (2) lagna lord is strong. """
    return _mridanga_yoga_calculation(chart_1d=chart_1d)
def mridanga_yoga_from_planet_positions(planet_positions):
    """ BVR-46 Mridanga Yoga: If (1) there are planets in own and exaltation signs in quadrants
        and trines and (2) lagna lord is strong. """
    return _mridanga_yoga_calculation(planet_positions=planet_positions)
def mridanga_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-46 Mridanga Yoga: If (1) there are planets in own and exaltation signs in quadrants
        and trines and (2) lagna lord is strong. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mridanga_yoga_calculation(planet_positions=planet_positions)
def _sreenaatha_yoga_calculation(chart_1d=None,planet_positions=None):
    """ BVR-31 Sreenaatha Yoga: If (1) the 7th lord is exalted in 10th and (2) 10th lord is with 9th lord. """
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    if planet_positions_available:
        seventh_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_7) % 12)
        ninth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_9) % 12)
        tenth_lord = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_10) % 12)        
    else:
        seventh_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_7) % 12)
        ninth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_9) % 12)
        tenth_lord = house.house_owner(chart_1d, (asc_house + const.HOUSE_10) % 12)
    seventh_lord_in_tenth = p_to_h[seventh_lord]==(asc_house+const.HOUSE_10)%12
    seventh_lord_exalted = utils.is_planet_in_exalation(seventh_lord, (asc_house+const.HOUSE_10)%12, planet_positions)
    ninth_lord_with_tenth_lord = p_to_h[ninth_lord] == p_to_h[tenth_lord]
    return (seventh_lord_in_tenth and seventh_lord_exalted) and ninth_lord_with_tenth_lord
def sreenaatha_yoga_from_planet_positions(planet_positions):
    """ BVR-31 Sreenaatha Yoga: If (1) the 7th lord is exalted in 10th and (2) 10th lord is with 9th lord. """
    return _sreenaatha_yoga_calculation(planet_positions=planet_positions)
def sreenaatha_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-31 Sreenaatha Yoga: If (1) the 7th lord is exalted in 10th and (2) 10th lord is with 9th lord. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sreenaatha_yoga_calculation(planet_positions=planet_positions)
def sreenaatha_yoga(chart_1d):
    """ BVR-31 Sreenaatha Yoga: If (1) the 7th lord is exalted in 10th and (2) 10th lord is with 9th lord. """
    return _sreenaatha_yoga_calculation(chart_1d=chart_1d)
def _matsya_yoga_calculation(chart_1d=None, planet_positions=None,
                              natural_benefics=None,
                              natural_malefics=None,
                              method=None,   # 1 = 'bv_raman' or 2 = 'parashara'
                              strict_exclusive=True):
    """ BVR-53 Matsya Yoga - 2 methods
    - BV Raman (300 Important Combinations): (method=1)
        (1) Malefics in Lagna AND 9th (optionally ONLY malefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)

    - Parasari / Jātaka Parijāta stream (common modern presentation): (method=2) PVR Book.
        (1) Benefics in Lagna AND 9th (optionally ONLY benefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)
    """
    if method is None: method = const.matsya_yoga_method
    # Prefer planet_positions to derive chart_1d if available
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # Absolute indices for involved houses
    lagna_abs  = asc_house
    fifth_abs  = (asc_house + const.HOUSE_5) % 12
    ninth_abs  = (asc_house + const.HOUSE_9) % 12
    fourth_abs = (asc_house + const.HOUSE_4) % 12
    eighth_abs = (asc_house + const.HOUSE_8) % 12

    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    _natural_benefics = set(_natural_benefics)

    # --- Malefics set (override or default) ---
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    # Helper: occupants of a given absolute house
    def occupants(abs_house_idx):
        return [p for p in SUN_TO_KETU if p_to_h[p] == abs_house_idx]

    # Occupancy sets
    occ_lagna  = set(occupants(lagna_abs))
    occ_fifth  = set(occupants(fifth_abs))
    occ_ninth  = set(occupants(ninth_abs))
    occ_fourth = set(occupants(fourth_abs))
    occ_eighth = set(occupants(eighth_abs))

    # --- (1) Lagna & 9th, based on authority ---
    if method == 1:
        lagna_ok = (len(occ_lagna & _natural_malefics) > 0) and (not strict_exclusive or occ_lagna <= _natural_malefics)
        ninth_ok = (len(occ_ninth & _natural_malefics) > 0) and (not strict_exclusive or occ_ninth <= _natural_malefics)
    else:  # method == 2  => 'parashara'
        lagna_ok = (len(occ_lagna & _natural_benefics) > 0) and (not strict_exclusive or occ_lagna <= _natural_benefics)
        ninth_ok = (len(occ_ninth & _natural_benefics) > 0) and (not strict_exclusive or occ_ninth <= _natural_benefics)
    cond1 = lagna_ok and ninth_ok

    # --- (2) 5th must contain BOTH benefic and malefic planets
    cond2 = (len(occ_fifth & _natural_benefics) > 0) and (len(occ_fifth & _natural_malefics) > 0)

    # --- (3) 4th & 8th ONLY malefics (and present)
    cond3 = (len(occ_fourth) > 0 and occ_fourth <= _natural_malefics) and \
            (len(occ_eighth) > 0 and occ_eighth <= _natural_malefics)

    return cond1 and cond2 and cond3
def matsya_yoga(chart_1d,method=None,natural_benefics=None,natural_malefics=None):
    """ BVR-53 Matsya Yoga - 2 methods
    - BV Raman (300 Important Combinations): (method=1)
        (1) Malefics in Lagna AND 9th (optionally ONLY malefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)

    - Parasari / Jātaka Parijāta stream (common modern presentation): (method=2) PVR Book.
        (1) Benefics in Lagna AND 9th (optionally ONLY benefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)
    """
    if method is None: method = const.matsya_yoga_method
    return _matsya_yoga_calculation(chart_1d=chart_1d,method=method,natural_benefics=natural_benefics,
                                    natural_malefics=natural_malefics)
def matsya_yoga_from_planet_positions(planet_positions,method=None,
                                      natural_benefics=None,natural_malefics=None):
    """ BVR-53 Matsya Yoga - 2 methods
    - BV Raman (300 Important Combinations): (method=1)
        (1) Malefics in Lagna AND 9th (optionally ONLY malefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)

    - Parasari / Jātaka Parijāta stream (common modern presentation): (method=2) PVR Book.
        (1) Benefics in Lagna AND 9th (optionally ONLY benefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)
    """
    if method is None: method = const.matsya_yoga_method
    return _matsya_yoga_calculation(planet_positions=planet_positions,method=method,natural_benefics=natural_benefics,
                                    natural_malefics=natural_malefics)
def matsya_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ BVR-53 Matsya Yoga - 2 methods
    - BV Raman (300 Important Combinations): (method=1)
        (1) Malefics in Lagna AND 9th (optionally ONLY malefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)

    - Parasari / Jātaka Parijāta stream (common modern presentation): (method=2) PVR Book.
        (1) Benefics in Lagna AND 9th (optionally ONLY benefics if strict_exclusive=True)
        (2) 5th contains BOTH benefics AND malefics
        (3) 4th AND 8th contain ONLY malefics (and at least one in each)
    """
    if method is None: method = const.matsya_yoga_method
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics,_natural_malefics = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _matsya_yoga_calculation(planet_positions=planet_positions, natural_benefics=_natural_benefics, 
                                     natural_malefics=_natural_malefics, method=method)
def _koorma_yoga_calculation(chart_1d=None, planet_positions=None, chart_navamsa=None,
                             planet_positions_navamsa=None, natural_benefics=None,
                             natural_malefics=None, method=None):
    """ BVR-54 Koorma Yoga: 
        Conditions: 
            (1) the 5th, 6th and 7th houses are occupied by benefics who are in own, 
                exaltation or friendly navamsa signs
            (2) the 1st, 3rd and 11th houses are occupied by benefics (BVR) / malefics (PVR) 
                who are in own or exaltation signs.(BVR did not say navamsa signs for 2nd condition)
        Method = 1 BV Raman - 
            2nd condition is also for BENEFICS (not malefics) AND 
            ONLY ONE of the above two conditions required
            Condition-2 >= Friend, exalt, own Or Samam
            Note: BVR Example Chart 39 - has Moon in Pisces in Navamsa - where it is Samam
        Method = 2 PVR - 
            BOTH conditions are required and 1st for benefics and 2nd for malefics
            Condition 1 == Friend/exalt/Own and Condition 2 >= exalt/Own (No Friend)
    """
    if method is None: 
        method = const.koorma_yoga_method
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None: return False
    _natural_benefics = set(_get_natural_benefics(chart_1d, natural_benefics))
    _natural_malefics = set(const.natural_malefics if natural_malefics is None else natural_malefics)

    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h_rasi.get(const._ascendant_symbol)
    if asc_house is None:
        return False
        
    occ_rasi = lambda h: [p for p in SUN_TO_KETU if p_to_h_rasi.get(p) == h]

    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa) if chart_navamsa else None
    occ_nav = lambda h: [p for p in SUN_TO_KETU if p_to_h_nav.get(p) == h] if p_to_h_nav else []

    houses_5_6_7 = [
        (asc_house + const.HOUSE_5) % 12,
        (asc_house + const.HOUSE_6) % 12,
        (asc_house + const.HOUSE_7) % 12
    ]
    houses_1_3_11 = [
        asc_house,
        (asc_house + const.HOUSE_3) % 12,
        (asc_house + const.HOUSE_11) % 12
    ]

    if method == 1:
        # Method 1 (B.V. Raman): Either condition 1 OR condition 2 (Both for benefics)
        # Condition 1: 5th, 6th, 7th in Navamsa (>= Samam to account for Moon in Pisces in Chart 39)
        cond_1 = bool(p_to_h_nav) and all(
            (benefics := [p for p in occ_rasi(h) if p in _natural_benefics]) and 
            all(const.house_strengths_of_planets[p][p_to_h_nav[p]] >= const._NEUTRAL_SAMAM for p in benefics)
            for h in houses_5_6_7
        )
        
        # Condition 2: 1st, 3rd, 11th in Rasi (>= Samam)
        cond_2 = all(
            (benefics := [p for p in occ_rasi(h) if p in _natural_benefics]) and 
            all(const.house_strengths_of_planets[p][p_to_h_rasi[p]] >= const._NEUTRAL_SAMAM for p in benefics)
            for h in houses_1_3_11
        )
        
        return cond_1 or cond_2

    else:
        # Method 2 (PVR): Both condition 1 AND condition 2 required
        # Condition 1: 5th, 6th, 7th in Rasi by benefics (>= Friend)
        cond_1 = all(
            (benefics := [p for p in occ_rasi(h) if p in _natural_benefics]) and 
            all(const.house_strengths_of_planets[p][p_to_h_rasi[p]] >= const._FRIEND for p in benefics)
            for h in houses_5_6_7
        )
        
        # Condition 2: 1st, 3rd, 11th in Rasi by malefics (Own or Exaltation only, no Friend)
        cond_2 = all(
            (malefics := [p for p in occ_rasi(h) if p in _natural_malefics]) and 
            all(const.house_strengths_of_planets[p][p_to_h_rasi[p]] >= const._EXALTED_UCCHAM for p in malefics)
            for h in houses_1_3_11
        )
        
        return cond_1 and cond_2

def koorma_yoga(chart_1d,chart_navamsa,method=None,natural_benefics=None,natural_malefics=None):
    """ BVR-54 Koorma Yoga: 
        Conditions: 
            (1) the 5th, 6th and 7th houses are occupied by benefics who are in own, 
                exaltation or friendly navamsa signs
            (2) the 1st, 3rd and 11th houses are occupied by benefics (BVR) / malefics (PVR) 
                who are in own or exaltation signs.(BVR did not say navamsa signs for 2nd condition)
        Method = 1 BV Raman - 
            2nd condition is also for BENEFICS (not malefics) AND 
            ONLY ONE of the above two conditions required
            Condition-2 >= Friend, exalt, own Or Samam
            Note: BVR Example Chart 39 - has Moon in Pisces in Navamsa - where it is Samam
        Method = 2 PVR - 
            BOTH conditions are required and 1st for benefics and 2nd for malefics
            Condition 1 == Friend/exalt/Own and Condition 2 >= exalt/Own (No Friend)
    """
    if method is None: method = const.koorma_yoga_method
    return _koorma_yoga_calculation(chart_1d=chart_1d,chart_navamsa=chart_navamsa,
                                    method=method,natural_benefics=natural_benefics,
                                    natural_malefics=natural_malefics)
def koorma_yoga_from_planet_positions(planet_positions,planet_positions_navamsa,method=None,
                                      natural_benefics=None,natural_malefics=None):
    """ BVR-54 Koorma Yoga: 
        Conditions: 
            (1) the 5th, 6th and 7th houses are occupied by benefics who are in own, 
                exaltation or friendly navamsa signs
            (2) the 1st, 3rd and 11th houses are occupied by benefics (BVR) / malefics (PVR) 
                who are in own or exaltation signs.(BVR did not say navamsa signs for 2nd condition)
        Method = 1 BV Raman - 
            2nd condition is also for BENEFICS (not malefics) AND 
            ONLY ONE of the above two conditions required
            Condition-2 >= Friend, exalt, own Or Samam
            Note: BVR Example Chart 39 - has Moon in Pisces in Navamsa - where it is Samam
        Method = 2 PVR - 
            BOTH conditions are required and 1st for benefics and 2nd for malefics
            Condition 1 == Friend/exalt/Own and Condition 2 >= exalt/Own (No Friend)
    """
    if method is None: method = const.koorma_yoga_method
    return _koorma_yoga_calculation(planet_positions=planet_positions,
                                    planet_positions_navamsa=planet_positions_navamsa,
                                    method=method,natural_benefics=natural_benefics,
                                    natural_malefics=natural_malefics)
def koorma_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ BVR-54 Koorma Yoga: 
        Conditions: 
            (1) the 5th, 6th and 7th houses are occupied by benefics who are in own, 
                exaltation or friendly navamsa signs
            (2) the 1st, 3rd and 11th houses are occupied by benefics (BVR) / malefics (PVR) 
                who are in own or exaltation signs.(BVR did not say navamsa signs for 2nd condition)
        Method = 1 BV Raman - 
            2nd condition is also for BENEFICS (not malefics) AND 
            ONLY ONE of the above two conditions required
            Condition-2 >= Friend, exalt, own Or Samam
            Note: BVR Example Chart 39 - has Moon in Pisces in Navamsa - where it is Samam
        Method = 2 PVR - 
            BOTH conditions are required and 1st for benefics and 2nd for malefics
            Condition 1 == Friend/exalt/Own and Condition 2 >= exalt/Own (No Friend)
    """
    if method is None: method = const.koorma_yoga_method
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_9 = charts.divisional_chart(jd,place,divisional_chart_factor=9)
    _natural_benefics,_natural_malefics = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _koorma_yoga_calculation(planet_positions=planet_positions, planet_positions_navamsa=pp_9,
                                    natural_benefics=_natural_benefics,
                                     natural_malefics=_natural_malefics, method=method)
def _khadga_yoga_calculation(chart_1d=None, planet_positions=None):
    """ Khadga Yoga: If (1) the 2nd lord is in the 9th house, (2) the 9th lord is in the 2nd
        house, and, (3) lagna lord is in a quadrant or a trine. """
    
    # 1. Standardize Inputs
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    # 2. Basic Setup
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # 3. Determine House Indices (0-11)
    # Using constants ensures consistency (e.g. const.HOUSE_2 usually maps to offset 1)
    second_house_idx = (asc_house + const.HOUSE_2) % 12
    ninth_house_idx  = (asc_house + const.HOUSE_9) % 12

    # 4. Find Lords (Prefer planet_positions for accuracy if your system distinguishes distinct states)
    if planet_positions_available:
        second_lord = house.house_owner_from_planet_positions(planet_positions, second_house_idx)
        ninth_lord  = house.house_owner_from_planet_positions(planet_positions, ninth_house_idx)
        lagna_lord  = house.house_owner_from_planet_positions(planet_positions, asc_house)
    else:
        second_lord = house.house_owner(chart_1d, second_house_idx)
        ninth_lord  = house.house_owner(chart_1d, ninth_house_idx)
        lagna_lord  = house.house_owner(chart_1d, asc_house)

    # 5. Verify Conditions
    # Cond 1 & 2: Exchange between 2nd and 9th lords
    second_lord_in_ninth_house = (p_to_h[second_lord] == ninth_house_idx) 
    ninth_lord_in_second_house = (p_to_h[ninth_lord] == second_house_idx)
    
    # Cond 3: Lagna lord in Quadrant or Trine
    # Note: 1st house is both a quadrant and a trine, set union handles overlap naturally.
    quadrants_and_trines = set(house.quadrants_of_the_raasi(asc_house) + house.trines_of_the_raasi(asc_house))
    lagna_lord_in_quadrant_or_trine = p_to_h[lagna_lord] in quadrants_and_trines

    return second_lord_in_ninth_house and ninth_lord_in_second_house and lagna_lord_in_quadrant_or_trine

def khadga_yoga_from_planet_positions(planet_positions):
    """ Khadga Yoga: If (1) the 2nd lord is in the 9th house, (2) the 9th lord is in the 2nd
        house, and, (3) lagna lord is in a quadrant or a trine. """
    return _khadga_yoga_calculation(planet_positions=planet_positions)
def khadga_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ Khadga Yoga: If (1) the 2nd lord is in the 9th house, (2) the 9th lord is in the 2nd
        house, and, (3) lagna lord is in a quadrant or a trine. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _khadga_yoga_calculation(planet_positions=planet_positions)
def khadga_yoga(chart_1d):
    """ Khadga Yoga: If (1) the 2nd lord is in the 9th house, (2) the 9th lord is in the 2nd
        house, and, (3) lagna lord is in a quadrant or a trine. """
    return _khadga_yoga_calculation(chart_1d=chart_1d)
def _kusuma_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, natural_malefics=None):
    """ BVR-52 Kusuma Yoga: If (1) lagna is in a fixed sign, (2) Venus is in a quadrant, (3) Moon is
        in a trine with a benefic, and, (4) Saturn is in the 10th house. """
    
    planet_positions_available = planet_positions is not None
    if planet_positions_available:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    # --- Benefics set (Standard Approach) ---
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # (1) Lagna is in a fixed sign
    lagna_in_fixed_sign = asc_house in const.fixed_signs
    if not lagna_in_fixed_sign:
        return False

    # (2) Venus is in a quadrant
    venus_in_quadrant = p_to_h[const.VENUS_ID] in house.quadrants_of_the_raasi(asc_house)
    if not venus_in_quadrant:
        return False

    # (4) Saturn is in the 10th house
    tenth_house_idx = (asc_house + const.HOUSE_10) % 12
    saturn_in_tenth_house = p_to_h[const.SATURN_ID] == tenth_house_idx
    if not saturn_in_tenth_house:
        return False

    # (3) Moon is in a trine with a benefic
    moon_in_trine_with_benefic = any([p_to_h[const.MOON_ID] in house.trines_of_the_raasi(p_to_h[benefic_id]) 
                                     for benefic_id in _natural_benefics])
    
    return moon_in_trine_with_benefic

def kusuma_yoga(chart_1d):
    """ BVR-52 Kusuma Yoga: If (1) lagna is in a fixed sign, (2) Venus is in a quadrant, (3) Moon is
        in a trine with a benefic, and, (4) Saturn is in the 10th house. """
    return _kusuma_yoga_calculation(chart_1d=chart_1d)

def kusuma_yoga_from_planet_positions(planet_positions):
    """ BVR-52 Kusuma Yoga: If (1) lagna is in a fixed sign, (2) Venus is in a quadrant, (3) Moon is
        in a trine with a benefic, and, (4) Saturn is in the 10th house. """
    return _kusuma_yoga_calculation(planet_positions=planet_positions)

def kusuma_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-52 Kusuma Yoga: If (1) lagna is in a fixed sign, (2) Venus is in a quadrant, (3) Moon is
        in a trine with a benefic, and, (4) Saturn is in the 10th house. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics, _natural_malefics = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _kusuma_yoga_calculation(planet_positions=planet_positions, natural_benefics=_natural_benefics, natural_malefics=_natural_malefics)

def kalaanidhi_yoga(chart_1d):
    """ BVR-49 Kalaanidhi Yoga: If (1) Jupiter is in the 2nd house or the 5th house and (2) he is
        conjoined or aspected by Mercury and Venus. """
    return _kalanidhi_yoga_calculation(chart_1d=chart_1d)

def kalaanidhi_yoga_from_planet_positions(planet_positions):
    """ BVR-49 Kalaanidhi Yoga: If (1) Jupiter is in the 2nd house or the 5th house and (2) he is
        conjoined or aspected by Mercury and Venus. """
    return _kalanidhi_yoga_calculation(planet_positions=planet_positions)

def kalaanidhi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-49 Kalaanidhi Yoga: If (1) Jupiter is in the 2nd house or the 5th house and (2) he is
        conjoined or aspected by Mercury and Venus. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kalanidhi_yoga_calculation(planet_positions=planet_positions)
def _kalpadruma_yoga_calculation(chart_1d_rasi=None, chart_1d_navamsa=None, 
                                 planet_positions_rasi=None,planet_positions_navamsa=None):
    """ BVR-47 Paarijaatha/Kalpadruma Yoga: Consider (1) lagna lord, (2) his dispositor, (3) the latter’s
        dispositor in rasi and (4) in navamsa. If all the four planets are all in quadrants, trines
        or exaltation signs. """
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d_rasi is None or chart_1d_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    
    asc_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    asc_house_navamsa = p_to_h_navamsa[const._ascendant_symbol]

    # Find the four key planets
    # 1. Lagna Lord
    if planet_positions_rasi is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions_rasi, asc_house_rasi)
        dispositor_1 = house.house_owner_from_planet_positions(planet_positions_rasi, p_to_h_rasi[lagna_lord])
        dispositor_2 = house.house_owner_from_planet_positions(planet_positions_rasi, p_to_h_rasi[dispositor_1])
    else:
        lagna_lord = house.house_owner(chart_1d_rasi, asc_house_rasi)
        dispositor_1 = house.house_owner(chart_1d_rasi, p_to_h_rasi[lagna_lord])
        dispositor_2 = house.house_owner(chart_1d_rasi, p_to_h_rasi[dispositor_1])
    if planet_positions_rasi is not None:
        dispositor_3 = house.house_owner_from_planet_positions(planet_positions_navamsa, p_to_h_navamsa[dispositor_1])
    else:
        dispositor_3 = house.house_owner(chart_1d_navamsa, p_to_h_navamsa[dispositor_1])

    all_four_planets = [lagna_lord, dispositor_1, dispositor_2, dispositor_3]
    
    # Define favorable areas (Quadrants and Trines)
    favorable_rasi = set(house.quadrants_of_the_raasi(asc_house_rasi) + house.trines_of_the_raasi(asc_house_rasi))
    favorable_navamsa = set(house.quadrants_of_the_raasi(asc_house_navamsa) + house.trines_of_the_raasi(asc_house_navamsa))

    # Condition: All four planets must be in Quadrant/Trine or Exalted in BOTH charts
    def is_well_placed(p, p_to_h, favorable_houses):
        house_idx = p_to_h[p]
        is_exalted_or_own = const.house_strengths_of_planets[p][house_idx] >= const._EXALTED_UCCHAM
        is_in_good_house = house_idx in favorable_houses
        return is_exalted_or_own or is_in_good_house

    condition_rasi = all(is_well_placed(p, p_to_h_rasi, favorable_rasi) for p in all_four_planets)
    condition_navamsa = all(is_well_placed(p, p_to_h_navamsa, favorable_navamsa) for p in all_four_planets)

    return condition_rasi and condition_navamsa

def kalpadruma_yoga(chart_1d_rasi, chart_1d_navamsa):
    """ BVR-47 Paarijaatha/Kalpadruma Yoga: Consider (1) lagna lord, (2) his dispositor, (3) the latter’s
        dispositor in rasi and (4) in navamsa. If all the four planets are all in quadrants, trines
        or exaltation signs. """
    return _kalpadruma_yoga_calculation(chart_1d_rasi=chart_1d_rasi, chart_1d_navamsa=chart_1d_navamsa)

def kalpadruma_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa):
    """ BVR-47 Paarijaatha/Kalpadruma Yoga: Consider (1) lagna lord, (2) his dispositor, (3) the latter’s
        dispositor in rasi and (4) in navamsa. If all the four planets are all in quadrants, trines
        or exaltation signs. """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _kalpadruma_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                        planet_positions_navamsa=planet_positions_navamsa)
def kalpadruma_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-47 Paarijaatha/Kalpadruma Yoga: Consider (1) lagna lord, (2) his dispositor, (3) the latter’s
        dispositor in rasi and (4) in navamsa. If all the four planets are all in quadrants, trines
        or exaltation signs. """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _kalpadruma_yoga_calculation(planet_positions_rasi=pp_rasi, 
                                        planet_positions_navamsa=pp_navamsa)
def _lagnaadhi_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, natural_malefics=None):
    """ Lagnaadhi Yoga: If (1) the 6th, 7th and 8th houses from lagna are occupied by benefics
        and (2) no malefics conjoin or aspect these planets. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # Target houses: 6th, 7th and 8th from Lagna
    yoga_houses = [const.HOUSE_6, const.HOUSE_7, const.HOUSE_8]
    target_houses = [(asc_house + mh) % 12 for mh in yoga_houses]
    # --- Determine Benefics (Same logic as your working Adhi Yoga) ---
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # Condition 1: All natural benefics must be in the 6th, 7th, or 8th from Lagna
    benefics_placed_well = all(p_to_h[pid] in target_houses for pid in _natural_benefics)
    if not benefics_placed_well:
        return False
    # Condition 2: No malefics in those same houses (conjunction check)
    if natural_malefics is None:
        _natural_malefics = const.natural_malefics # Usually [0, 2, 6, 7, 8]
    else:
        _natural_malefics = list(natural_malefics)
    malefics_in_yoga_houses = any(p_to_h[mid] in target_houses for mid in _natural_malefics)
    if malefics_in_yoga_houses:
        return False
    # Condition 3: No malefic aspects on those benefics
    for pid in _natural_benefics:
        aspected_by = house.aspected_planets_of_the_planet(chart_1d, pid)
        if any(mid in aspected_by for mid in _natural_malefics):
            return False
    return True

def lagnaadhi_yoga(chart_1d):
    """ Lagnaadhi Yoga: If (1) the 6th, 7th and 8th houses from lagna are occupied by benefics
        and (2) no malefics conjoin or aspect these planets. """
    return _lagnaadhi_yoga_calculation(chart_1d=chart_1d)

def lagnaadhi_yoga_from_planet_positions(planet_positions):
    """ Lagnaadhi Yoga: If (1) the 6th, 7th and 8th houses from lagna are occupied by benefics
        and (2) no malefics conjoin or aspect these planets. """
    return _lagnaadhi_yoga_calculation(planet_positions=planet_positions)
def lagnaadhi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _lagnaadhi_yoga_calculation(planet_positions=pp, natural_benefics=nb, natural_malefics=nm)
def _hari_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """ BVR-51 Hari Yoga (part of harihara brahma yoga): 
        If benefics occupy the 2nd, 12th and 8th houses counted from the 2nd lord. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    second_house_idx = (asc_house + const.HOUSE_2) % 12
    if planet_positions is not None:
        second_lord = house.house_owner_from_planet_positions(planet_positions, second_house_idx)
    else:
        second_lord = house.house_owner(chart_1d, second_house_idx)
    lord_pos = p_to_h[second_lord]
    target_houses = [
        (lord_pos + const.HOUSE_2) % 12, 
        (lord_pos + const.HOUSE_8) % 12, 
        (lord_pos + const.HOUSE_12) % 12
    ]
    # Determine Benefics
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # Condition: All natural benefics must be in the 2nd, 8th, or 12th from the 2nd lord
    return all(p_to_h[pid] in target_houses for pid in _natural_benefics)

def hari_yoga(chart_1d,natural_benefics=None):
    """ BVR-51 Hari Yoga (part of harihara brahma yoga): 
        If benefics occupy the 2nd, 12th and 8th houses counted from the 2nd lord. """
    return _hari_yoga_calculation(chart_1d=chart_1d,natural_benefics=natural_benefics)

def hari_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-51 Hari Yoga (part of harihara brahma yoga): 
        If benefics occupy the 2nd, 12th and 8th houses counted from the 2nd lord. """
    return _hari_yoga_calculation(planet_positions=planet_positions,natural_benefics=natural_benefics)

def hari_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-51 Hari Yoga (part of harihara brahma yoga): 
        If benefics occupy the 2nd, 12th and 8th houses counted from the 2nd lord. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _hari_yoga_calculation(planet_positions=planet_positions, natural_benefics=_natural_benefics)

def _hara_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """ BVR-51 Hara Yoga (part of harihara brahma yoga): 
    If benefics occupy the 4th, 9th and 8th houses counted from the 7th lord. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    seventh_house_idx = (asc_house + const.HOUSE_7) % 12
    if planet_positions is not None:
        seventh_lord = house.house_owner_from_planet_positions(planet_positions, seventh_house_idx)
    else:
        seventh_lord = house.house_owner(chart_1d, seventh_house_idx)
    lord_pos = p_to_h[seventh_lord]
    target_houses = [
        (lord_pos + const.HOUSE_4) % 12, 
        (lord_pos + const.HOUSE_9) % 12, 
        (lord_pos + const.HOUSE_8) % 12
    ]
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    return all(p_to_h[pid] in target_houses for pid in _natural_benefics if pid != seventh_lord)

def hara_yoga(chart_1d,natural_benefics=None):
    """ BVR-51 Hara Yoga (part of harihara brahma yoga): 
    If benefics occupy the 4th, 9th and 8th houses counted from the 7th lord. """
    return _hara_yoga_calculation(chart_1d=chart_1d,natural_benefics=natural_benefics)

def hara_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """ BVR-51 Hara Yoga (part of harihara brahma yoga): 
    If benefics occupy the 4th, 9th and 8th houses counted from the 7th lord. """
    return _hara_yoga_calculation(planet_positions=planet_positions,natural_benefics=natural_benefics)
def hara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-51 Hara Yoga (part of harihara brahma yoga): 
    If benefics occupy the 4th, 9th and 8th houses counted from the 7th lord. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _hara_yoga_calculation(planet_positions=planet_positions,natural_benefics=_natural_benefics)
def _brahma_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None,
                             method=None):
    """ BVR-51 Brahma Yoga (part of harihara brahma yoga): 
        Brahma Yoga: (Based on PVR Narasimha Rao)
        Method 1: Benefics in 4th, 10th and 11th from Lagna Lord.
        Method 2: Jupiter in quadrant from 9th lord, Venus in quadrant from 11th lord, 
                  and Mercury in quadrant from 1st or 10th lord.
    """
    if method is None: method = const.brahma_yoga_method
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_house)
        l9 = house.house_owner_from_planet_positions(planet_positions,(asc_house + const.HOUSE_9) % 12)
        l10 = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_10) % 12)
        l11 = house.house_owner_from_planet_positions(planet_positions, (asc_house + const.HOUSE_11) % 12)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
        l1 = house.house_owner(chart_1d, asc_house)
        l9 = house.house_owner(chart_1d, (asc_house + const.HOUSE_9) % 12)
        l10 = house.house_owner(chart_1d, (asc_house + const.HOUSE_10) % 12)
        l11 = house.house_owner(chart_1d, (asc_house + const.HOUSE_11) % 12)
    if method == 1:
        ll_pos = p_to_h[lagna_lord]
        m1_targets = [(ll_pos + const.HOUSE_4) % 12, (ll_pos + const.HOUSE_10) % 12, (ll_pos + const.HOUSE_11) % 12]
        _nb = _get_natural_benefics(chart_1d, natural_benefics)
        return all(p_to_h[pid] in m1_targets for pid in _nb if pid != lagna_lord)
    elif method == 2:
        ly2 = p_to_h[const.JUPITER_ID] in quadrants_of_the_house(p_to_h[l9])
        ly3 = p_to_h[const.VENUS_ID] in quadrants_of_the_house(p_to_h[l11])
        ly4_1 = p_to_h[const.MERCURY_ID] in quadrants_of_the_house(p_to_h[l1])
        ly4_2 = p_to_h[const.MERCURY_ID] in quadrants_of_the_house(p_to_h[l10])
        return ly2 and ly3 and (ly4_1 or ly4_2)
    return False
def brahma_yoga(chart_1d,natural_benefics=None,method=None):
    """ BVR-51 Brahma Yoga (part of harihara brahma yoga): 
        Brahma Yoga: (Based on PVR Narasimha Rao)
        Method 1: Benefics in 4th, 10th and 11th from Lagna Lord.
        Method 2: Jupiter in quadrant from 9th lord, Venus in quadrant from 11th lord, 
                  and Mercury in quadrant from 1st or 10th lord.
    """
    if method is None: method = const.brahma_yoga_method
    return _brahma_yoga_calculation(chart_1d=chart_1d,natural_benefics=natural_benefics,method=method)
def brahma_yoga_from_planet_positions(planet_positions,natural_benefics=None,method=None):
    """ BVR-51 Brahma Yoga (part of harihara brahma yoga): 
        Brahma Yoga: (Based on PVR Narasimha Rao)
        Method 1: Benefics in 4th, 10th and 11th from Lagna Lord.
        Method 2: Jupiter in quadrant from 9th lord, Venus in quadrant from 11th lord, 
                  and Mercury in quadrant from 1st or 10th lord.
    """
    if method is None: method = const.brahma_yoga_method
    return _brahma_yoga_calculation(planet_positions=planet_positions,natural_benefics=natural_benefics, method=method)
def brahma_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ BVR-51 Brahma Yoga (part of harihara brahma yoga): 
        Brahma Yoga: (Based on PVR Narasimha Rao)
        Method 1: Benefics in 4th, 10th and 11th from Lagna Lord.
        Method 2: Jupiter in quadrant from 9th lord, Venus in quadrant from 11th lord, 
                  and Mercury in quadrant from 1st or 10th lord.
    """
    if method is None: method = const.brahma_yoga_method
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _brahma_yoga_calculation(planet_positions=planet_positions,natural_benefics=_natural_benefics,method=method)
    
def _vishnu_yoga_calculation(chart_1d_rasi=None, chart_1d_navamsa=None, 
                             planet_positions_rasi=None, planet_positions_navamsa=None):
    """ BVR-62 Vishnu Yoga (PVR & BVR):
        BV Raman Definition:  the lord of Navamsa in which the 9th iord is placed, and the l0th lord joins the 2nd
            house in conjunction u ith the 9tk lord, Vishnu Yoga is caused.
        PVR Definition:
            1. 9th and 10th lords (from Rasi) are in the 2nd house of Rasi.
            2. The lord of the sign occupied by the 9th lord in Navamsa is also in the 2nd house of Rasi.
        both Methods appear the same
    """
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_1d_rasi is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    asc_rasi = p_to_h_rasi[const._ascendant_symbol]
    second_house_rasi = (asc_rasi + const.HOUSE_2) % 12
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d_navamsa is None: return False
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    house_9_idx = (asc_rasi + const.HOUSE_9) % 12
    house_10_idx = (asc_rasi + const.HOUSE_10) % 12
    if planet_positions_rasi is not None:
        l9 = house.house_owner_from_planet_positions(planet_positions_rasi, house_9_idx)
        navamsa_sign_idx = p_to_h_navamsa[l9]
        navamsa_dispositor = house.house_owner_from_planet_positions(planet_positions_rasi, navamsa_sign_idx)
        l10 = house.house_owner_from_planet_positions(planet_positions_rasi, house_10_idx)
    else:
        l9 = house.house_owner(chart_1d_rasi, house_9_idx)
        navamsa_sign_idx = p_to_h_navamsa[l9]
        navamsa_dispositor = house.house_owner(chart_1d_rasi, navamsa_sign_idx)
        l10 = house.house_owner(chart_1d_rasi, house_10_idx)
    cond_l9 = p_to_h_rasi[l9] == second_house_rasi
    cond_l10 = p_to_h_rasi[l10] == second_house_rasi
    cond_nav = p_to_h_rasi[navamsa_dispositor] == second_house_rasi
    return cond_l9 and cond_l10 and cond_nav
def vishnu_yoga(chart_1d_rasi,chart_1d_navamsa):
    """ BVR-62 Vishnu Yoga (PVR & BVR):
        BV Raman Definition:  the lord of Navamsa in which the 9th iord is placed, and the l0th lord joins the 2nd
            house in conjunction u ith the 9tk lord, Vishnu Yoga is caused.
        PVR Definition:
            1. 9th and 10th lords (from Rasi) are in the 2nd house of Rasi.
            2. The lord of the sign occupied by the 9th lord in Navamsa is also in the 2nd house of Rasi.
        both Methods appear the same
    """
    return _vishnu_yoga_calculation(chart_1d_rasi=chart_1d_rasi, chart_1d_navamsa=chart_1d_navamsa)
def vishnu_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa):
    """ BVR-62 Vishnu Yoga (PVR & BVR):
        BV Raman Definition:  the lord of Navamsa in which the 9th iord is placed, and the l0th lord joins the 2nd
            house in conjunction u ith the 9tk lord, Vishnu Yoga is caused.
        PVR Definition:
            1. 9th and 10th lords (from Rasi) are in the 2nd house of Rasi.
            2. The lord of the sign occupied by the 9th lord in Navamsa is also in the 2nd house of Rasi.
        both Methods appear the same
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _vishnu_yoga_calculation(planet_positions_rasi=planet_positions_rasi, planet_positions_navamsa=planet_positions_navamsa)
def vishnu_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-62 Vishnu Yoga (PVR & BVR):
        BV Raman Definition:  the lord of Navamsa in which the 9th iord is placed, and the l0th lord joins the 2nd
            house in conjunction u ith the 9tk lord, Vishnu Yoga is caused.
        PVR Definition:
            1. 9th and 10th lords (from Rasi) are in the 2nd house of Rasi.
            2. The lord of the sign occupied by the 9th lord in Navamsa is also in the 2nd house of Rasi.
        both Methods appear the same
    """
    planet_positions_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    planet_positions_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _vishnu_yoga_calculation(planet_positions_rasi=planet_positions_rasi, planet_positions_navamsa=planet_positions_navamsa)
def _vishnu_yoga_from_planet_positions(planet_positions):
    """ BVR-62 Vishnu Yoga (PVR & BVR):
        BV Raman Definition:  the lord of Navamsa in which the 9th iord is placed, and the l0th lord joins the 2nd
            house in conjunction u ith the 9tk lord, Vishnu Yoga is caused.
        PVR Definition:
            1. 9th and 10th lords (from Rasi) are in the 2nd house of Rasi.
            2. The lord of the sign occupied by the 9th lord in Navamsa is also in the 2nd house of Rasi.
        both Methods appear the same
    """
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    pp_9 = charts.navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
    p_to_h_navamsa = utils.get_planet_house_dictionary_from_planet_positions(pp_9)
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    asc_house = p_to_h[const._ascendant_symbol]
    ninth_lord_in_rasi = house.house_owner_from_planet_positions(planet_positions,(asc_house+const.HOUSE_9)%12) 
    vy1 = p_to_h[ninth_lord_in_rasi]==(asc_house+const.HOUSE_2)%12 and p_to_h[house.house_owner_from_planet_positions(planet_positions,(asc_house+9)%12)]==(asc_house+1)%12
    if not vy1:
        return False
    lord_of_ninth_in_navamsa = house.house_owner_from_planet_positions(planet_positions,p_to_h_navamsa[ninth_lord_in_rasi])
    vy2 = p_to_h[lord_of_ninth_in_navamsa] == (asc_house+const.HOUSE_2)%12
    return vy1 and vy2
def _siva_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-61 Siva Yoga: If (1) the 5th lord is in the 9th house, (2) the 9th lord is in the 10th house,
        and, (3) the 10th lord is in the 5th house """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12; nineth_house = (asc_house+const.HOUSE_9)%12
    tenth_house = (asc_house+const.HOUSE_10)%12
    if planet_positions is not None:
        fifth_lord = house.house_owner_from_planet_positions(planet_positions,fifth_house)
        nineth_lord = house.house_owner_from_planet_positions(planet_positions,nineth_house)
        tenth_lord = house.house_owner_from_planet_positions(planet_positions,tenth_house)
    else:
        fifth_lord = house.house_owner(chart_1d, fifth_house)
        nineth_lord = house.house_owner(chart_1d, nineth_house)
        tenth_lord = house.house_owner(chart_1d, tenth_house)
    fifth_in_nineth = p_to_h[fifth_lord] == nineth_house
    nineth_in_tenth =  p_to_h[nineth_lord] == tenth_house
    tenth_in_fifth = p_to_h[tenth_lord] == fifth_house
    return fifth_in_nineth and nineth_in_tenth and tenth_in_fifth
def siva_yoga(chart_1d):
    """ BVR-61 Siva Yoga: If (1) the 5th lord is in the 9th house, (2) the 9th lord is in the 10th house,
        and, (3) the 10th lord is in the 5th house """
    return _siva_yoga_calculation(chart_1d=chart_1d)
def siva_yoga_from_planet_positions(planet_positions):
    """ BVR-61 Siva Yoga: If (1) the 5th lord is in the 9th house, (2) the 9th lord is in the 10th house,
        and, (3) the 10th lord is in the 5th house """
    return _siva_yoga_calculation(planet_positions=planet_positions)
def siva_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-61 Siva Yoga: If (1) the 5th lord is in the 9th house, (2) the 9th lord is in the 10th house,
        and, (3) the 10th lord is in the 5th house """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _siva_yoga_calculation(planet_positions=planet_positions)
def _trilochana_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-69 Trilochana Yoga: If Sun, Moon and Mars are in mutual trines. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    sun_pos = p_to_h[const.SUN_ID]
    moon_pos = p_to_h[const.MOON_ID]
    mars_pos = p_to_h[const.MARS_ID]
    sun_trines = house.trines_of_the_raasi(sun_pos)
    moon_in_sun_trine = moon_pos in sun_trines
    mars_in_sun_trine = mars_pos in sun_trines
    return moon_in_sun_trine and mars_in_sun_trine
def trilochana_yoga(chart_1d):
    """ BVR-69 Trilochana Yoga: If Sun, Moon and Mars are in mutual trines. """
    return _trilochana_yoga_calculation(chart_1d=chart_1d)
def trilochana_yoga_from_planet_positions(planet_positions):
    """ BVR-69 Trilochana Yoga: If Sun, Moon and Mars are in mutual trines. """
    return _trilochana_yoga_calculation(planet_positions=planet_positions)
def trilochana_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ BVR-69 Trilochana Yoga: If Sun, Moon and Mars are in mutual trines. """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _trilochana_yoga_calculation(planet_positions=planet_positions)
    
def _gouri_yoga_calculation(chart_1d_rasi=None, chart_1d_navamsa=None, 
                            planet_positions_rasi=None, planet_positions_navamsa=None):
    """ BVR-28 Gouri Yoga: If the lord of the sign occupied in navamsa by the 10th lord is exalted in
        the 10th house and lagna lord joins him """
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_1d_rasi is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    asc_rasi = p_to_h_rasi[const._ascendant_symbol]
    h10_rasi = (asc_rasi + const.HOUSE_10) % 12
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d_navamsa is None: return False
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    if planet_positions_rasi is not None:
        l1 = house.house_owner_from_planet_positions(planet_positions_rasi, asc_rasi)
        l10 = house.house_owner_from_planet_positions(planet_positions_rasi, h10_rasi)
        nav_sign_of_l10 = p_to_h_navamsa[l10]
        nav_lord = house.house_owner_from_planet_positions(planet_positions_rasi, nav_sign_of_l10)
    else:
        l1 = house.house_owner(chart_1d_rasi, asc_rasi)
        l10 = house.house_owner(chart_1d_rasi, h10_rasi)
        nav_sign_of_l10 = p_to_h_navamsa[l10]
        nav_lord = house.house_owner(chart_1d_rasi, nav_sign_of_l10)
    is_exalted = const.house_strengths_of_planets[nav_lord][h10_rasi] >= const._EXALTED_UCCHAM
    in_h10 = p_to_h_rasi[nav_lord] == h10_rasi
    l1_joins = p_to_h_rasi[l1] == h10_rasi
    return is_exalted and in_h10 and l1_joins
def gouri_yoga(chart_1d_rasi, chart_1d_navamsa):
    """ BVR-28 Gouri Yoga: If the lord of the sign occupied in navamsa by the 10th lord is exalted in
        the 10th house and lagna lord joins him """
    return _gouri_yoga_calculation(chart_1d_rasi=chart_1d_rasi, chart_1d_navamsa=chart_1d_navamsa)
def gouri_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa):
    """ BVR-28 Gouri Yoga: If the lord of the sign occupied in navamsa by the 10th lord is exalted in
        the 10th house and lagna lord joins him """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _gouri_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                   planet_positions_navamsa=planet_positions_navamsa)
def gouri_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ BVR-28 Gouri Yoga: If the lord of the sign occupied in navamsa by the 10th lord is exalted in
        the 10th house and lagna lord joins him """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _gouri_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa)
def _chandikaa_yoga_calculation(chart_1d_rasi=None, chart_1d_navamsa=None, 
                                planet_positions_rasi=None, planet_positions_navamsa=None):
    """ BVR-57 Chandikaa Yoga: If (1) lagna is in a fixed sign aspected by 6th lord and (2) Sun
        joins the lords of the signs occupied in navamsa by 6th and 9th lords """
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_1d_rasi is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    asc_rasi = p_to_h_rasi[const._ascendant_symbol]
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d_navamsa is None: return False
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    is_fixed_lagna = asc_rasi in const.fixed_signs
    h6_idx = (asc_rasi + const.HOUSE_6) % 12
    h9_idx = (asc_rasi + const.HOUSE_9) % 12
    if planet_positions_rasi is not None:
        l6 = house.house_owner_from_planet_positions(planet_positions_rasi, h6_idx)
        l9 = house.house_owner_from_planet_positions(planet_positions_rasi, h9_idx)
        nav_sign_l6 = p_to_h_navamsa[l6]
        nav_sign_l9 = p_to_h_navamsa[l9]
        d6 = house.house_owner_from_planet_positions(planet_positions_rasi, nav_sign_l6)
        d9 = house.house_owner_from_planet_positions(planet_positions_rasi, nav_sign_l9)
    else:
        l6 = house.house_owner(chart_1d_rasi, h6_idx)
        l9 = house.house_owner(chart_1d_rasi, h9_idx)
        nav_sign_l6 = p_to_h_navamsa[l6]
        nav_sign_l9 = p_to_h_navamsa[l9]
        d6 = house.house_owner(chart_1d_rasi, nav_sign_l6)
        d9 = house.house_owner(chart_1d_rasi, nav_sign_l9)
    l6_aspects = house.aspected_rasis_of_the_planet(chart_1d_rasi, l6)
    is_aspected_by_l6 = asc_rasi in l6_aspects
    sun_pos = p_to_h_rasi[const.SUN_ID]
    d6_pos = p_to_h_rasi[d6]
    d9_pos = p_to_h_rasi[d9]
    return is_fixed_lagna and is_aspected_by_l6 and (sun_pos == d6_pos == d9_pos)
def chandikaa_yoga(chart_1d_rasi, chart_1d_navamsa):
    """ BVR-57 Chandikaa Yoga: If (1) lagna is in a fixed sign aspected by 6th lord and (2) Sun
        joins the lords of the signs occupied in navamsa by 6th and 9th lords """
    return _chandikaa_yoga_calculation(chart_1d_rasi=chart_1d_rasi, chart_1d_navamsa=chart_1d_navamsa)
def chandikaa_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa):
    """ BVR-57 Chandikaa Yoga: If (1) lagna is in a fixed sign aspected by 6th lord and (2) Sun
        joins the lords of the signs occupied in navamsa by 6th and 9th lords """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _chandikaa_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                       planet_positions_navamsa=planet_positions_navamsa)
def chandikaa_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ BVR-57 Chandikaa Yoga: If (1) lagna is in a fixed sign aspected by 6th lord and (2) Sun
        joins the lords of the signs occupied in navamsa by 6th and 9th lords """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _chandikaa_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa)
def _lakshmi_yoga_calculation(chart_1d=None, planet_positions=None, method=1):
    """ 
    BVR-27 Lakshmi Yoga: 
    Method 1 (PVR): 9th lord is in own sign or exaltation sign that happens to be a quadrant 
    from lagna and lagna lord is strong.
    Method 2 (BV Raman): Lagna lord is powerful and 9th lord occupies own or 
    exaltation sign identical with a Kendra or Thrikona.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    h9_idx = (asc_house + const.HOUSE_9) % 12
    if planet_positions is not None:
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_house)
        l9 = house.house_owner_from_planet_positions(planet_positions, h9_idx)
    else:
        l1 = house.house_owner(chart_1d, asc_house)
        l9 = house.house_owner(chart_1d, h9_idx)
    l1_pos = p_to_h[l1]
    l9_pos = p_to_h[l9]
    l9_strength = const.house_strengths_of_planets[l9][l9_pos]
    is_strong_l9 = l9_strength >= const._EXALTED_UCCHAM 
    quadrants = quadrants_of_the_house(asc_house)
    trines = trines_of_the_house(asc_house)
    is_kendra = l9_pos in quadrants
    is_thrikona = l9_pos in trines
    l1_strength = const.house_strengths_of_planets[l1][l1_pos]
    l1_is_powerful = (l1_strength >= const._EXALTED_UCCHAM or 
                      l1_pos in quadrants or l1_pos in trines)
    if method == 1:
        return is_strong_l9 and is_kendra and l1_is_powerful
    else:
        return is_strong_l9 and (is_kendra or is_thrikona) and l1_is_powerful
def lakshmi_yoga(chart_1d, method=1):
    """ 
    BVR-27 Lakshmi Yoga: 
    Method 1 (PVR): 9th lord is in own sign or exaltation sign that happens to be a quadrant 
    from lagna and lagna lord is strong.
    Method 2 (BV Raman): Lagna lord is powerful and 9th lord occupies own or 
    exaltation sign identical with a Kendra or Thrikona.
    """
    return _lakshmi_yoga_calculation(chart_1d=chart_1d, method=method)

def lakshmi_yoga_from_planet_positions(planet_positions, method=1):
    """ 
    BVR-27 Lakshmi Yoga: 
    Method 1 (PVR): 9th lord is in own sign or exaltation sign that happens to be a quadrant 
    from lagna and lagna lord is strong.
    Method 2 (BV Raman): Lagna lord is powerful and 9th lord occupies own or 
    exaltation sign identical with a Kendra or Thrikona.
    """
    return _lakshmi_yoga_calculation(planet_positions=planet_positions, method=method)
def lakshmi_yoga_from_jd_place(jd, place, divisional_chart_factor=1,method=1):
    """ 
    BVR-27 Lakshmi Yoga: 
    Method 1 (PVR): 9th lord is in own sign or exaltation sign that happens to be a quadrant 
    from lagna and lagna lord is strong.
    Method 2 (BV Raman): Lagna lord is powerful and 9th lord occupies own or 
    exaltation sign identical with a Kendra or Thrikona.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _lakshmi_yoga_calculation(planet_positions=pp, method=method)
def _saarada_yoga_calculation(chart_1d=None, planet_positions=None):
    """ Saarada Yoga: 
        (1) 10th lord in 5th house, 
        (2) Mercury in a quadrant, 
        (3) Sun strong in Leo, 
        (4) Mercury or Jupiter in a trine from Moon, 
        (5) Mars in 11th. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # (1) 10th lord in the 5th house
    h10_idx = (asc_house + const.HOUSE_10) % 12
    h5_idx = (asc_house + const.HOUSE_5) % 12
    if planet_positions is not None:
        l10 = house.house_owner_from_planet_positions(planet_positions, h10_idx)
    else:
        l10 = house.house_owner(chart_1d, h10_idx)
    tenth_lord_in_fifth_house = p_to_h[l10] == h5_idx
    # (2) Mercury in a quadrant from Lagna
    mercury_pos = p_to_h[const.MERCURY_ID]
    mercury_in_quadrant = mercury_pos in quadrants_of_the_house(asc_house)
    # (3) Sun strong in Leo
    # Leo is sign index 4. Check if Sun is there and strength >= 4 (Uccham/Owner)
    sun_pos = p_to_h[const.SUN_ID]
    sun_is_strong_on_leo = (sun_pos == 4) and (const.house_strengths_of_planets[const.SUN_ID][4] >= const._EXALTED_UCCHAM)
    # (4) Mercury or Jupiter in a trine from Moon
    moon_pos = p_to_h[const.MOON_ID]
    jupiter_pos = p_to_h[const.JUPITER_ID]
    trines_from_moon = trines_of_the_house(moon_pos)
    mercury_jupiter_in_moon_trine = (mercury_pos in trines_from_moon) or (jupiter_pos in trines_from_moon)
    # (5) Mars in 11th from Lagna
    h11_idx = (asc_house + const.HOUSE_11) % 12
    mars_in_eleventh = p_to_h[const.MARS_ID] == h11_idx
    return tenth_lord_in_fifth_house and mercury_in_quadrant and sun_is_strong_on_leo and mercury_jupiter_in_moon_trine and mars_in_eleventh
def saarada_yoga(chart_1d):
    """ Saarada Yoga: 
        (1) 10th lord in 5th house, 
        (2) Mercury in a quadrant, 
        (3) Sun strong in Leo, 
        (4) Mercury or Jupiter in a trine from Moon, 
        (5) Mars in 11th. """
    return _saarada_yoga_calculation(chart_1d=chart_1d)
def saarada_yoga_from_planet_positions(planet_positions):
    """ Saarada Yoga: 
        (1) 10th lord in 5th house, 
        (2) Mercury in a quadrant, 
        (3) Sun strong in Leo, 
        (4) Mercury or Jupiter in a trine from Moon, 
        (5) Mars in 11th. """
    return _saarada_yoga_calculation(planet_positions=planet_positions)
def saarada_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ Saarada Yoga: 
        (1) 10th lord in 5th house, 
        (2) Mercury in a quadrant, 
        (3) Sun strong in Leo, 
        (4) Mercury or Jupiter in a trine from Moon, 
        (5) Mars in 11th. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _saarada_yoga_calculation(planet_positions=pp)
def _bhaarathi_yoga_calculation(chart_1d_rasi=None, chart_1d_navamsa=None,
                                planet_positions_rasi=None,planet_positions_navamsa=None):
    """ BVR-29 Bhaarathi Yoga: If the lord of the sign occupied in navamsa by 2nd, 5th or 11th lord
        exalted and joins the 9th lord """
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    asc_house = p_to_h[const._ascendant_symbol]
    h_offsets = [const.HOUSE_2, const.HOUSE_5, const.HOUSE_11]
    h9_offset = const.HOUSE_9
    if planet_positions_rasi is not None and planet_positions_navamsa is not None:
        lords_x = [house.house_owner_from_planet_positions(planet_positions_rasi, (asc_house + h) % 12) for h in h_offsets]
        ninth_lord = house.house_owner_from_planet_positions(planet_positions_rasi, (asc_house + h9_offset) % 12)
        navamsa_lords = [house.house_owner_from_planet_positions(planet_positions_navamsa, p_to_h_navamsa[l]) for l in lords_x]
    else:
        lords_x = [house.house_owner(chart_1d_rasi, (asc_house + h) % 12) for h in h_offsets]
        ninth_lord = house.house_owner(chart_1d_rasi, (asc_house + h9_offset) % 12)
        navamsa_lords = [house.house_owner(chart_1d_navamsa, p_to_h_navamsa[l]) for l in lords_x]
    l9_pos = p_to_h[ninth_lord]
    # Check: Dispositor joins L9 AND is exalted (Strength >= 4)
    _bharathi_yoga = any([p_to_h[nl] == l9_pos and 
               const.house_strengths_of_planets[nl][p_to_h[nl]] >= const._EXALTED_UCCHAM 
               for nl in navamsa_lords])
    return _bharathi_yoga
def bhaarathi_yoga(chart_1d_rasi, chart_1d_navamsa):
    """ BVR-29 Bhaarathi Yoga: If the lord of the sign occupied in navamsa by 2nd, 5th or 11th lord
        exalted and joins the 9th lord """
    return _bhaarathi_yoga_calculation(chart_1d_rasi=chart_1d_rasi, chart_1d_navamsa=chart_1d_navamsa)
def bhaarathi_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa):
    """ BVR-29 Bhaarathi Yoga: If the lord of the sign occupied in navamsa by 2nd, 5th or 11th lord
        exalted and joins the 9th lord """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _bhaarathi_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                       planet_positions_navamsa=planet_positions_navamsa)
def bhaarathi_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ BVR-29 Bhaarathi Yoga: If the lord of the sign occupied in navamsa by 2nd, 5th or 11th lord
        exalted and joins the 9th lord """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _bhaarathi_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa)
def _saraswathi_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-161 Saraswathi Yoga: 
    (1) Mercury, Jupiter, and Venus each occupy a quadrant, trine, or the 2nd house.
    (2) Jupiter is in an own, friendly, or exaltation sign.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # 1. Identify placements
    mercury_pos = p_to_h[const.MERCURY_ID]
    jupiter_pos = p_to_h[const.JUPITER_ID]
    venus_pos = p_to_h[const.VENUS_ID]
    # 2. Define valid houses (Quadrants, Trines, and 2nd House)
    quadrants = quadrants_of_the_house(asc_house)
    trines = trines_of_the_house(asc_house)
    h2_idx = (asc_house + const.HOUSE_2) % 12
    valid_houses = set(quadrants) | set(trines) | {h2_idx}
    # Condition 1: Check if all three are in valid houses
    benefics_placed_well = (mercury_pos in valid_houses and 
                            jupiter_pos in valid_houses and 
                            venus_pos in valid_houses)
    # Condition 2: Jupiter's Strength
    jupiter_strength = const.house_strengths_of_planets[const.JUPITER_ID][jupiter_pos]
    jupiter_is_strong = jupiter_strength >= const._FRIEND
    return benefics_placed_well and jupiter_is_strong
def saraswathi_yoga(chart_1d):
    """ 
    BVR-161 Saraswathi Yoga: 
    (1) Mercury, Jupiter, and Venus each occupy a quadrant, trine, or the 2nd house.
    (2) Jupiter is in an own, friendly, or exaltation sign.
    """
    return _saraswathi_yoga_calculation(chart_1d=chart_1d)

def saraswathi_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-161 Saraswathi Yoga: 
    (1) Mercury, Jupiter, and Venus each occupy a quadrant, trine, or the 2nd house.
    (2) Jupiter is in an own, friendly, or exaltation sign.
    """
    return _saraswathi_yoga_calculation(planet_positions=planet_positions)
def saraswathi_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """ 
    BVR-161 Saraswathi Yoga: 
    (1) Mercury, Jupiter, and Venus each occupy a quadrant, trine, or the 2nd house.
    (2) Jupiter is in an own, friendly, or exaltation sign.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _saraswathi_yoga_calculation(planet_positions=pp)

def _amsaavatara_yoga_calculation(chart_1d=None, planet_positions=None, method=None):
    """ 
    BVR-50 Amsaavatara Yoga: 
    Method 1 (PVR): Jupiter, Venus, and exalted Saturn are in quadrants.
    Method 2 (BVR): Same as Method 1, but Lagna must be in a movable sign.
    """
    if method is None: method = const.amsaavatara_yoga_method
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    
    # 1. Identify placements
    jupiter_pos = p_to_h[const.JUPITER_ID]
    venus_pos = p_to_h[const.VENUS_ID]
    saturn_pos = p_to_h[const.SATURN_ID]
    
    # 2. Check for Quadrants (1, 4, 7, 10)
    quadrants = quadrants_of_the_house(asc_house)
    
    in_quadrants = (jupiter_pos in quadrants and 
                    venus_pos in quadrants and 
                    saturn_pos in quadrants)
    
    # 3. Check Saturn's Exaltation (Strength 4 in your matrix)
    saturn_exalted = const.house_strengths_of_planets[const.SATURN_ID][saturn_pos] == const._EXALTED_UCCHAM
    
    # 4. Movable Sign Check for BVR Method (Signs 0, 3, 6, 9)
    is_movable_lagna = asc_house in [0, 3, 6, 9]

    if method == 1:
        return in_quadrants and saturn_exalted
    else:
        return in_quadrants and saturn_exalted and is_movable_lagna
def amsaavatara_yoga(chart_1d, method=None):
    """ 
    BVR-50 Amsaavatara Yoga: 
    Method 1 (PVR): Jupiter, Venus, and exalted Saturn are in quadrants.
    Method 2 (BVR): Same as Method 1, but Lagna must be in a movable sign.
    """
    if method is None: method = const.amsaavatara_yoga_method
    return _amsaavatara_yoga_calculation(chart_1d=chart_1d, method=method)

def amsaavatara_yoga_from_planet_positions(planet_positions, method=None):
    """ 
    BVR-50 Amsaavatara Yoga: 
    Method 1 (PVR): Jupiter, Venus, and exalted Saturn are in quadrants.
    Method 2 (BVR): Same as Method 1, but Lagna must be in a movable sign.
    """
    if method is None: method = const.amsaavatara_yoga_method
    return _amsaavatara_yoga_calculation(planet_positions=planet_positions, method=method)
    
def amsaavatara_yoga_from_jd_place(jd,place,divisional_chart_factor=1, method=None):
    """ 
    BVR-50 Amsaavatara Yoga: 
    Method 1 (PVR): Jupiter, Venus, and exalted Saturn are in quadrants.
    Method 2 (BVR): Same as Method 1, but Lagna must be in a movable sign.
    """
    if method is None: method = const.amsaavatara_yoga_method
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _amsaavatara_yoga_calculation(planet_positions=pp,method=method)
def _devendra_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-55 Devendra Yoga: 
    (1) Lagna in a fixed sign.
    (2) Exchange between 2nd and 10th lords.
    (3) Exchange between Lagna and 11th lords.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    
    # 1. Condition: Fixed Sign Lagna
    if asc_house not in const.fixed_signs:
        return False

    # 2. Identify Lord Indices using your constants
    h2_idx = (asc_house + const.HOUSE_2) % 12
    h10_idx = (asc_house + const.HOUSE_10) % 12
    h11_idx = (asc_house + const.HOUSE_11) % 12
    
    if planet_positions is not None:
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_house)
        l2 = house.house_owner_from_planet_positions(planet_positions, h2_idx)
        l10 = house.house_owner_from_planet_positions(planet_positions, h10_idx)
        l11 = house.house_owner_from_planet_positions(planet_positions, h11_idx)
    else:
        l1 = house.house_owner(chart_1d, asc_house)
        l2 = house.house_owner(chart_1d, h2_idx)
        l10 = house.house_owner(chart_1d, h10_idx)
        l11 = house.house_owner(chart_1d, h11_idx)

    # 3. Check Exchanges
    # L2 in 10H and L10 in 2H
    exchange_2_10 = (p_to_h[l2] == h10_idx and p_to_h[l10] == h2_idx)
    # L1 in 11H and L11 in 1H
    exchange_1_11 = (p_to_h[l1] == h11_idx and p_to_h[l11] == asc_house)

    return exchange_2_10 and exchange_1_11
def devendra_yoga(chart_1d):
    """ 
    BVR-55 Devendra Yoga: 
    (1) Lagna is in a fixed sign.
    (2) 2nd and 10th lords have an exchange.
    (3) Lagna and 11th lords have an exchange.
    """
    return _devendra_yoga_calculation(chart_1d=chart_1d)

def devendra_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-55 Devendra Yoga: 
    (1) Lagna is in a fixed sign.
    (2) 2nd and 10th lords have an exchange.
    (3) Lagna and 11th lords have an exchange.
    """
    return _devendra_yoga_calculation(planet_positions=planet_positions)
def devendra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ 
    BVR-55 Devendra Yoga: 
    (1) Lagna is in a fixed sign.
    (2) 2nd and 10th lords have an exchange.
    (3) Lagna and 11th lords have an exchange.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _devendra_yoga_calculation(planet_positions=pp)

def _indra_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-64 Indra Yoga: 
    (1) Exchange between 5th and 11th lords.
    (2) Moon occupies the 5th house.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    
    # 1. Identify House Indices
    h5_idx = (asc_house + const.HOUSE_5) % 12
    h11_idx = (asc_house + const.HOUSE_11) % 12
    
    # 2. Identify Lords
    if planet_positions is not None:
        l5 = house.house_owner_from_planet_positions(planet_positions, h5_idx)
        l11 = house.house_owner_from_planet_positions(planet_positions, h11_idx)
    else:
        l5 = house.house_owner(chart_1d, h5_idx)
        l11 = house.house_owner(chart_1d, h11_idx)

    # 3. Condition 1: Exchange between 5th and 11th lords
    # L5 in 11H and L11 in 5H
    exchange_5_11 = (p_to_h[l5] == h11_idx and p_to_h[l11] == h5_idx)
    
    # 4. Condition 2: Moon (ID 1) occupies the 5th house
    moon_in_5 = (p_to_h[const.MOON_ID] == h5_idx)

    return exchange_5_11 and moon_in_5
def indra_yoga(chart_1d):
    """ 
    BVR-64 Indra Yoga: 
    (1) Exchange between 5th and 11th lords.
    (2) Moon occupies the 5th house.
    """
    return _indra_yoga_calculation(chart_1d=chart_1d)

def indra_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-64 Indra Yoga: 
    (1) Exchange between 5th and 11th lords.
    (2) Moon occupies the 5th house.
    """
    return _indra_yoga_calculation(planet_positions=planet_positions)
def indra_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ 
    BVR-64 Indra Yoga: 
    (1) Exchange between 5th and 11th lords.
    (2) Moon occupies the 5th house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _indra_yoga_calculation(planet_positions=pp)

def _ravi_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-65 Ravi Yoga: 
    (1) Sun is in the 10th house.
    (2) The 10th lord is in the 3rd house with Saturn.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    
    # Identify House Indices
    h3_idx = (asc_house + const.HOUSE_3) % 12
    h10_idx = (asc_house + const.HOUSE_10) % 12
    
    # Identify 10th Lord
    if planet_positions is not None:
        l10 = house.house_owner_from_planet_positions(planet_positions, h10_idx)
    else:
        l10 = house.house_owner(chart_1d, h10_idx)

    # Condition 1: Sun (ID 0) in the 10th house
    sun_in_10 = (p_to_h[const.SUN_ID] == h10_idx)
    
    # Condition 2: 10th lord and Saturn (ID 6) are both in the 3rd house
    l10_in_3 = (p_to_h[l10] == h3_idx)
    saturn_in_3 = (p_to_h[const.SATURN_ID] == h3_idx)

    return sun_in_10 and l10_in_3 and saturn_in_3

def ravi_yoga(chart_1d):
    """ 
    BVR-65 Ravi Yoga: 
    (1) Sun is in the 10th house.
    (2) The 10th lord is in the 3rd house with Saturn.
    """
    return _ravi_yoga_calculation(chart_1d=chart_1d)

def ravi_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-65 Ravi Yoga: 
    (1) Sun is in the 10th house.
    (2) The 10th lord is in the 3rd house with Saturn.
    """
    return _ravi_yoga_calculation(planet_positions=planet_positions)

def ravi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-65 Ravi Yoga: 
    (1) Sun is in the 10th house.
    (2) The 10th lord is in the 3rd house with Saturn.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _ravi_yoga_calculation(planet_positions=pp)
def _bhaaskara_yoga_calculation(chart_1d=None, planet_positions=None,method=1):
    """ BVR-159 Bhaaskara Yoga: 
        Method=1 (PVR) (1) Moon 12th from Sun (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon 
        Method=2 (BVR) (2) Moon 11th from Mercury (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # Locate Key Planets
    sun_idx = p_to_h[const.SUN_ID]
    moon_idx = p_to_h[const.MOON_ID]
    mercury_idx = p_to_h[const.MERCURY_ID]
    jupiter_idx = p_to_h[const.JUPITER_ID]
    
    # Condition 1: Moon in 12th from Sun or 11th from Mercury
    # (Sun Index + 11 signs) % 12
    moon_target = (sun_idx + const.HOUSE_12) % 12 if method==1 else (mercury_idx + const.HOUSE_11) % 12
    moon_in_target = (moon_idx == moon_target)
    
    # Condition 2: Mercury in 2nd from Sun
    # (Sun Index + 1 sign) % 12
    mercury_target = (sun_idx + const.HOUSE_2) % 12
    mercury_is_2nd_from_sun = (mercury_idx == mercury_target)
    
    # Condition 3: Jupiter in 5th or 9th from Moon
    # 5th from Moon: (Moon Index + 4 signs)
    # 9th from Moon: (Moon Index + 8 signs)
    jup_target_5 = (moon_idx + const.HOUSE_5) % 12
    jup_target_9 = (moon_idx + const.HOUSE_9) % 12
    jupiter_5th_from_moon = jupiter_idx == jup_target_5
    jupiter_9th_from_moon = jupiter_idx == jup_target_9
    
    return moon_in_target and mercury_is_2nd_from_sun and (jupiter_5th_from_moon or jupiter_9th_from_moon)

def bhaaskara_yoga(chart_1d,method=1):
    """ BVR-159 Bhaaskara Yoga: 
        Method=1 (PVR) (1) Moon 12th from Sun (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon 
        Method=2 (BVR) (2) Moon 11th from Mercury (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon
    """
    return _bhaaskara_yoga_calculation(chart_1d=chart_1d,method=method)

def bhaaskara_yoga_from_planet_positions(planet_positions,method=1):
    """ BVR-159 Bhaaskara Yoga: 
        Method=1 (PVR) (1) Moon 12th from Sun (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon 
        Method=2 (BVR) (2) Moon 11th from Mercury (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon
    """
    return _bhaaskara_yoga_calculation(planet_positions=planet_positions,method=method)

def bhaaskara_yoga_from_jd_place(jd, place, divisional_chart_factor=1,method=1):
    """ BVR-159 Bhaaskara Yoga: 
        Method=1 (PVR) (1) Moon 12th from Sun (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon 
        Method=2 (BVR) (2) Moon 11th from Mercury (2) Mercury 2nd from Sun (3) Jupiter 5/9 from Moon
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bhaaskara_yoga_calculation(planet_positions=pp,method=method)

def _kulavardhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-70 Kulavardhana Yoga: 
    If each planet (Sun to Saturn) occupies the 5th house from either:
    (1) Lagna, (2) Moon, or (3) Sun.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # 1. Identify Reference Indices
    asc_idx = p_to_h[const._ascendant_symbol]
    moon_idx = p_to_h[const.MOON_ID]
    sun_idx = p_to_h[const.SUN_ID]

    # 2. Calculate the valid "Target" Houses (5th from Ref)
    # Note: const.HOUSE_5 is usually 4 (0-based index offset)
    h5_from_lagna = (asc_idx + const.HOUSE_5) % 12
    h5_from_moon = (moon_idx + const.HOUSE_5) % 12
    h5_from_sun = (sun_idx + const.HOUSE_5) % 12
    
    valid_houses = {h5_from_lagna, h5_from_moon, h5_from_sun}

    # 3. Check all 7 main planets
    for p_id in SUN_TO_SATURN:
        p_house = p_to_h[p_id]
        if p_house not in valid_houses:
            return False
            
    return True
def kulavardhana_yoga(chart_1d):
    """ 
    BVR-70 Kulavardhana Yoga: 
    If each planet (Sun to Saturn) occupies the 5th house from either:
    (1) Lagna, (2) Moon, or (3) Sun.
    """
    return _kulavardhana_yoga_calculation(chart_1d=chart_1d)

def kulavardhana_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-70 Kulavardhana Yoga: 
    If each planet (Sun to Saturn) occupies the 5th house from either:
    (1) Lagna, (2) Moon, or (3) Sun.
    """
    return _kulavardhana_yoga_calculation(planet_positions=planet_positions)

def kulavardhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-70 Kulavardhana Yoga: 
    If each planet (Sun to Saturn) occupies the 5th house from either:
    (1) Lagna, (2) Moon, or (3) Sun.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kulavardhana_yoga_calculation(planet_positions=pp)

def _vasumathi_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """ 
    BVR-9 Vasumathi Yoga: 
    Benefics occupy Upachaya houses (3, 6, 10, 11) from Lagna or Moon.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    moon_house = p_to_h[const.MOON_ID]

    # Upachaya houses from Lagna and Moon
    upachayas_from_lagna = house.upachayas_of_the_raasi(asc_house)
    upachayas_from_moon = house.upachaya_aspects_of_the_raasi(moon_house)

    # Handle Benefics (Jupiter, Venus, and conditional Mercury/Moon)
    _nb = _get_natural_benefics(chart_1d, natural_benefics)

    # The yoga is generally defined as benefics occupying these houses
    # We check if each benefic is in an Upachaya house from EITHER Lagna OR Moon
    
    return all(p_to_h[pid] in upachayas_from_lagna or p_to_h[pid] in upachayas_from_moon for pid in _nb)
def vasumathi_yoga(chart_1d):
    """ 
    BVR-9 Vasumathi Yoga: 
    Benefics occupy Upachaya houses (3, 6, 10, 11) from Lagna or Moon.
    """
    return _vasumathi_yoga_calculation(chart_1d=chart_1d)

def vasumathi_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-9 Vasumathi Yoga: 
    Benefics occupy Upachaya houses (3, 6, 10, 11) from Lagna or Moon.
    """
    return _vasumathi_yoga_calculation(planet_positions=planet_positions)

def vasumathi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-9 Vasumathi Yoga: 
    Benefics occupy Upachaya houses (3, 6, 10, 11) from Lagna or Moon.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _vasumathi_yoga_calculation(planet_positions=pp, natural_benefics=_natural_benefics)

def _gandharva_yoga_calculation(chart_1d=None, planet_positions=None, method=1):
    """ 
    BVR-60 Gandharva Yoga:
    Method 1 (PVR Narasimha Rao):
        (1) 10th lord is in a trine from the 7th house.
        (2) Lagna lord is conjoined or aspected by Jupiter.
        (3) Sun is exalted and strong (Strength >= 4).
        (4) Moon is in the 9th house.
    Method 2 (BV Raman /Kama Trikona):
        (1) 10th Lord is in a Kama Trikona house (3rd, 7th, or 11th).
        (2) Lagna Lord and Jupiter are conjoined.
        (3) Sun is exalted and strong.
        (4) Moon is in the 9th house.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    h10_idx = (asc_house + const.HOUSE_10) % 12
    if planet_positions is not None:
        l10 = house.house_owner_from_planet_positions(planet_positions, h10_idx)
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_house)
    else:
        l10 = house.house_owner(chart_1d, h10_idx)
        l1 = house.house_owner(chart_1d, asc_house)
    jup_pos = p_to_h[const.JUPITER_ID]
    sun_pos = p_to_h[const.SUN_ID]
    # (3) Sun Exalted and Strong (Common)
    cond3 = const.house_strengths_of_planets[const.SUN_ID][sun_pos] >= const._EXALTED_UCCHAM
    # (4) Moon in 9th house (Common)
    cond4 = (p_to_h[const.MOON_ID] == (asc_house + const.HOUSE_9) % 12)
    if method == 1:
        # (1) 10L in trine from 7H
        h7_idx = (asc_house + const.HOUSE_7) % 12
        cond1 = p_to_h[l10] in trines_of_the_house(h7_idx)
        # (2) L1 conjoined or aspected by Jupiter
        cond2 = asc_house in house.aspected_rasis_of_the_planet(chart_1d, const.JUPITER_ID)
    elif method == 2:
        # (1) 10L in Kama Trikona (3, 7, 11)
        kama_houses = [(asc_house + off) % 12 for off in [const.HOUSE_3, const.HOUSE_7, const.HOUSE_11]]
        cond1 = p_to_h[l10] in kama_houses
        # (2) L1 and Jupiter conjoined
        cond2 = (p_to_h[l1] == jup_pos)
    return cond1 and cond2 and cond3 and cond4
def gandharva_yoga(chart_1d, method=1):
    """ 
    BVR-60 Gandharva Yoga:
    Method 1 (PVR Narasimha Rao):
        (1) 10th lord is in a trine from the 7th house.
        (2) Lagna lord is conjoined or aspected by Jupiter.
        (3) Sun is exalted and strong (Strength >= 4).
        (4) Moon is in the 9th house.
    Method 2 (BV Raman /Kama Trikona):
        (1) 10th Lord is in a Kama Trikona house (3rd, 7th, or 11th).
        (2) Lagna Lord and Jupiter are conjoined.
        (3) Sun is exalted and strong.
        (4) Moon is in the 9th house.
    """
    return _gandharva_yoga_calculation(chart_1d=chart_1d, method=method)
def gandharva_yoga_from_planet_positions(planet_positions, method=1):
    """ 
    BVR-60 Gandharva Yoga:
    Method 1 (PVR Narasimha Rao):
        (1) 10th lord is in a trine from the 7th house.
        (2) Lagna lord is conjoined or aspected by Jupiter.
        (3) Sun is exalted and strong (Strength >= 4).
        (4) Moon is in the 9th house.
    Method 2 (BV Raman /Kama Trikona):
        (1) 10th Lord is in a Kama Trikona house (3rd, 7th, or 11th).
        (2) Lagna Lord and Jupiter are conjoined.
        (3) Sun is exalted and strong.
        (4) Moon is in the 9th house.
    """
    return _gandharva_yoga_calculation(planet_positions=planet_positions, method=method)
def gandharva_yoga_from_jd_place(jd, place, divisional_chart_factor=1, method=1):
    """ 
    BVR-60 Gandharva Yoga:
    Method 1 (PVR Narasimha Rao):
        (1) 10th lord is in a trine from the 7th house.
        (2) Lagna lord is conjoined or aspected by Jupiter.
        (3) Sun is exalted and strong (Strength >= 4).
        (4) Moon is in the 9th house.
    Method 2 (BV Raman /Kama Trikona):
        (1) 10th Lord is in a Kama Trikona house (3rd, 7th, or 11th).
        (2) Lagna Lord and Jupiter are conjoined.
        (3) Sun is exalted and strong.
        (4) Moon is in the 9th house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _gandharva_yoga_calculation(planet_positions=pp, method=method)
def _go_yoga_calculation(chart_1d=None, planet_positions=None, enforce_trikona_degrees=False):
    """ 
    BVR-67 Go Yoga: 
    (1) Jupiter in Moolatrikona (Sag 0-10°).
    (2) 2nd Lord conjoined with Jupiter.
    (3) Lagna lord is exalted.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    jup_pos = p_to_h[const.JUPITER_ID]
    h2_idx = (asc_house + const.HOUSE_2) % 12
    # --- (1) Jupiter Moolatrikona Check (Early Exit) ---
    if planet_positions is not None:
        # Index ID+1, then index [1] to get the (sign, lon) tuple
        jup_tuple = planet_positions[const.JUPITER_ID + 1][1]
        if not utils.is_planet_in_moolatrikona(const.JUPITER_ID, p_pos_tuple=jup_tuple, 
                                               enforce_trikona_degrees=enforce_trikona_degrees):
            return False
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_house)
        l2 = house.house_owner_from_planet_positions(planet_positions, h2_idx)
    else:
        if not utils.is_planet_in_moolatrikona(const.JUPITER_ID, chart_1d_house=jup_pos):
            return False
        l1 = house.house_owner(chart_1d, asc_house)
        l2 = house.house_owner(chart_1d, h2_idx)
    # --- (2) 2nd Lord with Jupiter (Early Exit) ---
    if p_to_h[l2] != jup_pos:
        return False
    # --- (3) Lagna Lord is Exalted ---
    l1_strength = const.house_strengths_of_planets[l1][p_to_h[l1]]
    if l1_strength < const._EXALTED_UCCHAM:
        return False
    return True
def go_yoga(chart_1d):
    """ 
    BVR-67 Go Yoga: 
    (1) Jupiter in Moolatrikona (Sag 0-10°).
    (2) 2nd Lord conjoined with Jupiter.
    (3) Lagna lord is exalted.
    """
    return _go_yoga_calculation(chart_1d=chart_1d)
def go_yoga_from_planet_positions(planet_positions, enforce_trikona_degrees=False):
    """ 
    BVR-67 Go Yoga: 
    (1) Jupiter in Moolatrikona (Sag 0-10°).
    (2) 2nd Lord conjoined with Jupiter.
    (3) Lagna lord is exalted.
    """
    return _go_yoga_calculation(planet_positions=planet_positions, enforce_trikona_degrees=enforce_trikona_degrees)
def go_yoga_from_jd_place(jd, place, divisional_chart_factor=1,enforce_trikona_degrees=False):
    """ 
    BVR-67 Go Yoga: 
    (1) Jupiter in Moolatrikona (Sag 0-10°).
    (2) 2nd Lord conjoined with Jupiter.
    (3) Lagna lord is exalted.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _go_yoga_calculation(planet_positions=pp,enforce_trikona_degrees=enforce_trikona_degrees)
def _vidyut_yoga_calculation(chart_1d=None, planet_positions=None, enforce_deep_exaltation=True):
    """ 
    BVR-59 Vidyut Yoga: 
    (1) 11th lord is in deep exaltation.
    (2) 11th lord conjoins Venus.
    (3) Both are in a quadrant from the lagna lord.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # --- (1) Identify 11th Lord (Short-circuit Ownership) ---
    h11_idx = (asc_house + const.HOUSE_11) % 12
    l11 = (house.house_owner_from_planet_positions(planet_positions, h11_idx) 
           if planet_positions else house.house_owner(chart_1d, h11_idx))
    l11_pos = p_to_h[l11]
    if not utils.is_planet_in_exalation(l11, l11_pos, planet_positions, enforce_deep_exaltation):
        return False
    # --- (2) 11th Lord conjoins Venus (Early Exit) ---
    if l11_pos != p_to_h[const.VENUS_ID]:
        return False
    # --- (3) Quadrant from Lagna Lord ---
    l1 = (house.house_owner_from_planet_positions(planet_positions, asc_house) 
          if planet_positions else house.house_owner(chart_1d, asc_house))
    if l11_pos not in quadrants_of_the_house(p_to_h[l1]):
        return False
    return True
def vidyut_yoga(chart_1d, enforce_deep_exaltation=False):
    """ 
    BVR-59 Vidyut Yoga: 
    (1) 11th lord is in deep exaltation.
    (2) 11th lord conjoins Venus.
    (3) Both are in a quadrant from the lagna lord.
    """
    return _vidyut_yoga_calculation(chart_1d=chart_1d, enforce_deep_exaltation=enforce_deep_exaltation)
def vidyut_yoga_from_planet_positions(planet_positions, enforce_deep_exaltation=True):
    """ 
    BVR-59 Vidyut Yoga: 
    (1) 11th lord is in deep exaltation.
    (2) 11th lord conjoins Venus.
    (3) Both are in a quadrant from the lagna lord.
    """
    return _vidyut_yoga_calculation(planet_positions=planet_positions, enforce_deep_exaltation=enforce_deep_exaltation)
def vidyut_yoga_from_jd_place(jd, place, divisional_chart_factor=1, enforce_deep_exaltation=True):
    """ 
    BVR-59 Vidyut Yoga: 
    (1) 11th lord is in deep exaltation.
    (2) 11th lord conjoins Venus.
    (3) Both are in a quadrant from the lagna lord.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vidyut_yoga_calculation(planet_positions=pp, enforce_deep_exaltation=enforce_deep_exaltation)
def _chapa_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-30 Chapa Yoga: 
    (1) 4th and 10th lords have an exchange (Parivartana).
    (2) Lagna lord is exalted (Strength >= 4).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    # --- (1) Exchange between 4th and 10th Lords ---
    h4_idx = (asc_house + const.HOUSE_4) % 12
    h10_idx = (asc_house + const.HOUSE_10) % 12
    l4 = (house.house_owner_from_planet_positions(planet_positions, h4_idx) 
          if planet_positions else house.house_owner(chart_1d, h4_idx))
    l10 = (house.house_owner_from_planet_positions(planet_positions, h10_idx) 
           if planet_positions else house.house_owner(chart_1d, h10_idx))
    # Exchange logic: L4 is in 10th house AND L10 is in 4th house
    if not (p_to_h[l4] == h10_idx and p_to_h[l10] == h4_idx):
        return False
    # --- (2) Lagna Lord is Exalted ---
    l1 = (house.house_owner_from_planet_positions(planet_positions, asc_house) 
          if planet_positions else house.house_owner(chart_1d, asc_house))
    l1_pos = p_to_h[l1]
    if not utils.is_planet_in_exalation(l1, l1_pos, planet_positions):
        return False
    return True
def chapa_yoga(chart_1d):
    """ 
    BVR-30 Chapa Yoga: 
    (1) 4th and 10th lords have an exchange (Parivartana).
    (2) Lagna lord is exalted (Strength >= 4).
    """
    return _chapa_yoga_calculation(chart_1d=chart_1d)

def chapa_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-30 Chapa Yoga: 
    (1) 4th and 10th lords have an exchange (Parivartana).
    (2) Lagna lord is exalted (Strength >= 4).
    """
    return _chapa_yoga_calculation(planet_positions=planet_positions)

def chapa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-30 Chapa Yoga: 
    (1) 4th and 10th lords have an exchange (Parivartana).
    (2) Lagna lord is exalted (Strength >= 4).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _chapa_yoga_calculation(planet_positions=pp)
def _pushkala_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-26 Pushkala Yoga: 
    (1) Lagna lord is with Moon.
    (2) Dispositor of Moon is in a quadrant (Kendra) or in the house of an Adhimitra.
    (3) Dispositor of Moon aspects Lagna (Sign/Rasi Drishti).
    (4) Lagna should be occupied by a powerful planet (Note: Per BVR Chart 26, this is optional if conditions 1-3 are strong).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # (1) Lagna lord is with Moon
    l1 = (house.house_owner_from_planet_positions(planet_positions, asc_house) 
          if planet_positions else house.house_owner(chart_1d, asc_house))
    
    moon_pos = p_to_h[const.MOON_ID]
    if p_to_h[l1] != moon_pos:
        return False

    # (2) Dispositor of Moon Check
    l_moon = (house.house_owner_from_planet_positions(planet_positions, moon_pos) 
              if planet_positions else house.house_owner(chart_1d, moon_pos))
    l_moon_pos = p_to_h[l_moon]
    
    # Kendra Check
    is_in_quadrant = l_moon_pos in quadrants_of_the_house(asc_house)
    
    # Adhimitra Check
    sign_owner = (house.house_owner_from_planet_positions(planet_positions, l_moon_pos) 
                  if planet_positions else house.house_owner(chart_1d, l_moon_pos))
    friendship_score = const.compound_planet_relations[l_moon][sign_owner]
    is_in_adhimitra = (friendship_score == const._ADHIMITRA_GREATFRIEND)
    
    # Raman says "Kendra OR house of intimate friend"
    if not (is_in_quadrant or is_in_adhimitra):
        return False

    # (3) Dispositor aspects Lagna
    # We use aspected_rasis_of_the_planet to get a list of Sign Indices (0-11)
    aspected_rasis = house.aspected_rasis_of_the_planet(chart_1d, l_moon)
    
    return asc_house in aspected_rasis
def pushkala_yoga(chart_1d):
    """ 
    BVR-26 Pushkala Yoga: 
    (1) Lagna lord is with Moon.
    (2) Dispositor of Moon is in a quadrant (Kendra) or in the house of an Adhimitra.
    (3) Dispositor of Moon aspects Lagna (Sign/Rasi Drishti).
    (4) Lagna should be occupied by a powerful planet (Note: Per BVR Chart 26, this is optional if conditions 1-3 are strong).
    """
    return _pushkala_yoga_calculation(chart_1d=chart_1d)

def pushkala_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-26 Pushkala Yoga: 
    (1) Lagna lord is with Moon.
    (2) Dispositor of Moon is in a quadrant (Kendra) or in the house of an Adhimitra.
    (3) Dispositor of Moon aspects Lagna (Sign/Rasi Drishti).
    """
    return _pushkala_yoga_calculation(planet_positions=planet_positions)

def pushkala_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-26 Pushkala Yoga: 
    (1) Lagna lord is with Moon.
    (2) Dispositor of Moon is in a quadrant (Kendra) or in the house of an Adhimitra.
    (3) Dispositor of Moon aspects Lagna (Sign/Rasi Drishti).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _pushkala_yoga_calculation(planet_positions=pp)

def makuta_yoga(chart_1d):
    """ BVR-56 Makuta Yoga: Jupiter 9th from 9th lord, benefic 9th from Jupiter, Saturn in 10th """
    return _makuta_yoga_calculation(chart_1d=chart_1d)

def makuta_yoga_from_planet_positions(planet_positions):
    """ BVR-56 Makuta Yoga: Jupiter 9th from 9th lord, benefic 9th from Jupiter, Saturn in 10th """
    return _makuta_yoga_calculation(planet_positions=planet_positions)

def makuta_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-56 Makuta Yoga: Jupiter 9th from 9th lord, benefic 9th from Jupiter, Saturn in 10th """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _natural_benefics = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _makuta_yoga_calculation(planet_positions=pp, natural_benefics=_natural_benefics)

def _makuta_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """ BVR-56 Makuta Yoga: Jupiter 9th from 9th lord, benefic 9th from Jupiter, Saturn in 10th """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # (1) Saturn in the 10th house
    h10 = (asc_house + 9) % 12
    if p_to_h[const.SATURN_ID] != h10:
        return False

    # (2) Jupiter is in the 9th house from the 9th lord
    h9 = (asc_house + 8) % 12
    l9 = (house.house_owner_from_planet_positions(planet_positions, h9) 
          if planet_positions else house.house_owner(chart_1d, h9))
    
    l9_pos = p_to_h[l9]
    target_h_for_jup = (l9_pos + 8) % 12
    if p_to_h[const.JUPITER_ID] != target_h_for_jup:
        return False

    # (3) 9th house from Jupiter has a benefic
    jup_pos = p_to_h[const.JUPITER_ID]
    h9_from_jup = (jup_pos + 8) % 12
    
    planets_in_h9_jup = planets_in_raasi(h9_from_jup,p_to_h) # V4.8.0
    
    # Handle Benefics via template
    _nb = _get_natural_benefics(chart_1d, natural_benefics)
    
    return any(p in _nb for p in planets_in_h9_jup)

def jaya_yoga(chart_1d, enforce_deep_exaltation=False):
    """ BVR-58 Jaya Yoga: 10th lord in deep exaltation and 6th lord debilitated. """
    return _jaya_yoga_calculation(chart_1d=chart_1d, enforce_deep_exaltation=enforce_deep_exaltation)

def jaya_yoga_from_planet_positions(planet_positions, enforce_deep_exaltation=True):
    """ BVR-58 Jaya Yoga: 10th lord in deep exaltation and 6th lord debilitated. """
    return _jaya_yoga_calculation(planet_positions=planet_positions, enforce_deep_exaltation=enforce_deep_exaltation)

def jaya_yoga_from_jd_place(jd, place, divisional_chart_factor=1, enforce_deep_exaltation=True):
    """ BVR-58 Jaya Yoga: 10th lord in deep exaltation and 6th lord debilitated. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _jaya_yoga_calculation(planet_positions=pp, enforce_deep_exaltation=enforce_deep_exaltation)

def _jaya_yoga_calculation(chart_1d=None, planet_positions=None, enforce_deep_exaltation=True):
    """ BVR-58 Jaya Yoga: 10th lord in deep exaltation and 6th lord debilitated. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # --- (1) 10th Lord in Deep Exaltation ---
    h10_idx = (asc_house + const.HOUSE_10) % 12
    l10 = (house.house_owner_from_planet_positions(planet_positions, h10_idx) 
           if planet_positions else house.house_owner(chart_1d, h10_idx))
    
    l10_pos = p_to_h[l10]
    if not utils.is_planet_in_exalation(l10, l10_pos, planet_positions, enforce_deep_exaltation):
        return False
    # --- (2) 6th Lord is Debilitated ---
    h6_idx = (asc_house + const.HOUSE_6) % 12
    l6 = (house.house_owner_from_planet_positions(planet_positions, h6_idx) 
          if planet_positions else house.house_owner(chart_1d, h6_idx))
    
    l6_pos = p_to_h[l6]
    
    # Using 0 for debilitation strength
    if const.house_strengths_of_planets[l6][l6_pos] != const._DEBILITATED_NEECHAM:
        return False

    return True
def _vipareeta_yoga_calculation(target_house, chart_1d=None, planet_positions=None):
    """
    Generalized logic for Harsha, Sarala, and Vimala Yogas.
    Rule: The lord of a dusthana house (6, 8, or 12) occupies that same house.
    """
    # 1. Standardize input to a 1D chart list
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    # 2. Get Lagna house index
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # 3. Calculate the Rasi index for the target house (1-based input converted to 0-based offset)
    target_h_idx = (asc_house + (target_house - 1)) % 12
    
    # 4. Identify the Lord of that target house
    lord = (house.house_owner_from_planet_positions(planet_positions, target_h_idx) 
            if planet_positions else house.house_owner(chart_1d, target_h_idx))
    
    # 5. Check if the Lord is physically placed in that house
    # We use p_to_h[lord] for the current position vs target_h_idx for the house itself
    return p_to_h[lord] == target_h_idx
def harsha_yoga(chart_1d):
    """ BVR-105 Harsha Yoga: 6th lord occupies the 6th house """
    return _vipareeta_yoga_calculation(6, chart_1d=chart_1d)

def harsha_yoga_from_planet_positions(planet_positions):
    """ BVR-105 Harsha Yoga: 6th lord occupies the 6th house """
    return _vipareeta_yoga_calculation(6, planet_positions=planet_positions)

def harsha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-105 Harsha Yoga: 6th lord occupies the 6th house """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vipareeta_yoga_calculation(6, planet_positions=pp)

def sarala_yoga(chart_1d):
    """ BVR-106 Sarala Yoga: 8th lord occupies the 8th house """
    return _vipareeta_yoga_calculation(8, chart_1d=chart_1d)

def sarala_yoga_from_planet_positions(planet_positions):
    """ BVR-106 Sarala Yoga: 8th lord occupies the 8th house """
    return _vipareeta_yoga_calculation(8, planet_positions=planet_positions)

def sarala_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-106 Sarala Yoga: 8th lord occupies the 8th house """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vipareeta_yoga_calculation(8, planet_positions=pp)

def vimala_yoga(chart_1d):
    """ BVR-107 Vimala Yoga: 12th lord occupies the 12th house """
    return _vipareeta_yoga_calculation(12, chart_1d=chart_1d)

def vimala_yoga_from_planet_positions(planet_positions):
    """ BVR-107 Vimala Yoga: 12th lord occupies the 12th house """
    return _vipareeta_yoga_calculation(12, planet_positions=planet_positions)

def vimala_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-107 Vimala Yoga: 12th lord occupies the 12th house """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vipareeta_yoga_calculation(12, planet_positions=pp)
def _chatussagara_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-8 Chatussagara Yoga: All quadrants (1, 4, 7, 10) are occupied by planets. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # 1. Get the indices of the 4 quadrants
    kendra_indices = quadrants_of_the_house(asc_house)
    
    # 2. Get the set of houses where planets (0-8) are actually located
    # We exclude the Lagna symbol to ensure we only count physical planets
    planet_locations = {p_to_h[p_id] for p_id in range(9)}

    # 3. Check if EVERY quadrant index is present in the planet_locations set
    for h_idx in kendra_indices:
        if h_idx not in planet_locations:
            return False
            
    return True
def chatussagara_yoga(chart_1d):
    """ BVR-8 Chatussagara Yoga: All quadrants (1, 4, 7, 10) are occupied by planets. """
    return _chatussagara_yoga_calculation(chart_1d=chart_1d)

def chatussagara_yoga_from_planet_positions(planet_positions):
    """ BVR-8 Chatussagara Yoga: All quadrants (1, 4, 7, 10) are occupied by planets. """
    return _chatussagara_yoga_calculation(planet_positions=planet_positions)

def chatussagara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-8 Chatussagara Yoga: All quadrants (1, 4, 7, 10) are occupied by planets. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _chatussagara_yoga_calculation(planet_positions=pp)
def rajalakshana_yoga(chart_1d):
    """ BVR-10 Rajalakshana Yoga: Jupiter, Venus, Mercury, and Moon are in Kendras from Lagna. """
    return _rajalakshana_yoga_calculation(chart_1d=chart_1d)

def rajalakshana_yoga_from_planet_positions(planet_positions):
    """ BVR-10 Rajalakshana Yoga: Jupiter, Venus, Mercury, and Moon are in Kendras from Lagna. """
    return _rajalakshana_yoga_calculation(planet_positions=planet_positions)

def rajalakshana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-10 Rajalakshana Yoga: Jupiter, Venus, Mercury, and Moon are in Kendras from Lagna. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _rajalakshana_yoga_calculation(planet_positions=pp)

def _rajalakshana_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-10 Rajalakshana Yoga: Jupiter, Venus, Mercury, and Moon are in Kendras from Lagna. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # 1. Define the Kendra indices (Absolute Zodiac Indices)
    kendra_indices = quadrants_of_the_house(asc_house)
    
    # 2. Target Benefics: Jupiter(4), Venus(5), Mercury(3), Moon(1)
    target_planets = [const.JUPITER_ID, const.VENUS_ID, const.MERCURY_ID, const.MOON_ID]
    
    # 3. Check if all four are in one of the kendra indices
    for p_id in target_planets:
        if p_to_h[p_id] not in kendra_indices:
            return False
            
    return True
def vanchana_chora_bheethi_yoga(chart_1d, gulika_h_idx=None, natural_malefics=None):
    """ BVR-11 Vanchana Chora Bheethi: Lagna malefic/Gulika trine OR Gulika with Kendra/Trine lords OR L1 with Rahu/Sat/Ket. """
    return _vanchana_chora_bheethi_yoga_calculation(chart_1d=chart_1d, gulika_h_idx=gulika_h_idx, 
                                                    natural_malefics=natural_malefics)

def vanchana_chora_bheethi_yoga_from_planet_positions(planet_positions, gulika_h_idx=None, natural_malefics=None):
    """ BVR-11 Vanchana Chora Bheethi: Lagna malefic/Gulika trine OR Gulika with Kendra/Trine lords OR L1 with Rahu/Sat/Ket. """
    """ Vanchana Chora Bheethi: Same as above using planet positions. """
    return _vanchana_chora_bheethi_yoga_calculation(planet_positions=planet_positions, gulika_h_idx=gulika_h_idx, 
                                                    natural_malefics=natural_malefics)

def vanchana_chora_bheethi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-11 Vanchana Chora Bheethi: Lagna malefic/Gulika trine OR Gulika with Kendra/Trine lords OR L1 with Rahu/Sat/Ket. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    
    # We only need malefics for this yoga
    _, _natural_malefics = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    g_h_idx, _ = drik.dasavarga_from_long(g_lon_info) 
    return _vanchana_chora_bheethi_yoga_calculation(planet_positions=pp, gulika_h_idx=g_h_idx, 
                                                    natural_malefics=_natural_malefics)
def _vanchana_chora_bheethi_yoga_calculation(chart_1d=None, planet_positions=None, gulika_h_idx=None, natural_malefics=None):
    """ BVR-11 Vanchana Chora Bheethi: Lagna malefic/Gulika trine OR Gulika with Kendra/Trine lords OR L1 with Rahu/Sat/Ket. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]

    # --- Malefics set (override or default) ---
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    # Specific malefics for Condition 3 (Rahu, Saturn, Ketu)
    c3_malefics = {const.RAHU_ID, const.SATURN_ID, const.KETU_ID}

    # --- Condition 3: Lord of Lagna combined with Rahu, Saturn or Ketu ---
    l1 = (house.house_owner_from_planet_positions(planet_positions, asc_house) 
          if planet_positions else house.house_owner(chart_1d, asc_house))
    l1_house = p_to_h[l1]
    l1_house_content = planets_in_raasi(l1_house,p_to_h) # V4.8.0
    if any(m in l1_house_content for m in c3_malefics if m != l1): # V4.8.0
        return True

    if gulika_h_idx is not None:
        # --- Condition 1: Malefic in Lagna AND Gulika in Trine ---
        trines = trines_of_the_house(asc_house)
        lagna_content = planets_in_raasi(asc_house, p_to_h) # V4.8.0
        has_malefic_in_lagna = any(m in lagna_content for m in _natural_malefics)
        
        if has_malefic_in_lagna and (gulika_h_idx in trines):
            return True

        # --- Condition 2: Gulika associated with lords of Kendras and Thrikonas ---
        # Note: 'associated' here means conjoined in the same house
        kt_offsets = [0, 3, 6, 9, 4, 8] # 1,4,7,10 (Kendras) and 5,9 (Trines)
        kt_lords = { (house.house_owner_from_planet_positions(planet_positions, (asc_house + off) % 12) 
                     if planet_positions else house.house_owner(chart_1d, (asc_house + off) % 12)) 
                     for off in kt_offsets }
        
        gulika_house_content = planets_in_raasi(gulika_h_idx,p_to_h) # V4.8.0
        if any(lord in gulika_house_content for lord in kt_lords):
            return True

    return False
def harihara_brahma_yoga(chart_1d,method=1):
    """
        BVR-51 Definition per BV Raman. 
            If benefics are in the 8th or 12th from the 2nd lord OR 
            if Jupiter, the Moon and Mercury are in the 4th, 9th and 8th from the 7th lord OR 
            if the Sun, Venus and Mars are in the 4th, lOth and 11th from the lord of Lagna
            the above Yoga is caused.
    """
    _hari = hari_yoga(chart_1d)
    _hara = hara_yoga(chart_1d)
    _brahma = brahma_yoga(chart_1d, method=method) 
    return _hari or _hara or _brahma

def harihara_brahma_yoga_from_planet_positions(planet_positions,method=1):
    """
        BVR-51 Definition per BV Raman. 
            If benefics are in the 8th or 12th from the 2nd lord OR 
            if Jupiter, the Moon and Mercury are in the 4th, 9th and 8th from the 7th lord OR 
            if the Sun, Venus and Mars are in the 4th, lOth and 11th from the lord of Lagna
            the above Yoga is caused.
    """
    _hari = hari_yoga_from_planet_positions(planet_positions)
    _hara = hara_yoga_from_planet_positions(planet_positions)
    _brahma = brahma_yoga_from_planet_positions(planet_positions, method=method)
    return _hari or _hara or _brahma
def harihara_brahma_yoga_from_jd_place(jd, place, divisional_chart_factor=1,method=1):
    """
        BVR-51 Definition per BV Raman. 
            If benefics are in the 8th or 12th from the 2nd lord OR 
            if Jupiter, the Moon and Mercury are in the 4th, 9th and 8th from the 7th lord OR 
            if the Sun, Venus and Mars are in the 4th, lOth and 11th from the lord of Lagna
            the above Yoga is caused.
    """
    _hari = hari_yoga_from_jd_place(jd, place, divisional_chart_factor)
    _hara = hara_yoga_from_jd_place(jd, place, divisional_chart_factor)
    _brahma = brahma_yoga_from_jd_place(jd, place, divisional_chart_factor, method=method)
    return _hari or _hara or _brahma
def kahala_yoga(chart_1d):
    """ BVR-15 Kahala Yoga: L4 and L9 in mutual Kendras, and L1 is strong. """
    return _kahala_yoga_calculation(chart_1d=chart_1d)

def kahala_yoga_from_planet_positions(planet_positions):
    """ BVR-15 Kahala Yoga: L4 and L9 in mutual Kendras, and L1 is strong. """
    return _kahala_yoga_calculation(planet_positions=planet_positions)

def kahala_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-15 Kahala Yoga: L4 and L9 in mutual Kendras, and L1 is strong. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kahala_yoga_calculation(planet_positions=pp)

def _kahala_yoga_calculation(chart_1d=None, planet_positions=None):
    """ BVR-15 Kahala Yoga: L4 and L9 in mutual Kendras, and L1 is strong. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_h = p_to_h[const._ascendant_symbol]

    # 1. Identify Lords
    l1 = (house.house_owner_from_planet_positions(planet_positions, asc_h) 
          if planet_positions else house.house_owner(chart_1d, asc_h))
    
    l4_idx = (asc_h + const.HOUSE_4) % 12
    l4 = (house.house_owner_from_planet_positions(planet_positions, l4_idx) 
          if planet_positions else house.house_owner(chart_1d, l4_idx))
    
    l9_idx = (asc_h + const.HOUSE_9) % 12
    l9 = (house.house_owner_from_planet_positions(planet_positions, l9_idx) 
          if planet_positions else house.house_owner(chart_1d, l9_idx))

    # 2. Check if L1 is strong (in Kendra or Trine from Lagna)
    l1_h = p_to_h[l1]
    strong_houses = quadrants_of_the_house(asc_h) + trines_of_the_house(asc_h)
    if l1_h not in strong_houses:
        return False

    # 3. Check if L4 and L9 are in Kendras from each other
    l4_h = p_to_h[l4]
    l9_h = p_to_h[l9]
    
    # Position of L9 relative to L4 (1-indexed offset converted to 0-indexed math)
    relative_pos = (l9_h - l4_h) % 12
    # Kendras are 1st (0), 4th (3), 7th (6), and 10th (9) positions
    kendras_relative = [const.HOUSE_1, const.HOUSE_4, const.HOUSE_7, const.HOUSE_10]
    
    return relative_pos in kendras_relative
def mahabhagya_yoga(chart_1d, gender=0, day_time_birth=True):
    """ BVR-25 Mahabhagya Yoga: Formed based on gender, time of birth, and sign types. """
    return _mahabhagya_yoga_calculation(chart_1d=chart_1d, gender=gender, day_time_birth=day_time_birth)

def mahabhagya_yoga_from_planet_positions(planet_positions, gender=0, day_time_birth=True):
    """ BVR-25 Mahabhagya Yoga: Formed based on gender, time of birth, and sign types. """
    return _mahabhagya_yoga_calculation(planet_positions=planet_positions, gender=gender, day_time_birth=day_time_birth)

def mahabhagya_yoga_from_jd_place(jd, place, divisional_chart_factor=1, gender=0,**kwargs):
    """ BVR-25 Mahabhagya Yoga: Formed based on gender, time of birth, and sign types. """
    sun_rise = drik.sunrise(jd, place)[0] # local_time_in_float_hours
    sun_set = drik.sunset(jd, place)[0]
    _, _, _, fh = utils.jd_to_local(jd, place)
    
    # Birth is day-time if it falls between sunrise and sunset
    day_time_birth = sun_rise <= fh <= sun_set
    
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mahabhagya_yoga_calculation(planet_positions=pp, gender=gender, day_time_birth=day_time_birth)

def _mahabhagya_yoga_calculation(chart_1d=None, planet_positions=None, gender=0, day_time_birth=True):
    """ BVR-25 Mahabhagya Yoga: Formed based on gender, time of birth, and sign types. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_h = p_to_h[const._ascendant_symbol]
    sun_h = p_to_h[const.SUN_ID]
    moon_h = p_to_h[const.MOON_ID]

    # Sign check using library constants
    def _is_odd(h_idx): return h_idx in const.odd_signs
    def _is_even(h_idx): return h_idx in const.even_signs

    if gender == 0:  # Male
        # Man: Day birth, Sun, Moon, and Lagna in odd signs
        if day_time_birth and _is_odd(sun_h) and _is_odd(moon_h) and _is_odd(asc_h):
            return True
    else:  # Female
        # Woman: Night birth, Sun, Moon, and Lagna in even signs
        if not day_time_birth and _is_even(sun_h) and _is_even(moon_h) and _is_even(asc_h):
            return True

    return False
def sreenatha_yoga(chart_1d):
    """ 
    BVR-31 Sreenatha Yoga: The lord of the 7th should be invariably exalted in the 10th, 
    the lord of which, in turn, must be with the 9th lord. 
    """
    return _sreenatha_yoga_calculation(chart_1d=chart_1d)

def sreenatha_yoga_from_planet_positions(planet_positions):
    """ 
    BVR-31 Sreenatha Yoga: The lord of the 7th should be invariably exalted in the 10th, 
    the lord of which, in turn, must be with the 9th lord. 
    """
    return _sreenatha_yoga_calculation(planet_positions=planet_positions)

def sreenatha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
    BVR-31 Sreenatha Yoga: The lord of the 7th should be invariably exalted in the 10th, 
    the lord of which, in turn, must be with the 9th lord. 
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sreenatha_yoga_calculation(planet_positions=pp)
def _sreenatha_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
    BVR-31 Sreenatha Yoga: The lord of the 7th should be invariably exalted in the 10th, 
    the lord of which, in turn, must be with the 9th lord. 
    """
    
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    planet_to_house_map = utils.get_planet_to_house_dict_from_chart(chart_1d)
    ascendant_house = planet_to_house_map[const._ascendant_symbol]
    
    # Target House Rasi Indices (Offsets from Lagna)
    # BV Raman mentions 7th, 9th, and 10th houses.
    house_7_idx = (ascendant_house + const.HOUSE_7) % 12
    house_9_idx = (ascendant_house + const.HOUSE_9) % 12
    house_10_idx = (ascendant_house + const.HOUSE_10) % 12
    
    # Identify the Lords (Avoiding dual-lord ambiguity for chart_1d)
    if planet_positions:
        lord_of_seventh = house.house_owner_from_planet_positions(planet_positions, house_7_idx)
        lord_of_ninth = house.house_owner_from_planet_positions(planet_positions, house_9_idx)
        lord_of_tenth = house.house_owner_from_planet_positions(planet_positions, house_10_idx)
    else:
        lord_of_seventh = house.house_owner(chart_1d, house_7_idx)
        lord_of_ninth = house.house_owner(chart_1d, house_9_idx)
        lord_of_tenth = house.house_owner(chart_1d, house_10_idx)

    # Where the planets are actually sitting
    house_of_seventh_lord = planet_to_house_map[lord_of_seventh]
    house_of_ninth_lord = planet_to_house_map[lord_of_ninth]
    house_of_tenth_lord = planet_to_house_map[lord_of_tenth]

    # Condition 1: The 10th house sign must be the exaltation sign for the 7th Lord
    is_tenth_house_exaltation_sign = const.house_strengths_of_planets[lord_of_seventh][house_10_idx] >= const._EXALTED_UCCHAM
    
    # Condition 2: The 7th Lord must actually be placed in that 10th house
    is_seventh_lord_in_tenth = (house_of_seventh_lord == house_10_idx)
    
    # Condition 3: The 10th Lord must be conjunct (in the same house) as the 9th Lord
    is_tenth_lord_with_ninth_lord = (house_of_tenth_lord == house_of_ninth_lord)
    
    return is_tenth_house_exaltation_sign and is_seventh_lord_in_tenth and is_tenth_lord_with_ninth_lord
def _malika_yoga_calculation(start_house_index, chart_1d=None, planet_positions=None):
    """
        BVR 32 to 43 Malika Yoga: Checks if planets 0-6 occupy 7 contiguous houses 
        starting from start_house_index using house mapping.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # 1. Define the target range of 7 houses
    target_houses = [(start_house_index + i) % 12 for i in SUN_TO_SATURN]
    
    # 2. Track which of the 7 houses are occupied by at least one classical planet
    occupied_houses = set()
    
    for p in SUN_TO_SATURN:
        p_house = p_to_h[p]
        if p_house in target_houses:
            occupied_houses.add(p_house)
        else:
            # If any classical planet is outside the 7-house range, 
            # it cannot be a Malika yoga starting from that house.
            return False
            
    # 3. Final Check: Are all 7 houses in the range occupied?
    # Because we have 7 planets and 7 houses, if all planets are in range 
    # and all houses are occupied, it means there is exactly one planet per house.
    return len(occupied_houses) == 7
def lagna_malika_yoga(chart_1d):
    """
        BVR-32 Lagna Malika Yoga: Malika Yoga Starting from 1st House
    """
    return _lagna_malika_yoga_calc(chart_1d=chart_1d)

def lagna_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-32 Lagna Malika Yoga: Malika Yoga Starting from 1st House
    """
    return _lagna_malika_yoga_calc(planet_positions=planet_positions)

def lagna_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-32 Lagna Malika Yoga: Malika Yoga Starting from 1st House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _lagna_malika_yoga_calc(planet_positions=pp)

def _lagna_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-32 Lagna Malika Yoga: Malika Yoga Starting from 1st House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return _malika_yoga_calculation(p_to_h[const._ascendant_symbol], chart_1d=chart_1d)
def dhana_malika_yoga(chart_1d):
    """
        BVR-33 Dhana Malika Yoga: Malika Yoga Starting from 2nd House
    """
    return _dhana_malika_yoga_calc(chart_1d=chart_1d)

def dhana_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-33 Dhana Malika Yoga: Malika Yoga Starting from 2nd House
    """
    return _dhana_malika_yoga_calc(planet_positions=planet_positions)

def dhana_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-33 Dhana Malika Yoga: Malika Yoga Starting from 2nd House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_malika_yoga_calc(planet_positions=pp)

def _dhana_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-33 Dhana Malika Yoga: Malika Yoga Starting from 2nd House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_2) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def vikrama_malika_yoga(chart_1d):
    """
        BVR-34 Vikram  Malika Yoga: Malika Yoga Starting from 3rd House
    """
    return _vikrama_malika_yoga_calc(chart_1d=chart_1d)

def vikrama_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-34 Vikram  Malika Yoga: Malika Yoga Starting from 3rd House
    """
    return _vikrama_malika_yoga_calc(planet_positions=planet_positions)

def vikrama_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-34 Vikram  Malika Yoga: Malika Yoga Starting from 3rd House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vikrama_malika_yoga_calc(planet_positions=pp)

def _vikrama_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-34 Vikram  Malika Yoga: Malika Yoga Starting from 3rd House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_3) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def sukha_malika_yoga(chart_1d):
    """
        BVR-35 Sukha Malika Yoga: Malika Yoga Starting from 4th House
    """
    return _sukha_malika_yoga_calc(chart_1d=chart_1d)

def sukha_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-35 Sukha Malika Yoga: Malika Yoga Starting from 4th House
    """
    return _sukha_malika_yoga_calc(planet_positions=planet_positions)

def sukha_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-35 Sukha Malika Yoga: Malika Yoga Starting from 4th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sukha_malika_yoga_calc(planet_positions=pp)

def _sukha_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-35 Sukha Malika Yoga: Malika Yoga Starting from 4th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_4) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def putra_malika_yoga(chart_1d):
    """
        BVR-36 Puthra Malika Yoga: Malika Yoga Starting from 5th House
    """
    return _putra_malika_yoga_calc(chart_1d=chart_1d)

def putra_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-36 Puthra Malika Yoga: Malika Yoga Starting from 5th House
    """
    return _putra_malika_yoga_calc(planet_positions=planet_positions)

def putra_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-36 Puthra Malika Yoga: Malika Yoga Starting from 5th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _putra_malika_yoga_calc(planet_positions=pp)

def _putra_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-36 Puthra Malika Yoga: Malika Yoga Starting from 5th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_5) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def satru_malika_yoga(chart_1d):
    """
        BVR-37 Sathru Malika Yoga: Malika Yoga Starting from 6th House
    """
    return _satru_malika_yoga_calc(chart_1d=chart_1d)

def satru_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-37 Sathru Malika Yoga: Malika Yoga Starting from 6th House
    """
    return _satru_malika_yoga_calc(planet_positions=planet_positions)

def satru_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-37 Sathru Malika Yoga: Malika Yoga Starting from 6th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _satru_malika_yoga_calc(planet_positions=pp)

def _satru_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-37 Sathru Malika Yoga: Malika Yoga Starting from 6th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_6) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def kalatra_malika_yoga(chart_1d):
    """
        BVR-38 Kalathra Malika Yoga: Malika Yoga Starting from 7th House
    """
    return _kalatra_malika_yoga_calc(chart_1d=chart_1d)

def kalatra_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-38 Kalathra Malika Yoga: Malika Yoga Starting from 7th House
    """
    return _kalatra_malika_yoga_calc(planet_positions=planet_positions)

def kalatra_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-38 Kalathra Malika Yoga: Malika Yoga Starting from 7th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kalatra_malika_yoga_calc(planet_positions=pp)

def _kalatra_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-38 Kalathra Malika Yoga: Malika Yoga Starting from 7th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_7) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def randhra_malika_yoga(chart_1d):
    """
        BVR-39 Randhra Malika Yoga: Malika Yoga Starting from 8th House
    """
    return _randhra_malika_yoga_calc(chart_1d=chart_1d)

def randhra_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-39 Randhra Malika Yoga: Malika Yoga Starting from 8th House
    """
    return _randhra_malika_yoga_calc(planet_positions=planet_positions)

def randhra_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-39 Randhra Malika Yoga: Malika Yoga Starting from 8th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _randhra_malika_yoga_calc(planet_positions=pp)

def _randhra_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-39 Randhra Malika Yoga: Malika Yoga Starting from 8th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_8) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def bhagya_malika_yoga(chart_1d):
    """
        BVR-40 Bhagya Malika Yoga: Malika Yoga Starting from 9th House
    """
    return _bhagya_malika_yoga_calc(chart_1d=chart_1d)

def bhagya_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-40 Bhagya Malika Yoga: Malika Yoga Starting from 9th House
    """
    return _bhagya_malika_yoga_calc(planet_positions=planet_positions)

def bhagya_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-40 Bhagya Malika Yoga: Malika Yoga Starting from 9th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bhagya_malika_yoga_calc(planet_positions=pp)

def _bhagya_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-40 Bhagya Malika Yoga: Malika Yoga Starting from 9th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_9) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def karma_malika_yoga(chart_1d):
    """
        BVR-41 Karma Malika Yoga: Malika Yoga Starting from 10th House
    """
    return _karma_malika_yoga_calc(chart_1d=chart_1d)

def karma_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-41 Karma Malika Yoga: Malika Yoga Starting from 10th House
    """
    return _karma_malika_yoga_calc(planet_positions=planet_positions)

def karma_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-41 Karma Malika Yoga: Malika Yoga Starting from 10th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _karma_malika_yoga_calc(planet_positions=pp)

def _karma_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-41 Karma Malika Yoga: Malika Yoga Starting from 10th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_10) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def laabha_malika_yoga(chart_1d):
    """
        BVR-42 Laabha Malika Yoga: Malika Yoga Starting from 11th House
    """
    return _laabha_malika_yoga_calc(chart_1d=chart_1d)

def laabha_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-42 Laabha Malika Yoga: Malika Yoga Starting from 11th House
    """
    return _laabha_malika_yoga_calc(planet_positions=planet_positions)

def laabha_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-42 Laabha Malika Yoga: Malika Yoga Starting from 11th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _laabha_malika_yoga_calc(planet_positions=pp)

def _laabha_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-42 Laabha Malika Yoga: Malika Yoga Starting from 11th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_11) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def vyaya_malika_yoga(chart_1d):
    """
        BVR-43 Vyaya Malika Yoga: Malika Yoga Starting from 12th House
    """
    return _vyaya_malika_yoga_calc(chart_1d=chart_1d)

def vyaya_malika_yoga_from_planet_positions(planet_positions):
    """
        BVR-43 Vyaya Malika Yoga: Malika Yoga Starting from 12th House
    """
    return _vyaya_malika_yoga_calc(planet_positions=planet_positions)

def vyaya_malika_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR-43 Vyaya Malika Yoga: Malika Yoga Starting from 12th House
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vyaya_malika_yoga_calc(planet_positions=pp)

def _vyaya_malika_yoga_calc(chart_1d=None, planet_positions=None):
    """
        BVR-43 Vyaya Malika Yoga: Malika Yoga Starting from 12th House
    """
    if planet_positions: chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    # Using HOUSE_12 offset
    start_h = (p_to_h[const._ascendant_symbol] + const.HOUSE_12) % 12
    return _malika_yoga_calculation(start_h, chart_1d=chart_1d)
def parijatha_yoga(chart_1d):
    """ 
        BVR-47 Paarijaatha/Kalpadruma Yoga: The lord of the sign in which the lord of the house occupied by the Ascendant
        lord, or the lord of Navamsa occupied by the lord of the Rasi in which the Ascendant lord is posited, shall
        join a quadrant, a trine or his own or exaltation places.
    """
    return _parijatha_yoga_calculation(chart_1d=chart_1d)

def parijatha_yoga_from_planet_positions(planet_positions):
    """ 
        BVR-47 Paarijaatha/Kalpadruma Yoga: The lord of the sign in which the lord of the house occupied by the Ascendant
        lord, or the lord of Navamsa occupied by the lord of the Rasi in which the Ascendant lord is posited, shall
        join a quadrant, a trine or his own or exaltation places.
    """
    return _parijatha_yoga_calculation(planet_positions=planet_positions)
def parijatha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        BVR-47 Paarijaatha/Kalpadruma Yoga: The lord of the sign in which the lord of the house occupied by the Ascendant
        lord, or the lord of Navamsa occupied by the lord of the Rasi in which the Ascendant lord is posited, shall
        join a quadrant, a trine or his own or exaltation places.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vyaya_malika_yoga_calc(planet_positions=pp)
def _parijatha_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
        BVR-47 Paarijaatha/Kalpadruma Yoga: The lord of the sign in which the lord of the house occupied by the Ascendant
        lord, or the lord of Navamsa occupied by the lord of the Rasi in which the Ascendant lord is posited, shall
        join a quadrant, a trine or his own or exaltation places.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    planet_to_house_map = utils.get_planet_to_house_dict_from_chart(chart_1d)
    ascendant_house = planet_to_house_map[const._ascendant_symbol]

    # 1. Identify the Lagna Lord
    if planet_positions:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, ascendant_house)
    else:
        lagna_lord = house.house_owner(chart_1d, ascendant_house)
    
    # 2. Identify the house where Lagna Lord is posited
    house_of_lagna_lord = planet_to_house_map[lagna_lord]

    # 3. Identify the Dispositor of the Lagna Lord (Lord of the sign where L1 sits)
    if planet_positions:
        dispositor_of_lagna_lord = house.house_owner_from_planet_positions(planet_positions, house_of_lagna_lord)
    else:
        dispositor_of_lagna_lord = house.house_owner(chart_1d, house_of_lagna_lord)
    
    # 4. Identify the house where that Dispositor is posited
    house_of_dispositor = planet_to_house_map[dispositor_of_lagna_lord]

    # 5. Identify the "Target Planet" (Dispositor of the Dispositor)
    if planet_positions:
        target_planet = house.house_owner_from_planet_positions(planet_positions, house_of_dispositor)
    else:
        target_planet = house.house_owner(chart_1d, house_of_dispositor)
    
    target_planet_house = planet_to_house_map[target_planet]

    # --- Condition Checks for Target Planet ---
    # Check A: Is it in a Kendra or Trikona relative to Lagna?
    kendra_trikona_houses = quadrants_of_the_house(ascendant_house) + trines_of_the_house(ascendant_house)
    is_in_good_house = target_planet_house in kendra_trikona_houses

    # Check B: Is it in its own sign or exalted?
    dignity = const.house_strengths_of_planets[target_planet][target_planet_house]
    is_dignified = dignity >= const._EXALTED_UCCHAM

    return is_in_good_house or is_dignified
def gaja_yoga(chart_1d, method=1):
    """
    BVR-48 Gaja Yoga:
    Method 1 (BVR): The lord of the 9th from the 11th should occupy the 11th 
    in conjunction with the Moon and aspected by the lord of the 11th.
    Method 2 (Standard): 9th lord from Lagna and Moon occupy the 11th with the Moon.
    """
    return _gaja_yoga_calculation(chart_1d=chart_1d, method=method)

def gaja_yoga_from_planet_positions(planet_positions, method=1):
    """
    BVR-48 Gaja Yoga:
    Method 1 (BVR): The lord of the 9th from the 11th should occupy the 11th 
    in conjunction with the Moon and aspected by the lord of the 11th.
    Method 2 (Standard): 9th lord from Lagna and Moon occupy the 11th with the Moon.
    """
    return _gaja_yoga_calculation(planet_positions=planet_positions, method=method)

def gaja_yoga_from_jd_place(jd, place, method=1, divisional_chart_factor=1):
    """
    BVR-48 Gaja Yoga:
    Method 1 (BVR): The lord of the 9th from the 11th should occupy the 11th 
    in conjunction with the Moon and aspected by the lord of the 11th.
    Method 2 (Standard): 9th lord from Lagna and Moon occupy the 11th with the Moon.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _gaja_yoga_calculation(planet_positions=pp, method=method)

def _gaja_yoga_calculation(chart_1d=None, planet_positions=None, method=1):
    """
    BVR-48 Gaja Yoga:
    Method 1 (BVR): The lord of the 9th from the 11th should occupy the 11th 
    in conjunction with the Moon and aspected by the lord of the 11th.
    Method 2 (Standard): 9th lord from Lagna and Moon occupy the 11th with the Moon.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    
    h11 = (asc_h + const.HOUSE_11) % 12
    moon_h = p_to_h[const.MOON_ID]
    moon_in_11 = (moon_h == h11)

    if method == 1:
        h_9_from_11 = (h11 + const.HOUSE_9) % 12
        if planet_positions is not None:
            l11 = int(house.house_owner_from_planet_positions(planet_positions, h11))
            l9_from_11 = int(house.house_owner_from_planet_positions(planet_positions, h_9_from_11))
        else:
            l11 = int(house.house_owner(chart_1d, h11))
            l9_from_11 = int(house.house_owner(chart_1d, h_9_from_11))

        target_in_11 = (p_to_h[l9_from_11] == h11)
        
        # Checking both Graha and Rasi aspects to match BVR test data
        # l11 aspects l9_from_11
        graha_aspects = house.aspected_planets_of_the_planet(chart_1d, l11)
        l11_h = p_to_h[l11]
        rasi_aspects = house.aspected_planets_of_the_raasi(chart_1d, l11_h)
        aspected = (l9_from_11 in graha_aspects) or (l9_from_11 in rasi_aspects)
        
        return moon_in_11 and target_in_11 and aspected

    else:
        h9_lagna = (asc_h + const.HOUSE_9) % 12
        h9_moon = (moon_h + const.HOUSE_9) % 12
        
        if planet_positions is not None:
            l9_lagna = int(house.house_owner_from_planet_positions(planet_positions, h9_lagna))
            l9_moon = int(house.house_owner_from_planet_positions(planet_positions, h9_moon))
        else:
            l9_lagna = int(house.house_owner(chart_1d, h9_lagna))
            l9_moon = int(house.house_owner(chart_1d, h9_moon))
            
        l9_lagna_in_11 = (p_to_h[l9_lagna] == h11)
        l9_moon_in_11 = (p_to_h[l9_moon] == h11)
        return moon_in_11 and l9_lagna_in_11 and l9_moon_in_11
def kalanidhi_yoga(chart_1d):
    """
    BVR-49 Kalanidhi Yoga (B.V. Raman #49):
    Jupiter must join or be aspected by Mercury and Venus either in the 2nd 
    or in the 5th house; Jupiter must occupy the 2nd or 5th identical 
    with the swakshetra (sign) of Mercury or Venus.
    """
    return _kalanidhi_yoga_calculation(chart_1d=chart_1d)

def kalanidhi_yoga_from_planet_positions(planet_positions):
    """
    BVR-49 Kalanidhi Yoga (B.V. Raman #49):
    Jupiter must join or be aspected by Mercury and Venus either in the 2nd 
    or in the 5th house; Jupiter must occupy the 2nd or 5th identical 
    with the swakshetra (sign) of Mercury or Venus.
    """
    return _kalanidhi_yoga_calculation(planet_positions=planet_positions)

def kalanidhi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-49 Kalanidhi Yoga (B.V. Raman #49):
    Jupiter must join or be aspected by Mercury and Venus either in the 2nd 
    or in the 5th house; Jupiter must occupy the 2nd or 5th identical 
    with the swakshetra (sign) of Mercury or Venus.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kalanidhi_yoga_calculation(planet_positions=pp)

def _kalanidhi_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    BVR-49 Kalanidhi Yoga (B.V. Raman #49):
    Jupiter must join or be aspected by Mercury and Venus either in the 2nd 
    or in the 5th house; Jupiter must occupy the 2nd or 5th identical 
    with the swakshetra (sign) of Mercury or Venus.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    # Meaningful mapping of planetary positions
    planet_to_house_map = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = planet_to_house_map.get(const._ascendant_symbol)
    if lagna_house is None:
        return False

    # 1. Identify Target Houses (2nd and 5th from Lagna)
    second_house_index = (lagna_house + const.HOUSE_2) % 12
    fifth_house_index = (lagna_house + const.HOUSE_5) % 12
    
    # 2. Jupiter Position Check (Jupiter ID = 4)
    jupiter_house = planet_to_house_map.get(const.JUPITER_ID)
    if jupiter_house is None or int(jupiter_house) not in [second_house_index, fifth_house_index]:
        return False
    jupiter_house = int(jupiter_house)

    # 3. Resolve Influence: Mercury (3) and Venus (5)
    # Check for Conjunction (Joined)
    is_mercury_joined = (planet_to_house_map.get(const.MERCURY_ID) == jupiter_house)
    is_venus_joined = (planet_to_house_map.get(const.JUPITER_ID) == jupiter_house)
    
    # Check for Aspect (Aspected by)
    # Using house.aspected_planets_of_the_planet for Graha Drishti
    mercury_aspects = house.aspected_planets_of_the_planet(chart_1d, const.MERCURY_ID)
    venus_aspects = house.aspected_planets_of_the_planet(chart_1d, const.VENUS_ID)
    
    # Convert aspect lists to integers for comparison
    mer_asp_ints = [int(p) for p in mercury_aspects if str(p).isdigit()]
    ven_asp_ints = [int(p) for p in venus_aspects if str(p).isdigit()]

    has_mercury_influence = is_mercury_joined or (const.JUPITER_ID in mer_asp_ints)
    has_venus_influence = is_venus_joined or (const.JUPITER_ID in ven_asp_ints)

    # 4. Swakshetra Check: Jupiter in sign of Mercury (2,5) or Venus (1,6)
    jupiter_sign_owner = ( house.house_owner_from_planet_positions(planet_positions,jupiter_house) if planet_positions
                           else int(house.house_owner(chart_1d, jupiter_house)) )
    is_in_mercury_or_venus_sign = jupiter_sign_owner in [const.MERCURY_ID, const.JUPITER_ID]

    # BVR nuance: If Jupiter is conjoined with both Mercury and Venus in 2nd/5th, 
    # it satisfies the core strength of Kalanidhi even if the Rasi owner is different.
    is_strong_conjunction = is_mercury_joined and is_venus_joined

    return has_mercury_influence and has_venus_influence and \
           (is_in_mercury_or_venus_sign or is_strong_conjunction)

def garuda_yoga(chart_1d_rasi, chart_1d_navamsa, is_shukla_paksha, is_daytime_birth):
    """
    BVR-66 Garuda Yoga (B.V. Raman #58):
    The lord of Navamsa occupied by the Moon should be exalted in Rasi.
    Birth should occur during daytime when the Moon is waxing.
    """
    return _garuda_yoga_calculation(chart_1d_rasi=chart_1d_rasi, 
                                   chart_1d_navamsa=chart_1d_navamsa, 
                                   is_shukla_paksha=is_shukla_paksha, 
                                   is_daytime_birth=is_daytime_birth)

def garuda_yoga_from_planet_positions(pp_rasi, pp_navamsa, is_shukla_paksha, is_daytime_birth):
    """
    BVR-66 Garuda Yoga
    The lord of Navamsa occupied by the Moon should be exalted in Rasi.
    Birth should occur during daytime when the Moon is waxing.
    """
    return _garuda_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa,
                                    is_shukla_paksha=is_shukla_paksha, is_daytime_birth=is_daytime_birth)

def garuda_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """
    BVR-66 Garuda Yoga
    The lord of Navamsa occupied by the Moon should be exalted in Rasi.
    Birth should occur during daytime when the Moon is waxing.
    """
    # 1. Determine Shukla Paksha (0-14 is Waxing)
    tithi_val = drik.tithi(jd, place)[0]
    is_shukla = tithi_val < 15
    
    # 2. Determine Daytime Birth using fh (birth-time in hours)
    _, _, _, fh = utils.jd_to_local(jd, place)
    sunrise_time = drik.sunrise(jd, place)[0]
    sunset_time = drik.sunset(jd, place)[0]
    is_day = (sunrise_time <= fh <= sunset_time)
    
    # 3. Generate Charts
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    
    return _garuda_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa,
                                    is_shukla_paksha=is_shukla, is_daytime_birth=is_day)

def _garuda_yoga_calculation(planet_positions_rasi=None,chart_1d_rasi=None, planet_positions_navamsa=None,
                             chart_1d_navamsa=None, is_shukla_paksha=None, is_daytime_birth=None):
    """
    BVR-66 Garuda Yoga
    The lord of Navamsa occupied by the Moon should be exalted in Rasi.
    Birth should occur during daytime when the Moon is waxing.
    """
    # Core conditions check
    if not (is_shukla_paksha and is_daytime_birth):
        return False
    if planet_positions_rasi is not None:
        chart_1d_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    if chart_1d_rasi is None: return False
    if planet_positions_navamsa is not None:
        chart_1d_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d_navamsa is None: return False
    # Map planets in Navamsa and Rasi
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_1d_navamsa)
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_1d_rasi)
    
    # 1. Find Moon's sign in Navamsa
    moon_nav_h_idx = p_to_h_nav.get(const.MOON_ID)
    if moon_nav_h_idx is None: 
        return False
    
    # 2. Get the lord of that Navamsa sign
    # house_owner takes the chart and the house index
    nav_lord_of_moon = ( house.house_owner_from_planet_positions(planet_positions_navamsa, moon_nav_h_idx) if planet_positions_navamsa
        else int(house.house_owner(chart_1d_navamsa, moon_nav_h_idx)) )
    
    # 3. Check if that specific planet is exalted in the Rasi chart
    rasi_house_of_lord = p_to_h_rasi.get(nav_lord_of_moon)
    if rasi_house_of_lord is None: 
        return False
    
    return const.house_strengths_of_planets[nav_lord_of_moon][rasi_house_of_lord] >= const._EXALTED_UCCHAM
def _sankhya_yoga_calculation(chart_1d=None, planet_positions=None, required_count=7):
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return len(set([p_to_h[p] for p in SUN_TO_SATURN]))==required_count
def vallaki_yoga(chart_1d):
    """ BVR-91 Vallaki Yoga: 7 planets in 7 signs (B.V. Raman #82)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=7)

def vallaki_yoga_from_planet_positions(planet_positions):
    """ BVR-91 Vallaki Yoga: 7 planets in 7 signs (B.V. Raman #82)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=7)

def vallaki_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ BVR-91 Vallaki Yoga: 7 planets in 7 signs (B.V. Raman #82)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=7)
def dama_yoga(chart_1d):
    """BVR-92 Dama/Damni Yoga: 7 planets in 6 signs (B.V. Raman #83)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=6)

def dama_yoga_from_planet_positions(planet_positions):
    """BVR-92 Dama/Damni Yoga: 7 planets in 6 signs (B.V. Raman #83)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=6)

def dama_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """BVR-92 Dama/Damni Yoga: 7 planets in 6 signs (B.V. Raman #83)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=6)
def kedara_yoga(chart_1d):
    """BVR-94 Kedara Yoga: 7 planets in 4 signs (B.V. Raman #85)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=4)

def kedara_yoga_from_planet_positions(planet_positions):
    """BVR-94 Kedara Yoga: 7 planets in 4 signs (B.V. Raman #85)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=4)

def kedara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """BVR-94 Kedara Yoga: 7 planets in 4 signs (B.V. Raman #85)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=4)
def sula_yoga(chart_1d):
    """BVR-95 Sula Yoga: 7 planets in 3 signs (B.V. Raman #86)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=3)

def sula_yoga_from_planet_positions(planet_positions):
    """BVR-95 Sula Yoga: 7 planets in 3 signs (B.V. Raman #86)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=3)

def sula_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """BVR-95 Sula Yoga: 7 planets in 3 signs (B.V. Raman #86)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=3)
def yuga_yoga(chart_1d):
    """BVR-96 Yuga Yoga: 7 planets in 2 signs (B.V. Raman #87)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=2)

def yuga_yoga_from_planet_positions(planet_positions):
    """BVR-96 Yuga Yoga: 7 planets in 2 signs (B.V. Raman #87)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=2)

def yuga_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """BVR-96 Yuga Yoga: 7 planets in 2 signs (B.V. Raman #87)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=2)
def gola_yoga(chart_1d):
    """BVR-97 Gola Yoga: 7 planets in 1 sign (B.V. Raman #88)"""
    return _sankhya_yoga_calculation(chart_1d=chart_1d, required_count=1)

def gola_yoga_from_planet_positions(planet_positions):
    """BVR-97 Gola Yoga: 7 planets in 1 sign (B.V. Raman #88)"""
    return _sankhya_yoga_calculation(planet_positions=planet_positions, required_count=1)

def gola_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """BVR-97 Gola Yoga: 7 planets in 1 sign (B.V. Raman #88)"""
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sankhya_yoga_calculation(planet_positions=pp, required_count=1)
def _dhur_yoga_calculation(chart_1d=None,planet_positions=None):
    """ the lord of the 10th is situated in the 6th, 8th or 12th """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    sixth_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_6)%12
    eighth_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_8)%12
    tenth_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_10)%12
    twelth_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_12)%12
    if planet_positions is not None:
        lord_of_tenth = house.house_owner_from_planet_positions(planet_positions, tenth_house)
    else:
        lord_of_tenth = house.house_owner(chart_1d, tenth_house)
    return p_to_h[lord_of_tenth]==sixth_house or p_to_h[lord_of_tenth]==eighth_house or p_to_h[lord_of_tenth]== twelth_house 
def dhur_yoga(chart_1d):
    """ the lord of the 10th is situated in the 6th, 8th or 12th """
    return _dhur_yoga_calculation(chart_1d=chart_1d)
def dhur_yoga_from_planet_positions(planet_positions):
    """ the lord of the 10th is situated in the 6th, 8th or 12th """
    return _dhur_yoga_calculation(planet_positions=planet_positions)
def dhur_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ the lord of the 10th is situated in the 6th, 8th or 12th """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhur_yoga_calculation(planet_positions=pp)
def _dharidhra_yoga_bv_raman(chart_1d=None,planet_positions=None,chart_navamsa=None,planet_positions_navamsa=None,
                                natural_benefics=None,natural_malefics=None):
    if _dharidhra_yoga_144_calculation(chart_1d, planet_positions): return True
    if _dharidhra_yoga_145_calculation(chart_1d, planet_positions): return True
    if _dharidhra_yoga_146_calculation(chart_1d, planet_positions): return True
    if _dharidhra_yoga_147_calculation(chart_1d, planet_positions): return True
    if _dharidhra_yoga_148_calculation(chart_1d, planet_positions,natural_malefics=natural_malefics): return True
    if _dharidhra_yoga_149_calculation(chart_1d, planet_positions,natural_malefics=natural_malefics): return True
    if _dharidhra_yoga_150_calculation(chart_1d, planet_positions,natural_benefics=natural_benefics): return True
    if _dharidhra_yoga_151_calculation(chart_1d, planet_positions): return True
    if _dharidhra_yoga_152_calculation(chart_1d, planet_positions,natural_malefics=natural_malefics): return True
    if _dharidhra_yoga_153_calculation(chart_rasi=chart_1d, planet_positions_rasi=planet_positions, 
                                     chart_navamsa=chart_navamsa, planet_positions_navamsa=planet_positions_navamsa): return True
    return False
def _dharidhra_yoga_calculation(chart_rasi=None,planet_positions_rasi=None,chart_navamsa=None,
                                planet_positions_navamsa=None,method=None):
    """ 
        BVR 144 to 152
        Method=1 Ref: Medium - What is daridra yoga
        the lord of 2nd or 11th is situated in the 6th, 8th or 12th
        Method = 2 - Ref: BV Raman Dharidhra Yoga #144 to #152
    """
    if method is None: method = const.dharidhdra_yoga_method
    if method==2:
        return _dharidhra_yoga_bv_raman(chart_rasi,planet_positions_rasi,chart_navamsa=chart_navamsa,
                                        planet_positions_navamsa=planet_positions_navamsa)
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h[const._ascendant_symbol]
    second_house = (asc_house+const.HOUSE_2)%12
    sixth_house = (asc_house+const.HOUSE_6)%12
    eighth_house = (asc_house+const.HOUSE_8)%12
    eleventh_house = (asc_house+const.HOUSE_11)%12
    twelth_house = (asc_house+const.HOUSE_12)%12
    if planet_positions_rasi is not None:
        lord_of_second = house.house_owner_from_planet_positions(planet_positions_rasi, second_house)
        lord_of_eleventh = house.house_owner_from_planet_positions(planet_positions_rasi, eleventh_house)
    else:
        lord_of_second = house.house_owner(chart_rasi, second_house)
        lord_of_eleventh = house.house_owner(chart_rasi, eleventh_house)
    second_in_6_8_12 = p_to_h[lord_of_second]==sixth_house or p_to_h[lord_of_second]==eighth_house or p_to_h[lord_of_second]== twelth_house 
    eleventh_in_6_8_12 = p_to_h[lord_of_eleventh]==sixth_house or p_to_h[lord_of_eleventh]==eighth_house or p_to_h[lord_of_eleventh]== twelth_house 
    return second_in_6_8_12 or eleventh_in_6_8_12
def dharidhra_yoga(chart_rasi,chart_navamsa=None,method=None):
    """ 
        BVR 144 to 152
        Method=1 Ref: Medium - What is daridra yoga
        the lord of 2nd or 11th is situated in the 6th, 8th or 12th
        Method = 2 - Ref: BV Raman Dharidhra Yoga #144 to #152
    """
    if method is None: method = const.dharidhdra_yoga_method
    return _dharidhra_yoga_calculation(chart_rasi=chart_rasi,chart_navamsa=chart_navamsa,method=method)
def dharidhra_yoga_from_planet_positions(planet_positions,method=None):
    """ 
        BVR 144 to 152
        Method=1 Ref: Medium - What is daridra yoga
        the lord of 2nd or 11th is situated in the 6th, 8th or 12th
        Method = 2 - Ref: BV Raman Dharidhra Yoga #144 to #152
    """
    if method is None: method = const.dharidhdra_yoga_method
    return _dharidhra_yoga_calculation(planet_positions_rasi=planet_positions,method=method)
def dharidhra_yoga_from_jd_place(jd,place,divisional_chart_factor=1,method=None):
    """ 
        BVR 144 to 152
        Method=1 Ref: Medium - What is daridra yoga
        the lord of 2nd or 11th is situated in the 6th, 8th or 12th
        Method = 2 - Ref: BV Raman Dharidhra Yoga #144 to #152
    """
    if method is None: method = const.dharidhdra_yoga_method
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_calculation(planet_positions_rasi=pp,method=method)
def sareera_soukhya_yoga(chart_1d):
    """
    BVR-108 Sareera Soukhya Yoga
    The Lord of Lagna, Jupiter, or Venus should occupy a quadrant.
    """
    return _sareera_soukhya_calculation(chart_1d=chart_1d)
def sareera_soukhya_yoga_from_planet_positions(planet_positions):
    """
    BVR-108 Sareera Soukhya Yoga
    The Lord of Lagna, Jupiter, or Venus should occupy a quadrant.
    """
    return _sareera_soukhya_calculation(planet_positions=planet_positions)
def sareera_soukhya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-108 Sareera Soukhya Yoga
    The Lord of Lagna, Jupiter, or Venus should occupy a quadrant.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sareera_soukhya_calculation(planet_positions=pp)
def _sareera_soukhya_calculation(chart_1d=None, planet_positions=None):
    """
    BVR-108 Sareera Soukhya Yoga
    The Lord of Lagna, Jupiter, or Venus should occupy a quadrant.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if planet_positions is not None:
        lagna_lord = int(house.house_owner_from_planet_positions(planet_positions, asc_house))
    else:
        lagna_lord = int(house.house_owner(chart_1d, asc_house))
    # Identify Kendras using your lambda
    kendras = quadrants_of_the_house(asc_house)
    # Return True if any of the target planets are in a Kendra
    return any(p_to_h.get(p) in kendras for p in [lagna_lord, const.JUPITER_ID, const.VENUS_ID])
def dehapushti_yoga(chart_1d, natural_benefics=None):
    """
    BVR-109 Dehapushti Yoga
    The Lagna Lord is in a movable sign and is aspected by a benefic.
    """
    return _dehapushti_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)

def dehapushti_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """
    BVR-109 Dehapushti Yoga
    The Lagna Lord is in a movable sign and is aspected by a benefic.
    """
    return _dehapushti_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)

def dehapushti_yoga_from_jd_place(jd, place, divisional_chart_factor=1, natural_benefics=None):
    """
    BVR-109 Dehapushti Yoga
    The Lagna Lord is in a movable sign and is aspected by a benefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dehapushti_calculation(planet_positions=pp, natural_benefics=natural_benefics)

def _dehapushti_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    BVR-109 Dehapushti Yoga
    The Lagna Lord is in a movable sign and is aspected by a benefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if asc_house is None: return False
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    if planet_positions:
        ll = int(house.house_owner_from_planet_positions(planet_positions, asc_house))
    else:
        ll = int(house.house_owner(chart_1d, asc_house))
    ll_house = p_to_h.get(ll)
    if ll_house not in const.movable_signs:
        return False
    # 2. Aspect logic: planet to planet
    aspecting_planets = house.planets_aspecting_the_planet(chart_1d, ll)
    return any(p in _natural_benefics for p in aspecting_planets)
def rogagrastha_yoga(chart_1d, natural_benefics=None):
    """
        BVR-11 Rogagrastha Yoga
        Condition (a): The Lagna Lord is in the 1st House (Lagna) joined by a Dusthana Lord (6th, 8th, or 12th).
        Condition (b): A weak Lagna Lord is situated in a Kendra (1, 4, 7, 10) or a Trikona (1, 5, 9)
    """
    return _rogagrastha_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)

def rogagrastha_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """
        BVR-11 Rogagrastha Yoga
        Condition (a): The Lagna Lord is in the 1st House (Lagna) joined by a Dusthana Lord (6th, 8th, or 12th).
        Condition (b): A weak Lagna Lord is situated in a Kendra (1, 4, 7, 10) or a Trikona (1, 5, 9)
    """
    return _rogagrastha_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)

def rogagrastha_yoga_from_jd_place(jd, place, divisional_chart_factor=1, natural_benefics=None):
    """
        BVR-11 Rogagrastha Yoga
        Condition (a): The Lagna Lord is in the 1st House (Lagna) joined by a Dusthana Lord (6th, 8th, or 12th).
        Condition (b): A weak Lagna Lord is situated in a Kendra (1, 4, 7, 10) or a Trikona (1, 5, 9)
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _rogagrastha_calculation(planet_positions=pp, natural_benefics=natural_benefics)

def _rogagrastha_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        BVR-11 Rogagrastha Yoga
        Condition (a): The Lagna Lord is in the 1st House (Lagna) joined by a Dusthana Lord (6th, 8th, or 12th).
        Condition (b): A weak Lagna Lord is situated in a Kendra (1, 4, 7, 10) or a Trikona (1, 5, 9)
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h.get(const._ascendant_symbol)
    dusthana_houses = dushthanas_of_the_house(asc_house)
    quad_trine_houses = set(quadrants_of_the_house(asc_house) + trines_of_the_house(asc_house))
    if asc_house is None: return False
    if planet_positions:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
        dusthana_lords = [house.house_owner_from_planet_positions(planet_positions, dh) for dh in dusthana_houses]
        quad_trine_lords = [house.house_owner_from_planet_positions(planet_positions, dh) for dh in quad_trine_houses]
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
        dusthana_lords = [int(house.house_owner(chart_1d, dh)) for dh in dusthana_houses]
        quad_trine_lords = [int(house.house_owner(chart_1d, dh)) for dh in quad_trine_houses]
    lagna_lord_house = p_to_h[lagna_lord]
    lagna_lord_house_in_lagna = (lagna_lord_house==asc_house)
    lagna_lord_cojoins_dusthana_lords = any([lagna_lord_house==p_to_h[dl] for dl in dusthana_lords])
    condition_a = lagna_lord_house_in_lagna and lagna_lord_cojoins_dusthana_lords
    lagna_lord_cojoins_quad_trine_lords = any([lagna_lord_house==p_to_h[qtl] for qtl in quad_trine_lords])
    condition_b = lagna_lord_cojoins_quad_trine_lords and const.house_strengths_of_planets[lagna_lord][lagna_lord_house] <= const._NEUTRAL_SAMAM
    return condition_a or condition_b
def krisanga_yoga(chart_rasi, chart_navamsa=None):
    """
    BVR-112/113 Krisanga Yoga  
    Condition 1: Lagna lord in a dry sign or in a sign owned by a dry planet.
    Condition 2: The Navamsa Lagna is owned by a dry planet AND malefics join the Rasi Lagna.
    """
    return _krisanga_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa)

def krisanga_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa=None):
    """
    BVR-112/113 Krisanga Yoga  
    Condition 1: Lagna lord in a dry sign or in a sign owned by a dry planet.
    Condition 2: The Navamsa Lagna is owned by a dry planet AND malefics join the Rasi Lagna.
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _krisanga_yoga_calculation(planet_positions_rasi=planet_positions_rasi,
                                      planet_positions_navamsa=planet_positions_navamsa)

def krisanga_yoga_112_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-112 Krisanga Yoga  
    Lagna lord in a dry sign or in a sign owned by a dry planet.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    # Explicitly calculate D9 (Navamsa) for condition 2 
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _krisanga_yoga_112_calculation(planet_positions_rasi=pp,planet_positions_navamsa=pp_nav, natural_malefics=nm)
def krisanga_yoga_113_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-113 Krisanga Yoga  
    The Navamsa Lagna is owned by a dry planet AND malefics join the Rasi Lagna.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    # Explicitly calculate D9 (Navamsa) for condition 2 
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _krisanga_yoga_113_calculation(planet_positions_rasi=pp,planet_positions_navamsa=pp_nav, natural_malefics=nm)
def _krisanga_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None, natural_malefics=None):
    if _krisanga_yoga_112_calculation(chart_rasi, chart_navamsa, planet_positions_rasi, planet_positions_navamsa, natural_malefics): return True
    _krisanga_yoga_113_calculation(chart_rasi, chart_navamsa, planet_positions_rasi, planet_positions_navamsa, natural_malefics)
def _krisanga_yoga_112_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None, natural_malefics=None):
    """
    BVR-112 Krisanga Yoga  
    Lagna lord in a dry sign or in a sign owned by a dry planet.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if asc_house is None: return False

    if planet_positions_rasi is not None:
        lagna_lord = int(house.house_owner_from_planet_positions(planet_positions_rasi, asc_house))
    else:
        lagna_lord = int(house.house_owner(chart_rasi, asc_house))

    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    # --- Condition 1 (Rasi Logic) ---
    ll_house = p_to_h[lagna_lord]
    
    if planet_positions_rasi is not None:
        ll_house_owner = int(house.house_owner_from_planet_positions(planet_positions_rasi, ll_house))
    else:
        ll_house_owner = int(house.house_owner(chart_rasi, ll_house))
    
    # LL in dry sign OR LL house owned by dry planet 
    return (ll_house in const.dry_signs) or (ll_house_owner in const.dry_planets)

def _krisanga_yoga_113_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None, natural_malefics=None):
    """
    BVR-113 Krisanga Yoga  
    The Navamsa Lagna is owned by a dry planet AND malefics join the Rasi Lagna.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if asc_house is None: return False
    _natural_malefics= set(const.natural_malefics) if natural_malefics is None else set(natural_malefics)
    # --- Condition 2 (Navamsa + Rasi Conjunction Logic) ---
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
        p_to_h_9d = utils.get_planet_house_dictionary_from_planet_positions(planet_positions_navamsa)
        asc_house_9d = p_to_h_9d.get(const._ascendant_symbol)
        nav_lagna_owner = house.house_owner_from_planet_positions(planet_positions_navamsa, asc_house_9d)
    elif chart_navamsa is not None:
        p_to_h_9d = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
        asc_house_9d = p_to_h_9d.get(const._ascendant_symbol)
        nav_lagna_owner = int(house.house_owner(chart_navamsa, asc_house_9d))
    else: return False
    # Navamsa Lagna owned by dry planet AND Malefics in Rasi Lagna
    malefic_in_lagna = any(p_to_h[m] == asc_house for m in _natural_malefics if m in p_to_h)
    condition_2 = (nav_lagna_owner in const.dry_planets) and malefic_in_lagna
    return condition_2

def _krisanga_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-112/113 Krisanga Yoga  
    Condition 1: Lagna lord in a dry sign or in a sign owned by a dry planet.
    Condition 2: The Navamsa Lagna is owned by a dry planet AND malefics join the Rasi Lagna.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    # Explicitly calculate D9 (Navamsa) for condition 2 
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _krisanga_yoga_calculation(planet_positions_rasi=pp,planet_positions_navamsa=pp_nav, natural_malefics=nm)
def dehasthoulya_yoga_114_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR 114
    Dehasthoulya Yoga (Stout Body)
    Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dehasthoulya_yoga_114_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav,
                                              natural_benefics=nb)
def _dehasthoulya_yoga_114_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, 
                                       planet_positions_navamsa=None, natural_benefics=None):
    """
    BVR 114
    Dehasthoulya Yoga (Stout Body)
    Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_rasi is None: return False
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # 1. House Lord and Benefic Templates
    if planet_positions_rasi is not None:
        ll = int(house.house_owner_from_planet_positions(planet_positions_rasi, asc_house))
    else:
        ll = int(house.house_owner(chart_rasi, asc_house))
    _natural_benefics = _get_natural_benefics(chart_rasi, natural_benefics)

    # --- Condition 1 (Yoga #114) ---
    p_to_h_9d = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    ll_nav_house = p_to_h_9d.get(ll)
    # Finding the owner of the Navamsa sign where the Lagna Lord sits
    ll_nav_lord = ( house.house_owner_from_planet_positions(planet_positions_navamsa, ll_nav_house) if planet_positions_navamsa
        else int(house.house_owner(chart_navamsa, ll_nav_house)) )
    
    # Both LL and LL's Navamsa Lord must be in watery signs in Rasi
    ll_in_watery = p_to_h[ll] in const.water_signs
    ll_nav_lord_in_watery = p_to_h.get(ll_nav_lord) in const.water_signs
    return  ll_in_watery and ll_nav_lord_in_watery
def dehasthoulya_yoga_115_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR 115
    Dehasthoulya Yoga (Stout Body)
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dehasthoulya_yoga_115_calculation(planet_positions_rasi=pp, natural_benefics=nb)
def _dehasthoulya_yoga_115_calculation(chart_rasi=None, planet_positions_rasi=None, natural_benefics=None):
    """
    BVR 115
    Dehasthoulya Yoga (Stout Body)
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if asc_house is None: return False

    _natural_benefics = _get_natural_benefics(chart_rasi, natural_benefics)
    # --- Condition 2 (Yoga #115) ---
    j_h = p_to_h.get(const.JUPITER_ID)
    condition_2 = False
    if j_h is not None:
        # Part A: Jupiter in Lagna
        if j_h == asc_house:
            condition_2 = True
        # Part B: Jupiter aspects Lagna from a watery sign
        elif j_h in const.water_signs:
            # Jupiter aspects 5, 7, 9 houses away
            jupiter_aspects = [(j_h + 4) % 12, (j_h + 6) % 12, (j_h + 8) % 12]
            if asc_house in jupiter_aspects:
                condition_2 = True
    return condition_2
def dehasthoulya_yoga_116_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR 116
    Dehasthoulya Yoga (Stout Body)
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dehasthoulya_yoga_116_calculation(planet_positions_rasi=pp, natural_benefics=nb)
def _dehasthoulya_yoga_116_calculation(chart_rasi=None, planet_positions_rasi=None, natural_benefics=None):
    """
    BVR 116
    Dehasthoulya Yoga (Stout Body)
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if asc_house is None: return False

    # 1. House Lord and Benefic Templates
    if planet_positions_rasi is not None:
        ll = int(house.house_owner_from_planet_positions(planet_positions_rasi, asc_house))
    else:
        ll = int(house.house_owner(chart_rasi, asc_house))

    _natural_benefics = _get_natural_benefics(chart_rasi, natural_benefics)
    # --- Condition 3 (Yoga #116) ---
    # Part A: Lagna in watery sign with benefics
    ben_in_lagna = any(p_to_h.get(b) == asc_house for b in _natural_benefics)
    cond_3_a = (asc_house in const.water_signs) and ben_in_lagna
    # Part B: Lagna Lord is a watery planet
    cond_3_b = ll in const.watery_planets
    condition_3 = cond_3_a or cond_3_b
    return condition_3
def dehasthoulya_yoga(chart_rasi, chart_navamsa=None):
    """
    BVR 114 to 116
    Dehasthoulya Yoga (Stout Body)
    Condition 1: Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    return _dehasthoulya_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa)
def _dehasthoulya_yoga_calculation(chart_rasi=None, chart_navamsa=None,planet_positions_rasi=None,
                                   planet_positions_navamsa=None,natural_benefics=None):
    """
    BVR 114 to 116
    Dehasthoulya Yoga (Stout Body)
    Condition 1: Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    if _dehasthoulya_yoga_114_calculation(chart_rasi, chart_navamsa, planet_positions_rasi, planet_positions_navamsa, natural_benefics): return True
    if _dehasthoulya_yoga_115_calculation(chart_rasi=chart_rasi, planet_positions_rasi=planet_positions_rasi,
                                              natural_benefics=natural_benefics): return True
    return _dehasthoulya_yoga_116_calculation(chart_rasi=chart_rasi, planet_positions_rasi=planet_positions_rasi,
                                              natural_benefics=natural_benefics)
def dehasthoulya_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa=None):
    """
    BVR 114 to 116
    Dehasthoulya Yoga (Stout Body)
    Condition 1: Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _dehasthoulya_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                          planet_positions_navamsa=planet_positions_navamsa)

def dehasthoulya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR 114 to 116
    Dehasthoulya Yoga (Stout Body)
    Condition 1: Lagna Lord and its Navamsa Lord both occupy watery signs (in Rasi).
    Condition 2: Jupiter in Lagna OR Jupiter aspects Lagna from a watery sign.
    Condition 3: Lagna in a watery sign joined by benefics OR Lagna Lord is a watery planet.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _dehasthoulya_yoga_calculation(planet_positions_rasi=pp, 
                                          planet_positions_navamsa=pp_nav, 
                                          natural_benefics=nb)
def _sada_sanchara_yoga_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    BVR-117 Sada Sanchara Yoga
    Definition: The lord of either Lagna or the sign occupied by Lagna lord 
    must be in a movable sign (Aries, Cancer, Libra, Capricorn).
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    if planet_positions_rasi is not None:
        lagna_lord = int(house.house_owner_from_planet_positions(planet_positions_rasi, asc_house))
    else:
        lagna_lord = int(house.house_owner(chart_rasi, asc_house))
    # Condition 1: Lord of Lagna in a movable sign
    ll_house = p_to_h.get(lagna_lord)
    condition_1 = ll_house in const.movable_signs
    # Condition 2: Lord of the sign occupied by Lagna Lord is in a movable sign
    # (Dispositor of the Lagna Lord)
    if planet_positions_rasi is not None:
        ll_dispositor = int(house.house_owner_from_planet_positions(planet_positions_rasi, ll_house))
    else:
        ll_dispositor = int(house.house_owner(chart_rasi, ll_house))
    ll_dispositor_house = p_to_h.get(ll_dispositor)
    condition_2 = ll_dispositor_house in const.movable_signs
    return condition_1 or condition_2

def sada_sanchara_yoga(chart_rasi):
    """
    BVR-117 Sada Sanchara Yoga
    Definition: The lord of either Lagna or the sign occupied by Lagna lord 
    must be in a movable sign (Aries, Cancer, Libra, Capricorn).
    """
    return _sada_sanchara_yoga_calculation(chart_rasi=chart_rasi)

def sada_sanchara_yoga_from_planet_positions(planet_positions_rasi):
    """
    BVR-117 Sada Sanchara Yoga
    Definition: The lord of either Lagna or the sign occupied by Lagna lord 
    must be in a movable sign (Aries, Cancer, Libra, Capricorn).
    """
    return _sada_sanchara_yoga_calculation(planet_positions_rasi=planet_positions_rasi)

def sada_sanchara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-117 Sada Sanchara Yoga
    Definition: The lord of either Lagna or the sign occupied by Lagna lord 
    must be in a movable sign (Aries, Cancer, Libra, Capricorn).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sada_sanchara_yoga_calculation(planet_positions_rasi=pp)
def _dhana_yoga_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #118-122)
    Covers five specific planetary combinations involving the 5th and 11th houses.
    """
    if _dhana_yoga_118_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_119_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_120_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_121_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_122_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_123_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_124_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_125_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_126_calculation(chart_rasi, planet_positions_rasi): return True
    if _dhana_yoga_127_calculation(chart_rasi, planet_positions_rasi): return True
    return _dhana_yoga_128_calculation(chart_rasi, planet_positions_rasi)
def dhana_yoga_128_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #128)
    Venus should be in Lagna identicalwith his own sign and joined or aspectedby Saturn and Mercury
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_128_calculation(planet_positions_rasi=pp)
def _dhana_yoga_128_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #128)
    Venus should be in Lagna identicalwith his own sign and joined or aspectedby Saturn and Mercury
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 128: Venus in Taurus/Libra Lagna + Saturn and Mercury
    return ( (asc_house in [const.TAURUS, const.LIBRA] and p_to_h.get(const.VENUS_ID) == asc_house) and
             (is_planet_influenced_by(const.VENUS_ID, [const.SATURN_ID, const.MERCURY_ID]))
        )
def dhana_yoga_127_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #127)
    Jupiter should be in Lagna identical with his own sign and joined or aspected by Mercury and Mars.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_127_calculation(planet_positions_rasi=pp)
def _dhana_yoga_127_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #127)
    Jupiter should be in Lagna identical with his own sign and joined or aspected by Mercury and Mars.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 127: Jupiter in Sagit/Pisces Lagna + Mercury and Mars
    return ( (asc_house in [const.SAGITTARIUS, const.PISCES] and p_to_h.get(const.JUPITER_ID) == asc_house) and 
        ( is_planet_influenced_by(const.JUPITER_ID, [const.MERCURY_ID, const.MARS_ID]))
        )
def dhana_yoga_126_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #126)
    Mercury should be in Lagna identical with his own sign and joined or aspectedby Saturn and Venus.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_126_calculation(planet_positions_rasi=pp)
def _dhana_yoga_126_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #126)
    Mercury should be in Lagna identical with his own sign and joined or aspectedby Saturn and Venus.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 126: Mercury in Gemini/Virgo Lagna + Saturn and Venus
    return ( (asc_house in [const.GEMINI, const.VIRGO] and p_to_h.get(const.MERCURY_ID) == asc_house) and
        (is_planet_influenced_by(const.MERCURY_ID, [const.SATURN_ID, const.VENUS_ID]))
        )
def dhana_yoga_125_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #125)
    Mars should be in Lagna identical with Aries or Scorpio and joined or aspectedby the Moon, Venus and Saturn.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_125_calculation(planet_positions_rasi=pp)
def _dhana_yoga_125_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #125)
    Mars should be in Lagna identical with Aries or Scorpio and joined or aspectedby the Moon, Venus and Saturn.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True

    # 125: Mars in Aries/Scorpio Lagna + Moon, Venus, Saturn
    return ( (asc_house in [const.ARIES, const.SCORPIO] and p_to_h.get(const.MARS_ID) == asc_house) and 
              (is_planet_influenced_by(const.MARS_ID, [const.MOON_ID, const.VENUS_ID, const.SATURN_ID]))
        )
def dhana_yoga_124_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #124)
    If the Moon is in Lagna identical with Cancer and aspectedby Jupiter and Mars, this yoga is caused.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_124_calculation(planet_positions_rasi=pp)
def _dhana_yoga_124_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #124)
    If the Moon is in Lagna identical with Cancer and aspectedby Jupiter and Mars, this yoga is caused.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 124: Moon in Cancer Lagna + Jupiter and Mars
    return ( (asc_house == const.CANCER and p_to_h.get(const.MOON_ID) == asc_house) and 
             (is_planet_influenced_by(const.MOON_ID, [const.JUPITER_ID, const.MARS_ID]))
            )
def dhana_yoga_123_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #123)
    "If the Sun is in Lagna identical with Leo, and aspected or joined by Mars and Jupiter, this yoga is formed.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_123_calculation(planet_positions_rasi=pp)
def _dhana_yoga_123_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #123)
    "If the Sun is in Lagna identical with Leo, and aspected or joined by Mars and Jupiter, this yoga is formed.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 123: Sun in Leo Lagna + Mars and Jupiter
    return ( (asc_house == const.LEO and p_to_h.get(const.SUN_ID) == asc_house) and 
             (is_planet_influenced_by(const.SUN_ID, [const.MARS_ID, const.JUPITER_ID]))
           )
def dhana_yoga_122_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #122)
    If the 5th from Lagna happens to be a house of Jupiter with Jupiter there and Mars and the Moon 
    in the 11th, Dhana Yoga arises.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_122_calculation(planet_positions_rasi=pp)
def _dhana_yoga_122_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #122)
    If the 5th from Lagna happens to be a house of Jupiter with Jupiter there and Mars and the Moon 
    in the 11th, Dhana Yoga arises.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # h5 is 4 houses away from Lagna; h11 is 10 houses away from Lagna
    h5 = (asc_house + const.HOUSE_5) % 12
    h11 = (asc_house + const.HOUSE_11) % 12
    pos = {p: p_to_h.get(p) for p in range(9)}
    # 122: 5th is Jupiter sign (Sagittarius/Pisces), Jupiter in 5th, Mars & Moon in 11th
    return h5 in [const.SAGITTARIUS, const.PISCES] and pos[const.JUPITER_ID] == h5 and \
       pos[const.MARS_ID] == h11 and pos[const.MOON_ID] == h11
def dhana_yoga_121_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #121)
    The Sun must occupy the 5th identical with his own sign and Jupiter and the Moon should be in the 11th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_121_calculation(planet_positions_rasi=pp)
def _dhana_yoga_121_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #121)
    The Sun must occupy the 5th identical with his own sign and Jupiter and the Moon should be in the 11th.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # h5 is 4 houses away from Lagna; h11 is 10 houses away from Lagna
    h5 = (asc_house + const.HOUSE_5) % 12
    h11 = (asc_house + const.HOUSE_11) % 12
    pos = {p: p_to_h.get(p) for p in range(9)}
    # 121: 5th is Sun sign (Leo), Sun in 5th, Jupiter & Moon in 11th
    return h5 == const.LEO and pos[const.SUN_ID] == h5 and \
       pos[const.JUPITER_ID] == h11 and pos[const.MOON_ID] == h11
def dhana_yoga_120_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #120)
    Saturn should occupy his own sign which shouldbe the 5th from Lagna, and Mercury and Mars 
    should be posited in the 11th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_120_calculation(planet_positions_rasi=pp)
def _dhana_yoga_120_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #120)
    Saturn should occupy his own sign which shouldbe the 5th from Lagna, and Mercury and Mars 
    should be posited in the 11th.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # h5 is 4 houses away from Lagna; h11 is 10 houses away from Lagna
    h5 = (asc_house + const.HOUSE_5) % 12
    h11 = (asc_house + const.HOUSE_11) % 12
    pos = {p: p_to_h.get(p) for p in range(9)}
    # 120: 5th is Saturn sign (Capricorn/Aquarius), Saturn in 5th, Mercury & Mars in 11th
    return h5 in [const.CAPRICORN, const.AQUARIUS] and pos[const.SATURN_ID] == h5 and \
       pos[const.MERCURY_ID] == h11 and pos[const.MARS_ID] == h11
    #return False
def dhana_yoga_119_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #119)
    Mercury should occupy his own sign which should be the 5th from Lagna and the Moon and Mars should be in the 11th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_119_calculation(planet_positions_rasi=pp)
def _dhana_yoga_119_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #119)
    Mercury should occupy his own sign which should be the 5th from Lagna and the Moon and Mars should be in the 11th.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # h5 is 4 houses away from Lagna; h11 is 10 houses away from Lagna
    h5 = (asc_house + const.HOUSE_5) % 12
    h11 = (asc_house + const.HOUSE_11) % 12
    pos = {p: p_to_h.get(p) for p in range(9)}
    # 119: 5th is Mercury sign (Gemini/Virgo), Mercury in 5th, Moon & Mars in 11th
    return h5 in [const.GEMINI, const.VIRGO] and pos[const.MERCURY_ID] == h5 and \
       pos[const.MOON_ID] == h11 and pos[const.MARS_ID] == h11
def dhana_yoga_118_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #118)
    If the 5th from the Ascendant happens to be a sign of Venus, and if Venus and Saturn are situated 
    in the 5th and 11th respectively, Dhana Yoga is caused.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_118_calculation(planet_positions_rasi=pp)
def _dhana_yoga_118_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #118)
    If the 5th from the Ascendant happens to be a sign of Venus, and if Venus and Saturn are situated 
    in the 5th and 11th respectively, Dhana Yoga is caused.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # h5 is 4 houses away from Lagna; h11 is 10 houses away from Lagna
    h5 = (asc_house + const.HOUSE_5) % 12
    h11 = (asc_house + const.HOUSE_11) % 12
    pos = {p: p_to_h.get(p) for p in range(9)}
    # 118: 5th is Venus sign (Taurus/Libra), Venus in 5th, Saturn in 11th
    return h5 in [const.TAURUS, const.LIBRA] and pos[const.VENUS_ID] == h5 and pos[const.SATURN_ID] == h11
def dhana_yoga(chart_rasi):
    """
    Dhana Yogas (B.V. Raman #118-122)
    Covers five specific planetary combinations involving the 5th and 11th houses.
    """
    return _dhana_yoga_calculation(chart_rasi=chart_rasi)

def dhana_yoga_from_planet_positions(planet_positions_rasi):
    """
    Dhana Yogas (B.V. Raman #118-122)
    Covers five specific planetary combinations involving the 5th and 11th houses.
    """
    return _dhana_yoga_calculation(planet_positions_rasi=planet_positions_rasi)

def dhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dhana Yogas (B.V. Raman #118-122)
    Covers five specific planetary combinations involving the 5th and 11th houses.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dhana_yoga_calculation(planet_positions_rasi=pp)
def _dhana_yogas_123_128_calculation(chart_rasi=None, planet_positions_rasi=None):
    """
    Dhana Yogas (B.V. Raman #123-128)
    Definition: Planet in Lagna (own sign) joined or aspected by specific planets.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    asc_house = p_to_h.get(const._ascendant_symbol)
    # Helper: Check if a planet is influenced (conjoined or aspected) by targets
    def is_planet_influenced_by(target_p_id, influencers):
        # 1. Get planets aspecting the target planet
        aspecting = house.planets_aspecting_the_planet(chart_rasi, target_p_id)
        # 2. Check each influencer
        for inf_id in influencers:
            # Check for Conjunction (In the same house)
            conjoined = (p_to_h.get(target_p_id) == p_to_h.get(inf_id))
            # Check for Aspect
            aspected = inf_id in aspecting
            if not (conjoined or aspected):
                return False
        return True
    # 123: Sun in Leo Lagna + Mars and Jupiter
    if asc_house == const.LEO and p_to_h.get(const.SUN_ID) == asc_house:
        if is_planet_influenced_by(const.SUN_ID, [const.MARS_ID, const.JUPITER_ID]):
            return True

    # 124: Moon in Cancer Lagna + Jupiter and Mars
    if asc_house == const.CANCER and p_to_h.get(const.MOON_ID) == asc_house:
        if is_planet_influenced_by(const.MOON_ID, [const.JUPITER_ID, const.MARS_ID]):
            return True

    # 125: Mars in Aries/Scorpio Lagna + Moon, Venus, Saturn
    if asc_house in [const.ARIES, const.SCORPIO] and p_to_h.get(const.MARS_ID) == asc_house:
        if is_planet_influenced_by(const.MARS_ID, [const.MOON_ID, const.VENUS_ID, const.SATURN_ID]):
            return True

    # 126: Mercury in Gemini/Virgo Lagna + Saturn and Venus
    if asc_house in [const.GEMINI, const.VIRGO] and p_to_h.get(const.MERCURY_ID) == asc_house:
        if is_planet_influenced_by(const.MERCURY_ID, [const.SATURN_ID, const.VENUS_ID]):
            return True

    # 127: Jupiter in Sagit/Pisces Lagna + Mercury and Mars
    if asc_house in [const.SAGITTARIUS, const.PISCES] and p_to_h.get(const.JUPITER_ID) == asc_house:
        if is_planet_influenced_by(const.JUPITER_ID, [const.MERCURY_ID, const.MARS_ID]):
            return True
    # 128: Venus in Taurus/Libra Lagna + Saturn and Mercury
    if asc_house in [const.TAURUS, const.LIBRA] and p_to_h.get(const.VENUS_ID) == asc_house:
        if is_planet_influenced_by(const.VENUS_ID, [const.SATURN_ID, const.MERCURY_ID]):
            return True

    return False
def _bahudravyarjana_yoga_calculation(chart_1d=None,planet_positions=None):
    """
        BVR-129: Lord of the Lagna in the 2nd, lord of the 2nd in the 11th and the lord of the 11th in 
            Lagna will give rise to this Yoga.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h.get(const._ascendant_symbol)
    second_house = (asc_house+const.HOUSE_2)%12
    eleventh_house = (asc_house+const.HOUSE_11)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, asc_house)
        lord_of_second = house.house_owner_from_planet_positions(planet_positions, second_house)
        lord_of_eleventh = house.house_owner_from_planet_positions(planet_positions, eleventh_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d,asc_house)
        lord_of_second = house.house_owner(chart_1d, (asc_house+const.HOUSE_2)%12)
        lord_of_eleventh = house.house_owner(chart_1d, (asc_house+const.HOUSE_11)%12)
    lagna_lord_in_second = p_to_h[lord_of_lagna] == second_house
    lord_of_second_in_eleventh = p_to_h[lord_of_second] == eleventh_house 
    lord_of_eleventh_in_lagna = p_to_h[lord_of_eleventh] == asc_house
    return lagna_lord_in_second and lord_of_second_in_eleventh and lord_of_eleventh_in_lagna
def bahudravyarjana_yoga(chart_1d=None):
    """
        BVR-129: Lord of the Lagna in the 2nd, lord of the 2nd in the 11th and the lord of the 11th in 
            Lagna will give rise to this Yoga.
    """
    return _bahudravyarjana_yoga_calculation(chart_1d=chart_1d)
def bahudravyarjana_yoga_from_planet_positions(planet_positions=None):
    """
        BVR-129: Lord of the Lagna in the 2nd, lord of the 2nd in the 11th and the lord of the 11th in 
            Lagna will give rise to this Yoga.
    """
    return _bahudravyarjana_yoga_calculation(planet_positions=planet_positions)
def bahudravyarjana_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
        BVR-129: Lord of the Lagna in the 2nd, lord of the 2nd in the 11th and the lord of the 11th in 
            Lagna will give rise to this Yoga.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bahudravyarjana_yoga_calculation(planet_positions=pp)

def _swaveeryaddhana_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, 
                                      planet_positions_navamsa=None, natural_benefics=None,vaiseshikamsa_scores=None):
    """
        BVR-130-132 Swaveeryaddhana Yoga (Wealth by own effort) 
        130 - The Lord of Lagna, being the strongest planet, should occupy a kendra in conjunotion with Jupiter 
            and the 2nd lord should join Vaiseshikamsa.
        131 - The lord of the sign in which the lord of the Navamsa occupied by the Ascendant lord is, should be strong,
            and join a quadrant or a trine from the 2nd lord or should occupy his own or exaltation sign
        132 - The 2nd lord should occupy a quadrant or trine from the lst lord or the 2nd lord being a benefic should be 
            either in deep exaltation or in conjunction with an exalted planet-132.
    """
    # --- Setup Benefics --- 
    _natural_benefics = _get_natural_benefics(chart_rasi, natural_benefics)
    # --- Setup Lords and Positions for Rasi ---
    if planet_positions_rasi is not None:
        p_to_h_rasi = utils.get_planet_house_dictionary_from_planet_positions(planet_positions_rasi)
        lagna = p_to_h_rasi[const._ascendant_symbol]; house_2 = (lagna+const.HOUSE_2)%12
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
        lord_of_lagna = int(house.house_owner_from_planet_positions(planet_positions_rasi, lagna))
        lord_of_2nd = int(house.house_owner_from_planet_positions(planet_positions_rasi, house_2))
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    elif chart_rasi is not None:
        p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
        lagna = p_to_h_rasi[const._ascendant_symbol]; house_2 = (lagna+const.HOUSE_2)%12
        lord_of_lagna = int(house.house_owner(chart_rasi, lagna))
        lord_of_2nd = int(house.house_owner(chart_rasi, house_2))
    if chart_rasi is None: return False
    
    lagna_lord_house_rasi = p_to_h_rasi[lord_of_lagna]
    second_lord_house_rasi = p_to_h_rasi[lord_of_2nd]

    # --- (a) Raman 130: LL strong in Kendra + Jupiter + 2nd Lord Vaiseshikamsa ---
    lagna_lord_strength = const.house_strengths_of_planets[lord_of_lagna][lagna_lord_house_rasi]
    is_lagna_lord_strong = lagna_lord_strength >= const._EXALTED_UCCHAM # Exalted/Own
    lagna_quadrant = quadrants_of_the_house(lagna)
    is_ll_in_kendra = lagna_lord_house_rasi in lagna_quadrant
    is_ll_with_jupiter = p_to_h_rasi[const.JUPITER_ID] == p_to_h_rasi[lord_of_lagna]
    
    has_13_vargas = False
    if vaiseshikamsa_scores and lord_of_2nd in vaiseshikamsa_scores:
        if vaiseshikamsa_scores[lord_of_2nd] >= 13: # Kanduka Vaiseshikamsa
            has_13_vargas = True

    if is_lagna_lord_strong and is_ll_in_kendra and is_ll_with_jupiter and has_13_vargas:
        return True

    # --- (c, d, e) Raman 132: 2nd Lord Relations ---
    # (c) 2nd Lord in Kendra/Trine from 1st Lord
    #rel_pos_2_from_1 = (second_lord_house_rasi - lagna_lord_house_rasi) % 12
    kendra_1st_lord = house.quadrants_of_the_raasi(lagna_lord_house_rasi)
    trine_1st_lord = house.trines_of_the_raasi(lagna_lord_house_rasi)
    #is_2nd_rel_kendra_trine = rel_pos_2_from_1 in [0, 3, 6, 9, 4, 8]
    is_2nd_rel_kendra_trine= second_lord_house_rasi in kendra_1st_lord+trine_1st_lord
    # (d & e) 2nd Lord is a benefic AND (Exalted OR with Exalted planet)
    is_2nd_benefic = lord_of_2nd in _natural_benefics
    second_lord_strength = const.house_strengths_of_planets[lord_of_2nd][second_lord_house_rasi]
    #planets_in_2nd_lord_house = [p for p,h in p_to_h_rasi.items() if h==second_lord_house_rasi and p!=const._ascendant_symbol]
    planets_in_2nd_lord_house = planets_in_raasi(second_lord_house_rasi, p_to_h_rasi,exclude_lagna=True)
    is_with_exalted = any(const.house_strengths_of_planets[int(p)][second_lord_house_rasi] == const._EXALTED_UCCHAM
                          for p in planets_in_2nd_lord_house if p and p != 'L' and int(p) != lord_of_2nd)

    if is_2nd_rel_kendra_trine:
        return True
    if is_2nd_benefic and (second_lord_strength == 4 or is_with_exalted):
        return True

    if chart_navamsa is None: return False
    # --- (b) Raman 131: Navamsa-Sign-Dispositor Chain ---
    # Logic: LL -> Navamsa Sign -> Lord of that sign (NavLord) -> Sign NavLord is in Rasi -> Lord of THAT sign (Dispositor)
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    # 1. Sign occupied by LL in Navamsa
    nav_sign_of_ll = p_to_h_nav[lord_of_lagna]
    # 2. Lord of that sign (the Navamsa Lord)
    nav_lord = ( house.house_owner_from_planet_positions(planet_positions_navamsa, nav_sign_of_ll) if planet_positions_navamsa
                    else int(house.house_owner(chart_rasi, nav_sign_of_ll)) )
    # 3. Sign occupied by NavLord in Rasi
    rasi_sign_of_nav_lord = p_to_h_rasi[nav_lord]
    # 4. Ruler of that sign (the Final Dispositor)
    dispositor_of_nav_lord = ( 
        house.house_owner_from_planet_positions(planet_positions_rasi, rasi_sign_of_nav_lord) if planet_positions_rasi
            else int(house.house_owner(chart_rasi, rasi_sign_of_nav_lord)) 
            )
    
    dispositor_house = p_to_h_rasi[dispositor_of_nav_lord]
    dispositor_strength = const.house_strengths_of_planets[dispositor_of_nav_lord][dispositor_house]
    
    # Check relative position to 2nd lord
    kendra_2nd_lord = house.quadrants_of_the_raasi(second_lord_house_rasi)
    trine_2nd_lord = house.trines_of_the_raasi(second_lord_house_rasi)
    #rel_pos = (dispositor_house - second_lord_house_rasi) % 12
    #is_rel_kendra_trine = rel_pos in [0, 3, 6, 9, 4, 8]
    is_rel_kendra_trine = dispositor_house in kendra_2nd_lord+trine_2nd_lord
    is_own_or_exalted = dispositor_strength >= const._EXALTED_UCCHAM
    
    if dispositor_strength >= const._FRIEND and (is_rel_kendra_trine or is_own_or_exalted):
        return True
    return False

def swaveeryaddhana_yoga(chart_rasi, chart_navamsa=None,natural_benefics=None):
    """
    BVR-130-132 Swaveeryaddhana Yoga (Wealth by own effort) 
    and detailed varga/dispositor conditions.
    """
    return _swaveeryaddhana_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,natural_benefics=natural_benefics)

def swaveeryaddhana_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa=None,natural_benefics=None):
    """
    BVR-130-132 Swaveeryaddhana Yoga (Wealth by own effort) 
    and detailed varga/dispositor conditions.
    """
    if planet_positions_rasi is not None:
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _swaveeryaddhana_yoga_calculation(planet_positions_rasi=planet_positions_rasi,
                                             planet_positions_navamsa=planet_positions_navamsa,
                                             natural_benefics=natural_benefics)

def swaveeryaddhana_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """
    BVR-130-132 Swaveeryaddhana Yoga (Wealth by own effort) 
    and detailed varga/dispositor conditions.
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu][:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    # Using Shodhasavarga for the 13 vargas check
    v_scores = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    v_scores = [v[0] for _,v in v_scores.items()]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _swaveeryaddhana_yoga_calculation(planet_positions_rasi=pp_rasi, 
                                           chart_navamsa=utils.get_house_planet_list_from_planet_positions(pp_nav),
                                           natural_benefics=nb, vaiseshikamsa_scores=v_scores)
def _madhya_vayasi_dhana_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    BVR-133 Madhya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _ascendant = const._ascendant_symbol
    asc_house = p_to_h[_ascendant]
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, asc_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, asc_house)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    ll_house = p_to_h[lord_of_lagna]
    
    h2_from_ll = (ll_house + const.HOUSE_2) % 12
    h3_from_ll = (ll_house + const.HOUSE_3) % 12
    
    planets_in_2 = planets_in_raasi(h2_from_ll,p_to_h)
    planets_in_3 = planets_in_raasi(h3_from_ll,p_to_h)
    
    
    return any(p in _natural_benefics for p in planets_in_2) and any(p in _natural_benefics for p in planets_in_3)
def madhya_vayasi_dhana_yoga(chart_rasi):
    """
    BVR-133 Madhya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    return _madhya_vayasi_dhana_yoga_calculation(chart_rasi=chart_rasi)
def madhya_vayasi_dhana_yoga_from_planet_positions(planet_positions):
    """
    BVR-133 Madhya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    return _madhya_vayasi_dhana_yoga_calculation(planet_positions=planet_positions)
def madhya_vayasi_dhana_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    BVR-133 Madhya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb = charts.benefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _madhya_vayasi_dhana_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _anthya_vayasi_dhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    BVR-134 Anthya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _ascendant = const._ascendant_symbol
    asc_house = p_to_h[_ascendant]
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, asc_house)
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, (asc_house + 1) % 12)
    else:
        lord_of_lagna = house.house_owner(chart_1d, asc_house)
        lord_of_2nd = house.house_owner(chart_1d, (asc_house + 1) % 12)
    
    ll_house = p_to_h[lord_of_lagna]
    l2_house = p_to_h[lord_of_2nd]
    
    # Using saved lambda functions for quadrants/trines from context
    valid_houses = quadrants_of_the_house(ll_house) + trines_of_the_house(ll_house)
    return l2_house in valid_houses

def anthya_vayasi_dhana_yoga(chart_1d):
    """
    BVR-134 Anthya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    return _anthya_vayasi_dhana_yoga_calculation(chart_1d=chart_1d)

def anthya_vayasi_dhana_yoga_from_planet_positions(planet_positions):
    """
    BVR-134 Anthya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    return _anthya_vayasi_dhana_yoga_calculation(planet_positions=planet_positions)

def anthya_vayasi_dhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-134 Anthya Vayasi Dhana Yoga
    Covers wealth acquired or peaking in middle age.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _anthya_vayasi_dhana_yoga_calculation(planet_positions=pp)
def balya_dhana_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa,
                                            natural_benefics=None):
    """
    BVR-135 Balya Dhana Yoga
    Three conditions have to be fulfilled for its presence, viz., 
    (a) the 2nd and 10th lords should be in conjunction; 
    (b) they must occupy a kendra from Lagna, and 
    (c) they must be aspected by the planet who owns the Navamsa in which the lord of Lagna is located.
    """
    return _balya_dhana_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                         planet_positions_navamsa=planet_positions_navamsa, 
                                         natural_benefics=natural_benefics)
def balya_dhana_yoga(chart_rasi,chart_navamsa,natural_benefics=None):
    """
    BVR-135 Balya Dhana Yoga
    Three conditions have to be fulfilled for its presence, viz., 
    (a) the 2nd and 10th lords should be in conjunction; 
    (b) they must occupy a kendra from Lagna, and 
    (c) they must be aspected by the planet who owns the Navamsa in which the lord of Lagna is located.
    """
    return _balya_dhana_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                         natural_benefics=natural_benefics)
def balya_dhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    BVR-135 Balya Dhana Yoga
    Three conditions have to be fulfilled for its presence, viz., 
    (a) the 2nd and 10th lords should be in conjunction; 
    (b) they must occupy a kendra from Lagna, and 
    (c) they must be aspected by the planet who owns the Navamsa in which the lord of Lagna is located.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _balya_dhana_yoga_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav)
def _balya_dhana_yoga_calculation(chart_rasi=None, planet_positions_rasi=None, chart_navamsa=None,
                                  planet_positions_navamsa=None):
    """
    BVR-135 Balya Dhana Yoga
    Three conditions have to be fulfilled for its presence, viz., 
    (a) the 2nd and 10th lords should be in conjunction; 
    (b) they must occupy a kendra from Lagna, and 
    (c) they must be aspected by the planet who owns the Navamsa in which the lord of Lagna is located.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.nava_navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None and planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    house_of_lagna_rasi = p_to_h_rasi[const._ascendant_symbol]
    house_of_2nd_rasi = (house_of_lagna_rasi+const.HOUSE_2)%12
    house_of_10th_rasi =(house_of_lagna_rasi+const.HOUSE_10)%12
    rasi_lagna_kendras = quadrants_of_the_house(house_of_lagna_rasi)
    
    if planet_positions_rasi is not None:
        lord_of_lagna_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_lagna_rasi)
        lord_of_2nd_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_2nd_rasi)
        lord_of_10th_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_10th_rasi)
    else:
        lord_of_lagna_rasi = house.house_owner(chart_rasi, house_of_lagna_rasi)
        lord_of_2nd_rasi = house.house_owner(chart_rasi, house_of_2nd_rasi)
        lord_of_10th_rasi = house.house_owner(chart_rasi, house_of_10th_rasi)
    house_of_lagna_lord_in_navamsa = p_to_h_navamsa[lord_of_lagna_rasi]
    if planet_positions_navamsa is not None:
        lord_of_house_of_lagna_lord_in_navamsa = house.house_owner_from_planet_positions(planet_positions_navamsa, house_of_lagna_lord_in_navamsa)
    else:
        lord_of_house_of_lagna_lord_in_navamsa = house.house_owner(chart_navamsa, house_of_lagna_lord_in_navamsa)
    # (a) the 2nd and 10th lords should be in conjunction; 
    lord_2nd_and_lord_10th_in_conjunction = (p_to_h_rasi[lord_of_2nd_rasi]==p_to_h_rasi[lord_of_10th_rasi])
    if not lord_2nd_and_lord_10th_in_conjunction: return False
    #(b) they must occupy a kendra from Lagna, and 
    lords_occupy_lagna_kendra = p_to_h_rasi[lord_of_2nd_rasi] in rasi_lagna_kendras
    if not lords_occupy_lagna_kendra: return False
    #(c) they must be aspected by the planet who owns the Navamsa in which the lord of Lagna is located.
    # Lords of 2nd and 10th should be aspected by lord_of_house_of_lagna_lord_in_navamsa
    aspects_of_lord_of_2nd = house.planets_aspecting_the_planet(chart_rasi, lord_of_2nd_rasi) 
    lord_of_house_of_lagna_lord_in_navamsa_aspects_2nd_lord = lord_of_house_of_lagna_lord_in_navamsa in aspects_of_lord_of_2nd
    if not lord_of_house_of_lagna_lord_in_navamsa_aspects_2nd_lord: return False
    aspects_of_lord_of_10th = house.planets_aspecting_the_planet(chart_rasi, lord_of_10th_rasi) 
    lord_of_house_of_lagna_lord_in_navamsa_aspects_10th_lord = lord_of_house_of_lagna_lord_in_navamsa in aspects_of_lord_of_10th
    return lord_of_house_of_lagna_lord_in_navamsa_aspects_10th_lord
def _bhratrumooladdhanaprapti_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, vaiseshikamsa_scores=None):
    """
    Bhratrumooladdhanaprapti Yoga (BV Raman 136, 137)
    Covers wealth from brothers through specific conjunctions and aspects.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l3 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_3) % 12))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l3 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_3) % 12))

    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # 136 Logic: L1 and L2 in 3rd House; 3rd House aspected by Benefics
    h3 = (asc_h + const.HOUSE_3) % 12
    l1_l2_in_3 = p_to_h[l1] == h3 and p_to_h[l2] == h3
    
    h3_aspected_by_benefic = False
    for b in _natural_benefics:
        if h3 in house.aspected_rasis_of_the_planet(chart_1d, b):
            h3_aspected_by_benefic = True
            break
    
    if l1_l2_in_3 and h3_aspected_by_benefic: 
        return True

    # 137 Logic: L3 in 2nd with Jupiter; aspected or conjoined by L1
    h2 = (asc_h + const.HOUSE_2) % 12
    l3_in_2 = p_to_h[l3] == h2
    with_jupiter = const.JUPITER_ID in planets_in_raasi(h2,p_to_h) # V4.8.0
    l1_aspects_l3 = l3 in house.aspected_planets_of_the_planet(chart_1d, l1)
    l1_conj_l3 = p_to_h[l1] == p_to_h[l3]
    l1_vaiseshikamsa = vaiseshikamsa_scores and vaiseshikamsa_scores.get(l1, 0) >= 13

    return l3_in_2 and with_jupiter and (l1_aspects_l3 or l1_conj_l3) and l1_vaiseshikamsa

def bhratrumooladdhanaprapti_yoga(chart_1d):
    """
    Bhratrumooladdhanaprapti Yoga (BV Raman 136, 137)
    Covers wealth from brothers through specific conjunctions and aspects.
    """
    return _bhratrumooladdhanaprapti_yoga_calculation(chart_1d)

def bhratrumooladdhanaprapti_yoga_from_planet_positions(planet_positions):
    """
    Bhratrumooladdhanaprapti Yoga (BV Raman 136, 137)
    Covers wealth from brothers through specific conjunctions and aspects.
    """
    return _bhratrumooladdhanaprapti_yoga_calculation(planet_positions=planet_positions)

def bhratrumooladdhanaprapti_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Bhratrumooladdhanaprapti Yoga (BV Raman 136, 137)
    Covers wealth from brothers through specific conjunctions and aspects.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    
    # Fetch Vaiseshikamsa scores (list) and convert to dict for the calculation function
    scores_list = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    scores_dict = {i: score[0] for i, score in scores_list.items()}
    return _bhratrumooladdhanaprapti_yoga_calculation(
        planet_positions=pp, 
        natural_benefics=nb, 
        vaiseshikamsa_scores=scores_dict
    )
    
def _matrumooladdhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Matrumooladdhana Yoga (BV Raman 138)
    Definition: If the lord of the 2nd joins the 4th lord or is aspected by him.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l4 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_4) % 12))
    else:
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l4 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_4) % 12))

    conjoined = p_to_h[l2] == p_to_h[l4]
    l4_aspects_l2 = l2 in house.aspected_planets_of_the_planet(chart_1d, l4)

    return conjoined or l4_aspects_l2

def matrumooladdhana_yoga(chart_1d):
    """
    Matrumooladdhana Yoga (BV Raman 138)
    Definition: If the lord of the 2nd joins the 4th lord or is aspected by him.
    """
    return _matrumooladdhana_yoga_calculation(chart_1d)

def matrumooladdhana_yoga_from_planet_positions(planet_positions):
    """
    Matrumooladdhana Yoga (BV Raman 138)
    Definition: If the lord of the 2nd joins the 4th lord or is aspected by him.
    """
    return _matrumooladdhana_yoga_calculation(planet_positions=planet_positions)

def matrumooladdhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Matrumooladdhana Yoga (BV Raman 138)
    Definition: If the lord of the 2nd joins the 4th lord or is aspected by him.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _matrumooladdhana_yoga_calculation(planet_positions=pp)
def _putramooladdhana_yoga_calculation(chart_1d=None, planet_positions=None, vaiseshikamsa_scores=None):
    """
    Putramooladdhana Yoga (BV Raman 139)
    Definition: If the strong lord of the 2nd is in conjunction with the 5th lord 
    or Jupiter and if the lord of Lagna is in Vaiseshikamsa.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l5 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_5) % 12))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l5 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_5) % 12))

    l2_h = p_to_h[l2]
    l2_strong = const.house_strengths_of_planets[l2][l2_h] >= 4
    l1_vaiseshikamsa = vaiseshikamsa_scores and vaiseshikamsa_scores.get(l1, 0) >= 13
    
    planets_in_l2_h = planets_in_raasi(l2_h,p_to_h) # V4.8.0
    conj = (p_to_h[l2] == p_to_h[l5]) or (const.JUPITER_ID in planets_in_l2_h)
    
    return l2_strong and l1_vaiseshikamsa and conj

def putramooladdhana_yoga(chart_1d):
    """
    Putramooladdhana Yoga (BV Raman 139)
    Definition: If the strong lord of the 2nd is in conjunction with the 5th lord 
    or Jupiter and if the lord of Lagna is in Vaiseshikamsa.
    """
    return _putramooladdhana_yoga_calculation(chart_1d)

def putramooladdhana_yoga_from_planet_positions(planet_positions):
    """
    Putramooladdhana Yoga (BV Raman 139)
    Definition: If the strong lord of the 2nd is in conjunction with the 5th lord 
    or Jupiter and if the lord of Lagna is in Vaiseshikamsa.
    """
    return _putramooladdhana_yoga_calculation(planet_positions=planet_positions)

def putramooladdhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Putramooladdhana Yoga (BV Raman 139)
    Definition: If the strong lord of the 2nd is in conjunction with the 5th lord 
    or Jupiter and if the lord of Lagna is in Vaiseshikamsa.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    
    # Fetch Vaiseshikamsa scores (list) and convert to dict
    scores_list = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    scores_dict = {i: score[0] for i, score in scores_list.items()}
    
    return _putramooladdhana_yoga_calculation(
        planet_positions=pp, 
        vaiseshikamsa_scores=scores_dict
    )
    
def _shatrumooladdhana_yoga_calculation(chart_1d=None, planet_positions=None, vaiseshikamsa_scores=None):
    """
    Shatrumooladdhana Yoga (BV Raman 140)
    Definition: The strong lord of the 2nd should join the lord of the 6th or Mars 
    and the powerful lord of Lagna should be in Vaiseshikamsa.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l6 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_6) % 12))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l6 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_6) % 12))

    l2_h = p_to_h[l2]
    l2_strong = const.house_strengths_of_planets[l2][l2_h] >= 4
    l1_vaiseshikamsa = vaiseshikamsa_scores and vaiseshikamsa_scores.get(l1, 0) >= 13
    
    planets_in_l2_h = planets_in_raasi(l2_h,p_to_h)#V4.8.0
    conj = (p_to_h[l2] == p_to_h[l6]) or (const.MARS_ID in planets_in_l2_h)
    
    return l2_strong and l1_vaiseshikamsa and conj

def shatrumooladdhana_yoga(chart_1d):
    """
    Shatrumooladdhana Yoga (BV Raman 140)
    Definition: The strong lord of the 2nd should join the lord of the 6th or Mars 
    and the powerful lord of Lagna should be in Vaiseshikamsa.
    """
    return _shatrumooladdhana_yoga_calculation(chart_1d)

def shatrumooladdhana_yoga_from_planet_positions(planet_positions):
    """
    Shatrumooladdhana Yoga (BV Raman 140)
    Definition: The strong lord of the 2nd should join the lord of the 6th or Mars 
    and the powerful lord of Lagna should be in Vaiseshikamsa.
    """
    return _shatrumooladdhana_yoga_calculation(planet_positions=planet_positions)

def shatrumooladdhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Shatrumooladdhana Yoga (BV Raman 140)
    Definition: The strong lord of the 2nd should join the lord of the 6th or Mars 
    and the powerful lord of Lagna should be in Vaiseshikamsa.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    
    # Fetch Vaiseshikamsa scores (list) and convert to dict
    scores_list = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    scores_dict = {i: score[0] for i, score in scores_list.items()}
    
    return _shatrumooladdhana_yoga_calculation(
        planet_positions=pp, 
        vaiseshikamsa_scores=scores_dict
    )
    
def _kalatramooladdhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Kalatramooladdhana Yoga (BV Raman 141)
    Definition: The strong lord of the 2nd should join or be aspected by 
    the 7th lord and Venus and the lord of Lagna must be powerful.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l7 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_7) % 12))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l7 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_7) % 12))

    l1_strong = const.house_strengths_of_planets[l1][p_to_h[l1]] >= 4
    l2_strong = const.house_strengths_of_planets[l2][p_to_h[l2]] >= 4

    l2_h = p_to_h[l2]
    p_in_l2_h = planets_in_raasi(l2_h,p_to_h)#V4.8.0
    conjoined = (p_to_h[l2] == p_to_h[l7]) and (const.VENUS_ID in p_in_l2_h)
    
    l7_aspects_l2 = l2 in house.aspected_planets_of_the_planet(chart_1d, l7)
    venus_aspects_l2 = l2 in house.aspected_planets_of_the_planet(chart_1d, const.VENUS_ID)
    aspected = l7_aspects_l2 and venus_aspects_l2

    return l1_strong and l2_strong and (conjoined or aspected)

def kalatramooladdhana_yoga(chart_1d):
    """
    Kalatramooladdhana Yoga (BV Raman 141)
    Definition: The strong lord of the 2nd should join or be aspected by 
    the 7th lord and Venus and the lord of Lagna must be powerful.
    """
    return _kalatramooladdhana_yoga_calculation(chart_1d)

def kalatramooladdhana_yoga_from_planet_positions(planet_positions):
    """
    Kalatramooladdhana Yoga (BV Raman 141)
    Definition: The strong lord of the 2nd should join or be aspected by 
    the 7th lord and Venus and the lord of Lagna must be powerful.
    """
    return _kalatramooladdhana_yoga_calculation(planet_positions=planet_positions)

def kalatramooladdhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Kalatramooladdhana Yoga (BV Raman 141)
    Definition: The strong lord of the 2nd should join or be aspected by 
    the 7th lord and Venus and the lord of Lagna must be powerful.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kalatramooladdhana_yoga_calculation(planet_positions=pp)
def _amaranantha_dhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Amaranantha Dhana Yoga (BV Raman 142)
    Definition: If a number of planets occupy the 2nd house and the wealth-giving 
    ones are strong or occupy own or exaltation signs.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h2 = (asc_h + const.HOUSE_2) % 12

    planets_in_2 = planets_in_raasi(h2,p_to_h)
    if len(planets_in_2) < 3: 
        return False 

    if planet_positions is not None:
        l2 = int(house.house_owner_from_planet_positions(planet_positions, h2))
        l11 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_11) % 12))
    else:
        l2 = int(house.house_owner(chart_1d, h2))
        l11 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_11) % 12))
    
    wealth_planets = {l2, l11, const.JUPITER_ID}
    strong_wealth = any(p in planets_in_2 and const.house_strengths_of_planets[p][h2] >= 4 for p in wealth_planets)
    
    return strong_wealth

def amaranantha_dhana_yoga(chart_1d):
    """
    Amaranantha Dhana Yoga (BV Raman 142)
    Definition: If a number of planets occupy the 2nd house and the wealth-giving 
    ones are strong or occupy own or exaltation signs.
    """
    return _amaranantha_dhana_yoga_calculation(chart_1d)

def amaranantha_dhana_yoga_from_planet_positions(planet_positions):
    """
    Amaranantha Dhana Yoga (BV Raman 142)
    Definition: If a number of planets occupy the 2nd house and the wealth-giving 
    ones are strong or occupy own or exaltation signs.
    """
    return _amaranantha_dhana_yoga_calculation(planet_positions=planet_positions)

def amaranantha_dhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Amaranantha Dhana Yoga (BV Raman 142)
    Definition: If a number of planets occupy the 2nd house and the wealth-giving 
    ones are strong or occupy own or exaltation signs.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _amaranantha_dhana_yoga_calculation(planet_positions=pp)
def _ayatnadhanalabha_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Ayatnadhanalabha Yoga (BV Raman 143)
    Definition: The lord of the Lagna and the 2nd must exchange their places.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    lagna_house = p_to_h[_asc]
    second_house = (lagna_house + const.HOUSE_2) % 12

    if planet_positions is not None:
        lagna_lord = int(house.house_owner_from_planet_positions(planet_positions, lagna_house))
        second_lord = int(house.house_owner_from_planet_positions(planet_positions, second_house))
    else:
        lagna_lord = int(house.house_owner(chart_1d, lagna_house))
        second_lord = int(house.house_owner(chart_1d, second_house))
    return lagna_house == p_to_h[second_lord] and second_house==p_to_h[lagna_lord]

def ayatnadhanalabha_yoga(chart_1d):
    """
    Ayatnadhanalabha Yoga (BV Raman 143)
    Definition: The lord of the Lagna and the 2nd must exchange their places.
    """
    return _ayatnadhanalabha_yoga_calculation(chart_1d)

def ayatnadhanalabha_yoga_from_planet_positions(planet_positions):
    """
    Ayatnadhanalabha Yoga (BV Raman 143)
    Definition: The lord of the Lagna and the 2nd must exchange their places.
    """
    return _ayatnadhanalabha_yoga_calculation(planet_positions=planet_positions)

def ayatnadhanalabha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Ayatnadhanalabha Yoga (BV Raman 143)
    Definition: The lord of the Lagna and the 2nd must exchange their places.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _ayatnadhanalabha_yoga_calculation(planet_positions=pp)
def are_lords_exchanged(p_to_h,lord1,lord1_house,lord2,lord2_house):
    return lord1_house == p_to_h[lord2] and lord2_house==p_to_h[lord1_house]
def dharidhra_yoga_144_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 144)
    Definition: The lords of the 12th and Lagna exchange positions and 
    are conjoined with or aspected by the lord of the 7th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_144_calculation(planet_positions=pp)
def _dharidhra_yoga_144_calculation(chart_1d=None, planet_positions=None):
    """
    Daridra Yoga (BV Raman 144)
    Definition: The lords of the 12th and Lagna exchange positions and 
    are conjoined with or aspected by the lord of the 7th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    
    h12 = (asc_h + 11) % 12
    h7 = (asc_h + 6) % 12

    if planet_positions is not None:
        l1 = house.house_owner_from_planet_positions(planet_positions, asc_h)
        l12 = house.house_owner_from_planet_positions(planet_positions, h12)
        l7 = house.house_owner_from_planet_positions(planet_positions, h7)
    else:
        l1 = house.house_owner(chart_1d, asc_h)
        l12 = house.house_owner(chart_1d, h12)
        l7 = house.house_owner(chart_1d, h7)
    # Exchange logic: L1 in 12th house AND L12 in Lagna
    exchange = (p_to_h[l1] == h12) and (p_to_h[l12] == asc_h)
    if not exchange:
        return False
    
    l7_h = p_to_h[l7]
    conjoined = (l7_h == p_to_h[l1]) or (l7_h == p_to_h[l12])
    
    graha_aspects = house.aspected_planets_of_the_planet(chart_1d, l7)
    rasi_aspects = house.aspected_planets_of_the_raasi(chart_1d, l7_h)
    
    aspected = (l1 in graha_aspects or l12 in graha_aspects) or \
               (l1 in rasi_aspects or l12 in rasi_aspects)

    return exchange and (conjoined or aspected)
def dharidhra_yoga_145_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 145)
    Definition: The lords of the 6th and Lagna interchange positions and 
    the Moon is aspected by the 2nd or 7th lord.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_145_calculation(planet_positions=pp)
def _dharidhra_yoga_145_calculation(chart_1d=None, planet_positions=None):
    """
    Daridra Yoga (BV Raman 145)
    Definition: The lords of the 6th and Lagna interchange positions and 
    the Moon is aspected by the 2nd or 7th lord.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h6 = (asc_h + const.HOUSE_6) % 12
    h2 = (asc_h + const.HOUSE_2) % 12
    h7 = (asc_h + const.HOUSE_7) % 12

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l6 = int(house.house_owner_from_planet_positions(planet_positions, h6))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, h2))
        l7 = int(house.house_owner_from_planet_positions(planet_positions, h7))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l6 = int(house.house_owner(chart_1d, h6))
        l2 = int(house.house_owner(chart_1d, h2))
        l7 = int(house.house_owner(chart_1d, h7))

    exchange = (p_to_h[l1] == h6) and (p_to_h[l6] == asc_h)
    
    moon = const.MOON_ID
    # Aspect on Moon by L2 or L7
    asp_l2 = (moon in house.aspected_planets_of_the_planet(chart_1d, l2)) or \
             (moon in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[l2]))
    asp_l7 = (moon in house.aspected_planets_of_the_planet(chart_1d, l7)) or \
             (moon in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[l7]))

    return exchange and (asp_l2 or asp_l7)
def dharidhra_yoga_146_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 146)
    Definition: Ketu and the Moon should be in Lagna.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_146_calculation(planet_positions=pp)
def _dharidhra_yoga_146_calculation(chart_1d=None, planet_positions=None):
    """
    Daridra Yoga (BV Raman 146)
    Definition: Ketu and the Moon should be in Lagna.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    return (p_to_h[const.KETU_ID] == asc_h) and (p_to_h[const.MOON_ID] == asc_h)
def dharidhra_yoga_147_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 147)
    Definition: The lord of Lagna is in the 8th aspected by or in conjunction with the 2nd or 7th lord.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_147_calculation(planet_positions=pp)
def _dharidhra_yoga_147_calculation(chart_1d=None, planet_positions=None):
    """
    Daridra Yoga (BV Raman 147)
    Definition: The lord of Lagna is in the 8th aspected by or in 
    conjunction with the 2nd or 7th lord.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h8 = (asc_h + const.HOUSE_8) % 12
    h2 = (asc_h + const.HOUSE_2) % 12
    h7 = (asc_h + const.HOUSE_7) % 12

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, h2))
        l7 = int(house.house_owner_from_planet_positions(planet_positions, h7))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, h2))
        l7 = int(house.house_owner(chart_1d, h7))

    # Condition 1: L1 in 8th
    if p_to_h[l1] != h8:
        return False

    # Condition 2: Conjunction or Aspect with L2 or L7
    for maraka in [l2, l7]:
        if (p_to_h[maraka] == h8) or \
           (l1 in house.aspected_planets_of_the_planet(chart_1d, maraka)) or \
           (l1 in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[maraka])):
            return True
    return False
def dharidhra_yoga_148_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 148)
    Definition: Lord of Lagna in 6, 8, or 12 with a malefic, aspected by or 
    combined with the 2nd or 7th lord.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dharidhra_yoga_148_calculation(planet_positions=pp,natural_malefics=nm)
def _dharidhra_yoga_148_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
    Daridra Yoga (BV Raman 148)
    Definition: Lord of Lagna in 6, 8, or 12 with a malefic, aspected by or 
    combined with the 2nd or 7th lord.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    trik_houses = [(asc_h + h) % 12 for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]
    
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_2) % 12))
        l7 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_7) % 12))
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        l2 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_2) % 12))
        l7 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_7) % 12))

    l1_house = p_to_h[l1]
    if l1_house not in trik_houses:
        return False

    # Check if a malefic is in the same house as L1
    malefic_with_l1 = any(m for m in _natural_malefics if m != l1 and p_to_h[m] == l1_house)
    if not malefic_with_l1:
        return False

    # Check influence of L2 or L7 on L1
    for maraka in [l2, l7]:
        if (p_to_h[maraka] == l1_house) or \
           (l1 in house.aspected_planets_of_the_planet(chart_1d, maraka)) or \
           (l1 in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[maraka])):
            return True
    return False
def dharidhra_yoga_149_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 149)
    Definition: Lord of Lagna associated with 6th, 8th, or 12th lord and 
    subjected to malefic aspects.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dharidhra_yoga_149_calculation(planet_positions=pp,natural_malefics=nm)
def _dharidhra_yoga_149_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
    Daridra Yoga (BV Raman 149)
    Definition: Lord of Lagna associated with 6th, 8th, or 12th lord and 
    subjected to malefic aspects.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    if planet_positions is not None:
        l1 = int(house.house_owner_from_planet_positions(planet_positions, asc_h))
        trik_lords = [int(house.house_owner_from_planet_positions(planet_positions, (asc_h + h) % 12)) 
                      for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]
    else:
        l1 = int(house.house_owner(chart_1d, asc_h))
        trik_lords = [int(house.house_owner(chart_1d, (asc_h + h) % 12)) 
                      for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]

    # Association with Trik lord (Conjunction or Mutual Aspect)
    l1_h = p_to_h[l1]
    associated = False
    for tl in trik_lords:
        if (p_to_h[tl] == l1_h) or (l1 in house.aspected_planets_of_the_planet(chart_1d, tl)):
            associated = True
            break
    
    if not associated:
        return False

    # Subjected to malefic aspects
    malefic_aspect = False
    for m in _natural_malefics:
        if m != l1 and (l1 in house.aspected_planets_of_the_planet(chart_1d, m)):
            malefic_aspect = True
            break
            
    return malefic_aspect
def dharidhra_yoga_150_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 150)
    Definition: Lord of 5th joins lord of 6, 8, or 12 without beneficial aspects/conjunctions.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dharidhra_yoga_150_calculation(planet_positions=pp,natural_benefics=nb)
def _dharidhra_yoga_150_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Daridra Yoga (BV Raman 150)
    Definition: Lord of 5th joins lord of 6, 8, or 12 without beneficial aspects/conjunctions.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    if planet_positions is not None:
        l5 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_5) % 12))
        trik_lords = [int(house.house_owner_from_planet_positions(planet_positions, (asc_h + h) % 12)) 
                      for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]
    else:
        l5 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_5) % 12))
        trik_lords = [int(house.house_owner(chart_1d, (asc_h + h) % 12)) 
                      for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]

    # Joins (Conjunction) with Trik Lord
    l5_h = p_to_h[l5]
    joined = any(p_to_h[tl] == l5_h for tl in trik_lords)
    
    if not joined:
        return False

    # Check for beneficial aspects or conjunctions
    for b in _natural_benefics:
        if (p_to_h[b] == l5_h) or (l5 in house.aspected_planets_of_the_planet(chart_1d, b)):
            return False # Has beneficial influence
            
    return True
def dharidhra_yoga_151_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 151)
    Definition: Lord of 5th in 6th or 10th aspected by lords of 2, 6, 7, 8, or 12.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_151_calculation(planet_positions=pp)
def _dharidhra_yoga_151_calculation(chart_1d=None, planet_positions=None):
    """
    Daridra Yoga (BV Raman 151)
    Definition: Lord of 5th in 6th or 10th aspected by lords of 2, 6, 7, 8, or 12.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]

    if planet_positions is not None:
        l5 = int(house.house_owner_from_planet_positions(planet_positions, (asc_h + const.HOUSE_5) % 12))
        target_lords = [int(house.house_owner_from_planet_positions(planet_positions, (asc_h + h) % 12)) 
                        for h in [const.HOUSE_2, const.HOUSE_6, const.HOUSE_7, const.HOUSE_8, const.HOUSE_12]]
    else:
        l5 = int(house.house_owner(chart_1d, (asc_h + const.HOUSE_5) % 12))
        target_lords = [int(house.house_owner(chart_1d, (asc_h + h) % 12)) 
                        for h in [const.HOUSE_2, const.HOUSE_6, const.HOUSE_7, const.HOUSE_8, const.HOUSE_12]]

    l5_h = p_to_h[l5]
    if l5_h not in [(asc_h + const.HOUSE_6) % 12, (asc_h + const.HOUSE_10) % 12]:
        return False

    # Aspected by any of the target lords
    for tl in target_lords:
        if (l5 in house.aspected_planets_of_the_planet(chart_1d, tl)) or \
           (l5 in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[tl])):
            return True
            
    return False
def dharidhra_yoga_152_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Daridra Yoga (BV Raman 152)
    Definition: Natural malefics (not owning 9th or 10th) in Lagna associated 
    with or aspected by maraka lords (L2/L7).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dharidhra_yoga_152_calculation(planet_positions=pp,natural_malefics=nm)
def _dharidhra_yoga_152_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
    Daridra Yoga (BV Raman 152)
    Definition: Natural malefics (not owning 9th or 10th) in Lagna associated 
    with or aspected by maraka lords (L2/L7).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h9 = (asc_h + const.HOUSE_9) % 12
    h10 = (asc_h + const.HOUSE_10) % 12
    h2 = (asc_h + const.HOUSE_2) % 12
    h7 = (asc_h + const.HOUSE_7) % 12

    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    if planet_positions is not None:
        l9 = int(house.house_owner_from_planet_positions(planet_positions, h9))
        l10 = int(house.house_owner_from_planet_positions(planet_positions, h10))
        l2 = int(house.house_owner_from_planet_positions(planet_positions, h2))
        l7 = int(house.house_owner_from_planet_positions(planet_positions, h7))
    else:
        l9 = int(house.house_owner(chart_1d, h9))
        l10 = int(house.house_owner(chart_1d, h10))
        l2 = int(house.house_owner(chart_1d, h2))
        l7 = int(house.house_owner(chart_1d, h7))

    malefics_in_lagna = [m for m in _natural_malefics if p_to_h[m] == asc_h]
    valid_malefics = [m for m in malefics_in_lagna if m != l9 and m != l10]

    if not valid_malefics:
        return False

    for m in valid_malefics:
        # Check association or aspect with L2 or L7
        for maraka in [l2, l7]:
            if (p_to_h[m] == p_to_h[maraka]) or \
               (m in house.aspected_planets_of_the_planet(chart_1d, maraka)) or \
               (m in house.aspected_planets_of_the_raasi(chart_1d, p_to_h[maraka])):
                return True
    return False
def dharidhra_yoga_153_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        Dharidra Yoga (BV Raman 153)
        The lords of the Lagna and Navamsa Lagna should occupy the 6th, 8th or 12th and have the 
        aspect or conjunction of the lords of the 2nd and 7th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _dharidhra_yoga_153_calculation(planet_positions_rasi=pp,planet_positions_navamsa=pp_nav)
def _dharidhra_yoga_153_calculation(chart_rasi=None, planet_positions_rasi=None, chart_navamsa=None,
                                  planet_positions_navamsa=None):
    """
        Dharidra Yoga (BV Raman 153)
        The lords of the Lagna and Navamsa Lagna should occupy the 6th, 8th or 12th and have the 
        aspect or conjunction of the lords of the 2nd and 7th.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
        else:
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None and planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    house_of_rasi_lagna = p_to_h_rasi[const._ascendant_symbol]
    house_of_navamsa_lagna = p_to_h_navamsa[const._ascendant_symbol]
    house_of_rasi_2nd = (house_of_rasi_lagna+const.HOUSE_2)%12
    house_of_rasi_7th = (house_of_rasi_lagna+const.HOUSE_7)%12 
    rasi_lagna_dusthanas = [(house_of_rasi_lagna+h)%12 for h in [const.HOUSE_6, const.HOUSE_8, const.HOUSE_12]]
    if planet_positions_rasi is not None:
        lord_of_rasi_lagna = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_rasi_lagna)
        lord_of_rasi_2nd = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_rasi_2nd) 
        lord_of_rasi_7th = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_rasi_7th)
    else:
        lord_of_rasi_lagna = house.house_owner(chart_rasi, house_of_rasi_lagna)
        lord_of_rasi_2nd = house.house_owner(chart_rasi, house_of_rasi_2nd) 
        lord_of_rasi_7th = house.house_owner(chart_rasi, house_of_rasi_7th) 
    if planet_positions_navamsa is not None:
        lord_of_navamsa_lagna = house.house_owner_from_planet_positions(planet_positions_navamsa, house_of_navamsa_lagna)
    else:
        lord_of_navamsa_lagna = house.house_owner(chart_navamsa, house_of_navamsa_lagna)
    # The lords of the Lagna and Navamsa Lagna should occupy the 6th, 8th or 12th
    lord_of_lagna_occupy_lagna_dusthana = p_to_h_rasi[lord_of_rasi_lagna] in rasi_lagna_dusthanas
    if not lord_of_lagna_occupy_lagna_dusthana: return False
    lord_of_navamsa_occupy_lagna_dusthana = p_to_h_rasi[lord_of_navamsa_lagna] in rasi_lagna_dusthanas
    if not lord_of_navamsa_occupy_lagna_dusthana: return False

    # lords of the Lagna and Navamsa Lagna have the aspect or conjunction of the lords of the 2nd and 7th.
    planets_aspecting_lord_of_lagna = house.planets_aspecting_the_planet(chart_rasi, lord_of_rasi_lagna)
    lord_of_lagna_rasi_aspected_by_lords_of_2nd_and_7th = \
            all(p in planets_aspecting_lord_of_lagna for p in [lord_of_rasi_2nd, lord_of_rasi_7th])
    lord_of_lagna_rasi_conjoins_lords_of_2nd_and_7th = ( (p_to_h_rasi[lord_of_rasi_2nd]==p_to_h_rasi[lord_of_rasi_lagna]) and 
                                                    (p_to_h_rasi[lord_of_rasi_7th]==p_to_h_rasi[lord_of_rasi_lagna]) )
    if not (lord_of_lagna_rasi_aspected_by_lords_of_2nd_and_7th or lord_of_lagna_rasi_conjoins_lords_of_2nd_and_7th): return False
    
    planets_aspecting_lord_of_navamsa = house.planets_aspecting_the_planet(chart_rasi, lord_of_navamsa_lagna)
    lord_of_lagna_navamsa_aspected_by_lords_of_2nd_and_7th = \
            all(p in planets_aspecting_lord_of_navamsa for p in [lord_of_rasi_2nd, lord_of_rasi_7th])
    lord_of_lagna_navamsa_conjoins_lords_of_2nd_and_7th = ( (p_to_h_rasi[lord_of_rasi_2nd]==p_to_h_rasi[lord_of_navamsa_lagna]) and 
                                                    (p_to_h_rasi[lord_of_rasi_7th]==p_to_h_rasi[lord_of_navamsa_lagna]) )
    return (lord_of_lagna_navamsa_aspected_by_lords_of_2nd_and_7th or lord_of_lagna_navamsa_conjoins_lords_of_2nd_and_7th)
    

    
def _yukthi_samanwithavagmi_yoga_154_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Yukthi Samanwithavagmi Yoga (BV Raman 154)
    Definition: The 2nd lord should join a benefic in a kendra or thrikona, 
    or be exalted and combined with Jupiter.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h2 = (asc_h + const.HOUSE_2) % 12

    if planet_positions is not None:
        l2 = int(house.house_owner_from_planet_positions(planet_positions, h2))
    else:
        l2 = int(house.house_owner(chart_1d, h2))

    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    l2_h = p_to_h[l2]
    
    # Kendra/Thrikona logic using your saved lambda info
    # Assuming yoga.quadrants_of_the_house and yoga.trines_of_the_house are available
    kendras = quadrants_of_the_house(asc_h)
    thrikonas = trines_of_the_house(asc_h)
    auspicious_houses = set(kendras + thrikonas)

    # Condition A: L2 joins a benefic in Kendra or Thrikona
    cond_a = False
    if l2_h in auspicious_houses:
        for b in _natural_benefics:
            if b != l2 and p_to_h[b] == l2_h:
                cond_a = True
                break

    # Condition B: L2 is exalted and combined with Jupiter
    is_exalted = utils.is_planet_in_exalation(l2, l2_h, planet_positions,enforce_deep_exaltation=False)
    combined_with_jupiter = (p_to_h[const.JUPITER_ID] == l2_h)
    cond_b = is_exalted and combined_with_jupiter

    return cond_a or cond_b
def yukthi_samanwithavagmi_yoga_154_from_jd_place(jd,place,divisional_chart_factor=1):
    """
       Yukthi Samanwithavagmi Yoga (BV Raman 154)
        Definition: The 2nd lord should join a benefic in a kendra or thrikona, 
            or be exalted and combined with Jupiter.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _yukthi_samanwithavagmi_yoga_154_calculation(planet_positions=planet_positions, natural_benefics=nb)
def yukthi_samanwithavagmi_yoga_155_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    Yukthi Samanwithavagmi Yoga (BV Raman 155)
        Definition: The lord of speech should occupy a kendra, attain paramochha and gain Parvatamsa, 
        while Jupiter or Venus should be in Simhasanamsa.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    v_scores = charts.vaiseshikamsa_dhasavarga_of_planets(jd, place)
    return _yukthi_samanwithavagmi_yoga_155_calculation(planet_positions=planet_positions,vaiseshikamsa_scores=v_scores)
def yukthi_samanwithavagmi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    Method=1 => Yukthi Samanwithavagmi Yoga (BV Raman 154)
        Yukthi Samanwithavagmi Yoga (BV Raman 154)
        Definition: The 2nd lord should join a benefic in a kendra or thrikona, 
            or be exalted and combined with Jupiter.
    Method=2 => Yukthi Samanwithavagmi Yoga (BV Raman 155)
        Definition: L2 in Kendra, at Paramochha and Parvatamsa; 
            Jupiter/Venus in Simhasanamsa.
    """
    if yukthi_samanwithavagmi_yoga_154_from_jd_place(jd, place, divisional_chart_factor): 
        return True
    else:
        return yukthi_samanwithavagmi_yoga_155_from_jd_place(jd, place, divisional_chart_factor)
    
def _yukthi_samanwithavagmi_yoga_155_calculation(chart_1d=None, planet_positions=None,
                                                 vaiseshikamsa_scores=None):
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _asc = const._ascendant_symbol
    asc_h = p_to_h[_asc]
    h2 = (asc_h + const.HOUSE_2) % 12
    l2 = house.house_owner_from_planet_positions(planet_positions, h2)
    l2_h = p_to_h[l2]

    # 2. Get Vaisheshikamsa Scores specifically for Dasavarga
    # Names: Simhaasanaamsa (5), Paaraavataamsa (6)
    v_scores = vaiseshikamsa_scores

    # 3. L2 in Kendra (Quadrants of Lagna)
    if l2_h not in quadrants_of_the_house(asc_h):
        return False

    # 4. L2 at Paramochha (Deep Exaltation)
    if not utils.is_planet_in_exalation(l2, l2_h, planet_positions, enforce_deep_exaltation=True):
        return False

    # 5. Check Dasavarga Vaisheshikamsa Requirements
    # Parvatamsa (Paaraavataamsa) = 6
    # Simhasanamsa (Simhaasanaamsa) = 5
    l2_score = v_scores[l2]
    jup_score = v_scores[const.JUPITER_ID]
    ven_score = v_scores[const.VENUS_ID]

    has_parvatamsa = (l2_score >= 6)
    has_simhasanamsa = (jup_score >= 5 or ven_score >= 5)

    return has_parvatamsa and has_simhasanamsa
def parihasaka_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """
    156. Parihasaka Yoga:
    The lord of the Navamsa occupied by the Sun should attain Vaiseshikamsa 
    (score of 13 in Shodhasavarga) and be in the 2nd house of the Rasi chart.
    """

    # 1. Get Vaiseshikamsa scores (Shodhasavarga count)
    # Returns list where index = planet_id, value = count of own/exalted vargas
    v_scores = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    v_scores = [v[0] for k,v in v_scores.items()]
    # 2. Get Planet Positions for D1 and D9
    pp_d1 = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_d9 = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    
    # 3. Find Sun's sign in D9 and identify its Lord
    chart_d9 = utils.get_house_planet_list_from_planet_positions(pp_d9)
    p_to_h_d9 = utils.get_planet_to_house_dict_from_chart(chart_d9)
    sun_sign_d9 = p_to_h_d9[const.SUN_ID]
    
    # Identify the Lord of the sign Sun occupies in Navamsa
    lord_of_sun_navamsa = int(house.house_owner_from_planet_positions(pp_d9, sun_sign_d9))

    # 4. Check Criteria
    # Criteria A: Must attain Vaiseshikamsa (Score of 13 per BVR Raman)
    if v_scores[lord_of_sun_navamsa] < 13:
        return False

    # Criteria B: Must be in the 2nd House of the Rasi (D1) chart
    chart_d1 = utils.get_house_planet_list_from_planet_positions(pp_d1)
    p_to_h_d1 = utils.get_planet_to_house_dict_from_chart(chart_d1)
    
    asc_house_d1 = p_to_h_d1['L']
    second_house_d1 = (asc_house_d1 + 1) % 12
    lord_placement_d1 = p_to_h_d1[lord_of_sun_navamsa]

    return lord_placement_d1 == second_house_d1
def _asatyavadi_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        Asatyavadi Ycga Definition.*-If the lord of the 2nd occupies the
        house of Saturn or Mars and if malefics join kendras and thrikonas.
    """
    if planet_positions is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(utils.get_house_planet_list_from_planet_positions(planet_positions))
        asc_house = p_to_h['L']
        second_house = (asc_house + 1) % 12
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, second_house)
        lord_2nd_pos = p_to_h[lord_of_2nd]
        dispositor_of_2nd_lord = house.house_owner_from_planet_positions(planet_positions, lord_2nd_pos)
    else:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
        asc_house = p_to_h['L']
        second_house = (asc_house + 1) % 12
        lord_of_2nd = house.house_owner(chart_1d, second_house)
        lord_2nd_pos = p_to_h[lord_of_2nd]
        dispositor_of_2nd_lord = house.house_owner(chart_1d, lord_2nd_pos)

    # 1. Check if lord of 2nd occupies the house of Saturn or Mars
    # This means the sign occupied by the 2nd lord must be owned by Saturn or Mars
    if dispositor_of_2nd_lord not in [const.SATURN_ID, const.MARS_ID]:
        return False

    # 2. Check if malefics join kendras and thrikonas
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    # Using your lambda functions from yoga.py
    quadrants = quadrants_of_the_house(asc_house)
    trines = trines_of_the_house(asc_house)
    target_houses = set(quadrants) | set(trines)

    # Check if any malefics are in these houses
    for p_id in _natural_malefics:
        if p_id in p_to_h and p_to_h[p_id] in target_houses:
            return True
    return False

def asatyavadi_yoga(chart_1d, natural_malefics=None):
    """
        Asatyavadi Ycga Definition.*-If the lord of the 2nd occupies the
        house of Saturn or Mars and if malefics join kendras and thrikonas.
    """
    return _asatyavadi_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)

def asatyavadi_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """
        Asatyavadi Ycga Definition.*-If the lord of the 2nd occupies the
        house of Saturn or Mars and if malefics join kendras and thrikonas.
    """
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return _asatyavadi_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions, natural_malefics=natural_malefics)

def asatyavadi_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    """
        Asatyavadi Ycga Definition.*-If the lord of the 2nd occupies the
        house of Saturn or Mars and if malefics join kendras and thrikonas.
    """
    planet_positions = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _nb = charts.benefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return asatyavadi_yoga_from_planet_positions(planet_positions, natural_malefics=_nb)
def _jada_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None, mandi_house=None):
    """
        Defnition.-The lord of the 2nd should be posited in the l0th with maleficsor the 2nd must be 
        joined by the Sun and Mandi.
    """
    # Determine p_to_h and lord using the required template
    if planet_positions is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(utils.get_house_planet_list_from_planet_positions(planet_positions))
        asc_house = p_to_h['L']
        second_house = (asc_house + 1) % 12
        tenth_house = (asc_house + 9) % 12
        lord_of_2nd = int(house.house_owner_from_planet_positions(planet_positions, second_house))
    else:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
        asc_house = p_to_h['L']
        second_house = (asc_house + 1) % 12
        tenth_house = (asc_house + 9) % 12
        lord_of_2nd = int(house.house_owner(chart_1d, second_house))

    # Handle malefics template
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    # --- Criterion A: 2nd Lord in 10th with malefics ---
    cond_a = False
    if p_to_h[lord_of_2nd] == tenth_house:
        # Check if any other malefic is also in the 10th house
        for m_id in _natural_malefics:
            if m_id != lord_of_2nd and p_to_h.get(m_id) == tenth_house:
                cond_a = True
                break
                
    # --- Criterion B: 2nd House joined by Sun and Mandi ---
    cond_b = False
    if mandi_house is not None:
        sun_in_2nd = p_to_h.get(const.SUN_ID) == second_house
        mandi_in_2nd = mandi_house == second_house
        if sun_in_2nd and mandi_in_2nd:
            cond_b = True

    return cond_a or cond_b

def jada_yoga(chart_1d, natural_malefics=None, mandi_house=None):
    """
        Defnition.-The lord of the 2nd should be posited in the l0th with maleficsor the 2nd must be 
        joined by the Sun and Mandi.
    """
    return _jada_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics, mandi_house=mandi_house)

def jada_yoga_from_planet_positions(planet_positions, natural_malefics=None, mandi_house=None):
    """
        Defnition.-The lord of the 2nd should be posited in the l0th with maleficsor the 2nd must be 
        joined by the Sun and Mandi.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return _jada_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions, natural_malefics=natural_malefics, mandi_house=mandi_house)

def jada_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        Defnition.-The lord of the 2nd should be posited in the l0th with maleficsor the 2nd must be 
        joined by the Sun and Mandi.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    
    # Calculate Mandi per specific user instruction
    y, m, d, fh = utils.jd_to_local(jd, place)
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')

    mandi_h, _ = drik.dasavarga_from_long(g_lon_info) 
    return _jada_yoga_calculation(planet_positions=pp, natural_malefics=nm, mandi_house=mandi_h)
def _marud_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Marud Yoga: Jupiter in 5th or 9th from Venus, the Moon in the 5th from Jupiter 
    and the Sun in a kendra from the Moon.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # 1. Jupiter in 5th or 9th from Venus
    # (House of Jup - House of Ven) % 12 + 1 gives the relative position
    jup_from_ven = house.get_relative_house_of_planet(p_to_h[const.VENUS_ID],p_to_h[const.JUPITER_ID])
    cond1 = jup_from_ven in [5,9]
    
    # 2. Moon in 5th from Jupiter
    moon_from_jup = house.get_relative_house_of_planet(p_to_h[const.JUPITER_ID],p_to_h[const.MOON_ID])
    cond2 = (moon_from_jup == 5)
    
    # 3. Sun in a kendra (1,4,7,10) from the Moon
    # Using the lambda function quadrants_of_the_house
    sun_house = p_to_h[const.SUN_ID]
    moon_house = p_to_h[const.MOON_ID]
    cond3 = sun_house in quadrants_of_the_house(moon_house)
    
    return cond1 and cond2 and cond3

def marud_yoga(chart_1d):
    """
    Marud Yoga: Jupiter in 5th or 9th from Venus, the Moon in the 5th from Jupiter 
    and the Sun in a kendra from the Moon.
    """
    return _marud_yoga_calculation(chart_1d=chart_1d)

def marud_yoga_from_planet_positions(planet_positions):
    """
    Marud Yoga: Jupiter in 5th or 9th from Venus, the Moon in the 5th from Jupiter 
    and the Sun in a kendra from the Moon.
    """
    return _marud_yoga_calculation(planet_positions=planet_positions)

def marud_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _marud_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _budha_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Budha Yoga: Jupiter in Lagna, the Moon in a kendra, 
    Rahu in the 2nd from the Moon and the Sun and Mars in the 3rd from Rahu.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc = const._ascendant_symbol
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # 1. Jupiter in Lagna (House 0 in a house-based relative chart, but usually p_to_h[L] == p_to_h[Jup])
    # Based on standard Yoga logic: Jupiter must be in the 1st house
    jupiter_in_lagna = (p_to_h[const.JUPITER_ID] == p_to_h[asc])

    # 2. Moon in a kendra (1, 4, 7, 10 from Lagna)
    # Using the lambda quadrants_of_the_house
    moon_in_kendra = p_to_h[const.MOON_ID] in quadrants_of_the_house(p_to_h[asc])

    # 3. Rahu in the 2nd from the Moon
    rahu_from_moon = house.get_relative_house_of_planet(p_to_h[const.MOON_ID], p_to_h[const.RAHU_ID])
    rahu_2nd_from_moon = (rahu_from_moon == 2)

    # 4. Sun and Mars in the 3rd from Rahu
    sun_from_rahu = house.get_relative_house_of_planet(p_to_h[const.RAHU_ID], p_to_h[const.SUN_ID])
    mars_from_rahu = house.get_relative_house_of_planet(p_to_h[const.RAHU_ID], p_to_h[const.MARS_ID])
    sun_mars_3rd_from_rahu = (sun_from_rahu == 3 and mars_from_rahu == 3)

    return jupiter_in_lagna and moon_in_kendra and rahu_2nd_from_moon and sun_mars_3rd_from_rahu

def budha_yoga(chart_1d):
    """
    Budha Yoga: Jupiter in Lagna, the Moon in a kendra, 
    Rahu in the 2nd from the Moon and the Sun and Mars in the 3rd from Rahu.
    """
    return _budha_yoga_calculation(chart_1d=chart_1d)

def budha_yoga_from_planet_positions(planet_positions):
    """
    Budha Yoga: Jupiter in Lagna, the Moon in a kendra, 
    Rahu in the 2nd from the Moon and the Sun and Mars in the 3rd from Rahu.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return _budha_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)

def budha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Budha Yoga: Jupiter in Lagna, the Moon in a kendra, 
    Rahu in the 2nd from the Moon and the Sun and Mars in the 3rd from Rahu.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _budha_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _mooka_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Mooka Yoga: The 2nd lord should join the 8th with Jupiter. 
    The yoga does not apply if the 8th house happens to be Jupiter's own or exaltation sign.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # Identify the houses relative to Lagna
    house_2 = (p_to_h['L'] + 1) % 12
    house_8 = (p_to_h['L'] + 7) % 12

    # Get the 2nd Lord without int() casting
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)

    # Condition 1: 2nd Lord and Jupiter are in the 8th house
    second_lord_jupiter_in_eighth_house = (p_to_h[lord_of_2nd] == house_8) and (p_to_h[const.JUPITER_ID] == house_8)

    # Condition 2: Exception - Yoga does not apply if 8th house is Jupiter's own or exaltation sign
    jupiter_exalted = utils.is_planet_in_exalation(const.JUPITER_ID, house_8,enforce_deep_exaltation=False)
    return second_lord_jupiter_in_eighth_house and not jupiter_exalted

def mooka_yoga(chart_1d):
    """
    Mooka Yoga: The 2nd lord should join the 8th with Jupiter. 
    The yoga does not apply if the 8th house happens to be Jupiter's own or exaltation sign.
    """
    return _mooka_yoga_calculation(chart_1d)

def mooka_yoga_from_planet_positions(planet_positions):
    """
    Mooka Yoga: The 2nd lord should join the 8th with Jupiter. 
    The yoga does not apply if the 8th house happens to be Jupiter's own or exaltation sign.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return _mooka_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)

def mooka_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Mooka Yoga: The 2nd lord should join the 8th with Jupiter. 
    The yoga does not apply if the 8th house happens to be Jupiter's own or exaltation sign.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _mooka_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _netranasa_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Netranasa Yoga: If the lords of the 10th and 6th occupy Lagna with the 2nd lord, 
    or if they are in Neechamsat (debilitation).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # Identify the houses relative to Lagna
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    house_6 = (lagna_house + 5) % 12
    house_10 = (lagna_house + 9) % 12

    # Get the House Lords
    if planet_positions is not None:
        lord_of_2 = house.house_owner_from_planet_positions(planet_positions, house_2)
        lord_of_6 = house.house_owner_from_planet_positions(planet_positions, house_6)
        lord_of_10 = house.house_owner_from_planet_positions(planet_positions, house_10)
    else:
        lord_of_2 = house.house_owner(chart_1d, house_2)
        lord_of_6 = house.house_owner(chart_1d, house_6)
        lord_of_10 = house.house_owner(chart_1d, house_10)

    # Condition A: Lords of 10, 6, and 2 occupy Lagna
    cond_a = (p_to_h[lord_of_10] == lagna_house and 
              p_to_h[lord_of_6] == lagna_house and 
              p_to_h[lord_of_2] == lagna_house)
    # Condition B: Lords of 10, 6, and 2 are in Neecham (Debilitated)
    # Using the provided utils function
    deb_2 = utils.is_planet_in_debilitation(lord_of_2, p_to_h[lord_of_2], planet_positions, enforce_deep_debilitation=False)
    deb_6 = utils.is_planet_in_debilitation(lord_of_6, p_to_h[lord_of_6], planet_positions, enforce_deep_debilitation=False)
    deb_10 = utils.is_planet_in_debilitation(lord_of_10, p_to_h[lord_of_10], planet_positions, enforce_deep_debilitation=False)
    
    cond_b = (deb_2 and deb_6 and deb_10)

    return cond_a or cond_b

def netranasa_yoga(chart_1d):
    """
    Netranasa Yoga: If the lords of the 10th and 6th occupy Lagna with the 2nd lord, 
    or if they are in Neechamsat (debilitation).
    """
    return _netranasa_yoga_calculation(chart_1d=chart_1d)

def netranasa_yoga_from_planet_positions(planet_positions):
    """
    Netranasa Yoga: If the lords of the 10th and 6th occupy Lagna with the 2nd lord, 
    or if they are in Neechamsat (debilitation).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return _netranasa_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)

def netranasa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Netranasa Yoga: If the lords of the 10th and 6th occupy Lagna with the 2nd lord, 
    or if they are in Neechamsat (debilitation).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _netranasa_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _andha_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Andha Yoga: Mercury and the Moon should be in the 2nd OR the lords of 
    Lagna and the 2nd should join the 2nd with the Sun.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # Identify houses relative to Lagna
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12

    # Condition 1: Mercury (3) and Moon (1) in the 2nd house
    cond1 = (p_to_h[const.MERCURY_ID] == house_2 and p_to_h[const.MOON_ID] == house_2)

    # Condition 2: Lords of Lagna and 2nd in the 2nd house with the Sun (0)
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
        lord_of_2 = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
        lord_of_2 = house.house_owner(chart_1d, house_2)

    cond2 = (p_to_h[lord_of_lagna] == house_2 and 
             p_to_h[lord_of_2] == house_2 and 
             p_to_h[const.SUN_ID] == house_2)

    return cond1 or cond2

def andha_yoga(chart_1d):
    """
    Andha Yoga: Mercury and the Moon should be in the 2nd OR the lords of 
    Lagna and the 2nd should join the 2nd with the Sun.
    """
    return _andha_yoga_calculation(chart_1d=chart_1d)

def andha_yoga_from_planet_positions(planet_positions):
    """
    Andha Yoga: Mercury and the Moon should be in the 2nd OR the lords of 
    Lagna and the 2nd should join the 2nd with the Sun.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    return _andha_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)

def andha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Andha Yoga: Mercury and the Moon should be in the 2nd OR the lords of 
    Lagna and the 2nd should join the 2nd with the Sun.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _andha_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _sumukha_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, method=1, v_score=None):
    """
    Sumukha Yoga:
    Method 1 (166): Lord of 2nd in a kendra aspected by benefics, OR benefics join the 2nd house.
    Method 2 (167): Lord of 2nd in a kendra (Exalted/Own/Friend) AND the kendra lord is in Gopuramsa.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    kendras = quadrants_of_the_house(lagna_house)

    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)

    if method == 1:
        # 166: Lord of 2nd in kendra aspected by benefics
        cond_1a = False
        if p_to_h[lord_of_2nd] in kendras:
            aspections = house.aspected_planets_of_the_raasi(chart_1d, p_to_h[lord_of_2nd])
            if any(b in aspections for b in _natural_benefics):
                cond_1a = True
        
        # 166: OR benefics join the 2nd house
        planets_in_2nd = planets_in_raasi(house_2,p_to_h)#V4.8.0
        cond_1b = any(b in planets_in_2nd for b in _natural_benefics)
        
        return cond_1a or cond_1b

    elif method == 2:
        # 167: Lord of 2nd in a kendra + (Exalted, Own, or Friend)
        lord_2_house = p_to_h[lord_of_2nd]
        if lord_2_house not in kendras:
            return False
            
        is_strong = utils.is_planet_strong(lord_of_2nd, lord_2_house)
        # 167: Lord of that kendra attains Gopuramsa (v_score >= 4)
        if planet_positions is not None:
            kendra_lord = house.house_owner_from_planet_positions(planet_positions, lord_2_house)
        else:
            kendra_lord = house.house_owner(chart_1d, lord_2_house)
            
        # Gopuramsa usually refers to 4 Vaiseshikamsa divisions
        has_gopuramsa = v_score is not None and v_score[kendra_lord] >= 4
        
        return is_strong and has_gopuramsa

    return False
def sumukha_yoga(chart_1d=None, natural_benefics=None, method=1, v_score=None):
    """
    Sumukha Yoga:
    Method 1 (166): Lord of 2nd in a kendra aspected by benefics, OR benefics join the 2nd house.
    Method 2 (167): Lord of 2nd in a kendra (Exalted/Own/Friend) AND the kendra lord is in Gopuramsa.
    """
    return _sumukha_yoga_calculation(chart_1d=chart_1d,natural_benefics=natural_benefics, method=method,
                                     v_score=v_score)
def sumukha_yoga_from_planet_positions(planet_positions=None, natural_benefics=None, method=1, v_score=None):
    """
    Sumukha Yoga:
    Method 1 (166): Lord of 2nd in a kendra aspected by benefics, OR benefics join the 2nd house.
    Method 2 (167): Lord of 2nd in a kendra (Exalted/Own/Friend) AND the kendra lord is in Gopuramsa.
    """
    return _sumukha_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics, 
                                     method=method, v_score=v_score)
def sumukha_yoga_from_jd_place(jd, place, divisional_chart_factor=1, method=1):
    """
    Sumukha Yoga:
    Method 1 (166): Lord of 2nd in a kendra aspected by benefics, OR benefics join the 2nd house.
    Method 2 (167): Lord of 2nd in a kendra (Exalted/Own/Friend) AND the kendra lord is in Gopuramsa.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    # Calculate Vaiseshikamsa scores
    v_score = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place) # Assuming this function exists in library
    v_score = [v[0] for k,v in v_score.items()]
    return _sumukha_yoga_calculation(planet_positions=pp, natural_benefics=nb, method=method, v_score=v_score)
def _durmukha_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None, method=1, navamsa_chart=None, gulika_house=None):
    """
    Durmukha Yoga:
    Method 1 (168): Malefics in the 2nd AND its lord joins an evil planet or is in debilitation.
    Method 2 (169): Lord of 2nd (being evil) joins Gulika OR in unfriendly/debilitated Navamsa with malefics.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # Template for malefics
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)

    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12

    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)

    # 168: Malefics occupy the 2nd
    planets_in_2nd = planets_in_raasi(house_2,p_to_h)#V4.8.0
    has_malefic_in_2 = any(p != const._ascendant_symbol and int(p) in _natural_malefics for p in planets_in_2nd)
    
    # 168: Lord joins an evil planet
    house_of_lord = p_to_h[lord_of_2nd]
    planets_with_lord = planets_in_raasi(house_of_lord,p_to_h)#V4.8.0
    joins_evil = any(
        p != const._ascendant_symbol and int(p) in _natural_malefics 
        and int(p) != lord_of_2nd for p in planets_with_lord
        )
    
    # 168: Or lord is in debilitation
    is_debilitated = utils.is_planet_in_debilitation(lord_of_2nd, house_of_lord, planet_positions, enforce_deep_debilitation=False)
    
    if has_malefic_in_2 and (joins_evil or is_debilitated):
        return True

    # 169: Lord of 2nd must be a natural malefic
    if lord_of_2nd not in _natural_malefics:
        return False
        
    # 169: Joins Gulika
    joins_gulika = (p_to_h[lord_of_2nd] == gulika_house) if gulika_house is not None else False
    
    # 169: Or occupies unfriendly/debilitated Navamsa with malefics
    in_bad_navamsa = False
    if navamsa_chart is not None:
        p_to_h_nav = utils.get_planet_to_house_dict_from_chart(navamsa_chart)
        nav_house = p_to_h_nav[lord_of_2nd]
        strength = const.house_strengths_of_planets[lord_of_2nd][nav_house]
        
        # Unfriendly (1) or Debilitated (0)
        bad_strength = strength in [const._ENEMY, const._DEBILITATED_NEECHAM]
        # With malefics in Navamsa
        with_malefics_nav = any(
                p_to_h_nav[mp]==p_to_h_nav[lord_of_2nd] and mp != lord_of_2nd 
                for mp in _natural_malefics
                )
        in_bad_navamsa = bad_strength and with_malefics_nav
        
    return joins_gulika or in_bad_navamsa

    return False
def durmukha_yoga(chart_1d=None, natural_malefics=None, method=1, navamsa_chart=None, gulika_house=None):
    """
    Durmukha Yoga:
    Method 1 (168): Malefics in the 2nd AND its lord joins an evil planet or is in debilitation.
    Method 2 (169): Lord of 2nd (being evil) joins Gulika OR in unfriendly/debilitated Navamsa with malefics.
    """
    return _durmukha_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics, method=method,
                                      navamsa_chart=navamsa_chart, gulika_house=gulika_house)
def durmukha_yoga_from_planet_positions(planet_positions=None, natural_malefics=None, method=1, navamsa_chart=None, gulika_house=None):
    """
    Durmukha Yoga:
    Method 1 (168): Malefics in the 2nd AND its lord joins an evil planet or is in debilitation.
    Method 2 (169): Lord of 2nd (being evil) joins Gulika OR in unfriendly/debilitated Navamsa with malefics.
    """
    return _durmukha_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics, 
                                      method=method, navamsa_chart=navamsa_chart, gulika_house=gulika_house)
def durmukha_yoga_from_jd_place(jd, place, divisional_chart_factor=1, method=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    # Navamsa for method 2
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nav = utils.get_house_planet_list_from_planet_positions(pp_nav)
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    
    # Check if you have a function for Gulika position
    # gulika = charts.get_gulika_position(jd, place) 
    gulika_h = None # Placeholder - ask user if needed
    
    return _durmukha_yoga_calculation(planet_positions=pp, natural_malefics=nm, method=method, navamsa_chart=nav, gulika_house=gulika_h)
def _bhojana_soukhya_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, v_score=None):
    """
    Bhojana Soukhya Yoga: The powerful lord of the 2nd should occupy Vaiseshikamsa 
    and have the aspect of Jupiter or Venus.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # Identify the 2nd house and its lord
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)

    # 1. Powerful lord in Vaiseshikamsa (v_score >= 3, e.g., Parijatamsa or higher)
    has_vaiseshikamsa = v_score is not None and v_score[lord_of_2nd] >= 13
    
    # 2. Aspect of Jupiter or Venus
    # Get planets that aspect the lord of the 2nd
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_2nd)
    has_aspect = (const.JUPITER_ID in aspected_by or const.VENUS_ID in aspected_by)

    return has_vaiseshikamsa and has_aspect
def bhojana_soukhya_yoga(chart_1d=None, natural_benefics=None, v_score=None):
    """
    Bhojana Soukhya Yoga: The powerful lord of the 2nd should occupy Vaiseshikamsa 
    and have the aspect of Jupiter or Venus.
    """
    return _bhojana_soukhya_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics,
                                             v_score=v_score)
def bhojana_soukhya_yoga_from_planet_positions(planet_positions=None, natural_benefics=None, v_score=None):
    """
    Bhojana Soukhya Yoga: The powerful lord of the 2nd should occupy Vaiseshikamsa 
    and have the aspect of Jupiter or Venus.
    """
    return _bhojana_soukhya_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics,
                                             v_score=v_score)
def bhojana_soukhya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    # Get Vaiseshikamsa scores for the planets
    v_score = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    v_score = [v[0] for k,v in v_score.items()]
    return _bhojana_soukhya_yoga_calculation(planet_positions=pp, natural_benefics=nb, v_score=v_score)
def _annadana_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, v_score=None):
    """
    Annadana Yoga: The lord of the 2nd should join Vaiseshikamsa (score 13) 
    and be in conjunction with or aspected by Jupiter and Mercury.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # Identify the 2nd house and its lord
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)
    # 1. Lord of 2nd in Vaiseshikamsa (score of 13)
    has_vaiseshikamsa = v_score is not None and v_score[lord_of_2nd] >= 13 \
                or utils.is_planet_strong(lord_of_2nd, p_to_h[lord_of_2nd], include_neutral_samam=True)
    
    # 2. Conjunction with OR Aspected by Jupiter AND Mercury
    # Check Conjunction (same house)
    house_of_lord = p_to_h[lord_of_2nd]
    planets_in_house = planets_in_raasi(house_of_lord,p_to_h)#V4.8.0
    
    conj_jup = const.JUPITER_ID in planets_in_house
    conj_merc = const.MERCURY_ID in planets_in_house
    
    # Check Aspects
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_2nd)
    asp_jup = const.JUPITER_ID in aspected_by
    asp_merc = const.MERCURY_ID in aspected_by
    
    # Criteria: (Conj or Aspect Jup) AND (Conj or Aspect Merc)
    has_jup_link = conj_jup or asp_jup
    has_merc_link = conj_merc or asp_merc

    return has_vaiseshikamsa and has_jup_link and has_merc_link
def annadana_yoga(chart_1d=None, natural_benefics=None, v_score=None):
    """
    Annadana Yoga: The lord of the 2nd should join Vaiseshikamsa (score 13) 
    and be in conjunction with or aspected by Jupiter and Mercury.
    """
    return _annadana_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics, v_score=v_score)
def annadana_yoga_from_planet_position(planet_positions=None, natural_benefics=None, v_score=None):
    """
    Annadana Yoga: The lord of the 2nd should join Vaiseshikamsa (score 13) 
    and be in conjunction with or aspected by Jupiter and Mercury.
    """
    return _annadana_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics,
                                      v_score=v_score)
def annadana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    # Get Vaiseshikamsa scores for the planets
    v_score_dict = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    v_score = [v[0] for p,v in v_score_dict.items()]
    return _annadana_yoga_calculation(planet_positions=pp, natural_benefics=nb, v_score=v_score)
def _parannabhojana_yoga_calculation(chart_1d=None, planet_positions=None, navamsa_chart=None):
    """
    Parannabhojana Yoga: The lord of the 2nd should be in debilitation or in 
    unfriendly navamsas and aspected by a debilitated planet.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # 2nd House and Lord
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)

    # Condition 1: Lord of 2nd in debilitation (Rasi) OR unfriendly Navamsa
    # Rasi debilitation check
    is_deb_rasi = utils.is_planet_in_debilitation(lord_of_2nd, p_to_h[lord_of_2nd], planet_positions, enforce_deep_debilitation=False)
    
    # Navamsa unfriendly check
    is_unfriendly_nav = False
    if navamsa_chart is not None:
        p_to_h_nav = utils.get_planet_to_house_dict_from_chart(navamsa_chart)
        nav_house = p_to_h_nav[lord_of_2nd]
        strength_nav = const.house_strengths_of_planets[lord_of_2nd][nav_house]
        is_unfriendly_nav = strength_nav == 1 # _ENEMY constant
    
    cond1 = is_deb_rasi or is_unfriendly_nav

    # Condition 2: Aspected by a debilitated planet (in Rasi)
    aspected_by_planets = house.aspected_planets_of_the_planet(chart_1d, lord_of_2nd)
    
    has_deb_aspect = False
    for p in aspected_by_planets:
        if utils.is_planet_in_debilitation(p, p_to_h[p], planet_positions, enforce_deep_debilitation=False):
            has_deb_aspect = True
            break
            
    return cond1 and has_deb_aspect

def parannabhojana_yoga(chart_1d,navamsa_chart=None):
    return _parannabhojana_yoga_calculation(chart_1d=chart_1d,navamsa_chart=navamsa_chart)

def parannabhojana_yoga_from_planet_positions(planet_positions,navamsa_chart=None):
    return _parannabhojana_yoga_calculation(planet_positions=planet_positions,navamsa_chart=navamsa_chart)

def parannabhojana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nav = utils.get_house_planet_list_from_planet_positions(pp_nav)
    return _parannabhojana_yoga_calculation(planet_positions=pp, navamsa_chart=nav)
def _sraddhannabhuktha_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Sraddhannabhuktha Yoga: Saturn happens to own the 2nd, OR joins the 2nd lord, 
    OR the 2nd house is aspected by debilitated Saturn.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    # Identify the 2nd house and its lord
    lagna_house = p_to_h[const._ascendant_symbol]
    house_2 = (lagna_house + const.HOUSE_2) % 12
    
    if planet_positions is not None:
        lord_of_2nd = int(house.house_owner_from_planet_positions(planet_positions, house_2))
    else:
        lord_of_2nd = int(house.house_owner(chart_1d, house_2))
    # Condition 1: Saturn owns the 2nd house
    cond1 = (lord_of_2nd == const.SATURN_ID)
    # Condition 2: Saturn joins the 2nd lord
    cond2 = p_to_h[lord_of_2nd] == p_to_h[const.SATURN_ID]
    # Condition 3: 2nd house is aspected by debilitated Saturn
    # First check if Saturn is debilitated (Aries / House 0)
    is_saturn_debilitated = utils.is_planet_in_debilitation(const.SATURN_ID, p_to_h[const.SATURN_ID], planet_positions, enforce_deep_debilitation=False)
    cond3 = False
    if is_saturn_debilitated:
        # Get houses aspected by Saturn
        aspected_houses = house.aspected_houses_of_the_planet(chart_1d, const.SATURN_ID)
        if house_2 in aspected_houses:
            cond3 = True
    return cond1 or cond2 or cond3
def sraddhannabhuktha_yoga(chart_1d):
    return _sraddhannabhuktha_yoga_calculation(chart_1d=chart_1d)
def sraddhannabhuktha_yoga_from_planet_positions(planet_positions):
    return _sraddhannabhuktha_yoga_calculation(planet_positions=planet_positions)
def sraddhannabhuktha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sraddhannabhuktha_yoga_calculation(planet_positions=pp)
def _sarpaganda_yoga_calculation(chart_1d=None,planet_positions=None,maandi_house=None):
    """ Rahu should join the 2nd house with Mandi. """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    second_house = (p_to_h[const._ascendant_symbol]+const.HOUSE_2)%12
    if maandi_house:
        return p_to_h[const.RAHU_ID]==second_house and maandi_house==second_house
    return False
def sarpaganda_yoga(chart_1d,maandi_house):
    """ Rahu should join the 2nd house with Mandi. """
    return _sarpaganda_yoga_calculation(chart_1d=chart_1d, maandi_house=maandi_house)
def sarpaganda_yoga_from_planet_positions(planet_positions,maand_house):
    """ Rahu should join the 2nd house with Mandi. """
    return _sarpaganda_yoga_calculation(planet_positions=planet_positions, maandi_house=maand_house)
def sarpaganda_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """ Rahu should join the 2nd house with Mandi. """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    maandi_house, _ = drik.dasavarga_from_long(g_lon_info)
    return _sarpaganda_yoga_calculation(planet_positions=pp, maandi_house=maandi_house)
def vakchalana_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    Vakchalana Yoga (175): 
    1. A natural malefic owns the 2nd house.
    2. The 2nd lord joins a cruel Navamsa (owned by a malefic).
    3. The 2nd house is devoid of benefic aspect or association.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_9 = charts.divisional_chart(jd, place,divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    navamsa_chart = utils.get_house_planet_list_from_planet_positions(pp_9)
    nb,nm = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _vakchalana_yoga_calculation(planet_positions=pp, navamsa_chart=navamsa_chart,
                                        natural_benefics=nb, natural_malefics=nm)
def vakchalana_yoga_from_planet_positions(planet_positions,navamsa_chart,natural_benefics=None,natural_malefics=None):
    """
    Vakchalana Yoga (175): 
    1. A natural malefic owns the 2nd house.
    2. The 2nd lord joins a cruel Navamsa (owned by a malefic).
    3. The 2nd house is devoid of benefic aspect or association.
    """
    return _vakchalana_yoga_calculation(planet_positions=planet_positions, navamsa_chart=navamsa_chart,
                                        natural_benefics=natural_benefics, natural_malefics=natural_malefics)
def vakchalana_yoga(chart_1d,navamsa_chart,natural_benefics=None,natural_malefics=None):
    """
    Vakchalana Yoga (175): 
    1. A natural malefic owns the 2nd house.
    2. The 2nd lord joins a cruel Navamsa (owned by a malefic).
    3. The 2nd house is devoid of benefic aspect or association.
    """
    return _vakchalana_yoga_calculation(chart_1d=chart_1d,navamsa_chart=navamsa_chart,
                                        natural_benefics=natural_benefics, natural_malefics=natural_malefics)
def _vakchalana_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None, 
                                 natural_malefics=None,planet_positions_navamsa=None,navamsa_chart=None):
    """
    Vakchalana Yoga (175): 
    1. A natural malefic owns the 2nd house.
    2. The 2nd lord joins a cruel Navamsa (owned by a malefic).
    3. The 2nd house is devoid of benefic aspect or association.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
            navamsa_chart = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_1d is None or navamsa_chart is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    # Passing natural_benefics=None as per your preference
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_2 = (lagna_house + const.HOUSE_2) % 12
    # Use house_owner logic from planet_positions if available
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2)
    # 1. Malefic owns the 2nd house (Sun, Mars, Saturn)
    is_malefic_lord = lord_of_2nd in _natural_malefics
    # 2. 2nd Lord in a Cruel Navamsa
    is_cruel_nav = False
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(navamsa_chart)
    nav_house_idx = p_to_h_nav[lord_of_2nd]
    nav_lord = ( house.house_owner_from_planet_positions(planet_positions_navamsa, nav_house_idx) if planet_positions_navamsa
                 else house.house_owner(navamsa_chart, nav_house_idx) )
    if nav_lord in [const.SUN_ID, const.MARS_ID, const.SATURN_ID]:
        is_cruel_nav = True
    # 3. 2nd House devoid of benefic aspect/association
    planets_in_2nd = planets_in_raasi(house_2,p_to_h)#V4.8.0
    has_benefic_assoc = any(b != const._ascendant_symbol and b in planets_in_2nd for b in _natural_benefics)
    aspected_by = house.aspected_planets_of_the_raasi(chart_1d, house_2)
    has_benefic_aspect = any(b in aspected_by for b in _natural_benefics)
    return is_malefic_lord and is_cruel_nav and not (has_benefic_assoc or has_benefic_aspect)
def _vishaprayoga_yoga_calculation(chart_rasi=None, planet_positions=None, natural_malefics=None, 
                                   planet_positions_navamsa=None,navamsa_chart=None):
    """
    Vishaprayoga Yoga (176): 
    1. 2nd house joined AND aspected by malefics.
    2. 2nd lord in a cruel Navamsa (owned by malefic).
    3. 2nd lord (in Rasi) aspected by a malefic.
    """
    if planet_positions is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
            navamsa_chart = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or navamsa_chart is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    lagna_house = p_to_h['L']
    house_2 = (lagna_house + 1) % 12
    # Joined by malefic
    planets_in_2nd = planets_in_raasi(house_2,p_to_h,exclude_lagna=True)
    joined_by_malefic = any(m != const._ascendant_symbol and m in planets_in_2nd for m in _natural_malefics)
    # Aspected by malefic
    aspected_by = house.aspected_planets_of_the_raasi(chart_rasi, house_2)
    house_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    # 2nd Lord Details
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2)
    else:
        lord_of_2nd = house.house_owner(chart_rasi, house_2)
    # Cruel Navamsa
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(navamsa_chart)
    nav_lord = ( 
        house.house_owner_from_planet_positions(planet_positions_navamsa, p_to_h_nav[lord_of_2nd]) if planet_positions_navamsa
        else house.house_owner(navamsa_chart, p_to_h_nav[lord_of_2nd]) 
        )
    is_cruel_nav = nav_lord in [const.SUN_ID, const.MARS_ID, const.SATURN_ID]
    # Lord aspected by malefic (Rasi)
    lord_aspected_by = house.aspected_planets_of_the_planet(chart_rasi, lord_of_2nd)
    lord_aspected_by_malefic = any(m in lord_aspected_by for m in _natural_malefics)
    return joined_by_malefic and house_aspected_by_malefic and is_cruel_nav and lord_aspected_by_malefic
def vishaprayoga_yoga(chart_rasi,navamsa_chart,natural_malefics=None):
    """
    Vishaprayoga Yoga (176): 
    1. 2nd house joined AND aspected by malefics.
    2. 2nd lord in a cruel Navamsa (owned by malefic).
    3. 2nd lord (in Rasi) aspected by a malefic.
    """
    return _vishaprayoga_yoga_calculation(chart_rasi=chart_rasi,navamsa_chart=navamsa_chart, natural_malefics=natural_malefics )
def vishaprayoga_yoga_from_planet_positions(planet_positions,planet_positions_navamsa,natural_malefics=None):
    """
    Vishaprayoga Yoga (176): 
    1. 2nd house joined AND aspected by malefics.
    2. 2nd lord in a cruel Navamsa (owned by malefic).
    3. 2nd lord (in Rasi) aspected by a malefic.
    """
    return _vishaprayoga_yoga_calculation(planet_positions=planet_positions,planet_positions_navamsa=planet_positions_navamsa, 
                                          natural_malefics=natural_malefics )
def vishaprayoga_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    Vishaprayoga Yoga (176): 
    1. 2nd house joined AND aspected by malefics.
    2. 2nd lord in a cruel Navamsa (owned by malefic).
    3. 2nd lord (in Rasi) aspected by a malefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_9 = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _vishaprayoga_yoga_calculation(planet_positions=pp,planet_positions_navamsa=pp_9, natural_malefics=nm)
def _bhratruvriddhi_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    Bhratruvriddhi Yoga (177): 3rd lord, Mars, or 3rd house joined/aspected by benefics and strong.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    lagna_house = p_to_h['L']
    house_3 = (lagna_house + 2) % 12
    if planet_positions is not None:
        lord_of_3 = house.house_owner_from_planet_positions(planet_positions, house_3)
    else:
        lord_of_3 = house.house_owner(chart_1d, house_3)
    def check_strength_and_benefic(p_id):
        p_house = p_to_h[p_id]
        # Strength: Exalted, Own, or Friend
        is_strong = utils.is_planet_strong(p_id, p_house, include_neutral_samam=False)
        # Benefic link
        joined = any(b != const._ascendant_symbol and b in planets_in_raasi(p_house,p_to_h) for b in _natural_benefics if b != p_id)#V4.8.0
        aspected = any(b in house.aspected_planets_of_the_planet(chart_1d, p_id) for b in _natural_benefics)
        return is_strong and (joined or aspected)
    # Influence on House 3
    house_joined = any(b != const._ascendant_symbol and b in planets_in_raasi(house_3,p_to_h) for b in _natural_benefics)#V4.8.0
    house_aspected = any(b in house.aspected_planets_of_the_raasi(chart_1d, house_3) for b in _natural_benefics)
    return check_strength_and_benefic(lord_of_3) or check_strength_and_benefic(const.MARS_ID) or (house_joined or house_aspected)
def bhratruvriddhi_yoga(chart_1d, natural_benefics=None):
    """
    Bhratruvriddhi Yoga (177): 3rd lord, Mars, or 3rd house joined/aspected by benefics and strong.
    """
    return _bhratruvriddhi_yoga_calculation(chart_1d,natural_benefics=natural_benefics)
def bhratruvriddhi_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
    Bhratruvriddhi Yoga (177): 3rd lord, Mars, or 3rd house joined/aspected by benefics and strong.
    """
    return _bhratruvriddhi_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def bhratruvriddhi_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    Bhratruvriddhi Yoga (177): 3rd lord, Mars, or 3rd house joined/aspected by benefics and strong.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place,divisional_chart_factor=divisional_chart_factor)
    return _bhratruvriddhi_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def sodaranasa_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
    Sodaranasa Yoga: Mars and the 3rd lord should occupy the 8th (3rd, 5th or 7th) 
    house and be aspected by malefics.
    """
    if chart_1d is None and planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagnam_house = p_to_h[const._ascendant_symbol]
    # Identify the 3rd House
    third_house = (lagnam_house + const.HOUSE_3) % 12
    if planet_positions is not None:
        lord_of_3rd = int(house.house_owner_from_planet_positions(planet_positions, third_house))
    else:
        lord_of_3rd = int(house.house_owner(chart_1d, third_house))
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)
    # Target houses: 8th, 3rd, 5th, or 7th
    target_houses = [
        (lagnam_house + const.HOUSE_8) % 12, # 8th house
        third_house,                         # 3rd house
        (lagnam_house + const.HOUSE_5) % 12, # 5th house
        (lagnam_house + const.HOUSE_7) % 12 # 7th house
    ]
    mars_house = p_to_h[const.MARS_ID]
    third_lord_house = p_to_h[lord_of_3rd]
    # Mars and 3rd Lord must occupy one of the target houses
    if mars_house in target_houses and third_lord_house in target_houses:
        # Check for malefic aspects
        mars_aspected_by = house.planets_aspecting_the_planet(chart_1d, const.MARS_ID)
        lord_aspected_by = house.planets_aspecting_the_planet(chart_1d, lord_of_3rd)
        # Combined set of planets aspecting either Mars or the 3rd Lord
        all_aspecting_planets = set(mars_aspected_by) | set(lord_aspected_by)
        # If any malefic aspects either one, the condition is met
        if any(p in _natural_malefics for p in all_aspecting_planets):
            return True
    return False
def sodaranasa_yoga(chart_1d):
    """
    Sodaranasa Yoga: Mars and the 3rd lord should occupy the 8th (3rd, 5th or 7th) 
    house and be aspected by malefics.
    """
    return sodaranasa_yoga_calculation(chart_1d)
def sodaranasa_yoga_from_planet_positions(planet_positions):
    """
    Sodaranasa Yoga: Mars and the 3rd lord should occupy the 8th (3rd, 5th or 7th) 
    house and be aspected by malefics.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return sodaranasa_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)
def sodaranasa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Sodaranasa Yoga: Mars and the 3rd lord should occupy the 8th (3rd, 5th or 7th) 
    house and be aspected by malefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return sodaranasa_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _ekabhagini_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        179. Ekabhagini Yoga Definition.-Mercury, the lord of the 3rd and Mars should join 
        the 3rd house, the Moon and Saturn respectively.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    third_house = (asc_house+const.HOUSE_3)%12
    mercury_in_3rd_house = p_to_h[const.MERCURY_ID]==third_house
    if planet_positions is not None:
        lord_of_3rd = house.house_owner_from_planet_positions(planet_positions, third_house)
    else:
        lord_of_3rd = house.house_owner(chart_1d, third_house)
    moon_with_lord_of_3rd = p_to_h[const.MOON_ID]==p_to_h[lord_of_3rd]
    mars_with_saturn = p_to_h[const.MARS_ID]==p_to_h[const.SATURN_ID]
    return mercury_in_3rd_house and moon_with_lord_of_3rd and mars_with_saturn
def ekabhagini_yoga(chart_1d):
    """
        179. Ekabhagini Yoga Definition.-Mercury, the lord of the 3rd and Mars should join 
        the 3rd house, the Moon and Saturn respectively.
    """
    return _ekabhagini_yoga_calculation(chart_1d=chart_1d)
def ekabhagini_yoga_from_planet_positions(planet_positions):
    """
        179. Ekabhagini Yoga Definition.-Mercury, the lord of the 3rd and Mars should join 
        the 3rd house, the Moon and Saturn respectively.
    """
    return _ekabhagini_yoga_calculation(planet_positions=planet_positions)
def ekabhagini_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
        179. Ekabhagini Yoga Definition.-Mercury, the lord of the 3rd and Mars should join 
        the 3rd house, the Moon and Saturn respectively.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _ekabhagini_yoga_calculation(planet_positions=pp)
def dwadasa_sahodara_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Dwadasa Sahodara Yoga: If the 3rd lord is in a kendra and
    exalted Mars joins Jupiter in a thrikona from the 3rd lord, 
    the above yoga is caused.
    """
    if chart_1d is None and planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagnam_house = p_to_h[const._ascendant_symbol]
    third_house = (lagnam_house + const.HOUSE_3) % 12
    if planet_positions is not None:
        lord_of_3rd = int(house.house_owner_from_planet_positions(planet_positions, third_house))
    else:
        lord_of_3rd = int(house.house_owner(chart_1d, third_house))
    # Condition 1: 3rd Lord in a Kendra (1, 4, 7, 10) from Lagna
    kendra_houses = quadrants_of_the_house(lagnam_house)
    lord_3rd_house = p_to_h[lord_of_3rd]; mars_house = p_to_h[const.MARS_ID]
    jupiter_house = p_to_h[const.JUPITER_ID]
    
    third_lord_in_kendra = lord_3rd_house in kendra_houses
    is_mars_exalted = utils.is_planet_in_exalation(const.MARS_ID,mars_house, enforce_deep_exaltation=False)
    mars_cojoins_jupiter = (mars_house == jupiter_house)
    mars_in_trines_of_third_lord = mars_house in trines_of_the_house(lord_3rd_house)
    return third_lord_in_kendra and is_mars_exalted and mars_cojoins_jupiter and mars_in_trines_of_third_lord

def dwadasa_sahodara_yoga(chart_1d):
    """
    Dwadasa Sahodara Yoga: If the 3rd lord is in a kendra and
    exalted Mars joins Jupiter in a thrikona from the 3rd lord, 
    the above yoga is caused.
    """
    return dwadasa_sahodara_yoga_calculation(chart_1d)

def dwadasa_sahodara_yoga_from_planet_positions(planet_positions):
    """
    Dwadasa Sahodara Yoga: If the 3rd lord is in a kendra and
    exalted Mars joins Jupiter in a thrikona from the 3rd lord, 
    the above yoga is caused.
    """
    return dwadasa_sahodara_yoga_calculation(planet_positions=planet_positions)

def dwadasa_sahodara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Dwadasa Sahodara Yoga: If the 3rd lord is in a kendra and
    exalted Mars joins Jupiter in a thrikona from the 3rd lord, 
    the above yoga is caused.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return dwadasa_sahodara_yoga_calculation(planet_positions=pp)
def _sapthasankhya_sahodara_yoga_calculation(chart_1d=None, planet_positions=None):
    """
    Sapthasankhya Sahodara Yoga:
    Definition: Lord of the 12th should join Mars and the Moon should be in the 3rd 
    with Jupiter, devoid of association with or aspect of Venus.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    # Template for lord/owner retrieval
    if planet_positions is not None:
        lord_of_12 = int(house.house_owner_from_planet_positions(planet_positions, const.HOUSE_12))
    else:
        lord_of_12 = int(house.house_owner(chart_1d, const.HOUSE_12))
        
    # Condition 1: Lord of the 12th should join Mars
    lord_12_pos = p_to_h[lord_of_12]
    mars_pos = p_to_h[const.MARS_ID]
    cond1 = (lord_12_pos == mars_pos)

    # Condition 2: Moon should be in the 3rd house with Jupiter
    moon_pos = p_to_h[const.MOON_ID]
    jupiter_pos = p_to_h[const.JUPITER_ID]
    cond2 = (moon_pos == const.HOUSE_3) and (jupiter_pos == const.HOUSE_3)

    # Condition 3: Devoid of association (same house) or aspect of Venus
    venus_pos = p_to_h[const.VENUS_ID]
    not_associated = (venus_pos != const.HOUSE_3)
    
    # Check if Moon is in the list of planets aspected by Venus
    aspected_by_venus = house.aspected_planets_of_the_planet(chart_1d, const.VENUS_ID)
    not_aspected = const.MOON_ID not in aspected_by_venus
    
    return cond1 and cond2 and not_associated and not_aspected

def sapthasankhya_sahodara_yoga(chart_1d):
    """
    Sapthasankhya Sahodara Yoga:
    Definition: Lord of the 12th should join Mars and the Moon should be in the 3rd 
    with Jupiter, devoid of association with or aspect of Venus.
    """
    return _sapthasankhya_sahodara_yoga_calculation(chart_1d)

def sapthasankhya_sahodara_yoga_from_planet_positions(planet_positions):
    """
    Sapthasankhya Sahodara Yoga:
    Definition: Lord of the 12th should join Mars and the Moon should be in the 3rd 
    with Jupiter, devoid of association with or aspect of Venus.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    return _sapthasankhya_sahodara_yoga_calculation(chart_1d=chart_1d, planet_positions=planet_positions)

def sapthasankhya_sahodara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    Sapthasankhya Sahodara Yoga:
    Definition: Lord of the 12th should join Mars and the Moon should be in the 3rd 
    with Jupiter, devoid of association with or aspect of Venus.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sapthasankhya_sahodara_yoga_calculation(planet_positions=pp)
def _parakrama_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None, natural_benefics=None):
    """
    Parakrama Yoga:
    Definition: The lord of the 3rd should join a benefic navamsa (or be exalted) being aspected by 
    (or conjoined with) benefic planets, and Mars should occupy benefic signs.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)

    _natural_benefics = _get_natural_benefics(chart_rasi, natural_benefics)
    rasi_3rd_house = (p_to_h_rasi[const._ascendant_symbol]+const.HOUSE_3)%12
    # 1. Identify Lord of the 3rd House from Rasi
    if planet_positions_rasi is not None:
        lord_of_3rd = int(house.house_owner_from_planet_positions(planet_positions_rasi, rasi_3rd_house))
    else:
        lord_of_3rd = int(house.house_owner(chart_rasi, rasi_3rd_house))
    rasi_house_of_lord_of_3rd = p_to_h_rasi[lord_of_3rd]
    navamsa_house_of_lord_of_3rd = p_to_h_navamsa[lord_of_3rd]
    # Condition 1 lord of 3d in benefic signs in navamsa
    lord_of_3rd_in_navamsa_benefic_sign = navamsa_house_of_lord_of_3rd in const.benefic_signs
    # Condition 2. The 3rd House Lord Conjunct or Aspected by Benefics
    lord_of_3rd_conjuct_with_benefics = any([rasi_house_of_lord_of_3rd==p_to_h_rasi[bp] for bp in _natural_benefics])
    planets_aspecting_lord_of_3rd = house.planets_aspecting_the_planet(chart_rasi, lord_of_3rd)
    lord_of_3rd_aspected_by_benefics = any([bp in planets_aspecting_lord_of_3rd for bp in _natural_benefics])
    # Condition 3. Mars in a Benefic Sign
    mars_in_benefic_sign = p_to_h_rasi[const.MARS_ID] in const.benefic_signs
    return lord_of_3rd_in_navamsa_benefic_sign and \
           (lord_of_3rd_conjuct_with_benefics or lord_of_3rd_aspected_by_benefics) and \
           mars_in_benefic_sign     
def parakrama_yoga(chart_rasi=None, chart_navamsa=None):
    return _parakrama_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa)

def parakrama_yoga_from_planet_positions(planet_positions_rasi=None, planet_positions_navamsa=None):
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _parakrama_yoga_calculation(planet_positions_rasi=planet_positions_rasi, planet_positions_navamsa=planet_positions_navamsa)

def parakrama_yoga_from_jd_place(jd, place,divisional_chart_factor=1):
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _parakrama_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa, natural_benefics=nb)
def _yuddha_praveena_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None,
                                      planet_positions_navamsa=None,shadvarga_data=None):
    """
        Yuddha praveenayoga - Definition.-If the lord of the navamsajoined by the planet who owns the navamsa 
        in which the 3rd lord is placed, joins his own vargas,
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_house_in_rasi = p_to_h_rasi[const._ascendant_symbol]
    third_house_in_rasi = (lagna_house_in_rasi+const.HOUSE_3)%12
    # Find lord of 3rd house in Rasi - Planet A
    if planet_positions_rasi is not None:
        lord_of_3rd_in_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, third_house_in_rasi)
    else:
        lord_of_3rd_in_rasi = house.house_owner(chart_rasi, third_house_in_rasi)
    # Find Planet A' sign in navamsa 
    house_of_rasi3rdlord_in_navamsa = p_to_h_navamsa[lord_of_3rd_in_rasi]
    # find lord of that sign in navamsa - Planet B
    if planet_positions_rasi is not None:
        lord_of_house_of_rasi3rdlord_in_navamsa = house.house_owner_from_planet_positions(planet_positions_navamsa, house_of_rasi3rdlord_in_navamsa)
    else:
        lord_of_house_of_rasi3rdlord_in_navamsa = house.house_owner(chart_navamsa, house_of_rasi3rdlord_in_navamsa)
    # Find Planet B's sign in Navamsa
    house_of_lord_of_house_of_rasi3rdlord_in_navamsa = p_to_h_navamsa[lord_of_house_of_rasi3rdlord_in_navamsa]
    # find lord of above lord in navamsa - Planet C
    if planet_positions_rasi is not None:
        lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa = house.house_owner_from_planet_positions(planet_positions_navamsa, house_of_lord_of_house_of_rasi3rdlord_in_navamsa)
    else:
        lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa = house.house_owner(chart_navamsa, house_of_lord_of_house_of_rasi3rdlord_in_navamsa)
    # Check if Planet C in its own varga in nvamsa
    house_of_lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa = p_to_h_navamsa[lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa]
    # Check if Planet C owns that sign
    if shadvarga_data is None:
        return const.house_strengths_of_planets[lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa][house_of_lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa] == const._OWNER_RULER
    else:
        vaiseshikamsa_shadvarga_count = shadvarga_data[lord_of_house_of_lord_of_house_of_rasi3rdlord_in_navamsa][0]
        return vaiseshikamsa_shadvarga_count >= 2
def yuddha_praveena_yoga(chart_rasi=None, chart_navamsa=None,shadvarga_data=None):
    """
        Yuddha praveenayoga - Definition.-If the lord of the navamsajoined by the planet who owns the navamsa 
        in which the 3rd lord is placed, joins his own vargas,
    """
    _yuddha_praveena_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                      shadvarga_data=shadvarga_data)
def yuddha_praveena_yoga_from_planet_positions(planet_positions_rasi=None,planet_positions_navamsa=None,
                                               shadvarga_data=None):
    """
        Yuddha praveenayoga - Definition.-If the lord of the navamsajoined by the planet who owns the navamsa 
        in which the 3rd lord is placed, joins his own vargas,
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _yuddha_praveena_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                             planet_positions_navamsa=planet_positions_navamsa,
                                             shadvarga_data=shadvarga_data)
def yuddha_praveena_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
        Yuddha praveenayoga - Definition.-If the lord of the navamsa joined by the planet who owns the navamsa 
        in which the 3rd lord is placed, joins his own vargas,
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    shadvarga_data = charts.vaiseshikamsa_shadvarga_of_planets(jd, place)
    return _yuddha_praveena_yoga_calculation(planet_positions_rasi=pp_rasi, 
                                             planet_positions_navamsa=pp_navamsa,
                                             shadvarga_data=shadvarga_data)
def yuddhatpoorvadridhachitta_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        184 - The exalted lord of the 3rd should join malefics in movable Rasis or Navamsas
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _yuddhatpoorvadridhachitta_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa,
                                                       natural_malefics=nm)
def yuddhatpoorvadridhachitta_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa=None,
                                                         natural_malefics=None):
    """
        184 - The exalted lord of the 3rd should join malefics in movable Rasis or Navamsas
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _yuddhatpoorvadridhachitta_yoga_calculation(planet_positions_rasi=planet_positions_rasi,
                                                       planet_positions_navamsa=planet_positions_navamsa,
                                                       natural_malefics=natural_malefics)
def yuddhatpoorvadridhachitta_yoga(chart_rasi, chart_navamsa, natural_malefics=None):
    """
        184 - The exalted lord of the 3rd should join malefics in movable Rasis or Navamsas
    """
    return _yuddhatpoorvadridhachitta_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                                       natural_malefics=natural_malefics)
def _yuddhatpoorvadridhachitta_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None,
                                      planet_positions_navamsa=None, natural_malefics=None):
    """
        184 - The exalted lord of the 3rd should join malefics in movable Rasis or Navamsas
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_house_in_rasi = p_to_h_rasi[const._ascendant_symbol]
    third_house_in_rasi = (lagna_house_in_rasi+const.HOUSE_3)%12
    # Find lord of 3rd house in Rasi - Planet A
    if planet_positions_rasi is not None:
        lord_of_3rd_in_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, third_house_in_rasi)
    else:
        lord_of_3rd_in_rasi = house.house_owner(chart_rasi, third_house_in_rasi)
    house_of_rasi3rdlord_in_rasi = p_to_h_rasi[lord_of_3rd_in_rasi]
    house_of_rasi3rdlord_in_navamsa = p_to_h_navamsa[lord_of_3rd_in_rasi]
    is_3rd_lord_exalted_in_rasi = utils.is_planet_in_exalation(lord_of_3rd_in_rasi, house_of_rasi3rdlord_in_rasi, 
                                                planet_positions=planet_positions_rasi, enforce_deep_exaltation=False)
    if natural_malefics is None:
        _natural_malefics = set(const.natural_malefics)
    else:
        _natural_malefics = set(natural_malefics)
    # Is 3rd lord cojoins malefics in movables rasi in Rasi or Navamsa
    third_lord_cojoins_malefics_in_movable_rasi = \
        any( \
            [house_of_rasi3rdlord_in_rasi==p_to_h_rasi[mp] and p_to_h_rasi[mp] in const.movable_signs \
              for mp in _natural_malefics if mp != lord_of_3rd_in_rasi])
    third_lord_cojoins_malefics_in_movable_navamsa = \
        any( \
            [house_of_rasi3rdlord_in_navamsa==p_to_h_navamsa[mp] and p_to_h_navamsa[mp] in const.movable_signs \
              for mp in _natural_malefics if mp != lord_of_3rd_in_rasi])
    return is_3rd_lord_exalted_in_rasi and (third_lord_cojoins_malefics_in_movable_rasi or third_lord_cojoins_malefics_in_movable_navamsa)

def _yuddhatpaschaddrudha_yoga_calculation(chart_rasi=None,chart_navamsa=None,
                                           planet_positions_rasi=None,planet_positions_navamsa=None,
                                           deity_index=None):
    """
    185. Yuddhatpaschaddrudha Yoga
    Definition.- The lord of the 3rd should occupy a fixed Rasi, a fixed Navamsa 
    and a cruel Shashtiamsa and the lord of the Rasi so occupied should be in debility.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    # 1. Get 3rd Lord
    lagna_house = p_to_h_rasi[const._ascendant_symbol]
    third_house_in_rasi = (lagna_house + const.HOUSE_3) % 12
    
    if planet_positions_rasi is not None:
        lord_of_3rd_in_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, third_house_in_rasi)
    else:
        lord_of_3rd_in_rasi = house.house_owner(chart_rasi, third_house_in_rasi)
    # 2. Check Fixed Rasi and Fixed Navamsa
    house_of_lord_of_3rd_in_rasi = p_to_h_rasi[lord_of_3rd_in_rasi] # This is sign index
    house_of_lord_of_3rd_in_navamsa = p_to_h_navamsa[lord_of_3rd_in_rasi]
    
    if house_of_lord_of_3rd_in_rasi not in const.fixed_signs or house_of_lord_of_3rd_in_navamsa not in const.fixed_signs:
        return False
    # 4. Dispositor of 3rd Lord in Debility
    # Get the lord of the sign where the 3rd lord sits in D1
    if planet_positions_rasi is not None:
        dispositor = house.house_owner_from_planet_positions(planet_positions_rasi, house_of_lord_of_3rd_in_rasi)
    else:
        dispositor = house.house_owner(chart_rasi, house_of_lord_of_3rd_in_rasi)
    dispositor_house = p_to_h_rasi[dispositor]
    if not utils.is_planet_in_debilitation(dispositor, dispositor_house,enforce_deep_debilitation=False):
        return False
    if planet_positions_rasi is not None:
        # 3. Check Cruel Shashtiamsa (Requires Longitude)
        lon_in_sign = planet_positions_rasi[lord_of_3rd_in_rasi+1][1][1]
        # Calculate 0-59 index with Odd/Even logic
        deity_idx = utils.get_amsa_ruler_from_planet_longitude(lon_in_sign, house_of_lord_of_3rd_in_rasi)
        if not utils.is_kroora_shashtiamsa_ruler(deity_idx):
            return False
    elif deity_index is not None and not utils.is_kroora_shashtiamsa_ruler(deity_index):
        return False
    return True
def yuddhatpaschaddrudha_yoga(chart_rasi=None,chart_navamsa=None,deity_index=None):
    """
    185. Yuddhatpaschaddrudha Yoga
    Definition.- The lord of the 3rd should occupy a fixed Rasi, a fixed Navamsa 
    and a cruel Shashtiamsa and the lord of the Rasi so occupied should be in debility.
    """
    return _yuddhatpaschaddrudha_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa, deity_index=deity_index)
def yuddhatpaschaddrudha_yoga_from_planet_positions(planet_positions_rasi=None,planet_positions_navamsa=None,
                                           deity_index=None):
    """
    185. Yuddhatpaschaddrudha Yoga
    Definition.- The lord of the 3rd should occupy a fixed Rasi, a fixed Navamsa 
    and a cruel Shashtiamsa and the lord of the Rasi so occupied should be in debility.
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _yuddhatpaschaddrudha_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                                  planet_positions_navamsa=planet_positions_navamsa,
                                                  deity_index=deity_index)
def yuddhatpaschaddrudha_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    185. Yuddhatpaschaddrudha Yoga
    Definition.- The lord of the 3rd should occupy a fixed Rasi, a fixed Navamsa 
    and a cruel Shashtiamsa and the lord of the Rasi so occupied should be in debility.
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _yuddhatpaschaddrudha_yoga_calculation(planet_positions_rasi=pp_rasi, 
                                                  planet_positions_navamsa=pp_navamsa)
def _satkathadisravana_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
    186. Satkathadisravana yoga 
    Definition: The 3rd house should be a benefic sign aspected by benefic planets 
    and the 3rd lord should join a benefic amsa (cojoins with or aspected by a benefic).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)

    # 1. Identify Lagna and 3rd House
    lagna_house = p_to_h[const._ascendant_symbol] 
    third_house = (lagna_house + 2) % 12 

    # 2. Get 3rd Lord using the required if-else template 
    if planet_positions is not None:
        lord_of_3rd = int(house.house_owner_from_planet_positions(planet_positions, third_house))
    else:
        lord_of_3rd = int(house.house_owner(chart_1d, third_house))

    # 3. Third house should be a benefic sign (Owned by a natural benefic)
    third_house_in_benefic_sign = lord_of_3rd in _natural_benefics

    # 4. Third house should be aspected by benefic planet
    planets_aspecting_third = house.planets_aspecting_the_raasi(chart_1d, third_house)
    aspected_by_benefic = any(p in _natural_benefics for p in planets_aspecting_third)
    # 5. 3rd Lord joins (conjunction) or is aspected by a benefic
    cojoins_benefic = any(p_to_h[bp] == p_to_h[lord_of_3rd] for bp in _natural_benefics if bp != lord_of_3rd)
    
    aspects_on_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_3rd)
    lord_aspected_by_benefic = any(p in _natural_benefics for p in aspects_on_lord)
    lord_requirement = cojoins_benefic or lord_aspected_by_benefic
    return third_house_in_benefic_sign and aspected_by_benefic and lord_requirement
def satkathadisravana_yoga(chart_1d=None, natural_benefics=None):
    """
    186. Satkathadisravana yoga 
    Definition: The 3rd house should be a benefic sign aspected by benefic planets 
    and the 3rd lord should join a benefic amsa (cojoins with or aspected by a benefic).
    """
    return _satkathadisravana_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def satkathadisravana_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
    186. Satkathadisravana yoga 
    Definition: The 3rd house should be a benefic sign aspected by benefic planets 
    and the 3rd lord should join a benefic amsa (cojoins with or aspected by a benefic).
    """
    return _satkathadisravana_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def satkathadisravana_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
    186. Satkathadisravana yoga 
    Definition: The 3rd house should be a benefic sign aspected by benefic planets 
    and the 3rd lord should join a benefic amsa (cojoins with or aspected by a benefic).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _satkathadisravana_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _utthama_graha_yoga_calculation(chart_1d=None,planet_positions=None, natural_benefics=None):
    """
        187. Uttama Griha Yoga Definition.--The lord of the 4th house should join benefics and 
        aspected by benefics in a kendra or thrikona.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # 1. Get 3rd Lord
    lagna_house = p_to_h[const._ascendant_symbol]
    fourth_house = (lagna_house + const.HOUSE_4) % 12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
    house_of_fourth_lord = p_to_h[lord_of_4th]
    kendra_trikona_houses = quadrants_of_the_house(lagna_house) + trines_of_the_house(lagna_house)
    fourth_lord_in_kendra_trikona = house_of_fourth_lord in kendra_trikona_houses
    # Lord of 4th joins benefics in kendra or trikona
    fourth_lord_joins_benefic = any([p_to_h[nb]==house_of_fourth_lord for nb in _natural_benefics])
    aspecting_planets = house.planets_aspecting_the_planet(chart_1d, lord_of_4th)
    fourth_lord_aspected_by_benefic = any(p in _natural_benefics for p in aspecting_planets)
    return fourth_lord_in_kendra_trikona and fourth_lord_joins_benefic and fourth_lord_aspected_by_benefic
def utthama_graha_yoga(chart_1d=None,natural_benefics=None):
    """
        187. Uttama Griha Yoga Definition.--The lord of the 4th house should join benefics and 
        aspected by benefics in a kendra or thrikona.
    """
    return _utthama_graha_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def utthama_graha_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
        187. Uttama Griha Yoga Definition.--The lord of the 4th house should join benefics and 
        aspected by benefics in a kendra or thrikona.
    """
    return _utthama_graha_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def utthama_graha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        187. Uttama Griha Yoga Definition.--The lord of the 4th house should join benefics and 
        aspected by benefics in a kendra or thrikona.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _satkathadisravana_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _vichitra_saudha_prakara_yoga_calculation(chart_1d=None,planet_positions=None, natural_benefics=None):
    """
        188. Vichitra Saudha Prakara Yoga 
        Definition.-If the lords of the 4th and 10th are conjoined together with Saturn and Mars
        the above yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # 1. Get 3rd Lord
    lagna_house = p_to_h[const._ascendant_symbol]
    fourth_house = (lagna_house + const.HOUSE_4) % 12
    tenth_house = (lagna_house + const.HOUSE_10) % 12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
        lord_of_10th = house.house_owner_from_planet_positions(planet_positions, tenth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
        lord_of_10th = house.house_owner(chart_1d, tenth_house)
    house_of_4th_lord = p_to_h[lord_of_4th]; saturn_house = p_to_h[const.SATURN_ID]
    house_of_10th_lord = p_to_h[lord_of_10th]; mars_house = p_to_h[const.MARS_ID]
    return house_of_4th_lord == house_of_10th_lord == saturn_house == mars_house
def vichitra_saudha_prakara_yoga(chart_1d=None,natural_benefics=None):
    """
        188. Vichitra Saudha Prakara Yoga 
        Definition.-If the lords of the 4th and l0th are conjoined together with Saturn and Mars
        the above yoga is given rise to.
    """
    return _vichitra_saudha_prakara_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def vichitra_saudha_prakara_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
        188. Vichitra Saudha Prakara Yoga 
        Definition.-If the lords of the 4th and l0th are conjoined together with Saturn and Mars
        the above yoga is given rise to.
    """
    return _vichitra_saudha_prakara_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def vichitra_saudha_prakara_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
        188. Vichitra Saudha Prakara Yoga 
        Definition.-If the lords of the 4th and l0th are conjoined together with Saturn and Mars
        the above yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _vichitra_saudha_prakara_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _ayatna_griha_prapta_yoga_from_jd_place(jd,place,divisional_chart_factor=1):
    """
        189 and 190. Ayatna Griha Prapta Yogas 
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _ayatna_griha_prapta_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def ayatna_griha_prapta_yoga(chart_1d=None,natural_benefics=None):
    """
        189 and 190. Ayatna Griha Prapta Yogas 
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    return _ayatna_griha_prapta_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def ayatna_griha_prapta_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
        189 and 190. Ayatna Griha Prapta Yogas 
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    return _ayatna_griha_prapta_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def _ayatna_griha_prapta_yoga_calculation(chart_1d=None,planet_positions=None, natural_benefics=None):
    """
        189 and 190. Ayatna Griha Prapta Yogas 
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    if _ayatna_griha_prapta_yoga_189_calculation(chart_1d=chart_1d,planet_positions=planet_positions,
                                                 natural_benefics=natural_benefics): return True
    return _ayatna_griha_prapta_yoga_190_calculation(chart_1d=chart_1d,planet_positions=planet_positions,
                                                 natural_benefics=natural_benefics)
def ayatna_griha_prapta_yoga_189_from_jd_place(jd, place, divisional_chart_factor=1):
    """
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _ayatna_griha_prapta_yoga_189_calculation(planet_positions=pp, natural_benefics=nb)
def _ayatna_griha_prapta_yoga_189_calculation(chart_1d=None,planet_positions=None, natural_benefics=None):
    """
            189. Lords of Lagna and the 7th should occupy Lagna or the 4th, aspected by benefics. 
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # 1. Get 3rd Lord
    lagna_house = p_to_h[const._ascendant_symbol]
    fourth_house = (lagna_house + const.HOUSE_4)%12
    seventh_house = (lagna_house + const.HOUSE_7) % 12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, seventh_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
        lord_of_7th = house.house_owner(chart_1d, seventh_house)
    lagna_7th_lords_in_lagna = (p_to_h[lord_of_lagna] == lagna_house == p_to_h[lord_of_7th])
    lagna_7th_lords_in_4th = (p_to_h[lord_of_lagna] == fourth_house == p_to_h[lord_of_7th])
    planets_aspecting_lagna_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_lagna) 
    planets_aspecting_7th_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_7th) 
    lagna_lord_aspected_by_benefic = any(p in _natural_benefics for p in planets_aspecting_lagna_lord)
    seventh_lord_aspected_by_benefic = any(p in _natural_benefics for p in planets_aspecting_7th_lord)
    variation_1 =  (lagna_7th_lords_in_lagna or lagna_7th_lords_in_4th) and \
           (lagna_lord_aspected_by_benefic or seventh_lord_aspected_by_benefic)
    return variation_1
def ayatna_griha_prapta_yoga_190_from_jd_place(jd, place, divisional_chart_factor=1):
    """
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _ayatna_griha_prapta_yoga_190_calculation(planet_positions=pp, natural_benefics=nb)
def _ayatna_griha_prapta_yoga_190_calculation(chart_1d=None,planet_positions=None, natural_benefics=None):
    """
            190. The lord of the 9th should be posited in a kendra and the lord of the 4th must be 
            in exaltation, moola-thrikona or own house.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # 1. Get 3rd Lord
    lagna_house = p_to_h[const._ascendant_symbol]
    fourth_house = (lagna_house + const.HOUSE_4)%12
    nineth_house = (lagna_house + const.HOUSE_9) % 12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
        lord_of_9th = house.house_owner_from_planet_positions(planet_positions, nineth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
        lord_of_9th = house.house_owner(chart_1d, nineth_house)
    ### Variation 2
    # 3. Check Condition 1: 9th Lord in Kendra
    kendra_houses = quadrants_of_the_house(lagna_house)
    ninth_lord_in_kendra = p_to_h[lord_of_9th] in kendra_houses
    # 4. Check Condition 2: 4th Lord Strength
    current_house_of_4th_lord = p_to_h[lord_of_4th]
    # A) Check matrix for Own Sign (5) or Exalted (4)
    #strength_score = const.house_strengths_of_planets[lord_of_4th][current_house_of_4th_lord]
    #is_strong_by_matrix = strength_score in [const._OWNER_RULER, const._EXALTED_UCCHAM]
    lord_is_strong = utils.is_planet_strong(lord_of_4th, current_house_of_4th_lord, include_neutral_samam=False)
    # B) Check Moola Trikona list
    is_moola_trikona = current_house_of_4th_lord == const.moola_trikona_of_planets[lord_of_4th]
    return ninth_lord_in_kendra and (lord_is_strong or is_moola_trikona)
def _grihanasa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _grihanasa_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_nav,
                                       natural_malefics=nm)
def grihanasa_yoga(chart_rasi=None, chart_navamsa=None, natural_malefics=None):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    return _grihanasa_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                       natural_malefics=natural_malefics)
def grihanasa_yoga_planet_positions(planet_positions_rasi=None,planet_positions_navamsa=None,natural_malefics=None):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _grihanasa_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                       planet_positions_navamsa=planet_positions_navamsa,
                                       natural_malefics=natural_malefics)
def _grihanasa_yoga_calculation(chart_rasi=None, planet_positions_rasi=None, 
                                chart_navamsa=None, planet_positions_navamsa=None, natural_malefics=None):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    if _grihanasa_yoga_191_calculation(chart_rasi=chart_rasi, planet_positions_rasi=planet_positions_rasi, 
                                natural_malefics=natural_malefics): return True
    return _grihanasa_yoga_192_calculation(chart_rasi=chart_rasi, planet_positions_rasi=planet_positions_rasi, 
                                chart_navamsa=chart_navamsa, planet_positions_navamsa=planet_positions_navamsa,
                                natural_malefics=natural_malefics)
def grihanasa_yoga_191_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _grihanasa_yoga_191_calculation(planet_positions_rasi=pp, natural_malefics=nb)
def _grihanasa_yoga_191_calculation(chart_rasi=None, planet_positions_rasi=None, natural_malefics=None):
    """
    191 - The lord of the 4th should be in the 12th aspected by a malefic.
    """
    # 1. Standardize Rasi and Navamsa charts
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics

    lagna_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    house_12_rasi = (lagna_house_rasi + const.HOUSE_12) % 12
    house_4_rasi = (lagna_house_rasi + const.HOUSE_4) % 12
    
    if planet_positions_rasi is not None:
        lord_of_4th_rasi = int(house.house_owner_from_planet_positions(planet_positions_rasi, house_4_rasi))
    else:
        lord_of_4th_rasi = int(house.house_owner(chart_rasi, house_4_rasi))
    # --- Yoga 191 Calculation ---
    is_4th_lord_in_12th_rasi = p_to_h_rasi[lord_of_4th_rasi] == house_12_rasi
    aspects_on_4th_lord = house.planets_aspecting_the_planet(chart_rasi, lord_of_4th_rasi)
    is_aspected_by_malefic = any(p in _natural_malefics for p in aspects_on_4th_lord)
    return is_4th_lord_in_12th_rasi and is_aspected_by_malefic
def grihanasa_yoga_192_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _grihanasa_yoga_192_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav,
                                           natural_malefics=nb)
def _grihanasa_yoga_192_calculation(chart_rasi=None, planet_positions_rasi=None, 
                                chart_navamsa=None, planet_positions_navamsa=None, natural_malefics=None):
    """
    192 - The lord of the navamsa occupied by the lord of the 4th should be disposed in the 12th.
    """
    # 1. Standardize Rasi and Navamsa charts
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics

    lagna_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    house_12_rasi = (lagna_house_rasi + const.HOUSE_12) % 12
    house_4_rasi = (lagna_house_rasi + const.HOUSE_4) % 12
    
    if planet_positions_rasi is not None:
        lord_of_4th_rasi = int(house.house_owner_from_planet_positions(planet_positions_rasi, house_4_rasi))
    else:
        lord_of_4th_rasi = int(house.house_owner(chart_rasi, house_4_rasi))
# --- Yoga 192 Calculation ---
    yoga_192 = False
    nav_sign_idx  = p_to_h_navamsa[lord_of_4th_rasi]
    if planet_positions_navamsa is not None:
        nav_dispositor = int(house.house_owner_from_planet_positions(planet_positions_navamsa, nav_sign_idx))
    else:
        nav_dispositor = int(house.house_owner(chart_navamsa, nav_sign_idx))
    yoga_192 = p_to_h_rasi[nav_dispositor] == house_12_rasi
    return yoga_192
def bandhu_pujya_yoga(chart_1d=None, natural_benefics=None):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    return _bandhu_pujya_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def bandhu_pujya_yoga_from_planet_positions(planet_positions=None, natural_benefics=None):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    return _bandhu_pujya_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def _bandhu_pujya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _bandhu_pujya_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _bandhu_pujya_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    if _bandhu_pujya_yoga_193_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                      natural_benefics=natural_benefics): return True
    return _bandhu_pujya_yoga_194_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                      natural_benefics=natural_benefics)
def bandhu_pujya_yoga_193_from_jd_place(jd, place,divisional_chart_factor=1):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_= charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _bandhu_pujya_yoga_193_calculation(planet_positions=pp, natural_benefics=nb)
def _bandhu_pujya_yoga_193_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        193 - If the benefic lord of rhe 4th is aspected by another benefic and Mercury is situated 
            in Lagna, the above yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False   
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house_idx = (asc_house + 3) % 12  # 4th house (0-indexed)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    lord_of_4th = ( house.house_owner_from_planet_positions(planet_positions,fourth_house_idx) if planet_positions
                    else house.house_owner(chart_1d, fourth_house_idx) )
    # --- Rule 193 Logic ---
    # A) Benefic lord of 4th
    lord_4_is_benefic = lord_of_4th in _natural_benefics
    # B) Aspected by ANOTHER benefic
    aspects_to_lord_4 = house.planets_aspecting_the_planet(chart_1d, lord_of_4th)
    aspected_by_other_benefic = any(bp in aspects_to_lord_4 for bp in _natural_benefics if bp != lord_of_4th)
    # C) Mercury in Lagna
    mercury_in_lagna = p_to_h.get(const.MERCURY_ID) == asc_house
    return lord_4_is_benefic and aspected_by_other_benefic and mercury_in_lagna
def bandhu_pujya_yoga_194_from_jd_place(jd, place,divisional_chart_factor=1):
    """
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_= charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _bandhu_pujya_yoga_194_calculation(planet_positions=pp, natural_benefics=nb)
def _bandhu_pujya_yoga_194_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        194 = The 4th house or the 4th lord should have the association or aspect of Jupiter.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)   
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house_idx = (asc_house + const.HOUSE_4) % 12  # 4th house (0-indexed)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    lord_of_4th = ( house.house_owner_from_planet_positions(planet_positions,fourth_house_idx) if planet_positions
                    else house.house_owner(chart_1d, fourth_house_idx) )
    # --- Rule 194 Logic ---
    fourth_house_rasi = (asc_house + const.HOUSE_4) % 12  # Assuming 0-indexed Rasis
    # 1. Check if Jupiter is IN the 4th house
    jup_in_4th = p_to_h.get(const.JUPITER_ID) == fourth_house_rasi
    # 2. Check if Jupiter ASPECTS the 4th house (Rasi)
    aspects_to_4th_rasi = house.planets_aspecting_the_raasi(chart_1d, fourth_house_rasi)
    jup_aspects_4th_house = const.JUPITER_ID in aspects_to_4th_rasi
    # 3. Check if Jupiter ASPECTS or CONJOINS the 4th Lord
    jup_conjoins_4th_lord = p_to_h.get(const.JUPITER_ID) == p_to_h.get(lord_of_4th)
    aspects_to_4th_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_4th)
    jup_aspects_4th_lord = const.JUPITER_ID in aspects_to_4th_lord
    return jup_in_4th or jup_aspects_4th_house or jup_conjoins_4th_lord or jup_aspects_4th_lord
def bandhubhisthyaktha_yoga(chart_1d, natural_malefics=None):
    """
    195. The 4th lord must be associated with malefics or occupy evil shashtiamsas or join 
    inimical or debilitation signs.
    """
    return _bandhubhisthyaktha_yoga_calculation(chart_1d, natural_malefics=natural_malefics)
def bandhubhisthyaktha_yoga_from_planet_positions(planet_positions=None, natural_malefics=None):
    """
    195. The 4th lord must be associated with malefics or occupy evil shashtiamsas or join 
    inimical or debilitation signs.
    """
    return _bandhubhisthyaktha_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def bandhubhisthyaktha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    195. The 4th lord must be associated with malefics or occupy evil shashtiamsas or join 
    inimical or debilitation signs.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _bandhubhisthyaktha_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _bandhubhisthyaktha_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
    195. The 4th lord must be associated with malefics or occupy evil shashtiamsas or join 
    inimical or debilitation signs.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_of_4th = (house_of_lagna+const.HOUSE_4)%12
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, house_of_4th)
        associations_of_lord_of_4th = house.associations_of_the_planet(planet_positions=planet_positions, planet=lord_of_4th)
        evil_deity = utils.get_amsa_ruler_from_planet_longitude(planet_positions[lord_of_4th][1][1], p_to_h[lord_of_4th])
        lord_of_4th_occupy_evil_shashtiamsa = evil_deity in const.shashti_amsa_rulers_kroora
    else:
        lord_of_4th = house.house_owner(chart_1d, house_of_4th)
        associations_of_lord_of_4th = house.associations_of_the_planet(house_to_planet_list=chart_1d, planet=lord_of_4th)
        lord_of_4th_occupy_evil_shashtiamsa = False
    lord_of_4th_associated_with_malefics = any(p in _natural_malefics for p in associations_of_lord_of_4th)
    lord_of_4th_debilitated_inimical = const.house_strengths_of_planets[lord_of_4th][p_to_h[lord_of_4th]]<=const._ENEMY
    return lord_of_4th_occupy_evil_shashtiamsa or lord_of_4th_associated_with_malefics or lord_of_4th_debilitated_inimical
def matrudeerghayur_yoga(chart_rasi, chart_navamsa=None,natural_benefics=None):
    """
        196 -  benefic must occupy the 4th, the 4th lord must be exalted, and the Moon must be strong.
        197 - The lord of the navamsaoccupiedby the 4th lord should be strong and occupy a kendra from Lagna
        as well as Chandra Lagna.
    """
    if _matrudeerghayur_yoga_196_calculation(chart_1d=chart_rasi,natural_benefics=natural_benefics): return True
    return _matrudeerghayur_yoga_197_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa)
def matrudeerghayur_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa=None,natural_benefics=None):
    """
        196 -  benefic must occupy the 4th, the 4th lord must be exalted, and the Moon must be strong.
        197 - The lord of the navamsaoccupiedby the 4th lord should be strong and occupy a kendra from Lagna
        as well as Chandra Lagna.
    """
    if _matrudeerghayur_yoga_196_calculation(planet_positions=planet_positions,natural_benefics=natural_benefics): return True
    return _matrudeerghayur_yoga_197_calculation(planet_positions_rasi=planet_positions_rasi, 
                                                 planet_positions_navamsa=planet_positions_navamsa)
def _matrudeerghayur_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, 
                                      planet_positions_navamsa=None,natural_benefics=None):
    """
        196 -  benefic must occupy the 4th, the 4th lord must be exalted, and the Moon must be strong.
        197 - The lord of the navamsaoccupiedby the 4th lord should be strong and occupy a kendra from Lagna
        as well as Chandra Lagna.
    """
    if _matrudeerghayur_yoga_196_calculation(chart_1d=chart_rasi, planet_positions=planet_positions,
                                             natural_benefics=natural_benefics): return True
    return _matrudeerghayur_yoga_197_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa, 
                        planet_positions_rasi=planet_positions_rasi, planet_positions_navamsa=planet_positions_navamsa)
def matrudeerghayur_yoga_196_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        196 -  benefic must occupy the 4th, the 4th lord must be exalted, and the Moon must be strong.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _matrudeerghayur_yoga_196_calculation(planet_positions=pp,natural_benefics=nb)
def _matrudeerghayur_yoga_196_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        196 -  benefic must occupy the 4th, the 4th lord must be exalted, and the Moon must be strong.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h['L']
    house_4_rasi = (lagna_house + const.HOUSE_4) % 12
    if planet_positions is not None:
        lord_4 = int(house.house_owner_from_planet_positions(planet_positions, house_4_rasi))
    else:
        lord_4 = int(house.house_owner(chart_1d, house_4_rasi))
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # Criteria A: Benefic in the 4th house
    planets_in_4th = planets_in_raasi(house_4_rasi,p_to_h,exclude_lagna=True)
    has_benefic_in_4th = any(p != const._ascendant_symbol and p in _natural_benefics for p in planets_in_4th)
    # Criteria B: 4th Lord must be Exalted (4) [cite: 6, 7]
    lord_4_rasi = p_to_h[lord_4]
    is_lord_4_exalted = const.house_strengths_of_planets[lord_4][lord_4_rasi] >= const._EXALTED_UCCHAM
    # Criteria C: Moon must be strong (Exalted or Ruler) [cite: 7]
    is_moon_strong = const.house_strengths_of_planets[const.MOON_ID][p_to_h[const.MOON_ID]] >= const._EXALTED_UCCHAM
    return has_benefic_in_4th and is_lord_4_exalted and is_moon_strong
def matrudeerghayur_yoga_197_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        197 - The lord of the navamsaoccupiedby the 4th lord should be strong and occupy a kendra from Lagna
        as well as Chandra Lagna.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _matrudeerghayur_yoga_197_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav)
def _matrudeerghayur_yoga_197_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None):
    """
        197 - The lord of the navamsaoccupiedby the 4th lord should be strong and occupy a kendra from Lagna
        as well as Chandra Lagna.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_rasi is None: return False
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    # 1. Find 4th lord of Rasi
    lagna_rasi = p_to_h_rasi['L']
    house_4_rasi_idx = (lagna_rasi + const.HOUSE_4) % 12
    if planet_positions_rasi is not None:
        lord_4_rasi = int(house.house_owner_from_planet_positions(planet_positions_rasi, house_4_rasi_idx))
    else:
        lord_4_rasi = int(house.house_owner(chart_rasi, house_4_rasi_idx))
    # 2. Find the Navamsa Rasi occupied by that 4th lord
    navamsa_rasi_of_4th_lord = p_to_h_nav[lord_4_rasi]
    # 3. Find the Lord of that Navamsa Rasi (Navamsa Lord)
    if planet_positions_navamsa is not None:
        nav_lord = int(house.house_owner_from_planet_positions(planet_positions_navamsa, navamsa_rasi_of_4th_lord))
    else:
        nav_lord = int(house.house_owner(chart_navamsa, navamsa_rasi_of_4th_lord))
    # [cite_start]4. Criteria: Navamsa Lord must be strong (in Rasi chart) [cite: 7]
    nav_lord_rasi_pos = p_to_h_rasi[nav_lord]
    is_nav_lord_strong = const.house_strengths_of_planets[nav_lord][nav_lord_rasi_pos] >= const._OWNER_RULER
    # 5. Criteria: Occupy Kendra from Lagna and Chandra Lagna (in Rasi)
    kendra_from_lagna = quadrants_of_the_house(lagna_rasi)
    chandra_lagna = p_to_h_rasi[const.MOON_ID]
    kendra_from_chandra = quadrants_of_the_house(chandra_lagna)
    nav_lord_house = p_to_h_rasi[nav_lord]
    in_kendra = (nav_lord_house in kendra_from_lagna) and (nav_lord_house in kendra_from_chandra)
    return is_nav_lord_strong and in_kendra
def _matrunasa_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None,
                                planet_positions_navamsa=None, natural_malefics=None):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    if _matrunasa_yoga_198_calculation(chart_rasi=chart_rasi, natural_malefics=natural_malefics): return True
    return _matrunasa_yoga_199_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                           natural_malefics=natural_malefics)    
def matrunasa_yoga_198_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _matrunasa_yoga_198_calculation(planet_positions_rasi=pp, natural_malefics=nm)
def _matrunasa_yoga_198_calculation(chart_rasi=None, planet_positions_rasi=None, natural_malefics=None):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
    if chart_rasi is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    moon_house = p_to_h_rasi[const.MOON_ID]
    # --- Yoga 198 Logic ---
    # Per BVR: Moon hemmed, associated with, or aspected by evil planets
    # 1. Associated with malefic (Conjunction)
    #planets_in_moon_house = [p for p, h in p_to_h_rasi.items() if h == moon_house]
    planets_in_moon_house = planets_in_raasi(moon_house,p_to_h_rasi,exclude_lagna=True)
    associated_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_moon_house)
    # 2. Aspected by malefic
    aspected_by_malefic = any(p in _natural_malefics for p in house.aspected_planets_of_the_raasi(chart_rasi, moon_house))
    # 3. Hemmed in (Papa Kartari)
    prev_house = (moon_house - 1) % 12
    next_house = (moon_house + 1) % 12
    prev_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(prev_house,p_to_h_rasi,exclude_lagna=True))
    next_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(next_house,p_to_h_rasi,exclude_lagna=True))
    hemmed = prev_house_malefic and next_house_malefic
    return hemmed or associated_malefic or aspected_by_malefic
def matrunasa_yoga_199_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _matrunasa_yoga_199_calculation(planet_positions_rasi=pp, natural_malefics=nm)
def _matrunasa_yoga_199_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None, planet_positions_navamsa=None, natural_malefics=None):
    """
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    lagna_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    # --- Yoga 199 Logic ---
    # Navamsa chain: 4th lord's Navamsa lord -> its Navamsa lord -> Rasi position in 6/8/12
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    # Step A: Find 4th lord in Rasi
    h4_rasi_idx = (lagna_house_rasi + const.HOUSE_4) % 12
    if planet_positions_rasi is not None:
        lord_4 = int(house.house_owner_from_planet_positions(planet_positions_rasi, h4_rasi_idx))
    else:
        lord_4 = int(house.house_owner(chart_rasi, h4_rasi_idx))
    # Step B: Lord of the Navamsa occupied by the 4th lord
    nav_house_of_lord4 = p_to_h_navamsa[lord_4]
    if planet_positions_navamsa is not None:
        lord_of_nav_house = int(house.house_owner_from_planet_positions(planet_positions_navamsa, nav_house_of_lord4))
    else:
        lord_of_nav_house = int(house.house_owner(chart_navamsa, nav_house_of_lord4))
    # Step C: The planet owning the Navamsa in which 'lord_of_nav_house' is situated
    nav_house_of_step_b = p_to_h_navamsa[lord_of_nav_house]
    if planet_positions_navamsa is not None:
        final_planet = int(house.house_owner_from_planet_positions(planet_positions_navamsa, nav_house_of_step_b))
    else:
        final_planet = int(house.house_owner(chart_navamsa, nav_house_of_step_b))
    # Step D: Final planet must be in 6th, 8th, or 12th house in Rasi chart
    final_planet_house_rasi = p_to_h_rasi[final_planet]
    # Using your formulas for house calculation
    house_6_rasi = (lagna_house_rasi + const.HOUSE_6) % 12
    house_8_rasi = (lagna_house_rasi + const.HOUSE_8) % 12
    house_12_rasi = (lagna_house_rasi + const.HOUSE_12) % 12
    return final_planet_house_rasi in [house_6_rasi, house_8_rasi, house_12_rasi]
def matrunasa_yoga(chart_rasi, chart_navamsa=None,natural_malefics=None):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    if _matrunasa_yoga_198_calculation(chart_rasi=chart_rasi, natural_malefics=natural_malefics): return True
    return _matrunasa_yoga_199_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                           natural_malefics=natural_malefics)    
def matrunasa_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa=None,natural_malefics=None):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if _matrunasa_yoga_198_calculation(planet_positions_rasi=planet_positions_rasi, 
                planet_positions_navamsa=planet_positions_navamsa, natural_malefics=natural_malefics): return True
    return _matrunasa_yoga_199_calculation(planet_positions_rasi, planet_positions_navamsa, natural_malefics)
def matrunasa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        198 - The Moon should be hemmed in between, associated with or aspected by evil planets.
        199 - The planet owning the navamsa, in which the lord of the navamsa occupied by the 4th lord is 
            situated should be disposed in the 6th, 8th or 12th house.
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=1)
    return _matrunasa_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_nav, 
                                     natural_malefics=nm)
def kapata_yoga(chart_1d, maandi_house=None, natural_malefics=None):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    return _kapata_yoga_calculation(chart_1d=chart_1d, maandi_house=maandi_house, natural_malefics=natural_malefics)
def kapata_yoga_from_planet_positions(planet_positions, maandi_house=None, natural_malefics=None):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    return _kapata_yoga_calculation(planet_positions=planet_positions, maandi_house=maandi_house,
                                    natural_malefics=natural_malefics)
def _kapata_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    mandi_h, _ = drik.dasavarga_from_long(g_lon_info)
    return _kapata_yoga_calculation(planet_positions=pp, maandi_house=mandi_h, natural_malefics=nm)
def kapata_yoga_202_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _kapata_yoga_202_calculation(planet_positions=pp, natural_malefics=nm)
def _kapata_yoga_202_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d,fourth_house)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    malefic_joins_4th_house = any(p_to_h[m] == fourth_house for m in _natural_malefics)
    house_of_lord_of_4th = p_to_h[lord_of_4th]
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_4th)
    lord_of_4th_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    lord_of_4th_joined_by_malefic = any(p_to_h[m] == house_of_lord_of_4th for m in _natural_malefics)
    prev_house = (house_of_lord_of_4th - 1) % 12
    next_house = (house_of_lord_of_4th + 1) % 12
    prev_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(prev_house,p_to_h,exclude_lagna=True))
    next_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(next_house,p_to_h,exclude_lagna=True))
    is_4th_lord_hemmed_between_malefics = prev_house_malefic and next_house_malefic
    return malefic_joins_4th_house and (lord_of_4th_aspected_by_malefic or lord_of_4th_joined_by_malefic or 
                                        is_4th_lord_hemmed_between_malefics)
def kapata_yoga_203_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _kapata_yoga_203_calculation(planet_positions=pp, natural_malefics=nm)
def _kapata_yoga_203_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    ## Yoga 203 Check
    # 4th house occupied by Saturn, Mars, Rahu
    fourth_occupied_by_saturn_mars_rahu = (p_to_h[const.SATURN_ID]==p_to_h[const.MARS_ID]==p_to_h[const.RAHU_ID]==fourth_house)
    # 10th lord aspected by malefics
    tenth_house = (asc_house+const.HOUSE_10)%12
    if planet_positions is not None:
        lord_of_10th = house.house_owner_from_planet_positions(planet_positions, tenth_house)
    else:
        lord_of_10th = house.house_owner(chart_1d,tenth_house)
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_10th)
    lord_of_10th_is_a_malefic = lord_of_10th in _natural_malefics
    lord_of_10th_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    return fourth_occupied_by_saturn_mars_rahu and lord_of_10th_is_a_malefic \
                    and lord_of_10th_aspected_by_malefic
def kapata_yoga_204_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    mh, _ = drik.dasavarga_from_long(g_lon_info)
    return _kapata_yoga_204_calculation(planet_positions=pp, maandi_house=mh, natural_malefics=nm)
def _kapata_yoga_204_calculation(chart_1d=None, planet_positions=None, maandi_house=None, natural_malefics=None):
    """
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d,fourth_house)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    house_of_lord_of_4th = p_to_h[lord_of_4th]
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_4th)
    lord_of_4th_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    # Yoga 204 check
    # The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    if maandi_house is None:
        lord_of_4th_joins_saturn_mandi_rahu = False
    else:
        lord_of_4th_joins_saturn_mandi_rahu = (p_to_h[const.SATURN_ID]==maandi_house==p_to_h[const.RAHU_ID]==house_of_lord_of_4th)
    return lord_of_4th_joins_saturn_mandi_rahu and lord_of_4th_aspected_by_malefic
def _kapata_yoga_calculation(chart_1d=None, planet_positions=None, maandi_house=None, natural_malefics=None):
    """
        202 - The 4th house must be joined by a malefic and the 4rh lord must be associated with or 
            aspected by malefics or be hemmed in between malefics.
        203 - The 4th must be occupied by Sani, Kuja, Rahu, and the malefic 1Oth lord, who in his turn should 
            be aspected by malefics.
        204 - The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d,fourth_house)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    malefic_joins_4th_house = any(p_to_h[m] == fourth_house for m in _natural_malefics)
    house_of_lord_of_4th = p_to_h[lord_of_4th]
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_4th)
    lord_of_4th_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    lord_of_4th_joined_by_malefic = any(p_to_h[m] == house_of_lord_of_4th for m in _natural_malefics)
    prev_house = (house_of_lord_of_4th - 1) % 12
    next_house = (house_of_lord_of_4th + 1) % 12
    prev_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(prev_house,p_to_h,exclude_lagna=True))
    next_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(next_house,p_to_h,exclude_lagna=True))
    is_4th_lord_hemmed_between_malefics = prev_house_malefic and next_house_malefic
    yoga_202 = malefic_joins_4th_house and (lord_of_4th_aspected_by_malefic or lord_of_4th_joined_by_malefic or 
                                        is_4th_lord_hemmed_between_malefics)
    ## Yoga 203 Check
    # 4th house occupied by Saturn, Mars, Rahu
    fourth_occupied_by_saturn_mars_rahu = (p_to_h[const.SATURN_ID]==p_to_h[const.MARS_ID]==p_to_h[const.RAHU_ID]==fourth_house)
    # 10th lord aspected by malefics
    tenth_house = (asc_house+const.HOUSE_10)%12
    if planet_positions is not None:
        lord_of_10th = house.house_owner_from_planet_positions(planet_positions, tenth_house)
    else:
        lord_of_10th = house.house_owner(chart_1d,tenth_house)
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_10th)
    lord_of_10th_is_a_malefic = lord_of_10th in _natural_malefics
    lord_of_10th_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    yoga_203 = fourth_occupied_by_saturn_mars_rahu and lord_of_10th_is_a_malefic \
                    and lord_of_10th_aspected_by_malefic
    # Yoga 204 check
    # The 4th lord must join Saturn, Mandi and Rahu and aspected by malefics
    if maandi_house is None:
        lord_of_4th_joins_saturn_mandi_rahu = False
    else:
        lord_of_4th_joins_saturn_mandi_rahu = (p_to_h[const.SATURN_ID]==maandi_house==p_to_h[const.RAHU_ID]==house_of_lord_of_4th)
    yoga_204 = lord_of_4th_joins_saturn_mandi_rahu and lord_of_4th_aspected_by_malefic
    return yoga_202 or yoga_203 or yoga_204
def _nishkapata_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    v_scores = charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place)
    v_scores = [v[0] for _,v in v_scores.items()]
    return _nishkapata_yoga_calculation(planet_positions=pp, natural_benefics=nb, vaiseshikamsa_scores=v_scores)
def nishkapata_yoga_from_planet_positions(planet_positions,natural_benefics=None, vaiseshikamsa_scores=None):
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
    return _nishkapata_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics,
                                        vaiseshikamsa_scores=vaiseshikamsa_scores)
def nishkapata_yoga(chart_1d,natural_benefics=None, vaiseshikamsa_scores=None):
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
    return _nishkapata_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics,
                                        vaiseshikamsa_scores=vaiseshikamsa_scores)
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
def _nishkapata_yoga_calculation(chart_1d=None, planet_positions=None, 
                                 natural_benefics=None, vaiseshikamsa_scores=None):
    if _nishkapata_yoga_205_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                        natural_benefics=natural_benefics): return True
    return _nishkapata_yoga_206_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                        natural_benefics=natural_benefics, vaiseshikamsa_scores=vaiseshikamsa_scores)
def nishkapata_yoga_205_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _nishkapata_yoga_205_calculation(planet_positions=pp, natural_benefics=nb)
def _nishkapata_yoga_205_calculation(chart_1d=None, planet_positions=None, 
                                 natural_benefics=None):
    """
        205 - The 4th house must be occupied by a benefic, or a planet in exaltation, friendly or own 
            house,or the 4th house must be a benefic sign.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    planets_in_4th_house = planets_in_raasi(fourth_house,p_to_h,exclude_lagna=True)
    # The 4th house must be occupied by a benefic
    benefic_occupies_4th_house = any(p_to_h[bp]==fourth_house for bp in _natural_benefics)
    # The 4th house must be occupied by a planet in exaltation, friendly or own house
    is_4th_house_strong = any(
        utils.is_planet_strong(p, fourth_house, include_neutral_samam=False) for p in planets_in_4th_house
            if p != const._ascendant_symbol)
    # The 4th house must be a benefic sign.
    is_4th_house_in_benefic_signs = fourth_house in const.benefic_signs
    return benefic_occupies_4th_house or is_4th_house_strong or is_4th_house_in_benefic_signs
def nishkapata_yoga_206_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    v_scores = charts.vaiseshikamsa_dhasavarga_of_planets(jd, place)
    v_scores = [v[0] for _,v in v_scores.items()]
    return _nishkapata_yoga_206_calculation(planet_positions=pp, natural_benefics=nb, vaiseshikamsa_scores=v_scores)
def _nishkapata_yoga_206_calculation(chart_1d=None, planet_positions=None, 
                                 natural_benefics=None, vaiseshikamsa_scores=None):
    """
        206 - Lord of Lagna should join the 4th in conjunction with or aspected by a benefic 
            or occupy Parvata or Uttamamsa.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    # Yoga 206 Check
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, asc_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d,asc_house)
    lagna_lord_house = p_to_h[lord_of_lagna]
    # Lagna lord in 4th house
    lagna_lord_in_4th_house = lagna_lord_house == fourth_house
    # Lagna lord cojoins a benefic
    lagna_lord_cojoins_benefic = any(p_to_h[bp]==lagna_lord_house for bp in _natural_benefics)
    # Lagna lord aspected by benefics
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_lagna)
    lagna_lord_aspected_by_benefic = any(m in aspected_by for m in _natural_benefics)
    # Lord of Lagna should occupy Parvatamsa or Uttamamsa.
    lagna_lord_in_uttamamsa = False
    lagna_lord_in_paarvatamsa = False
    if vaiseshikamsa_scores and lord_of_lagna in vaiseshikamsa_scores:
        lagna_lord_in_uttamamsa = vaiseshikamsa_scores[lord_of_lagna] == 3
        lagna_lord_in_paarvatamsa = vaiseshikamsa_scores[lord_of_lagna] == 6
    return (lagna_lord_in_4th_house and (lagna_lord_cojoins_benefic or lagna_lord_aspected_by_benefic
                    or lagna_lord_in_uttamamsa or lagna_lord_in_paarvatamsa))
def matru_satrutwa_yoga(chart_1d, natural_malefics=None):
    """
        Mercury, being lord of Lagna and the 4th, must join with or be aspected by a malefic.
    """
    return _matru_satrutwa_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def matru_satrutwa_yoga_from_planet_position(planet_positions,natural_malefics=None):
    """
        Mercury, being lord of Lagna and the 4th, must join with or be aspected by a malefic.
    """
    return _matru_satrutwa_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def matru_satrutwa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        Mercury, being lord of Lagna and the 4th, must join with or be aspected by a malefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _matru_satrutwa_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _matru_satrutwa_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        Mercury, being lord of Lagna and the 4th, must join with or be aspected by a malefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d,fourth_house)
    mercury_is_lord_of_lagna_and_4th_house = (p_to_h[const.MERCURY_ID] == asc_house == p_to_h[lord_of_4th])
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    mercury_cojoins_malefic = any(p_to_h[bp]==asc_house for bp in _natural_malefics)
    aspected_by = house.aspected_planets_of_the_planet(chart_1d, const.MERCURY_ID)
    mercury_aspected_by_malefic = any(m in aspected_by for m in _natural_malefics)
    return mercury_is_lord_of_lagna_and_4th_house and (mercury_cojoins_malefic or mercury_aspected_by_malefic)
def matru_sneha_yoga_from_planet_positions(planet_positions,natural_benefics=None):
    """
        First Variation - The Lagna (1st house) and the 4th house have the same planetary ruler
        The lst and 4th houses can have common lords only in respect of Ge/Vi (Me) or Sg/Pi (Ju) 
        Second Variation - The lords of the 1st and 4th houses are either natural or temporal friends.
        Third Variation - The Lagna lord (1st house ruler) and the 4th house lord are aspected by benefics.
    """
    return _matru_sneha_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def matru_sneha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        First Variation - The Lagna (1st house) and the 4th house have the same planetary ruler
        The lst and 4th houses can have common lords only in respect of Ge/Vi (Me) or Sg/Pi (Ju) 
        Second Variation - The lords of the 1st and 4th houses are either natural or temporal friends.
        Third Variation - The Lagna lord (1st house ruler) and the 4th house lord are aspected by benefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _matru_sneha_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def matru_sneha_yoga(chart_1d,natural_benefics=None):
    """
        First Variation - The Lagna (1st house) and the 4th house have the same planetary ruler
        The lst and 4th houses can have common lords only in respect of Ge/Vi (Me) or Sg/Pi (Ju) 
        Second Variation - The lords of the 1st and 4th houses are either natural or temporal friends.
        Third Variation - The Lagna lord (1st house ruler) and the 4th house lord are aspected by benefics.
    """
    return _matru_sneha_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def _matru_sneha_yoga_calculation(chart_1d=None,planet_positions=None,natural_benefics=None):
    """
        First Variation - The Lagna (1st house) and the 4th house have the same planetary ruler
        The lst and 4th houses can have common lords only in respect of Ge/Vi (Me) or Sg/Pi (Ju) 
        Second Variation - The lords of the 1st and 4th houses are either natural or temporal friends.
        Third Variation - The Lagna lord (1st house ruler) and the 4th house lord are aspected by benefics.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
    variation_1 = (lagna_lord == lord_of_4th)
    
    temp_friends_of_lagna_lord = [p for p,h in p_to_h.items() \
        if p not in[const._ascendant_symbol,lagna_lord] and ((h - p_to_h[lagna_lord]) % 12) in const.temporary_friend_raasi_positions]
    temp_friends_of_lord_of_4th = [p for p,h in p_to_h.items() \
        if p not in[const._ascendant_symbol,lord_of_4th] and ((h - p_to_h[lord_of_4th]) % 12) in const.temporary_friend_raasi_positions]
    natural_friends_of_lagna_lord = const.friendly_planets[lagna_lord]
    natural_friends_of_lord_of_4th = const.friendly_planets[lord_of_4th]
    variation_2_1 = (lagna_lord in temp_friends_of_lord_of_4th) and (lord_of_4th in temp_friends_of_lagna_lord)
    variation_2_2 = (lagna_lord in natural_friends_of_lord_of_4th) and (lord_of_4th in natural_friends_of_lagna_lord)
    variation_2 = variation_2_1 or variation_2_2
    
    lagna_lord_aspected_by = house.aspected_planets_of_the_planet(chart_1d, lagna_lord)
    lagna_lord_aspected_by_benefic = any(bp in lagna_lord_aspected_by for bp in _natural_benefics)
    lord_of_4th_aspected_by = house.aspected_planets_of_the_planet(chart_1d, lord_of_4th)
    lord_of_4th_aspected_by_benefic = any(bp in lord_of_4th_aspected_by for bp in _natural_benefics)
    variation_3 = lagna_lord_aspected_by_benefic and lord_of_4th_aspected_by_benefic
    return variation_1 or variation_2 or variation_3
def _vahana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vahana_yoga_calculation(planet_positions=pp)
def vahana_yoga_from_planet_positions(planet_positions):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    return _vahana_yoga_calculation(planet_positions=planet_positions)
def vahana_yoga(chart_1d):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    return _vahana_yoga_calculation(chart_1d=chart_1d)
def _vahana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    if _vahana_yoga_209_calculation(chart_1d, planet_positions): return True
    return _vahana_yoga_210_calculation(chart_1d, planet_positions)
def vahana_yoga_209_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vahana_yoga_209_calculation(planet_positions=pp)
def _vahana_yoga_209_calculation(chart_1d=None, planet_positions=None):
    """
        209 - The lord of Lagna must join the 4th, 11th or the 9th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    nineth_house = (asc_house+const.HOUSE_9)%12
    eleventh_house = (asc_house+const.HOUSE_11)%12
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, asc_house)
    else:
        lagna_lord = house.house_owner(chart_1d, asc_house)
    # Variation 1 check - Ruler of the 1st house is in the 4th, 9th or 11th house
    yoga_209 = (
                    (p_to_h[lagna_lord] == fourth_house) or 
                    (p_to_h[lagna_lord] == nineth_house) or
                    (p_to_h[lagna_lord] == eleventh_house)
                  )
    return yoga_209
def vahana_yoga_210_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _vahana_yoga_210_calculation(planet_positions=pp)
def _vahana_yoga_210_calculation(chart_1d=None, planet_positions=None):
    """
        210 - The 4th lord must be exalted and the lord of the exaltation sign must occupy a kendra or trikona
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fourth_house = (asc_house+const.HOUSE_4)%12
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
    # Variation 2 - check - 
    house_of_4th_lord = p_to_h[lord_of_4th] 
    # 2.1 Ruler of the 4th house is in its exaltation sign 
    yoga_210_1 = utils.is_planet_in_exalation(lord_of_4th, house_of_4th_lord,enforce_deep_exaltation=False)
    if not yoga_210_1: return False
    # 2.2 ruler of the exaltation sign is in a kendra (0,3,6,9) house.
    if planet_positions is not None:
        lord_of_4th_exaltation_sign = house.house_owner_from_planet_positions(planet_positions, house_of_4th_lord)
    else:
        lord_of_4th_exaltation_sign = house.house_owner(chart_1d, house_of_4th_lord)
    house_of_lord_of_4th_exaltation_sign = p_to_h[lord_of_4th_exaltation_sign]
    yoga_210_2 = house_of_lord_of_4th_exaltation_sign in quadrants_of_the_house(asc_house)
    # 2.3 ruler of the exaltation sign is in a trikona (0,4,8) house.
    yoga_210_3 = house_of_lord_of_4th_exaltation_sign in trines_of_the_house(asc_house)
    return yoga_210_1 and (yoga_210_2 or yoga_210_3)
def anapathya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        Jupiter and the lords of Lagna, the 7th and the 5th are weak
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _anapathya_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def anapathya_yoga_from_planet_positions(planet_positions=None,natural_malefics=None):
    """
        Jupiter and the lords of Lagna, the 7th and the 5th are weak
    """
    return _anapathya_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def anapathya_yoga(chart_1d=None,natural_malefics=None):
    """
        Jupiter and the lords of Lagna, the 7th and the 5th are weak
    """
    return _anapathya_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def _anapathya_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        Jupiter and the lords of Lagna, the 7th and the 5th are weak
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12
    seventh_house = (asc_house+const.HOUSE_7)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, asc_house)
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, seventh_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, asc_house)
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
        lord_of_7th = house.house_owner(chart_1d, seventh_house)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    is_jupiter_weak = utils.is_planet_weak(const.JUPITER_ID, p_to_h[const.JUPITER_ID], planet_to_house_dict=p_to_h,
                                planet_positions=planet_positions, asc_house=asc_house, 
                                natural_malefics=_natural_malefics)
    is_lord_of_lagna_weak = utils.is_planet_weak(lord_of_lagna, p_to_h[lord_of_lagna], planet_to_house_dict=p_to_h,
                                planet_positions=planet_positions, asc_house=asc_house, 
                                natural_malefics=_natural_malefics)
    is_lord_of_5th_weak = utils.is_planet_weak(lord_of_5th, p_to_h[lord_of_5th], planet_to_house_dict=p_to_h,
                                planet_positions=planet_positions, asc_house=asc_house, 
                                natural_malefics=_natural_malefics)
    is_lord_of_7th_weak = utils.is_planet_weak(lord_of_7th, p_to_h[lord_of_7th], planet_to_house_dict=p_to_h,
                                planet_positions=planet_positions, asc_house=asc_house, 
                                natural_malefics=_natural_malefics)
    return is_jupiter_weak and is_lord_of_lagna_weak and is_lord_of_5th_weak and is_lord_of_7th_weak
def _sarpasaapa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        212 - The 5th should be occupied by Rahu and aspected by Kuja or the 5th house being a sign 
            of Mars, should be occupied by Rahu
        213 - The 5th lord is in conjunction with Rahu, and  Saturn is in the 5th house aspected by 
            or asssociated with the Moon
        214 - The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, 
            and the 5th lord in a dusthana
        215 - The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated
            with Mercury
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sarpasaapa_yoga_calculation(planet_positions=pp)
def sarpasaapa_yoga_from_planet_positions(planet_positions=None):
    """
        212 - The 5th should be occupied by Rahu and aspected by Kuja or the 5th house being a sign 
            of Mars, should be occupied by Rahu
        213 - The 5th lord is in conjunction with Rahu, and  Saturn is in the 5th house aspected by 
            or asssociated with the Moon
        214 - The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, 
            and the 5th lord in a dusthana
        215 - The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated
            with Mercury
    """
    return _sarpasaapa_yoga_calculation(planet_positions=planet_positions)
def sarpasaapa_yoga(chart_1d=None):
    """
        212 - The 5th should be occupied by Rahu and aspected by Kuja or the 5th house being a sign 
            of Mars, should be occupied by Rahu
        213 - The 5th lord is in conjunction with Rahu, and  Saturn is in the 5th house aspected by 
            or asssociated with the Moon
        214 - The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, 
            and the 5th lord in a dusthana
        215 - The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated
            with Mercury
    """
    return _sarpasaapa_yoga_calculation(chart_1d=chart_1d)
def _sarpasaapa_yoga_calculation(chart_1d=None, planet_positions=None):
    if _sarpasaapa_yoga_212_calculation(chart_1d, planet_positions): return True
    if _sarpasaapa_yoga_213_calculation(chart_1d, planet_positions): return True
    if _sarpasaapa_yoga_214_calculation(chart_1d, planet_positions): return True
    return _sarpasaapa_yoga_215_calculation(chart_1d, planet_positions)
def sarpasaapa_yoga_212_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        212 - The 5th should be occupied by Rahu and aspected by Kuja or the 5th house being a sign 
            of Mars, should be occupied by Rahu
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sarpasaapa_yoga_212_calculation(planet_positions=pp)
def _sarpasaapa_yoga_212_calculation(chart_1d=None, planet_positions=None):
    """
        212 - The 5th should be occupied by Rahu and aspected by Kuja or the 5th house being a sign 
            of Mars, should be occupied by Rahu
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
    else:
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
    # Check for Yoga 212
    rahu_in_5th = p_to_h[const.RAHU_ID] == fifth_house
    aspected_by_mars = house.aspected_planets_of_the_planet(chart_1d, const.MARS_ID)
    mars_aspects_5th = const.RAHU_ID in aspected_by_mars
    if rahu_in_5th and mars_aspects_5th: return True
    # 5th house being a sign of Mars, should be occupied by Rahu
    mars_sign_5th_with_rahu = (lord_of_5th == const.MARS_ID) and (p_to_h[const.RAHU_ID]==fifth_house)
    yoga_212 = (rahu_in_5th and mars_aspects_5th) or mars_sign_5th_with_rahu
    return yoga_212
def sarpasaapa_yoga_213_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        213 - The 5th lord is in conjunction with Rahu, and  Saturn is in the 5th house aspected by 
            or asssociated with the Moon
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sarpasaapa_yoga_213_calculation(planet_positions=pp)
def _sarpasaapa_yoga_213_calculation(chart_1d=None, planet_positions=None):
    """
        213 - The 5th lord is in conjunction with Rahu, and  Saturn is in the 5th house aspected by 
            or asssociated with the Moon
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
    else:
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
    house_of_5th_lord = p_to_h[lord_of_5th]
    # The 5th lord is in conjunction with Rahu, and 
    # Saturn is in the 5th house aspected by or asssociated with the Moon
    rahu_with_5th_lord = (p_to_h[const.RAHU_ID]==house_of_5th_lord)
    saturn_in_5th = p_to_h[const.SATURN_ID]==fifth_house
    aspected_by_moon = house.aspected_houses_of_the_planet(chart_1d, const.MOON_ID)
    moon_aspects_5th = fifth_house in aspected_by_moon
    moon_in_5th = p_to_h[const.MOON_ID]==fifth_house
    yoga_213 = (rahu_with_5th_lord and saturn_in_5th and (moon_aspects_5th or moon_in_5th))
    return yoga_213
def sarpasaapa_yoga_214_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        214 - The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, 
            and the 5th lord in a dusthana
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sarpasaapa_yoga_214_calculation(planet_positions=pp)
def _sarpasaapa_yoga_214_calculation(chart_1d=None, planet_positions=None):
    """
        214 - The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, 
            and the 5th lord in a dusthana
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
    else:
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
    house_of_5th_lord = p_to_h[lord_of_5th]
    # The karaka of children (Jupiter) in association with Mars, Rahu in Lagna, and the 5th lord in a dusthana
    jupiter_joins_mars = (p_to_h[const.JUPITER_ID]==p_to_h[const.MARS_ID])
    rahu_in_lagna = (p_to_h[const.RAHU_ID]==asc_house)
    house_of_5th_lord_in_dusthana = house_of_5th_lord in house.dushthanas_of_the_raasi(asc_house)
    yoga_214 = jupiter_joins_mars and rahu_in_lagna and house_of_5th_lord_in_dusthana
    return yoga_214
def sarpasaapa_yoga_215_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        215 - The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated
            with Mercury
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sarpasaapa_yoga_215_calculation(planet_positions=pp)
def _sarpasaapa_yoga_215_calculation(chart_1d=None, planet_positions=None):
    """
        215 - The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated
            with Mercury
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    fifth_house = (asc_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
    else:
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
    # The 5th house, being a sign of Mars, must be conjoined by Rahu and aspected by or associated with Mercury
    mars_is_lord_of_5th = (lord_of_5th == const.MARS_ID) # Mars rules fifth house
    rahu_in_5th = p_to_h[const.RAHU_ID] == fifth_house
    mercury_in_5th = (p_to_h[const.MERCURY_ID]==fifth_house) ## associated with
    mercury_aspects_5th = fifth_house in house.aspected_houses_of_the_planet(chart_1d, const.MERCURY_ID)
    return mars_is_lord_of_5th and rahu_in_5th and (mercury_in_5th or mercury_aspects_5th)
def pithru_saapa_sutakshaya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR 216 - Pithru Saapa Sutakshaya Yoga
        5th House must be occupied by Sun
        A. Sun should be in sign of debilitation (Sun in Mithuna/Gemini)
           OR
        B. Sun's Navamsa should be in Makara/Capricorn or Kumbha/Aquarius
        C. Sun is hemmed either side with malefics
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _pithru_saapa_sutakshaya_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa,
                                                  natural_malefics=nm)
def pithru_saapa_sutakshaya_yoga_from_planet_positions(planet_positions_rasi=None,planet_positions_navamsa=None,
                                                    natural_malefics=None):
    """
        BVR 216 - Pithru Saapa Sutakshaya Yoga
        5th House must be occupied by Sun
        A. Sun should be in sign of debilitation (Sun in Mithuna/Gemini)
           OR
        B. Sun's Navamsa should be in Makara/Capricorn or Kumbha/Aquarius
        C. Sun is hemmed either side with malefics
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _pithru_saapa_sutakshaya_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                        planet_positions_navamsa=planet_positions_navamsa, natural_malefics=natural_malefics)
def pithru_saapa_sutakshaya_yoga(chart_rasi, chart_navamsa, natural_malefics=None):
    """
        BVR 216 - Pithru Saapa Sutakshaya Yoga
        5th House must be occupied by Sun
        A. Sun should be in sign of debilitation (Sun in Mithuna/Gemini)
           OR
        B. Sun's Navamsa should be in Makara/Capricorn or Kumbha/Aquarius
        C. Sun is hemmed either side with malefics
    """
    return _pithru_saapa_sutakshaya_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                                  natural_malefics=natural_malefics)
def _pithru_saapa_sutakshaya_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None,
                                          planet_positions_navamsa=None, natural_malefics=None):
    """
        BVR 216 - Pithru Saapa Sutakshaya Yoga
        5th House must be occupied by Sun
        A. Sun should be in sign of debilitation (Sun in Mithuna/Gemini)
           OR
        B. Sun's Navamsa should be in Makara/Capricorn or Kumbha/Aquarius
        C. Sun is hemmed either side with malefics
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    sun_house_rasi = p_to_h_rasi[const.SUN_ID]
    sun_house_navamsa = p_to_h_navamsa[const.SUN_ID]
    fifth_house_rasi = (lagna_house_rasi+const.HOUSE_5)%12
    # 5th House must be occupied by Sun
    sun_in_fifth_house = (sun_house_rasi == fifth_house_rasi)
    if not sun_in_fifth_house: return False
    # A. Sun should be in sign of debilitation (Sun in Mithuna/Gemini)
    sun_in_debilitation_sign = const.house_strengths_of_planets[const.SUN_ID][sun_house_rasi] == const._DEBILITATED_NEECHAM
    if sun_in_debilitation_sign: return True
    # B. Sun's Navamsa should be in Makara/Capricorn or Kumbha/Aquarius
    navamsa_sun_in_capricorn_or_aquarius = (sun_house_navamsa==const.CAPRICORN) or (sun_house_navamsa==const.AQUARIUS)
    if navamsa_sun_in_capricorn_or_aquarius: True 
    # C. Sun is hemmed either side with malefics
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    prev_house = (sun_house_rasi - 1) % 12
    next_house = (sun_house_rasi + 1) % 12
    prev_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(prev_house,p_to_h_rasi,exclude_lagna=True))
    next_house_malefic = any(p != const._ascendant_symbol and p in _natural_malefics for p in planets_in_raasi(next_house,p_to_h_rasi,exclude_lagna=True))
    sun_hemmed_between_malefics = prev_house_malefic and next_house_malefic
    return sun_in_fifth_house and (sun_in_debilitation_sign or navamsa_sun_in_capricorn_or_aquarius or sun_hemmed_between_malefics)
def maathru_saapa_sutakshaya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR 217 - Maathru Saapa Sutakshya Yoga
        A. The 8th lord is in the 5th lord's house AND the 5th lord is in the 8th lord's house AND 
        B the Moon and the 4th lord join the 6th house
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _maathru_saapa_sutakshaya_yoga_calculation(planet_positions=pp)
def maathru_saapa_sutakshaya_yoga_from_planet_positions(planet_positions):
    """
        BVR 217 - Maathru Saapa Sutakshya Yoga
        A. The 8th lord is in the 5th lord's house AND the 5th lord is in the 8th lord's house AND 
        B the Moon and the 4th lord join the 6th house
    """
    return _maathru_saapa_sutakshaya_yoga_calculation(planet_positions=planet_positions)
def maathru_saapa_sutakshaya_yoga(chart_1d):
    """
        BVR 217 - Maathru Saapa Sutakshya Yoga
        A. The 8th lord is in the 5th lord's house AND the 5th lord is in the 8th lord's house AND 
        B the Moon and the 4th lord join the 6th house
    """
    return _maathru_saapa_sutakshaya_yoga_calculation(chart_1d=chart_1d)
def _maathru_saapa_sutakshaya_yoga_calculation(chart_1d=None,planet_positions=None):
    """
        BVR 217 - Maathru Saapa Sutakshya Yoga
        A. The 8th lord is in the 5th lord's house AND the 5th lord is in the 8th lord's house AND 
        B the Moon and the 4th lord join the 6th house
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    fourth_house = (lagna_house+const.HOUSE_4)%12
    fifth_house = (lagna_house+const.HOUSE_5)%12
    sixth_house = (lagna_house+const.HOUSE_6)%12
    eighth_house = (lagna_house+const.HOUSE_8)%12
    moon_house = p_to_h[const.MOON_ID]
    if planet_positions is not None:
        lord_of_4th = house.house_owner_from_planet_positions(planet_positions, fourth_house)
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, sixth_house)
        lord_of_8th = house.house_owner_from_planet_positions(planet_positions, eighth_house)
    else:
        lord_of_4th = house.house_owner(chart_1d, fourth_house)
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
        lord_of_6th = house.house_owner(chart_1d, sixth_house)
        lord_of_8th = house.house_owner(chart_1d, eighth_house)

        # A. The 8th lord is in the 5th lord's house AND the 5th lord is in the 8th lord's house AND
        lord_of_8th_lord_of_5th_swap_houses = (p_to_h[lord_of_8th]==fifth_house and p_to_h[lord_of_5th]==eighth_house)  
        # B the Moon and the 4th lord join the 6th house
        moon_and_4th_lord_in_6th_house = (moon_house==sixth_house and p_to_h[lord_of_4th]==sixth_house)
        return lord_of_8th_lord_of_5th_swap_houses and moon_and_4th_lord_in_6th_house
def bhraathru_saapa_sutakshaya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR 218 - Bhraathru Saapa Sutakshya Yoga
        A. The lords of Lagna and the 5th must join the 8th house AND 
        B. the lord of the 3rd should combine with Mars and Rahu in the 5th house.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bhraathru_saapa_sutakshaya_yoga_calculation(planet_positions=pp)
def bhraathru_saapa_sutakshaya_yoga_from_planet_positions(planet_positions):
    """
        BVR 218 - Bhraathru Saapa Sutakshya Yoga
        A. The lords of Lagna and the 5th must join the 8th house AND 
        B. the lord of the 3rd should combine with Mars and Rahu in the 5th house.
    """
    return _bhraathru_saapa_sutakshaya_yoga_calculation(planet_positions=planet_positions)
def bhraathru_saapa_sutakshaya_yoga(chart_1d):
    """
        BVR 218 - Bhraathru Saapa Sutakshya Yoga
        A. The lords of Lagna and the 5th must join the 8th house AND 
        B. the lord of the 3rd should combine with Mars and Rahu in the 5th house.
    """
    return _bhraathru_saapa_sutakshaya_yoga_calculation(chart_1d=chart_1d)
def _bhraathru_saapa_sutakshaya_yoga_calculation(chart_1d=None,planet_positions=None):
    """
        BVR 218 - Bhraathru Saapa Sutakshya Yoga
        A. The lords of Lagna and the 5th must join the 8th house AND 
        B. the lord of the 3rd should combine with Mars and Rahu in the 5th house.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    third_house = (lagna_house+const.HOUSE_3)%12
    fifth_house = (lagna_house+const.HOUSE_5)%12
    eighth_house = (lagna_house+const.HOUSE_8)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
        lord_of_3rd = house.house_owner_from_planet_positions(planet_positions, third_house)
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, fifth_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
        lord_of_3rd = house.house_owner(chart_1d, third_house)
        lord_of_5th = house.house_owner(chart_1d, fifth_house)
    # A. The lords of Lagna and the 5th must join the 8th house
    lords_of_lagna_5th_in_8th_house = (p_to_h[lord_of_lagna]==eighth_house) and (p_to_h[lord_of_5th]==eighth_house)
    # B. the lord of the 3rd should combine with Mars and Rahu in the 5th house.
    lord_of_3rd_with_mars_rahu_in_5th_house = ( p_to_h[lord_of_3rd] == fifth_house and 
                                                p_to_h[const.MARS_ID] == fifth_house and 
                                                p_to_h[const.RAHU_ID] == fifth_house
                                              )
    return lords_of_lagna_5th_in_8th_house and lord_of_3rd_with_mars_rahu_in_5th_house
def pretha_saapa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        BVR 219 - Pretha Saapa Yoga
        The Sun and Saturn in the 5th house, weak Moon in the 7th house, Rahu in Lagna and Jupiter in the 12th house
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _pretha_saapa_yoga_calculation(planet_positions=pp)
def pretha_saapa_yoga_from_planet_positions(planet_positions):
    """
        BVR 219 - Pretha Saapa Yoga
        The Sun and Saturn in the 5th house, weak Moon in the 7th house, Rahu in Lagna and Jupiter in the 12th house
    """
    return _pretha_saapa_yoga_calculation(planet_positions=planet_positions)
def pretha_saapa_yoga(chart_1d):
    """
        BVR 219 - Pretha Saapa Yoga
        The Sun and Saturn in the 5th house, weak Moon in the 7th house, Rahu in Lagna and Jupiter in the 12th house
    """
    return _pretha_saapa_yoga_calculation(chart_1d=chart_1d)
def _pretha_saapa_yoga_calculation(chart_1d=None,planet_positions=None):
    """
        BVR 219 - Pretha Saapa Yoga
        The Sun and Saturn in the 5th house, weak Moon in the 7th house, Rahu in Lagna and Jupiter in the 12th house
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    fifth_house = (lagna_house+const.HOUSE_5)%12
    seventh_house = (lagna_house+const.HOUSE_7)%12
    twelveth_house = (lagna_house+const.HOUSE_12)%12
    moon_house = p_to_h[const.MOON_ID]; sun_house = p_to_h[const.SUN_ID]
    jupiter_house = p_to_h[const.JUPITER_ID]; saturn_house = p_to_h[const.SATURN_ID]
    rahu_house = p_to_h[const.RAHU_ID]
    sun_saturn_in_5th_house = (sun_house == fifth_house) and (saturn_house == fifth_house)
    if not sun_saturn_in_5th_house: return False
    weak_moon_in_7th_house = (moon_house == seventh_house)
    if not weak_moon_in_7th_house: return False
    rahu_in_lagna = (rahu_house == lagna_house)
    if not rahu_in_lagna: return False
    jupiter_in_12th_house = (jupiter_house == twelveth_house)
    return jupiter_in_12th_house
def _bahu_puthra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _bahu_puthra_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_navamsa)
def bahu_puthra_yoga_from_planet_positions(planet_positions_rasi=None,planet_positions_navamsa=None):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _bahu_puthra_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                         planet_positions_navamsa=planet_positions_navamsa)
def bahu_puthra_yoga(chart_rasi=None,chart_navamsa=None):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    return _bahu_puthra_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa)
def _bahu_puthra_yoga_calculation(chart_rasi=None,chart_navamsa=None,planet_positions_rasi=None,
                                  planet_positions_navamsa=None):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    if _bahu_puthra_yoga_220_calculation(chart_rasi, chart_navamsa, planet_positions_rasi, planet_positions_navamsa): return True
    return _bahu_puthra_yoga_221_calculation(chart_rasi, chart_navamsa, planet_positions_rasi, planet_positions_navamsa)
def bahu_puthra_yoga_220_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _bahu_puthra_yoga_220_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav)
def _bahu_puthra_yoga_220_calculation(chart_rasi=None,chart_navamsa=None,planet_positions_rasi=None,
                                  planet_positions_navamsa=None):
    """
        220 - Rahu is in 5th house. And Rahu is not in Saturn's Navamsa (i.e Rahu in D9 not in Aq/Cp)
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None and planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_rasi_house = p_to_h_rasi[const._ascendant_symbol]
    rasi_5th_house = (lagna_rasi_house+const.HOUSE_5)%12
    # Rahu in rasi 5th house and Rahu not in Aq/Cp in D9
    rahu_in_rasi_5th = (p_to_h_rasi[const.RAHU_ID] == rasi_5th_house)
    rahu_not_in_saturn_navamsa = (p_to_h_navamsa[const.RAHU_ID] not in [const.AQUARIUS, const.CAPRICORN])
    return rahu_in_rasi_5th and rahu_not_in_saturn_navamsa
def bahu_puthra_yoga_221_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    return _bahu_puthra_yoga_221_calculation(planet_positions_rasi=pp, planet_positions_navamsa=pp_nav)
def _bahu_puthra_yoga_221_calculation(chart_rasi=None,chart_navamsa=None,planet_positions_rasi=None,
                                  planet_positions_navamsa=None):
    """
        221 - The same yoga arises if the lord of the Navamsa occupied by a planet who is in association
            with the 7th lord is in the 1st, 2nd or 5th house.
            Steps: (1) Get 7th Lord in Rasi. (2) Find which rasi this 7th lord is in Navamsa chart
            (3) Find the lord of that sign of step-2. (4) Find the sign of the Lord found from step-3 in rasi chart
            (5) That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None and planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_rasi_house = p_to_h_rasi[const._ascendant_symbol]
    rasi_2nd_house = (lagna_rasi_house+const.HOUSE_2)%12
    rasi_5th_house = (lagna_rasi_house+const.HOUSE_5)%12
    rasi_7th_house = (lagna_rasi_house+const.HOUSE_7)%12
    # 221 Step 1. Get 7th Lord in Rasi
    if planet_positions_rasi is not None:
        lord_7th_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, rasi_7th_house)
    else:
        lord_7th_rasi = house.house_owner(chart_rasi, rasi_7th_house)
    # 221 Step 2. Find which rasi this 7th lord is in Navamsa chart
    navamsa_of_7th_lord = p_to_h_navamsa[lord_7th_rasi]
    # 221 Step 3. Find the lord of that sign of step-2
    if planet_positions_navamsa is not None:
        lord_of_step_2 = house.house_owner_from_planet_positions(planet_positions_navamsa, navamsa_of_7th_lord)
    else:
        lord_of_step_2 = house.house_owner(chart_navamsa, navamsa_of_7th_lord)
    # 221 Step 4. Find the sign of the Lord found from step-3 in rasi chart
    sign_of_step_3 = p_to_h_rasi[lord_of_step_2]
    # 221 Step 5. That sign should be either 1st, or 2nd or 5th from Lagna in rasi
    step_4_sign_in_1st_or_2nd_or_5th = sign_of_step_3 in [lagna_rasi_house,rasi_2nd_house,rasi_5th_house]
    return step_4_sign_in_1st_or_2nd_or_5th
def _dattha_puthra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        222 - Mars and Saturn should occupy the 5th house and the lord of Lagna should be in a sign 
            of Mercury, aspected by or in association with the same planet (Mercury).
        223 - The lord of the 7th must be posited in the 11th, the 5th lord must join a benefic 
            and the 5th house must be occupied by Mars or Saturn.
    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _dattha_puthra_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def dattha_puthra_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """
        222 - Mars and Saturn should occupy the 5th house and the lord of Lagna should be in a sign 
            of Mercury, aspected by or in association with the same planet (Mercury).
        223 - The lord of the 7th must be posited in the 11th, the 5th lord must join a benefic 
            and the 5th house must be occupied by Mars or Saturn.
    
    """
    return _dattha_puthra_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def dattha_puthra_yoga(chart_1d, natural_benefics=None):
    """
        222 - Mars and Saturn should occupy the 5th house and the lord of Lagna should be in a sign 
            of Mercury, aspected by or in association with the same planet (Mercury).
        223 - The lord of the 7th must be posited in the 11th, the 5th lord must join a benefic 
            and the 5th house must be occupied by Mars or Saturn.
    
    """
    return _dattha_puthra_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def _dattha_puthra_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    if _dattha_puthra_yoga_222_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                           natural_benefics=natural_benefics): return True
    return _dattha_puthra_yoga_223_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                           natural_benefics=natural_benefics)
def dattha_puthra_yoga_222_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        222 - Mars and Saturn should occupy the 5th house and the lord of Lagna should be in a sign 
            of Mercury, aspected by or in association with the same planet (Mercury).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dattha_puthra_yoga_222_calculation(planet_positions=pp, natural_benefics=nb)
def _dattha_puthra_yoga_222_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        222 - Mars and Saturn should occupy the 5th house and the lord of Lagna should be in a sign 
            of Mercury, aspected by or in association with the same planet (Mercury).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house+const.HOUSE_5)%12; house_7th = (lagna_house+const.HOUSE_7)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
    # Mars and Saturn should occupy the 5th house
    mars_saturn_in_5th_house = (p_to_h[const.MARS_ID]==house_5th) and (p_to_h[const.SATURN_ID]==house_5th)
    # the lord of lagna cojoins mercury.
    lord_of_lagna_cojoins_mercury = (p_to_h[lord_of_lagna]==p_to_h[const.MERCURY_ID])
    # the lord of lagna aspected by mercury
    planets_aspected_by_mercury = house.aspected_planets_of_the_planet(chart_1d, const.MERCURY_ID)
    lord_of_lagna_aspected_by_mercury = lord_of_lagna in planets_aspected_by_mercury
    # the lord of Lagna in a sign of Mercury (Ge/Vi)
    lord_of_lagna_in_mercury_signs = lord_of_lagna in [const.GEMINI, const.VIRGO]
    yoga_222 = (mars_saturn_in_5th_house and 
                (lord_of_lagna_cojoins_mercury or lord_of_lagna_aspected_by_mercury or lord_of_lagna_in_mercury_signs)
               )
    if yoga_222: return True
def dattha_puthra_yoga_223_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        223 - The lord of the 7th must be posited in the 11th, the 5th lord must join a benefic 
            and the 5th house must be occupied by Mars or Saturn.
    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dattha_puthra_yoga_223_calculation(planet_positions=pp, natural_benefics=nb)
def _dattha_puthra_yoga_223_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """
        223 - The lord of the 7th must be posited in the 11th, the 5th lord must join a benefic 
            and the 5th house must be occupied by Mars or Saturn.
    
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house+const.HOUSE_5)%12; house_7th = (lagna_house+const.HOUSE_7)%12
    house_11th = (lagna_house+const.HOUSE_11)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, house_7th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5th)
        lord_of_7th = house.house_owner(chart_1d, house_7th)
    # The lord of the 7th must be posited in the 11th house
    house_of_lord_of_7th = p_to_h[lord_of_7th]
    lord_of_7th_in_11_house = (house_of_lord_of_7th == house_11th)
    if not lord_of_7th_in_11_house: return False
    # the 5th lord must join a benefic 
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    house_of_lord_of_5th = p_to_h[lord_of_5th]
    lord_of_5th_joins_a_benefic = any(p_to_h[nb]==house_of_lord_of_5th for nb in _natural_benefics)
    if not lord_of_5th_joins_a_benefic: return False
    # the 5th house must be occupied by Mars or Saturn.
    mars_or_saturn_in_5th_house = (p_to_h[const.MARS_ID]==house_5th) or (p_to_h[const.SATURN_ID]==house_5th)
    return mars_or_saturn_in_5th_house
def aputhra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        224 - The lord of the 5th house should occupy a dusthana.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _aputhra_yoga_calculation(planet_positions=pp)
def aputhra_yoga_from_planet_positions(planet_positions):
    """
        224 - The lord of the 5th house should occupy a dusthana.
    """
    return _aputhra_yoga_calculation(planet_positions=planet_positions)
def aputhra_yoga(chart_1d):
    """
        224 - The lord of the 5th house should occupy a dusthana.
    """
    return _aputhra_yoga_calculation(chart_1d=chart_1d)
def _aputhra_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        224 - The lord of the 5th house should occupy a dusthana.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house+const.HOUSE_5)%12; house_7th = (lagna_house+const.HOUSE_7)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5th)
    house_of_lord_of_5th = p_to_h[lord_of_5th]
    return house_of_lord_of_5th in house.dushthanas_of_the_raasi(lagna_house)
def eka_puthra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        225 - Lord of 5th house should join a kendra or trikona
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _eka_puthra_yoga_calculation(planet_positions=pp)
def eka_puthra_yoga_from_planet_positions(planet_positions):
    """
        225 - Lord of 5th house should join a kendra or trikona.
    """
    return _eka_puthra_yoga_calculation(planet_positions=planet_positions)
def eka_puthra_yoga(chart_1d):
    """
        225 - Lord of 5th house should join a kendra or trikona
    """
    return _eka_puthra_yoga_calculation(chart_1d=chart_1d)
def _eka_puthra_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        225 - Lord of 5th house should join a kendra or trikona
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5th)
    house_of_lord_of_5th = p_to_h[lord_of_5th]
    lord_5th_in_kendra = house_of_lord_of_5th in quadrants_of_the_house(lagna_house)
    lord_5th_in_trine = house_of_lord_of_5th in trines_of_the_house(lagna_house)
    return lord_5th_in_kendra or lord_5th_in_trine
def suputhra_yoga(chart_1d):
    """
        226 - Jupiter is lord of 5th house (=Lagna in Le/Sc) and 
            Sun in favorable position (own, exalted,friendly sign)
    """
    return _suputhra_yoga_calculation(chart_1d=chart_1d)
def suputhra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        226 - Jupiter is lord of 5th house (=Lagna in Le/Sc) and 
            Sun in favorable position (own, exalted,friendly sign)
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _suputhra_yoga_calculation(planet_positions=pp)
def suputhra_yoga_from_planet_positions(planet_positions):
    """
        226 - Jupiter is lord of 5th house (=Lagna in Le/Sc) and 
            Sun in favorable position (own, exalted,friendly sign)
    """
    return _suputhra_yoga_calculation(planet_positions=planet_positions)
def _suputhra_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        226 - Jupiter is lord of 5th house (=Lagna in Le/Sc) and 
            Sun in favorable position (own, exalted,friendly sign)
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    sun_house = p_to_h[const.SUN_ID]
    lagna_in_Le_or_Sc = lagna_house in [const.LEO,const.SCORPIO]
    sun_in_favorable_sign = utils.is_planet_strong(const.SUN_ID, sun_house, include_neutral_samam=False)
    return lagna_in_Le_or_Sc and sun_in_favorable_sign
def kaalanirdesat_puthra_yoga(chart_1d=None):
    """
        227 - Jupiter should be in the 5th house and the lord of the 5th should join Venus
        228 - Jupiter must also occupy the 9th from Lagna and Venus should be in the 9th from Jupiter,
            in conjunction with the lord of Lagna
    """
    _kaalanirdesat_puthra_yoga_calculation(chart_1d=chart_1d)
def _kaalanirdesat_puthra_yoga_from_planet_positions(planet_positions):
    """
        227 - Jupiter should be in the 5th house and the lord of the 5th should join Venus
        228 - Jupiter must also occupy the 9th from Lagna and Venus should be in the 9th from Jupiter,
            in conjunction with the lord of Lagna
    """
    return _kaalanirdesat_puthra_yoga_calculation(planet_positions=planet_positions)
def _kaalanirdesat_puthra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        227 - Jupiter should be in the 5th house and the lord of the 5th should join Venus
        228 - Jupiter must also occupy the 9th from Lagna and Venus should be in the 9th from Jupiter,
            in conjunction with the lord of Lagna
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kaalanirdesat_puthra_yoga_calculation(planet_positions=pp)
def _kaalanirdesat_puthra_yoga_calculation(chart_1d=None, planet_positions=None):
    if _kaalanirdesat_puthra_yoga_227_calculation(chart_1d=chart_1d, planet_positions=planet_positions): return True
    return _kaalanirdesat_puthra_yoga_228_calculation(chart_1d=chart_1d, planet_positions=planet_positions)
def kaalanirdesat_puthra_yoga_227_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        227 - Jupiter should be in the 5th house and the lord of the 5th should join Venus
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kaalanirdesat_puthra_yoga_227_calculation(planet_positions=pp)
def _kaalanirdesat_puthra_yoga_227_calculation(chart_1d=None, planet_positions=None):
    """
        227 - Jupiter should be in the 5th house and the lord of the 5th should join Venus
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    jupiter_house = p_to_h[const.JUPITER_ID]
    venus_house = p_to_h[const.VENUS_ID]
    house_5th = (lagna_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5th)
    jupiter_in_5th = (jupiter_house==house_5th)
    lord_of_5th_joins_venus = (p_to_h[lord_of_5th]==venus_house)
    return jupiter_in_5th and lord_of_5th_joins_venus
def kaalanirdesat_puthra_yoga_228_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        228 - Jupiter must also occupy the 9th from Lagna and Venus should be in the 9th from Jupiter,
            in conjunction with the lord of Lagna
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kaalanirdesat_puthra_yoga_228_calculation(planet_positions=pp)
def _kaalanirdesat_puthra_yoga_228_calculation(chart_1d=None, planet_positions=None):
    """
        228 - Jupiter must also occupy the 9th from Lagna and Venus should be in the 9th from Jupiter,
            in conjunction with the lord of Lagna
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    jupiter_house = p_to_h[const.JUPITER_ID]
    venus_house = p_to_h[const.VENUS_ID]
    house_5th = (lagna_house+const.HOUSE_5)%12
    house_9th = (lagna_house+const.HOUSE_9)%12
    jupiter_9th = (jupiter_house+const.HOUSE_9)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
    jupiter_in_9th_from_lagna = (jupiter_house == house_9th)
    if not jupiter_in_9th_from_lagna: return False
    venus_in_9th_from_jupiter = (venus_house == jupiter_9th)
    if not venus_in_9th_from_jupiter: return False
    venus_with_lord_of_lagna = (venus_house == p_to_h[lord_of_lagna])
    return venus_with_lord_of_lagna
def kaalanirdesat_puthranaasa_yoga(chart_1d,natural_malefics=None):
    """
        229 - Rahu must occupy the 5th house, the lord of the 5th must be in conjunction with a 
            malefic and Jupiter should be debilitated.
        230 - Malefics should be disposed (cojoins or aspect) in 5th from Jupiter and 5th from Lagna
    """
    return _kaalanirdesat_puthranaasa_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def _kaalanirdesat_puthranaasa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        229 - Rahu must occupy the 5th house, the lord of the 5th must be in conjunction with a 
            malefic and Jupiter should be debilitated.
        230 - Malefics should be disposed (cojoins or aspect) in 5th from Jupiter and 5th from Lagna
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _kaalanirdesat_puthranaasa_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def kaalanirdesat_puthranaasa_yoga_from_planet_positions(planet_positions,natural_malefics=None):
    """
        229 - Rahu must occupy the 5th house, the lord of the 5th must be in conjunction with a 
            malefic and Jupiter should be debilitated.
        230 - Malefics should be disposed (cojoins or aspect) in 5th from Jupiter and 5th from Lagna
    """
    return _kaalanirdesat_puthranaasa_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def _kaalanirdesat_puthranaasa_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    if _kaalanirdesat_puthranaasa_yoga_229_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                                       natural_malefics=natural_malefics): return True
    return _kaalanirdesat_puthranaasa_yoga_230_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                                       natural_malefics=natural_malefics)
def kaalanirdesat_puthranaasa_yoga_229_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        229 - Rahu must occupy the 5th house, the lord of the 5th must be in conjunction with a 
            malefic and Jupiter should be debilitated.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _kaalanirdesat_puthranaasa_yoga_229_calculation(planet_positions=pp, natural_malefics=nm)
def _kaalanirdesat_puthranaasa_yoga_229_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        229 - Rahu must occupy the 5th house, the lord of the 5th must be in conjunction with a 
            malefic and Jupiter should be debilitated.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    jupiter_house = p_to_h[const.JUPITER_ID]
    house_5th = (lagna_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5th)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    rahu_in_5th = (p_to_h[const.RAHU_ID] == house_5th)
    jupiter_debilititated = utils.is_planet_in_debilitation(const.JUPITER_ID, jupiter_house, planet_positions=planet_positions, enforce_deep_debilitation=False)
    lord_of_5th_with_malefic = any(p_to_h[lord_of_5th]==p_to_h[mp] for mp in _natural_malefics)
    return rahu_in_5th and jupiter_debilititated and lord_of_5th_with_malefic
def kaalanirdesat_puthranaasa_yoga_230_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        230 - Malefics should be disposed (cojoins or aspect) in 5th from Jupiter and 5th from Lagna
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _kaalanirdesat_puthranaasa_yoga_230_calculation(planet_positions=pp, natural_malefics=nm)
def _kaalanirdesat_puthranaasa_yoga_230_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        230 - Malefics should be disposed (cojoins or aspect) in 5th from Jupiter and 5th from Lagna
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    jupiter_house = p_to_h[const.JUPITER_ID]
    house_5th = (lagna_house+const.HOUSE_5)%12
    jupiter_5th = (jupiter_house+const.HOUSE_5)%12
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    malefic_5th_from_lagna = any(p_to_h[mp]==house_5th for mp in _natural_malefics)
    malefics_aspecting_5th_from_lagna = any(mp in house.planets_aspecting_the_raasi(chart_1d, house_5th) for mp in _natural_malefics)
    malefic_5th_from_jupiter = any(p_to_h[mp]==jupiter_5th for mp in _natural_malefics)
    malefics_aspecting_5th_from_jupiter = any(mp in house.planets_aspecting_the_raasi(chart_1d, jupiter_5th) for mp in _natural_malefics)
    yoga_230 = ((malefic_5th_from_lagna or malefics_aspecting_5th_from_lagna) and 
                (malefic_5th_from_jupiter or malefics_aspecting_5th_from_jupiter))
    return yoga_230
def buddhimaturya_yoga_from_jd_place(jd, place, divisional_chart_factor=1, require_lord_of_5th_to_be_benefic=True):
    """
        231 - If the 5th lord, being a benefic, is either aspected by another benefic or occupies a 
            benefic sign, the above yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _buddhimaturya_yoga_calculation(planet_positions=pp, natural_benefics=nb,
                                    require_lord_of_5th_to_be_benefic=require_lord_of_5th_to_be_benefic)
def buddhimaturya_yoga_from_planet_positions(planet_positions=None,natural_benefics=None,
                                    require_lord_of_5th_to_be_benefic=True):
    """
        231 - If the 5th lord, being a benefic, is either aspected by another benefic or occupies a 
            benefic sign, the above yoga is given rise to.
    """
    return _buddhimaturya_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics,
                                    require_lord_of_5th_to_be_benefic=require_lord_of_5th_to_be_benefic)
def buddhimaturya_yoga(chart_1d, natural_benefics=None, require_lord_of_5th_to_be_benefic=True):
    """
        231 - If the 5th lord, being a benefic, is either aspected by another benefic or occupies a 
            benefic sign, the above yoga is given rise to.
    """
    return _buddhimaturya_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics,
                                require_lord_of_5th_to_be_benefic=require_lord_of_5th_to_be_benefic)
def _buddhimaturya_yoga_calculation(chart_1d=None, planet_positions=None,natural_benefics=None,
                                    require_lord_of_5th_to_be_benefic=True):
    """
        231 - If the 5th lord, being a benefic, is either aspected by another benefic or occupies a 
            benefic sign, the above yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5 = (lagna_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_5)
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    lord_of_5th_is_benfic = lord_of_5th in _natural_benefics if require_lord_of_5th_to_be_benefic else True
    lord_of_5th_aspected_by = house.planets_aspecting_the_planet(chart_1d, lord_of_5th)
    lord_of_5th_aspected_by_benefic = any(bp in lord_of_5th_aspected_by for bp in _natural_benefics)
    lord_of_5th_cojoins_benefic = any(p_to_h[lord_of_5th]==p_to_h[bp] for bp in _natural_benefics)
    lord_of_5th_in_benefic_sign = p_to_h[lord_of_5th] in const.benefic_signs
    return lord_of_5th_is_benfic and (lord_of_5th_cojoins_benefic or lord_of_5th_aspected_by_benefic or lord_of_5th_in_benefic_sign)
def theevrabuddhi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        232 - Lord of 5th in rasi should be a benefic and should in Navamsa Lagna.
            Lord of Navamsa Lagna should be a benefic or aspected by benefic.
    """
    pp_rasi = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _theevrabuddhi_yoga_calculation(planet_positions_rasi=pp_rasi, planet_positions_navamsa=pp_nav,
                                           natural_benefics=nb)
def theevrabuddhi_yoga_from_planet_positions(planet_positions_rasi,planet_positions_navamsa,natural_benefics=None):
    """
        232 - Lord of 5th in rasi should be a benefic and should in Navamsa Lagna.
            Lord of Navamsa Lagna should be a benefic or aspected by benefic
    """
    if planet_positions_navamsa is None:
        planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    return _theevrabuddhi_yoga_calculation(planet_positions_rasi=planet_positions_rasi, 
                                           planet_positions_navamsa=planet_positions_navamsa, 
                                           natural_benefics=natural_benefics)
def theevrabuddhi_yoga_calculation(chart_rasi,chart_navamsa,natural_benefics=None):
    """
        232 - Lord of 5th in rasi should be a benefic and should in Navamsa Lagna.
            Lord of Navamsa Lagna should be a benefic or aspected by benefic
    """
    return _theevrabuddhi_yoga_calculation(chart_rasi=chart_rasi, chart_navamsa=chart_navamsa,
                                           natural_benefics=natural_benefics)
def _theevrabuddhi_yoga_calculation(chart_rasi=None,chart_navamsa=None,planet_positions_rasi=None,
                                    planet_positions_navamsa=None,natural_benefics=None):
    """
        232 - Lord of 5th in rasi should be a benefic and should in Navamsa Lagna.
            Lord of Navamsa Lagna should be a benefic or aspected by benefic
    """
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if chart_rasi is None: return False
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    lagna_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    lagna_house_navamsa = p_to_h_navamsa[const._ascendant_symbol]
    house_5th_rasi = (lagna_house_rasi+const.HOUSE_5)%12
    _nb_rasi = _get_natural_benefics(chart_rasi, natural_benefics)
    _nb_navamsa = _get_natural_benefics(chart_navamsa, natural_benefics)
    if planet_positions_rasi is not None:
        lord_of_5th_rasi = house.house_owner_from_planet_positions(planet_positions_rasi, house_5th_rasi)
    else:
        lord_of_5th_rasi = house.house_owner(chart_rasi, house_5th_rasi)
    if planet_positions_rasi is not None:
        lord_of_lagna_navamsa = house.house_owner_from_planet_positions(planet_positions_navamsa, lagna_house_navamsa)
    else:
        lord_of_lagna_navamsa = house.house_owner(chart_navamsa, lagna_house_navamsa)
    # Lord of 5th in rasi should be a benefic and should in Navamsa Lagna.
    lord_of_5th_rasi_is_benefic = lord_of_5th_rasi in _nb_rasi
    lord_of_5th_rasi_is_in_navamsa_lagna = (p_to_h_navamsa[lord_of_5th_rasi]==lagna_house_navamsa)
    # Lord of Navamsa Lagna should be a benefic or aspected by benefic
    lord_of_lagna_navamsa_is_benefic = lord_of_lagna_navamsa in _nb_navamsa
    lord_of_lagna_navamsa_aspected_by = house.planets_aspecting_the_planet(chart_rasi, lord_of_lagna_navamsa)
    lord_of_lagna_navamsa_aspected_by_benefic = any(_nb in lord_of_lagna_navamsa_aspected_by for _nb in _nb_rasi)
    return (lord_of_5th_rasi_is_benefic and lord_of_5th_rasi_is_in_navamsa_lagna and
            (lord_of_lagna_navamsa_is_benefic or lord_of_lagna_navamsa_aspected_by_benefic))
def buddhi_jada_yoga_from_jd_place(jd, place, divisional_chart_factor=1):    
    """
        233 - Lord of Lagna cojoins or aspected by malefics. AND Saturn occupies 5th house, AND 
            Lord of lagna is aspected by Saturn.
            OR
            5th lord is conjoined with malefics AND 
            (Saturn aspects 5th Lord) OR Moon in 5th House 
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _buddhi_jada_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def buddhi_jada_yoga_from_planet_positions(planet_positions, natural_malefics=None):    
    """
        233 - Lord of Lagna cojoins or aspected by malefics. AND Saturn occupies 5th house, AND 
            Lord of lagna is aspected by Saturn.
            OR
            5th lord is conjoined with malefics AND 
            (Saturn aspects 5th Lord) OR Moon in 5th House 
    """
    return _buddhi_jada_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def  buddhi_jada_yoga(chart_1d, natural_malefics=None):
    """
        233 - Lord of Lagna cojoins or aspected by malefics. AND Saturn occupies 5th house, AND 
            Lord of lagna is aspected by Saturn.
            OR
            5th lord is conjoined with malefics AND 
            (Saturn aspects 5th Lord) OR Moon in 5th House 
    """
    return _buddhi_jada_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def _buddhi_jada_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):    
    """
        233 - Lord of Lagna cojoins or aspected by malefics. AND Saturn occupies 5th house, AND 
            Lord of lagna is aspected by Saturn.
            OR
            5th lord is conjoined with malefics AND 
            (Saturn aspects 5th Lord) OR Moon in 5th House 
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house+const.HOUSE_5)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_5th)
    else:
        lord_of_lagna = house.house_owner(chart_1d,lagna_house)
        lord_of_5th = house.house_owner(chart_1d, house_5th)
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    house_of_lord_of_lagna = p_to_h[lord_of_lagna]
    house_of_lord_of_5th = p_to_h[lord_of_5th]
    # 1. Lord of Lagna cojoins and aspected by malefics.    
    lord_of_lagna_cojoins_malefic = any(p_to_h[mp]==house_of_lord_of_lagna for mp in _natural_malefics)
    planets_aspecting_lord_of_lagna = house.planets_aspecting_the_planet(chart_1d, lord_of_lagna)
    lord_of_lagna_aspected_by_malefics = any(mp in planets_aspecting_lord_of_lagna for mp in _natural_malefics)
    yoga_233_1 = lord_of_lagna_cojoins_malefic or lord_of_lagna_aspected_by_malefics
    # 2. Saturn occupies 5th house
    saturn_in_5th_house = (p_to_h[const.SATURN_ID]==house_5th)
    # 3. Lord of lagna is aspected by Saturn
    lord_of_lagna_aspected_by_saturn = const.SATURN_ID in planets_aspecting_lord_of_lagna
    yoga_233_1 = ( (planets_aspecting_lord_of_lagna or lord_of_lagna_aspected_by_malefics) and
                   saturn_in_5th_house and lord_of_lagna_aspected_by_saturn)
    if yoga_233_1: return True
    # Alternate Path
    lord_of_5th_conjoins_malefics = any(p_to_h[mp]==house_of_lord_of_5th for mp in _natural_malefics)
    lord_of_lagna_aspected_by_saturn = const.SATURN_ID in house.planets_aspecting_the_planet(chart_1d, lord_of_5th) 
    moon_in_5th_house = (p_to_h[const.MOON_ID]==house_5th)
    return lord_of_5th_conjoins_malefics and (lord_of_lagna_aspected_by_saturn or moon_in_5th_house)
def thrikaala_gnana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
    NOTE: This yoga requires Jupiter longitude information through planet_positions argument
          and hence does not support chart_1d argument
    234 - Jupiter in Mrudwamsa in his own navamsa.
        OR
        Jupiter in Gopuramsa (score >= 4) AND aspected by a benefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    v_scores = charts.vaiseshikamsa_dhasavarga_of_planets(jd, place)
    v_scores = [v[0] for _,v in v_scores.items()]
    jupiter_vaiseshikamsa_dhasavarga_score = v_scores[const.JUPITER_ID]
    return _thrikaala_gnana_yoga_calculation(planet_positions=pp, 
                        jupiter_vaiseshikamsa_dhasavarga_score=jupiter_vaiseshikamsa_dhasavarga_score,
                        natural_benefics=nb)
def thrikaala_gnana_yoga_from_planet_positions(planet_positions,jupiter_vaiseshikamsa_dhasavarga_score=None,
                                      natural_benefics=None):
    """
    NOTE: This yoga requires Jupiter longitude information through planet_positions argument
          and hence does not support chart_1d argument
    234 - Thrikalagnana Yoga
    Path A: Jupiter in Mrudwamsa in his own navamsa.
    OR
    Path B: Jupiter in Gopuramsa (score >= 4) AND aspected by a benefic.
    """
    return _thrikaala_gnana_yoga_calculation(planet_positions, jupiter_vaiseshikamsa_dhasavarga_score, natural_benefics)
def _thrikaala_gnana_yoga_calculation(planet_positions=None, jupiter_vaiseshikamsa_dhasavarga_score=None,
                                      natural_benefics=None):
    """
    NOTE: This yoga requires Jupiter longitude information through planet_positions argument
          and hence does not support chart_1d argument
    234 - Thrikalagnana Yoga
    Path A: Jupiter in Mrudwamsa in his own navamsa.
    OR
    Path B: Jupiter in Gopuramsa (score >= 4) AND aspected by a benefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        jupiter_longitude = planet_positions[const.JUPITER_ID+1][1][1]
    if chart_1d is None:
        return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    jupiter_house = p_to_h[const.JUPITER_ID] 
    # --- Path A: Intrinsic Power (No external aspect required) ---
    def is_jupiter_in_own_navamsa_and_mrudwamsa():
        # own navamsa check
        jupiter_total_long = jupiter_house*30 + jupiter_longitude
        jupiter_navamsa_index = int((jupiter_total_long / (30/9))) % 12
        is_own_navamsa = (jupiter_navamsa_index == 8 or jupiter_navamsa_index == 11)
        shastiamsa_count = int(jupiter_longitude * 2) + 1
        is_odd_sign = (jupiter_house % 2 == 0)
        is_mridu_shastiamsa = False
        if is_odd_sign:
            if shastiamsa_count == 19: is_mridu_shastiamsa = True
        else:
            if shastiamsa_count == 42: is_mridu_shastiamsa = True
        return (is_mridu_shastiamsa and is_own_navamsa)
    # --- Path B: External Strength (Gopuramsa + Benefic Aspect) ---
    def is_gopuramsa_with_benefic():
        # Check if score is provided and meets Gopuramsa (4)
        if jupiter_vaiseshikamsa_dhasavarga_score is None or jupiter_vaiseshikamsa_dhasavarga_score < 4:
            return False
        # Check for benefic aspect or conjunction
        _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
        planets_aspecting_jupiter = house.planets_aspecting_the_planet(chart_1d, const.JUPITER_ID)
        # Aspected by benefic
        jupiter_aspected_by_benefic = any(mp in planets_aspecting_jupiter for mp in _natural_benefics)
        # Conjoined by benefic (In the same house)
        jupiter_conjoined_benefic = any(
            p_to_h[mp] == jupiter_house for mp in _natural_benefics if mp != const.JUPITER_ID
        )
        return (jupiter_aspected_by_benefic or jupiter_conjoined_benefic)
    # Final logic: Path A OR Path B
    return is_jupiter_in_own_navamsa_and_mrudwamsa() or is_gopuramsa_with_benefic()
def jara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        236 - The 10th house must be occupied by the lords of the 10th, 2nd and 7th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _jara_yoga_calculation(planet_positions=pp)
def jara_yoga_from_planet_positions(chart_1d=None, planet_positions=None):
    """
        236 - The 10th house must be occupied by the lords of the 10th, 2nd and 7th.
    """
    return _jara_yoga_calculation(planet_positions=planet_positions)
def jara_yoga(chart_1d):
    """
        236 - The 10th house must be occupied by the lords of the 10th, 2nd and 7th.
    """
    return _jara_yoga_calculation(chart_1d=chart_1d)
def _jara_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        236 - The 10th house must be occupied by the lords of the 10th, 2nd and 7th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_2nd = (lagna_house+const.HOUSE_2)%12
    house_7th = (lagna_house+const.HOUSE_7)%12
    house_10th = (lagna_house+const.HOUSE_10)%12
    if planet_positions is not None:
        lord_of_2nd = house.house_owner_from_planet_positions(planet_positions, house_2nd)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, house_7th)
        lord_of_10th = house.house_owner_from_planet_positions(planet_positions, house_10th)
    else:
        lord_of_2nd = house.house_owner(chart_1d, house_2nd)        
        lord_of_7th = house.house_owner(chart_1d, house_7th)        
        lord_of_10th = house.house_owner(chart_1d, house_10th)
    return ( p_to_h[lord_of_2nd] == house_10th and 
             p_to_h[lord_of_7th] == house_10th and 
             p_to_h[lord_of_10th] == house_10th )
def jarajaputra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        237. Powerful lords of the 5th and the 7th must join with the lord of the 6th and 
        be aspected by benefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _jarajaputra_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def jarajaputra_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """ 
        237. Powerful lords of the 5th and the 7th must join with the lord of the 6th and 
        be aspected by benefics.
    """
    return _jarajaputra_yoga_calculation(planet_positions, natural_benefics)
def jarajaputra_yoga(chart_1d, natural_benefics=None):
    """ 
        237. Powerful lords of the 5th and the 7th must join with the lord of the 6th and 
        be aspected by benefics.
    """
    return _jarajaputra_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def _jarajaputra_yoga_calculation(chart_1d=None, planet_positions=None, natural_benefics=None):
    """ 
        237. Powerful lords of the 5th and the 7th must join with the lord of the 6th and 
        be aspected by benefics.
"""
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_of_5th = (house_of_lagna+const.HOUSE_5)%12
    house_of_6th = (house_of_lagna+const.HOUSE_6)%12
    house_of_7th = (house_of_lagna+const.HOUSE_7)%12
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    if planet_positions is not None:
        lord_of_5th = house.house_owner_from_planet_positions(planet_positions, house_of_5th)
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, house_of_6th)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, house_of_7th)
    else:
        lord_of_5th = house.house_owner(chart_1d, house_of_5th)
        lord_of_6th = house.house_owner(chart_1d, house_of_6th)
        lord_of_7th = house.house_owner(chart_1d, house_of_7th)
    house_of_lord_of_5th = p_to_h[lord_of_5th]
    house_of_lord_of_6th = p_to_h[lord_of_6th]
    house_of_lord_of_7th = p_to_h[lord_of_7th]
    lord_of_5th_is_powerful = utils.is_planet_strong(lord_of_5th, house_of_lord_of_5th)
    lord_of_7th_is_powerful = utils.is_planet_strong(lord_of_7th, house_of_lord_of_7th)
    lords_are_powerful = lord_of_5th_is_powerful and lord_of_7th_is_powerful
    if not lords_are_powerful: return False
    powerful_lords_join_6th_lord = ( (house_of_lord_of_5th==house_of_lord_of_6th) and
                                     (house_of_lord_of_7th==house_of_lord_of_6th) )
    if not powerful_lords_join_6th_lord: return False
    planets_aspecting_5th_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_5th)
    planets_aspecting_7th_lord = house.planets_aspecting_the_planet(chart_1d, lord_of_7th)
    benefics_aspect_5th_lord = any(bp in planets_aspecting_5th_lord for bp in _natural_benefics)
    benefics_aspect_7th_lord = any(bp in planets_aspecting_7th_lord for bp in _natural_benefics)
    benefics_aspect_lords = benefics_aspect_5th_lord and benefics_aspect_7th_lord
    return benefics_aspect_lords
def bahu_sthree_yoga(chart_1d):
    """
        238 - If the lords of the Lagna and the 7th are in conjunction or aspect with each other, the 
        above yoga is given rise to.
    """
    return _bahu_sthree_yoga_calculation(chart_1d=chart_1d)
def bahu_sthree_yoga_from_planet_positions(planet_positions):
    """
        238 - If the lords of the Lagna and the 7th are in conjunction or aspect with each other, the 
        above yoga is given rise to.
    """
    return _bahu_sthree_yoga_calculation(planet_positions=planet_positions)
def bahu_sthree_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        238 - If the lords of the Lagna and the 7th are in conjunction or aspect with each other, the 
        above yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bahu_sthree_yoga_calculation(planet_positions=pp)
def _bahu_sthree_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        238 - If the lords of the Lagna and the 7th are in conjunction or aspect with each other, the 
        above yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_of_7th = (house_of_lagna+const.HOUSE_7)%12
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, house_of_lagna)
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, house_of_7th)
    else:
        lord_of_lagna = house.house_owner(chart_1d, house_of_lagna)
        lord_of_7th = house.house_owner(chart_1d, house_of_7th)
    house_of_lord_of_lagna = p_to_h[lord_of_lagna]
    house_of_lord_of_7th = p_to_h[lord_of_7th]
    lords_are_in_conjunction = (house_of_lord_of_lagna==house_of_lord_of_7th)
    planets_aspecting_lord_of_lagna = house.planets_aspecting_the_planet(chart_1d, lord_of_lagna)
    planets_aspecting_lord_of_7th = house.planets_aspecting_the_planet(chart_1d, lord_of_7th)
    lords_aspect_each_other = ( lord_of_7th in planets_aspecting_lord_of_lagna and
                                lord_of_lagna in planets_aspecting_lord_of_7th )
    return lords_are_in_conjunction or lords_aspect_each_other
def satkalatra_yoga(chart_1d):
    """
        239 - The lord of the 7th or Venus should join or be aspected by Jupiter or Mercury.
    """
    return _satkalatra_yoga_calculation(chart_1d=chart_1d)
def satkalatra_yoga_from_planet_positions(planet_positions):
    """
        239 - The lord of the 7th or Venus should join or be aspected by Jupiter or Mercury.
    """
    return _satkalatra_yoga_calculation(planet_positions=planet_positions)
def satkalatra_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        239 - The lord of the 7th or Venus should join or be aspected by Jupiter or Mercury.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _satkalatra_yoga_calculation(planet_positions=pp)
def _satkalatra_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        239 - The lord of the 7th or Venus should join or be aspected by Jupiter or Mercury.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None:
        return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_of_7th = (house_of_lagna + const.HOUSE_7) % 12
    if planet_positions is not None:
        lord_of_7th = house.house_owner_from_planet_positions(planet_positions, house_of_7th)
    else:
        lord_of_7th = house.house_owner(chart_1d, house_of_7th)
    jupiter = const.JUPITER_ID
    mercury = const.MERCURY_ID
    venus   = const.VENUS_ID
    # Conjunction checks (same house)
    l7_conj_jup = (p_to_h[lord_of_7th] == p_to_h[jupiter])
    l7_conj_mer = (p_to_h[lord_of_7th] == p_to_h[mercury])
    ven_conj_jup = (p_to_h[venus] == p_to_h[jupiter])
    ven_conj_mer = (p_to_h[venus] == p_to_h[mercury])
    # Aspect checks (who aspects the target planet)
    l7_aspected_by = house.planets_aspecting_the_planet(chart_1d, lord_of_7th)
    ven_aspected_by = house.planets_aspecting_the_planet(chart_1d, venus)
    l7_aspected_by_jup_or_mer = (jupiter in l7_aspected_by) or (mercury in l7_aspected_by)
    ven_aspected_by_jup_or_mer = (jupiter in ven_aspected_by) or (mercury in ven_aspected_by)
    # Condition per sutra: (L7 joined/aspected by Jup/Merc) OR (Venus joined/aspected by Jup/Merc)
    l7_condition = l7_conj_jup or l7_conj_mer or l7_aspected_by_jup_or_mer
    venus_condition = ven_conj_jup or ven_conj_mer or ven_aspected_by_jup_or_mer
    return l7_condition or venus_condition
def bhaga_chumbana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        240. A. 7th lord in 4th and in conjunction with Venus. OR
             B. if Lagna lord is debilitated in rasi or in navamsa
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    planet_positions_navamsa = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    return _bhaga_chumbana_yoga_calculation(planet_positions=pp, chart_navamsa=chart_navamsa)

def bhaga_chumbana_yoga_from_planet_positions(planet_positions, chart_navamsa=None):
    """
        240. A. 7th lord in 4th and in conjunction with Venus. OR
             B. if Lagna lord is debilitated in rasi or in navamsa
    """
    if chart_navamsa is None:
        pp_nav = charts.navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(pp_nav)
    return _bhaga_chumbana_yoga_calculation(planet_positions=planet_positions, chart_navamsa=chart_navamsa)
def bhaga_chumbana_yoga(chart_1d, chart_navamsa=None):
    """
        240. A. 7th lord in 4th and in conjunction with Venus. OR
             B. if Lagna lord is debilitated in rasi or in navamsa
    """
    return _bhaga_chumbana_yoga_calculation(chart_1d=chart_1d, chart_navamsa=chart_navamsa)
def _bhaga_chumbana_yoga_calculation(chart_1d=None, planet_positions=None,chart_navamsa=None):
    """
    240. A. 7th lord in 4th and in conjunction with Venus. OR
         B. if Lagna lord is debilitated in rasi or in navamsa
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        if chart_navamsa is None:
            pp_9 = charts.nava_navamsa_chart(planet_positions)
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(pp_9)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L_house = p_to_h[const._ascendant_symbol]
    H4 = (L_house + const.HOUSE_4) % 12
    H7 = (L_house + const.HOUSE_7) % 12
    if planet_positions is not None:
        L7 = house.house_owner_from_planet_positions(planet_positions, H7)
        L1 = house.house_owner_from_planet_positions(planet_positions, L_house)
    else:
        L7 = house.house_owner(chart_1d, H7)
        L1 = house.house_owner(chart_1d, L_house)
    # Conjunction in 4th with Venus
    venus = const.VENUS_ID
    in_4th = (p_to_h[L7] == H4)
    venus_in_4th = (p_to_h[venus] == H4)
    main_condition = in_4th and venus_in_4th
    if main_condition:
        return True
    # Rasi debilitation via your strength matrix (0 = debilitated)
    h_of_L1 = p_to_h[L1]
    if utils.is_planet_in_debilitation(L1, h_of_L1, planet_positions): return True
    # if navamsa chart supplied - check this
    if chart_navamsa is None: return False
    p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    return (const.house_strengths_of_planets[L1][p_to_h_nav[L1]] == const._DEBILITATED_NEECHAM)
def bhaagya_yoga(chart_1d, natural_benefics=None):
    """
        241 -  strong benefic should be in Lagna, the 3rd or 5th, simultaneously aspecting the 9th.
    """
    return _bhaagya_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def bhaagya_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """
        241 -  strong benefic should be in Lagna, the 3rd or 5th, simultaneously aspecting the 9th.
    """
    return _bhaagya_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def bhaagya_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        241 -  strong benefic should be in Lagna, the 3rd or 5th, simultaneously aspecting the 9th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _bhaagya_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _bhaagya_yoga_calculation(chart_1d=None, planet_positions=None,natural_benefics=None):
    """
        241 -  strong benefic should be in Lagna, the 3rd or 5th, simultaneously aspecting the 9th.
    """    
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L_house = p_to_h[const._ascendant_symbol]
    H3 = (L_house + const.HOUSE_3) % 12
    H5 = (L_house + const.HOUSE_5) % 12
    H9 = (L_house + const.HOUSE_9) % 12
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    benefics_in_lagna_h3_h5 = [p for p,h in p_to_h.items() if h in [L_house, H3,H5] and p in _natural_benefics]
    if not benefics_in_lagna_h3_h5: return False
    strong_benefics_in_lagna_h2_h3 = [bp for bp in benefics_in_lagna_h3_h5 if utils.is_planet_strong(bp, p_to_h[bp])]
    if not strong_benefics_in_lagna_h2_h3: return False
    aspecting_H9 = house.planets_aspecting_the_raasi(chart_1d, H9)
    return any(bp in aspecting_H9 for bp in strong_benefics_in_lagna_h2_h3)
def jananatpurvam_pitru_marana_yoga(chart_1d):
    """
        242 - The Sun must be in the 6th, 8th or 12th; lord of the 8th must be in the 9th; 
            lord of the 12th in Lagna and the lord of the 6th in the 5th.
    """
    return _jananatpurvam_pitru_marana_yoga_calculation(chart_1d=chart_1d)
def jananatpurvam_pitru_marana_yoga_from_planet_positions(planet_positions):
    """
        242 - The Sun must be in the 6th, 8th or 12th; lord of the 8th must be in the 9th; 
            lord of the 12th in Lagna and the lord of the 6th in the 5th.
    """
    return _jananatpurvam_pitru_marana_yoga_calculation(planet_positions=planet_positions)
def jananatpurvam_pitru_marana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        242 - The Sun must be in the 6th, 8th or 12th; lord of the 8th must be in the 9th; 
            lord of the 12th in Lagna and the lord of the 6th in the 5th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _jananatpurvam_pitru_marana_yoga_calculation(planet_positions=pp)
def _jananatpurvam_pitru_marana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        242 - The Sun must be in the 6th, 8th or 12th; lord of the 8th must be in the 9th; 
            lord of the 12th in Lagna and the lord of the 6th in the 5th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L_house = p_to_h[const._ascendant_symbol]
    sun_in_6th_or_8th_or_12th = any(p_to_h[const.SUN_ID]==(L_house+h-1)%12 for h in [6,8,12] )
    if not sun_in_6th_or_8th_or_12th: return False
    if planet_positions is not None:
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, (L_house+const.HOUSE_6)%12)
        lord_of_12th = house.house_owner_from_planet_positions(planet_positions, (L_house+const.HOUSE_12)%12)
    else:
        lord_of_6th = house.house_owner(chart_1d, (L_house+const.HOUSE_6)%12)
        lord_of_12th = house.house_owner(chart_1d, (L_house+const.HOUSE_12)%12)
    lord_of_12th_in_lagna = (p_to_h[lord_of_12th] == L_house)
    if not lord_of_12th_in_lagna: return False
    lord_of_6th_in_5th = (p_to_h[lord_of_6th] == (L_house+const.HOUSE_5)%12)
    return lord_of_6th_in_5th
def dhatrutwa_yoga(chart_1d, natural_benefics=None):
    """
        243. The lord of the 9th should be exalted, and aspected by a benefic, 
        and the 9th house should be occupied by a benefic.
    """
    return _dhatrutwa_yoga_calculation(chart_1d=chart_1d, natural_benefics=natural_benefics)
def dhatrutwa_yoga_from_planet_positions(planet_positions, natural_benefics=None):
    """
        243. The lord of the 9th should be exalted, and aspected by a benefic, 
        and the 9th house should be occupied by a benefic.
    """
    return _dhatrutwa_yoga_calculation(planet_positions=planet_positions, natural_benefics=natural_benefics)
def dhatrutwa_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        243. The lord of the 9th should be exalted, and aspected by a benefic, 
        and the 9th house should be occupied by a benefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    nb, _ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _dhatrutwa_yoga_calculation(planet_positions=pp, natural_benefics=nb)
def _dhatrutwa_yoga_calculation(chart_1d=None, planet_positions=None,natural_benefics=None): 
    """
        243. The lord of the 9th should be exalted, and aspected by a benefic, 
        and the 9th house should be occupied by a benefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    L_house = p_to_h[const._ascendant_symbol]
    house_9th = (L_house+const.HOUSE_9)%12
    if planet_positions is not None:
        lord_of_9th = house.house_owner_from_planet_positions(planet_positions, house_9th)
    else:
        lord_of_9th = house.house_owner(chart_1d, house_9th)
    house_of_lord_of_9th = p_to_h[lord_of_9th]
    # A. Lord 9th is exalted
    lord_of_9th_exalted = const.house_strengths_of_planets[lord_of_9th][house_of_lord_of_9th] >= const._EXALTED_UCCHAM
    if not lord_of_9th_exalted: return False
    # B. Lord of 9th receives aspect from benefic
    _natural_benefics = _get_natural_benefics(chart_1d, natural_benefics)
    planets_aspecting_lord_of_9th = house.planets_aspecting_the_planet(chart_1d, lord_of_9th)
    lord_of_9th_aspected_by_benefic = any(bp in planets_aspecting_lord_of_9th for bp in _natural_benefics)
    if not lord_of_9th_aspected_by_benefic: return False
    # C. Benefic placed in 9th house
    benefic_in_9th_house = any(p_to_h[bp]==house_9th for bp in _natural_benefics)
    return benefic_in_9th_house
def apakeerthi_yoga(chart_rasi, chart_navamsa, natural_malefics=None):
    """
        244 - The 10th house must be occupied by the Sun and Saturn who should join malefic amsas 
        or be aspected by malefics.
    """
    return _apakeerthi_yoga_calculation(chart_rasi=chart_rasi,chart_navamsa=chart_navamsa,
                                        natural_malefics=natural_malefics)
def apakeerthi_yoga_from_planet_positions(planet_positions_rasi, planet_positions_navamsa, natural_malefics=None):
    """
        244 - The 10th house must be occupied by the Sun and Saturn who should join malefic amsas 
        or be aspected by malefics.
    """
    return _apakeerthi_yoga_calculation(planet_positions_rasi=planet_positions_rasi,
                                        planet_positions_navamsa=planet_positions_navamsa,
                                        natural_malefics=natural_malefics)
def apakeerthi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        244 - The 10th house must be occupied by the Sun and Saturn who should join malefic amsas 
        or be aspected by malefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp_nav = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _apakeerthi_yoga_calculation(planet_positions_rasi=pp,planet_positions_navamsa=pp_nav,natural_malefics=nm)
def _apakeerthi_yoga_calculation(chart_rasi=None, chart_navamsa=None, planet_positions_rasi=None,
                                 planet_positions_navamsa=None, natural_malefics=None): 
    """
        244 - The 10th house must be occupied by the Sun and Saturn who should join malefic amsas 
        or be aspected by malefics.
    """
    # Build charts if positions are given
    if planet_positions_rasi is not None:
        chart_rasi = utils.get_house_planet_list_from_planet_positions(planet_positions_rasi)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.navamsa_chart(planet_positions_rasi)[:const._pp_count_upto_ketu]
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    if chart_rasi is None or chart_navamsa is None: return False
    p_to_h_rasi = utils.get_planet_to_house_dict_from_chart(chart_rasi)
    L_house_rasi = p_to_h_rasi[const._ascendant_symbol]
    house_10th = (L_house_rasi + const.HOUSE_10) % 12

    sun_house = p_to_h_rasi[const.SUN_ID]
    saturn_house = p_to_h_rasi[const.SATURN_ID]
    sun_saturn_occupy_10th_house = (sun_house == house_10th and saturn_house == house_10th)
    if not sun_saturn_occupy_10th_house:
        return False
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    # ---- Clause: "... or be aspected by malefics" (in rāśi) ----
    # Any malefic aspecting the 10th affects both Sun & Saturn sitting there.
    malefics_aspecting_h10 = [
        p for p in house.planets_aspecting_the_raasi(chart_rasi, house_10th)
        if p in _natural_malefics
    ]
    if malefics_aspecting_h10:
        return True
    # ---- Clause: "join malefic amsas" via Navamsa (D9) ----
    # Only compute when navamsa is available
    p_to_h_navamsa = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    sun_house_navamsa = p_to_h_navamsa[const.SUN_ID]
    saturn_house_navamsa = p_to_h_navamsa[const.SATURN_ID]
    if planet_positions_navamsa is not None:
        sun_navamsa_lord = house.house_owner_from_planet_positions(planet_positions_navamsa, sun_house_navamsa)
        saturn_navamsa_lord = house.house_owner_from_planet_positions(planet_positions_navamsa, saturn_house_navamsa)
    else:
        sun_navamsa_lord = house.house_owner(chart_navamsa, sun_house_navamsa)
        saturn_navamsa_lord = house.house_owner(chart_navamsa, saturn_house_navamsa)
    # Conservative reading: both Sun and Saturn "join malefic aṁśas"
    sun_saturn_has_malefic_navamsa = (
        sun_navamsa_lord in _natural_malefics and 
        saturn_navamsa_lord in _natural_malefics
    )
    if sun_saturn_has_malefic_navamsa: return True
    # ---- Clause: "join malefic amsas" via D60 (Krūra Śaṣṭiāṁśa) ----
    # Only attempt if rasi positions are available (fixed order: 'L', 0..8)
    if planet_positions_rasi is None: return False
    sun_rasi_position = planet_positions_rasi[const.SUN_ID + 1][1]
    saturn_rasi_position = planet_positions_rasi[const.SATURN_ID + 1][1]
    sun_shastiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(sun_rasi_position[1], sun_rasi_position[0])
    saturn_shastiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(saturn_rasi_position[1], saturn_rasi_position[0])
    sun_saturn_have_kroora_rulers = (
        utils.is_kroora_shashtiamsa_ruler(sun_shastiamsa_ruler) and 
        utils.is_kroora_shashtiamsa_ruler(saturn_shastiamsa_ruler)
    )
    return sun_saturn_have_kroora_rulers
#### Arishta Yogas 
def galakarna_yoga(chart_1d,maandi_house=None):
    """
        264. The 3rd house must be occupied by Mandi and Rahu 
            or by Mars in the shashtiamsa of Preta Puriha (Cruel deities).
    """
    return _galakarna_yoga_calculation(chart_1d=chart_1d, maandi_house=maandi_house)
def galakarna_yoga_from_planet_positions(planet_positions,maandi_house=None):
    """
        264. The 3rd house must be occupied by Mandi and Rahu 
            or by Mars in the shashtiamsa of Preta Puriha (Cruel deities).
    """
    return _galakarna_yoga_calculation(planet_positions=planet_positions, maandi_house=maandi_house)
def galakarna_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        264. The 3rd house must be occupied by Mandi and Rahu 
            or by Mars in the shashtiamsa of Preta Puriha (Cruel deities).
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    maandi_house, _ = drik.dasavarga_from_long(g_lon_info)
    return _galakarna_yoga_calculation(planet_positions=pp, maandi_house=maandi_house)
def _galakarna_yoga_calculation(chart_1d=None, planet_positions=None,maandi_house=None):
    """
        264. The 3rd house must be occupied by Mandi and Rahu 
            or by Mars in the shashtiamsa of Preta Puriha (Cruel deities).
    """
    if maandi_house is None: return False
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_3rd = (house_of_lagna+const.HOUSE_3)%12
    rahu_maandi_in_3rd_house = ( p_to_h[const.RAHU_ID]==house_3rd and maandi_house==house_3rd)
    if planet_positions is None:
        return rahu_maandi_in_3rd_house
    mars_in_3rd_house = (p_to_h[const.MARS_ID]==house_3rd)
    mars_rasi_position = planet_positions[const.MARS_ID + 1][1] 
    mars_shastiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(mars_rasi_position[1], mars_rasi_position[0])
    return mars_in_3rd_house and utils.is_cruel_shashtiamsa_ruler(mars_shastiamsa_ruler)
def vrana_yoga(chart_1d,natural_malefics=None):
    """
        265 - The 6th lord, being a malefic, should occupy the Lagna, 8th or 1Oth. 
            Impacted organs depending on 6th lord: 
                Sun- Spleen,heart. 
                Moon-Oesophagus, alimentary canal. 
                Mars-Genitals, left cerebral hemisphere, red colouring matter in blood,rectum. 
                Mercury- Nerves, right cerebral hemisphere, cerebro-spinal-system, bronchial tubes, ears, tongue. 
                Jupiter- Liver, supra-renals. 
                Venus- Throat, kidneys, uterus, ovaries. 
                Saturn- Teeth, skin, vagus nerve. 
                Rahu- Pituitary body. 
                Kethu- Pineal glands.
    """
    return _vrana_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def vrana_yoga_from_planet_positions(planet_positions,natural_malefics=None):
    """
        265 - The 6th lord, being a malefic, should occupy the Lagna, 8th or 1Oth. 
            Impacted organs depending on 6th lord: 
                Sun- Spleen,heart. 
                Moon-Oesophagus, alimentary canal. 
                Mars-Genitals, left cerebral hemisphere, red colouring matter in blood,rectum. 
                Mercury- Nerves, right cerebral hemisphere, cerebro-spinal-system, bronchial tubes, ears, tongue. 
                Jupiter- Liver, supra-renals. 
                Venus- Throat, kidneys, uterus, ovaries. 
                Saturn- Teeth, skin, vagus nerve. 
                Rahu- Pituitary body. 
                Kethu- Pineal glands.
    """
    return _vrana_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def vrana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        265 - The 6th lord, being a malefic, should occupy the Lagna, 8th or 1Oth. 
            Impacted organs depending on 6th lord: 
                Sun- Spleen,heart. 
                Moon-Oesophagus, alimentary canal. 
                Mars-Genitals, left cerebral hemisphere, red colouring matter in blood,rectum. 
                Mercury- Nerves, right cerebral hemisphere, cerebro-spinal-system, bronchial tubes, ears, tongue. 
                Jupiter- Liver, supra-renals. 
                Venus- Throat, kidneys, uterus, ovaries. 
                Saturn- Teeth, skin, vagus nerve. 
                Rahu- Pituitary body. 
                Kethu- Pineal glands.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _vrana_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _vrana_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        265 - The 6th lord, being a malefic, should occupy the Lagna, 8th or 1Oth. 
            Impacted organs depending on 6th lord: 
                Sun- Spleen,heart. 
                Moon-Oesophagus, alimentary canal. 
                Mars-Genitals, left cerebral hemisphere, red colouring matter in blood,rectum. 
                Mercury- Nerves, right cerebral hemisphere, cerebro-spinal-system, bronchial tubes, ears, tongue. 
                Jupiter- Liver, supra-renals. 
                Venus- Throat, kidneys, uterus, ovaries. 
                Saturn- Teeth, skin, vagus nerve. 
                Rahu- Pituitary body. 
                Kethu- Pineal glands.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_6th = (house_of_lagna+const.HOUSE_6)%12
    if planet_positions is not None:
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, house_6th)
    else:
        lord_of_6th = house.house_owner(chart_1d, house_6th)
    house_of_lord_of_6th = p_to_h[lord_of_6th]
    _natural_malefics = natural_malefics if natural_malefics else const.natural_malefics
    lord_6th_is_malefic = lord_of_6th in _natural_malefics 
    if not lord_6th_is_malefic: return False
    # 6th lord should occupy the Lagna, 8th or 1Oth.
    return house_of_lord_of_6th in [house_of_lagna,(house_of_lagna+const.HOUSE_8)%12,(house_of_lagna+const.HOUSE_10)%12]
def sisnavyadhi_yoga(chart_1d):
    """
        266 - Mercury should join Lagna in conjunction with the lords of the 6th and 8th
    """
    return _sisnavyadhi_yoga_calculation(chart_1d=chart_1d)
def sisnavyadhi_yoga_from_planet_positions(planet_positions):
    """
        266 - Mercury should join Lagna in conjunction with the lords of the 6th and 8th
    """
    return _sisnavyadhi_yoga_calculation(planet_positions=planet_positions)
def sisnavyadhi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        266 - Mercury should join Lagna in conjunction with the lords of the 6th and 8th
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sisnavyadhi_yoga_calculation(planet_positions=pp)
def _sisnavyadhi_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        266 - Mercury should join Lagna in conjunction with the lords of the 6th and 8th
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    house_of_lagna = p_to_h[const._ascendant_symbol]
    house_6th = (house_of_lagna+const.HOUSE_6)%12
    house_8th = (house_of_lagna+const.HOUSE_8)%12
    if planet_positions is not None:
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, house_6th)
        lord_of_8th = house.house_owner_from_planet_positions(planet_positions, house_8th)
    else:
        lord_of_6th = house.house_owner(chart_1d, house_6th)
        lord_of_8th = house.house_owner(chart_1d, house_8th)
    house_of_mercury = p_to_h[const.MERCURY_ID]
    house_of_lord_of_6th = p_to_h[lord_of_6th]
    house_of_lord_of_8th = p_to_h[lord_of_8th]
    return ( house_of_mercury==house_of_lagna and house_of_lord_of_6th==house_of_lagna and 
             house_of_lord_of_8th==house_of_lagna)
def kushtaroga_yoga(chart_1d):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house.
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    return _kushtaroga_yoga_calculation(chart_1d=chart_1d)
def kushtaroga_yoga_from_planet_positions(planet_positions):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house.
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    return _kushtaroga_yoga_calculation(planet_positions=planet_positions)
def _kushtaroga_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house.
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    if _kushtaroga_yoga_268_calculation(chart_1d, planet_positions): return True
    return _kushtaroga_yoga_269_calculation(chart_1d, planet_positions)
def kushtaroga_yoga_268(chart_1d):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house .
    """
    return _kushtaroga_yoga_268_calculation(chart_1d=chart_1d)
def kushtaroga_yoga_268_from_planet_positions(planet_positions):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house .
    """
    return _kushtaroga_yoga_268_calculation(planet_positions=planet_positions)
def kushtaroga_yoga_268_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house .
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kushtaroga_yoga_268_calculation(planet_positions=pp)
def _kushtaroga_yoga_268_calculation(chart_1d=None, planet_positions=None):
    """
        268 - The lord of Lagna must join Mars and Mercury in the 4th or 12th house .
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_4th = (lagna_house+const.HOUSE_4)%12
    house_12th = (lagna_house+const.HOUSE_12)%12
    mars_house = p_to_h[const.MARS_ID]; mercury_house = p_to_h[const.MERCURY_ID]
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, lagna_house)
    else:
        lagna_lord = house.house_owner(chart_1d, lagna_house)
    house_of_lagna_lord = p_to_h[lagna_lord]
    lagna_lord_mars_mercury_in_4th_house = (mars_house==house_4th and 
                                            mercury_house==house_4th and 
                                            house_of_lagna_lord==house_4th)
    if lagna_lord_mars_mercury_in_4th_house: return True
    lagna_lord_mars_mercury_in_12th_house = (mars_house==house_12th and 
                                            mercury_house==house_12th and 
                                            house_of_lagna_lord==house_12th)
    return lagna_lord_mars_mercury_in_12th_house
def kushtaroga_yoga_269(chart_1d):
    """
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    return _kushtaroga_yoga_269_calculation(chart_1d=chart_1d)
def kushtaroga_yoga_269_from_planet_positions(planet_positions):
    """
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    return _kushtaroga_yoga_269_calculation(planet_positions=planet_positions)
def kushtaroga_yoga_269_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _kushtaroga_yoga_269_calculation(planet_positions=pp)
def _kushtaroga_yoga_269_calculation(chart_1d=None, planet_positions=None):
    """
        269 - Jupiter in conjunction with Saturn and the Moon should occupy the 6th house.    
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_6th = (lagna_house+const.HOUSE_6)%12
    jupiter_house = p_to_h[const.JUPITER_ID]
    moon_house = p_to_h[const.MOON_ID]; saturn_house = p_to_h[const.SATURN_ID]
    return (moon_house==house_6th and saturn_house==house_6th and jupiter_house==house_6th)
def kshayaroga_yoga(chart_1d, maandi_house=None,skip_other_variations=True):
    """
        270 - Rahu in the 6th, Mandi in a kendra from Lagna, and the lord of Lagna in the 8th gives rise to this yoga.
    """
    return _kshayaroga_yoga_calculation(
        chart_1d=chart_1d,
        maandi_house=maandi_house,
        skip_other_variations=True
    )
def kshayaroga_yoga_from_planet_positions(planet_positions, maandi_house=None,skip_other_variations=True):
    """
        270 - Rahu in the 6th, Mandi in a kendra from Lagna, and the lord of Lagna in the 8th gives rise to this yoga.
    """
    return _kshayaroga_yoga_calculation(
        planet_positions=planet_positions,
        maandi_house=maandi_house,
        skip_other_variations=skip_other_variations
    )
def kshayaroga_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        270 - Rahu in the 6th, Mandi in a kendra from Lagna, and the lord of Lagna in the 8th gives rise to this yoga.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    maandi_house, _ = drik.dasavarga_from_long(g_lon_info)
    return _kshayaroga_yoga_calculation(
        planet_positions=pp,
        maandi_house=maandi_house,
        skip_other_variations=True
    )
def _kshayaroga_yoga_calculation(chart_1d=None, planet_positions=None, maandi_house=None,
                                 skip_other_variations=True):
    """
        270 - Rahu in the 6th, Mandi in a kendra from Lagna, and the lord of Lagna in the 8th gives rise to this yoga.
    """
    if maandi_house is None and not skip_other_variations: return False
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_6th = (lagna_house+const.HOUSE_6)%12
    house_8th = (lagna_house+const.HOUSE_8)%12
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, lagna_house)
    else:
        lagna_lord = house.house_owner(chart_1d, lagna_house)
    house_of_lagna_lord = p_to_h[lagna_lord]
    kendras_from_lagna = quadrants_of_the_house(lagna_house)
    if skip_other_variations: return ( p_to_h[const.RAHU_ID] == house_6th and maandi_house in kendras_from_lagna and 
             house_of_lagna_lord == house_8th )
    # Rahu in 8th Maandi in kendra and Lord of lagna in 8th
    variation_1 = ( p_to_h[const.RAHU_ID] == house_8th and 
                    (maandi_house is not None and maandi_house in kendras_from_lagna) and 
             house_of_lagna_lord == house_8th )
    if variation_1: return True
    """ TODO: Implement the below after reviewing/fixing planet aspect functions """
    # Me/Ma in 6th aspected by Ve/Mo
    # Ma/Sa in 6th aspected by Su/Ra
    return False
def bhandhana_yoga(chart_1d):
    """
        271 - The lord of the Lagna and the 6th conjoin with Saturn or Rahu or Kethu, in a kendra or thrikona  
        the above yoga is given rise to.
    """
    return _bhandhana_yoga_calculation(chart_1d=chart_1d)
def bhandhana_yoga_from_planet_positions(planet_positions):
    """
        271 - The lord of the Lagna and the 6th conjoin with Saturn or Rahu or Kethu, in a kendra or thrikona  
        the above yoga is given rise to.
    """
    return _bhandhana_yoga_calculation(planet_positions=planet_positions)
def bhandhana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        271 - The lord of the Lagna and the 6th conjoin with Saturn or Rahu or Kethu, in a kendra or thrikona  
        the above yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _bhandhana_yoga_calculation(planet_positions=pp)
def _bhandhana_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        271 - The lord of the Lagna and the 6th conjoin with Saturn or Rahu or Kethu, in a kendra or thrikona  
        the above yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_6th = (lagna_house+const.HOUSE_6)%12
    if planet_positions is not None:
        lagna_lord = house.house_owner_from_planet_positions(planet_positions, lagna_house)
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, house_6th)
    else:
        lagna_lord = house.house_owner(chart_1d, lagna_house)
        lord_of_6th = house.house_owner(chart_1d, house_6th)
    house_of_lagna_lord = p_to_h[lagna_lord]
    house_of_6th_lord = p_to_h[lord_of_6th]
    if (house_of_lagna_lord != house_of_6th_lord): return False
    favorable_houses = set(quadrants_of_the_house(lagna_house)) | set(trines_of_the_house(lagna_house))
    for planet in [const.SATURN_ID, const.RAHU_ID, const.KETU_ID]:
        _yoga_check = ( house_of_lagna_lord == p_to_h[planet] and 
                                house_of_lagna_lord == house_of_6th_lord and
                                house_of_lagna_lord in favorable_houses )
        if _yoga_check: return True
    return False
def karascheda_yoga(chart_1d):
    """
        272 - Saturn and Jupiter should be in 9th and 3rd houses.
    """
    return _karascheda_yoga_calculation(chart_1d=chart_1d)
def karascheda_yoga_from_planet_positions(planet_positions):
    """
        272 - Saturn and Jupiter should be in 9th and 3rd houses.
    """
    return _karascheda_yoga_calculation(planet_positions=planet_positions)
def karascheda_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        272 - Saturn and Jupiter should be in 9th and 3rd houses.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _karascheda_yoga_calculation(planet_positions=pp)
def _karascheda_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        272 - Saturn and Jupiter should be in 9th and 3rd houses.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    return ( p_to_h[const.SATURN_ID]==(lagna_house+const.HOUSE_9)%12 and p_to_h[const.JUPITER_ID]==(lagna_house+const.HOUSE_3)%12)
def sirachcheda_yoga(chart_1d, planets_must_share_same_sashtiamsa=False):
    """ 
        273 - The lord of the 6th must be in conjunction with Venus while the Sun or Saturn should 
        join Rahu in a cruel shashtiamsa.
        Use planets_must_share_same_sashtiamsa=True - if you want planets have SAME cruel sashtiamsa
    """
    # Convert chart to planet_positions if your codebase provides such a helper.
    # Replace the call below with the appropriate utility in your project if needed.
    return _sirachcheda_yoga_calculations(
        chart_1d=chart_1d,
        planets_must_share_same_sashtiamsa=planets_must_share_same_sashtiamsa
    )
def sirachcheda_yoga_from_planet_positions(planet_positions, planets_must_share_same_sashtiamsa=False):
    """ 
        273 - The lord of the 6th must be in conjunction with Venus while the Sun or Saturn should 
        join Rahu in a cruel shashtiamsa.
        Use planets_must_share_same_sashtiamsa=True - if you want planets have SAME cruel sashtiamsa
    """
    return _sirachcheda_yoga_calculations(
        planet_positions=planet_positions,
        planets_must_share_same_sashtiamsa=planets_must_share_same_sashtiamsa
    )
def sirachcheda_yoga_from_jd_place(jd, place, divisional_chart_factor=1, planets_must_share_same_sashtiamsa=False):
    """ 
        273 - The lord of the 6th must be in conjunction with Venus while the Sun or Saturn should 
        join Rahu in a cruel shashtiamsa.
        Use planets_must_share_same_sashtiamsa=True - if you want planets have SAME cruel sashtiamsa
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _sirachcheda_yoga_calculations(
        planet_positions=pp,
        planets_must_share_same_sashtiamsa=planets_must_share_same_sashtiamsa
    )
def _sirachcheda_yoga_calculations(planet_positions,planets_must_share_same_sashtiamsa=False):
    """ 
        273 - The lord of the 6th must be in conjunction with Venus while the Sun or Saturn should 
        join Rahu in a cruel shashtiamsa.
        Use planets_must_share_same_sashtiamsa=True - if you want planets have SAME cruel sashtiamsa
    """
    if planet_positions is None: return False
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    lagna_house = p_to_h[const._ascendant_symbol]
    house_6th = (lagna_house+const.HOUSE_6)%12
    lord_of_6th = house.house_owner_from_planet_positions(planet_positions, house_6th)
    venus_with_lord_of_6th = ( p_to_h[const.VENUS_ID]==p_to_h[lord_of_6th])
    if not venus_with_lord_of_6th: return False
    sun_with_rahu = (p_to_h[const.SUN_ID]==p_to_h[const.RAHU_ID])
    saturn_with_rahu = (p_to_h[const.SATURN_ID]==p_to_h[const.RAHU_ID])
    if not (sun_with_rahu or saturn_with_rahu): return False
    rahu_pos = planet_positions[const.RAHU_ID+1][1]
    rahu_sashtiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(rahu_pos[1], rahu_pos[0])
    if rahu_sashtiamsa_ruler not in const.shashti_amsa_rulers_kroora: return False
    if sun_with_rahu:
        sun_pos = planet_positions[const.SUN_ID+1][1]
        sun_sashtiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(sun_pos[1], sun_pos[0])
        sun_in_cruel_sashtiamsa = sun_sashtiamsa_ruler in const.shashti_amsa_rulers_kroora
        sun_rahu_has_same_sashtiamsa = (sun_sashtiamsa_ruler==rahu_sashtiamsa_ruler)
    if saturn_with_rahu:
        saturn_pos = planet_positions[const.SATURN_ID+1][1]
        saturn_sashtiamsa_ruler = utils.get_amsa_ruler_from_planet_longitude(saturn_pos[1], saturn_pos[0])
        saturn_in_cruel_sashtiamsa = saturn_sashtiamsa_ruler in const.shashti_amsa_rulers_kroora
        saturn_rahu_has_same_sashtiamsa = (saturn_sashtiamsa_ruler==rahu_sashtiamsa_ruler)
    if planets_must_share_same_sashtiamsa:
        if sun_with_rahu and saturn_with_rahu:
            return ( (sun_in_cruel_sashtiamsa and sun_rahu_has_same_sashtiamsa) and 
                      (saturn_in_cruel_sashtiamsa and saturn_rahu_has_same_sashtiamsa) )
        elif sun_with_rahu: return (sun_in_cruel_sashtiamsa and sun_rahu_has_same_sashtiamsa)
        else: return (saturn_in_cruel_sashtiamsa and saturn_rahu_has_same_sashtiamsa)
    else:
        if sun_with_rahu and saturn_with_rahu: return sun_in_cruel_sashtiamsa and saturn_in_cruel_sashtiamsa
        elif sun_with_rahu: return sun_in_cruel_sashtiamsa
        else: return saturn_in_cruel_sashtiamsa
    return False
def durmarana_yoga(chart_1d, maandi_house=None):
    """
        274 - The Moon being aspected by lord of Lagna should occupy the 6th, 8th or 12th in 
            association/conjunction with Saturn, Mandi or Rahu.
    """
    return _dhurmarana_yoga_calculation(chart_1d=chart_1d, maandi_house=maandi_house)
def durmarana_yoga_from_planet_positions(planet_positions, maandi_house=None):
    """
        274 - The Moon being aspected by lord of Lagna should occupy the 6th, 8th or 12th in 
            association/conjunction with Saturn, Mandi or Rahu.
    """
    return _dhurmarana_yoga_calculation(planet_positions=planet_positions, maandi_house=maandi_house)
def dhurmarana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        274 - The Moon being aspected by lord of Lagna should occupy the 6th, 8th or 12th in 
            association/conjunction with Saturn, Mandi or Rahu.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    maandi_house, _ = drik.dasavarga_from_long(g_lon_info)
    return _dhurmarana_yoga_calculation(planet_positions=pp, maandi_house=maandi_house)
def _dhurmarana_yoga_calculation(chart_1d=None, planet_positions=None,maandi_house=None,
                                 check_other_variations=False):
    """
        274 - The Moon being aspected by lord of Lagna should occupy the 6th, 8th or 12th in 
            association/conjunction with Saturn, Mandi or Rahu.
            use check_other_variations=True for other combinations given by BV Raman
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if chart_1d is None: return False
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    lagna_house = p_to_h[const._ascendant_symbol]
    moon_house = p_to_h[const.MOON_ID]; saturn_house = p_to_h[const.SATURN_ID]
    rahu_house = p_to_h[const.RAHU_ID]
    dusthanas = house.dushthanas_of_the_raasi(lagna_house)
    if planet_positions is not None:
        lord_of_lagna = house.house_owner_from_planet_positions(planet_positions, lagna_house)
    else:
        lord_of_lagna = house.house_owner(chart_1d, lagna_house)
    planets_aspecting_moon = house.planets_aspecting_the_planet(chart_1d, const.MOON_ID)
    lord_of_lagna_aspects_moon = lord_of_lagna in planets_aspecting_moon
    if not lord_of_lagna_aspects_moon: return False
    moon_in_dusthanas = moon_house in dusthanas
    if not moon_in_dusthanas: return False
    moon_in_afflicted_houses = ( moon_house==saturn_house or moon_house==rahu_house or 
                                 (moon_house == maandi_house) if maandi_house is not None else False
                               )
    if moon_in_afflicted_houses: return True
    if check_other_variations:
        # (a) The conjunction of the Sun, Saturn and Rahu in the 7th-death by poisonous reptiles.
        house_7th = (lagna_house+const.HOUSE_7)%12
        variation_1= (p_to_h[const.SUN_ID]==house_7th and saturn_house==house_7th and rahu_house==house_7th)
        if variation_1: return True
        # (b) Mars in Capricorn or Aquarius and Mercury in a house of Jupiter-will be killdd by a tiger.
        variation_2 = ( (p_to_h[const.MARS_ID] in [const.AQUARIUS, const.CAPRICORN]) and
                        (p_to_h[const.MERCURY_ID] in [const.SAGITTARIUS, const.PISCES]) )
        if variation_2: return True
        # (c) Mars in the 9th and Saturn, Rahu and the Sun in association-deathby weapons.
        variation_3 = ( (p_to_h[const.MARS_ID]==(lagna_house+const.HOUSE_9)%12) and 
                        (saturn_house==rahu_house and p_to_h[const.SUN_ID]==rahu_house)
                        )
        if variation_3: return True
    return False
def yuddha_marana_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        275 - Mars, being lord of the 6th or 8th, should conjoin the 3rd lord and Rahu, Saturn or 
        Maandi in cruel shashti-amsas.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    g_lon_info = charts.get_chart_element_longitude(jd, place, divisional_chart_factor=divisional_chart_factor,
                                                    dhasa_starting_planet='Md')
    maandi_pos = drik.dasavarga_from_long(g_lon_info)
    shashtiamsa_maandi = utils.get_amsa_ruler_from_planet_longitude(maandi_pos[1], maandi_pos[0])
    shashtiamsa_rahu = utils.get_amsa_ruler_from_planet_longitude(pp[const.RAHU_ID+1][1][1], pp[const.RAHU_ID+1][1][0])
    shashtiamsa_saturn = utils.get_amsa_ruler_from_planet_longitude(pp[const.SATURN_ID+1][1][1], pp[const.SATURN_ID+1][1][0])
    return _yuddha_marana_yoga_calculation(planet_positions=pp, shashtiamsa_rahu=shashtiamsa_rahu,
                                           shashtiamsa_saturn=shashtiamsa_saturn, 
                                           shashtiamsa_maandi=shashtiamsa_maandi,maandi_house=maandi_pos[0])
def yuddha_marana_yoga_from_planet_positions(planet_positions, shashtiamsa_rahu=None, shashtiamsa_saturn=None,
                                             shashtiamsa_maandi=None,maandi_house=None):
    """
        275 - Mars, being lord of the 6th or 8th, should conjoin the 3rd lord and Rahu, Saturn or 
        Maandi in cruel shashti-amsas.
    """
    return _yuddha_marana_yoga_calculation(planet_positions=planet_positions, shashtiamsa_rahu=shashtiamsa_rahu,
                                           shashtiamsa_saturn=shashtiamsa_saturn, shashtiamsa_maandi=shashtiamsa_maandi,
                                           maandi_house=maandi_house)
def yuddha_marana_yoga(chart_1d, shashtiamsa_rahu=None, shashtiamsa_saturn=None,shashtiamsa_maandi=None,
                       maandi_house=None):
    """
        275 - Mars, being lord of the 6th or 8th, should conjoin the 3rd lord and Rahu, Saturn or 
        Maandi in cruel shashti-amsas.
    """
    return _yuddha_marana_yoga_calculation(chart_1d=chart_1d, shashtiamsa_rahu=shashtiamsa_rahu,
                                           shashtiamsa_saturn=shashtiamsa_saturn, 
                                           shashtiamsa_maandi=shashtiamsa_maandi,maandi_house=maandi_house)
def _yuddha_marana_yoga_calculation(chart_1d=None, planet_positions=None,shashtiamsa_rahu=None,
                                    shashtiamsa_saturn=None,shashtiamsa_maandi=None,maandi_house=None):
    """
        275 - Mars, being lord of the 6th or 8th, should conjoin the 3rd lord and Rahu, Saturn or 
        Mandi in cruel amsas.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d) 
    else: return False
    # Lagna has to be in one of Mesha, Mithuna, Kanya, Vrichiga if Mars has to be 6th or 8th lord
    lagna_house = p_to_h[const._ascendant_symbol]; mars_house = p_to_h[const.MARS_ID]
    house_3rd = (lagna_house+const.HOUSE_3)%12
    lagna_in_favorable_houses = lagna_house in [const.MESHAM, const.MITHUNAM, const.KANNI, const.VIRUCHIGAM]
    if not lagna_in_favorable_houses: return False
    if planet_positions is not None:
        lord_of_3rd = house.house_owner_from_planet_positions(planet_positions, house_3rd)
    else:
        lord_of_3rd = house.house_owner(chart_1d, house_3rd)
    mars_conjoins_3rd_lord = (mars_house==p_to_h[lord_of_3rd])
    if not mars_conjoins_3rd_lord: return False
    if (shashtiamsa_maandi is not None and utils.is_kroora_shashtiamsa_ruler(shashtiamsa_maandi) and 
        (mars_house == maandi_house) if maandi_house is not None else False
        ): return True
    if (shashtiamsa_saturn is not None and utils.is_kroora_shashtiamsa_ruler(shashtiamsa_saturn) and 
        (mars_house==p_to_h[const.SATURN_ID])
        ): return True
    if (shashtiamsa_rahu is not None and utils.is_kroora_shashtiamsa_ruler(shashtiamsa_rahu) and
        (mars_house==p_to_h[const.RAHU_ID])
        ): return True
    if planet_positions is not None:
        return _yuddha_marana_yoga_variation(planet_positions)
    return False
def _yuddha_marana_yoga_variation(planet_positions):
    # --- Possible variation (B.V. Raman): "lord of the drekkana occupied by Saturn" ---
    chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    # Build D3 & D9 from the SAME rāśi positions you already have
    planet_positions_d3 = charts.drekkana_chart(planet_positions)[:const._pp_count_upto_ketu]
    planet_positions_d9 = charts.navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
    # Saturn's D3 sign is the drekkana Saturn occupies
    d3_sign = planet_positions_d3[const.SATURN_ID + 1][1][0]
    # Drekkana-lord = sign lord of Saturn’s D3 sign
    drekkana_lord = house.house_owner_from_planet_positions(planet_positions_d3, d3_sign)
    # (A) "in a Rāśi of Mars" (Aries or Scorpio) in D1
    drek_lord_rasi_sign = planet_positions[drekkana_lord + 1][1][0]
    in_mars_rasi = drek_lord_rasi_sign in (const.MESHAM, const.VIRUCHIGAM)  # Aries/Scorpio
    # (B) "aspected by Mars" (graha-dṛṣṭi) in D1
    drek_lord_aspected_by_mars = False
    if chart_1d is not None:
        aspecting_planets = house.planets_aspecting_the_planet(chart_1d, drekkana_lord)
        drek_lord_aspected_by_mars = (const.MARS_ID in aspecting_planets)
    # (C) "in a Navāṁśa of Mars" (Aries or Scorpio) in D9
    drek_lord_navamsa_sign = planet_positions_d9[drekkana_lord + 1][1][0]
    in_mars_navamsa = drek_lord_navamsa_sign in (const.MESHAM, const.VIRUCHIGAM)
    return in_mars_rasi or drek_lord_aspected_by_mars or in_mars_navamsa
def pittharoga_yoga(chart_1d, natural_malefics=None):
    """ 
        279 - The 6th house must be occupied by the Sun in conjunction with a malefic and further
            aspected by another malefic.
    """
    return _pittharoga_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def pittharoga_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """ 
        279 - The 6th house must be occupied by the Sun in conjunction with a malefic and further
            aspected by another malefic.
    """
    return _pittharoga_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def pittharoga_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        279 - The 6th house must be occupied by the Sun in conjunction with a malefic and further
            aspected by another malefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _pittharoga_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _pittharoga_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """ 
        279 - The 6th house must be occupied by the Sun in conjunction with a malefic and further
            aspected by another malefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d) 
    else: return False
    _natural_malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    # remove sun from _natural_malefics if it exists
    _natural_malefics = [mp for mp in _natural_malefics if mp != const.SUN_ID]
    lagna_house = p_to_h[const._ascendant_symbol]
    house_6th = (lagna_house+const.HOUSE_6)%12
    sun_house = p_to_h[const.SUN_ID]
    if (sun_house != house_6th): return False
    malefics_with_sun = [mp for mp in _natural_malefics if p_to_h[mp]==sun_house]
    if len(malefics_with_sun)==0: return False
    planets_aspecting_sun = house.planets_aspecting_the_planet(chart_1d, const.SUN_ID)
    return any(mp in planets_aspecting_sun and mp not in malefics_with_sun for mp in _natural_malefics)
def putrakalatraheena_yoga(chart_1d, natural_malefics=None):
    """
        281 - When the waning Moon is in the 5th and malefics occupy the 12th, 7th and Lagna, the yoga is formed.
        The person will be 'deprived of his family and children.'
    """
    return _putrakalatraheena_yoga_calculation(
        chart_1d=chart_1d,
        natural_malefics=natural_malefics,
    )
def putrakalatraheena_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """
        281 - When the waning Moon is in the 5th and malefics occupy the 12th, 7th and Lagna, the yoga is formed.
        The person will be 'deprived of his family and children.'
    """
    return _putrakalatraheena_yoga_calculation(
        planet_positions=planet_positions,
        natural_malefics=natural_malefics,
    )
def putrakalatraheena_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        281 - When the waning Moon is in the 5th and malefics occupy the 12th, 7th and Lagna, the yoga is formed.
        The person will be 'deprived of his family and children.'
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _putrakalatraheena_yoga_calculation(
        planet_positions=pp,
        natural_malefics=nm,
    )
def _putrakalatraheena_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        281 - When the waning Moon is in the 5th and malefics occupy the 12th, 7th and Lagna,
        the yoga is formed.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    _natural_malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    # Check moon is in malefic - Waning moon
    if const.MOON_ID not in _natural_malefics: return False
    # 1) Moon must be in the 5th from Lagna
    lagna_house = p_to_h[const._ascendant_symbol]
    house_5th = (lagna_house + const.HOUSE_5) % 12
    moon_house = p_to_h[const.MOON_ID]
    if moon_house != house_5th: return False
    # 2) Malefics must occupy Lagna, 7th and 12th (at least one malefic in each)
    house_7th = (lagna_house + const.HOUSE_7) % 12
    house_12th = (lagna_house + const.HOUSE_12) % 12
    lagna_has_malefic   = any(p_to_h.get(mp) == lagna_house for mp in _natural_malefics)
    seventh_has_malefic = any(p_to_h.get(mp) == house_7th   for mp in _natural_malefics)
    twelfth_has_malefic = any(p_to_h.get(mp) == house_12th  for mp in _natural_malefics)
    return lagna_has_malefic and seventh_has_malefic and twelfth_has_malefic
def bharyasahavyabhichara_yoga(chart_1d, natural_malefics=None):
    """
        282 - Venus, Saturn and Mars must join the Moon in the 7th house.
             Variation: 7th lord in conjunction with Venus, aspected by Saturn;
                        7th house aspected by Saturn and Mars;
                        Venus and Moon afflicted by malefics.
    """
    return _bharyasahavyabhichara_yoga_calculation(chart_1d=chart_1d,natural_malefics=natural_malefics)
def bharyasahavyabhichara_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """
        282 - Venus, Saturn and Mars must join the Moon in the 7th house.
             Variation: 7th lord in conjunction with Venus, aspected by Saturn;
                        7th house aspected by Saturn and Mars;
                        Venus and Moon afflicted by malefics.
    """
    return _bharyasahavyabhichara_yoga_calculation(planet_positions=planet_positions,natural_malefics=natural_malefics)
def bharyasahavyabhichara_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        282 - Venus, Saturn and Mars must join the Moon in the 7th house.
             Variation: 7th lord in conjunction with Venus, aspected by Saturn;
                        7th house aspected by Saturn and Mars;
                        Venus and Moon afflicted by malefics.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _bharyasahavyabhichara_yoga_calculation(planet_positions=pp,natural_malefics=nm)
def _bharyasahavyabhichara_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        282 - Bharyasahavyabhichara Yoga
        Definition: Venus, Saturn and Mars must join the Moon in the 7th house.
        Variation: 7th lord is in conjunction with Venus, aspected by Saturn; 7th house aspected by Saturn and Mars;
                   Venus and Moon are afflicted by malefics (from natural_malefics).
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False

    _natural_malefics = natural_malefics if natural_malefics is not None else const.natural_malefics

    lagna_house = p_to_h[const._ascendant_symbol]
    house_7th = (lagna_house + const.HOUSE_7) % 12

    moon_house   = p_to_h[const.MOON_ID]
    venus_house  = p_to_h[const.VENUS_ID]
    saturn_house = p_to_h[const.SATURN_ID]
    mars_house   = p_to_h[const.MARS_ID]

    base_ok = (
        moon_house   == house_7th and
        venus_house  == house_7th and
        saturn_house == house_7th and
        mars_house   == house_7th
    )
    if base_ok: return True

    if planet_positions is not None:
        lord_7 = house.house_owner_from_planet_positions(planet_positions, house_7th)
    else:
        lord_7 = house.house_owner(chart_1d, house_7th)

    asp_planet = lambda pid: (house.planets_aspecting_the_planet(chart_1d, pid) or [])
    asp_house  = lambda hid: (house.planets_aspecting_the_raasi(chart_1d, hid) or [])

    a_conj = (p_to_h[lord_7] == venus_house)
    b_aspected = (const.SATURN_ID in asp_planet(lord_7))
    aspecting_7th = set(asp_house(house_7th))
    c_house_aspected = (const.SATURN_ID in aspecting_7th) and (const.MARS_ID in aspecting_7th)
    venus_afflicted = any(p_to_h.get(m) == venus_house for m in _natural_malefics) or \
                      any(m in asp_planet(const.VENUS_ID) for m in _natural_malefics)
    moon_afflicted  = any(p_to_h.get(m) == moon_house  for m in _natural_malefics) or \
                      any(m in asp_planet(const.MOON_ID)  for m in _natural_malefics)
    variation_ok = a_conj and (b_aspected or c_house_aspected) and (venus_afflicted or moon_afflicted)
    return variation_ok
def vamsacheda_yoga(chart_1d, natural_malefics=None):
    """
        283 - The 10th, 7th and 4th must be occupied by the Moon, Venus and malefics respectively.
              Variation: Moon and Venus in the 7th and malefics in the 4th and 10th.
    """
    return _vamsacheda_yoga_calculation(chart_1d=chart_1d,natural_malefics=natural_malefics)
def vamsacheda_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """
        283 - The 10th, 7th and 4th must be occupied by the Moon, Venus and malefics respectively.
              Variation: Moon and Venus in the 7th and malefics in the 4th and 10th.
    """
    return _vamsacheda_yoga_calculation(planet_positions=planet_positions,natural_malefics=natural_malefics)
def vamsacheda_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        283 - The 10th, 7th and 4th must be occupied by the Moon, Venus and malefics respectively.
              Variation: Moon and Venus in the 7th and malefics in the 4th and 10th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _vamsacheda_yoga_calculation(planet_positions=pp,natural_malefics=nm)
def _vamsacheda_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        283 - The 10th, 7th and 4th must be occupied by the Moon, Venus and malefics respectively.
        Variation: Moon and Venus in the 7th and malefics in the 4th and 10th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False

    _natural_malefics = natural_malefics if natural_malefics is not None else const.natural_malefics

    lagna_house = p_to_h[const._ascendant_symbol]
    house_10th  = (lagna_house + const.HOUSE_10) % 12
    house_7th   = (lagna_house + const.HOUSE_7)  % 12
    house_4th   = (lagna_house + const.HOUSE_4)  % 12

    moon_house  = p_to_h[const.MOON_ID]
    venus_house = p_to_h[const.VENUS_ID]

    malefic_in_4th = any(p_to_h.get(m) == house_4th for m in _natural_malefics)
    malefic_in_10th = any(p_to_h.get(m) == house_10th for m in _natural_malefics)

    base_ok = (moon_house == house_10th) and (venus_house == house_7th) and malefic_in_4th
    if base_ok:
        return True

    variation_ok = (moon_house == house_7th) and (venus_house == house_7th) and malefic_in_4th and malefic_in_10th
    return variation_ok

def guhyaroga_yoga(chart_navamsa, natural_malefics=None):
    """
        284 - The Moon should join malefics in the Navamsa of Cancer or Scorpio.
    """
    return _guhyaroga_yoga_calculation(chart_navamsa=chart_navamsa, natural_malefics=natural_malefics)
def guhyaroga_yoga_from_planet_positions(planet_positions_navamsa, natural_malefics=None):
    """
        284 - The Moon should join malefics in the Navamsa of Cancer or Scorpio.
    """
    _guhyaroga_yoga_calculation(planet_positions_navamsa=planet_positions_navamsa, natural_malefics=natural_malefics)
def guhyaroga_yoga_from_jd_place(jd,place,divisional_chart_factor=9):
    """
        284 - The Moon should join malefics in the Navamsa of Cancer or Scorpio.
    """
    pp9 = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=9)
    return _guhyaroga_yoga_calculation(planet_positions_navamsa=pp9, natural_malefics=nm)
def _guhyaroga_yoga_calculation(chart_navamsa=None, planet_positions_navamsa=None, natural_malefics=None):
    """
        284 - The Moon should join malefics in the Navamsa of Cancer or Scorpio.
    """
    if planet_positions_navamsa is not None:
        p_to_h_nav = utils.get_planet_house_dictionary_from_planet_positions(planet_positions_navamsa)
        moon_sign_in_navamsa = planet_positions_navamsa[const.MOON_ID + 1][1][0]
    elif chart_navamsa is not None:
        p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
        moon_sign_in_navamsa = p_to_h_nav[const.MOON_ID]
    else: return False
    _malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    if moon_sign_in_navamsa not in (const.CANCER, const.SCORPIO): return False
    malefics_with_moon = any(p_to_h_nav[mp]==moon_sign_in_navamsa and mp!= const.MOON_ID for mp in _malefics)
    return malefics_with_moon
def angaheena_yoga(chart_1d):
    """ 
        285 - When the Moon is in the 10th, Mars in the 7th and Saturn in the 2nd from the Sun, 
        the above yoga is formed.
    """
    return _angaheena_yoga_calculation(chart_1d=chart_1d)
def angaheena_yoga_from_planet_positions(planet_positions):
    """ 
        285 - When the Moon is in the 10th, Mars in the 7th and Saturn in the 2nd from the Sun, 
        the above yoga is formed.
    """
    return _angaheena_yoga_calculation(planet_positions=planet_positions)
def angaheena_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        285 - When the Moon is in the 10th, Mars in the 7th and Saturn in the 2nd from the Sun, 
        the above yoga is formed.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _angaheena_yoga_calculation(planet_positions=pp)
def _angaheena_yoga_calculation(chart_1d=None, planet_positions=None):
    """ 
        285 - When the Moon is in the 10th, Mars in the 7th and Saturn in the 2nd from the Sun, 
        the above yoga is formed.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    return ( p_to_h[const.MOON_ID]==(lagna_house+const.HOUSE_10)%12 and
             p_to_h[const.MARS_ID]==(lagna_house+const.HOUSE_7)%12 and
             p_to_h[const.SATURN_ID]==(p_to_h[const.SUN_ID]+const.HOUSE_2)%12)
def swetakushta_yoga(chart_1d):
    """
        286 -  Mars and Saturn are in the 2nd and 12th, the Moon in Lagna and the Sun in the 7th,
        the above Yoga is given rise to.
    """
    return _swetakushta_yoga_calculation(chart_1d=chart_1d)
def swetakushta_yoga_from_planet_positions(planet_positions):
    """
        286 -  Mars and Saturn are in the 2nd and 12th, the Moon in Lagna and the Sun in the 7th,
        the above Yoga is given rise to.
    """
    return _swetakushta_yoga_calculation(planet_positions=planet_positions)
def swetakushta_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        286 -  Mars and Saturn are in the 2nd and 12th, the Moon in Lagna and the Sun in the 7th,
        the above Yoga is given rise to.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _swetakushta_yoga_calculation(planet_positions=pp)
def _swetakushta_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        286 -  Mars and Saturn are in the 2nd and 12th, the Moon in Lagna and the Sun in the 7th,
        the above Yoga is given rise to.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    return ( p_to_h[const.MARS_ID]==(lagna_house+const.HOUSE_2)%12 and
             p_to_h[const.SATURN_ID]==(lagna_house+const.HOUSE_12)%12 and
             p_to_h[const.MOON_ID]==lagna_house and 
             p_to_h[const.SUN_ID]==(lagna_house+const.HOUSE_7)%12)
def pisacha_grastha_yoga(chart_1d=None,natural_malefics=None):
    """
        287 - When Rahu is in Lagna in conjunction with the Moon and the malefics join trines,
        the above yoga is given rise to.    
    """
    return _pisacha_grastha_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def pisacha_grastha_yoga_from_planet_positions(planet_positions,natural_malefics=None):
    """
        287 - When Rahu is in Lagna in conjunction with the Moon and the malefics join trines,
        the above yoga is given rise to.    
    """
    return _pisacha_grastha_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def pisacha_grastha_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        287 - When Rahu is in Lagna in conjunction with the Moon and the malefics join trines,
        the above yoga is given rise to.    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _pisacha_grastha_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _pisacha_grastha_yoga_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        287 - When Rahu is in Lagna in conjunction with the Moon and the malefics join trines,
        the above yoga is given rise to.    
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    _malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    rahu_with_lagna_and_moon = ( p_to_h[const.RAHU_ID]==lagna_house and p_to_h[const.MOON_ID]==lagna_house)
    if not rahu_with_lagna_and_moon: return False
    return any(mp in house.trines_of_the_raasi(lagna_house) for mp in _malefics)
def andha_yoga_288(chart_1d=None,natural_malefics=None):
    """
        288 - When Rahu is in Lagna in conjunction with the Sun and the malefics join trines,
        the above yoga is given rise to.    
    """
    return _andha_yoga_288_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def andha_yoga_288_from_planet_positions(planet_positions,natural_malefics=None):
    """
        288 - When Rahu is in Lagna in conjunction with the Sun and the malefics join trines,
        the above yoga is given rise to.    
    """
    return _andha_yoga_288_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def andha_yoga_288_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        288 - When Rahu is in Lagna in conjunction with the Sun and the malefics join trines,
        the above yoga is given rise to.    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _andha_yoga_288_calculation(planet_positions=pp, natural_malefics=nm)
def _andha_yoga_288_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        288 - When Rahu is in Lagna in conjunction with the Sun and the malefics join trines,
        the above yoga is given rise to.    
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    _malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    rahu_with_lagna_and_sun = ( p_to_h[const.RAHU_ID]==lagna_house and p_to_h[const.SUN_ID]==lagna_house)
    if not rahu_with_lagna_and_sun: return False
    return any(mp in house.trines_of_the_raasi(lagna_house) for mp in _malefics)
def andha_yoga_289(chart_1d=None,natural_malefics=None):
    """
        289 - Mars, the Moon, Saturn and the Sun should respectively occupy the 2nd, 6th, 12th and 8th    
    """
    return _andha_yoga_289_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def andha_yoga_289_from_planet_positions(planet_positions,natural_malefics=None):
    """
        289 - Mars, the Moon, Saturn and the Sun should respectively occupy the 2nd, 6th, 12th and 8th    
    """
    return _andha_yoga_289_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def andha_yoga_289_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        289 - Mars, the Moon, Saturn and the Sun should respectively occupy the 2nd, 6th, 12th and 8th    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _,nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _andha_yoga_289_calculation(planet_positions=pp, natural_malefics=nm)
def _andha_yoga_289_calculation(chart_1d=None, planet_positions=None,natural_malefics=None):
    """
        289 - Mars, the Moon, Saturn and the Sun should respectively occupy the 2nd, 6th, 12th and 8th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    _malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    return ( p_to_h[const.MARS_ID]==(lagna_house+const.HOUSE_2)%12 and
             p_to_h[const.MOON_ID]==(lagna_house+const.HOUSE_6)%12 and
             p_to_h[const.SATURN_ID]==(lagna_house+const.HOUSE_12)%12 and
             p_to_h[const.SUN_ID]==(lagna_house+const.HOUSE_8)%12
             )
def vaatharoga_yoga(chart_1d=None, is_moon_waning=False, method=1):
    """ 
        290 - When Jupiter is in Lagna and Saturn in the 7th house,the above yoga is caused.
        Method=2: Mars in 5th/7th/9th OR Sun in Lagna, malefic moon and Saturn in 12th
    """
    return _vaatharoga_yoga_calculation(chart_1d=chart_1d, is_moon_waning=is_moon_waning, method=method)
def vaatharoga_yoga_from_planet_positions(planet_positions, is_moon_waning=False, method=1):
    """ 
        290 - When Jupiter is in Lagna and Saturn in the 7th house,the above yoga is caused.
        Method=2: Mars in 5th/7th/9th OR Sun in Lagna, malefic moon and Saturn in 12th
    """
    return _vaatharoga_yoga_calculation(planet_positions=planet_positions, is_moon_waning=is_moon_waning, method=method)
def vaatharoga_yoga_from_jd_place(jd, place, divisional_chart_factor=1,method=1):
    """ 
        290 - When Jupiter is in Lagna and Saturn in the 7th house,the above yoga is caused.
        Method=2: Mars in 5th/7th/9th OR Sun in Lagna, malefic moon and Saturn in 12th
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    tithi_index = drik.tithi(jd, place)[0]
    is_moon_waning = True if tithi_index > 15 else False
    return _vaatharoga_yoga_calculation(planet_positions=pp, is_moon_waning=is_moon_waning, method=method)
def _vaatharoga_yoga_calculation(chart_1d=None, planet_positions=None,is_moon_waning=False,method=1):
    """ 
        290 - When Jupiter is in Lagna and Saturn in the 7th house,the above yoga is caused.
        Method=2: Mars in 5th/7th/9th OR Sun in Lagna, malefic moon and Saturn in 12th
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    if method==1: # BV Raman 
        house_7th = (lagna_house+const.HOUSE_7)%12
        return (p_to_h[const.JUPITER_ID]==lagna_house and p_to_h[const.SATURN_ID]==house_7th)
    else: # Ref: https://blog.pocketpandit.com/vataroga-yoga/
        # Mars in 5th/7th/9th
        alt_290_1 = p_to_h[const.MARS_ID] in [(lagna_house+h-1)%12 for h in [5,7,9]]
        if alt_290_1: return True
        # Sun in Lagna, malefic moon and Saturn in 12th
        return (p_to_h[const.SUN_ID]==lagna_house and is_moon_waning and
                     p_to_h[const.MOON_ID]==(lagna_house+const.HOUSE_12)%12 and 
                     p_to_h[const.SATURN_ID]==p_to_h[const.MOON_ID])
def mathibhramana_yoga_291_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        291 - Jupiter and Mars should occupy the Lagna and the 7th respectively.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mathibhramana_yoga_291_calculation(planet_positions=pp)
def _mathibhramana_yoga_291_calculation(chart_1d=None, planet_positions=None): 
    """ 
        291 - Jupiter and Mars should occupy the Lagna and the 7th respectively.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]; house_7th = (lagna_house+const.HOUSE_7)%12
    return ( p_to_h[const.JUPITER_ID]==lagna_house and p_to_h[const.MARS_ID] == house_7th )
def mathibhramana_yoga_292_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        292 - Saturn must be in Lagna and Mars should join the 9th, 5th or 7th.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mathibhramana_yoga_292_calculation(planet_positions=pp)
def _mathibhramana_yoga_292_calculation(chart_1d=None, planet_positions=None): 
    """ 
        292 - Saturn must be in Lagna and Mars should join the 9th, 5th or 7th.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    return ( p_to_h[const.SATURN_ID]==lagna_house and p_to_h[const.MARS_ID] in [(lagna_house+h-1) for h in[5,7,9]])
def mathibhramana_yoga_293_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        293 - Saturn must occupy the 12th with the waning Moon.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    tithi_index = drik.tithi(jd, place)[0]
    is_waning_moon = True if tithi_index > 15 else False
    return _mathibhramana_yoga_293_calculation(planet_positions=pp, is_waning_moon=is_waning_moon)
def _mathibhramana_yoga_293_calculation(chart_1d=None, planet_positions=None,is_waning_moon=False): 
    """ 
        293 - Saturn must occupy the 12th with the waning Moon.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    return ( is_waning_moon and p_to_h[const.SATURN_ID]==(lagna_house+const.HOUSE_12)%12)
def mathibhramana_yoga_294_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        294 - The Moon and Mercury should be in a kendra, aspected by or conjoined with any other planet.    
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mathibhramana_yoga_294_calculation(planet_positions=pp)
def _mathibhramana_yoga_294_calculation(chart_1d=None, planet_positions=None): 
    """ 
        294 - The Moon and Mercury should be in a kendra, aspected by or conjoined with any other planet.    
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    favorable_houses = quadrants_of_the_house(lagna_house)
    planets_aspecting_moon = house.planets_aspecting_the_planet(chart_1d, const.MOON_ID)
    planets_aspecting_mercury = house.planets_aspecting_the_planet(chart_1d, const.MERCURY_ID)
    return ( p_to_h[const.MOON_ID] in favorable_houses and p_to_h[const.MERCURY_ID] in favorable_houses and
             len(planets_aspecting_moon)>0 and len(planets_aspecting_mercury)>0)
def _mathibhramana_yoga_calculation(chart_1d=None, planet_positions=None, is_waning_moon=False,
                               check_other_variations=False,chart_navamsa=None): 
    """ 
        291 - Jupiter and Mars should occupy the Lagna and the 7th respectively.
        292 - Saturn must be in Lagna and Mars should join the 9th, 5th or 7th.
        293 - Saturn must occupy the 12th with the waning Moon.
        294 - The Moon and Mercury should be in a kendra, aspected by or conjoined with any other planet. 
        This yoga occurs, per B.V.Raman Variations, if - 
            (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
            (2) The 6th lord is further affiicted by conjunction with Mars.
            (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
            (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    """
    if _mathibhramana_yoga_291_calculation(chart_1d=chart_1d, planet_positions=planet_positions): return True
    elif _mathibhramana_yoga_292_calculation(chart_1d=chart_1d, planet_positions=planet_positions): return True
    elif _mathibhramana_yoga_293_calculation(chart_1d=chart_1d, planet_positions=planet_positions,
                                             is_waning_moon=is_waning_moon): return True
    elif _mathibhramana_yoga_294_calculation(chart_1d=chart_1d, planet_positions=planet_positions): return True
    elif check_other_variations: return _mathibhramana_yoga_variation_calculation(chart_1d=chart_1d,
                                planet_positions=planet_positions)
def mathibhramana_yoga_from_planet_positions(planet_positions, is_waning_moon=False, check_other_variations=False):
    """ 
        291 - Jupiter and Mars should occupy the Lagna and the 7th respectively.
        292 - Saturn must be in Lagna and Mars should join the 9th, 5th or 7th.
        293 - Saturn must occupy the 12th with the waning Moon.
        294 - The Moon and Mercury should be in a kendra, aspected by or conjoined with any other planet. 
        This yoga occurs, per B.V.Raman Variations, if - 
            (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
            (2) The 6th lord is further affiicted by conjunction with Mars.
            (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
            (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    """
    return _mathibhramana_yoga_calculation(
        planet_positions=planet_positions,
        is_waning_moon=is_waning_moon,
        check_other_variations=check_other_variations
    )
def mathibhramana_yoga(chart_1d=None, is_waning_moon=False, check_other_variations=False, chart_navamsa=None):
    """ 
        291 - Jupiter and Mars should occupy the Lagna and the 7th respectively.
        292 - Saturn must be in Lagna and Mars should join the 9th, 5th or 7th.
        293 - Saturn must occupy the 12th with the waning Moon.
        294 - The Moon and Mercury should be in a kendra, aspected by or conjoined with any other planet. 
        This yoga occurs, per B.V.Raman Variations, if - 
            (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
            (2) The 6th lord is further affiicted by conjunction with Mars.
            (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
            (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    """
    return _mathibhramana_yoga_calculation(
        chart_1d=chart_1d,
        is_waning_moon=is_waning_moon,
        check_other_variations=check_other_variations,
        chart_navamsa=chart_navamsa
    )
def mathibhramana_yoga_variation_from_jd_place(jd, place, divisional_chart_factor=1):
    """ 
        BVR Variations:
            (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
            (2) The 6th lord is further affiicted by conjunction with Mars.
            (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
            (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _mathibhramana_yoga_variation_calculation(planet_positions=pp)
def _mathibhramana_yoga_variation_calculation(chart_1d=None, planet_positions=None,planet_positions_navamsa=None,
                                              chart_navamsa=None): 
    """ 
        BVR Variations:
            (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
            (2) The 6th lord is further affiicted by conjunction with Mars.
            (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
            (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
        lord_of_6th = house.house_owner_from_planet_positions(planet_positions, 
                                                    (p_to_h[const._ascendant_symbol]+const.HOUSE_6)%12)
        if planet_positions_navamsa is None:
            planet_positions_navamsa = charts.nava_navamsa_chart(planet_positions)[:const._pp_count_upto_ketu]
            chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
        lord_of_6th = house.house_owner(chart_1d,(p_to_h[const._ascendant_symbol]+const.HOUSE_6)%12)
    if chart_1d is None: return False
    lagna_house = p_to_h[const._ascendant_symbol]
    # (1) The 6th is occupied by Rahu and aspected by Kethu. BVR Chart
    var_1 = ( p_to_h[const.RAHU_ID]==(lagna_house+const.HOUSE_6)%12 and 
              const.KETU_ID in house.planets_aspecting_the_planet(chart_1d, const.RAHU_ID) )
    if var_1: return True
    # (2) The 6th lord is further affiicted by conjunction with Mars.
    var_2 = ( p_to_h[lord_of_6th]==p_to_h[const.MARS_ID])
    if var_2: return True
    # (3) The planet of nerves Mercury is in a common sign in conjunction with two malefics, Mars and Sun.
    var_3 = ( p_to_h[const.MERCURY_ID]== p_to_h[const.MARS_ID] and 
              p_to_h[const.MERCURY_ID]== p_to_h[const.SUN_ID])
    if var_3: return True
    # (4) In the Navamsa again Mercury occupies the 6th with Rahu and the 6th lord is in conjunction with Mars
    if chart_navamsa is None: return False
    p_to_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
    nav_lagna_house = p_to_nav[const._ascendant_symbol]; house_of_6th=(nav_lagna_house+const.HOUSE_6)%12
    lord_of_6th_in_nav = ( house.house_owner_from_planet_positions(planet_positions_navamsa, house_of_6th) if planet_positions_navamsa
                    else house.house_owner(chart_navamsa, house_of_6th) )
    return ( ( p_to_nav[const.RAHU_ID]==house_of_6th and p_to_nav[const.MERCURY_ID]==house_of_6th) and 
               p_to_nav[lord_of_6th_in_nav]==p_to_nav[const.MARS_ID] ) 
def khalwata_yoga(chart_1d=None, natural_malefics=None):
    """
        295 - The ascendant must be a malefic sign or Sagittarius or Taurus aspected by malefic planets.
    """
    return _khalwata_yoga_calculation(chart_1d=chart_1d, natural_malefics=natural_malefics)
def khalwata_yoga_from_planet_positions(planet_positions, natural_malefics=None):
    """
        295 - The ascendant must be a malefic sign or Sagittarius or Taurus aspected by malefic planets.
    """
    return _khalwata_yoga_calculation(planet_positions=planet_positions, natural_malefics=natural_malefics)
def khalwata_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        295 - The ascendant must be a malefic sign or Sagittarius or Taurus aspected by malefic planets.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    _, nm = charts.benefics_and_malefics(jd, place, divisional_chart_factor=divisional_chart_factor)
    return _khalwata_yoga_calculation(planet_positions=pp, natural_malefics=nm)
def _khalwata_yoga_calculation(chart_1d=None, planet_positions=None, natural_malefics=None):
    """
        295 - The ascendant must be a malefic sign or Sagittarius or Taurus aspected by malefic planets.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    lagna_house = p_to_h[const._ascendant_symbol]
    favorable_houses = const.malefic_signs +[const.SAGITTARIUS, const.TAURUS]
    _malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
    planets_aspecting_lagna = house.planets_aspecting_the_raasi(chart_1d, lagna_house)
    return ( lagna_house in favorable_houses and any(mp in planets_aspecting_lagna for mp in _malefics) )
def nishturabhashi_yoga(chart_1d=None):
    """
        296 - The Moon must be in conjunction with Saturn without Jupiter aspect.
    """
    return _nishturabhashi_yoga_calculation(chart_1d=chart_1d)
def nishturabhashi_yoga_from_planet_positions(planet_positions):
    """
        296 - The Moon must be in conjunction with Saturn without Jupiter aspect.
    """
    return _nishturabhashi_yoga_calculation(planet_positions=planet_positions)
def nishturabhashi_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        296 - The Moon must be in conjunction with Saturn without Jupiter aspect.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _nishturabhashi_yoga_calculation(planet_positions=pp)
def _nishturabhashi_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        296 - The Moon must be in conjunction with Saturn without Jupiter aspect.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
    elif chart_1d is not None:
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    else:
        return False
    return ( p_to_h[const.MOON_ID]==p_to_h[const.SATURN_ID] and 
             const.JUPITER_ID not in house.planets_aspecting_the_planet(chart_1d,const.MOON_ID) )
def rajabhrashta_yoga(chart_1d=None):
    """
        297 - The lords of Aroodha Lagna (A1/AL) and Aroodha Dwadasa (A12/UL) should be in conjunction.
    """
    return _rajabhrashta_yoga_calculation(chart_1d=chart_1d)
def rajabhrashta_yoga_from_planet_positions(planet_positions):
    """
        297 - The lords of Aroodha Lagna (A1/AL) and Aroodha Dwadasa (A12/UL) should be in conjunction.
    """
    return _rajabhrashta_yoga_calculation(planet_positions=planet_positions)
def rajabhrashta_yoga_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        297 - The lords of Aroodha Lagna (A1/AL) and Aroodha Dwadasa (A12/UL) should be in conjunction.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return _rajabhrashta_yoga_calculation(planet_positions=pp)
def _rajabhrashta_yoga_calculation(chart_1d=None, planet_positions=None):
    """
        297 - The lords of Aroodha Lagna (A1/AL) and Aroodha Dwadasa (A12/UL) should be in conjunction.
    """
    from jhora.horoscope.chart import arudhas
    if planet_positions is not None:
        arudha_paadhas = arudhas.bhava_arudhas_from_planet_positions(planet_positions, arudha_base=0)
        lord_of_A1 = house.house_owner_from_planet_positions(planet_positions, arudha_paadhas[0])
        lord_of_A12 = house.house_owner_from_planet_positions(planet_positions, arudha_paadhas[-1])
        p_to_h = utils.get_planet_house_dictionary_from_planet_positions(planet_positions)
        return p_to_h[lord_of_A1]==p_to_h[lord_of_A12]
    elif chart_1d is not None:
        arudha_paadhas = arudhas.bhava_arudhas_from_chart(chart_1d, arudha_base=0)
        lord_of_A1 = house.house_owner(chart_1d, arudha_paadhas[0])
        lord_of_A12 = house.house_owner(chart_1d, arudha_paadhas[-1])
        p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
        return p_to_h[lord_of_A1]==p_to_h[lord_of_A12]
    else:
        return False
def raja_bhanga_yoga_298_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        298 - The ascendant being Leo, Saturn must be in exaltation occupying a debilitated Navamsa 
            or aspected by benefic.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    pp9 = charts.divisional_chart(jd, place, divisional_chart_factor=9)[:const._pp_count_upto_ketu]
    nb,_ = charts.benefics_and_malefics(jd, place, divisional_chart_factor)
    return _raja_bhanga_yoga_298_calculation(planet_positions=pp, planet_positions_navamsa=pp9,
                                             natural_benefics=nb)
def raja_bhanga_yoga_298_from_planet_positions(planet_positions, planet_positions_navamsa, natural_benefics=None):
    """
        298 - The ascendant being Leo, Saturn must be in exaltation occupying a debilitated Navamsa 
            or aspected by benefic.
    """
    return _raja_bhanga_yoga_298_calculation(planet_positions=planet_positions, 
                                             planet_positions_navamsa=planet_positions_navamsa,
                                             natural_benefics=natural_benefics)
def raja_bhanga_yoga_298(chart_1d, chart_navamsa, natural_benefics=None):
    """
        298 - The ascendant being Leo, Saturn must be in exaltation occupying a debilitated Navamsa 
            or aspected by benefic.
    """
    return _raja_bhanga_yoga_298_calculation(chart_1d=chart_1d, chart_navamsa=chart_navamsa, natural_benefics=natural_benefics)
def _raja_bhanga_yoga_298_calculation(chart_1d=None, planet_positions=None, chart_navamsa=None, 
                                      planet_positions_navamsa=None, natural_benefics=None):
    """
        298 - The ascendant being Leo, Saturn must be in exaltation occupying a debilitated Navamsa 
            or aspected by benefic.
    """
    if planet_positions is not None:
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
    if planet_positions_navamsa is not None:
        chart_navamsa = utils.get_house_planet_list_from_planet_positions(planet_positions_navamsa)

    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    asc_house = p_to_h[const._ascendant_symbol]
    if asc_house != const.LEO: return False

    saturn_house = p_to_h[const.SATURN_ID]
    if not utils.is_planet_in_exalation(const.SATURN_ID, saturn_house, planet_positions, enforce_deep_exaltation=False):
        return False

    debilitated_navamsa = False
    if chart_navamsa is not None:
        p_to_h_nav = utils.get_planet_to_house_dict_from_chart(chart_navamsa)
        saturn_nav_house = p_to_h_nav[const.SATURN_ID]
        debilitated_navamsa = (saturn_nav_house == const.ARIES)

    _benefics = natural_benefics if natural_benefics is not None else const.natural_benefics
    planets_aspecting_saturn = house.planets_aspecting_the_planet(chart_1d, const.SATURN_ID)
    benefics_aspect_saturn = any(bp in planets_aspecting_saturn for bp in _benefics)

    return debilitated_navamsa or benefics_aspect_saturn
def raja_bhanga_yoga_299_from_jd_place(jd, place, divisional_chart_factor=1):
    """
        299 - The Sun must occupy the 10th degree of Libra.
    """
    pp = charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)[:const._pp_count_upto_ketu]
    return raja_bhanga_yoga_299_from_planet_positions(pp)
def raja_bhanga_yoga_299_from_planet_positions(planet_positions):
    """
        299 - The Sun must occupy the 10th degree of Libra.
    """
    return utils.is_planet_in_debilitation(const.SUN_ID,planet_positions[const.SUN_ID+1][1][0],
        planet_positions=planet_positions,enforce_deep_debilitation=True)

if __name__ == "__main__":
    lang = 'en'
    utils.set_language(lang)
    from jhora.tests.pvr_tests import test_example
    exercise = "Koorma Yoga "
    ## Test Data BV Raman Chart # 39
    chart_1d = ['L',"","","5/8","0/4","3/2","1","6","","7","",""]
    chart_navamsa = ["L/7","3","","2","6","0/5","8","","4","","","1"]
    """ We have to force benefics and malefics to meet all the criteria """
    expected_result = True; nb = [1,3,4,5]; nm = [0,2,6,7,8]; method=1
    test_example(exercise,expected_result,
                    _koorma_yoga_calculation(chart_1d=chart_1d,chart_navamsa=chart_navamsa,
                                                natural_benefics=nb,natural_malefics=nm,
                                                method=method),chart_1d)
    exit()
    from datetime import datetime
    current_date_str,current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
    y,m,d = map(int,current_date_str.split(','))
    hh,mm,ss = map(int,current_time_str.split(':'))
    jd = utils.julian_day_number(drik.Date(2026,3,19),(18,30,0))
    place = drik.Place('Kathmandu, Nepal',27.7017,85.3206,5.75)
    dcf = 1
    if const.check_yogas_on_all_divisional_charts:
        print(get_yoga_details_for_all_charts(jd, place, language=lang))
    else:
        print(get_yoga_details(jd, place, divisional_chart_factor=dcf, language=lang))
    exit()


