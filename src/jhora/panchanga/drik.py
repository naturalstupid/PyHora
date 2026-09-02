#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# py -- routines for computing tithi, vara, etc.
#
# Copyright (C) 2013 Satish BD  <bdsatish@gmail.com>
# Downloaded from https://github.com/bdsatish/drik-panchanga
#
# This file is part of the "drik-panchanga" Python library
# for computing Hindu luni-solar calendar based on the Swiss ephemeris
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
# Copyright (C) Open Astro Technologies, USA.
# Modified by Sundar Sundaresan, USA. carnaticmusicguru2015@comcast.net
# Downloaded from https://github.com/naturalstupid/PyJHora
"""
    To calculate panchanga/calendar elements such as tithi, nakshatra, etc.
    Uses swiss ephemeris
"""
"""
    Release History:
    V4.8.9:
        -vyaptipata supports 2 methods. 
        `nava_thaara`, `special_thaara` functions updated to support `base_star_planet` argument
        vighati lagna rate factor Fixed. Earlier it was 15.0 - corrected to 5.0
    V4.8.7 
        - Handling Rahu/Ketu retrograde/stationary/speed-info for true/mean nodes revised
        - graha yudh logic revised. removed Rahu/Ketu from calculations
        - dhasavarga - set_planet_list no longer set inside this anymore.
        - next_planet_entry_date_general - speed factor default changed to 0.001
        - removed rounding from speed-info
    V4.8.6 - get_planet_speed_sign, planets_in_stationary and next_planet_stationary_duration
            added to getting stationary planets. 
            next_planet_retrograde_change_date updated
            true tropical year function modified
"""
from math import ceil
from collections import namedtuple as struct
import swisseph as swe
from _datetime import datetime, timedelta
from datetime import date
import math, os, warnings
from jhora import utils, const

""" Since datetime does not accept BC year values Use the following structure to represent dates """
Date = struct('Date', ['year', 'month', 'day'])

from functools import lru_cache

_PlaceBase = struct('Place', ['name', 'latitude', 'longitude', 'timezone'])

@lru_cache(maxsize=4096)
def _elevation_lookup(lat, lon):
    try:
        return float(utils.get_elevation(lat, lon)) if const.get_place_elevation_from_internet else 0.0
    except Exception:
        return 0.0


class Place:
    __slots__ = ("_base", "_elevation")

    def __init__(self, name, latitude, longitude, timezone, elevation=None):
        self._base = _PlaceBase(
            name,
            float(latitude),
            float(longitude),
            float(timezone)
        )
        self._elevation = None if elevation is None else float(elevation)

    @property
    def name(self):
        return self._base.name

    @property
    def latitude(self):
        return self._base.latitude

    @property
    def longitude(self):
        return self._base.longitude

    @property
    def timezone(self):
        return self._base.timezone

    @property
    def elevation(self):
        if self._elevation is None:
            self._elevation = _elevation_lookup(self.latitude, self.longitude)
        return self._elevation

    def __iter__(self):
        # backward-compatible unpacking for old code expecting 4 fields
        yield self.name
        yield self.latitude
        yield self.longitude
        yield self.timezone

    def __repr__(self):
        return (
            f"Place(Place={self.name!r}, latitude={self.latitude}, "
            f"longitude={self.longitude}, timezone={self.timezone}, "
            f"elevation={self._elevation!r})"
        )

planet_list = {const._SUN:const.SUN_ID,const._MOON:const.MOON_ID,const._MARS:const.MARS_ID,
                   const._MERCURY:const.MERCURY_ID,const._JUPITER:const.JUPITER_ID,const._VENUS:const.VENUS_ID,
                   const._SATURN:const.SATURN_ID, const._RAHU:const.RAHU_ID,const._KETU:const.KETU_ID}
_sidereal_planet_list = {const._SUN:const.SUN_ID,const._MOON:const.MOON_ID,const._MARS:const.MARS_ID,
                   const._MERCURY:const.MERCURY_ID,const._JUPITER:const.JUPITER_ID,const._VENUS:const.VENUS_ID,
                   const._SATURN:const.SATURN_ID, const._RAHU:const.RAHU_ID,const._KETU:const.KETU_ID,
                   const._URANUS:const.URANUS_ID,const._NEPTUNE:const.NEPTUNE_ID,
                   const._PLUTO:const.PLUTO_ID}
if const._INCLUDE_URANUS_TO_PLUTO: {**_sidereal_planet_list,**{const._URANUS:const.URANUS_ID,const._NEPTUNE:const.NEPTUNE_ID,
                   const._PLUTO:const.PLUTO_ID}}

_tropical_planet_list = {const._SUN:const.SUN_ID,const._MOON:const.MOON_ID,const._MARS:const.MARS_ID,
                   const._MERCURY:const.MERCURY_ID,const._JUPITER:const.JUPITER_ID,const._VENUS:const.VENUS_ID,
                   const._SATURN:const.SATURN_ID,const._URANUS:const.URANUS_ID,const._NEPTUNE:const.NEPTUNE_ID,
                   const._PLUTO:const.PLUTO_ID} # Rahu = MEAN_NODE
# Hindu sunrise/sunset is calculated w.r.t middle of the sun's disk
# They are geometric, i.e. "true sunrise/set", so refraction is not considered
_rise_flags = swe.BIT_HINDU_RISING | swe.FLG_TRUEPOS | swe.FLG_SPEED # V3.2.3 # Speed flag added for retrogression
PLANET_FLAGS = utils.set_flags_for_planet_positions()
RISE_FLAGS = utils.set_flags_for_rise_set(flags_for_rise=True)
SET_FLAGS = utils.set_flags_for_rise_set(flags_for_rise=False)
def refresh_planet_flags(longitude=None,latitude=None,elevation=None):
    global PLANET_FLAGS, RISE_FLAGS, SET_FLAGS
    PLANET_FLAGS = utils.set_flags_for_planet_positions()
    RISE_FLAGS = utils.set_flags_for_rise_set(flags_for_rise=True)
    SET_FLAGS = utils.set_flags_for_rise_set(flags_for_rise=False)

    if PLANET_FLAGS & swe.FLG_TOPOCTR and None not in (longitude, latitude, elevation):
        swe.set_topo(longitude,latitude,elevation)

def set_tropical_planets():
    global planet_list
    planet_list = _tropical_planet_list    
def set_sideral_planets():
    global planet_list
    planet_list = _sidereal_planet_list
    
#PLANET_NAMES= ['Suriyan', 'Chandran', 'Sevvay','Budhan','Viyaazhan','VeLLi','Sani','Raahu','Kethu','Uranus','Neptune']
def _ayanamsa_surya_siddhantha_model(jd):
    maha_yuga_years = 4320000
    completed_maha_yuga_years = 3888000
    cycle_of_equinoxes = 7200
    """ 
    Precession Rate Reference
            Walter Cruttenden and Vince Dayes, “Understanding Precession of the Equinox”, New Frontiers in Science. 
            http://carlotto.us/newfrontiersinscience/Papers/v02n01a/v02n01a.pdf
    """
    precession_rate_maximum = 12 # As per above reference max 12 arc seconds in 21600 years
    yuga_of_equinoxes = 3 * cycle_of_equinoxes # half period
    ayanamsa_peak_in_degrees = 27.0 # 27 degrees either side from Aries 0 degrees
    kali_yuga_jd =  swe.julday(-3101,1,23,12,cal=swe.JUL_CAL)
    ss_sideral_year = 365.256363 #365.2421988 # 365.2587565
    diff_days = jd - kali_yuga_jd
    sideral_diff_days = diff_days / ss_sideral_year
    ayanamsa_cycle_fraction = (sideral_diff_days/cycle_of_equinoxes)
    ayanamsa_rate_cycle_fraction = (sideral_diff_days/yuga_of_equinoxes)
    precession_rate = -precession_rate_maximum * math.sin(ayanamsa_rate_cycle_fraction * math.pi)
    ayanamsa = math.sin(ayanamsa_cycle_fraction * 2.0 * math.pi) *(ayanamsa_peak_in_degrees+precession_rate)
    return ayanamsa
def _calculate_ayanamsa_senthil_from_jd(jd):
    #print('calling senthil')
    reference_jd =  swe.julday(2000, 1, 1, 12,cal=swe.GREG_CAL)
    sidereal_year = 365.242198781
    p0 = 50.27972324
    m = 0.0002225
    a0 = 85591.25323
    q = m / 2
    diff_days = (jd - reference_jd) # in days
    t = diff_days / sidereal_year
    ayanamsa = a0 + p0*t + q*t*t
    ayanamsa /= 3600
    return ayanamsa
def get_ayanamsa_value(jd):
    """
        Get ayanamsa value for the julian day number
        Note: Recommended to call this  immediately after calling set_ayanamsa_mode
        returns the ayanamsa value for the ayanamsa mode passed to set_ayanamsa_mode or that of const._DEFAULT_AYANAMSA_MODE
        @param jd: Julian Day Number
        @return: ayanamsa value - ayanamsa for the day based on the model used. 
    """
    key = const._DEFAULT_AYANAMSA_MODE#_ayanamsa_mode.lower()
    if key.lower() =='sidm_user':
        _ayanamsa_value = swe.get_ayanamsa(jd)
        return _ayanamsa_value
    elif key.lower() =='senthil':
        return _calculate_ayanamsa_senthil_from_jd(jd)
    elif key.lower() == 'sundar_ss':
        return _ayanamsa_surya_siddhantha_model(jd)
    else:
        _ayanamsa_value = swe.get_ayanamsa(jd)
        return _ayanamsa_value
def set_ayanamsa_mode(ayanamsa_mode = None,ayanamsa_value=None,jd=None):
    """
        Set Ayanamsa mode
        @param ayanamsa_mode - Default - const._DEFAULT_AYANAMSA_MODE
            Other possible values: 
            FAGAN, KP, RAMAN, USHASHASHI, YUKTESHWAR, SURYASIDDHANTA, SURYASIDDHANTA_MSUN,ARYABHATA,ARYABHATA_MSUN,
            SS_CITRA, TRUE_CITRA, TRUE_REVATI, SS_REVATI, SENTHIL, SUNDAR_SS, SIDM_USER
        @param ayanamsa_value - Need to be supplied only in case of 'SIDM_USER'
        @param jd: Julian day number to be supplied only for ayanamsa modes: SENTHIL and SUNDAR_SS
        See 'available_ayanamsa_modes' for the list of available models
        @return None
    """
    if ayanamsa_mode is None: ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
    key = ayanamsa_mode.upper()
    if key in [am.upper() for am in const.available_ayanamsa_modes.keys()]:
        if key == "SIDM_USER" and jd is not None and ayanamsa_value is not None:
            swe.set_sid_mode(swe.SIDM_USER,t0=jd,ayan_t0=ayanamsa_value)
        elif key == "SENTHIL" and jd is not None:
            _ayanamsa_value = _calculate_ayanamsa_senthil_from_jd(jd)
            swe.set_sid_mode(swe.SIDM_USER,t0=jd,ayan_t0=_ayanamsa_value)
        elif key == "SUNDAR_SS" and jd is not None:
            _ayanamsa_value = _ayanamsa_surya_siddhantha_model(jd)
            swe.set_sid_mode(swe.SIDM_USER,t0=jd,ayan_t0=_ayanamsa_value)
        else:
            swe.set_sid_mode(const.available_ayanamsa_modes[key])
    else:
        print(ayanamsa_mode,"Unsupported Ayanamsa mode:",const._DEFAULT_AYANAMSA_MODE+" Assumed")
        ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
        swe.set_sid_mode(const.available_ayanamsa_modes[const._DEFAULT_AYANAMSA_MODE] )
    _ayanamsa_mode = ayanamsa_mode
    const._DEFAULT_AYANAMSA_MODE = _ayanamsa_mode

set_ayanamsa_mode()

reset_ayanamsa_mode = lambda: swe.set_sid_mode(const.available_ayanamsa_modes[const._DEFAULT_AYANAMSA_MODE]) \
                      if const._DEFAULT_AYANAMSA_MODE not in ['SIDM_USER','SENTHIL','SUNDAR_SS','KP-SENTHIL'] else \
                      swe.set_sid_mode(swe.SIDM_TRUE_PUSHYA)
""" TODO: Need to make panchanga resource independent """

# Ketu is always 180° after Rahu, so same coordinates but different constellations
# i.e if Rahu is in Pisces, Ketu is in Virgo etc
ketu = lambda rahu: (rahu + 180) % 360
rahu = lambda ketu: (ketu + 180) % 360

jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)   # returns (y, m, d, h, min, s)

# moon daily motion
def _lunar_daily_motion(jd):
    """ lunar daily motion"""
    today_longitude = lunar_longitude(jd)
    tomorrow_longitude = lunar_longitude(jd+1)
    #      print(tomorrow_longitude,today_longitude)
    if (tomorrow_longitude < today_longitude):
      tomorrow_longitude += utils.from_dms(360,0,0)
    daily_motion = tomorrow_longitude - today_longitude
    #      print(tomorrow_longitude,today_longitude)
    return daily_motion
  
# sun daily motion
def _solar_daily_motion(jd):
    """ Sun daily motion"""
    today_longitude = solar_longitude(jd)
    tomorrow_longitude = solar_longitude(jd+1)
    if (tomorrow_longitude < today_longitude):
      tomorrow_longitude = tomorrow_longitude + utils.from_dms(360,0,0)
    daily_motion = tomorrow_longitude - today_longitude
    #  print(tomorrow_longitude,today_longitude)
    return daily_motion

def nakshatra_pada(longitude):
    """ 
        Gives nakshatra (1..27) and paada (1..4) in which given longitude lies
        @param longitude: longitude of the planet 
        @return [nakshathra index, paadham, longitude remainder in the nakshathra]
            Note: Nakshatra index [1..27], Paadha [1..4] reminder in float degrees 
    """
    # 27 nakshatras span 360°
    one_star = (360 / 27)  # = 13°20'
    # Each nakshatra has 4 padas, so 27 x 4 = 108 padas in 360°
    one_pada = (360 / 108) # = 3°20'
    quotient = int(longitude / one_star)
    #reminder = (longitude - quotient * one_star)
    reminder = longitude%one_star
    pada = int(reminder / one_pada)
    #  print (longitude,quotient,pada)
    # convert 0..26 to 1..27 and 0..3 to 1..4
    #print(longitude,quotient,reminder,pada)
    return [1 + quotient, 1 + pada,reminder]
def ephemeris_planet_index(planet):
    if planet == const._ascendant_symbol: return planet
    return [p_swe for p_swe,p_id in planet_list.items() if p_id==planet][0]
def _planet_speed_sign(jd, place, planet):  # V4.8.6
    if planet in [const.RAHU_ID, const.KETU_ID] and not const._use_true_nodes_for_rahu_ketu:
        return -1
    speed_tolerance = const.one_arc_second
    dsp = daily_planet_speed(jd, place, planet)
    if dsp > speed_tolerance:
        return 1
    elif dsp < -speed_tolerance:
        return -1
    else:
        return 0

def sidereal_longitude(jd_utc, planet):
    """
        The sequence number of 0 to 8 for planets is not followed by swiss ephemeris
        Need to be sure we pass correct planet reference to swiss ephemeris
        Make sure to pass planets as const._SUN, const._MOON .. const._KETU etc
        For all other functions of this PyJHora libarary one can use 0 to 8 for Sun to Ketu and 9-11 for Urnaus to Pluto
        Computes nirayana (sidereal) longitude of given planet on jd
        Note: This is where the selected/default ayanamsa is adjusted to tropical longitude obtained from swiss ephimeride
        @param jd: Julian Day Number of the UTC date/time.
        NOTE: The julian day number supplied to this function must be UTC date/time.
              All other functions of this PyJHora library will require JD and not JD_UTC
              JD_UTC = JD - Place.TimeZoneInFloatHours
              For example for India JD_UTC = JD - 5.5. For wester time zone -5.0 it JD_UTC = JD - (-5.0)
        @param planet: index of the planet Use const._SUN, const._RAHU etc.
        @return: the sidereal longitude of the planet (0-360 degrees)
    """
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH + swe.FLG_SPEED
    else:
        flags = PLANET_FLAGS #swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    if planet == const._KETU:
        longi,_ = swe.calc_ut(jd_utc, const._RAHU, flags = flags)
        ketu_long = (longi[0]+180)%360
        return ketu_long
    else:
        longi,_ = swe.calc_ut(jd_utc, planet, flags = flags)
    return utils.norm360(longi[0]) # degrees
def planets_in_retrograde(jd,place):
    """
        To get the list of retrograding planets
        @param jd: julian day number (not UTC)
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: list of retrograding planets e.g. [3,5]
        NOTE: To find the retrograding planets for kundali charts use this function.
        There is another function in `jhora.horoscope.chart.charts` module which calculates
        retrograding planet based on their positions and is used in yoga, dhasa calculations
        NOTE: Sun and Moon do not retrograde. 
            Rahu/Ketu always retrograde as Mean Nodes (and do not exibit stationary or direct)
            Rahu/Ketu as True nodes - retrograde, stationary or even direct
    """
    global planet_list
    jd_utc = jd - place.timezone / 24.
    flags = PLANET_FLAGS # swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    retro_planets = []
    _planet_list = {p:p_id for p,p_id in planet_list.items() if p not in [const._SUN, const._MOON]}
    for planet,p_id in _planet_list.items():
        if p_id == const.KETU_ID:
            longi,_ = swe.calc_ut(jd_utc, const._RAHU, flags = flags)
            if longi[3]<0 : retro_planets.append(p_id)
            continue
        longi,_ = swe.calc_ut(jd_utc, planet, flags = flags)
        if longi[3]<0 : retro_planets.append(p_id)
    return retro_planets

def planets_in_stationary(jd,place,zero_threshold=None): # V4.8.6
    """
        To get the list of stationary planets
        @param jd: julian day number (not UTC)
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: list of stationary planets e.g. [3,5]
        NOTE: Sun and Moon do not retrograde. 
            Rahu/Ketu always retrograde as Mean Nodes (and do not exibit stationary or direct)
            Rahu/Ketu as True nodes - retrograde, stationary or even direct
    """
    if zero_threshold is None: zero_threshold = const.one_arc_second
    global planet_list
    jd_utc = jd - place.timezone / 24.
    flags = PLANET_FLAGS # swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    zero_planets = []
    excluded_planets = [const._SUN, const._MOON]
    if not const._use_true_nodes_for_rahu_ketu: excluded_planets += [const._RAHU, const._KETU]
    _planet_list = {p:p_id for p,p_id in planet_list.items() if p not in excluded_planets}
    for planet,p_id in _planet_list.items():
        longi,_ = swe.calc_ut(jd_utc, planet, flags = flags)
        if abs(longi[3]) < zero_threshold : zero_planets.append(p_id)
    return zero_planets
def _planet_speed_info(jd, place,planet):
    """ 
        JD (not UTC)
        planet = 0 to 7 - Ketu is same as Rahu 
        @return: [longitude,latitude,distance_from_earth,longitude_speed,latitude_speed,distance_speed]
    """
    if planet == const._ascendant_symbol: return ascendant_speed(jd, place)
    p_swe = ephemeris_planet_index(planet)
    jd_utc = jd - place.timezone / 24.
    flags = PLANET_FLAGS
    if planet != const.KETU_ID:
        longi,_ = swe.calc_ut(jd_utc, p_swe, flags = flags)
        return longi
    else:
        rahu_data,_ = swe.calc_ut(jd_utc, const._RAHU, flags = flags)
        ketu_data = list(rahu_data)
        ketu_data[0] = utils.norm360(rahu_data[0] + 180)  # Mirror Longitude
        ketu_data[1] = -rahu_data[1]                       # Invert Latitude
        ketu_data[4] = -rahu_data[4]                       # Invert Latitude speed
        return ketu_data

daily_moon_speed = lambda jd,place: _planet_speed_info(jd,place,const._MOON)[3]
daily_sun_speed = lambda jd,place: _planet_speed_info(jd,place,const._SUN)[3]
daily_planet_speed = lambda jd,place,planet: _planet_speed_info(jd, place, planet)[3]
def planets_speed_info(jd,place):
    """
        To get the speed information of planets
        @param jd: julian day number (not UTC)
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [(longitude,latitude,distance_from_earth,longitude_speed,latitude_speed,distance_speed),...]
    """
    return {planet: _planet_speed_info(jd, place, planet) for _,planet in planet_list.items()}
    jd_utc = jd - place.timezone / 24.
    flags = PLANET_FLAGS # swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    _planets_speed_info = {}
    for planet,planet_index in planet_list.items():
        if planet_index==const.KETU_ID:#planet == const._KETU:
            rahu_data,_ = swe.calc_ut(jd_utc, const._RAHU, flags = flags)
            ketu_data = list(rahu_data)
            ketu_data[0] = utils.norm360(rahu_data[0] + 180)  # Mirror Longitude
            ketu_data[1] = -rahu_data[1]                       # Invert Latitude
            ketu_data[4] = -rahu_data[4]                       # Invert Latitude speed
            _planets_speed_info[planet_index] = ketu_data#[round(l,round_factors[i]) for i,l in enumerate(ketu_data)]
            continue
        longi,_ = swe.calc_ut(jd_utc, planet, flags = flags)
        _planets_speed_info[planet_index] = longi #[round(l,round_factors[i]) for i,l in enumerate(longi)]
    return _planets_speed_info
def planets_in_graha_yudh(jd,place):
    """
        Graha Yudh
        Bhed-yuti (भेद युति): Happens when longitudes of two planets and also the latitude in the same direction (N or S) are exactly the same, even to the last second. During this, one planet transits over the other and covers the other exactly.
        Ullekh-yuti: (उल्लेख युति)  when longitudes are equal and latitudes of both planets, in the same direction are mutually away by 15-20”. here planets moves neck to neck by touching almost their ends.
        Apsavya-yuti (अपसव्य युति) moving at equal longitude, two planets move within 1° distance in latitude.
        Anshumard-yuti (अंशु-मर्दन युति) with equal longitudes, the two pass each other with less than 1° difference in latitude.
        Ref: https://www.planetarypositions.com/yoga/2014/10/30/conjunction-planets-grah-yudh/

        NOTE: Looks like last 2 categories are identical whereas JHora seem to use 2° difference in latitude for Anshumard-yuti
            So we have used 2° difference in latitude for Anshumard-yuti
            
        @return graha yudh pairs of planets with the category of yudh
            [(planet1, planet2, yudh category)]
                yudh category 0 =>Bhed-yuti
                yudh category 1 =>Ullekh-yuti: (उल्लेख युति)
                yudh category 2 =>Apsavya-yuti (अपसव्य युति)
                yudh category 3 =>Anshumard-yuti (अंशु-मर्दन युति)
            For Example: Date=(2014,11,13) Time=(6,26,0) for Bangalore, India
            we will get [(5, 6, 3)] => Venus and Saturn are within 2° difference in latitude for Anshumard-yuti
    """
    from math import radians, sin, atan2, sqrt, degrees
    def lat_distance(lat1, lat2):
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        dlat = lat2_rad - lat1_rad
        a = sin(dlat / 2) ** 2
        return degrees(2 * atan2(sqrt(a), sqrt(1 - a)))

    def compare_planet_coordinates(planet_coords):
        result = []
        n = len(planet_coords)

        for i in range(n):
            for j in range(i + 1, n):
                p1, long1, lat1 = planet_coords[i]
                p2, long2, lat2 = planet_coords[j]

                # 1. Use an orb check for floating-point longitudes instead of pure equality
                if abs(long1 - long2) <= 1.0:
                    lat_diff = lat_distance(lat1, lat2)
                    lat_diff_arcsec = lat_diff * 3600.0
                    
                    # Safe directional check handling exact 0.0 ecliptic crossings
                    same_direction = (lat1 >= 0 and lat2 >= 0) or (lat1 <= 0 and lat2 <= 0)

                    # 2. Evaluate from the strictest specific criteria down to the broadest
                    if long1 == long2 and lat1 == lat2:
                        result.append((p1, p2, 0))  # Bhed-yuti
                        
                    elif same_direction and (lat_diff_arcsec <= const.graha_yudh_criteria_1):
                        result.append((p1, p2, 1))  # Ullekh-yuti
                        
                    elif same_direction and (lat_diff <= const.graha_yudh_criteria_2):
                        result.append((p1, p2, 2))  # Apsavya-yuti
                        
                    elif lat_diff <= const.graha_yudh_criteria_3:
                        result.append((p1, p2, 3))  # Anshumard-yuti (Using JHora 2° standard)
        return result

    eligible_planets = [const.MARS_ID, const.MERCURY_ID, const.JUPITER_ID, const.VENUS_ID, const.SATURN_ID]

    planet_coords = []
    for planet in eligible_planets:
        long, lat, _, _, _, _ = _planet_speed_info(jd, place, planet)
        planet_coords.append((planet, long, lat))

    return compare_planet_coordinates(planet_coords)


solar_longitude = lambda jd_utc: sidereal_longitude(jd_utc, const._SUN)
lunar_longitude = lambda jd_utc: sidereal_longitude(jd_utc, const._MOON)
def sunrise(jd, place):
    """
        Sunrise when centre of disc is at horizon for given date and place
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [sunrise time as local time in float hours, local time string, and sunrise julian number]
            e.g. [6.5,'06:30 AM',2450424.94]
    """
    # First convert jd to UTC
    y, m, d,_  = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    
    _,lat, lon, tz = place; ele = place.elevation
    result = swe.rise_trans(jd_utc - tz/24, swe.SUN, geopos=(lon, lat,ele), rsmi = RISE_FLAGS, flags=PLANET_FLAGS)
    rise_jd = result[1][0]  # julian-day number
    rise_local_time = (rise_jd - jd_utc) * 24 + tz
    """ ADDED THE FOLLOWING IN V2.5.2 TO RECALCULATE RISE_JD"""
    dob = (y,m,d)
    tob = tuple(utils.to_dms(rise_local_time, as_string=False))
    rise_jd = utils.julian_day_number(dob, tob)
    # Convert to local time
    return [rise_local_time, utils.to_dms(rise_local_time),rise_jd]
def midday(jd,place):
    """
        Return midday time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [midday time as local time in float hours, local time string, and midday julian number]
            e.g. [12.1,'12:10 PM',2450424.94]
    """
    sun_rise = sunrise(jd, place)#[2]
    sun_set = sunset(jd, place)#[2]
    _,_,_,srh = utils.jd_to_gregorian(sun_rise[2])
    _,_,_,ssh = utils.jd_to_gregorian(sun_set[2]) # V4.4.0
    mdhl = 0.5*(srh+ssh)
    return mdhl, 0.5*(sun_rise[2]+sun_set[2])
def midnight(jd,place):
    """
        Return midnight time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [midnight time as local time in float hours, local time string, and midnight julian number]
            e.g. [0.1,'00:10 AM',2450424.94]
    """
    sun_rise = sunrise(jd, place)#[2]
    prev_sun_set = sunset(jd-1, place)# V4.8.5
    _,_,_,srh = utils.jd_to_gregorian(sun_rise[2])
    _,_,_,pssh = utils.jd_to_gregorian(prev_sun_set[2]) # V4.8.5
    mnhl = 0.5*(srh+pssh)
    if mnhl < 12:
        mnhl = 12 - mnhl
    else:
        mnhl -= 12
    return mnhl
def day_length(jd, place):
    """
        Return local day length in float hours
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: day length in float hours. e.g. 12.125
    """
    return (sunset(jd, place)[0] - sunrise(jd, place)[0])
def night_length(jd, place):
    """
        Return local night length in float hours
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: night length in float hours. e.g. 12.125
    """
    return (24.0 + sunrise(jd+1, place)[0] - sunset(jd, place)[0])
def sunset(jd, place):
    """
        Sunset when centre of disc is at horizon for given date and place
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return sunset  time as local time in float hours, local time string, and rise sd julian number date
            Time Format: float hours or hh:mm:ss AM/PM
    """
    # First convert jd to UTC
    y, m, d,_  = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    _,lat, lon, tz = place; ele = place.elevation
    result = swe.rise_trans(jd_utc - tz/24, swe.SUN, geopos=(lon, lat,ele), rsmi = SET_FLAGS, flags=PLANET_FLAGS )
    set_jd = result[1][0]
    set_local_time = (set_jd - jd_utc) * 24 + tz
    # Convert to local time
    """ ADDED THE FOLLOWING IN V4.2.0 TO RECALCULATE RISE_JD"""
    dob = (y,m,d)
    tob = tuple(utils.to_dms(set_local_time, as_string=False))
    set_jd = utils.julian_day_number(dob, tob)
    return [set_local_time, utils.to_dms(set_local_time),set_jd]
def moonrise(jd, place):
    """
        Return local moonrise time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [Moonrise time as local time in float hours, local time string, and Moonrise julian number]
            e.g. [2.5,'02:30 AM',2450424.94]
    """
    # First convert jd to UTC
    y, m, d, h = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    city, lat, lon, tz = place; ele = place.elevation
    result = swe.rise_trans(jd_utc - tz/24, swe.MOON, geopos=(lon, lat,ele), rsmi = RISE_FLAGS, flags=PLANET_FLAGS)
    rise = result[1][0]  # julian-day number
    # Convert to local time
    local_time = (rise - jd_utc) * 24 + tz
    return [local_time,utils.to_dms(local_time),rise]

def moonset(jd, place):
    """
        Return local moonset time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [Moonset time as local time in float hours, local time string, and Moonset julian number]
            e.g. [14.5,'14:30 PM',2450424.94]
    """
    # First convert jd to UTC
    y, m, d, h = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    city, lat, lon, tz = place; ele = place.elevation
    result = swe.rise_trans(jd_utc - tz/24, swe.MOON, geopos=(lon, lat,ele), rsmi = SET_FLAGS, flags=PLANET_FLAGS)
    setting = result[1][0]  # julian-day number
    # Convert to local time
    local_time = (setting - jd_utc) * 24 + tz
    return [local_time,utils.to_dms(local_time),setting]
def _get_tithi(jd,place,tithi_index=1,planet1=const._MOON,planet2=const._SUN,cycle=1):
    # tithi_index = 1=>Janma Tithi 2=>Dhana 3=>Bhratri, 4=>Matri 5=Putra 6=>Satru 7=>Kalatra 8=>Mrutyu 9=>Bhagya 10=>Karma 11=>Laabha 12=>Vyaya
    """
        TODO: Cycle option is not working as per JHora. Algorithm not clear
        So the results cannot be trusted
    """ 
    tz = place.timezone
    # First convert jd to UTC  # 2.0.3
    y, m, d,bt = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    # 1. Find time of sunrise
    rise = sunrise(jd, place)[2] # V2.2.8
    # 2. Find tithi at this JDN
    moon_phase = _special_tithi_phase(rise, planet1, planet2, tithi_index, cycle)
    today = ceil(moon_phase / 12)
    """ SPECIAL CASE OF TITHI SKIPPING BEFORE MAHABHARATHA TIME 
        See Dr. Jayasree Saranatha Mahabharatha date validation book """
    if const.increase_tithi_by_one_before_kali_yuga and jd < const.mahabharatha_tithi_julian_day: #V3.2.0
        #print('tithi increased by 1 before mahabharatha date from',today,'to',today+1)
        today = (today+1)%30
    degrees_left = today * 12 - moon_phase
    # 3. Compute longitudinal differences at intervals of 0.25 days from sunrise
    offsets = [0.25, 0.5, 0.75, 1.0]
    planet1_long_diff = [ (sidereal_longitude(rise + t,planet1) - sidereal_longitude(rise,planet1)) % 360 for t in offsets ]
    planet2_long_diff = [ (sidereal_longitude(rise + t,planet2) - sidereal_longitude(rise,planet2)) % 360 for t in offsets ]
    relative_motion = [ (tithi_index*(p1-p2)+(cycle-1)*180)%360 for (p1, p2) in zip(planet1_long_diff, planet2_long_diff) ]
    # 4. Find end time by 4-point inverse Lagrange interpolation
    y = relative_motion; x = offsets
    # compute fraction of day (after sunrise) needed to traverse 'degrees_left'
    approx_end = utils.inverse_lagrange(x, y, degrees_left)
    ends = (rise + approx_end -jd_utc) * 24 + tz #jd changed to jd_utc 2.0.3
    tithi_no = int(today)
    #""" Start Time 
    answer = [tithi_no, ends]
    # 5. Check for skipped tithi
    moon_phase_tmrw = _special_tithi_phase(rise+1, planet1, planet2, tithi_index, cycle)
    tomorrow = ceil(moon_phase_tmrw / 12)
    """ SPECIAL CASE OF TITHI SKIPPING BEFORE MAHABHARATHA TIME See Dr. Jayasree Saranatha Mahabharatha datte validation book """
    if jd < const.mahabharatha_tithi_julian_day: #V3.2.0
        tomorrow = (tomorrow+1)%30
    isSkipped = (tomorrow - today) % 30 > 1
    if isSkipped:
        # interpolate again with same (x,y)
        leap_tithi = today + 1
        tithi_no = int(leap_tithi)
        degrees_left = leap_tithi * 12 - moon_phase_tmrw
        approx_end = utils.inverse_lagrange(x, y, degrees_left)
        ends = (rise + approx_end -jd_utc) * 24 + tz #jd changed to jd_utc 2.0.3
        leap_tithi = 1 if today == 30 else leap_tithi
        answer += [tithi_no, ends]
    return answer
def tithi_using_planet_speed(jd,place,tithi_index=1,planet1=const._MOON,planet2=const._SUN,cycle=1):
    _,_,_,jd_hours = utils.jd_to_gregorian(jd)
    #if not const.use_planet_speed_for_panchangam_end_timings: return _general_tithi(jd, place, tithi_index, planet1, planet2)
    def _get_tithi_using_planet_speed(jd,place):
        jd_utc = jd - place.timezone/24.
        #sunrise_jd = sunrise(jd, place)[2]
        tithi_phase = _special_tithi_phase(jd_utc, planet1=planet1, planet2=planet2, tithi_index=tithi_index, cycle=cycle)
        total = tithi_phase % 360
        one_tithi = 360/30
        tit = ceil(total /one_tithi)
        tithi_no = int(tit)
        degrees_left = tit * one_tithi-total
        one_day_hours = day_length(jd, place)+night_length(jd, place)
        """ Use only Moon/Sun Speeds for end time calculations and not the speeds of respective planets """
        daily_planet1_motion = daily_moon_speed(jd,place)
        daily_planet2_motion = daily_sun_speed(jd,place)
        end_time = jd_hours + degrees_left/(daily_planet1_motion-daily_planet2_motion)*one_day_hours
        frac_left = degrees_left/one_tithi
        start_time = end_time - (end_time-jd_hours)/frac_left
        """ SPECIAL CASE OF TITHI SKIPPING BEFORE MAHABHARATHA TIME 
            See Dr. Jayasree Saranatha Mahabharatha date validation book
        """
        #"""
        if const.increase_tithi_by_one_before_kali_yuga and jd < const.mahabharatha_tithi_julian_day: #V3.2.0
            #print('tithi increased by 1 before mahabharatha date from',tithi_no,'to',tithi_no+1)
            tithi_no = (tithi_no)%30+1
        #"""
        return [tithi_no,start_time,end_time]
    ret = _get_tithi_using_planet_speed(jd,place)
    if ret[2] < 24:
        ret1 = _get_tithi_using_planet_speed(jd+ret[2]/24, place)
        #print('next tithi',ret1)
        _next_tithi = (ret[0])%30+1; _next_tithi_start_time = ret[2]; _next_tithi_end_time = ret[2]+ret1[2]
        ret += [_next_tithi,_next_tithi_start_time,_next_tithi_end_time]
    return ret
def tithi(jd,place,tithi_index=1,planet1=const._MOON, planet2=const._SUN,cycle=1,force_tithi_at_sunrise=False):    
    """
        Tithi given jd and place. Also returns tithi's end time.
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param tithi_index = 1=>Janma Tithi 2=>Dhana 3=>Bhratri, 4=>Matri 5=Putra 6=>Satru 7=>Kalatra 
                            8=>Mrutyu 9=>Bhagya 10=>Karma 11=>Laabha 12=>Vyaya (Default Janma tithi)
        @return [tithi number, tithi_start_time, tithi ending time, tithi_fraction,
                 next_tithi_number, next_tithi_start_time, next_tithi ending time, next_tithi_fraction]
          next tithi number and next tithi time is additionally returned if two tithis on same day
    """
    """
        TODO: Handle similar to JHora if planets are same
    """
    jd_tithi = sunrise(jd,place)[2] if force_tithi_at_sunrise else jd # V4.8.5
    if const.use_planet_speed_for_panchangam_end_timings:
        return tithi_using_planet_speed(jd_tithi, place, tithi_index, planet1, planet2, cycle)
    else:
        return tithi_using_inverse_lagrange(jd_tithi, place, tithi_index, planet1, planet2, cycle)
def tithi_using_inverse_lagrange(jd,place,tithi_index=1,planet1=const._MOON, planet2=const._SUN,cycle=1):    
    """
        Tithi given jd and place. Also returns tithi's end time.
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param tithi_index = 1=>Janma Tithi 2=>Dhana 3=>Bhratri, 4=>Matri 5=Putra 6=>Satru 7=>Kalatra 
                            8=>Mrutyu 9=>Bhagya 10=>Karma 11=>Laabha 12=>Vyaya (Default Janma tithi)
        @return [tithi number, tithi_start_time, tithi ending time, tithi_fraction,
                 next_tithi_number, next_tithi_start_time, next_tithi ending time, next_tithi_fraction]
          next tithi number and next tithi time is additionally returned if two tithis on same day
    """
    """
        TODO: Handle similar to JHora if planets are same
    """
    def __get_tithi_lagrange(jd,place,tithi_index=tithi_index,planet1=planet1, planet2=planet2,cycle=cycle):
        _tithi = _get_tithi(jd,place,tithi_index,planet1,planet2,cycle=cycle)
        _tithi_prev = _get_tithi(jd-1,place,tithi_index,planet1,planet2,cycle=cycle)
        _tithi_no = _tithi[0]; _tithi_start = _tithi_prev[1]; _tithi_end = _tithi[1]
        if _tithi_start < 24.0:
            _tithi_start = -_tithi_start
        elif _tithi_start > 24:
            _tithi_start -= 24.0
        result = [_tithi_no,_tithi_start,_tithi_end]
        return result
    ret = __get_tithi_lagrange(jd,place,tithi_index=tithi_index,planet1=planet1, planet2=planet2,cycle=cycle)
    if ret[2] < 24.0:
        ret1 = __get_tithi_lagrange(jd+ret[2]/24,place,tithi_index=tithi_index,planet1=planet1, planet2=planet2,cycle=cycle)
        _next_tithi = (ret[0])%30+1; _next_tithi_start_time = ret[2]; _next_tithi_end_time = ret[2]+ret1[2]
        ret += [_next_tithi,_next_tithi_start_time,_next_tithi_end_time]
    return ret
def _special_tithi_phase(jd,planet1=const._MOON,planet2=const._SUN,tithi_index=1,cycle=1):
    planet1_long = sidereal_longitude(jd,planet1)
    planet2_long = sidereal_longitude(jd,planet2)
    tithi_phase = (tithi_index*(planet1_long - planet2_long)+(cycle-1)*180) % 360
    return tithi_phase    
def raasi(jd, place):
    """
        returns the raasi at julian day/time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [raasi number, raasi ending time, raasi fraction left, 
                 next raasi number, next raasi ending time, next rasi fraction left]
          next raasi index and next raasi time is additionally returned if two raasis on same day 
          raasi number = [1..12]        
    """
    tz = place.timezone
    # First convert jd to UTC # 2.0.3
    y, m, d, _ = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d)); jd_ut = jd - tz/24.
    rise = sunrise(jd, place)[2] # - tz / 24 #V2.3.0
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
    longitudes = [lunar_longitude(rise+t) for t in offsets] #V2.3.0 # Fixed 1.1.0 lunar longitude from sunrise to next sunrise
    # V4.4.0 changed from jd_ut to jd to match Adhik Maasa calculations
    nirayana_long = lunar_longitude(jd)
    raasi_no = int(nirayana_long/30)+1
    frac_left = 1.0 - (nirayana_long/30) % 1
    # 3. Find end time by 5-point inverse Lagrange interpolation
    y = utils.unwrap_angles(longitudes)
    x = offsets
    approx_end = utils.inverse_lagrange(x, y, raasi_no * 30)
    ends = (rise - jd_utc + approx_end) * 24 + tz #jd changed to jd_utc 2.0.3
    answer = [raasi_no, ends, frac_left]
    
    # 4. Check for skipped raasi
    raasi_tmrw = ceil(longitudes[-1] / 30)
    frac_left = 1.0 - (longitudes[-1] / 30) % 1
    isSkipped = (raasi_tmrw - raasi_no) % 12 > 1
    if isSkipped:
        leap_raasi = raasi_no + 1
        approx_end = utils.inverse_lagrange(offsets, longitudes, leap_raasi * 30)
        ends = (rise+1 - jd_utc + approx_end) * 24 + tz #rise => rise + 1
        leap_raasi = 1 if raasi_no == 12 else leap_raasi
        raasi_no = int(leap_raasi)
        answer += [raasi_no, ends, frac_left]
    return answer
def _get_nakshathra(jd, place):
    """
        V4.2.1 With CoPilot help fixed special case of inverse lagrange
        where y list for Revathi may have longitudes either 0-14 degrees or 350-365 degrees
        or a mix of 0-14 and 350-365. This is now fixed 'somewhat'
    """
    tz = place.timezone
    y, m, d, _ = utils.jd_to_gregorian(jd)
    jd_ut = utils.gregorian_to_jd(Date(y, m, d))
    jd_utc = jd - place.timezone / 24.
    rise = sunrise(jd_utc, place)[2]
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
    longitudes = [sidereal_longitude(rise + t, const._MOON) for t in offsets]
    unwrapped_longitudes = utils.unwrap_angles(longitudes)
    #print("Unwrapped longitudes:", unwrapped_longitudes)

    # Extend angle range if needed
    extended_longitudes = utils.extend_angle_range(unwrapped_longitudes, 360)
    x = offsets * (len(extended_longitudes) // len(unwrapped_longitudes))
    
    nirayana_long = lunar_longitude(jd_utc)
    nak_no, padam_no, _ = nakshatra_pada(nirayana_long)
    y_check = (nak_no * 360 / 27)

    # Normalize y_check to the same range as extended_longitudes
    y_check = utils.normalize_angle(y_check, start=min(extended_longitudes))
    approx_end = utils.inverse_lagrange(x, extended_longitudes, y_check)
    #print(x, extended_longitudes, y_check, approx_end)

    ends = (rise - jd_ut + approx_end) * 24 + tz
    answer = [nak_no, padam_no, ends]
    leap_nak = nak_no + 1
    y_check = (leap_nak * 360 / 27)
    y_check = utils.normalize_angle(y_check, start=min(extended_longitudes))
    approx_end = utils.inverse_lagrange(x, extended_longitudes, y_check)
    ends = (rise - jd_ut + approx_end) * 24 + tz # V4.3.0 Changed back to jd_ut from jd_utc
    leap_nak = 1 if nak_no == 27 else leap_nak
    nak_no = int(leap_nak)
    answer += [nak_no, padam_no, ends]
    return answer
def _get_nakshathra_old(jd,place):
    """
        TODO: For Revathi 4th padha specifically - when looking for 360 deg end, Lagrange gives strange results
                because offsets may near 0 degrees while longitudes near 360
    """
    tz = place.timezone
    y, m, d, _ = jd_to_gregorian(jd)
    jd_ut = utils.gregorian_to_jd(Date(y, m, d))
    jd_utc = jd - place.timezone / 24.
    rise = sunrise(jd_utc, place)[2] # Changed to jd_utc in V2.9.6
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
    longitudes = [sidereal_longitude(rise+t, const._MOON) for t in offsets]
    nirayana_long = lunar_longitude(jd_utc) # Changed to jd_utc in V2.9.7
    nak_no,padam_no,_ = nakshatra_pada(nirayana_long)
    y = utils.unwrap_angles(longitudes)
    x = offsets; y_check = (nak_no * 360 / 27)
    approx_end = utils.inverse_lagrange(x, y, y_check)
    ends = (rise - jd_ut + approx_end) * 24 + tz
    answer = [nak_no,padam_no, ends]
    # 4. Check for skipped nakshatra
    leap_nak = nak_no + 1
    y_check = (leap_nak * 360 / 27)
    approx_end = utils.inverse_lagrange(offsets, longitudes, y_check)
    ends = (rise - jd_ut + approx_end) * 24 + tz
    leap_nak = 1 if nak_no == 27 else leap_nak
    nak_no = int(leap_nak)
    answer += [nak_no,padam_no, ends]
    return answer
def nakshatra(jd,place):
    """
        returns the nakshathra at julian day/time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [nakshatra number, nakshatra starting time, nakshatra ending time, nakshatra fraction left, 
                 next nakshatra number, next nakshatra starting time, next nakshatra ending time, next nakshatra fraction left]
          next nakshatra index and next nakshatra time is additionally returned if two nakshatras on same day 
          nakshatra number = [1..27]  Aswini to Revathi
    """
    _nak = _get_nakshathra(jd, place)
    _nak_prev = _get_nakshathra(jd-1, place)
    _nak_no = _nak[0]; _pad_no = _nak[1]; _nak_start = _nak_prev[2]; _nak_end = _nak[2]
    if _nak_start < 24.0:
        _nak_start = -_nak_start
    elif _nak_start > 24:
        _nak_start -= 24.0
    result = [_nak_no,_pad_no,_nak_start,_nak_end]+_nak[3:]
    return result
def nakshatra_new(jd,place):
    """
        returns the nakshathra at julian day/time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [nakshatra number, nakshatra starting time, nakshatra ending time, nakshatra fraction left, 
                 next nakshatra number, next nakshatra starting time, next nakshatra ending time, next nakshatra fraction left]
          next nakshatra index and next nakshatra time is additionally returned if two nakshatras on same day 
          nakshatra number = [1..27]  Aswini to Revathi
    """
    """
        TODO:
            If jd is at the Nakshathra time - results are awkward. Need to check the logic below
    """
    if not const.use_planet_speed_for_panchangam_end_timings: return nakshatra(jd, place)
    _,_,_,jd_hours = utils.jd_to_gregorian(jd)
    def _get_nakshathra_new(jd):
        jd_utc = jd - place.timezone/24.
        one_star = 360/27
        moon_long = lunar_longitude(jd_utc)
        nak_no, padam_no, _ = nakshatra_pada(moon_long)
        degrees_left = nak_no*one_star-moon_long
        end_time = jd_hours + degrees_left/daily_moon_speed(jd,place)*24
        #frac_left = degrees_left/one_star
        ret = [nak_no,padam_no,end_time]
        return ret
    _nak = _get_nakshathra_new(jd)
    _nak_prev = _get_nakshathra_new(jd-1)
    _nak_no = _nak[0]; _pad_no = _nak[1]; _nak_start = _nak_prev[2]; _nak_end = _nak[2]
    if _nak_start < 24.0:
        _nak_start = -_nak_start
    elif _nak_start > 24:
        _nak_start -= 24.0
    result = [_nak_no,_pad_no,_nak_start,_nak_end]+_nak[3:]
    return result
def _special_yoga_phase(jd,planet1=const._MOON,planet2=const._SUN,tithi_index=1,cycle=1):
    planet1_long = sidereal_longitude(jd,planet1)
    planet2_long = sidereal_longitude(jd,planet2)
    tithi_phase = (tithi_index*(planet1_long + planet2_long)+(cycle-1)*180) % 360
    return tithi_phase
def _get_yogam(jd,place,planet1=const._MOON,planet2=const._SUN,tithi_index=1,cycle=1):
    # 1. Find time of sunrise
    city, lat, lon, tz = place
    y, m, d,bt = jd_to_gregorian(jd);jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    rise = sunrise(jd, place)[2] # V2.2.8
    one_yoga = 360./27.
    # 2. Find the Nirayana longitudes and add them
    total = _special_yoga_phase(rise, planet1, planet2, tithi_index, cycle)
    # There are 27 Yogas spanning 360 degrees
    yog = ceil(total /one_yoga)
    yogam_no = int(yog)
    # 3. Find how many longitudes is there left to be swept
    degrees_left = yog * one_yoga - total
    
    # 3. Compute longitudinal sums at intervals of 0.25 days from sunrise
    offsets = [0.0,0.25, 0.5, 0.75, 1.0]
    """ Use only Moon/Sun longitudes for end time calculations and not the speeds of respective planets """
    planet1_long_diff = [ (lunar_longitude(rise + t) - lunar_longitude(rise)) % 360 for t in offsets ]
    planet2_long_diff = [ (solar_longitude(rise + t,) - solar_longitude(rise)) % 360 for t in offsets ]
    total_motion = [ (tithi_index*(p1+p2)+(cycle-1)*180)%360 for (p1, p2) in zip(planet1_long_diff, planet2_long_diff) ]
    
    # 4. Find end time by 4-point inverse Lagrange interpolation
    y = total_motion
    x = offsets
    # compute fraction of day (after sunrise) needed to traverse 'degrees_left'
    approx_end = utils.inverse_lagrange(x, y, degrees_left)
    ends = (rise + approx_end - jd_utc) * 24 + tz
    #print(utils.jd_to_gregorian(rise),utils.jd_to_gregorian(jd_utc),utils.jd_to_gregorian(rise+approx_end),total,yog,degrees_left,x,y,approx_end,ends)
    answer = [yogam_no, ends]
    # 5. Check for skipped yoga
    total_tmrw = _special_yoga_phase(rise+1, planet1, planet2, tithi_index, cycle)
    tomorrow = ceil(total_tmrw / one_yoga)
    isSkipped = (tomorrow - yog) % 27 > 1
    if isSkipped:
        # interpolate again with same (x,y)
        leap_yog = yog + 1
        degrees_left = leap_yog * one_yoga - total
        approx_end = utils.inverse_lagrange(x, y, degrees_left)
        ends = (rise + approx_end - jd_utc) * 24 + tz
        leap_yog = 1 if yog == 27 else leap_yog
        yogam_no = int(leap_yog)
        answer += [yogam_no, ends]
    return answer
def yogam(jd,place,tithi_index=1,planet1=const._MOON,planet2=const._SUN,cycle=1):
    if not const.use_planet_speed_for_panchangam_end_timings: return yogam_old(jd, place)
    _,_,_,jd_hours = utils.jd_to_gregorian(jd)
    def _get_yogam_new(jd):
        jd_utc = jd - place.timezone/24.
        yoga_phase = _special_yoga_phase(jd_utc, planet1=planet1, planet2=planet2, tithi_index=tithi_index, cycle=cycle)
        total = yoga_phase % 360
        one_yoga = 360/27
        yog = ceil(total /one_yoga)
        yogam_no = int(yog)
        # 3. Find how many longitudes is there left to be swept
        degrees_left = yog * one_yoga-total
        """ Use only Moon/Sun Speeds for end time calculations and not the speeds of respective planets """
        daily_planet1_motion = daily_moon_speed(jd,place)
        daily_planet2_motion = daily_sun_speed(jd,place)
        end_time = jd_hours + degrees_left/(daily_planet1_motion+daily_planet2_motion)*24
        frac_left = degrees_left/one_yoga
        start_time = end_time - (end_time-jd_hours)/frac_left
        #print('_get_yogam_new',yogam_no,end_time,'fracion left',frac_left,start_time)
        return [yogam_no,start_time,end_time,frac_left]
    result = _get_yogam_new(jd)
    if result[2] < 24:
        next_res = _get_yogam_new(jd+result[2])
        next_res [1] = result[2];
        next_res[2] += 24
        next_res[3] = utils.get_fraction(next_res[1], next_res[2], jd_hours)
        result += next_res
    return result
def yogam_old(jd,place,planet1=const._MOON,planet2=const._SUN,tithi_index=1,cycle=1):
    """
        returns the yogam at julian day/time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [yogam number, yogam starting time, yogam ending time, yogam fraction left, 
                 next yogam number, next yogam starting time, next yogam ending time, next yogam fraction left]
          next yogam index and next yogam time is additionally returned if two yogams on same day 
          yogam index = [1..27]  1 = Vishkambha, 2 = Priti, ..., 27 = Vaidhrti
    """
    """
        TODO: Ending time calculation using get_yogam() appears incorrect
    """
    #if const.use_planet_speed_for_panchangam_end_timings: return yogam(jd, place, tithi_index, planet1, planet2, cycle)
    _yoga = _get_yogam(jd,place, planet1, planet2, tithi_index, cycle)
    _yoga_prev = _get_yogam(jd-1,place, planet1, planet2, tithi_index, cycle)
    _yoga_no = _yoga[0]; _yoga_start = _yoga_prev[1]; _yoga_end = _yoga[1]
    if _yoga_start < 24.0:
        _yoga_start = -_yoga_start #utils.to_dms(_tithi_start)+'(-1)'
    elif _yoga_start > 24:
        _yoga_start -= 24.0
    _,_,_,birth_time_hrs = utils.jd_to_gregorian(jd)
    yoga_frac = utils.get_fraction(_yoga_start, _yoga_end, birth_time_hrs)
    result = [_yoga_no,_yoga_start,_yoga_end]+_yoga[2:]
    return result
def karana(jd, place):
    """
        returns the karanam of the day
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return karanam index, karanam starting time, karanam ending time, karanam fraction left 
          karanam index = [1..60]  1 = Kimstugna, 2 = Bava, ..., 60 = Naga
        This is corrected function from V4.2.8 onwards
    """
    _,_,_,birth_time_hrs = utils.jd_to_gregorian(jd)
    _tithi = tithi(jd,place)
    _t_start = _tithi[1]; _t_end = _tithi[2]; _t_mid = 0.5*(_t_start+_t_end)
    _karana = _tithi[0]*2-1
    if birth_time_hrs> _t_mid: # second half of tithi
        _karana += 1
        _k_start = _t_mid; _k_end = _t_end
    else: # first of tithi
        _k_start = _t_start; _k_end = _t_mid
    return _karana,_k_start,_k_end
def civil_weekday(jd):
    """
        returns civil Weekday (local midnight to midnight)
        @param jd: Julian Day Number of the date/time
        @return: day of the date
          0 = Sunday, 1 = Monday,..., 6 = Saturday
    """
    return math.floor(jd+1.5)%7
def vedic_weekday(jd, place):
    """
        returns Vedic Weekday (sunrise to sunrise)
        @param jd: Julian Day Number of the date/time
        @param place Place(city,latitude,longitude,timezone_hours)
        @return: day of the date
          0 = Sunday, 1 = Monday,..., 6 = Saturday
    """
    cw = civil_weekday(jd)
    t_local_hour = utils.jd_to_gregorian(jd)[-1]
    sr = sunrise(jd, place)
    sunrise_local_hour = float(sr[0])
    return (cw - 1) % 7 if t_local_hour < sunrise_local_hour else cw
def vaara(jd,place,show_vedic_day=True):
    """
        Weekday for given Julian day. 
        @param jd: Julian Day Number of the date/time
        @param place Place(city,latitude,longitude,timezone_hours)
        @param show_vedic_day
            True will return day based sunrise to sunrise. (Default)
            False will return civil day (local midnight to midnight)
        @return: day of the date
          0 = Sunday, 1 = Monday,..., 6 = Saturday
    """
    return vedic_weekday(jd, place) if show_vedic_day else civil_weekday(jd)
def _vaara(jd):
    """
        Weekday for given Julian day. 
        @param jd: Julian Day Number of the date/time
        @return: day of the date
          0 = Sunday, 1 = Monday,..., 6 = Saturday
    """
    return ( int(ahargana(jd)) % 7 + 5) % 7 if const.use_aharghana_for_vaara_calcuation else int(ceil(jd + 1) % 7)  
def lunar_month(jd, place):
    """
        Returns lunar month and if it is adhika or not.
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [indian month index, whether leap month (adhika lunar_month) or not - boolean]
            1 = Chaitra, 2 = Vaisakha, ..., 12 = Phalguna
            True if adhika lunar_month
    """
    ti = tithi(jd, place)[0]
    critical = sunrise(jd, place)[2] # V2.2.8
    last_new_moon = new_moon(critical, ti, -1)
    next_new_moon = new_moon(critical, ti, +1)
    this_solar_month = raasi(last_new_moon,place)[0]
    next_solar_month = raasi(next_new_moon,place)[0]
    is_leap_month = (this_solar_month == next_solar_month)
    _lunar_month = (this_solar_month+1)%12
    #if _lunar_month > 12: _lunar_month = (_lunar_month % 12)
    is_nija_month = False
    if not is_leap_month:
        pm,pa,_ = lunar_month(jd-30, place)
        is_nija_month = (pm==_lunar_month and pa)
    return [int(_lunar_month), is_leap_month,is_nija_month]
def vedic_date(jd, place,calendar_type=None,sankranti_rule=None,ghatikas=None,hijri_options=None):
    """
        Returns lunar month, lunar day and if it is adhika or not. and the vedic year
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param calendar_type: one of const.CALENDAR_TYPE
             const.CALENDAR_TYPE.SOLAR    Solar Calendar (0 Default)
             const.CALENDAR_TYPE.LUNAR_AMANTHA    1=Amantha and 
             const.CALENDAR_TYPE.PURNIMANTHA    2 = Purnimatha Lunar Calendar
             const.CALENDAR_TYPE.HIJRI_ISLAMIC  3 = Hijri/Islamic Calendar
        @param sankranti_rule one of - for solar calendar type only
            const.SANKRANTI_RULE.TAMIL_NADU_SUNSET_RULE = 1 (Default: Sankranti day if sun enters zodiac before sunset)
            const.SANKRANTI_RULE.BEFORE_GHATIKAS = 2 (Sankranti day before prescribed ghatikas)
                    ghatikas = 18 => Malabar calendar
                    ghatikas = 30 => Bengal Calendar
                    ghatikas = 45 => Kerala Calendar
            const.SANKRANTI_RULE.SUNRISE_TO_SUNRISE = 3 (Sankranti day if sun enters within sunrise to sunrise)
        @return:
            vedic month,day,year,is_adhik_maasa?,is_nija_maaja?
            Vedic Year 0=Prabhava, 1=Vibhava... 58=Krodhana, 59=Akshaya
            Month range = 1 = Chaitra, 2 = Vaisakha, ..., 12 = Phalguna
            adhika lunar_month True/False,
            Nija Month True/False
    """
    if calendar_type==const.CALENDAR_TYPE.SOLAR:
        py,pm,pd,_ = utils.jd_to_gregorian(jd); panchanga_date = Date(py,pm,pd)
        #_month,_day = tamil_solar_month_and_date_from_jd(jd, place)
        _month, _day = solar_month_date(jd, place, sankranti_rule, ghatikas)
        _year = samvatsara(panchanga_date, place, zodiac=0)
        return _month+1,_day,_year, False,False
    elif calendar_type==const.CALENDAR_TYPE.HIJRI_ISLAMIC:
        from jhora.panchanga.hijri import islamic_lunar_date as hijri_lunar_date
        y,m,d = hijri_lunar_date(jd,place) if hijri_options is None else hijri_lunar_date(jd,place,hijri_options)
        return m,d,y,False,False
    else:
        use_purnimanta_system = (calendar_type==const.CALENDAR_TYPE.LUNAR_PURNIMANTHA)
        return lunar_month_date(jd, place, use_purnimanta_system)
def lunar_month_date(jd, place,use_purnimanta_system=False):
    """
        Returns lunar month, lunar day and if it is adhika or not.
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [indian month index,lunar_day, vedic_year,Adhika_Maasa_Boolean,Nija_Maasa_Boolean]
            1 = Chaitra, 2 = Vaisakha, ..., 12 = Phalguna
            True if adhika lunar_month
        TODO: Purnimanta System Calculations have not been validated yet.
    """
    critical = sunrise(jd, place)[2] # V2.2.8
    ti = tithi(critical, place)[0]
    last_new_moon = new_moon(critical, ti, -1)
    next_new_moon = new_moon(critical, ti, +1)
    this_solar_month = raasi(last_new_moon,place)[0]-1
    next_solar_month = raasi(next_new_moon,place)[0]-1
    is_leap_month = (this_solar_month == next_solar_month)
    _lunar_month = (this_solar_month+1)%12
    lunar_day = utils.cyclic_count_of_numbers(from_number=1,to_number=ti,number_count=30,direction=1)
    if use_purnimanta_system:
        if lunar_day > 15: _lunar_month = (_lunar_month+1)%12
        lunar_day = (lunar_day - 16)%30 + 1
    is_nija_month = False
    if not is_leap_month:
        pm,pa,_ = lunar_month(jd-30, place)
        is_nija_month = (pm==_lunar_month and pa)
    _lunar_year = lunar_year_index(jd, _lunar_month+1)
    return [int(_lunar_month+1),lunar_day,_lunar_year, is_leap_month,is_nija_month]
def lunar_year_index(jd,maasa_index):
    """ 
        TODO: Need to investigate the following patching stuff 
        return samvat_index-1 returns -1 sometimes which is wrong??
    """
    kali = elapsed_year(jd, maasa_index)[0]
    kali_base = 14; kali_start = 27 # Pramaadhi
    """ Following is patching to match Prmaadhi at kali yuga start date """
    if kali < 4009 and const.force_kali_start_year_for_years_before_kali_year_4009:
        kali_start = const.kali_start_year
    if kali >= 4009:    kali = (kali - kali_base) % 60
    samvat_index = (kali + kali_start + int((kali * 211 - 108) / 18000)) % 60
    return samvat_index-1
# epoch-midnight to given midnight
# Days elapsed since beginning of Kali Yuga
ahargana = lambda jd: jd - const.mahabharatha_tithi_julian_day
kali_ahargana_days = lambda jd: int(ahargana(jd))
def elapsed_year(jd, maasa_index):
    """
        returns Indian era/epoch year indices (kali year number, saka year and vikrama year numbers)
        @param jd: Julian Day Number of the date/time
        @param maasa_index: [1..12] (use jhora.panchanga.drik.lunar_month function to get this) 
        @return kali year number, vikrama year number, saka year number 
    """
    """ TODO - may not be right for dates before Kali yuaga - to be checked """
    ahar = ahargana(jd)  # or (jd + sunrise(jd, place)[0])
    kali = int((ahar + (4 - maasa_index) * 30) / const.sidereal_year)
    year = jd_to_gregorian(jd)[0]
    #kali = 3101+year
    saka = kali - 3179
    vikrama = saka + 135
    return kali, vikrama, saka

# New moon day: sun and moon have same longitude (0 degrees = 360 degrees difference)
# Full moon day: sun and moon are 180 deg apart
def new_moon(jd, tithi_, opt = -1):
    """Returns JDN, where
       opt = -1:  JDN < jd such that lunar_phase(JDN) = 360 degrees
       opt = +1:  JDN >= jd such that lunar_phase(JDN) = 360 degrees
    """
    if opt == -1:  start = jd - tithi_         # previous new moon
    if opt == +1:  start = jd + (30 - tithi_)  # next new moon
    # Search within a span of (start +- 2) days
    x = [ -2 + offset/4 for offset in range(17) ]
    y = [lunar_phase(start + i) for i in x]
    y = utils.unwrap_angles(y)
    y0 = utils.inverse_lagrange(x, y, 360)
    #print('new moon',tithi(start+y0,place))
    return start + y0
def full_moon(jd, tithi_, opt = -1):
    """Returns JDN, where
       opt = -1:  JDN < jd such that lunar_phase(JDN) = 180 degrees
       opt = +1:  JDN >= jd such that lunar_phase(JDN) = 180 degrees
    """
    if tithi_ <=15:
        start = jd - tithi_ - 15 if opt==-1 else jd + (15-tithi_)
    else:
        start = jd - (tithi_ - 15) if opt==-1 else jd + (45 - tithi_)
    # Search within a span of (start +- 2) days
    x = [ -2 + offset/4 for offset in range(17) ]
    y = [lunar_phase(start + i) for i in x]
    y = utils.unwrap_angles(y)
    y0 = utils.inverse_lagrange(x, y, 180)
    return start + y0
def next_tithi(jd,place,required_tithi,opt=1,start_of_tithi=True):
    """
    TODO: UNDER EXPERIMENTATION
      Returns JDN, where
       opt = -1:  JDN < jd such that lunar_phase(JDN) = required_tithi*12 degrees
       opt = +1:  JDN >= jd such that lunar_phase(JDN) = required_tithi*12 degrees
    """
    tz = place.timezone
    tithi_ = tithi(jd,place)[0]
    tithi_angle = (required_tithi-1)*12 if start_of_tithi else required_tithi*12 
    if tithi_ <=required_tithi:
        inc_days = - tithi_ - required_tithi if opt==-1 else  (required_tithi-tithi_)
    else:
        inc_days = - (tithi_ - required_tithi) if opt==-1 else  (30+required_tithi - tithi_)
    start = jd + inc_days
    #print(tithi_,required_tithi,inc_days,utils.jd_to_gregorian(start))
    x = [ -2 + offset/4 for offset in range(17) ]
    y = [lunar_phase(start + i) for i in x]
    #y = utils.unwrap_angles(y)
    y0 = utils.inverse_lagrange(x, y, tithi_angle)
    tithi_jd = start+y0+tz/24
    #print(tithi(tithi_jd,place),solar_longitude(tithi_jd),lunar_longitude(tithi_jd),lunar_phase(tithi_jd))
    return tithi_jd
def next_lunar_month(jd, place,lunar_month_type=None,direction=1):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = (utils.jd_to_gregorian(next_planet_entry_date(const.SUN_ID, jd, place)[0]) if direction==1 
                            else utils.jd_to_gregorian(previous_planet_entry_date(0, jd, place)[0]))
        return Date(lmy,lmm,lmd),lmh
    if lunar_month_type==const.LUNAR_MONTH_TYPE.AMANTHA:
        ncp_jd,_,_ = next_conjunction_of_planet_pair(jd,place, const.SUN_ID, const.MOON_ID, separation_angle=0.0,
                                              direction=direction)
        return utils.jd_to_gregorian(ncp_jd)
    else:
        ncp_jd,_,_ = next_conjunction_of_planet_pair(jd,place, const.SUN_ID, const.MOON_ID, separation_angle=180.0,
                                              direction=direction)
        return utils.jd_to_gregorian(ncp_jd)
    
def _next_lunar_month(jd, place,lunar_month_type=None,direction=1):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = utils.jd_to_gregorian(next_planet_entry_date(0, jd, place)[0]) if direction==1 else \
                          utils.jd_to_gregorian(previous_planet_entry_date(0, jd, place)[0])
        return Date(lmy,lmm,lmd),lmh
    _tithi_to_check = 30 if lunar_month_type==0 else 15
    tithi_ = tithi(jd,place)[0]
    lm_jd = (new_moon(jd, tithi_, opt=direction) if lunar_month_type==const.LUNAR_MONTH_TYPE.AMANTHA 
             else full_moon(jd, tithi_, opt=direction) )
    _tit = tithi(lm_jd,place); #; print('tithi',_tit)
    lmh = _tit[2] if _tit[0]==_tithi_to_check else _tit[1]
    lmy,lmm,lmd,_ = utils.jd_to_gregorian(lm_jd)
    if lmh > 24:
        extra_days,lmh = divmod(lmh,24)
        lmy,lmm,lmd = utils.next_panchanga_day(Date(lmy,lmm,lmd), add_days=extra_days)
    elif lmh < 0:
        extra_days,lmh = 1,lmh+24
        lmy,lmm,lmd = utils.previous_panchanga_day(Date(lmy,lmm,lmd), minus_days=extra_days)
    return Date(lmy,lmm,lmd),lmh
def previous_lunar_month(jd, place,lunar_month_type=None,direction=-1):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = (utils.jd_to_gregorian(next_planet_entry_date(const.SUN_ID, jd, place)[0]) if direction==1 
                            else utils.jd_to_gregorian(previous_planet_entry_date(0, jd, place)[0]))
        return lmy,lmm,lmd,lmh
    if lunar_month_type==const.LUNAR_MONTH_TYPE.AMANTHA:
        ncp_jd,_,_ = next_conjunction_of_planet_pair(jd,place, const.SUN_ID, const.MOON_ID, separation_angle=0.0,
                                              direction=direction)
        return utils.jd_to_gregorian(ncp_jd)
    else:
        ncp_jd,_,_ = next_conjunction_of_planet_pair(jd,place, const.SUN_ID, const.MOON_ID, separation_angle=180.0,
                                              direction=direction)
        return utils.jd_to_gregorian(ncp_jd)
def _previous_lunar_month(jd, place,lunar_month_type=None,direction=-1):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = (utils.jd_to_gregorian(next_planet_entry_date(const.SUN_ID, jd, place)[0]) if direction==1 
                            else utils.jd_to_gregorian(previous_planet_entry_date(0, jd, place)[0]))
        return lmy,lmm,lmd,lmh
    _tithi_to_check = 30 if lunar_month_type==const.LUNAR_MONTH_TYPE.AMANTHA else 15
    tithi_ = tithi(jd,place)[0]
    lm_jd = (new_moon(jd, tithi_, opt=direction) if lunar_month_type==const.LUNAR_MONTH_TYPE.AMANTHA 
             else full_moon(jd, tithi_, opt=direction) )
    _tit = tithi(lm_jd,place); #; print('tithi',_tit)
    lmh = _tit[2] if _tit[0]==_tithi_to_check else _tit[1]
    lmy,lmm,lmd,_ = utils.jd_to_gregorian(lm_jd)
    if lmh > 24:
        extra_days,lmh = divmod(lmh,24)
        lmy,lmm,lmd = utils.next_panchanga_day(Date(lmy,lmm,lmd), add_days=extra_days)
    elif lmh < 0:
        extra_days,lmh = 1,lmh+24
        lmy,lmm,lmd = utils.previous_panchanga_day(Date(lmy,lmm,lmd), minus_days=extra_days)
    return Date(lmy,lmm,lmd),lmh
def lunar_phase(jd,tithi_index=1):
    solar_long = solar_longitude(jd)
    lunar_long = lunar_longitude(jd)
    moon_phase = tithi_index*(lunar_long - solar_long) % 360
    return moon_phase
def samvatsara(panchanga_date,place,zodiac=0):
    """
        Returns Shaka Samvatsara
        @param panchanga_date: Date as struct (year,month,day)
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param zodiac: [0 .. 11] Aries/Mesham to Pisces/Meenam
        @return: samvastsara year index [0..59] 
        NOTE: This algorithm is for Solar Years.
         TODO: Chithirai always shows previous year
         Should we use previous sakranti which is solar based? 
        Is there an algorithm for lunar samvastra?
        0=Prabhava, 1=Vibhava... 58=Krodhana, 59=Akshaya
    """ 
    ps = _previous_sankranti_date_new(panchanga_date, place,zodiac=zodiac)
    year = ps[0][0]
    if year >0: year-=1 # To account for removing 0BC/AD Year V4.4.5
    sv = (year-1926)%60
    #if sv==0:
    #    sv=60
    return sv
def ritu(maasa_index):
    """ returns ritu / season index. 
        @param maasa_index: [1..12] (use jhora.panchanga.drik.lunar_month function to get this) 
        @return: ritu index  0 = Vasanta,1=greeshma,2=varsha,3=Sharath,4=hemantha,5 = Shishira
    """
    return (maasa_index - 1) // 2

def gauri_choghadiya(jd, place):
    """
        Get end times of gauri chogadiya for the given julian day
        Chogadiya is 1/8th of daytime or nighttime practiced as time measure in North India 
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [(chogadiyua type,start_time_string,end_time_string)...]
    """
    srise = sunrise(jd, place); sset = sunset(jd,place) # V4.8.5
    day_dur = (sset[0] - srise[0])/24
    end_times = []; start_time = srise[1]
    _vaara = vaara(jd,place)
    for i in range(1, 9):
        gt = srise[2]+(i*day_dur)/8; _,_,_,fh = utils.jd_to_gregorian(gt); end_time = utils.to_dms(fh)
        gc_type = const.gauri_choghadiya_day_table[_vaara][i-1]
        end_times.append((gc_type,start_time,end_time))
        start_time = end_time
    
    # Night duration = time from today's sunset to tomorrow's sunrise
    srise = sunrise(jd+1,place); night_dur = (24+srise[0] - sset[0])/24
    for i in range(1, 9):
        gt = sset[2]+(i*night_dur)/8; _,_,_,fh = utils.jd_to_gregorian(gt); end_time = utils.to_dms(fh)
        gc_type = const.gauri_choghadiya_night_table[_vaara][i-1]
        end_times.append((gc_type,start_time,end_time))
        start_time = end_time
    
    return end_times
def amrit_kaalam(jd,place):
    return [(gb,ge) for gc,gb,ge in gauri_choghadiya(jd, place) if gc==3]
def shubha_hora(jd, place):
    """
        Get end times of Shubha Hora for the given julian day
        hora is 1/12th of daytime or nighttime practiced as time measure in South India 
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [(hora_planet,start_time_string,end_time_string)...]
    """
    srise = sunrise(jd, place); sset = sunset(jd,place) # V4.8.5
    day_dur = (sset[0] - srise[0])/24
    end_times = []; start_time = srise[1]
    _vaara = vaara(jd,place)
    for i in range(1, 13):
        gt = srise[2]+(i*day_dur)/12; _,_,_,fh = utils.jd_to_gregorian(gt); end_time = utils.to_dms(fh)
        gc_type = const.shubha_hora_day_table[i-1][_vaara]
        end_times.append((gc_type,start_time,end_time))
        start_time = end_time
    
    # Night duration = time from today's sunset to tomorrow's sunrise
    srise = sunrise(jd+1,place); night_dur = (24+srise[0] - sset[0])/24
    for i in range(1, 13):
        gt = sset[2]+(i*night_dur)/12; _,_,_,fh = utils.jd_to_gregorian(gt); end_time = utils.to_dms(fh)
        gc_type = const.shubha_hora_night_table[i-1][_vaara]
        end_times.append((gc_type,start_time,end_time))
        start_time = end_time
    
    return end_times

def trikalam(jd, place, option='raahu kaalam'):
    """
        Get tri kaalam (Raahu kaalam, yama kandam and Kuligai Kaalam) for the given Julian day
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param option: one of 'raahu kaalam', 'gulikai', 'yamagandam'. Default:'raahu kaalam' 
            Note: One can use separate lambda function for each of these options
        raahu_kaalam = lambda jd, place: trikalam(jd, place, 'raahu kaalam')
            yamaganda_kaalam = lambda jd, place: trikalam(jd, place, 'yamagandam')
            gulikai_kaalam = lambda jd, place: trikalam(jd, place, 'gulikai')
        @return: start and end time of requested tri column - as list e.g. [start_time, end_time]
    """
    srise = sunrise(jd, place)[0] # V4.3.0
    day_dur = day_length(jd, place)
    weekday = vaara(jd,place)
    
    # value in each array is for given weekday (0 = sunday, etc.)
    offsets = { 'raahu kaalam': [0.875, 0.125, 0.75, 0.5, 0.625, 0.375, 0.25],
                'gulikai': [0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0.0],
                'yamagandam': [0.5, 0.375, 0.25, 0.125, 0.0, 0.75, 0.625] }
    
    start_time = srise + day_dur * offsets[option][weekday]
    end_time = start_time + 0.125 * day_dur
    
    start_time = utils.to_dms(start_time)
    end_time = utils.to_dms(end_time)
    
    return [start_time, end_time] # decimal hours to H:M:S

raahu_kaalam = lambda jd, place: trikalam(jd, place, 'raahu kaalam')
yamaganda_kaalam = lambda jd, place: trikalam(jd, place, 'yamagandam')
gulikai_kaalam = lambda jd, place: trikalam(jd, place, 'gulikai')

def durmuhurtam(jd, place):
    """
        Get dhur muhurtham timing for the given julian day
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: start and end time of dhur muhurtham - as list e.g. [start_time, end_time]
    """
    # Night = today's sunset to tomorrow's sunrise
    srise = sunrise(jd, place)[0]; day_dur = day_length(jd,place); night_dur = night_length(jd,place)
    sset = sunset(jd,place)[0]
    weekday = vaara(jd,place)
    
    # There is one durmuhurtam on Sun, Wed, Sat; the rest have two
    # Offsets from sunrise 10.4 means 6 + 10.4 = 16.4 = 4:24 PM
    # Ref: Panchangam Calculations - Karanam Ramakumar
    offsets = [[10.4, 0.0],  # Sunday
               [6.4, 8.8],   # Monday
               [2.4, 4.8],   # Tuesday, [day_duration , night_duration]
               [5.6, 0.0],   # Wednesday
               [4.0, 8.8],   # Thursday
               [2.4, 6.4],   # Friday
               [1.6, 0.0]]   # Saturday
    
    # second durmuhurtam of tuesday uses night_duration instead of day_duration
    dur = [day_dur, day_dur]
    base = [srise, srise]
    if weekday == 2:  dur[1] = night_dur; base[1] = sset
    
    # compute start and end timings
    start_times = [0, 0]
    end_times = [0, 0]
    answer = []
    for i in range(0, 2):
        offset = offsets[weekday][i]
        if offset != 0.0:
            start_times[i] = base[i] + dur[i] * offsets[weekday][i] / 12
            end_times[i] = start_times[i] + day_dur * 0.8 / 12
            start_times[i] = utils.to_dms(start_times[i])
            end_times[i] = utils.to_dms(end_times[i])
            answer += [start_times[i],end_times[i]]
    return answer

def abhijit_muhurta(jd, place):
    """
        Get Abhijit muhurta timing for the given julian day
        Abhijit muhurta is the 8th muhurta (middle one) of the 15 muhurtas during the day_duration (~12 hours)
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: start and end time of Abhijit muhurta - as list e.g. [start_time, end_time]
    """
    _, lat, lon, tz = place
    srise = sunrise(jd,place)[0]; sset = sunset(jd,place)[0] 
    day_dur = day_length(jd, place)
    
    start_time = srise + 7 / 15 * day_dur
    end_time = srise + 8 / 15 * day_dur
    start_time = utils.to_dms(start_time)
    end_time = utils.to_dms(end_time)
    # to local time
    return [start_time, end_time]

# 'jd' can be any time: ex, 2015-09-19 14:20 UTC
# today = swe.julday(2015, 9, 19, 14 + 20./60)
def planetary_positions(jd, place):
    """
        Computes instantaneous planetary positions (i.e., which celestial object lies in which constellation)
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: 2D List of [ [planet index, planet longitude, planet constellation],...]]
            Example: [ [0,87.32148,2],...] - Sun longitude 87.32148, Gemini,...
        Note: Planet list includes Uranus/Neptune/Pluto by default.
              use const._INCLUDE_URANUS_TO_PLUTO = False to remove them from the list.
        Note: swiss ephimeris does not include Rahu and Ketu. Rahu is mapped to MEAN_MODE (Planet index = 10)
            And Ketu is calculated 180 degrees from Rahu/Mean Mode.
            Though Rahu's ephimeris planet index is 10, we use 7 and 8 respectively in charts respectively.
        NOTE:DOES NOT INCLUDE ASCENDANT POSITION AND LONGITUDE. TO GET ASCENDANT CALL: ascendant()
    """
    jd_ut = jd - place.timezone / 24.
    
    positions = []
    for planet, p_id in planet_list.items():
        if planet == const._KETU:
            nirayana_long = ketu(sidereal_longitude(jd_ut, const._RAHU))
        else: # Ketu
            nirayana_long = sidereal_longitude(jd_ut, planet)
        constellation = int(nirayana_long / 30)
        coordinates = nirayana_long-constellation*30
        positions.append([p_id,coordinates, constellation])
    return positions
def _assign_planets_to_houses(planet_positions,bhava_houses,bhava_madhya_method=1):
    _bhava_houses = []#bhava_houses[:]
    for _bhava_house in bhava_houses:
        [_bhava_start,_bhava_mid,_bhava_end] = _bhava_house; planets_in_house = []
        if _bhava_end < _bhava_start: _bhava_end+=360
        for p,(h,long) in planet_positions:
            p_long = h*30+long
            if (p_long >= _bhava_start and p_long < _bhava_end) or \
                (p_long+360 >= _bhava_start and p_long+360 < _bhava_end):
                planets_in_house.append(p)
        if bhava_madhya_method==1 or bhava_madhya_method==5: # Rasi is based on bhava cusp or Equal Rasi method
            _bhava_houses.append([int(_bhava_mid/30),(_bhava_start,_bhava_mid,_bhava_end),planets_in_house])
        elif bhava_madhya_method==2: # Rasi is based on bhava start
            _bhava_houses.append([int(_bhava_start/30),(_bhava_start,_bhava_mid,_bhava_end),planets_in_house])
        elif bhava_madhya_method in [3,4]+list(const.western_house_systems.keys()): # Sripati / KP method / Western House System
            _bhava_houses.append([int(_bhava_start/30),(_bhava_start%360,_bhava_mid%360,_bhava_end%360),planets_in_house])
    return _bhava_houses
def _bhaava_madhya_new(jd, place,bhava_madhya_method=None):
    """
        returns house longitudes (start, cusp, end)
        @param jd: Julian Day number
        @param place: Place('name',latitude,longitude,timezone_hours)
        @param bhava_madhya_method:   
            1=> Equal Housing - Lagna in the middle start = lagna-15, end lagna+15; asc same for all houses
            2=> Equal Housing - Lagna as start
            3=> Sripati method.
            4=> KP Method (aka Placidus Houses method)
            5=> Each Rasi is the house (rasi is the house, 0 is start and 30 is end, asc is asc+rasi*30)
            'P':'Placidus','K':'Koch','O':'Porphyrius','R':'Regiomontanus','C':'Campanus','A':'Equal (cusp 1 is Ascendant)',
            'V':'Vehlow equal (Asc. in middle of house 1)','X':'axial rotation system','H':'azimuthal or horizontal system',
            'T':'Polich/Page (topocentric system)','B':'Alcabitus','M':'Morinus'        
        
        @return: [[house1_rasi,(house1_start,house1_cusp,house1_end)],(...),[house12_rasi,(house12_start,house12_cusp,house12_end)]]
    """
    if bhava_madhya_method is None: bhava_madhya_method = const.bhaava_madhya_method
    if not utils.is_valid_option(bhava_madhya_method,const.available_house_systems()):
        warn_msg = "bhava_madhya_method should be one of const.available_house_systems keys\n Value 1 assumed"
        warnings.warn(warn_msg)
        bhava_madhya_method = const.BHAVA_METHODS.KN_RAO_JHORA_DEFAULT
    ascendant_constellation, ascendant_longitude, _, _ = ascendant(jd,place)
    ascendant_full_longitude = (ascendant_constellation*30+ascendant_longitude)%360
    planet_positions = dhasavarga(jd,place,divisional_chart_factor=1)
    planet_positions = [[const._ascendant_symbol,(ascendant_constellation, ascendant_longitude)]] + planet_positions
    bhava_houses = []
    if bhava_madhya_method ==1: #Equal Housing - Lagna in the middle
        _bhava_mid = ascendant_full_longitude; 
        for h in range(12):
            _bhava_start = (_bhava_mid-15.0)%360; _bhava_end = (_bhava_mid+15.0)%360 
            bhava_houses.append((_bhava_start,_bhava_mid,_bhava_end))
            _bhava_mid = utils.norm360(_bhava_mid + 30)
        return _assign_planets_to_houses(planet_positions, bhava_houses,bhava_madhya_method=bhava_madhya_method)
    elif bhava_madhya_method ==2: #Equal Housing - Lagna as start
        _bhava_mid = ascendant_full_longitude; 
        for h in range(12):
            _bhava_start = _bhava_mid; _bhava_mid=(_bhava_start+15.0)%360; _bhava_end = (_bhava_mid+15.0)%360 
            bhava_houses.append((_bhava_start,_bhava_mid,_bhava_end))
            _bhava_mid = utils.norm360(_bhava_start + 30)
        return _assign_planets_to_houses(planet_positions, bhava_houses,bhava_madhya_method=bhava_madhya_method)
    elif bhava_madhya_method ==3: #Sripati method
        bm = bhaava_madhya_sripathi(jd, place); bm = bm[:]+[bm[0]]
        for h in range(12):
            _bhava_start = bm[h]; _bhava_mid = 0.5*(bm[h]+bm[h+1]); _bhava_end = bm[h+1] 
            bhava_houses.append((_bhava_start%360,_bhava_mid%360,_bhava_end%360))
        return _assign_planets_to_houses(planet_positions, bhava_houses,bhava_madhya_method=bhava_madhya_method)
    elif bhava_madhya_method ==4 or bhava_madhya_method in const.western_house_systems.keys(): #KP Method (aka swiss ephemeris method) or western house systems
        bm = bhaava_madhya_kp(jd, place) if bhava_madhya_method ==4 else bhaava_madhya_swe(jd, place, house_code=bhava_madhya_method)
        bm = bm[:]+[bm[0]]
        for h in range(12):
            bmh = bm[h]; bmh1 = bm[h+1]
            if bmh1 < bmh: bmh1+=360
            _bhava_start = bmh; _bhava_mid = 0.5*(bmh+bmh1); _bhava_end = bmh1 
            bhava_houses.append((_bhava_start%360,_bhava_mid%360,_bhava_end%360))
        return _assign_planets_to_houses(planet_positions, bhava_houses,bhava_madhya_method=bhava_madhya_method)
    elif bhava_madhya_method ==5: #Each Rasi is the house
        for h in range(12):
            h1 = (h+ascendant_constellation)%12
            _bhava_start = h1*30; _bhava_mid = _bhava_start + ascendant_longitude; _bhava_end = ((h1+1)%12)*30
            bhava_houses.append((_bhava_start%360,_bhava_mid%360,_bhava_end%360))
        return _assign_planets_to_houses(planet_positions, bhava_houses,bhava_madhya_method=bhava_madhya_method)
def bhaava_madhya(jd, place,bhava_method=None):
    """
        returns house longitudes
        @param jd: Julian Day number
        @param place: Place('name',latitude,longitude,timezone_hours)
        @param bhava_method:   
        bhava_method = 1 Swiss Ephemeres Ascendant Cusp Calculations
                     = 2 Sripati modifications from swiss calculations
        @return: [house longitudes as a list] # First element first house longitude and so on
    """
    if bhava_method is None: bhava_method = const.bhaava_madhya_method
    if bhava_method==1: # SWISS methof
        return bhaava_madhya_kp(jd, place)
    else: # SRIPATI METHOD
        return bhaava_madhya_sripathi(jd, place)
def bhaava_madhya_swe(jd,place,house_code='P'):
    """
        Acceptable house system codes in Swiss Ephemeris
        hsys= ‘P’     Placidus
            ‘K’     Koch
            ‘O’     Porphyrius
            ‘R’     Regiomontanus
            ‘C’     Campanus
            ‘A’ or ‘E’     Equal (cusp 1 is Ascendant)
            ‘V’     Vehlow equal (Asc. in middle of house 1)
            ‘X’     axial rotation system
            ‘H’     azimuthal or horizontal system
            ‘T’     Polich/Page (“topocentric” system)
            ‘B’     Alcabitus
            ‘G’     Gauquelin sectors
            ‘M’     Morinus
        
    """
    if house_code not in const.western_house_systems.keys():
        warn_msg = "house_code should be one of const.western_house_systems keys\n Value 1 assumed"
        warnings.warn(warn_msg)
        house_code = 'P'
    hsys = bytes(house_code,encoding='ascii')
    _, lat, lon, tz = place
    jd_utc = jd - (tz / 24.)
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SIDEREAL
    return list(swe.houses_ex(jd_utc, lat, lon,hsys, flags = flags)[0])
def bhaava_madhya_kp(jd,place):
    """
        Compute the mid angle / cusp of each of each house.
        0th element is ascendant, 9th element is mid-heaven (mid coeli) etc 
        KP is same as Swiss ephemeris Placidus method
    """
    _, lat, lon, tz = place
    jd_utc = jd - (tz / 24.)
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SIDEREAL
    return list(swe.houses_ex(jd_utc, lat, lon, hsys=b'P', flags = flags)[0])
def bhaava_madhya_sripathi(jd, place):
    bm = bhaava_madhya_kp(jd, place)
    bmf = [0,3,6,9,12]
    for b in bmf[1:]:
        ib = bmf.index(b)
        bi1 = bmf[ib-1]%12
        bi2 = bmf[ib]%12
        b1 = bm[bi1]
        b2 = bm[bi2]
        if b2 < b1:
            b2 += 360
        bd = abs(b2-b1)/3.0
        #print(ib,bi1,bm[bi1],bi2,bm[bi2],bd)
        bm[(bi1+1)%12] = (bm[bi1%12]+bd)%360
        bm[(bi2-1)%12] = (bm[bi2%12]-bd)%360
        #print((bi1+1)%12,bm[(bi1+1)%12],(bi2-1)%12,bm[(bi2-1)%12])
    return bm
def ascendant(jd, place,dhasa_progression_correction=0.0):
    """
        Compute Lagna (=ascendant) position/longitude at any given time & place
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: [constellation of Lagna, longitude of lagna, Lagna nakshatra number, Lagna paadham number]
    """
    _, lat, lon, tz = place
    jd_utc = jd - (tz / 24.)
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    nirayana_lagna = utils.norm360(swe.houses_ex(jd_utc, lat, lon, flags = flags)[1][0]+dhasa_progression_correction)
    nak_no,paadha_no,_ = nakshatra_pada(nirayana_lagna)
    constellation = int(nirayana_lagna / 30)
    coordinates = nirayana_lagna-constellation*30
    return [constellation, coordinates, nak_no, paadha_no]    
def dasavarga_from_long(longitude, divisional_chart_factor=1):
    """
        Calculates the dasavarga-sign in which given longitude falls
        @param longitude: longitude of the planet
        @param divisional_chart_factor: divisional chart index as below. 
          divisional_chart_factor = 1=> Rasi, 2 => Hora, 3=>Drekana 4=>Chaturthamsa 5=>Panchamsa, 6=>Shashthamsa
          7=>Saptamsa, 8=>Ashtamsa, 9=>Navamsa, 10=>Dasamsa, 11=>Rudramsa, 12=>Dwadamsa, 16=>Shodamsa, 
          20=>Vimsamsa, 24=>Chaturvimsamsa, 27=>Nakshatramsa, 30=>Trisamsa, 40=>Khavedamsa, 
          45=>Akshavedamsa, 60=>Shastyamsa
        @return: constellation,longitude within_raasi
            0 = Aries, 1 = Taurus, ..., 11 = Pisces
    """
    #if divisional_chart_factor not in const.division_chart_factors:
    #    raise ValueError("Wrong divisional_chart_factor",divisional_chart_factor,' Valid value:',const.division_chart_factors)
    one_pada = (360.0 / (12 * divisional_chart_factor))  # There are also 108 navamsas
    one_sign = 12.0 * one_pada    # = 40 degrees exactly
    signs_elapsed = longitude / one_sign
    fraction_left = signs_elapsed % 1
    constellation = int(fraction_left * 12)
    long_in_raasi = (longitude-(constellation*30)) % 30
    " if long_in_raasi 30 make it and zero and add a rasi"
    if int(long_in_raasi+const.one_arc_second) == 30:
        long_in_raasi = 0; constellation = (constellation+1)%12
    return constellation,long_in_raasi

navamsa_from_long = lambda longitude: dasavarga_from_long(longitude,9) 

# http://www.oocities.org/talk2astrologer/LearnAstrology/Details/Navamsa.html
# Useful for making D9 divisional chart
def navamsa_from_long_old(longitude):
    """Calculates the navamsa-sign in which given longitude falls
    0 = Aries, 1 = Taurus, ..., 11 = Pisces
    """
    one_pada = (360 / (12 * 9))  # There are also 108 navamsas
    one_sign = 12 * one_pada    # = 40 degrees exactly
    signs_elapsed = longitude / one_sign
    fraction_left = signs_elapsed % 1
    return int(fraction_left * 12)

def _dhasavarga(jd, place,divisional_chart_factor=1):
    """
        Calculate planet positions for a given divisional chart index
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param divisional_chart_factor: divisional chart index as below. 
          divisional_chart_factor = 1=> Rasi, 2 => Hora, 3=>Drekana 4=>Chaturthamsa 5=>Panchamsa, 6=>Shashthamsa
          7=>Saptamsa, 8=>Ashtamsa, 9=>Navamsa, 10=>Dasamsa, 11=>Rudramsa, 12=>Dwadamsa, 16=>Shodamsa, 
          20=>Vimsamsa, 24=>Chaturvimsamsa, 27=>Nakshatramsa, 30=>Trisamsa, 40=>Khavedamsa, 
          45=>Akshavedamsa, 60=>Shastyamsa
        @return: 2D List of planet positions in the following format:
        [ [planet_index,[planet_raasi, planet_longitude],...]
        The planet index is in range [0..8]
        NOTE:DOES NOT INCLUDE ASCENDANT POSITION AND LONGITUDE
        TO GET ASCENDANT CALL: dasavarga_from_long()
    """
    jd_utc = jd - place.timezone / 24.
    positions = []
    for planet in planet_list:
        p_id = planet_list.index(planet)
        if planet != const._KETU:
            nirayana_long = sidereal_longitude(jd_utc, planet)
        else: # Ketu
            nirayana_long = ketu(sidereal_longitude(jd_utc, const._RAHU)) # 7 = swe.RAHU
        divisional_chart = dasavarga_from_long(nirayana_long,divisional_chart_factor)
        positions.append([p_id, divisional_chart])
    return positions
def dhasavarga(jd, place,divisional_chart_factor=1,set_rahu_ketu_as_true_nodes=None,include_western_planets=None,
               dhasa_progression_correction=0.0):
    """
        Calculate planet positions for a given divisional chart index
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @param divisional_chart_factor: divisional chart index as below. 
          divisional_chart_factor = 1=> Rasi, 2 => Hora, 3=>Drekana 4=>Chaturthamsa 5=>Panchamsa, 6=>Shashthamsa
          7=>Saptamsa, 8=>Ashtamsa, 9=>Navamsa, 10=>Dasamsa, 11=>Rudramsa, 12=>Dwadamsa, 16=>Shodamsa, 
          20=>Vimsamsa, 24=>Chaturvimsamsa, 27=>Nakshatramsa, 30=>Trisamsa, 40=>Khavedamsa, 
          45=>Akshavedamsa, 60=>Shastyamsa
        @return: 2D List of planet positions in the following format:
        [ [planet_index,[planet_raasi, planet_longitude],...]
        The planet index is in range [0..8]
        NOTE:DOES NOT INCLUDE ASCENDANT POSITION AND LONGITUDE
        TO GET ASCENDANT CALL: ascendant()
    """
    global planet_list
    """ Below portion commented in V4.8.7 - it is altering/forcing other than configured values  and will be removed
    if set_rahu_ketu_as_true_nodes is None: set_rahu_ketu_as_true_nodes = const._use_true_nodes_for_rahu_ketu
    if include_western_planets is None: include_western_planets = const._INCLUDE_URANUS_TO_PLUTO
    set_planet_list(set_rahu_ketu_as_true_nodes=set_rahu_ketu_as_true_nodes,
                    include_western_planets=include_western_planets)
    """
    jd_utc = jd - place.timezone / 24.
    positions = []
    for planet,p_id in planet_list.items():
        if p_id==const.KETU_ID: continue
        nirayana_long = utils.norm360(sidereal_longitude(jd_utc, planet)+dhasa_progression_correction)
        divisional_chart = dasavarga_from_long(nirayana_long,divisional_chart_factor)
        positions.append([p_id, divisional_chart])
        if p_id == const.RAHU_ID:
            p_id = planet_list[const._KETU]
            ketu_long = utils.norm360(nirayana_long+180)
            divisional_chart = dasavarga_from_long(ketu_long,divisional_chart_factor)
            positions.append([p_id, divisional_chart])
    positions = sorted(positions, key=lambda x: -1 if x[0] == 'L' else x[0])
    return positions
def declination_of_planets(jd,place):
    """
        return declination of planets
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return: declination as a list
        first element for sun and last element for saturn
        
    """
    _ayanamsa = get_ayanamsa_value(jd)
    pp = dhasavarga(jd,place,divisional_chart_factor=1)[:7]
    bhujas = [0 for _ in const.SUN_TO_SATURN]
    north_south_sign = [1 for _ in const.SUN_TO_SATURN]
    for p,(h,long) in pp:
        p_long = h*30 + long+_ayanamsa #V4.5.0
        if p_long >= 0.0 and p_long < 180.0: # North
            north_south_sign[p] = -1
            if p in [const.SUN_ID, const.MARS_ID, const.JUPITER_ID, const.VENUS_ID]: # [0,2,4,5]:
                north_south_sign[p] = 1
        else: # South
            north_south_sign[p] = -1
            if p in [const.MOON_ID, const.SATURN_ID]: #[1,6]:
                north_south_sign[p] = 1
        bhujas[p] = p_long%360
        if p_long > 90.0 and p_long < 180.0:
            bhujas[p] = 180.0 - p_long
        elif p_long > 180.0 and p_long < 270.0:
            bhujas[p] = p_long - 180.0
        elif p_long > 270.0 and p_long < 360.0:
            bhujas[p] = 360.0 - p_long
        bhujas[p] = round(bhujas[p],2)
    north_south_sign[3] = 1
    bd = [0,362/60.0,703/60.0,1002/60.0,1238/60.0,1388/60.0,1440/60.0]
    bx = [i*15 for i in const.SUN_TO_SATURN]
    declinations = [0 for _ in const.SUN_TO_SATURN]
    for p in const.SUN_TO_SATURN:
        declinations[p] = north_south_sign[p] * utils.inverse_lagrange(bd, bx, bhujas[p])
    return declinations
""" TODO: Upagrah longitudes to be computed from planet positions using ayanamsa, div factor, chart method etc """
### Upagraha longitudes
_dhuma_longitude = lambda sun_long: (sun_long+133+20.0/60) % 360
def _vyatipaata_longitude(sun_long):
    dhuma = _dhuma_longitude(sun_long)
    return ((360.0 - dhuma) %360 if const.vyatipada_calculation_method == 1
            else (dhuma + 53 + 2.0 / 3.0)) % 360
_parivesha_longitude = lambda sun_long: (_vyatipaata_longitude(sun_long)+180.0) % 360
_indrachaapa_longitude = lambda sun_long: (360.0-_parivesha_longitude(sun_long))%360
_upaketu_longitude = lambda sun_long: (sun_long-30.0)%360
def solar_upagraha_longitudes(solar_longitude,upagraha, dhasa_progression_correction=0.0):
    """
        Get logitudes of solar based upagrahas
        ['dhuma', 'vyatipaata', 'parivesha', 'indrachaapa', 'upaketu']
        @param jd: Jilian day number for the date/time
        @param upagraha: one of the values from ['dhuma', 'vyatipaata', 'parivesha', 'indrachaapa', 'upaketu']
        @param divisional_chart_factor: divisional chart factor
          divisional_chart_factor = 2 => Hora, 3=>Drekana 4=>Chaturthamsa 5=>Panchamsa, 6=>Shashthamsa
          7=>Saptamsa, 8=>Ashtamsa, 9=>Navamsa, 10=>Dasamsa, 11=>Rudramsa, 12=>Dwadamsa, 16=>Shodamsa, 
          20=>Vimsamsa, 24=>Chaturvimsamsa, 27=>Nakshatramsa, 30=>Trisamsa, 40=>Khavedamsa, 
          45=>Akshavedamsa, 60=>Shastyamsa
        @return: [constellation,longitude]
    """
    if upagraha.lower() in const._solar_upagraha_list:
        import sys
        func_name = '_' + upagraha + "_longitude"
        long = getattr(sys.modules[__name__], func_name)(solar_longitude)
        constellation,coordinates = dasavarga_from_long(long+dhasa_progression_correction)
        return [constellation,coordinates]
"""
  Kaala rises at the middle of Sun’s part. In other words, we find the time at the
  middle of Sun’s part and find lagna rising then. That gives Kaala’s longitude.
"""
kaala_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.SUN_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
""" Mrityu rises at the middle of Mars’s part."""
mrityu_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.MARS_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
""" Artha Praharaka rises at the middle of Mercury’s part."""
artha_praharaka_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.MERCURY_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
""" Yama Ghantaka rises at the middle of Jupiter’s part. """
yama_ghantaka_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.JUPITER_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
""" Gulika rises at the start of Saturn’s part. (Book says middle) """
gulika_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.SATURN_ID,upagraha_part='begin',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
""" Maandi rises at the middle of Saturn’s part. (Book says start) """
maandi_longitude = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    upagraha_longitude(dob,tob,place,planet_index=const.SATURN_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )
# Raw Getters for High-Precision Math
kaala_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.SUN_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

mrityu_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.MARS_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

artha_praharaka_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.MERCURY_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

yama_ghantaka_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.JUPITER_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

gulika_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.SATURN_ID,upagraha_part='begin',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

maandi_raw = (
    lambda dob,tob,place,dhasa_progression_correction=0.0:
    _upagraha_longitude_full(dob,tob,place,planet_index=const.SATURN_ID,upagraha_part='middle',
                       dhasa_progression_correction=dhasa_progression_correction)
    )

def _upagraha_longitude_full(dob,tob,place,planet_index,upagraha_part='middle',dhasa_progression_correction=0.0):
    jd_utc = utils.gregorian_to_jd(Date(dob.year,dob.month,dob.day))
    
    # 1. Use [0] (float hours) directly from your sunrise/sunset functions
    srise_res = sunrise(jd_utc, place)
    sset_res = sunset(jd_utc, place)
    
    srise = srise_res[0]
    sset = sset_res[0]

    planet_part = const.day_rulers[vaara(utils.julian_day_number(dob, tob), place)].index(planet_index)            
    tob_hrs = tob[0]+tob[1]/60.0+tob[2]/3600.0

    # 2. Handle previous day/next day using JD comparison if needed, 
    # but keep using the float hours for calculations
    if tob_hrs < srise:
        sset = sunset((jd_utc-1), place)[0]
        planet_part = const.night_rulers[vaara(utils.julian_day_number(dob, tob), place)].index(planet_index)
    if tob_hrs > sset:
        srise = sunrise((jd_utc+1), place)[0]
        planet_part = const.night_rulers[vaara(utils.julian_day_number(dob, tob), place)].index(planet_index)
            
    day_dur = abs(sset - srise)
    one_part = day_dur/8.0
    planet_start_time = srise + planet_part * one_part
    
    if upagraha_part.lower()=='middle':
        planet_middle_time = planet_start_time + 0.5 * one_part
        jd_kaala = swe.julday(dob.year,dob.month,dob.day,planet_middle_time)
    else:
        jd_kaala = swe.julday(dob.year,dob.month,dob.day,planet_start_time)

    clong = ascendant(jd_kaala, place)
    upagraha_long = utils.norm360(clong[0]*30+clong[1] + dhasa_progression_correction)
    return upagraha_long

def upagraha_longitude(dob,tob,place,planet_index,upagraha_part='middle',dhasa_progression_correction=0.0):
    """
      get upagraha longitude from dob,tob, place-lat/long and day/night ruling planet's part
      @param dob Date of birth as Date(year,month,day)
      @param tob Time of birth as (hours,minutes,seconds)
      @param planet_index 0=Sun, 1=Moon, 2=Mars, 3=Mercury,4=Jupiter, 5=Venus, 6=Saturn
      @param upagraha_part = 'Middle' or 'Begin'
      Notes:
          Since Kaala is upagraha of Sun so planet_index should be 0
              Kaala rises at the middle of Sun’s part. In other words, we find the time at the
              middle of Sun’s part and find lagna rising then. That gives Kaala’s longitude.
          Since Mrityu is upagraha of Mars so planet_index should be 2
              Mrityu rises at the middle of Mars’s part.
          Since Artha Praharaka is upagraha of Mercury so planet_index should be 3
              Artha Praharaka rises at the middle of Mercury’s part.
          Since Kaala is upagraha of Jupiter so planet_index should be 4
              Yama Ghantaka rises at the middle of Jupiter’s part.
          Since Gulika is upagraha of Saturn so planet_index should be 6
              Gulika rises at the beginning of Saturn’s part.
          Since Maandi is upagraha of Saturn so planet_index should be 6
              Maandi rises at the middle of Saturn’s part.
          You can also use specific lambda functions.
              kaala_longitude(dob,tob,place,divisional_chart_factor)
              mrityu_longitude(dob,tob,place,divisional_chart_factor)
              artha_longitude(dob,tob,place,,divisional_chart_factor)
              yama_ghantaka_longitude(dob,tob,place,divisional_chart_factor)
              gulika_longitude(dob,tob,place,divisional_chart_factor)
              maandi_longitude(dob,tob,place,divisional_chart_factor)
      @return: [constellation of upagraha,upagraha_longitude within constellation]
    """
    """
        TODO: Upagraha longitudes are not matching with JHora for divisional charts
              Upagraha longitudes are based on sunrise times - how does sunrise time change in div charts?
    """
    upagraha_long = _upagraha_longitude_full(dob, tob, place, planet_index, upagraha_part, dhasa_progression_correction)
    constellation,coordinates = dasavarga_from_long(upagraha_long) #int(upagraha_long / 30)
    return [constellation,coordinates]
""" NOTE: Bhava Lagna Calculation in Section 5.2 of PVR Book should have mentioned DIVIDE BY 4 in Step (2) """
bhava_lagna = (
    lambda jd, place, dhasa_progression_correction=0.0,special_lagna_continuity=None:
        special_ascendant(
            jd,place,lagna_rate_factor=0.25, dhasa_progression_correction=dhasa_progression_correction,
            special_lagna_continuity=special_lagna_continuity)
        )
hora_lagna = (
    lambda jd,place,dhasa_progression_correction=0.0,special_lagna_continuity=None: 
        special_ascendant(jd,place,lagna_rate_factor=0.5,
                          dhasa_progression_correction=dhasa_progression_correction,
                          special_lagna_continuity=special_lagna_continuity)
        )
ghati_lagna = (
    lambda jd,place,dhasa_progression_correction=0.0,special_lagna_continuity=None: 
        special_ascendant(jd,place,lagna_rate_factor=1.25,
                          dhasa_progression_correction=dhasa_progression_correction,
                          special_lagna_continuity=special_lagna_continuity)
        ) 
vighati_lagna = (
    lambda jd,place,dhasa_progression_correction=0.0,special_lagna_continuity=None: 
        special_ascendant(jd,place,lagna_rate_factor=5.0,
                          dhasa_progression_correction=dhasa_progression_correction,
                          special_lagna_continuity=special_lagna_continuity)
        ) 
def special_ascendant(jd,place,lagna_rate_factor=1.0,dhasa_progression_correction=0.0,special_lagna_continuity=None):
    """
        Get constellation and longitude of special lagnas (Bhava,Hora,Ghati,vighati)
        @param jd: Julian day number
        @param place: Struct ('place name',latitude,longitude,time zone)
        @param lagna_rate_factor:    
            lagna_rate_factor   = 1 for Bhava Lagna
                                = 0.5 for Hora Lagna
                                = 5/4 for Ghati Lagna  
                                = 15.0 for vighati Lagna                          
        @param divisional_chart_factor: divisional chart factor
          divisional_chart_factor = 2 => Hora, 3=>Drekana 4=>Chaturthamsa 5=>Panchamsa, 6=>Shashthamsa
          7=>Saptamsa, 8=>Ashtamsa, 9=>Navamsa, 10=>Dasamsa, 11=>Rudramsa, 12=>Dwadamsa, 16=>Shodamsa, 
          20=>Vimsamsa, 24=>Chaturvimsamsa, 27=>Nakshatramsa, 30=>Trisamsa, 40=>Khavedamsa, 
          45=>Akshavedamsa, 60=>Shastyamsa
        @param special_lagna_continuity: Set to True to use the alternative definition that ensures 
            mathematical continuity around sunrise.
        @return: [special lagnas constellation, special lagna's longitude within constellation]
        Note: You can also individual lambda function for each special lagna without lagna_rate_factor
        Example: 
            bhava_lagna(jd,place,divisional_chart_factor)
            hora_lagna(jd,place,divisional_chart_factor)
            ghati_lagna(jd,place,divisional_chart_factor)
            vighati_lagna(jd,place,divisional_chart_factor)
        NOTE: There are separate functions for pranapada, indu,sree, bhrigu_bindhu, kunda with same arguments
    """
    if special_lagna_continuity is None: special_lagna_continuity = const.special_lagna_continuity
    _,_,_, time_of_birth_in_hours = jd_to_gregorian(jd)
    srise = sunrise(jd, place) #V2.3.1 Get sunrise JD - as we need sun longitude at sunrise
    sun_rise_hours = srise[0]
    time_diff_mins = (time_of_birth_in_hours-sun_rise_hours)*60
    from jhora.horoscope.chart import charts
    """ 
        Change in V3.6.3
        We need Sun position at sunrise. So we use srise[2] returned from sunrise function.
        Since sunrise function returns JD Local at sunrise we add local time here because charts will minus it to get UTC
    """
    jd_spl_lagna = jd if special_lagna_continuity else srise[2]+place.timezone/24
    pp = dhasavarga(jd_spl_lagna, place)
    sun_long = pp[const.SUN_ID][1][0]*30+pp[const.SUN_ID][1][1]
    spl_long = utils.norm360(sun_long + (time_diff_mins * lagna_rate_factor) + dhasa_progression_correction )
    da = dasavarga_from_long(spl_long)
    return da
def pranapada_lagna(
    jd,
    place,
    dhasa_progression_correction=0.0,
    special_lagna_continuity=None,
):
    """
    Calculate Pranapada Lagna.

    Classical rule:
        Convert time from sunrise to birth into vighatis.
        Divide by 15.
        Convert the result into signs and degrees.
        If Sun is in movable sign, add to Sun's longitude.
        If Sun is in fixed sign, add to 9th from Sun.
        If Sun is in dual sign, add to 5th from Sun.

    Parameters
    ----------
    jd : float
        Julian day number of birth.
    place : tuple / struct
        Place information: name, latitude, longitude, timezone.
    divisional_chart_factor : int
        Vargas such as 1=D1, 9=D9, 10=D10, etc.
    special_lagna_continuity : bool
        If True, use Sun longitude at sunrise.
        If False, use Sun longitude at birth time.

    Returns
    -------
    tuple
        Pranapada Lagna sign and longitude in requested divisional chart.
    """
    jd_utc = jd - place.timezone/24.0
    _vighati_lagna = vighati_lagna(jd, place,dhasa_progression_correction,
                            special_lagna_continuity=special_lagna_continuity)
    _vighati_long = _vighati_lagna[0]*30 + _vighati_lagna[1]
    sun_long = solar_longitude(jd_utc)
    sun_sign, _ = dasavarga_from_long(sun_long)
    # Movable: add directly.
    # Fixed: add 9th from Sun = +240 degrees.
    # Dual: add 5th from Sun = +120 degrees.
    if sun_sign in const.fixed_signs:
        offset = 240.0
    elif sun_sign in const.dual_signs:
        offset = 120.0
    else:
        offset = 0.0
    pranapada_longitude = utils.norm360(_vighati_long + offset + dhasa_progression_correction)
    da = dasavarga_from_long(pranapada_longitude)
    return da
def indu_lagna(jd,place,dhasa_progression_correction=0.0):  # BV Raman Method
    """
        Get constellation and longitude of indu lagna
        @param jd: Julian day number
        @param place: Struct ('place name',latitude,longitude,time zone)
        @return: [indu lagnas constellation, indu lagna's longitude within constellation]
    """
    il_factors = [30,16,6,8,10,12,1] # Sun to Saturn. Rahu/Ketu exempted
    jd_utc = jd - place.timezone/24.0
    moon_long_full = lunar_longitude(jd_utc)
    moon_house,moon_long = dasavarga_from_long(moon_long_full)
    asc = ascendant(jd, place)
    asc_house = asc[0]
    ninth_lord = const._house_owners_list[(asc_house+const.HOUSE_9)%12]
    ninth_lord_from_moon = const._house_owners_list[(moon_house+const.HOUSE_9)%12]
    il1 = (il_factors[ninth_lord]+il_factors[ninth_lord_from_moon])%12
    if il1==0: il1 = 12
    _indu_rasi = (moon_house+il1-1)%12
    return _indu_rasi,moon_long
def kunda_lagna(jd,place,dhasa_progression_correction=0.0):
    """
        Get constellation and longitude of kunda lagna
        @param jd: Julian day number
        @param place: Struct ('place name',latitude,longitude,time zone)
        @return: [kunda lagnas constellation, kunda lagna's longitude within constellation]
    """
    asc = ascendant(jd, place)
    al = asc[0]*30+asc[1]; al1 = utils.norm360(al*81+dhasa_progression_correction)
    spl = dasavarga_from_long(al1)
    return spl
def bhrigu_bindhu_lagna(jd,place,dhasa_progression_correction=0.0):
    """
        Get constellation and longitude of bhrigu bindhu lagna
        @param jd: Julian day number
        @param place: Struct ('place name',latitude,longitude,time zone)
        @return: [bhrigu bindhu lagnas constellation, bhrigu bindhu lagna's longitude within constellation]
    """
    jd_utc = jd - place.timezone/24.0
    moon_long_full = lunar_longitude(jd_utc)
    rahu_long_full = sidereal_longitude(jd_utc, const._RAHU)
    moon_add = 0 if moon_long_full > rahu_long_full else 360
    bb = utils.norm360(0.5*(rahu_long_full+moon_long_full+moon_add)+dhasa_progression_correction)
    return dasavarga_from_long(bb)
def sree_lagna(jd,place,dhasa_progression_correction=0.0):
    """
        Get constellation and longitude of Sree Lagna
        @param jd: Julian day number
        @param place: Struct ('place name',latitude,longitude,time zone)
        @return: [Sree lagna constellation, Sree lagna's longitude within constellation]
    """
    jd_utc = jd - place.timezone/24.0
    moon_long = lunar_longitude(jd_utc)
    asc = ascendant(jd, place)
    asc_long = asc[0]*30+asc[1]
    sl = sree_lagna_from_moon_asc_longitudes(moon_long, asc_long)
    return sl
def sree_lagna_from_moon_asc_longitudes(moon_longitude,ascendant_longitude):
    moon_long = moon_longitude
    asc_long = ascendant_longitude
    reminder = nakshatra_pada(moon_long)[2]
    reminder_fraction = reminder * 27
    sree_long = asc_long + reminder_fraction
    constellation,coordinates = dasavarga_from_long(sree_long)
    return constellation,coordinates
def tamil_solar_month_and_date_V4_3_8(panchanga_date,place):
    """
        Returns tamil month and date (e.g. Aadi 28 )
        @param panchanga_date: Date Struct (year, month, day)
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return: tamil_month_number, tamil_date_number
        i.e. [0..11, 1..32]
        Note: Tamil month is sankranti based solar month - not lunar month
    """ 
    start_jd = utils.gregorian_to_jd(panchanga_date)
    sl = solar_longitude(start_jd)
    _tamil_month = int(sl/30)
    sunset_count=1
    while True:
        if sl%30<1 and sl%30>0:
            break
        start_jd -= 1
        sl = solar_longitude(start_jd)
        sunset_count+=1
    _tamil_day = sunset_count
    return _tamil_month, _tamil_day
def tamil_solar_month_and_date_V4_3_5(panchanga_date,place): # _V4_3_5
    """
        Returns tamil month and date (e.g. Aadi 28 )
        @param panchanga_date: Date Struct (year, month, day)
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return: tamil_month_number, tamil_date_number
        i.e. [0..11, 1..32]
        Note: Tamil month is sankranti based solar month - not lunar month
        And it is very sensitive to solar longitude. 
    """ 
    jd = utils.gregorian_to_jd(panchanga_date)
    sunset_jd = sunset(jd, place)[2]
    sl = solar_longitude(sunset_jd)
    _tamil_month = int(sl/30)
    daycount=1
    while True:
        if sl%30<1 and sl%30>0:
            break
        sunset_jd -= 1
        sl = solar_longitude(sunset_jd)
        daycount+=1
    _tamil_day = daycount
    return _tamil_month, _tamil_day#, month_days
def tamil_solar_month_and_date_RaviAnnnaswamy(panchanga_date,place): #_RaviAnnnaswamy V4.4.0
    jd = utils.julian_day_number(panchanga_date, (10,0,0))
    jd_set = sunset(jd, place)[2]
    jd_utc = jd_set - place.timezone/24
    sr = solar_longitude(jd_utc)
    tamil_month = int(sr/30)
    daycount=1
    while True:
        if sr%30<1 and sr%30>0:
            break
        jd_utc -= 1
        sr = solar_longitude(jd_utc)
        daycount+=1
    return tamil_month, daycount
def tamil_solar_month_and_date(panchanga_date,place,tamil_month_method=None,base_time=0,use_utc=True):
    """
        Returns tamil month and date (e.g. Aadi 28 )
        @param panchanga_date: Date Struct (year, month, day)
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @param base_time: 0 => sunset time, 1 => sunrise time 2 => midday time
        @param use_utc: True (default) use uninversal time
        @return: tamil_month_number, tamil_date_number
        i.e. [0..11, 1..32]
        Note: Tamil month is sankranti based solar month - not lunar month
        And it is very sensitive to solar longitude. 
    """
    if tamil_month_method is None: tamil_month_method = const.tamil_month_method
    if tamil_month_method==const.TAMIL_MONTH_METHOD.BASED_ON_LOCAL_10AM: # sunset and UTC
        return tamil_solar_month_and_date_RaviAnnnaswamy(panchanga_date, place)
    elif tamil_month_method==const.TAMIL_MONTH_METHOD.BASED_ON_SUNSET_TIME: # sunset jd as starting jd
        return tamil_solar_month_and_date_V4_3_5(panchanga_date, place)
    elif tamil_month_method==const.TAMIL_MONTH_METHOD.BASED_ON_BIRTH_TIME: # startjd at 10AM
        return tamil_solar_month_and_date_V4_3_8(panchanga_date, place)
    else: #
        return tamil_solar_month_and_date_new(panchanga_date, place, base_time, use_utc)
def tamil_solar_month_and_date_new(panchanga_date,place,base_time=0,use_utc=True): # V4.4.0
    """
        @param base_time: 0 => sunset time, 1 => sunrise time 2 => midday time
        @param use_utc: True (default) use uninversal time
    """
    jd = utils.julian_day_number(panchanga_date, (10,0,0))
    jd_base = sunset(jd, place)[2] if base_time==0 else (sunrise(jd,place)[2] if base_time==1 else midday(jd, place)[1])
    jd_utc = jd_base - place.timezone/24 if use_utc else jd_base
    sr = solar_longitude(jd_utc)
    tamil_month = int(sr/30)
    daycount=1
    while True:
        if sr%30<1 and sr%30>0:
            break
        jd -= 1
        jd_base = sunset(jd, place)[2] if base_time==0 else (sunrise(jd,place)[2] if base_time==1 else midday(jd, place)[1])
        jd_utc = jd_base - place.timezone/24 if use_utc else jd_base
        sr = solar_longitude(jd_utc)
        daycount+=1
    return tamil_month, daycount
def tamil_solar_month_and_date_from_jd(jd,place):
    return solar_month_date(jd, place, sankranti_rule=const.SANKRANTI_RULE.TAMIL_NADU_SUNSET_RULE)
def days_in_tamil_month(panchanga_date,place):
    """ get # of days in that tamil month """
    jd = utils.gregorian_to_jd(panchanga_date)
    sunset_jd = sunset(jd, place)[2]
    sl = solar_longitude(sunset_jd)
    _,daycount = tamil_solar_month_and_date(panchanga_date, place)
    while True:
        if sl%30<30 and sl%30>29:
            break
        sunset_jd += 1
        sl = solar_longitude(sunset_jd)
        daycount+=1
    month_days = daycount
    return month_days
def _previous_sankranti_date_new(panchanga_date,place,zodiac=None):
    prev_day = utils.previous_panchanga_day(panchanga_date, minus_days=1)
    if zodiac is None:
        t_month,_ = tamil_solar_month_and_date(prev_day, place)
        multiple = t_month * 30
    else:
        multiple = zodiac * 30
    #print(prev_day,t_month,t_day)
    jd = utils.gregorian_to_jd(prev_day)
    sunset_jd = sunset(jd, place)[2]
    sl = solar_longitude(sunset_jd)
    while True:
        slq,slr = divmod(sl,30)
        if slr<1 and slr>0 and zodiac is None:
            break
        if slr<1 and slr>0 and zodiac is not None and int(slq)==int(zodiac):
            break
        sunset_jd -= 1
        sl = solar_longitude(sunset_jd)
    sank_date = jd_to_gregorian(sunset_jd)
    sank_sunrise = sunrise(sunset_jd,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    tamil_month,tamil_day = tamil_solar_month_and_date(sank_date, place)
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    solar_longs = [ solar_longitude(sank_sunrise + t) % 360 for t in offsets ]
    solar_hour = utils.inverse_lagrange(offsets, solar_longs, multiple % 360) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    solar_hour1 = (sank_sunrise + solar_hour - sank_jd_utc)*24+place.timezone
    #print('before tm call sank date',sank_date,solar_hour,solar_hour1)
    sank_date,solar_hour1 = utils._convert_to_tamil_date_and_time(sank_date, solar_hour1,place)
    #print('after tm call sank date',sank_date)
    return sank_date, solar_hour1,tamil_month,tamil_day
def previous_sankranti_date(panchanga_date,place):
    """
        Get the previous sankranti date (sun entry to a raasi)
        @param panchanga_date: Date Struct (year, month, day)
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return: sankranti_date as Struct(y,m,d), sankranti time as float hours,tamil_month_number, tamil_date_number        
    """
    next_day = utils.previous_panchanga_day(panchanga_date, 1)# Date(panchanga_date[0],panchanga_date[1],panchanga_date[2]-1)
    t_month,_ = tamil_solar_month_and_date(next_day, place)
    multiple = t_month * 30
    #print(next_day,t_month,t_day)
    jd = utils.gregorian_to_jd(next_day)
    sunset_jd = sunset(jd, place)[2]
    sl = solar_longitude(sunset_jd)
    while True:
        #print(sunset_jd,sl,multiple)
        if sl%30<1 and sl%30>0:
            break
        sunset_jd -= 1
        sl = solar_longitude(sunset_jd)
    sank_date = jd_to_gregorian(sunset_jd)
    sank_sunrise = sunrise(sunset_jd,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    tamil_month,tamil_day = tamil_solar_month_and_date(sank_date, place)
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    solar_longs = [ solar_longitude(sank_sunrise + t) % 360 for t in offsets ]
    solar_hour = utils.inverse_lagrange(offsets, solar_longs, multiple % 360) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    solar_hour1 = (sank_sunrise + solar_hour - sank_jd_utc)*24+place.timezone
    sank_date,solar_hour1 = utils._convert_to_tamil_date_and_time(sank_date, solar_hour1,place)
    return sank_date, solar_hour1,tamil_month,tamil_day
def next_sankranti_date_from_jd(jd,place, direction=1, increment_days=0.01, precision=0.1, raasi=None):
    """ Returns next sankranti date (y,m,d,fh) and sankranti_zodiac/raasi. Does not return tamil day """
    npe = next_planet_entry_date(const.SUN_ID, jd, place, direction=direction, increment_days=increment_days,
                                  precision=precision, raasi=raasi)
    return utils.jd_to_gregorian(npe[0]),int(npe[1]//30),1 # On Sankranti day is always 1
def previous_sankranti_date_from_jd(jd,place, increment_days=0.01, precision=0.1, raasi=None):
    """ Returns previous sankranti date (y,m,d,fh) and sankranti_zodiac/raasi. Does not return tamil day """
    ppe = previous_planet_entry_date(const.SUN_ID, jd, place, increment_days=increment_days,precision=precision, raasi=raasi)
    return utils.jd_to_gregorian(ppe[0]),int(ppe[1]//30),1 # On Sankranti day is always 1
def next_sankranti_date(panchanga_date,place):
    """
        Get the next sankranti date (sun entry to a raasi)
        @param panchanga_date: Date Struct (year, month, day)
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return: sankranti_date as Struct(y,m,d), sankranti time as float hours,tamil_month_number, tamil_date_number        
    """
    next_day = utils.previous_panchanga_day(panchanga_date, 1)# Date(panchanga_date[0],panchanga_date[1],panchanga_date[2]-1)
    t_month,_ = tamil_solar_month_and_date(next_day, place)
    multiple = (t_month+1)%12 * 30
    #print(next_day,t_month,t_day)
    jd = utils.gregorian_to_jd(next_day)
    sunset_jd = sunset(jd, place)[2]
    sl = solar_longitude(sunset_jd)
    while True:
        #print(sunset_jd,sl,multiple,jd_to_gregorian(sunset_jd))
        if sl%30<1 and sl%30>0:
            break
        sunset_jd += 1
        sl = solar_longitude(sunset_jd)
    sank_date = jd_to_gregorian(sunset_jd)
    sank_sunrise = sunrise(sunset_jd,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    tamil_month,tamil_day = tamil_solar_month_and_date(sank_date, place)
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    solar_longs = [ solar_longitude(sank_sunrise + t) % 360 for t in offsets ]
    solar_hour = utils.inverse_lagrange(offsets, solar_longs, multiple % 360) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    solar_hour1 = (sank_sunrise + solar_hour - sank_jd_utc)*24+place.timezone
    sank_date,solar_hour1 = utils._convert_to_tamil_date_and_time(sank_date, solar_hour1,place)
    return sank_date, solar_hour1,tamil_month,tamil_day # V2.3.0 date returned as tuple
def __next_solar_jd(jd,place,sun_long):
    """
        TODO: Handle While loop if not converging - provide max count to stop
    """
    jd_next = jd
    sl = solar_longitude(jd_next)
    while True:
        #print(jd_next,sl,sun_long,jd_to_gregorian(jd_next))
        sank_date = swe.revjul(jd_next)
        #print('sank_date',sank_date,sun_long,sl,sun_long+1)
        if sl<sun_long+1 and sl>sun_long:
            jd_next -= 1
            break
        jd_next += 1
        sl = solar_longitude(jd_next)
    sank_date = jd_to_gregorian(jd_next)
    #print('sank_date',sank_date)
    sank_sunrise = sunrise(jd_next,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    solar_longs = [ (solar_longitude(sank_sunrise + t)) for t in offsets ]
    #print(solar_longs,sun_long)
    solar_hour = utils.inverse_lagrange(offsets, solar_longs, sun_long) # Do not move % 360 above
    #print('solar_hour',solar_hour)
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    solar_hour1 = (sank_sunrise + solar_hour - sank_jd_utc)*24+place.timezone
    next_solar_jd = swe.julday(sank_date[0],sank_date[1],sank_date[2],solar_hour1)
    return next_solar_jd    
def next_solar_date(
    jd_at_dob,
    place,
    years=1,
    months=1,
    sixty_hours=1,
    sookshma=1,
    prana=1,
    dehantar=1,
    use_sidereal=False,
):
    """
    Returns the next date at which the Sun's longitude equals its longitude at jd_at_dob,
    shifted by Varsha/Tajaka subdivisions (years → months → sixty_hours → sookshma → prana → dehantar).

    Parameters
    ----------
    jd_at_dob : float
        Julian Day at time of birth.
    place : tuple
        Place Struct ('place', latitude, longitude, timezone) used by downstream functions.
    years : int, default 1
        Varsha index (1 = birth year).
    months : int, default 1
        Antar index within the year (1..12).
    sixty_hours : int, default 1
        Pratyantar index within the month (1..12); each step ≈ 2.5° ≈ ~60h.
    sookshma : int, default 1
        Sookshma index within the pratyantar (1..12).
    prana : int, default 1
        Prana index within the sookshma (1..12).
    dehantar : int, default 1
        Dehantar index within the prana (1..12).
    use_sidereal : bool, default False
        If True, use const.sidereal_year; else const.tropical_year.

    Returns
    -------
    float
        Julian Day for the matching solar date.
    """
    # Fast-path: if everything is the first sub-period, return DOB JD.
    if (years == 1 and months == 1 and sixty_hours == 1
        and sookshma == 1 and prana == 1 and dehantar == 1):
        return jd_at_dob
    # Ordered 12-fold denominators for each level (year:1, month:12, …)
    denominators = [
        ("years",        1,        years),
        ("months",       12,       months),
        ("sixty_hours",  12**2,    sixty_hours),
        ("sookshma",     12**3,    sookshma),
        ("prana",        12**4,    prana),
        ("dehantar",     12**5,    dehantar),
    ]
    # Compute cumulative fraction of the year from birth
    frac_of_year = 0.0
    for _, denom, idx in denominators:
        # Each index is 1-based; index==1 means "no additional offset" at that level.
        frac_of_year += (int(idx) - 1) / float(denom)
    # Sun's natal longitude (absolute in degrees 0..360)
    sun_long_at_dob = dhasavarga(jd_at_dob, place, divisional_chart_factor=1)[0][1]
    sun_long_at_dob = sun_long_at_dob[0] * 30.0 + sun_long_at_dob[1]
    # Target longitude and time guess
    sun_long_next = (sun_long_at_dob + 360.0 * frac_of_year) % 360.0
    year_len = const.sidereal_year if use_sidereal else const.tropical_year
    jd_next_guess = jd_at_dob + year_len * frac_of_year
    return __next_solar_jd(jd_next_guess, place, sun_long_next)
def _next_solar_date(jd_at_dob,place,years=1,months=1,sixty_hours=1):
    """
        returns the next date at which sun's longitue is same as at jd_at_dob (at birth say)
        For example if someone was born on 1970,2,10 and years = 10, 
        will return date in 1979 at which sun longitude is same as calculated at (1970,2,10)
        These are used for Tajaka yearly/monthly/shashti-hora(60hr) charts
        @param jd_at_dob: Julian number at the time of birth
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @param year: Number of years since birth (year=1 for the birth year)
        @param months: Number of months from the birth month (month=1 for the same birth month)
        @param sixty_hours: Number of 60 hr count
        @return: julian number for the matching solar date
    """
    if (years==1 and months==1 and sixty_hours==1): return jd_at_dob
    sun_long_at_dob = dhasavarga(jd_at_dob, place,divisional_chart_factor=1)[0][1]
    sun_long_at_dob = sun_long_at_dob[0]*30+sun_long_at_dob[1]
    (y,m,d,fh) = swe.revjul(jd_at_dob)
    #print((int(sun_long_at_dob/30),utils.to_dms(sun_long_at_dob%30,is_lat_long='plong')),(y,m,d,utils.to_dms(fh)))
    sun_long_extra = ((years-1)*360+(months-1)*30+(sixty_hours-1)*2.5)%360
    jd_extra = (((years-1)+(months-1)/12+(sixty_hours-1)/144)*const.tropical_year) #const.sidereal_year)
    #print('jd_extra',jd_extra)
    jd_next = jd_at_dob+jd_extra
    #print('jd_next',jd_next,swe.revjul(jd_next))
    #print('sun_long_extra',sun_long_extra)
    sun_long_next = (sun_long_at_dob+sun_long_extra)%360
    #print((years,months,sixty_hours),(int(sun_long_next/30),utils.to_dms(sun_long_next%30,is_lat_long='plong')),(y,m,d,utils.to_dms(fh)))
    return __next_solar_jd(jd_next,place, sun_long_next)
def next_annual_solar_date_approximate(dob,tob,years):
    week_days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    tobh = (tob[0]+tob[1]/60+tob[2]/3600)/24
    jd_at_dob = utils.julian_day_number(dob,tob)
    weekday_of_dob = ceil(jd_at_dob % 7)
    acsp = {k:d+(h+m/60+s/3600)/24 for k,(d,h,m,s) in const.annual_chart_solar_positions.items() }
    d = sum(acsp[x] for x in [int(y)*(10**(len(str(years-1))-i-1)) for i,y in enumerate(str(years-1))])
    dy,dh = (int(d),d%1)
    weekday_increment = int(weekday_of_dob+dy)%7
    bday = date(dob[0]+years-1,dob[1],dob[2])
    bwd = (bday.weekday()+1)%7
    #print('find nearest',week_days[weekday_increment],'to',bwd)
    bday1 = timedelta( (weekday_increment-bwd) % 7 )
    bday0 = -timedelta( (bwd-weekday_increment) % 7 )
    dday = bday+min(bday0,bday1)
    #print(bday0,bday,bday1,dday)
    nd, nh = (int(tobh + dh),(tobh+dh)%1*24)
    dday += timedelta(days=nd)
    #print(dday,utils.to_dms(nh))
    next_jd = utils.julian_day_number((dday.year,dday.month,dday.day), utils.to_dms(nh,as_string=False))
    return next_jd
def is_solar_eclipse(jd,place):
    y, m, d, h = jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(Date(y, m, d))
    lon,lat = place.latitude, place.longitude; ele = place.elevation
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = PLANET_FLAGS #swe.FLG_SWIEPH | swe.FLG_SIDEREAL | _rise_flags
    ret,_ = swe.sol_eclipse_how(jd_utc,geopos=(lon, lat,ele),flags=flags)
    return ret
def next_solar_eclipse(jd,place):
    """
        @param jd: Julian number 
        @param place: Place Struct ('place',latitude,longitude,timezone)
        returns next solar eclipse date, percentage of eclipse etc
        @param jd: Julian number
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return: retflag, tret, attrs
        we can extract several info about eclipse from retflag, tret and attrs
            retflag != -1 = eclipse found 
            
            tret[0] = time of greatest eclipse (Julian day number)            
            tret[1] = first contact
            tret[2] = second contact
            tret[3] = third contact
            tret[4] = fourth contact
            
            attr[0]   fraction of solar diameter covered by moon;
                    with total/annular eclipses, it results in magnitude acc. to IMCCE.
            attr[1]   ratio of lunar diameter to solar one
            attr[2]   fraction of solar disc covered by moon (obscuration)
            attr[3]   diameter of core shadow in km
            attr[4]   azimuth of sun at tjd
            attr[5]   true altitude of sun above horizon at tjd
            attr[6]   apparent altitude of sun above horizon at tjd
            attr[7]   elongation of moon in degrees
            attr[8]   magnitude acc. to NASA;
                      = attr[0] for partial and attr[1] for annular and total eclipses
            attr[9]   saros series number (if available; otherwise -99999999) 
            attr[10]  saros series member number (if available; otherwise -99999999)

    """
    #ecl_dict = {"Annular":swe.ECL_ANNULAR | swe.ECL_CENTRAL | swe.ECL_NONCENTRAL,
    #            "Total":swe.ECL_TOTAL | swe.ECL_CENTRAL | swe.ECL_NONCENTRAL,
    #            "Annular Total":swe.ECL_ANNULAR_TOTAL | swe.ECL_CENTRAL | swe.ECL_NONCENTRAL,
    #            "Partial":swe.ECL_PARTIAL | swe.ECL_CENTRAL | swe.ECL_NONCENTRAL}
    geopos = (place.longitude, place.latitude,place.elevation)
    retflag,tret,attrs = swe.sol_eclipse_when_loc(jd,geopos)
    #print(ecl_dict.values(),retflag)
    #if retflag in ecl_dict.values(): print( list(ecl_dict.keys())[list(ecl_dict.values()).index(retflag)])
    #y,m,d,fh_ut = utils.jd_to_gregorian(tret[1])
    #fh_l = fh_ut + place.timezone
    #ecl_local = (y,m,d,fh_l)
    return [retflag,tret,attrs]
def next_lunar_eclipse(jd,place):
    """
        @param jd: Julian number 
        @param place: Place Struct ('place',latitude,longitude,timezone)
        returns next lunar eclipse date, percentage of eclipse etc
        @return: retflag, tret, attrs
        we can extract several info about eclipse from retflag, tret and attrs
            retflag != -1 = eclipse found 
            
            NOTE: All the times are in UT to get local time add timezone
            tret[0] = time of greatest eclipse (Julian day number)            
            tret[1] = first contact
            tret[2] = second contact
            tret[3] = third contact
            tret[4] = fourth contact
            
            attr[0]   fraction of solar diameter covered by moon;
                    with total/annular eclipses, it results in magnitude acc. to IMCCE.
            attr[1]   ratio of lunar diameter to solar one
            attr[2]   fraction of solar disc covered by moon (obscuration)
            attr[3]   diameter of core shadow in km
            attr[4]   azimuth of sun at tjd
            attr[5]   true altitude of sun above horizon at tjd
            attr[6]   apparent altitude of sun above horizon at tjd
            attr[7]   elongation of moon in degrees
            attr[8]   magnitude acc. to NASA;
                      = attr[0] for partial and attr[1] for annular and total eclipses
            attr[9]   saros series number (if available; otherwise -99999999) 
            attr[10]  saros series member number (if available; otherwise -99999999)

    """
    geopos = (place.longitude, place.latitude,place.elevation)
    retflag,tret,attrs = swe.lun_eclipse_when_loc(jd,geopos)
    #y,m,d,fh_ut = utils.jd_to_gregorian(tret[1])
    #fh_l = fh_ut + place.timezone
    #ecl_local = (y,m,d,fh_l)
    return [retflag,tret,attrs]
def _birthtime_rectification_nakshathra_suddhi(jd,place):
    """
        !!!!!! EXPERIMENTAL WORK - RESULTS MAY NOT BE ACCURATE !!!!
        Calculates expected birth star and if it does not match with actual,
        iteratively reduce/time birth time to see if matches with actual birth star
        If Successful - returns revised birth time as a tuple
            otherwise returns False and possible closest star for the time
    """
    step_minutes = const.birth_rectification_step_minutes; loop_count = const.birth_rectification_loop_count
    adjust_minutes = 0
    nak = nakshatra(jd, place)[0]
    def _get_estimated_nakshatra(jd,place):
        ud = utils.udhayadhi_nazhikai(jd, place)
        ud1n = int(round(ud[1]*60)*4//9); ud1d = int(ud[1]*4%9)
        #print(round(ud[1]*60),'The mixed number of {}/{} is {} and {}/{}'.format(round(ud[1]*60*4),9,ud1n, ud1d, 9))
        ud2 = [int(ud1d+n*9)%27+1 for n in range(3)]
        #print(ud2)
        rectification_required = not (nak in ud2); nak_close = nak
        if rectification_required:
            nak_close = utils.closest_element_from_list(ud2,nak)
            #print('Expected Star',nak,'Actual Star',nak_close,ud1d,'rectification_required',rectification_required)
        return [rectification_required, nak_close]
    [rectification_required, nak_close] = _get_estimated_nakshatra(jd, place)
    if not rectification_required:
        return adjust_minutes
    else:
        l = 0;
        while l < loop_count:
            l += 1
            adjust_minutes = l*step_minutes
            jd1 = jd + adjust_minutes/1440.0
            [rectification_required, nak_close] = _get_estimated_nakshatra(jd1, place)
            _,_,_,fh = utils.jd_to_gregorian(jd1)
            if not rectification_required:
                #print('loop',l,'CONVERGED',adjust_minutes,fh)
                revised_birth_time = tuple(utils.to_dms(fh, as_string=False))
                return revised_birth_time
            adjust_minutes = -l*step_minutes
            jd1 = jd + adjust_minutes/1440.0
            [rectification_required, nak_close] = _get_estimated_nakshatra(jd1, place)
            _,_,_,fh = utils.jd_to_gregorian(jd1)
            if not rectification_required:
                #print('loop',l,'CONVERGED',adjust_minutes,fh)
                revised_birth_time = tuple(utils.to_dms(fh, as_string=False))
                return revised_birth_time
    print('Could not rectify birth time beyond',int(step_minutes*loop_count),'minutes')
    return [rectification_required, nak_close]
def _birthtime_rectification_lagna_suddhi(jd,place):
    """
        !!!!!! EXPERIMENTAL WORK - RESULTS MAY NOT BE ACCURATE !!!!
        Checks if lagna is [1,5,7,9] from Moon or Maandi in Raasi and Navamsa
        Returns True (if rectification is required) False if no rectification is required
    """
    from jhora.horoscope.chart import charts,house
    y,m,h,fh = utils.jd_to_gregorian(jd); dob = Date(y,m,h); tob = tuple(utils.to_dms(fh, as_string=False))
    #print(dob,tob)
    ppr = charts.rasi_chart(jd, place); ppn = charts.divisional_chart(jd, place, divisional_chart_factor=9)
    lagna = ppr[0][1][0]; moon = ppr[2][1][0]
    maandi = maandi_longitude(dob,tob,place)[0]
    if house.get_relative_house_of_planet(lagna,moon) in [1,5,7,9]: return False
    #print('lagna not in [1,5,7,9] from moon',lagna,moon)
    if house.get_relative_house_of_planet(lagna,maandi) in [1,5,7,9]: return False
    #print('lagna not in [1,5,7,9] from Maandi',lagna,maandi)
    lagna = ppn[0][1][0]; moon = ppn[2][1][0]
    maandi = maandi_longitude(dob,tob,place, divisional_chart_factor=9)[0]
    if house.get_relative_house_of_planet(lagna,moon) in [1,5,7,9]: return False
    #print('Navamsa lagna not in [1,5,7,9] from moon',lagna,moon)
    if house.get_relative_house_of_planet(lagna,maandi) in [1,5,7,9]: return False
    #print('Navamsa lagna not in [1,5,7,9] from Maandi',lagna,maandi)
    return True
def _birthtime_rectification_janma_suddhi(jd,place,gender):
    """
        Convert Ishtakaal Ghatikas to Phala (* 60)
        Divide by 225; If the reminder is:
        0 - 15 - Male /  16 - 45 - Female / 46 - 90 - Male / 91 - 150 - Female / 151 - 224 - Male
        Will check if actual gender does not matche with above calculation and return True/False 
        False => birthtime rectification is NOT required based on gender match
        True => birthtime rectification IS required based on gender match
    """
    ud = utils.udhayadhi_nazhikai(jd, place)
    ud1n = int(round(ud[1]*60)//225); ud1d = int(ud[1]*60%225)
    #print(round(ud[1]*60),'The mixed number of {}/{} is {} and {}/{}'.format(round(ud[1]*60),225,ud1n, ud1d, 225))
    janma_suddhi_dict = {0:[(0,15),(46,90),(151,224)],1:[(16,45),(91,150)]}
    jsc = not any([(ud1d > js_pair[0] and ud1d < js_pair[1]) for js_pair in janma_suddhi_dict[gender]])
    return jsc
def __next_conjunction_of_planet_pair(jd,panchanga_place:Place,p1,p2,direction=1,separation_angle=0,
                                      finer_tolerance=None):
    if finer_tolerance is None: finer_tolerance = const.minimum_separation_longitude
    p1_key = ephemeris_planet_index(p1)
    p2_key = ephemeris_planet_index(p2)
    divisional_chart_factor = 1
    start_jd = jd
    cur_jd = start_jd - 1*direction
    end_jd = start_jd + 1*direction
    while cur_jd*direction < end_jd*direction:
        cur_jd_utc = cur_jd - panchanga_place.timezone/24.0
        if p1==const.KETU_ID:
            p1_long = (ketu(sidereal_longitude(cur_jd_utc, const._RAHU)))
        elif p1==const._ascendant_symbol:
            sla = ascendant(cur_jd, panchanga_place); p1_long = (sla[0]*30+sla[1])*divisional_chart_factor%360
        else:
            p1_long = (sidereal_longitude(cur_jd_utc, p1_key))
        if p2==const.KETU_ID:
            p2_long = (ketu(sidereal_longitude(cur_jd_utc, const._RAHU)))
        elif p2==const._ascendant_symbol:
            sla = ascendant(cur_jd, panchanga_place); p2_long = (sla[0]*30+sla[1])*divisional_chart_factor%360
        else:
            p2_long = (sidereal_longitude(cur_jd_utc, p2_key))
        p_long_diff = direction*(p1_long-p2_long)
        long_diff = (p_long_diff - separation_angle)%360
        if abs(long_diff) < const.minimum_separation_longitude:
            #print('Found closest time:',utils.jd_to_gregorian(cur_jd))
            return cur_jd,utils.norm360(p1_long),utils.norm360(p2_long)
        cur_jd += const.conjunction_increment*direction
    return None
def next_conjunction_of_planet_pair(jd,panchanga_place:Place,p1,p2,direction=1,separation_angle=0,
                                    increment_speed_factor=0.25,angle_tolerance=0.5,finer_angle_tolerance=0.001):
    """
        get the date when conjunction of given two planets occur
        @param p1: planet1 index (0=Sun..8=Kethu)
        @param p2: planet2 index (0=Sun..8=Kethu)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param panchanga_start_date: Date struct (y,m,d)
        @param direction: 1= next conjunction -1 previous conjunction
        @param separation_angle - angle by which the planets to each other
        @return: Julian day of conjunction   
    """
    if (p1==const.RAHU_ID and p2==const.KETU_ID) or (p1==const.KETU_ID and p2==const.RAHU_ID):
        warnings.warn("Rahu and Ketu do not conjoin ever. Program returns error")
        return None
    """         # swap planets Dont ask me Why I do this But it helps """
    if p1 in [const.RAHU_ID,const.KETU_ID]: tmp = p2; p2 = p1; p1 =tmp
    if p2 == const._ascendant_symbol and direction == -1: tmp = p1; p1 = p2; p2 =tmp
    if p2 in [const.RAHU_ID,const.KETU_ID] and p1 != const._ascendant_symbol: increment_speed_factor=0.01
    if finer_angle_tolerance is None: finer_angle_tolerance = const.minimum_separation_longitude
    p1_key = ephemeris_planet_index(p1)
    p2_key = ephemeris_planet_index(p2)
    asc_speed = ascendant_speed(jd, panchanga_place)
    _planet_speeds = [asc_speed]+[abs(psi[3]) for p,psi in planets_speed_info(jd, panchanga_place).items()]
    p1_speed = _planet_speeds[0] if p1=='L' else _planet_speeds[p1+1]
    p2_speed = _planet_speeds[0] if p2=='L' else _planet_speeds[p2+1]
    increment_days = increment_speed_factor/p1_speed if p1_speed > p2_speed else increment_speed_factor/p2_speed
    increment_days *= direction
    _DEBUG_ = False
    #increment_days=1.0/24.0/60.0*direction if p1 in ['L'] or p2 in ['L'] else 1*direction
    long_diff_check = angle_tolerance# if p1 in ['L'] or p2 in ['L'] else 1.0
    max_days_to_search = 1000000
    cur_jd = jd# utils.julian_day_number(panchanga_start_date, (0,0,0))
    cur_jd_utc = cur_jd - panchanga_place.timezone/24.0
    search_counter = 1
    while search_counter < max_days_to_search:
        cur_jd += increment_days
        cur_jd_utc = cur_jd - panchanga_place.timezone/24.0
        if p1==const.KETU_ID:
            p1_long = (ketu(sidereal_longitude(cur_jd_utc, const._RAHU)))
        elif p1==const._ascendant_symbol:
            sla = ascendant(cur_jd, panchanga_place); p1_long = (sla[0]*30+sla[1])
        else:
            p1_long = (sidereal_longitude(cur_jd_utc, p1_key))
        if p2==const.KETU_ID:
            p2_long = (ketu(sidereal_longitude(cur_jd_utc, const._RAHU)))
        elif p2==const._ascendant_symbol:
            sla = ascendant(cur_jd, panchanga_place); p2_long = (sla[0]*30+sla[1])
        else:
            p2_long = (sidereal_longitude(cur_jd_utc, p2_key))
        p_long_diff = direction*(p1_long-p2_long)
        long_diff = (360+p_long_diff - separation_angle)%360
        if _DEBUG_: print(search_counter,p1,p1_key,p1_long,p2,p2_key,p2_long,long_diff,long_diff_check,utils.jd_to_gregorian(cur_jd))
        if long_diff<long_diff_check:
            if _DEBUG_: print(long_diff,'<',long_diff_check)
            #ret = __next_conjunction_of_planet_pair(p1,p2,panchanga_place,cur_jd,direction,separation_angle)
            jd_list = [cur_jd+t*increment_days for t in range(-10,10)]
            long_diff_list = []
            for jdt in jd_list:
                if p1==const.KETU_ID:
                    p1_long = (ketu(sidereal_longitude(jdt-panchanga_place.timezone/24, const._RAHU)))
                elif p1==const._ascendant_symbol:
                    sla = ascendant(jdt, panchanga_place); p1_long = (sla[0]*30+sla[1])
                else:
                    p1_long = (sidereal_longitude(jdt-panchanga_place.timezone/24, p1_key))
                if p2==const.KETU_ID:
                    p2_long = (ketu(sidereal_longitude(jdt-panchanga_place.timezone/24, const._RAHU)))
                elif p2==const._ascendant_symbol:
                    sla = ascendant(jdt, panchanga_place); p2_long = (sla[0]*30+sla[1])
                else:
                    p2_long = (sidereal_longitude(jdt-panchanga_place.timezone/24, p2_key))
                p_long_diff = direction * (p1_long-p2_long)
                long_diff = (360+p_long_diff-separation_angle)%360
                long_diff_list.append(long_diff)
            """ TODO: For separation Angle > 180 Lagrange may not work """
            try:
                if _DEBUG_: print('Lagrange method of fine tuning')
                if _DEBUG_: print(jd_list,'\n',long_diff_list)
                conj_jd = utils.inverse_lagrange(jd_list, long_diff_list, 0.0)
                if p1==const.KETU_ID:
                    p1_long = (ketu(sidereal_longitude(conj_jd-panchanga_place.timezone/24, const._RAHU)))
                elif p1==const._ascendant_symbol:
                    sla = ascendant(conj_jd, panchanga_place); p1_long = (sla[0]*30+sla[1])
                else:
                    p1_long = (sidereal_longitude(conj_jd-panchanga_place.timezone/24, p1_key))
                if p2==const.KETU_ID:
                    p2_long = (ketu(sidereal_longitude(conj_jd-panchanga_place.timezone/24, const._RAHU)))
                elif p2==const._ascendant_symbol:
                    sla = ascendant(conj_jd, panchanga_place); p2_long = (sla[0]*30+sla[1])
                else:
                    p2_long = (sidereal_longitude(conj_jd-panchanga_place.timezone/24, p2_key))
                if conj_jd is not None:
                    if _DEBUG_: print(p1,p2,utils.jd_to_gregorian(conj_jd),p1_long,p2_long)
                    return conj_jd, p1_long, p2_long
            except:
                if _DEBUG_: print('Normal method of fine tuning - since Lagrange failed')
                if _DEBUG_: print(search_counter,p1,p1_long,p2,p2_long,long_diff,long_diff_check,utils.jd_to_gregorian(cur_jd))
                ret = __next_conjunction_of_planet_pair(cur_jd,panchanga_place,p1,p2,direction,separation_angle,
                                                        finer_tolerance=finer_angle_tolerance)
                if ret is not None:
                    return ret
                
        search_counter += 1
    print('Could not find planetary conjunctions for sep angle',separation_angle,' Try increasing search range')
    return None
def __previous_conjunction_of_planet_pair(p1,p2,panchanga_place:Place,start_jd,separation_angle=0):
    return __next_conjunction_of_planet_pair(p1, p2, panchanga_place, start_jd, direction=-1,separation_angle=separation_angle)
def previous_conjunction_of_planet_pair(jd,panchanga_place:Place,p1,p2,separation_angle=0,increment_speed_factor=0.25):
    return next_conjunction_of_planet_pair(jd, panchanga_place, p1, p2, direction=-1, separation_angle=separation_angle,
                                           increment_speed_factor=increment_speed_factor)
def previous_planet_entry_date(planet,jd,place,increment_days=0.01,precision=0.1,raasi=None):
    return next_planet_entry_date(planet,jd,place,direction=-1,increment_days=increment_days,precision=precision,raasi=raasi)
def previous_ascendant_entry_date(jd,place,increment_days=0.01,precision=0.1,raasi=None,divisional_chart_factor=1):
    return next_ascendant_entry_date(jd, place, direction=-1, increment_days=increment_days, precision=precision, raasi=raasi,divisional_chart_factor=divisional_chart_factor)
def next_ascendant_entry_date(jd, place, direction=1, precision=0.01, raasi=None, divisional_chart_factor=1):
    """
    Optimized drop-in replacement using Bisection followed by Exact Linear Interpolation.
    Yields 0.0s execution time with mathematically perfect sub-arcsecond accuracy.
    """
    _DEBUG_ = False
    
    # 1. Calculate starting longitude
    sla = ascendant(jd, place)
    sl = (sla[0] * 30 + sla[1]) * divisional_chart_factor % 360
    
    # 2. Determine target boundary
    if raasi is None:
        multiple = (((sl // 30) + 1) % 12) * 30
        if direction == -1: 
            multiple = ((sl // 30) % 12) * 30
    else: 
        multiple = (raasi - 1) * 30 if raasi > 0 else 0

    target_long = multiple

    def get_diff(t):
        sla_t = ascendant(t, place)
        sl_t = (sla_t[0] * 30 + sla_t[1]) * divisional_chart_factor % 360
        diff = (sl_t - target_long) % 360
        if diff > 180: 
            diff -= 360
        return diff

    # 3. Dynamic Step Size for Bracketing (~1 hour steps)
    step_days = (1.0 / 24.0) / divisional_chart_factor * direction

    t0 = jd
    diff0 = get_diff(t0)

    if abs(diff0) < 0.0001:
        t0 += (1.0 / 24.0 / 60.0 / divisional_chart_factor) * direction
        diff0 = get_diff(t0)

    t1 = t0
    diff1 = diff0

    # Phase 1: Bracket the root
    for _ in range(1000):
        t1 += step_days
        diff1 = get_diff(t1)
        
        if diff0 * diff1 <= 0 and abs(diff0) < 45: 
            break
            
        t0 = t1
        diff0 = diff1
    else:
        raise ValueError("Could not find an Ascendant transit within search limits.")

    # Phase 2: Fast Bisection to narrow the gap to ~1 minute
    precision_days = 0.001  # Broaden to ~1.4 minutes to save loops

    while abs(t1 - t0) > precision_days:
        t_mid = (t0 + t1) / 2.0
        diff_mid = get_diff(t_mid)
        
        if diff_mid == 0.0:
            t0 = t_mid
            diff0 = 0.0
            t1 = t_mid
            diff1 = 0.0
            break
        elif diff0 * diff_mid < 0:
            t1 = t_mid
            diff1 = diff_mid
        else:
            t0 = t_mid
            diff0 = diff_mid

    # Phase 3: Exact Linear Interpolation for Sub-Arcsecond Precision
    # Since the gap is now microscopic, planetary motion is a perfectly straight line.
    # This equation calculates the exact fractional Julian day of the 0.0" crossing.
    if diff1 - diff0 != 0:
        exact_jd = t0 - diff0 * (t1 - t0) / (diff1 - diff0)
    else:
        exact_jd = (t0 + t1) / 2.0

    sla_exact = ascendant(exact_jd, place)
    exact_long = (sla_exact[0] * 30 + sla_exact[1]) * divisional_chart_factor % 360
    
    if _DEBUG_: 
        print('JD', utils.jd_to_gregorian(exact_jd), 'asc long', exact_long)

    return exact_jd, exact_long
def next_ascendant_entry_date_old(jd,place,direction=1,precision=0.01,raasi=None,divisional_chart_factor=1):
    """
        get the date when the ascendant enters a zodiac
        @param panchanga_date: Date struct (y,m,d)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param direction: 1= next entry, -1 previous entry
        @param precision: precision in degrees within which longitude entry whould be (default: 1.0 degrees)
        @param raasi: raasi at which planet should enter. 
            If raasi==None: gives entry to next constellation
            If raasi is specified [1..12] gives entry to specified constellation/raasi
        @return Julian day number of planet entry into zodiac
    """
    _DEBUG_ = False
    increment_days = 1.0/24.0/60.0/divisional_chart_factor # For moon/lagna increment days in minutes
    sla = ascendant(jd, place); sl = sla[0]*30+sla[1]
    if raasi==None:
        multiple = (((sl*divisional_chart_factor//30)+1)%12)*30
        if direction==-1: multiple = (sl*divisional_chart_factor//30)%12*30
    else: 
        multiple = (raasi-1)*30 if raasi>0 else 0
    if _DEBUG_: print(utils.jd_to_gregorian(jd),'sla',sla,'multiple',multiple,'precision',precision)
    while True:
        if sl < (multiple+precision) and sl>(multiple-precision):
            break
        jd += increment_days*direction
        sla = ascendant(jd, place); sl = (sla[0]*30+sla[1])*divisional_chart_factor%360
        if _DEBUG_: print('sl',sl,utils.jd_to_gregorian(jd),'multiple',multiple)
    offsets = [t*increment_days for t in range(-10,10)] 
    asc_longs = []
    for t in offsets:
        sla = ascendant(jd+t, place); sl = (sla[0]*30+sla[1])*divisional_chart_factor%360
        asc_longs.append(sl)
    if _DEBUG_: print(offsets,asc_longs,multiple)
    asc_hour = utils.inverse_lagrange(offsets, asc_longs, multiple) # Do not move % 360 above
    #asc_hour /= divisional_chart_factor
    jd += asc_hour
    sla = ascendant(jd, place); asc_long = (sla[0]*30+sla[1])*divisional_chart_factor%360
    if _DEBUG_: print('JD',utils.jd_to_gregorian(jd),'asc long',asc_long)
    return jd,asc_long
def next_planet_entry_date_old(planet,jd,place,direction=1,increment_days=0.01,precision=0.1,raasi=None):
    """
        get the date when a planet enters a zodiac
        @param planet: planet index (0=Sun..8=Kethu)
        @param panchanga_date: Date struct (y,m,d)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param direction: 1= next entry, -1 previous entry
        @param increment_days: incremental steps in days algorithm to check for entry (Default=1 day)
        @param precision: precision in degrees within which longitude entry whould be (default: 0.1 degrees)
        @param raasi: raasi at which planet should enter. 
            If raasi==None: gives entry to next constellation
            If raasi is specified [1..12] gives entry to specified constellation/raasi
        @return Julian day number of planet entry into zodiac
    """
    search_jd = jd
    if planet == const._ascendant_symbol:
        return next_ascendant_entry_date(search_jd, place, direction=direction, precision=1.0, raasi=raasi)
    pl = ephemeris_planet_index(planet)
    if planet in [const._ascendant_symbol,const._MOON]: increment_days = 1.0/24.0/60.0 # For moon/lagna increment days in minutes
    if pl==const._KETU:
        raghu_raasi = (raasi-1+6)%12+1 if raasi!=None else raasi
        ret = next_planet_entry_date(const.RAHU_ID, search_jd, place,direction=direction,raasi=raghu_raasi)
        p_long = (ret[1]+180)%360
        return ret[0],p_long
    jd_utc = search_jd - place.timezone/24.0
    sl = sidereal_longitude(jd_utc,pl)
    #if planet in [const.RAHU_ID,const.KETU_ID]: direction *= -1 # Rahu/Ketu always in reverse direction
    if raasi==None:
        multiple = (((sl//30)+1)%12)*30
        if direction==-1: multiple = (sl//30)%12*30
        if pl == const._RAHU:
            multiple = ((sl//30)%12 * 30)%360
            if direction==-1:
                multiple = ((sl//30+1)%12*30)%360
    else: 
        multiple = (raasi-1)*30 if raasi>0 else 0
    while True:
        if sl < (multiple+precision) and sl>(multiple-precision):
            break
        search_jd += increment_days*direction; jd_utc = search_jd - place.timezone/24.0
        sl = sidereal_longitude(jd_utc,pl)
    sank_date = jd_to_gregorian(jd_utc)
    sank_sunrise = sunrise(jd_utc,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    planet_longs = []
    for t in offsets:
        sl = sidereal_longitude(sank_sunrise+t,pl)
        planet_longs.append(sl)
    planet_hour = utils.inverse_lagrange(offsets, planet_longs, multiple) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    planet_hour1 = (sank_sunrise + planet_hour - sank_jd_utc)*24+place.timezone
    sank_jd_utc += planet_hour1/24.0
    planet_long = sidereal_longitude(sank_jd_utc-place.timezone/24,pl)
    y,m,d,fh = jd_to_gregorian(sank_jd_utc); sank_date = Date(y,m,d); planet_hour1 = fh
    return sank_jd_utc,planet_long

def next_planet_entry_date(planet, jd, place, direction=1, increment_days=0.01, precision=0.1, raasi=None):
    """
    Hyper-Optimized using Kinematic Predictive Jumps, False Position, and 
    Exact Linear Interpolation for absolute down-to-the-second precision.
    """
    search_jd = jd
    
    # 1. Handle Ascendant 
    if planet == const._ascendant_symbol:
        return next_ascendant_entry_date(search_jd, place, direction=direction, precision=precision, raasi=raasi)
        
    pl = ephemeris_planet_index(planet)
    
    # 2. Handle Ketu recursively via Rahu
    if pl == const._KETU:
        raghu_raasi = (raasi - 1 + 6) % 12 + 1 if raasi is not None else raasi
        ret = next_planet_entry_date(const.RAHU_ID, search_jd, place, direction=direction, raasi=raghu_raasi)
        p_long = (ret[1] + 180) % 360
        return ret[0], p_long

    jd_utc = search_jd - place.timezone / 24.0
    current_sl = sidereal_longitude(jd_utc, pl)

    # 3. Determine target boundary
    if raasi is None:
        multiple = (((current_sl // 30) + 1) % 12) * 30
        if direction == -1: 
            multiple = (current_sl // 30) % 12 * 30
            
        if pl == const._RAHU:
            multiple = ((current_sl // 30) % 12 * 30) % 360
            if direction == -1:
                multiple = ((current_sl // 30 + 1) % 12 * 30) % 360
    else: 
        multiple = (raasi - 1) * 30 if raasi > 0 else 0

    target_long = multiple

    def get_diff(t):
        sl = sidereal_longitude(t, pl)
        diff = (sl - target_long) % 360
        if diff > 180: 
            diff -= 360
        return diff

    # 4. Kinematic Maximum Speeds (degrees per day)
    max_speeds = {
        const._MOON: 15.5,
        const._SUN: 1.05,
        const._MERCURY: 2.5,
        const._VENUS: 1.3,
        const._MARS: 0.85,
        const._JUPITER: 0.26,
        const._SATURN: 0.13,
        const._RAHU: 0.07
    }
    max_speed = max_speeds.get(pl, 2.0)
    
    bracket_steps = {
        const._MOON: 0.25,
        const._SUN: 2.0,
        const._MERCURY: 1.0,
        const._VENUS: 1.0,
        const._MARS: 3.0,
        const._JUPITER: 5.0,
        const._SATURN: 10.0,
        const._RAHU: 10.0
    }
    safe_bracket = bracket_steps.get(pl, 1.0) * direction

    t0 = jd_utc
    diff0 = get_diff(t0)

    if abs(diff0) < 0.0001:
        t0 += (0.01 * direction)
        diff0 = get_diff(t0)

    t1 = t0
    diff1 = diff0

    # Phase 1: Kinematic Predictive Bracketing
    for _ in range(1000):
        distance = abs(diff1)
        if distance > 3.0:
            step = (distance / max_speed) * 0.85 * direction
        else:
            step = safe_bracket
            
        t1 += step
        diff1 = get_diff(t1)
        
        if diff0 * diff1 <= 0 and abs(diff0) < 45: 
            break
            
        t0 = t1
        diff0 = diff1
    else:
        raise ValueError(f"Could not find a transit for planet {planet} within search limits.")

    # Phase 2: False Position to narrow the gap to ~1 minute (~0.001 days)
    precision_days = 0.001 

    while abs(t1 - t0) > precision_days:
        if diff1 - diff0 == 0:
            t_mid = (t0 + t1) / 2.0
        else:
            t_mid = t1 - diff1 * (t1 - t0) / (diff1 - diff0)
            
        diff_mid = get_diff(t_mid)
        
        if abs(diff_mid) < 0.000001:
            t0 = t_mid
            t1 = t_mid
            break
            
        if diff0 * diff_mid < 0:
            t1 = t_mid
            diff1 = diff_mid
        else:
            t0 = t_mid
            diff0 = diff_mid

    # Phase 3: Exact Linear Interpolation for Sub-Arcsecond Precision
    # Pinpoints the exact microscopic fraction of a second where longitude hits target_long exactly.
    if diff1 - diff0 != 0:
        exact_jd_utc = t0 - diff0 * (t1 - t0) / (diff1 - diff0)
    else:
        exact_jd_utc = (t0 + t1) / 2.0

    exact_long = sidereal_longitude(exact_jd_utc, pl)

    # 5. Return to local JD
    sank_jd_local = exact_jd_utc + place.timezone / 24.0
    
    return sank_jd_local, exact_long
def next_planet_retrograde_change_date(planet, panchanga_date, place, increment_days=1, direction=1):
    """
        Optimized drop-in replacement using Dynamic Bracketing and Bisection Root-Finding.
        Yields ~0.0s execution time with sub-second precision.
    """
    if planet in [const.SUN_ID, const.MOON_ID]:
        print(planet, "is not a retrograding planet")
        return 
    if not const._use_true_nodes_for_rahu_ketu and planet in [const.RAHU_ID, const.KETU_ID]:
        raise ValueError("Rahu/Ketu are always in retrograde if configured as Mean Nodes")
        return

    jd = utils.gregorian_to_jd(panchanga_date)

    # Helper function to get the current speed direction cleanly
    def get_sign(t):
        return _planet_speed_sign(t, place, planet)

    s0 = get_sign(jd)

    # If starting point itself is exactly stationary, nudge forward slightly
    while s0 == 0:
        jd += 0.01 * direction
        s0 = get_sign(jd)

    # Phase 1: Dynamic Bracketing
    # We set safe max steps to bracket the change rapidly. 
    # Mercury retrogrades for ~21 days, so a safe step is ~3 days to ensure we never jump over it.
    # Slower planets can safely jump further.
    step_map = {
        const.MERCURY_ID: 3.0,
        const.VENUS_ID: 10.0,
        const.MARS_ID: 15.0,
        const.JUPITER_ID: 30.0,
        const.SATURN_ID: 30.0,
        const.RAHU_ID: 1.0,
        const.KETU_ID: 1.0
    } if hasattr(const, 'MERCURY_ID') else {} # Safety fallback if constant names differ
    
    # Use dynamic step, but fallback to a foolproof 3.0 days (or 1.0 for nodes) if unmapped
    default_safe_step = 1.0 if planet in [const.RAHU_ID, const.KETU_ID] else 3.0
    safe_step = step_map.get(planet, default_safe_step) * direction

    t0 = jd
    t1 = t0
    s1 = s0

    # Fast forward until the direction sign flips
    for _ in range(1000):
        t1 += safe_step
        s1 = get_sign(t1)

        if s1 == 0: 
            break  # Exact stationary point hit by chance
        if s1 != s0:
            break  # Sign flipped, the zero crossing is trapped between t0 and t1

        t0 = t1
    else:
        raise ValueError(f"Could not find a retrograde direction change within search limits.")

    # Phase 2: Ultra-Precise Bisection Root-Finding
    # Halves the gap repeatedly, zeroing in on the exact stationary moment.
    # 0.0000001 days = 0.008 seconds of real-time accuracy.
    precision_days = 0.0000001  

    while abs(t1 - t0) > precision_days:
        t_mid = (t0 + t1) / 2.0
        s_mid = get_sign(t_mid)

        if s_mid == 0:  # Perfect mathematical zero hit
            t0 = t_mid
            t1 = t_mid
            break
        elif s_mid == s0:
            t0 = t_mid
        else:
            t1 = t_mid

    exact_jd = (t0 + t1) / 2.0
    
    # The new direction is mathematically the opposite of the initial non-zero direction
    new_direction = -s0 
    
    return exact_jd, new_direction
def next_planet_retrograde_change_date_old(planet, panchanga_date, place, increment_days=1, direction=1):
    """
        get the date when a retrograde planet changes its direction
        @param planet: planet index (0=Sun..8=Kethu)
        @param panchanga_date: Date struct (y,m,d)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param increment_days: incremental steps in days algorithm to check for entry (Default=1 day)
        @param direction: 1= next direction change, -1 previous direction change
        @return Julian day number of planet changes retrograde direction
        NOTE: Sun and Moon do not retrograde. 
            Rahu/Ketu always retrograde as Mean Nodes (and do not exibit stationary or direct)
            Rahu/Ketu as True nodes - retrograde, stationary or even direct
    """
    if planet in [const.SUN_ID, const.MOON_ID]:
        print(planet,"is not a retrograding planet")
        return 
    if not const._use_true_nodes_for_rahu_ketu and planet in [const.RAHU_ID,const.KETU_ID]:
        raise ValueError("Rahu/Ketu are always in retrograde if configured as Mean Nodes")
        return

    jd = utils.gregorian_to_jd(panchanga_date)

    sl_sign = _planet_speed_sign(jd, place, planet)

    # if starting point itself is stationary, move until a definite direction is found
    while sl_sign == 0:
        jd += increment_days * direction
        sl_sign = _planet_speed_sign(jd, place, planet)

    sl_sign_next = sl_sign

    # coarse search: ignore stationary (0), stop only when opposite nonzero sign is found
    while True:
        jd += increment_days * direction
        sl_sign_next = _planet_speed_sign(jd, place, planet)

        if sl_sign_next == 0:
            continue

        if sl_sign_next == sl_sign:
            continue

        break

    # go back to previous coarse point
    jd -= increment_days * direction

    # refine with smaller step
    increment_days = const.conjunction_increment
    sl_sign_next = sl_sign

    while True:
        jd += increment_days * direction
        sl_sign_next = _planet_speed_sign(jd, place, planet)

        if sl_sign_next == 0:
            continue

        if sl_sign_next == sl_sign:
            continue

        break

    return jd, sl_sign_next
def _next_planet_retrograde_change_date(planet,panchanga_date,place,increment_days=1,direction=1):
    """
        get the date when a retrograde planet changes its direction
        @param planet: planet index (0=Sun..8=Kethu)
        @param panchanga_date: Date struct (y,m,d)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param increment_days: incremental steps in days algorithm to check for entry (Default=1 day)
        @param direction: 1= next direction change, -1 previous direction change
        @return Julian day number of planet changes retrogade direction
        NOTE: Sun and Moon do not retrograde. 
            Rahu/Ketu always retrograde as Mean Nodes (and do not exibit stationary or direct)
            Rahu/Ketu as True nodes - retrograde, stationary or even direct
    """
    if planet in [const.SUN_ID, const.MOON_ID]:
        print(planet,"is not a retrograding planet")
        return 
    if not const._use_true_nodes_for_rahu_ketu and planet in [const.RAHU_ID,const.KETU_ID]:
        raise ValueError("Rahu/Ketu are always in retrograde if configured as Mean Nodes")
        return
    jd = utils.gregorian_to_jd(panchanga_date)
    sl_sign = _planet_speed_sign(jd,place,planet); sl_sign_next = sl_sign
    while sl_sign == sl_sign_next:
        jd += increment_days*direction
        sl_sign_next = _planet_speed_sign(jd,place,planet)
    jd -= increment_days*direction; increment_days=const.conjunction_increment; sl_sign_next=sl_sign
    while sl_sign == sl_sign_next:
        jd += increment_days*direction
        sl_sign_next = _planet_speed_sign(jd,place,planet)
    return jd,sl_sign_next
def next_planet_stationary_duration(
    planet,
    current_jd,
    place,
    threshold=0.02, # We use 0.02 deg/day instead of 1 arcsecond to get bigger window for stationary interval
    direction=1,
    step=0.01,
):
    """
    Find a stationary interval relative to current_jd.
    Uses ultra-fast float-safe bisection to perfectly capture the threshold boundaries.
    """
    if planet in [const.MOON_ID, const.SUN_ID]:
        raise ValueError("Sun/Moon are not stationary planets")
    if not const._use_true_nodes_for_rahu_ketu and planet in [const.RAHU_ID, const.KETU_ID]:
        raise ValueError("Rahu/Ketu are always in retrograde if configured as Mean Nodes")
    if direction not in (+1, -1):
        raise ValueError("direction must be +1 or -1")

    def get_speed(jd_):
        return daily_planet_speed(jd_, place, planet)

    def find_boundary(jd_in, step_dir):
        """Steps outward then bisects to find the exact millisecond it crosses the threshold."""
        jd_out = jd_in
        # Step outward until we exceed the threshold
        while abs(get_speed(jd_out)) < threshold:
            jd_out += step_dir * step
            
        # Bisect down to millisecond precision
        for _ in range(30):
            mid = (jd_in + jd_out) / 2.0
            if abs(get_speed(mid)) < threshold:
                jd_in = mid
            else:
                jd_out = mid
        return (jd_in + jd_out) / 2.0

    jd = current_jd
    v_curr = get_speed(jd)

    # --------------------------------------------------
    # 1. Handle if we are ALREADY inside a stationary interval
    # --------------------------------------------------
    if abs(v_curr) < threshold:
        start_jd = find_boundary(jd, -1)
        end_jd = find_boundary(jd, 1)
        
        if direction == -1:
            return utils.jd_to_gregorian(start_jd), utils.jd_to_gregorian(end_jd)
            
        # Fast-forward safely out of the current interval
        jd = end_jd + step
        while abs(get_speed(jd)) < threshold:
            jd += step
        v_curr = get_speed(jd)

    # --------------------------------------------------
    # 2. Fast forward to find the exact zero-crossing
    # --------------------------------------------------
    v_prev = v_curr
    coarse_step = max(step, 0.5)  # Safe large steps to skip days quickly
    
    while True:
        jd += direction * coarse_step
        v = get_speed(jd)

        # Jumped directly into the threshold?
        if abs(v) < threshold:
            jd_inside = jd
            break

        # Did the speed cross zero? (Boolean sign check - immune to float underflow)
        if (v > 0) != (v_prev > 0):
            a = jd - direction * coarse_step
            b = jd
            v_a = v_prev
            
            # Bisect exactly where speed == 0 
            for _ in range(30):
                mid = (a + b) / 2.0
                v_mid = get_speed(mid)
                if (v_mid > 0) == (v_a > 0):
                    a = mid
                    v_a = v_mid
                else:
                    b = mid
            
            jd_inside = (a + b) / 2.0
            break
            
        v_prev = v

    # --------------------------------------------------
    # 3. We found the anchor point. Resolve the exact boundaries.
    # --------------------------------------------------
    start_jd = find_boundary(jd_inside, -1)
    end_jd = find_boundary(jd_inside, 1)

    # Ensure chronological order
    if start_jd > end_jd:
        start_jd, end_jd = end_jd, start_jd

    return utils.jd_to_gregorian(start_jd), utils.jd_to_gregorian(end_jd)

def next_planet_stationary_duration_old(
    planet,
    current_jd,
    place,
    threshold=const.one_arc_second,
    direction=1,
    step=0.01,
):
    """
    Find a stationary interval relative to current_jd.

    direction:
        +1 -> return the next stationary interval whose start_jd > current_jd
        -1 -> return the stationary interval whose start_jd < current_jd;
              if already inside a stationary interval, return the current one

    threshold:
        Speed in degrees/day below which the planet is considered stationary.
        NOTE: Sun and Moon do not retrograde. 
            Rahu/Ketu always retrograde as Mean Nodes (and do not exibit stationary or direct)
            Rahu/Ketu as True nodes - retrograde, stationary or even direct
    """
    if planet in [const.MOON_ID, const.SUN_ID]:
        raise ValueError("Sun/Moon are not stationary planets")
    if not const._use_true_nodes_for_rahu_ketu and planet in [const.RAHU_ID,const.KETU_ID]:
        raise ValueError("Rahu/Ketu are always in retrograde if configured as Mean Nodes")
    if direction not in (+1, -1):
        raise ValueError("direction must be +1 or -1")

    def is_stationary(jd_):
        return abs(daily_planet_speed(jd_, place, planet)) < threshold

    def get_stationary_interval_containing(jd_):
        start_jd = jd_
        while is_stationary(start_jd):
            start_jd -= step

        end_jd = jd_
        while is_stationary(end_jd):
            end_jd += step
        _interval = start_jd + step, end_jd - step
        return _interval

    # --------------------------------------------------
    # If already inside a stationary interval:
    #   direction = -1 -> return current interval
    #   direction = +1 -> skip current interval and find next
    # --------------------------------------------------
    if is_stationary(current_jd):
        current_start, current_end = get_stationary_interval_containing(current_jd)

        if direction == -1:
            return utils.jd_to_gregorian(current_start), utils.jd_to_gregorian(current_end)

        # direction == +1
        jd = current_end + step
        while not is_stationary(jd):
            jd += step
        _sjd1,_sjd2 = get_stationary_interval_containing(jd)
        return utils.jd_to_gregorian(_sjd1), utils.jd_to_gregorian(_sjd2)

    # --------------------------------------------------
    # Not currently stationary:
    # search in requested direction until entering one
    # --------------------------------------------------
    jd = current_jd
    while not is_stationary(jd):
        jd += direction * step

    _sjd1,_sjd2 = get_stationary_interval_containing(jd)
    return utils.jd_to_gregorian(_sjd1), utils.jd_to_gregorian(_sjd2)
def _nisheka_time(jd,place):
    """
        @param jd: Julian number 
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @return julian date number of nisheka time
        TODO: Formula needs to be checked
        Does not match JHora value (differs by upto 15 days)
    """
    y,m,d,fh = utils.jd_to_gregorian(jd); dob = Date(y,m,d); tob = utils.to_dms(fh,as_string=False)
    from jhora.horoscope.chart.charts import rasi_chart
    pp = rasi_chart(jd,place)
    sat_long = pp[const.SATURN_ID+1][1][0]*30+pp[7][1][1]
    moon_long=pp[const.MOON_ID+1][1][0]*30+pp[2][1][1]
    lagna_long = pp[0][1][0]*30+pp[0][1][1]
    ninth_house_long = (const.HOUSE_9*30+lagna_long+15)%360
    gl = gulika_longitude(dob,tob,place); gulika_long = gl[0]*30+gl[1]
    ml = maandi_longitude(dob,tob,place); maandi_long = ml[0]*30+ml[1]
    a = 0.5*( (sat_long-gulika_long)%30 + ((sat_long-maandi_long)%30) ); b = (ninth_house_long-lagna_long)%360
    c = (a+b)%360 ; c1 = c%30; bm = c//30
    d = (c1+moon_long%30)
    jd_nisheka = jd - (bm*const.sidereal_year/12+d)
    return jd_nisheka
def _nisheka_time_1(jd,place):
    y,m,d,fh = utils.jd_to_gregorian(jd); dob = Date(y,m,d); tob = utils.to_dms(fh,as_string=False)
    from jhora.horoscope.chart.charts import rasi_chart
    from jhora.horoscope.chart.house import house_owner_from_planet_positions
    pp = rasi_chart(jd,place)
    asc_house = pp[0][1][0]; lagna_long = asc_house*30 + pp[0][1][1]
    lagna_lord = house_owner_from_planet_positions(pp,asc_house,check_during_dhasa=False)
    lagna_lord_long = pp[lagna_lord+1][1][0]*30+pp[lagna_lord+1][1][1]
    p_to_h = utils.get_planet_house_dictionary_from_planet_positions(pp)
    drishya = 1.0
    if (lagna_lord_long < (lagna_long+15)) or (lagna_lord_long>(lagna_long+195)):
        drishya = -1
    sat_long = pp[7][1][0]*30+pp[7][1][1]; gl = gulika_longitude(dob,tob,place); gulika_long = gl[0]*30+gl[1]
    moon_long=pp[2][1][1]
    a = abs(sat_long-gulika_long)%30; c= (a+moon_long)%30
    print('a',a,c,drishya)
    jd_nisheka = jd - (273 + drishya*c*27.3217/30)
    return jd_nisheka
def graha_drekkana(jd,place,use_bv_raman_table=False):
    return [const.drekkana_table_bvraman[h][int(long//10)] for _,(h,long) in dhasavarga(jd, place)] if use_bv_raman_table \
        else [const.drekkana_table[h][int(long//10)] for _,(h,long) in dhasavarga(jd, place)]
def sahasra_chandrodayam_old(dob,tob,place):
    """
        TODO: Does not support BCE dates as ephem supports only datetime
    """
    if '-' in str(dob[0]): return (-1,-1,-1)
    import ephem
    from datetime import datetime, timedelta
    try:
        birth_date = datetime(dob[0],dob[1],dob[2],tob[0],tob[1])
        current_date = birth_date - timedelta(hours=place.timezone)  # Convert to UTC
    except:
        print(birth_date,'not a valid date')
        return None
    observer = ephem.Observer()
    observer.lat = str(place.latitude)
    observer.lon = str(place.longitude)
    observer.elevation = 0
    full_moons_count = 0
    while full_moons_count < 1000:
        observer.date = current_date
        next_full_moon = ephem.next_full_moon(observer.date)
        full_moons_count += 1
        current_date = next_full_moon.datetime()
    sahasra_date = current_date + timedelta(hours=place.timezone)
    return sahasra_date.timetuple()[:-3]
def sahasra_chandrodayam(jd,place):
    full_moons_count = 0
    tithi_ = tithi(jd,place)[0]
    while full_moons_count < 1000:
        full_moon_jd = full_moon(jd, tithi_, opt=1)
        #print(full_moons_count,utils.jd_to_gregorian(full_moon_jd))
        full_moons_count += 1
        jd = full_moon_jd+0.25
        tithi_ = tithi(jd,place)[0]
    sahasra_date = utils.jd_to_gregorian(full_moon_jd)
    return sahasra_date[:-1]
def amrita_gadiya(jd,place):
    """ Ref: Panchangam Calculations: Karanam Ramakumar """
    nak,_,nak_beg,nak_end = nakshatra(jd,place)[:4]
    nak_durn = nak_end-nak_beg
    nak_fac = const.amrita_gadiya_varjyam_star_map[nak-1][0]/24
    ag_start = nak_beg + nak_fac*nak_durn
    ag_durn = nak_durn * 1.6/24; ag_end = ag_start+ag_durn
    return ag_start,ag_end
def varjyam(jd,place):
    """ Ref: Panchangam Calculations: Karanam Ramakumar """
    nak,_,nak_beg,nak_end = nakshatra(jd,place)[:4]
    nak_durn = nak_end-nak_beg
    if (nak == 19): # Moolam has two Varjyam timings
        nak_fac1 = const.amrita_gadiya_varjyam_star_map[nak-1][1][0]/24
        nak_fac2 = const.amrita_gadiya_varjyam_star_map[nak-1][1][1]/24
        ag_start1 = nak_beg + nak_fac1*nak_durn
        ag_start2 = nak_beg + nak_fac2*nak_durn
        ag_durn = nak_durn * 1.6/24
        ag_end1 = ag_start1+ag_durn
        ag_end2 = ag_start2+ag_durn
        return ag_start1,ag_end1,ag_start2,ag_end2
    else:
        nak_fac = const.amrita_gadiya_varjyam_star_map[nak-1][1]/24
        ag_start = nak_beg + nak_fac*nak_durn
        ag_durn = nak_durn * 1.6/24; ag_end = ag_start+ag_durn
        return ag_start,ag_end
def anandhaadhi_yoga(jd,place):
    nak = nakshatra(jd,place)
    day = vaara(jd,place)
    return const.anandhaadhi_yoga_day_star_list[day].index(nak[0]-1),nak[2]
def triguna(jd,place):
    _,_,_,fh = utils.jd_to_gregorian(jd)
    day = vaara(jd,place)
    return utils.triguna_of_the_day_time(day,fh)
def vivaha_chakra_palan(jd,place):
    """
        1. Collateral damage to family
        2. Wealthy and Blessed
        3. Collateral damage to girl's family
        4. Poverty and cursed
        5. Gainful and beneficial
        6. Loss of reputation and honour
        7. Devastating results for the girl
        8. Completely successfull
        9. Wonderful pair and blessed
    """
    jd_utc = jd - place.timezone/24
    sun_long = sidereal_longitude(jd, const._SUN)
    sun_star = nakshatra_pada(sun_long)[0]
    
    moon_long = sidereal_longitude(jd, const._MOON)
    moon_star = nakshatra_pada(moon_long)[0]

    # Initialize 3x3 grid with three stars each cell
    grid = [[[(sun_star + (i + j) - 1) % 27 + 1 for j in range(-1, 2)] for i in range(-1, 2)] for _ in range(3)]

    # Define positions to place stars in 3x3 grid starting East and moving clockwise
    positions = [(1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (0, 0), (0, 1), (0, 2)]

    # Populate the grid with the calculated stars
    all_stars = [(sun_star + i - 2) % 27 + 1 for i in range(27)]
    for i, (r, c) in enumerate(positions):
        grid[r][c] = all_stars[3*(i+1):3*(i+2)]

    # Find the moon star position using next()
    position = next((i, j) for i in range(3) for j in range(3) if moon_star in grid[i][j])
    if position:
        r, c = position
        mapping = {(1, 1): 1, (1, 2): 2, (2, 2): 3, (2, 1): 4, (2, 0): 5, (1, 0): 6, (0, 0): 7, (0, 1): 8, (0, 2): 9}
        return mapping[(r, c)]
    return None
def tamil_yogam(jd, place,check_special_yogas=True,use_sringeri_panchanga_version=False):
    """
        @return tamil yoga index
        0:'siddha', 1:'prabalarishta', 2:'marana', 3:'amritha',4:'amritha_siddha',5:'mrithyu',6:'daghda',
        7:'yamaghata',8:'utpata'
    """
    panchang = const.tamil_basic_yoga_sringeri_panchanga_list if use_sringeri_panchanga_version else const.tamil_basic_yoga_list 
    nak = nakshatra(jd, place)
    naks = nak[0]-1
    wday = vaara(jd,place)
    #print(utils.DAYS_LIST[wday],utils.NAKSHATRA_LIST[naks],nak)
    yi = panchang[wday][naks]
    if not check_special_yogas: return yi,nak[2],nak[3]
    # Additional yoga checks
    ad = [const.amrita_siddha_yoga_dict,const.mrityu_yoga_dict,const.daghda_yoga_dict, const.yamaghata_yoga_dict,
          const.utpata_yoga_dict]
    for d in ad:
        if d[wday]==naks: return 4+ad.index(d),nak[2],nak[3],yi
    if naks in const.sarvartha_siddha_yoga[wday]: return len(const.tamil_yoga_names)-1,nak[2],nak[3]
    return yi,nak[2],nak[3],yi
def brahma_muhurtha(jd, place):
    dl = day_length(jd, place); nl = night_length(jd, place)
    dm = dl/15.0 ; nm = nl/15.0
    sunrise_hours = sunrise(jd, place)[0]
    bm_start = sunrise_hours-2*nm; bm_end = sunrise_hours-nm
    return bm_start,bm_end
def godhuli_muhurtha(jd, place):
    dl = day_length(jd, place); nl = night_length(jd, place)
    dm = dl/15.0 ; nm = nl/15.0
    sunset_hours = sunset(jd, place)[0]
    bm_start = sunset_hours-0.25*dm; bm_end = sunset_hours+0.25*nm
    return bm_start,bm_end
def sandhya_periods(jd,place):
    """
        returns three sandhya periods: - each (Ghati is 1/30th of day length)
            Pratah - 2 ghatis before sunrise and 1 ghati after sunrise
            Madhyaahna - 1.5 ghatis before noon and 1.5 ghatis after noon
            Saayam - 1 ghati before sunset and 2 after sunset
    """
    dl = day_length(jd, place); ghati = dl/30.
    sunrise_hours = sunrise(jd, place)[0]; sunset_hours = sunset(jd, place)[0]
    noon = sunrise_hours+0.5*dl
    ps = (sunrise_hours-2*ghati, sunrise_hours+ghati)
    ms = (noon-1.5*ghati, noon+1.5*ghati)
    ss = (sunset_hours-ghati,sunset_hours+2*ghati)
    return ps,ms,ss
def vijaya_muhurtha(jd,place):
    dl = day_length(jd, place); gd = dl/30.
    nl = night_length(jd, place); gn = nl/30.0
    sunrise_hours = sunrise(jd, place)[0]; sunset_hours = sunset(jd, place)[0]
    noon = sunrise_hours+0.5*dl; _midnight = sunset_hours+0.5*nl
    vmd = (noon-gd, noon+gd)
    vmn = (_midnight-gn, _midnight+gn)
    return vmd,vmn
def nishita_kaala(jd,place):
    """ Eighth muhurtha of the night """
    nl = night_length(jd, place); gn = nl/30.0
    sunset_hours = sunset(jd, place)[0]
    return sunset_hours+7*gn, sunset_hours+8*gn
def tamil_jaamam(jd,place,jaamam_count=8):
    """ 
        Same as Gauri Chogadiya
        In tamil there 8 jaamam (aka yaamam) 4 for day and 4 for night
        Alternative there is another ancient tamil system with 10 yaamam (5+5)
        In Tamil 1 jaamam = 3 muhurthas. 10 jaamam = 1 day (5 jaamam) and night (5 jaamam)
        8th jaamam = 3rd muhurtha of night
        In Sanskrit these are 8 prahar (4+4) => Gauri Chogadiya
    """
    if jaamam_count not in [8,10]: jaamam_count = 8
    dl = day_length(jd, place); day_jaamam = dl/jaamam_count/2
    nl = night_length(jd, place); night_jaamam = nl/jaamam_count/2
    sunrise_hours = sunrise(jd, place)[0]
    sunset_hours = sunset(jd, place)[0]
    jaamam = [(sunrise_hours+j*day_jaamam,sunrise_hours+(j+1)*day_jaamam) for j in range(5)]
    jaamam += [(sunset_hours+j*night_jaamam,sunset_hours+(j+1)*night_jaamam) for j in range(5)]
    return jaamam
def nishita_muhurtha(jd,place):
    """ 2 ghathis around midnight """
    nl = night_length(jd, place); gn = nl/30.0
    sunset_hours = sunset(jd, place)[0]
    _midnight = sunset_hours+0.5*nl
    return _midnight-gn,_midnight+gn
def thaaraabalam(jd,place,return_only_good_stars=True):
    """
    thaarabalam_names = [('Paramitra','Good'),('Janma','Not Good'),('Sampatha','Very Good'),('Vipatha','Bad'),
                        ('Kshema','Good'),('Pratyaka','Not Good'),('Sadhana','Very Good'),('Naidhana','Totally Bad'),
                         ('Mitra','Good')]
    """
    good_tharaabalam = [0,2,4,6,8]; gtb = []
    nak = nakshatra(jd, place); todays_star = nak[0]
    #print('todays star',utils.NAKSHATRA_LIST[todays_star-1],utils.to_dms(nak[2]))
    tb_dict = [[] for _ in range(9)]
    for birth_star in range(1,28):
        tb_div = utils.count_stars(birth_star,todays_star)%9
        if return_only_good_stars and tb_div in good_tharaabalam: gtb.append(birth_star)
        tb_dict[tb_div].append(birth_star) 
    return gtb if return_only_good_stars else tb_dict
def muhurthas(jd, place):
    dl = day_length(jd, place); day_muhurtha = dl/15
    nl = night_length(jd, place); night_muhurtha = nl/15
    sunrise_hours = sunrise(jd, place)[0]
    sunset_hours = sunset(jd, place)[0]
    _muhurthas = [(sunrise_hours+j*day_muhurtha,sunrise_hours+(j+1)*day_muhurtha) for j in range(15)]#Fixed V4.3.6
    _muhurthas += [(sunset_hours+j*night_muhurtha,sunset_hours+(j+1)*night_muhurtha) for j in range(15)]#Fixed 4.3.6
    _mh_list = [(mk,const.muhurthas_of_the_day[mk],_muhurthas[mh]) for mh,mk in enumerate(const.muhurthas_of_the_day.keys()) ]
    return _mh_list
def udhaya_lagna_muhurtha(jd,place):
    """
        returns ascendant entry jd into each of 12 rasis from given date/time
        returns [(rasi,rasi_entry_jd,rasi_exit_jd),...]
    """
    asc = ascendant(jd, place)[0]
    jd_start = next_ascendant_entry_date(jd, place, direction=-1)[0]
    jd = jd_start+const.conjunction_increment
    ulm = []
    for l in range(12):
        jd_end = next_ascendant_entry_date(jd, place,precision=1.0)[0]
        _,_,_,fhs = utils.jd_to_gregorian(jd_start)
        _,_,_,fhe = utils.jd_to_gregorian(jd_end)
        ulm.append(((asc+l)%12,fhs,fhe))
        jd_start = jd_end
        jd = jd_end+const.conjunction_increment
    return ulm
def chandrabalam(jd,place):
    ascs = [(ulm[0],ulm[1]) for ulm in udhaya_lagna_muhurtha(jd, place)]
    moon = int(lunar_longitude(jd)/30)+1
    next_sunrise = sunrise(jd+1,place)[-1]
    cb_good = [1,3,6,7,10]
    cb = [ah for ah,at in ascs if utils.count_rasis(ah,moon) in cb_good and at < next_sunrise]
    next_moon = next_planet_entry_date(planet=1, jd=jd, place=place)[0]
    if next_moon < next_sunrise:
        #print('moon in two rasis today')
        cb += [ah for ah,at in ascs if utils.count_rasis(ah,(moon+1)%12) in cb_good and at < next_sunrise]
    return cb
def panchaka_rahitha(jd,place):
    ulm = udhaya_lagna_muhurtha(jd, place)
    bad_panchakas = [1,2,4,6,8]
    pr = []
    for asc,asc_beg,asc_end in ulm:
        _tithi = tithi(jd, place)[0]+1
        _nak = nakshatra(jd, place)[0]
        _day = vaara(jd,place)+1
        _asc_rasi = asc+1
        rem = (_tithi+_nak+_day+_asc_rasi)%9
        if rem in bad_panchakas:
            pr.append((rem,asc_beg,asc_end))
        else:
            pr.append((0,asc_beg,asc_end))
    return pr
def next_panchaka_days(jd,place):
    """
        Added in V4.2.6
        Start and ending of panchak nakshthras
        The five Panchak Nakshatras are as follows:3rd and 4th pada of Dhanishta, Shatabisha, Purva Bhadrapada
        Uttara Bhadrapada, Revati.
        Calculate moon entry of Kumbha (Dhanishta 3rd paadham) and moon entry of Aries (end of Revathi)
        @return: start_jd_of_dhanishta 3rd paada, end_jd_of_revathi
    """
    panchaka_start_jd = next_planet_entry_date(const._MOON, jd, place, raasi=const.AQUARIUS+1)[0]
    panchaka_end_jd = next_planet_entry_date(const._MOON, jd, place, raasi=const.ARIES+1)[0]
    return utils.jd_to_gregorian(panchaka_start_jd), utils.jd_to_gregorian(panchaka_end_jd)
def chandrashtama(jd, place):
    jd_utc = jd - place.timezone/24.
    moon_long = lunar_longitude(jd_utc); moon = dasavarga_from_long(moon_long)[0]
    _chandrashtama_rasi = (moon-7)%12+1
    next_moon_jd = next_planet_entry_date(const._MOON, jd, place)[0]
    return _chandrashtama_rasi, next_moon_jd
def nava_thaara_old(jd,place,from_lagna_or_moon=None):
    if from_lagna_or_moon is None: from_lagna_or_moon = const.NAVA_THARA.FROM_LAGNA
    base_star = ( nakshatra(jd, place)[0]-1 if from_lagna_or_moon==const.NAVA_THARA.FROM_MOON
                  else ascendant(jd,place)[2]-1 )
    ntl = [[(base_star+s)%27 for s in star_list] for _, star_list in const.nakshathra_lords.items()]
    return [(lord,sl) for sl in ntl for lord,csl in const.nakshathra_lords.items() if sorted(sl)==sorted(csl) ]
def _nava_thaara_from_planet_longitude(planet_longitude):
    base_star = nakshatra_pada(planet_longitude)[0]-1
    ntl = [[(base_star+s)%27 for s in star_list] for _, star_list in const.nakshathra_lords.items()]
    result = [(lord,sl) for sl in ntl for lord,csl in const.nakshathra_lords.items() if sorted(sl)==sorted(csl) ]
    return result

def _special_thaara_from_planet_longitude(planet, planet_longitude):
    # Get 1-based nakshatra index and convert to 0-based (0 to 26 for standard 27)
    base_star = nakshatra_pada(planet_longitude)[0] - 1
    
    # Fix: Both Lagna and planets must use the same base increment (-1) 
    # so that the Janma star correctly matches the reference body's actual nakshatra.
    base_inc = -1 
    
    # Adjust base star index if it lies on or past Abhijit in the 28-star arrangement
    if base_star >= const._ABHIJITH_STAR_INDEX:
        base_star += 1
        
    stl = [(base_star + s + base_inc) % 28 for s in const.special_thaara_map]
    
    return [
        (lord, star - 1 if star > const._ABHIJITH_STAR_INDEX else star) 
        for star in stl 
        for lord, csl in const.special_thaara_lords_1.items() 
        if star in csl
    ]

def nava_thaara(jd,place,base_star_planet=None):
    if base_star_planet is None: _base_star_planet = const._ascendant_symbol
    if base_star_planet not in [const._ascendant_symbol]+const.SUN_TO_KETU:
        raise ValueError("Base star planet should be either 'L' or 0 (Sun) to 8(Ketu)")
    if base_star_planet == const._ascendant_symbol:
        asc =  ascendant(jd,place)
        _planet_longitude = asc[0]*30+asc[1] 
    else:
        p_swe = ephemeris_planet_index(base_star_planet)
        jd_utc = jd - place.timezone/24.0
        _planet_longitude = sidereal_longitude(jd_utc,p_swe)
    return _nava_thaara_from_planet_longitude(_planet_longitude)
def special_thaara_old(jd,place,from_lagna_or_moon=0):
    """
        Note: the star list includes Abhijith as 21st star
    """
    base_star = nakshatra(jd, place)[0]-1 if from_lagna_or_moon==1 else ascendant(jd,place)[2]-1
    base_inc = -1  if from_lagna_or_moon==1 else 0
    stl = [(base_star+s+base_inc)%28 for s in const.special_thaara_map]
    _star_list = utils.get_nakshathra_list_with_abhijith()
    if base_star+1 > const._ABHIJITH_STAR_INDEX: base_star += 1
    return [(lord,star) for star in stl for lord, csl in const.special_thaara_lords_1.items() if star in csl]

def special_thaara(jd,place,base_star_planet=None):
    if base_star_planet is None: base_star_planet = const._ascendant_symbol
    if base_star_planet not in [const._ascendant_symbol]+const.SUN_TO_KETU:
        raise ValueError("Base star planet should be either 'L' or 0 (Sun) to 8(Ketu)")
    if base_star_planet == const._ascendant_symbol:
        asc = ascendant(jd,place)
        planet_longitude = asc[0] * 30 + asc[1]
    else:
        p_swe = ephemeris_planet_index(base_star_planet)
        jd_utc = jd - place.timezone/24.0
        planet_longitude = sidereal_longitude(jd_utc,p_swe)
    return _special_thaara_from_planet_longitude(base_star_planet, planet_longitude)
def karaka_tithi(jd,place):
    pp = [['L',(0,-10)]]+dhasavarga(jd, place) # Dummy Lagna Positions added
    from jhora.horoscope.chart.house import chara_karakas
    ks = chara_karakas(pp)
    p1 = [k for k,v in planet_list.items() if v==ks[1]][0]
    p2 = [k for k,v in planet_list.items() if v==ks[0]][0]
    kt = tithi(jd, place, tithi_index=1, planet1=p1, planet2=p2)
    return kt
def karaka_yogam(jd,place):
    """
        returns the yogam at julian day/time
        @param jd: Julian Day Number of the date/time
        @param place: Place as struct ('Place',latitude,longitude,timezone)
        @return [yogam number, yogam starting time, yogam ending time, yogam fraction left, 
                 next yogam number, next yogam starting time, next yogam ending time, next yogam fraction left]
          next yogam index and next yogam time is additionally returned if two yogams on same day 
          yogam index = [1..27]  1 = Vishkambha, 2 = Priti, ..., 27 = Vaidhrti
    """
    pp = [['L',(0,-10)]]+dhasavarga(jd, place) # Dummy Lagna Positions added
    from jhora.horoscope.chart import house
    ks = house.chara_karakas(pp)
    p1 = [k for k,v in planet_list.items() if v==ks[1]][0]
    p2 = [k for k,v in planet_list.items() if v==ks[0]][0]
    return yogam(jd, place, tithi_index=1, planet1=p1, planet2=p2, cycle=1)
    _yoga = _get_yogam(jd, place,planet1=p1,planet2=p2)
    _yoga_prev = _get_yogam(jd-1, place,planet1=p1,planet2=p2)
    _yoga_no = _yoga[0]; _yoga_start = _yoga_prev[1]; _yoga_end = _yoga[1]
    if _yoga_start < 24.0:
        _yoga_start = -_yoga_start
    elif _yoga_start > 24:
        _yoga_start -= 24.0
    result = [_yoga_no,_yoga_start,_yoga_end]
    if len(_yoga)>2:
        _yn = _yoga[2]; _yn_start = _yoga_end; _yn_end = _yoga[3]
        result += [_yn,_yn_start,_yn_end]
    return result
def fraction_moon_yet_to_traverse(jd,place,round_to_digits=5):
    jd_utc = jd - place.timezone/24.
    one_star = 360/27
    moon_long = lunar_longitude(jd_utc)
    _,_,rem = nakshatra_pada(moon_long)
    moon_fraction_yet_to_traverse = (one_star-rem)/one_star
    return moon_fraction_yet_to_traverse#round(moon_fraction_yet_to_traverse,round_to_digits)
def shiva_vaasa(jd,place,method=2):
    """ 
        Ref: https://vijayalur.com/2014/07/24/shiva-agni-vasa/
        Method=1: general from tithi table
        Method=2: for rudrabisheka
        Method: 1
            Tithis              Shiva’s Place                 Result
            1, 8 & 15           In Cemetery                   Death
            2, 9 & 30           With Gowri                    Happiness & Wealth
            3 & 10              In assembly                   Grief
            4 & 11              At work / play                Difficulty
            5 & 12              At Kailash                    Happiness
            6 & 13              Mounted on Vrishabha (Nandi)  Success
            7 & 14              At Dinner / Meditation        Trouble (Peeda)
        Method: 2
            (tithi_index (1 to 30) * 2 + 5) / 7 => Get Remainder
            {1: 5-Kailash 2: 2-With Gowri 3: 6-Mounted on Nandi 4: 3-In assembly
            5: 7-At dinner / meditation 6: 4-At work / play 0: 1-In cemetry
        @return shiva_vaasa_index (1:In Cemetery,2:With Gowri, 3:In assembly, 4:At work / play
                                   5:At Kailash, 6:Mounted on Vrishabha (Nandi), 7:At Dinner / Meditation
    """
    tit = tithi(jd,place); tithi_index = tit[0]; t_end = tit[2]
    _place_dict1 = {1:1,2:2,3:3,4:4,5:5,6:6,7:7,
                    8:1,9:2,10:3,11:4,12:5,13:6,14:7,
                    16:1,17:2,18:3,19:4,20:5,21:6,22:7,
                    23:1,24:2,25:3,26:4,27:5,28:6,29:7,
                    15:1,30:2}
    _place_dict2 = {0:1,1:5,2:2,3:6,4:3,5:7,6:4}
    _place_dict = _place_dict1 if method==1 else _place_dict2
    return _place_dict1[tithi_index] if method==1 else _place_dict2[(tithi_index*2+5) % 7],t_end
def agni_vaasa(jd,place):
    """
        
        @return agni_vaasa_index 
            1:Prithvi (Earth) - bestow comfort, 
            2:Akaasha (Space) - life threatening
            3:PaathaaLa (Nadir) - destroy wealth
    """
    tit = tithi(jd,place); tithi_index = tit[0]; t_end = tit[2]
    day = vaara(jd,place)+1
    _av_list = [1,2,3,1]
    return _av_list[(tithi_index+1+day)%4], t_end
def pushkara_yoga(jd, place):
    """
        returns dwi/tri pushkara yoga if exists
        @return 
            0,'',1/-1: No Dwi/Tri pushkara yoga
            1,time,1/-1: dwi pushakara yoga
            2,time,1/-1: tri pushkara yoga
                last element 1 means from time
                            -1 means to time
    """
    _tithi_list = [2, 17, 7, 22, 12, 27]; _day_list = [1,3,7]
    _dwi_star_list = [5, 14, 23]; _tri_star_list = [16, 7, 3, 11, 21, 25]
    tit = tithi(jd, place); _t_no = tit[0]; _t_start = tit[1]; _t_end = tit[2]
    day = vaara(jd,place)+1
    nk = nakshatra(jd, place);nak = nk[0]; _n_start = nk[2]; _n_end = nk[3]
    srise1 = sunrise(jd,place)[0]; srise2 = sunrise(jd+1,place)
    ptimes = ()
    chkd = day in _day_list
    chkt = _t_no in _tithi_list or (_t_no+29)%30 in _tithi_list
    if chkd and chkt:
        chkn11 = nak in _dwi_star_list; chkn12 = (nak+26)%27 in _dwi_star_list
        if chkn11 or chkn12:
            ptimes = (1,_n_start,srise2) if chkn11 else (1,srise1,_n_start)
        chkn21 = nak in _tri_star_list; chkn22 = (nak+26)%27 in _tri_star_list
        if chkn21 or chkn22:
            ptimes = (2,_n_start,srise2) if chkn11 else (2,srise1,_n_start)
    return ptimes
def aadal_yoga(jd,place):
    jd_utc = jd - place.timezone/24.
    nak = nakshatra(jd, place); star_end = nak[3]
    moon_star = nakshatra_pada(lunar_longitude(jd_utc))[0]
    sun_star = nakshatra_pada(solar_longitude(jd_utc))[0]
    srise = sunrise(jd,place)[0]
    knt = utils.cyclic_count_of_stars_with_abhijit_in_22(const.abhijit_order_of_stars, sun_star-1,moon_star-1)
    #print(moon_star,sun_star,knt,'in',[2,7,9,14,16,21,23,28])
    return (srise,star_end) if knt in [2,7,9,14,16,21,23,28] else ()
def vidaal_yoga(jd,place):
    jd_utc = jd - place.timezone/24.
    nak = nakshatra(jd, place); star_end = nak[3]
    moon_star = nakshatra_pada(lunar_longitude(jd_utc))[0]
    sun_star = nakshatra_pada(solar_longitude(jd_utc))[0]
    srise = sunrise(jd,place)[0]
    knt = utils.cyclic_count_of_stars_with_abhijit_in_22(const.abhijit_order_of_stars, sun_star-1,moon_star-1)
    #print(moon_star,sun_star,knt,'in',[3,6,10,13,17,20,24,27])
    return (srise,star_end) if knt in [3,6,10,13,17,20,24,27] else ()
def disha_shool(jd,place):
    return const.disha_shool_map[vaara(jd,place)]
def yogini_vaasa(jd,place):
    tithi_index = tithi(jd,place)[0]
    return const.yogini_vaasa_tithi_map[tithi_index-1]
 # Convert to Ghati, Phala Vighati
def vedic_time_equal_day_night_ghati(jd,place,float_hours=None,
                                                    vedic_hours_per_day=60):
    """
        @param vedic_hours_per_day = 30 (Muhurthas) or 60 (Ghati)
        This feature is for experimental purpose. 
        Some panchang websites like drikpanchang may force 30 ghatis for both day and night
        so that sunset is always equals to 30 ghati. 
        But traditionally vedic praharas are unequal when day/nights are unequal
        So use this function with caution
    """
    if vedic_hours_per_day not in [30,60]: vedic_hours_per_day = 60
    _half_vedic_hour_per_day = vedic_hours_per_day/2
    _DEBUG_ = False
    if float_hours is None:
        if _DEBUG_: print('getting float hours from jd')
        _, _, _, float_hours = utils.jd_to_gregorian(jd)
    if _DEBUG_: print('float_hours',float_hours)
    today_sunrise = sunrise(jd, place)[0]; today_sunset = sunset(jd,place)[0]
    _day_length = day_length(jd, place); _night_length = night_length(jd, place)
    if _DEBUG_: print('today_sunrise',today_sunrise,'today_sunset',today_sunset)
    day_ghati_per_hour = _half_vedic_hour_per_day / _day_length
    night_ghati_per_hour = _half_vedic_hour_per_day / _night_length
    if _DEBUG_: print('day_ghati_per_hour',day_ghati_per_hour,'night_ghati_per_hour',night_ghati_per_hour)
    if float_hours <= today_sunset and float_hours >= today_sunrise:
        if _DEBUG_: print('float hours in day time')  
        ghati_hours = float_hours - today_sunrise
        if ghati_hours < 0:
            ghati_hours += 24
        total_ghati = ghati_hours * day_ghati_per_hour
    else:
        if _DEBUG_: print('float hours in night time')
        total_ghati = _half_vedic_hour_per_day + (float_hours-today_sunset)*night_ghati_per_hour if float_hours>=today_sunset \
                        else vedic_hours_per_day - (today_sunrise-float_hours)*night_ghati_per_hour
    total_ghati = total_ghati % vedic_hours_per_day  # Reset to 0 after 60 ghatis

    ghati = int(total_ghati)
    phala = int((total_ghati - ghati) * vedic_hours_per_day)
    vighati = int(((total_ghati - ghati) * vedic_hours_per_day - phala) * vedic_hours_per_day)

    return int(ghati), int(phala), int(vighati)
def vedic_time(jd, place, float_hours=None, force_equal_day_night_ghati=True,
                              vedic_hours_per_day=60):
    """
        @param vedic_hours_per_day = 30 (Muhurthas) or 60 (Ghati)
        @return (ghati, phala, vighati) for the given jd and place
        force_equal_day_night_ghati = True will force equal 30 ghatis for day and night.
        This feature is for experimental purpose. 
        Some panchang websites like drikpanchang may force 30 ghatis for both day and night
        so that sunset is always equals to 30 ghati. 
        But traditionally vedic praharas are unequal when day/nights are unequal
        So use this function with caution. 
        Also enabling this feature in vedic clock will show unqual hand movements
    """
    if vedic_hours_per_day not in [30, 60]: vedic_hours_per_day = 60
    if force_equal_day_night_ghati: return vedic_time_equal_day_night_ghati(jd, place, float_hours)
    if float_hours is None:
        _, _, _, float_hours = utils.jd_to_gregorian(jd)

    sunrise_1 = sunrise(jd, place)[0]

    # evaluation sunrise baselines
    if float_hours < sunrise_1:
        sunrise_0 = sunrise(jd - 1, place)[0] - 24  # yesterday sunrise on a continuous timeline
        sunrise_2 = sunrise_1                        # "end" is today's sunrise
    else:
        sunrise_2 = 24 + sunrise(jd + 1, place)[0]  # tomorrow sunrise on a continuous timeline
        sunrise_0 = sunrise_1                        # "start" is today's sunrise

    ghati_per_hour = vedic_hours_per_day / (sunrise_2 - sunrise_0)
    # ---- CHANGE ENDS HERE ----

    local_hours_since_sunrise = float_hours - sunrise_1
    if local_hours_since_sunrise < 0:
        local_hours_since_sunrise += 24

    total_ghati = local_hours_since_sunrise * ghati_per_hour
    total_ghati = total_ghati % vedic_hours_per_day  # Reset to 0 after 60 ghatis

    ghati = int(total_ghati)
    phala = int((total_ghati - ghati) * vedic_hours_per_day)
    vighati = int(((total_ghati - ghati) * vedic_hours_per_day - phala) * vedic_hours_per_day)

    return int(ghati), int(phala), int(vighati)
def next_solar_month(jd,place,raasi=None):
    """
        Next solar month is when Sun Enters a next zodiac/raasi
    """
    return next_planet_entry_date(0, jd, place,raasi=raasi)
def previous_solar_month(jd,place,raasi=None):
    """
        Previous solar month is when Sun Enters a previous/current zodiac/raasi
    """
    return previous_planet_entry_date(0, jd, place,raasi=raasi)
def next_solar_year(jd,place):
    """
        Next solar month is when Sun Enters Aries
    """
    return next_planet_entry_date(0, jd, place,raasi=1)
def previous_solar_year(jd,place):
    """
        Previous solar month is when Sun Enters Aries
    """
    return previous_planet_entry_date(0, jd, place, raasi=1)
def next_lunar_year(jd,place,lunar_month_type=None,direction=1):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    _DEBUG_= False
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = utils.jd_to_gregorian(next_solar_year(jd, place)[0]); 
        return Date(lmy,lmm,lmd),lmh
    for _ in range(13):
        lmy,lmm,lmd,lmh = next_lunar_month(jd, place, lunar_month_type) if direction==1 else previous_lunar_month(jd, place, lunar_month_type)
        #tithi_ = tithi(jd,place)[0]
        #lmy,lmm,lmd,lmh = utils.jd_to_gregorian(new_moon(jd,tithi_,opt=direction)) if lunar_month_type==0 else utils.jd_to_gregorian(full_moon(jd,tithi_,opt=direction))
        if _DEBUG_: print(lunar_month_type,(lmy,lmm,lmd),lmh)
        jd = utils.julian_day_number(Date(lmy,lmm,lmd), (lmh,0,0))
        lm = lunar_month_date(jd, place, use_purnimanta_system=(lunar_month_type==const.LUNAR_MONTH_TYPE.PURNIMANTHA))
        if _DEBUG_: print('lunar month date',lm)
        _lunar_month_number=((lm[0]+1)%12 if lm[1]==30 else lm[0]) ##<<< TODO: Something wrong lm[-1] is not lunar day
        _lunar_month_start = 1
        if _lunar_month_number==_lunar_month_start:
            _tithi = tithi(jd,place)
            if _DEBUG_: print('found lunar year date',_tithi)
            if _DEBUG_: print('before lm',lm)
            if lm[-1]>1 and direction==1:
                if _DEBUG_: print('lunar month day is >1',lm[-1])
                lmy,lmm,lmd = utils.previous_panchanga_day(Date(lmy,lmm,lmd), minus_days=1)
                lm_jd = utils.julian_day_number(Date(lmy,lmm,lmd),(lmh,0,0))
                _tithi = tithi(lm_jd,place)
                lmh = _tithi[2]
                if _DEBUG_: print('after lm',lunar_month_date(jd-1, place,
                                        use_purnimanta_system=(lunar_month_type==const.LUNAR_MONTH_TYPE.PURNIMANTHA)))
            elif _tithi[1] < 0 and (_tithi[0]==1 or _tithi[0]==16) and direction==1:
                if _DEBUG_: print('tithi on lunar year day starts previous day',_tithi[1])
                lmy,lmm,lmd = utils.previous_panchanga_day(Date(lmy,lmm,lmd), minus_days=1)
                lmh = abs(_tithi[1])
            return Date(lmy,lmm,lmd),lmh
        jd += direction*14
    if _DEBUG_: print('next/prev lunar_year could not be found')
def previous_lunar_year(jd,place,lunar_month_type=None):
    """
        @param lunar_month_type: 0=>Amantha 1=>Purnimantha 2=>Solar month
    """
    if lunar_month_type is None: lunar_month_type = const.LUNAR_MONTH_TYPE.AMANTHA
    _DEBUG_ = False
    if lunar_month_type==2:
        lmy,lmm,lmd,lmh = utils.jd_to_gregorian(previous_solar_year(jd, place)[0]); 
        return Date(lmy,lmm,lmd),lmh
    return next_lunar_year(jd, place, lunar_month_type, direction=-1)
special_tithis = lambda jd,place: [[tithi(jd, place, tithi_index=t,cycle=c) for t in range(1,13)] for c in range(1,4)]
def is_night_birth(jd, place):
    """
    Night birth = (birth_time >= sunset on birth date) or (birth_time < sunrise on birth date).
    Assumptions:
      - utils.jd_to_gregorian(jd) returns local date and local float hours for the birth place/time.
      - drik.sunrise/sunset return local float hours (as first item in their tuple) for that date and place.
    """
    _, _, _, birth_hours = utils.jd_to_gregorian(jd)
    sunrise_hours = sunrise(jd, place)[0]
    sunset_hours  = sunset(jd, place)[0]
    return (birth_hours >= sunset_hours) or (birth_hours < sunrise_hours)
def set_planet_list(set_rahu_ketu_as_true_nodes=None,
                    include_western_planets=None):
    """
        @param set_rahu_ketu_as_true_nodes:
            True (Default) Rahu/Ketu are set as True Nodes 
            False: Rahu/Ketu are set as Mean Nodes
            None: Exclude Rahu/Ketu from the list
        @param include_western_planets:
            False: (Default) Uranus/Neptune/Pluto are excluded
            True: Uranus/Neptune/Pluto are included
    """
    if set_rahu_ketu_as_true_nodes is None: set_rahu_ketu_as_true_nodes = const._use_true_nodes_for_rahu_ketu
    if include_western_planets is None: include_western_planets = const._INCLUDE_URANUS_TO_PLUTO
    const._INCLUDE_URANUS_TO_PLUTO = include_western_planets # V4.8.5
    const._use_true_nodes_for_rahu_ketu = set_rahu_ketu_as_true_nodes
    global planet_list
    swe_rahu = swe.TRUE_NODE if set_rahu_ketu_as_true_nodes else swe.MEAN_NODE
    planet_list = {const._SUN:const.SUN_ID,const._MOON:const.MOON_ID,const._MARS:const.MARS_ID,
                   const._MERCURY:const.MERCURY_ID,const._JUPITER:const.JUPITER_ID,const._VENUS:const.VENUS_ID,
                   const._SATURN:const.SATURN_ID,swe_rahu:const.RAHU_ID,const._KETU:const.KETU_ID}
    _western_planets = {const._URANUS:const.URANUS_ID,const._NEPTUNE:const.NEPTUNE_ID, const._PLUTO:const.PLUTO_ID}
    if include_western_planets:planet_list = {**planet_list,**_western_planets}
set_planet_list()
def ascendant_speed(jd,place):
    _,lat,lon,tz = place
    jd_utc = jd = tz/24.0
    asc_speed = swe.houses_ex2(jd_utc,lat,lon,flags=_rise_flags)[3][0]
    return asc_speed
def ardra_pravesha_date(jd,place,direction=1,increment_speed_factor=0.01,precision=0.1):
    return next_planet_nakshathra_pravesha_date(planet=const.SUN_ID, nakshathra=6, jd=jd, place=place, direction=direction,
                                                increment_speed_factor=increment_speed_factor, precision=precision)
def next_planet_nakshathra_pravesha_date(planet,nakshathra,jd,place,direction=1,increment_speed_factor=0.01,
                                          precision=0.1):
    """
        get the date when a planet enters a zodiac
        @param planet: planet index (0=Sun..8=Kethu)
        @param panchanga_date: Date struct (y,m,d)
        @param panchanga_place: Place struct ('place',latitude,longitude,timezone)
        @param direction: 1= next entry, -1 previous entry
        @param increment_days: incremental steps in days algorithm to check for entry (Default=1 day)
        @param precision: precision in degrees within which longitude entry whould be (default: 0.1 degrees)
        @param raasi: raasi at which planet should enter. 
            If raasi==None: gives entry to next constellation
            If raasi is specified [1..12] gives entry to specified constellation/raasi
        @return Julian day number of planet entry into zodiac
    """
    multiple = 360.0/27.0*(nakshathra-1)
    p_swe = ephemeris_planet_index(planet)
    p_speed = daily_planet_speed(jd,place,planet)
    if abs(p_speed)<1.e-6: p_speed = 0.1 # Keep some non-zero speed
    jd_utc = jd - place.timezone/24.0
    increment_days = increment_speed_factor/p_speed
    if planet in [const.RAHU_ID,const.KETU_ID]: direction *= -1 # Rahu/Ketu always in reverse direction
    sl = sidereal_longitude(jd_utc,p_swe)
    while True:
        if sl < (multiple+precision) and sl>(multiple-precision):
            break
        jd += increment_days*direction; jd_utc = jd - place.timezone/24.0
        sl = sidereal_longitude(jd_utc,p_swe)
    sank_date = jd_to_gregorian(jd_utc)
    sank_sunrise = sunrise(jd_utc,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    planet_longs = []
    for t in offsets:
        sl = sidereal_longitude(sank_sunrise+t,p_swe)
        planet_longs.append(sl)
    planet_hour = utils.inverse_lagrange(offsets, planet_longs, multiple) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    planet_hour1 = (sank_sunrise + planet_hour - sank_jd_utc)*24+place.timezone
    sank_jd_utc += planet_hour1/24.0
    planet_long = sidereal_longitude(sank_jd_utc-place.timezone/24,p_swe)
    y,m,d,fh = jd_to_gregorian(sank_jd_utc); sank_date = Date(y,m,d); planet_hour1 = fh
    return sank_jd_utc,planet_long
def next_planet_entry_date_general(jd, place, planet, planet_longitude=None, nakshathra=None, raasi=None, direction=1,
                                    increment_speed_factor=0.001, precision=0.1, divisional_chart_factor=1,
                                    increment_days=0.01):
    """
    Optimized general entry date finder for custom longitudes, nakshatras, or raasis.
    Uses Kinematic Bracketing, False Position, and Exact Linear Interpolation.
    """
    jd_utc = jd - place.timezone / 24.0
    
    # 1. Handle Ascendant delegation
    if planet == const._ascendant_symbol:
        ret_jd, ret_long = next_ascendant_entry_date(
            jd=jd, place=place, direction=direction, raasi=raasi, 
            precision=max(precision, 0.1), divisional_chart_factor=divisional_chart_factor
        )
        return ret_jd, ret_long
        
    p_swe = ephemeris_planet_index(planet)
    
    # 2. Handle Rahu/Ketu delegation for standard constellation entry
    if planet_longitude is None and nakshathra is None and planet in [const.RAHU_ID, const.KETU_ID]:
        ret_jd, ret_long = next_planet_entry_date(planet, jd, place, direction, raasi=raasi)
        return ret_jd, ret_long

    # 3. Determine target boundary precisely
    if planet_longitude is not None: 
        multiple = planet_longitude
    elif nakshathra is not None: 
        multiple = (nakshathra - 1) * (360.0 / 27.0)
    elif raasi is not None: 
        multiple = (raasi - 1) * 30.0
    else:
        p_long = sidereal_longitude(jd_utc, p_swe)
        multiple = (((p_long // 30) + 1) % 12) * 30.0
        if direction == -1: 
            multiple = (p_long // 30) * 30.0

    target_long = multiple % 360.0

    def get_diff(t):
        sl = sidereal_longitude(t, p_swe)
        diff = (sl - target_long) % 360.0
        if diff > 180.0: 
            diff -= 360.0
        return diff

    # 4. Kinematic Maximum Speeds (degrees per day)
    max_speeds = {
        const._MOON: 15.5,
        const._SUN: 1.05,
        const._MERCURY: 2.5,
        const._VENUS: 1.3,
        const._MARS: 0.85,
        const._JUPITER: 0.26,
        const._SATURN: 0.13,
        const._RAHU: 0.07
    }
    max_speed = max_speeds.get(p_swe, 2.0)
    
    bracket_steps = {
        const._MOON: 0.25,
        const._SUN: 2.0,
        const._MERCURY: 1.0,
        const._VENUS: 1.0,
        const._MARS: 3.0,
        const._JUPITER: 5.0,
        const._SATURN: 10.0,
        const._RAHU: 10.0
    }
    safe_bracket = bracket_steps.get(p_swe, 1.0) * direction

    t0 = jd_utc
    diff0 = get_diff(t0)

    # Nudge forward slightly if starting exactly on target
    if abs(diff0) < 0.0001:
        t0 += (0.01 * direction)
        diff0 = get_diff(t0)

    t1 = t0
    diff1 = diff0

    # Phase 1: Kinematic Predictive Bracketing
    for _ in range(1000):
        distance = abs(diff1)
        if distance > 3.0:
            step = (distance / max_speed) * 0.85 * direction
        else:
            step = safe_bracket
            
        t1 += step
        diff1 = get_diff(t1)
        
        if diff0 * diff1 <= 0 and abs(diff0) < 45: 
            break
            
        t0 = t1
        diff0 = diff1
    else:
        raise ValueError(f"Could not find transit for planet {planet} within search limits.")

    # Phase 2: False Position Root-Finding to narrow to ~1 minute
    precision_days = 0.001 

    while abs(t1 - t0) > precision_days:
        if diff1 - diff0 == 0:
            t_mid = (t0 + t1) / 2.0
        else:
            t_mid = t1 - diff1 * (t1 - t0) / (diff1 - diff0)
            
        diff_mid = get_diff(t_mid)
        
        if abs(diff_mid) < 0.000001:
            t0 = t_mid
            t1 = t_mid
            break
            
        if diff0 * diff_mid < 0:
            t1 = t_mid
            diff1 = diff_mid
        else:
            t0 = t_mid
            diff0 = diff_mid

    # Phase 3: Exact Linear Interpolation for Sub-Arcsecond Precision
    if diff1 - diff0 != 0:
        exact_jd_utc = t0 - diff0 * (t1 - t0) / (diff1 - diff0)
    else:
        exact_jd_utc = (t0 + t1) / 2.0

    exact_long = sidereal_longitude(exact_jd_utc, p_swe)
    exact_jd = exact_jd_utc + place.timezone / 24.0
    return exact_jd, exact_long
def next_planet_entry_date_general_old(jd,place,planet,planet_longitude=None,nakshathra=None,raasi=None,direction=1,
                            increment_speed_factor=0.001,precision=0.1,divisional_chart_factor=1,
                            increment_days=0.01):
    """
        get the date when a planet enters a zodiac or nakshathra or a given longitude
        @param jd: julian day 
        @param planet: planet index (0=Sun..8=Kethu)
        @param place: Place struct ('place',latitude,longitude,timezone)
        Specify one of:
            @param planet_longitude: specific longitude of the planet
            @param nakshathra: Planet coinciding with a specified nakshathra (1 to 27)
            @param raasi: raasi at which planet should enter. 
                If raasi==None: gives entry to next constellation
                If raasi is specified [1..12] gives entry to specified constellation/raasi
        @param direction: 1= next entry, -1 previous entry
        @param increment_speed_factor: speed adjustment factor 
        @param increment_days: incremental steps in days algorithm to check for entry (Default=1 day)
        @param precision: precision in degrees within which longitude entry whould be (default: 0.1 degrees)
        @param divisional_chart_factor: varga chart index (default= 1 = Raasi chart) 
        @return (year,month,day,float_hours),planet_longitude
    """
    jd_utc = jd - place.timezone/24.0
    p_swe = ephemeris_planet_index(planet)
    if planet_longitude is None and nakshathra is None:
        if planet==const._ascendant_symbol:
            """ Do not decrease precision below 0.5 or even 0.1 Asc entry values are sensitive """
            return next_ascendant_entry_date(jd=jd, place=place, direction=direction,raasi=raasi, precision=0.5,
                                             divisional_chart_factor=divisional_chart_factor)
        if planet in [const.RAHU_ID,const.KETU_ID]:# and direction ==-1:
            return next_planet_entry_date(planet,jd, place, direction,raasi=raasi,increment_days=increment_days)
    if planet_longitude is not None: multiple = planet_longitude
    elif nakshathra is not None: multiple = (nakshathra-1)*(360/27.0)
    elif raasi is not None: multiple = (raasi-1)*30
    else:
        p_long = sidereal_longitude(jd_utc, p_swe)
        multiple = (((p_long//30)+1)%12)*30
        if direction==-1: multiple = (p_long//30)%12*30
    p_speed = daily_planet_speed(jd,place,planet)
    #if abs(p_speed)<1.e-6: p_speed = 0.1 # Keep some non-zero speed
    increment_days = increment_speed_factor/p_speed 
    if planet in [const.RAHU_ID,const.KETU_ID]: direction *= -1 # Rahu/Ketu always in reverse direction
    sl = sidereal_longitude(jd_utc,p_swe)
    while True:
        if sl < (multiple+precision) and sl>(multiple-precision):
            break
        jd += increment_days*direction; jd_utc = jd - place.timezone/24.0
        sl = sidereal_longitude(jd_utc,p_swe)
    sank_date = jd_to_gregorian(jd_utc)
    sank_sunrise = sunrise(jd_utc,place)[2]
    sank_date = Date(sank_date[0],sank_date[1],sank_date[2])
    offsets = [0.0, 0.25, 0.5, 0.75, 1.0] 
    planet_longs = []
    for t in offsets:
        sl = sidereal_longitude(sank_sunrise+t,p_swe)
        planet_longs.append(sl)
    planet_hour = utils.inverse_lagrange(offsets, planet_longs, multiple) # Do not move % 360 above
    sank_jd_utc = utils.gregorian_to_jd(sank_date)
    planet_hour1 = (sank_sunrise + planet_hour - sank_jd_utc)*24+place.timezone
    sank_jd_utc += planet_hour1/24.0
    planet_long = sidereal_longitude(sank_jd_utc-place.timezone/24,p_swe)
    y,m,d,fh = jd_to_gregorian(sank_jd_utc); sank_date = Date(y,m,d); planet_hour1 = fh
    return sank_jd_utc,planet_long
def _get_next_raasi(pl,sl,direction=1):
    _next_raasi = int(((sl//30)+1)%12)
    if direction==-1: _next_raasi = int((sl//30)%12)
    if pl == const._RAHU:
        _next_raasi = int((sl//30)%12)
        if direction==-1:
            _next_raasi = int((sl//30+1)%12)
    #print(pl,sl,_next_raasi)
    return _next_raasi
def _true_tropical_year(jd,place,round_to_digits=6):
    """
        Tropical Year = Duration sun takes to pass from one venral equinox to the next
            it is the time sun takes to return to the same position in sky - as viewed from earth (no Ayanamsa applied)
        returns duration in float up to six digits by default e.g. const.tropical_year
    """
    jd_utc = jd-place.timezone/24.0
    veq1 = swe.solcross_ut(0.0,jd_utc-180)
    veq2 = swe.solcross_ut(0.0,veq1+300)
    return veq2-veq1#round(veq2-veq1,round_to_digits)
def true_tropical_year(jd_start, place,round_to_digits=6):
    """
    Computes the True Tropical Year for a given date.
    p
    1. Finds the Sun's true tropical longitude on the input date.
    2. Finds the exact moment the Sun returns to that same longitude next year.
    3. Returns the precise duration in days.
    """
    # 1. Convert local Julian Date to UTC
    jd_utc = jd_start - (place.timezone / 24.0)
    
    # 2. Get the Sun's true ecliptic longitude on this specific date
    # Flag swe.FLG_SWIEPH uses the true, apparent position (no Ayanamsa)
    res, _ = swe.calc_ut(jd_utc, swe.SUN, swe.FLG_SWIEPH)
    target_longitude = res[0]  # First element is longitude in degrees (0-360)
    
    # 3. Find the exact moment the Sun returns to this longitude next year
    # We step forward 300 days to avoid finding the current day's position
    jd_next_return = swe.solcross_ut(target_longitude, jd_utc + 300.0)
    
    # 4. The difference is the True Tropical Year for this specific date
    true_tropical_year_duration = jd_next_return - jd_utc
    
    return true_tropical_year_duration
def true_sidereal_year(jd,place,round_to_digits=6):
    """
        Sidereal Year = Duration earth takes to complete one revoultion around the sun relative fixed stars (Ayanamsa applied)
        returns duration in float up to six digits by default e.g. const.sidereal_year
    """
    jd_sid1,_ = previous_planet_entry_date(const.SUN_ID, jd, place, raasi=1)
    jd_sid2,_ = next_planet_entry_date(const.SUN_ID, jd, place, raasi=1)
    return jd_sid2-jd_sid1# round(jd_sid2-jd_sid1,round_to_digits)
def tithi_year(jd,place,round_to_digits=6):
    ps_date,psh = previous_lunar_year(jd, place, lunar_month_type=const.LUNAR_MONTH_TYPE.AMANTHA)
    jd_prev = utils.julian_day_number(ps_date,(psh,0,0))
    ps_date,psh = next_lunar_year(jd, place, lunar_month_type=const.LUNAR_MONTH_TYPE.AMANTHA)
    jd_next = utils.julian_day_number(ps_date,(psh,0,0))
    return jd_next-jd_prev# round(jd_next-jd_prev,round_to_digits)
def lunar_year(jd,place,round_to_digits=6):
    """
        duration of 12 full cycles of moon ~= 354 days
        returns duration in float up to six digits by default e.g. const.lunar_year
    """
    return const.lunar_year # round(const.lunar_year,round_to_digits)
def savana_year(jd,place,round_to_digits=6,savana_year_method=None):
    """ 
        Returns savana year = duration of 360 sunrise days
        savana_method = -1 (jd-360 to jd) # const.SAVANA_METHOD.RETROSPECTIVE
        savana_method = 0 (jd-180 to jd+180) # const.SAVANA_METHOD.MIDPOINT
        savana_method = 1 (jd to jd+360) # const.SAVANA_METHOD.PROSPECTIVE_0_to_360_JHORA
    """
    if savana_year_method is None: savana_year_method = const.SAVANA_YEAR_METHOD.PROSPECTIVE_0_to_360_JHORA
    jd1 = ( jd if savana_year_method==const.SAVANA_YEAR_METHOD.PROSPECTIVE_0_to_360_JHORA 
            else (jd-180 if savana_year_method==const.SAVANA_YEAR_METHOD.MIDPOINT else jd-360) )
    jd2 = ( jd+360 if savana_year_method==const.SAVANA_YEAR_METHOD.PROSPECTIVE_0_to_360_JHORA 
            else (jd+180 if savana_year_method==const.SAVANA_YEAR_METHOD.MIDPOINT else jd) )
    jd1_rise = sunrise(jd1,place)[-1]
    jd2_rise = sunrise(jd2,place)[-1]
    return jd2_rise-jd1_rise# round(jd2_rise-jd1_rise,round_to_digits)

def _tithi_number_at_jd(jd, place):
    """
    Return instantaneous tithi number at JD.

    Assumes tithi(jd, place, force_tithi_at_sunrise=False)[0]
    returns tithi number 1..30 at the exact JD.
    """
    return int(tithi(jd, place, force_tithi_at_sunrise=False)[0])

def _tithi_boundary_jd(
    jd,
    place,
    direction=+1,
    step_days=0.2,
    max_days=2.0,
    iterations=24,
):
    """
    Find the nearest tithi boundary relative to `jd`.

    Parameters
    ----------
    jd : float
        Julian day
    place : object
        Location / place object used by tithi()
    direction : int
        +1 -> next boundary after jd
        -1 -> previous boundary before jd
    step_days : float
        Scan step in days
    max_days : float
        Maximum scan distance in the chosen direction
    iterations : int
        Number of bisection iterations

    Returns
    -------
    float
        JD of the boundary
    """
    if direction not in (+1, -1):
        raise ValueError("direction must be +1 (next) or -1 (previous)")

    eps = 1.0 / 86400.0
    sign = 1.0 if direction > 0 else -1.0

    # Start just away from jd to avoid landing exactly on boundary
    current = jd + sign * eps
    t_current = _tithi_number_at_jd(current, place)

    probe = current + sign * step_days
    limit = current + sign * max_days

    def within_limit(x):
        return x <= limit if sign > 0 else x >= limit

    while within_limit(probe):
        t_probe = _tithi_number_at_jd(probe, place)

        if t_probe != t_current:
            # Arrange bracket so:
            #   t(lo) = old tithi
            #   t(hi) = new tithi
            if sign > 0:
                lo, hi = current, probe
                t_lo = t_current
            else:
                lo, hi = probe, current
                t_lo = t_probe

            for _ in range(iterations):
                mid = (lo + hi) / 2.0
                t_mid = _tithi_number_at_jd(mid, place)

                if t_mid == t_lo:
                    lo = mid
                else:
                    hi = mid

            return hi

        current = probe
        t_current = t_probe
        probe += sign * step_days

    raise RuntimeError(
        f"Could not find {'next' if direction > 0 else 'previous'} "
        f"tithi boundary within max_days."
    )
def true_tithi_year(jd, place,true_lunar_year_method=None, round_to_digits=6):
    """
    True duration of 360 actual tithis near the given JD.
    Counts exactly 360 instantaneous tithi transitions.
    """
    if true_lunar_year_method is None: true_lunar_year_method = const.true_lunar_year_method_default
    if true_lunar_year_method == const.TRUE_LUNAR_YEAR_METHOD.TITHI_AT_DOB:
        return _true_tithi_year_same_phase(jd, place, round_to_digits)
    return _true_tithi_year_boundary(jd, place, round_to_digits)
def _true_tithi_year_same_phase(jd, place, round_to_digits=6):
    jd_utc = jd - place.timezone/24
    theta0 = lunar_longitude(jd_utc)-solar_longitude(jd_utc)
    #print(tithi(jd,place))
    mean_synodic_month = 29.530588853
    seed = jd + 12 * mean_synodic_month - 2.0  # safely before 12th recurrence

    end_jd = next_conjunction_of_planet_pair(
        seed,
        place,
        const.MOON_ID,
        const.SUN_ID,
        direction=1,
        separation_angle=theta0,
        increment_speed_factor=0.25,
        angle_tolerance=0.5,
        finer_angle_tolerance=0.001,
    )[0]
    #print(tithi(end_jd,place))
    return end_jd - jd # round(end_jd - jd, round_to_digits)
def _true_tithi_year_boundary(
    jd,
    place,
    round_to_digits=6,
    months=12,
    mean_synodic_month=29.530588853,
    increment_speed_factor=0.25,
    angle_tolerance=0.5,
    finer_angle_tolerance=0.001,
):
    """
    Fast computation of the true duration of 360 tithis near `jd`.

    This is a faster replacement for counting 360 successive tithi transitions.
    It works by:

      1) finding the previous tithi boundary before `jd`
      2) determining the exact boundary phase angle (multiple of 12 degrees)
      3) finding the next recurrence of that same Moon-Sun separation angle
         near 12 synodic months later

    Parameters
    ----------
    jd : float
        Starting Julian day
    place : Place
        Panchanga place object
    round_to_digits : int
        Final rounding digits
    months : int
        Number of synodic months; default 12 gives 360 tithis
    mean_synodic_month : float
        Mean synodic month in days
    increment_speed_factor : float
        Passed through to next_conjunction_of_planet_pair()
    angle_tolerance : float
        Passed through to next_conjunction_of_planet_pair()
    finer_angle_tolerance : float
        Passed through to next_conjunction_of_planet_pair()

    Returns
    -------
    float
        Duration in days of 360 true tithis

    Notes
    -----
    This assumes that next_conjunction_of_planet_pair(..., separation_angle=x)
    finds the next JD where the *directed* separation angle

        (longitude(p1) - longitude(p2)) % 360

    equals x (within tolerance).

    For tithi logic, that must be a full 0..360 degree phase angle,
    NOT the smallest/unsigned angular separation.
    """
    eps = 1.0 / 86400.0

    # 1) Find the previous tithi boundary before jd
    start_jd = _tithi_boundary_jd(jd, place, direction=-1)

    # 2) Determine which tithi starts immediately after that boundary
    #    If boundary is the start of tithi N, its phase angle is (N-1)*12 degrees.
    t_after = int(tithi(start_jd + eps, place, force_tithi_at_sunrise=False)[0])
    target_angle = ((t_after - 1) * 12.0) % 360.0

    # 3) Seed the phase-angle search safely between the 11th and 12th recurrence
    #    so that "next occurrence" lands on the 12th one, not earlier.
    #
    #    For months=12, this places the seed at 11.5 mean synodic months after start.
    #    That is usually a very safe location.
    seed_jd = start_jd + (months - 0.5) * mean_synodic_month

    # 4) Find the next recurrence of the SAME Moon-Sun phase angle
    end_jd = next_conjunction_of_planet_pair(
        seed_jd,
        place,
        const.MOON_ID,
        const.SUN_ID,
        direction=1,
        separation_angle=target_angle,
        increment_speed_factor=increment_speed_factor,
        angle_tolerance=angle_tolerance,
        finer_angle_tolerance=finer_angle_tolerance,
    )[0]

    return end_jd - start_jd # round(end_jd - start_jd, round_to_digits)
    
def true_lunar_year(jd, place, round_to_digits=6):
    """
    Alias/wrapper for true_tithi_year.

    True lunar year here means:
        360 actual tithi transitions near the given JD.
    """
    return true_tithi_year(jd, place, round_to_digits)
def solar_month_date(jd, place, sankranti_rule=None, ghatikas=None):
    """
        returns solar month and day
        @param jd: julian day
        @param place: Place Struct ('place',latitude,longitude,timezone)
        @param sankranti_rule one of:
            const.SANKRANTI_RULE.TAMIL_NADU_SUNSET_RULE = 1 (Default: Sankranti day if sun enters zodiac before sunset)
            const.SANKRANTI_RULE.BEFORE_GHATIKAS = 2 (Sankranti day before prescribed ghatikas)
                    ghatikas = 18 => Malabar calendar
                    ghatikas = 30 => Bengal Calendar
                    ghatikas = 45 => Kerala Calendar
            const.SANKRANTI_RULE.SUNRISE_TO_SUNRISE = 3 (Sankranti day if sun enters within sunrise to sunrise)
    """
    if sankranti_rule is None: sankranti_rule = const.SANKRANTI_RULE.TAMIL_NADU_SUNSET_RULE
    # Helper function to evaluate the civil start day for any given transit
    def get_civil_start_sunrise(transit_jd):
        _, _, sr_trans_jd = sunrise(transit_jd, place)
        _, _, ss_trans_jd = sunset(transit_jd, place)
        is_day_one = False
        
        if sankranti_rule == const.SANKRANTI_RULE.TAMIL_NADU_SUNSET_RULE:
            is_day_one = transit_jd < ss_trans_jd
        elif sankranti_rule == const.SANKRANTI_RULE.BEFORE_GHATIKAS and ghatikas is not None:
            is_day_one = transit_jd < (sr_trans_jd + ghatikas/60.0)
        elif sankranti_rule == const.SANKRANTI_RULE.SUNRISE_TO_SUNRISE:
            is_day_one = transit_jd < sr_trans_jd
        else:
            is_day_one = transit_jd < ss_trans_jd # error conditions is Tamil Nadu
        if is_day_one:
            return sr_trans_jd
        else:
            _, _, next_sr = sunrise(sr_trans_jd + 1.1, place)
            return next_sr

    # 1. Anchor the calculation to the Sunrise of the requested civil day
    _, _, current_sunrise_jd = sunrise(jd, place)

    # 2. Find the astronomical month at the exact moment of this sunrise
    jd_utc = current_sunrise_jd - (place.timezone / 24.0)
    lon = solar_longitude(jd_utc)
    astronomical_month_idx = int(lon / 30)

    # 3. Find the most recent transit (entry into current astronomical month)
    sankranti_jd, _ = next_planet_entry_date(const.SUN_ID, current_sunrise_jd, place, direction=-1)
    start_jd_current = get_civil_start_sunrise(sankranti_jd)

    # 4. Determine final Civil Month and Start Date
    if int(round(current_sunrise_jd)) < int(round(start_jd_current)):
        # EDGE CASE A: Astronomically in new month, but civilly the month hasn't started yet.
        # Belong to the previous month. Find the transit from ~30 days ago.
        sankranti_jd_prev, _ = next_planet_entry_date(const.SUN_ID, sankranti_jd - 1.0, place, direction=-1)
        final_start_jd = get_civil_start_sunrise(sankranti_jd_prev)
        final_month_idx = (astronomical_month_idx - 1) % 12
        
    else:
        # We are at least in the current month. 
        # EDGE CASE B: What if transit to the NEXT month happens later today?
        sankranti_jd_next, _ = next_planet_entry_date(const.SUN_ID, current_sunrise_jd, place, direction=1)
        start_jd_next = get_civil_start_sunrise(sankranti_jd_next)

        # If the next month's start day is evaluated to be today, today is Day 1 of the next month.
        if int(round(current_sunrise_jd)) >= int(round(start_jd_next)):
            final_start_jd = start_jd_next
            final_month_idx = (astronomical_month_idx + 1) % 12
        else:
            # Standard case: safely in the current month
            final_start_jd = start_jd_current
            final_month_idx = astronomical_month_idx

    # 5. Calculate continuous day number
    day_number = int(round(current_sunrise_jd)) - int(round(final_start_jd)) + 1

    return final_month_idx, day_number
def dhasa_year_duration(dhasa_duration_type=None,jd=None,place=None,round_to_digits=6,
                        savana_year_method=None,true_lunar_year_method=None): #V4.8.5
    jd_place_not_none = (jd is not None and place is not None)
    if dhasa_duration_type is None: dhasa_duration_type = const.dhasa_year_duration_default
    if savana_year_method is None: savana_year_method = const.SAVANA_YEAR_METHOD.PROSPECTIVE_0_to_360_JHORA
    if dhasa_duration_type == const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR: return const.sidereal_year
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR: return const.tropical_year
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.TRUE_SIDEREAL_YEAR and jd_place_not_none:
        return true_sidereal_year(jd, place, round_to_digits)
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.TRUE_TROPICAL_YEAR and jd_place_not_none:
        return true_tropical_year(jd, place, round_to_digits)
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.SAVANA_YEAR and jd_place_not_none:
        return savana_year(jd, place, round_to_digits,savana_year_method)
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.MEAN_LUNAR_YEAR and jd_place_not_none:
        return const.lunar_year#round(const.lunar_year,round_to_digits)
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR and jd_place_not_none:
        return true_tithi_year(jd, place, true_lunar_year_method, round_to_digits)
    elif dhasa_duration_type == const.DHASA_YEAR_DURATION.GREGORIAN_YEAR:
        return const.average_gregorian_year
    else: return const.sidereal_year

def get_planet_speed_sign(jd,place,planet): # V4.8.6 
    """
        Get Planet Speed Sign if retrograde "R" if Stationary "S" otherwise ""
    """
    return (
        const.ret_stat_symbols[_planet_speed_sign(jd, place, planet)] 
        if planet not in [const.SUN_ID,const.MOON_ID] else '' )

def _get_dhasa_start_jd_savana(jd_birth:float, place:Place, fraction_elapsed:float,
                               total_dasa_years:float) -> float:
    elapsed_days_savana = fraction_elapsed * total_dasa_years * const.savana_year
    jd_start_local = jd_birth - elapsed_days_savana
    return jd_start_local
    
def _get_dhasa_start_jd_lunar(jd_birth: float, place: Place, nakshatra_fraction: float, 
                                 total_dasa_years: float) -> float:
    """
    Dynamically and precisely calculates the 360 Tithi Year Vimshottari Dasa start date.
    It counts continuous Tithis and lunar months backward to find the exact second
    the target Moon-Sun elongation occurred in history, eliminating month-jumping errors.
    """
    # 1. Convert local Julian Date of birth to Universal Time (UTC)
    jd_utc_birth = jd_birth - (place.timezone / 24.0)
    
    # 2. Get the exact planetary positions at birth (True apparent coordinates)
    res_m, _ = swe.calc_ut(jd_utc_birth, swe.MOON, PLANET_FLAGS)
    res_s, _ = swe.calc_ut(jd_utc_birth, swe.SUN, PLANET_FLAGS)
    birth_moon = res_m[0]
    birth_sun = res_s[0]
    
    # 3. Calculate Natal Elongation (0.0 to 360.0 degrees)
    natal_elongation = (birth_moon - birth_sun) % 360.0
    
    # 4. Total Dasa Years elapsed from the Moon fraction
    dasa_elapsed_years = nakshatra_fraction * total_dasa_years  # e.g., 1.927673 years
    
    # 5. Convert Dasa Years to absolute continuous Tithis (360 Tithis per Dasa Year)
    total_tithis_elapsed = dasa_elapsed_years * 360.0          # e.g., 693.9622 Tithis
    
    # 6. Convert Tithis to absolute elapsed Lunar Months (1 Lunar Month = 30 Tithis)
    # This identifies exactly how many full phase cycles the Moon made relative to the Sun.
    total_lunar_months = total_tithis_elapsed / 30.0            # e.g., 23.13207 Months
    
    # Extract full cycles and the remaining fractional cycle arc in degrees
    full_lunar_cycles = int(total_lunar_months)                 # 23 full months
    fractional_month = total_lunar_months - full_lunar_cycles
    remaining_degrees = fractional_month * 360.0                # Remaining elongation degrees
    
    # 7. Identify the precise target elongation angle at the destination point
    target_elongation = (natal_elongation - remaining_degrees) % 360.0
    
    # 8. ANCHOR THE SEED TO THE EXACT MONTH IN HISTORY:
    # We use the true standard astronomical mean synodic month duration (29.530589 days) 
    # to jump back into the exact historical month window, matching the full cycles.
    mean_synodic_month = 29.530589
    approx_days_back = (full_lunar_cycles * mean_synodic_month) + (remaining_degrees / 12.1907)
    estimated_target_jd = jd_utc_birth - approx_days_back
    
    # 9. HIGH-PRECISION RECONCILIATION LOOP:
    # Restricting the search net to a tight +/- 1.0 day window prevents the binary 
    # solver from catching adjacent month cycles, forcing it to solve the correct cycle.
    low_jd = estimated_target_jd - 1.0
    high_jd = estimated_target_jd + 1.0
    
    jd_start_utc = estimated_target_jd
    for _ in range(50):
        mid_jd = (low_jd + high_jd) / 2.0
        
        m_pos, _ = swe.calc_ut(mid_jd, swe.MOON, PLANET_FLAGS)
        s_pos, _ = swe.calc_ut(mid_jd, swe.SUN, PLANET_FLAGS)
        
        current_elongation = (m_pos[0] - s_pos[0]) % 360.0
        
        # Calculate coordinate difference safely across the 0/360 boundary
        diff = (current_elongation - target_elongation + 180) % 360 - 180
        
        if abs(diff) < 1e-7:  # Precision threshold down to a fraction of a second
            jd_start_utc = mid_jd
            break
        elif diff > 0:
            high_jd = mid_jd
        else:
            low_jd = mid_jd
    else:
        jd_start_utc = (low_jd + high_jd) / 2.0
        
    # 10. Convert the final calculated UTC Julian Date back to Local Time
    jd_start_local = jd_start_utc + (place.timezone / 24.0)
    return jd_start_local

def _get_dhasa_start_jd(jd_birth:float, place:Place, fraction_elapsed:float,
                      total_dasa_years:float, dasha_sesham_method=None) -> float:
    """
    Dynamically calculates the True Sidereal/Tropical Dasa start date by tracking 
    the absolute solar arc revolutions backward through time.
    """
    if dasha_sesham_method is None: dasha_sesham_method = const.default_dasha_sesham_method
    if dasha_sesham_method == const.DASHA_SESHAM_METHOD.REVERSE:
        fraction_elapsed = 1.0 - fraction_elapsed
    elif dasha_sesham_method == const.DASHA_SESHAM_METHOD.NONE:
        fraction_elapsed = 0.0
    jd_utc_birth = jd_birth - (place.timezone / 24.0)
    
    # 3. Calculate exact Dasa years elapsed from the fixed Nakshatra fraction
    dasa_elapsed_years = fraction_elapsed * total_dasa_years  # 1.927673 years
    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR:
        period_elapsed = dasa_elapsed_years *const.sidereal_year
        start_jd = jd_birth - period_elapsed
        return start_jd
    elif const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR:
        period_elapsed = dasa_elapsed_years * const.tropical_year
        start_jd = jd_birth - period_elapsed
        return start_jd
    elif const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_LUNAR_YEAR:
        period_elapsed = dasa_elapsed_years * const.lunar_year
        start_jd = jd_birth - period_elapsed
        return start_jd
    elif const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.SAVANA_YEAR:
        return _get_dhasa_start_jd_savana(jd_birth, place, fraction_elapsed, total_dasa_years)
    elif const.dhasa_year_duration_default in [const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR,
                                               const.DHASA_YEAR_DURATION.MEAN_LUNAR_YEAR]:
        return _get_dhasa_start_jd_lunar(jd_birth, place, fraction_elapsed, total_dasa_years)
    # Extract whole years and the remaining fractional year
    whole_years = int(dasa_elapsed_years)                       # 1 full year
    fractional_year = dasa_elapsed_years - whole_years          # 0.927673 year
    
    tropical = const.dhasa_year_duration_default in [const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR, 
                                                     const.DHASA_YEAR_DURATION.TRUE_TROPICAL_YEAR]
    flag = swe.FLG_TROPICAL if tropical else PLANET_FLAGS
    year_length = const.average_gregorian_year # const.tropical_year if tropical else const.sidereal_year 
    # 4. Get the Sun's exact longitude at the moment of birth
    res, _ = swe.calc_ut(jd_utc_birth, swe.SUN, swe.FLG_SWIEPH | flag)
    birth_sun_long = res[0]
    
    # =========================================================================
    # STEP 5: CALCULATE FULL REVOLUTIONS DYNAMICALLY
    # Loop backward one full year at a time. We subtract 390.0 days (instead of 365.25)
    # to drop the seed safely behind the prior year's crossing point.
    # =========================================================================
    current_jd_anchor = jd_utc_birth
    for _ in range(whole_years):
        search_seed = current_jd_anchor - year_length - 1 # Step back 1 extra day to ensure we are behind the crossing
        current_jd_anchor = swe.solcross_ut(birth_sun_long, search_seed, flag)
        
    # =========================================================================
    # STEP 6: CALCULATE THE FRACTIONAL YEAR ARC DYNAMICALLY
    # Now we find the target coordinate for the final fractional piece.
    # =========================================================================
    target_fractional_arc = fractional_year * 360.0             # 333.96228 degrees
    
    # Subtract the fractional arc from the year-anchor's longitude
    target_longitude = (birth_sun_long - target_fractional_arc) % 360.0
    
    # Estimate the final day step back for the fraction and pad it by 15 days
    # to push the search seed securely into the past before the crossing window.
    approx_days_for_fraction = fractional_year * year_length
    final_search_seed = current_jd_anchor - (approx_days_for_fraction + 15.0)
    
    # Find the exact moment the True Sun crossed this final coordinate
    jd_start_utc = swe.solcross_ut(target_longitude, final_search_seed, flag)
    
    # 7. Convert the final calculated UTC Julian Date back to Local Time
    jd_start_local = jd_start_utc + (place.timezone / 24.0)
    
    return jd_start_local

def _get_dhasa_end_jd_savana(
    start_jd: float,
    place: Place,
    total_dasa_years: float,
) -> float:
    """
    Calculates Dasa end JD using Savana year duration.
    One Savana year = const.savana_year days.
    """
    elapsed_days_savana = total_dasa_years * const.savana_year
    return start_jd + elapsed_days_savana
def _get_dhasa_end_jd_lunar(
    start_jd: float,
    place: Place,
    total_dasa_years: float,
) -> float:
    """
    Calculates Dasa end JD using true lunar/tithi year logic.

    A lunar dasha year is treated as 360 tithis.
    Therefore total_dasa_years corresponds to:
        total_dasa_years * 360 tithis
    or:
        total_dasa_years * 12 lunar months.
    """
    jd_utc_start = start_jd - (place.timezone / 24.0)

    res_m, _ = swe.calc_ut(jd_utc_start, swe.MOON, PLANET_FLAGS)
    res_s, _ = swe.calc_ut(jd_utc_start, swe.SUN, PLANET_FLAGS)

    start_moon = res_m[0]
    start_sun = res_s[0]

    start_elongation = (start_moon - start_sun) % 360.0

    total_tithis = total_dasa_years * 360.0
    total_lunar_months = total_tithis / 30.0

    full_lunar_cycles = int(total_lunar_months)
    fractional_month = total_lunar_months - full_lunar_cycles
    remaining_degrees = fractional_month * 360.0

    target_elongation = (start_elongation + remaining_degrees) % 360.0

    mean_synodic_month = 29.530589
    approx_days_forward = (
        full_lunar_cycles * mean_synodic_month
        + remaining_degrees / 12.1907
    )

    estimated_target_jd = jd_utc_start + approx_days_forward

    low_jd = estimated_target_jd - 1.0
    high_jd = estimated_target_jd + 1.0

    jd_end_utc = estimated_target_jd

    for _ in range(50):
        mid_jd = (low_jd + high_jd) / 2.0

        m_pos, _ = swe.calc_ut(mid_jd, swe.MOON, PLANET_FLAGS)
        s_pos, _ = swe.calc_ut(mid_jd, swe.SUN, PLANET_FLAGS)

        current_elongation = (m_pos[0] - s_pos[0]) % 360.0

        diff = (current_elongation - target_elongation + 180.0) % 360.0 - 180.0

        if abs(diff) < 1e-7:
            jd_end_utc = mid_jd
            break

        if diff > 0.0:
            high_jd = mid_jd
        else:
            low_jd = mid_jd
    else:
        jd_end_utc = (low_jd + high_jd) / 2.0

    jd_end_local = jd_end_utc + (place.timezone / 24.0)

    return jd_end_local

def _get_dhasa_end_jd(
    start_jd: float,
    place: Place,
    total_dasa_years: float,
) -> float:
    """
    Calculates Dasa end JD from the Dasa start JD and duration.
    Optimized to handle any duration (Mahadasha to Deha) in a single ephemeris call.
    """
    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR:
        return start_jd + total_dasa_years * const.sidereal_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR:
        return start_jd + total_dasa_years * const.tropical_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_LUNAR_YEAR:
        return start_jd + total_dasa_years * const.lunar_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.SAVANA_YEAR:
        return _get_dhasa_end_jd_savana(
            start_jd=start_jd,
            place=place,
            total_dasa_years=total_dasa_years,
        )

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR:
        return _get_dhasa_end_jd_lunar(
            start_jd=start_jd,
            place=place,
            total_dasa_years=total_dasa_years,
        )

    jd_utc_start = start_jd - (place.timezone / 24.0)

    tropical = const.dhasa_year_duration_default in [
        const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR,
        const.DHASA_YEAR_DURATION.TRUE_TROPICAL_YEAR,
    ]

    flag = swe.FLG_TROPICAL if tropical else PLANET_FLAGS
    year_length = const.average_gregorian_year

    res, _ = swe.calc_ut(jd_utc_start, swe.SUN, swe.FLG_SWIEPH | flag)
    start_sun_long = res[0]

    if total_dasa_years == 0.0:
        jd_end_utc = jd_utc_start
    else:
        # Net fractional arc remaining after accounting for whole years
        fractional_year = total_dasa_years % 1.0
        target_fractional_arc = fractional_year * 360.0
        target_longitude = (start_sun_long + target_fractional_arc) % 360.0

        approx_total_days = total_dasa_years * year_length

        # Place the search seed safely near the end (handles Dehas and Mahadashas alike)
        if approx_total_days < 1.0:
            # For micro-periods (Deha, Prana), place seed just fractions of a day before the end
            final_search_seed = jd_utc_start + approx_total_days - 0.001
        else:
            # For long periods, place seed 30 days before the expected end 
            # (or closer if the total period itself is shorter than 120 days)
            margin = min(30.0, approx_total_days / 4.0)
            final_search_seed = jd_utc_start + approx_total_days - margin

        # Single root-finding call scanning forward into the final stretch
        jd_end_utc = swe.solcross_ut(
            target_longitude,
            final_search_seed,
            flag,
        )

    jd_end_local = jd_end_utc + (place.timezone / 24.0)

    return jd_end_local

def _get_dhasa_end_jd_old(
    start_jd: float,
    place: Place,
    total_dasa_years: float,
) -> float:
    """
    Calculates Dasa end JD from the Dasa start JD and duration.

    This mirrors _get_dhasa_start_jd() and respects
    const.dhasa_year_duration_default.
    """
    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR:
        return start_jd + total_dasa_years * const.sidereal_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR:
        return start_jd + total_dasa_years * const.tropical_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.MEAN_LUNAR_YEAR:
        return start_jd + total_dasa_years * const.lunar_year

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.SAVANA_YEAR:
        return _get_dhasa_end_jd_savana(
            start_jd=start_jd,
            place=place,
            total_dasa_years=total_dasa_years,
        )

    if const.dhasa_year_duration_default == const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR:
        return _get_dhasa_end_jd_lunar(
            start_jd=start_jd,
            place=place,
            total_dasa_years=total_dasa_years,
        )

    jd_utc_start = start_jd - (place.timezone / 24.0)

    whole_years = int(total_dasa_years)
    fractional_year = total_dasa_years - whole_years

    tropical = const.dhasa_year_duration_default in [
        const.DHASA_YEAR_DURATION.MEAN_TROPICAL_YEAR,
        const.DHASA_YEAR_DURATION.TRUE_TROPICAL_YEAR,
    ]

    flag = swe.FLG_TROPICAL if tropical else PLANET_FLAGS
    year_length = const.average_gregorian_year

    res, _ = swe.calc_ut(jd_utc_start, swe.SUN, swe.FLG_SWIEPH | flag)
    start_sun_long = res[0]

    current_jd_anchor = jd_utc_start

    for _ in range(whole_years):
        search_seed = current_jd_anchor + year_length - 1.0
        current_jd_anchor = swe.solcross_ut(
            start_sun_long,
            search_seed,
            flag,
        )

    if fractional_year == 0.0:
        jd_end_utc = current_jd_anchor
    else:
        target_fractional_arc = fractional_year * 360.0
        target_longitude = (start_sun_long + target_fractional_arc) % 360.0

        approx_days_for_fraction = fractional_year * year_length
        final_search_seed = current_jd_anchor + approx_days_for_fraction - 15.0

        jd_end_utc = swe.solcross_ut(
            target_longitude,
            final_search_seed,
            flag,
        )

    jd_end_local = jd_end_utc + (place.timezone / 24.0)

    return jd_end_local

if __name__ == "__main__":
    import time
    utils.set_language('en')
    run_ayanamsa_mode = "TRUE_PUSHYA" #"LAHIRI" #
    if run_ayanamsa_mode.upper() == "TRUE_PUSHYA":
        const._use_true_nodes_for_rahu_ketu = True
        set_planet_list(set_rahu_ketu_as_true_nodes=True, include_western_planets=False)
    else:
        const._use_true_nodes_for_rahu_ketu = False
        set_planet_list(set_rahu_ketu_as_true_nodes=False, include_western_planets=False)
    set_ayanamsa_mode(run_ayanamsa_mode)
    dob = Date(1996,12,7); tob = (10,34,0); place = Place('Chennai,India',13.0878,80.2785,5.5)
    jd = utils.julian_day_number(dob, tob); jd_utc = jd - place.timezone/24.0
    increment_speed_factor = 0.001
    planet = const.JUPITER_ID; dirn = 1
    jhora_pushya = {const.MARS_ID:["(1995,3,24) 22:42:16 20Cn30'24.96\"","(1997,2,6) 5:57:44 13Vi14'27.02\""],
            const.MERCURY_ID:["(1996,9,26) 22:31:34 26Le19'16.13\"","(1996,12,24) 01:08:57 26Sg32'44.46\""],
            const.JUPITER_ID:["(1996,9,3) 19:25:53 15Sg08'36.44\"","(1997,6,10) 05:14:00 29Cp15'18.31\""],
            const.VENUS_ID:["(1996,7,2) 12:19:20 19Ta06'5.1\"","(1997,12,27) 02:47:31 11Cp14'43.78\""],
            const.SATURN_ID:["(1996, 12, 3) 16:41:59 07Pi55'47.45\"","(1997,8,1) 21:01:44 27Pi40'22.41\""],
            const.RAHU_ID:["(1996, 10, 11) 22:05:16 15Vi22'26.32\"","(1997,2,24) 18:16:58 06Vi03'03.08\""]}
    jhora_lahiri = {const.MARS_ID:["(1995,3,24) 22:49:17 19Cn22'18.51\"","(1997,2,6) 5:57:44 13Vi14'27.02\""],
            const.MERCURY_ID:["(1996,9,26) 22:38:06 25Le11'9.78\"","(1996,12,24) 01:08:57 26Sg32'44.46\""],
            const.JUPITER_ID:["(1996,9,3) 20:04:33 14Sg00'30.08\"","(1997,6,10) 05:14:00 29Cp15'18.31\""],
            const.VENUS_ID:["(1996,7,2) 12:22:17 17Ta57'58.71\"","(1997,12,27) 02:47:31 11Cp14'43.78\""],
            const.SATURN_ID:["(1996, 12, 3) 17:57:45 06Pi47'41.11\"","(1997,8,1) 21:01:44 27Pi40'22.41\""],
            const.RAHU_ID:["(1996, 10, 11) 22:05:16 14Vi14'30.93\"","(1997,2,24) 18:16:58 06Vi03'03.08\""]}
    jhora_results = jhora_pushya if const._DEFAULT_AYANAMSA_MODE=="TRUE_PUSHYA" else jhora_lahiri
    threshold = 0.02 #const.one_arc_second #
    chapter = "Stationary Duration Test: "
    for dirn in [-1,1]:
        di = 0 if dirn == -1 else 1
        di_str = "Before:" if dirn == -1 else "After:"
        for planet,jhora_result in jhora_results.items():
            #if planet == const.RAHU_ID: continue # Skip calculating for Rahu
            pstr = utils.PLANET_NAMES[planet]
            start_time = time.time()
            sjd1,sjd2 = next_planet_stationary_duration_old(planet, jd, place,direction=dirn,
                                                        threshold=const.one_arc_second)
            y1,m1,d1,fh1 = sjd1; jd1 = utils.julian_day_number(Date(y1,m1,d1),(fh1,0,0))
            y2,m2,d2,fh2 = sjd2; jd2 = utils.julian_day_number(Date(y2,m2,d2),(fh2,0,0))
            print('old',utils.PLANET_NAMES[planet],'from',(y1,m1,d1),utils.to_dms(fh1),
                'to',(y2,m2,d2),utils.to_dms(fh2), time.time()-start_time)
            jdm = 0.5*(jd1+jd2); y,m,d,fh = utils.jd_to_gregorian(jdm)
            jdm_utc = jdm-place.timezone/24.0
            retStr = const.ret_stat_symbols[_planet_speed_sign(jdm, place, planet)]
            p_swe = ephemeris_planet_index(planet)
            p_long = sidereal_longitude(jdm_utc,p_swe)
            pstr += retStr
            act = f"({y},{m},{d} {utils.to_dms(fh)} {utils.deg_to_sign_str(p_long)}"
            print(di_str+pstr,act,"JHora Results:",jhora_result[di])
            
            pstr = utils.PLANET_NAMES[planet]
            start_time = time.time()
            sjd1,sjd2 = next_planet_stationary_duration(planet, jd, place,direction=dirn,
                                                        threshold=threshold)
            y1,m1,d1,fh1 = sjd1; jd1 = utils.julian_day_number(Date(y1,m1,d1),(fh1,0,0))
            y2,m2,d2,fh2 = sjd2; jd2 = utils.julian_day_number(Date(y2,m2,d2),(fh2,0,0))
            from jhora.tests.test_helper import compare_lists_within_tolerance
            print('new',utils.PLANET_NAMES[planet],'from',(y1,m1,d1),utils.to_dms(fh1),
                'to',(y2,m2,d2),utils.to_dms(fh2), time.time()-start_time)
            jdm = 0.5*(jd1+jd2); y,m,d,fh = utils.jd_to_gregorian(jdm)
            jdm_utc = jdm-place.timezone/24.0
            retStr = const.ret_stat_symbols[_planet_speed_sign(jdm, place, planet)]
            p_swe = ephemeris_planet_index(planet)
            p_long = sidereal_longitude(jdm_utc,p_swe)
            pstr += retStr
            act = f"({y},{m},{d} {utils.to_dms(fh)} {utils.deg_to_sign_str(p_long)}"
            print(di_str+pstr,act,"JHora Results:",jhora_result[di],"\n")
