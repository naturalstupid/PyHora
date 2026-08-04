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
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, QStringListModel, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QCompleter, QSizePolicy

from jhora import utils

# Minimum readable width when the row is tight (px).
_PLACE_FIELD_MIN_WIDTH = 200


class PlaceWidget(QWidget):
    """
    Reusable place input widget with:
      - QLineEdit
      - dynamic QCompleter
      - debounced search via utils.search_places_contains()
      - place resolution via utils.get_location_record()

    Signals:
      placeSelected(str)        -> emitted with the selected / resolved display label
      locationResolved(dict)    -> emitted with resolved location record
      locationLookupFailed(str) -> emitted when place could not be resolved
      textEditedSignal(str)     -> emitted when user edits text
    """

    placeSelected = pyqtSignal(str)
    locationResolved = pyqtSignal(dict)
    locationLookupFailed = pyqtSignal(str)
    textEditedSignal = pyqtSignal(str)

    def __init__(
        self,
        parent=None,
        initial_text="",
        placeholder_text="Enter place of birth, country name",
        tooltip_text="Enter place of birth, country name",
        min_chars=2,
        debounce_ms=150,
        max_visible_items=20,
        auto_load_database=False
    ):
        super().__init__(parent)

        self._min_chars = min_chars
        self._debounce_ms = debounce_ms
        self._selection_in_progress = False
        self._popup_mouse_down = False
        self._ignore_next_editing_finished = False
        if auto_load_database:
            utils.use_database_for_world_cities(True)

        self._line_edit = QLineEdit(initial_text, self)
        self._line_edit.setPlaceholderText(placeholder_text)
        self._line_edit.setToolTip(tooltip_text)
        # Stretch with the parent row instead of locking to a fixed glyph width.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(_PLACE_FIELD_MIN_WIDTH)
        self._line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._line_edit.setMinimumWidth(_PLACE_FIELD_MIN_WIDTH)

        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setMaxVisibleItems(max_visible_items)

        self._line_edit.setCompleter(self._completer)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._update_completions)

        # Signals
        self._line_edit.textEdited.connect(self._on_text_edited)

        # IMPORTANT:
        # Use returnPressed for manual commit
        self._line_edit.returnPressed.connect(self._on_return_pressed)

        # Keep editingFinished, but guard it carefully
        self._line_edit.editingFinished.connect(self._on_editing_finished)

        # Completer selection
        self._completer.activated.connect(self._on_place_selected)

        # Track mouse press on popup so editingFinished doesn't hijack selection
        popup = self._completer.popup()
        popup.pressed.connect(self._on_popup_pressed)
        popup.clicked.connect(self._on_popup_pressed)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line_edit, 1)

    # --------------------------------------------------------
    # Public helpers
    # --------------------------------------------------------
    def lineEdit(self):
        return self._line_edit

    def text(self):
        return self._line_edit.text()

    def setText(self, text):
        self._line_edit.setText(text)

    def setPlaceholderText(self, text):
        self._line_edit.setPlaceholderText(text)

    def setToolTip(self, text):
        self._line_edit.setToolTip(text)

    def setMinChars(self, value: int):
        self._min_chars = max(1, int(value))

    def setDebounceMs(self, value: int):
        self._debounce_ms = max(0, int(value))

    # --------------------------------------------------------
    # Internal UI handlers
    # --------------------------------------------------------
    def _on_text_edited(self, text):
        self.textEditedSignal.emit(text)
        self._search_timer.start(self._debounce_ms)

    def _update_completions(self):
        text = self._line_edit.text().strip()

        if len(text) < self._min_chars:
            self._completer_model.setStringList([])
            self._completer.popup().hide()
            return

        suggestions = utils.search_places_contains(text, limit=30)
        self._completer_model.setStringList(suggestions)

        popup = self._completer.popup()
        popup.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)

        if suggestions and self._line_edit.hasFocus():
            # IMPORTANT:
            # We already filtered suggestions in Python.
            # Prevent QCompleter from re-filtering against the typed text.
            self._completer.setCompletionPrefix("")

            fm = popup.fontMetrics()
            widest = max(fm.horizontalAdvance(s) for s in suggestions)
            padding = 40
            popup_width = max(self._line_edit.width(), widest + padding)

            popup.setMinimumWidth(popup_width)
            popup.resize(popup_width, popup.sizeHint().height())

            self._completer.complete()
        else:
            popup.hide()

    def _on_popup_pressed(self, *_):
        # Mouse click on popup is starting a real selection
        self._popup_mouse_down = True
        self._selection_in_progress = True

    def _on_place_selected(self, text):
        selected_text = str(text).strip()
        if not selected_text:
            self._popup_mouse_down = False
            self._selection_in_progress = False
            self._ignore_next_editing_finished = False
            return
    
        # A real popup selection is happening now.
        # editingFinished often fires immediately afterward due to focus change.
        # We must ignore that one extra editingFinished event.
        self._selection_in_progress = True
        self._ignore_next_editing_finished = True
    
        self._resolve_and_emit(selected_text)
    
        # clear selection flags after current event loop cycle
        QtCore.QTimer.singleShot(0, self._clear_selection_guard)

    def _clear_selection_guard(self):
        self._selection_in_progress = False
        self._popup_mouse_down = False

    def _on_return_pressed(self):
        """
        Manual commit by pressing Enter in the line edit.
        If popup is open and has suggestions, let user choose;
        don't prematurely resolve ambiguous partial text.
        """
        text = self._line_edit.text().strip()
        if not text:
            return

        popup = self._completer.popup()

        # If popup is visible, user is in the middle of choosing.
        # Don't force resolution here.
        if popup.isVisible():
            return

        self._resolve_or_disambiguate(text)

    def _on_editing_finished(self):
        """
        Guard against focus-loss firing when clicking/selecting from the popup.
    
        Important:
        After a real completer selection, Qt may still emit editingFinished.
        In that case we must ignore exactly one editingFinished event,
        otherwise the same selection gets resolved twice.
        """
        popup = self._completer.popup()
    
        # Ignore the first editingFinished immediately after popup selection
        if self._ignore_next_editing_finished:
            self._ignore_next_editing_finished = False
            return
    
        # If popup selection is in progress or popup is visible, do nothing
        if self._selection_in_progress or self._popup_mouse_down or popup.isVisible():
            return
    
        text = self._line_edit.text().strip()
        if not text:
            return
    
        self._resolve_or_disambiguate(text)

    def _resolve_or_disambiguate(self, text):
        """
        If exact alias is ambiguous (e.g. 'Pune'), show exact choices.
        Otherwise emit/place-resolve normally.
        """
        exact_labels = utils.get_exact_alias_labels(text, limit=30)
        if len(exact_labels) > 1:
            self._completer_model.setStringList(exact_labels)

            popup = self._completer.popup()
            popup.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)

            if self._line_edit.hasFocus():
                self._completer.setCompletionPrefix("")

                fm = popup.fontMetrics()
                widest = max(fm.horizontalAdvance(s) for s in exact_labels)
                padding = 40
                popup_width = max(self._line_edit.width(), widest + padding)

                popup.setMinimumWidth(popup_width)
                popup.resize(popup_width, popup.sizeHint().height())
                self._completer.complete()

            return

        # No ambiguity -> resolve directly
        self._resolve_and_emit(text)

    def _resolve_and_emit(self, text):
        selected_text = str(text).strip()
    
        # Let utils parse alias — canonical if present
        rec = utils.get_location_record(selected_text)
    
        if not rec:
            self.locationLookupFailed.emit(selected_text)
            return
    
        # IMPORTANT: keep exactly what the user selected visible
        self._line_edit.setText(selected_text)
    
        # Emit selected text AS SHOWN
        self.placeSelected.emit(selected_text)
        self.locationResolved.emit(rec)
    
        