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
Personal settings for the Issai GUI.
"""

import os
import tomlkit

from PySide6 import QtGui
from PySide6.QtCore import QRect

from issai.core import ENTITY_TYPE_CASE, ISSAI_CONFIG_PATH, ISSAI_GUI_SETTINGS_FILE_NAME
from issai.core.issai_exception import IssaiException
from issai.core.messages import W_GUI_WRITE_GUI_CONFIGURATION_FAILED
from issai.core.util import full_path_of


class GuiSettings(dict):
    """
    Holds user specific settings and preferences of the Issai GUI.
    """
    def __init__(self):
        """
        Constructor.
        """
        super().__init__()

    def lru_entities(self, entity_type):
        """
        Returns recently used test entities for specified type, the latest ones first.
        :param int entity_type: the entity type (test case or test plan)
        :returns: recently used entities
        :rtype: list
        """
        _key = entity_type == ENTITY_TYPE_CASE and _KEY_LRU_CASES or _KEY_LRU_PLANS
        _lru_list = self.get(_key)
        return [] if _lru_list is None else _lru_list

    def entity_used(self, entity_type, entity_id, entity_name):
        """
        :param int entity_type: the entity type (test case or test plan)
        :param int entity_id: the TCMS entity ID
        :param str entity_name: the TCMS entity name
        :returns: recently used test entities for specified type, the latest ones first
        :rtype: list
        """
        _entity_info = '%s %s' % (str(entity_id), entity_name.strip())
        _key = _KEY_LRU_CASES if entity_type == ENTITY_TYPE_CASE else _KEY_LRU_PLANS
        _lru_list = self.get(_key)
        if _lru_list is None:
            self[_key] = [_entity_info]
            return
        for _i, _v in enumerate(_lru_list):
            if _v == _entity_info:
                if _i > 0:
                    for _j in range(_i, 0, -1):
                        _lru_list[_j] = _lru_list[_j-1]
                    _lru_list[0] = _entity_info
                return
        _lru_list.insert(0, _entity_info)
        if len(_lru_list) > self.max_lru_size():
            del _lru_list[-1]

    def entity_not_found(self, entity_type, entity_info):
        """
        Removes an entity from LRU list.
        :param int entity_type: the entity type (test case or test plan)
        :param str entity_info: the entity info string, TCMS entity ID - entity name
        """
        _key = _KEY_LRU_CASES if entity_type == ENTITY_TYPE_CASE else _KEY_LRU_PLANS
        _lru_list = self.get(_key)
        if _lru_list is None:
            return
        for _i, _v in enumerate(_lru_list):
            if _v == entity_info:
                del _lru_list[_i]
                return

    def latest_input_dir(self):
        """
        :returns: latest directory used to read a file for execution or import
        :rtype: str
        """
        _value = self.get(_KEY_LATEST_INPUT_DIR)
        return full_path_of(_DEFAULT_DIR) if _value is None else _value

    def latest_output_dir(self):
        """
        :returns: latest directory used for file export
        :rtype: str
        """
        _value = self.get(_KEY_LATEST_OUTPUT_DIR)
        return full_path_of(_DEFAULT_DIR) if _value is None else _value

    def max_lru_size(self):
        """
        :returns: maximum number of elements in a list of recently used entities
        :rtype: int
        """
        _value = self.get(_KEY_MAX_LRU_LIST_SIZE)
        return _DEFAULT_MAX_LRU_LIST_SIZE if _value is None else _value

    def win_geometry(self):
        """
        :returns: latest geometry of main window
        :rtype: QRect
        """
        _value = self.get(_KEY_WIN_GEOMETRY)
        return QRect(*_default_win_geometry()) if _value is None else QRect(*_value)

    def set_latest_input_dir(self, path):
        """
        Sets the latest directory used for file import
        :param str path: full directory of most recently used import file
        """
        self[_KEY_LATEST_INPUT_DIR] = path

    def set_latest_output_dir(self, path):
        """
        Sets the latest directory used for file export
        :param str path: most recently used path for an export
        """
        self[_KEY_LATEST_OUTPUT_DIR] = path

    def set_win_geometry(self, geometry):
        """
        Sets the geometry of main window
        :param QRect geometry: geometry of main window
        """
        self[_KEY_WIN_GEOMETRY] = (geometry.x(), geometry.y(), geometry.width(), geometry.height())

    def save(self):
        """
        Saves personal settings to file.
        :raises IssaiException: if settings could not be saved
        """
        # noinspection PyBroadException
        _file_name = os.path.join(full_path_of(ISSAI_CONFIG_PATH), ISSAI_GUI_SETTINGS_FILE_NAME)
        try:
            with open(_file_name, 'w') as _f:
                tomlkit.dump(self, _f)
        except Exception as e:
            raise IssaiException(W_GUI_WRITE_GUI_CONFIGURATION_FAILED, _file_name, str(e))

    @staticmethod
    def default():
        """
        Creates and returns default settings.
        :returns: default Issai GUI settings
        :rtype: GuiSettings
        """
        _settings = GuiSettings()
        _settings[_KEY_MAX_LRU_LIST_SIZE] = _DEFAULT_MAX_LRU_LIST_SIZE
        _settings[_KEY_LRU_CASES] = []
        _settings[_KEY_LRU_PLANS] = []
        _settings[_KEY_LATEST_INPUT_DIR] = full_path_of(_DEFAULT_DIR)
        _settings[_KEY_LATEST_OUTPUT_DIR] = full_path_of(_DEFAULT_DIR)
        _settings[_KEY_WIN_GEOMETRY] = _DEFAULT_WIN_GEOMETRY
        return _settings

    @staticmethod
    def load():
        """
        Loads personal settings from file.
        Returns default settings, if file can't be read.
        :returns: Issai GUI settings
        :rtype: GuiSettings
        """
        # noinspection PyBroadException
        try:
            _file_name = os.path.join(full_path_of(ISSAI_CONFIG_PATH), ISSAI_GUI_SETTINGS_FILE_NAME)
            with open(_file_name, 'r') as _f:
                _persistent_settings = tomlkit.load(_f)
            _settings = GuiSettings()
            for _k, _v in _persistent_settings.items():
                _settings[_k] = _v
            return _settings
        except Exception:
            return GuiSettings.default()


def _default_win_geometry():
    """
    :returns: default window geometry
    :rtype: (int,int,int,int)
    """
    _screen_geometry = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    _width = min(1280, _screen_geometry.width())
    _height = min(960, _screen_geometry.height())
    return 0, 0, _width, _height


_DEFAULT_MAX_LRU_LIST_SIZE = 4
_DEFAULT_DIR = '~'
_DEFAULT_WIN_GEOMETRY = [0, 0, 1280, 960]
_KEY_LATEST_INPUT_DIR = 'latest_input_dir'
_KEY_LATEST_OUTPUT_DIR = 'latest_output_dir'
_KEY_LRU_CASES = 'lru_cases'
_KEY_LRU_PLANS = 'lru_plans'
_KEY_MAX_LRU_LIST_SIZE = 'max_lru_list_size'
_KEY_WIN_GEOMETRY = 'win_geometry'
