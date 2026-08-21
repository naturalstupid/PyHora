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
    This is an attempt to create horoscope based surya sidhantha meant/true position calculations
    Reference: Indian Astronomy - An Introduction - S. Balachandra Rao
    WORK STILL IN PROGRESS - NOT WORKING FOR SOME PLANETS YET
"""
import math
from jhora import utils, const
from jhora.panchanga import drik as drik
import swisseph as swe
from jhora.horoscope.chart import charts
from jhora.panchanga.vratha import pradosham_dates

sind = lambda x : math.sin(math.radians(x)) 
cosd = lambda x : math.cos(math.radians(x))
to_dms = lambda x: utils.to_dms(x,is_lat_long='plong')
ahargana_khanda_khaadyaka = lambda jd: jd - 1964031
#ahargana_graha_laghavam = lambda jd: jd - 1687850
mandaphala_of_sun = 0.0
# SS працює тільки з 9 класичними планетами; список фіксований,
# щоб не залежати від drik.planet_list (який змінюється true/mean nodes,
# включенням Uranus-Pluto тощо). Ключі = const._RAHU/_KETU (11/-10 або 10/-10).
SS_PLANET_LIST = [const._SUN, const._MOON, const._MARS, const._MERCURY,
                  const._JUPITER, const._VENUS, const._SATURN, const._RAHU, const._KETU]
def _manda_periphery(planet):
    """Класичні SS-периферії манди: скаляр або (Po,Pe) → (Po,Pe)."""
    mp = const.planet_mandaphala_periphery[planet]
    if isinstance(mp, (int, float)):
        return float(mp), float(mp)
    return float(mp[0]), float(mp[1])
def kali_ahargana(jd):
    """ TODO: CHECK: Should this be int or float? """
    kad = int(jd - const.mahabharatha_tithi_julian_day) # (jd - 588466)
    wday = int(kad) % 7
    wdayjd = drik.civil_weekday(jd)   # drik.vaara тепер вимагає place; для ахаргани потрібен просто день тижня
    winc = (wdayjd - 5 - wday)
    wdayc = (wday + winc + 5) % 7
    assert wdayc==wdayjd
    return kad+winc
def _mean_solar_longitude(jd):
    mean_daily_motion_sun_at_kali = const.mean_revolutions_sun_kali / const.civil_days_in_mahayuga * 360
    kan = kali_ahargana(jd)
    mean_longitude_sun = (kan * mean_daily_motion_sun_at_kali) %360
    return mean_longitude_sun,utils.to_dms(mean_longitude_sun,is_lat_long='plong')
def _mean_lunar_longitude(jd):
    mean_daily_motion_moon_at_kali = const.mean_revolutions_moon_kali / const.civil_days_in_mahayuga * 360
    kan = kali_ahargana(jd)
    mean_longitude_moon = (kan * mean_daily_motion_moon_at_kali) %360
    return mean_longitude_moon,utils.to_dms(mean_longitude_moon,is_lat_long='plong')
def _mean_lunar_apogee_longitude(jd):
    mean_daily_motion_moon_apogee = const.madocca_revolutions[const._MOON] / const.civil_days_in_mahayuga * 360
    kan = kali_ahargana(jd)
    mean_longitude_moon_apogee = (kan * mean_daily_motion_moon_apogee) %360 + const.manodcca_positions_at_kali[const._MOON]
    return mean_longitude_moon_apogee,utils.to_dms(mean_longitude_moon_apogee,is_lat_long='plong')
def _mean_rahu_longitude(jd):
    mean_daily_motion_rahu_at_kali = const.mean_revolutions_rahu_kali / const.civil_days_in_mahayuga * 360
    kan = kali_ahargana(jd)
    mean_longitude_rahu = 180.0 - (kan * mean_daily_motion_rahu_at_kali) %360
    return mean_longitude_rahu,utils.to_dms(mean_longitude_rahu,is_lat_long='plong')
def _mean_ketu_longitude(jd):
    mean_longitude_ketu = (180.0 + _mean_rahu_longitude(jd)[0]) % 360 
    return mean_longitude_ketu,utils.to_dms(mean_longitude_ketu,is_lat_long='plong')
def _planet_mean_longitude(jd, place,planet):
    """ TODO: Mars not matching close to Drik """
    """ RESET Planet's mean longitude"""
    p_id = list(SS_PLANET_LIST).index(planet)
    const.planet_mean_longitudes[planet] = 0.0 
    mean_revolutions = const.planet_mean_revolutions_at_kali[planet]
    mean_daily_motion = mean_revolutions / const.civil_days_in_mahayuga * 360 # round(...,7) дає похибку ~5' на сучасних датах
    kan = kali_ahargana(jd)
    mean_longitude = ((kan * mean_daily_motion) + 360) %360
    #print('planet,kan,mean_revolutions,mean_daily_motion,mean_longitude',p_id,kan,mean_revolutions,
    #      mean_daily_motion,const.daily_mean_motions[planet],mean_longitude,utils.to_dms(mean_longitude,is_lat_long='plong'))
    if planet in [const._RAHU, const._KETU]:
        mean_longitude = 180.0 - mean_longitude
    if planet == const._KETU:
        mean_longitude = (180.0 + mean_longitude) % 360
    #print('mean long',kan,planet,mean_daily_motion,mean_revolutions,mean_longitude)
    """ Apply Corrections """
    dc = _desantara_correction(place, planet)
    corrected_long = (mean_longitude+dc+360.0)%360
    #print(p_id,'mean longitude after DC',corrected_long,utils.to_dms(corrected_long,is_lat_long='plong')) 
    const.planet_mean_longitudes[planet] = corrected_long   
    return corrected_long
def _desantara_correction(place:drik.Place,planet):
    p_id = list(SS_PLANET_LIST).index(planet)
    planet_daily_motion = const.daily_mean_motions[planet]
    plong = place.longitude
    ulong = const.ujjain_lat_long[1]
    dc = (ulong - plong)/360.0 * planet_daily_motion
    #print('_desantara_correction',p_id,dc,utils.to_dms(dc,is_lat_long='plong'))
    return dc
def bhujantara_correction(planet,mandaphala_of_sun):
    """ TODO: To use Planet's true motion """
    p_id = list(SS_PLANET_LIST).index(planet)
    bc = const.daily_mean_motions[planet]*mandaphala_of_sun/360
    #print(p_id,'bhujantara_correction',mandaphala_of_sun*60,const.daily_mean_motions[planet]*60,bc,utils.to_dms(bc,is_lat_long='plong'))
    return bc
def ascendant_new(jd, place:drik.Place, sun_long):
    """ TODO NOT WORKING STILL UNDER TESTING """
    _,lat,_,_ = place
    R = 3438
    eps = math.radians(24.0)
    def _delination(lat): # radians
        delination = [11.733998794908114, 20.624646006223887, 24.0]
        td = [R/6* math.tan(math.radians(lat))* math.tan(math.radians(d)) for d in delination]
        td = [-td[0]] + [-(y-x) for x,y in zip(td,td[1:])]
        td1 = td.copy()
        td1.reverse()
        td += [-d1 for d1 in td1]
        td2 = td.copy()
        td2.reverse()
        td += [d1 for d1 in td2]
        return td
    td = _delination(lat)
    lanka_rising_durations = [278,299,323,323,299,278,278,299,323,323,299,278]
    place_rising_durations = [d1+d2 for d1,d2 in zip(lanka_rising_durations,td)]
    sun_rise = drik.sunrise(jd, place)
    jd_sunrise = sun_rise[-1]
    y, m, d,_  = utils.jd_to_gregorian(jd)
    jd_utc = utils.gregorian_to_jd(drik.Date(y, m, d))
    #print(jd,jd_sunrise,sun_rise[1],jd_utc)
    time_from_sunrise_vinadi = (jd-jd_sunrise)*24/2.5*60
    sun_long_rem = sun_long % 30
    sun_long_rem_vinadi = sun_long_rem * 60.0
    sun_long_raasi = int(sun_long/30)
    #print('sun_long',sun_long,'sun_long_raasi',sun_long_raasi,'sun_long_rem',sun_long_rem)
    place_rising = place_rising_durations[sun_long_raasi]*sun_long_rem_vinadi/(30*60)
    #print('time_from_sunrise_vinadi',time_from_sunrise_vinadi,'sun_long_rem_vinadi',sun_long_rem_vinadi,'place_rising',place_rising)
    residue = time_from_sunrise_vinadi-place_rising
    #print('residue',residue)
    asc_long = residue/place_rising_durations[(sun_long_raasi+1)%12]*30
    #print('asc_long',asc_long)
    return int(asc_long/30),asc_long%30
def ascendant(jd, place:drik.Place, sun_long):
    """ TODO NOT WORKING STILL UNDER TESTING """
    _,lat,_,_ = place
    R = 3438
    eps = math.radians(24.0)
    def _delination(lat): # radians
        delination = [11.733998794908114, 20.624646006223887, 24.0]
        td = [R/6* math.tan(math.radians(lat))* math.tan(math.radians(d)) for d in delination]
        td = [-td[0]] + [-(y-x) for x,y in zip(td,td[1:])]
        td1 = td.copy()
        td1.reverse()
        td += [-d1 for d1 in td1]
        td2 = td.copy()
        td2.reverse()
        td += [d1 for d1 in td2]
        return td
    td = _delination(lat)
    lanka_rising_durations = [278,299,323,323,299,278,278,299,323,323,299,278]
    place_rising_durations = [d1+d2 for d1,d2 in zip(lanka_rising_durations,td)]
    #print(lanka_rising_durations)
    #print(td)
    #print(place_rising_durations)
    sun_long_rem = sun_long % 30
    sun_long_rem_vinadi = sun_long_rem * 60.0
    sun_long_raasi = int(sun_long/30)
    place_rising = place_rising_durations[sun_long_raasi]*sun_long_rem_vinadi/(30*60)
    srt = utils.from_dms_str_to_dms(drik.sunrise(jd, place)[1])
    ud = utils.udhayadhi_nazhikai((10,34,0), srt)[1]
    asc_long = (ud * 60. - sun_long_rem_vinadi)/place_rising_durations[sun_long_raasi]*30.0
    asc_rasi = int(asc_long / 30)
    asc_coordinates = asc_long % 30 
    if const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SIDEREAL
        drik.set_ayanamsa_mode(drik._ayanamsa_mode,drik._ayanamsa_value,jd) # needed for swe.houses_ex()
    nak_no,paadha_no,_ = drik.nakshatra_pada(asc_long)
    return [const._ascendant_symbol,[asc_rasi,asc_coordinates]]#,nak_no,paadha_no]
def _mandaphala_planet_new(jd,planet):
    """ Mandaphala using just periphery and mandocca """
    pass
def _true_daily_motion_planet(jd, place, planet):
    planet_mean_long = _planet_mean_longitude(jd, place, planet)
    p_id = list(SS_PLANET_LIST).index(planet)
    if planet in [const._RAHU, const._KETU]:
        return 0.0
    kan = kali_ahargana(jd)
    mandocca_mean_revolutions = const.madocca_revolutions[planet]
    planet_mandocca_at_kali = const.manodcca_positions_at_kali[planet]
    mandocca_motion = (kan / (const.civil_days_in_mahayuga) * mandocca_mean_revolutions*360) %360 # Degrees
    #print(p_id,'kan,mandocca_motion',kan,mandocca_mean_revolutions,mandocca_motion,utils.to_dms(mandocca_motion,is_lat_long='plong'))
    planet_mandocca = planet_mandocca_at_kali + mandocca_motion
    #print(p_id,'planet_mandocca_at_kali,mandocca_motion,planet_mandocca',planet_mandocca_at_kali,mandocca_motion,planet_mandocca)
    #planet_mandocca_anomaly = (planet_mandocca + 360.0 - planet_mean_long) %360 
    #print(p_id,'planet_mandocca',utils.to_dms(planet_mandocca,is_lat_long='plong'))
    #print(p_id,'planet mean long, planet_anomaly',utils.to_dms(planet_mean_long,is_lat_long='plong'),utils.to_dms(planet_mandocca_anomaly,is_lat_long='plong'))
    planet_mean_motion = const.daily_mean_motions[planet] 
    mandakendra = (planet_mandocca - planet_mean_long + 360 ) % 360
    planet_mandocca_anomaly = mandakendra
    #print(p_id,'mandakendra',utils.to_dms(mandakendra,is_lat_long='plong'))
    mandakendra_sign = 1.0
    if mandakendra > 180.0:
        mandakendra_sign = -1.0
    " Mandaphala - Equarion of Center"
    if planet in [const._SUN, const._MOON]:
        #planet_mandaphala_periphery = const.planet_mandaphala_periphery_modern[planet]
        #corrected_periphery = planet_mandaphala_periphery - (1.0/3.0)*abs(sind(mandakendra))
        Po,Pe = _manda_periphery(planet)
        corrected_periphery = Pe - (Pe-Po) * abs(sind(mandakendra))
        if planet == const._MOON:
            #print(p_id,'planet_mean_motion before',planet_mean_motion)
            planet_mean_motion = planet_mean_motion - const.moon_apogee_mean_motion
            #print(p_id,'planet_mean_motion after',planet_mean_motion)
        #print(p_id,'corrected_periphery',corrected_periphery)
        rectified_periphery = (const.mandakendrajya_indian_sine_radius/360.0) * corrected_periphery
        #print(p_id,'rectified_periphery',rectified_periphery) 
        tab_sine_diff = abs(225*0.991335735*cosd(1.024764846*(180.0-planet_mandocca_anomaly-3.75)))
        #print(p_id,'tab_sine_diff',tab_sine_diff)
        " You should use true motion here"
        planet_true_motion_correction = corrected_periphery*planet_mean_motion*tab_sine_diff/(360*225)
        planet_true_motion = planet_mean_motion + mandakendra_sign * planet_true_motion_correction
    else:
        Po,Pe = _manda_periphery(planet)
        corrected_periphery = Pe - (Pe-Po) * abs(sind(mandakendra))
        #print(p_id,'mandaphala corrected_periphery',Po,Pe,corrected_periphery)
        # Для інших планет похідна мандафали (true motion) = середній рух + знак*поправка
        tab_sine_diff = abs(cosd(mandakendra))  # d(mandaphala)/d(kendra) ~ cos
        planet_true_motion_correction = corrected_periphery*planet_mean_motion*tab_sine_diff/(360*225)
        planet_true_motion = planet_mean_motion + mandakendra_sign * planet_true_motion_correction
    return planet_true_motion
    
def _mandaphala_planet(jd,planet,planet_mean_long):
    p_id = list(SS_PLANET_LIST).index(planet)
    if planet in [const._RAHU, const._KETU]:
        return 0.0
    kan = kali_ahargana(jd)
    mandocca_mean_revolutions = const.madocca_revolutions[planet]
    planet_mandocca_at_kali = const.manodcca_positions_at_kali[planet]
    mandocca_motion = (kan / (const.civil_days_in_mahayuga) * mandocca_mean_revolutions*360) %360 # Degrees
    #print(p_id,'kan,mandocca_motion',kan,mandocca_mean_revolutions,mandocca_motion,utils.to_dms(mandocca_motion,is_lat_long='plong'))
    planet_mandocca = planet_mandocca_at_kali + mandocca_motion
    #print(p_id,'planet_mandocca_at_kali,mandocca_motion,planet_mandocca',planet_mandocca_at_kali,mandocca_motion,planet_mandocca)
    #planet_mandocca_anomaly = (planet_mandocca + 360.0 - planet_mean_long) %360 
    #print(p_id,'planet_mandocca',utils.to_dms(planet_mandocca,is_lat_long='plong'))
    #print(p_id,'planet mean long, planet_anomaly',utils.to_dms(planet_mean_long,is_lat_long='plong'),utils.to_dms(planet_mandocca_anomaly,is_lat_long='plong'))
    planet_mean_motion = const.daily_mean_motions[planet] 
    mandakendra = (planet_mandocca - planet_mean_long + 360 ) % 360
    planet_mandocca_anomaly = mandakendra
    #print(p_id,'mandakendra',utils.to_dms(mandakendra,is_lat_long='plong'))
    mandakendra_sign = 1.0
    if mandakendra > 180.0:
        mandakendra_sign = -1.0
    " Mandaphala - Equarion of Center"
    if planet in [const._SUN, const._MOON]:
        #planet_mandaphala_periphery = const.planet_mandaphala_periphery_modern[planet]
        #corrected_periphery = planet_mandaphala_periphery - (1.0/3.0)*abs(sind(mandakendra))
        Po,Pe = _manda_periphery(planet)
        corrected_periphery = Pe - (Pe-Po) * abs(sind(mandakendra))
        if planet == const._MOON:
            #print(p_id,'planet_mean_motion before',planet_mean_motion)
            planet_mean_motion = planet_mean_motion - const.moon_apogee_mean_motion
            #print(p_id,'planet_mean_motion after',planet_mean_motion)
        #print(p_id,'corrected_periphery',corrected_periphery)
        rectified_periphery = (const.mandakendrajya_indian_sine_radius/360.0) * corrected_periphery
        #print(p_id,'rectified_periphery',rectified_periphery) 
        tab_sine_diff = abs(225*0.991335735*cosd(1.024764846*(180.0-planet_mandocca_anomaly-3.75)))
        #print(p_id,'tab_sine_diff',tab_sine_diff)
        " You should use true motion here"
        planet_true_motion_correction = corrected_periphery*planet_mean_motion*tab_sine_diff/(360*225)
        planet_true_motion = planet_mean_motion + mandakendra_sign * planet_true_motion_correction
        #print(p_id,'planet_true_motion',planet_mean_motion,planet_true_motion_correction,corrected_periphery,tab_sine_diff,utils.to_dms(planet_true_motion,is_lat_long='plong')) 
        mandaphala_correction = mandakendra_sign * rectified_periphery*sind(mandakendra)
    else:
        Po,Pe = _manda_periphery(planet)
        corrected_periphery = Pe - (Pe-Po) * abs(sind(mandakendra))
        #print(p_id,'mandaphala corrected_periphery',Po,Pe,corrected_periphery)
        mandaphala_correction = const.mandakendrajya_indian_sine_radius/360.0 * corrected_periphery * sind(mandakendra)
    """ TODO Check sine inverse is required for MPH """
    #mandaphala_correction = math.asin(mandaphala_correction*math.pi/180.0)
    #print(p_id,'mandaphala_correction',mandaphala_correction)
    return mandaphala_correction
def _true_longitude_after_sighra_correction(jd,place,planet,planet_mean_long,mandaphala_correction):
    p_id = list(SS_PLANET_LIST).index(planet)
    MP = planet_mean_long
    if planet in [const._SUN, const._MOON, const._RAHU, const._KETU]:
        return 0.0
    p_id = list(SS_PLANET_LIST).index(planet)
    def _get_sighra_anamoly(jd,planet,long):
        if const.planet_mean_longitudes[const._SUN]==0.0:
            const.planet_mean_longitudes[const._SUN] = _mean_solar_longitude(jd)[0] #_planet_mean_longitude(jd, place, const._SUN)
        if planet in [const._MERCURY, const._VENUS]:
            m = (long - const.planet_mean_longitudes[const._SUN]+360)%360
            #print(p_id,'Sighra anomaly = Planets sighrocca - mean sun',to_dms(long),'-',to_dms(const.planet_mean_longitudes[const._SUN]),'=',to_dms(m))                  
        else:
            m = (const.planet_mean_longitudes[const._SUN] - long+360)%360 #const.planet_mean_longitudes[planet]+360)%360
            #print(p_id,'Sighra anomaly = Mean sun - mean planet',to_dms(const.planet_mean_longitudes[const._SUN]),'-', to_dms(const.planet_mean_longitudes[planet]),'=',to_dms(m))
        return m
    def _get_sighra_correction(jd,planet,p_m_l):
        m = _get_sighra_anamoly(jd, planet, p_m_l)
        """
        p_id = list(SS_PLANET_LIST).index(planet)
        if const.planet_mean_longitudes[const._SUN]==0.0:
            const.planet_mean_longitudes[const._SUN] = _mean_solar_longitude(jd)[0] #_planet_mean_longitude(jd, place, const._SUN)
        if planet in [const._MERCURY, const._VENUS]:
            m = (p_m_l - const.planet_mean_longitudes[const._SUN]+360)%360
            print(p_id,'Sighra anomaly = Planets sighrocca - mean sun',to_dms(p_m_l),'-',to_dms(const.planet_mean_longitudes[const._SUN]),'=',to_dms(m))                  
        else:
            m = (const.planet_mean_longitudes[const._SUN] - p_m_l+360)%360 #const.planet_mean_longitudes[planet]+360)%360
            #print(p_id,'Sighra anomaly = Mean sun - mean planet',to_dms(const.planet_mean_longitudes[const._SUN]),'-', to_dms(const.planet_mean_longitudes[planet]),'=',to_dms(m))
        """
        #print(p_id,'sighra anamoly - m',m)
        sign = 1.0
        if m > 90. and m < 270.0:
            sign = -1.0
        """ Calculate corrected sighra periphery """
        Po,Pe = const.planet_sighra_peripheries[planet]
        P = Pe - (Pe-Po) * abs(sind(m))
        r = P/360.0
        R = const.mandakendrajya_indian_sine_radius * 60.0
        #print(p_id,'Po,Pe,P,r,sighra anomaly(m)',to_dms(Po),to_dms(Pe),to_dms(P),r,to_dms(m))
        dohphala = r * R * sind(m)
        kotiphala = r * R * cosd(m)
        sphutakoti = R + kotiphala
        sighrakarna = math.sqrt(sphutakoti*sphutakoti+dohphala*dohphala)
        rsinsighraphala = dohphala*R/sighrakarna
        #print(p_id,'dohphala,kotiphala,sphutakoti,sighrakarna,rsinsighraphala',dohphala,kotiphala,sphutakoti,sighrakarna,rsinsighraphala)
        sighraphala = math.asin(rsinsighraphala/R)*180.0/math.pi
        #print(p_id,'sighraphala',to_dms(sighraphala))
        return sighraphala
    SE1 = _get_sighra_correction(jd,planet,MP)
    P1 = MP + 0.5 * SE1
    #print(p_id,'first step _get_sighra_correction','MP,SE1,P1',MP,SE1,P1)
    ME1 = mandaphala_correction
    P2 = P1 + 0.5 * ME1
    #print(p_id,'2nd step','P1,ME1,P2',P1,ME1,P2)
    ME2 = _mandaphala_planet(jd,planet, P2)
    P3 = MP + ME2
    const.planet_mean_longitudes[planet] = P3
    #print(p_id,'3rd step _mandaphala_planet','MP,ME2,P3',MP,ME2,P3)
    SE2 = _get_sighra_correction(jd,planet,P3)
    P4 = P3 + SE2
    #print(p_id,'4th step _get_sighra_correction','P3,SE2,P4',P3,SE2,P4)
    if planet in [const._MERCURY, const._VENUS]:
        """ Нижні планети: сігра-фала = елонгація відносно Сонця.
            Геоцентрична довгота = довгота Сонця + елонгація (не mean + фала!). """
        if const.planet_mean_longitudes[const._SUN] == 0.0:
            const.planet_mean_longitudes[const._SUN] = _planet_mean_longitude(jd, place, const._SUN)
        sun_long = _planet_true_longitude(jd, place, const._SUN, const.planet_mean_longitudes[const._SUN])
        P4 = (sun_long + SE2) % 360
    return P4
def _planet_true_longitude(jd,place,planet,planet_mean_long):
    p_id = list(SS_PLANET_LIST).index(planet)
    if planet in [const._RAHU, const._KETU]:
        return planet_mean_long
    """ Correction for Equation of Center aka Mandaphala """
    mandaphala = _mandaphala_planet(jd,planet,planet_mean_long)
    if planet == const._SUN:
        global mandaphala_of_sun
        mandaphala_of_sun = mandaphala
    #print(p_id,'mandaphala',mandaphala,utils.to_dms(mandaphala,is_lat_long='plong'))
    mandaphala_corrected_longitude = planet_mean_long + mandaphala
    #print(p_id,'_planet_true_longitude',planet_mean_long,mandaphala_of_sun,mandaphala_corrected_longitude,utils.to_dms(mandaphala_corrected_longitude,is_lat_long='plong'))
    bcs = bhujantara_correction(planet, mandaphala_of_sun)
    mandaphala_corrected_longitude += bcs
    true_longitude = (mandaphala_corrected_longitude+360)%360
    #print(p_id,'planet true longitude',true_longitude)
    if planet in [const._SUN, const._MOON, const._RAHU, const._KETU]: 
        return true_longitude
    else:
        true_longitude = (_true_longitude_after_sighra_correction(jd,place,planet,planet_mean_long,mandaphala)+360)%360
        """ CRUDE FIX - INCORRECT - NO LOGIC
        if planet in [const._MERCURY]:#, const._VENUS]:
            true_longitude += const.manodcca_positions_at_kali[planet]
        elif planet in [const._VENUS]:#, const._VENUS]:
            true_longitude -= const.manodcca_positions_at_kali[planet]
        """
        return true_longitude
def planet_positions(jd,place:drik.Place):
    planet_positions_ss = []
    #planet_corrections = [0,90.0,0,-120.0,0,-180,0,0,0]
    #drik.set_ayanamsa_mode('SURYASIDDHANTA', ayanamsa_value=None, jd=jd)
    #ss_ayanamsa = drik.get_ayanamsa_value(jd)
    #print('SS Ayanamsa',ss_ayanamsa)
    planet_corrections = [0,0.0,0,0.0,0,0,0,0,0] # [x-ss_ayanamsa for x in [0,0.0,0,0.0,0,0,0,0,0]]
    for planet in SS_PLANET_LIST: #[const._SUN,const._MOON,const._SATURN]:#
        p_id = list(SS_PLANET_LIST).index(planet)
        mean_long = _planet_mean_longitude(jd,place,planet)
        #print(p_id,'mean longitude',planet,mean_long,utils.to_dms(mean_long, is_lat_long='plong'))
        corrected_long = (_planet_true_longitude(jd,place,planet, mean_long)+planet_corrections[p_id])%360.
        planet_positions_ss.append([p_id,[int(corrected_long/30),corrected_long%30]]    )
        #print(p_id,'true longitude',planet,corrected_long,utils.to_dms(corrected_long, is_lat_long='plong'))
    # Calculate ascendant and add to planet positions
    #asc = drik.ascendant(jd, place)
    sun_long = planet_positions_ss[0][1][0]*30+planet_positions_ss[0][1][1]
    asc = ascendant_new(jd, place, sun_long)
    planet_positions_ss = [[const._ascendant_symbol,[asc[0],asc[1]]]] + planet_positions_ss
    #print('planet_positions_ss',planet_positions_ss)
    return planet_positions_ss
def _lunar_evection(sun_mean_longitude, moon_mean_longitude):
    pass
def _declination_of_sun_1(jd):
    d = jd - 2451545.0
    mean_anamoly_sun = (357.529*0.98560028*d)%360
    mean_long_sun = (280.459 + 0.98564736 * d)%360
    sun_ecliptic_long = mean_long_sun + 1.915*sind(mean_anamoly_sun) + 0.020*sind(2*mean_anamoly_sun)
    obliquity_sun = 23.439 - 0.00000036 * d
    decl = math.asin(sind(obliquity_sun) * sind(sun_ecliptic_long))*180/math.pi
    #print(jd,mean_anamoly_sun,mean_long_sun,obliquity_sun,decl)
    return decl
def _declination_of_sun(jd):
    y,m,d,_ = utils.jd_to_gregorian(jd)
    jd_eq = utils.julian_day_number((y,3,21), (12,0,0))
    days = jd-jd_eq
    deli = (23+27/60.)*sind(360*days/365.25)
    #print(jd_eq,jd,days,deli)
    return deli
def sunrise_set(jd,place):
    decl = drik.declination_of_planets(jd, place)
    decl_sun = _declination_of_sun(jd)
    lat = place.latitude
    prad = math.pi/180.0
    sr_hrs = math.acos(-math.tan(lat*prad)*math.tan(decl_sun*prad))/prad/15.0
    srise = 12.0-sr_hrs
    sset = 12.0+sr_hrs
    return [srise,utils.to_dms(srise),sset,utils.to_dms(sset)]
def tithi(jd, place):
    pp = planet_positions(jd, place)
    sun_long = pp[1][1][0]*30+pp[1][1][1]
    moon_long = pp[2][1][0]*30+pp[2][1][1]
    l_diff = (moon_long+360-sun_long)%360
    _tithi = (l_diff/12)%30
    _tithi_no = math.ceil(_tithi)
    _td_left = _tithi_no*12-l_diff
    sun_dm = _true_daily_motion_planet(jd, place, const._SUN)
    moon_dm = _true_daily_motion_planet(jd, place, const._MOON)
    _th_left = _td_left/(moon_dm-sun_dm)*24.0
    _,_,_,h = utils.jd_to_gregorian(jd)
    _,_,_,fh = utils.jd_to_gregorian(jd+_th_left)
    fh +=h
    return[_tithi_no,utils.to_dms(fh)]
def nakshatra(jd,place):
    pp = planet_positions(jd, place)
    moon_long = pp[2][1][0]*30+pp[2][1][1]
    nak_no,padham_no,_ = drik.nakshatra_pada(moon_long)
    rem = (nak_no / 27 * 360.)-moon_long
    moon_dm = _true_daily_motion_planet(jd, place, const._MOON)
    _nak_left = rem/moon_dm*24.0
    _,_,_,h = utils.jd_to_gregorian(jd)
    _,_,_,fh = utils.jd_to_gregorian(jd+_nak_left)
    fh +=h
    return [nak_no,padham_no,utils.to_dms(fh)]
def solar_month_and_date(panchanga_date,place,base_time=0,use_utc=True): # V4.4.0
    """
        @param base_time: 0 => sunset time, 1 => sunrise time 2 => midday time
        @param use_utc: True (default) use uninversal time
    """
    jd = utils.julian_day_number(panchanga_date, (10,0,0))
    #srise_hr,_,sset_hr,_ = sunrise_set(jd, place)
    #jd_base = sunset(jd, place)[2] if base_time==0 else (sunrise(jd,place)[2] if base_time==1 else midday(jd, place)[1])
    #jd_utc = jd_base - place.timezone/24 if use_utc else jd_base
    #sr = solar_longitude(jd_utc)
    solar_mean_long = _planet_mean_longitude(jd, place, const._SUN)
    sr = _planet_true_longitude(jd, place, const._SUN, solar_mean_long)
    tamil_month = int(sr/30)
    daycount=1
    while True:
        if sr%30<1 and sr%30>0:
            break
        jd -= 1
        #jd_base = sunset(jd, place)[2] if base_time==0 else (sunrise(jd,place)[2] if base_time==1 else midday(jd, place)[1])
        #jd_utc = jd_base - place.timezone/24 if use_utc else jd_base
        #sr = solar_longitude(jd_utc)
        solar_mean_long = _planet_mean_longitude(jd, place, const._SUN)
        sr = _planet_true_longitude(jd, place, const._SUN, solar_mean_long)
        daycount+=1
    return tamil_month, daycount
def _balachandra_rao_basic_program():
    """ ########## Conversion of BASIC Program to python below ################# """
    pi = 3.141592653589793
    print("Year:"); y = int(input())
    print("Month:"); mm = int(input())
    print("Date:"); d1 = int(input())
    print("Hours:"); h1 = int(input())
    print("Minutes:"); m1 = int(input())
    print("Longitude: -ve for West")
    print("Degrees:"); ld = int(input())
    print("Minutes:"); lm = int(input())
    print("Latitude: -ve for South")
    print("Degrees:"); pd = int(input())
    print("Minutes:"); pm = int(input())
    lam = ld - lm/60 if ld < 0 else ld + lm/60
    phi = pd - pm/60 if pd < 0 else pd + pm/60
    """ Ujjain Long/Lat: 75.75E 23.18N """
    ulam = 75.75-lam
    tc = int((y-1900)/100)
    t = y-100*(y/100)
    if tc < -4:
        e = 13
    if tc == -4 and y < 1582:
        e = 13
    if tc == -4 and y > 1582:
        e = 3
    if tc < -4 and tc <= 0:
        e = -tc
    if tc > 0:
        e = -(tc-1)
    q = - (t%4)
    dd = 0
    month_lengths = [0,31,28,31,30,31,30,31,31,30,31,30]
    dd = sum(month_lengths[1:mm+1])

if __name__ == "__main__":
    utils.set_language('en')
    #place = drik.Place('Ujjain',23.1765, 75.7885,5.5)
    #dob = drik.Date(-3101,1,22)
    #tob = (6,37,11)
    #dob = drik.Date(505,3,23)
    #dob = (0,0,1)
    #place = drik.Place('Bangalore',12.9716,77.5946,5.5)
    #dob = drik.Date(1970,3,22)
    #tob = (0,0,1)
    dob = drik.Date(1981,9,13); tob = (1,30,0); place = drik.Place('unknown',28+39/60,77+13/60,5.5)
    jd = utils.julian_day_number(dob, tob)
    drik.set_ayanamsa_mode('SURYASIDDHANTA')
    for p_id,planet in enumerate([const._SUN, const._MOON,const._MARS, const._MERCURY, const._JUPITER, const._VENUS, const._SATURN]):
        planet_mean_long = _planet_mean_longitude(jd, place, planet)
        print(p_id,planet,planet_mean_long, _planet_true_longitude(jd, place, planet, planet_mean_long))
    #exit()
    place = drik.Place('Chennai',13.0878,80.2785,5.5)
    dob = drik.Date(-508,3,28)#(1996,12,7)#
    tob = (12,0,0)
    jd = utils.julian_day_number(dob, tob)
    sm,sd = solar_month_and_date(dob, place)
    print('tamil month',utils.MONTH_LIST[sm],'tamil day',sd)
    vd = drik.vedic_date(jd, place, calendar_type=1)
    print('vedic date',utils.MONTH_LIST[vd[0]-1],vd[1],utils.YEAR_LIST[vd[2]-1])
    print(jd,'ahargana',kali_ahargana(jd))
    print(sunrise_set(jd, place),drik.sunrise(jd, place),drik.sunset(jd, place))
    print(utils.TITHI_LIST[tithi(jd, place)[0]-1],utils.TITHI_LIST[drik.tithi(jd, place)[0]-1])
    print(utils.NAKSHATRA_LIST[nakshatra(jd,place)[0]-1],utils.NAKSHATRA_LIST[drik.nakshatra(jd, place)[0]-1])
    exit()
    #"""
    planet_positions_ss = planet_positions(jd,place)
    sun_long = planet_positions_ss[1][1][0]*30+planet_positions_ss[1][1][1]
    print(ascendant_new(jd, place, sun_long))
    print(planet_positions_ss)
    planet_positions_drik = charts.rasi_chart(jd, place)
    print(planet_positions_drik)
    for p in range(len(planet_positions_ss)):
        p_long_ss = planet_positions_ss[p][1][0]*30+planet_positions_ss[p][1][1]
        p_long_drik = planet_positions_drik[p][1][0]*30+planet_positions_drik[p][1][1]
        p_diff = abs(p_long_drik-p_long_ss)
        print(planet_positions_drik[p][0],'drik-posn',p_long_drik,'ss-posn',p_long_ss,'diff',p_diff)
    sun_long = planet_positions_ss[1][1][0]*30+planet_positions_ss[1][1][1]
    print(sun_long,ascendant_new(jd, place, sun_long), drik.ascendant(jd, place))