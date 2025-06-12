# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# issai - Framework to run tests specified in Kiwi Test Case Management System
#
# Copyright (c) 2025, Frank Sommer.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------------------------

"""
Dialog window to edit configuration data based on TOML files.
"""

import tomlkit
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QTabWidget, QAbstractScrollArea, QGroupBox, QWidget, QLineEdit, QComboBox, QDialog,
                               QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox, QCheckBox, QSizePolicy,
                               QTableWidget, QHeaderView, QLabel, QTabBar, QStyle)

from issai.core.config import *
from issai.core.tcms import *
from issai.core.util import full_path_of
from issai.gui.dialogs import exception_box, IssaiProductSelectionDialog


class EditorTabFolder(QTabWidget):
    """
    Holds all tab items of the config editor.
    """
    def __init__(self, parent, config_data, meta_data, file_type):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param tomlkit.TOMLDocument config_data: the persistent data
        :param dict meta_data: the metadata describing supported groups, attributes and their types
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        """
        super().__init__(parent)
        self.__meta_data = meta_data
        self.__addition_tab = None
        self.__signals = EditorSignals()
        self.setStyleSheet(_TAB_FOLDER_STYLE)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._tab_close_requested)
        _missing_group_names = []
        for _group_name, _group_meta in sorted_metadata_items(meta_data):
            _group_data = group_data_of(config_data, _group_name)
            if _group_data is None or (len(_group_data.keys()) == 0 and len(_group_name) == 0):
                if file_type != _FILE_TYPE_MASTER_CONFIG or _group_meta[META_KEY_ALLOWED_IN_MASTER]:
                    _missing_group_names.append(_group_name)
                continue
            self._insert_tab(_group_name, _group_meta, _group_data)
        if len(_missing_group_names) > 0:
            self._append_addition_tab(_missing_group_names)

    def _tab_close_requested(self, index):
        """
        Called when the close icon on a tab has been clicked.
        :param int index: index of tab to close
        """
        _group_name = self.tabText(index)
        if not _group_name.startswith('['):
            return
        _group_name = _group_name[1:-1]
        _rc = QMessageBox.question(self, localized_label(L_MBOX_TITLE_INFO),
                                   localized_message(L_MBOX_INFO_REMOVE_GROUP, _group_name))
        if _rc == QMessageBox.StandardButton.Yes:
            self.removeTab(index)
            if self.__addition_tab is None:
                self._append_addition_tab([_group_name])
            self.__signals.group_removed.emit(_group_name)

    def group_names(self):
        """
        :returns: names of all groups in tab folder
        :rtype: set
        """
        _group_names = set()
        for _i in range(0, self.count()):
            _group_name = self.tabText(_i)
            if _group_name != _ADDITION_WIDGET_TEXT:
                _group_names.add(_group_name[1:-1])
        return _group_names

    def qualified_attribute_names(self):
        """
        :returns: qualified names of all attributes in tab folder
        :rtype: set
        """
        _attr_names = set()
        for _i in range(0, self.count()):
            _tab = self.widget(_i)
            if not isinstance(_tab, EditorGroupTab):
                continue
            _attr_names.update(_tab.qualified_attribute_names())
        return _attr_names

    def gui_values(self):
        """
        :returns: TOML values for all attributes managed by the tab folder, keys are qualified attribute names
        :rtype: dict
        """
        _gui_values = {}
        for _i in range(0, self.count()):
            _tab = self.widget(_i)
            if not isinstance(_tab, EditorGroupTab):
                continue
            _gui_values.update(_tab.gui_values())
        return _gui_values

    def gui_data(self):
        """
        :returns: all GUI data in TOML format
        :rtype: tomlkit.TOMLDocument
        """
        _gui_data = tomlkit.TOMLDocument()
        for _group in self.group_names():
            if len(_group) > 0:
                _gui_data.append(_group, tomlkit.table())
        _gui_values = self.gui_values()
        for _k, _v in _gui_values.items():
            if _k.find('.') < 0:
                _gui_data.append(_k, _v)
            else:
                _g, _a = _k.split('.')
                _gui_data.get(_g).append(_a, _v)
        return _gui_data

    def current_tab(self):
        """
        :returns: currently selected tab item
        :rtype: EditorTab
        """
        return self.currentWidget()

    def add_group(self, group_info):
        """
        Called by addition tab, when a new tab item shall be created.
        :param tuple group_info: group name, flag indicating whether it's the last supported group
        """
        _group_name, _is_last_group = group_info
        _group_data = tomlkit.table()
        self._insert_tab(_group_name, self.__meta_data.get(_group_name), _group_data, self.count()-1)
        if _is_last_group:
            self._remove_addition_tab()

    def _insert_tab(self, group_name, group_meta, group_data, index=-1):
        """
        Inserts a new tab item for a group. Tab header is group name enclosed in brackets.
        :param str group_name: the group name
        :param dict group_meta: the group metadata
        :param tomlkit.items.Table group_data: the persistent group data
        :param int index: the insertion index
        """
        if len(group_meta[META_KEY_ATTRS]) == 0:
            _tab = EditorCustomGroupTab(self, group_name, group_meta, group_data)
        else:
            _tab = EditorSystemGroupTab(self, group_name, group_meta, group_data)
        _tab_index = self.insertTab(index, _tab, f'[{group_name}]')
        if not group_meta[META_KEY_OPT]:
            _tab_bar = self.tabBar()
            _style_hint = _tab_bar.style().styleHint(QStyle.StyleHint.SH_TabBar_CloseButtonPosition, None, _tab_bar)
            _tab_bar.setTabButton(_tab_index, QTabBar.ButtonPosition(_style_hint), None)

    def _append_addition_tab(self, missing_group_names):
        """
        Adds a special tab where the user can create additional group tab items.
        :param list missing_group_names: names of all groups currently not shown in the tab folder
        """
        if self.__addition_tab is None:
            self.__addition_tab = EditorAdditionTab(self, missing_group_names)
            _tab_index = self.addTab(self.__addition_tab, _ADDITION_WIDGET_TEXT)
            _tab_bar = self.tabBar()
            _style_hint = _tab_bar.style().styleHint(QStyle.StyleHint.SH_TabBar_CloseButtonPosition, None, _tab_bar)
            _tab_bar.setTabButton(_tab_index, QTabBar.ButtonPosition(_style_hint), None)
            self.__signals.group_removed.connect(self.__addition_tab.group_removed)

    def _remove_addition_tab(self):
        """
        Removes special tab where the user can create additional group tab items.
        """
        if self.__addition_tab is None:
            return
        _index = self.indexOf(self.__addition_tab)
        if _index >= 0:
            self.removeTab(_index)
        self.__addition_tab = None


class EditorSignals(QObject):
    """
    Custom signals used within the editor.
    """
    # editor addition tab indicates new group to tab folder (parameter group name, last group indicator flag)
    add_group_requested = Signal(tuple)
    # popup menu on a tab indicates deleted group to tab folder (parameter group name)
    group_removed = Signal(str)
    # button in table indicates deleted attribute to tab (parameter attribute name)
    remove_attr_requested = Signal(str)


class RemoveAttrButton(QPushButton):
    """
    Push button to remove an attribute from an editor tab.
    """
    def __init__(self, attr_name, signal_handler):
        """
        Constructor.
        :param function signal_handler: the function handling clicks on the button
        :param str attr_name: the attribute name
        """
        super().__init__(_REMOVE_WIDGET_TEXT)
        self.setStyleSheet(_REMOVE_ATTR_BUTTON_STYLE)
        self.setMaximumWidth(20)
        self.__attr_name = attr_name
        self.__signals = EditorSignals()
        self.__signals.remove_attr_requested.connect(signal_handler)
        self.clicked.connect(self._clicked)

    def _clicked(self):
        """
        Called when the button to remove an attribute was clicked.
        Emits signal to the editor tab that an attribute shall be deleted. Two-stage signalling needed, because
        standard clicked signal doesn't allow a parameter for the attribute name.
        """
        self.__signals.remove_attr_requested.emit(self.__attr_name)


class EditorTab(QWidget):
    """
    Base class for all tab items.
    """
    def __init__(self, parent):
        """
        Constructor.
        :param QWidget parent: the parent widget
        """
        super().__init__(parent)

    def is_removable(self):
        """
        :returns: True, if tab can be removed from the folder, i.e. it manages an optional group.
        :rtype: bool
        """
        return True


class EditorGroupTab(EditorTab):
    """
    Base class for tab items managing a single group.
    """
    def __init__(self, parent, group_name, group_meta):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str group_name: the name of the group manage by this tab
        :param dict group_meta: the metadata describing supported group attributes and their types
        """
        super().__init__(parent)
        self.group_name = group_name
        self.meta = group_meta
        self.attr_widgets = {}
        self.setLayout(QVBoxLayout())
        self.attr_table = self.create_attr_table()
        self.attr_descriptors = {}

    def name_widget(self, row):
        """
        :returns: widget containing the attribute name of specified table row
        :rtype: QLabel
        """
        _widget = self.attr_table.cellWidget(row, 1)
        return _widget if isinstance(_widget, QLabel) else None

    def attribute_names(self):
        """
        :returns: pure names of all attributes in tab
        :rtype: set
        """
        return set([_a for _a in self.attr_widgets.keys()])

    def qualified_attribute_names(self):
        """
        :returns: qualified names of all attributes in tab
        :rtype: set
        """
        return set([qualified_attr_name_for(self.group_name, _a) for _a in self.attr_widgets.keys()])

    def gui_values(self):
        """
        :returns: TOML values for all attributes managed by the tab, keys are qualified attribute names
        :rtype: dict
        """
        _gui_values = {}
        for _attr_name, _widget in self.attr_widgets.items():
            _attr_desc = self.attr_descriptors.get(_attr_name)
            _gui_values[qualified_attr_name_for(self.group_name, _attr_name)] = _toml_value_of(_widget, _attr_desc)
        return _gui_values

    def create_attr_table(self):
        """
        :returns: table to manage the attributes of the group
        :rtype: QTableWidget
        """
        _table = QTableWidget(self)
        _table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        _table.setColumnCount(3)
        _table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        _table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        _table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        _table.setHorizontalHeaderLabels([localized_label(L_ACTION), localized_label(L_ATTRIBUTE),
                                          localized_label(L_VALUE)])
        _table.verticalHeader().hide()
        return _table

    @staticmethod
    def create_add_attr_button(signal_handler):
        """
        :param function signal_handler: the function handling button clicks
        :return: button to add an attribute
        :rtype: QWidget
        """
        _add_button = QPushButton(_ADDITION_WIDGET_TEXT)
        _add_button.setStyleSheet(_ADD_ATTR_BUTTON_STYLE)
        _add_button.setMaximumWidth(20)
        _add_button.clicked.connect(signal_handler)
        _add_button_frame = QWidget()
        _layout = QHBoxLayout()
        _layout.addWidget(_add_button)
        _layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _add_button_frame.setLayout(_layout)
        return _add_button_frame

    @staticmethod
    def create_remove_attr_button(attr_name, signal_handler):
        """
        :param str attr_name: the name of the attribute
        :param function signal_handler: the function handling button clicks
        :return: button to remove the attribute with specified name from the table
        :rtype: QWidget
        """
        _remove_button = RemoveAttrButton(attr_name, signal_handler)
        _remove_button_frame = QWidget()
        _layout = QHBoxLayout()
        _layout.addWidget(_remove_button)
        _layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _remove_button_frame.setLayout(_layout)
        return _remove_button_frame


class EditorSystemGroupTab(EditorGroupTab):
    """
    Tab item for the management of a single group with a system defined set of attributes only.
    """
    def __init__(self, parent, group_name, group_meta, group_data):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str group_name: the name of the group manage by this tab
        :param dict group_meta: the metadata describing supported group attributes and their types
        :param tomlkit.items.Table group_data: the persistent data
        """
        super().__init__(parent, group_name, group_meta)
        for _attr_desc in group_meta[META_KEY_ATTRS]:
            self.attr_descriptors[_attr_desc[META_KEY_ATTR_NAME]] = _attr_desc
        _group_data_count = len(group_data.unwrap())
        self.attr_table.setRowCount(_group_data_count)
        _row = 0
        for _attr_name, _attr_value in group_data.items():
            _attr_value = _gui_value_of(_attr_value)
            if self.attr_descriptors.get(_attr_name)[META_KEY_OPT]:
                _remove_button = self.create_remove_attr_button(_attr_name, self.remove_system_attr)
                self.attr_table.setCellWidget(_row, 0, _remove_button)
            _name_label = QLabel(_attr_name)
            _name_label.setToolTip(localized_label(self.attr_descriptors[_attr_name][META_KEY_COMMENT]))
            self.attr_table.setCellWidget(_row, 1, _name_label)
            self.attr_widgets[_attr_name] = self._attr_value_widget_for(_attr_name, _attr_value)
            self.attr_table.setCellWidget(_row, 2, self.attr_widgets[_attr_name])
            _row += 1
        if _group_data_count < len(self.attr_descriptors):
            self._create_attr_addition_row()
        self.attr_table.resizeColumnsToContents()
        self.layout().addWidget(self.attr_table)

    def is_removable(self):
        """
        :returns: True, if tab can be removed from the folder, i.e. it manages an optional group.
        :rtype: bool
        """
        return self.meta[META_KEY_OPT]

    def remove_system_attr(self, attr_name):
        """
        Called, when the remove button for specified attribute was clicked.
        Removes corresponding row from the table and input widget from internal managed attributes dict.
        :param str attr_name: the attribute name
        """
        for _row in range(0, self.attr_table.rowCount()):
            _name_widget = self.name_widget(_row)
            if _name_widget is None or _name_widget.text() != attr_name:
                continue
            del self.attr_widgets[attr_name]
            self.attr_table.removeRow(_row)
            break
        _attr_selection_combo = self._addition_line_combo()
        if _attr_selection_combo is None:
            self._create_attr_addition_row()
        else:
            self._fill_attr_selection_combo(_attr_selection_combo)
        self.attr_table.resizeColumnToContents(1)
        self.attr_table.clearSelection()

    def _addition_line_combo(self):
        """
        :returns: Combo box to add new attributes; None, if no addition line exists
        :rtype: QComboBox
        """
        _widget = self.attr_table.cellWidget(self.attr_table.rowCount() - 1, 1)
        return None if _widget is None or not isinstance(_widget, QComboBox) else _widget

    def _attr_value_widget_for(self, attr_name, attr_value=None):
        """
        :param str attr_name: the attribute name
        :param attr_value: the optional attribute value
        :returns: widget for specified attribute, value filled if specified
        :rtype: QWidget
        """
        _attr_desc = self.attr_descriptors.get(attr_name)
        _attr_type = _attr_desc[META_KEY_ATTR_TYPE]
        if _attr_type == META_TYPE_BOOLEAN:
            _attr_widget = QCheckBox()
            if attr_value is not None:
                if isinstance(attr_value, (bool, tomlkit.items.Bool)):
                    _attr_widget.setChecked(_python_value_of(attr_value))
                elif isinstance(attr_value, str):
                    _attr_widget.setChecked(bool(attr_value))
        elif _attr_type.startswith(META_TYPE_ENUM):
            _enum_values = _attr_type[2:].split(',')
            _attr_widget = QComboBox()
            for _v in _enum_values:
                _attr_widget.addItem(_v)
            if attr_value is not None:
                _attr_widget.setCurrentText(attr_value)
        else:
            _attr_widget = QLineEdit()
            if _attr_type == META_TYPE_STR_PASSWORD:
                _attr_widget.setEchoMode(QLineEdit.EchoMode.Password)
            if attr_value is not None:
                _attr_widget.setText(_gui_value_of(attr_value))
        return _attr_widget

    def _create_attr_addition_row(self):
        """
        Creates a row for attribute addition at the bottom of the table.
        Table row count must have been incremented in advance.
        """
        _row = self.attr_table.rowCount()
        self.attr_table.insertRow(_row)
        self.attr_table.setCellWidget(_row, 0, EditorGroupTab.create_add_attr_button(self._add_attr_clicked))
        _attr_selection_combo = self._create_attr_selection_combo()
        self.attr_table.setCellWidget(_row, 1, _attr_selection_combo)
        self.attr_table.resizeColumnToContents(1)

    def _create_attr_selection_combo(self):
        """
        :returns: combo box to select attributes currently not shown in the tab.
        :rtype: QComboBox
        """
        _attr_selection_combo = QComboBox()
        _attr_selection_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        _attr_selection_combo.currentTextChanged.connect(self._addition_attr_selected)
        self._fill_attr_selection_combo(_attr_selection_combo)
        return _attr_selection_combo

    def _fill_attr_selection_combo(self, selection_combo):
        """
        :param QComboBox selection_combo: the attribute selection combo box
        (Re-)fills combo box to select attributes currently not shown in the tab.
        """
        _supported_attrs = set(self.attr_descriptors.keys())
        _displayed_attrs = self.attribute_names()
        _hidden_attrs = _supported_attrs - _displayed_attrs
        selection_combo.clear()
        _index = 0
        for _attr_name in sorted(_hidden_attrs):
            selection_combo.addItem(_attr_name)
            _tool_tip = localized_label(self.attr_descriptors[_attr_name][META_KEY_COMMENT])
            selection_combo.setItemData(_index, _tool_tip, Qt.ItemDataRole.ToolTipRole)
            _index += 1
        selection_combo.setCurrentIndex(0)

    def _add_attr_clicked(self):
        """
        Called when the '+'-Button to add an attribute was clicked.
        """
        _row = self.attr_table.rowCount() - 1
        _attr_selection_combo = self.attr_table.cellWidget(_row, 1)
        _attr_name = _attr_selection_combo.currentText()
        _hidden_attr_count = _attr_selection_combo.count()
        _attr_value_widget = self.attr_table.cellWidget(_row, 2)
        _attr_value = _toml_value_of(_attr_value_widget, self.attr_descriptors[_attr_name])
        self.attr_widgets[_attr_name] = self._attr_value_widget_for(_attr_name, _attr_value)
        _remove_button = EditorGroupTab.create_remove_attr_button(_attr_name, self.remove_system_attr)
        self.attr_table.removeRow(_row)
        _new_row_count = _row + 1 if _hidden_attr_count == 1 else _row + 2
        self.attr_table.setRowCount(_new_row_count)
        self.attr_table.setCellWidget(_row, 0, _remove_button)
        _name_label = QLabel(_attr_name)
        _name_label.setToolTip(localized_label(self.attr_descriptors[_attr_name][META_KEY_COMMENT]))
        self.attr_table.setCellWidget(_row, 1, _name_label)
        self.attr_table.setCellWidget(_row, 2, self.attr_widgets[_attr_name])
        if _hidden_attr_count > 1:
            _attr_selection_combo = self._create_attr_selection_combo()
            _row += 1
            self.attr_table.setRowCount(_row + 1)
            self.attr_table.setCellWidget(_row, 0, EditorGroupTab.create_add_attr_button(self._add_attr_clicked))
            self.attr_table.setCellWidget(_row, 1, _attr_selection_combo)
        self.attr_table.resizeColumnToContents(1)
        self.attr_table.clearSelection()

    def _addition_attr_selected(self, attr_name):
        """
        Called when the user selects an attribute from the combo box of supported attributes.
        Creates an input widget matching the attribute type in the third table column.
        :param str attr_name: the selected attribute name
        """
        if len(attr_name) == 0:
            return
        _row = self.attr_table.rowCount() - 1
        self.attr_table.setCellWidget(_row, 2, self._attr_value_widget_for(attr_name))


class EditorCustomGroupTab(EditorGroupTab):
    """
    Tab item for the management of a single group with custom attributes only.
    """
    def __init__(self, parent, group_name, group_meta, group_data):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str group_name: the name of the group manage by this tab
        :param tomlkit.items.Table group_data: the persistent data
        """
        super().__init__(parent, group_name, group_meta)
        self.attr_table.setRowCount(len(group_data.unwrap()) + 1)
        _row = 0
        for _attr_name, _attr_value in group_data.items():
            _attr_value = _gui_value_of(_attr_value)
            _remove_button = self.create_remove_attr_button(_attr_name, self.remove_custom_attr)
            self.attr_table.setCellWidget(_row, 0, _remove_button)
            self.attr_table.setCellWidget(_row, 1, QLabel(_attr_name))
            self.attr_widgets[_attr_name] = QLineEdit(_attr_value)
            self.attr_table.setCellWidget(_row, 2, self.attr_widgets[_attr_name])
            _row += 1
        self.attr_table.setCellWidget(_row, 0, EditorGroupTab.create_add_attr_button(self.add_custom_attr))
        self.attr_table.setCellWidget(_row, 1, QLineEdit())
        self.attr_table.setCellWidget(_row, 2, QLineEdit())
        self.attr_table.resizeColumnsToContents()
        self.layout().addWidget(self.attr_table)

    def add_custom_attr(self):
        """
        Called, when the add button was clicked.
        """
        _row = self.attr_table.rowCount() - 1
        _attr_name = self.attr_table.cellWidget(_row, 1).text()
        if len(_attr_name) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO), localized_label(I_GUI_NO_ATTRIBUTE_NAME))
            return
        _attr_name_pattern = self.meta[META_KEY_NAME_PATTERN]
        if _attr_name_pattern is not None:
            if not _attr_name_pattern.match(_attr_name):
                QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                        localized_message(I_GUI_INVALID_ATTRIBUTE_NAME, _attr_name,
                                                          _attr_name_pattern.pattern))
                return
        if _attr_name in self.attribute_names():
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_ATTRIBUTE_EXISTS, _attr_name))
            return
        _attr_value = self.attr_table.cellWidget(_row, 2).text()
        _remove_button = EditorGroupTab.create_remove_attr_button(_attr_name, self.remove_custom_attr)
        self.attr_table.insertRow(_row)
        _attr_value_widget = QLineEdit(_attr_value)
        self.attr_widgets[_attr_name] = _attr_value_widget
        self.attr_table.setCellWidget(_row, 0, _remove_button)
        self.attr_table.setCellWidget(_row, 1, QLabel(_attr_name))
        self.attr_table.setCellWidget(_row, 2, _attr_value_widget)
        _row += 1
        self.attr_table.setCellWidget(_row, 0, EditorGroupTab.create_add_attr_button(self.add_custom_attr))
        self.attr_table.setCellWidget(_row, 1, QLineEdit())
        self.attr_table.setCellWidget(_row, 2, QLineEdit())

    def remove_custom_attr(self, attr_name):
        """
        Called, when the remove button for specified attribute was clicked.
        :param str attr_name: the attribute name
        """
        for _row in range(0, self.attr_table.rowCount()):
            _name_widget = self.name_widget(_row)
            if _name_widget is None or _name_widget.text() != attr_name:
                continue
            del self.attr_widgets[attr_name]
            self.attr_table.removeRow(_row)
            return


class EditorAdditionTab(EditorTab):
    """
    Tab item to add groups.
    """
    def __init__(self, parent, missing_group_names):
        """
        Constructor.
        :param EditorTabFolder parent: the parent widget
        :param list missing_group_names: the group names currently not shown in the editor
        """
        super().__init__(parent)
        self.__missing_group_names = set(missing_group_names)
        self.__signals = EditorSignals()
        self.__signals.add_group_requested.connect(parent.add_group)
        _tab_layout = QVBoxLayout(self)
        _tab_layout.setSpacing(20)
        _group_box = QGroupBox(localized_label(L_SELECT_GROUP), self)
        _group_layout = QVBoxLayout()
        _group_layout.setContentsMargins(10, 20, 10, 20)
        _group_box.setStyleSheet(_GROUP_BOX_STYLE)
        self.__groups_combo = QComboBox(self)
        self._fill_group_combo()
        _group_layout.addWidget(self.__groups_combo)
        _group_box.setLayout(_group_layout)
        _tab_layout.addWidget(_group_box)
        _add_button = QPushButton(localized_label(L_ADD))
        _add_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        _add_button.clicked.connect(self._add_clicked)
        _tab_layout.addWidget(_add_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _tab_layout.addStretch()
        self.setLayout(_tab_layout)

    def is_removable(self):
        """
        :returns: True, if tab can be removed from the folder, i.e. it manages an optional group.
        :rtype: bool
        """
        return False

    def group_removed(self, group_name):
        """
        Called by the editor when a tab item for a group was removed.
        :param str group_name: the name of the removed group
        """
        self.__missing_group_names.add(group_name)
        self._fill_group_combo()

    def _add_clicked(self):
        """
        Called when the add button was clicked. Emits event to editor to add a new tab item for the selected group.
        """
        _group_to_add = self.__groups_combo.currentData()
        _is_last_group = len(self.__missing_group_names) == 1
        self.__missing_group_names.remove(_group_to_add)
        self._fill_group_combo()
        self.__signals.add_group_requested.emit((_group_to_add, _is_last_group))

    def _fill_group_combo(self):
        """
        (Re-)fills group selection combo box from list of missing groups.
        """
        self.__groups_combo.clear()
        for _group_name in sorted(self.__missing_group_names):
            _display_group_name = _ROOT_GROUP_DISPLAY_TEXT if len(_group_name) == 0 else _group_name
            self.__groups_combo.addItem(_display_group_name, _group_name)
        self.__groups_combo.setCurrentIndex(0)


class ConfigEditor(QDialog):
    """
    Dialog window to edit Issai and tcms-api configuration files.
    The editor class is mainly responsible for reading and writing configuration files.
    """

    def __init__(self, parent, title, metadata, file_path, file_type):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str title: the localized dialog window title
        :param dict metadata: the metadata describing supported attributes and their types
        :param str file_path: the name of the file containing the data to edit including path
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        """
        super().__init__(parent)
        self.setMinimumSize(_MINIMUM_EDITOR_WIDTH, _MINIMUM_EDITOR_HEIGHT)
        try:
            _config_data, _comments_found = ConfigEditor._read_config_file(metadata, file_path, file_type)
        except IssaiException as _e:
            _msg_box = exception_box(QMessageBox.Icon.Warning, _e,
                                     localized_label(L_MBOX_INFO_USE_DEFAULT_CONFIG),
                                     QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Ok)
            if _msg_box.exec() == QMessageBox.StandardButton.Cancel:
                raise
            _config_data = ConfigEditor._default_configuration(metadata, file_type)
            _comments_found = False
        self.__config_data = _config_data
        self.__meta_data = metadata
        self.__file_path = file_path
        self.__file_type = file_type
        self.__file_has_comments = _comments_found
        self.setWindowTitle(title)
        _layout = QVBoxLayout()
        self.__tab_folder = EditorTabFolder(self, _config_data, metadata, file_type)
        _layout.addWidget(self.__tab_folder)
        _button_box = QGroupBox(self)
        _button_box_layout = QHBoxLayout()
        _save_button = QPushButton(localized_label(L_SAVE))
        _save_button.clicked.connect(self._save_clicked)
        _button_box_layout.addWidget(_save_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.clicked.connect(self._cancel_clicked)
        _button_box_layout.addWidget(_cancel_button)
        _button_box.setLayout(_button_box_layout)
        _layout.addWidget(_button_box)
        self.setLayout(_layout)

    def closeEvent(self, event):
        """
        :param QEvent event: the close event
        Called when the dialog shall be closed, either by Save resp. Cancel button or from window close button.
        Asks for confirmation, if changes would be lost.
        """
        if self._data_has_been_changed():
            _rc = QMessageBox.question(self, localized_label(L_MBOX_TITLE_DATA_EDITED),
                                       localized_label(L_MBOX_INFO_DISCARD_CHANGES))
            if _rc == QMessageBox.StandardButton.No:
                event.setAccepted(False)

    def _data_has_been_changed(self):
        """
        Indicates whether configuration data has been changed.
        :returns: True, if persistent and GUI data differs
        :rtype: bool
        """
        # check whether group names differ
        _group_names = self.__tab_folder.group_names()
        if self._persistent_group_names() != _group_names:
            return True
        # check whether attribute names differ
        if self._qualified_persistent_attribute_names() != self.__tab_folder.qualified_attribute_names():
            return True
        # check whether any attribute value differs
        _gui_values = self.__tab_folder.gui_values()
        for _k, _v in self.__config_data.items():
            if isinstance(_v, tomlkit.items.Table):
                for _ak, _av in _v.items():
                    if _av != _gui_values[qualified_attr_name_for(_k, _ak)]:
                        return True
            else:
                if _v != _gui_values[_k]:
                    return True
        return False

    def _persistent_group_names(self):
        """
        :returns: names of all groups in persistent configuration
        :rtype: set
        """
        _group_names = set()
        for _k, _v in self.__config_data.items():
            _group_name = _k if isinstance(_v, tomlkit.items.Table) else ''
            _group_names.add(_group_name)
        return _group_names

    def _qualified_persistent_attribute_names(self):
        """
        :returns: qualified names of all attributes in persistent configuration
        :rtype: set
        """
        _attr_names = set()
        for _k, _v in self.__config_data.items():
            if isinstance(_v, tomlkit.items.Table):
                for _attr_name in _v.keys():
                    _attr_names.add(qualified_attr_name_for(_k, _attr_name))
            else:
                _attr_names.add(_k)
        return _attr_names

    def _save_clicked(self):
        """
        Called when the save button was clicked.
        Writes configuration data to file, if they were changed and closes the dialog window.
        """
        if self._data_has_been_changed():
            if self.__file_has_comments:
                _rc = QMessageBox.warning(self, localized_label(L_MBOX_TITLE_WARNING),
                                          localized_message(W_GUI_WRITE_CONFIG_LOSES_COMMENTS),
                                          QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
                if _rc != QMessageBox.StandardButton.Ok:
                    return
            _rc = QMessageBox.StandardButton.Yes
            while _rc != QMessageBox.StandardButton.No:
                _rc = QMessageBox.StandardButton.No
                try:
                    _gui_data = self.__tab_folder.gui_data()
                    self._write_config_file(_gui_data)
                    self.__config_data = _gui_data
                except IssaiException as _e:
                    _msg_box = exception_box(QMessageBox.Icon.Critical, _e,
                                             localized_label(L_MBOX_INFO_RETRY),
                                             QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
                                             QMessageBox.StandardButton.Yes)
                    _rc = _msg_box.exec()
            if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                # noinspection PyBroadException
                try:
                    TcmsInterface.reset()
                except BaseException:
                    pass
        self.close()

    def _cancel_clicked(self):
        """
        Called when the cancel button was clicked.
        Closes the dialog window, if the configuration data were not changed.
        Asks for confirmation to discard changes, if the configuration data were edited.
        """
        self.close()

    @staticmethod
    def _read_config_file(metadata, file_path, file_type):
        """
        Reads configuration data from file.
        :param dict metadata: the metadata describing supported attributes and their types
        :param str file_path: the name of the file containing the data to edit including path
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        :rtype: tuple[tomlkit.TOMLDocument, bool]
        :raises IssaiException: if file is malformed
        """
        _comments_found = False
        if not os.path.isfile(file_path):
            return ConfigEditor._default_configuration(metadata, file_type), _comments_found
        # noinspection PyBroadException
        try:
            _data = tomlkit.document()
            if file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                # XML-RPC credentials file - TOML with unquoted string values
                _current_group = None
                _current_group_name = ''
                with open(file_path, 'r') as _f:
                    _line = _f.readline()
                    while _line:
                        _line = _line.strip()
                        if len(_line) == 0:
                            _line = _f.readline()
                            continue
                        if re.match(r'\s*#.*', _line):
                            _comments_found = True
                            _line = _f.readline()
                            continue
                        for _group_name, _group_meta in metadata.items():
                            _grp_pattern = rf'\s*\[{_group_name}\]'
                            _m = re.match(_grp_pattern, _line)
                            if _m:
                                _current_group_name = _group_name
                                _current_group = tomlkit.table()
                                _data.append(tomlkit.key(_group_name), _current_group)
                                _comment_prefix = f'g{_group_name} '
                                break
                            for _a in _group_meta[META_KEY_ATTRS]:
                                _attr_name = _a[META_KEY_ATTR_NAME]
                                _attr_pattern = rf'\s*{_attr_name}\s*=\s*(.*)$'
                                _m = re.match(_attr_pattern, _line)
                                if _m:
                                    _attr_key = tomlkit.key(_attr_name)
                                    if _a[META_KEY_ATTR_TYPE] == META_TYPE_BOOLEAN:
                                        _attr = tomlkit.boolean(_m.group(1).lower())
                                    else:
                                        _attr = tomlkit.string(_m.group(1))
                                    _qualified_attr_name = qualified_attr_name_for(_current_group_name, _attr_name)
                                    if _current_group is None:
                                        _data.append(_attr_key, _attr)
                                    else:
                                        _current_group.append(_attr_key, _attr)
                                    break
                        _line = _f.readline()
            else:
                # plain TOML (issai configuration files)
                with open(file_path, 'r') as _f:
                    _contents = _f.read()
                    if re.search(r'^\s*#.*$', _contents, re.MULTILINE | re.DOTALL):
                        _comments_found = True
                    _data = tomlkit.loads(_contents)
                    validate_config_structure(_data, file_path, file_type == _FILE_TYPE_PRODUCT_CONFIG)
            ConfigEditor._fill_mandatory_attributes(_data, metadata, file_type)
            return _data, _comments_found
        except Exception as _e:
            raise IssaiException(W_GUI_READ_CONFIG_DATA_FAILED, file_path, _e)

    def _write_config_file(self, config_data):
        """
        Writes configuration data to file.
        :param tomlkit.TOMLDocument config_data: the configuration data
        :raises IssaiException: if configuration data can't be saved to file
        """
        # noinspection PyBroadException
        try:
            with open(self.__file_path, 'w') as _f:
                if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                    # TOML with unquoted string values (XML-RPC credentials file)
                    for _k, _v in config_data.items():
                        if isinstance(_v, tomlkit.items.Table):
                            _f.write(f'[{_k}]{os.linesep}')
                            for _ak, _av in _v.items():
                                _f.write(f'{_ak} = {_python_value_of(_av)}{os.linesep}')
                        else:
                            _f.write(f'{_k} = {_python_value_of(_v)}{os.linesep}')
                else:
                    # plain TOML (issai configuration files)
                    tomlkit.dump(config_data, _f)
        except Exception as _e:
            raise IssaiException(E_GUI_WRITE_CONFIG_DATA_FAILED, self.__file_path, _e)

    @staticmethod
    def _fill_mandatory_attributes(config_data, metadata, file_type):
        """
        Adds mandatory attributes to specified configuration data if missing.
        :param tomlkit.TOMLDocument config_data: the configuration data
        :param dict metadata: the metadata describing supported attributes and their types
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        """
        _defaults = ConfigEditor._default_configuration(metadata, file_type)
        for _gk, _gv in _defaults.items():
            if isinstance(_gv, dict):
                if _gk not in config_data:
                    config_data[_gk] = _gv.copy()
                else:
                    for _ak, _av in _gv.items():
                        if _ak not in config_data[_gk]:
                            config_data[_gk][_ak] = _av
                continue
            if _gk not in config_data:
                config_data[_gk] = _gv

    @staticmethod
    def _default_configuration(metadata, file_type):
        """
        :param dict metadata: metadata with all TOML groups and attributes
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        :returns: default configuration of specified file type based on the metadata definitions
        :rtype: dict
        """
        _data = {}
        for _group_name, _group_meta in metadata.items():
            if file_type == _FILE_TYPE_MASTER_CONFIG and not _group_meta[META_KEY_ALLOWED_IN_MASTER]:
                continue
            if _group_meta[META_KEY_OPT]:
                continue
            if len(_group_name) > 0:
                _data[_group_name] = {}
            _attributes = _group_meta[META_KEY_ATTRS]
            for _a in _attributes:
                if _a[META_KEY_OPT]:
                    continue
                _attr_name = _a[META_KEY_ATTR_NAME]
                _attr_value = _a[META_KEY_ATTR_DEFAULT_VALUE]
                if len(_group_name) == 0:
                    _data[_attr_name] = _attr_value
                else:
                    _data[_group_name][_attr_name] = _attr_value
        return _data


def master_config_editor(parent, config_path):
    """
    :param QWidget parent: the parent widget
    :param str config_path: the Issai configuration root path
    :returns: Dialog window to edit Issai master configuration file
    :rtype: ConfigEditor
    :raises IssaiException: if the editor can't be created
    """
    _master_config_file_path = os.path.join(config_path, ISSAI_MASTER_CONFIG_FILE_NAME)
    return ConfigEditor(parent, localized_label(L_DLG_TITLE_MASTER_CONFIG_EDITOR), config_meta_data(),
                        _master_config_file_path, _FILE_TYPE_MASTER_CONFIG)


def product_config_editor(parent, products):
    """
    :param QWidget parent: the parent widget
    :param list products: names of all products in Issai configuration directory
    :returns: Dialog window to edit Issai product configuration file
    :rtype: ConfigEditor
    :raises IssaiException: if the editor can't be created
    """
    _sel_dlg = IssaiProductSelectionDialog(parent, products)
    if _sel_dlg.exec() == 0:
        return None
    _product_config_dir_path = _sel_dlg.selected_product_config_path()
    _product_config_file_path = os.path.join(_product_config_dir_path, ISSAI_PRODUCT_CONFIG_FILE_NAME)
    _dlg_title = localized_message(L_DLG_TITLE_PRODUCT_CONFIG_EDITOR, os.path.basename(_product_config_dir_path))
    return ConfigEditor(parent, _dlg_title, config_meta_data(), _product_config_file_path, _FILE_TYPE_PRODUCT_CONFIG)


def xml_rpc_credentials_editor(parent):
    """
    :param QWidget parent: the parent widget
    :returns: Dialog window to edit the credentials for XML-RPC communication with Kiwi TCMS
    :rtype: ConfigEditor
    :raises IssaiException: if the editor can't be created
    """
    return ConfigEditor(parent, localized_label(L_DLG_TITLE_XML_RPC_EDITOR), _META_XML_RPC_CFG,
                        full_path_of(TCMS_XML_RPC_CREDENTIALS_FILE_PATH), _FILE_TYPE_XML_RPC_CREDENTIALS)


def sorted_metadata_items(metadata):
    """
    :param dict metadata: the metadata describing supported groups and attributes of a configuration file
    :returns: metadata items sorted for the need of the tab item
    :rtype: list
    """
    _sorted_items = sorted(metadata.items())
    if CFG_GROUP_PRODUCT in metadata.keys():
        for _i in range(1, len(_sorted_items)):
            if _sorted_items[_i][0] == CFG_GROUP_PRODUCT:
                _sorted_items[1], _sorted_items[_i] = _sorted_items[_i], _sorted_items[1]
                break
    return _sorted_items


def _python_value_of(toml_value):
    """
    :param tomlkit.items.Item toml_value: the TOML value
    :returns: Python value of specified TOML value
    """
    # noinspection PyBroadException
    try:
        return toml_value.unwrap()
    except BaseException:
        return toml_value


def _toml_value_of(widget, attr_desc):
    """
    :param QWidget widget: the widget holding the GUI value
    :param dict attr_desc: the attribute descriptor, may be None
    :returns: TOML value of specified widget
    """
    if isinstance(widget, QCheckBox):
        return tomlkit.boolean(str(widget.isChecked()).lower())
    if isinstance(widget, QComboBox):
        return tomlkit.string(widget.currentText())
    if isinstance(widget, QLineEdit):
        _gui_value = widget.text().strip()
        if attr_desc is None:
            return tomlkit.string(_gui_value)
        _attr_type = attr_desc[META_KEY_ATTR_TYPE]
        if _attr_type == META_TYPE_INT:
            return tomlkit.integer(_gui_value)
        if _attr_type.startswith(META_TYPE_LIST):
            _toml_value = tomlkit.array()
            _gui_value = _gui_value.lstrip('[').rstrip(']').strip()
            if len(_gui_value) == 0:
                return _toml_value
            _items = _gui_value.split(',')
            for _item in _items:
                if _attr_type == META_TYPE_LIST_OF_INT:
                    _toml_value.append(tomlkit.integer(_item.strip()))
                else:
                    _toml_value.append(_item.strip())
            return _toml_value
        if _attr_type.startswith(META_TYPE_MAPPING):
            _toml_value = tomlkit.inline_table()
            _gui_value = _gui_value.lstrip('{').rstrip('}').strip()
            if len(_gui_value) == 0:
                return _toml_value
            _items = _gui_value.split(',')
            for _item in _items:
                _k, _v = _item.strip().split('=')
                _toml_value.append(_k.strip(), tomlkit.string(_v.strip()))
            return _toml_value
        return tomlkit.string(_gui_value)
    return None


def _gui_value_of(toml_value):
    """
    :param tomlkit.items.  toml_value: the TOML value
    :returns: GUI (string) value of specified TOML value
    :rtype: str
    """
    if isinstance(toml_value, tomlkit.items.Array):
        _items = ','.join(toml_value.unwrap())
        return f'[{_items}]'
    if isinstance(toml_value, tomlkit.items.InlineTable):
        _items = ','.join([f'{_k}={_v}' for _k, _v in toml_value.unwrap().items()])
        return f'{{{_items}}}'
    return _python_value_of(toml_value)


_MINIMUM_EDITOR_HEIGHT = 400
_MINIMUM_EDITOR_WIDTH = 600

_ADD_ATTR_BUTTON_STYLE = 'background-color: green; color: white; font-weight: bold'
_REMOVE_ATTR_BUTTON_STYLE = 'background-color: darkred; color: white; font-weight: bold'
_ATTR_NAME_STYLE = 'font-weight: bold'
_GROUP_BOX_STYLE = '''QGroupBox {font: bold; border: 1px solid black; border-radius: 6px; margin-top: 6px;}
QGroupBox:title{subcontrol-origin: margin;
subcontrol-position: top left;
left: 7px;}
'''
_TAB_FOLDER_STYLE = 'QTabBar {font-weight: bold}'

_ADDITION_WIDGET_TEXT = '+'
_REMOVE_WIDGET_TEXT = '-'
_ROOT_GROUP_DISPLAY_TEXT = "'' (root)"

_DATA_KEY_ATTR_TYPE = 'type'
_DATA_KEY_ATTR_VALUE = 'value'
_DATA_KEY_WIDGET = 'widget'

_FILE_TYPE_MASTER_CONFIG = 1
_FILE_TYPE_PRODUCT_CONFIG = 2
_FILE_TYPE_XML_RPC_CREDENTIALS = 3

_META_XML_RPC = {META_KEY_ALLOWED_IN_MASTER: True,
                 META_KEY_NAME_PATTERN: None,
                 META_KEY_OPT: False,
                 META_KEY_UNQUOTED_STR_VALUES: True,
                 META_KEY_VALUE_TYPE: None,
                 META_KEY_ATTRS: [{META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_URL[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_URL,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                                   META_KEY_ATTR_DEFAULT_VALUE: 'https://localhost/xml-rpc/',
                                   META_KEY_COMMENT: L_CFG_PAR_TCMS_XML_RPC_URL,
                                   META_KEY_OPT: False},
                                  {META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_USERNAME[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_USERNAME,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                                   META_KEY_ATTR_DEFAULT_VALUE: '',
                                   META_KEY_COMMENT: L_CFG_PAR_TCMS_XML_RPC_USERNAME,
                                   META_KEY_OPT: False},
                                  {META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_PASSWORD[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_PASSWORD,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_PASSWORD,
                                   META_KEY_ATTR_DEFAULT_VALUE: '',
                                   META_KEY_COMMENT: L_CFG_PAR_TCMS_XML_RPC_PASSWORD,
                                   META_KEY_OPT: False},
                                  {META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_USE_KERBEROS[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_USE_KERBEROS,
                                   META_KEY_ATTR_TYPE: META_TYPE_BOOLEAN,
                                   META_KEY_ATTR_DEFAULT_VALUE: False,
                                   META_KEY_COMMENT: L_CFG_PAR_TCMS_XML_RPC_USE_KERBEROS,
                                   META_KEY_OPT: True}
                                  ]
                 }

_META_XML_RPC_CFG = {CFG_GROUP_TCMS: _META_XML_RPC}
