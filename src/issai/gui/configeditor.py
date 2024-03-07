# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# issai - Framework to run tests specified in Kiwi Test Case Management System
#
# Copyright (c) 2024, Frank Sommer.
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
Dialog window to edit settings based on TOML files.
"""

import tomlkit
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QTabWidget, QFormLayout, QGroupBox, QWidget, QLabel, QLineEdit, QComboBox, QDialog,
                               QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox, QCheckBox, QSizePolicy)

from issai.core.config import *
from issai.core.tcms import *
from issai.core.util import full_path_of
from issai.gui.dialogs import exception_box, IssaiProductSelectionDialog


class EditorData(dict):
    """
    Holds the data needed by the editor.
    Class is a dictionary using fully qualified TOML attribute names as keys.
    For every attribute there are three sub keys, one for the value as read from file, one for the attribute type and
    one for the widget responsible for editing the attribute value.
    """

    def __init__(self, metadata, settings):
        """
        Constructor.
        :param dict metadata: the metadata describing supported attributes and their types
        :param tomlkit.TOMLDocument settings: the actual settings to edit
        """
        super().__init__()
        self.__document_comments = []
        self.__group_comments = {}
        self.__attr_comments = {}
        for _t, _v in settings.body:
            if isinstance(_v, tomlkit.items.Comment):
                _comment = _v.as_string()[2:].strip()
                if _comment.startswith('d '):
                    self.__document_comments.append(_comment[2:])
                    continue
                if _comment.startswith('g'):
                    _prefix_end = _comment.find(' ')
                    _group_name = _comment[1:_prefix_end]
                    if _group_name not in self.__group_comments:
                        self.__group_comments[_group_name] = []
                    self.__group_comments[_group_name].append(_comment[_prefix_end+1:])
                    continue
                if _comment.startswith('a'):
                    _prefix_end = _comment.find(' ')
                    _attr_name = _comment[1:_prefix_end]
                    if _attr_name not in self.__attr_comments:
                        self.__attr_comments[_attr_name] = []
                    self.__attr_comments[_attr_name].append(_comment[_prefix_end+1:])
                    continue
        for _group_name, _group_meta in metadata.items():
            if len(_group_name) > 0:
                _group_name += '.'
            _attrs = _group_meta[META_KEY_ATTRS]
            for _attr in _attrs:
                _qualified_attr_name = _attr[META_KEY_ATTR_QUALIFIED_NAME]
                _attr_type = _attr[META_KEY_ATTR_TYPE]
                _attr_value = EditorData._attr_value(settings, _qualified_attr_name)
                if _attr_value is None:
                    continue
                self[_qualified_attr_name] = {}
                self[_qualified_attr_name][_DATA_KEY_ATTR_TYPE] = _attr_type
                self[_qualified_attr_name][_DATA_KEY_ATTR_VALUE] = _attr_value
                self[_qualified_attr_name][_DATA_KEY_WIDGET] = None

    def document_comments(self):
        """
        :returns: all comments at the top of XML-RPC credentials file
        :rtype: list
        """
        return self.__document_comments

    def group_comments(self, group_name):
        """
        :param str group_name: the desired group name
        :returns: all comments following specified TOML group
        :rtype: list
        """
        _comments = self.__group_comments.get(group_name)
        return [] if _comments is None else _comments

    def attribute_comments(self, attribute_name):
        """
        :param str attribute_name: the desired attribute name
        :returns: all comments following specified TOML attribute
        :rtype: list
        """
        _comments = self.__attr_comments.get(attribute_name)
        return [] if _comments is None else _comments

    def persistent_value(self, dotted_key):
        """
        Returns an attribute value as loaded from file resp. as to be stored to file.
        :param str dotted_key: the attribute ID
        :returns: the attribute value
        """
        return self.get(dotted_key).get(_DATA_KEY_ATTR_VALUE)

    def gui_value(self, dotted_key):
        """
        Returns an attribute value as displayed on the GUI.
        :param str dotted_key: the attribute ID
        :returns: the attribute value
        """
        _widget = self.get(dotted_key).get(_DATA_KEY_WIDGET)
        _attr_type = self.get(dotted_key).get(_DATA_KEY_ATTR_TYPE)
        if _attr_type.startswith(META_TYPE_STR):
            # QLineEdit
            return _widget.text()
        if _attr_type == META_TYPE_INT:
            # QLineEdit
            return int(_widget.text())
        if _attr_type == META_TYPE_BOOLEAN:
            # QCheckBox
            return _widget.isChecked()
        if _attr_type == META_TYPE_LIST_OF_STR:
            # QLineEdit
            _value = _widget.text().strip()
            return [] if len(_value) == 0 else [_item.strip() for _item in _value.split(',')]
        if _attr_type == META_TYPE_LIST_OF_INT:
            # QLineEdit
            _value = _widget.text().strip()
            return [] if len(_value) == 0 else [int(_item.strip()) for _item in _value.split(',')]
        if _attr_type.startswith(META_TYPE_ENUM):
            # QComboBox
            return _widget.currentText()
        return None

    def is_changed(self):
        """
        Indicates whether at least one attribute value has been changed on the GUI.
        :returns: True, if changes exist
        :rtype: bool
        """
        for _attr_id in self.keys():
            if self.persistent_value(_attr_id) != self.gui_value(_attr_id):
                return True
        return False

    def xml_rpc_credentials_modified(self):
        """
        :returns: True, if TCMS server URL has been changed in the editor; otherwise False
        :rtype: bool
        """
        _result = False
        for _attr in [CFG_PAR_TCMS_XML_RPC_URL, CFG_PAR_TCMS_XML_RPC_USERNAME, CFG_PAR_TCMS_XML_RPC_PASSWORD]:
            _widget = self.get(_attr).get(_DATA_KEY_WIDGET)
            _result = _result | _widget.isModified()
        return _result

    def apply_changes(self):
        """
        Copies attribute values from GUI widgets into the variables representing persistent values.
        """
        for _attr_id in self.keys():
            self.get(_attr_id)[_DATA_KEY_ATTR_VALUE] = self.gui_value(_attr_id)

    def settings(self):
        """
        :returns: all persistent settings
        :rtype: dict
        """
        _data = {}
        for _attr_id in self.keys():
            if _attr_id.find('.') < 0:
                _data[_attr_id] = self.get(_attr_id).get(_DATA_KEY_ATTR_VALUE)
            else:
                _attr_parts = _attr_id.split('.')
                _grp = _attr_parts[0]
                _attr = _attr_parts[1]
                if _grp not in _data:
                    _data[_grp] = {}
                _data[_grp][_attr] = self.get(_attr_id).get(_DATA_KEY_ATTR_VALUE)
        return _data

    @staticmethod
    def _attr_value(data, dotted_key):
        """
        Returns an attribute value contained in the hierarchy of the given dictionary.
        :param dict data: the TOML data
        :param str dotted_key: the attribute ID
        :returns: the attribute value; None if attribute with given ID not contained in the dictionary
        """
        if dotted_key.find('.') < 0:
            _node = data.get(dotted_key)
        else:
            _node = data
            _key_parts = dotted_key.split('.')
            for _key_part in _key_parts:
                if _key_part not in _node:
                    return None
                _node = _node[_key_part]
        return _node


class EditorTab(QWidget):
    """
    Tab item for a single group.
    """
    def __init__(self, parent, group_meta, group_data, file_type):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param dict|None group_meta: the metadata describing supported group attributes and their types
        :param tomlkit.items.Table|None group_data: the persistent settings of the group
        :param int|None file_type: the file type (master config, product config, XML-RPC credentials)
        """
        super().__init__(parent)
        self.__meta = group_meta
        self.__data = group_data
        self.__file_type = file_type
        self.__attr_widgets = {}

    def attribute_widgets(self):
        """
        :returns: value widgets for all attributes managed by the tab
        :rtype: dict
        """
        return self.__attr_widgets

    def manages_master_config_group(self):
        """
        :returns: True, if the tab manages a master configuration group
        :rtype: dict
        """
        return self.__file_type == _FILE_TYPE_MASTER_CONFIG

    @staticmethod
    def group_addition_tab(parent):
        """
        :param QWidget parent: the parent widget
        :returns: special tab to add a new group
        :rtype: EditorTab
        """
        return EditorTab(parent, None, None, None)


class EditorSignals(QObject):
    add_group_requested = Signal(tuple)


class EditorAdditionTab(QWidget):
    """
    Tab item to add groups.
    """
    def __init__(self, parent, missing_group_names):
        """
        Constructor.
        :param ConfigEditor parent: the parent widget
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

    def group_removed(self, group_name):
        """
        Called by the editor if a tab item for a group was removed.
        :param str group_name: the name of the removed group
        """
        self.__missing_group_names.add(group_name)
        self._fill_group_combo()

    def _add_clicked(self):
        """
        Add button was clicked. Emits event to editor to add a new tab item for the selected group.
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
            _display_group_name = "'' (root)" if len(_group_name) == 0 else _group_name
            self.__groups_combo.addItem(_display_group_name, _group_name)
        self.__groups_combo.setCurrentIndex(0)


class ConfigEditor(QDialog):
    """
    Dialog window to edit Issai and tcms-api configuration files.
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
        self.__comments_skipped = False
        try:
            _config_data = ConfigEditor._read_config_file(metadata, file_path, file_type)
        except IssaiException as _e:
            _msg_box = exception_box(QMessageBox.Icon.Warning, _e,
                                     localized_label(L_MBOX_INFO_USE_DEFAULT_SETTINGS),
                                     QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Ok)
            if _msg_box.exec() == QMessageBox.StandardButton.Cancel:
                raise
            _config_data = ConfigEditor._default_settings(metadata, file_type)
        self.__meta_data = metadata
        self.__file_path = file_path
        self.__file_type = file_type
        self.setWindowTitle(title)
        self.__editor_data = EditorData(metadata, _config_data)
        _layout = QVBoxLayout()
        _tabs = QTabWidget(self)
        _tabs.setStyleSheet(_TABS_STYLE)
        _missing_group_names = []
        for _group_name, _group_meta in sorted_metadata_items(metadata):
            _group_data = group_data_of(_config_data, _group_name)
            if _group_data is None or len(_group_data.keys()) == 0:
                _missing_group_names.append(_group_name)
                continue
            _tab = self._create_tab(_group_name, _group_meta, _group_data)
            if _tab is not None:
                _tabs.addTab(_tab, f'[{_group_name}]')
        if len(_missing_group_names) > 0:
            _tabs.addTab(EditorAdditionTab(self, _missing_group_names), '+')
        _layout.addWidget(_tabs)
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

    def add_group(self, group_info):
        print(f'add_group({group_info})')

    def _save_clicked(self):
        """
        Called when the save button was clicked.
        Writes settings to file, if they were changed and closes the dialog window.
        """
        if self.__editor_data.is_changed():
            if self.__comments_skipped:
                # comment lines were skipped during file load, save will result in all comments being deleted
                _rc = QMessageBox.question(self, localized_label(L_MBOX_TITLE_INFO),
                                           localized_label(L_MBOX_INFO_DISCARD_COMMENTS),
                                           QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                                           QMessageBox.StandardButton.Cancel)
                if _rc == QMessageBox.StandardButton.Cancel:
                    return
            _xml_rpc_credentials_modified = False
            if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                _xml_rpc_credentials_modified = self.__editor_data.xml_rpc_credentials_modified()
            self.__editor_data.apply_changes()
            _rc = QMessageBox.StandardButton.Yes
            while _rc != QMessageBox.StandardButton.No:
                _rc = QMessageBox.StandardButton.No
                try:
                    self._write_config_file()
                except IssaiException as _e:
                    _msg_box = exception_box(QMessageBox.Icon.Critical, _e,
                                             localized_label(L_MBOX_INFO_RETRY),
                                             QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
                                             QMessageBox.StandardButton.Yes)
                    _rc = _msg_box.exec()
            if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                # noinspection PyBroadException
                try:
                    if _xml_rpc_credentials_modified:
                        TcmsInterface.reset()
                except BaseException:
                    pass
        self.close()

    def _cancel_clicked(self):
        """
        Called when the cancel button was clicked.
        Closes the dialog window, if the settings were not changed.
        Asks for confirmation to discard changes, if the settings were edited.
        """
        if self.__editor_data.is_changed():
            _rc = QMessageBox.question(self, localized_label(L_MBOX_TITLE_DATA_EDITED),
                                       localized_label(L_MBOX_INFO_DISCARD_CHANGES))
            if _rc == QMessageBox.StandardButton.No:
                return
        self.close()

    def _create_tab(self, group_name, group_meta, group_data):
        """
        Creates a tab to allow editing attributes of a specific group.
        Closes the dialog window, if the settings were not changed.
        Asks for confirmation to discard changes, if the settings were edited.
        :param str group_name: the group name
        :param dict group_meta: the metadata group descriptor
        :param dict group_data: the group descriptor
        """
        _tab = EditorTab(self, group_meta, group_data_of(group_data, group_name), self.__file_type)
        _tab_layout = QFormLayout()
        _attributes = group_meta[META_KEY_ATTRS]
        for _a in _attributes:
            _attr_name = _a[META_KEY_ATTR_NAME]
            _qualified_attr_name = qualified_attr_name_for(group_name, _attr_name)
            _attr_type = _a[META_KEY_ATTR_TYPE]
            _attr_is_optional = _a[META_KEY_OPT]
            _attr_value = group_data.get(_attr_name)
            if _a[META_KEY_OPT] and _attr_value is None:
                continue
            _attr_label = QLabel(_attr_name)
            _attr_label.setStyleSheet(_ATTR_NAME_STYLE)
            if _attr_type.startswith(META_TYPE_STR) or _attr_type == META_TYPE_INT:
                _attr_widget = QLineEdit()
                _attr_widget.setFixedWidth(400)
                if _attr_type == META_TYPE_STR_PASSWORD:
                    _attr_widget.setEchoMode(QLineEdit.EchoMode.Password)
                _attr_widget.setText(_attr_value)
            elif _attr_type == META_TYPE_BOOLEAN:
                _attr_widget = QCheckBox()
                _attr_widget.setChecked(_attr_value)
            elif _attr_type.startswith(META_TYPE_LIST):
                _attr_widget = QLineEdit()
                _attr_widget.setFixedWidth(400)
                _attr_widget.setText(','.join(_attr_value))
            elif _attr_type.startswith(META_TYPE_MAPPING):
                _attr_widget = QLineEdit()
                _attr_widget.setFixedWidth(400)
                _attr_widget.setText(str(_attr_value))
            elif _attr_type.startswith(META_TYPE_ENUM):
                _enum_values = _attr_type[2:].split(',')
                _attr_widget = QComboBox()
                for _v in _enum_values:
                    _attr_widget.addItem(_v)
                _attr_widget.setCurrentText(_attr_value)
            else:
                _emsg = localized_message(E_GUI_SETTINGS_META_DEFINITION, _qualified_attr_name)
                _ex = IssaiException(E_INTERNAL_ERROR, _emsg)
                _msg_box = exception_box(QMessageBox.Icon.Critical, _ex, '',
                                         QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                _msg_box.exec()
                raise _ex
            _tab_layout.addRow(_attr_label, _attr_widget)
            self.__editor_data[_qualified_attr_name][_DATA_KEY_WIDGET] = _attr_widget
        _tab.setLayout(_tab_layout)
        return _tab

    @staticmethod
    def _read_config_file(metadata, file_path, file_type):
        """
        Reads configuration data from file.
        :param dict metadata: the metadata describing supported attributes and their types
        :param str file_path: the name of the file containing the data to edit including path
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        :rtype: tomlkit.TOMLDocument
        :raises IssaiException: if file is malformed
        """
        if not os.path.isfile(file_path):
            return ConfigEditor._default_settings(metadata, file_type)
        # noinspection PyBroadException
        try:
            _data = tomlkit.document()
            if file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                # XML-RPC credentials file - TOML with unquoted string values
                _current_group = None
                _current_group_name = ''
                _comment_prefix = 'd '
                with open(file_path, 'r') as _f:
                    _line = _f.readline()
                    while _line:
                        _line = _line.strip()
                        if len(_line) == 0:
                            _line = _f.readline()
                            continue
                        _m = re.match(r'\s*#(.*)', _line)
                        if _m:
                            _data.add(tomlkit.comment(f'{_comment_prefix}{_m.group(1)}'))
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
                                    _attr = tomlkit.string(_m.group(1))
                                    _qualified_attr_name = qualified_attr_name_for(_current_group_name, _attr_name)
                                    _comment_prefix = f'a{_qualified_attr_name} '
                                    if _current_group is None:
                                        _data.append(_attr_key, _attr)
                                    else:
                                        _current_group.append(_attr_key, _attr)
                                    break
                        _line = _f.readline()
            else:
                # plain TOML (issai configuration files)
                with open(file_path, 'r') as _f:
                    _data = tomlkit.load(_f)
                    validate_config_structure(_data, file_path, file_type == _FILE_TYPE_PRODUCT_CONFIG)
            ConfigEditor._fill_mandatory_attributes(_data, metadata, file_type)
            return _data
        except Exception as _e:
            raise IssaiException(W_GUI_READ_SETTINGS_FAILED, file_path, _e)

    def _write_config_file(self):
        """
        Writes settings to file.
        :raises IssaiException: if settings can't be saved to file
        """
        # noinspection PyBroadException
        _settings = self.__editor_data.settings()
        try:
            with open(self.__file_path, 'w') as _f:
                if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                    # TOML with unquoted string values (XML-RPC credentials file)
                    for _comment in self.__editor_data.document_comments():
                        _f.write(f'#{_comment}{os.linesep}')
                    for _k, _v in _settings.items():
                        if isinstance(_v, dict):
                            _f.write(f'[{_k}]{os.linesep}')
                            for _comment in self.__editor_data.group_comments(_k):
                                _f.write(f'#{_comment}{os.linesep}')
                            for _ak, _av in _v.items():
                                _f.write(f'{_ak} = {str(_av)}{os.linesep}')
                                _qualified_ak = qualified_attr_name_for(_k, _ak)
                                for _comment in self.__editor_data.attribute_comments(_qualified_ak):
                                    _f.write(f'#{_comment}{os.linesep}')
                        else:
                            _f.write(f'{_k} = {str(_v)}{os.linesep}')
                            for _comment in self.__editor_data.attribute_comments(_k):
                                _f.write(f'#{_comment}{os.linesep}')
                else:
                    # plain TOML (issai configuration files)
                    tomlkit.dump(_settings, _f)
        except Exception as _e:
            raise IssaiException(E_GUI_WRITE_SETTINGS_FAILED, self.__file_path, _e)

    @staticmethod
    def _fill_mandatory_attributes(settings, metadata, file_type):
        """
        Adds mandatory attributes if missing.
        :param dict settings: the settings
        :param dict metadata: the metadata describing supported attributes and their types
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        """
        _defaults = ConfigEditor._default_settings(metadata, file_type)
        for _gk, _gv in _defaults.items():
            if isinstance(_gv, dict):
                if _gk not in settings:
                    settings[_gk] = _gv.copy()
                else:
                    for _ak, _av in _gv.items():
                        if _ak not in settings[_gk]:
                            settings[_gk][_ak] = _av
                continue
            if _gk not in settings:
                settings[_gk] = _gv

    @staticmethod
    def _default_settings(metadata, file_type):
        """
        Returns default settings based on the metadata definitions.
        :param dict metadata: metadata with all TOML groups and attributes
        :param int file_type: the file type (master config, product config, XML-RPC credentials)
        :returns: default settings
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


def master_config_editor(parent):
    """
    Creates and returns a dialog window to edit the Issai master configuration file
    :param QWidget parent: the parent widget
    :returns: Dialog window to edit Issai master configuration file
    :rtype: ConfigEditor
    :raises IssaiException: if the editor can't be created
    """
    _master_config_file_path = os.path.join(full_path_of(ISSAI_CONFIG_PATH), ISSAI_MASTER_CONFIG_FILE_NAME)
    return ConfigEditor(parent, localized_label(L_DLG_TITLE_MASTER_CONFIG_EDITOR), config_meta_data(),
                        _master_config_file_path, _FILE_TYPE_MASTER_CONFIG)


def product_config_editor(parent, products):
    """
    Creates and returns a dialog window to edit an Issai product configuration file
    :param QWidget parent: the parent widget
    :param list products: the parent widget
    :returns: Dialog window to edit Issai product configuration file
    :rtype: ConfigEditor
    :raises IssaiException: if the editor can't be created
    """
    _sel_dlg = IssaiProductSelectionDialog(parent, products)
    if _sel_dlg.exec() == 0:
        return
    _product_config_dir_path = _sel_dlg.selected_product_config_path()
    _product_config_file_path = os.path.join(_product_config_dir_path, ISSAI_PRODUCT_CONFIG_FILE_NAME)
    _dlg_title = localized_message(L_DLG_TITLE_PRODUCT_CONFIG_EDITOR, os.path.basename(_product_config_dir_path))
    return ConfigEditor(parent, _dlg_title, config_meta_data(), _product_config_file_path, _FILE_TYPE_PRODUCT_CONFIG)


def xml_rpc_credentials_editor(parent):
    """
    Creates and returns a dialog window to edit the credentials for XML-RPC communication with Kiwi TCMS
    :param QWidget parent: the parent widget
    :returns: Dialog window to edit XML-RPC credentials
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


_ATTR_NAME_STYLE = 'font-weight: bold'
_GROUP_BOX_STYLE = '''QGroupBox {font: bold; border: 1px solid black; border-radius: 6px; margin-top: 6px;}
QGroupBox:title{subcontrol-origin: margin;
subcontrol-position: top left;
left: 7px;}
'''
_TABS_STYLE = 'QTabBar {font-weight: bold}'

_DATA_KEY_ATTR_TYPE = 'type'
_DATA_KEY_ATTR_VALUE = 'value'
_DATA_KEY_WIDGET = 'widget'

_FILE_TYPE_MASTER_CONFIG = 1
_FILE_TYPE_PRODUCT_CONFIG = 2
_FILE_TYPE_XML_RPC_CREDENTIALS = 3

_META_XML_RPC = {META_KEY_ALLOWED_IN_MASTER: True,
                 META_KEY_NAME_PATTERN: None,
                 META_KEY_OPT: False,
                 META_KEY_VALUE_TYPE: None,
                 META_KEY_ATTRS: [{META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_URL[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_URL,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                                   META_KEY_ATTR_DEFAULT_VALUE: 'https://localhost/xml-rpc/',
                                   META_KEY_OPT: False},
                                  {META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_USERNAME[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_USERNAME,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                                   META_KEY_ATTR_DEFAULT_VALUE: '',
                                   META_KEY_OPT: False},
                                  {META_KEY_ATTR_NAME: CFG_PAR_TCMS_XML_RPC_PASSWORD[len(CFG_GROUP_TCMS)+1:],
                                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_XML_RPC_PASSWORD,
                                   META_KEY_ATTR_TYPE: META_TYPE_STR_PASSWORD,
                                   META_KEY_ATTR_DEFAULT_VALUE: '',
                                   META_KEY_OPT: False}
                                  ]
                 }

_META_XML_RPC_CFG = {CFG_GROUP_TCMS: _META_XML_RPC}
