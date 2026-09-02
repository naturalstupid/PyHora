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
    TODO: Check use of julian_day vs julian_years if used consistently
    For example: Special Lagna/Ascendant Calculations require jd_years or years/months/60hrs and new tob
"""
"""
    TODO: When selecting Janma, Annual, Tithi Pravesha - which TABS should it be applied and which ones not
    For example only charts? Dhasa Bhukthi as well, how about other TABS line dosha, compatibility etc
    Which TABS should always be based on NATAL CHART?
"""
import swisseph as swe
from datetime import date
from jhora import const, utils
from jhora.panchanga import drik, surya_sidhantha
from jhora.horoscope.chart import house,charts

_lang_path = const._LANGUAGE_PATH
chara_karakas = ['atma_karaka','amatya_karaka','bhratri_karaka','maitri_karaka','pitri_karaka','putra_karaka','jnaati_karaka','data_karaka']

dhasavarga_dict = {}
class Horoscope():  
    def __init__(self,place_with_country_code:str=None,latitude:float=None,longitude:float=None,timezone_offset:float=None,
                 date_in:drik.Date=None,birth_time:str=None,
                 calculation_type:str='drik',years=1,months=1,sixty_hours=1,pravesha_type=0,
                 bhava_madhya_method = None,language=None):
        if language is None: language = const._DEFAULT_LANGUAGE
        if bhava_madhya_method is None: bhava_madhya_method = const.bhaava_madhya_method
        self._language = language
        self._bhava_madhya_method = bhava_madhya_method
        utils.set_language(language)
        self.cal_key_list = utils.resource_strings
        self.place_name = place_with_country_code
        self.latitude = latitude
        self.longitude = longitude
        self.timezone_offset = timezone_offset
        self.Date = date_in
        self.birth_time = birth_time
        self.pravesha_type = pravesha_type
        self._22nd_drekkana = {}
        self._64th_navamsa = {}
        if self.place_name is None:
            if self.latitude is None or self.longitude is None or self.timezone_offset is None:
                raise ValueError('Please provide either place_with_country_code or latitude, longitude, and timezone_offset')
            else:
                self.place_name = 'Not Provided'
                self.latitude = latitude
                self.longitude = longitude
                self.timezone_offset = timezone_offset                
        else:
            if self.latitude is None or self.longitude is None or self.timezone_offset is None:
                [_,self.latitude,self.longitude,self.timezone_offset] = \
                    utils.get_location_using_nominatim(place_with_country_code)
                
                
        if date_in is None :
            self.Date = drik.Date(date.today().year,date.today().month,date.today().day)
        else:
            self.Date = drik.Date(date_in.year,date_in.month,date_in.day)
        self.Place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        self.julian_utc = utils.gregorian_to_jd(self.Date)
        #self.timezone_offset = drik.get_place_timezone_offset(self.latitude,self.longitude)
        if (birth_time!=None):
            normalized_birth_time = birth_time.strip().upper()
            is_pm = normalized_birth_time.endswith('PM')
            is_am = normalized_birth_time.endswith('AM')
            normalized_birth_time = normalized_birth_time.replace('AM','').replace('PM','').strip()
            btArr = normalized_birth_time.split(':')
            birth_hour = int(btArr[0])
            if is_pm and birth_hour < 12:
                birth_hour += 12
            elif is_am and birth_hour == 12:
                birth_hour = 0
            self.julian_day = swe.julday(self.Date.year,self.Date.month,self.Date.day, birth_hour+int(btArr[1])/60)
            self.birth_time = (birth_hour,int(btArr[1]),0)
            if (len(btArr)==3):
                self.julian_day = swe.julday(self.Date.year,self.Date.month,self.Date.day, birth_hour+int(btArr[1])/60+int(btArr[2])/3600)
                self.birth_time = (birth_hour,int(btArr[1]),int(btArr[2]))
        else:
            self.julian_day = utils.gregorian_to_jd(self.Date)
        # Set Ayanamsa Mode
        if calculation_type not in const.available_horoscope_calculation_methods:
            print('calculation type',calculation_type,' not in list of available calculation methods',const.available_horoscope_calculation_methods,'Default:drik is used')
            calculation_type = 'drik'
        self.calculation_type = calculation_type.lower()
        """ Force Surya sidhantha ayanamsa for SS calculation type"""
        if self.calculation_type == 'ss':
            print('Horoscope:main: Forcing ayanamsa to SURYASIDDHANTA for the SURYA SIDDHANTA calculation type')
            drik.set_ayanamsa_mode('SURYASIDDHANTA')
        self.ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
        self.ayanamsa_value = drik.get_ayanamsa_value(self.julian_day)
        self.years = years; self.months=months; self.sixty_hours=sixty_hours
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        self.julian_years = drik.next_solar_date(self.julian_day, place, years, months, sixty_hours)
        self.julian_years_utc = utils.julian_day_utc(self.julian_day,self.Place)
        self.calendar_info = self.get_calendar_information()
        self.bhava_chart,self.bhava_chart_info,self._bhava_ascendant_house = self.get_bhava_chart_information(self.julian_years,place,self._bhava_madhya_method)
        return
    def _get_planet_list(self):
        return utils.PLANET_NAMES,utils.PLANET_SHORT_NAMES
    def _get_raasi_list(self):
        return utils.RAASI_LIST,utils.RAASI_SHORT_LIST
    def _get_calendar_resource_strings(self):#, language='en'):
        list_file = _lang_path + 'list_values_'+self._language+'.txt'
        msg_file = _lang_path + 'msg_strings_'+self._language+'.txt'
        cal_key_list=utils._read_resource_messages_from_file(msg_file) #utils.get_resource_messages(msg_file)
        _ = utils._read_resource_lists_from_file(list_file)#utils.get_resource_lists(list_file)
        return cal_key_list
    def get_calendar_information(self):#, language='en'):
        jd = self.julian_day # self.julian_day #jd = self.julian_years #
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        #utils.set_language(language)
        cal_key_list = utils.resource_strings
        self.cal_key_list = cal_key_list
        self._ascendant_str = cal_key_list['ascendant_str']
        as_string = True
        calendar_info = {
            cal_key_list['place_str'] : self.place_name,
            cal_key_list['latitude_str'] : utils.to_dms(self.latitude,is_lat_long='lat',as_string=as_string), #"{0:.2f}".format(self.latitude),
            cal_key_list['longitude_str'] : utils.to_dms(self.longitude,is_lat_long='long',as_string=as_string), # "{0:.2f}".format(self.longitude),
            cal_key_list['timezone_offset_str'] : "{0:.2f}".format(self.timezone_offset),
            cal_key_list['report_date_str'] : "{0:d}-{1:d}-{2:d}".format(self.Date.year,self.Date.month,self.Date.day)#self.Date.isoformat(),         
        }
        vaaram = drik.vaara(jd, place)
        calendar_info[cal_key_list['vaaram_str']]=utils.DAYS_LIST[vaaram]
        calendar_info[cal_key_list['calculation_type_str']]=cal_key_list['drik_panchang_str']
        if self.calculation_type.lower()=='ss':
            calendar_info[cal_key_list['calculation_type_str']]=cal_key_list['ss_panchang_str']
        jd = self.julian_years #jd = self.julian_day
        maasam_no,adhik_maasa,nija_maasa = drik.lunar_month(jd,place)
        """ Check if current month is Nija Maasa """
        nija_month_str = ''
        if nija_maasa:
            nija_month_str = cal_key_list['nija_month_str']
        _tithi = drik.tithi(self.julian_day,place)
        _paksha = 0
        if _tithi[0] > 15: _paksha = 1 # V3.1.1
        """ Lunar Day is nothing but tithi number """
        #day_no = _tithi[0]
        """ Tamil Calendar gives solar day """
        tm,td = drik.tamil_solar_month_and_date(self.Date, place)
        #maasam = utils.MONTH_LIST[maasam_no-1]
        adhik_maasa_str = ''; 
        if adhik_maasa:
            adhik_maasa_str = cal_key_list['adhika_maasa_str']
        _samvatsara = drik.samvatsara(self.Date, place, zodiac=0)
        calendar_info[cal_key_list['lunar_year_month_str']]=utils.YEAR_LIST[_samvatsara]+' / '+utils.MONTH_LIST[maasam_no-1]+' '+adhik_maasa_str+nija_month_str
        calendar_info[cal_key_list['tamil_month_str']] = utils.MONTH_LIST[tm] +" "+cal_key_list['date_str']+' '+str(td)
        [kali_year, vikrama_year,saka_year] = drik.elapsed_year(jd,maasam_no)
        calendar_info[cal_key_list['kali_year_str']] = kali_year
        calendar_info[cal_key_list['vikrama_year_str']] = vikrama_year
        calendar_info[cal_key_list['saka_year_str']] = saka_year
        sun_rise = drik.sunrise(self.julian_utc,place)
        calendar_info[cal_key_list['sunrise_str']] = sun_rise[1]
        sun_set = drik.sunset(self.julian_utc,place)
        calendar_info[cal_key_list['sunset_str']] = sun_set[1]
        moon_rise = drik.moonrise(self.julian_utc,place)[1]
        calendar_info[cal_key_list['moonrise_str']] = moon_rise
        moon_set = drik.moonset(self.julian_utc,place)[1]
        calendar_info[cal_key_list['moonset_str']] = moon_set
        jd = self.julian_day # 2.0.3
        _,_,_,birth_time_hrs = utils.jd_to_gregorian(jd)
        frac_left = 100*utils.get_fraction(_tithi[1], _tithi[2], birth_time_hrs)
        calendar_info[cal_key_list['tithi_str']]= utils.PAKSHA_LIST[_paksha]+' '+utils.TITHI_LIST[_tithi[0]-1]+ \
                        ' (' + utils.TITHI_DEITIES[_tithi[0]-1]+') '+ utils.to_dms(_tithi[1])+ ' '+\
                        cal_key_list['starts_at_str'] + ' ' + \
                        utils.to_dms(_tithi[2])+ ' ' + cal_key_list['ends_at_str']+' ('+"{0:.2f}".format(frac_left)+'% ' + \
                        cal_key_list['balance_str']+' )'
        rasi = drik.raasi(jd,place)
        frac_left = rasi[2]*100
        calendar_info[cal_key_list['raasi_str']] = utils.RAASI_LIST[rasi[0]-1]+' '+utils.to_dms(rasi[1])+ ' ' + \
                    cal_key_list['ends_at_str'] +' ('+"{0:.2f}".format(frac_left)+'% ' + \
                    cal_key_list['balance_str']+' )'
        nak = drik.nakshatra(jd,place)
        frac_left = 100*utils.get_fraction(nak[2],nak[3],birth_time_hrs)
        #print('nakshatra',nak,frac_left)
        calendar_info[cal_key_list['nakshatra_str']] = utils.NAKSHATRA_LIST[nak[0]-1]+' '+  \
                    ' ('+utils.PLANET_SHORT_NAMES[utils.nakshathra_lord(nak[0])]+') '+ cal_key_list['paadham_str']+\
                    str(nak[1]) + ' '+ utils.to_dms(nak[2]) + ' '+ cal_key_list['starts_at_str'] + ' ' + \
                    utils.to_dms(nak[3]) + ' ' + cal_key_list['ends_at_str'] + \
                    ' ('+"{0:.2f}".format(frac_left)+'% ' + cal_key_list['balance_str']+' )'
        self._nakshatra_number, self._paadha_number = nak[0],nak[1]
        jd = self.julian_day 
        _raahu_kaalam = drik.raahu_kaalam(jd,place)
        calendar_info[cal_key_list['raahu_kaalam_str']] = _raahu_kaalam[0] + ' '+ cal_key_list['starts_at_str']+\
                        ' '+ _raahu_kaalam[1]+' '+cal_key_list['ends_at_str']
        kuligai = drik.gulikai_kaalam(jd,place)
        calendar_info[cal_key_list['kuligai_str']] = kuligai[0] + ' '+ cal_key_list['starts_at_str']+\
                        ' '+ kuligai[1]+' '+cal_key_list['ends_at_str']
        yamagandam = drik.yamaganda_kaalam(jd,place)
        calendar_info[cal_key_list['yamagandam_str']] = yamagandam[0] + ' '+ cal_key_list['starts_at_str']+\
                        ' '+ yamagandam[1]+' '+cal_key_list['ends_at_str']
        yogam = drik.yogam(self.julian_day,place)
        frac_left = 100*utils.get_fraction(yogam[1], yogam[2], birth_time_hrs)
        yoga_lord = ' ('+utils.PLANET_SHORT_NAMES[const.yogam_lords_and_avayogis[yogam[0]-1][0]]+'/'+\
                        utils.PLANET_SHORT_NAMES[const.yogam_lords_and_avayogis[yogam[0]-1][1]]+') '
        calendar_info[cal_key_list['yogam_str']] = utils.YOGAM_LIST[yogam[0]-1] + yoga_lord + \
                        '  '+utils.to_dms(yogam[1])+ ' ' +\
                        cal_key_list['starts_at_str'] + ' ' + utils.to_dms(yogam[2])+ ' ' + \
                        cal_key_list['ends_at_str']+' ('+"{0:.2f}".format(frac_left)+'% ' + cal_key_list['balance_str']+' )'
        karanam = drik.karana(jd,place); frac_left= 100*utils.get_fraction(karanam[1], karanam[2], birth_time_hrs)
        karana_lord = utils.PLANET_SHORT_NAMES[utils.karana_lord(karanam[0])]
        calendar_info[cal_key_list['karanam_str']] = utils.KARANA_LIST[karanam[0]-1]+' ('+ karana_lord +') '+\
                        utils.to_dms(karanam[1])+ ' ' +\
                        cal_key_list['starts_at_str'] + ' ' + utils.to_dms(karanam[2])+ ' ' + \
                        cal_key_list['ends_at_str']+' ('+"{0:.2f}".format(frac_left)+'% ' + cal_key_list['balance_str']+' )'
        abhijit = drik.abhijit_muhurta(jd,place)
        calendar_info[cal_key_list['abhijit_str']] = abhijit[0] + ' '+ cal_key_list['starts_at_str']+\
                        ' '+ abhijit[1]+' '+cal_key_list['ends_at_str']
        _dhurmuhurtham = drik.durmuhurtam(jd,place)
        calendar_info[cal_key_list['dhurmuhurtham_str']] = _dhurmuhurtham[0] + ' '+ cal_key_list['starts_at_str']+\
                        ' '+ _dhurmuhurtham[1]+' '+cal_key_list['ends_at_str']
        return calendar_info
    def get_horoscope_chart_counter(self,chart_key):
        global dhasavarga_dict
        value_list = list(dhasavarga_dict.values())
        counter = [ index for index,value in enumerate(value_list) if chart_key in value][0]
        return counter
    def get_bhava_chart_information(self, jd,place,divisional_chart_factor=1,
                                    bhaava_madhya_method=None,
                                    chart_method=None, base_rasi=None, count_from_end_of_sign=None):
        if bhaava_madhya_method is None: bhaava_madhya_method = const.bhaava_madhya_method
        _bhava_chart_info = []; cal_key_list = self.cal_key_list; _bhava_chart = [ ''  for _ in range(len(utils.RAASI_LIST))]
        #jd = self.julian_day; place = self.Place
        #_bhava_info = charts.bhava_chart(jd, place,bhava_madhya_method=bhaava_madhya_method)
        _bhava_info = charts._bhaava_madhya_new(jd, place,divisional_chart_factor=divisional_chart_factor,
                                                bhava_madhya_method=bhaava_madhya_method,
                                                chart_method=chart_method, base_rasi=base_rasi,
                                                count_from_end_of_sign=count_from_end_of_sign)
        retrograde_planets = drik.planets_in_retrograde(jd, place)
        h = 1; planet_separator = '\n'
        for br,(bs,bm,be),pls in _bhava_info:
            key = cal_key_list['house_str']+'-'+str(h)
            bs1 = drik.dasavarga_from_long(bs);bm1 = drik.dasavarga_from_long(bm);be1 = drik.dasavarga_from_long(be)
            bss = utils.RAASI_SHORT_LIST[bs1[0]]+' ' + utils.to_dms(bs1[1],is_lat_long='plong')
            bms = utils.RAASI_SHORT_LIST[bm1[0]]+' ' + utils.to_dms(bm1[1],is_lat_long='plong')
            bes = utils.RAASI_SHORT_LIST[be1[0]]+' ' + utils.to_dms(be1[1],is_lat_long='plong')
            ps = ''; retStr = ''
            for p in pls:
                if p==const._ascendant_symbol:
                    ps = cal_key_list['ascendant_short_str']+planet_separator
                    _bhava_chart[br] += cal_key_list['ascendant_str'] +"\n"
                    _bhava_ascendant_house = br
                else:
                    p1 = int(p)
                    retStr=const._retrogade_symbol if p1 in retrograde_planets else ''
                    ps += utils.PLANET_SHORT_NAMES[p1]+retStr+planet_separator
                    planet_name = utils.PLANET_NAMES[p1]+retStr
                    _bhava_chart[br] += planet_name + "\n"
            _bhava_chart_info.append((key,bss,bms,bes,ps.strip()))
            h += 1
        return _bhava_chart,_bhava_chart_info,_bhava_ascendant_house
    def get_horoscope_information_for_chart(self,chart_index=0,chart_method=1,divisional_chart_factor=None,
                                            base_rasi=None,count_from_end_of_sign=None,varnada_method=None):
        horoscope_info = {}
        self._vimsottari_balance = ();self._yoga_vimsottari_balance = ()
        self._arudha_lagna_data_kundali = {}
        self._sphuta_data_kundali = {}
        self._graha_lagna_data_kundali = {}
        self._hora_lagna_data_kundali = {}; self._ghati_lagna_data_kundali = {}; self._vighati_lagna_data_kundali = {}
        self._pranapada_lagna_data_kundali = {}; self._indu_lagna_data_kundali = {}; self._bhrigu_bindhu_lagna_data_kundali = {}
        self._bhava_lagna_data_kundali = {}; self._sree_lagna_data_kundali = {}; self._kunda_lagna_data_kundali={}
        self._varnada_lagna_data_kundali = {}
        self._maandhi_data_kundali = {}#; self._aayu_dhasa_type = -1; self._kaala_dhasa_type = -1
        horoscope_charts = [ ''  for _ in range(len(utils.RAASI_LIST))]
        horoscope_ascendant_house = -1
        cal_key_list = self.cal_key_list#self._get_calendar_resource_strings(language)
        jd = self.julian_day # V3.1.9 If Julian_Years to be used then years/months arguments should not be used
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        dob = drik.Date(self.Date.year,self.Date.month,self.Date.day)
        tob=self.birth_time
        tob_in_hrs = tob[0]+tob[1]/60.0+tob[2]/3600.0
        global dhasavarga_dict
        dhasavarga_dict={1:cal_key_list['raasi_str'],
                         2:cal_key_list['hora_str'],
                         3:cal_key_list['drekkanam_str'],
                         4:cal_key_list['chaturthamsa_str'],
                         5:cal_key_list['panchamsa_str'],
                         6:cal_key_list['shashthamsa_str'],
                         7:cal_key_list['saptamsam_str'],
                         8:cal_key_list['ashtamsa_str'],
                         9:cal_key_list['navamsam_str'],
                         10:cal_key_list['dhasamsam_str'],
                         11:cal_key_list['rudramsa_str'],
                         12:cal_key_list['dhwadamsam_str'],
                         16:cal_key_list['shodamsa_str'],
                         20:cal_key_list['vimsamsa_str'],
                         24:cal_key_list['chaturvimsamsa_str'],
                         27:cal_key_list['nakshatramsa_str'],
                         30:cal_key_list['thrisamsam_str'],
                         40:cal_key_list['khavedamsa_str'],
                         45:cal_key_list['akshavedamsa_str'],
                         60:cal_key_list['sashtiamsam_str'],
                         81:cal_key_list['nava_navamsa_str'],
                         108:cal_key_list['ashtotharamsa_str'],
                         144:cal_key_list['dwadas_dwadasamsa_str'],
        }
        if divisional_chart_factor is None :
            if chart_index == len(const.division_chart_factors):
                dhasavarga_factor = const.DEFAULT_CUSTOM_VARGA_FACTOR
            else:
                dhasavarga_factor = const.division_chart_factors[chart_index]
        else:
            dhasavarga_factor = divisional_chart_factor
        planet_positions = charts.divisional_chart(jd, place, 
                                            divisional_chart_factor=dhasavarga_factor,chart_method=chart_method,
                                            years=self.years,months=self.months,sixty_hours=self.sixty_hours,
                                            calculation_type='drik',pravesha_type=self.pravesha_type,
                                            base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
        ascendant_navamsa = planet_positions[0][1]
        asc_house = ascendant_navamsa[0]
        #if dhasavarga_factor==9:
        #    self._64th_navamsa = charts.get_64th_navamsa(planet_positions)
        #elif dhasavarga_factor==3:
        #    self._22nd_drekkana = charts.get_22nd_drekkana(planet_positions)
        horoscope_ascendant_house = asc_house
        jd = self.julian_day #V3.1.9
        horoscope_charts[asc_house] += cal_key_list['ascendant_str'] +"\n"
        self._get_sphuta(dob, tob, place, divisional_chart_factor=dhasavarga_factor)
        abl = self._get_arudha_padhas(dob, tob, place, divisional_chart_factor=dhasavarga_factor,
                                chart_method=chart_method,years=self.years,months=self.months,
                                sixty_hours=self.sixty_hours,pravesha_type=self.pravesha_type,
                                base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
        #self._arudha_lagna_data_kundali = self._arudha_lagna_data[dhasavarga_factor].copy()
        for bli,_ in const._arudha_lagnas_included_in_chart.items():
            key = list(abl)[bli-1]
            value = abl[key]
            horoscope_info[key] = value
        jd = self.julian_years # V3.1.9 Special Lagna do not take years arguments - so use julian years
        key_dhasa_factor = dhasavarga_dict[dhasavarga_factor] if divisional_chart_factor in const.division_chart_factors else cal_key_list['custom_varga_kundali_str']
        key = key_dhasa_factor +'-'+cal_key_list['bhava_lagna_str']+' ('+cal_key_list['bhava_lagna_short_str']+')'
        value = drik.bhava_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._bhava_lagna_data_kundali[dhasavarga_factor] = value[0] # V3.1.9
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['hora_lagna_str']+' ('+cal_key_list['hora_lagna_short_str']+')'
        value = drik.hora_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._hora_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['ghati_lagna_str']+' ('+cal_key_list['ghati_lagna_short_str']+')'
        value = drik.ghati_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._ghati_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['vighati_lagna_str']+' ('+cal_key_list['vighati_lagna_short_str']+')'
        value = drik.vighati_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._vighati_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['pranapada_lagna_str']+' ('+cal_key_list['pranapada_lagna_short_str']+')'
        value = drik.pranapada_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._pranapada_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['indu_lagna_str']+' ('+cal_key_list['indu_lagna_short_str']+')'
        value = drik.indu_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._indu_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['bhrigu_bindhu_lagna_str']+' ('+cal_key_list['bhrigu_bindhu_lagna_short_str']+')'
        value = drik.bhrigu_bindhu_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._bhrigu_bindhu_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['kunda_lagna_str']+' ('+cal_key_list['kunda_lagna_short_str']+')'
        value = drik.kunda_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._kunda_lagna_data_kundali[dhasavarga_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['sree_lagna_str']+' ('+cal_key_list['sree_lagna_short_str']+')'
        jd = self.julian_day # V3.1.9 revert to julian after special lagna calculations
        value = drik.sree_lagna(jd,place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._sree_lagna_data_kundali[dhasavarga_factor] = value[0] # V3.1.9
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['varnada_lagna_str']+' ('+cal_key_list['varnada_lagna_short_str']+')'
        value = charts.varnada_lagna(dob, tob, place,divisional_chart_factor=dhasavarga_factor,
                                 chart_method=chart_method,base_rasi=base_rasi,
                                 count_from_end_of_sign=count_from_end_of_sign)
        self._varnada_lagna_data_kundali[dhasavarga_factor]=value[0]            
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['maandi_str']+' ('+cal_key_list['maandi_short_str']+')'
        value = drik.maandi_longitude(dob,tob,place,divisional_chart_factor=dhasavarga_factor)
        self._maandhi_data_kundali[dhasavarga_factor]=value[0]            
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        horoscope_info[key_dhasa_factor +'-'+cal_key_list['ascendant_str']] = \
            utils.RAASI_LIST[ascendant_navamsa[0]]+' '+utils.to_dms(ascendant_navamsa[1],True,'plong')
        """ Chara karakas are based only on Rasi Chart???. Fixed V3.7.2 """
        chara_karaka_names = [x+'_str' for x in house.chara_karaka_names]
        chara_karaka_dict = get_chara_karakas(jd, place, years=self.years,
                                              months=self.months, sixty_hours=self.sixty_hours,
                                              calculation_type=self.calculation_type, pravesha_type=self.pravesha_type)
        retrograde_planets = drik.planets_in_retrograde(jd, place)
        for p,(h,long) in planet_positions[1:]:
            ret_str = ''
            if p in retrograde_planets:
                ret_str = const._retrogade_symbol
            planet_name = utils.PLANET_NAMES[p]+ret_str
            #print('dhasavarga_factor',dhasavarga_factor,'planet_name',planet_name)
            k = key_dhasa_factor+'-'+planet_name
            planet_house = h
            ck_str = ''
            if p !='L' and p < 8:
                ck_index = chara_karaka_dict.index(p)
                ck_str = ' (' + cal_key_list[chara_karaka_names[ck_index]] +')' # Fixed V3.7.2
            v = utils.RAASI_LIST[h]+' ' +utils.to_dms(long,is_lat_long='plong') + ck_str
            horoscope_charts[planet_house] += planet_name +'\n'
            horoscope_info[k]= v
        sub_planet_list_1 = {'kaala_str':'kaala_longitude','mrityu_str':'mrityu_longitude','artha_praharaka_str':'artha_praharaka_longitude','yama_str':'yama_ghantaka_longitude',
                           'gulika_str':'gulika_longitude','maandi_str':'maandi_longitude'}
        sub_planet_list_2 = ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu']
        #sun_long = planet_positions[1][1][0]*30+planet_positions[1][1][1]
        for sp,sp_func in sub_planet_list_1.items():
            k = key_dhasa_factor+'-'+cal_key_list[sp]+' ('+cal_key_list[sp.replace('_str','_short_str')]+')'
            v = eval('drik.'+sp_func+'(dob,tob,place,divisional_chart_factor=dhasavarga_factor)')
            horoscope_info[k] = utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong') 
        for sp in sub_planet_list_2:
            k = key_dhasa_factor+'-'+cal_key_list[sp+'_str']+' ('+cal_key_list[sp+'_short_str']+')'
            v = eval('charts.'+'solar_upagraha_longitudes(planet_positions,sp,divisional_chart_factor=dhasavarga_factor)') # Fixed in V3.6.9
            horoscope_info[k] = utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong')
        for h in range(12):
            vl = charts.varnada_lagna(dob, tob, place, divisional_chart_factor=dhasavarga_factor,
                                      chart_method=chart_method, house_index=h+1, varnada_method=varnada_method,
                                      base_rasi=base_rasi, count_from_end_of_sign=count_from_end_of_sign)
            k = key_dhasa_factor+'-'+cal_key_list['varnada_lagna_str']+' (V'+str(h+1)+')'
            horoscope_info[k] = utils.RAASI_LIST[vl[0]] +' '+utils.to_dms(vl[1],is_lat_long='plong') 
        spl_list = ['tri','chatur','pancha','prana','deha','mrityu','sookshma_tri','beeja','kshetra','tithi','yoga',
                    'yogi','avayogi','rahu_tithi']
        for spl in spl_list:
            from jhora.horoscope.chart import sphuta
            vl = eval('sphuta.'+spl+'_sphuta(dob,tob,place,divisional_chart_factor=dhasavarga_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)')
            k = key_dhasa_factor+'-'+cal_key_list[spl+'_sphuta_str']+' '+cal_key_list['sphuta_str']
            horoscope_info[k] = utils.RAASI_LIST[vl[0]] +' '+utils.to_dms(vl[1],is_lat_long='plong') 
        return horoscope_info, horoscope_charts,horoscope_ascendant_house
    def get_special_planets_for_chart(self,jd,place,divisional_chart_factor=1,chart_method=1,
                                            base_rasi=None,count_from_end_of_sign=None):
        y,m,h,fh = utils.jd_to_gregorian(jd); dob = drik.Date(y,m,h); tob=(fh,0,0)
        cal_key_list = self.cal_key_list
        sub_planet_list = {'Kl':'kaala_str','Mr':'mrityu_str','Ap':'artha_praharaka_str','Yg':'yama_str',
                           'Gk':'gulika_str','Md':'maandi_str','Dm':'dhuma_str','Vp':'vyatipaata_str',
                           'Pv':'parivesha_str','Ic':'indrachaapa_str','Uk':'upaketu_str'}
        spl = charts.special_planet_longitudes(dob, tob, place, divisional_chart_factor=divisional_chart_factor, 
                            chart_method=chart_method, base_rasi=base_rasi, count_from_end_of_sign=count_from_end_of_sign)
        _special_planet_chart = ['' for _ in range(12)]
        for sp,(h,_) in spl:
            _special_planet_chart[h] += cal_key_list[sub_planet_list[sp].replace('_str','_short_str')]+'\n'
        return {cal_key_list['upagraha_str']:_special_planet_chart}
    def get_special_planets_for_mixed_chart(self,jd,place,varga_factor_1=1,chart_method_1=1,varga_factor_2=1,
                                            chart_method_2=1):
        cal_key_list = self.cal_key_list
        y,m,d,fh = utils.jd_to_gregorian(jd); dob = drik.Date(y,m,d); tob=(fh,0,0)
        sub_planet_list = {'Kl':'kaala_str','Mr':'mrityu_str','Ap':'artha_praharaka_str','Yg':'yama_str',
                           'Gk':'gulika_str','Md':'maandi_str','Dm':'dhuma_str','Vp':'vyatipaata_str',
                           'Pv':'parivesha_str','Ic':'indrachaapa_str','Uk':'upaketu_str'}
        spl = charts.special_planet_longitudes_mixed_chart(dob, tob, place, varga_factor_1=varga_factor_1,
                                                chart_method_1=chart_method_1, varga_factor_2=varga_factor_2,
                                                chart_method_2=chart_method_2)
        _special_planet_chart = ['' for _ in range(12)]
        for sp,(h,_) in spl:
            _special_planet_chart[h] += cal_key_list[sub_planet_list[sp].replace('_str','_short_str')]+'\n'
        return {cal_key_list['upagraha_str']:_special_planet_chart}
    def get_horoscope_information_for_mixed_chart(self,chart_index_1=0,chart_method_1=1,chart_index_2=0,
                                                  chart_method_2=1,varnada_method=None):
        horoscope_info = {}
        self._arudha_lagna_data_kundali = {}
        self._sphuta_data_kundali = {}
        self._graha_lagna_data_kundali = {}
        self._hora_lagna_data_kundali = {}; self._ghati_lagna_data_kundali = {}; self._vighati_lagna_data_kundali = {}
        self._pranapada_lagna_data_kundali = {}; self._indu_lagna_data_kundali = {}; self._bhrigu_bindhu_lagna_data_kundali = {}
        self._bhava_lagna_data_kundali = {}; self._sree_lagna_data_kundali = {}; self._kunda_lagna_data_kundali={}
        self._varnada_lagna_data_kundali = {}
        self._maandhi_data_kundali = {}#; self._aayu_dhasa_type = -1; self._kaala_dhasa_type = -1
        horoscope_charts = [ ''  for _ in range(len(utils.RAASI_LIST))]
        cal_key_list = self.cal_key_list#self._get_calendar_resource_strings(language)
        jd = self.julian_day # V3.1.9 If Julian_Years to be used then years/months arguments should not be used
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        dob = drik.Date(self.Date.year,self.Date.month,self.Date.day)
        tob=self.birth_time
        global dhasavarga_dict
        dhasavarga_dict={1:cal_key_list['raasi_str'],
                         2:cal_key_list['hora_str'],
                         3:cal_key_list['drekkanam_str'],
                         4:cal_key_list['chaturthamsa_str'],
                         5:cal_key_list['panchamsa_str'],
                         6:cal_key_list['shashthamsa_str'],
                         7:cal_key_list['saptamsam_str'],
                         8:cal_key_list['ashtamsa_str'],
                         9:cal_key_list['navamsam_str'],
                         10:cal_key_list['dhasamsam_str'],
                         11:cal_key_list['rudramsa_str'],
                         12:cal_key_list['dhwadamsam_str'],
                         16:cal_key_list['shodamsa_str'],
                         20:cal_key_list['vimsamsa_str'],
                         24:cal_key_list['chaturvimsamsa_str'],
                         27:cal_key_list['nakshatramsa_str'],
                         30:cal_key_list['thrisamsam_str'],
                         40:cal_key_list['khavedamsa_str'],
                         45:cal_key_list['akshavedamsa_str'],
                         60:cal_key_list['sashtiamsam_str'],
                         81:cal_key_list['nava_navamsa_str'],
                         108:cal_key_list['ashtotharamsa_str'],
                         144:cal_key_list['dwadas_dwadasamsa_str'],
        }
        dhasavarga_factor_1 = const.division_chart_factors[chart_index_1]
        dhasavarga_factor_2 = const.division_chart_factors[chart_index_2]
        mixed_dvf = dhasavarga_factor_1*dhasavarga_factor_2
        planet_positions = charts.mixed_chart(jd, place,varga_factor_1=dhasavarga_factor_1,chart_method_1=chart_method_1,
                                              varga_factor_2=dhasavarga_factor_2,chart_method_2=chart_method_2)
        ascendant_navamsa = planet_positions[0][1]
        asc_house = ascendant_navamsa[0]
        horoscope_ascendant_house = asc_house
        jd = self.julian_day #V3.1.9
        horoscope_charts[asc_house] += cal_key_list['ascendant_str'] +"\n"
        self._get_sphuta_mixed_chart(dob, tob, place, dhasavarga_factor_1, chart_method_1, dhasavarga_factor_2, chart_method_2)
        abl = self._get_arudha_padhas_mixed_chart(dob, tob, place, dhasavarga_factor_1, chart_method_1, dhasavarga_factor_2, chart_method_2)
        #self._arudha_lagna_data_kundali = self._arudha_lagna_data[mixed_dvf].copy()
        for bli,_ in const._arudha_lagnas_included_in_chart.items():
            key = list(abl)[bli-1]
            value = abl[key]
            horoscope_info[key] = value
        jd = self.julian_years # V3.1.9 Special Lagna do not take years arguments - so use julian years
        key_dhasa_factor = 'D'+str(dhasavarga_factor_1)+'x'+'D'+str(dhasavarga_factor_2)
        key = key_dhasa_factor +'-'+cal_key_list['bhava_lagna_str']+' ('+cal_key_list['bhava_lagna_short_str']+')'
        value = drik.bhava_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._bhava_lagna_data_kundali[mixed_dvf] = value[0] # V3.1.9
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['hora_lagna_str']+' ('+cal_key_list['hora_lagna_short_str']+')'
        value = drik.hora_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._hora_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['ghati_lagna_str']+' ('+cal_key_list['ghati_lagna_short_str']+')'
        value = drik.ghati_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._ghati_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['vighati_lagna_str']+' ('+cal_key_list['vighati_lagna_short_str']+')'
        value = drik.vighati_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._vighati_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['pranapada_lagna_str']+' ('+cal_key_list['pranapada_lagna_short_str']+')'
        value = drik.pranapada_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._pranapada_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['indu_lagna_str']+' ('+cal_key_list['indu_lagna_short_str']+')'
        value = drik.indu_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._indu_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['bhrigu_bindhu_lagna_str']+' ('+cal_key_list['bhrigu_bindhu_lagna_short_str']+')'
        value = drik.bhrigu_bindhu_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._bhrigu_bindhu_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor+'-'+cal_key_list['kunda_lagna_str']+' ('+cal_key_list['kunda_lagna_short_str']+')'
        value = drik.kunda_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._kunda_lagna_data_kundali[mixed_dvf] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['sree_lagna_str']+' ('+cal_key_list['sree_lagna_short_str']+')'
        jd = self.julian_day # V3.1.9 revert to julian after special lagna calculations
        value = drik.sree_lagna_mixed_chart(jd,place,dhasavarga_factor_1,chart_method_1,dhasavarga_factor_2,chart_method_2)
        self._sree_lagna_data_kundali[mixed_dvf] = value[0] # V3.1.9
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['varnada_lagna_str']+' ('+cal_key_list['varnada_lagna_short_str']+')'
        value = charts.varnada_lagna_mixed_chart(dob, tob, place, house_index=1, 
                                                 varga_factor_1=dhasavarga_factor_1, chart_method_1=chart_method_1, 
                                                 varga_factor_2=dhasavarga_factor_2, chart_method_2=chart_method_2)
        self._varnada_lagna_data_kundali[mixed_dvf]=value[0]            
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = key_dhasa_factor +'-'+cal_key_list['maandi_str']+' ('+cal_key_list['maandi_short_str']+')'
        value = drik.maandi_longitude(dob,tob,place,divisional_chart_factor=mixed_dvf)
        self._maandhi_data_kundali[mixed_dvf]=value[0]            
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        horoscope_info[key_dhasa_factor +'-'+cal_key_list['ascendant_str']] = \
            utils.RAASI_LIST[ascendant_navamsa[0]]+' '+utils.to_dms(ascendant_navamsa[1],True,'plong')
        chara_karaka_names = [x+'_str' for x in house.chara_karaka_names]
        chara_karaka_dict = house.chara_karakas(planet_positions)
        retrograde_planets = drik.planets_in_retrograde(jd, place)
        for p,(h,long) in planet_positions[1:]:
            ret_str = ''
            if p in retrograde_planets:
                ret_str = const._retrogade_symbol
            planet_name = utils.PLANET_NAMES[p]+ret_str
            #print('dhasavarga_factor',dhasavarga_factor,'planet_name',planet_name)
            k = key_dhasa_factor+'-'+planet_name
            planet_house = h
            ck_str = ''
            if p !='L' and p < 8:
                ck_index = chara_karaka_dict.index(p)
                ck_str = ' (' + cal_key_list[chara_karaka_names[ck_index]] +')' # Fixed V3.7.2
            v = utils.RAASI_LIST[h]+' ' +utils.to_dms(long,is_lat_long='plong') + ck_str
            horoscope_charts[planet_house] += planet_name +'\n'
            horoscope_info[k]= v
        sub_planet_list = {'Kl':'kaala_str','Mr':'mrityu_str','Ap':'artha_praharaka_str','Yg':'yama_str',
                           'Gk':'gulika_str','Md':'maandi_str','Dm':'dhuma_str','Vp':'vyatipaata_str',
                           'Pv':'parivesha_str','Ic':'indrachaapa_str','Uk':'upaketu_str'}
        spl = charts.special_planet_longitudes_mixed_chart(dob, tob, place, varga_factor_1=dhasavarga_factor_1, 
                                        chart_method_1=chart_method_1, varga_factor_2=dhasavarga_factor_2,
                                        chart_method_2=chart_method_2)
        self._special_planet_chart = ['' for _ in range(12)]
        for sp,(h,long) in spl:
            k = key_dhasa_factor+'-'+cal_key_list[sub_planet_list[sp]]+' ('+cal_key_list[sub_planet_list[sp].replace('_str','_short_str')]+')'
            horoscope_info[k] = utils.RAASI_LIST[h] +' '+utils.to_dms(long,is_lat_long='plong')
            self._special_planet_chart[h] += cal_key_list[sub_planet_list[sp].replace('_str','_short_str')]+'\n'
        for h in range(12):
            vl = charts.varnada_lagna_mixed_chart(dob, tob, place, house_index=h+1,
                        varga_factor_1=dhasavarga_factor_1,chart_method_1=chart_method_1,
                        varga_factor_2=dhasavarga_factor_2,chart_method_2=chart_method_2,varnada_method=varnada_method)
            k = key_dhasa_factor+'-'+cal_key_list['varnada_lagna_str']+' (V'+str(h+1)+')'
            horoscope_info[k] = utils.RAASI_LIST[vl[0]] +' '+utils.to_dms(vl[1],is_lat_long='plong') 
        spl_list = ['tri','chatur','pancha','prana','deha','mrityu','sookshma_tri','beeja','kshetra','tithi','yoga',
                    'yogi','avayogi','rahu_tithi']
        for spl in spl_list:
            from jhora.horoscope.chart import sphuta
            vl = vl = eval('sphuta.'+spl+'_sphuta_mixed_chart(dob,tob,place, varga_factor_1=dhasavarga_factor_1, chart_method_1=chart_method_1, varga_factor_2=dhasavarga_factor_2, chart_method_2=chart_method_2)')
            k = key_dhasa_factor+'-'+cal_key_list[spl+'_sphuta_str']+' '+cal_key_list['sphuta_str']
            horoscope_info[k] = utils.RAASI_LIST[vl[0]] +' '+utils.to_dms(vl[1],is_lat_long='plong') 
        return horoscope_info, horoscope_charts,horoscope_ascendant_house
    def get_horoscope_information(self):#,language='en'):
        horoscope_info = {}
        self._vimsottari_balance = ();self._yoga_vimsottari_balance = ()
        self._arudha_lagna_data = {}
        self._sphuta_data = {}
        self._graha_lagna_data = {}
        self._hora_lagna_data = {}; self._ghati_lagna_data = {}; self._vighati_lagna_data = {}
        self._pranapada_lagna_data = {}; self._indu_lagna_data = {}; self._bhrigu_bindhu_lagna_data = {}
        self._bhava_lagna_data = {}; self._sree_lagna_data = {}; self._kunda_lagna_data = {}
        self._varnada_lagna_data = {}
        self._maandhi_data = {}; self._aayu_dhasa_type = -1; self._kaala_dhasa_type = -1
        cal_key_list = self.cal_key_list#self._get_calendar_resource_strings(language)
        global dhasavarga_dict
        dhasavarga_dict={2:cal_key_list['hora_str'],
                         3:cal_key_list['drekkanam_str'],
                         4:cal_key_list['chaturthamsa_str'],
                         5:cal_key_list['panchamsa_str'],
                         6:cal_key_list['shashthamsa_str'],
                         7:cal_key_list['saptamsam_str'],
                         8:cal_key_list['ashtamsa_str'],
                         9:cal_key_list['navamsam_str'],
                         10:cal_key_list['dhasamsam_str'],
                         11:cal_key_list['rudramsa_str'],
                         12:cal_key_list['dhwadamsam_str'],
                         16:cal_key_list['shodamsa_str'],
                         20:cal_key_list['vimsamsa_str'],
                         24:cal_key_list['chaturvimsamsa_str'],
                         27:cal_key_list['nakshatramsa_str'],
                         30:cal_key_list['thrisamsam_str'],
                         40:cal_key_list['khavedamsa_str'],
                         45:cal_key_list['akshavedamsa_str'],
                         60:cal_key_list['sashtiamsam_str'],
                         81:cal_key_list['nava_navamsa_str'],
                         108:cal_key_list['ashtotharamsa_str'],
                         144:cal_key_list['dwadas_dwadasamsa_str'],
        }
        jd = self.julian_day # V3.1.9 If Julian_Years to be used then years/months arguments should not be used
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        dob = drik.Date(self.Date.year,self.Date.month,self.Date.day)
        tob=self.birth_time
        tob_in_hrs = tob[0]+tob[1]/60.0+tob[2]/3600.0
        """ TODO: 
            Planet Positions return type should match for both Drik and SS
            SS does not have Lagna/Ascendant in planet positions - should be included
            retrograde depends on return types of planet positions
        """
        if self.calculation_type=='ss':
            planet_positions = surya_sidhantha.planet_positions(jd, place)
        else:
            planet_positions = charts.rasi_chart(jd, place, years=self.years,months=self.months,
                                                 sixty_hours=self.sixty_hours,pravesha_type=self.pravesha_type)
        #retrograde_planets = charts.planets_in_retrograde(planet_positions)
        retrograde_planets = drik.planets_in_retrograde(jd, place)
        #print('rasi retrograde planets',retrograde_planets)
        _ascendant = planet_positions[0][1] #drik.ascendant(jd,place)
        horoscope_charts = [[ ''  for _ in range(len(utils.RAASI_LIST))] for _ in range(len(dhasavarga_dict)+1)]
        horoscope_ascendant_houses = [-1 for _ in range(len(const.division_chart_factors))]
        chart_counter = 0
        divisional_chart_factor=1
        jd = self.julian_day#jd = self.julian_years #
        #"""
        self._get_sphuta(dob, tob, place, divisional_chart_factor)
        abl = self._get_arudha_padhas(dob, tob, place, divisional_chart_factor=divisional_chart_factor,
                                      years=self.years,months=self.months,sixty_hours=self.sixty_hours,
                                                 pravesha_type=self.pravesha_type)
        #print('_get_arudha_padhas returned',abl)
        for bli,blk in const._arudha_lagnas_included_in_chart.items():
            key = list(abl)[bli-1]
            #print('arudha padha key',key,'value',abl[key])
            value = abl[key]
            horoscope_info[key] = value
        #"""
        jd = self.julian_years # V3.1.9 Special Lagna do not take years arguments - so use julian years
        key = cal_key_list['raasi_str']+'-'+cal_key_list['bhava_lagna_str']+' ('+cal_key_list['bhava_lagna_short_str']+')'
        value = drik.bhava_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._bhava_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['hora_lagna_str']+' ('+cal_key_list['hora_lagna_short_str']+')'
        value = drik.hora_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._hora_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['ghati_lagna_str']+' ('+cal_key_list['ghati_lagna_short_str']+')'
        value = drik.ghati_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._ghati_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['vighati_lagna_str']+' ('+cal_key_list['vighati_lagna_short_str']+')'
        value = drik.vighati_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._vighati_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['pranapada_lagna_str']+' ('+cal_key_list['pranapada_lagna_short_str']+')'
        value = drik.pranapada_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._pranapada_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['indu_lagna_str']+' ('+cal_key_list['indu_lagna_short_str']+')'
        value = drik.indu_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        #print('indu lagna',value)
        self._indu_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['bhrigu_bindhu_lagna_str']+' ('+cal_key_list['bhrigu_bindhu_lagna_short_str']+')'
        value = drik.bhrigu_bindhu_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._bhrigu_bindhu_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str']+'-'+cal_key_list['kunda_lagna_str']+' ('+cal_key_list['kunda_lagna_short_str']+')'
        value = drik.kunda_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._kunda_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str'] +'-'+cal_key_list['sree_lagna_str']+' ('+cal_key_list['sree_lagna_short_str']+')'
        value = drik.sree_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
        self._sree_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str'] +'-'+cal_key_list['varnada_lagna_str']+' ('+cal_key_list['varnada_lagna_short_str']+')'
        value = charts.varnada_lagna(dob, tob, place,divisional_chart_factor=divisional_chart_factor)
        self._varnada_lagna_data[divisional_chart_factor] = value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        key = cal_key_list['raasi_str'] +'-'+cal_key_list['maandi_str']+' ('+cal_key_list['maandi_short_str']+')'
        value = drik.maandi_longitude(dob,tob,place,divisional_chart_factor=divisional_chart_factor)
        self._maandhi_data[divisional_chart_factor]=value[0]
        horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
        jd = self.julian_day # V3.1.9 revert to julian after special lagna calculations
        asc_house = _ascendant[0]
        horoscope_ascendant_houses[chart_counter] = asc_house
        horoscope_charts[chart_counter][asc_house] += cal_key_list['ascendant_str'] +"\n"
        horoscope_info[cal_key_list['raasi_str']+'-'+cal_key_list['ascendant_str']] = utils.RAASI_LIST[asc_house] +' ' + utils.to_dms(_ascendant[1],is_lat_long='plong')
        chara_karaka_names = [x+'_str' for x in house.chara_karaka_names]
        chara_karaka_dict = house.chara_karakas(planet_positions)
        for p,(h,long) in planet_positions[1:]:
            ret_str = ''
            if p in retrograde_planets:
                ret_str = const._retrogade_symbol
            planet_name = utils.PLANET_NAMES[p]+ret_str
            k = cal_key_list['raasi_str']+'-'+planet_name
            ck_str = ''
            if p !='L' and p < 8:
                ck_index = chara_karaka_dict.index(p)
                ck_str = ' (' + cal_key_list[chara_karaka_names[ck_index]] +')'
            v = utils.RAASI_LIST[h]+' '+ utils.to_dms(long,is_lat_long='plong') + ck_str
            planet_house = h
            horoscope_charts[chart_counter][planet_house] += planet_name + "\n"
            relative_planet_house = house.get_relative_house_of_planet(asc_house, planet_house)
            horoscope_info[k]=v # + str(relative_planet_house)
        # Shadow Sub Planet information
        #k = cal_key_list['raasi_str']+'-'+cal_key_list['upagraha_str']
        #horoscope_info[k]=''
        sub_planet_list_1 = {'kaala_str':'kaala_longitude','mrityu_str':'mrityu_longitude','artha_praharaka_str':'artha_praharaka_longitude','yama_str':'yama_ghantaka_longitude',
                           'gulika_str':'gulika_longitude','maandi_str':'maandi_longitude'}
        sub_planet_list_2 = ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu']
        place = drik.Place(self.place_name,self.latitude,self.longitude,self.timezone_offset)
        sun_long = planet_positions[1][1][0]*30+planet_positions[1][1][1]
        for sp,sp_func in sub_planet_list_1.items():
            k = cal_key_list['raasi_str']+'-'+cal_key_list[sp]+' ('+cal_key_list[sp.replace('_str','_short_str')]+')'
            v = eval('drik.'+sp_func+'(dob,tob,place,divisional_chart_factor=divisional_chart_factor)')
            horoscope_info[k]= utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong')
        for sp in sub_planet_list_2:
            k = cal_key_list['raasi_str']+'-'+cal_key_list[sp+'_str']+' ('+cal_key_list[sp+'_short_str']+')'
            v = eval('drik.'+'solar_upagraha_longitudes(sun_long,sp,divisional_chart_factor=divisional_chart_factor)')
            horoscope_info[k]= utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong')
        ## Dhasavarga Charts
        jd = self.julian_day  #V3.1.9
        for dhasavarga_factor in dhasavarga_dict.keys():
            " planet_positions lost: [planet_id, planet_constellation, planet_longitude] " 
            chart_counter += 1
            planet_positions = charts.divisional_chart(jd, place, 
                                                       divisional_chart_factor=dhasavarga_factor,
                                                       years=self.years,months=self.months,sixty_hours=self.sixty_hours,
                                                       calculation_type=self.calculation_type,pravesha_type=self.pravesha_type)
            chara_karaka_dict = house.chara_karakas(planet_positions)
            ascendant_navamsa = planet_positions[0][1]
            asc_house = ascendant_navamsa[0]
            horoscope_ascendant_houses[chart_counter] = asc_house
            ascendant_longitude = ascendant_navamsa[1]
            jd = self.julian_day #V3.1.9
            horoscope_charts[chart_counter][asc_house] += cal_key_list['ascendant_str'] +"\n"
            self._get_sphuta(dob, tob, place, divisional_chart_factor=dhasavarga_factor)
            abl = self._get_arudha_padhas(dob, tob, place, divisional_chart_factor=dhasavarga_factor,
                                      years=self.years,months=self.months,sixty_hours=self.sixty_hours,
                                      pravesha_type=self.pravesha_type)
            for bli,blk in const._arudha_lagnas_included_in_chart.items():
                key = list(abl)[bli-1]
                #print('arudha padha key',key,'value',abl[key])
                value = abl[key]
                horoscope_info[key] = value
            jd = self.julian_years # V3.1.9 Special Lagna do not take years arguments - so use julian years
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['bhava_lagna_str']+' ('+cal_key_list['bhava_lagna_short_str']+')'
            value = drik.bhava_lagna(jd,place,divisional_chart_factor=dhasavarga_factor)
            self._bhava_lagna_data[dhasavarga_factor] = value[0] # V3.1.9
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['hora_lagna_str']+' ('+cal_key_list['hora_lagna_short_str']+')'
            value = drik.hora_lagna(jd,place,divisional_chart_factor=dhasavarga_factor)
            self._hora_lagna_data[dhasavarga_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['ghati_lagna_str']+' ('+cal_key_list['ghati_lagna_short_str']+')'
            value = drik.ghati_lagna(jd,place,divisional_chart_factor=dhasavarga_factor)
            self._ghati_lagna_data[dhasavarga_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['vighati_lagna_str']+' ('+cal_key_list['vighati_lagna_short_str']+')'
            value = drik.vighati_lagna(jd,place,divisional_chart_factor=dhasavarga_factor)
            self._vighati_lagna_data[dhasavarga_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list['pranapada_lagna_str']+' ('+cal_key_list['pranapada_lagna_short_str']+')'
            value = drik.pranapada_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
            self._pranapada_lagna_data[divisional_chart_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list['indu_lagna_str']+' ('+cal_key_list['indu_lagna_short_str']+')'
            value = drik.indu_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
            self._indu_lagna_data[divisional_chart_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list['bhrigu_bindhu_lagna_str']+' ('+cal_key_list['bhrigu_bindhu_lagna_short_str']+')'
            value = drik.bhrigu_bindhu_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
            self._bhrigu_bindhu_lagna_data[divisional_chart_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list['kunda_lagna_str']+' ('+cal_key_list['kunda_lagna_short_str']+')'
            value = drik.kunda_lagna(jd,place,divisional_chart_factor=divisional_chart_factor)
            self._kunda_lagna_data[divisional_chart_factor] = value[0]
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['sree_lagna_str']+' ('+cal_key_list['sree_lagna_short_str']+')'
            jd = self.julian_day # V3.1.9 revert to julian after special lagna calculations
            value = drik.sree_lagna(jd,place,divisional_chart_factor=dhasavarga_factor)
            self._sree_lagna_data[dhasavarga_factor] = value[0] # V3.1.9
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['varnada_lagna_str']
            value = charts.varnada_lagna(dob, tob, place,divisional_chart_factor=dhasavarga_factor)
            self._varnada_lagna_data[dhasavarga_factor]=value[0]            
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            key = dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['maandi_str']+' ('+cal_key_list['maandi_short_str']+')'
            value = drik.maandi_longitude(dob,tob,place,divisional_chart_factor=dhasavarga_factor)
            self._maandhi_data[dhasavarga_factor]=value[0]            
            horoscope_info[key] = utils.RAASI_LIST[value[0]] +' ' + utils.to_dms(value[1],is_lat_long='plong')
            horoscope_info[dhasavarga_dict[dhasavarga_factor] +'-'+cal_key_list['ascendant_str']] = \
                utils.RAASI_LIST[ascendant_navamsa[0]]+' '+utils.to_dms(ascendant_navamsa[1],True,'plong')
            for p,(h,long) in planet_positions[1:]:
                ret_str = ''
                if p in retrograde_planets:
                    ret_str = const._retrogade_symbol
                planet_name = utils.PLANET_NAMES[p]+ret_str
                #print('dhasavarga_factor',dhasavarga_factor,'planet_name',planet_name)
                k = dhasavarga_dict[dhasavarga_factor]+'-'+planet_name
                planet_house = h
                ck_str = ''
                if p !='L' and p < 8:
                    #print('D'+str(dhasavarga_factor),planet_name,chara_karaka_dict[p])
                    ck_str = ' (' + cal_key_list[chara_karaka_names[chara_karaka_dict[p]]] +')'
                v = utils.RAASI_LIST[h]+' ' +utils.to_dms(long,is_lat_long='plong') + ck_str
                horoscope_charts[chart_counter][planet_house] += planet_name +'\n'
                relative_planet_house = house.get_relative_house_of_planet(asc_house, planet_house)
                horoscope_info[k]= v #+ [relative_planet_house]
            sun_long = planet_positions[1][1][0]*30+planet_positions[1][1][1]
            for sp,sp_func in sub_planet_list_1.items():
                k = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list[sp]+' ('+cal_key_list[sp.replace('_str','_short_str')]+')'
                v = eval('drik.'+sp_func+'(dob,tob,place,divisional_chart_factor=dhasavarga_factor)')
                horoscope_info[k] = utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong') 
            for sp in sub_planet_list_2:
                k = dhasavarga_dict[dhasavarga_factor]+'-'+cal_key_list[sp+'_str']+' ('+cal_key_list[sp+'_short_str']+')'
                v = eval('drik.'+'solar_upagraha_longitudes(sun_long,sp,divisional_chart_factor=divisional_chart_factor)')
                horoscope_info[k] = utils.RAASI_LIST[v[0]] +' '+utils.to_dms(v[1],is_lat_long='plong')
        return horoscope_info, horoscope_charts,horoscope_ascendant_houses#, vimsottari_dhasa_bhukti_info,ashtottari_dhasa_bhukti_info,narayana_dhasa_info
    def get_varnada_lagna_for_chart(self,dob, tob, place, divisional_chart_factor=1, chart_method=None,
                                    varnada_method=None, base_rasi=None, count_from_end_of_sign=None):
        _vl_chart = ['' for _ in range(12)]
        for h in range(12):
            vl = charts.varnada_lagna(dob, tob, place, divisional_chart_factor=divisional_chart_factor,
                        chart_method=chart_method,house_index=h+1,
                        varnada_method=varnada_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
            _vl_chart[vl[0]] += 'V'+str(h+1)+'\n'
        _varnada_chart_dict = {self.cal_key_list['varnada_lagna_str']:_vl_chart}
        return _varnada_chart_dict
    def get_varnada_lagna_for_mixed_chart(self,dob, tob, place,varga_factor_1=None, chart_method_1=None,
                                          varga_factor_2=None, chart_method_2=None,
                            varnada_method=None):
        _vl_chart = ['' for _ in range(12)]
        for h in range(12):
            vl = charts.varnada_lagna_mixed_chart(dob, tob, place, house_index=h+1,
                        varga_factor_1=varga_factor_1, chart_method_1=chart_method_1,
                        varga_factor_2=varga_factor_2, chart_method_2=chart_method_2, varnada_method=varnada_method)
            _vl_chart[vl[0]] += 'V'+str(h+1)+'\n'
        _varnada_chart_dict = {self.cal_key_list['varnada_lagna_str']:_vl_chart}
        return _varnada_chart_dict
    def _get_shad_bala(self,dob,tob,place):
        from jhora.horoscope.chart import strength
        jd = utils.julian_day_number(dob, tob)
        return strength.shad_bala(jd, place)
    def _get_bhava_bala(self,dob,tob,place):
        from jhora.horoscope.chart import strength
        jd = utils.julian_day_number(dob, tob)
        bb = strength.bhava_bala(jd, place)
        #print('main bhava bala info',bb)
        import numpy as np
        bb = list(np.array(bb).T)
        #print('main bhava bala info',bb)
        return bb
    def _get_other_bala(self,dob,tob,place):
        #from jhora.horoscope.transit import tajaka
        from jhora.horoscope.chart import strength
        jd = utils.julian_day_number(dob, tob)
        hb = strength.harsha_bala(dob, tob, place)
        hb1 = {utils.PLANET_NAMES[p]:hb[p] for p in const.SUN_TO_SATURN}
        pvb = strength.pancha_vargeeya_bala(jd, place)
        pvb1 = {utils.PLANET_NAMES[p]:pvb[p] for p in const.SUN_TO_SATURN}
        dvb = strength.dwadhasa_vargeeya_bala(jd, place)
        dvb1 = {utils.PLANET_NAMES[p]:dvb[p] for p in const.SUN_TO_SATURN}
        return [hb1, pvb1, dvb1]
    def _get_vimsopaka_bala(self,dob,tob,place_as_tuple):
        jd_at_dob = utils.julian_day_number(dob, tob)
        sv = charts.vimsopaka_shadvarga_of_planets(jd_at_dob, place_as_tuple)
        sv1 = {}
        for p in range(9):
            sv1[utils.PLANET_NAMES[p]]=utils.SHADVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vimsopaka_sapthavarga_of_planets(jd_at_dob, place_as_tuple)
        sv2 = {}
        for p in range(9):
            sv2[utils.PLANET_NAMES[p]]=utils.SAPTAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vimsopaka_dhasavarga_of_planets(jd_at_dob, place_as_tuple)
        dv = {}
        for p in range(9):
            dv[utils.PLANET_NAMES[p]]=utils.DHASAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vimsopaka_shodhasavarga_of_planets(jd_at_dob, place_as_tuple)
        sv3 = {}
        for p in range(9):
            sv3[utils.PLANET_NAMES[p]]=utils.SHODASAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        return [sv1,sv2,dv,sv3]
    def _get_vaiseshikamsa_bala(self,dob,tob,place_as_tuple):
        jd_at_dob = utils.julian_day_number(dob, tob)
        sv = charts.vaiseshikamsa_shadvarga_of_planets(jd_at_dob, place_as_tuple)
        sv1 = {}
        for p in range(9):
            sv1[utils.PLANET_NAMES[p]]=utils.SHADVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vaiseshikamsa_sapthavarga_of_planets(jd_at_dob, place_as_tuple)
        sv2 = {}
        for p in range(9):
            sv2[utils.PLANET_NAMES[p]]=utils.SAPTAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vaiseshikamsa_dhasavarga_of_planets(jd_at_dob, place_as_tuple)
        dv = {}
        for p in range(9):
            dv[utils.PLANET_NAMES[p]]=utils.DHASAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        sv = charts.vaiseshikamsa_shodhasavarga_of_planets(jd_at_dob, place_as_tuple)
        sv3 = {}
        for p in range(9):
            sv3[utils.PLANET_NAMES[p]]=utils.SHODASAVARGAMSA_NAMES[sv[p][0]]+'\n('+sv[p][1]+ ')\n'+str(round(sv[p][2],1))
        return [sv1,sv2,dv,sv3]
    def _get_sphuta_mixed_chart(self,dob,tob,place,varga_factor_1=1,chart_method_1=1,varga_factor_2=1,chart_method_2=1):
        from jhora.horoscope.chart import sphuta
        _sphuta_dict = {}
        for s in const.sphuta_list:
            key = self.cal_key_list[s+'_sphuta_str']+' '+self.cal_key_list['sphuta_str']+' ('+self.cal_key_list[s+'_sphuta_short_str']+')'
            fn = 'sphuta.'+s+'_sphuta_mixed_chart(dob,tob,place,varga_factor_1=varga_factor_1,chart_method_1=chart_method_1,varga_factor_2=varga_factor_2,chart_method_2=chart_method_2)'
            value = eval(fn)
            _sphuta_dict[key] = utils.RAASI_LIST[value[0]]+' '+utils.to_dms(value[1], is_lat_long='plong')
        #self._sphuta_data.update(_sphuta_dict)
        return _sphuta_dict
    def _get_sphuta(self,dob,tob,place,divisional_chart_factor=1,chart_method=1,
                                        base_rasi=None,count_from_end_of_sign=None):
        from jhora.horoscope.chart import sphuta
        _sphuta_dict = {}
        for s in const.sphuta_list:
            key = self.cal_key_list[s+'_sphuta_str']+' '+self.cal_key_list['sphuta_str']+' ('+self.cal_key_list[s+'_sphuta_short_str']+')'
            fn = 'sphuta.'+s+'_sphuta(dob,tob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)'
            value = eval(fn)
            _sphuta_dict[key] = utils.RAASI_LIST[value[0]]+' '+utils.to_dms(value[1], is_lat_long='plong')
        #self._sphuta_data.update(_sphuta_dict)
        return _sphuta_dict
    def _get_arudha_padhas_mixed_chart(self,dob,tob,place,varga_factor_1=1,chart_method_1=1,varga_factor_2=1,chart_method_2=1):
        from jhora.horoscope.chart import arudhas
        jd_at_dob = utils.julian_day_number(dob, tob)
        mixed_dvf = varga_factor_1*varga_factor_2
        planet_positions = charts.mixed_chart(jd_at_dob, place, varga_factor_1, chart_method_1, varga_factor_2, chart_method_2)
        self._arudha_menu_dict = self._get_arudha_padhas_menu_dict(planet_positions)
        asc_house = planet_positions[0][1][0]
        ba = arudhas.bhava_arudhas_from_planet_positions(planet_positions)
        #self._arudha_lagna_data[mixed_dvf] = ['' for _ in range(12)]
        for bk,bv in const._arudha_lagnas_included_in_chart.items():
            bai = int(bv.replace('bhava_arudha_a','').replace('_str',''))
            #self._arudha_lagna_data[mixed_dvf][ba[bai-1]] += '\n'+self.cal_key_list[bv.replace("_str","_short_str")]
        houses = [(h + asc_house) % 12 for h in range(12)]
        bhava_arudhas = {}
        for i, h in enumerate(houses):
            bhava_arudhas['D'+str(varga_factor_1)+'xD'+str(varga_factor_2) +'-'\
                          +self.cal_key_list['bhava_arudha_a'+str(i+1)+'_str'] \
                          +' ('+self.cal_key_list['bhava_arudha_a'+str(i+1)+'_short_str']+')']=utils.RAASI_LIST[ba[i]]
        ga = arudhas.graha_arudhas_from_planet_positions(planet_positions)
        #self._graha_lagna_data['D'+str(varga_factor_1)+'xD'+str(varga_factor_2)+'-'+self.cal_key_list['ascendant_str']]=utils.RAASI_LIST[ga[0]]    
        #for p in range(1,const._pp_count_upto_ketu):
        #    self._graha_lagna_data['D'+str(varga_factor_1)+'xD'+str(varga_factor_2)+'-'+utils.PLANET_NAMES[p-1]]=utils.RAASI_LIST[ga[p]]
        return bhava_arudhas
    def _get_arudha_padhas_menu_dict(self,planet_positions):
        from jhora.horoscope.chart import arudhas
        arudha_base_list = [self.cal_key_list['ascendant_short_str']]+ utils.PLANET_SHORT_NAMES[:const._planets_upto_ketu]
        arudha_menu_dict = {self.cal_key_list[r]:[] for r in const._bhava_arudha_list}
        for ab,(key,_) in enumerate(arudha_menu_dict.items()):
            ba = arudhas.bhava_arudhas_from_planet_positions(planet_positions,arudha_base=ab)
            ba_chart = ['' for _ in range(12)]
            astr = arudha_base_list[ab]
            for p,r in enumerate(ba):
                ba_chart[r] += self.cal_key_list['bhava_arudha_a'+str(p+1)+'_short_str']+'\n' if ab==0 else astr+str(p+1)+'\n'
            for b in range(len(ba_chart)):
                if ba_chart[b] != '' and ba_chart[b][-1]=='\n': ba_chart[b] = ba_chart[b][:-1]
            arudha_menu_dict[key] = ba_chart
        #arudha_menu_dict = {self.cal_key_list['arudhas_str']:arudha_menu_dict}
        return arudha_menu_dict
    def _get_arudha_padhas(self,dob,tob,place,divisional_chart_factor=1,chart_method=1,
                           years=1,months=1,sixty_hours=1,pravesha_type=0,
                           base_rasi=None,count_from_end_of_sign=None):
        from jhora.horoscope.chart import arudhas
        jd_at_dob = utils.julian_day_number(dob, tob)
        planet_positions = charts.divisional_chart(jd_at_dob, place, divisional_chart_factor=divisional_chart_factor,
                                                   chart_method=chart_method,years=years,months=months,
                                                   sixty_hours=sixty_hours,pravesha_type=pravesha_type,
                                            base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
        self._arudha_menu_dict = self._get_arudha_padhas_menu_dict(planet_positions)
        asc_house = planet_positions[0][1][0]
        ba = arudhas.bhava_arudhas_from_planet_positions(planet_positions)
        self._arudha_lagna_data_kundali = ['' for _ in range(12)]
        for bk,bv in const._arudha_lagnas_included_in_chart.items():
            bai = int(bv.replace('bhava_arudha_a','').replace('_str',''))
            self._arudha_lagna_data_kundali[ba[bai-1]] += '\n'+self.cal_key_list[bv.replace("_str","_short_str")]
        houses = [(h + asc_house) % 12 for h in range(12)]
        bhava_arudhas = {}
        for i, h in enumerate(houses):
            bhava_arudhas['D-'+str(divisional_chart_factor)+'-'+self.cal_key_list['bhava_arudha_a'+str(i+1)+'_str'] \
                          +' ('+self.cal_key_list['bhava_arudha_a'+str(i+1)+'_short_str']+')']=utils.RAASI_LIST[ba[i]]
        ga = arudhas.graha_arudhas_from_planet_positions(planet_positions)
        #self._graha_lagna_data['D'+str(divisional_chart_factor)+'-'+self.cal_key_list['ascendant_str']]=utils.RAASI_LIST[ga[0]]       
        #for p in range(1,const._pp_count_upto_ketu):
        #    self._graha_lagna_data['D'+str(divisional_chart_factor)+'-'+utils.PLANET_NAMES[p-1]]=utils.RAASI_LIST[ga[p]]
        return bhava_arudhas
    def _get_graha_dhasa_bhukthi(self,dob,tob,place):
        self._vimsottari_balance,_vimsottari_dhasa_bhkthi_info = self._get_vimsottari_dhasa_bhukthi(dob, tob, place)
        #print('horo _vimsottari_balance',self._vimsottari_balance)
        _ashtottari_dhasa_bhkthi_info = self._get_ashtottari_dhasa_bhukthi(dob, tob, place)
        _yogini_dhasa_bhkthi_info = self._get_yogini_dhasa_bhukthi(dob, tob, place)
        return _vimsottari_dhasa_bhkthi_info,_ashtottari_dhasa_bhkthi_info, _yogini_dhasa_bhkthi_info
    def _get_rasi_dhasa_bhukthi(self,dob,tob,place):
        _narayana_dhasa_bhukthi_info = self._get_narayana_dhasa(dob,tob,place)
        _kendraadhi_rasi_dhasa_bhukthi_info = self._get_kendraadhi_rasi_dhasa(dob,tob,place)
        _sudasa_dhasa_bhukthi_info = self._get_sudasa_dhasa(dob,tob,place)
        _drig_dhasa_bhukthi_info = self._get_drig_dhasa(dob,tob,place)
        _nirayana_dhasa_bhukthi_info = self._get_nirayana_dhasa(dob,tob,place)
        _shoola_dhasa_bhukthi_info = self._get_shoola_dhasa(dob,tob,place)
        _kendraadhi_karaka_dhasa_bhukthi_info = self._get_kendraadhi_karaka_dhasa(dob,tob,place)
        _chara_dhasa_bhukthi_info = self._get_chara_dhasa(dob,tob,place)
        _lagnamsaka_dhasa_bhukthi_info = self._get_lagnamsaka_dhasa(dob,tob,place)
        _padhanadhamsa_dhasa_bhukthi_info = self._get_padhanadhamsa_dhasa(dob, tob, place)
        _mandooka_dhasa_bhukthi_info = self._get_mandooka_dhasa(dob, tob, place)
        _sthira_dhasa_bhukthi_info = self._get_sthira_dhasa(dob, tob, place)
        _tara_lagna_dhasa_bhukthi_info = self._get_tara_lagna_dhasa(dob, tob, place)
        return [_narayana_dhasa_bhukthi_info, _kendraadhi_rasi_dhasa_bhukthi_info, _sudasa_dhasa_bhukthi_info, \
            _drig_dhasa_bhukthi_info, _nirayana_dhasa_bhukthi_info, _shoola_dhasa_bhukthi_info, \
            _kendraadhi_karaka_dhasa_bhukthi_info, _chara_dhasa_bhukthi_info, _lagnamsaka_dhasa_bhukthi_info, \
            _padhanadhamsa_dhasa_bhukthi_info]
    def _get_annual_dhasa_bhukthi(self,divisional_chart_factor=1):
        _patyayini_dhasa_bhukthi_info = self._get_patyatini_dhasa_bhukthi(divisional_chart_factor=divisional_chart_factor)
        _mudda_dhasa_bhukthi_info = self._get_varsha_vimsottari_dhasa(self.julian_day, self.Place, self.years-1,divisional_chart_factor=divisional_chart_factor)
        _varsha_narayana_dhasa_bhukthi_info = self._get_varsha_narayana_dhasa(self.Date, self.birth_time, self.Place, self.years,divisional_chart_factor=divisional_chart_factor)
        return [_patyayini_dhasa_bhukthi_info,_mudda_dhasa_bhukthi_info,_varsha_narayana_dhasa_bhukthi_info]
    def _get_varsha_narayana_dhasa(self,dob,tob,place,years,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import narayana
        db = narayana.varsha_narayana_dhasa_bhukthi(dob, tob, place, years, divisional_chart_factor=divisional_chart_factor,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA)
        #print('varsha narayana dhasa',db)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_varsha_vimsottari_dhasa(self,jd, place, years,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.annual import mudda
        md = mudda.varsha_vimsottari_dhasa_bhukthi(jd, place, years,divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = []
        for pd,pb,bs,_ in md:
            dhasa_lord = utils.PLANET_NAMES[pd]
            bhukthi_lord = utils.PLANET_NAMES[pb]
            dhasa_bhukti_info.append((dhasa_lord+'-'+bhukthi_lord,bs))
        return dhasa_bhukti_info
    def _get_patyatini_dhasa_bhukthi(self,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.annual import patyayini
        self.julian_years = drik.next_solar_date(self.julian_day, self.Place, self.years, self.months, self.sixty_hours)
        p_d_b = patyayini.patyayini_dhasa(self.julian_years, self.Place, divisional_chart_factor=divisional_chart_factor)
        #print('p_d_b',p_d_b)
        dhasa_bhukti_info = []
        for p,bhukthis,_ in p_d_b:
            #print('p,bhukthis',p,bhukthis)
            if p=='L':
                dhasa_lord = self._ascendant_str
            else:
                dhasa_lord = utils.PLANET_NAMES[p]
            for bk,bs in bhukthis:
                #print('bk,bs',bk,bs)
                if bk=='L':
                    bhukthi_lord = self._ascendant_str
                else:
                    bhukthi_lord = utils.PLANET_NAMES[bk]
                dhasa_bhukti_info.append((dhasa_lord+'-'+bhukthi_lord,bs))
                #print('key',dhasa_lord+'-'+bhukthi_lord,'value',bs)
        return dhasa_bhukti_info
    def _get_tara_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import tara
        db = tara.get_dhasa_bhukthi(dob, tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.DHASA_LIST[dhasa_lord]+'-'+utils.BHUKTHI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_karaka_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        jd = utils.julian_day_number(dob, tob)
        from jhora.horoscope.dhasa.graha import karaka
        planet_positions = charts.rasi_chart(jd, place)
        db = karaka.get_dhasa_antardhasa(dob, tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,
                                         show_karaka_as_pair=1,**kwargs)
        chara_karaka_names = [x+'_str' for x in house.chara_karaka_names]
        chara_karaka_dict = house.chara_karakas(planet_positions)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [(dhasa_karaka,dhasa_lord), (bukthi_karaka,bukthi_lord),bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'\n'+self.cal_key_list[chara_karaka_names[dhasa_karaka]]+'\n'
                                      +'-'+utils.PLANET_NAMES[bukthi_lord]+'\n'+self.cal_key_list[chara_karaka_names[bukthi_karaka]]+'\n',bukthi_start))
        return dhasa_bhukti_info
    def _get_naisargika_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import naisargika
        db = naisargika.get_dhasa_bhukthi(dob, tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_str=self.cal_key_list['ascendant_str'] if dhasa_lord == const._ascendant_symbol else utils.PLANET_NAMES[dhasa_lord]
            bukthi_str=self.cal_key_list['ascendant_str'] if bukthi_lord == const._ascendant_symbol else utils.PLANET_NAMES[bukthi_lord]
            dhasa_bhukti_info.append((dhasa_str+'-'+bukthi_str,bukthi_start))
        return dhasa_bhukti_info
    def _get_aayu_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        jd = utils.julian_day_number(dob, tob)
        from jhora.horoscope.dhasa.graha import aayu
        self._aayu_dhasa_type,db = aayu.get_dhasa_antardhasa(jd, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_str=self._ascendant_str if dhasa_lord==const._ascendant_symbol else utils.PLANET_NAMES[dhasa_lord]
            bukthi_str=self._ascendant_str if bukthi_lord==const._ascendant_symbol else utils.PLANET_NAMES[bukthi_lord]                
            dhasa_bhukti_info.append((dhasa_str+'-'+bukthi_str,bukthi_start))
        return dhasa_bhukti_info
    def _get_vimsottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):#,divisional_chart_factor=1):
        jd = utils.julian_day_number(dob, tob)
        from jhora.horoscope.dhasa.graha import vimsottari
        self._vimsottari_balance,db = vimsottari.get_dhasa_bhukthi(jd, place,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start]=db[i]
            #dhasa_bhukti_info[utils.DHASA_LIST[dhasa_lord]+'-'+utils.BHUKTHI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_kaala_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import kaala
        self._kaala_dhasa_type,db = kaala.get_dhasa_antardhasa(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_chakra_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import chakra
        db = chakra.get_dhasa_antardhasa(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_sandhya_panchaka_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import sandhya
        db = sandhya.get_dhasa_antardhasa(dob,tob, place,use_panchaka_variation=True,divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_rasi_bhukthi_vimsottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        jd = utils.julian_day_number(dob, tob)
        from jhora.horoscope.dhasa.graha import vimsottari
        _,db = vimsottari.get_dhasa_bhukthi(jd, place,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_yoga_vimsottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        jd = utils.julian_day_number(dob, tob)
        from jhora.horoscope.dhasa.graha import yoga_vimsottari
        self._yoga_vimsottari_balance,db = yoga_vimsottari.get_dhasa_bhukthi(jd, place,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start]=db[i]
            #dhasa_bhukti_info[utils.DHASA_LIST[dhasa_lord]+'-'+utils.BHUKTHI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_ashtottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import ashtottari
        jd = utils.julian_day_number(dob,tob)
        db = ashtottari.get_dhasa_bhukthi(jd, place,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_tithi_ashtottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import tithi_ashtottari
        jd = utils.julian_day_number(dob,tob)
        db = tithi_ashtottari.get_ashtottari_dhasa_bhukthi(jd, place,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start]=db[i]
            #dhasa_bhukti_info[utils.DHASA_LIST[dhasa_lord]+'-'+utils.BHUKTHI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        #print(dhasa_bhukti_info)
        return dhasa_bhukti_info
    def _get_buddhi_gathi_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import buddhi_gathi
        jd = utils.julian_day_number(dob,tob)
        db = buddhi_gathi.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_yogini_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import yogini
        db = yogini.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_tithi_yogini_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import tithi_yogini
        db = tithi_yogini.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_shodasottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import shodasottari
        db = shodasottari.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_dwadasottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import dwadasottari
        db = dwadasottari.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_dwisatpathi_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import dwisatpathi
        db = dwisatpathi.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_panchottari_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import panchottari
        db = panchottari.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_satabdika_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import sataatbika
        db = sataatbika.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_chaturaaseeti_sama_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import chathuraaseethi_sama
        db = chathuraaseethi_sama.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_karana_chaturaaseeti_sama_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import karana_chathuraaseethi_sama
        db = karana_chathuraaseethi_sama.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_shashtisama_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import shastihayani
        db = shastihayani.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_shattrimsa_sama_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import shattrimsa_sama
        db = shattrimsa_sama.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.PLANET_NAMES[dhasa_lord]+'-'+utils.PLANET_NAMES[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_saptharishi_nakshathra_dhasa_bhukthi(self,dob,tob,place,**kwargs):
        from jhora.horoscope.dhasa.graha import saptharishi_nakshathra
        db = saptharishi_nakshathra.get_dhasa_bhukthi(dob,tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA,**kwargs)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            if not db[i]:
                continue
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.NAKSHATRA_LIST[dhasa_lord]+'-'+utils.NAKSHATRA_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_narayana_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import narayana
        db = narayana.narayana_dhasa_for_rasi_chart(dob, tob, place,dhasa_level_index=const.MAHA_DHASA_DEPTH.ANTARA)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_kendraadhi_rasi_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import kendradhi_rasi
        db = kendradhi_rasi.kendradhi_rasi_dhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_sudasa_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import sudasa
        db = sudasa.sudasa_dhasa_bhukthi(dob, tob, place, divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_drig_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import drig
        db = drig.drig_dhasa_bhukthi(dob, tob, place, divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_nirayana_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import nirayana
        db = nirayana.nirayana_shoola_dhasa_bhukthi(dob, tob, place, divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_shoola_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import shoola
        db = shoola.shoola_dhasa_bhukthi(dob, tob, place, divisional_chart_factor)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_kendraadhi_karaka_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import kendradhi_rasi
        db = kendradhi_rasi.karaka_kendradhi_rasi_dhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor, karaka_index=1)
        dhasa_bhukti_info = []
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_chara_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import chara
        db = chara.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor, chara_method=1)
        #print('chara dasa',db)
        dhasa_bhukti_info = []
        for _dhasa,_bhukthi,dhasa_start,_ in db:
            dhasa_lord = utils.RAASI_LIST[_dhasa]
            bukthi_lord = utils.RAASI_LIST[_bhukthi]
            #dhasa_start = '%04d-%02d-%02d' %(y,m,d) +' '+utils.to_dms(fh, as_string=True)
            dhasa_bhukti_info.append((dhasa_lord+'-'+bukthi_lord,dhasa_start))
        return dhasa_bhukti_info
    def _get_lagnamsaka_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import lagnamsaka
        db = lagnamsaka.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_padhanadhamsa_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import padhanadhamsa
        db = padhanadhamsa.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_mandooka_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import mandooka
        db = mandooka.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_sthira_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import sthira
        db = sthira.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_tara_lagna_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import tara_lagna
        db = tara_lagna.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_brahma_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import brahma
        db = brahma.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_varnada_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import varnada
        db = varnada.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_yogardha_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import yogardha
        db = yogardha.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_navamsa_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import navamsa
        db = navamsa.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            #dhasa_bhukti_info[utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord]]=bukthi_start
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_paryaaya_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import paryaaya
        dhasa_type, db = paryaaya.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        #print('paryaaya dhasa',db)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
            #dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_trikona_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import trikona
        db = trikona.get_dhasa_antardhasa(dob, tob, place, divisional_chart_factor=divisional_chart_factor)
        #print('trikona dhasa',db)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
            #dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def _get_kalachakra_dhasa(self,dob,tob,place,divisional_chart_factor=1):
        from jhora.horoscope.dhasa.raasi import kalachakra
        jd_at_dob = utils.julian_day_number(dob, tob)
        pp = charts.divisional_chart(jd_at_dob, place, divisional_chart_factor=divisional_chart_factor)
        moon_long = pp[2][1][0]*30+pp[2][1][1]
        db = kalachakra.kalachakra_dhasa(moon_long, jd_at_dob)
        dhasa_bhukti_info = [] #{}
        for i in range(len(db)):
            [dhasa_lord, bukthi_lord,bukthi_start,_]=db[i]
            dhasa_bhukti_info.append((utils.RAASI_LIST[dhasa_lord]+'-'+utils.RAASI_LIST[bukthi_lord],bukthi_start))
        return dhasa_bhukti_info
    def get_chara_karakas_for_chart(self,jd_at_dob, place, divisional_chart_factor=1, chart_method=None,base_rasi=None,
                                    count_from_end_of_sign=None):
        _vl_chart = ['' for _ in range(12)]
        planet_positions = charts.divisional_chart(jd_at_dob, place,divisional_chart_factor=divisional_chart_factor,
                            chart_method=chart_method,base_rasi=base_rasi, count_from_end_of_sign=count_from_end_of_sign)
        _karakas = get_chara_karakas(jd_at_dob, place)
        for ki,k in enumerate(_karakas):
            h = planet_positions[k+1][1][0]
            _vl_chart[h] = self.cal_key_list[const.chara_karaka_names[ki]+'_short_str']+'\n'+_vl_chart[h]
        _karaka_chart_dict = {self.cal_key_list['karakas_str']:_vl_chart}
        return _karaka_chart_dict
    def get_chara_karakas_for_mixed_chart(self,jd_at_dob, place,varga_factor_1=None, chart_method_1=None,
                                          varga_factor_2=None, chart_method_2=None):
        _vl_chart = ['' for _ in range(12)]
        planet_positions = charts.mixed_chart(jd_at_dob, place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1,
                                varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)
        _karakas = get_chara_karakas(jd_at_dob, place)
        for ki,k in enumerate(_karakas):
            h = planet_positions[k+1][1][0]
            _vl_chart[h] = self.cal_key_list[const.chara_karaka_names[ki]+'_short_str']+'\n'+_vl_chart[h]
        _karaka_chart_dict = {self.cal_key_list['karakas_str']:_vl_chart}
        return _karaka_chart_dict
    def get_special_lagnas_for_chart(self,jd_at_dob, place, divisional_chart_factor=1, chart_method=None,base_rasi=None,
                                    count_from_end_of_sign=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        spl_list = ['hora_lagna','bhava_lagna','ghati_lagna','vighati_lagna','sree_lagna',
                   'pranapada_lagna','indu_lagna','bhrigu_bindhu_lagna','kunda_lagna','varnada_lagna',]
        _vl_chart = ['' for _ in range(12)]
        for spl in spl_list:
            if spl == 'varnada_lagna':
                vl = eval('charts.'+spl+'(dob,tob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)')
            else:
                vl = eval('drik.'+spl+'(jd_at_dob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)')
            _vl_chart[vl[0]] += self.cal_key_list[spl+'_short_str'] +'\n'
        _special_lagna_dict = {self.cal_key_list['special_lagnas_str']:_vl_chart}
        return _special_lagna_dict 
    def get_special_lagnas_for_mixed_chart(self,jd_at_dob, place,varga_factor_1=None, chart_method_1=None,
                                          varga_factor_2=None, chart_method_2=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        spl_list = ['hora_lagna','bhava_lagna','ghati_lagna','vighati_lagna','sree_lagna',
                   'pranapada_lagna','indu_lagna','bhrigu_bindhu_lagna','kunda_lagna','varnada_lagna',]
        _vl_chart = ['' for _ in range(12)]
        for spl in spl_list:
            if spl == 'varnada_lagna':
                vl = eval('charts.'+spl+'_mixed_chart(dob,tob, place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1, varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)')
            else:
                vl = eval('drik.'+spl+'_mixed_chart(jd_at_dob, place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1, varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)')
            _vl_chart[vl[0]] += self.cal_key_list[spl+'_short_str'] +'\n'
        _special_lagna_dict = {self.cal_key_list['special_lagnas_str']:_vl_chart}
        return _special_lagna_dict
    def get_sphutas_for_chart(self,jd_at_dob, place, divisional_chart_factor=1, chart_method=None,base_rasi=None,
                                    count_from_end_of_sign=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        spl_list = ['tri','chatur','pancha','prana','deha','mrityu','sookshma_tri','beeja','kshetra','tithi','yoga',
                    'yogi','avayogi','rahu_tithi']
        _vl_chart = ['' for _ in range(12)]
        for spl in spl_list:
            from jhora.horoscope.chart import sphuta
            vl = eval('sphuta.'+spl+'_sphuta(dob,tob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)')
            _vl_chart[vl[0]] += self.cal_key_list[spl+'_sphuta_short_str'] +'\n'
        _sphuta_menu_dict = {self.cal_key_list['sphuta_str']:_vl_chart}
        return _sphuta_menu_dict
    def get_sphutas_for_mixed_chart(self,jd_at_dob, place,varga_factor_1=None, chart_method_1=None,
                                          varga_factor_2=None, chart_method_2=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        spl_list = ['tri','chatur','pancha','prana','deha','mrityu','sookshma_tri','beeja','kshetra','tithi','yoga',
                    'yogi','avayogi','rahu_tithi']
        _vl_chart = ['' for _ in range(12)]
        for spl in spl_list:
            from jhora.horoscope.chart import sphuta
            vl = eval('sphuta.'+spl+'_sphuta_mixed_chart(dob,tob,place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1, varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)')
            _vl_chart[vl[0]] += self.cal_key_list[spl+'_sphuta_short_str'] +'\n'
        _sphuta_menu_dict = {self.cal_key_list['sphuta_str']:_vl_chart}
        return _sphuta_menu_dict
    def get_ava_saha_yoga_info_for_chart(self,jd_at_dob, place, divisional_chart_factor=1, chart_method=None,base_rasi=None,
                                    count_from_end_of_sign=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        line_sep = '<br>'
        from jhora.horoscope.chart import sphuta
        yh,yl = sphuta.yogi_sphuta(dob,tob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
        ystr = self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['raasi_str']+':'+\
                utils.RAASI_LIST[yh]+' '+self.cal_key_list['longitude_str']+':'+utils.to_dms(yl,is_lat_long='plong')
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['nakshatra_str']+':'+ \
                utils.NAKSHATRA_LIST[ynak[0]-1]
        yogi_planet = [l for l,naks in const.nakshathra_lords.items() if ynak[0]-1 in naks][0]
        ystr += line_sep+self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[yogi_planet]
        sahayogi_planet = const._house_owners_list[yh]
        ystr += line_sep+self.cal_key_list['sahayogi_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[sahayogi_planet]
        yh,yl = sphuta.avayogi_sphuta(dob,tob,place,divisional_chart_factor=divisional_chart_factor,chart_method=chart_method,base_rasi=base_rasi,count_from_end_of_sign=count_from_end_of_sign)
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['raasi_str']+':'+\
                utils.RAASI_LIST[yh]+' '+self.cal_key_list['longitude_str']+':'+utils.to_dms(yl,is_lat_long='plong')
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['nakshatra_str']+':'+ \
                utils.NAKSHATRA_LIST[ynak[0]-1]
        yogi_planet = [l for l,naks in const.nakshathra_lords.items() if ynak[0]-1 in naks][0]
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[yogi_planet]
        key = self.cal_key_list['yogi_sphuta_str']+', '+self.cal_key_list['avayogi_sphuta_str']+', '+self.cal_key_list['sahayogi_str']
        return {key:ystr}       
    def get_ava_saha_yoga_for_mixed_chart(self,jd_at_dob, place,varga_factor_1=None, chart_method_1=None,
                                          varga_factor_2=None, chart_method_2=None):
        y,m,d,fh = utils.jd_to_gregorian(jd_at_dob);dob = drik.Date(y,m,d); tob = (fh,0,0)
        line_sep = '<br>'
        from jhora.horoscope.chart import sphuta
        yh,yl = sphuta.yogi_sphuta_mixed_chart(dob,tob,place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1, varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)
        ystr = self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['raasi_str']+':'+\
                utils.RAASI_LIST[yh]+' '+self.cal_key_list['longitude_str']+':'+utils.to_dms(yl,is_lat_long='plong')
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['nakshatra_str']+':'+ \
                utils.NAKSHATRA_LIST[ynak[0]-1]
        yogi_planet = [l for l,naks in const.nakshathra_lords.items() if ynak[0]-1 in naks][0]
        ystr += line_sep+self.cal_key_list['yogi_sphuta_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[yogi_planet]
        sahayogi_planet = const._house_owners_list[yh]
        ystr += line_sep+self.cal_key_list['sahayogi_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[sahayogi_planet]
        yh,yl = sphuta.avayogi_sphuta_mixed_chart(dob,tob,place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1, varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['raasi_str']+':'+\
                utils.RAASI_LIST[yh]+' '+self.cal_key_list['longitude_str']+':'+utils.to_dms(yl,is_lat_long='plong')
        ynak = drik.nakshatra_pada(yh*30+yl)
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['nakshatra_str']+':'+ \
                utils.NAKSHATRA_LIST[ynak[0]-1]
        yogi_planet = [l for l,naks in const.nakshathra_lords.items() if ynak[0]-1 in naks][0]
        ystr += line_sep+self.cal_key_list['avayogi_sphuta_str']+' '+self.cal_key_list['planet_str']+':'+ \
                utils.PLANET_NAMES[yogi_planet]
        key = self.cal_key_list['yogi_sphuta_str']+', '+self.cal_key_list['avayogi_sphuta_str']+', '+self.cal_key_list['sahayogi_str']
        return {key:ystr}       
    def get_sahams(self,planet_positions):
        _saham_info = {}
        from jhora.horoscope.transit import saham
        _vl_chart = ['' for _ in range(12)]
        for sah in const._saham_list:
            sl = eval('saham.'+sah+'_saham(planet_positions)')
            vl = drik.dasavarga_from_long(sl)
            _vl_chart[vl[0]] += self.cal_key_list[sah+'_saham_short_str'] +'\n'
            key = self.cal_key_list[sah+'_saham_str']+' '+self.cal_key_list['saham_str']
            value = utils.RAASI_LIST[vl[0]]+' '+utils.to_dms(vl[1],is_lat_long='plong')
            _saham_info[key] = value
            #print(key,value)
        _saham_menu_dict = {self.cal_key_list['saham_str']:_vl_chart}
        return _saham_menu_dict, _saham_info        
def get_chara_karakas(jd, place, years=1,months=1,sixty_hours=1,calculation_type='drik',pravesha_type=0):
    rasi_planet_positions = charts.rasi_chart(jd, place, years, months, sixty_hours, calculation_type, pravesha_type)
    return house.chara_karakas(rasi_planet_positions)
if __name__ == "__main__":
    horoscope_language = 'ta' # """ Matplotlib charts available only English"""
    dob = drik.Date(1996,12,7); tob = (10,34,0); place = drik.Place('Chennai,IN',13.0389, 80.2619, +5.5)
    chart_index = 8; dcf = 3; chart_method = 1; base_rasi=None; count_from_end_of_sign=None
    varga_factor_1 = 9; chart_method_1=1; varga_factor_2=12; chart_method_2=1
    jd_at_dob = utils.julian_day_number(dob, tob)
    a = Horoscope(place_with_country_code=place.Place,latitude=place.latitude,longitude=place.longitude,
                  timezone_offset=place.timezone,date_in=drik.Date(dob[0],dob[1],dob[2]),birth_time="10:34:00")

    horo_info,chart_info,asc_info = a.get_horoscope_information_for_chart(chart_index=chart_index, chart_method=chart_method,
                                            divisional_chart_factor=dcf, base_rasi=base_rasi,
                                            count_from_end_of_sign=count_from_end_of_sign, varnada_method=None)
    print(a.calendar_info)
    print('horo_info',horo_info)
    print('chart_info',chart_info)
    print('asc_info',asc_info)
    print('_22nd_drekkana',a._22nd_drekkana)
    exit()
    planet_positions = charts.mixed_chart(jd_at_dob, place, varga_factor_1=varga_factor_1, chart_method_1=chart_method_1,
                                              varga_factor_2=varga_factor_2, chart_method_2=chart_method_2)
    planet_positions = charts.divisional_chart(jd_at_dob, place,divisional_chart_factor=dcf,
                            chart_method=chart_method,base_rasi=base_rasi,
                            count_from_end_of_sign=count_from_end_of_sign)
    print('yogi info chart',a.get_ava_saha_yoga_info_for_chart(jd_at_dob, place, dcf, chart_method, base_rasi, count_from_end_of_sign))
    exit()
    chart_index_1 = 8; chart_method_1=1; chart_index_2=12; chart_method_2=1
    horo_info,chart_info,asc_info = a.get_horoscope_information_for_mixed_chart(chart_index_1, chart_method_1, 
                                                                                chart_index_2, chart_method_2)
    print('chart_index_1',chart_index_1,'chart_method_1',chart_method_1)
    print('chart_index_2',chart_index_2,'chart_method_2',chart_method_2)
    print('horo_info',horo_info)
    print('chart_info',chart_info)
    print('asc_info',asc_info)
    print('arudha lagna data',a._arudha_lagna_data_kundali)
    print('_hora_lagna_data_mixed',a._hora_lagna_data_kundali)
    print('_ghat_lagna_data_mixed',a._ghati_lagna_data_kundali)
    print('_vighati_lagna_data_mixed',a._vighati_lagna_data_kundali)
    print('_bhava_lagna_data_mixed',a._bhava_lagna_data_kundali)
    print('_sree_lagna_data_mixed',a._sree_lagna_data_kundali)
    print('_maandhi_data_mixed',a._maandhi_data_kundali)
    print('varnada_data_mixed',a._varnada_lagna_data_kundali)
    exit()
    print(a.calendar_info)
    print(a.horoscope_charts[0])
    #exit()
    #pp = charts.rasi_chart(jd_at_dob, place)
    #h_to_p = utils.get_house_planet_list_from_planet_positions(pp)
    planet = 2
    h_to_p = ['5/2/3/0','','','L/4','6/7','','','1','','','8','']
    p_to_h = utils.get_planet_to_house_dict_from_chart(h_to_p)
    print('aspects of ',utils.PLANET_NAMES[planet],house.aspected_planets_of_the_raasi(h_to_p, p_to_h[planet]))
    #exit()
    as_string = True
    a= Horoscope(place_with_country_code=place.Place,latitude=place.latitude,
                 longitude=place.longitude,timezone_offset=place.timezone,date_in=dob,birth_time='10:34:00',
                 language=horoscope_language)
    #a= Horoscope(latitude=35.994,longitude=-78.8986,timezone_offset=-4.0,date_in=dob,birth_time='23:43:00'
    a._sphuta_data = {}
    print(a._get_sphuta(dob, tob, place,divisional_chart_factor=1))
    print(a._sphuta_data)
    exit()
    db = a._get_kalachakra_dhasa(dob, tob, place)
    print(db)
    exit()
    a._arudha_lagna_data = {}
    a._get_arudha_padhas(dob, tob, place, divisional_chart_factor=1)
    a._get_arudha_padhas(dob, tob, place, divisional_chart_factor=9)
    exit()
    #db = a._get_drig_dhasa_bhukthi(dob, tob, place)
    #db = a._get_ashtottari_dhasa_bhukthi(dob, tob, place)
    db = a._get_narayana_dhasa(dob, tob, place)
    print('narayana',db)
    """
    db = a._get_naryana_dhasa(dob, tob, place)
    print('narayana',db)
    db = a._get_kendraadhi_dhasa(dob, tob, place)
    print('kendraadhi rasi',db)
    db = a._get_sudasa_dhasa(dob,tob,place)
    print('sudasa',db)
    db = a._get_drig_dhasa(dob,tob,place)
    print('drig',db)
    db = a._get_varsha_naryana_dhasa(dob, tob, place, years=1)
    print('varsha narayana',db)
    ba, ga = a._get_arudha_padhas(dob,tob,place,divisional_chart_factor=1)
    print(ba)
    print(ga)
    """
    exit()
