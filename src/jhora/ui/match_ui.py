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
import re
import sys
import os
from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from _datetime import datetime, timedelta,time,date
import img2pdf
from jhora.horoscope.match import compatibility
from jhora import utils

_DATA_PATH = '../data/'
_IMAGES_PATH = '../images/'
_IMAGE_ICON_PATH=_IMAGES_PATH +"lord_ganesha2.jpg"
_INPUT_DATA_FILE = _DATA_PATH+'program_inputs.txt'


available_languages = {"English":'en','Tamil':'ta','Telugu':'te'}
_main_window_width = 600
_main_window_height = 510 #630

class MatchWindow(QWidget):
    def __init__(self,chart_type='south indian'):
        super().__init__()
        self.setMinimumSize(_main_window_width,_main_window_height)
        self.resize(_main_window_width, _main_window_height)
        fp = open(_INPUT_DATA_FILE, encoding='utf-8', mode='r')
        window_title = fp.readline().split('=')[1]
        header_title = fp.readline().split('=')[1]
        self._image_icon_path = fp.readline().split('=')[1]
        fp.close()
        self.setWindowIcon(QtGui.QIcon(_IMAGE_ICON_PATH))
        self._language = list(available_languages.keys())[0]
        self.setWindowTitle(window_title)
        v_layout = QVBoxLayout()
        """
        footer_label = QLabel(header_title)#"Copyright © Dr. Sundar Sundaresan, Open Astro Technologies, USA.")
        footer_label.setStyleSheet("border: 1px solid black;")
        footer_label.setFont(QtGui.QFont("Arial Bold",12))
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setFixedHeight(15)
        footer_label.setFixedWidth(self.width())
        v_layout.addWidget(footer_label)
        """
        h_layout = QHBoxLayout()
        self._boy_star_label = QLabel("Boy's Birth Star:")
        h_layout.addWidget(self._boy_star_label)
        self._boy_star_combo = QComboBox()
        self._boy_star_combo.addItems(compatibility.nakshatra_list)
        h_layout.addWidget(self._boy_star_combo)
        self._boy_paadham_label = QLabel("Boy's Star Paadham:")
        h_layout.addWidget(self._boy_paadham_label)
        self._boy_paadham_combo = QSpinBox()
        self._boy_paadham_combo.setRange(1,4)
        h_layout.addWidget(self._boy_paadham_combo)
        self._boy_show_all_matches_label = QLabel('Show All Matching Girl stars:')
        h_layout.addWidget(self._boy_show_all_matches_label)
        v_layout.addLayout(h_layout)
        self._boy_show_all_matches_check = QCheckBox()
        self._boy_show_all_matches_check.setChecked(False)
        h_layout.addWidget(self._boy_show_all_matches_check)
        self._boy_show_all_matches_combo = QSpinBox()
        self._boy_show_all_matches_combo.setRange(0.0,36.0)
        self._boy_show_all_matches_combo.setSingleStep(0.5)
        self._boy_show_all_matches_combo.setValue(18.0)
        h_layout.addWidget(self._boy_show_all_matches_combo)
        v_layout.addLayout(h_layout)

        h_layout = QHBoxLayout()
        self._girl_star_label = QLabel("Girl's Birth Star:")
        h_layout.addWidget(self._girl_star_label)
        self._girl_star_combo = QComboBox()
        self._girl_star_combo.addItems(compatibility.nakshatra_list)
        self._girl_star_combo.setCurrentText('Swati')
        h_layout.addWidget(self._girl_star_combo)
        self._girl_paadham_label = QLabel("Girl's Star Paadham:")
        h_layout.addWidget(self._girl_paadham_label)
        self._girl_paadham_combo = QSpinBox()
        self._girl_paadham_combo.setRange(1,4)
        h_layout.addWidget(self._girl_paadham_combo)
        self._girl_show_all_matches_label = QLabel('Show All Matching Boy stars:')
        h_layout.addWidget(self._girl_show_all_matches_label)
        v_layout.addLayout(h_layout)
        self._girl_show_all_matches_check = QCheckBox()
        self._girl_show_all_matches_check.setChecked(False)
        h_layout.addWidget(self._girl_show_all_matches_check)
        self._girl_show_all_matches_combo = QSpinBox()
        self._girl_show_all_matches_combo.setRange(0.0,36.0)
        self._girl_show_all_matches_combo.setSingleStep(0.5)
        self._girl_show_all_matches_combo.setValue(18.0)
        h_layout.addWidget(self._girl_show_all_matches_combo)
        v_layout.addLayout(h_layout)

        h_layout = QHBoxLayout()
        self._mahendra_label = QLabel('Mahendra Porutham:')
        h_layout.addWidget(self._mahendra_label)
        self._mahendra_porutham_check = QCheckBox()
        self._mahendra_porutham_check.setChecked(True)
        h_layout.addWidget(self._mahendra_porutham_check)
        self._vedha_label = QLabel('Vedha Porutham:')
        h_layout.addWidget(self._vedha_label)
        self._vedha_porutham_check = QCheckBox()
        self._vedha_porutham_check.setChecked(True)
        h_layout.addWidget(self._vedha_porutham_check)
        v_layout.addLayout(h_layout)

        h_layout = QHBoxLayout()
        self._rajju_label = QLabel('Rajju Porutham:')
        h_layout.addWidget(self._rajju_label)
        self._rajju_porutham_check = QCheckBox()
        self._rajju_porutham_check.setChecked(True)
        h_layout.addWidget(self._rajju_porutham_check)
        self._shree_dheerga_label = QLabel('Shree Dheerga Porutham:')
        h_layout.addWidget(self._shree_dheerga_label)
        self._shree_dheerga_porutham_check = QCheckBox()
        self._shree_dheerga_porutham_check.setChecked(True)
        h_layout.addWidget(self._shree_dheerga_porutham_check)
        v_layout.addLayout(h_layout)
        self._compute_button = QPushButton('Show Match')
        v_layout.addWidget(self._compute_button)
        h_layout = QHBoxLayout()
        self._matching_star_list = QListWidget()
        self._matching_star_list.currentRowChanged.connect(self._update_compatibility_table)
        self._matching_star_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._matching_star_list.setVerticalScrollBar(QScrollBar(self))
        h_layout.addWidget(self._matching_star_list)
        self._results_table = QTableWidget(13,4)
        self._results_table.verticalHeader().hide()
        self._results_table.setHorizontalHeaderItem(0,QTableWidgetItem('Porutham/Koota'))
        self._results_table.setHorizontalHeaderItem(1,QTableWidgetItem('Score'))
        self._results_table.setHorizontalHeaderItem(2,QTableWidgetItem('Max Score'))
        self._results_table.setHorizontalHeaderItem(3,QTableWidgetItem('%'))
        self._results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._results_table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        h_layout.addWidget(self._results_table)
        self._matching_star_list.setMinimumHeight(self._results_table.height())
        v_layout.addLayout(h_layout)

        self._boy_show_all_matches_check.toggled.connect(self._check_only_boy_or_girl)
        self._girl_show_all_matches_check.toggled.connect(self._check_only_boy_or_girl)
        self._compute_button.clicked.connect(self._get_compatibility)
        self.setLayout(v_layout)
        self._v_layout = v_layout
    def _get_compatibility(self):
        if self._girl_show_all_matches_check.isChecked():
            bn = None
            bp = None
        else:
            bn = self._boy_star_combo.currentIndex()+1
            bp = self._boy_paadham_combo.value()+1
        if self._boy_show_all_matches_check.isChecked():
            gn = None
            gp = None
        else:
            gn = self._girl_star_combo.currentIndex()+1
            gp = self._girl_paadham_combo.value()+1
        if self._mahendra_porutham_check.isChecked():
            m_check = True
        else:
            m_check = None
        if self._vedha_porutham_check.isChecked():
            v_check = True
        else:
            v_check = None
        if self._rajju_porutham_check.isChecked():
            r_check = True
        else:
            r_check = None
        if self._shree_dheerga_porutham_check.isChecked():
            s_check = True
        else:
            s_check = None
        comp = compatibility.Match(boy_nakshatra_number=bn,boy_paadham_number=bp,girl_nakshatra_number=gn,girl_paadham_number=gp,\
                                   check_for_mahendra_porutham=m_check,check_for_vedha_porutham=v_check,\
                                   check_for_rajju_porutham=r_check,check_for_shreedheerga_porutham=s_check)
        self._matching_stars_tuple = utils.sort_tuple(comp.get_matching_partners(),4,reverse=True)
        
        if not self._matching_stars_tuple:
            self._matching_star_list.clear()
            self._matching_star_list.addItems(['No matching found'])
        else:
            self._matching_star_list.clear()
            matching_stars = []
            for t,m_s_tup in enumerate(self._matching_stars_tuple):
                nakshatra = compatibility.nakshatra_list[m_s_tup[0]-1]
                paadham = 'Paadham'+str(m_s_tup[1])+'-'+str(m_s_tup[2])
                matching_stars.append(nakshatra+'-'+paadham)
            self._matching_star_list.addItems(matching_stars)
            self._matching_star_list.setCurrentRow(0)
    def _get_compatibility_old(self):
        boy_nakshatra_number = self._boy_star_combo.currentIndex()+1
        boy_paadham_number = self._boy_paadham_combo.value()+1
        girl_nakshatra_number = self._girl_star_combo.currentIndex()+1
        girl_paadham_number = self._girl_paadham_combo.value()+1
        a = compatibility.Ashtakoota(boy_nakshatra_number,boy_paadham_number,girl_nakshatra_number,girl_paadham_number)
        ettu_poruthham_list = ['varna porutham', 'vasiya porutham', 'gana porutham', 'nakshathra porutham', 'yoni porutham', 'adhipathi porutham', 'raasi porutham', 'naadi porutham']
        naalu_porutham_list = ['mahendra porutham','vedha porutham','rajju porutham','sthree dheerga porutham']
        ettu_porutham_results,compatibility_score,naalu_porutham_results = a.compatibility_score()
        result = ''
        self._results_table.setHorizontalHeaderItem(0,QTableWidgetItem('Porutham'))
        self._results_table.setHorizontalHeaderItem(1,QTableWidgetItem('Score'))
        self._results_table.setHorizontalHeaderItem(2,QTableWidgetItem('Maximum'))
        format_str = format_str = '%-40s%-20s%-20s\n'
        row = 0
        for p,porutham in enumerate(ettu_poruthham_list):
            #result += format_str % (porutham,str(ettu_porutham_results[p][0]),str(ettu_porutham_results[p][1]))
            self._results_table.setItem(row,0,QTableWidgetItem(porutham))
            self._results_table.setItem(row,1,QTableWidgetItem(str(ettu_porutham_results[p][0])))
            self._results_table.setItem(row,2,QTableWidgetItem(str(ettu_porutham_results[p][1])))
            row += 1
        for p,porutham in enumerate(naalu_porutham_list):
            #result += format_str % (porutham,str(naalu_porutham_results[p]),'')
            self._results_table.setItem(row,0,QTableWidgetItem(porutham))
            self._results_table.setItem(row,1,QTableWidgetItem(str(naalu_porutham_results[p])))
            self._results_table.setItem(row,2,QTableWidgetItem('True'))
            row += 1
        #result += format_str % ('Overall Compatibility Score:', str(compatibility_score) +' out of '+ str(compatibility.max_compatibility_score),'')
        self._results_table.setItem(row,0,QTableWidgetItem('Overall Compatibility Score:'))
        self._results_table.setItem(row,1,QTableWidgetItem(str(compatibility_score)))
        self._results_table.setItem(row,2,QTableWidgetItem(str(compatibility.max_compatibility_score)))
        self._results_table.resizeColumnToContents(0)
        self._results_table.resizeColumnToContents(1)
        self._results_table.resizeColumnToContents(2)
        #self._results_label.setText(result)
    def _check_only_boy_or_girl(self):
        if self._boy_show_all_matches_check.isChecked():
            ' disable all girl ui elements'
            self._girl_star_label.setEnabled(False)
            self._girl_star_combo.setEnabled(False)
            self._girl_paadham_label.setEnabled(False)
            self._girl_paadham_combo.setEnabled(False)
        else: #if not self._boy_show_all_matches_check.isChecked():
            ' enable all girl ui elements'
            self._girl_star_label.setEnabled(True)
            self._girl_star_combo.setEnabled(True)
            self._girl_paadham_label.setEnabled(True)
            self._girl_paadham_combo.setEnabled(True)
        if self._girl_show_all_matches_check.isChecked():
            ' disable all boy ui elements'
            self._boy_star_label.setEnabled(False)
            self._boy_star_combo.setEnabled(False)
            self._boy_paadham_label.setEnabled(False)
            self._boy_paadham_combo.setEnabled(False)
        else: #if not self._girl_show_all_matches_check.isChecked():
            ' enable all boy ui elements'
            self._boy_star_label.setEnabled(True)
            self._boy_star_combo.setEnabled(True)
            self._boy_paadham_label.setEnabled(True)
            self._boy_paadham_combo.setEnabled(True)
    def _update_compatibility_table(self):
        cur_row = self._matching_star_list.currentRow()
        cur_item = self._matching_star_list.currentItem()
        if cur_item:
            if 'matching' in cur_item.text():
                return
        """ Show the selected item in the results table """
        selected_list_index = self._matching_star_list.currentRow()
        selected_matching_star_tuple = self._matching_stars_tuple[selected_list_index]
        ettu_poruthham_list = ['varna porutham', 'vasiya porutham', 'gana porutham', 'nakshathra porutham', 'yoni porutham', 'adhipathi porutham', 'raasi porutham', 'naadi porutham']
        ettu_porutham_max_score = [compatibility.varna_max_score,compatibility.vasiya_max_score,compatibility.gana_max_score,\
                                    compatibility.nakshathra_max_score,compatibility.yoni_max_score,compatibility.raasi_adhipathi_max_score, \
                                    compatibility.raasi_max_score, compatibility.naadi_max_score]
        naalu_porutham_list = ['mahendra porutham','vedha porutham','rajju porutham','sthree dheerga porutham']
        ettu_porutham_results = selected_matching_star_tuple[3]
        compatibility_score = selected_matching_star_tuple[4]
        naalu_porutham_results = selected_matching_star_tuple[5]
        nakshatra = compatibility.nakshatra_list[selected_matching_star_tuple[0]-1]
        paadham = 'Paadham'+str(selected_matching_star_tuple[1])+'-'+str(selected_matching_star_tuple[2])
        result = ''
        results_table = self._results_table
        row = 0
        for p,porutham in enumerate(ettu_poruthham_list):
            #result += format_str % (porutham,str(ettu_porutham_results[p][0]),str(ettu_porutham_results[p][1]))
            results_table.setItem(row,0,QTableWidgetItem(porutham))
            results_table.setItem(row,1,QTableWidgetItem(str(ettu_porutham_results[p])))
            results_table.setItem(row,2,QTableWidgetItem(str(ettu_porutham_max_score[p])))
            perc = '{:3.0f}%'.format(ettu_porutham_results[p]/ettu_porutham_max_score[p]*100)
            results_table.setItem(row,3,QTableWidgetItem(str(perc)))
            row += 1
        for p,porutham in enumerate(naalu_porutham_list):
            #result += format_str % (porutham,str(naalu_porutham_results[p]),'')
            results_table.setItem(row,0,QTableWidgetItem(porutham))
            results_table.setItem(row,1,QTableWidgetItem(str(naalu_porutham_results[p])))
            results_table.setItem(row,2,QTableWidgetItem('True'))
            if naalu_porutham_results[p]:
                results_table.setItem(row,3,QTableWidgetItem(str('\u2705')))
            else:
                results_table.setItem(row,3,QTableWidgetItem(str('\u274C')))
            row += 1
        results_table.setItem(row,0,QTableWidgetItem('Overall Matching Score'))
        results_table.setItem(row,1,QTableWidgetItem(str(compatibility_score)))
        results_table.setItem(row,2,QTableWidgetItem(str(compatibility.max_compatibility_score)))
        perc = '{:3.0f}%'.format(compatibility_score/compatibility.max_compatibility_score*100)
        results_table.setItem(row,3,QTableWidgetItem(str(perc)))
        for c in range(3):
            results_table.resizeColumnToContents(c)
        for r in range(13):
            results_table.resizeRowToContents(r)
if __name__ == "__main__":
    def except_hook(cls, exception, traceback):
        print('exception called')
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook
    App = QApplication(sys.argv)
    chart = MatchWindow()
    chart.show()
    sys.exit(App.exec())