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
import tomlkit

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
        :param list metadata: the metadata describing supported attributes and their types
        :param dict settings: the actual settings to edit
        """
        super().__init__()
        for _group in metadata:
            _group_name = _group[_META_KEY_GROUP]
            if len(_group_name) > 0:
                _group_name += '.'
            _attrs = _group[_META_KEY_ATTRS]
            for _attr in _attrs:
                _attr_name = _attr[_META_KEY_ATTR_NAME]
                _attr_id = '%s%s' % (_group_name, _attr_name)
                _attr_type = _attr[_META_KEY_ATTR_TYPE]
                _attr_value = EditorData._attr_value(settings, _attr_id)
                if _attr_value is None:
                    continue
                self[_attr_id] = {}
                self[_attr_id][_DATA_KEY_ATTR_TYPE] = _attr_type
                self[_attr_id][_DATA_KEY_ATTR_VALUE] = _attr_value
                self[_attr_id][_DATA_KEY_WIDGET] = None

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
        if _attr_type == _META_TYPE_STR or _attr_type == _META_TYPE_PASSWORD:
            # QLineEdit
            return _widget.text()
        if _attr_type == _META_TYPE_INT:
            # QLineEdit
            return int(_widget.text())
        if _attr_type == _META_TYPE_BOOLEAN:
            # QCheckBox
            return _widget.isChecked()
        if _attr_type == _META_TYPE_STR_LIST:
            # QLineEdit
            _value = _widget.text().strip()
            return [] if len(_value) == 0 else [_item.strip() for _item in _value.split(',')]
        if _attr_type == _META_TYPE_INT_LIST:
            # QLineEdit
            _value = _widget.text().strip()
            return [] if len(_value) == 0 else [int(_item.strip()) for _item in _value.split(',')]
        if _attr_type.startswith(_META_TYPE_ENUM):
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


class TomlEditor(QDialog):
    """
    Dialog window to edit TOML based settings.
    """

    def __init__(self, parent, title, metadata, file_path, file_type):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str title: the dialog window title
        :param list metadata: the metadata describing supported attributes and their types
        :param str file_path: the name of the file containing the data to edit including path
        :param int file_type: the file type (plain TOML or unquoted TOML)
        """
        super().__init__(parent)
        try:
            _settings = TomlEditor._read_settings(file_path, file_type, metadata)
        except IssaiException as _e:
            _msg_box = exception_box(QMessageBox.Icon.Warning, _e,
                                     localized_label(L_MBOX_INFO_USE_DEFAULT_SETTINGS),
                                     QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Ok)
            if _msg_box.exec() == QMessageBox.StandardButton.Cancel:
                raise
            _settings = TomlEditor._default_settings(metadata)
        self.setWindowTitle(title)
        self.__meta_data = metadata
        self.__file_path = file_path
        self.__file_type = file_type
        self.__editor_data = EditorData(metadata, _settings)
        _layout = QVBoxLayout()
        _tabs = QTabWidget(self)
        _tabs.setStyleSheet(_TABS_STYLE)
        for _group in metadata:
            _group_name = _group[_META_KEY_GROUP]
            _group_values = _settings if len(_group_name) == 0 else _settings.get(_group_name)
            if _group_values is None:
                if _group[_META_KEY_OPT]:
                    continue
                raise IssaiException(W_GUI_READ_SETTINGS_FAILED, file_path, f'Mandatory group {_group_name} missing')
            _tab = self._create_tab(_group, _group_values)
            if _tab is not None:
                _tabs.addTab(_tab, '[%s]' % _group_name)
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
        # TODO check for user or URL changes and reinit TCMS interface
        if self.__editor_data.is_changed():
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

    def _create_tab(self, group_meta, group_data):
        """
        Creates a tab to allow editing attributes of a specific group.
        Closes the dialog window, if the settings were not changed.
        Asks for confirmation to discard changes, if the settings were edited.
        :param dict group_meta: the metadata group descriptor
        :param dict group_data: the group descriptor
        """
        _tab = QWidget(self)
        _tab_layout = QFormLayout()
        _group_name = group_meta[_META_KEY_GROUP]
        if len(_group_name) > 0:
            _group_name += '.'
        _attributes = group_meta[_META_KEY_ATTRS]
        for _a in _attributes:
            _attr_name = _a[_META_KEY_ATTR_NAME]
            _attr_id = '%s%s' % (_group_name, _attr_name)
            _attr_type = _a[_META_KEY_ATTR_TYPE]
            _attr_is_optional = _a[_META_KEY_OPT]
            _attr_value = group_data.get(_attr_name)
            if _a[_META_KEY_OPT] and _attr_value is None:
                continue
            _attr_label = QLabel(_attr_name)
            _attr_label.setStyleSheet(_ATTR_NAME_STYLE)
            if _attr_type in [_META_TYPE_STR, _META_TYPE_PASSWORD, _META_TYPE_INT]:
                _attr_widget = QLineEdit()
                _attr_widget.setFixedWidth(400)
                if _attr_type == _META_TYPE_PASSWORD:
                    _attr_widget.setEchoMode(QLineEdit.EchoMode.Password)
                _attr_widget.setText(_attr_value)
            elif _attr_type == _META_TYPE_BOOLEAN:
                _attr_widget = QCheckBox()
                _attr_widget.setChecked(_attr_value)
            elif _attr_type == _META_TYPE_STR_LIST or _attr_type == _META_TYPE_INT_LIST:
                _attr_widget = QLineEdit()
                _attr_widget.setFixedWidth(400)
                _attr_widget.setText(','.join(_attr_value))
            elif _attr_type.startswith(_META_TYPE_ENUM):
                _enum_values = _attr_type[2:].split(',')
                _attr_widget = QComboBox()
                for _v in _enum_values:
                    _attr_widget.addItem(_v)
                _attr_widget.setCurrentText(_attr_value)
            else:
                _emsg = localized_message(E_GUI_SETTINGS_META_DEFINITION, _attr_id)
                _ex = IssaiException(E_INTERNAL_ERROR, _emsg)
                _msg_box = exception_box(QMessageBox.Icon.Critical, _ex, '',
                                         QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                _msg_box.exec()
                raise _ex
            _tab_layout.addRow(_attr_label, _attr_widget)
            self.__editor_data[_attr_id][_DATA_KEY_WIDGET] = _attr_widget
        _tab.setLayout(_tab_layout)
        return _tab

    @staticmethod
    def _read_settings(file_path, file_type, metadata):
        """
        Reads settings from file.
        :param str file_path: the name of the input file
        :param int file_type: the type of the input file (plain or unquoted TOML)
        :param list metadata: the metadata describing supported attributes and their types
        :returns: settings from file
        :rtype: dict
        :raises IssaiException: if file is malformed
        """
        if not os.path.isfile(file_path):
            return TomlEditor._default_settings(metadata)
        # noinspection PyBroadException
        try:
            _data = {}
            if file_type == _FILE_TYPE_PLAIN_TOML:
                with open(file_path, 'r') as _f:
                    _data = tomlkit.load(_f)
            elif file_type == _FILE_TYPE_UNQUOTED_TOML:
                _current_grp = ''
                with open(file_path, 'r') as _f:
                    _line = _f.readline()
                    while _line:
                        _line = _line.strip()
                        if len(_line) == 0:
                            _line = _f.readline()
                            continue
                        for _grp in metadata:
                            _grp_pattern = r'\[%s\]' % _grp[_META_KEY_GROUP]
                            _m = re.search(_grp_pattern, _line)
                            if _m:
                                _current_grp = _grp[_META_KEY_GROUP]
                                _data[_current_grp] = {}
                                break
                            for _a in _grp[_META_KEY_ATTRS]:
                                _attr_name = _a[_META_KEY_ATTR_NAME]
                                _attr_pattern = r'\s*%s\s*=\s*(.*)$' % _attr_name
                                _m = re.search(_attr_pattern, _line)
                                if _m:
                                    if len(_current_grp) == 0:
                                        _data[_attr_name] = _m.group(1)
                                    else:
                                        _data[_current_grp][_attr_name] = _m.group(1)
                                    break
                        _line = _f.readline()
            TomlEditor._fill_mandatory_attributes(_data, metadata)
            return _data
        except Exception as _e:
            raise IssaiException(W_GUI_READ_SETTINGS_FAILED, file_path, _e)

    def _write_settings(self):
        """
        Writes given settings to file.
        :raises IssaiException: if settings can't be saved to file
        """
        # noinspection PyBroadException
        _settings = self.__editor_data.settings()
        try:
            with open(self.__file_path, 'w') as _f:
                if self.__file_type == _FILE_TYPE_PLAIN_TOML:
                    # plain TOML (issai configuration files)
                    tomlkit.dump(_settings, _f)
                elif self.__file_type == _FILE_TYPE_UNQUOTED_TOML:
                    # TOML with unquoted string values (XML-RPC credentials file)
                    for _k, _v in _settings.items():
                        if isinstance(_v, dict):
                            _f.write('[%s]%s' % (_k, os.linesep))
                            for _ak, _av in _v.items():
                                _f.write('%s = %s%s' % (_ak, str(_av), os.linesep))
                        else:
                            _f.write('%s = %s%s' % (_k, str(_v), os.linesep))
        except Exception as _e:
            raise IssaiException(E_GUI_WRITE_SETTINGS_FAILED, self.__file_path, _e)

    @staticmethod
    def _fill_mandatory_attributes(settings, metadata):
        """
        Adds mandatory attributes if missing.
        :param dict settings: the settings
        :param list metadata: the metadata describing supported attributes and their types
        """
        _defaults = TomlEditor._default_settings(metadata)
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
        :param list metadata: metadata with all TOML groups and attributes
        :returns: default settings
        :rtype: dict
        """
        _data = {}
        for _grp in metadata:
            if _grp[_META_KEY_OPT]:
                continue
            _group_name = _grp[_META_KEY_GROUP]
            if len(_group_name) > 0:
                _data[_group_name] = {}
            _attributes = _grp[_META_KEY_ATTRS]
            for _a in _attributes:
                if _a[_META_KEY_OPT]:
                    continue
                _attr_name = _a[_META_KEY_ATTR_NAME]
                _attr_value = _a[_META_KEY_ATTR_DEFAULT_VALUE]
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
    :rtype: TomlEditor
    :raises IssaiException: if the editor can't be created
    """
    _master_config_file_path = os.path.join(full_path_of(ISSAI_CONFIG_PATH), ISSAI_MASTER_CONFIG_FILE_NAME)
    return TomlEditor(parent, localized_label(L_DLG_TITLE_MASTER_CONFIG_EDITOR), _MASTER_META,
                      _master_config_file_path, _FILE_TYPE_PLAIN_TOML)


def product_config_editor(parent, products):
    """
    Creates and returns a dialog window to edit an Issai product configuration file
    :param QWidget parent: the parent widget
    :param list products: the parent widget
    :returns: Dialog window to edit Issai product configuration file
    :rtype: TomlEditor
    :raises IssaiException: if the editor can't be created
    """
    _sel_dlg = IssaiProductSelectionDialog(parent, products)
    if _sel_dlg.exec() == 0:
        return
    _product_config_dir_path = _sel_dlg.selected_product_config_path()
    _product_config_file_path = os.path.join(_product_config_dir_path, ISSAI_PRODUCT_CONFIG_FILE_NAME)
    _dlg_title = localized_message(L_DLG_TITLE_PRODUCT_CONFIG_EDITOR, os.path.basename(_product_config_dir_path))
    return TomlEditor(parent, _dlg_title, _PRODUCT_META,
                      _product_config_file_path, _FILE_TYPE_PLAIN_TOML)


def xml_rpc_credentials_editor(parent):
    """
    Creates and returns a dialog window to edit the credentials for XML-RPC communication with Kiwi TCMS
    :param QWidget parent: the parent widget
    :returns: Dialog window to edit XML-RPC credentials
    :rtype: TomlEditor
    :raises IssaiException: if the editor can't be created
    """
    return TomlEditor(parent, localized_label(L_DLG_TITLE_XML_RPC_EDITOR), _XML_RPC_META,
                      full_path_of(TCMS_XML_RPC_CREDENTIALS_FILE_PATH), _FILE_TYPE_UNQUOTED_TOML)


_ATTR_NAME_STYLE = 'font-weight: bold'
_TABS_STYLE = 'QTabBar {font-weight: bold}'

_DATA_KEY_ATTR_TYPE = 'type'
_DATA_KEY_ATTR_VALUE = 'value'
_DATA_KEY_WIDGET = 'widget'

_FILE_TYPE_PLAIN_TOML = 1
_FILE_TYPE_UNQUOTED_TOML = 2

_META_KEY_COMMENT = 'comment'
_META_KEY_GROUP = 'group'
_META_KEY_ATTR_DEFAULT_VALUE = 'default'
_META_KEY_ATTR_NAME = 'name'
_META_KEY_ATTR_TYPE = 'type'
_META_KEY_ATTRS = 'attributes'
_META_KEY_OPT = 'optional'

_META_TYPE_BOOLEAN = 'b'
_META_TYPE_ENUM = 'e'
_META_TYPE_INT = 'i'
_META_TYPE_INT_LIST = 'li'
_META_TYPE_LABEL_SCHEME = 'e:none,version,build'
_META_TYPE_LIST = 'l'
_META_TYPE_PRODUCT_NATURE = 'e:executable,dynamic-library,static-library'
_META_TYPE_PASSWORD = 'p'
_META_RESULT_MANAGEMENT = 'e:auto,manual'
_META_TYPE_SPEC_MANAGEMENT = 'e:auto,manual'
_META_TYPE_STR = 's'
_META_TYPE_STR_LIST = 'ls'

_MASTER_META = [{_META_KEY_GROUP: '', _META_KEY_OPT: True,
                 _META_KEY_ATTRS: [
                     {_META_KEY_ATTR_NAME: 'mini-part-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                      _META_KEY_ATTR_DEFAULT_VALUE: '',
                      _META_KEY_OPT: True,
                      _META_KEY_COMMENT: 'path to small partition for testing "file system full" behaviour'},
                     {_META_KEY_ATTR_NAME: 'read-only-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                      _META_KEY_ATTR_DEFAULT_VALUE: '',
                      _META_KEY_OPT: True,
                      _META_KEY_COMMENT: 'path without write permission'},
                     {_META_KEY_ATTR_NAME: 'testing-root-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                      _META_KEY_ATTR_DEFAULT_VALUE: '',
                      _META_KEY_OPT: True,
                      _META_KEY_COMMENT: 'root path for runtime data'},
                 ]
                 }]

_PRODUCT_META = [{_META_KEY_GROUP: 'product', _META_KEY_OPT: False,
                  _META_KEY_ATTRS: [
                      {_META_KEY_ATTR_NAME: 'name', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: False,
                       _META_KEY_COMMENT: 'product name as defined in Kiwi TCMS, case sensitive'},
                      {_META_KEY_ATTR_NAME: 'nature', _META_KEY_ATTR_TYPE: _META_TYPE_PRODUCT_NATURE,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: False,
                       _META_KEY_COMMENT: 'product nature: executable, dynamic-library, static-library'},
                      {_META_KEY_ATTR_NAME: 'repository-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: False,
                       _META_KEY_COMMENT: 'path of repository containing the product files'},
                      {_META_KEY_ATTR_NAME: 'source-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'root path for product source code, '
                                          'defaults to subdirectory src under repository path'},
                      {_META_KEY_ATTR_NAME: 'test-data-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'root path for test data files, '
                                          'defaults to subdirectory testdata under repository path'},
                      {_META_KEY_ATTR_NAME: 'locales', _META_KEY_ATTR_TYPE: _META_TYPE_STR_LIST,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'locales supported by product, defaults to ["en"]'},
                  ]
                  },
                 {_META_KEY_GROUP: 'tcms', _META_KEY_OPT: True,
                  _META_KEY_ATTRS: [
                      {_META_KEY_ATTR_NAME: 'label-scheme', _META_KEY_ATTR_TYPE: _META_TYPE_LABEL_SCHEME,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'labeling scheme for test runs and executions; none, version or build'},
                      {_META_KEY_ATTR_NAME: 'spec-management', _META_KEY_ATTR_TYPE: _META_TYPE_SPEC_MANAGEMENT,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'management of test runs and executions; auto or manual'},
                      {_META_KEY_ATTR_NAME: 'result-management', _META_KEY_ATTR_TYPE: _META_RESULT_MANAGEMENT,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'management of test results; auto or manual'},
                      {_META_KEY_ATTR_NAME: 'relevant-attachments', _META_KEY_ATTR_TYPE: _META_TYPE_STR_LIST,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'list of attachment file names to be downloaded for tests'},
                      {_META_KEY_ATTR_NAME: 'permuting-properties', _META_KEY_ATTR_TYPE: _META_TYPE_STR_LIST,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'list of property names triggering repeated execution of test cases '
                                          'for all value items of the property'},
                  ]
                  },
                 {_META_KEY_GROUP: 'build', _META_KEY_OPT: True,
                  _META_KEY_ATTRS: [
                      {_META_KEY_ATTR_NAME: 'build-before-test', _META_KEY_ATTR_TYPE: _META_TYPE_BOOLEAN,
                       _META_KEY_ATTR_DEFAULT_VALUE: True,
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'indicator whether to build product before test'},
                      {_META_KEY_ATTR_NAME: 'target-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'path for compiled sources'},
                      {_META_KEY_ATTR_NAME: 'profile', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'build profile to use'},
                      {_META_KEY_ATTR_NAME: 'features', _META_KEY_ATTR_TYPE: _META_TYPE_STR_LIST,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'features to use for build'},
                  ]
                  },
                 {_META_KEY_GROUP: 'runner', _META_KEY_OPT: False,
                  _META_KEY_ATTRS: [
                      {_META_KEY_ATTR_NAME: 'working-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '/tmp',
                       _META_KEY_OPT: False,
                       _META_KEY_COMMENT: 'working directory for the tests'},
                      {_META_KEY_ATTR_NAME: 'test-driver-executable', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'name of test driver executable including path'},
                      {_META_KEY_ATTR_NAME: 'product-executable', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'name of product executable including path'},
                      {_META_KEY_ATTR_NAME: 'locale', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: 'en',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'locale to use for the test'},
                      {_META_KEY_ATTR_NAME: 'custom-module-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'python module with custom functions for test execution'},
                      {_META_KEY_ATTR_NAME: 'custom-script-path', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                       _META_KEY_ATTR_DEFAULT_VALUE: '',
                       _META_KEY_OPT: True,
                       _META_KEY_COMMENT: 'path of custom python scripts for test execution'},
                  ]
                  },
                 ]

_XML_RPC_META = [{_META_KEY_GROUP: 'tcms', _META_KEY_OPT: False,
                  _META_KEY_ATTRS: [{_META_KEY_ATTR_NAME: 'url', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                                     _META_KEY_ATTR_DEFAULT_VALUE: 'https://localhost/xml-rpc/',
                                     _META_KEY_OPT: False},
                                    {_META_KEY_ATTR_NAME: 'username', _META_KEY_ATTR_TYPE: _META_TYPE_STR,
                                     _META_KEY_ATTR_DEFAULT_VALUE: '',
                                     _META_KEY_OPT: False},
                                    {_META_KEY_ATTR_NAME: 'password', _META_KEY_ATTR_TYPE: _META_TYPE_PASSWORD,
                                     _META_KEY_ATTR_DEFAULT_VALUE: '',
                                     _META_KEY_OPT: False}
                                    ]
                  }]
