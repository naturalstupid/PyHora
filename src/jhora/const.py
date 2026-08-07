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
        V4.8.9
            - Ashtakavarga shodhaya pinda constants updated to support PVR and alternate sources
            - special lagna continuity
            - chart method enum classes added
"""
""" Module describing PyJHora constants"""
import os
import swisseph as swe
import numpy as np
from enum import IntEnum, unique, Enum
from jhora._package_info import version as _APP_VERSION

" setup paths "
_sep = os.path.sep
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(ROOT_DIR+_sep+"data"+_sep)
FACTORY_SETTINGS_FILE = os.path.join(_DATA_DIR, "factory_settings.json")
USER_SETTINGS_FILE = os.path.join(_DATA_DIR, "user_settings.json")
_IMAGES_PATH = os.path.dirname(ROOT_DIR+_sep+"images"+_sep)
_IMAGE_ICON_PATH=os.path.join(_IMAGES_PATH+_sep+"lord_ganesha2.jpg")
_INPUT_DATA_FILE = _DATA_DIR +'program_inputs.txt' #os.path.join(ROOT_DIR,'data'+_sep+'program_inputs.txt')
_FESTIVAL_FILE = _DATA_DIR +_sep+'hindu_festivals_multilingual_unicode_bom.csv'
class PLACE_DATABASE_ENGINE:
    NONE = 0
    CSV_5K = 1          # CSV countries >5000 population
    PICKLE_5K = 2       # PICKLE countries >5000 population
    SQLITE_5K = 3       # SQLITE countries >5000 population
    CSV_5K_IN = 4       # CSV countries > 5000 population PLUS All Indian Cities Population >= 0
    PICKLE_5K_IN = 5    # Pickle countries > 5000 population PLUS All Indian Cities Population >= 0
    SQLITE_5K_IN = 6    # SQLite countries > 5000 population PLUS All Indian Cities Population >= 0
    CSV_500 = 7         # CSV countries >500 population
    PICKLE_500 = 8      # Pickle countries >500 population
    SQLITE_500 = 9      # SQLite countries >500 population
    CSV_500_IN = 10     # CSV countries > 500 population PLUS All Indian Cities Population >= 0
    PICKLE_500_IN = 11  # PICKLE countries > 500 population PLUS All Indian Cities Population >= 0
    SQLITE_500_IN = 12  # SQLITE countries > 500 population PLUS All Indian Cities Population >= 0
    CSV_1K = 13         # CSV countries >1000 population
    PICKLE_1K = 14      # Pickle countries >1000 population
    SQLITE_1K = 15      # SQLite countries >1000 population
    CSV_1K_IN = 16     # CSV countries > 1000 population PLUS All Indian Cities Population >= 0
    PICKLE_1K_IN = 17  # PICKLE countries > 1000 population PLUS All Indian Cities Population >= 0
    SQLITE_1K_IN = 18  # SQLITE countries > 1000 population PLUS All Indian Cities Population >= 0
    CSV_10K = 19         # CSV countries >10000 population
    PICKLE_10K = 20      # Pickle countries >10000 population
    SQLITE_10K = 21      # SQLite countries >10000 population
    CSV_10K_IN = 22     # CSV countries > 10000 population PLUS All Indian Cities Population >= 0
    PICKLE_10K_IN = 23  # PICKLE countries > 10000 population PLUS All Indian Cities Population >= 0
    SQLITE_10K_IN = 24  # SQLITE countries > 10000 population PLUS All Indian Cities Population >= 0
_PLACE_DATABASE_FILES = {
    PLACE_DATABASE_ENGINE.NONE: None,
    PLACE_DATABASE_ENGINE.CSV_5K: "geonames_places_5k.csv",
    PLACE_DATABASE_ENGINE.PICKLE_5K: "geonames_places_5k.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_5K: "geonames_places_5k.db",
    PLACE_DATABASE_ENGINE.CSV_5K_IN: "geonames_places_5k_IN.csv",
    PLACE_DATABASE_ENGINE.PICKLE_5K_IN: "geonames_places_5k_IN.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_5K_IN: "geonames_places_5k_IN.db",
    PLACE_DATABASE_ENGINE.CSV_500: "geonames_places_500.csv",
    PLACE_DATABASE_ENGINE.PICKLE_500: "geonames_places_500.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_500: "geonames_places_500.db",
    PLACE_DATABASE_ENGINE.CSV_500_IN: "geonames_places_500_IN.csv",
    PLACE_DATABASE_ENGINE.PICKLE_500_IN: "geonames_places_500_IN.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_500_IN: "geonames_places_500_IN.db",
    PLACE_DATABASE_ENGINE.CSV_1K: "geonames_places_1K.csv",
    PLACE_DATABASE_ENGINE.PICKLE_1K: "geonames_places_1K.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_1K: "geonames_places_1K.db",
    PLACE_DATABASE_ENGINE.CSV_1K_IN: "geonames_places_1K_IN.csv",
    PLACE_DATABASE_ENGINE.PICKLE_1K_IN: "geonames_places_1K_IN.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_1K_IN: "geonames_places_1K_IN.db",
    PLACE_DATABASE_ENGINE.CSV_10K: "geonames_places_10K.csv",
    PLACE_DATABASE_ENGINE.PICKLE_10K: "geonames_places_10K.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_10K: "geonames_places_10K.db",
    PLACE_DATABASE_ENGINE.CSV_10K_IN: "geonames_places_10K_IN.csv",
    PLACE_DATABASE_ENGINE.PICKLE_10K_IN: "geonames_places_10K_IN.pkl",
    PLACE_DATABASE_ENGINE.SQLITE_10K_IN: "geonames_places_10K_IN.db",
}
database_engine = PLACE_DATABASE_ENGINE.SQLITE_5K
_place_database_file = None
def set_place_database_engine(engine):
    global database_engine, _place_database_file

    if engine not in _PLACE_DATABASE_FILES:
        raise ValueError(f"Unsupported database engine: {engine}")

    database_engine = engine

    filename = _PLACE_DATABASE_FILES[engine]
    _place_database_file = None if filename is None else os.path.join(ROOT_DIR, "data", filename)
set_place_database_engine(database_engine)

_open_elevation_api_url = lambda lat,long:f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}'
_EPHIMERIDE_DATA_PATH = os.path.join(ROOT_DIR,'data'+_sep+'ephe'+_sep)
_LANGUAGE_PATH = os.path.join(ROOT_DIR,'lang'+_sep)
_DEFAULT_LANGUAGE = 'en'
_DEFAULT_LANGUAGE_LIST_STR = 'list_values_'
_DEFAULT_LANGUAGE_MSG_STR = 'msg_strings_'
_DEFAULT_YOGA_JSON_FILE_PREFIX = "yoga_msgs_" 
_DEFAULT_RAJA_YOGA_JSON_FILE_PREFIX = "raja_yoga_msgs_" 
_DEFAULT_DOSHA_JSON_FILE_PREFIX = "dosha_msgs_" 
_DEFAULT_PREDICTION_JSON_FILE_PREFIX = "prediction_msgs_" 
""" To use Ur/Ne/Pl TODO: You have to exclude them all vedic astrology functions e.g. dhasa. strength"""
_INCLUDE_URANUS_TO_PLUTO = False#True # Only for Western Charts
_degree_symbol = "°" 
_minute_symbol = u'\u2019'
_second_symbol = '"'
_retrogade_symbol = '℞'
_stationary_symbol = 'Ꞩ' #"\ua7a8"
ret_stat_symbols = {-1:_retrogade_symbol,0:_stationary_symbol,1:''} # V4.8.6
_ascendant_symbol = 'L'
" Planet names mapped to swiss ephemerides "
_use_true_nodes_for_rahu_ketu = True
_KETU = -10 #99 if _use_true_nodes_for_rahu_ketu else -swe.MEAN_NODE
KETU_ID = 8
_RAHU = swe.TRUE_NODE if _use_true_nodes_for_rahu_ketu else swe.MEAN_NODE
RAHU_ID = 7
_SUN = swe.SUN; SURYA = _SUN ; SUN_ID = 0
_MOON = swe.MOON; CHANDRA = _MOON; MOON_ID = 1; CHANDRA_ID = 1
_MARS = swe.MARS; KUJA = _MARS; KUJA_ID = 2; MARS_ID = 2
_MERCURY = swe.MERCURY; BUDHA = _MERCURY; MERCURY_ID = 3; BUDHA_ID = 3 
_JUPITER = swe.JUPITER; GURU = _JUPITER; JUPITER_ID = 4; GURU_ID = 4
_VENUS = swe.VENUS; SUKRA = _VENUS; VENUS_ID = 5; SUKRA_ID = 5
_SATURN = swe.SATURN; SANI = _SATURN; SANI_ID = 6; SATURN_ID = 6
_URANUS = swe.URANUS; URANUS_ID = 9
_NEPTUNE = swe.NEPTUNE; NEPTUNE_ID = 10
_PLUTO = swe.PLUTO; PLUTO_ID = 11

def set_node_mode(use_true: bool) -> None:
    """
    Switch Rahu/Ketu between True and Mean nodes at runtime.
    Call this ONCE at process start (e.g., tests or app bootstrap).
    """
    global _use_true_nodes_for_rahu_ketu, _RAHU, _KETU
    _use_true_nodes_for_rahu_ketu = bool(use_true)
    _RAHU = swe.TRUE_NODE if _use_true_nodes_for_rahu_ketu else swe.MEAN_NODE
    """ _KETU is always kept as -10 because no other number is allowed in swiss Ephemris """
    _KETU = -10 if _use_true_nodes_for_rahu_ketu else -swe.MEAN_NODE

set_node_mode(_use_true_nodes_for_rahu_ketu)

SUN_TO_SATURN = [*range(SUN_ID,SATURN_ID+1)]
SUN_TO_KETU = [*range(SUN_ID,KETU_ID+1)]
SUN_TO_PLUTO = [*range(SUN_ID,PLUTO_ID+1)]
HOUSE_1 = 0; HOUSE_2 = 1; HOUSE_3 = 2; HOUSE_4 = 3; HOUSE_5 = 4; HOUSE_6 = 5
HOUSE_7 = 6; HOUSE_8 = 7; HOUSE_9 = 8; HOUSE_10 = 9; HOUSE_11 = 10; HOUSE_12 = 11
ARIES = 0; TAURUS = 1; GEMINI = 2; CANCER = 3; LEO = 4; VIRGO = 5; LIBRA = 6
SCORPIO = 7; SAGITTARIUS = 8; CAPRICORN = 9; AQUARIUS = 10; PISCES = 11
MESHAM = ARIES; RISHABAM = TAURUS; MITHUNAM = GEMINI; KATAKAM = CANCER; SIMMAM = LEO; KANNI = VIRGO; THULAM = LIBRA
VIRUCHIGAM=SCORPIO; DHANUS=SAGITTARIUS; MAKARAM=CAPRICORN;KUMBAM=AQUARIUS;MEENAM=PISCES
_pp_count_upto_saturn = 8; _pp_count_upto_ketu = 10; _pp_count_upto_rahu = 9; _pp_count_upto_pluto = 13
_planets_upto_ketu = 9; _planets_upto_saturn = 7; _planets_upto_rahu = 8

""" Surya Siddhantha Constants """
planet_mean_revolutions_at_kali = {_SUN: 4320000,_MOON:57753336,_MARS: 2296832,_MERCURY: 17937060,
                                   _JUPITER:364220,_VENUS:7022376,_SATURN:146568,_RAHU:232238,_KETU:232238,
                                   _URANUS:51417, _NEPTUNE:26219, _PLUTO:17390}
mean_revolutions_sun_kali = 4320000
mean_revolutions_moon_kali = 57753336
mean_revolutions_rahu_kali = 232238
moon_mandocca_revolutions = 488203
sun_mandocca_revolutions = 0.387 # 387 revolutions in a Kalpa
mandakendrajya_indian_sine_radius = 3438/60.0
planet_eccentricity = {_SUN:0.01675104,_MOON:0.0549,_MARS:0.093,_MERCURY:0.206,_JUPITER:0.048,_VENUS:0.007,_SATURN:0.056,_URANUS:0.047,_NEPTUNE:0.009,_PLUTO:0.248}
#planet_eccentricity_coefficients = {p:((2.0*e-0.25*pow(e,3)),(1.25*pow(e,2)-11.0/24.0*pow(e,4))) for p,e in planet_eccentricity.items()}
planet_eccentricity_coefficients={_SUN: (0.03350090492567891, 0.0003507105895375814), 
                                  _MOON: (0.10975863271274999, 0.003763348882538287), 
                                  _MARS: (0.18579891075, 0.010776964282875001), 
                                  _MERCURY: (0.409814546, 0.05221962687266666), 
                                  _JUPITER: (0.095972352, 0.0028775669760000002), 
                                  _VENUS: (0.01399991425, 6.124889954166668e-05), 
                                  _SATURN: (0.111956096, 0.003915492522666667), 
                                  _URANUS: (0.09397404425, 0.0027590134795416666), 
                                  _NEPTUNE: (0.017999817749999997, 0.00010124699287499999), 
                                  _PLUTO: (0.492186752, 0.07514624324266665)}
""" mandaphala = E1 * sin(M) + E2 * sin (2M) - where M is manda anomaly  E1,E2 are above coefficients """

planet_mandaphala_periphery = {_SUN:14.0,_MOON:32.0,_MARS:(72.0,75.0),_MERCURY:(28.0,30),_JUPITER:(32.0,33.0),_VENUS:(11.0,12.0),_SATURN:(48.0,49.0)}
planet_mandaphala_periphery_modern = {_SUN:(11.78,12.29),_MOON:(36.98,42.43),_MARS:(60.27,76.20),_MERCURY:(117.72,198.19),_JUPITER:(32.77,36.97),_VENUS:(4.8,4.88),_SATURN:(36.28,41.52)}
planet_sighra_peripheries = {_MARS:(232.0,235.0),_MERCURY:(132.0,133.0),_JUPITER:(72.0,70.0),_VENUS:(260.0,262.0),_SATURN:(40.0,39.0)}
civil_days_in_mahayuga = 1577917828
daily_mean_motions_1 = [0.0+59.0/60+8/3600.0+10.0/2160600+9.7/12960000, 
                      13.0+10.0/60+34/3600.0+52.0/2160600+2./12960000,
                      0.0+31.0/60+26/3600.0+28.0/2160600+10./12960000,
                      4.0+5.0/60+32/3600.0+20.0/2160600+42./12960000,
                      0.0+4.0/60+59/3600.0+8.0/2160600+48./12960000,
                      1.0+36.0/60+7/3600.0+43.0/2160600+37./12960000,
                      0.0+2.0/60+0.0/3600.0+22.0/2160600+53./12960000,
                      -0.0-3.0/60-10/3600.0-44.0/2160600-43./12960000, # << Rahu
                      -0.0-3.0/60-10/3600.0-44.0/2160600-43./12960000, # << Ketu
                     ]
daily_mean_motions = {_SUN:0.9855609323563241, _MOON:13.176135332820786, _MARS:0.5240193,
                      _MERCURY: 4.0923181,_JUPITER: 0.0830963,_VENUS: 1.6021464,
                      _SATURN: 0.0334393,_RAHU: -0.05280146039251785, _KETU: -0.05280146039251785}
planet_mean_longitudes = {_SUN:0.0,_MOON:0.0, _MARS:0.0,_MERCURY:0.0,_JUPITER:0.0,_VENUS:0.0,_SATURN:0.0,_RAHU:0.0,_KETU:0.0}
moon_apogee_mean_motion = 6.684/60 # minutes
ujjain_lat_long = [23.1765, 75.7885]
planet_mean_positions_at_kali = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,180.0] # Sun to Rahu
manodcca_positions_at_kali = {_SUN:77.13,_MOON:90.0,_MARS:129.96,_MERCURY:220.32,_JUPITER:171.0,_VENUS:79.65,_SATURN:236.61,
                              _RAHU:180.0,_KETU:180.0}
madocca_revolutions = {_SUN:0.387,_MOON:488203,_MARS:204,_MERCURY:0.368,_JUPITER:0.900,_VENUS:0.535,_SATURN:0.039}
mandocca_sun_at_kali = 77.13 #77.0+7.0/60+48/3600.0
mandocca_moon_at_kali = 90.0

_planet_symbols=['ℒ','☉','☾','♂','☿','♃','♀','♄','☊','☋']
_zodiac_symbols = ['\u2648', '\u2649', '\u264A', '\u264B', '\u264C', '\u264D', '\u264E', '\u264F', '\u2650', '\u2651', '\u2652', '\u2653']

available_languages = {"English":'en','Tamil':'ta','Telugu':'te','Hindi':"hi",'Kannada':'ka','Malayalam':'ml'}
reverse_languages = {v: k for k, v in available_languages.items()}
" declare constants "
"""
# Planet Rulers of the 8 parts of the DAY and NIGHT
# Column = Weekday (0=Sun,1=Mon..7=Sat)
# Row= part of the day (0-7) =< (1st-8th) part of the day
# Value of the cell is the planet 0=>Sun, 1=>Moon, .. 6=>Saturn) 
# -1 means no ruler at that part of the day
"""
day_rulers = [[0,1,2,3,4,5,6,-1],[1,2,3,4,5,6,-1,0],[2,3,4,5,6,-1,0,1],[3,4,5,6,-1,0,1,2],[4,5,6,-1,0,1,2,3],[5,6,-1,0,1,2,3,4],[6,-1,0,1,2,3,4,5]]
night_rulers = [[4,5,6,-1,0,1,2,3],[5,6,-1,0,1,2,3,4],[6,-1,0,1,2,3,4,5],[0,1,2,3,4,5,6,-1],[1,2,3,4,5,6,-1,0],[2,3,4,5,6,-1,0,1],[3,4,5,6,-1,0,1,2]]
division_chart_factors = [1,2,3,4,5,6,7,8,9,10,11,12,16,20,24,27,30,40,45,60,81,108,144,150]
dhasavarga_amsa_vimsopaka = {1:3,2:1.5,3:1.5,7:1.5,9:1.5,10:1.5,12:1.5,16:1.5,30:1.5,60:5}
shadvarga_amsa_vimsopaka = {1:6,2:2,3:4,9:5,12:2,30:1}
sapthavarga_amsa_vimsopaka = {1:5,2:2,3:3,7:1,9:2.5,12:4.5,30:2}
shodhasa_varga_amsa_vimsopaka = {1:3.5,2:1,3:1,4:0.5,7:0.5,9:3,10:0.5,12:0.5,16:2,20:0.5,24:0.5,27:0.5,30:1,40:0.5,45:0.5,60:4}
vimsamsa_varga_amsa_factors = division_chart_factors
""" In the order: Own, Adhimitra,Mithra,Neutral/Samam,Sathru,Enemy,Great Enemy/Adhisathru """
vimsopaka_planet_position_values = [20,18,15,10,7,5] 
dhasavarga_amsa_vaiseshikamsa = {1:1,2:1,3:1,7:1,9:1,10:1,12:1,16:1,30:1,60:1}
shadvarga_amsa_vaiseshikamsa = {1:1,2:1,3:1,9:1,12:1,30:1}
sapthavarga_amsa_vaiseshikamsa = {1:1,2:1,3:1,7:1,9:1,12:1,30:1}
shodhasa_varga_amsa_vaiseshikamsa = {1:1,2:1,3:1,4:1,7:1,9:1,10:1,12:1,16:1,20:1,24:1,27:1,30:1,40:1,45:1,60:1}
""" In the order: Own, Adhimitra,Mithra,Neutral/Samam,Sathru,Enemy,Great Enemy/Adhisathru """
vaiseshikamsa_planet_position_values = [20,18,15,10,7,5] 

### String Constants for panchanga.
"""
    set this to =swe.PLUTO  for Vimoshotari functions. BUT KETHU will be SHOWN AS PLUTO DHASA/BHUKTI
    set this to - -10 for chart creation (otherwise chart will show Pluto for Kethu)
    following assignments due to changes in swiss ephe 2.8
    !!! IMPORTANT NOTE !!!
        swiss ephemeris constant values of planets such swe.MARS are different what is used in PyHor
        If PyJHora does not use const. values explicitly it assumes the planet values as follows:
                0 = Sun, 1= Moon, 2=Mars, 6=Saturn 7=Rahu and 8=Ketu
    !!!!!!!!!!!!!!!!!!!!!!!!  
"""
_TROPICAL_MODE = False
_EPHIMERIDE_DATA_PATH = ROOT_DIR+'/data/ephe/'
_LANGUAGE_PATH = ROOT_DIR+'/lang/'
_solar_upagraha_list = ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu']
_other_upagraha_list = ['kaala','mrityu','artha_prabhakara','yama','gulika','maandi']
_special_lagna_list = ['bhava_lagna','hora_lagna','ghati_lagna','vighati_lagna','sree_lagna','varnada_lagna',
                       'pranapada_lagna','indu_lagna','bhrigu_bindhu']

_ephe_path = os.path.abspath(_EPHIMERIDE_DATA_PATH)
swe.set_ephe_path(_ephe_path)
sidereal_year = 365.256364   # From JHora
lunar_year = 354.36707
savana_year = 360
nakshathra_year = 324
average_gregorian_year = 365.2425
tropical_year = 365.242190#365.242190=>JHora value #PyJHora Value=>365.24219879 
human_life_span_for_dhasa = 120. ## years
human_life_span_for_ashtottari_dhasa = 108
# Nakshatra lords, order matters. See https://en.wikipedia.org/wiki/Dasha_(astrology)
adhipati_list = [ 8, 5, 0, 1, 2, 7, 4, 6, 3 ]

# (Maha-)dasha periods (in years)
mahadasa = { 8: 7, 5: 20, 0: 6, 1: 10, 2: 7,7: 18, 4: 16, 6: 19, 3: 17 }

# assert(0 <= nak <= 26)
available_horoscope_calculation_methods = ['drik','ss']
available_ayanamsa_modes = {"FAGAN":swe.SIDM_FAGAN_BRADLEY ,"KP": swe.SIDM_KRISHNAMURTI, "LAHIRI": swe.SIDM_LAHIRI, 
                            "RAMAN": swe.SIDM_RAMAN, "USHASHASHI": swe.SIDM_USHASHASHI, 
                            "YUKTESHWAR": swe.SIDM_YUKTESHWAR, "SURYASIDDHANTA": swe.SIDM_SURYASIDDHANTA,
                            "SURYASIDDHANTA_MSUN": swe.SIDM_SURYASIDDHANTA_MSUN, "ARYABHATA":swe.SIDM_ARYABHATA, 
                            "ARYABHATA_MSUN":swe.SIDM_ARYABHATA_MSUN,"SS_CITRA":swe.SIDM_SS_CITRA, 
                            "TRUE_CITRA":swe.SIDM_TRUE_CITRA, "TRUE_REVATI":swe.SIDM_TRUE_REVATI,
                            "SS_REVATI": swe.SIDM_SS_REVATI,'SENTHIL':'', "TRUE_LAHIRI":swe.SIDM_TRUE_CITRA,
                            "TRUE_PUSHYA":swe.SIDM_TRUE_PUSHYA, "TRUE_MULA":swe.SIDM_TRUE_MULA,
                            "KP-SENTHIL":swe.SIDM_KRISHNAMURTI_VP291,
                            "SIDM_USER":swe.SIDM_USER,'SUNDAR_SS':'',
                            #"ARYABHATA_522":swe.SIDM_ARYABHATA_522, 
                            }
_DEFAULT_AYANAMSA_MODE = 'LAHIRI' #'TRUE_CITRA'
human_life_span_for_vimsottari_dhasa = 120
# Nakshatra lords, order matters. See https://en.wikipedia.org/wiki/Dasha_(astrology)
 # Nak Lord Order: Aswini(Rahu),Bharani(Mars),Krithika(Moon),Rohini(Sun),Mrigasira(Venus),Ardra(Ketu),...
vimsottari_adhipati_list = [ 8, 5, 0, 1, 2, 7, 4, 6, 3 ]
# In the above Dhasa Seed for Ketu is Aswini. As variations we can choose any star as the Starting Dhasa Lord for Ketu
# And the next stars will be for Venus, Sun etc..

# (Maha-)dasha periods (in years)
vimsottari_dict = { 8: 7, 5: 20, 0: 6, 1: 10, 2: 7, 7: 18, 4: 16, 6: 19, 3: 17 }

varsha_vimsottari_days = {0:18, 1:30, 2:21, 7:54, 4:48,6:57, 3:51, 8:21, 5:60}
varsha_vimsottari_adhipati_list = list(varsha_vimsottari_days.keys())
human_life_span_for_varsha_vimsottari_dhasa = sum(varsha_vimsottari_days.values())
#varsha_vimsottari_adhipati_list = [0, 1, 2, 7, 4, 6, 3, 8, 5]
# assert(0 <= nak <= 26)
# Return nakshatra lord (adhipati)
rasi_names_en = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
savya_stars_1 = [0,2,6,8,12,14,18,20,24]
savya_stars_2 = [1,7,13,19,25,26]
apasavya_stars_1 = [3,9,15,21]
apasavya_stars_2 = [4,5,10,11,16,17,22,23]
kalachakra_stars = [savya_stars_1,savya_stars_2,apasavya_stars_1,apasavya_stars_2]
kalachakra_dhasa_duration = [7,16,9,21,5,9,16,7,10,4,4,10]
savya_stars_1_rasis =[[0,1,2,3,4,5,6,7,8],[9,10,11,7,6,5,3,4,2],[1,0,11,10,9,8,0,1,2],[3,4,5,6,7,8,9,10,11]]
savya_stars_1_rasis_paramayush=[100,85,83,86]
savya_stars_2_rasis =[[7,6,5,3,4,2,1,0,11],[10,9,8,0,1,2,3,4,5],[6,7,8,9,10,11,7,6,5],[3,4,2,1,0,11,10,9,8]]
savya_stars_2_rasis_paramayush=savya_stars_1_rasis_paramayush
apasavya_stars_1_rasis=[[8,9,10,11,0,1,2,4,3],[5,6,7,11,10,9,8,7,6],[5,4,3,2,1,0,8,9,10],[11,0,1,2,4,3,5,6,7]]
apasavya_stars_1_rasis_paramayush=[86,83,85,100]
apasavya_stars_2_rasis=[[11,10,9,8,7,6,5,4,3],[2,1,0,8,9,10,11,0,1],[2,4,3,5,6,7,11,10,9],[8,7,6,5,4,3,2,1,0]]
apasavya_stars_2_rasis_paramayush=apasavya_stars_1_rasis_paramayush
kalachakra_rasis = [savya_stars_1_rasis,savya_stars_2_rasis,apasavya_stars_1_rasis,apasavya_stars_2_rasis]
kalachakra_rasis_list = sum(savya_stars_1_rasis,[])+sum(savya_stars_2_rasis,[])+sum(apasavya_stars_1_rasis,[])+sum(apasavya_stars_2_rasis,[])
#print(kalachakra_rasis_list)

kalachakra_paramayush = [savya_stars_1_rasis_paramayush,savya_stars_2_rasis_paramayush,apasavya_stars_1_rasis_paramayush,apasavya_stars_2_rasis_paramayush]
# ashtaka_varga_dict[target][source] = list of house numbers (1..12)
# that are benefic (table value = 1) for the target planet/lagna,
# counted from the source planet/lagna.
#
# target = top-level dict key:
#     "0"=Sun, "1"=Moon, "2"=Mars, "3"=Mercury,
#     "4"=Jupiter, "5"=Venus, "6"=Saturn, "7"=Lagna
#
# source = index inside the value list:
#     0=Sun, 1=Moon, 2=Mars, 3=Mercury,
#     4=Jupiter, 5=Venus, 6=Saturn, 7=Lagna
#
# Example:
# ashtaka_varga_dict["0"][3] = [3, 5, 6, 9, 10, 11, 12]
# means:
# In Sun's Ashtakavarga, the benefic houses counted from Mercury
# are the 3rd, 5th, 6th, 9th, 10th, 11th, and 12th houses.
ashtaka_varga_dict={ #7 is used for Lagna here
    "0":[[1,2,4,7,8,9,10,11],[3,6,10,11],[1,2,4,7,8,9,10,11],[3,5,6,9,10,11,12],[5,6,9,11],[6,7,12],[1,2,4,7,8,9,10,11],[3,4,6,10,11,12]],
    "1":[[3,6,7,8,10,11 ],[1,3,6,7,9,10,11],[2,3,5,6,10,11],[1,3,4,5,7,8,10,11],[1,2,4,7,8,10,11],[3,4,5,7,9,10,11],[3,5,6,11],[3,6,10,11]],
    "2":[[3,5,6,10,11],[3,6,11],[1,2,4,7,8,10,11],[3,5,6,11],[6,10,11,12],[6,8,11,12],[1,4,7,8,9,10,11],[1,3,6,10,11]],
    "3":[[5,6,9,11,12],[2,4,6,8,10,11],[1,2,4,7,8,9,10,11],[1,3,5,6,9,10,11,12],[6,8,11,12],[1,2,3,4,5,8,9,11],[1,2,4,7,8,9,10,11],[1,2,4,6,8,10,11]],
    "4":[[1,2,3,4,7,8,9,10,11],[2,5,7,9,11],[1,2,4,7,8,10,11],[1,2,4,5,6,9,10,11],[1,2,3,4,7,8,10,11],[2,5,6,9,10,11],[3,5,6,12],[1,2,4,5,6,7,9,10,11]],
    "5":[[8,11,12],[1,2,3,4,5,8,9,11,12],[3,4,6,9,11,12],[3,5,6,9,11],[5,8,9,10,11],[1,2,3,4,5,8,9,10,11],[3,4,5,8,9,10,11],[1,2,3,4,5,8,9,11]],
    "6":[[1,2,4,7,8,10,11],[3,6,11],[3,5,6,10,11,12],[6,8,9,10,11,12],[5,6,11,12],[6,11,12],[3,5,6,11],[1,3,4,6,10,11]],
    "7":[[3,4,6,10,11,12],[3,6,10,11,12],[1,3,6,10,11],[1,2,4,6,8,10,11],[1,2,4,5,6,7,9,10,11],[1,2,3,4,5,8,9],[1,3,4,6,10,11],[3,6,10,11]] ## This is for Lagna
    }
#Jupiter/Venus. Mercury benefic if alone or with other benefics. Moon benefic in sukla paksha (tithi <=15)
natural_benefics = [4,5] 
natural_malefics = [0,2,6,7,8]
""" TODO: Check some of the following female planets should go to neutral planets 
    It will impact Harsha Bala calculations as well.
"""
feminine_planets = [1,3,5,6]
masculine_planets = [0,2,4]
harsha_bala_houses = [8,2,5,0,10,11,11]
harsha_bala_feminine_houses = [0,1,2,6,7,8]
harsha_bala_masculine_houses = [3,4,5,9,10,11]
nakshatra_lords = [8,5,0,1,2,7,4,6,3,8,5,0,1,2,7,4,6,3,8,5,0,1,2,7,4,6,3]
" house module constants " #V2.3.0
# in the order of Janma, Sampath,Vipath, Kshema, Prathyak, Saadhana, Naidhana, Mithra, Parama/Adhi Mithra
nakshathra_lords = {8:(0,9,18), 5:(1,10,19), 0:(2,11,20), 1:(3,12,21), 2:(4,13,22), 7:(5,14,23), 
                    4:(6,15,24), 6:(7,16,25), 3:(8,17,26)}
# Ref: https://www.indiadivine.org/content/topic/1423092-special-tara-table/
special_thaara_lords = {8:(0,9,18,26), 5:(1,10,19), 0:(2,11,27), 1:(3,12,20), 2:(4,13,21), 7:(5,14,22), 
                    4:(6,15,23), 6:(7,16,24), 3:(8,17,25)}
special_thaara_lords_1 = {8:(0,9,18), 5:(1,10,19), 0:(2,11,20), 1:(3,12,21,22), 2:(4,13,23,), 7:(5,14,24),
                          4:(6,15,25,), 6:(7,16,26), 3:(8,17,27)}
# In the order of Janma, Karma, Samudayika, Sanghatika, Jaathi, Naidhana, Desha,Abhisheka, Aadhaana, Vainasika, Maanasa
#special_thaara_map = [1,10,18,16,4,7,12,27,19,22,25]#[1,10,18,16,4,7,12,28,19,22,25]
special_thaara_map = [1, 10, 18, 16, 4, 7, 12, 28, 19, 22, 25]
_ABHIJITH_STAR_INDEX = 21 # In the range of 1..28
house_lords_dict = {0:[4],1:[3],2:[0,7],3:[2,5],4:[8,11],5:[1,6],6:[9,10],7:[10],8:[7]}
houses_of_rahu_kethu = {7:10,8:7}
#Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi
#Sc Ge Cp Sg Cn Aq Ta Sg Cn Ge Cp Le
rudra_eighth_house = [7,2,9,8,3,10,1,8,3,2,9,4]
# Uccham = Exhalted  Neecham = Debilated
_OWNER_RULER = 5
_EXALTED_UCCHAM = 4
_FRIEND = 3
_NEUTRAL_SAMAM = 2
_ENEMY = 1
_DEBILITATED_NEECHAM = 0
house_strength_types = {5:'Ruler/Owner/Lord',4:'Uccham/Exalted',3:'Friend',2:'Samam',1:'Enemy',0:'Neecham/Defibilated'}
house_strengths_of_planets = [
    #Ar,Ta,Ge,Cn,Le,Vi,Li,Sc,Sg,Cp,Aq,Pi
    [4, 1, 2, 2, 5, 2, 0, 3, 3, 1, 1, 3], # 0 Sun
    [2, 4, 3, 5, 3, 3, 2, 0, 2, 2, 2, 2], # 1 Moon
    [5, 2, 1, 0, 3, 1, 2, 5, 3, 4, 2, 3], # 2 Mars
    [2, 3, 5, 1, 3, 5, 3, 2, 2, 2, 2, 0], # 3 Mercury
    [3, 1, 1, 4, 3, 1, 1, 3, 5, 0, 2, 5], # 4 Jupiter #Fixed per Issue#67
    [2, 5, 3, 1, 1, 0, 5, 2, 3, 3, 3, 4], # 5 Venus
    [0, 3, 3, 1, 1, 3, 4, 1, 2, 5, 5, 2], # 6 Saturn
    [1, 4, 4, 1, 1, 3, 3, 0, 0, 3, 1, 3], # 7 Rahu (Exalted 1,2 | Debilitated 7,8)
    [1, 0, 0, 1, 1, 3, 3, 4, 4, 3, 1, 3], # 8 Ketu (Debilitated 1,2 | Exalted 7,8)
    #[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5, 2], # 9 Uranus # Aquarius
    #[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5], # 10 Neptune #Pisces
    #[2, 2, 2, 2, 2, 2, 2, 5, 2, 2, 2, 2], # 11 Pluto # Scorpio
]
__house_strengths_of_planets_old=[[4,1,2,2,5,2,0,3,3,1,1,3],
                            [2,4,3,5,3,3,2,0,2,2,2,2],
                            [5,2,1,0,3,1,2,5,3,4,2,3],
                            [2,3,5,1,3,5,3,2,2,2,2,0],
                            [3,1,1,4,3,3,1,3,5,0,2,5],
                            [2,5,3,1,1,0,5,2,3,3,3,4],
                            [0,3,3,1,1,3,4,1,2,5,5,2],
                            [1,0,3,1,1,3,3,4,3,3,1,3],
                            [1,0,3,1,1,3,3,4,3,3,1,3]]

moola_trikona_of_planets = [4,1,0,5,8,6,10,5,11]
# Moolatrikona Ranges: (Sign_Index, Start_Degree, End_Degree)
moola_trikona_range_of_planets = {
    SUN_ID: (4, 0.0, 20.0),      # Leo 0-20
    MOON_ID: (1, 3.0, 30.0),     # Taurus 3-30
    MARS_ID: (0, 0.0, 12.0),     # Aries 0-12 (Note: PVR/Standard says Aries, not Leo)
    MERCURY_ID: (5, 15.0, 20.0), # Virgo 15-20
    JUPITER_ID: (8, 0.0, 10.0),  # Sag 0-10
    VENUS_ID: (6, 0.0, 15.0),    # Libra 0-15
    SATURN_ID: (10, 0.0, 20.0)   # Aq 0-20
}
temporary_friend_raasi_positions = [1,2,3,9,10,11]
temporary_enemy_raasi_positions = [0,4,5,6,7,8]
friend_enemy_addition =   [[0.5, 0],
                           [0  , 0],
                           [0, -0.5]
                          ] 
"""
        Table 8: Compound Relationships
                Temporary friend             Temporary enemy
Natural friend     Adhimitra (good friend)     Sama (neutral)
Natural neutral     Mitra (friend)             Satru (enemy)
Natural enemy       Sama (neutral)             Adhisatru (bad enemy)
"""
compound_relations_of_planets = [[5,3],[4,2],[3,1]]
""" 5: AdhiMitra/GreatFriend 4:Mitra/Friend 3: Neutral/Samam 2: Satru/Enemy 1: AdhiSatru/GreatEnemy """
_ADHIMITRA_GREATFRIEND = 5
_MITHRA_FRIEND = 4
_SAMAM_NEUTRAL = 3
_SATHRU_ENEMY = 2
_ADHISATHRU_GREATENEMY = 1
compound_planet_relations = [[-1,5,5,4,3,3,3,3,3], # Sun
                             [5,-1,2,5,2,2,4,1,1], # Moon
                             [5,3,-1,3,3,2,4,1,5], # Mars
                             [5,3,4,-1,2,5,2,4,2], # Mercury
                             [3,3,3,1,-1,1,2,3,4], # Jupiter
                             [3,1,2,5,2,-1,5,3,5], # Venus
                             [3,3,3,3,2,5,-1,5,1], # Saturn
                             [3,1,1,4,2,3,5,-1,1], # Rahu
                             [3,1,5,2,4,5,1,1,-1]] # Ketu
compound_planet_relations_including_western_planets = [  # V4.8.5
    # Sun, Moon, Mars, Mer, Jup, Ven, Sat, Rah, Ket, Ura, Nep, Plu
    [-1, 5, 5, 4, 3, 3, 3, 3, 3, 5, 5, 5], # Sun
    [5, -1, 2, 5, 2, 2, 4, 1, 1, 4, 5, 2], # Moon
    [5, 3, -1, 3, 3, 2, 4, 1, 5, 4, 4, 5], # Mars
    [5, 3, 4, -1, 2, 5, 2, 4, 2, 5, 3, 2], # Mercury
    [3, 3, 3, 1, -1, 1, 2, 3, 4, 4, 5, 4], # Jupiter
    [3, 1, 2, 5, 2, -1, 5, 3, 5, 2, 2, 1], # Venus
    [3, 3, 3, 3, 2, 5, -1, 5, 1, 3, 2, 2], # Saturn
    [3, 1, 1, 4, 2, 3, 5, -1, 1, 2, 1, 1], # Rahu
    [3, 1, 5, 2, 4, 5, 1, 1, -1, 4, 5, 5], # Ketu
    [5, 4, 4, 5, 4, 2, 3, 2, 4, -1, 4, 4], # Uranus (Higher Octave Mercury)
    [5, 5, 4, 3, 5, 2, 2, 1, 5, 4, -1, 4], # Neptune (Higher Octave Moon/Ketu)
    [5, 2, 5, 2, 4, 1, 2, 1, 5, 4, 4, -1]  # Pluto (Higher Octave Mars)
]
""" 3:'Friend',2:'Samam',1:'Enemy' """
planet_relations = [ [5,3,3,2,3,1,1,1,2], #Sun
                     [3,5,2,3,2,2,2,2,2], #Moon
                     [3,3,5,1,3,2,2,2,2], #Mars
                     [3,1,2,5,2,3,2,2,1], #Mercury
                     [3,3,3,1,5,1,2,1,2], #Jupiter
                     [1,1,2,3,2,5,3,3,2], #Venus
                     [1,1,1,3,2,3,5,3,1], #Saturn
                     [1,1,1,2,2,3,3,5,2], #Rahu
                     [3,2,3,2,2,1,1,2,5]  #Ketu
                   ]
friendly_planets = []
for row in planet_relations:
    fp = []
    for c,col in enumerate(row):
        if _FRIEND == col:
            fp.append(c)
    friendly_planets.append(fp)
neutral_planets = []
for row in planet_relations:
    fp = []
    for c,col in enumerate(row):
        if _NEUTRAL_SAMAM == col:
            fp.append(c)
    neutral_planets.append(fp)
enemy_planets = []
for row in planet_relations:
    fp = []
    for c,col in enumerate(row):
        if _ENEMY == col:
            fp.append(c)
    enemy_planets.append(fp)
#print('planet_relations',planet_relations)
#print('friendly_planets',friendly_planets)
#print('neutral_planets',neutral_planets)
#print('enemy_planets',enemy_planets)
#"""
_friendly_planets = [[1,2,4],[0,3],[0,1,4],[0,5],[0,1,2],[3,6],[3,5]]
_neutral_planets = [[3],[2,4,5,6],[5,6],[2,4,6],[6],[2,4],[4]]
_enemy_planets = [[5,6],[],[3],[1],[3,5],[0,1],[0,1,2]]
#"""
house_owners = np.where(np.array(house_strengths_of_planets).transpose()==_OWNER_RULER)[1].tolist() # V4.8.6
_house_owners_list = [2,5,3,1,0,3,5,2,4,6,6,4]
planet_deep_exaltation_longitudes = [10.0,33.0,298.0,165.0,95.0,357.0,200.0]
planet_deep_exaltation_tolerance = 1.0 # 1 degree
planet_deep_debilitation_longitudes = [(e+180.0)%360 for e in planet_deep_exaltation_longitudes]
planet_deep_debilitation_tolerance = 1.0 # 1 degree
graha_drishti = {0:[7],1:[7],2:[4,7,8],3:[7],4:[5,7,9],5:[7],6:[3,7,10],7:[7],8:[7],9:[7],10:[7],11:[7]}
movable_signs = [0,3,6,9]
chara_rasis = movable_signs
fixed_signs = [1,4,7,10]
sthira_rasis = fixed_signs
dual_signs = [2,5,8,11]
ubhaya_rasis = dual_signs
longevity = {0:[(0,0),(1,2),(2,1)],1:[(0,1),(1,0),(2,2)],2:[(0,2),(1,1),(2,0)]} #0=>Fixed, 1=> Movable, 2=>Dual
longevity_years = [[32,36,40],[64,72,80],[96,108,120]] # 0th element Short Life, 1st : Middle Life, 2nd element: Long Life
odd_signs = [0,2,4,6,8,10] # => 1,3,5,7,9,11
even_signs = [1,3,5,7,9,11]# 2,4,6,8,10, 12
odd_footed_signs = [0,1,2,6,7,8]
even_footed_signs = [3,4,5,9,10,11]
fire_signs = [0,4,8]
earth_signs = [1,5,9]
air_signs = [2,6,10]
water_signs = [3,7,11]
space_signs = [*range(12)]
pittha_nature_signs = [0,4,8]
vaatha_nature_signs = [1,5,9]
kapa_nature_signs = [3,7,11]
mixed_nature_signs = [2,6,10]
east_signs = [0,4,8]
south_signs = [1,5,9]
west_signs = [2,6,10]
north_signs = [3,7,11]
dry_signs = [ARIES,TAURUS,GEMINI,LEO,VIRGO,SAGITTARIUS]
dry_planets = [SUN_ID,MARS_ID,SATURN_ID]
watery_planets = [MOON_ID,VENUS_ID]
nara_rasi_longitudes = [(60,90),(150,180),(180,210),(240,255),(300,330)] # Rasi and longitude range
jalachara_rasi_longitudes = [(90,120),(285,300),(330,360)]
chatushpada_rasis = [(0,30),(30,60),(120,150),(255,270),(270,285)]
keeta_rasis = [(210,240)]

argala_houses = [2,4,5,11]
argala_houses_str = ['2nd','4th','5th','11th']
virodhargala_houses = [12,10,9,3] # respectively to argala houses [2,4,11,5]
virodhargala_houses_str = ['12th','10th','9th','3rd']
houses_str = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th']
" Tajaka constants"
hadda_lords = [[(4,6),(5,12),(3,20),(2,25),(6,30)], #Aries (planet, long_degree_max
               [(5,8),(3,14),(5,22),(6,27),(2,30)], #Taurus
               [(3,6),(5,12),(4,17),(2,24),(6,30)], #Gemini
               [(2,7),(5,13),(3,19),(4,26),(6,30)], #Cancer
               [(4,6),(5,11),(6,18),(3,24),(2,30)], #Leo
               [(3,7),(5,17),(4,21),(2,28),(6,30)], #Virgo
               [(6,6),(3,14),(4,21),(5,28),(2,30)], #Libra
               [(2,7),(5,11),(3,19),(4,24),(6,30)], #Scorpio
               [(4,12),(5,17),(3,21),(2,26),(6,30)], #Sagitarius
               [(3,7),(4,14),(5,22),(6,26),(2,30)], #Capricorn
               [(3,7),(5,13),(4,20),(2,25),(6,50)], #Aquarius
               [(5,12),(4,16),(3,19),(2,28),(6,30)]] #Pisces
hadda_points = [15,7.5,3.75] # [15,11.5,7.5,3.75] # Own, Friend, Enemy, Neutral
" Narayana Dhasa constants "
human_life_span_for_narayana_dhasa = 144
narayana_dhasa_normal_progression = \
    [[0,1,2,3,4,5,6,7,8,9,10,11],
    [1,8,3,10,5,0,7,2,9,4,11,6],
    [2,10,6,5,1,9,8,4,0,11,7,3],
    [3,2,1,0,11,10,9,8,7,6,5,4],
    [4,9,2,7,0,5,10,3,8,1,6,11],
    [5,9,1,2,6,10,11,3,7,8,0,4],
    [6,7,8,9,10,11,0,1,2,3,4,5],
    [7,2,9,4,11,6,1,8,3,10,5,0],
    [8,4,0,11,7,3,2,10,6,5,1,9],
    [9,8,7,6,5,4,3,2,1,0,11,10],
    [10,3,8,1,6,11,4,9,2,7,0,5],
    [11,3,7,8,0,4,5,9,1,2,6,10]]
narayana_dhasa_saturn_exception_progression = \
    [[0,1,2,3,4,5,6,7,8,9,10,11],
    [1,2,3,4,5,6,7,8,9,10,11,0],
    [2,3,4,5,6,7,8,9,10,11,0,1],
    [3,4,5,6,7,8,9,10,11,0,1,2],
    [4,5,6,7,8,9,10,11,0,1,2,3],
    [5,6,7,8,9,10,11,0,1,2,3,4],
    [6,7,8,9,10,11,0,1,2,3,4,5],
    [7,8,9,10,11,0,1,2,3,4,5,6],
    [8,9,10,11,0,1,2,3,4,5,6,7],
    [9,10,11,0,1,2,3,4,5,6,7,8],
    [10,11,0,1,2,3,4,5,6,7,8,9],
    [11,0,1,2,3,4,5,6,7,8,9,10]]
narayana_dhasa_ketu_exception_progression = \
    [[0,11,10,9,8,7,6,5,4,3,2,1],
    [1,6,11,4,9,2,7,0,5,10,3,8],
    [2,6,10,11,3,7,8,0,4,5,9,1],
    [3,4,5,6,7,8,9,10,11,0,1,2],
    [4,11,6,1,8,3,10,5,0,7,2,9],
    [5,1,9,8,4,0,11,7,3,2,10,6],
    [6,5,4,3,2,1,0,11,10,9,8,7],
    [7,0,5,10,3,8,1,6,11,4,9,2],
    [8,0,4,5,9,1,2,6,10,11,3,7],
    [9,10,11,0,1,2,3,4,5,6,7,8],
    [10,5,0,7,2,9,4,11,6,1,8,3],
    [11,7,3,2,10,6,5,1,9,8,4,0]]
tri_rasi_daytime_lords = [0,5,6,5,4,1,3,2,6,2,4,1]
tri_rasi_nighttime_lords = [4,1,3,2,0,5,6,5,6,2,4,1]
# TRUE => Saravali formula from https://saravali.github.io/astrology/bala_sthana.html#uchcha 
# Sarvali formula is also used in BV Raman Book
# False => PVR Book formua
use_saravali_formula_for_uccha_bala = True  
pancha_vargeeya_bala_strength_threshold = 10
order_of_planets_by_speed = [6,7,8,4,2,0,5,3,1] # Saturn is slowest and moon is fastest
deeptaamsa_of_planets=[15,12,8,7,9,7,9] #sun, moon,mars,mercury,jupiter,venus,saturn
combustion_range_of_planets_from_sun = [12,17,14,10,11,15] #moon,mars,mercury,jupiter,venus,saturn
combustion_range_of_planets_from_sun_while_in_retrogade = [12,8,12,11,8,16] # [12,17,12,8,11,15] #moon,mars,mercury,jupiter,venus,saturn
ritu_per_solar_tamil_month = True # False means calculate ritu based on north indian lunaro month index
annual_chart_solar_positions = {1:(1,6,9,12),2:(2,12,18,18),3:(3,18,27,30),4:(5,0,36,36),5:(6,6,45,48),6:(0,12,55,0),7:(1,19,4,6),
                                8:(3,1,13,18),9:(4,7,22,30),10:(5,13,31,36),20:(4,3,3,12),30:(2,16,34,54),40:(1,6,6,30),50:(6,19,38,6),
                                60:(5,9,9,42),70:(3,22,41,24),80:(2,12,13,0),90:(1,1,44,36),100:(6,15,16,12)}
_arudha_lagnas_included_in_chart = {k:'bhava_arudha_a'+str(k)+'_str' for k in range(1,13)}# [1,12]}
northern_rasis = [0,1,2,9,10,11]
southern_rasis = [3,4,5,6,7,8]
planets_disc_diameters = [-1,-1,9.4,6.6,190.4,16.6,158.0,-1,-1]
planet_mean_daily_motions_at_1900 = [257.4568, -1, 270.22, 164.0, 220.04, 328.51, 236.74]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_solar_daily_motions_table_from_1900 = [
    [0.9856, 98.5602, 265.6026, 136.0265],
    [1.9712, 197.1205, 171.2053, 272.0531],
    [2.9568, 295.6808, 76.8080,  48.0796],
    [3.9424, 34.2411, 342.4106, 184.1062],
    [4.9280, 132.8013, 248.0133, 320.1327],
    [5.9136, 231.3616, 153.6159, 96.1593],
    [6.8992, 329.9218, 59.2186, 232.1868],
    [7.8848, 68.4821, 324.8212, 8.2124],
    [8.8704, 167.0424, 230.4239, 144.2389]]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_mars_daily_motions_table_from_1900 = [
    [0.524, 52.40, 164.02, 200.19],
    [1.048, 104.80, 328.04, 40.39],
    [1.572, 157.21, 132.06, 240.58],
    [2.096, 209.61, 296.08, 80.78],
    [2.620, 262.01, 100.10, 280.97],
    [3.144, 314.41, 264.12, 121.16],
    [3.668, 6.81  , 68.14 , 321.36],
    [4.192, 59.22, 232.15,  161.55],
    [4.716, 111.62, 36.17,  1.74]]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_jupiter_daily_motions_table_from_1900 = [
    [0.08, 0.83, 8.31, 83.1, 110.96],
    [0.17, 1.66, 16.62, 166.19, 221.93],
    [0.25, 2.49, 24.93, 249.29, 332.89],
    [0.33, 3.32, 33.24, 332.39, 83.85],
    [0.41, 4.15, 41.55, 55.48, 194.82],
    [0.50, 4.99, 49.86, 138.58, 305.78],
    [0.58, 5.82, 58.17, 221.67, 56.74],
    [0.66, 6.65, 66.48, 304.77, 167.71],
    [0.75, 7.48, 74.79, 27.87, 278.67]]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_saturn_daily_motions_table_from_1900 = [
    [.03, 0.33, 3.34, 33.44, 334.39],
    [0.07, 0.67, 6.69, 66.88, 308.79],
    [0.10, 1.00, 10.03, 100.32, 283.18],
    [0.13, 1.34, 13.38, 133.76,257.57],
    [0.17, 1.67, 16.72, 167.20, 231.97],
    [0.20, 2.01, 20.06, 200.64, 206.36],
    [0.23, 2.34, 23.41, 234.08, 180.75],
    [0.27, 2.68, 26.75, 267.51, 155.14],
    [0.30, 3.01, 30.10, 300.95, 129.54]]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_mercury_daily_motions_table_from_1900 = [
    [4.09, 40.92, 49.23, 132.32, 243.18],
    [8.18, 81.84, 98.46, 264.64, 126.36],
    [12.28, 122.77, 147.70, 36.95, 9.54],
    [16.37, 163.69, 196.93, 169.27, 252.72],
    [20.46, 204.62, 246.16, 301.59, 135.90],
    [24.55, 245.54, 295.39, 73.91, 19.08],
    [28.65, 286.46, 344.62, 206.23, 262.26],
    [32.74, 327.38, 33.85, 338.54, 145.44],
    [36.83, 8.31, 83.09, 110.86, 28.63]]
""" Columns => Units, Hundreds, thousands, ten thousands """
mean_venus_daily_motions_table_from_1900 = [
    [1.60, 16.02, 160.21, 162.15, 181.46],
    [3.20, 32.04, 320.43, 324.29, 2.93],
    [4.81, 48.06, 120.64, 126.44, 184.39],
    [6.41, 64.09, 280.86, 288.59, 5.86],
    [8.01, 80.11, 81.07,  90.73, 187.32],
    [9.61, 96.13, 241.29,  252.88,  8.78],
    [11.21, 112.15, 41.50, 55.02, 190.25],
    [12.82, 128.17, 201.72, 217.17, 11.71],
    [14.42, 144.19, 1.93, 19.32, 193.18]]
naisargika_bala = [60.00,51.43,17.14,25.71,34.29,42.86,8.57,0.0,0.0]
minimum_bhava_bala_rupa = 7.0
planets_retrograde_limits_from_sun = {2:(164,196),3:(144,216),4:(130,230),5:(163,197),6:(115,245)}
lunar_gregory_month_max = 6
sthree_dheerga_threshold = 13
sthree_dheerga_threshold_south = 7
raasi_threshold_south = 6
gana_threshold_south = 14
rasi_sandhi_duration = 1.0
annual_maximum_age = 90
""" Baadhakas [Baadhaka Sthaana,[baadhaka planets]]..."""
baadhakas = [[10,[6,7]],[9,[6]],[8,[4]],[1,[5]],[0,[2]],[11,[4]],[4,[0]],[3,[1]],[2,[3]],[7,[2,8]],[6,[5]],[5,[3]]]
ganda_moola_stars = [1,9,10,18,19,27] # Ashwini, Ashlesha/Ayilyam, Magha, Jyeshta, Moola, or Revati
conjunction_aspect_threshold = 8.0
square_aspect_threshold = 8.0 ; chathusra_aspect_threshold = square_aspect_threshold
sextile_aspect_threshold = 7.0; trine_aspect_threhold = 8.0; parallel_aspect_threshold = 1.0
compatibility_minimum_score_north = 18.0
compatibility_minimum_score_south = 6.0
compatibility_maximum_score_south = 10.0
compatibility_maximum_score_north = 36.0
mandatory_compatibility_south_list = [1,2,3,5] # Gana(1), Dhinam/Thara/Star(2), Yoni(3), Rasi(5). Rajju is also added.
available_chart_types = ['south indian','north indian','east indian','western','sudarsana chakra']
class CHART_STYLE(IntEnum):
    SOUTH_INDIAN_REGULAR = 1
    NORTH_INDIAN = 2
    EAST_INDIAN_WITH_FRAME = 3
    WESTERN = 4
    SUDARSANA_CHAKRA = 5
    SOUTH_INDIAN_IRREGULAR = 6
    EAST_INDIAN_NO_FRAME = 7
default_chart_type = CHART_STYLE.SOUTH_INDIAN_REGULAR

birth_rectification_step_minutes = 0.25
birth_rectification_loop_count = 120 # Number of steps
_GREEN_CHECK = '\u2705' ; _RED_CROSS = '\u274C'
_GREEN_OR_RED = lambda b:_GREEN_CHECK if b else _RED_CROSS
include_special_and_arudha_lagna_in_charts = False # V3.1.9
""" SPECIAL CASE OF TITHI SKIPPING BEFORE MAHABHARATHA TIME 
    See Dr. Jayasree Saranatha Mahabharatha date validation book
"""
increase_tithi_by_one_before_kali_yuga = True
mahabharatha_tithi_julian_day = 588465.0

use_aharghana_for_vaara_calcuation = False # V4.4.5
minimum_separation_longitude=0.00001
conjunction_increment=0.00001 #1.0/86400 #
include_charts_only_for_western_type = False
include_maandhi_in_charts=True
_PRAVESHA_LIST = ['birth_str','annual_str','tithi_pravesha_str','lunar_month_year_str','present_str','planetary_conjunctions_str',
                  'planet_transit_str','vakra_gathi_change_str','eclipse_str','prenatal_time_str','vrathas_str',
                  'customized_str','nakshathra_dhasa_progression_str']
sphuta_list = ["tri","chatur","pancha","prana","deha","mrityu","sookshma_tri","beeja","kshetra","tithi","yoga",
               "rahu_tithi","yogi","avayogi"]
ashtottari_bhukthi_starts_from_dhasa_lord = True #PVR Book says this should be False. But JHora has this True
chara_karaka_names = ['atma_karaka','amatya_karaka','bhratri_karaka','maitri_karaka','pitri_karaka','putra_karaka',
                      'jnaati_karaka','data_karaka']
""" Donot remember from where I got this dictionary of karana to lord mapping. JHora does not have Rahu and Kethu
    for Karana Chathuraseethi sama dasa. So the lords of Rahu/Ketu have been distributed to other lords as per the original sequence.
"""
karana_lords = {0:[(2,9,16,23,30,37,44,51,58),12],1:[(3,10,17,24,31,38,45,52,59),12],2:[(4,11,18,25,32,39,46,53,60),12],
                3:[(5,12,19,26,33,40,47,54,1),12],4:[(6,13,20,27,34,41,48,55),12],5:[(7,14,21,28,35,42,49,56),12],
                6:[(8,15,22,29,36,43,50,57),12],7:[(58,60),12],8:[(1,59),12]}
pindayu_full_longevity_of_planets=[19,25,15,12,15,21,20] #in years for Sun to Saturn - when they are in highest exhaltation
pindayu_base_longevity_of_planets=[0.5*full for full in pindayu_full_longevity_of_planets] #in years for Sun to Saturn - when they are in deepest debilitation
nisargayu_full_longevity_of_planets=[20,1,2,9,18,20,50] #in years for Sun to Saturn - when they are in highest exhaltation
nisargayu_base_longevity_of_planets=[0.5*full for full in nisargayu_full_longevity_of_planets] #in years for Sun to Saturn - when they are in deepest debilitation
aayu_dhasa_types = ['pinda','nisarga','amsa']
kaala_dhasa_types = ['dawn','day','dusk','night']
aayu_types = {0:['alpaayu','0-32'],1:['madhyaayu','33-70'],2:['poornaayu','71-100']}
nakshatra_rulers = ['Aswini Kumara','Yama','Agni','Bramha','Moon','Shiva','Aditi','Jupiter','Rahu','Sun','Aryaman','Sun',
                    'Viswakarma','Vaayu','Indra','Mitra','Indra','Nirriti','Varuna','Viswaa deva','Brahma','Vishnu','Vasu',
                    'Varuna','Ajacharana','Ahirbudhanya','Pooshan']
amsa_rulers = {
                2:['Devas','Pitris'],
                3:['Naarada','Agastya','Durvaasa'],
                4:['Sanaka','Sananda','Kumaara','Sanaatana'],
                7:['Kshaara','Ksheera','Dadhi','Ghrita','Ikshu Rasa','Madya','Suddha Jala'],
                10:['Indra','Agni','Yama','Nirriti','Varuna','Vayu','Kubera','Ishana','Brahma','Ananta'],
                12:['Ganesha','Aswini Kumara','Yama','Sarpa (Ahi)','Ganesha','Aswini Kumara','Yama','Sarpa (Ahi)',
                    'Ganesha','Aswini Kumara','Yama','Sarpa (Ahi)'],
                16:['Brahma','Vishnu','Shiva','Surya']*4,
                20:['Kali/Daya','Gouri','Chinna Sheersha','Pishachini','Dhoomavati',
                    'Vimalaa','Baalaa','Taaraa','Arunaa','Swethaa','Pingalaa','Bagalamukhi','Ghoraa','Sachi','Roudri',
                    'Sitaa','Varadaa','Jayaa','Tripura/Mangala','Sumkhi/Aparaajita'],
                24:['Skanda','Parashudhara', 'Anala', 'Vishvakarma', 'Bhaga', 'Mitra', 'Maya', 'Antaka', 'Vrishdhawaja',
                    'Govinda','Madana','Bhima']*2,
                27:nakshatra_rulers,
                30:['Agni','Vaayu','Indra','Kubera','Varuna']*6,
                40:['Vishnu','Chandra','Marichi','Twashta','Dhata','Shiva','Ravi','Yama','Yaksha',
                    'Gandharva','Kaala','Varuna']*3+['Vishnu','Chandra','Marichi','Twashta'],
                60:['Ghoraa','Rakshasa','Deva','Kuber','Yaksha','Kinnar','Bhrashta','Kulaghna','Garala','Agni/Vahini','Maya',
                    'Purishaka','Apampati','Marut','Kaala','Sarpa','Amrita','Indu','Mridu','Komala','Heramba','Brahma','Vishnu',
                    'Maheshwara','Deva','Ardra','Kalinasha','Kshitish','Kamalakara','Gulika','Mrityu','Kaal','Daavagni',
                    'Ghora','Yama','Kantaka','Sudha','Amrita','Poornachandra','Vishadagdha','Kulanasha','Vanshakshya',
                    'Utpata','Kaal','Saumya','Komal','Sheetala','Karal danstra','Chandramukhi','Praveena','Kalagni',
                    'Dandayuda','Nirmala','Saumya','Kroora','Atisheetala','Amrita','Payodhi','Bhramana','Chandrarekha'],
                150:["Vasudhaa","Vaishnavi","Braahmi","Kaalakoota","Shaankari","Sudhaakari","Samaa","Saumyaa","Suraa","Maayaa",
        "Manoharaa","Maadhavi","Manjuswanaa","Ghoraa","Kumbhini","Kutilaa","Prabhaa","Paraa","Payasvini","Maalaa","Jagati",
        "Jarjharaa","Dhruvaa","Musalaa","Mudgaraa","Paashaa","Champakaa","Daamakaa(Daamini)","Mahi","Kulashaa","Kamalaa",
        "Kaantaa","Kaalaa","Karikaraa","Kahamaa","Durdharaa","Durbhagaa","Vishwaa","Visheernaa","Vikataa","Avilaa",
        "Vibhramaa","Sukhadaa","Snigdhaa","Sodaraa","Surasundari","Amritaplaavini","Kaalaa","Kaamadhuk","Karaveerani",
        "Gahvaraa","Kundini","Raudraa","Vishaakhyaa","Vishanaashini","Narmadaa","Sheetalaa","Nimnaa","Preetaa",
        "Priyavardhini","Maanaghnaa","Durbhagaa","Chiraa","Chitrini","Chiranjeevini","Bhoopaa","Gakaharaa","Naalaa","Nalini",
        "Nirmalaa","Nadi","Sudhaamritaamshu","Kaalikaa","Kalushankuraa","Trailokyamohankari","Mahaamaari","Susheetalaa",
        "Sukhadaa","Suprabhaa","Shobhaa","Shobhanaa","Shivadaa","Shivaa","Balaa","Jwaalaa","Gadaa","Gaadhaa","Nootanaa",
        "Sumanoharaa","Somavalli","Somalataa","Mangalaa","Mudrikaa","Kshudhaa","Mokshaapavargaa","Balayaa","Navaneeta",
        "Nishaachari","Nirritti","Nigadaa","Saraa","Sangeetaa","Saamadaa","Samaa","Viwhwambharaa","Kumaari","Kokilaa",
        "Kunjaraakriti","Aindraa","Swaahaa","Swaraa","Vahni","Preetaa","Rakshajalaaplavaa","Vaaruni","Madiraa","Maitri",
        "Haarini","Harini","Marut","Dhananjayaa","Dhanakari","Dhanadaa","Kamchhapaambuja","Maamshaani","Shooeini","Raudri",
        "Shivaa","Shivakari","Kalaa","Kundaa","Mukundaa","Bharataa","Haritaa","Kadalee","Smaraa","Kandalaa","Kokilaa",
        "Paapaa","Kaamini","Kalashodbhavaa","Veeraprasoo","Sangaraa","Shatayajnaa","Shataavari","Prahvi","Paatalini",
        "Naagaa","Pankajaa","Parameshwari"]
                }
# Cruel/Kroora Shashtamsa Rulers
shashti_amsa_rulers_kroora = [0,1,7,8,9,10,11,14,15,29,30,31,32,33,34,39,41,42,43,47,50,51,58]
# Good/Soumya Shashtamsa Rulers
shashti_amsa_rulers_soumya = [2,3,4,5,6,12,13,16,17,18,19,20,21,22,23,24,25,26,27,28,35,36,37,
                              38,40,44,45,46,48,49,52,53,54,55,56,57,59]

hora_chart_by_pvr_method = True
mrityu_bhaga_tolerances = {0:1/3, 1:2/3, 2:0.25, 3:2/3, 4:0.25,5:0.25,6:0.25,7:0.25,8:0.25,'Md':0.25,'L':2/3}
# For each rasi (row) Order of planets Sun, Moon, Mars, Merc, Jup, Ven,Sat,Rah,Ket,Mandi,Lagna
mrityu_bhaga_base_longitudes = [[20,26,19,15,19,28,10,14,8,23,1],
                                [9,12,28,14,29,15,4,13,18,24,9],
                                [12,13,25,13,12,11,7,12,20,11,22],
                                [6,25,23,12,27,17,9,11,10,12,22],
                                [8,24,29,8,6,10,12,24,21,13,25],
                                [24,11,28,18,4,13,16,23,22,14,2],
                                [16,26,14,20,13,4,3,22,23,8,4],
                                [17,14,21,10,10,6,18,21,24,18,23],
                                [22,13,2,21,17,27,28,10,11,20,18],
                                [2,25,15,22,11,12,14,20,12,10,20],
                                [3,5,11,7,15,29,13,18,13,21,24],
                                [23,12,6,5,28,19,15,8,14,22,10]
                                ]

south_indian_regular_chart_2d_map = [(0,1),(0,2),(0,3),(1,3),(2,3),(3,3),(3,2),(3,1),(3,0),(2,0),(1,0),(0,0)]
south_indian_irregular_chart_2d_map = [(0,2),(0,1),(0,0),(1,0),(2,0),(3,0),(3,1),(3,2),(3,3),(2,3),(1,3),(0,3)]
hora_list_raman = [(7,9), (1,11), (5,0), (3,6), (4,2),(2,3),(6,4), (0,5), (11,1), (9,7), (10,8), (8,10)] 
drekkana_jagannatha = [(0,4,8),(9,1,5),(6,10,2),(3,7,11), (0,4,8),(9,1,5),(6,10,2),(3,7,11), (0,4,8),(9,1,5),(6,10,2),(3,7,11)]
# Kalachakra Navamsa - Star => Rasi/padha mapping
# For Aswini (0) Padham 1 is Ar (0, P2=1(Ta) etc
kalachakra_navamsa = {0:[0,1,2,3], 1:[4,5,6,7], 2:[8,9,10,11], 3:[7,6,5,3], 4:[4,2,1,0],5:[11,10,9,8],
            6:[0,1,2,3], 7:[4,5,6,7], 8:[8,9,10,11], 9:[7,6,5,3], 10:[4,2,1,0],11:[11,10,9,8],
           12:[0,1,2,3],13:[4,5,6,7],14:[8,9,10,11],15:[7,6,5,3],16:[4,2,1,0],17:[11,10,9,8],
           18:[0,1,2,3],19:[4,5,6,7],20:[8,9,10,11],21:[7,6,5,3],22:[4,2,1,0],23:[11,10,9,8],
           24:[0,1,2,3],25:[4,5,6,7],26:[8,9,10,11]}
# chart_method options for each varga chart {varga:(number_of_options,defualt_option)}
varga_option_dict = {2:(6,1),3:(5,1),4:(4,1),5:(4,1),6:(4,1),7:(6,1),8:(4,1),9:(5,1),10:(6,1),11:(5,1),12:(5,1),16:(4,1),
                      20:(4,1),24:(3,1),27:(4,1),30:(5,1),40:(4,1),45:(4,1),60:(4,1),81:(3,1),108:(4,1),144:(4,1)
                      }
MAX_DHASAVARGA_FACTOR = 300
DEFAULT_CUSTOM_VARGA_FACTOR=57
# If True standard vargas such as D2,D3 etc will follow custom calculations and not standard calculations
""" DO NOT CHANGE THIS TO TRUE. NOT IMPLEMENTED YET """
TREAT_STANDARD_CHART_AS_CUSTOM = False
_bhava_arudha_list = ['bhava_arudha_str','sun_arudha','moon_arudha','mars_arudha','mercury_arudha','jupiter_arudha',
                      'venus_arudha','saturn_arudha','rahu_arudha','ketu_arudha']
"""
# Kota Chakra Star Placement - From Outer square to Inner Square
# For Inner most square - only middle no corner placement
# Order of stars are as below for the placement of kota chakra stars:
# NOTE: Abhijit is added after Uthiraadam (UttaraShada)
#Aswini,Bharani,Karthigai,Rohini,Mrigasheesham,Thiruvaathirai,Punarpoosam,Poosam,Aayilyam,Makam,Pooram,Uthiram,
#Hastham,Chithirai,Swaathi,Visaakam,Anusham,Kaettai,Moolam,Pooraadam,Uthiraadam,ABHIJIT,
#Thiruvonam,Avittam,Sadhayam,#Poorattathi,Uthirattathi,Revathi
# Number 1 in below list indicates Birth star (i.e. 1st position from birth star). 2=> 2nd position from birth star etc.
Star positions are as per birth star even for tajaka charts.
But Planets are placed per tajaka chart at its star longitude/position
"""
abhijit_order_of_stars = [*range(21)]+[27]+[*range(21,27)]
kota_chakra_star_placement_from_birth_star = [[1,7,8,14,15,21,22,28],[2,6,9,13,16,20,23,27],[3,5,10,12,17,19,24,26],
                                              [4,11,18,25]]
kota_paala_lord_for_star_paadha = [
[5,5,5,1],[1,1,1,1],[0,0,0,0],[0,1,1,1],[1,1,2,2],[2,2,2,5],[2,2,7,7],[7,7,7,3],[3,3,3,3],[6,6,6,6],[6,3,3,3],[3,3,6,6],[6,7,3,3],[6,6,1,1],
[1,1,1,4],[4,4,4,4],[4,4,4,4],[4,1,1,1],[1,1,6,6],[6,4,6,3],[6,6,5,5],[3,3,3,3],[3,3,3,3],[3,7,7,7],[7,7,4,4],[4,4,5,5],[4,4,5,5],[4,4,4,4]
]

# {kp_no: [rasi, nakshatra,(start_degress),(end_degrees),sign_lord,star lord, star sub lord]}
prasna_kp_249_dict = {
                        1:[0,0,0,0.777777777777778,2,8,8],
                        2:[0,0,0.777777777777778,3,2,8,5],
                        3:[0,0,3,3.66666666666667,2,8,0],
                        4:[0,0,3.66666666666667,4.77777777777778,2,8,1],
                        5:[0,0,4.77777777777778,5.55555555555556,2,8,2],
                        6:[0,0,5.55555555555556,7.55555555555556,2,8,7],
                        7:[0,0,7.55555555555556,9.33333333333333,2,8,4],
                        8:[0,0,9.33333333333333,11.4444444444444,2,8,6],
                        9:[0,0,11.4444444444444,13.3333333333333,2,8,3],
                        10:[0,1,13.3333333333333,15.5555555555556,2,5,5],
                        11:[0,1,15.5555555555556,16.2222222222222,2,5,0],
                        12:[0,1,16.2222222222222,17.3333333333333,2,5,1],
                        13:[0,1,17.3333333333333,18.1111111111111,2,5,2],
                        14:[0,1,18.1111111111111,20.1111111111111,2,5,7],
                        15:[0,1,20.1111111111111,21.8888888888889,2,5,4],
                        16:[0,1,21.8888888888889,24,2,5,6],
                        17:[0,1,24,25.8888888888889,2,5,3],
                        18:[0,1,25.8888888888889,26.6666666666667,2,5,8],
                        19:[0,2,26.6666666666667,27.3333333333333,2,0,0],
                        20:[0,2,27.3333333333333,28.4444444444444,2,0,1],
                        21:[0,2,28.4444444444444,29.2222222222222,2,0,2],
                        22:[0,2,29.2222222222222,30,2,0,7],
                        23:[1,2,0,1.22222222222222,5,0,7],
                        24:[1,2,1.22222222222222,3,5,0,4],
                        25:[1,2,3,5.11111111111111,5,0,6],
                        26:[1,2,5.11111111111111,7,5,0,3],
                        27:[1,2,7,7.77777777777778,5,0,8],
                        28:[1,2,7.77777777777778,10,5,0,5],
                        29:[1,3,10,11.1111111111111,5,1,1],
                        30:[1,3,11.1111111111111,11.8888888888889,5,1,2],
                        31:[1,3,11.8888888888889,13.8888888888889,5,1,7],
                        32:[1,3,13.8888888888889,15.6666666666667,5,1,4],
                        33:[1,3,15.6666666666667,17.7777777777778,5,1,6],
                        34:[1,3,17.7777777777778,19.6666666666667,5,1,3],
                        35:[1,3,19.6666666666667,20.4444444444444,5,1,8],
                        36:[1,3,20.4444444444444,22.6666666666667,5,1,5],
                        37:[1,3,22.6666666666667,23.3333333333333,5,1,0],
                        38:[1,4,23.3333333333333,24.1111111111111,5,2,2],
                        39:[1,4,24.1111111111111,26.1111111111111,5,2,7],
                        40:[1,4,26.1111111111111,27.8888888888889,5,2,4],
                        41:[1,4,27.8888888888889,30,5,2,6],
                        42:[2,4,0,1.88888888888889,3,2,3],
                        43:[2,4,1.88888888888889,2.66666666666667,3,2,8],
                        44:[2,4,2.66666666666667,4.88888888888889,3,2,5],
                        45:[2,4,4.88888888888889,5.55555555555556,3,2,0],
                        46:[2,4,5.55555555555556,6.66666666666667,3,2,1],
                        47:[2,5,6.66666666666667,8.66666666666667,3,7,7],
                        48:[2,5,8.66666666666667,10.4444444444444,3,7,4],
                        49:[2,5,10.4444444444444,12.5555555555556,3,7,6],
                        50:[2,5,12.5555555555556,14.4444444444444,3,7,3],
                        51:[2,5,14.4444444444444,15.2222222222222,3,7,8],
                        52:[2,5,15.2222222222222,17.4444444444444,3,7,5],
                        53:[2,5,17.4444444444444,18.1111111111111,3,7,0],
                        54:[2,5,18.1111111111111,19.2222222222222,3,7,1],
                        55:[2,5,19.2222222222222,20,3,7,2],
                        56:[2,6,20,21.7777777777778,3,4,4],
                        57:[2,6,21.7777777777778,23.8888888888889,3,4,6],
                        58:[2,6,23.8888888888889,25.7777777777778,3,4,3],
                        59:[2,6,25.7777777777778,26.5555555555556,3,4,8],
                        60:[2,6,26.5555555555556,28.7777777777778,3,4,5],
                        61:[2,6,28.7777777777778,29.4444444444444,3,4,0],
                        62:[2,6,29.4444444444444,30,3,4,1],
                        63:[3,6,0,0.555555555555556,1,4,1],
                        64:[3,6,0.555555555555556,1.33333333333333,1,4,2],
                        65:[3,6,1.33333333333333,3.33333333333333,1,4,7],
                        66:[3,7,3.33333333333333,5.44444444444444,1,6,6],
                        67:[3,7,5.44444444444444,7.33333333333333,1,6,3],
                        68:[3,7,7.33333333333333,8.11111111111111,1,6,8],
                        69:[3,7,8.11111111111111,10.3333333333333,1,6,5],
                        70:[3,7,10.3333333333333,11,1,6,0],
                        71:[3,7,11,12.1111111111111,1,6,1],
                        72:[3,7,12.1111111111111,12.8888888888889,1,6,2],
                        73:[3,7,12.8888888888889,14.8888888888889,1,6,7],
                        74:[3,7,14.8888888888889,16.6666666666667,1,6,4],
                        75:[3,8,16.6666666666667,18.5558333333333,1,3,3],
                        76:[3,8,18.5558333333333,19.3333333333333,1,3,8],
                        77:[3,8,19.3333333333333,21.5555555555556,1,3,5],
                        78:[3,8,21.5555555555556,22.2222222222222,1,3,0],
                        79:[3,8,22.2222222222222,23.3333333333333,1,3,1],
                        80:[3,8,23.3333333333333,24.1111111111111,1,3,2],
                        81:[3,8,24.1111111111111,26.1111111111111,1,3,7],
                        82:[3,8,26.1111111111111,27.8888888888889,1,3,4],
                        83:[3,8,27.8888888888889,30,1,3,6],
                        84:[4,9,0,0.777777777777778,0,8,8],
                        85:[4,9,0.777777777777778,3,0,8,5],
                        86:[4,9,3,3.66666666666667,0,8,0],
                        87:[4,9,3.66666666666667,4.77777777777778,0,8,1],
                        88:[4,9,4.77777777777778,5.55555555555556,0,8,2],
                        89:[4,9,5.55555555555556,7.55555555555556,0,8,7],
                        90:[4,9,7.55555555555556,9.33333333333333,0,8,4],
                        91:[4,9,9.33333333333333,11.4444444444444,0,8,6],
                        92:[4,9,11.4444444444444,13.3333333333333,0,8,3],
                        93:[4,10,13.3333333333333,15.5555555555556,0,5,5],
                        94:[4,10,15.5555555555556,16.2222222222222,0,5,0],
                        95:[4,10,16.2222222222222,17.3333333333333,0,5,1],
                        96:[4,10,17.3333333333333,18.1111111111111,0,5,2],
                        97:[4,10,18.1111111111111,20.1111111111111,0,5,7],
                        98:[4,10,20.1111111111111,21.8888888888889,0,5,4],
                        99:[4,10,21.8888888888889,24,0,5,6],
                        100:[4,10,24,25.8888888888889,0,5,3],
                        101:[4,10,25.8888888888889,26.6666666666667,0,5,8],
                        102:[4,11,26.6666666666667,27.3333333333333,0,0,0],
                        103:[4,11,27.3333333333333,28.4444444444444,0,0,1],
                        104:[4,11,28.4444444444444,29.2222222222222,0,0,2],
                        105:[4,11,29.2222222222222,30,0,0,7],
                        106:[5,11,0,1.22222222222222,3,0,7],
                        107:[5,11,1.22222222222222,3,3,0,4],
                        108:[5,11,3,5.11111111111111,3,0,6],
                        109:[5,11,5.11111111111111,7,3,0,3],
                        110:[5,11,7,7.77777777777778,3,0,8],
                        111:[5,11,7.77777777777778,10,3,0,5],
                        112:[5,12,10,11.1111111111111,3,1,1],
                        113:[5,12,11.1111111111111,11.8888888888889,3,1,2],
                        114:[5,12,11.8888888888889,13.8888888888889,3,1,7],
                        115:[5,12,13.8888888888889,15.6666666666667,3,1,4],
                        116:[5,12,15.6666666666667,17.7777777777778,3,1,6],
                        117:[5,12,17.7777777777778,19.6666666666667,3,1,3],
                        118:[5,12,19.6666666666667,20.4444444444444,3,1,8],
                        119:[5,12,20.4444444444444,22.6666666666667,3,1,5],
                        120:[5,12,22.6666666666667,23.3333333333333,3,1,0],
                        121:[5,13,23.3333333333333,24.1111111111111,3,2,2],
                        122:[5,13,24.1111111111111,26.1111111111111,3,2,7],
                        123:[5,13,26.1111111111111,27.8888888888889,3,2,4],
                        124:[5,13,27.8888888888889,30,3,2,6],
                        125:[6,13,0,1.88888888888889,5,2,3],
                        126:[6,13,1.88888888888889,2.66666666666667,5,2,8],
                        127:[6,13,2.66666666666667,4.88888888888889,5,2,5],
                        128:[6,13,4.88888888888889,5.55555555555556,5,2,0],
                        129:[6,13,5.55555555555556,6.66666666666667,5,2,1],
                        130:[6,14,6.66666666666667,8.66666666666667,5,7,7],
                        131:[6,14,8.66666666666667,10.4444444444444,5,7,4],
                        132:[6,14,10.4444444444444,12.5555555555556,5,7,6],
                        133:[6,14,12.5555555555556,14.4444444444444,5,7,3],
                        134:[6,14,14.4444444444444,15.2222222222222,5,7,8],
                        135:[6,14,15.2222222222222,17.4444444444444,5,7,5],
                        136:[6,14,17.4444444444444,18.1111111111111,5,7,0],
                        137:[6,14,18.1111111111111,19.2222222222222,5,7,1],
                        138:[6,14,19.2222222222222,20,5,7,2],
                        139:[6,15,20,21.7777777777778,5,4,4],
                        140:[6,15,21.7777777777778,23.8888888888889,5,4,6],
                        141:[6,15,23.8888888888889,25.7777777777778,5,4,3],
                        142:[6,15,25.7777777777778,26.5555555555556,5,4,8],
                        143:[6,15,26.5555555555556,28.7777777777778,5,4,5],
                        144:[6,15,28.7777777777778,29.4444444444444,5,4,0],
                        145:[6,15,29.4444444444444,30,5,4,1],
                        146:[7,15,0,0.555555555555556,2,4,1],
                        147:[7,15,0.555555555555556,1.33333333333333,2,4,2],
                        148:[7,15,1.33333333333333,3.33333333333333,2,4,7],
                        149:[7,16,3.33333333333333,5.44444444444444,2,6,6],
                        150:[7,16,5.44444444444444,7.33333333333333,2,6,3],
                        151:[7,16,7.33333333333333,8.11111111111111,2,6,8],
                        152:[7,16,8.11111111111111,10.3333333333333,2,6,5],
                        153:[7,16,10.3333333333333,11,2,6,0],
                        154:[7,16,11,12.1111111111111,2,6,1],
                        155:[7,16,12.1111111111111,12.8888888888889,2,6,2],
                        156:[7,16,12.8888888888889,14.8888888888889,2,6,7],
                        157:[7,16,14.8888888888889,16.6666666666667,2,6,4],
                        158:[7,17,16.6666666666667,18.5555555555556,2,3,3],
                        159:[7,17,18.5555555555556,19.3333333333333,2,3,8],
                        160:[7,17,19.3333333333333,21.5555555555556,2,3,5],
                        161:[7,17,21.5555555555556,22.2222222222222,2,3,0],
                        162:[7,17,22.2222222222222,23.3333333333333,2,3,1],
                        163:[7,17,23.3333333333333,24.1111111111111,2,3,2],
                        164:[7,17,24.1111111111111,26.1111111111111,2,3,7],
                        165:[7,17,26.1111111111111,27.8888888888889,2,3,4],
                        166:[7,17,27.8888888888889,30,2,3,6],
                        167:[8,18,0,0.777777777777778,4,8,8],
                        168:[8,18,0.777777777777778,3,4,8,5],
                        169:[8,18,3,3.66666666666667,4,8,0],
                        170:[8,18,3.66666666666667,4.77777777777778,4,8,1],
                        171:[8,18,4.77777777777778,5.88888888888889,4,8,2],
                        172:[8,18,5.88888888888889,7.55555555555556,4,8,7],
                        173:[8,18,7.55555555555556,9.33333333333333,4,8,4],
                        174:[8,18,9.33333333333333,11.4444444444444,4,8,6],
                        175:[8,18,11.4444444444444,13.3333333333333,4,8,3],
                        176:[8,19,13.3333333333333,15.5555555555556,4,5,5],
                        177:[8,19,15.5555555555556,16.2222222222222,4,5,0],
                        178:[8,19,16.2222222222222,17.3333333333333,4,5,1],
                        179:[8,19,17.3333333333333,18.1111111111111,4,5,2],
                        180:[8,19,18.1111111111111,20.1111111111111,4,5,7],
                        181:[8,19,20.1111111111111,21.8888888888889,4,5,4],
                        182:[8,19,21.8888888888889,24,4,5,6],
                        183:[8,19,24,25.8888888888889,4,5,3],
                        184:[8,19,25.8888888888889,26.6666666666667,4,5,8],
                        185:[8,20,26.6666666666667,27.3333333333333,4,0,0],
                        186:[8,20,27.3333333333333,28.4444444444444,4,0,1],
                        187:[8,20,28.4444444444444,29.2222222222222,4,0,2],
                        188:[8,20,29.2222222222222,30,4,0,7],
                        189:[9,20,0,1.22222222222222,6,0,7],
                        190:[9,20,1.22222222222222,3,6,0,4],
                        191:[9,20,3,5.11111111111111,6,0,6],
                        192:[9,20,5.11111111111111,7,6,0,3],
                        193:[9,20,7,7.77777777777778,6,0,8],
                        194:[9,20,7.77777777777778,10,6,0,5],
                        195:[9,21,10,11.1111111111111,6,1,1],
                        196:[9,21,11.1111111111111,11.8888888888889,6,1,2],
                        197:[9,21,11.8888888888889,13.8888888888889,6,1,7],
                        198:[9,21,13.8888888888889,15.6666666666667,6,1,4],
                        199:[9,21,15.6666666666667,17.7777777777778,6,1,6],
                        200:[9,21,17.7777777777778,19.6666666666667,6,1,3],
                        201:[9,21,19.6666666666667,20.7777777777778,6,1,8],
                        202:[9,21,20.7777777777778,22.6666666666667,6,1,5],
                        203:[9,21,22.6666666666667,23.3333333333333,6,1,0],
                        204:[9,22,23.3333333333333,24.1111111111111,6,2,2],
                        205:[9,22,24.1111111111111,26.1111111111111,6,2,7],
                        206:[9,22,26.1111111111111,27.8888888888889,6,2,4],
                        207:[9,22,27.8888888888889,30,6,2,6],
                        208:[10,22,0,1.88888888888889,6,2,3],
                        209:[10,22,1.88888888888889,2.66666666666667,6,2,8],
                        210:[10,22,2.66666666666667,4.88888888888889,6,2,5],
                        211:[10,22,4.88888888888889,5.55555555555556,6,2,0],
                        212:[10,22,5.55555555555556,6.67222222222222,6,2,1],
                        213:[10,23,6.67222222222222,8.66666666666667,6,7,7],
                        214:[10,23,8.66666666666667,10.4444444444444,6,7,4],
                        215:[10,23,10.4444444444444,12.5555555555556,6,7,6],
                        216:[10,23,12.5555555555556,14.4444444444444,6,7,3],
                        217:[10,23,14.4444444444444,15.2222222222222,6,7,8],
                        218:[10,23,15.2222222222222,17.4444444444444,6,7,5],
                        219:[10,23,17.4444444444444,18.1111111111111,6,7,0],
                        220:[10,23,18.1111111111111,19.2222222222222,6,7,1],
                        221:[10,23,19.2222222222222,20,6,7,2],
                        222:[10,24,20,21.7777777777778,6,4,4],
                        223:[10,24,21.7777777777778,23.8888888888889,6,4,6],
                        224:[10,24,23.8888888888889,25.7777777777778,6,4,3],
                        225:[10,24,25.7777777777778,26.5555555555556,6,4,8],
                        226:[10,24,26.5555555555556,28.7777777777778,6,4,5],
                        227:[10,24,28.7777777777778,29.4444444444444,6,4,0],
                        228:[10,24,29.4444444444444,30,6,4,1],
                        229:[11,24,0,0.555555555555556,4,4,1],
                        230:[11,24,0.555555555555556,1.33333333333333,4,4,2],
                        231:[11,24,1.33333333333333,3.33333333333333,4,4,7],
                        232:[11,25,3.33333333333333,5.44444444444444,4,6,6],
                        233:[11,25,5.44444444444444,7.33333333333333,4,6,3],
                        234:[11,25,7.33333333333333,8.11111111111111,4,6,8],
                        235:[11,25,8.11111111111111,10.3333333333333,4,6,5],
                        236:[11,25,10.3333333333333,11,4,6,0],
                        237:[11,25,11,12.1111111111111,4,6,1],
                        238:[11,25,12.1111111111111,12.8888888888889,4,6,2],
                        239:[11,25,12.8888888888889,14.8888888888889,4,6,7],
                        240:[11,25,14.8888888888889,16.6666666666667,4,6,4],
                        241:[11,26,16.6666666666667,18.5555555555556,4,3,3],
                        242:[11,26,18.5555555555556,19.3333333333333,4,3,8],
                        243:[11,26,19.3333333333333,21.5555555555556,4,3,5],
                        244:[11,26,21.5555555555556,22.2222222222222,4,3,0],
                        245:[11,26,22.2222222222222,23.3333333333333,4,3,1],
                        246:[11,26,23.3333333333333,24.1111111111111,4,3,2],
                        247:[11,26,24.1111111111111,26.1111111111111,4,3,7],
                        248:[11,26,26.1111111111111,27.8888888888889,4,3,4],
                        249:[11,26,27.8888888888889,30,4,3,6],
}
_saham_list = ['punya','vidya','yasas','mitra','mahatmaya','asha','samartha','bhratri','gaurava','pithri','rajya','maathri',
               'puthra','jeeva','karma','roga','kali','sastra','bandhu','mrithyu','paradesa','artha','paradara','vanika',
               'karyasiddhi','vivaha','santapa','sraddha','preethi','jadya','vyaapaara','sathru','jalapatna','bandhana',
               'apamrithyu','laabha']
"""
# Tuples in the order Pachaka, Bhodhaka, Kaarka and Vedhaka.
# First element planet is Pachaka etc if it is in the 2nd element house from the planet
# For Example 0:[(6,6),(2,7),(4,9),(5,11)]
    Saturn is Sun's Pachaka if it is 6th house from Sun - 'E' stands for inimical relation
    Mars is Sun's Bodhaka if it is in 7th house from Sun
    Jupiter is Sun's Karaka if it is in 9th house from Sun
    Venus is Sun's Vedhaka if it is in 11th house from Sun
"""
paachakaadi_sambhandha = {0:[(6,6,'E'),(2,7,''),(4,9,''),(5,11,'')],1:[(5,7,''),(2,9,''),(6,11,''),(0,3,'')],
                         2:[(0,2,''),(1,6,''),(6,11,''),(3,12,'E')],3:[(1,2,''),(4,4,''),(5,5,''),(2,3,'E')],
                         4:[(6,6,'E'),(2,5,''),(1,7,''),(0,12,'')],5:[(1,2,''),(3,6,''),(0,12,''),(6,4,'E')],
                         6:[(5,3,''),(1,11,''),(4,6,'E'),(2,7,'')]
                         }
paachaadi_relations = ['paachaka','bodhaka','kaaraka','vedhaka']
# Pushkara bhaga = specific degress at which each sign is beneficial
# Pushkara navamsa = 3.20 degree range at which each sign is beneficial
pushkara_navamsa = [20,6+40/60,16+40/60,0,20,6+40/60,16+40/60,0,20,6+40/60,16+40/60,0]
pushkara_bhagas = [21,14,24,7,21,14,24,7,21,14,24,7]
pushkara_bhaga_jathaka_paarijaatha = [21,14,18,8,19,9,24,11,23,14,19,9]
graha_yudh_criteria_1 = 20 # planet latitudes are within 20 seconds
graha_yudh_criteria_2 = 1 # planet latitudes are within 1 degree
graha_yudh_criteria_3 = 2 # planet latitudes are within 2 degrees
planetary_aspect_ratios_on_houses = [
    [0,0,0.25,0.75,0.5,0,1.0,0.75,0.5,0.25,0,0], #Sun
    [0,0,0.25,0.75,0.5,0,1.0,0.75,0.5,0.25,0,0], #Moon
    [0,0,0.5,1.0,0.75,0,0.25,1.0,0.75,0.5,0,0], #Mars
    [0,0,0.25,0.75,0.5,0,1.0,0.75,0.5,0.25,0,0], #Mercury
    [0,0,0.75,0.25,1.0,0,0.5,0.25,1.0,0.75,0,0], #Jupiter
    [0,0,0.25,0.75,0.5,0,1.0,0.75,0.5,0.25,0,0], #Venus
    [0,0,1.0,0.5,0.25,0,0.75,0.5,0.25,1.0,0,0], #Saturn
    [1,1,1,1,1,1,1,1,1,1,1,1], # Rahu
    [1,1,1,1,1,1,1,1,1,1,1,1] #Ketu
]
 # Sun in 12th house, Moon/8th,Ma/7th,Me/7th,Ju/3rd,Ve/6th,Sa/1st,Ra/9th house,Ke/4th
marana_karaka_sthana_of_planets= [12,8,7,7,3,6,1,9,4]
# Latta Stars of planets = (nth star from planet's star based on its longitude, forward=1/backward=-1)
latta_stars_of_planets = [(12,1),(22,-1),(3,1),(7,-1),(6,1),(5,-1),(8,1),(9,-1),(9,-1)]
# Drekkana Table for each rasi with drekkana type for each drekkana hora
# Drekkana hora is 1st part 0-10 deg, 2nd part 10-20 and 3rd 20-30
# Drekkana types are Ayudha (1), Paasa (2), Nigala (3), Sarpa (4) Pakshi (5) and Chatushpada (6). And None = 0
# For example: Ar = Ayudha if rasi long in 0-10deg, Chatushpada if in 10-20 deg, Ayudha if rasi long in 20-30 deg
graha_drekkana_types = ['','ayudha','paasa','nigala','sarpa','pakshi','chatushpaada']
drekkana_table = [(1,6,1),(0,6,4),(0,1,1),(6,0,5),(4,0,1),(0,1,0),(0,4,1),(5,2,6),(1,0,1),(3,0,0),(4,0,0),(0,0,5)]
drekkana_table_bvraman = [(1,5,0),(0,6,6),(0,5,1),(6,4,4),(5,1,6),(0,1,5),(0,0,6),(4,4,6),(6,0,1),(2,0,1),(0,0,0),(0,0,0)]
# 3d List
# 1st 2d list is Vulture Last 2d list is Peacock
# 2d List: Each row is day (Sunday to Saturday) and Each column is 5 divisions of day time (sunrise to sunset)
# Activities: 1- Rule. 2- Eat. 3- Walk. 4- Sleep. 5- Die
pancha_pakshi_sukla_paksha_ruling_day_timings = [
    [[2,3,1,4,5],[5,2,3,1,4],[2,3,1,4,5],[5,2,3,1,4],[4,5,2,3,1],[1,4,5,2,3],[3,1,4,5,2] ], # Vulture
    ]
pancha_pakshi_sukla_paksha_ruling_night_timings = [
    [[5,3,4,2,1],[3,4,2,1,5],[5,3,4,2,1],[3,4,2,1,5],[4,2,1,5,3],[2,1,5,3,4],[1,5,3,4,2] ], # Vulture
    ]
pancha_pakshi_krishna_paksha_ruling_day_timings = [
    [[],[],[],[],[],[],[] ], # Vulture
    ]
pancha_pakshi_krishna_paksha_ruling_night_timings = [
    [[],[],[],[],[],[],[] ], # Vulture
    ]
#0:Udveg (Bad), 1:Chara(Good), 2:Laabha (Good), 3:Amrit(Good), 4:Kaala(Bad), 5:Shubha (Good), 6:Rog(Bad)
# Rows = Days Columns - choghadiyas
gauri_choghadiya_types = ['0:Udveg (Bad)','1:Chara(Good)','2:Laabha (Good)','3:Amrit(Good)','4:Kaala(Bad)','5:Shubha (Good)','6:Rog(Bad)']
gauri_choghadiya_day_table = [[0,1,2,3,4,5,6,0], # Sunday
                          [3,4,5,6,0,1,2,3], # Monday
                          [6,0,1,2,3,4,5,6], # Tuesday
                          [2,3,4,5,6,0,1,2], # Wednesday
                          [5,6,0,1,2,3,4,5], # Thursday
                          [1,2,3,4,5,6,0,1], # Friday
                          [4,5,6,0,1,2,3,4] # Saturday
                          ]
gauri_choghadiya_night_table = [[5,3,1,6,4,2,0,5], # Sunday
                          [1,6,4,2,0,5,3,1], # Monday
                          [4,2,0,5,3,1,6,4], # Tuesday
                          [0,5,3,1,6,4,2,0], # Wednesday
                          [3,1,6,4,2,0,5,3], # Thursday
                          [6,4,2,0,5,3,1,6], # Friday
                          [2,0,5,3,1,6,4,2] # Saturday
                          ]
#Rows = Days, Columns = Hora (12 hora for day and 12 hora for night)
#Hora = day/night length / 12.
#Each element is the planet that gives hora result
#Moon,Mercury,Jupiter and Venus are good
#order of hora results by planets [0:'Vigorous (Bad)',1:'Gentle (Good)' 2:'Aggressive (Bad)',3:'Quick (Good)',
#4:'Fruitful (Good), 5:'Beneficial (Good), 6:'Sluggish (Bad)'
shubha_hora_day_table = [[0, 1, 2, 3, 4, 5, 6],[5, 6, 0, 1, 2, 3, 4],[3, 4, 5, 6, 0, 1, 2],[1, 2, 3, 4, 5, 6, 0],
                         [6, 0, 1, 2, 3, 4, 5],[4, 5, 6, 0, 1, 2, 3],[2, 3, 4, 5, 6, 0, 1],[0, 1, 2, 3, 4, 5, 6],
                         [5, 6, 0, 1, 2, 3, 4],[3, 4, 5, 6, 0, 1, 2],[1, 2, 3, 4, 5, 6, 0],[6, 0, 1, 2, 3, 4, 5]
                        ]
shubha_hora_night_table = [[4, 5, 6, 0, 1, 2, 3],[2, 3, 4, 5, 6, 0, 1],[0, 1, 2, 3, 4, 5, 6],[5, 6, 0, 1, 2, 3, 4],
                            [3, 4, 5, 6, 0, 1, 2],[1, 2, 3, 4, 5, 6, 0],[6, 0, 1, 2, 3, 4, 5],[4, 5, 6, 0, 1, 2, 3],
                            [2, 3, 4, 5, 6, 0, 1],[0, 1, 2, 3, 4, 5, 6],[5, 6, 0, 1, 2, 3, 4],[3, 4, 5, 6, 0, 1, 2]
                        ]
# First element is starting time for amrita gadiya and second element starting time for varjyam for each star
# First tuple is Aswini and Last one for Revathi
# AmritaGadiya/Varjyam Starting time = starting time of star * factor from below table/24
# Duration = Duration of Star * 1.6/24 

amrita_gadiya_varjyam_star_map = [(16.8,20),(19.2,9.6),(21.6,12),(20.8,16),(15.2,5.6),(14,8.4),(21.6,12),(17.6,8),
                                  (22.4,12.8),(21.6,12),(17.6,8),(16.8,7.2),(18,8.4),(17.6,8),(15.2,5.6),(15.2,5.6),
                                  (13.6,4),(15.2,5.6),(17.6,(8,22.4)),(19.2,9.6),(17.6,8),(13.6,4),(13.6,4),
                                  (16.8,7.2),(16,6.4),(19.2,9.6),(21.6,12)]

anandhaadhi_yoga_names = ['anand','kaal','dhumra','prajapathi','soumya','dhwanksha','dhwaja','shreevathsa','vajra',
                          'mudgar','chathra','mithra','mansa','padhma','lumbkak','uthpath','mrithyu','kaan',
                          'siddhi','shubha','amruth','musal','gada','maathanga','raakshasa','chara','sthira',
                          'vrudh']
_get_abhijith_order_of_stars = lambda start_nak=1: \
            [*range(start_nak,21)]+[27]+[*range(21,27)]+[*range(start_nak)] if start_nak < 21 else \
            [*range(start_nak,27)]+[*range(21)]+[27]+[*range(21,start_nak)]
anandhaadhi_yoga_day_star_list = [_get_abhijith_order_of_stars(0), # Sunday
                                  _get_abhijith_order_of_stars(4), # Monday
                                  _get_abhijith_order_of_stars(7), # Tuesday
                                  _get_abhijith_order_of_stars(12),# Wednesday
                                  _get_abhijith_order_of_stars(16),# Thursday
                                  _get_abhijith_order_of_stars(20),# Friday
                                  _get_abhijith_order_of_stars(23) # Saturday
                                  ]
#0=Sathva 1=Rajas 2=Thamas index of each value element is Day
triguna_names = ['sathva','rajas','thamas']
triguna_days_dict = {1.3:[2,0,1,2,0,1,2],3:[0,1,2,0,1,2,0],4.5:[1,2,0,1,2,0,1],6:[2,0,1,2,0,1,2],7.5:[0,1,2,0,1,2,0],
                     9:[1,2,0,1,2,0,1],10.5:[2,0,1,2,0,1,2],12:[0,1,2,0,1,2,0],13.3:[1,2,0,1,2,0,1],15:[2,0,1,2,0,1,2],
                     16.5:[0,1,2,0,1,2,0],18:[1,2,0,1,2,0,1],19.5:[2,0,1,2,0,1,2],21:[0,1,2,0,1,2,0],22.5:[1,2,0,1,2,0,1],
                     24:[2,0,1,2,0,1,2]}
""" ========== Tamil Yogam Constants ========= """
tamil_yoga_names = ['siddha', 'prabalarishta', 'marana', 'amirtha','amirtha_siddha','mrithyu','daghda','yamaghata',
                    'uthpatha','sarvartha_siddha']
### Ref: https://tuningmymelody.blogspot.com/2023/04/the-type-of-yogas-and-muhurtha-yogas.html
tamil_basic_yoga_list=[[0,1,0,0,0,0,0,0,0,2,0,3,0,0,0,2,2,2,3,0,3,3,2,0,0,3,3], #Sunday
                       [0,0,2,3,0,0,3,0,0,2,0,0,0,1,3,2,0,0,0,2,2,3,0,0,0,0,0], #Monday
                       [0,0,0,3,0,2,0,0,0,0,0,3,0,0,0,2,0,2,3,0,1,0,0,2,2,3,0], #Tuesday
                       [2,0,3,0,0,0,0,0,0,0,3,3,2,0,0,0,0,0,2,3,3,0,1,0,3,0,2], #Wednesday
                       [3,0,2,2,2,2,3,0,0,3,0,2,0,0,3,0,0,1,0,0,0,0,0,2,0,0,0], #Thursday
                       [3,0,0,2,0,0,0,2,2,2,0,0,3,0,0,0,0,2,3,1,0,2,0,0,0,0,0], #Friday
                       [0,0,0,3,0,0,0,0,2,3,0,2,2,2,0,0,0,0,0,0,0,0,0,3,2,0,1]  #Saturday
                      ]
#Ref: https://sringeri.net/wp-content/uploads/2024/04/2024_25_krodhi_tamil_panchanga_sringeri.pdf
tamil_basic_yoga_sringeri_panchanga_list=[
        [0,0,0,3,0,0,0,0,0,2,0,3,3,0,0,2,2,2,3,0,3,3,2,0,0,3,3], #Sunday
        [0,0,2,3,3,0,3,0,0,2,0,0,0,0,3,2,0,0,0,0,2,3,0,0,2,0,0], #Monday
        [0,0,0,3,0,2,0,0,0,0,0,3,0,0,0,2,0,0,3,0,0,0,0,2,2,3,0], #Tuesday
        [2,0,3,0,0,0,0,0,0,0,3,3,2,0,0,0,0,0,2,3,3,0,1,0,3,0,2], #Wednesday
        [3,0,2,2,2,2,3,3,0,3,0,2,0,0,3,0,0,0,0,0,0,0,0,2,0,0,0], #Thursday
        [3,0,0,2,0,0,0,2,2,2,0,0,3,0,0,0,0,2,3,0,0,2,0,0,0,0,3], #Friday
        [0,0,3,3,0,0,0,0,2,3,0,2,2,2,3,0,0,0,0,0,0,0,0,3,2,0,2]  #Saturday
        ]
amrita_siddha_yoga_dict = {0:12,1:4,2:0,3:16,4:7,5:26,6:3} # day:star
mrityu_yoga_dict = {0:16, 1:20, 2:23, 3:0, 4:4, 5:17, 6:12} # day:star
daghda_yoga_dict = {0:1,1:13,2:20,3:22, 4:11,5:8,6:26}# day:star
yamaghata_yoga_dict = {0:9,1:15,2:5,3:18,4:2,5:3,6:12}# day: star
utpata_yoga_dict = {0:15, 1:19, 2:22, 3:26, 4:3, 5:7, 6:11}#day:star

sarvartha_siddha_yoga = {0:(12,18,20,11,25,0,7),1:(21,3,4,7,16),2:(0,25,2,8),3:(3,16,12,2,4),4:(26,16,0,6,7),
                       5:(26,16,0,6,21),6:(21,3,14)}# day:star

use_24hour_format_in_to_dms = True # V4.2.6
""" ============================================"""
tithi_deities = ['kaameshwari','bhaagamaalini','nithyaklinna','bherunda','vaahinivaasini','mahaavajreshwari',
                 'shivadoothi','thwaritha','kulasundari','nithya','neelapathaka','vijaya','sarvamangala',
                 'jwaalamaalini','chithra','shodhashi'] ## Last 2 are Amavasai and Pournami
#(Yogam Ruling Planet / Yoga Point , Avayogi Planet)
yogam_lords_and_avayogis = [(6,1),(3,2),(8,7),(5,4),(0,6),(1,3),(2,8),(7,5),(4,0),
                            (6,1),(3,2),(8,7),(5,4),(0,6),(1,3),(2,8),(7,5),(4,0),
                            (6,1),(3,2),(8,7),(5,4),(0,6),(1,3),(2,8),(7,5),(4,0)
                            ]
use_planet_speed_for_panchangam_end_timings = True # True # Changed to False in V4.6.0
#0=East, 1=South, 2=West, 3=North
disha_shool_map = [2,0,3,3,1,2,0]#Sunday to Saturday

#Ref:https://www.astrodivine.com/chandra_bhedi_plot.htm
#0=East, 1=South, 2=West, 3=North, 4=South West, 5=North West, 6=North East 7=South East
yogini_vaasa_tithi_map = [0,3,7,5,1,2,5,6,0,3,7,5,1,2,5,0,3,7,5,1,2,5,6,0,3,7,5,1,2,6]
periods_of_the_day = ['purvaanha','madhyannha','aparanha','saayankaala','pradosha','nishitha','triyaama','ushaa']
muhurthas_of_the_day = {'rudra':0,'aahi':0,'mithra':1,'pithra':0,'vasu':1,'varaaha':1,'vishvedeva':1,'vidhi':1,
                         'sathamukhi':1,'puruhootha':0,'vaahini':0,'nakthanakaara':0,'varuna':1,'aaryaman':1,'bhaga':0,
                         'girisha':1,'ajapaadha':0,'aahirbhudhnya':1,'pushya':1,'ashvini':1,'yama':0,'agni':1,
                         'vidharth':1,'kanda':1,'adhithi':1,'jeeva':1,'vishnu':1,'dhyumadadhyuthi':1,
                         'brahma':1,'samudhra':1} # 0 - Inauspicious 1=Auspicious
### Tamil month methods: 0=> Ravi Annasamy (sunset/UTC) 1=>V4.3.5 (sunset as starting jd) 2=>Start jd with 10AM
##                       3 => Midday, UTC
class TAMIL_MONTH_METHOD:
    BASED_ON_LOCAL_10AM = 0
    BASED_ON_SUNSET_TIME = 1
    BASED_ON_BIRTH_TIME = 2
    FLEXIBLE_METHOD = 3
tamil_month_method = TAMIL_MONTH_METHOD.FLEXIBLE_METHOD
#### Enable / Disable World City Checking
check_database_for_world_cities = True
use_internet_for_location_check = True
one_arc_second = 1.0/3600.
""" To match Pramaadhi (North Indian) or Prabhava (South Indian) Set ONLY ONE of the below to True.
    Or If you dont like this experiment set both to False
    This means before Kali Year 4099 - i.e. 908AD - The South And North do not share year names
"""
force_kali_start_year_for_years_before_kali_year_4009 = True
kali_start_year = 13 # 13 (Pramaadhi) North or 1 (Prabhava) for South
# Special Tithis
special_tithis = ['janma','dhana','bhrartri','matri','putra','satru','kalatra','mrutyu','bhagya','karma','laabha','vyaya']
skip_using_girls_varna_for_minimum_tamil_porutham = True # V4.5.5
benefic_signs = [TAURUS, GEMINI, CANCER, VIRGO, LIBRA, SAGITTARIUS, PISCES]
malefic_signs = [ARIES, LEO, SCORPIO, CAPRICORN, AQUARIUS]
show_yoga_caution_message = True
ashtakavarga_rasi_owners=[4,3,(0,7),(2,5),(8,11),(1,6),(9,10)]
## Based on PVR's book value an alternate is added
## But still rasi pinda differs by book value for Saturn
## The Alternate is picked up from Horosoft
### Ref: https://www.horosoft.net/learnastro_Zodiacal_Planetary_Products.html
### Ref: https://astrobix.com/learn/360-shodhya-pinda-of-ashtakavarga.html
class RASIMANA_MULTIPLIER_OPTION:
    RASIMANA_PVR = 1
    RASIMANA_ALTERNATE = 2
RASIMANA_MULTIPLIERS = {
    RASIMANA_MULTIPLIER_OPTION.RASIMANA_PVR: (7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12),
    RASIMANA_MULTIPLIER_OPTION.RASIMANA_ALTERNATE: (7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12),
}
ashtakavarga_rasimana_multiplier_option = RASIMANA_MULTIPLIER_OPTION.RASIMANA_ALTERNATE
ashtakavarga_rasimana_multipliers = RASIMANA_MULTIPLIERS[ashtakavarga_rasimana_multiplier_option]
ashtakavarga_grahamana_multipliers = [5,5,8,5,10,7,5]
planet_hora_dict_for_odd_even_signs = {0:(4,4),1:(3,3),2:(7,0),3:(5,2),4:(11,8),5:(6,1),6:(10,9),7:(10,10),8:(4,4)}
panchamsa_odd_signs = [0,10,8,2,6]
panchamsa_even_signs = [1,5,11,9,7]
vimsopaka_bala_scores = [5,7,10,15,18]
KP_lord_fractions = [7/120, 20/120,6/120,10/120,7/120,18/120,16/120,19/120,17/120]
dosha_manglik_houses = [4,7,8,12]
kalathra_dosha_houses = [HOUSE_1,HOUSE_2,HOUSE_4,HOUSE_7,HOUSE_8,HOUSE_12]
varga_viswa_scores = [5,7,10,15,18]
western_planets = [URANUS_ID, NEPTUNE_ID,PLUTO_ID]
sapthavargaja_factors = [1, 2, 3, 7, 9, 12, 30]
dreshkon_bala_list = [(0,2,4),(3,6),(1,5)]
dig_bala_powerless_houses_of_planets = [3,9,3,6,6,9,0]
abdahipathi_weekdays = [2,3,4,5,6,0,1]
hora_bala_hora_order = [6,4,2,0,5,3,1]
shad_bala_factors = [5,6,5,7,6.5,5.5,5]
subha_asubha_factors_dict = {12:(0,0.5),11:(0.5,0.75),10:(2/3,5/6),9:(3/4,7/8),8:(4/5,9/10),7:(5/6,11/12)}
check_yogas_on_all_divisional_charts = False
# 1st house from Sun, 2nd house from jupiter etc...
naisargika_karakas = [SUN_ID, JUPITER_ID, MARS_ID, MOON_ID, JUPITER_ID, MARS_ID, VENUS_ID, SATURN_ID, JUPITER_ID,
                      MERCURY_ID, JUPITER_ID, SATURN_ID]

@unique
class MAHA_DHASA_DEPTH(IntEnum):
    MAHA_DHASA_ONLY   = 1   # Maha only (no Antara)
    ANTARA      = 2   # + Antara (Bhukthi)
    PRATYANTARA = 3   # + Pratyantara
    SOOKSHMA    = 4   # + Sookshma
    PRANA       = 5   # + Prana
    DEHA        = 6   # + Deha-antara
DHASA_DURATION_ROUNDING_TO = 2

""" V4.6.5 - Use the below constants to force and reset owners of Sc/Aq for dhasa calculations """ 
scorpio_owner_for_dhasa_calculations = None # Or MARS_ID Or KETU_ID
aquarius_owner_for_dhasa_calculations = None # Or SATURN_ID or Rahu_ID
use_kp_dictionary_for_lords_calculation = False
_JULIAN_TRANSITION_DAY = 2299149.5 # (1582,10,4) (0,0,0)

# -------------------------------
# Aṣṭakavarga Daśā: fixed choices
# -------------------------------

class ASHTAKAVARGA_DHASA_METHOD:
    """Available AV-based dasha methods (documented in practitioner literature)."""
    BAV_PLANET   = "BAV_PLANET"    # Graha dasha; carriers = Sun..Saturn (0..6); weights = planetary BAV totals
    SAV_SIGN     = "SAV_SIGN"      # Rāśi dasha; carriers = 12 signs (0..11); weights = sign SAV (SAV total=337)
    PINDA_PLANET = "PINDA_PLANET"  # Graha dasha; carriers = Sun..Saturn; weights = Sodhya-Pinda per planet

class ASHTAKAVARGA_DHASA_START_RULE:
    """How to choose which carrier appears first (then rotate base order accordingly)."""
    MAX_STRENGTH        = "MAX_STRENGTH"         # start from highest-weight item
    LAGNA_SIGN          = "LAGNA_SIGN"           # (SAV_SIGN only) start from Lagna sign
    JANMA_RASI          = "JANMA_RASI"           # (SAV_SIGN only) start from Moon sign
    USER_DEFINED_SIGN   = "USER_DEFINED_SIGN"    # (SAV_SIGN only) start from a sign id (0..11)
    USER_DEFINED_PLANET = "USER_DEFINED_PLANET"  # (planet methods only) start from a planet id (0..6)

class ASHTAKAVARGA_DHASA_SEQUENCE_RULE:
    """How to build the base order before rotating with the start rule."""
    STRENGTH_ORDER     = "STRENGTH_ORDER"      # sort carriers by weight high→low
    ZODIACAL_ORDER          = "ZODIACAL_ORDER"           # (SAV_SIGN only) signs 0..11 (Ar..Pi)
    FIXED_SUN_SATURN  = "FIXED_SUN_SATURN"   # (planet methods only) planets 0..6 (Sun..Saturn)

# -------------------------------
# Allowed combinations (policy)
# -------------------------------

# Start-rule compatibility
ASHTAKAVARGA_DHASA_ALLOWED_START_RULES = {
    ASHTAKAVARGA_DHASA_METHOD.BAV_PLANET:   {ASHTAKAVARGA_DHASA_START_RULE.MAX_STRENGTH, 
                                             ASHTAKAVARGA_DHASA_START_RULE.USER_DEFINED_PLANET},
    ASHTAKAVARGA_DHASA_METHOD.PINDA_PLANET: {ASHTAKAVARGA_DHASA_START_RULE.MAX_STRENGTH, 
                                             ASHTAKAVARGA_DHASA_START_RULE.USER_DEFINED_PLANET},
    ASHTAKAVARGA_DHASA_METHOD.SAV_SIGN:     {ASHTAKAVARGA_DHASA_START_RULE.MAX_STRENGTH, 
                                             ASHTAKAVARGA_DHASA_START_RULE.LAGNA_SIGN,
                             ASHTAKAVARGA_DHASA_START_RULE.JANMA_RASI, ASHTAKAVARGA_DHASA_START_RULE.USER_DEFINED_SIGN},
}

# Sequence-rule compatibility
ASHTAKAVARGA_DHASA_ALLOWED_SEQUENCE_RULES = {
    ASHTAKAVARGA_DHASA_METHOD.BAV_PLANET:   {ASHTAKAVARGA_DHASA_SEQUENCE_RULE.STRENGTH_ORDER, 
                                             ASHTAKAVARGA_DHASA_SEQUENCE_RULE.FIXED_SUN_SATURN},
    ASHTAKAVARGA_DHASA_METHOD.PINDA_PLANET: {ASHTAKAVARGA_DHASA_SEQUENCE_RULE.STRENGTH_ORDER, 
                                             ASHTAKAVARGA_DHASA_SEQUENCE_RULE.FIXED_SUN_SATURN},
    ASHTAKAVARGA_DHASA_METHOD.SAV_SIGN:     {ASHTAKAVARGA_DHASA_SEQUENCE_RULE.STRENGTH_ORDER, 
                                             ASHTAKAVARGA_DHASA_SEQUENCE_RULE.ZODIACAL_ORDER},
}
class AAYU_TYPE:
    PINDA = 0
    NISARGA = 1
    AMSA = 2
    NONE = None
class KAALA_TYPE:
    DAWN = 0
    DAY = 1
    DUSK = 2
    NIGHT = 3
class RASHMI_TYPE:
    BPHS_HIGHEST_RAY = 1
    NATURAL_ORDER = 2
    VIMSOTTARI_ORDER = 3
class TARA_TYPE:
    SANJAY_RATH = 1
    PARASARA = 2
class CHARA_TYPE:
    PVN_RAO = 1
    KN_RAO = 2
    IRANGATTI_MALE1 = 3
    IRANGATTI_MALE2 = 4
    MIND_SUTRA = 5
class DRIG_TYPE:
    PVR_PAPER = 1
    PVR_BOOK = 2
class KALACHAKRA_TYPE:
    PVR_BOOK = 1
    SANJAY_RATH = 2
    RAGHAVACHARYA = 3
class MANDOOKA_TYPE:
    SANJAY_RATH = 1
    KN_RAO = 2
class PADHANADHAMSA_TYPE:
    IRANGATTI_RANGACHARYA = 1
    SANJAY_RATH = 2
    PVR_JHORA = 3
# ============================================================
# Dhasa Method defaults
# ============================================================
ASHTAKAVARGA_DHASA_METHOD_DEFAULT = ASHTAKAVARGA_DHASA_METHOD.SAV_SIGN
ASHTAKAVARGA_DHASA_START_RULE_DEFAULT = ASHTAKAVARGA_DHASA_START_RULE.MAX_STRENGTH
ASHTAKAVARGA_DHASA_SEQUENCE_RULE_DEFAULT = ASHTAKAVARGA_DHASA_SEQUENCE_RULE.STRENGTH_ORDER

AAYU_TYPE_DEFAULT = AAYU_TYPE.NONE
RASHMI_TYPE_DEFAULT = RASHMI_TYPE.BPHS_HIGHEST_RAY
TARA_TYPE_DEFAULT = TARA_TYPE.SANJAY_RATH
CHARA_TYPE_DEFAULT = CHARA_TYPE.KN_RAO
DRIG_TYPE_DEFAULT = DRIG_TYPE.PVR_PAPER
KALACHAKRA_TYPE_DEFAULT = KALACHAKRA_TYPE.PVR_BOOK
MANDOOKA_TYPE_DEFAULT = MANDOOKA_TYPE.KN_RAO
PADHANADHAMSA_TYPE_DEFAULT = PADHANADHAMSA_TYPE.IRANGATTI_RANGACHARYA

_chart_names = ['raasi_str','hora_str','drekkanam_str','chaturthamsa_str','panchamsa_str',
              'shashthamsa_str','saptamsam_str','ashtamsa_str','navamsam_str','dhasamsam_str','rudramsa_str',
              'dhwadamsam_str','shodamsa_str','vimsamsa_str','chaturvimsamsa_str','nakshatramsa_str','thrisamsam_str',
              'khavedamsa_str','akshavedamsa_str','sashtiamsam_str','nava_navamsa_str','ashtotharamsa_str',
              'dwadas_dwadasamsa_str','nadiamsa_str','custom_varga_kundali_str','mixed_varga_kundali_str']
_chart_names_upto_d144 = _chart_names[:-2]
_bala_names = ['amsa_ruler_str','sphuta_str','drishti_str','bhava_graha_arudha_str','vimsopaka_bala_str','vaiseshikamsa_bala_str',
               'harsha_pancha_dwadhasa_vargeeya_bala_str','shad_bala_str','bhava_bala_str']
_graha_dhasa_dict = {'vimsottari':[3,10,3,9,1,0,[],[]],'yoga_vimsottari':[3,10,3,9,1,0,[],[]],'rasi_bhukthi_vimsottari':[3,10,3,12,1,0,[],[]],
                     'ashtottari':[3,10,3,8,1,0,[],[]],'tithi_ashtottari':[3,10,3,8,1,0,[],[]],'yogini':[4,8,4,8,1,0,[],[]],
                     'tithi_yogini':[4,8,4,8,1,0,[],[]],'shodasottari':[2,8,4,8,1,0,[],[]],'dwadasottari':[2,8,4,8,1,0,[],[]],
                     'dwisatpathi':[4,8,4,8,1,0,[],[]],'panchottari':[2,8,4,7,1,0,[],[]],'satabdika':[2,8,4,7,1,0,[],[]],
                     'chaturaaseeti_sama':[2,8,4,7,1,0,[],[]],'karana_chaturaaseethi_sama':[2,8,4,7,1,0,[],[]],
                     'shashtisama':[2,8,4,8,1,0,[],[]],'shattrimsa_sama':[6,7,4,8,1,0,[],[]],'naisargika':[2,8,4,6,1,0,[],[]],
                     'tara':[3,10,3,9,1,0,[],[]],'karaka':[4,7.5,4,8,1,0,[],[]],'buddhi_gathi':[5,7,4,9,1,0,[],[]],
                     'kaala':[6,8,3,18,1,0,[],[]],'aayu':[2,8,4,8,1,0,[],[]],'saptharishi_nakshathra':[3,8,3,11,1,0,[],[]],
                     'rashmi':[5,7,4,9,1,0,[],[]],'ashtaka_varga_planet':[5,7,4,9,1,0,[],[]],
                     'ashtaka_varga_pinda':[5,7,4,9,1,0,[],[]],
                     }
dhasa_default_options={'vimsottari':[False,2,1,0,0,0,-1],'yoga_vimsottari':[False,0],
                             'rasi_bhukthi_vimsottari':[True,False,2,1,0,0,0,-1],'ashtottari':[False,5,1,0,0,0,-1],
                       'tithi_ashtottari':[0,False,2],'yogini':[False,6,1,0,0,0,-1],'tithi_yogini':[0,False,0],
                       'shodasottari':[False,7,1,0,0,0,-1],'dwadasottari':[False,26,1,0,0,0,-1],
                       'dwisatpathi':[False,18,1,0,0,0,-1],'panchottari':[False,16,1,0,0,0,-1],
                       'satabdika':[False,26,1,0,0,0,-1],'chaturaaseeti_sama':[False,14,1,0,0,0,-1],
                       'karana_chaturaaseethi_sama':[False,0],'shashtisama':[False,0,1,0,0,0,-1],
                       'shattrimsa_sama':[False,21,1,0,0,0,-1],'naisargika':[True,False,False],
                       'tara':[0,0,-1],'karaka':[0,-1],'buddhi_gathi':[0,-1],'kaala':[],'aayu':[3],
                       'saptharishi_nakshathra':[False,1,0,0,0,-1],'rashmi':[0,-1],'ashtaka_varga_planet':[0,-1],
                       'ashtaka_varga_pinda':[0,-1],
                       'narayana':[0,-1],'lagna_kendraadhi':[0,-1],'sudasa':[0,-1],'drig':[0,-1],
                'niryaana':[0,-1], 'shoola':[0,-1],'karaka_kendraadhi':[0,-1],
                'chara':[0,-1],'lagnamsaka':[0,-1],'padhanadhamsa':[0,-1],
                'mandooka':[0,-1],'sthira':[0,-1],'tara_lagna':[0,-1],
                'brahma':[0,-1],'varnada':[0,-1],'yogardha':[0,-1],
                'navamsa':[0,-1],'paryaaya':[0,-1],'trikona':[0,-1],
                'kalachakra':[0,-1],'chakra':[0,-1],
                'sandhya':[0,-1],'pachaka':[0,-1],
                'raashiyanka':[0,-1],'ashtaka_varga_sign':[0,-1],
                'chathurvidha_lagna_utthara':[0,-1],'chathurvidha_kendra_utthara':[0,-1],
                'chathurvidha_trikona_utthara':[0,-1],'chathurvidha_dasha_utthara':[0,-1],
                }
_rasi_dhasa_dict = {'narayana':[4,7,3,12,1,0,[],[]],'lagna_kendraadhi':[4,7,3,12,1,0,[],[]],'sudasa':[4,7,3,12,1,0,[],[]],'drig':[3,8,4,12,1,0,[],[]],
                'niryaana':[4,7,3,12,1,0,[],[]], 'shoola':[4,7,3,12,1,0,[],[]],'karaka_kendraadhi':[4,7,3,12,1,0,[],[]],
                'chara':[4,7,3,12,1,0,[],[]],'lagnamsaka':[4,7,3,12,1,0,[],[]],'padhanadhamsa':[4,7,3,12,1,0,[],[]],
                'mandooka':[4,7,3,12,1,0,[],[]],'sthira':[4,7,3,12,1,0,[],[]],'tara_lagna':[4,7,3,12,1,0,[],[]],
                'brahma':[4,7,3,12,1,0,[],[]],'varnada':[4,7,3,12,1,0,[],[]],'yogardha':[4,7,3,12,1,0,[],[]],
                'navamsa':[3,7.5,4,12,1,0,[],[]],'paryaaya':[3,7.5,4,12,1,0,[],[]],'trikona':[3,7.5,4,12,1,0,[],[]],
                'kalachakra':[3,8,3,9,1,0,[],[]],'chakra':[3,7.5,4,12,1,0,[],[]],
                'sandhya':[3,7.5,4,12,1,0,[],[]],'pachaka':[3,7.5,4,12,1,0,[],[]],
                'raashiyanka':[3,7.5,4,12,1,0,[],[]],'ashtaka_varga_sign':[3,7.5,4,12,1,0,[],[]],
                'chathurvidha_lagna_utthara':[3,7.5,4,12,1,0,[],[]],'chathurvidha_kendra_utthara':[3,7.5,4,12,1,0,[],[]],
                'chathurvidha_trikona_utthara':[3,7.5,4,12,1,0,[],[]],'chathurvidha_dasha_utthara':[3,7.5,4,12,1,0,[],[]],
                }
_annual_dhasa_dict ={'patyayini':[2,7.5,4,8,1,0,[],[]],'varsha_vimsottari':[3,9,3,9,1,0,[],[]],
                     'varsha_narayana':[5,7.5,4,12,1,0,[],[]],'sudarsana_chakra':[5,7.5,4,12,1,0,[],[]],
                     'panchasvara':[5,7.5,4,12,1,0,[],[]]}
#M=Mandi,G=Gulika,B=BhriguBindu,I=Indu Lagna,P=PranaPadaLagna,T=Triphuta,A1-A12=ArudhaLagna,V1-V12=VarnadaLagna
_everything_considered_for_charts = ['L']+[*range(12)]+["M", "G", "T", "I", "B", "I", "P"]
sub_planet_dict_1 = {'kaala_str':'kaala_longitude','mrityu_str':'mrityu_longitude','artha_str':'artha_praharaka_longitude',
                     'yama_ghantaka_str':'yama_ghantaka_longitude',
                   'gulika_str':'gulika_longitude','maandi_str':'maandi_longitude'}
sub_planet_list_2 = ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu']

_multi_cycle_dhasas = {'narayana':2,'lagna_kendraadhi':2,'karaka_kendraadhi':2,'paryaaya':2,'yogini':3,'tithi_yogini':3,
                       'sudasa':2,'drig':2,'niryaana':2, 'lagnamsaka':2,'dwisatpathi':2,'shashtisama':2,'shattrimsa_sama':3,
                       'buddhi_gathi':2,'rashmi':8,'panchasvara':2,'sudarsana_chakra':9}
""" 
    Following dhasa cycles depend on their methods:
    padhanadhamsa: _dhasa_cycle_count = 1 if _dhasa_method==1 else 2
"""

planet_dhasas = ['vimsottari','yoga_vimsottari','ashtottari','tithi_ashtottari','yogini','tithi_yogini','shodasottari',
                 'dwadasottari','dwisatpathi','panchottari','satabdika','chaturaaseeti_sama','karana_chaturaaseethi_sama','shashtisama',
                 'shattrimsa_sama','tara','buddhi_gathi','kaala','aayu','rashmi','ashtaka_varga_planet',
                 'ashtaka_varga_pinda','naisargika','patyayini']
rasi_dhasas = ['narayana','lagna_kendraadhi','sudasa','drig','niryaana','shoola','karaka_kendraadhi','chara','lagnamsaka','padhanadhamsa',
                'mandooka','sthira','tara_lagna','brahma','varnada','yogardha','navamsa','paryaaya','trikona','kalachakra','chakra','sandhya',
                'pachaka','raashiyanka','ashtaka_varga_sign','chathurvidha_lagna_utthara','chathurvidha_kendra_utthara','chathurvidha_trikona_utthara',
                'chathurvidha_dasha_utthara','sudarsana_chakra']
nakshathra_dhasas = ['saptharishi_nakshathra']
karaka_dhasas = ['karaka']
tuple_dhasas = ['karaka','sudarsana_chakra']
special_dhasas = ['panchasvara']
supported_dhasas = planet_dhasas+rasi_dhasas+nakshathra_dhasas+karaka_dhasas+special_dhasas
# Minimal registry of aliases/variants → 1 canonical module
SPECIAL_DASHA_OPTIONS = {
    "satabdika":{"module":"sataatbika","domain":"graha"},
    "chaturaaseeti_sama":{"module":"chathuraaseethi_sama","domain":"graha"},
    "karana_chaturaaseethi_sama":{"module":"karana_chathuraaseethi_sama","domain":"graha"},
    "panchasvara":{"module":"panchasvara","domain":""},
    "patyayini":{"module":"patyayini","domain":"annual"},
    "sudarsana_chakra":{"module":"sudharsana_chakra","domain":""},
    "pachaka": {
        "module": "sandhya",
        "domain": "raasi",
        "defaults": {"use_pachaka_variation": True},
    },
    "sandhya": {
        "module": "sandhya",
        "domain": "raasi",
        "defaults": {},
    },
    "pinda_aayu": {"module":"aayu", "domain":"graha","defaults":{"aayur_type":AAYU_TYPE.PINDA}},
    "nisarga_aayu": {"module":"aayu", "domain":"graha","defaults":{"aayur_type":AAYU_TYPE.NISARGA}},
    "amsa_aayu": {"module":"aayu", "domain":"graha","defaults":{"aayur_type":AAYU_TYPE.AMSA}},
    # Chathurvidha variants (4 methods) — each is a daśā by itself
    "chathurvidha_lagna_utthara":   {"module": "chathurvidha_utthara", "domain": "raasi", "defaults": {"dhasa_method": 1}},
    "chathurvidha_kendra_utthara":  {"module": "chathurvidha_utthara", "domain": "raasi", "defaults": {"dhasa_method": 2}},
    "chathurvidha_trikona_utthara": {"module": "chathurvidha_utthara", "domain": "raasi", "defaults": {"dhasa_method": 3}},
    "chathurvidha_dasha_utthara":   {"module": "chathurvidha_utthara", "domain": "raasi", "defaults": {"dhasa_method": 4}},

    # Ashtaka-varga with explicit “virtual names” for clarity
    "ashtaka_varga_planet": {"module": "ashtaka_varga", "defaults": {"dhasa_method": ASHTAKAVARGA_DHASA_METHOD.BAV_PLANET}},
    "ashtaka_varga_sign":   {"module": "ashtaka_varga", "defaults": {"dhasa_method": ASHTAKAVARGA_DHASA_METHOD.SAV_SIGN}},
    "ashtaka_varga_pinda":  {"module": "ashtaka_varga", "defaults": {"dhasa_method": ASHTAKAVARGA_DHASA_METHOD.PINDA_PLANET}},

    # The canonical “ashtaka_varga” (no baked-in method; user must pass dhasa_method or your module has a default)
    "ashtaka_varga": {"module": "ashtaka_varga", "defaults": {}},
}
class BHAVA_METHODS(Enum):
    KN_RAO_JHORA_DEFAULT = 1 #KN Rao method (Parashari - Bhava Chalita - cusp-15,cusp,cusp+15)
    PARASHARI = 2 #Parashari - (Whole Sign - Houses 0-30, cusps as calculated from Swiss Ephimeris)
    KP = 3 #KP Method (houses start from cusp and end at cusp)
    BV_RAMAN = 4 #BV Raman (get 1,4,6,10 cusps, equally divided houses. Sandhi/edges 1/2 of adjacent cusps.
    NAKSHATHRA_PAADHA = 5 #Equal Houses based on nakshathra padas (9 padhas each)
    SRIPATHI_PORPHYRIUS = 'O' #Sripathi/Porphyrius - To match Jagannatha Hora,
    SRIPATHI_ASTRODIENST = 'S' #Sripathi/Astrodienst - to match Sripati padhati - book by  V. Subramanya Sastri
    EQUAL_CUSP_ASC1_A = 'A' # Equal (cusp 1 is Ascendant)
    EQUAL_CUSP_ASC1_E = 'E' # Equal (cusp 1 is Ascendant)
    ALCABITUS = 'B' #Alcabitus
    CAMPANUS = 'C'  #Campanus
    AZIMUTHAL = 'H' # azimuthal or horizontal system
    KOCH = 'K'
    MORINUS = 'M'
    PLACIDUS = 'P'
    PORPHYRIUS_SRIPATHI = 'O' #Sripathi/Porphyrius - To match Jagannatha Hora
    REGIOMONTANUS = 'R' #Regiomontanus
    VEHLOW = 'V'  # Vehlow equal (Asc. in middle of house 1)
    AXIAL_ROTATION = 'X' # axial rotation system
    WHOLE_SIGN = 'W'   # Whole Sign - (0,15,30),(30,45,60) - Same as Rasi Chart
    TOPOCENTRIC = 'T'  # Polich/Page (topocentric system)
indian_house_systems = {1 : 'KN Rao method (Parashari - Bhava Chalita - cusp-15,cusp,cusp+15)',
         2 : 'Parashari - (Whole Sign - Houses 0-30, cusps as calculated from Swiss Ephimeris)',
         3 : 'KP Method (houses start from cusp and end at cusp)',
         4 : 'BV Raman (get 1,4,6,10 cusps, equally divided houses. Sandhi/edges 1/2 of adjacent cusps.',
         5 : 'Equal Houses based on nakshathra padas (9 padhas each)',
         'O' : 'Sripathi/Porphyrius - To match Jagannatha Hora',
         'S' : 'Sripathi/Astrodienst - to match Sripati padhati - book by  V. Subramanya Sastri' 
}
include_western_house_systems = True
western_house_systems = {'A':'Equal (cusp 1 is Ascendant)', 'B':'Alcabitus','C':'Campanus', 
                         'E':'Equal (cusp 1 is Ascendant)', 
                         'H':'azimuthal or horizontal system','K':'Koch','M':'Morinus',
                         'O' : 'Sripathi/Porphyrius - To match Jagannatha Hora',
                         'P':'Placidus','R':'Regiomontanus', 
                         'S' : 'Sripathi/Astrodienst - to match Sripati padhati - book by  V. Subramanya Sastri',
                         'V':'Vehlow equal (Asc. in middle of house 1)', 
                         'X':'axial rotation system',
                         'W':'Whole Sign - (0,15,30),(30,45,60) - Same as Rasi Chart',
                         'T':'Polich/Page (topocentric system)'}
available_house_systems = lambda : {**indian_house_systems, **western_house_systems} if include_western_house_systems \
                                else indian_house_systems
""" Bhaava Madhya Methods: = one of the above keys as the value """
bhaava_madhya_method = 1 #'KN Rao method (Parashari - Bhava Chalita - cusp-15,cusp,cusp+15)'
class SANKRANTI_RULE(IntEnum):
    TAMIL_NADU_SUNSET_RULE = 1
    BEFORE_GHATIKAS = 2
    SUNRISE_TO_SUNRISE = 3
class CALENDAR_TYPE(IntEnum):
    SOLAR = 0
    LUNAR_AMANTHA = 1
    LUNAR_PURNIMANTHA = 2
    HIJRI_ISLAMIC = 3
    GREGORIAN = 4
class LUNAR_MONTH_TYPE(IntEnum):
    AMANTHA = 0
    PURNIMANTHA = 1
class NAVA_THARA(IntEnum):
    FROM_LAGNA = 0
    FROM_MOON = 1
include_islamic_calendar = False
class SAVANA_YEAR_METHOD(IntEnum):
    PROSPECTIVE_0_to_360_JHORA = 1
    MIDPOINT = 0
    RETROSPECTIVE_360_to_0 = -1
    DEFAULT = PROSPECTIVE_0_to_360_JHORA
class TRUE_LUNAR_YEAR_METHOD(IntEnum):
    TITHI_BOUNDARY = 1
    TITHI_AT_DOB = 2
    DEFAULT = TITHI_AT_DOB
true_lunar_year_method_default = TRUE_LUNAR_YEAR_METHOD.DEFAULT
get_place_elevation_from_internet = False
class DHASA_YEAR_DURATION(IntEnum):
    MEAN_SIDEREAL_YEAR = 1  # 
    TRUE_SIDEREAL_YEAR = 2
    MEAN_TROPICAL_YEAR = 3
    TRUE_TROPICAL_YEAR = 4
    SAVANA_YEAR = 5
    MEAN_LUNAR_YEAR = 6
    TRUE_LUNAR_YEAR = 7
    GREGORIAN_YEAR = 8
    JHORA_DEFAULT = TRUE_SIDEREAL_YEAR
dhasa_year_duration_default = DHASA_YEAR_DURATION.JHORA_DEFAULT
apply_daylight_savings_correction = True
## If True every UI tab will expanded when saved as PDF. False only Kundali and last 4 tabs expanded.
expand_all_tabs_to_save_as_pdf = False

# ============================================================
# Swiss Ephemeris / astronomy configuration defaults
# ============================================================

# Planet positions:
#   True  -> geocentric
#   False -> topocentric (requires swe.set_topo(lon, lat, alt_m))
PLANET_POSITIONS_GEOCENTRIC = True

# Position type:
#   False -> apparent positions
#   True  -> true positions (FLG_TRUEPOS)
PLANET_POSITIONS_TRUE = True

# These two are only meaningful when PLANET_POSITIONS_TRUE == False
PLANET_POSITIONS_USE_ABERRATION = True
PLANET_POSITIONS_USE_DEFLECTION = True

# Nutation is independent of sidereal/tropical
PLANET_POSITIONS_USE_NUTATION = True

# Rise / Set defaults
RISE_SET_USE_REFRACTION = False
RISE_SET_USE_DISC_CENTER_FOR_RISING = True
RISE_SET_HINDU_RISING = True
# ============================================================
# Optional setters (nice for config binding; direct attr also works)
# ============================================================

def set_planet_positions_geocentric(value: bool) -> None:
    global PLANET_POSITIONS_GEOCENTRIC
    PLANET_POSITIONS_GEOCENTRIC = bool(value)


def set_planet_positions_true(value: bool) -> None:
    global PLANET_POSITIONS_TRUE
    PLANET_POSITIONS_TRUE = bool(value)


def set_planet_positions_use_aberration(value: bool) -> None:
    global PLANET_POSITIONS_USE_ABERRATION
    PLANET_POSITIONS_USE_ABERRATION = bool(value)


def set_planet_positions_use_deflection(value: bool) -> None:
    global PLANET_POSITIONS_USE_DEFLECTION
    PLANET_POSITIONS_USE_DEFLECTION = bool(value)


def set_planet_positions_use_nutation(value: bool) -> None:
    global PLANET_POSITIONS_USE_NUTATION
    PLANET_POSITIONS_USE_NUTATION = bool(value)


def set_rise_set_use_refraction(value: bool) -> None:
    global RISE_SET_USE_REFRACTION
    RISE_SET_USE_REFRACTION = bool(value)

stationary_planet_speed_percent = 0.25

vedic_mean_speeds = {
    SUN_ID:   0.985556,   # 0°59'08"
    MOON_ID: 13.176667,   # 13°10'36"
    MERCURY_ID: 1.383333,  # 01° 23' 00''
    VENUS_ID: 1.200000,    # 01° 12' 00''
    MARS_ID: 0.524167,     # 00° 31' 25''
    JUPITER_ID: 0.083056,  # 00° 04' 59''
    SATURN_ID: 0.033611,    # 00° 02' 01''
    RAHU_ID: 0.050000,   # -0°03'00"
    KETU_ID: 0.050000,   # same as Rahu in mean-node mode
}

planet_info_round_factors = [3,3,4,3,3,6]
maximum_visible_search_places_in_UI = 20
maximum_queried_search_places = 30

class CHARA_KARAKA_METHOD(IntEnum):
    EIGHT_KARAKA_PARASHARI = 1 # Sun to Rahu fit to 8 karaka
    SEVEN_KARAKA_KNRAO_NOPiK = 2 # No Rahu - No Pitru Karaka
    SEVEN_KARAKA_PK_MERGED_WITH_MK = 3 # No Rahu and Pk/Mk are merged
    MIXED_SEVEN_EIGHT_KARAKA_PARASHARA = 4 # 
chara_karaka_default_method = CHARA_KARAKA_METHOD.EIGHT_KARAKA_PARASHARI
### Vyatipada method = 1 => 360.0 - dhuma
### Vyatipada method = 2 => dhuma + 53deg20min
vyatipada_calculation_method = 1 
# ==========================================
# Ashtakavarga Calculation Preferences Setup
# ==========================================
# True => counts how many target planets receive a benefic point from reference planet in that sign.
ashtakavarga_reverse_ashtakavarga = False
# True=> SAV is calculated based on relative house offsets from the planet itself instead of absolute zodiac signs.
ashtakavarga_consolidate_houses = False
# True=>Lagna is treated as a fully active planet contributing to the collective destiny points.
ashtakavarga_include_lagna_as_planet = False 
# Parasara-Varahamihira Discrepancy checkboxes
p_v_moon_benefic_9_from_moon = True
p_v_moon_malefic_9_from_mars = True
p_v_moon_benefic_2_from_jupiter = True
p_v_moon_malefic_12_from_jupiter = True
p_v_venus_benefic_4_from_mars = True
p_v_venus_malefic_5_from_mars = True
### Use of special lagna definition of giving continuity
special_lagna_continuity = True
exclude_non_planets_in_varga_chart_calculations = True

class VARNADA_METHOD(IntEnum):
    BV_RAMAN = 1
    SHARMA_SANTHANAM = 2
    SANJAY_RATH = 3
    JHA_PANDEY = 4
varnada_method_default = 1
use_default_house_owner_for_saham_calculation = True
class D2_CHART_METHOD(IntEnum):
    PARASARA_UMA_SHAMBU_VARIATION = 1
    TRADITIONA_PARASARA_WITH_Le_Cn_ONLY = 2
    RAMAN_1st_11th_DAY_NIGHT = 3
    PARIVRITTI_DWAYA_BICYCLICAL_HORA = 4
    KASHINATHA_HORA_OWNERSHIP_DAY_NIGHT = 5
    SOMANATHA_PARIVRITTI_ALTERNATE = 6
d2_chart_method_default = D2_CHART_METHOD.PARASARA_UMA_SHAMBU_VARIATION
class D3_CHART_METHOD(IntEnum):
    PARASARA_UMA_SHAMBU = 1
    PARIVRITTI_TRAYA = 2
    SOMANATHA_PARIVRITTI_ALTERNATE = 3
    JAGANAATHA = 4
    PARASARA_PARIVRITTI_EVEN_REVERSE = 5
d3_chart_method_default = D3_CHART_METHOD.PARASARA_UMA_SHAMBU
class D4_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d4_chart_method_default = D4_CHART_METHOD.PARASARA_TRADITIONAL
class D5_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d5_chart_method_default = D5_CHART_METHOD.PARASARA_TRADITIONAL
class D6_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d6_chart_method_default = D6_CHART_METHOD.PARASARA_TRADITIONAL
class D7_CHART_METHOD(IntEnum):
    PARASARA_EVEN_START_7TH_GO_FORWARD = 1
    PARASARA_EVEN_START_7TH_GO_BACKWARD = 2
    PARASARA_EVEN_REVERSE_END_7TH = 3
    PARIVRITTI_CYCLIC = 4
    PARIVRITTI_EVEN_REVERSE = 5
    SOMANATHA_PARIVRITTI_ALTERNATE = 6
d7_chart_method_default = D7_CHART_METHOD.PARASARA_EVEN_START_7TH_GO_FORWARD
class D8_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d8_chart_method_default = D8_CHART_METHOD.PARASARA_TRADITIONAL
class D9_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARASARA_EVEN_REVERSAL_UNIFORM_KRISHNA_MISRA = 2
    KALACHAKRA_NAVAMSA = 3
    RANGACHARYA_KRISHNA_MISRA_SANJAY_RATH_NADI_NAVAMSA = 4
    PARIVRITTI_CYCLIC = 5
    SOMANATHA_PARIVRITTI_ALTERNATE = 6
d9_chart_method_default = D9_CHART_METHOD.PARASARA_TRADITIONAL
class D10_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA_START_9TH_FORWARD = 1
    PARASARA_EVEN_START_9TH_BACKWARD = 2
    PARASARA_EVEN_START_REVERSE_9TH_BACKWARD = 3
    PARIVRITTI_CYCLIC_OJHA = 4
    PARIVRITTI_EVEN_REVERSE = 5
    SOMANATHA_PARIVRITTI_ALTERNATE = 6
d10_chart_method_default = D10_CHART_METHOD.TRADITIONAL_PARASARA_START_9TH_FORWARD    
class D11_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA_SANJAY_RATH = 1
    BVRAMAN_EKADASAMSA_ANTI_ZODIACAL = 2
    PARIVRITTI_CYCLIC_OJHA = 3
    PARIVRITTI_EVEN_REVERSE = 4
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d11_chart_method_default = D11_CHART_METHOD.TRADITIONAL_PARASARA_SANJAY_RATH
class D12_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA = 1
    TRADITIONAL_PARASARA_EVEN_REVERSAL = 2
    PARIVRITTI_CYCLIC_OJHA = 3
    PARIVRITTI_EVEN_REVERSE = 4
    SOMANATHA_PARIVRITTI_ALTERNATE = 5
d12_chart_method_default = D12_CHART_METHOD.TRADITIONAL_PARASARA
class D16_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_EVEN_REVERSE = 2
    PARIVRITTI_CYCLIC = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d16_chart_method_default = D16_CHART_METHOD.PARASARA_TRADITIONAL
class D20_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_EVEN_REVERSE = 2
    PARIVRITTI_CYCLIC = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d20_chart_method_default = D20_CHART_METHOD.PARASARA_TRADITIONAL
class D24_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA = 1
    PARASARA_EVEN_REVERSE = 2
    PARASARA_EVEN_DOUBLE_REVERSE = 3
d24_chart_method_default = D24_CHART_METHOD.TRADITIONAL_PARASARA
class D27_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA = 1
    PARASARA_EVEN_REVERSE = 2
    SOMANATHA_PARIVRITTI_ALTERNATE = 3
d27_chart_method_default = D27_CHART_METHOD.TRADITIONAL_PARASARA
class D30_CHART_METHOD(IntEnum):
    TRADITIONAL_PARASARA = 1
    PARIVRITTI_CYCLIC_TRIMSAMSA = 2
    SASHTYAMSA_LIKE_TRIMSAMSA = 3
    PARASARA_EVEN_REVERSE = 4
    SOMANATHA_PARIVRITTI_ALTERNATE = 5
d30_chart_method_default = D30_CHART_METHOD.TRADITIONAL_PARASARA
class D40_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d40_chart_method_default = D40_CHART_METHOD.PARASARA_TRADITIONAL
class D45_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d45_chart_method_default = D45_CHART_METHOD.PARASARA_TRADITIONAL
class D60_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL_FROM_SIGN = 1
    PARASARA_CYCLIC_FROM_ARIES = 2
    PARASARA_EVEN_REVERSE_FROM_ARIES = 3
    PARASARA_EVEN_REVERSE_FROM_SIGN = 4
d60_chart_method_default = D60_CHART_METHOD.PARASARA_TRADITIONAL_FROM_SIGN
class D81_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL_PARIVRITTI_CYCLIC= 1
    PARIVRITTI_EVEN_REVERSE = 2
    SOMANATHA_PARIVRITTI_ALTERNATE = 3
    KALACHAKRA_NAVA_NAVAMSA = 4
d81_chart_method_default = D81_CHART_METHOD.PARASARA_TRADITIONAL_PARIVRITTI_CYCLIC
class D108_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d108_chart_method_default = D108_CHART_METHOD.PARASARA_TRADITIONAL
class D144_CHART_METHOD(IntEnum):
    PARASARA_TRADITIONAL = 1
    PARIVRITTI_CYCLIC = 2
    PARIVRITTI_EVEN_REVERSE = 3
    SOMANATHA_PARIVRITTI_ALTERNATE = 4
d144_chart_method_default = D144_CHART_METHOD.PARASARA_TRADITIONAL
class D150_CHART_METHOD(IntEnum):
    PVR_JHORA_METHOD_OWN_SIGN_UNIFORM_DIRECT = 1
    DEVA_KERALAM_CHANDRA_KALA_NADI_NON_UNIFORM = 2
    DEVA_KERALAM_CHANDRA_KALA_NADI_UNIFORM_DIRECT = 3
    PARIVRITTI_CYCLIC = 4
    MOVABLE_ARIES_FWD_FIXED_TAURUS_BACK_DUAL_GEMINI_FWD = 5
    MOVABLE_ARIES_FWD_FIXED_SCORPIO_BACK_DUAL_SAGITARIUS_FWD = 6
    MOVABLE_ARIES_FWD_FIXED_LEO_BACK_DUAL_SAGITARIUS_FWD = 7
    MOVABLE_SIGN_FWD_FIXED_SIGN_BACK_DUAL_SIGN_FWD = 8
d150_chart_method_default = D150_CHART_METHOD.PVR_JHORA_METHOD_OWN_SIGN_UNIFORM_DIRECT
amsa_supported_vargas = [2,3,4,7,9,10,12,16,20,24,27,30,45,60,150]
AVAILABLE_CHART_STYLES = {
    CHART_STYLE.SOUTH_INDIAN_REGULAR: {"class": "SouthIndianChart", "args": {"chart_style_irregular": False},
                                             "resource":"south_indian_str"},
    CHART_STYLE.NORTH_INDIAN: {"class": "NorthIndianChart","args": {},"resource":"north_indian_str"},
    CHART_STYLE.EAST_INDIAN_WITH_FRAME: {"class": "EastIndianChart","args": {"draw_frames": True},
                                             "resource":"east_indian_str"},
    CHART_STYLE.WESTERN: {"class": "WesternChart","args": {},"resource":"western_str"},
    CHART_STYLE.SUDARSANA_CHAKRA: {"class": "SudarsanaChakraChart","args": {},"resource":"sudarsana_chakra_str"},
    CHART_STYLE.SOUTH_INDIAN_IRREGULAR: {"class": "SouthIndianChart","args": {"chart_style_irregular": True},
                                             "resource":"south_indian_irregular_str"},
    CHART_STYLE.EAST_INDIAN_NO_FRAME: {"class": "EastIndianChart","args": {"draw_frames": False},
                                             "resource":"east_indian_noframe_str"},
}
_SOUTH_CHART_TYPES = (
    CHART_STYLE.SOUTH_INDIAN_REGULAR,
    CHART_STYLE.SOUTH_INDIAN_IRREGULAR,
)

_EAST_CHART_TYPES = (
    CHART_STYLE.EAST_INDIAN_WITH_FRAME,
    CHART_STYLE.EAST_INDIAN_NO_FRAME,
)

_SOUTH_EAST_TYPES = _SOUTH_CHART_TYPES + _EAST_CHART_TYPES

south_regular_zodiac_symbol_map = [
    ['\u2653', '\u2648', '\u2649', '\u264A'],
    ['\u2652', '', '', '\u264B'],
    ['\u2651', '', '', '\u264C'],
    ['\u2650', '\u264F', '\u264E', '\u264D']
]

south_irregular_zodiac_symbol_map = [
    ['\u264A', '\u2649', '\u2648', '\u2653'],
    ['\u264B', '', '', '\u2652'],
    ['\u264C', '', '', '\u2651'],
    ['\u264D', '\u264E', '\u264F', '\u2650']
]

class DASHA_SESHAM_METHOD(IntEnum):
    STANDARD = 1
    REVERSE = 2
    NONE = 3
default_dasha_sesham_method = DASHA_SESHAM_METHOD.STANDARD

class CHAKRA_TYPE(IntEnum):
    KOTA_CHAKRA = 0
    KAALA_CHAKRA = 1
    SARVATOBADRA_CHAKRA = 2
    SURYA_KALANALA_CHAKRA = 3
    CHANDRA_KALANALA_CHAKRA = 4
    SHOOLA_CHAKRA = 5
    TRIPATAKI_CHAKRA = 6
    SAPTHA_SHALAKA_CHAKRA = 7
    PANCHA_SHALAKA_CHAKRA = 8
    SAPTHA_NADI_CHAKRA = 9
special_thaara_names = ['janma_str', 'karma_str', 'samudayika_str', 'sangathika_str','jaathi_str',
                        'naidhana_str', 'desha_str', 'abhisheka_str','aadhaana_str', 
                        'vainasika_str', 'maanasa_str']
""" 
    BVR-72 Sara/Ishu Yoga: all the planets are in 4th, 5th, 6th and 7th houses from lagna, 
    NOTE: BV Raman in his book states 4,5,9,7. Not sure spellinhg mistake? (method=2) 
    In one place in the book BVR says:  in 4th, 5th, 9th and 7th, Ishu or Sara is produced;
    In another place, he says: Thus, for instance,I shu Yoga, said to be caused by the 
    seven planets occupying the 4th, 5th, 6th and 7th houses. Chart-48 has 4,5,6,7
    Choose method = 2 only if you want to use 4th, 5th, 7th and 9th.
"""
sara_yoga_method = 1 
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
matsya_yoga_method = 1
""" BVR-54 Koorma Yoga: If (1) the 5th, 6th and 7th houses are occupied by benefics who are in
    own, exaltation or friendly signs and (2) the 1st, 3rd and 11th houses are occupied by
    malefics who are in own or exaltation signs. 
    Method = 1 BV Raman - 
        2nd condition is also for BENEFICS (not malefics) AND 
        ONLY ONE of the above two conditions required
        Condition >= Friend, exalt, own
    Method = 2 PVR - 
        BOTH conditions are required and 1st for benefics and 2nd for malefics
        Condition 1 == Friend/exalt/Own and Condition 2 >= exalt/Own (No Friend)
"""
koorma_yoga_method = 1
""" BVR-51 Brahma Yoga (part of harihara brahma yoga): 
    Brahma Yoga: (Based on PVR Narasimha Rao)
    Method 1: Benefics in 4th, 10th and 11th from Lagna Lord.
    Method 2: Jupiter in quadrant from 9th lord, Venus in quadrant from 11th lord, 
                and Mercury in quadrant from 1st or 10th lord.
"""
brahma_yoga_method = 1
""" 
BVR-50 Amsaavatara Yoga: 
Method 1 (PVR): Jupiter, Venus, and exalted Saturn are in quadrants.
Method 2 (BVR): Same as Method 1, but Lagna must be in a movable sign.
"""
amsaavatara_yoga_method = 1
""" 
    BVR 144 to 152
    Method=1 Ref: Medium - What is daridra yoga
    the lord of 1nd or 11th is situated in the 6th, 8th or 12th
    Method = 2 - Ref: BV Raman Dharidhra Yoga #144 to #152
"""
dharidhdra_yoga_method = 2


if __name__ == "__main__":
    print('graha',len(_graha_dhasa_dict),len(dhasa_default_options))
    print('rasi',len(_rasi_dhasa_dict))
    print('planet',len(planet_dhasas))
    print('rasi',len(rasi_dhasas))
    print([x for x in _graha_dhasa_dict.keys() if x not in planet_dhasas])
    pass
