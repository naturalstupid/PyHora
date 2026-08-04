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
    Module for Pancha Paksha Sastra UI
"""

import sys
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon, QFont, QFontMetrics, QColor, QMovie
from PyQt6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, \
                QLineEdit, QHBoxLayout,QLabel, QCompleter, QMessageBox, QPushButton, QComboBox, \
                QStyledItemDelegate, QProgressBar, QHeaderView
from PyQt6.QtCore import Qt, QDateTime, QRect, QTimer, QSize
from datetime import datetime
from jhora import utils, const
from jhora.panchanga import drik, pancha_paksha
from jhora.ui.place_widget import PlaceWidget

IMAGE_PATH = const._IMAGES_PATH + const._sep
_WEEK_DAY_INDEX = 0; _PAKSHA_INDEX = 1; _DAYNIGHT_INDEX = 2
_NAK_BIRD_INDEX = 3; _NAK_ACTIVITY_INDEX = 4; _SUB_BIRD_INDEX = 5; _SUB_ACTIVITY_INDEX = 6
_DURATION_FACTOR = 7; _RELATION = 8; _POWER_FACTOR=9;_EFFECT = 10; _RATING=11;
_PADU_PAKSHI = 12; _BHARANA_PAKSHI = 13
_LAST_COL_FOR_READING = _BHARANA_PAKSHI#_RELATION
_DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"  # Custom format string

_FROM_DATE_DISP = 0; _TO_DATE_DISP=1; _DURATION_DISP=2; _MAIN_BIRD_DISP=3;
_MAIN_ACT_DISP = 4; _SUB_BIRD_DISP = 5; _SUB_ACT_DISP = 6; _RELATION_DISP = 7; _POWER_FACTOR_DISP = 8
_EFFECT_DISP = 9; _RATING_DISP = 10

_DEFAULT_ICON_SIZE = 16
#Pancha Pakshi for each star (birth if sukla paksha, birth if in krishna paksha)
#1:Vulture 2:Owl, 3:Crow, 4:Cock, 5:Peacock
pancha_pakshi_birds = ['vulture','owl','crow','cock','peacock']
pancha_pakshi_images = ['vulture.png','owl.png','crow.png','cock.png','peacock.png']
pancha_pakshi_activities = ['ruling','eating','walking','sleeping','dying']
pp_activity_background_colors = ['dark green','yellow','light green','orange','red']
pp_relations = ['enemy','same','friend']; pp_relation_colors = ['orange','yellow','light green']
pp_effect = ['very_bad','bad','average','good','very_good']
pp_effect_colors = ['red','orange','yellow','light green','dark green']
pancha_pakshi_activity_images = [p+'.png' for p in pancha_pakshi_activities]
def set_treewidget_font_size(tree, font_size):
    font = tree.font()
    font.setPointSizeF(font_size)  # Set the desired font size

    # Set the font for the QTreeWidget
    tree.setFont(font)

    # Set the font for the header
    tree.header().setFont(font)

    # Dynamically set the font for all items in the QTreeWidget
    def set_item_font(item):
        for column in range(tree.columnCount()):
            item.setFont(column, font)
        for child_index in range(item.childCount()):
            set_item_font(item.child(child_index))

    for row_index in range(tree.topLevelItemCount()):
        set_item_font(tree.topLevelItem(row_index))

def format_cell_value(cell):
    """Helper function to format cell values by handling new lines in strings and tuples."""
    if isinstance(cell, str):
        return cell.replace('\\n', '\n')
    elif isinstance(cell, tuple):
        return tuple(format_cell_value(item) for item in cell)
    else:
        return str(cell)
def add_text_above_parent_row(tree, parent_level_labels=None):
    # Create an intermediate item to hold the custom widget
    intermediate_item = QTreeWidgetItem()
    intermediate_item.setFlags(intermediate_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

    # Create a QWidget to hold the custom layout
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    
    for (text,icon_path) in parent_level_labels:
        # Add QLabel to the layout
        label = QLabel(text)
        layout.addWidget(label)
        # Add icon if provided
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(IMAGE_PATH+icon_path).pixmap(_DEFAULT_ICON_SIZE, _DEFAULT_ICON_SIZE))
            layout.addWidget(icon_label)
    
    layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
    container.setLayout(layout)
    
    # Add the intermediate item with the custom widget to the tree
    tree.addTopLevelItem(intermediate_item)
    tree.setItemWidget(intermediate_item, 0, container)
        # Span the custom widget across all columns
    intermediate_item.setFirstColumnSpanned(True)

class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(Qt.BrushStyle.SolidPattern)
        text = self.model().headerData(logicalIndex, self.orientation(), Qt.ItemDataRole.DisplayRole)
        if text:
            text_rect = QRect(rect)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
class CustomDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)

        if not index.parent().isValid():  # Only draw border for parent items
            parent_index = index
            parent_rect = option.widget.visualRect(parent_index)
            rect = parent_rect

            # Calculate the rectangle encompassing all children
            for i in range(option.widget.model().rowCount(parent_index)):
                child_index = option.widget.model().index(i, 0, parent_index)
                child_rect = option.widget.visualRect(child_index)
                rect = rect.united(child_rect)

            # Draw the border around the combined area of parent and children
            painter.save()
            painter.setPen(QColor(0, 0, 0))
            painter.drawRect(rect)
            painter.restore()

class PanchaPakshiSastraWidget(QWidget):
    def __init__(self, birth_bird_index=None, headers=None, parent_level_list=None, child_level_list=None, hide_headers=True,
                 parent_level_labels=None,tree_font_size=9,expand_one_row_at_a_time=False,synch_with_local_clock=False,
                 synch_timer_frequency_in_minutes=1,
                 use_world_city_database=None,
                 use_internet_for_location_check=None,
                 ):
        super().__init__()
        use_world_city_database = (
            const.check_database_for_world_cities if use_world_city_database is None
            else use_world_city_database
        )
        use_internet_for_location_check = (
            const.use_internet_for_location_check if use_internet_for_location_check is None
            else use_internet_for_location_check
        )
        self.setWindowTitle(utils.resource_strings['pancha_pakshi_sastra_str'])
        self.setGeometry(50, 50, 800, 600)
        # Layout
        v_layout = QVBoxLayout()

        h_layout = QHBoxLayout()
        _dob_label = QLabel("Date:")
        h_layout.addWidget(_dob_label)
        self._dob_text = QLineEdit('')
        self._dob_text.setToolTip('Date in the format YYYY,MM,DD')
        _dob_label.setMaximumWidth(75)
        self._dob_text.setMaximumWidth(75)
        h_layout.addWidget(self._dob_text)
        _tob_label = QLabel("Time:")
        h_layout.addWidget(_tob_label)
        self._tob_text = QLineEdit('')
        self._tob_text.setToolTip('Enter time in the format HH:MM:SS if afternoon use 12+ hours')
        _tob_label.setMaximumWidth(75)
        self._tob_text.setMaximumWidth(75)
        current_date_str,current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
        self._dob_text.setText(current_date_str)
        self._tob_text.setText(current_time_str)
        h_layout.addWidget(self._tob_text)
        self.use_world_city_database = use_world_city_database
        utils.use_database_for_world_cities(self.use_world_city_database)
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
        h_layout.addWidget(self._place_widget, 1)
        self._lat_label = QLabel("Latidude:")
        h_layout.addWidget(self._lat_label)
        self._lat_text = QLineEdit('')
        self._latitude = 0.0
        self._lat_text.setMaximumWidth(90)
        self._lat_text.setToolTip('Enter Latitude preferably exact at place of birth: Format: +/- xx.xxx')
        h_layout.addWidget(self._lat_text)
        self._long_label = QLabel("Longitude:")
        h_layout.addWidget(self._long_label)
        self._long_text = QLineEdit('')
        self._longitude = 0.0
        self._long_text.setMaximumWidth(90)
        self._long_text.setToolTip('Enter Longitude preferably exact at place of birth. Format +/- xx.xxx')
        h_layout.addWidget(self._long_text)
        self._tz_label = QLabel("Time Zone:")
        h_layout.addWidget(self._tz_label)
        self._tz_text = QLineEdit('')
        self._time_zone = 0.0
        self._tz_text.setMaximumWidth(70)
        self._tz_text.setToolTip('Enter Time offset from GMT e.g. -5.5 or 4.5')
        h_layout.addWidget(self._tz_text)
        if const.use_internet_for_location_check:
            " Initialize with default place based on IP"
            loc = utils.get_place_from_user_ip_address()
            if len(loc)>=4:
                elev = float(loc[4]) if len(loc) >= 5 else 0.0
                self.place(loc[0],loc[1],loc[2],loc[3],elev)
                self._elevation = elev
        _show_button = QPushButton('Show')
        _show_button.clicked.connect(self._calculate_results)
        h_layout.addWidget(_show_button)
        self.birth_bird_index = birth_bird_index if birth_bird_index is not None else 1
        self.bird_combo = QComboBox()
        self.bird_combo.addItems([utils.resource_strings[b+'_str'] for b in pancha_pakshi_birds])
        self.bird_combo.setCurrentIndex(self.birth_bird_index-1)
        h_layout.addWidget(self.bird_combo)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)
        # Tree Widget
        self.tree = QTreeWidget()
        self._tree_font_size = tree_font_size
        set_treewidget_font_size(self.tree, tree_font_size)
        delegate = CustomDelegate()
        self.tree.setItemDelegate(delegate)
        # Connect to the itemExpanded signal
        if expand_one_row_at_a_time: self.tree.itemExpanded.connect(self.on_item_expanded)
        v_layout.addWidget(self.tree)
        self._display_sand_clock = False
        if synch_with_local_clock:
            # Set up the QTimer to update the row based on the current time
            self.timer = QTimer(self)
            self._search_datetime = None
            self.timer.timeout.connect(self.expand_row_with_datetime)
            self.timer.start(synch_timer_frequency_in_minutes*60000)
            self._display_sand_clock = True
        
        # Populate TreeWidget with data
        if headers and parent_level_list and child_level_list:
            self.populate_tree(birth_bird_index,headers,parent_level_list, child_level_list, hide_headers,
                               parent_level_labels=parent_level_labels,tree_font_size=self._tree_font_size)
    def restart_sandclock(self, timer_frequency):
        self.timer.stop()
        self.timer.start(timer_frequency)
    def place(self,place_name,latitude,longitude,timezone_hrs,elevation=0.0):
        """
            Set the place of birth
            @param - place_name - Specify with country code. e.g. Chennai, IN
            NOTE: Uses Nominatim to get the latitude and longitude
            An error message displayed if lat/long could not be found in which case enter lat/long manually.
            Also NOTE: calling latitude() or longitude() will replace the lat/long values added already
        """
        self._place_name = place_name
        self._latitude = latitude; self._longitude = longitude
        self._time_zone = timezone_hrs
        self._place_text.setText(self._place_name)
        self._lat_text.setText(str(self._latitude))
        self._long_text.setText(str(self._longitude))
        self._tz_text.setText(str(self._time_zone))
        self._elevation = 0.0
    def _resize_place_text_size(self):
        return
    def _get_location(self,place_name):
        result = utils.get_location(place_name)
        print("pancha pakshi RESULT",result)
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
        
    def on_item_expanded(self, item):
        # Collapse all other top-level items
        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if top_item != item:
                self.tree.collapseItem(top_item)
    def show_remove_sandclock(self,row_item,column_index,remove_clock=False):
        if remove_clock: 
            self.tree.setItemWidget(row_item, column_index, None)
            return
        sandclock_movie = QMovie(IMAGE_PATH+"sandclock.gif")
        sandclock_movie.setScaledSize(QSize(32, 32))  # Resize the GIF
        sandclock_label = QLabel()
        sandclock_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sandclock_label.setMovie(sandclock_movie)
        sandclock_movie.start()
        
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(sandclock_label)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        
        self.tree.setItemWidget(row_item, column_index, widget)  # Set in the 6th column (index 5)
    def expand_row_with_datetime(self, search_datetime=None):
        if search_datetime is None:
            search_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            search_datetime = QDateTime.fromString(search_datetime, _DATE_FORMAT)
        _DEBUG_ = False
        if _DEBUG_: print('expand_row_with_datetime', search_datetime, 'isValid:', search_datetime.isValid())
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent_item = root.child(i)
            from_datetime_string = parent_item.text(0)
            to_datetime_string = parent_item.text(1)
            if _DEBUG_: print('Parent item texts:', from_datetime_string, to_datetime_string)
            from_datetime = QDateTime.fromString(from_datetime_string, _DATE_FORMAT)
            to_datetime = QDateTime.fromString(to_datetime_string, _DATE_FORMAT)
            if _DEBUG_: print('Parsed datetimes:', from_datetime, to_datetime)
            if _DEBUG_: print(f"From isValid: {from_datetime.isValid()}, To isValid: {to_datetime.isValid()}")
    
            try:
                if _DEBUG_: print(f"Comparison: {from_datetime} <= {search_datetime} <= {to_datetime}")
                if from_datetime.isValid() and to_datetime.isValid() and from_datetime <= search_datetime <= to_datetime:
                    if _DEBUG_: print('Expanding parent', from_datetime, search_datetime, to_datetime)
                    self.tree.expandItem(parent_item)
                    #if self._display_sand_clock:
                    #    self.show_remove_sandclock(parent_item, _SUB_BIRD_DISP,remove_clock=False)
                    for j in range(parent_item.childCount()):
                        child_item = parent_item.child(j)
                        child_from_datetime_string = child_item.text(0)
                        child_to_datetime_string = child_item.text(1)
                        child_from_datetime = QDateTime.fromString(child_from_datetime_string, _DATE_FORMAT)
                        child_to_datetime = QDateTime.fromString(child_to_datetime_string, _DATE_FORMAT)
                        if _DEBUG_: print('Checking child:', child_from_datetime, child_to_datetime)
                        if _DEBUG_: print(f"Child Comparison: {child_from_datetime} <= {search_datetime} <= {child_to_datetime}")
                        if self._display_sand_clock:
                            self.show_remove_sandclock(child_item, _FROM_DATE_DISP,remove_clock=True)
                        if child_from_datetime.isValid() and child_to_datetime.isValid() and child_from_datetime <= search_datetime <= child_to_datetime:
                            if _DEBUG_: print('Found datetime', child_from_datetime, search_datetime, child_to_datetime)
                            #time_left = child_to_datetime.secsTo(search_datetime)//60
                            #print(search_datetime, child_to_datetime,'time left to move to next row',time_left,'minutes')
                            self.tree.expandItem(child_item)
                            self.tree.setCurrentItem(child_item)
                            if self._display_sand_clock:
                                self.show_remove_sandclock(child_item, _FROM_DATE_DISP,remove_clock=False)
                            #for col in range(self.tree.columnCount()):
                            #    child_item.setBackground(col, QColor('lightblue'))
                            break
                    break
            except Exception as e:
                print('Error processing search_datetime', search_datetime, 'Exception:', e)
    def populate_tree(self, birth_bird_index, headers, parent_level_list, child_level_list, hide_headers, 
                      search_datetime=None,parent_level_labels=None,tree_font_size=9):
        headers = [h.replace('\\n', '\n') for h in headers]
        self.tree.clear()
        self._tree_font_size = tree_font_size
        set_treewidget_font_size(self.tree, self._tree_font_size)
        self.bird_combo.setCurrentIndex(birth_bird_index-1)
        self.birth_bird_index = birth_bird_index
        # Set custom header view
        custom_header = CustomHeaderView(Qt.Orientation.Horizontal, self.tree)
        self.tree.setHeader(custom_header)
    
        if headers is not None:
            self.tree.setColumnCount(len(headers))
            self.tree.setHeaderLabels(headers)
        else:
            self.tree.setColumnCount(len(parent_level_list[0]))
        self.tree.setHeaderHidden(hide_headers)
    
        for parent_index, parent_row in enumerate(parent_level_list):
            if parent_level_labels:
                # Add custom text and icon above each parent row
                add_text_above_parent_row(self.tree, parent_level_labels[parent_index])
            parent_item = QTreeWidgetItem()
            self.set_item_icon_and_text(parent_item, parent_row)
            self.tree.addTopLevelItem(parent_item)
    
            for child_row in child_level_list[parent_index]:
                child_item = QTreeWidgetItem()
                # Check the type of each cell item
                processed_child_row = [format_cell_value(cell) for cell in child_row]
                self.set_item_icon_and_text(child_item, processed_child_row)
                parent_item.addChild(child_item)
    
                power_factor_progress_bar1 = QProgressBar()
                power_factor_progress_bar1.setValue(int(child_row[_POWER_FACTOR_DISP] * 100))  # Convert to percentage
                power_factor_progress_bar1.setStyleSheet("QProgressBar::chunk {background-color: lightgreen;}")
                power_factor_progress_bar1.setFixedWidth(60)
                self.tree.setItemWidget(child_item, _POWER_FACTOR_DISP, power_factor_progress_bar1)
                rating_progress_bar2 = QProgressBar()
                column_value = int(child_row[_RATING_DISP])  # Assuming column values are integers between 1 and 10
                rating_progress_bar2.setValue(column_value * 10)  # Convert to percentage
                rating_progress_bar2.setStyleSheet("QProgressBar::chunk {background-color: lightgreen;}")
                rating_progress_bar2.setFixedWidth(80)
                self.tree.setItemWidget(child_item, _RATING_DISP, rating_progress_bar2)
    
        self.tree.setColumnWidth(_RATING_DISP, 120)
        self.tree.itemExpanded.connect(self.resize_all_columns)
    
        if search_datetime:
            search_datetime = QDateTime.fromString(search_datetime, _DATE_FORMAT)
            self.expand_row_with_datetime(search_datetime)
        else:
            self._calculate_results()
    
        self.resize_all_columns()
        
    def set_item_icon_and_text(self, item, row):
        for column, cell_value in enumerate(row):
            if isinstance(cell_value,tuple):
                if len(cell_value)==3:
                    icon_path,text,color = cell_value
                    item.setBackground(column,QColor(color))
                else:
                    icon_path,text = cell_value
                if icon_path:
                    item.setIcon(column, QIcon(IMAGE_PATH+icon_path))
            else:
                text = cell_value
            item.setText(column, str(text))
    def resize_all_columns(self):
        """Resize columns of the tree widget to fit contents."""
        for column in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(column)
    def _calculate_results(self):
        from datetime import datetime
        year,month,day = self._dob_text.text().split(","); hh,mm,ss = self._tob_text.text().split(":")
        dob = (int(year),int(month),int(day))
        tob = tuple([int(x) for x in self._tob_text.text().split(':')])
        dob1 = datetime.strptime(self._dob_text.text(),"%Y,%m,%d")
        tob1 = datetime.strptime(self._tob_text.text(),"%H:%M:%S")
        jd_local = utils.julian_day_number(drik.Date(int(year),int(month),int(day)),(int(hh),int(mm),int(ss)))
        tz_hours = ( utils.get_place_timezone_offset(float(self._lat_text.text()),float(self._long_text.text()), jd_local)
                         if const.apply_daylight_savings_correction else float(self._tz_text.text()))
        self._tz_text.setText(str(tz_hours))
        sdate = datetime.combine(dob1.date(), tob1.time())
        search_datetime = sdate.strftime("%Y-%m-%d %H:%M:%S")
        place = drik.Place(self._place_text.text(),float(self._lat_text.text()),float(self._long_text.text()),
                           float(self._tz_text.text()))
        bird_index = self.bird_combo.currentIndex()+1
        self.birth_bird_index = bird_index
        headers,top_level_list,child_level_list,parent_level_labels = pancha_paksha.construct_pancha_pakshi_information(dob, tob, place, nakshathra_bird_index=bird_index)
        self.populate_tree(bird_index,headers, top_level_list, child_level_list,hide_headers=False,
                           search_datetime=search_datetime,parent_level_labels=parent_level_labels,
                           tree_font_size=self._tree_font_size)        
if __name__ == "__main__":
    utils.set_language('ta')
    #_create_pancha_paksha_db(); exit()
    dob = drik.Date(1996,12,7); tob = (10,34,0); place = drik.Place('Chennai,India',13.0878,80.2785,5.5)
    jd = utils.julian_day_number(dob, tob)
    bs = pancha_paksha._get_birth_nakshathra(jd, place)
    paksha_index = pancha_paksha._get_paksha(jd, place)
    bird_index = pancha_paksha._get_birth_bird_from_nakshathra(bs,paksha_index)
    weekday_index = drik.vaara(jd,place)+1
    print('bird',bird_index,utils.resource_strings[pancha_pakshi_birds[bird_index-1]+'_str'])
    dt = datetime.now().timetuple()
    dob = dt[0:3]; tob=dt[3:6]
    headers,top_level_list,child_level_list,parent_level_labels = pancha_paksha.construct_pancha_pakshi_information(dob, tob, place, nakshathra_bird_index=bird_index)
    app = QApplication(sys.argv)
    demo = PanchaPakshiSastraWidget(birth_bird_index=bird_index,headers=headers,parent_level_list=top_level_list,child_level_list=child_level_list,
                          hide_headers=False,tree_font_size=6.7,synch_with_local_clock=True,expand_one_row_at_a_time=False)
    demo.show()
    sys.exit(app.exec())
