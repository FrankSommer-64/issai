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

from PySide6.QtWidgets import (QTabWidget, QFormLayout, QGroupBox, QWidget, QLabel, QLineEdit, QComboBox, QDialog,
                               QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox, QCheckBox)

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
        :param dict settings: the actual settings to edit
        """
        super().__init__()
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
        self.__meta_data = metadata
        self.__file_path = file_path
        self.__file_type = file_type
        self.__comments_skipped = False
        try:
            _settings = self._read_settings()
        except IssaiException as _e:
            _msg_box = exception_box(QMessageBox.Icon.Warning, _e,
                                     localized_label(L_MBOX_INFO_USE_DEFAULT_SETTINGS),
                                     QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Ok)
            if _msg_box.exec() == QMessageBox.StandardButton.Cancel:
                raise
            _settings = ConfigEditor._default_settings(metadata)
        self.setWindowTitle(title)
        self.__editor_data = EditorData(metadata, _settings)
        _layout = QVBoxLayout()
        _tabs = QTabWidget(self)
        _tabs.setStyleSheet(_TABS_STYLE)
        for _group_name, _group_meta in metadata.items():
            _group_values = _settings if len(_group_name) == 0 else _settings.get(_group_name)
            if _group_values is None:
                if _group_meta[META_KEY_OPT]:
                    continue
                raise IssaiException(W_GUI_READ_SETTINGS_FAILED, file_path, f'Mandatory group {_group_name} missing')
            _tab = self._create_tab(_group_name, _group_meta, _group_values)
            if _tab is not None:
                _tabs.addTab(_tab, f'[{_group_name}]')
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
                    self._write_settings()
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
        _tab = QWidget(self)
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

    def _read_settings(self):
        """
        Reads settings from file.
        :rtype: dict
        :raises IssaiException: if file is malformed
        """
        if not os.path.isfile(self.__file_path):
            return ConfigEditor._default_settings(self.__meta_data)
        # noinspection PyBroadException
        try:
            _data = {}
            if self.__file_type == _FILE_TYPE_XML_RPC_CREDENTIALS:
                # TOML with unquoted string values (XML-RPC credentials file)
                _current_grp = ''
                with open(self.__file_path, 'r') as _f:
                    _line = _f.readline()
                    while _line:
                        _line = _line.strip()
                        if len(_line) == 0:
                            _line = _f.readline()
                            continue
                        if re.match(r'\s*#', _line):
                            self.__comments_skipped = True
                            _line = _f.readline()
                            continue
                        for _group_name, _group_meta in self.__meta_data.items():
                            _grp_pattern = rf'\s*\[{_group_name}\]'
                            _m = re.match(_grp_pattern, _line)
                            if _m:
                                _current_grp = _group_name
                                _data[_current_grp] = {}
                                break
                            for _a in _group_meta[META_KEY_ATTRS]:
                                _attr_name = _a[META_KEY_ATTR_NAME]
                                _attr_pattern = rf'\s*{_attr_name}\s*=\s*(.*)$'
                                _m = re.match(_attr_pattern, _line)
                                if _m:
                                    if len(_current_grp) == 0:
                                        _data[_attr_name] = _m.group(1)
                                    else:
                                        _data[_current_grp][_attr_name] = _m.group(1)
                                    break
                        _line = _f.readline()
            else:
                # plain TOML (issai configuration files)
                with open(self.__file_path, 'r') as _f:
                    _data = tomlkit.load(_f)
            ConfigEditor._fill_mandatory_attributes(_data, self.__meta_data)
            return _data
        except Exception as _e:
            raise IssaiException(W_GUI_READ_SETTINGS_FAILED, self.__file_path, _e)

    def _write_settings(self):
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
                    for _k, _v in _settings.items():
                        if isinstance(_v, dict):
                            _f.write(f'[{_k}]{os.linesep}')
                            for _ak, _av in _v.items():
                                _f.write(f'{_ak} = {str(_av)}{os.linesep}')
                        else:
                            _f.write(f'{_k} = {str(_v)}{os.linesep}')
                else:
                    # plain TOML (issai configuration files)
                    tomlkit.dump(_settings, _f)
        except Exception as _e:
            raise IssaiException(E_GUI_WRITE_SETTINGS_FAILED, self.__file_path, _e)

    @staticmethod
    def _fill_mandatory_attributes(settings, metadata):
        """
        Adds mandatory attributes if missing.
        :param dict settings: the settings
        :param dict metadata: the metadata describing supported attributes and their types
        """
        _defaults = ConfigEditor._default_settings(metadata)
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
    def _default_settings(metadata):
        """
        Returns default settings based on the metadata definitions.
        :param dict metadata: metadata with all TOML groups and attributes
        :returns: default settings
        :rtype: dict
        """
        _data = {}
        for _group_name, _group_meta in metadata.items():
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


_ATTR_NAME_STYLE = 'font-weight: bold'
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
