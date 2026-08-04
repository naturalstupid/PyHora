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
import sys, os
from datetime import datetime
from PyQt6 import QtCore
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QPushButton, QCompleter, QMessageBox,
                            QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialog, QToolTip)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, pyqtSlot, QSize, QTimer, QStringListModel
from jhora.panchanga import drik, pancha_paksha, vratha
from jhora import utils, const
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor, QPen, QPixmap, QIcon, QKeyEvent
from jhora.ui.panchangam import PanchangaInfoDialog
from jhora.ui.place_widget import PlaceWidget
from jhora.panchanga.info import _get_tithi_dict_pair
from jhora.panchanga.hijri import islamic_lunar_date
#""" Uncomment/Comment as required 
vratha.load_festival_data(const._FESTIVAL_FILE)
#"""
_SHOW_MUHURTHA_OR_SHUBHA_HORA = 1 # 0=Muhurtha 1=Shubha Hora
nakshatra_icons = ['ashvini','bharani','kritthika','rohini','mrigashirsha','ardra','punarvasu','pushya','ashlesha',
        'magha','purva_phalguni','uttara_phalguni','hastha','chitra','swathi','vishaka','anuradha','jyeshta',
        'mula','purva_ashada','uttara_ashada','shravana','dhanishta','shatabisha','purva_bhadrapada','uttara_bhadrapada','revathi']
_festival_folder = os.path.abspath(const._IMAGES_PATH) + const._sep 
_sunrise_icon = os.path.abspath(const._IMAGES_PATH) + const._sep + "sunrise1.png"
_sunset_icon = os.path.abspath(const._IMAGES_PATH) + const._sep + "sunset1.png"
_tithi_icons = {k:_festival_folder+ti+'.png' for k,ti in {3:'third_crescent',8:'ashtami',9:'navami',15:'pournami',
                23:'ashtami',24:'navami',30:'amavasai'}.items()}
_shukla_paksha_icon = os.path.abspath(const._IMAGES_PATH) + const._sep + "shukla_paksha.png"
_krishna_paksha_icon = os.path.abspath(const._IMAGES_PATH) + const._sep + "krishna_paksha.png"
_INFO_LABELS_HAVE_SCROLL = True
_info_label1_font_size = 6# if not _INFO_LABELS_HAVE_SCROLL else 6
_info_label2_font_size = 4.87 if (not _INFO_LABELS_HAVE_SCROLL or _SHOW_MUHURTHA_OR_SHUBHA_HORA==1) else 5
_info_label3_font_size = 4.87 if not _INFO_LABELS_HAVE_SCROLL else 6
_ICON_SIZE_SMALL = 12
_ICON_SIZE_MEDIUM = 18
_ICON_SIZE_ZOOM = 32
_TOOLTIP_ZOOM_OFFSET = 10

# New center-icon layout tuning
_CENTER_ICON_WIDTH_FRACTION = 0.35   # use 75% of cell width for center icons
_CENTER_ICON_GAP_FRACTION = 0.05     # gap between icons = 12% of icon size
_CENTER_ICON_MIN_SIZE = 8            # never smaller than this
_CENTER_ICON_MAX_SIZE = 16           # regular max size in center row
_CENTER_ICON_ZOOM_MAX = 24           # hover zoom max for center icons

_top_left_font_size = 9; _top_right_font_size = 9
_bottom_left_font_size = 9; _bottom_right_font_size = 9
_center_left_font_size = 12; _center_right_font_size = 16
_calendar_cell_width = 100
_calendar_cell_height = 80 
_label_offset_x = 2; _label_offset_y = 1
_info_label1_width = 275
_HEADER_CELL_HEIGHT = 20; _HEADER_COLOR='green'
_HEADER_LABEL_HEIGHT = 50; _HEADER_LABEL_COLOR = 'maroon'
_KEY_COLOR = 'brown'; _VALUE_COLOR = 'blue'
_KEY_LENGTH=50; _VALUE_LENGTH=200; _HEADER_LENGTH=100
_HEADER_FORMAT_ = '<b><span style="color:'+_HEADER_COLOR+';">{:.'+str(_HEADER_LENGTH)+'}</span></b><br>'
_KEY_VALUE_FORMAT_ = '<span style="color:'+_KEY_COLOR+';">{:.'+str(_KEY_LENGTH)+'}</span><span style="color:'+\
        _VALUE_COLOR+';">{:.'+str(_VALUE_LENGTH)+'}</span><br>'
previous_month_color = "orange"; default_color = "lightyellow"
input_day_color = "lightgreen"; next_month_color = "lightblue"
_top_left_label_color = 'magenta'; _top_right_label_color = 'blue'
_middle_left_label_color = 'red'; _middle_right_label_color = 'black'
_bottom_left_label_color = 'green'; _bottom_right_label_color = 'blue'
_cell_border_line_color = 'brown'; _cell_border_line_thickness = 1
_SKIP_LAST_BUT_LINES = 0
class CustomLabel(QLabel):
    clicked = pyqtSignal()

    # class-level pixmap cache: (icon_path, size) -> QPixmap
    _pixmap_cache = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.icon_tooltips = []
        self.texts = {}
        self.hovered_icon_rect = None

        self.font_sizes = {
            "top_left": _top_left_font_size, "top_right": _top_right_font_size,
            "middle_left": _center_left_font_size, "middle_right": _center_right_font_size,
            "bottom_left": _bottom_left_font_size, "bottom_right": _bottom_right_font_size,
            "center": _center_right_font_size
        }
        self.colors = {
            "top_left": QColor(_top_left_label_color), "top_right": QColor(_top_right_label_color),
            "middle_left": QColor(_middle_left_label_color), "middle_right": QColor(_middle_right_label_color),
            "bottom_left": QColor(_bottom_left_label_color), "bottom_right": QColor(_bottom_right_label_color),
            "center": QColor(_middle_right_label_color),
        }
        self.setStyleSheet("border: " + str(_cell_border_line_thickness) + "px solid " + _cell_border_line_color + ";")

    @classmethod
    def _get_scaled_pixmap(cls, icon_path: str, icon_size: int):
        if not icon_path:
            return QPixmap()

        key = (icon_path, icon_size)
        if key not in cls._pixmap_cache:
            cls._pixmap_cache[key] = QPixmap(icon_path).scaled(
                icon_size, icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return cls._pixmap_cache[key]

    def set_texts(self, text_pos):
        self.texts = text_pos
        self.update()

    def paintEvent(self, event):
        self.icon_tooltips.clear()
        try:
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QColor(Qt.GlobalColor.black))

            for pos, value in self.texts.items():
                alignment = self.get_alignment(pos)
                cell_width = self.width() // 2
                cell_height = self.height() // 3
                cell_x = (0 if 'left' in pos else self.width() // 2)
                cell_y = (0 if 'top' in pos else self.height() // 3 if 'middle' in pos else 2 * self.height() // 3)
                cell_y = self.height() // 2 if 'center' in pos else cell_y

                text_rect = QRect(cell_x, cell_y, cell_width, cell_height)
                rect = QRect(cell_x + _label_offset_x, cell_y + _label_offset_y,
                             text_rect.width() - _label_offset_x, text_rect.height() - _label_offset_y)

                font = painter.font()
                font_size = self.font_sizes.get(pos, 9)
                pen_color = self.colors.get(pos, QColor('black'))
                painter.setPen(pen_color)
                font.setPointSizeF(font_size)
                font.setBold(True)
                painter.setFont(font)

                if pos == "center" and isinstance(value, list):
                    items = value[:8]   # hard cap safety if you want max 8 icons
                    icon_count = len(items)
                
                    start_x, start_y, base_size, gap, _band_w = self._center_icon_layout(icon_count)
                
                    icon_x = start_x
                
                    for item in items:
                        if isinstance(item, tuple):
                            icon_path, text, *tooltip = item
                            tooltip = tooltip[0] if tooltip else ''
                        else:
                            icon_path, text, tooltip = '', str(item), ''
                
                        icon_rect = QRect(icon_x, start_y, base_size, base_size)
                
                        hovered = self.hovered_icon_rect and self.hovered_icon_rect.contains(icon_rect.center())
                        if hovered:
                            zoom_size = min(_CENTER_ICON_ZOOM_MAX, int(base_size * 1.35))
                            zoom_y = start_y - max(0, (zoom_size - base_size) // 2)
                            icon_rect = QRect(icon_x, zoom_y, zoom_size, zoom_size)
                            icon_size = zoom_size
                        else:
                            icon_size = base_size
                
                        icon = self._get_scaled_pixmap(icon_path, icon_size)
                        painter.drawPixmap(icon_rect, icon)
                
                        if tooltip:
                            self.icon_tooltips.append((QRect(icon_rect), tooltip))
                
                        icon_x += base_size + gap
                
                    # no text in center area, icons only
                    painter.drawText(rect, int(alignment), "")
                else:
                    if isinstance(value, tuple):
                        if len(value) == 3:
                            icon_path, text, tooltip = value
                        elif len(value) == 2:
                            icon_path, text = value
                            tooltip = ''
                        else:
                            icon_path, text = '', str(value)
                            tooltip = ''

                        icon_size = _ICON_SIZE_MEDIUM if 'center' in pos else _ICON_SIZE_SMALL
                        icon_height = int(0.8 * self.height()) if 'bottom' in pos else cell_y
                        icon_rect = QRect(cell_x, icon_height, icon_size, icon_size)

                        if self.hovered_icon_rect and self.hovered_icon_rect.contains(icon_rect.center()):
                            icon_size = _ICON_SIZE_ZOOM
                            icon_rect.setSize(QSize(icon_size, icon_size))

                        icon = self._get_scaled_pixmap(icon_path, icon_size)
                        painter.drawPixmap(icon_rect, icon)
                        rect.setLeft(icon_rect.right())
                        if tooltip:
                            self.icon_tooltips.append((QRect(icon_rect), tooltip))
                    else:
                        text = value
                    painter.drawText(rect, int(alignment), str(text))

                painter.setPen(QPen())
            painter.end()
        except Exception as e:
            print(f"VedicCalendar: CustomLabel paintEvent - An error occurred: {e}")
    def _center_icon_layout(self, icon_count: int, hovered_index: int = -1):
        """
        Compute center-band layout for festival icons.
    
        Rules:
        - reserve 75% of the cell width for center icons
        - center the band horizontally
        - fit all icons inside the band
        - keep icons within the middle row height
        """
        cell_w = max(1, self.width())
        cell_h = max(1, self.height())
        row_h = max(1, cell_h // 3)
    
        band_w = max(24, int(cell_w * _CENTER_ICON_WIDTH_FRACTION))
        band_x = (cell_w - band_w) // 2
        band_y = row_h
    
        icon_count = max(1, icon_count)
    
        # Start with a size limited by row height and band width
        # width budget includes gaps
        # n*size + (n-1)*gap <= band_w
        # use gap proportional to icon size
        size_from_height = int(row_h * 0.70)
        size_from_width = int(band_w / (icon_count + max(0, icon_count - 1) * _CENTER_ICON_GAP_FRACTION))
    
        icon_size = min(size_from_height, size_from_width, _CENTER_ICON_MAX_SIZE)
        icon_size = max(_CENTER_ICON_MIN_SIZE, icon_size)
    
        gap = max(2, int(icon_size * _CENTER_ICON_GAP_FRACTION))
    
        total_w = icon_count * icon_size + (icon_count - 1) * gap
    
        # If still too wide, shrink one more time
        if total_w > band_w:
            icon_size = max(_CENTER_ICON_MIN_SIZE, (band_w - (icon_count - 1) * gap) // icon_count)
            gap = max(1, int(icon_size * _CENTER_ICON_GAP_FRACTION))
            total_w = icon_count * icon_size + (icon_count - 1) * gap
    
        start_x = band_x + max(0, (band_w - total_w) // 2)
        start_y = band_y + max(0, (row_h - icon_size) // 2)
    
        return start_x, start_y, icon_size, gap, band_w

    def get_alignment(self, pos):
        if "top" in pos:
            vertical = Qt.AlignmentFlag.AlignTop
        elif "bottom" in pos:
            vertical = Qt.AlignmentFlag.AlignBottom
        else:
            vertical = Qt.AlignmentFlag.AlignVCenter

        if "left" in pos:
            horizontal = Qt.AlignmentFlag.AlignLeft
        elif "right" in pos:
            horizontal = Qt.AlignmentFlag.AlignRight
        else:
            horizontal = Qt.AlignmentFlag.AlignHCenter

        return horizontal | vertical

    def mouseMoveEvent(self, event):
        try:
            hovered = None
            for rect, tooltip in self.icon_tooltips:
                if rect.contains(event.pos()):
                    hovered = rect
                    tooltip_pos = event.globalPosition().toPoint() + QPoint(_TOOLTIP_ZOOM_OFFSET, _TOOLTIP_ZOOM_OFFSET)
                    QToolTip.showText(tooltip_pos, tooltip, self)
                    break
            else:
                QToolTip.hideText()

            if hovered != self.hovered_icon_rect:
                self.hovered_icon_rect = hovered
                self.update()
        except Exception as e:
            print(f"mouseMoveEvent error: {e}")

    def leaveEvent(self, event):
        self.hovered_icon_rect = None
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

class VedicCalendar(QWidget):
    def __init__(self,start_date:drik.Date=None,place:drik.Place=None, language=None,use_purnimanta_system=None,
                 use_world_city_database=None,
                 use_internet_for_location_check=None,
                 ayanamsa_mode=None):
        """
            @param use_purnimanta_system: None => Solar Calendar, False=>Amantha, True=>Purnimantha 
        """
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)        
        self._day_info_cache = {}
        self._info_label_cache = {}
        self._last_ui_language = None
        
        use_world_city_database = (
            const.check_database_for_world_cities if use_world_city_database is None
            else use_world_city_database
        )
        use_internet_for_location_check = (
            const.use_internet_for_location_check if use_internet_for_location_check is None
            else use_internet_for_location_check
        )
        self._ayanamsa_mode = ( ayanamsa_mode 
                                if ayanamsa_mode is not None and ayanamsa_mode in const.available_ayanamsa_modes.keys()
                                else const._DEFAULT_AYANAMSA_MODE
                                )
        drik.set_ayanamsa_mode(self._ayanamsa_mode)
        self._language = const.reverse_languages[const._DEFAULT_LANGUAGE] if language is None else language
        self.use_world_city_database = use_world_city_database
        utils.set_language(const.available_languages[self._language])
        utils.use_database_for_world_cities(self.use_world_city_database)
        self.use_internet_for_location_check = use_internet_for_location_check
        self._use_purnimanta_system = use_purnimanta_system
        self.res = utils.resource_strings
        self._elevation = 0.0
        self.start_date = start_date; self.start_place=place
        self.selected_cell = None; self.previous_month_cell=None; self.next_month_cell=None
        self.setWindowTitle(self.res['calendar_str']+' '+const._APP_VERSION)
        self.setWindowIcon(QIcon(const._IMAGE_ICON_PATH))
        self.setMinimumSize(900, 650)
        self.col_min = 0; self.row_min = 0; self.col_max = 6; self.row_max = 6
        self.initUI()
        self.showMaximized()
        self.setFocus()
    def _calendar_cache_key(self, jd):
        return (
            round(float(jd), 6),
            self._place_text.text().strip(),
            self._lat_text.text().strip(),
            self._long_text.text().strip(),
            self._tz_text.text().strip(),
            self._language,
            self._calendar_combo.currentIndex(),
            self._use_purnimanta_system,
            self._ayanamsa_mode,
        )

    def _clear_calendar_caches(self):
        self._day_info_cache.clear()
        self._info_label_cache.clear()
        
    def initUI(self):
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        if self.start_date is None:
            current_date_str = datetime.now().strftime('%Y,%m,%d')
        else:
            year,month,day = self.start_date
            current_date_str = str(year)+','+str(month)+','+str(day)
        self.date_text = QLineEdit(self)
        self.date_text.setText(current_date_str)
        self.date_text.editingFinished.connect(self.computeCalendar)
        if self.start_place is None and self.use_internet_for_location_check:
            loc = utils.get_place_from_user_ip_address()
            print('loc from IP address', loc)
            if len(loc) >= 4:
                print('setting values from loc')
                elev = float(loc[4]) if len(loc) >= 5 else 0.0
                self._elevation = elev
                self.start_place = drik.Place(loc[0], loc[1], loc[2], loc[3], elev)
        self._place_name = ''
        self._elevation = 0.0
        self._place_widget = PlaceWidget(
            self,
            initial_text=self._place_name,
            placeholder_text="Enter place of birth, country name",
            tooltip_text="Enter place of birth, country name",
            min_chars=2,
            debounce_ms=150
        )
        
        self._place_text = self._place_widget.lineEdit()
        self._place_widget.textEditedSignal.connect(self._resize_place_text_size)
        self._place_widget.placeSelected.connect(self._get_location)
        self._place_text.setToolTip('Enter place of birth, country name')
        self._lat_text = QLineEdit(self)
        self._long_text = QLineEdit(self)
        self._tz_text = QLineEdit(self)
        if isinstance(self.start_place,drik.Place):
            self._place_text.setText(self.start_place.name)
            self._lat_text.setText(str(self.start_place.latitude))
            self._long_text.setText(str(self.start_place.longitude))
            self._tz_text.setText(str(self.start_place.timezone))
        self._dob_label = QLabel('Date:')
        input_layout.addWidget(self._dob_label)
        input_layout.addWidget(self.date_text)
        self._place_label = QLabel('Place Name:')
        input_layout.addWidget(self._place_label)
        input_layout.addWidget(self._place_widget, 1)
        self._lat_label = QLabel('Latitude:')
        input_layout.addWidget(self._lat_label)
        self._lat_text.setMaximumWidth(90)
        input_layout.addWidget(self._lat_text)
        self._long_label = QLabel('Longitude:')
        input_layout.addWidget(self._long_label)
        self._long_text.setMaximumWidth(90)
        input_layout.addWidget(self._long_text)
        self._tz_label = QLabel('TimeZone Hours:')
        input_layout.addWidget(self._tz_label)
        self._tz_text.setMaximumWidth(70)
        input_layout.addWidget(self._tz_text)
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(const.available_languages.keys())
        self._lang_combo.setCurrentText(self._language)
        self._lang_combo.activated.connect(self._change_language)
        self._lang_combo.setToolTip('Choose language for display')
        input_layout.addWidget(self._lang_combo)
        self._calendar_combo = QComboBox()
        _calendar_list = [self.res[s]+' '+self.res['calendar_str'] for s in ['solar_str','amantha_str','purnimantha_str']]
        if const.include_islamic_calendar: _calendar_list += [self.res['hijri_str']+' '+self.res['calendar_str']]
        self._calendar_combo.addItems(_calendar_list)
        self._calendar_combo.activated.connect(self._change_calendar_type)#self._change_language)
        _calendar_index = const.CALENDAR_TYPE.SOLAR
        self._calendar_combo.setCurrentIndex(_calendar_index)
        input_layout.addWidget(self._calendar_combo)
        self.compute_btn = QPushButton(self.res['calendar_str'], self)
        self.compute_btn.clicked.connect(self.computeCalendar)
        input_layout.addWidget(self.compute_btn)

        main_layout.addLayout(input_layout)

        h_layout = QHBoxLayout()
        self._info_label1 = QLabel("Information:")
        self._info_label1.setFixedWidth(_info_label1_width)
        self._info_label1.setStyleSheet("border: 1px solid black; font-size: "+str(_info_label1_font_size)+" pt")
        # Use setTextFormat and setTextInteractionFlags to make the link clickable
        self._info_label1.setTextFormat(Qt.TextFormat.RichText)
        self._info_label1.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._info_label1.setOpenExternalLinks(False)  # Disable opening links in the default browser
        h_layout.addWidget(self._info_label1)
        v_layout = QVBoxLayout()
        self.header_label = QLabel('')
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("border: 1px solid black; font-weight: bold; font-size: "+str(12)+"pt")
        self.header_label.setFixedHeight(_HEADER_LABEL_HEIGHT)
        v_layout.setSpacing(0); v_layout.setContentsMargins(0,0,0,0)
        v_layout.addWidget(self.header_label)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.cells = []; self.jd = []

        headers = ['<b><span style="color:'+_HEADER_COLOR+';">'+str(h)+'</span></b>' for h in utils.DAYS_SHORT_NAMES]
        self.day_labels = ['' for _ in utils.DAYS_SHORT_NAMES]
        for col, header in enumerate(headers):
            self.day_labels[col] = QLabel(header)
            self.day_labels[col].setFixedHeight(_HEADER_CELL_HEIGHT)  # Set a fixed height for the header
            self.day_labels[col].setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the text
            _cell_style = "border: "+str(_cell_border_line_thickness)+"px solid "+_cell_border_line_color+";"
            self.day_labels[col].setStyleSheet(_cell_style)
            self.grid_layout.addWidget(self.day_labels[col], 0, col)

        for row in range(1, 8):
            week = []; jd_week = []
            for col in range(7):
                cell = CustomLabel(self)
                cell.setMinimumSize(_calendar_cell_width, _calendar_cell_height)
                cell.setVisible(False)
                cell.clicked.connect(lambda r=row, c=col: self.cell_clicked(r, c))
                self.grid_layout.addWidget(cell, row, col)
                week.append(cell); jd_week.append(None)
            self.cells.append(week); self.jd.append(jd_week)

        v_layout.addLayout(self.grid_layout)
        h_layout.addLayout(v_layout)
        main_layout.addLayout(h_layout)
        self.move(50,50)
        self.setLayout(main_layout)
        self.computeCalendar()
    def keyPressEvent(self, event: QKeyEvent):
        _DEBUG_ = False
        try:
            row_min = self.row_min; row_max = self.row_max; col_min = self.col_min; col_max = self.col_max
            def _check_if_valid_cell(next_cell):
                next_row,next_col = next_cell
                _, previous_month_col = self.previous_month_cell
                _, next_month_col = self.next_month_cell
                _invalid_cell = (next_row == row_min and next_col < previous_month_col) or \
                                (next_row == row_max and next_col > next_month_col) or \
                                (next_row < row_min or next_row > row_max) or \
                                (next_col < col_min or next_col > col_max)
                return not _invalid_cell
            current_row,current_col = self.selected_cell
            next_cell = self.selected_cell
            if event.key() == Qt.Key.Key_Up:
                next_cell = (current_row-1,current_col) if current_row != row_min else (row_max,current_col)
            elif event.key() == Qt.Key.Key_Down:
                next_cell = (current_row+1,current_col) if current_row != row_max else (row_min,current_col)
            elif event.key() == Qt.Key.Key_Left:
                next_cell = (current_row,current_col-1) if current_col != col_min else (current_row-1,col_max)
            elif event.key() == Qt.Key.Key_Right:
                next_cell = (current_row,current_col+1) if current_col != col_max else (current_row+1,col_min)
            else:
                super().keyPressEvent(event)
            if _check_if_valid_cell(next_cell):
                next_row,next_col = next_cell
                self.cell_clicked(next_row+1, next_col) 
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"VedicCalendar:keyEventPressed: - An error occurred: {e}",'line number',tb.tb_lineno)
    @pyqtSlot(str,float,object)
    def _on_show_more_link_clicked(self, link,jd, place):
        if link == "show_more":
            try:
                _info_dialog = QDialog(self) 
                _info_dialog.setWindowTitle(self.res['panchangam_str'])
                dialog_layout = QVBoxLayout()
                from jhora.ui import panchangam
                panchangam._SHOW_SPECIAL_TITHIS = True
                panchanga_widget = PanchangaInfoDialog(language=self._language,jd=jd,place=place,
                                                       info_labels_have_scroll=_INFO_LABELS_HAVE_SCROLL,
                                                       ayanamsa_mode=self._ayanamsa_mode)
                dialog_layout.addWidget(panchanga_widget)
                _info_dialog.setLayout(dialog_layout)
                #"""
                _info_dialog.setWindowFlags(
                    _info_dialog.windowFlags() | 
                    Qt.WindowType.WindowMinimizeButtonHint | 
                    Qt.WindowType.WindowMaximizeButtonHint | 
                    Qt.WindowType.WindowCloseButtonHint
                )
                _info_dialog.resize(800,600)#showFullScreen()
                _info_dialog.setModal(True)
                _info_dialog.exec()
            except Exception as e:
                tb = sys.exc_info()[2]
                print(f"VedicCalendar:_on_show_more_link_clicked: An error occurred: {e}",'line number',tb.tb_lineno)
    def _change_language(self):
        self._language = self._lang_combo.currentText()
        _calendar_index = self._calendar_combo.currentIndex()
        if _calendar_index == const.CALENDAR_TYPE.SOLAR:
            self._use_purnimanta_system = None
        elif _calendar_index ==const.CALENDAR_TYPE.LUNAR_AMANTHA:
            self._use_purnimanta_system = False
        elif _calendar_index ==const.CALENDAR_TYPE.LUNAR_PURNIMANTHA:
            self._use_purnimanta_system = True
        else: self._use_purnimanta_system = None
        utils.set_language(const.available_languages[self._language])
        self.res = utils.resource_strings
        self._clear_calendar_caches()
        self.setWindowTitle(self.res['calendar_str']+' '+const._APP_VERSION)
        self.computeCalendar()
        
    def _reshade_cells(self):
        for row in range(7):
            for col in range(7):
                cell = self.cells[row][col]
                if cell.isVisible():
                    _cell_style = "border: "+str(_cell_border_line_thickness)+"px solid "+_cell_border_line_color+"; "
                    if (row,col)==self.selected_cell:
                        _cell_style +=  f"background-color: {input_day_color}"
                    elif (row,col)==self.previous_month_cell:
                        _cell_style +=  f"background-color: {previous_month_color}"
                    elif (row,col)==self.next_month_cell:
                        _cell_style +=  f"background-color: {next_month_color}"
                    else:
                        _cell_style +=  f"background-color: {default_color}"
                    cell.setStyleSheet(_cell_style)
    def _resize_place_text_size(self):
        return

    def _get_location(self, place_name):
        result = utils.get_location(place_name)
        if result:
            self._place_name, self._latitude, self._longitude, self._time_zone,self._elevation = result
            self._place_text.setText(self._place_name)
            self._lat_text.setText(str(self._latitude))
            self._long_text.setText(str(self._longitude))
            self._tz_text.setText(str(self._time_zone))
        else:
            msg = place_name + " could not be found in OpenStreetMap.\nTry entering latitude and longitude manually.\nOr try entering nearest big city"
            print(msg)
            QMessageBox.about(self, "City not found", msg)
            self._lat_text.setText('')
            self._long_text.setText('')
        self._resize_place_text_size()

    def _get_days_panchanga_info(self,row,col):
        jd = self.jd[row][col]
        if jd is None: return None,""
        cache_key = self._calendar_cache_key(jd)
        cached = self._day_info_cache.get(cache_key)
        if cached is not None:
            return cached
        place = self.start_place; y,m,d,_ = utils.jd_to_gregorian(jd); date_in = drik.Date(y,m,d)
        _tithi_returned = drik.tithi(jd, place); _tit = _tithi_returned[0]
        _,_tithi_value,_paksha = _get_tithi_dict_pair(_tithi_returned,jd)
        if _tit in _tithi_icons:
            _tithi_icon = _tithi_icons[_tit]
        elif len(_tithi_returned) > 3 and _tithi_returned[3] in _tithi_icons:
            _tithi_icon = _tithi_icons[_tithi_returned[3]]
        else:
            _tithi_icon = ''
        _tithi = utils.TITHI_SHORT_LIST[_tit-1]
        kp_icon = _shukla_paksha_icon if _paksha==0 else  _krishna_paksha_icon
        _srise = utils.to_dms(drik.sunrise(jd, place)[0],round_to_minutes=True).strip()
        _sset = utils.to_dms(drik.sunset(jd, place)[0],round_to_minutes=True).strip()
        _naks = drik.nakshatra(jd, place); _nak_id = _naks[0]
        _nak = utils.NAKSHATRA_SHORT_LIST[_nak_id-1]
        _lang = const.available_languages[self._language]
        tm = None; td = None; adhik_maasa = None; _vaara = drik.vaara(jd,place)+1
        if self._calendar_combo.currentIndex()==const.CALENDAR_TYPE.SOLAR:
            tm,td = drik.tamil_solar_month_and_date_from_jd(jd, place)
            day_str = str(td)
            spl_month_text = utils.MONTH_LIST[tm]+' '+day_str+ ' ('+self.res['solar_str']+')'
            _samvatsara = drik.samvatsara(date_in, place, zodiac=0)
            year_str = utils.YEAR_LIST[_samvatsara]
        elif self._calendar_combo.currentIndex()==const.CALENDAR_TYPE.HIJRI_ISLAMIC:
            ty,tm,td = islamic_lunar_date(jd, place)
            day_str= str(td)+'*'
            spl_month_text = utils.ISLAMIC_MONTH_LIST[tm-1]+' '+day_str+ ' ('+self.res['hijri_str']+')'
            year_str = '('+str(ty)+')'
        else:
            tm,td,_lunar_year,adhik_maasa,nija_maasa = drik.lunar_month_date(jd,place,
                                                    use_purnimanta_system=self._use_purnimanta_system)
            day_str = str(td)
            tm -= 1
            adhik_maasa_str = ''; 
            if adhik_maasa:
                adhik_maasa_str = self.res['adhika_maasa_str']
            """ Check if current month is Nija Maasa """
            nija_month_str = ''
            if nija_maasa:
                nija_month_str = self.res['nija_month_str']
            _lmonth_str= ' ('+self.res['purnimantha_str']+')' if self._use_purnimanta_system else  ' ('+self.res['amantha_str']+')'
            spl_month_text = utils.MONTH_LIST[tm]+' '+ adhik_maasa_str+nija_month_str+' '+day_str+_lmonth_str
            year_str = utils.YEAR_LIST[_lunar_year]
        calendar_type = self._calendar_combo.currentIndex()
        _festival_list = vratha.get_festivals_of_the_day(jd,place)
        fest_icon = ''; fest_ttip = ''
        fest_list = []
        if len(_festival_list) >0:
            for f_row in _festival_list:
                fest_icon = _festival_folder+f_row['icon_file']
                fest_ttip = f_row['Festival_'+const.available_languages[self._language]]
                fest_list.append((fest_icon,'',fest_ttip))
        kp_ttip = _tithi_value
        nak_ttip = utils.NAKSHATRA_LIST[_naks[0]-1]+' '+  \
                        ' ('+utils.PLANET_SHORT_NAMES[utils.nakshathra_lord(_naks[0])]+') '+ self.res['paadham_str']+\
                        str(_naks[1]) + ' '+ utils.to_dms(_naks[3]) + ' ' + self.res['ends_at_str']
        if _naks[3] < 24:
            _next_nak = (_naks[0])%27+1
            nak_ttip += '\n'+self.res['after_str']+' '+ utils.NAKSHATRA_LIST[_next_nak-1]+' '+  \
                        ' ('+utils.PLANET_SHORT_NAMES[utils.nakshathra_lord(_next_nak)]+') '
        nak_icon = _festival_folder+nakshatra_icons[_nak_id-1]+'.png'
        #print('calendar type',self._calendar_combo.currentIndex(),spl_month_text,'month',tm,'day',td)
        _panchanga_dict = {
            'top_left': (kp_icon, _tithi, kp_ttip),
            'middle_left': (_tithi_icon, day_str, utils.TITHI_LIST[_tit-1] if _tit in _tithi_icons.keys() else ''),
            'middle_right': ('',str(d)),
            'center':fest_list,#[(fest_icon,'',fest_ttip),(fest_icon,'',fest_ttip),(fest_icon,'',fest_ttip)],
            'bottom_left': (nak_icon, _nak,nak_ttip),
            'top_right': (_sunrise_icon, _srise, self.res['sunrise_str']+' '+str(_srise)),
            'bottom_right': (_sunset_icon, _sset, self.res['sunset_str']+' '+str(_sset))
        }
        header_text = year_str+' '+str(y)+' '+ utils.MONTH_LIST_EN[m-1]+' '+str(d)+' '+utils.DAYS_LIST[drik.vaara(jd,place)]+' '+\
                      spl_month_text+' '+ utils.PAKSHA_LIST[_paksha]+' ' + \
                      utils.TITHI_LIST[_tit-1]
        result = (_panchanga_dict, header_text)
        self._day_info_cache[cache_key] = result
        return result
    def _update_resources(self):
        msgs = self.res
        self._dob_label.setText(msgs['date_of_birth_str'])
        self._dob_label.setToolTip(msgs['dob_tooltip_str'])
        self._place_label.setText(msgs['place_str'])
        self._place_label.setToolTip(msgs['place_tooltip_str'])
        self._lat_label.setText(msgs['latitude_str'])
        self._lat_label.setToolTip(msgs['latitude_tooltip_str'])
        self._long_label.setText(msgs['longitude_str'])
        self._long_label.setToolTip(msgs['longitude_tooltip_str'])
        self._tz_label.setText(msgs['timezone_offset_str'])
        self._tz_label.setToolTip(msgs['timezone_tooltip_str'])
        self.compute_btn.setText(msgs['calendar_str'])
        _calendar_list = [self.res[s]+' '+self.res['calendar_str'] for s in ['solar_str','amantha_str','purnimantha_str']]
        if const.include_islamic_calendar: _calendar_list += [self.res['hijri_str']+' '+self.res['calendar_str']]
        _cal_index = self._calendar_combo.currentIndex()
        self._calendar_combo.clear()
        self._calendar_combo.addItems(_calendar_list)
        self._calendar_combo.setCurrentIndex(_cal_index)
    def _change_calendar_type(self):
        _calendar_index = self._calendar_combo.currentIndex()
        if _calendar_index == 0:
            self._use_purnimanta_system = None
        elif _calendar_index == 1:
            self._use_purnimanta_system = False
        else:
            self._use_purnimanta_system = True
        self._clear_calendar_caches()
        self.computeCalendar()
    def computeCalendar(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.setUpdatesEnabled(False)
            self._update_resources_if_needed()
            date_str = self.date_text.text()
            place_name = self._place_text.text()
            latitude = float(self._lat_text.text())
            longitude = float(self._long_text.text())
            timezone = float(self._tz_text.text())
            year, month, day = utils.get_year_month_day_from_date_format(date_str)#map(int,date_str.split(","))#
            selected_date = drik.Date(year,month,day)
            _jd = utils.julian_day_number((year, month, 1), (10, 0, 0))
            tz_hours = ( utils.get_place_timezone_offset(latitude, longitude, _jd)
                         if const.apply_daylight_savings_correction else timezone)
            self._tz_text.setText(str(tz_hours))
            self.start_place = drik.Place(place_name, latitude, longitude, timezone,self._elevation)
            sunrise_hours = drik.sunrise(_jd,self.start_place)[0]
            _jd = utils.julian_day_number((year, month, 1), (sunrise_hours, 0, 0))
            first_day = drik.Date(year, month, 1)
            previous_month_end = utils.previous_panchanga_day(first_day, minus_days=1)
            if month == 12:
                last_day = 31
                next_month_start = drik.Date(year+1,1,1)
            else:
                last_day = utils.next_panchanga_day(drik.Date(year,(month+1)%13,1), -1)
                next_month_start = utils.next_panchanga_day(last_day, add_days=1)
                last_day = last_day.day
            _jd -= 1; current_date = previous_month_end
            start_day = drik.vaara(_jd,self.start_place)+1
            reached_end_of_month = False
            [self.cells[row][col].setVisible(False) for col in range(7) for row in range(7)]
            _,current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
            hh,mm,ss = current_time_str.split(":")
            for row in range(7):
                for col in range(7):
                    cell = self.cells[row][col]
                    cell.clear()
                    if reached_end_of_month:
                        break
                    if row * 7 + col >= start_day:
                        _year,_month,_day,_ = utils.jd_to_gregorian(_jd)
                        _jd = utils.julian_day_number((_year, _month, _day), (int(hh), int(mm), int(ss)))
                        self.jd[row][col]=_jd; self.row_max = row
                        cell.setVisible(True)
                        panchanga_dict,_ = self._get_days_panchanga_info(row,col)
                        if panchanga_dict is not None: cell.set_texts(panchanga_dict)
                        _cell_style = "border: "+str(_cell_border_line_thickness)+"px solid "+_cell_border_line_color+"; "
                        if current_date == selected_date:
                            _cell_style += f"background-color: {input_day_color}"
                            self.selected_cell = (row+1,col)
                        elif current_date == previous_month_end:
                            _cell_style += f"background-color: {previous_month_color}"
                            self.previous_month_cell = (row,col)
                        elif current_date == next_month_start:
                            _cell_style += f"background-color: {next_month_color}"
                            self.next_month_cell = (row,col)
                        else:
                            _cell_style += f"background-color: {default_color}"
                        cell.setStyleSheet(_cell_style)
                            
                        reached_end_of_month = (current_date == next_month_start)
                        current_date = utils.next_panchanga_day(current_date, add_days=1)
                        _jd += 1
            if self.selected_cell is not None:
                self.cell_clicked(self.selected_cell[0], self.selected_cell[1])
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"VedicCalendar:computeCalendar: An error occurred:\n{tb}")
        finally:
            self.setUpdatesEnabled(True)
            self.update()
            QApplication.restoreOverrideCursor()
    def cell_clicked(self,row,col):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.selected_cell = (row-1,col)
            jd = self.jd[row-1][col]; place = self.start_place
            self._reshade_cells()
            sep_str = '<br>'#'\n'
            info_list = self._fill_information_label1(jd,place).split(sep_str)
            info_list = utils.trim_info_list_lines(info_list,_SKIP_LAST_BUT_LINES)
            panchanga_dict,header_text = self._get_days_panchanga_info(row-1,col)
            self.cells[row-1][col].set_texts(panchanga_dict)
            self.header_label.setText('<b><span style="color:'+_HEADER_LABEL_COLOR+';">'+str(header_text)+'</span></b>')
            for c,day in enumerate(utils.DAYS_SHORT_NAMES):
                _cell_style = "border: "+str(_cell_border_line_thickness)+"px solid "+_cell_border_line_color+";"
                self.day_labels[c].setStyleSheet(_cell_style)
                self.day_labels[c].setText('<b><span style="color:'+_HEADER_COLOR+';">'+str(day)+'</span></b>')
            font = QFont(); font.setPointSizeF(_info_label1_font_size); self._info_label1.setFont(font)
            self._info_label1.setText(sep_str.join(info_list[:]))
            y,m,d,_ = utils.jd_to_gregorian(self.jd[row-1][col])
            self.date_text.setText(str(y)+','+str(m)+','+str(d))
            if self.selected_cell == self.previous_month_cell or self.selected_cell==self.next_month_cell:
                self.computeCalendar()
            # Grow-only so month navigation does not undo maximize / user resize.
            if not self.isMaximized():
                hint = self.minimumSizeHint()
                cur = self.size()
                self.resize(max(cur.width(), hint.width()), max(cur.height(), hint.height()))
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"VedicCalendar:cell_clicked: An error occurred: {e}",'line number',tb.tb_lineno)
        finally:
            QApplication.restoreOverrideCursor()
            self.setFocus(Qt.FocusReason.OtherFocusReason)
    def _update_resources_if_needed(self):
        if self._last_ui_language != self._language:
            self._update_resources()
            self._last_ui_language = self._language

    def _fill_information_label1(self, jd, place, show_more_link=True):
        try:
            cache_key = ("info_label",) + self._calendar_cache_key(jd)
            cached = self._info_label_cache.get(cache_key)
            if cached is None:
                from jhora.ui import panchangam
                panchangam._SHOW_SPECIAL_TITHIS = False
                cached = PanchangaInfoDialog._fill_information_label1(
                    self, show_more_link=False, jd=jd, place=place
                )
                self._info_label_cache[cache_key] = cached

            info_str = cached

            format_str = _KEY_VALUE_FORMAT_
            if show_more_link:
                info_str += format_str.format('<a href="show_more">Show more</a>', '')
                try:
                    self._info_label1.linkActivated.disconnect()
                except TypeError:
                    pass
                self._info_label1.linkActivated.connect(
                    lambda link: self._on_show_more_link_clicked(link, jd, place)
                )
            return info_str
        except Exception as e:
            tb = sys.exc_info()[2]
            print(f"An error occurred: {e}", 'line number', tb.tb_lineno)
if __name__ == '__main__':
    try:
        import time
        start_time = time.time()
        from jhora import config
        config.initialize_runtime(force_reload=True, silent=False)
        app = QApplication(sys.argv)
        #lang = 'English'
        _ayanamsa = "TRUE_PUSHYA"
        start_date = None; start_place = None
        ex = VedicCalendar(start_date=start_date,place=start_place,use_purnimanta_system=None,
                           ayanamsa_mode=_ayanamsa)
        ex.show()
        print('elapsed time',time.time()-start_time)
        sys.exit(app.exec())
    except Exception as e:
        print(f"An error occurred: {e}")
