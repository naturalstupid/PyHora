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
import re, sys, os
sys.path.append('../')
""" Get Package Version from _package_info.py """
#import importlib.metadata
#_APP_VERSION = importlib.metadata.version('PyJHora')
#----------
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import ( QStyledItemDelegate, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QTextEdit, QLayout, QLabel, QSizePolicy, QLineEdit, QCompleter, QComboBox, 
                            QPushButton, QApplication, QMessageBox, QFileDialog, QDialog )
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QDateTime, QTimeZone, QStringListModel
from _datetime import datetime
import img2pdf
from PIL import Image
from jhora import const, utils, config
from jhora.ui.config_dialog import ConfigDialog
from jhora.panchanga import drik, pancha_paksha, vratha, info
from jhora.ui.place_widget import PlaceWidget
_festival_file = const._FESTIVAL_FILE
vratha.load_festival_data(_festival_file)

_available_ayanamsa_modes = [k for k in list(const.available_ayanamsa_modes.keys()) if k not in ['SENTHIL', 'SIDM_USER']]

_KEY_COLOR = 'brown'
_VALUE_COLOR = 'blue'
_HEADER_COLOR = 'green'
_KEY_LENGTH = 100
_VALUE_LENGTH = 200
_HEADER_LENGTH = 100

_HEADER_FORMAT_ = '<b><span style="color:' + _HEADER_COLOR + ';">{:' + '<' + str(_HEADER_LENGTH) + '}</span></b><br>'
_KEY_VALUE_FORMAT_ = '<span style="color:' + _KEY_COLOR + ';">{:.' + str(_KEY_LENGTH) + '}' + '  ' + \
                     '</span><span style="color:' + _VALUE_COLOR + ';">{:.' + str(_VALUE_LENGTH) + '}</span><br>'

_images_path = const._IMAGES_PATH
_IMAGES_PER_PDF_PAGE = 2
_IMAGE_ICON_PATH = const._IMAGE_ICON_PATH
_INPUT_DATA_FILE = const._INPUT_DATA_FILE
_SHOW_SPECIAL_TITHIS = True
_SHOW_MUHURTHA_OR_SHUBHA_HORA = 0  # 0=Muhurtha 1=Shubha Hora
_VEDIC_HOURS_PER_DAY = 60  # 30 for Muhurthas and 60 for Ghati
_planet_symbols = const._planet_symbols
_zodiac_symbols = const._zodiac_symbols

""" UI Constants """
_main_window_width = 1000
_main_window_height = 725
_main_ui_label_button_font_size = 10

_info_label1_height = 250
_INFO_LABEL_HAS_SCROLL = True
_info_label1_width = 100
_info_label1_font_size = 4.87 if not _INFO_LABEL_HAS_SCROLL else 6
_info_label2_height = _info_label1_height
_info_label3_height = _info_label1_height
_info_label2_width = 100
_info_label2_font_size = 4.87 if not _INFO_LABEL_HAS_SCROLL else 6
_info_label3_font_size = 4.87 if not _INFO_LABEL_HAS_SCROLL else 6

_row3_widget_width = 75
_chart_info_label_width = 230
_footer_label_font_height = 8
_footer_label_height = 30
_chart_size_factor = 1.35

_tab_names = ['panchangam_str', '']
_tab_count = len(_tab_names)
_tabcount_before_chart_tab = 1

available_languages = const.available_languages

_scrollbar_border_size = "1px"
_scrollbar_border_color = "#999999"

SCROLLBAR_BORDER_SIZE = "1px"
SCROLLBAR_BORDER_COLOR = "#999999"
SCROLLBAR_BACKGROUND = "#f0f0f0"
SCROLLBAR_WIDTH = "15px"
SCROLLBAR_MARGIN = "0px 0px 0px 0px"

HANDLE_BACKGROUND = "#55aaff"
HANDLE_MIN_HEIGHT = "20px"
HANDLE_BORDER_RADIUS = "5px"


def set_scrollbar_stylesheet(scroll_widget):
    scroll_widget.verticalScrollBar().setStyleSheet(f"""
        QScrollBar:vertical {{
            border: {SCROLLBAR_BORDER_SIZE} solid {SCROLLBAR_BORDER_COLOR};
            background: {SCROLLBAR_BACKGROUND};
            width: {SCROLLBAR_WIDTH};
            margin: {SCROLLBAR_MARGIN};
        }}

        QScrollBar::handle:vertical {{
            background: {HANDLE_BACKGROUND};
            min-height: {HANDLE_MIN_HEIGHT};
            border-radius: {HANDLE_BORDER_RADIUS};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """)


class PanchangaInfoDialog(QWidget):
    def __init__(self, language=None, jd=None, place: drik.Place = None,
                 info_label1_font_size=_info_label1_font_size,
                 info_label2_font_size=_info_label2_font_size,
                 info_label3_font_size=_info_label3_font_size,
                 info_label_height=_info_label1_height,
                 info_labels_have_scroll=_INFO_LABEL_HAS_SCROLL,
                 ayanamsa_mode=None):
        """
            @param jd: Julian Day Number
            @param place_of_birth: drik.Place
            @param language: One of 'English','Hindi','Tamil','Telugu','Kannada'; Default:const._DEFAULT_LANGUAGE
        """
        super().__init__()
        self._options_epoch = 0
        self.start_jd = jd
        self.place = place
        
        self._full_panchanga_cache = {}
        self._basic_panchanga_cache = {}
        self._last_info_html_1 = None
        self._last_info_html_2 = None
        self._last_info_html_3 = None

        self.info_labels_have_scroll = info_labels_have_scroll

        self._ayanamsa_mode = (
            ayanamsa_mode
            if ayanamsa_mode is not None and ayanamsa_mode in const.available_ayanamsa_modes.keys()
            else const._DEFAULT_AYANAMSA_MODE
        )
        drik.set_ayanamsa_mode(self._ayanamsa_mode)

        self._info_label1_font_size = info_label1_font_size
        self._info_label2_font_size = info_label2_font_size
        self._info_label3_font_size = info_label3_font_size
        self._info_label1_height = info_label_height
        self._info_label2_height = info_label_height
        self._info_label3_height = info_label_height
        self._language = utils._lang_to_display(language)
        self.set_language(self._language)
        current_date_str, current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
        if self.start_jd is None:
            year, month, day = current_date_str.split(',')
            dob = drik.Date(int(year), int(month), int(day))
            tob = current_time_str.split(':')
            self.start_jd = utils.julian_day_number(dob, (int(tob[0]), int(tob[1]), int(tob[2])))

        self.initUI()

        if self.place is not None:
            self.update_panchangam_info(self.start_jd, self.place)

    def set_options_epoch(self, epoch: int):
        self._options_epoch = int(epoch or 0)
    
    def invalidate_panchanga_cache(self, clear_existing: bool = False):
        """
        Invalidate panchanga-related caches after option changes.
        If clear_existing=True, also free cached data immediately.
        """
        self._options_epoch = getattr(self, "_options_epoch", 0) + 1
    
        if clear_existing:
            self._full_panchanga_cache.clear()
            self._basic_panchanga_cache.clear()
    
        self._last_info_html_1 = None
        self._last_info_html_2 = None
        self._last_info_html_3 = None

    def _panchanga_cache_key(self, jd, place):
        if jd is None or place is None:
            return None
        return (
            round(float(jd), 6),
            getattr(place, "name", ""),
            float(getattr(place, "latitude", 0.0)),
            float(getattr(place, "longitude", 0.0)),
            float(getattr(place, "timezone", 0.0)),
            utils._lang_to_display(self._language),
            self._ayanamsa_mode,
            self._options_epoch,
        )

    def clear_panchanga_caches(self):
        self._full_panchanga_cache.clear()
        self._basic_panchanga_cache.clear()
        self._last_info_html_1 = None
        self._last_info_html_2 = None
        self._last_info_html_3 = None
        
    def set_language(self, language):
        self._language = utils._lang_to_display(language)
        utils.set_language(utils._lang_to_code(language))
        self.res = utils.resource_strings

    def initUI(self):
        h_layout = QHBoxLayout()
        h_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self._info_label1 = QTextEdit("Information:") if self.info_labels_have_scroll else QLabel("Information:")
        if self.info_labels_have_scroll:
            self._info_label1.setReadOnly(True)
            self._info_label1.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._info_label1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            set_scrollbar_stylesheet(self._info_label1)
        self._info_label1.setMinimumHeight(self._info_label1_height)
        self._info_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._info_label1.setStyleSheet("border: 1px solid black;" + ' font-size:' + str(self._info_label1_font_size) + 'pt')
        _margin = int(self._info_label1_font_size)
        self._info_label1.setContentsMargins(_margin, _margin, _margin, _margin)
        h_layout.addWidget(self._info_label1)

        self._info_label2 = QTextEdit("Information:") if self.info_labels_have_scroll else QLabel("Information:")
        if self.info_labels_have_scroll:
            self._info_label2.setReadOnly(True)
            self._info_label2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._info_label2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            set_scrollbar_stylesheet(self._info_label2)
        self._info_label2.setMinimumHeight(self._info_label2_height)
        self._info_label2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._info_label2.setStyleSheet("border: 1px solid black;" + ' font-size:' + str(self._info_label2_font_size) + 'pt')
        _margin = int(self._info_label2_font_size)
        self._info_label2.setContentsMargins(_margin, _margin, _margin, _margin)
        h_layout.addWidget(self._info_label2)

        self._info_label3 = QTextEdit("Information:") if self.info_labels_have_scroll else QLabel("Information:")
        if self.info_labels_have_scroll:
            self._info_label3.setReadOnly(True)
            self._info_label3.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._info_label3.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            set_scrollbar_stylesheet(self._info_label3)
        self._info_label3.setMinimumHeight(self._info_label3_height)
        self._info_label3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._info_label3.setStyleSheet("border: 1px solid black;" + ' font-size:' + str(self._info_label3_font_size) + 'pt')
        _margin = int(self._info_label3_font_size)
        self._info_label3.setContentsMargins(_margin, _margin, _margin, _margin)
        h_layout.addWidget(self._info_label3)

        self.setLayout(h_layout)
        self.setWindowTitle(self.res['panchangam_str'])
        self.move(50, 50)

    def update_panchangam_info(self, jd=None, place: drik.Place = None):
        try:
            if jd is not None:
                self.start_jd = jd
            if place is not None:
                self.place = place

            if self.start_jd is None or self.place is None:
                return

            cache_key = self._panchanga_cache_key(self.start_jd, self.place)
            results_dict = self._full_panchanga_cache.get(cache_key)

            if results_dict is None:
                results_dict = info.get_panchangam_resources(
                    self.start_jd,
                    self.place,
                    ayanamsa_mode=self._ayanamsa_mode
                )
                self._full_panchanga_cache[cache_key] = results_dict

            sep_str = '<br>'
            format_str = _KEY_VALUE_FORMAT_
            header = _HEADER_FORMAT_

            info_str = ''.join([
                header.format(k) if v.strip() == '' else format_str.format(k, v)
                for k, v in results_dict.items()
            ])

            info_list = [ele for ele in info_str.split(sep_str) if ele.strip() != '']
            info_len = int(len(info_list) / 3)

            html1 = sep_str.join(info_list[:info_len])
            html2 = sep_str.join(info_list[info_len:2 * info_len])
            html3 = sep_str.join(info_list[2 * info_len:])

            self.setUpdatesEnabled(False)
            try:
                # Only update panes if content actually changed
                if html1 != self._last_info_html_1:
                    self._info_label1.clear()
                    self._info_label1.setStyleSheet(
                        "border: 1px solid black;" + ' font-size:' + str(self._info_label1_font_size) + 'pt'
                    )
                    self._info_label1.setHtml(html1)
                    self._last_info_html_1 = html1

                if html2 != self._last_info_html_2:
                    self._info_label2.clear()
                    self._info_label2.setStyleSheet(
                        "border: 1px solid black;" + ' font-size:' + str(self._info_label2_font_size) + 'pt'
                    )
                    self._info_label2.setHtml(html2)
                    self._last_info_html_2 = html2

                if html3 != self._last_info_html_3:
                    self._info_label3.clear()
                    self._info_label3.setStyleSheet(
                        "border: 1px solid black;" + ' font-size:' + str(self._info_label3_font_size) + 'pt'
                    )
                    self._info_label3.setHtml(html3)
                    self._last_info_html_3 = html3
            finally:
                self.setUpdatesEnabled(True)
            #self.adjustSize()  ## Commentd to avoid panchango 3 labels shrinking
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"Panchangam:update_panchangam_info: An error occurred: {e}", 'line number', tb.tb_lineno)

    def _fill_information_label1(self, show_more_link=True, jd=None, place=None):
        try:
            jd = self.start_jd if jd is None else jd
            place = self.place if place is None else place
    
            if jd is None or place is None:
                return ''
    
            if not hasattr(self, "_basic_panchanga_cache"):
                self._basic_panchanga_cache = {}
    
            if hasattr(self, "_panchanga_cache_key"):
                cache_key = self._panchanga_cache_key(jd, place)
            else:
                # Fallback key for callers like VedicCalendar
                cache_key = (
                    round(float(jd), 6),
                    getattr(place, "name", ""),
                    float(getattr(place, "latitude", 0.0)),
                    float(getattr(place, "longitude", 0.0)),
                    float(getattr(place, "timezone", 0.0)),
                    getattr(self, "_language", ""),
                    getattr(self, "_ayanamsa_mode", const._DEFAULT_AYANAMSA_MODE),
                )
    
            info_str = self._basic_panchanga_cache.get(cache_key)
    
            if info_str is None:
                format_str = _KEY_VALUE_FORMAT_
                results_dict = info.get_panchangam_resources_basic(
                    jd,
                    place,
                    ayanamsa_mode=getattr(self, "_ayanamsa_mode", const._DEFAULT_AYANAMSA_MODE)
                )
                info_str = ''.join([format_str.format(k, v) for k, v in results_dict.items()])
                self._basic_panchanga_cache[cache_key] = info_str
    
            if show_more_link:
                info_str += _KEY_VALUE_FORMAT_.format('<a href="show_more">Show more</a>', '')
    
            return info_str
    
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"PanchangaInfoDialog - An error occurred: {e}", 'line number', tb.tb_lineno)
            return ''
        
class PanchangaWidget(QWidget):
    def __init__(self, calculation_type: str = 'drik', language=None,
                 date_of_birth=None, time_of_birth=None, place_of_birth=None,
                 show_vedic_digital_clock=False, show_local_clock=False,
                 show_vedic_analog_clock=False,
                 use_world_city_database=None,
                 use_internet_for_location_check=None,
                 panchanga_update_minutes: int = 0):
        """
            @param date_of_birth: string in the format 'yyyy,m,d' e.g. '2024,1,1' or '2024,01,01'
            @param place_of_birth: tuple in the format
                ('place_name', latitude_float, longitude_float, timezone_hrs_float[, elevation_float])
            @param language: One of 'English','Hindi','Tamil','Telugu','Kannada'; Default:English
        """
        self._options_epoch = 0
        config.initialize_runtime(force_reload=True, silent=False)
        use_world_city_database = (
            const.check_database_for_world_cities if use_world_city_database is None
            else use_world_city_database
        )
        self.use_world_city_database = use_world_city_database
        use_internet_for_location_check = (
            const.use_internet_for_location_check if use_internet_for_location_check is None
            else use_internet_for_location_check
        )
        self.use_internet_for_location_check = use_internet_for_location_check
        import time
        init_time = time.time()
        super().__init__()

        # ----------------------------
        # changed/dirty tracking flags
        # ----------------------------
        self._inputs_changed = False
        self._suspend_input_change_tracking = True

        self.panchanga_update_minutes = int(panchanga_update_minutes or 0)
        self._panchanga_update_timer = None

        self.show_vedic_digital_clock = show_vedic_digital_clock
        self.show_vedic_analog_clock = show_vedic_analog_clock and show_vedic_digital_clock
        self.show_local_clock = show_local_clock

        self._horo = None
        self._language = utils._lang_to_display(language)
        utils.set_language(utils._lang_to_code(language))

        start_time = time.time()
        utils.use_database_for_world_cities(self.use_world_city_database)
        print('end load place engine', time.time() - start_time)
        self._database_engine = const.database_engine
        self.resources = utils.resource_strings
        self._calculation_type = calculation_type
        self._ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
        self._ayanamsa_value = None

        self._place_obj = None
        self.place = None
        self.julian_day = None
        self._birth_julian_day = None

        current_date_str, current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')

        self._init_main_window()
        self._v_layout = QVBoxLayout()
        self._create_row1_ui()
        self._create_row_2_ui()

        if date_of_birth is None:
            self.date_of_birth(current_date_str)
        else:
            self.date_of_birth(date_of_birth)

        if time_of_birth is None:
            self.time_of_birth(current_time_str)
        else:
            self.time_of_birth(time_of_birth)

        # Compute initial JD BEFORE creating tab widgets
        year, month, day = self._dob_text.text().split(",")
        dob = (int(year), int(month), int(day))
        tob = tuple(int(x) for x in self._tob_text.text().split(':'))
        self._birth_julian_day = utils.julian_day_number(dob, tob)
        self.julian_day = self._birth_julian_day

        # Resolve place ONCE here
        if place_of_birth is not None:
            if len(place_of_birth) >= 5:
                p_name, lat, lon, tz, elev = place_of_birth[:5]
            else:
                p_name, lat, lon, tz = place_of_birth[:4]
                elev = 0.0

            self.set_place_fields(p_name, lat, lon, tz, elev)
            self._place_obj = drik.Place(p_name, lat, lon, tz, elev)

        elif self.use_internet_for_location_check:
            loc = utils.get_place_from_user_ip_address()
            print('loc from IP address', loc)
            if len(loc) == 5:
                print('setting values from loc')
                self.set_place_fields(loc[0], loc[1], loc[2], loc[3], loc[4])
                self._place_obj = drik.Place(loc[0], loc[1], loc[2], loc[3], loc[4])

        self.place = self._place_obj

        # Now create tabs/dialog using prepared jd/place
        self._init_tab_widget_ui()
        if hasattr(self, "panchanga_info_dialog") and self.panchanga_info_dialog is not None:
            self.panchanga_info_dialog.set_options_epoch(self._options_epoch)
        # end init -> enable change tracking and ensure clean button state
        self._suspend_input_change_tracking = False
        self._clear_inputs_changed()

        """ Commented in V4.0.4 to force explicit calling """
        # self.compute_horoscope(calculation_type=self._calculation_type)
        print('Init elapsed time', time.time() - init_time)

    # =========================================================
    # CHANGED / DIRTY FLAG HELPERS
    # =========================================================
    def _mark_inputs_changed(self, reason: str = ""):
        """
        Mark UI inputs as changed, so the current panchangam/results are stale.

        This does NOT change the localized button text.
        It only bolds the Show Chart button.
        """
        if getattr(self, "_suspend_input_change_tracking", False):
            return

        self._inputs_changed = True
        self._update_compute_button_changed_state()

    def _clear_inputs_changed(self):
        """
        Clear changed flag after a successful compute.
        """
        self._inputs_changed = False
        self._update_compute_button_changed_state()

    def _update_compute_button_changed_state(self):
        """
        Visual cue on the Compute button when inputs have changed.

        Keep the localized button text unchanged.
        Only toggle button font bold/normal.
        """
        if not hasattr(self, "_compute_button"):
            return

        font = self._compute_button.font()
        font.setBold(bool(getattr(self, "_inputs_changed", False)))
        self._compute_button.setFont(font)

    def _compute_and_clear_changed(self):
        """
        Wrapper used by the Show Chart button.
        Runs compute_horoscope(), then clears changed flag only if compute succeeds.
        """
        ok = self.compute_horoscope(calculation_type=self._calculation_type)
        if ok:
            self._clear_inputs_changed()

    # =========================================================
    # EXISTING METHODS
    # =========================================================
    def _ensure_panchanga_update_timer(self):
        """Start/stop live panchangam refresh timer depending on panchanga_update_minutes."""
        if self.panchanga_update_minutes <= 0:
            if self._panchanga_update_timer is not None:
                self._panchanga_update_timer.stop()
                self._panchanga_update_timer.deleteLater()
                self._panchanga_update_timer = None
            return

        if self._panchanga_update_timer is None:
            self._panchanga_update_timer = QTimer(self)
            self._panchanga_update_timer.timeout.connect(self._auto_update_panchanga_now)

        self._panchanga_update_timer.setInterval(self.panchanga_update_minutes * 60 * 1000)
        if not self._panchanga_update_timer.isActive():
            self._panchanga_update_timer.start()

    def _auto_update_panchanga_now(self):
        """
        Refresh Panchangam & clock using current datetime in the chart's place timezone.
        Minimal side effects: does NOT call compute_horoscope() or overwrite all UI fields.
        """
        try:
            if self.place is None:
                return

            tz_hours = float(self.place.timezone)
            time_zone = QTimeZone(int(tz_hours * 3600))
            dt = QDateTime.currentDateTime().toTimeZone(time_zone)

            y = dt.date().year()
            m = dt.date().month()
            d = dt.date().day()
            hh = dt.time().hour()
            mm = dt.time().minute()
            ss = dt.time().second()

            jd_now = utils.julian_day_number((y, m, d), (hh, mm, ss))
            self.julian_day = jd_now

            if hasattr(self, "panchanga_info_dialog") and self.panchanga_info_dialog is not None:
                self.panchanga_info_dialog.update_panchangam_info(jd_now, self.place)

            if self.show_vedic_digital_clock or self.show_local_clock:
                self._update_clock_tab_text()

            if getattr(self, "_vedic_analog_clock", None) is not None:
                self._vedic_analog_clock.jd = jd_now
                self._vedic_analog_clock.place = self.place
                self._vedic_analog_clock._get_drik_info()

            self._tob_text.setText(f"{hh:02d}:{mm:02d}:{ss:02d}")

        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"Auto Panchangam update error: {e}", "line", tb.tb_lineno)

    def _hide_2nd_row_widgets(self, show=True):
        self._dob_label.setVisible(show)
        self._dob_text.setVisible(show)
        self._tob_label.setVisible(show)
        self._tob_text.setVisible(show)

    def _init_tab_widget_ui(self):
        self.tabNames = _tab_names
        self.tabWidget = QTabWidget()
        self.horo_tabs = []
        self._v_layout.addWidget(self.tabWidget)

        self.tabCount = len(self.tabNames)
        t = 0
        self._init_panchanga_tab_widgets(t)

        if self.show_vedic_digital_clock or self.show_local_clock:
            t += 1
            self._init_clock_tab(t)

        self.tabCount = self.tabWidget.count()
        self._add_footer_to_chart()
        self.setLayout(self._v_layout)

    def _init_clock_tab(self, tab_index):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_clock_tab_text)
        self.timer.start(1000)

        if self.show_vedic_analog_clock:
            from jhora.ui.vedic_clock import VedicAnalogClock
            self._vedic_analog_clock = VedicAnalogClock()
            self.horo_tabs.append(self._vedic_analog_clock)
            self.tabWidget.addTab(self.horo_tabs[tab_index], 'Clock')
            self.tabWidget.tabBar().setTabEnabled(1, True)
        else:
            self.horo_tabs.append(QWidget())
            self.tabWidget.addTab(self.horo_tabs[tab_index], 'Clock')
            self.tabWidget.tabBar().setTabEnabled(1, False)

    def _update_clock_tab_text(self):
        if not (self.show_vedic_digital_clock or self.show_local_clock):
            return
        if self.place is None or self.julian_day is None:
            return
        if self.tabWidget.count() < 2:
            return

        jd = self.julian_day
        place = self.place

        current_datetime = QDateTime.currentDateTime()
        local_time_zone_hours = float(place.timezone)
        time_zone = QTimeZone(int(local_time_zone_hours * 3600))
        current_datetime = current_datetime.toTimeZone(time_zone)

        current_time = current_datetime.time().hour() + \
                       current_datetime.time().minute() / 60 + \
                       current_datetime.time().second() / 3600

        local_time = ''
        if self.show_local_clock:
            lc = self.resources['present_str'] + ' ' + f"{self.resources['time_of_birth_str']} "
            local_time = lc + current_datetime.time().toString("HH:mm:ss") + ' / '

        vedic_time = drik.vedic_time(jd, place, current_time, vedic_hours_per_day=_VEDIC_HOURS_PER_DAY)
        vc1 = self.resources['vedic_clock_str'] + ' '
        vc = vc1 + f"{self.resources['ghati_str']}:{self.resources['pala_str']}:{self.resources['vighati_str']} "
        vedic_time_str = local_time + vc + f"{vedic_time[0]:02}:{vedic_time[1]:02}:{vedic_time[2]:02}"

        self.tabWidget.setTabText(1, vedic_time_str)
        self.tabWidget.tabBar().setStyleSheet("QTabBar::tab { color: green; font-weight: bold; }")

    def _init_panchanga_tab_widgets(self, tab_index):
        self.panchanga_info_dialog = PanchangaInfoDialog(
            language=self._language,
            jd=self._birth_julian_day,
            place=self._place_obj,
            info_label1_font_size=_info_label1_font_size,
            info_label2_font_size=_info_label2_font_size,
            info_label3_font_size=_info_label3_font_size,
            info_label_height=_info_label1_height,
            ayanamsa_mode=self._ayanamsa_mode
        )
        self.horo_tabs.append(self.panchanga_info_dialog)
        self.tabWidget.addTab(self.horo_tabs[tab_index], self.tabNames[tab_index])

    def _init_main_window(self):
        self._footer_title = ''
        self.setWindowIcon(QtGui.QIcon(_IMAGE_ICON_PATH))
        # DO NOT overwrite self._language here
        # Allow user resize / maximize / fullscreen (setFixedSize blocked that).
        self.setMinimumSize(_main_window_width, _main_window_height)
        self.resize(_main_window_width, _main_window_height)
        self.showMaximized()

    def _create_row1_ui(self):
        self._row1_h_layout = QHBoxLayout()

        self._dob_label = QLabel("Date of Birth:")
        self._row1_h_layout.addWidget(self._dob_label)

        self._date_of_birth = ''
        self._dob_text = QLineEdit(self._date_of_birth)
        self._dob_text.setToolTip('Date of birth in the format YYYY,MM,DD\nFor BC enter negative years.\nAllowed Year Range: -13000 (BC) to 16800 (AD)')
        self._dob_label.setMaximumWidth(_row3_widget_width)
        self._dob_text.setMaximumWidth(_row3_widget_width)
        self._dob_text.textChanged.connect(lambda _t: self._mark_inputs_changed("date changed"))
        self._row1_h_layout.addWidget(self._dob_text)

        self._tob_label = QLabel("Time of Birth:")
        self._row1_h_layout.addWidget(self._tob_label)

        self._time_of_birth = ''
        self._tob_text = QLineEdit(self._time_of_birth)
        self._tob_text.setToolTip('Enter time of birth in the format HH:MM:SS if afternoon use 12+ hours')
        self._tob_label.setMaximumWidth(_row3_widget_width)
        self._tob_text.setMaximumWidth(_row3_widget_width)
        self._tob_text.textChanged.connect(lambda _t: self._mark_inputs_changed("time changed"))
        self._row1_h_layout.addWidget(self._tob_text)

        self._place_label = QLabel("Place:")
        self._row1_h_layout.addWidget(self._place_label)

        self._place_name = ''
        self._elevation = 0.0
        self._place_widget = PlaceWidget(
            self,
            initial_text=self._place_name,
            placeholder_text="Enter place of birth, country name",
            tooltip_text="Enter place of birth, country name",
        )

        self._place_text = self._place_widget.lineEdit()
        self._place_widget.textEditedSignal.connect(self._resize_place_text_size)
        self._place_widget.placeSelected.connect(self._get_location)
        self._place_widget.textEditedSignal.connect(lambda _t: self._mark_inputs_changed("place edited"))

        self._row1_h_layout.addWidget(self._place_widget, 1)
        self._place_text.setToolTip('Enter place of birth, country name')

        self._lat_label = QLabel("Latidude:")
        self._row1_h_layout.addWidget(self._lat_label)

        self._lat_text = QLineEdit('')
        self._latitude = 0.0
        self._lat_text.setMaximumWidth(90)
        self._lat_text.setToolTip('Enter Latitude preferably exact at place of birth: Format: +/- xx.xxx')
        self._lat_text.textChanged.connect(lambda _t: self._mark_inputs_changed("latitude changed"))
        self._row1_h_layout.addWidget(self._lat_text)

        self._long_label = QLabel("Longitude:")
        self._row1_h_layout.addWidget(self._long_label)

        self._long_text = QLineEdit('')
        self._longitude = 0.0
        self._long_text.setMaximumWidth(90)
        self._long_text.setToolTip('Enter Longitude preferably exact at place of birth. Format +/- xx.xxx')
        self._long_text.textChanged.connect(lambda _t: self._mark_inputs_changed("longitude changed"))
        self._row1_h_layout.addWidget(self._long_text)

        self._tz_label = QLabel("Time Zone:")
        self._row1_h_layout.addWidget(self._tz_label)

        self._tz_text = QLineEdit('')
        self._time_zone = 0.0
        self._tz_text.setMaximumWidth(70)
        self._tz_text.setToolTip('Enter Time offset from GMT e.g. -5.5 or 4.5')
        self._tz_text.textChanged.connect(lambda _t: self._mark_inputs_changed("timezone changed"))
        self._row1_h_layout.addWidget(self._tz_text)

        self._v_layout.addLayout(self._row1_h_layout)

    def _create_row_2_ui(self):
        self._row2_h_layout = QHBoxLayout()

        self._options_button = QPushButton(self.resources['options_str'])
        self._options_button.setFont(QtGui.QFont("Arial Bold", 9))
        self._options_button.clicked.connect(self._open_options_dialog)
        self._options_button.setToolTip(self.resources['options_str'])
        self._row2_h_layout.addWidget(self._options_button)

        self._compute_button = QPushButton(self.resources['show_chart_str'])
        self._compute_button.setFont(QtGui.QFont("Arial Bold", 9))
        self._compute_button.clicked.connect(self._compute_and_clear_changed)
        self._compute_button.setToolTip(self.resources['compute_tooltip_str'])
        self._row2_h_layout.addWidget(self._compute_button)

        self._save_image_button = QPushButton(self.resources['save_pdf_str'])
        self._save_image_button.setFont(QtGui.QFont("Arial Bold", 8))
        self._save_image_button.clicked.connect(lambda: self.save_as_pdf(pdf_file_name=None))
        self._save_image_button.setToolTip(self.resources['savepdf_tooltip_str'])
        self._row2_h_layout.addWidget(self._save_image_button)

        self._save_city_button = QPushButton(self.resources['save_city_str'])
        self._save_city_button.clicked.connect(self._save_city_to_database)
        self._save_city_button.setToolTip(self.resources['savecity_tooltip_str'])
        self._row2_h_layout.addWidget(self._save_city_button)

        self._v_layout.addLayout(self._row2_h_layout)

    def _add_footer_to_chart(self):
        self._footer_label = QLabel('')
        self._footer_label.setTextFormat(Qt.TextFormat.RichText)
        self._footer_label.setText(self._footer_title)
        self._footer_label.setStyleSheet("border: 1px solid black;")
        self._footer_label.setFont(QtGui.QFont("Arial Bold", _footer_label_font_height))
        self._footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_label.setFixedHeight(_footer_label_height)
        self._footer_label.setFixedWidth(self.width())
        self._footer_label.setWordWrap(True)
        self._footer_label.setOpenExternalLinks(True)
        self._v_layout.addWidget(self._footer_label)

    def _on_application_exit(self):
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook
        QApplication.quit()

    def ayanamsa_mode(self, ayanamsa_mode, ayanamsa=None):
        """
            Set Ayanamsa mode
            @param ayanamsa_mode - Default - Lahiri
            See 'drik.available_ayanamsa_modes' for the list of available models
        """
        if ayanamsa_mode.upper() in const.available_ayanamsa_modes.keys():
            self._ayanamsa_mode = ayanamsa_mode
            self._ayanamsa_value = ayanamsa
            const._DEFAULT_AYANAMSA_MODE = self._ayanamsa_mode

    def set_place_fields(self, place_name, latitude, longitude, timezone_hrs, elevation=0.0):
        """
            Set the place of birth fields on UI.
        """
        self._place_name = place_name
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._time_zone = float(timezone_hrs)
        self._elevation = float(elevation)

        self._place_text.setText(self._place_name)
        self._lat_text.setText(str(self._latitude))
        self._long_text.setText(str(self._longitude))
        self._tz_text.setText(str(self._time_zone))

    def latitude(self, latitude):
        self._latitude = float(latitude)
        self._lat_text.setText(str(latitude))

    def longitude(self, longitude):
        self._longitude = float(longitude)
        self._long_text.setText(str(longitude))

    def time_zone(self, time_zone):
        self._time_zone = float(time_zone)
        self._tz_text.setText(str(time_zone))

    def date_of_birth(self, date_of_birth):
        self._date_of_birth = date_of_birth
        self._dob_text.setText(self._date_of_birth)

    def time_of_birth(self, time_of_birth):
        self._time_of_birth = time_of_birth
        self._tob_text.setText(self._time_of_birth)

    def language(self, language):
        if language in available_languages.keys():
            self._language = language

    def _validate_ui(self):
        all_data_ok = self._place_text.text().strip() != '' and \
                      re.match(r"[\+|\-]?\d+\.\d+\s?", self._lat_text.text().strip(), re.IGNORECASE) and \
                      re.match(r"[\+|\-]?\d+\.\d+\s?", self._long_text.text().strip(), re.IGNORECASE) and \
                      re.match(r"[\+|\-]?\d{1,5}\,\d{1,2}\,\d{1,2}", self._dob_text.text().strip(), re.IGNORECASE)
        return all_data_ok

    def _update_main_window_label_and_tooltips(self):
        try:
            if self.resources:
                msgs = self.resources

                self._place_label.setText(msgs['place_str'])
                self._place_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._place_label.setToolTip(msgs['place_tooltip_str'])

                self._lat_label.setText(msgs['latitude_str'])
                self._lat_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._lat_label.setToolTip(msgs['latitude_tooltip_str'])

                self._long_label.setText(msgs['longitude_str'])
                self._long_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._long_label.setToolTip(msgs['longitude_tooltip_str'])

                self._tz_label.setText(msgs['timezone_offset_str'])
                self._tz_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._tz_label.setToolTip(msgs['timezone_tooltip_str'])

                self._dob_label.setText(msgs['date_of_birth_str'])
                self._dob_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._dob_label.setToolTip(msgs['dob_tooltip_str'])

                self._tob_label.setText(msgs['time_of_birth_str'])
                self._tob_label.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._tob_label.setToolTip(msgs['tob_tooltip_str'])

                if hasattr(self, "_options_button") and self._options_button is not None:
                    self._options_button.setText(msgs['options_str'])
                    self._options_button.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                    self._options_button.setToolTip(msgs['options_str'])

                self._compute_button.setText(msgs['show_chart_str'])
                self._compute_button.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._compute_button.setToolTip(msgs['compute_tooltip_str'])

                self._save_image_button.setText(msgs['save_pdf_str'])
                self._save_image_button.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._save_image_button.setToolTip(msgs['savepdf_tooltip_str'])

                self._save_city_button.setText(msgs['save_city_str'])
                self._save_city_button.setStyleSheet('font-size:' + str(_main_ui_label_button_font_size) + 'pt')
                self._save_city_button.setToolTip(msgs['savecity_tooltip_str'])

                self._footer_label.setText(msgs['window_footer_title'])
                self.setWindowTitle(msgs['window_title'] + '-' + const._APP_VERSION)
                self.update()

                print('UI Language change to', utils._lang_to_display(self._language), 'completed')

        except:
            print('Some error happened during changing to', self._language, ' language and displaying UI in that language.\n' +
                  'Please Check resources file:', const._DEFAULT_LANGUAGE_MSG_STR + available_languages[self._language] + '.txt')
            print(sys.exc_info())

    def _open_options_dialog(self):
        """
        Open ConfigDialog. If saved, mark inputs changed so Show Chart becomes bold.
        """
        try:
            dlg = ConfigDialog(mode="both", parent=self)
            result = dlg.exec()
    
            if result == QDialog.DialogCode.Accepted:
                # bump local cache epoch
                self._options_epoch += 1
    
                # sync copied runtime values from const
                self.use_world_city_database = const.check_database_for_world_cities
                self.use_internet_for_location_check = const.use_internet_for_location_check
                self._database_engine = const.database_engine
                self._ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
    
                # propagate epoch to PanchangaInfoDialog and invalidate its caches
                if hasattr(self, "panchanga_info_dialog") and self.panchanga_info_dialog is not None:
                    self.panchanga_info_dialog.set_options_epoch(self._options_epoch)
                    self.panchanga_info_dialog.invalidate_panchanga_cache(clear_existing=True)
    
                # results are stale until recomputed
                self._mark_inputs_changed("options saved")
    
                QMessageBox.information(
                    self,
                    self.resources.get('options_str', 'Options'),
                    "Settings saved.\nClick Show Chart to refresh results."
                )
    
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"_open_options_dialog error: {e}", "line", tb.tb_lineno)        

    def compute_horoscope(self, calculation_type='drik'):
        """
            Compute the horoscope based on details entered
            if details missing - error is displayed
        """
        import time
        cmp_time = time.time()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            from jhora import config
            config.initialize_runtime(force_reload=True, silent=False)
            ### Load Place Database again if changed
            self.use_world_city_database = const.check_database_for_world_cities
            utils.use_database_for_world_cities(self.use_world_city_database)
            self._database_engine = const.database_engine

            self._ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
            if not self._validate_ui():
                print('values are not filled properly')
                return False
    
            self._place_name = self._place_text.text()
            self._latitude = float(self._lat_text.text())
            self._longitude = float(self._long_text.text())
    
            self._language = const._DEFAULT_LANGUAGE
            utils.set_language(self._language)
            self.resources = utils.resource_strings
    
            year, month, day = self._dob_text.text().split(",")
            dob = (int(year), int(month), int(day))
            tob = tuple([int(x) for x in self._tob_text.text().split(':')])
    
            self.julian_day = utils.julian_day_number(dob, tob)
            tz_hours = ( utils.get_place_timezone_offset(self._latitude, self._longitude, self.julian_day)
                         if const.apply_daylight_savings_correction else self._time_zone)
            self._tz_text.setText(str(tz_hours))
            self._time_zone = tz_hours
            self._place_obj = drik.Place(
                self._place_name,
                float(self._latitude),
                float(self._longitude),
                float(self._time_zone),
                float(self._elevation)
            )
            self.place = self._place_obj
    
            if self._ayanamsa_mode.upper() == 'SUNDAR_SS':
                drik.set_ayanamsa_mode(self._ayanamsa_mode, jd=self.julian_day)
            else:
                drik.set_ayanamsa_mode(self._ayanamsa_mode)
    
            info_str = ''
            format_str = _KEY_VALUE_FORMAT_
            self._fill_panchangam_info(info_str, format_str)
    
            if self.show_vedic_digital_clock or self.show_local_clock:
                self._update_clock_tab_text()
    
            if self.show_vedic_analog_clock and getattr(self, "_vedic_analog_clock", None) is not None:
                self._vedic_analog_clock.jd = self.julian_day
                self._vedic_analog_clock.place = self.place
                self._vedic_analog_clock._get_drik_info()
    
            self.tabWidget.setCurrentIndex(0)
            self._update_main_window_label_and_tooltips()
            self._update_chart_ui_with_info()
            # Do not shrink after compute — keeps maximized / user-resized window size.
            if not self.isMaximized():
                hint = self.minimumSizeHint()
                cur = self.size()
                self.resize(max(cur.width(), hint.width()), max(cur.height(), hint.height()))
            self.tabWidget.setFocus()
    
            self._ensure_panchanga_update_timer()
            print('compute time elapsed',time.time()-cmp_time)
        finally:
            QApplication.restoreOverrideCursor()
        return True

    def _recreate_chart_tab_widgets(self):
        self._v_layout.removeWidget(self.tabWidget)
        current_tab = self.tabWidget.currentIndex()
        self.tabWidget.deleteLater()
        self._footer_label.deleteLater()
        self.tabWidget = None
        self._init_tab_widget_ui()
        self.tabWidget.setCurrentIndex(current_tab)

    def _fill_panchangam_info(self, info_str, format_str):
        jd = self.julian_day
        place = self.place

        self.panchanga_info_dialog._ayanamsa_mode = self._ayanamsa_mode
        self.panchanga_info_dialog.set_language(self._language)
        self.panchanga_info_dialog.update_panchangam_info(jd, place)

    def _update_chart_ui_with_info(self):
        for t in range(_tabcount_before_chart_tab):
            self.tabWidget.setTabText(t, self.resources[_tab_names[t]])
        self.update()

    def _reset_place_text_size(self):
        self._place_text.setCursorPosition(0)

    def _resize_place_text_size(self):
        return

    def _get_location(self, place_name):
        result = utils.get_location(place_name)
        print('RESULT', result)

        if result:
            self._place_name, self._latitude, self._longitude, self._time_zone, self._elevation = result

            self._place_text.setText(self._place_name)
            self._lat_text.setText(str(self._latitude))
            self._long_text.setText(str(self._longitude))
            self._tz_text.setText(str(self._time_zone))

            self._place_obj = drik.Place(
                self._place_name,
                float(self._latitude),
                float(self._longitude),
                float(self._time_zone),
                float(self._elevation)
            )
            self.place = self._place_obj

        else:
            msg = place_name + " could not be found in OpenStreetMap.\nTry entering latitude and longitude manually.\nOr try entering nearest big city"
            print(msg)
            QMessageBox.about(self, "City not found", msg)
            self._lat_text.setText('')
            self._long_text.setText('')

        self._mark_inputs_changed("place selected")
        self._reset_place_text_size()

    def _save_city_to_database(self):
        if self._validate_ui():
            tmp_arr = self._place_name.split(',')
            country = 'N/A'
            city = tmp_arr[0]
            if len(tmp_arr) > 1:
                country = ','.join(tmp_arr[1:])
            location_data = [country, city, self._latitude, self._longitude, country, self._time_zone, self._elevation]
            utils.save_location_to_database(location_data)
        return

    def _save_info_labels_by_click_scroll(self, image_id, image_files):
        labels = [
            self.panchanga_info_dialog._info_label1,
            self.panchanga_info_dialog._info_label2,
            self.panchanga_info_dialog._info_label3
        ]

        scrollbars = [label.verticalScrollBar() for label in labels]
        finished = [False, False, False]

        QApplication.processEvents()
        image_file = _images_path + f'pdf_info_label_{image_id}.png'
        image = self.grab()
        image.save(image_file)
        image_files.append(image_file)
        image_id += 1

        while not all(finished):
            for i, sb in enumerate(scrollbars):
                if not finished[i]:
                    current = sb.value()
                    step = sb.pageStep()
                    max_val = sb.maximum()
                    new_val = current + step
                    sb.setValue(min(new_val, max_val))
                    finished[i] = new_val >= max_val

            QApplication.processEvents()

            image_file = _images_path + f'pdf_info_label_{image_id}.png'
            image = self.grab()
            image.save(image_file)
            image_files.append(image_file)
            image_id += 1

        return image_id

    def _save_info_labels_as_images(self, image_id, image_files):
        label1 = self.panchanga_info_dialog._info_label1
        label2 = self.panchanga_info_dialog._info_label2
        label3 = self.panchanga_info_dialog._info_label3

        def get_scrollable_pages(text_edit: QTextEdit) -> int:
            scroll_bar = text_edit.verticalScrollBar()
            step = scroll_bar.pageStep()
            max_val = scroll_bar.maximum()
            return max(1, int(max_val // step + 1))

        pages_label1 = get_scrollable_pages(label1)
        pages_label2 = get_scrollable_pages(label2)
        pages_label3 = get_scrollable_pages(label3)

        max_pages = max(pages_label1, pages_label2, pages_label3)
        print(pages_label1, pages_label2, pages_label3, max_pages)

        for page in range(max_pages):
            if pages_label1 > 1:
                label1.verticalScrollBar().setValue(int(min(page, pages_label1 - 1) * label1.verticalScrollBar().maximum() / (pages_label1 - 1)))
            else:
                label1.verticalScrollBar().setValue(0)

            if pages_label2 > 1:
                label2.verticalScrollBar().setValue(int(min(page, pages_label2 - 1) * label2.verticalScrollBar().maximum() / (pages_label2 - 1)))
            else:
                label2.verticalScrollBar().setValue(0)

            if pages_label3 > 1:
                label3.verticalScrollBar().setValue(int(min(page, pages_label3 - 1) * label3.verticalScrollBar().maximum() / (pages_label3 - 1)))
            else:
                label3.verticalScrollBar().setValue(0)

            QApplication.processEvents()

            image_file = _images_path + f'pdf_info_label_{image_id}.png'
            image = self.grab()
            image.save(image_file)
            image_files.append(image_file)
            image_id += 1

        return image_id

    def save_as_pdf(self, pdf_file_name=None):
        """
            Save the displayed chart as a pdf
            Choose a file from file save dialog displayed
        """
        image_prefix = 'pdf_grb_'
        image_ext = '.png'

        if pdf_file_name is None:
            path = QFileDialog.getSaveFileName(self, 'Choose folder and file to save as PDF file', './output', 'PDF files (*.pdf)')
            pdf_file_name = path[0]

        image_files = []
        combined_image_files = []
        image_id = 1

        def __save_scrollable_list_widget_as_image(widget: QWidget, image_id, image_files, _row_steps=1, widget_is_combo=False, row_count_size=None):
            _sleep_time = 0.01
            scroll_tab_count = 0
            import time
            row_count = widget.count() if row_count_size is None else row_count_size

            for row in range(0, row_count, _row_steps):
                self._hide_show_even_odd_pages(image_id)
                if widget_is_combo:
                    widget.setCurrentIndex(row)
                    if widget == self._dhasa_combo:
                        self._dhasa_type_selection_changed()
                else:
                    widget.setCurrentRow(row)

                image_file = _images_path + image_prefix + str(image_id) + image_ext
                time.sleep(_sleep_time)
                im = self.grab()
                im.save(image_file)
                image_files.append(image_file)
                image_id += 1
                scroll_tab_count += 1

            return image_id

        if pdf_file_name:
            self._hide_show_layout_widgets(self._row2_h_layout, False)

            image_id = self._save_info_labels_by_click_scroll(image_id, image_files)
            self._reset_all_ui()

            ci = 1
            for i in range(0, len(image_files), _IMAGES_PER_PDF_PAGE):
                combined_image_file = _images_path + 'combined_' + str(ci) + image_ext
                _combine_multiple_images(image_files[i:i + 2], combined_image_file)
                combined_image_files.append(combined_image_file)
                ci += 1

            with open(pdf_file_name, "wb") as f:
                f.write(img2pdf.convert(combined_image_files))

        for image_file in image_files + combined_image_files:
            if os.path.exists(image_file):
                os.remove(image_file)

    def _reset_all_ui(self):
        self._hide_show_layout_widgets(self._row1_h_layout, True)
        self._hide_show_layout_widgets(self._row2_h_layout, True)
        self._footer_label.show()
        for t in range(self.tabCount):
            self.tabWidget.setTabVisible(t, True)

    def _hide_show_even_odd_pages(self, image_id):
        if image_id % 2 == 0:
            self._hide_show_layout_widgets(self._row1_h_layout, False)
            self._hide_show_layout_widgets(self._row2_h_layout, False)
            self._footer_label.show()
        else:
            self._hide_show_layout_widgets(self._row1_h_layout, True)
            if image_id == 1:
                self._hide_show_layout_widgets(self._row2_h_layout, True)
            self._footer_label.hide()

    def _hide_show_layout_widgets(self, layout, show):
        for index in range(layout.count()):
            myWidget = layout.itemAt(index).widget()
            if show:
                myWidget.show()
            else:
                myWidget.hide()

    def exit(self):
        self.close()
        QApplication.quit()
        print('Application Closed')

    def _show_only_tab(self, t):
        for ti in range(self.tabCount):
            self.tabWidget.setTabVisible(ti, False)
            if t == ti:
                self.tabWidget.setTabVisible(ti, True)
        
def _index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return -1


def _combine_multiple_images(image_list, output_image, combine_mode='vertical', image_quality_in_pixels=100):
    total_width = 0
    total_height = 0
    max_width = 0
    max_height = 0
    ix = []

    for img in image_list:
        im = Image.open(img)
        size = im.size
        w = size[0]
        h = size[1]
        total_width += w
        total_height += h

        if h > max_height:
            max_height = h
        if w > max_width:
            max_width = w
        ix.append(im)

    if combine_mode.lower() == 'vertical':
        target = Image.new('RGB', (max_width, total_height))
    else:
        target = Image.new('RGB', (total_width, max_height))

    pre_w = 0
    pre_h = 0
    for img in ix:
        if combine_mode.lower() == 'vertical':
            target.paste(img, (pre_w, pre_h, pre_w + max_width, pre_h + img.size[1]))
            pre_h += img.size[1]
        else:
            target.paste(img, (pre_w, pre_h, pre_w + img.size[0], pre_h + img.size[1]))
            pre_w += img.size[0]

    target.save(output_image, quality=image_quality_in_pixels)


if __name__ == "__main__":
    def except_hook(cls, exception, traceback):
        print('exception called')
        sys.__excepthook__(cls, exception, traceback)

    sys.excepthook = except_hook
    import time
    start_time = time.time()
    from jhora import config
    #config.initialize_runtime(force_reload=True, silent=False)
    App = QApplication(sys.argv)

    chart = PanchangaWidget(
        show_vedic_digital_clock=True,
        show_vedic_analog_clock=True,
        show_local_clock=True,
        panchanga_update_minutes=1
    )
    chart.compute_horoscope()
    chart.show()
    print("Elapsed time to show",time.time()-start_time)
    sys.exit(App.exec())