#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Multi-row wrapping tab bar for crowded QTabWidget UIs."""
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLayout, QSizePolicy,
    QPushButton, QButtonGroup, QTabWidget,
)


class FlowLayout(QLayout):
    """Left-to-right flow that wraps to the next row when width is exceeded."""

    def __init__(self, parent=None, margin=0, h_spacing=4, v_spacing=4):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0
        for item in self._items:
            wid = item.widget()
            space_x = self._h_spacing
            space_y = self._v_spacing
            if wid is not None:
                space_x += wid.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
                space_y += wid.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y() + m.bottom()


class WrappingTabBar(QWidget):
    """Checkable buttons that wrap across rows; exclusive selection."""

    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flow = FlowLayout(self, margin=2, h_spacing=3, v_spacing=3)
        self.setLayout(self._flow)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.idClicked.connect(self._on_id_clicked)
        self._buttons = []
        self._block = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 3px 8px;
                background: #ececec;
                color: #222;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #e0e8f5;
            }
            QPushButton:checked {
                background: #ffffff;
                border: 1px solid #3a6ea5;
                border-bottom: 2px solid #3a6ea5;
                font-weight: 600;
                color: #1a1a1a;
            }
            QPushButton:disabled {
                color: #999;
                background: #f5f5f5;
            }
            """
        )

    def _on_id_clicked(self, tab_id):
        if self._block:
            return
        self.currentChanged.emit(tab_id)

    def set_tabs(self, entries):
        """
        entries: list of (index, text, visible) for each tab in the host widget.
        Only visible tabs get buttons; button id == real tab index.
        """
        self._block = True
        while self._flow.count():
            item = self._flow.takeAt(0)
            w = item.widget()
            if w is not None:
                self._group.removeButton(w)
                w.deleteLater()
        self._buttons = []
        for index, text, visible in entries:
            if not visible:
                continue
            label = (text or '').replace('\n', ' ').strip() or f'Tab {index + 1}'
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(label)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._group.addButton(btn, index)
            self._flow.addWidget(btn)
            self._buttons.append(btn)
        self._block = False
        self.updateGeometry()

    def setCurrentIndex(self, index):
        self._block = True
        btn = self._group.button(index)
        if btn is not None:
            btn.setChecked(True)
        self._block = False

    def currentIndex(self):
        return self._group.checkedId()


class MultiRowTabWidget(QWidget):
    """
    Drop-in stand-in for QTabWidget with a wrapping tab selector above content.
    Native tab bar is hidden; full tab titles wrap onto multiple rows.
    """

    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = QTabWidget(self)
        self._tabs.tabBar().hide()
        self._tabs.setDocumentMode(True)
        self._bar = WrappingTabBar(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._bar)
        layout.addWidget(self._tabs, 1)
        self._bar.currentChanged.connect(self._on_bar_changed)
        self._tabs.currentChanged.connect(self._on_tabs_changed)
        self._syncing = False
        self._refresh_pending = False

    def _on_bar_changed(self, index):
        if self._syncing or index < 0:
            return
        self._syncing = True
        self._tabs.setCurrentIndex(index)
        self._syncing = False
        self.currentChanged.emit(index)

    def _on_tabs_changed(self, index):
        if self._syncing:
            return
        self._syncing = True
        self._bar.setCurrentIndex(index)
        self._syncing = False
        self.currentChanged.emit(index)

    def refresh_tab_bar(self):
        # Coalesce bursts of addTab/setTabText into one rebuild per event-loop tick.
        if self._refresh_pending:
            return
        self._refresh_pending = True
        QTimer.singleShot(0, self._do_refresh_tab_bar)

    def _do_refresh_tab_bar(self):
        self._refresh_pending = False
        entries = []
        for i in range(self._tabs.count()):
            entries.append((i, self._tabs.tabText(i), self._tabs.isTabVisible(i)))
        current = self._tabs.currentIndex()
        self._bar.set_tabs(entries)
        if current >= 0:
            self._bar.setCurrentIndex(current)

    def addTab(self, widget, label=''):
        idx = self._tabs.addTab(widget, label)
        self.refresh_tab_bar()
        return idx

    def insertTab(self, index, widget, label=''):
        idx = self._tabs.insertTab(index, widget, label)
        self.refresh_tab_bar()
        return idx

    def removeTab(self, index):
        self._tabs.removeTab(index)
        self.refresh_tab_bar()

    def setTabText(self, index, text):
        self._tabs.setTabText(index, text)
        self.refresh_tab_bar()

    def tabText(self, index):
        return self._tabs.tabText(index)

    def setTabVisible(self, index, visible):
        self._tabs.setTabVisible(index, visible)
        self.refresh_tab_bar()

    def isTabVisible(self, index):
        return self._tabs.isTabVisible(index)

    def setTabToolTip(self, index, tip):
        self._tabs.setTabToolTip(index, tip)

    def currentIndex(self):
        return self._tabs.currentIndex()

    def setCurrentIndex(self, index):
        self._tabs.setCurrentIndex(index)

    def currentWidget(self):
        return self._tabs.currentWidget()

    def widget(self, index):
        return self._tabs.widget(index)

    def count(self):
        return self._tabs.count()

    def indexOf(self, widget):
        return self._tabs.indexOf(widget)

    def clear(self):
        self._tabs.clear()
        self.refresh_tab_bar()

    def setFocus(self, reason=Qt.FocusReason.OtherFocusReason):
        self._tabs.setFocus(reason)

    def __getattr__(self, name):
        return getattr(self._tabs, name)
