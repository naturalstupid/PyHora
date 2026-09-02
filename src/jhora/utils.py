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
    utils module
    contains common functions used by various PyJHora modules
"""
"""
    Release History:
    V4.8.6 - count_stars, count_rasis - dir changed direction argument. Revised set_flags_for_planet_positions.
            added validate_raasi_index and validate_star_index
"""
import os
import codecs
import warnings
import geocoder
import requests
from pytz import timezone, utc
from timezonefinder import TimezoneFinder
import csv
import numpy as np
import swisseph as swe
from geopy.geocoders import Nominatim
from jhora import const

import json
import datetime as dt
from dateutil import relativedelta
from enum import Enum

google_maps_url = "https://www.google.cl/maps/place/"#+' time zone'

sort_tuple = lambda tup,tup_index,reverse=False: sorted(tup,key = lambda x: x[tup_index],reverse=reverse)

def save_location_to_database_old(location_data):
    columns = ['place_name','state','country','latitude','longitude','timezone_hours','altitude/elevation']
    global _world_city_db_df
    print('writing ',location_data,' to ',const._place_database_file)
    _world_city_db_df.loc[len(_world_city_db_df.index)] = location_data
    _world_city_db_df.to_csv(const._place_database_file,mode='w',header=columns,index=False)#,quoting=None)
def save_location_to_database(location_data):
    print("Save Location to Database disabled for now. Requires New Implementation")
    return
    global world_cities_dict
    print('writing ',location_data,' to ',const._place_database_file)
    with open(const._place_database_file, mode='a', newline='', encoding='ISO-8859-1') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(location_data)
    world_cities_dict[location_data[1]] = len(world_cities_dict)
" Flatten a list of lists "
flatten_list = lambda list: [item for sublist in list for item in sublist]
def _get_place_from_ipinfo():
    url = 'http://ipinfo.io/json'
    response = requests.get(url)
    data = json.loads(response.text)
    print('data recd from ipinfo',data)
    place = data['city']+','+data['country']
    latitude,longitude = data['loc'].split(',')
    time_zone_offset = get_place_timezone_offset(latitude,longitude)
    return place,latitude,longitude,time_zone_offset
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_place_from_user_ip_address_cached():
    """
    Internal cached function.
    Returns a tuple:
        (place, latitude, longitude, time_zone_offset, elevation)
    or empty tuple on failure.
    """
    try:
        print("Trying to get using IP Address of the user")
        g = geocoder.ip('me')  # ipinfo('me')

        if g is None or g == '' or not getattr(g, 'latlng', None):
            print('Trying using ipinfo website')
            try:
                place, latitude, longitude, time_zone_offset = _get_place_from_ipinfo()
                elevation = get_elevation(latitude, longitude) if const.get_place_elevation_from_internet else 0.0
                print('Location obtained from IP Address:', place, [latitude, longitude, time_zone_offset, elevation])
                return (
                    place,
                    float(latitude),
                    float(longitude),
                    float(time_zone_offset),
                    float(elevation)
                )
            except Exception:
                print('No latitude/longitude provided. Could not guess location from IP Address')
                return tuple()

        city = g.city if getattr(g, 'city', None) else ''
        country = g.country if getattr(g, 'country', None) else ''
        latlng = g.latlng if getattr(g, 'latlng', None) else []

        if len(latlng) < 2:
            print('No latitude/longitude provided. Could not guess location from IP Address')
            return tuple()

        latitude, longitude = latlng
        place = f"{city},{country}".strip(',')

        time_zone_offset = get_place_timezone_offset(latitude, longitude)
        elevation = get_elevation(latitude, longitude) if const.get_place_elevation_from_internet else 0.0

        print('Location obtained from IP Address:', place, [latitude, longitude, time_zone_offset, elevation])
        return (
            place,
            float(latitude),
            float(longitude),
            float(time_zone_offset),
            float(elevation)
        )

    except Exception:
        print('No latitude/longitude provided. Could not guess location from IP Address')
        return tuple()


def get_place_from_user_ip_address():
    """
    Public wrapper.
    Returns:
        [place, latitude, longitude, time_zone_offset, elevation]
    or []
    """
    result = _get_place_from_user_ip_address_cached()
    return list(result) if result else []
import certifi
import requests

def get_elevation(lat=None, long=None):
    if lat is None or long is None:
        return 0.0

    query = const._open_elevation_api_url(lat, long)
    try:
        r = requests.get(query, timeout=20, verify=certifi.where())
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        return float(results[0].get("elevation", 0.0)) if results else 0.0
    except requests.RequestException as e:
        print("Request failed:", e)
        return 0.0
    except (ValueError, TypeError, KeyError) as e:
        print("Bad JSON/structure:", e)
        return 0.0
def _validate_data(place,latitude,longitude,time_zone_offset,dob,tob,divisional_chart_factor):
    country = ''
    if place  is not None and (latitude is None or longitude is None):
        city,latitude,longitude,time_zone_offset = get_location(place)
    if latitude is None or longitude is None:
        place,latitude,longitude,time_zone_offset = get_place_from_user_ip_address()
    if dob is None:
        today = dt.datetime.today()
        dob = (today.year,today.month,today.day)
        print("Today's Date:",dob,'assumed')
    if tob is None:
        tob = tuple(str(dt.datetime.now()).split()[1].split(':'))
        print('Current time:',tob,'assumed')
    if divisional_chart_factor not in const.division_chart_factors:
        str_dvf = ','.join([str(x) for x in const.division_chart_factors])
        w_msg = '\nInvalid value for dhasa varga factor. '+str(divisional_chart_factor)+ \
        '\nAllowed values '+ str_dvf +'\n' + 'division_chart_factor=1 (for Raasi) is assumed now '
        warnings.warn(w_msg)
        divisional_chart_factor = 1
    return place,latitude,longitude,time_zone_offset,dob,tob,divisional_chart_factor
def _get_location(place_name=None):
    """
        function to get place's latitude, longitude and timezone
        if will make call following functions one by one until location info is obtained
            1. if place_name is none - it will try to get the place from the user's IP address.
            2. If step-1 fails, check if lat/long in world cities database file in data folder
            3. if step-2 fails, try google using _scrap_google_map_for_latlongtz_from_city_with_country()
            4. if step-3 fails, Try OpenStreetMaps using get_location_using_nominatim()
            5. if step-4 fails - return [] empty list
        
        @param place_name: Place name. Example: 'Shillong, India' 'Hoffman Estates,IL,US'
        @return: [place_name,latitude,longitude,time_zone] 
    """
    result = None
    place_found = False
    if place_name is None or place_name.strip()=='':
        result = get_place_from_user_ip_address()
        if result:
            return result
    ' first check if lat/long in world cities db'
    place_index = world_cities_dict.get(place_name.lower())
    #print('place_name,place_name_1,place_index',place_name,place_index)
    if place_index is not None and place_index>=0:
        place_found = True
        #print(place_name,'in the database',place_index)
        with open(const._place_database_file, encoding='ISO-8859-1') as csvfile:
            reader = csv.reader(csvfile)
            for idx, row in enumerate(reader):
                if idx == place_index:
                    city = row[1]
                    _latitude = round(float(row[2]), 4)
                    _longitude = round(float(row[3]), 4)
                    _time_zone = round(float(row[5]), 2)
                    result = [city, _latitude, _longitude, _time_zone]
                    #print("RESULT:",result)
                    return result
    else:
        print(place_name,'not in '+const._place_database_file+'.Trying to get from Google')
        result = _scrap_google_map_for_latlongtz_from_city_with_country(place_name)
        if result  is not None and len(result)==3:
            place_found = True
            #print(place_name,' found from google maps')
            _place_name = place_name
            _latitude = round(result[0],4)
            _longitude = round(result[1],4)
            _time_zone = round(result[2],2)
            result = [place_name,_latitude,_longitude,_time_zone]
            print('google result',result)
            """ TODO: To save in database
            result should be converted to the CSV format in world_cities file
            Country, place, lat, long, timezone string, timezone hours
            from place_name we should extract country and place name
            And somehow we should get timezone string
            """
            if ',' in place_name:
                _city,_country = place_name.split(','); _tz_str = ''
                #print('city,country',_city,_country)
                if _city not in world_cities_dict.keys():
                    #print('saving to database',_city,_country)
                    save_location_to_database([_country,_city,_latitude,_longitude,_tz_str,_time_zone])
        else:
            print('Could not get',place_name,'from google.Trying to get from OpenStreetMaps')
            place_found = False
            result = get_location_using_nominatim(place_name)
            if result:
                place_found = True
                print(place_name,'found in OpenStreetMap')
                [_place_name,_latitude,_longitude,_time_zone] = result
                _arr = place_name.split(','); 
                if len(_arr)>=2:
                    _city = ','.join(_arr[:-1]); _country=_arr[-1];_tz_str=''
                    #print('city,country',_city,_country)
                    if _city not in world_cities_dict.keys():
                        print('saving to database',_city,_country)
                        save_location_to_database([_country,_city,_latitude,_longitude,_tz_str,_time_zone])
    if place_found:
        return result
    return []
def scrap_google_map_for_latlongtz_from_city_with_country(city_with_country):
    """
        function to scrap google maps to get latitude/longitude of a city/country
        @param city_with_country: city name <comma> country name
            Example: Chennai, India
        @return [city,latitude,longitude,time_zone_offset]
    """
    url = google_maps_url+city_with_country
    resp=requests.request(method="GET",url=url)
    r = requests.get(url)
    txt = r.text
    
    find1 = "window.APP_INITIALIZATION_STATE="
    find2 = ";window.APP"
    
    i1 = txt.find(find1)
    i2 = txt.find(find2, i1+1 )
    js = txt[i1+len(find1):i2]
    data = json.loads(js)[0][0][1:3]
    latitude = data[1]
    longitude = data[0]
    timezone_offset = get_place_timezone_offset(latitude, longitude)
    print('city',city_with_country,'lat=',latitude,'long=',longitude,'timezone offset',timezone_offset)
    return city_with_country,latitude,longitude,timezone_offset
def get_location_using_nominatim(place_with_country_code):
    """
        function to get latitude/longitude from city with country code using Nominatim
        requires geopy installed
        @param place_with_country_code: city name <comma> country name
            Example: Chennai, IN
        @return [city,latitude,longitude,time_zone_offset]
    """
    #[city,latitude,longitude,tz_offset]=''
    geolocator = Nominatim(user_agent="Astro") #,format_string="%s, Bangalore")
    while True:
        try:
            #print('try')
            address,(latitude,longitude) = geolocator.geocode("city:" + place_with_country_code, featuretype='city')
            break
        except (RuntimeError, TypeError, NameError):
            #print('except')
            ValueError('City:'+place_with_country_code+' not found in OpenStreetMap')
            address = ''
            break
    if address:    
        #print('address')
        city = address.split(',')[0]
        time_zone_offset = get_place_timezone_offset(latitude, longitude)
        return [city,latitude,longitude,time_zone_offset]
    return None
def _scrap_google_map_for_latlongtz_from_city_with_country(city_with_country):
    url = "https://www.google.cl/maps/place/"+city_with_country#+' time zone'
    try:
        resp=requests.request(method="GET",url=url)
        r = requests.get(url)
        txt = r.text
        
        find1 = "window.APP_INITIALIZATION_STATE="
        find2 = ";window.APP"
        
        i1 = txt.find(find1)
        i2 = txt.find(find2, i1+1 )
        js = txt[i1+len(find1):i2]
        #print('_scrap_google_map_for_latlongtz_from_city_with_country','txt',txt,'js',js)
        data = json.loads(js)[0][0][1:3]
        latitude = data[1]
        longitude = data[0]
        timezone_offset = get_place_timezone_offset(latitude, longitude)
        print('city',city_with_country,'lat=',latitude,'long=',longitude,'timezone offset',timezone_offset)
        return latitude,longitude,timezone_offset
    except Exception as e: 
        print(e)
        warnings.warn("Unable to get location from Google Map Scrap. Aborted")
        return []
def _get_timezone_from_pytz(timezone_str_from_geocoder):
    print("Trying pytz to get timezone value")
    from pytz import timezone
    tz = dt.datetime.now(timezone(timezone_str_from_geocoder)).utcoffset().total_seconds()/60/60
    return tz
def get_place_timezone_offset(latitude, longitude,jd_local=None):
    """
        This can be used when latitude/longitude are known but not the time zone offset of the place.
        This is an internal function that returns a location's time zone offset from UTC in minutes - using latitude/longitude of the place.
        @param latitude: latitude of the place
        @param longitude: longitude of the place
        @return [city,latitude,longitude,time_zone_offset]
    """
    try:
        tf = TimezoneFinder()
        if jd_local is None:
            today = dt.datetime.now()
        else:
            y,m,d,fh = jd_to_gregorian(jd_local); hh,mm,ss = to_dms(fh,as_string=False)
            """ For BCE Dates for now it returns DST of current year and same month/day since datetime does not support BCE """
            today = dt.datetime(y,m,d,hh,mm,ss) if y>0 else dt.datetime(dt.datetime.now().year,m,d,hh,mm,ss)
        tz_target = timezone(tf.timezone_at(lng=longitude, lat=latitude))
        # ATTENTION: tz_target could be None! handle error case
        today_target = tz_target.localize(today)
        today_utc = utc.localize(today)
        tz_offset = (today_utc - today_target).total_seconds() / 3600.0 # in hours
        #print('timezone offset',tz_offset)
        return tz_offset
    except Exception as err:        
        print('Error in get_place_timezone_offset',err)
        print('WARNING: Time Zone returned as default +5.0. Need to change it')
        return 5.0
def get_house_to_planet_dict_from_planet_to_house_dict(planet_to_house_dict):
    """
        function to get house_to_planet list from planet_to_house dictionary 
        @param planet_to_house_dict: Format {planet_id : raasi_number, ....}
                Example: {0:0, 1:1,2:1,...} Sun in Aries, Moon in Tarus, Mars in Gemini etc
        @return: house_to_planet list - in the format ['0','1/2',...] Aries has Sun, Tarus has Moon/Mars etc
    """
    h_to_p = ['' for h in range(12)]
    for p,h in planet_to_house_dict.items():
        h_to_p[h] += str(p) + '/'
    h_to_p = [p[:-1] for p in h_to_p]
    return h_to_p
def get_planet_to_house_dict_from_chart(house_to_planet_list):
    """
        function to get planet_to_house dictionary from house_to_planet list  
        @param house_to_planet list - in the format ['0','1/2',...] Aries has Sun, Tarus has Moon/Mars etc
                'L' is used for Lagna
        @return: house_to_planet_list: 
                Format {planet_id : raasi_number, ....}
                Example: {0:0, 1:1,2:1,...} Sun in Aries, Moon in Tarus, Mars in Gemini etc
                Last element will be 'L' for Lagna
    """
    p_to_h = {p:h for p in const.SUN_TO_KETU+[const._ascendant_symbol] for h,planets in enumerate(house_to_planet_list) if str(p) in planets }
    return p_to_h
def get_planet_house_dictionary_from_planet_positions(planet_positions):
    """ 
        Get Planet_to_House Dictionary {p:h}  from Planet_Positions {p:(h,long)}
        @param planet_positions: Format: {planet_index:(raasi_index,planet_longitude_in_the_raasi),...
        @return: planet_to_house_dictionary in the format {planet_index:raasi_index,...} 
    """ 
    p_to_h = {p:h for p,(h,_) in planet_positions}
    return p_to_h
def get_house_planet_list_from_planet_positions(planet_positions):
    """
        to convert from the format [planet,(house,planet_longitude,...]
        into a dict of {house_1:planet_1/planet_2,house_2:Lagnam/planet_2,....}
        @param planet_positions: Format: {planet_index:(raasi_index,planet_longitude_in_the_raasi),...
        @return: house_to_planet list - in the format ['0','1/2',...] Aries has Sun, Tarus has Moon/Mars etc
    """
    h_to_p = ['' for h in range(12)] 
    for sublist in planet_positions:
        p = sublist[0]
        h = sublist[1][0]
        h_to_p[h] += str(p) + '/'
    h_to_p = [x[:-1] for x in h_to_p]
    return h_to_p
def set_ephemeris_data_path(data_path=None):
    if data_path is None: data_path = const._ephe_path
    swe.set_ephe_path(data_path)
def set_language(language=None):
    if language is None: language=const._DEFAULT_LANGUAGE
    global resource_strings
    #print('language',language)
    if language in const.available_languages.values():
        #print('default language set to',language)
        const._DEFAULT_LANGUAGE = language
        language_list_file = const._LANGUAGE_PATH+const._DEFAULT_LANGUAGE_LIST_STR+language+'.txt'
        #print('language_list_file',language_list_file)
        language_message_file = const._LANGUAGE_PATH+const._DEFAULT_LANGUAGE_MSG_STR+language+'.txt'
        
        get_resource_lists(language_list_file)
        resource_strings = get_resource_messages(language_message_file=language_message_file)
def _read_resource_messages_from_file(message_file):
    if not os.path.exists(message_file):
        print('Error: List Types File:'+message_file+' does not exist. Script aborted.')
        exit()
    cal_key_list = {}
    with codecs.open(message_file, encoding='utf-8', mode='r') as fp:
        line_list = fp.read().splitlines()
    fp.close()
    for line in line_list: #  fp:
        if line.replace("\r\n","").replace("\r","").rstrip().lstrip()[0] == '#':
            continue
        splitLine = line.split('=')
        cal_key_list[splitLine[0].strip()]=splitLine[1].strip()
    #print ('length of messages',len(cal_key_list))
    return cal_key_list       
def get_resource_messages(language_message_file=const._LANGUAGE_PATH + const._DEFAULT_LANGUAGE_MSG_STR + const._DEFAULT_LANGUAGE + '.txt'):
    """
        Retrieve message strings from language specific message resource file
        @param param:language_message_file -language specific message resource file name
            Default: const._LANGUAGE_PATH + 'msg_strings_' + const._DEFAULT_LANGUAGE + '.txt'
            Defualt: ./lang/msg_strings_en.txt
        @return: dictionary of message keys with language specific values
    """
    res = _read_resource_messages_from_file(language_message_file)
    return res
resource_strings = get_resource_messages(const._LANGUAGE_PATH+const._DEFAULT_LANGUAGE_MSG_STR+const._DEFAULT_LANGUAGE+'.txt')
def _read_resource_lists_from_file(language_list_file):
    import sys,os
    module = sys.modules[__name__]
    file_path = language_list_file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    #print('_read_resource_lists_from_file')
    with open(file_path, 'r',encoding='utf-8') as file: # V4.5.0
        for line in file:
            line = line.strip()
            if line.startswith("###"):
                continue
            elif "=" in line:
                var_name, var_value = line.split("=")
                var_name = var_name.strip()
                var_value = var_value.split(',')
                setattr(module, var_name, var_value)
                #print('length of',var_name,len(var_value))
def get_resource_lists(language_list_file=const._LANGUAGE_PATH + const._DEFAULT_LANGUAGE_LIST_STR + const._DEFAULT_LANGUAGE + '.txt'):
    """
        Retrieve resource list from language specific resource list file
        list values in resource language are read and returned
        @param param:language_message_file -language specific message resource file name
            Default: _DEFAULT_LANGUAGE_LIST_FILE = _LANGUAGE_PATH + 'list_values_' + _DEFAULT_LANGUAGE + '.txt'
            Defualt: ./lang/list_values_en.txt
        @return: [PLANET_NAMES,NAKSHATRA_LIST,NAKSHATRA_SHORT_LIST,TITHI_LIST,RAASI_LIST,KARANA_LIST,DAYS_LIST,PAKSHA_LIST,
                 YOGAM_LIST,MONTH_LIST,YEAR_LIST,DHASA_LIST,BHUKTHI_LIST,PLANET_SHORT_NAMES,RAASI_SHORT_LIST,
                 SHADVARGAMSA_NAMES,SAPTAVARGAMSA_NAMES,DHASAVARGAMSA_NAMES,SHODASAVARGAMSA_NAMES,ISLAMIC_MONTH_LIST]
    """
    _read_resource_lists_from_file(language_list_file)
# Convert 23d 30' 30" to 23.508333 degrees
from_dms = lambda degs, mins, secs: degs + mins/60 + secs/3600
from_dms_to_str = lambda dms_list: str(dms_list[0])+const._degree_symbol + str(dms_list[1])+const._minute_symbol + str(dms_list[2])+const._second_symbol
def from_dms_str_to_dms(dms_str):
    if '+1' in dms_str:
        dmsh = 24
    elif '-1' in dms_str:
        dmsh = -24
    else:
        dmsh = 0
    dms = dms_str.replace('(+1)','').replace('(-1)','').replace(' AM','').replace(' PM','').split(':')
    return dmsh+int(dms[0]),int(dms[1]),int(dms[2])
def from_dms_str_to_degrees(dms_str):
    dms = from_dms_str_to_dms(dms_str)
    return dms[0]+dms[1]/60.+dms[2]/3600.
# the inverse
def to_dms_prec(deg):
  """
      convert float degrees to (int)degrees, (int) minutes, (float) seconds tuple
  """
  d = int(deg)
  mins = (deg - d) * 60
  m = int(mins)
  s = round((mins - m) * 60, 2) # changed from 6 digit precision in 2.0.3
  return [d, m, s]

def to_dms(deg,as_string=True, is_lat_long=None,round_seconds_to_digits=None,round_to_minutes=None,
           use_24hour_format=None):
    """
        convert float degrees to (int)degrees, (int) minutes, (int) seconds tuple
        @param deg: degrees as float
        @param as_string: True - output will be single string with degree symbols
                          False - output will be tuple (int)degrees, (int) minutes, (float) seconds tuple
        @param is_lat_long: works with as_string=True
                            = plong - degree symbol shown
                            = lat  - N / S symbol is shown for degrees
                            = long - E / W symbol is shown for degrees
        @return: degrees/minutes/seconds as string or tuple depending on as_string=True and is_lat_long values
    """
    if use_24hour_format is None: use_24hour_format = const.use_24hour_format_in_to_dms
    sep = ':'
    am = " AM"
    pm = " PM"
    ampm= am
    degree_symbol = const._degree_symbol 
    minute_symbol = const._minute_symbol
    second_symbol = const._second_symbol
    next_day = ''
    d = int(deg)
    mins = (deg - d) * 60
    if round_to_minutes:
        m = int(round(mins,0))
    else:
        m = int(mins)
    ss = (mins-m)*60
    s = round(ss,round_seconds_to_digits) # V2.3.1 int changed to round
    #"""
    if (is_lat_long is None):
        if d > 23:
            q = d // 24
            d = d % 24 #d -= 24
            next_day = ' (+'+str(q)+')' if q>0 else ''
        elif d < 0:
            q = abs(d) // 24 + 1# V4.2.7
            d = abs(d) % 24
            m = abs(m)
            s = abs(s)
            next_day = ' (-'+str(q)+')' if q>0 else '' # V4.2.7
    #      print('d=',d)
    #"""
    if d >= 12:
        ampm = pm
    if s==60:
        m += 1
        s = 0
    if m==60:
        d += 1
        m = 0
    if round_to_minutes:
        answer = [d,m]
    else:
        answer = [d, m, s]
    if use_24hour_format: ampm = ''
    if as_string or is_lat_long  is not None:
        if is_lat_long=='plong':
            answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol+" "+str(abs(s))+second_symbol
            if round_to_minutes:
                answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol
        elif is_lat_long=='lat':
            answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol+" "+str(abs(s))+second_symbol
            if round_to_minutes:
                answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol
            if d > 0: answer += ' N'
            else: answer +=' S' 
        elif is_lat_long=='long':
            answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol+" "+str(abs(s))+second_symbol
            if round_to_minutes:
                answer = str((d))+degree_symbol+" "+str(abs(m))+minute_symbol
            if d > 0: answer += ' E'
            else: answer +=' W' 
        else: ## as_string = =True
            answer= str(d).zfill(2)+ sep +str(m).zfill(2)+ sep +str(s).zfill(2)+ampm+next_day
            if round_to_minutes:
                answer = str(d).zfill(2)+ sep +str(m).zfill(2)+ampm+next_day # V4.4.0
    return answer
def _to_dms_old(deg):
  d, m, s = to_dms_prec(deg)
  return [d, m, int(s)]
def normalize_angle(angle, start=0):
    """
    Normalize angle to be within the range from start to start + 360 degrees.
    """
    while angle >= start + 360:
        angle -= 360
    while angle < start:
        angle += 360
    return angle
def extend_angle_range(angles, target):
    """
    Extend angles to cover a wider range if needed for interpolation.
    """
    extended_angles = angles[:]
    while max(extended_angles) - min(extended_angles) < target:
        extended_angles = extended_angles + [angle + 360 for angle in angles]
    return extended_angles

def unwrap_angles(angles):
    """
    Normalize angles to handle circular continuity.
    For example, if angles are [340, 350, 10, 20], it converts them to [340, 350, 370, 380].
    """
    result = [angles[0]]
    for i in range(1, len(angles)):
        angle = angles[i]
        if angle < result[i-1]:  # Detecting the wrap-around point
            angle += 360
        result.append(angle)
    return result

def unwrap_angles_old(angles):
  """
      Add 360 to those elements in the input list so that all elements are sorted in ascending order.
  """
  result = angles
  for i in range(1, len(angles)):
    if result[i] < result[i-1]: result[i] += 360

  assert(result == sorted(result))
  return result

# Make angle lie between [-180, 180) instead of [0, 360)
norm180 = lambda angle: (angle - 360) if angle >= 180 else angle;

# Make angle lie between [0, 360)
norm360 = lambda angle: angle % 360

def _function(point):
    swe.set_sid_mode(swe.SIDM_USER, point, 0.0)
    #swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Place Revati at 359°50'
    #fval = norm180(swe.fixstar_ut("Revati", point, flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]) - ((359 + 49/60 + 59/3600) - 360)
    # Place Revati at 0°0'0"
    #fval = norm180(swe.fixstar_ut("Revati", point, flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0])
    # Place Citra at 180°
    fval = swe.fixstar_ut("Citra", point, flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0] - (180)
    # Place Pushya (delta Cancri) at 106°
    # fval = swe.fixstar_ut(",deCnc", point, flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0] - (106)
    return fval

def _bisection_search(func, start, stop):
  left = start
  right = stop
  epsilon = 5E-10   # Anything better than this puts the loop below infinite

  while True:
    middle = (left + right) / 2
    midval =  func(middle)
    rtval = func(right)
    if midval * rtval >= 0:
      right = middle
    else:
      left = middle

    if (right - left) <= epsilon: break

  return (right + left) / 2

def inverse_lagrange(x, y, ya):
  """Given two lists x and y, find the value of x = xa when y = ya, i.e., f(xa) = ya"""
  assert(len(x) == len(y))
  total = 0
  for i in range(len(x)):
    numer = 1
    denom = 1
    for j in range(len(x)):
      if j != i:
        numer *= (ya - y[j])
        denom *= (y[i] - y[j])

    total += numer * x[i] / denom

  return total
def newton_polynomial(x_data, y_data, x):
    """
    x_data: data points at x
    y_data: data points at y
    x: evaluation point(s)
    """
    def _poly_newton_coefficient(x, y):
        """
        x: list or np array contanining x data points
        y: list or np array contanining y data points
        """
    
        m = len(x)
    
        x = np.copy(x)
        a = np.copy(y)
        for k in range(1, m):
            a[k:m] = (a[k:m] - a[k - 1])/(x[k:m] - x[k - 1])
    
        return a

    a = _poly_newton_coefficient(x_data, y_data)
    n = len(x_data) - 1  # Degree of polynomial
    p = a[n]

    for k in range(1, n + 1):
        p = a[n - k] + (x - x_data[n - k])*p

    return p
def julian_day_utc(julian_day,place):
     return julian_day - (place.timezone / 24.)
def julian_day_number_new(date_of_birth_as_tuple,time_of_birth_as_tuple):
    y,m,d = date_of_birth_as_tuple
    h,mm,s = time_of_birth_as_tuple
    jdn = d + int((153*m+2)/5) + 365*y + int(y/4) - int(y/100) + int(y/400) - 32045
    jdt =  h + mm/60 + s/3600
    jd = jdn+(jdt-12)/24,3
    return jd
def julian_day_number(date_of_birth_as_tuple,time_of_birth_as_tuple):
    """
        return julian day number for give Date of birth and time of birth as tuples
        @param date_of_birth_as_tuple: Date of birth as tuple. e.g. (2000,1,1)
            Note: For BC Dates use negative year e.g. (-3114,1,1) means 1-Jan of 3114 BC
            Note: There is no 0 BC or 0 AD so avoid Zero year
        @param time_of_birth_as_tuple: time of birth as tuple e.g. (18,0,30)
        @return julian day number 
    """
    tob_in_hours = time_of_birth_as_tuple[0]+time_of_birth_as_tuple[1]/60.0+time_of_birth_as_tuple[2]/3600.0
    jd = swe.julday(date_of_birth_as_tuple[0],date_of_birth_as_tuple[1],date_of_birth_as_tuple[2],tob_in_hours)
    return jd
# Julian Day number as on (year, month, day) at 00:00 UTC
gregorian_to_jd = lambda date: swe.julday(date.year, date.month, date.day, 0.0)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)   # returns (y, m, d, fh
def jd_to_local(jd,place):
    from jhora.panchanga.drik import Date
    y, m, d,_  = jd_to_gregorian(jd)
    jd_utc = gregorian_to_jd(Date(y, m, d))
    fhl = (jd - jd_utc) * 24 + place.timezone
    return y,m,d,fhl
def deeptaamsa_range_of_planet(planet,planet_longitude_within_raasi):
    """
        get deeptaaamsa range of the planet
        @param planet: the index of the planet 0 for Sun, 1 for moon, ... 7 for Rahu and 8 for Ketu
        @param planet_longitude_within_raasi: longitude of the planet within the raasi (0.0 to 30.0 degrees)
        @return: deeptaamsa range of the planet as a tuple (deeptaamsa_minimum, deeptaamsa_maximum) 
    """
    return (planet_longitude_within_raasi-const.deeptaamsa_of_planets[planet],
            const.deeptaamsa_of_planets[planet]+planet_longitude_within_raasi) 

def local_time_to_jdut1(year, month, day, hour = 0, minutes = 0, seconds = 0, timezone = 0.0):
  """Converts local time to JD(UT1)"""
  y, m, d, h, mnt, s = swe.utc_time_zone(year, month, day, hour, minutes, seconds, timezone)
  jd_et, jd_ut1 = swe.utc_to_jd(y, m, d, h, mnt, s, cal=swe.GREG_CAL)
  return jd_ut1
def _convert_to_tamil_date_and_time(panchanga_date,time_of_day_in_hours,place=None):
    from jhora.panchanga.drik import sunset
    extra_days = 0
    sign = 1
    if time_of_day_in_hours < 0:
        extra_days = int(abs(time_of_day_in_hours/24))+1
        sign = -1
        #print(extra_days, sign)
    elif time_of_day_in_hours > 24:
        extra_days = int(abs(time_of_day_in_hours/24))
        sign = 1
    time_of_day_in_hours += - sign * extra_days*24
    #print('extra_days, sign',extra_days, sign,'time_of_day_in_hours',time_of_day_in_hours)
    #print('panchanga data before',panchanga_date)
    if extra_days !=0:
        panchanga_date = next_panchanga_day(panchanga_date, add_days=sign*extra_days)
    #print('panchanga data after',panchanga_date)
    if place  is not None: # if solar time > sunset time move to next day
        jd = gregorian_to_jd(panchanga_date)
        sunset_jd = sunset(jd, place)[0] - (place.timezone/24.)
        sunset_time = from_dms_str_to_degrees(sunset(sunset_jd,place)[1])
        if sunset_time < time_of_day_in_hours:
            new_panchanga_date = next_panchanga_day(panchanga_date, add_days=1)
            #print(panchanga_date,'sunset_time < solar_hour1',sunset_time,time_of_day_in_hours,'new_panchanga_date',new_panchanga_date)
            panchanga_date = new_panchanga_date
    #print('panchanga data returned',panchanga_date)
    return panchanga_date,time_of_day_in_hours
def previous_panchanga_day(panchanga_date,minus_days=1):
    from jhora.panchanga.drik import Date
    np_date = np.datetime64(panchanga_date)
    prev_date = np_date - np.timedelta64(minus_days,"D")
    p_date_str = np.datetime_as_string(prev_date).split('-')
    if len(p_date_str) == 4:
        p_date = Date(-int(p_date_str[1]),int(p_date_str[2]),int(p_date_str[3]))
    else:
        p_date = Date(int(p_date_str[0]),int(p_date_str[1]),int(p_date_str[2]))
    return p_date 
def next_panchanga_day(panchanga_date,add_days=1):
    from jhora.panchanga.drik import Date
    np_date = np.datetime64(panchanga_date)
    add_days_int = int(add_days)
    prev_date = np_date + np.timedelta64(int(add_days_int),"D")
    p_date_str = np.datetime_as_string(prev_date).split('-')
    #print('np_date',np_date,'add_days_int',add_days_int,'prev_date',prev_date,'p_date_str',p_date_str)
    if len(p_date_str) == 4:
        p_date = Date(-int(p_date_str[1]),int(p_date_str[2]),int(p_date_str[3]))
    else:
        p_date = Date(int(p_date_str[0]),int(p_date_str[1]),int(p_date_str[2]))
    return p_date 
def panchanga_date_diff(panchanga_date1,panchanga_date2):
    npdate1 = np.datetime64(panchanga_date1) ; npdate2 = np.datetime64(panchanga_date2)
    days_diff = (npdate2-npdate1)/np.timedelta64(1,"D")
    years_diff,days_diff = divmod(days_diff,const.sidereal_year)
    months_diff,days_diff = divmod(days_diff,(const.sidereal_year/12))
    days_diff = round(days_diff,0)
    return int(years_diff),int(months_diff),int(days_diff)
def panchanga_time_delta(panchanga_date1, panchanga_date2):#,**kwargs=None):
    np_date1 = np.datetime64(panchanga_date1)
    np_date2 = np.datetime64(panchanga_date2)
    diff_days = (np_date1-np_date2)/np.timedelta64(1,"D")
    return diff_days
def panchanga_date_to_tuple(panchanga_date): #V2.3.0
    return panchanga_date[0],panchanga_date[1],panchanga_date[2]
def date_diff_in_years_months_days(start_date_str,end_date_str,date_format_str='%Y-%m%-d'):
    start_date = dt.datetime.strptime(start_date_str,date_format_str)
    end_date = dt.datetime.strptime(end_date_str,date_format_str)
    delta = relativedelta.relativedelta(end_date, start_date)
    return delta.years,delta.months, delta.days
def get_dob_years_months_60hrs_from_today(dob,tob):
    jd_dob = julian_day_number(dob, tob)
    current_date_str,_ = dt.datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
    yt,mt,dt = map(int,current_date_str.split(','))
    jd_now = julian_day_number((yt,mt,dt), tob)
    if jd_now > jd_dob:
        years = int((jd_now-jd_dob)/const.sidereal_year)
        jdm = (jd_now-jd_dob) % const.sidereal_year
        months = int(jdm/30)
        jdh = jdm % 30
        _60hrs = int(jdh/2.5)
        return years+1,months+1,_60hrs
    else:
        return 1,1,1
def closest_elements(arr1, arr2):
    """
        Returns closest elements between arr1 and arr2
        Note: It assumes no two elements within an array are identical
    """
    result = []
    for a1 in arr1:
        for a2 in arr2:
            if a1 != a2:
                if a1 > a2:
                    result.append([a1, a2, a1-a2])
                else:
                    result.append([a1, a2, a2-a1])
    return sorted(result, key=lambda i:i[-1])[0][:2]
def _solar_mean_motion_since_1900(days_since_1900):
    """ Not working """
    i_d = int(days_since_1900)
    f_d = days_since_1900-i_d
    i_d_s = str(i_d) ; l = len(i_d_s)
    for i,c in enumerate(i_d_s):
        c1 = int(c)
        if c1!=0:
            lng = const.mean_solar_daily_motions_table_from_1900[c1-1][i]
            #print(i,c,'row',c1-1,'column',10**i,lng)
def udhayadhi_nazhikai(jd,place):
    from jhora.panchanga.drik import sunrise
    import math
    _,_,_,birth_time_hrs = jd_to_gregorian(jd)
    sunrise_time_in_float_hours = sunrise(jd, place)[0]
    """ TODO If birthtime < sunrise then it is from previous day sun rise """
    time_diff = birth_time_hrs - sunrise_time_in_float_hours
    if birth_time_hrs < sunrise_time_in_float_hours:
        sunrise_time_in_float_hours = sunrise(jd-1, place)[0]
        #print('birth time less than sunrise - previous day sunrise considered',sunrise_time_in_float_hours)
        time_diff = 24.0+birth_time_hrs-sunrise_time_in_float_hours
    hours,minutes,seconds = to_dms(time_diff,as_string=False)
    tharparai1 = (int(hours))*9000+int(minutes)*150+int(seconds)
    naazhigai = math.floor(tharparai1/3600)
    vinadigal = math.floor( (tharparai1-(naazhigai*3600))/60 )
    tharparai = math.floor(tharparai1 - naazhigai*3600 - vinadigal*60)
    return [str(naazhigai)+':'+str(vinadigal)+':'+str(tharparai),tharparai1/3600.0]
closest_element_from_list = lambda list_array, value: list_array[min(range(len(list_array)), key = lambda i: abs(list_array[i]-value))]
def get_fraction(start_time_hrs,end_time_hrs,birth_time_hrs):
    tl = end_time_hrs - start_time_hrs
    if start_time_hrs < 0:
        tl = int(abs(start_time_hrs)/24+1)*24 + end_time_hrs - abs(start_time_hrs)
    tf = min((end_time_hrs-birth_time_hrs)/tl,1.0)
    #print(start_time_hrs,end_time_hrs,birth_time_hrs,'duration',tl,'frac',tf)
    #print('birth time',birth_time_hrs, 'tithi start',tithi_start_time_hrs,'tithi end',tithi_end_time_hrs,'tithi duration',tl,'tithi fraction',tf)
    return tf
def get_fraction_old(start_time_hrs,end_time_hrs,birth_time_hrs):
    tl = end_time_hrs - start_time_hrs
    if start_time_hrs < 0:
        tl = 24 + end_time_hrs - abs(start_time_hrs)
        print('duration',tl)
    tf = (end_time_hrs-birth_time_hrs)/tl
    #print('birth time',birth_time_hrs, 'tithi start',tithi_start_time_hrs,'tithi end',tithi_end_time_hrs,'tithi duration',tl,'tithi fraction',tf)
    return tf

count_stars = lambda from_star,to_star,direction=1,total=27: ((total + direction * (to_star - from_star)) % total)+1
count_rasis = lambda from_rasi,to_rasi,direction=1,total=12: ((total + direction * (to_rasi - from_rasi)) % total)+1
def parivritti_even_reverse(dcf,dirn=1):
    """
        generates parivritti tuple (rasi_sign, hora_portion_of_varga, varga_sign)
        in this method for varga factor = 2 (hora chart)
            for the first sign hora portion increases from 0 to 1 (varga factor - 1)
            for the next sign hora portion decreases from 1 to 0
            for rasi = 0 the tuples are (0,0,0), (0,1,1) (the middle hora element 0 and 1)
            for next rasi = 1 (1,1,2), (1,0,3) (the middle hora element 1 and 0)
        in this method for varga factor = 3 (drekkana chart)
            for the first sign hora portion increases from 0 to 2
            for the next sign hora portion decreases from 2 to 0
            for rasi = 0 the tuples are (0,0,0), (0,1,1),(0,2,2) (the middle hora element increase 0,1,2)
            for next rasi = 1 (1,2,3), (1,1,4), (1,0,5) (the middle hora element decrease 2,1,0)
        @param varga divisional chart factor: 2=>Hora, 3=Drekkana etc
        @return parivritti even reverse tuple 
    """
    pc = []
    hs = 0
    for r in range(0,12,2):
        for h in range(0,dcf):
            pc.append((r,h,hs))
            hs = (hs+dirn)%12
        next_r = r + 1
        for h in range(dcf-1,-1,-1):
            pc.append((next_r,h,hs))
            hs = (hs+dirn)%12
    return pc
def parivritti_cyclic(dcf,dirn=1):
    """
        generates parivritti tuple (rasi_sign, hora_portion_of_varga, varga_sign)
        In this method each hora portion gets zodiac order of the rasis
        for rasi_sign = 0, first hora portion gets rasi=0, next hora portion gets rasi=1 and so on
        For hora chart 
            (0-15 deg) of rasi sign = 0(Ar), 15-30deg of Ar  gets next rasi = 1 (Ta) = > (0,1), 
            Now for rasi sign = 2 (Gemini) 0-15 deg is Ge (2) and 15-30 deg is Cn (3) => (2,3)
            And so on (0,1), (2,3)..
            Similarly for drekkana (0,1,2), (3,4,5), (6,7,8), (9,10,11), (0,1,2)... 
        @param varga divisional chart factor: 2=>Hora, 3=Drekkana etc
        @return parivritti cyclical tuple 
    """
    pc = []
    hs = 0
    for _ in range(12):
        t = tuple()
        for _ in range(dcf):
            t += (hs%12,); hs = (hs+dirn)%12
        pc.append(t)
    return pc
def parivritti_alternate(dcf,dirn=1):
    """
        Generates alternate parivritti tuple. Used for Somanatha method
        Odd Rasis get increasing rasis from Ar. Even rasis get decreasing rasis from Pi
        For Hora Ar = (Ar,Ta), Ta = (Pi, Aq), Ge = (Ge,Cn), Cn = (Cp,Sg) and so on
        @param varga divisional chart factor: 2=>Hora, 3=Drekkana etc
        @return parivritti alternate tuple 
    """
    pc = []
    hs1 = 0; hs2 = 11
    for _ in range(0,12,2):
        t1 = tuple(); t2 = tuple()
        for _ in range(dcf):
            t1 += (hs1%12,); hs1 = (hs1+dirn)%12
            t2 += (hs2%12,); hs2 = (hs2-dirn)%12
        pc.append(t1); pc.append(t2)
    return pc
    
def __varga_non_cyclic(dcf, base_rasi=0, start_sign_variation=1, count_from_end_of_sign=False):
    """
        Generates varga non_cyclic varga rasi tuple (rasi_sign, hora_portion_of_varga, varga_sign)
        ... (your existing docstrings) ...
    """
    pc = []
    
    for sign in range(12):
        # FIX 1: Reset direction to forward at the start of EVERY sign
        dirn = 1 
        
        # 1. Determine the initial base seed (0 for Aries, or the sign itself)
        seed = 0 if base_rasi == 0 else sign
        
        # 2. Apply the start_sign_variation to find the normal forward starting sign
        start_sign = seed
        
        if start_sign_variation == 1 and sign in const.even_signs: start_sign = (seed + 6) % 12
        elif start_sign_variation == 2 and sign in const.even_signs: start_sign = (seed + 8) % 12
        elif start_sign_variation == 3 and sign in const.even_signs: start_sign = (seed + 4) % 12
        elif start_sign_variation == 4 and sign in const.even_signs: start_sign = (seed + 10) % 12
        elif start_sign_variation == 5 and sign in const.even_signs: start_sign = (seed + 2) % 12
        elif start_sign_variation == 6:
            if sign in const.fixed_signs: start_sign = (seed + 4) % 12
            elif sign in const.dual_signs: start_sign = (seed + 8) % 12
        elif start_sign_variation == 7:
            if sign in const.fixed_signs: start_sign = (seed + 8) % 12
            elif sign in const.dual_signs: start_sign = (seed + 4) % 12
        elif start_sign_variation == 8:
            if sign in const.earth_signs: start_sign = (seed + 3) % 12
            elif sign in const.air_signs: start_sign = (seed + 6) % 12
            elif sign in const.water_signs: start_sign = (seed + 9) % 12
        elif start_sign_variation == 9:
            if sign in const.earth_signs: start_sign = (seed + 9) % 12
            elif sign in const.air_signs: start_sign = (seed + 6) % 12
            elif sign in const.water_signs: start_sign = (seed + 3) % 12
            
        # FIX 2 & 3: Apply the backward calculation AFTER the base mapping, 
        # and base it on the newly calculated `start_sign`, not the raw `sign`.
        if count_from_end_of_sign and sign in const.even_signs:
            # Shift the start sign backward by (dcf - 1)
            start_sign = (start_sign - dcf + 1) % 12
            dirn = -1

        # Generate the tuple for this sign mathematically 
        t = tuple((start_sign + dirn * h) % 12 for h in range(dcf))
        pc.append(t)
        
    return pc
def _index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return -1
def _convert_1d_house_data_to_2d(rasi_1d,chart_type=None):
    if chart_type is None: chart_type = const.default_chart_type
    separator = '/'
    if chart_type  == const.CHART_STYLE.SOUTH_INDIAN_REGULAR:
        row_count = 4
        col_count = 4
        map_to_2d = [ [11,0,1,2], [10,"","",3], [9,"","",4], [8,7,6,5] ]
    elif chart_type  == const.CHART_STYLE.SOUTH_INDIAN_IRREGULAR:
        row_count = 4
        col_count = 4
        map_to_2d = [ [2,1,0,11], [3,"","",10], [4,"","",9], [5,6,7,8] ]
    elif chart_type in [const.CHART_STYLE.EAST_INDIAN_WITH_FRAME, const.CHART_STYLE.EAST_INDIAN_NO_FRAME]:
        row_count = 3
        col_count = 3
        map_to_2d = [['2'+separator+'1','0','11'+separator+'10'], ['3', "",'9' ], ['4'+separator+'5','6','7'+separator+'8']]
    rasi_2d = [['X']*row_count for _ in range(col_count)]
    for p,val in enumerate(rasi_1d):
        for index, row in enumerate(map_to_2d):
            if chart_type in [const.CHART_STYLE.SOUTH_INDIAN_IRREGULAR, const.CHART_STYLE.SOUTH_INDIAN_REGULAR]:
                i,j = [(index, row.index(p)) for index, row in enumerate(map_to_2d) if p in row][0]
                rasi_2d[i][j] = str(val)
            elif chart_type in [const.CHART_STYLE.EAST_INDIAN_WITH_FRAME, const.CHART_STYLE.EAST_INDIAN_NO_FRAME]:
                p_index = _index_containing_substring(row,str(p))
                if p_index != -1:
                    i,j = (index, p_index)
                    if rasi_2d[i][j] != 'X':
                        if index > 0:
                            rasi_2d[i][j] += separator + str(val)
                        else:
                            rasi_2d[i][j] = str(val) + separator + rasi_2d[i][j]
                    else:
                        rasi_2d[i][j] = str(val)
    for i in range(row_count):
        for j in range(col_count):
            if rasi_2d[i][j] == 'X':
                rasi_2d[i][j] = ''
    return rasi_2d
get_prasna_lagna_KP_249_for_rasi_chart = lambda kp_no: const.prasna_kp_249_dict[kp_no][0]
get_prasna_lagna_KP_249_for_varga_chart = lambda kp_no,varga_no=1: \
    int(0.5*(const.prasna_kp_249_dict[kp_no][2]+const.prasna_kp_249_dict[kp_no][3])//(30.0/varga_no))%12 if varga_no>1 \
    else get_prasna_lagna_KP_249_for_rasi_chart(kp_no)

get_prasna_lagna_108_for_rasi_chart = lambda kp_no: kp_no//9
get_prasna_lagna_108_for_navamsa = lambda kp_no: 11 if (kp_no%12==0) else (kp_no%12)-1 
get_prasna_lagna_108_for_varga_chart = lambda nadi_no,varga_no=1: \
    get_prasna_lagna_108_for_rasi_chart(nadi_no) if varga_no==1 else \
    (get_prasna_lagna_108_for_navamsa(nadi_no) if varga_no==9 else int(nadi_no//(108/varga_no))%12)
get_prasna_lagna_nadi_for_rasi_chart = lambda nadi_no: nadi_no//150
get_prasna_lagna_nadi_for_varga_chart = lambda nadi_no,varga_no=1: \
    int(nadi_no//(150/varga_no))%12 if varga_no>1 else get_prasna_lagna_nadi_for_rasi_chart(nadi_no)
# Get row,col of the element that contains a string
get_2d_list_index = lambda matrix,search_string,contains_in_element=False: next((i, j) for i, row in enumerate(matrix) \
                        for j, element in enumerate(row) if (contains_in_element and search_string in element) \
                            or (not contains_in_element and search_string == element))
get_1d_list_index = lambda matrix, search_string, contains_in_element=False: \
    next((i for i, element in enumerate(matrix) if (contains_in_element and search_string in element) \
            or (not contains_in_element and search_string == element)), None)
get_KP_nakshathra_from_kp_no = lambda kp_no: const.prasna_kp_249_dict[kp_no][1]
get_KP_details_from_planet_longitude = lambda planet_longitude: \
    {kp_no:[r,n,sd,ed,rl,sl,ssl] for kp_no,[r,n,sd,ed,rl,sl,ssl] in const.prasna_kp_249_dict.items() \
     if planet_longitude >= (r*30+sd) and planet_longitude <= (r*30+ed)}
# Search and replace a string from element of 1d/2d list
def search_replace(input_list, s1, s2):
    if isinstance(input_list[0], list):  # Check if the input_list is a 2D list
        return [[element.replace(s1, s2) if s1 in element else element for element in row] for row in input_list]
    else:  # It's a 1D list
        return [element.replace(s1, s2) if s1 in element else element for element in input_list]
# Lambda function for cyclic counting if stars in the range 1 to 28 (including Abhijit as 22
cyclic_count_of_stars_with_abhijit_in_22 = lambda lst, from_star, to_star: \
                                                (lambda start_idx, end_idx: 
                (end_idx - start_idx + 1) % len(lst) if start_idx <= end_idx else len(lst) - start_idx + end_idx + 1)(lst.index(from_star), lst.index(to_star))
cyclic_count_of_stars_with_abhijit = lambda from_star, count, direction=1,star_count=28: ((from_star - 1 + (count - 1) * direction) % star_count) + 1
cyclic_count_of_stars = lambda from_star, count, direction=1:cyclic_count_of_stars_with_abhijit(from_star, count, direction,star_count=27)
cyclic_count_of_stars_without_abhijit = lambda from_star, count, direction=1:cyclic_count_of_stars_with_abhijit(from_star, count, direction,star_count=27)
cyclic_count_of_numbers = lambda from_number, to_number, direction=1,number_count=30: \
    ((from_number - 1 + (to_number - 1) * direction) % number_count) + 1
def triguna_of_the_day_time(day_index, time_of_day):
    keys = sorted(const.triguna_days_dict.keys())
    
    # Finding min key and next key
    min_key = max((k for k in keys if k <= time_of_day), default=keys[-1])
    next_key = min((k for k in keys if k > min_key), default=keys[0])
    
    return const.triguna_days_dict[min_key][day_index], min_key, next_key
def date_time_string_to_date_time_tuple(date_time_string):
    """ convert 1998-03-01 13:30:00 PM to (1998,3,1,13.5) """
    date_time_string.replace("AM","").replace("PM","")
    dstr,tstr = date_time_string.split(" ")
    y,m,d = dstr.strip().split("-")
    hh,mm,ss = tstr.strip().split(":")
    t1 = int(hh)+int(mm)/60.0+int(ss)/3600.0
    return (int(y),int(m),int(d),float(t1))
def julian_day_to_date_time_string(jd):
    y, m, d, h = jd_to_gregorian(jd)
    t = to_dms(h, as_string=True,use_24hour_format=True)
    ampm = "AM" if 0 <= h < 12 else "PM"
    return f"{y:04d}-{m:02d}-{d:02d} {t} {ampm}"
def date_time_tuple_to_date_time_string(y,m,d,h):
    t = to_dms(h, as_string=True,use_24hour_format=True)
    ampm = "AM" if 0 <= h < 12 else "PM"
    return f"{y:04d}-{m:02d}-{d:02d} {t} {ampm}"
def get_nakshathra_list_with_abhijith():
    return [NAKSHATRA_LIST[s] for s in range(20)]+[NAKSHATRA_LIST[27]]+[NAKSHATRA_LIST[s] for s in range(20,27)]
karana_lord = lambda karana_index: [_karana_lord for _karana_lord,kar_list in const.karana_lords.items() if karana_index in kar_list[0]][0]
nakshathra_lord = lambda nak_no: const.nakshatra_lords[nak_no-1]
kali_yuga_jd = lambda jd: jd - swe.julday(-3101,1,23,12,cal=swe.JUL_CAL)
def get_year_month_day_from_date_format(date_text):
    # Detect BCE year based on the count of hyphens
    is_bce = False
    hyphen_count = date_text.count('-')
    if hyphen_count in [1,4]:
        is_bce = True
        date_text = date_text[1:]  # Remove the minus sign for parsing
    parts = date_text.split(',')
    if len(parts) == 3 and len(parts[0]) < 4:
        parts[0] = parts[0].zfill(4)
        date_text = ','.join(parts)
    # Define possible date formats
    date_formats = [
        "%d/%m/%Y",  # 29/03/2025
        "%d/%m/%y",  # 29/03/25
        "%Y,%m,%d",  # 2025,02,09
        "%Y-%m-%d",  # 2025-02-09
        "%d-%m-%Y",  # 09-02-2025
        "%m/%d/%Y",  # 02/09/2025
        "%d/%m/%Y",  # 09/02/2025
        "%Y/%m/%d",  # 2025/02/09
        "%B %d, %Y",  # February 09, 2025
        "%b %d, %Y",  # Feb 09, 2025
        "%y,%m,%d",  # 25,02,09
        "%y-%m-%d",  # 25-02-09
        "%d-%m-%y",  # 09-02-25
        "%m/%d/%y",  # 02/09/25
        "%d/%m/%y",  # 09/02/25
        "%y/%m/%d",  # 25/02/09
    ]
    
    # Try to parse the date using the defined formats
    for fmt in date_formats:
        try:
            date_obj = dt.datetime.strptime(date_text, fmt)
            if is_bce:
                date_obj = -date_obj.year,date_obj.month,date_obj.day
                return date_obj
            else:
                return date_obj.year, date_obj.month, date_obj.day
        except ValueError:
            continue
    # If no format matches, return None
    return map(int,date_text.split(','))
def vaakya_tamil_month(year, month_number):
    """
        Ref: https://groups.google.com/g/mintamil/c/DSXP2KHvgRw - by Ravi Annaswamy
    """
    tamil_month_names = 'சித்திரை,வைகாசி,ஆனி,ஆடி,ஆவணி,புரட்டாசி,ஐப்பசி,கார்த்திகை,மார்கழி,தை,மாசி,பங்குனி'.split(',')

    tamil_month_start_days = \
    [0,
     30.925555,
     62.328888,
     93.939444,
     125.409444,
     156.445555,
     186.901666,
     216.803611,
     246.310277,
     275.658333,
     305.112777,
     334.919444]
    
    
    # Step 1: Calculate how many Kali years are over.
    # Kali yuga started 3101 B.C. when all planets were aligned on one
    # star on other side of earth, so invisible in India.
    kali_year_finished = year+3101
    #print('Year:', year, 'Finished kali:', kali_year_finished)
    
    # Step 2: Count the number of solar years in days
    kd_base = 365.25868055555554 * kali_year_finished
    
    # Step 3: Adjust for Kali arrival delay time. This count represents
    # absolute count of days for this year's new year day.
    kali_sudda_dinam = kd_base - 2.147569444444444
    
    # Step 4: Calculate month start by adding the start days of the month according to
    # Aryabhatiya approximation for average month lengths.
    month_start_kd = kali_sudda_dinam + tamil_month_start_days[month_number-1]
    
    # Step 5: If this happened after sunset, then make the next day 
    kddays=int(month_start_kd)
    kdhours=month_start_kd-kddays
    hours=int(kdhours*24)
    #print(hours)
    minutes=round(((kdhours*24)-hours)*60)
    #print(hours,minutes)
    if kdhours>0.5:
        kddays+=1
    #print(kddays)
    
    # Step 6: Find the day of the week
    weekday = 'வெள்ளி சனி ஞாயிறு திங்கள் செவ்வாய் புதன் வியாழன்'.split()[kddays%7]
    
    # Step 7: Convert to English date.
    # January 1st of 1900 was Kali yuga's 1826555'th day
    # See how many days have elapsed since and add to English date.
    diff=kddays-1826555
    month_birthday = dt.datetime(1900,1,1,0,0,0)+dt.timedelta(days=diff)
    
    # Step 8: To calculate how many days in this month, find next month start.
    if month_number < 12:
        next_mon_kd = kali_sudda_dinam + tamil_month_start_days[month_number]
    else:
        next_mon_kd = kali_sudda_dinam + 365.258680555
    if next_mon_kd - int(next_mon_kd)>0.5:
        next_mon_kd=int(next_mon_kd)+1
    else:
        next_mon_kd=int(next_mon_kd)
    next_mon_birthday = dt.datetime(1900,1,1,0,0,0)+dt.timedelta(days=next_mon_kd-1826555)
    num_days_in_this_month = (next_mon_birthday-month_birthday).days
    
    return tamil_month_names[month_number-1], dt.datetime.strftime(month_birthday, '%d-%m-%Y'), weekday, num_days_in_this_month, month_start_kd
def _validate_language_resources(lang):
    set_language(lang)
def trim_info_list_lines(info_lines: list[str], skip_lines: int) -> list[str]:
    """
    Trims the info_lines list by removing the last `skip_lines` before the final "Show more" line.
    Handles cases where the last line may be empty and "Show more" is second-to-last.

    Parameters:
        info_lines (list[str]): The full info list as a list of lines.
        skip_lines (int): Number of lines to skip before the "Show more" line.

    Returns:
        list[str]: The trimmed list of lines.
    """
    if skip_lines == 0 or len(info_lines) <= skip_lines:
        return info_lines

    # Identify the "Show more" line (last non-empty line)
    show_more_index = None
    for i in reversed(range(len(info_lines))):
        if info_lines[i].strip():  # skip empty lines
            show_more_index = i
            break

    if show_more_index is None or show_more_index <= skip_lines:
        return info_lines  # not enough lines to trim

    # Calculate the index to slice up to
    trimmed_end_index = show_more_index - skip_lines

    # Create the trimmed list
    trimmed_lines = info_lines[:trimmed_end_index]

    # Add the original "Show more" line back
    trimmed_lines.append(info_lines[show_more_index])

    return trimmed_lines
def get_varga_option_dict():
    global resource_strings
    from jhora import config  # Import your config manager
    
    """ dict: {dcf:(method_count,method_index,base_rasi_index,count_from_end_of_sign)}"""
    _varga_option_dict = {}; _res = resource_strings
    
    if const.TREAT_STANDARD_CHART_AS_CUSTOM:
        _varga_option_dict[1] = (None,None,None,None)
        for dcf in range(2,const.MAX_DHASAVARGA_FACTOR+1):                
            _opt_count = len([k for k in _res.keys() if 'dn_custom_option' in k ])
            
            # Fetch user's saved choice from config (fallback to 0)
            # *Note: adjust the key "varga_d{dcf}_method" to match your factory_settings.json
            saved_idx = config.get_value(f"d{dcf}_chart_method_default", 1)
            _varga_option_dict[dcf] = (_opt_count, saved_idx, None, None)
    else:
        _varga_option_dict[1] = (None,None,None,None)
        for dcf in const.division_chart_factors[1:]:
            _opt_count = len([k for k in _res.keys() if 'd'+str(dcf)+'_option' in k ])
            
            # Fetch user's saved choice from config (fallback to 1)
            saved_idx = config.get_value(f"d{dcf}_chart_method_default", 1)
            _varga_option_dict[dcf] = (_opt_count, saved_idx, None, None)
            
        for dcf in [d for d in range(2,const.MAX_DHASAVARGA_FACTOR+1) if d not in const.division_chart_factors]:                
            _opt_count = len([k for k in _res.keys() if 'dn_custom_option' in k ])
            
            # Fetch user's saved choice from config (fallback to 0)
            saved_idx = config.get_value(f"d{dcf}_chart_method_default", 1)
            _varga_option_dict[dcf] = (_opt_count, saved_idx, None, None)
    return _varga_option_dict
def _get_varga_option_dict():
    global resource_strings
    """ dict: {dcf:(method_count,method_index,base_rasi_index,count_from_end_of_sign)}"""
    _varga_option_dict = {}; _res = resource_strings
    if const.TREAT_STANDARD_CHART_AS_CUSTOM:
        _varga_option_dict[1] = (None,None,None,None)
        for dcf in range(2,const.MAX_DHASAVARGA_FACTOR+1):                
            _opt_count = len([k for k in _res.keys() if 'dn_custom_option' in k ])
            _varga_option_dict[dcf] = (_opt_count,0,None,None)
    else:
        _varga_option_dict[1] = (None,None,None,None)
        for dcf in const.division_chart_factors[1:]:
            _opt_count = len([k for k in _res.keys() if 'd'+str(dcf)+'_option' in k ])
            _varga_option_dict[dcf] = (_opt_count,1,None,None)
        for dcf in [d for d in range(2,const.MAX_DHASAVARGA_FACTOR+1) if d not in const.division_chart_factors]:                
            _opt_count = len([k for k in _res.keys() if 'dn_custom_option' in k ])
            _varga_option_dict[dcf] = (_opt_count,0,None,None)
    return _varga_option_dict
def is_planet_in_moolatrikona(planet_id, p_pos_tuple=None, chart_1d_house=None, enforce_trikona_degrees=False):
    """
    Checks if a planet is in its Moolatrikona range.
    - If enforce_trikona_degrees is True and p_pos_tuple is provided: checks Sign AND Longitude.
    - Otherwise: checks Sign only (using p_pos_tuple[0] or chart_1d_house).
    """
    m_sign, m_start, m_end = const.moola_trikona_range_of_planets.get(planet_id, (None, None, None))
    
    # Priority 1: Precision check (Sign + Degree)
    if p_pos_tuple is not None and enforce_trikona_degrees:
        sign, lon = p_pos_tuple
        return sign == m_sign and m_start <= lon <= m_end
    # Priority 2: Zodiac check from tuple
    if p_pos_tuple is not None:
        return p_pos_tuple[0] == m_sign
    # Priority 3: Zodiac check from 1D house index
    return chart_1d_house == m_sign
def is_planet_in_exalation(planet,planet_house,planet_positions=None,enforce_deep_exaltation=True):
    if planet_positions is not None and enforce_deep_exaltation and planet in const.SUN_TO_SATURN:
        sign_idx, lon_in_sign = planet_positions[planet + 1][1]
        abs_longitude = (sign_idx * 30) + lon_in_sign
        deep_ex_lon = const.planet_deep_exaltation_longitudes[planet]
        if abs(abs_longitude - deep_ex_lon) <= const.planet_deep_exaltation_tolerance:
            return True
    else:
        if const.house_strengths_of_planets[planet][planet_house] >= const._EXALTED_UCCHAM:
            return True
    return False
def is_planet_strong(planet,planet_house,include_neutral_samam=False):
    """ 
        If include_neutral_samam = True >= const.SAMAM_NEUTRAL
        else: >= const._FRIEND
    """
    if include_neutral_samam:
        return const.house_strengths_of_planets[planet][planet_house] >= const._NEUTRAL_SAMAM
    else:
        return const.house_strengths_of_planets[planet][planet_house] >= const._FRIEND
def is_planet_in_debilitation(planet,planet_house,planet_positions=None,enforce_deep_debilitation=True):
    if (planet_positions is not None and enforce_deep_debilitation and 
            planet not in [const.KETU_ID, const.RAHU_ID, const._ascendant_symbol]): 
        sign_idx, lon_in_sign = planet_positions[planet + 1][1]
        abs_longitude = (sign_idx * 30) + lon_in_sign
        deep_ex_lon = const.planet_deep_debilitation_longitudes[planet]
        if abs(abs_longitude - deep_ex_lon) <= const.planet_deep_debilitation_tolerance:
            return True
    else:
        if const.house_strengths_of_planets[planet][planet_house] == const._DEBILITATED_NEECHAM:
            return True
    return False

def is_planet_weak(
    planet: int,
    planet_house: int,
    planet_to_house_dict: dict | None = None,
    planet_positions: dict | None = None,
    asc_house: int | None = None,
    enforce_deep_debilitation: bool = False,
    check_malefic_affliction: bool = True,
    natural_malefics: set | None = None,
    check_dusthana: bool = True,
    check_combustion: bool = True,
    explain: bool = False
):
    """
    Determine whether `planet` is weak using whichever inputs are available.

    Works with partial data:
      - If only planet_house is given → matrix debilitation.
      - If planet_positions is given → deep debilitation, combustion, malefic affliction become available.
      - If asc_house is given → dusthana test can be done relative to asc.

    Criteria applied when data allows:
      1) Debilitated by sign (matrix-based)            [needs planet_house]
      2) Deep debilitation by longitude                [needs planet_positions & enforce_deep_debilitation]
      3) Afflicted by malefics (aspect/conjunction)    [needs planet_positions]
      4) Dusthana placement (6/8/12)                   [needs asc_house]
      5) Combustion relative to Sun                    [needs planet_positions]

    Args:
        planet: int (0..8) planet id per your scheme.
        planet_house: int (0..11) zodiac index of the planet (sign/house index).
        planet_to_house_dict: {'L":1,0:6,....} Planet to House dictionary
        planet_positions: dict with longitude info; if None, longitude-based checks are skipped.
        asc_house: int ascendant index (0..11); if None, dusthana check is skipped.
        enforce_deep_debilitation: bool: use deep debilitation tolerance when possible.
        check_malefic_affliction: bool: attempt malefic affliction when possible.
        natural_malefics: set|None: override malefics; defaults to const.natural_malefics.
        check_dusthana: bool: check 6/8/12 relative to asc_house (if asc_house is provided).
        check_combustion: bool: check combustion if positions exist.
        combustion_orb_degrees: float|None: override sun-combustion orb; otherwise use const.combustion_orb_degrees[planet].
        explain: bool: if True, return (weak_bool, details_dict); else return weak_bool.

    Returns:
        bool or (bool, dict): weakness flag; optionally with explanation per criterion used.
    """
    details = {}

    # 1) Debilitated by sign (matrix-based)
    debilitated_by_sign = (const.house_strengths_of_planets[planet][planet_house] <= const._DEBILITATED_NEECHAM)
    details['debilitated_by_sign'] = debilitated_by_sign

    # 2) Deep debilitation by longitude (optional)
    deep_debilitation = False
    if planet_positions is not None and enforce_deep_debilitation and planet in const.SUN_TO_SATURN:
        sign_idx, lon_in_sign = planet_positions[planet + 1][1]
        abs_longitude = (sign_idx * 30.0) + lon_in_sign
        deep_deb_lon  = const.planet_deep_debilitation_longitudes[planet]
        deep_debilitation = (abs(abs_longitude - deep_deb_lon) <= const.planet_deep_debilitation_tolerance)
    details['deep_debilitation'] = deep_debilitation if planet_positions is not None else None

    # 3) Malefic affliction (optional, requires positions)
    afflicted_by_malefic = False
    if check_malefic_affliction and planet_positions is not None:
        from jhora.horoscope.chart import house
        house_to_planet_list = get_house_planet_list_from_planet_positions(planet_positions)
        planet_aspects = house.planets_aspecting_the_planet(house_to_planet_list, planet)
        _natural_malefics = natural_malefics if natural_malefics is not None else const.natural_malefics
        afflicted_by_malefic = any(m in planet_aspects for m in _natural_malefics)
    details['afflicted_by_malefic'] = afflicted_by_malefic if planet_positions is not None else None

    # 4) Combustion (optional, requires positions)
    combust = False
    if check_combustion:
        if planet_positions is not None:
            from jhora.horoscope.chart import charts
            combust_set = charts.planets_in_combustion(planet_positions, use_absolute_longitude=True)
            combust = (planet in combust_set)
        elif planet_to_house_dict is not None:
            combust = planet_to_house_dict[const.SUN_ID]==planet_to_house_dict[planet] #Planet same house as Sun
    details['combust'] = combust if planet_positions is not None else None
    
    # 5) Check Dusthanasa
    weak_by_dusthana = False
    from jhora.horoscope.chart import house
    if check_dusthana:
        weak_by_dusthana = planet_house in house.dushthanas_of_the_raasi(asc_house)
        details['dusthana'] = weak_by_dusthana
    # Final decision across available criteria
    weak = (
        debilitated_by_sign
        or (details['deep_debilitation'] or False)
        or (details['afflicted_by_malefic'] or False)
        or (details['combust'] or False)
        or (details['dusthana'] or False)
    )

    return (weak, details) if explain else weak

def remove_tropical_planets_from_chart(chart_1d):
    to_remove = [str(const.URANUS_ID), str(const.NEPTUNE_ID),str(const.PLUTO_ID)]
    result = []
    for item in chart_1d[:]:
        parts = item.split('/')
        new_parts = [p for p in parts if p not in to_remove]
        new_string = "/".join(new_parts)
        result.append(new_string)
    return result
def get_amsa_ruler_from_planet_longitude(planet_longitude, planet_house):
    base_idx = int((planet_longitude * 2) % 60) 
    if planet_house % 2 == 0:  # Even Sign
        return 59 - base_idx
    else:                    # Odd Sign
        return base_idx
is_cruel_shashtiamsa_ruler = lambda deity_index : deity_index in const.shashti_amsa_rulers_kroora
is_kroora_shashtiamsa_ruler = lambda deity_index : is_cruel_shashtiamsa_ruler(deity_index)
is_soumya_shashtiamsa_ruler = lambda deity_index : deity_index in const.shashti_amsa_rulers_soumya
is_good_shashtiamsa_ruler = lambda deity_index : is_soumya_shashtiamsa_ruler(deity_index)
def show_exception(e: Exception, debug=True):
    _DEBUG_APP = debug
    import inspect, traceback
    def print_outer_frames():
        print('JHora: showing complete trace...')
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        for i, f in enumerate(outer_frames):
            print(f"JHora: [{i}] File: {os.path.basename(f.filename)}, Function: {f.function}, Line: {f.lineno}")
    def print_full_traceback(e: Exception):
        tb = traceback.extract_tb(e.__traceback__)
        if _DEBUG_APP: print("JHora: Full traceback:\n")
        for i, frame in enumerate(tb):
            file_name = os.path.basename(frame.filename)
            function_name = frame.name
            line_number = frame.lineno
            code_line = frame.line
            print(f"JHora: [{i}] File: {file_name}, Function: {function_name}, Line: {line_number}\n")
            print(f"JHora:     Code: {code_line}\n")
    tb = traceback.extract_tb(e.__traceback__)
    if tb:
        last_trace = tb[-1]
        file_name = os.path.basename(last_trace.filename)
        function_name = last_trace.name
        line_number = last_trace.lineno
        outer_frames_list = []
    else:
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        file_name = os.path.basename(outer_frames[1].filename)
        function_name = outer_frames[1].function
        line_number = outer_frames[1].lineno
        print_outer_frames()
    log_message = f"JHora: [ERROR] {file_name}:{function_name}:{line_number} - {str(e)}\n outer_frames:{outer_frames_list}"
    if _DEBUG_APP: print("JHora: ",log_message)
    print_full_traceback(e)

# --- Sign formatting helpers ---

SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

def norm360(x: float) -> float:
    """Normalize any angle to [0, 360)."""
    return x % 360.0

def deg_to_sign_str(
    lon_deg: float,
    zero_pad_deg: bool = True,
    include_seconds: bool = True,
    sec_precision: int = 2
) -> str:
    """
    Convert a ecliptic longitude in [0,360) to JHora-style string.

    Examples:
        89.5833  (≈ 29 Ge 35' ) -> '29Ge35'
        75.5     (≈ 15 Ge 30' ) -> '15Ge30'
        293.56816 (≈ 23 Cp 34' 05.38") with include_seconds=True -> '23Cp34\'05.38"'
    """
    lon = norm360(lon_deg)  # expects 0..360; norm handles anything

    # Determine sign and within-sign longitude
    sign_idx = int(lon // 30.0)
    sign_abbr = SIGN_ABBR[sign_idx]
    within = lon - sign_idx * 30.0  # 0..30

    # Degrees within sign
    d = int(within)  # 0..29

    if include_seconds:
        # Minutes & seconds (with carry handling)
        minutes_exact = (within - d) * 60.0          # 0..60
        m = int(minutes_exact)                       # 0..59
        seconds_exact = (minutes_exact - m) * 60.0   # 0..60

        # Round seconds and carry if needed
        s = round(seconds_exact, sec_precision)
        if s >= 60.0:
            s = 0.0
            m += 1

        # Carry minutes to degrees if needed
        if m >= 60:
            m = 0
            d += 1
            if d >= 30:
                d = 0
                sign_idx = (sign_idx + 1) % 12
                sign_abbr = SIGN_ABBR[sign_idx]

        # Build components
        d_str = f"{d:02d}" if zero_pad_deg else f"{d}"
        m_str = f"{m:02d}"
        # Seconds as fixed precision (e.g., 05.37 or 5.37). JHora typically shows 2-digit minutes;
        # for seconds, it’s acceptable without leading zero on the seconds field. We’ll keep no leading zero.
        s_str = f"{s:.{sec_precision}f}".rstrip('0').rstrip('.') if sec_precision > 0 else f"{int(s)}"

        return f"{d_str}{sign_abbr}{m_str}'{s_str}\""

    else:
        # Minutes only (original behavior), with rounding and carry
        m = int(round((within - d) * 60.0))  # 0..60 (may round up)
        if m == 60:
            m = 0
            d += 1
            if d == 30:
                d = 0
                sign_idx = (sign_idx + 1) % 12
                sign_abbr = SIGN_ABBR[sign_idx]

        d_str = f"{d:02d}" if zero_pad_deg else f"{d}"
        return f"{d_str}{sign_abbr}{m:02d}"

def format_triplet(triple, labels=("Start", "Cusp", "End")) -> str:
    """
    Given a (start, mid/cusp, end) triple in degrees, return a single formatted line.
    """
    s, c, e = triple
    return f"{labels[0]}: {deg_to_sign_str(s)}, {labels[1]}: {deg_to_sign_str(c)}, {labels[2]}: {deg_to_sign_str(e)}"

def print_bhava_houses(bhava_houses, start_label="Start", mid_label="Cusp", end_label="End"):
    """
    Pretty-print a list of 12 (start, mid, end) triples in JHora-like notation.
    """
    for i, triple in enumerate(bhava_houses, start=1):
        s, m, e = triple
        line = format_triplet((s, m, e), (start_label, mid_label, end_label))
        print(f"House {i:02d}: {line}")

""" KP Lord Calculation Functions Start here """
from typing import Dict, List, Union

# ---- Required constants (already in your env) ----
# const.vimsottari_adhipati_list = [8, 5, 0, 1, 2, 7, 4, 6, 3]  # Ketu,Venus,Sun,Moon,Mars,Rahu,Jupiter,Saturn, Mercury
# const.vimsottari_dict          = {8:7, 5:20, 0:6, 1:10, 2:7, 7:18, 4:16, 6:19, 3:17}
# const._house_owners_list       = [...]  # sign lords for 0..11 (Ar..Pi) in your planet ID scheme

VIMS_ORDER: List[int] = const.vimsottari_adhipati_list
VIMS_YEARS: Dict[int, int] = const.vimsottari_dict
ORDER_POS = {pid: i for i, pid in enumerate(VIMS_ORDER)}  # to avoid .index() calls

NAK_MIN = 13 * 60 + 20  # 800 arc-minutes per Nakshatra

def kp_lords_for_longitude(
    planet_label: Union[int, str],
    lon_deg: float,
    include_sign_lord: bool = False,
    include_kp_index: bool = True,
    levels: int = 5  # 6 => Sub, Praty, Sookshma, Praana, Deha (+ star always returned)
) -> Dict[Union[int, str], List[int]]:
    """
    Iterative KP micro-lord calculator (single function).
    Returns {planet_label: [kp_index?, (sign_lord?), star, sub, praty, sookshma, praana, deha]}.
    """
    # --- normalize input ---
    lon = lon_deg % 360.0

    out: List[int] = []

    # --- KP index (1..249) O(1) formula ---
    if include_kp_index:
        kp_index = int((lon * 249.0) // 360.0) + 1
        if kp_index < 1: kp_index = 1
        elif kp_index > 249: kp_index = 249
        out.append(kp_index)

    # --- optional sign lord ---
    if include_sign_lord:
        sign_idx = int(lon // 30.0)     # 0..11
        out.append(const._house_owners_list[sign_idx])

    # --- Nakshatra index (0..26) & offset minutes within that Nakshatra ---
    total_min = lon * 60.0
    nak_idx = int(total_min // NAK_MIN)             # 0..26
    off_in_nak = total_min - nak_idx * NAK_MIN      # 0..800

    # --- Star lord (9-cycle repeats) ---
    star_lord = VIMS_ORDER[nak_idx % 9]
    out.append(star_lord)

    # --- Walk down the KP micro-levels iteratively ---
    # Level 1: Sub (inside Nakshatra of length 800′, starting from star_lord)
    # Then keep descending: parent_len, start_lord, and offset shrink each time.
    parent_len = float(NAK_MIN)   # in arc-minutes (800.0)
    start_lord = star_lord
    offset = off_in_nak
    eps = 1e-9

    # guard: clamp levels to [1..6] if someone changes default
    levels = max(1, min(6, int(levels)))

    for lvl in range(levels):  # 6 → Sub, Praty, Sookshma, Praana, Deha
        # Split parent into 9 KP parts, starting from 'start_lord'
        one_year = parent_len / 120.0  # divide once; multiply by years for each segment
        acc = 0.0

        start_pos = ORDER_POS[start_lord]
        chosen_lord = start_lord
        chosen_len = parent_len
        chosen_off = 0.0

        for i in range(9):
            pid = VIMS_ORDER[(start_pos + i) % 9]
            seg_len = VIMS_YEARS[pid] * one_year
            nxt = acc + seg_len
            # inclusive last segment to avoid boundary flip-flop
            if offset < (nxt + (eps if i < 8 else 10 * eps)):
                chosen_lord = pid
                chosen_len = seg_len
                chosen_off = max(0.0, offset - acc)
                break
            acc = nxt
        # append this level's lord
        out.append(chosen_lord)
        # descend into the chosen segment
        start_lord = chosen_lord
        parent_len = chosen_len
        offset = chosen_off

    return {planet_label: out}
""" KP Lord Calculation Functions End here """
def _set_flags_for_planet_positions(
    *,
    sidereal_positions: bool = True,          # False = tropical
    geometric_positions: bool = True,         # False = topocentric (observer-based)
    true_positions: bool = True,              # False = apparent
    use_aberration_of_light: bool = True,     # False -> disable aberration
    use_gravitational_deflection: bool = False, # True to include deflection; default Swiss Ephemeris includes it for apparent
    use_nutation: bool = False,               # True to include nutation (true equator/ecliptic of date)
    include_default_engine: bool = True,       # optionally include swe.FLG_SWIEPH here
    include_speed = True, # required for planet speed calculations
) -> int:
    """
    Return flags for swe_calc* (planetary positions).
    """
    flags = 0
    if include_default_engine: flags |= swe.FLG_SWIEPH
    if sidereal_positions: flags |= swe.FLG_SIDEREAL
    if not geometric_positions: flags |= swe.FLG_TOPOCTR  # Remember to call swe.set_topo(lon, lat, alt) elsewhere
    if true_positions: flags |= swe.FLG_TRUEPOS
    if not use_aberration_of_light: flags |= swe.FLG_NOABERR
    if not use_gravitational_deflection: flags |= swe.FLG_NOGDEFL
    if not use_nutation: flags |= swe.FLG_NONUT
    if include_speed: flags |= swe.FLG_SPEED
    return flags

def set_flags_for_planet_positions(
    *,
    sidereal_positions: bool = True,               # False = tropical
    geocentric_positions: bool | None = None,      # preferred new name
    geometric_positions: bool | None = None,       # backward-compatible alias
    true_positions: bool | None = None,            # False = apparent, True = true
    use_aberration_of_light: bool | None = None,   # False -> disable aberration
    use_gravitational_deflection: bool | None = None,  # True to include deflection
    use_nutation: bool | None = None,              # True to include nutation
    include_default_engine: bool = True,
    include_speed: bool = True,
) -> int:
    """
    Return flags for swe_calc* (planetary positions).

    Priority:
      1. Explicit function argument
      2. backward-compatible alias (geometric_positions)
      3. jhora.const runtime setting
      4. original historical default from PyJHora
    """
    flags = 0

    # --------------------------------------------------
    # Geo / Topo
    # Original default: geometric_positions=True
    # --------------------------------------------------
    if geocentric_positions is None:
        if geometric_positions is not None:
            geocentric_positions = bool(geometric_positions)
        else:
            geocentric_positions = bool(
                getattr(const, "PLANET_POSITIONS_GEOCENTRIC", True)
            )
    # --------------------------------------------------
    # True / Apparent
    # Original default: true_positions=True
    # --------------------------------------------------
    if true_positions is None:
        true_positions = bool(
            getattr(const, "PLANET_POSITIONS_TRUE", True)
        )

    # --------------------------------------------------
    # Aberration
    # Original default: use_aberration_of_light=True
    # --------------------------------------------------
    if use_aberration_of_light is None:
        use_aberration_of_light = bool(
            getattr(const, "PLANET_POSITIONS_USE_ABERRATION", True)
        )

    # --------------------------------------------------
    # Gravitational deflection
    # Original default: use_gravitational_deflection=False
    # --------------------------------------------------
    if use_gravitational_deflection is None:
        use_gravitational_deflection = bool(
            getattr(const, "PLANET_POSITIONS_USE_DEFLECTION", False)
        )

    # --------------------------------------------------
    # Nutation
    # Original default: use_nutation=False
    # --------------------------------------------------
    if use_nutation is None:
        use_nutation = bool(
            getattr(const, "PLANET_POSITIONS_USE_NUTATION", False)
        )

    # --------------------------------------------------
    # Build flags
    # --------------------------------------------------
    if include_default_engine:
        flags |= swe.FLG_SWIEPH

    if sidereal_positions:
        flags |= swe.FLG_SIDEREAL

    if not geocentric_positions:
        flags |= swe.FLG_TOPOCTR  # remember to call swe.set_topo(...)

    if true_positions:
        flags |= swe.FLG_TRUEPOS

    # For true positions aberration and deflection flags are ignored by Swiss Ephemeris
    if not use_aberration_of_light:
        flags |= swe.FLG_NOABERR

    # original semantics:
    # if user says "do not use gravitational deflection", set NOGDEFL
    if not use_gravitational_deflection:
        flags |= swe.FLG_NOGDEFL

    # original semantics:
    # if user says "do not use nutation", set NONUT
    if not use_nutation:
        flags |= swe.FLG_NONUT

    if include_speed:
        flags |= swe.FLG_SPEED

    return flags

def apply_topocentric_observer_if_needed(longitude: float, latitude: float, altitude_m: float = 0.0) -> None:
    """
    Call swe.set_topo(...) only if current config requires topocentric positions.
    altitude_m must be in meters.
    """
    if not bool(getattr(const, "PLANET_POSITIONS_GEOCENTRIC", True)):
        swe.set_topo(longitude, latitude, altitude_m)

def set_flags_for_rise_set(
    *,
    flags_for_rise: bool = True,                   # True -> rise, False -> set
    use_disc_center_for_rising: bool | None = None,
    use_refraction: bool | None = None,
    hindu_rising: bool | None = None,
) -> int:
    """
    Return flags for swe_rise_transit / swe_rise_transit_ex.

    Two main user-controlled dimensions:
      1. Disc reference:
         - center
         - bottom
      2. Horizon model:
         - with refraction (apparent horizon)
         - without refraction (true horizon)

    Plus optional Hindu rising convention.
    """
    if use_disc_center_for_rising is None:
        use_disc_center_for_rising = bool(
            getattr(const, "RISE_SET_USE_DISC_CENTER_FOR_RISING", True)
        )

    if use_refraction is None:
        use_refraction = bool(
            getattr(const, "RISE_SET_USE_REFRACTION", False)
        )

    if hindu_rising is None:
        hindu_rising = bool(
            getattr(const, "RISE_SET_HINDU_RISING", True)
        )

    flags = 0

    if hindu_rising:
        flags |= swe.BIT_HINDU_RISING

    if not use_refraction:
        flags |= swe.BIT_NO_REFRACTION
    else:
        flags &= ~swe.BIT_NO_REFRACTION

    flags |= swe.BIT_DISC_CENTER if use_disc_center_for_rising else swe.BIT_DISC_BOTTOM

    flags &= ~(swe.CALC_RISE | swe.CALC_SET | swe.CALC_MTRANSIT | swe.CALC_ITRANSIT)
    flags |= swe.CALC_RISE if flags_for_rise else swe.CALC_SET

    return flags


set_flag_for_calendar = lambda jd: swe.GREG_CAL if jd >= const._JULIAN_TRANSITION_DAY else swe.JUL_CAL

def secant_interpolation(x,y,y0):
    x0 = 0
    for i in range(len(y) - 1):
        if y[i] * y[i+1] <= 0:  # Sign change found
            # Safety check: if the movement is zero, don't divide!
            denom = y[i+1] - y[i]
            if abs(denom) < y0: 
                x0 = x[i]
            else:
                fraction = -y[i] / denom
                x0 = x[i] + fraction * (x[i+1] - x[i])
            break
    return x0

angle_diff = lambda a,b: (a-b+180)%360-180
def get_place_from_latitude_longitude(latitude, longitude):
    geo_locator = Nominatim(user_agent="PyJHora")
    coorindates = f"{latitude},{longitude}"
    location = geo_locator.reverse(coorindates,exactly_one=True)
    return location

import bisect

ONE_NAK = 360.0 / 27.0  # 13°20'

def degrees_between_jds(jds, jd_birth, jd_current):
    """Assumes both JDs are inside [jds[0], jds[-1])."""
    def pos(t):
        i = bisect.bisect_right(jds, t) - 1
        i = max(0, min(i, len(jds) - 2))  # clamp
        span = jds[i+1] - jds[i]
        f = 0.0 if span <= 0 else (t - jds[i]) / span
        return i + f
    delta_segments = pos(jd_current) - pos(jd_birth)
    mpl =  delta_segments * ONE_NAK
    return mpl
from typing import Sequence, Tuple

ONE_NAK = 13.333333333333334  # 13°20′ in decimal degrees
NUM_NAK = 27

def degrees_between_jds_with_birth_star(
    jds: Sequence[float],
    jd_current: float,
    birth_star_index: int,
) -> Tuple[float, float]:
    """
    Compute the progressed longitude (Vimsottari progression) assuming `jds`
    are MAHADASA boundaries (one full nakshatra per span).

    Parameters
    ----------
    jds : ascending list of JD boundaries such that
          jds[0] = start of the birth star's mahadasa (progressed pos at start of nakshatra),
          jds[1] = start of next nakshatra, etc.
    jd_current : JD timestamp of interest (must satisfy jds[0] <= jd_current < jds[-1])
    birth_star_index : 0..26 index of the birth nakshatra (Aśvinī=0, Bharanī=1, ..., Revatī=26)
                       used only if you want to sanity-check against anchor computations.
    birth_star_anchor_long : absolute longitude (0..360) of the START of the birth star
                             in your zodiac/ayanāṁśa (e.g., 0.0 if Aśvinī starts at 0° Aries).

    Returns
    -------
    rel_arc_deg : float
        Relative arc from the START of the birth star (0 at birth star start),
        i.e., i*ONE_NAK + frac*ONE_NAK (can be >= 360 if you provide >27 spans).
    abs_long_deg : float
        Absolute ecliptic longitude (0..360) = (birth_star_anchor_long + rel_arc_deg) % 360
    """
    if len(jds) < 2:
        raise ValueError("jds must contain at least two boundaries (start and end).")
    # Find the segment i with jds[i] <= jd_current < jds[i+1]
    i = bisect.bisect_right(jds, jd_current) - 1
    i = max(0, min(i, len(jds) - 2))  # clamp

    span = jds[i+1] - jds[i]
    if span <= 0:
        raise ValueError("jds must be strictly increasing.")

    frac = (jd_current - jds[i]) / span  # fraction of the current nakshatra traversed

    rel_arc_deg = (i * ONE_NAK) + (frac * ONE_NAK)
    progressed_longitude = (birth_star_index*ONE_NAK + rel_arc_deg) % 360.0
    return progressed_longitude

ONE_NAK = 13.333333333333334  # 13°20′ in decimal degrees

def progressed_abs_long_general(
    jds_level: Sequence[float],
    jd_current: float,
    birth_star_index: int,
    dhasa_level_index: int = const.MAHA_DHASA_DEPTH.ANTARA,
    total_lords_in_dhasa=9, # 8 for yogini
) -> Tuple[float, float]:
    """
    Compute the progressed absolute longitude using Vimśottarī-as-progression
    at an arbitrary dasha level (L):
        L=1 mahadasa, L=2 antardasa (default), L=3 pratyantardasa,
        L=4 sookshma, L=5 praana, L=6 deha.

    Assumptions
    -----------
    - `jds_level` is a COMPLETE, strictly increasing list of boundaries at level L,
      starting at the *start of the birth-star mahadasa* (progressed arc = 0 there).
      Each half-open span [jds_level[i], jds_level[i+1]) is one segment at level L.
    - Standard 27 equal nakshatras: one mahadasa = ONE_NAK = 13°20′ of arc.
      Each deeper level divides the *same arc* by 9, so segment_arc = ONE_NAK / 9**(L-1).
      (Per P.V.R. Narasimha Rao’s method.)  # See citation below
    - By default, we assume Aśvinī starts at 0°, so the birth-star anchor is:
          birth_star_index * ONE_NAK
    Parameters
    ----------
    jds_level : Sequence[float]
        JD boundaries at the chosen level L (complete from birth-star MD start).
    jd_current : float
        JD timestamp to evaluate.
    birth_star_index : int
        0..26 (Aśvinī=0, Bharanī=1, ..., Revatī=26)
    dhasa_level_index : int, default=2
        Level index: 1=MD, 2=AD, 3=PD, 4=SD, 5=PAD, 6=DAD (deha).
    Returns
    -------
    rel_arc_deg : float
        Degrees progressed since the *start of the birth-star MD*.
    abs_long_deg : float
        Absolute ecliptic longitude (0..360) for aspect/transit/D-chart use.

    Raises
    ------
    ValueError
        If inputs are out of range or `jds_level` is not strictly increasing.
    """
    if len(jds_level) < 2:
        raise ValueError("Need at least two boundaries at the chosen level.")
    if not (const.MAHA_DHASA_DEPTH.MAHA_DHASA_ONLY <= dhasa_level_index <= const.MAHA_DHASA_DEPTH.DEHA):
        raise ValueError("dhasa_level_index must be in 1..6 (1=MD ... 6=deha).")

    # Locate the segment i: jds[i] <= jd_current < jds[i+1]
    i = bisect.bisect_right(jds_level, jd_current) - 1
    i = max(0, min(i, len(jds_level) - 2))  # clamp to a valid index

    span = jds_level[i+1] - jds_level[i]
    if span <= 0:
        raise ValueError("`jds_level` must be a strictly increasing sequence.")

    # Fraction within the current segment (0..1)
    frac = (jd_current - jds_level[i]) / span

    # Geometry: one MD = ONE_NAK; each deeper level divides by 9
    seg_arc_deg = ONE_NAK / (total_lords_in_dhasa ** (dhasa_level_index - 1))

    # Relative arc since birth-star MD start
    rel_arc_deg = (i + frac) * seg_arc_deg

    anchor = (birth_star_index * ONE_NAK) % 360.0
    # Absolute longitude
    abs_long_deg = (anchor + rel_arc_deg) % 360.0
    return abs_long_deg
def get_running_dhasa_for_given_date(jd_given, dhasa_periods):
    """
    Select the running daśā for jd_given from a list of periods.

    Accepts rows in ANY of these shapes (mixed lists allowed):
      - (lords, start_tuple)
      - (lords, start_tuple, duration_years)
      - (lords, start_tuple, end_tuple)

    Returns:
      (lords, start_tuple, end_tuple)  with half-open semantics [start, end).

    Robust to zero-duration periods:
      - Skips over runs of identical start times to find the next DISTINCT start
        when an end is not provided.
      - If there is no next distinct start, returns a zero-length interval (start, start)
        for that row instead of raising.
    """
    if not dhasa_periods:
        raise ValueError("Empty dhasa_periods.")

    import bisect
    from jhora import const
    from jhora.panchanga.drik import Date

    # --- Canonical tuple <-> JD helpers ---
    def _tuple_to_jd(t):
        y, m, d, fh = t
        return julian_day_number(Date(y, m, d), (fh, 0, 0))

    def _jd_to_tuple(jd):
        # In your codebase this returns (Y, M, D, fractional_hour)
        return jd_to_gregorian(jd)

    # --- days per year basis for duration -> end  (sidereal) ---
    DAYS_PER_YEAR = const.sidereal_year

    # --- Normalize to a working list with parsed starts/ends ---
    # Each item: (lords, start_tuple, start_jd, end_tuple_or_None, end_jd_or_None, src_row)
    work = []
    for row in dhasa_periods:
        if not isinstance(row, (list, tuple)):
            raise TypeError("Each period must be a list/tuple.")
        if len(row) < 2:
            raise ValueError("Each period must have at least (lords, start_tuple).")

        lords = row[0]
        start_tuple = tuple(row[1])
        sjd = _tuple_to_jd(start_tuple)

        end_tuple = None
        ejd = None

        if len(row) >= 3:
            third = row[2]
            # 3rd field can be duration_years (float) or end_tuple (tuple)
            if isinstance(third, (int, float)):
                # duration in YEARS -> end jd
                ejd = sjd + float(third) * DAYS_PER_YEAR
                end_tuple = _jd_to_tuple(ejd)
            elif isinstance(third, (list, tuple)) and len(third) == 4:
                end_tuple = tuple(third)
                ejd = _tuple_to_jd(end_tuple)
            else:
                # ignore unknown 3rd field
                pass

        work.append((lords, start_tuple, sjd, end_tuple, ejd, row))

    # --- Sort by start jd (stable) ---
    work.sort(key=lambda x: x[2])
    starts = [w[2] for w in work]
    n = len(work)

    # --- Locate the group whose start <= jd_given ---
    i = bisect.bisect_right(starts, jd_given) - 1
    if i < 0:
        # Earlier than the very first start
        raise ValueError("jd_given is earlier than the first period start.")

    # Walk forward across groups until we find a containing interval or hit the end
    idx = i
    while idx < n:
        sjd = work[idx][2]

        # Find the contiguous block [g0..g1] of rows that share this same start
        g0 = idx
        while g0 > 0 and work[g0 - 1][2] == sjd:
            g0 -= 1
        g1 = idx
        while g1 + 1 < n and work[g1 + 1][2] == sjd:
            g1 += 1

        # Compute the "next distinct start" jd (used to bound rows that lack an explicit end)
        next_distinct_jd = None
        g_next = g1 + 1
        while g_next < n and work[g_next][2] == sjd:
            g_next += 1
        if g_next < n:
            next_distinct_jd = work[g_next][2]

        # Check rows in this group for containment
        chosen = None
        for k in range(g0, g1 + 1):
            lords, start_t, sjd_k, end_t, ejd_k, _src = work[k]

            # Determine effective end:
            if ejd_k is not None:
                end_jd_eff = ejd_k
                end_t_eff = end_t
            elif next_distinct_jd is not None:
                end_jd_eff = next_distinct_jd
                end_t_eff = _jd_to_tuple(end_jd_eff)
            else:
                # No next distinct start and no explicit end -> zero-length at start
                end_jd_eff = sjd_k
                end_t_eff = start_t

            # Half-open containment [start, end)
            if sjd_k <= jd_given < end_jd_eff:
                chosen = (lords, start_t, end_t_eff)
                break

        if chosen is not None:
            return chosen

        # If nothing contained jd_given in this group:
        if next_distinct_jd is None:
            # We're at the terminal group with no bound; return zero-length for the last row
            lords_last, start_last, _, _, _, _ = work[g1]
            return lords_last, start_last, start_last

        # If jd_given is before the next distinct start but wasn't contained,
        # it means all rows here were zero-length AND jd_given == sjd (or floating issues).
        # In that edge case, return a zero-length selection for the last row in this group.
        if jd_given < next_distinct_jd and jd_given >= sjd:
            lords_last, start_last, _, _, _, _ = work[g1]
            return lords_last, start_last, start_last

        # Otherwise advance to the next distinct group and try again
        idx = g_next

    # If we exit the loop without return, jd_given is beyond all known coverage
    raise ValueError("jd_given is not covered by the provided periods.")

def get_running_dhasa_at_all_levels_for_given_date(
    jd_given,
    dhasa_periods,             # [(lords_tuple, start) ] or [(lords_tuple, start, duration)] or [(lords_tuple, start, end)]
    dhasa_level_index,         # d (deepest level for this list)
    *,
    dhasa_cycle_count = 1,
    extract_running_period_for_all_levels=False,
):
    """
    Return the running daśā at all levels (1..d) that contains jd_given.

    Supports rows in any of these shapes (mixed allowed):
        (lords_tuple, start)
        (lords_tuple, start, duration_years)
        (lords_tuple, start, end_tuple)

    End for a block is inferred as:
      • start of the next block, if available; else
      • if the *last* block in the cycle and an explicit duration/end is available on the last leaf row of that block,
        use start_last_leaf + duration_last_leaf (or end_tuple), else None.

    Half-open semantics: [start, end).
    """
    from bisect import bisect_right
    from jhora.panchanga.drik import Date
    from jhora import const

    # ---- Helper: convert to JD ----
    def _to_jd(start):
        if isinstance(start, (tuple, list)) and len(start) == 4:
            y, m, d, fh = start
            return julian_day_number(Date(y, m, d), (fh, 0, 0))
        return float(start)

    def _row_end_jd(row):
        """
        Try to get an end JD from a row's 3rd field:
          - If duration (float), end = start + duration * sidereal_year
          - If end tuple, use it
          - Else None
        """
        if len(row) < 3:
            return None
        third = row[2]
        if isinstance(third, (int, float)):
            return _to_jd(row[1]) + float(third) * const.sidereal_year
        if isinstance(third, (list, tuple)) and len(third) == 4:
            return _to_jd(third)
        return None

    # ---- Basic checks ----
    L = len(dhasa_periods)
    if L < 2:
        raise ValueError("dhasa_periods must have at least 2 rows.")
    d = dhasa_level_index
    if not (1 <= d <= 12):
        raise ValueError("dhasa_level_index must be between 1 and 12.")

    if dhasa_cycle_count < 1 or int(dhasa_cycle_count) != dhasa_cycle_count:
        raise ValueError("dhasa_cycle_count must be a positive integer.")
    dhasa_cycle_count = int(dhasa_cycle_count)

    if L % dhasa_cycle_count != 0:
        print("ValueError:",
            f"len(dhasa_periods)={L} is not divisible by dhasa_cycle_count={dhasa_cycle_count}."
        )
        return None

    base_len = L // dhasa_cycle_count  # rows per cycle; should be n**d

    # ---- Robust integer nth-root ----
    def _int_nth_root_exact(x, n_):
        r = int(round(x ** (1.0 / n_)))
        while r > 0 and r ** n_ > x:
            r -= 1
        while (r + 1) ** n_ <= x:
            r += 1
        return r

    n = _int_nth_root_exact(base_len, d)
    if n < 2 or n ** d != base_len:
        print("ValueError:",
            f"Per-cycle length {base_len} is not an exact {d}-th power; cannot infer n (got n={n})."
        )
        return None
    M = n ** d

    # ---- Global starts (non-decreasing) ----
    starts_global = [_to_jd(p[1]) for p in dhasa_periods]

    i_global = bisect_right(starts_global, jd_given) - 1
    if i_global < 0:
        i_global = 0
    if i_global >= L:
        i_global = L - 1

    # ---- Cycle view ----
    c = min(i_global // M, dhasa_cycle_count - 1)
    base = c * M
    i_in_cycle = i_global - base

    segment = dhasa_periods[base : base + M]  # leaf rows for this cycle

    def _start_of_row(rows, idx):
        return rows[idx][1]

    def _end_for_block(idx0, block_len):
        """
        Prefer next block's start. If not available (last block and no next cycle),
        try to compute end from the *last leaf row's* duration/end if present.
        Otherwise None.
        """
        idx1 = idx0 + block_len
        if idx1 < M:
            return segment[idx1][1]  # next block's first start (same cycle)
        # no next block in this cycle -> try next cycle
        next_cycle_base = base + M
        if next_cycle_base < L:
            return dhasa_periods[next_cycle_base][1]  # first of next cycle

        # Final fallback: compute from last leaf row's duration/end if available
        last_leaf_idx = min(M - 1, idx0 + block_len - 1)
        end_jd = _row_end_jd(segment[last_leaf_idx])
        if end_jd is not None:
            # Convert end_jd back to tuple using your utils
            return jd_to_gregorian(end_jd)
        return None

    def _bisect_interval(level_rows, *, k, stride):
        lvl_starts_jd = [_to_jd(r[1]) for r in level_rows]
        j = bisect_right(lvl_starts_jd, jd_given) - 1
        if j < 0:
            j = 0
        if j >= len(level_rows):
            j = len(level_rows) - 1

        idx0 = j * stride

        lords_tuple = segment[idx0][0]
        lord_k = tuple(lords_tuple[:k]) if isinstance(lords_tuple, (tuple, list)) else lords_tuple

        start_k = _start_of_row(segment, idx0)
        end_k   = _end_for_block(idx0, stride)
        return (lord_k, start_k, end_k)

    if extract_running_period_for_all_levels:
        out = []
        for k in range(1, d + 1):
            stride = n ** (d - k)
            lvl = segment[::stride]
            lord_k, start_k, end_k = _bisect_interval(lvl, k=k, stride=stride)
            out.append((lord_k, start_k, end_k))
        return out

    k = d
    stride = n ** (d - k)
    lvl = segment[::stride]
    lord_k, start_k, end_k = _bisect_interval(lvl, k=k, stride=stride)
    return (lord_k, start_k, end_k)

from typing import List, Tuple, Optional, Union
def _fraction_traversed_deep_first(lords_path, order):
    """
    Nested fraction at the start of the final level (deep -> shallow),
    as in the paper's worked example.  (DAD first, then PAD, then SD, ... up to AD)
    Ref: https://vedicastrologer.org/articles/transit_vimso_prog.pdf
    """
    lords = list(lords_path)
    N = len(order)
    if len(lords) == 1:
        return 0.0
    pos = {lord: i for i, lord in enumerate(order)}
    # overs shallow->deep
    overs = [(pos[lords[i]] - pos[lords[i - 1]]) % N for i in range(1, len(lords))]
    # fold deep->shallow
    F = overs[-1] / N
    for x in reversed(overs[:-1]):
        F = (F + x) / N
    return F

def progressed_longitude_for_event_date(
    period_tuple: Tuple[
        Tuple[int, ...],                                # (MD, AD, ..., deepest)
        Union[Tuple[int, int, int, float], float],      # start bound (tuple or JD)
        Union[Tuple[int, int, int, float], float],      # end   bound (tuple or JD)
    ],
    adhipathi_list: List[int],
    birth_star_index: int,
    jd_event: Optional[Union[float, Tuple[int, int, int, float]]] = None,
) -> float:
    """
    Returns ABSOLUTE progressed longitude (0..360°).
      - If jd_event is None: longitude at START of deepest period (paper’s method).
      - If jd_event is JD (float) or (y,m,d,fh): linearly INTERPOLATED inside deepest period.

    period_tuple = ((lords_path), start_bound, end_bound)
      - start_bound/end_bound can be JD floats or (y,m,d,fh) tuples (IST or your chosen scale).
    """
    from jhora.panchanga.drik import Date
    lords_path, start_bound, end_bound = period_tuple
    if not isinstance(lords_path,tuple):lords_path=[lords_path]
    N = len(adhipathi_list)

    # 1) MD's nakshatra index from birth seed + lord offset
    birth_lord = adhipathi_list[(birth_star_index - 1) % N]
    md_lord = lords_path[0]
    pos = {lord: i for i, lord in enumerate(adhipathi_list)}
    lord_offset = (pos[md_lord] - pos[birth_lord]) % N
    md_star_index = ((birth_star_index - 1 + lord_offset) % 27) + 1

    # 2) Fraction at start of deepest level (deep -> shallow)
    F = _fraction_traversed_deep_first(lords_path, adhipathi_list)  # per Rao  [1](https://vedicastrologer.org/articles/transit_vimso_prog.pdf)

    # 3) Start longitude & per-level span
    md_star_start_deg = (md_star_index - 1) * ONE_NAK
    start_deg = norm360(md_star_start_deg + F * ONE_NAK)
    level_span = ONE_NAK / (N ** (len(lords_path) - 1))  # e.g., Deha in Vimśottari ≈ 0.8129″  [1](https://vedicastrologer.org/articles/transit_vimso_prog.pdf)

    # 4) No interpolation requested -> return start-of-period (paper)
    if jd_event is None:
        return start_deg

    # 5) Convert bounds and event to JD if needed
    if isinstance(start_bound, (int, float)):
        jd_start = float(start_bound)
    else:
        y, m, d, fh = start_bound
        jd_start = julian_day_number(Date(y, m, d), (fh, 0, 0))

    if isinstance(end_bound, (int, float)):
        jd_end = float(end_bound)
    else:
        y, m, d, fh = end_bound
        jd_end = julian_day_number(Date(y, m, d), (fh, 0, 0))

    if isinstance(jd_event, (int, float)):
        jd_e = float(jd_event)
    else:
        y, m, d, fh = jd_event
        jd_e = julian_day_number(Date(y, m, d), (fh, 0, 0))

    # 6) Interpolation (clamped): the one-liner you suggested
    t = 0.0 if jd_end <= jd_start else max(0.0, min(1.0, (jd_e - jd_start) / (jd_end - jd_start)))

    # 7) Absolute longitude at event
    return norm360(start_deg + t * level_span)
from typing import Dict, List, Tuple, Optional, Union
STAR_LENGTH_DEG = 360.0 / 27.0  # 13°20′ per nakshatra

def _deg_normalize(x: float) -> float:
    x %= 360.0
    return x if x >= 0 else x + 360.0

def progressed_longitude_for_period(
    period_tuple: Tuple[
        Tuple[int, ...],                               # (MD, AD, ..., deepest)
        Union[Tuple[int,int,int,float], float],        # start bound (tuple or JD)
        Union[Tuple[int,int,int,float], float],        # end   bound (tuple or JD)
    ],
    adhipathi_dict: Dict[int, float],                  # {lord: duration}; **insertion order = cycle order**
    birth_star_index: int,                             # 1..27 (seed star at birth)
    jd_event: Optional[Union[float, Tuple[int,int,int,float]]] = None,
) -> float:
    """
    Returns ABSOLUTE progressed longitude (0..360°).
      - If jd_event is None: longitude at START of the deepest period (paper's method).
      - If jd_event is JD (float) or (y,m,d,fh): linearly INTERPOLATED inside the deepest window.

    Assumptions:
      * The insertion order of `adhipathi_dict` keys is the forward cycle of lords.
      * Each level (AD..deepest) starts from the parent lord and cycles forward.
    """
    from jhora.panchanga.drik import Date
    print('period_tuple',period_tuple)
    lords_path, start_bound, end_bound = period_tuple

    # ---- derive order & basic maps from adhipathi_dict ----
    order: List[int] = list(adhipathi_dict.keys())      # cycle order from insertion order
    durations = adhipathi_dict                           # alias
    N = len(order)
    pos = {lord: i for i, lord in enumerate(order)}
    H = sum(durations[l] for l in order)                 # total of one cycle (used for shares)

    # ---- map current MD's nakshatra from birth seed + lord offset ----
    birth_lord = order[(birth_star_index - 1) % N]
    md_lord = lords_path[0]
    lord_offset = (pos[md_lord] - pos[birth_lord]) % N
    md_star_index = ((birth_star_index - 1 + lord_offset) % 27) + 1

    # ---- time fraction inside deepest window (for interpolation) ----
    if jd_event is None:
        t_deep = 0.0
        # JD bounds not needed if we only want start-of-period
    else:
        # convert bounds to JD if needed
        if isinstance(start_bound, (int, float)):
            jd_start = float(start_bound)
        else:
            y, m, d, fh = start_bound
            jd_start = julian_day_number(Date(y, m, d), (fh, 0, 0))

        if isinstance(end_bound, (int, float)):
            jd_end = float(end_bound)
        else:
            y, m, d, fh = end_bound
            jd_end = julian_day_number(Date(y, m, d), (fh, 0, 0))

        if isinstance(jd_event, (int, float)):
            jd_e = float(jd_event)
        else:
            y, m, d, fh = jd_event
            jd_e = julian_day_number(Date(y, m, d), (fh, 0, 0))

        # the one-liner, clamped
        t_deep = 0.0 if jd_end <= jd_start else max(0.0, min(1.0, (jd_e - jd_start) / (jd_end - jd_start)))

    # ---- compute fraction inside the MD star via recursive ascent (variable durations) ----
    # Core recurrence (correct for equal or variable durations):
    #   Given child fraction F_child in [0,1) inside child segment C of duration D_C,
    #   the fraction in the parent cycle (starting at parent-lord P) is:
    #       F_parent = (sum_{lords before C from P} dur(l)) / H  +  F_child * (D_C / H)
    #
    # Start from the deepest level (child fraction = t_deep) and fold upward till AD.
    F = t_deep
    for k in range(len(lords_path) - 1, 0, -1):
        child  = lords_path[k]
        parent = lords_path[k - 1]
        i_parent = pos[parent]
        i_child  = pos[child]
        steps = (i_child - i_parent) % N  # lords passed before child (starting at parent)
        over_sum = 0.0
        for s in range(steps):
            over_sum += durations[order[(i_parent + s) % N]]
        F = (over_sum / H) + F * (durations[child] / H)

    # F is now the fraction of the current MD's nakshatra covered at the event (or at start if jd_event=None)

    # ---- absolute longitude ----
    md_star_start_deg = (md_star_index - 1) * STAR_LENGTH_DEG
    lon = _deg_normalize(md_star_start_deg + F * STAR_LENGTH_DEG)
    return lon
def build_main_planets():
    if 'PLANET_NAMES' not in globals():
        set_language(const._DEFAULT_LANGUAGE)
    planets_upto = 12 if const._INCLUDE_URANUS_TO_PLUTO else 9
    return {p: PLANET_NAMES[p] for p in range(planets_upto)}
build_main_planets()
_main_planets = {p:PLANET_NAMES[p] for p in range(12)}
_ascendant = {const._ascendant_symbol:resource_strings['ascendant_str']}
_drik_upagrahas = {'Kl':'kaala','Mr':'mrityu','Ap':'artha_praharaka','Yg':'yama_ghantaka','Gk':'gulika','Md':'maandi'}
_chart_upagrahas = {'Dm':'dhuma','Vp':'vyatipaata','Pv':'parivesha','Ic':'indrachaapa','Uk':'upaketu'}
_upagrahas = (_drik_upagrahas | _chart_upagrahas )
_special_lagnas= {'BL':'bhava_lagna','HL':'hora_lagna','GL':'ghati_lagna','PL':'pranapada_lagna',
                                 'VL':'vighati_lagna','KL':'kunda_lagna','BBL':'bhrigu_bindhu_lagna',
                                 'SL':'sree_lagna','IL':'indu_lagna'}
_arudha_lagnas = {"A"+str(k):'bhava_arudha_a'+str(k) for k in range(1,13)}
_varnada_lagnas = {"V"+str(k):'varnada_lagna (V'+str(k)+")" for k in range(1,13)}
_sphutas = {"S"+str(s+1):sp for s,sp in enumerate(const.sphuta_list)}
_sahams = {'Pn': 'punya', 'Vd': 'vidya', 'Ys': 'yasas', 'Mi': 'mitra', 'Mh': 'mahatmaya', 'As': 'asha', 'Sm': 'samartha', 
           'Bh': 'bhratri', 'Gv': 'gaurava', 'Pi': 'pithri', 'Rj': 'rajya', 'Ma': 'maathri', 'Pu': 'puthra', 
           'Jv': 'jeeva', 'Km': 'karma', 'Rg': 'roga', 'Ka': 'kali', 'Ss': 'sastra', 'Bd': 'bandhu', 'Mu': 'mrithyu', 
           'Pr': 'paradesa', 'Ar': 'artha', 'Pd': 'paradara', 'Vk': 'vanika', 'Ks': 'karyasiddhi', 'Vv': 'vivaha', 
           'Sn': 'santapa', 'Sr': 'sraddha', 'Pt': 'preethi', 'Jd': 'jadya', 'Vy': 'vyaapaara', 'St': 'sathru', 
           'Jp': 'jalapatna', 'Ba':'bandhana', 'Am': 'apamrithyu', 'Lb': 'laabha'}

all_chart_planets = (_ascendant | _main_planets | _drik_upagrahas | _chart_upagrahas | _special_lagnas 
                        | _arudha_lagnas | _varnada_lagnas | _sphutas | _sahams )

def set_owner_overrides_for_dhasa(overrides=None):
    """
    Global dhasa override setter (JHora-like). Call once; persists until changed.

    overrides: dict or None
      If None -> resets to defaults (no owner forcing; clears stronger-pair rules).

    Expected dict schema:
      {
        "owners": { const.SCORPIO: planet_id, const.AQUARIUS: planet_id },
        "stronger_pairs": {
            (signA, signB): {"stronger": signX, "exception": "NONE"|"KETU"|"SATURN"|"SATURN_KETU"},
            ...
        }
      }

    Notes:
      - Owner overrides affect all PyJHora immediately because house_owner uses const.* globals.
      - Stronger-pair overrides are stored globally and used by modules that consult them (DRIG does).
    """
    # Reset
    if overrides is None:
        const.scorpio_owner_for_dhasa_calculations = None
        const.aquarius_owner_for_dhasa_calculations = None
        const.DHASA_STRONGER_PAIR_RULES = {}
        return

    if not isinstance(overrides, dict):
        raise TypeError("overrides must be a dict or None")

    owners = overrides.get("owners", {}) or {}
    pairs  = overrides.get("stronger_pairs", {}) or {}

    # ---- owners
    # Only accept valid owner choices if you want strictness; otherwise accept as-is.
    if const.SCORPIO in owners:
        const.scorpio_owner_for_dhasa_calculations = int(owners[const.SCORPIO])
    if const.AQUARIUS in owners:
        const.aquarius_owner_for_dhasa_calculations = int(owners[const.AQUARIUS])

    # ---- stronger pair rules: normalize to (min,max) key
    norm = {}
    for k, v in dict(pairs).items():
        if not (isinstance(k, (tuple, list)) and len(k) == 2):
            raise ValueError(f"stronger_pairs key must be a 2-tuple (signA, signB). Got: {k}")
        a, b = int(k[0]) % 12, int(k[1]) % 12
        if not isinstance(v, dict) or "stronger" not in v:
            raise ValueError(f"stronger_pairs[{k}] must be dict with 'stronger'. Got: {v}")

        stronger = int(v["stronger"]) % 12
        exception = str(v.get("exception", "NONE")).upper().strip()
        if exception not in ("NONE", "KETU", "SATURN", "SATURN_KETU"):
            raise ValueError(f"Invalid exception '{exception}' for pair {k}")

        norm[(min(a, b), max(a, b))] = {"stronger": stronger, "exception": exception}

    const.DHASA_STRONGER_PAIR_RULES = norm

def get_dhasa_stronger_pair_rules():
    """
    Accessor for globally configured stronger-pair rules.
    Returns dict: (min_sign,max_sign) -> {"stronger": sign, "exception": "..."}
    """
    return getattr(const, "DHASA_STRONGER_PAIR_RULES", {}) or {}
def _get_import_dhasa_module(dhasa_name):
    entry = const.SPECIAL_DASHA_OPTIONS.get(dhasa_name)
    module_name = entry["module"] if entry else dhasa_name
    defaults    = entry.get("defaults", {}) if entry else {}
    preferred   = entry.get("domain") if entry else ""
    try_paths = []
    if preferred in ("graha", "raasi","annual"):
        try_paths.append(f"jhora.horoscope.dhasa.{preferred}.{module_name}")
    else:
        try_paths.extend([f"jhora.horoscope.dhasa.graha.{module_name}",
                          f"jhora.horoscope.dhasa.{module_name}",
                          f"jhora.horoscope.dhasa.raasi.{module_name}",
                          f"jhora.horoscope.dhasa.annual.{module_name}"])
    module = None
    import importlib
    for mp in try_paths:
        try:
            module = importlib.import_module(mp)
            break
        except ImportError:
            continue
    if module is None:
        raise ImportError(f"Could not import any of: {', '.join(try_paths)}")
    return module, defaults
def is_valid_option(arg, allowed) -> bool:
    """
    arg: raw value (e.g., 1, 'P') OR Enum member (e.g., BHAVA_METHODS.PARASHARI)
    allowed: Enum class (e.g., BHAVA_METHODS) OR container/mapping of allowed raw values (e.g., dict)
    """
    value = getattr(arg, "value", arg)  # Enum member -> its .value, else unchanged

    # If allowed is an Enum class
    if isinstance(allowed, type) and issubclass(allowed, Enum):
        if isinstance(arg, allowed):
            return True
        try:
            allowed(value)  # lookup by enum value
            return True
        except (ValueError, TypeError):
            return False

    # Otherwise allowed is a container/mapping of raw values (dict/set/list/keys-view)
    try:
        return value in allowed  # dict checks keys; set/list checks elements
    except TypeError:
        return False
next_index = lambda index, start, end, step=1, direction=1: \
    ((index - start + direction * step) % (end - start + 1)) + start
next_tithi_index = lambda index, start=1, end=30, step=1, direction=1: next_index(index,start,end,step,direction)

""" PLACE DATABASE HELPERS """
from jhora import place_db
def use_database_for_world_cities(enable_database=False):
    return place_db.use_database_for_world_cities(enable_database)

def search_places_for_completer(query, limit=15):
    return place_db.search_places_for_completer(query, limit)

def search_places_contains(query, limit=30):
    return place_db.search_places_contains(query, limit)

def get_exact_alias_labels(query, limit=15):
    return place_db.get_exact_alias_labels(query, limit)

def get_location_record(place_name=None):
    return place_db.get_location_record(place_name)

def get_location(place_name=None):
    return place_db.get_location(place_name)

def get_place(place_name=None):
    return place_db.get_place(place_name)

def debug_trace_alias(query, limit=20):
    return place_db.debug_trace_alias(query, limit)

reverse_languages = getattr(const, "reverse_languages", {v: k for k, v in const.available_languages.items()})
def _lang_to_display(language_value):
    """
    Accept either display name ('Tamil') or code ('ta') and return display name.
    """
    if language_value is None:
        return reverse_languages.get(getattr(const, "_DEFAULT_LANGUAGE", "en"), "English")

    # already display name
    if language_value in const.available_languages:
        return language_value

    # language code
    if language_value in reverse_languages:
        return reverse_languages[language_value]

    # fallback
    return reverse_languages.get(getattr(const, "_DEFAULT_LANGUAGE", "en"), "English")


def _lang_to_code(language_value):
    """
    Accept either display name ('Tamil') or code ('ta') and return language code.
    """
    if language_value is None:
        return getattr(const, "_DEFAULT_LANGUAGE", "en")
    # display name
    if language_value in const.available_languages:
        return const.available_languages[language_value]
    # already code
    if language_value in reverse_languages:
        return language_value
    # fallback
    return getattr(const, "_DEFAULT_LANGUAGE", "en")
class Profiler:
    def __init__(self, enabled=True, prefix="[PROFILE]"):
        self.enabled = enabled
        self.prefix = prefix
        self.marks = {}

    def start(self, label="default"):
        """
        Start a profiling session or a named profiling section.
        """
        if not self.enabled: return
        from time import perf_counter
        if not hasattr(self, "marks") or not isinstance(self.marks, dict):
            self.marks = {}
        now = perf_counter()
        self.marks[label] = {
            "_start": now,
            "_last": now,
        }
        print(f"[PROFILE] {label}: started")

    def mark(self, phase_name, label="default"):
        """
        Mark a phase inside a profiling session/section.
        """
        if not self.enabled: return
        from time import perf_counter
        if not hasattr(self, "marks") or label not in self.marks: return
        now = perf_counter()
        last = self.marks[label]["_last"]
        start = self.marks[label]["_start"]
        delta_last = now - last
        delta_total = now - start
        print(f"[PROFILE][{label}] {phase_name}: +{delta_last:.3f}s | total {delta_total:.3f}s")
        self.marks[label]["_last"] = now
    
    def end(self, label="default"):
        """
        End a profiling session or named profiling section.
        """
        if not self.enabled: return
        from time import perf_counter
        if not hasattr(self, "marks") or label not in self.marks:return
        total = perf_counter() - self.marks[label]["_start"]
        print(f"[PROFILE] {label}: finished in {total:.3f}s")
        del self.marks[label]
def validate_star_index(star,min_index=1,max_index=27):
    if not (min_index <= star <= max_index):
        raise ValueError(f"star must be in range of {min_index}..{max_index}")
def validate_raasi_index(raasi,min_index=1,max_index=12):
    if not (min_index <= raasi <= max_index):
        raise ValueError(f"Raasi must be in range of {min_index}..{max_index}")


def get_available_chart_styles(chart_style_module="jhora.ui.chart_styles"):
    import importlib, copy
    chart_module = importlib.import_module(chart_style_module)

    available_chart_styles = copy.deepcopy(const.AVAILABLE_CHART_STYLES)

    for _, config in available_chart_styles.items():
        class_name = config.get("class")

        if isinstance(class_name, str):
            config["class"] = getattr(chart_module, class_name)

    return available_chart_styles
    
if __name__ == "__main__":
    print(len(all_chart_planets))
    exit()
    import time
    start_time = time.time()
    from jhora.panchanga.drik import Date,Place
    dob = Date(-1,1,1); tob = (8,30,0); place = Place('Chicago,US', 41.85, -87.65, -5.0)
    jd_local = julian_day_number(dob, tob)
    print(get_place_timezone_offset(41.85, -87.65, jd_local),time.time()-start_time)
    exit()
    use_database_for_world_cities(True)
    print(get_location("Pune"))
    print(search_places_contains("Vadalur", limit=10))
    print(search_places_contains("Inverness", limit=10))
