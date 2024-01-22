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
Issai runtime configuration.
The framework is configured by files located under Issai configuration directory. This directory
can be specified in environment variable ISSAI_CONFIG_PATH, it defaults to $HOME/.config/issai.
If there is a file named default.toml, it is considered as master configuration for all products.
For each product, there must be a subdirectory with the Issai product name and inside the subdirectory
a file product.toml containing product specific configuration.
During test execution, the configuration may be updated from attachment files contained in test plans
or test cases.
"""

import importlib
import importlib.util
import re
import sys

import tomlkit

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.util import full_path_of


_DEFAULT_CONFIG_PATH = '~/.config/issai'
_MASTER_CFG_FILE_NAME = 'default.toml'
_PRODUCT_CFG_FILE_NAME = 'product.toml'


class LocalConfig(dict):
    """
    Holds attributes specific to local environment.
    """
    def __init__(self, root_path):
        """
        Constructor.
        :param str root_path: the issai configuration root directory
        """
        super().__init__()
        self.__custom_module = None
        self.__custom_script_path = None
        self.__config_root = root_path

    def root_path(self):
        """
        :returns: root path of issai configuration
        :rtype: str
        """
        return self.__config_root

    def issai_name(self):
        """
        :returns: product name used in Issai
        :rtype: str
        """
        return self[CFG_GROUP_PRODUCT]['issai-name']

    def tcms_name(self):
        """
        :returns: product name used in TCMS
        :rtype: str
        """
        return self[CFG_GROUP_PRODUCT]['name']

    def localized_label_scheme(self):
        """
        :returns: label scheme as localized string
        :rtype: str
        """
        _scheme = self.get_value(CFG_PAR_TCMS_LABEL_SCHEME)
        if _scheme is not None:
            if _scheme == 'none':
                return localized_label(L_TYPE_LABEL_SCHEME_NONE)
            elif _scheme == 'build':
                return localized_label(L_TYPE_LABEL_SCHEME_BUILD)
        return localized_label(L_TYPE_LABEL_SCHEME_VERSION)

    def download_patterns_match(self, file_name):
        """
        :param str file_name: the pure file name
        :returns: True, if specified file name must be downloaded as attachment
        :rtype: bool
        """
        return self.attachment_patterns_match(CFG_PAR_TCMS_SPEC_ATTACHMENTS, file_name)

    def upload_patterns_match(self, file_name):
        """
        :param str file_name: the pure file name
        :returns: True, if specified file name must be uploaded as attachment
        :rtype: bool
        """
        return self.attachment_patterns_match(CFG_PAR_TCMS_RESULT_ATTACHMENTS, file_name)

    def attachment_patterns_match(self, cfg_par, file_name):
        """
        Indicates whether patterns defined for TCMS attachments match given pure file name.
        :param str cfg_par: the configuration parameter
        :param str file_name: the pure file name
        :returns: True, if specified file name must be treated as attachment
        :rtype: bool
        """
        _patterns = self.get_list_value(cfg_par)
        if _patterns is not None:
            for _pattern in _patterns:
                if re.match(_pattern, file_name):
                    return True
        return False

    def custom_function(self, function_name):
        """
        Returns pointer to custom function with specified name.
        :param str function_name: the name of the function
        :returns: custom function pointer
        :rtype: function
        :raises IssaiException: if custom module path is not defined or function doesn't exist in module
        """
        if self.__custom_module is None:
            _mod_path = self.get_str_value(CFG_PAR_RUNNER_CUSTOM_MODULE_PATH)
            if _mod_path is None:
                raise IssaiException(E_CFG_CUSTOM_MOD_NOT_DEFINED)
            if not os.path.isfile(_mod_path):
                raise IssaiException(E_CFG_CUSTOM_MOD_NOT_FOUND, _mod_path)
            try:
                _mod_dir = os.path.dirname(_mod_path)
                if _mod_dir not in sys.path:
                    sys.path.append(_mod_dir)
                _mod_name = os.path.basename(_mod_path)[:-3]
                module = importlib.import_module(_mod_name)
                return getattr(module, function_name)
            except BaseException as _e:
                raise IssaiException(E_CFG_CUSTOM_MOD_INVALID, _mod_path, str(_e))
        raise IssaiException(E_CFG_CUSTOM_RUNNER_FN_NOT_FOUND, function_name)

    def custom_script(self, script_name):
        """
        Returns full path of custom script with specified name.
        :param str script_name: the name of the script
        :returns: full script path
        :rtype: str
        :raises IssaiException: if custom script path is not defined or script doesn't exist in that path
        """
        if self.__custom_script_path is None:
            _script_dir = self.get_str_value(CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH)
            if _script_dir is None:
                raise IssaiException(E_CFG_CUSTOM_SCRIPT_PATH_NOT_DEFINED)
            if not os.path.isdir(_script_dir):
                raise IssaiException(E_CFG_CUSTOM_SCRIPT_PATH_NOT_FOUND, _script_dir)
            self.__custom_script_path = _script_dir
            _script_path = os.path.join(_script_dir, script_name)
            if not os.path.isfile(_script_path):
                raise IssaiException(E_CFG_CUSTOM_SCRIPT_NOT_FOUND, _script_path)
            return _script_path

    def output_log(self):
        """
        :returns: pure name of output file where to store console output from test execution
        :rtype: str
        """
        return self.get_str_value(CFG_PAR_RUNNER_OUTPUT_LOG, DEFAULT_OUTPUT_LOG)

    def custom_execution_status(self, issai_status_name):
        """
        Returns the execution status name from local configuration.
        :param str issai_status_name: the internal default status name
        :returns: matching customized status name
        :rtype: str
        """
        _mapping = self.get_value(CFG_PAR_TCMS_EXECUTION_STATES)
        if _mapping is None:
            return issai_status_name
        _custom_value = _mapping.get(issai_status_name)
        return issai_status_name if _custom_value is None else _custom_value

    def merged_copy(self, other):
        """
        Returns a copy of this configuration with attributes from given other configuration merged, i.e. if an item is
        present both in this and other configuration, value from other takes precedence.
        :param dict other: configuration to merge
        :returns: LocalConfig
        """
        _clone = LocalConfig(_config_root_path())
        _clone.update(self)
        _clone.update(other)
        return _clone

    @staticmethod
    def from_file(file_path, is_master=False):
        """
        Creates runtime configuration from TOML file.
        :param str file_path: name of configuration file including full path
        :param bool is_master: indicates whether the file contains Issai master configuration (True) or a product
                               configuration (False)
        :returns: runtime configuration
        :rtype: LocalConfig
        :raises IssaiException: if file cannot be processed
        """
        try:
            _cfg = LocalConfig(os.path.dirname(file_path))
            with open(file_path, 'r') as _f:
                _file_data = tomlkit.load(_f)
            # TODO check mandatory attributes, if file is a product config
            if not is_master:
                _file_data[CFG_GROUP_PRODUCT]['issai-name'] = os.path.basename(os.path.dirname(file_path))
            return _cfg.merged_copy(_file_data)
        except Exception as e:
            raise IssaiException(E_CFG_READ_FILE_FAILED, file_path, e)

    def __lt__(self, other):
        """
        :param LocalConfig other: the local configuration to compare with this one
        :returns: True, if this local configuration's Issai name is less than the specified other configuration's
        :rtype: bool
        """
        return self[CFG_GROUP_PRODUCT]['issai-name'] < other[CFG_GROUP_PRODUCT]['issai-name']

    def get_value(self, dotted_key, default_value=None):
        """
        Returns the value associated with the specified key. Dotted keys are automatically converted to tree.
        :param str p_dotted_key: the dotted key
        :param p_default_value: the value to return, if key is not defined
        :returns: value associated with key; None, if key is not defined
        """
        if dotted_key.find('.') < 0:
            _val = self.get(dotted_key)
            return default_value if _val is None else _val
        _node = self
        _key_parts = dotted_key.split('.')
        for _key_part in _key_parts:
            if _key_part not in _node:
                return default_value
            _node = _node[_key_part]
        return _node

    def get_str_value(self, dotted_key, default_value=None):
        """
        Returns the value associated with the specified key. Dotted keys are automatically converted to tree.
        :param str dotted_key: the dotted key
        :param str default_value: the value to return, if key is not defined
        :returns: value associated with key; None, if key is not defined
        :rtype: str
        """
        _value = self.get_value(dotted_key, default_value)
        if _value is None:
            return None
        if not isinstance(_value, str):
            raise IssaiException(E_CFG_INVALID_DATA_TYPE, dotted_key, 'str')
        return self._resolved_value_of(dotted_key, _value)

    def get_list_value(self, dotted_key, default_value=None):
        """
        Returns the value associated with the specified key. Dotted keys are automatically converted to tree.
        :param str dotted_key: the dotted key
        :param list default_value: the value to return, if key is not defined
        :returns: value associated with key; None, if key is not defined
        :rtype: list
        """
        _value = self.get_value(dotted_key, default_value)
        if _value is None:
            return None
        if isinstance(_value, str):
            _value = [_value]
        elif not isinstance(_value, list):
            raise IssaiException(E_CFG_INVALID_DATA_TYPE, dotted_key, 'list, str')
        for i in range(0, len(_value)):
            _elem = _value[i]
            _literal_elem = self.literal_value(_elem)
            _value[i] = _literal_elem
        return _value

    def _resolved_value_of(self, dotted_key, value):
        if isinstance(value, str):
            _last_dot_pos = dotted_key.rfind('.')
            _parent_key = '' if _last_dot_pos < 0 else dotted_key[0:_last_dot_pos]
            _value = value
            _pattern = re.compile(r'\$\{.*}')
            _m = _pattern.search(_value)
            while _m is not None:
                _var = _value[_m.start():_m.end()]
                _value = _value.replace(_var, self.variable_value(_var, _parent_key), 1)
                _m = _pattern.search(_value)
            return _value
        return [self._resolved_value_of(dotted_key, _v) for _v in value]

    def literal_value(self, value):
        """
        Returns value with all variables replaced.
        :param str value: the value, eventually containing variables
        :returns: value with all variables replaced
        :rtype: str
        :raises IssaiException: if at least one referenced variable is not defined
        """
        if not isinstance(value, str):
            return value
        _var_pattern = re.compile(r'\$\{(.*)}')
        _literal_value = value
        _m = _var_pattern.search(_literal_value)
        while _m:
            _var_name = _m.group(1)
            _var_value = self.get_str_value(_var_name)
            if _var_value is None:
                raise IssaiException(E_CFG_VAR_NOT_DEFINED, _var_name)
            _literal_value = _literal_value.replace('${%s}' % _var_name, _var_value)
            _m = _var_pattern.search(_literal_value)
        return _literal_value

    def variable_value(self, variable, group):
        """
        Returns value of given variable, specified as ${variable-name} in a string value.
        :param str variable: the variable name, enclosed in ${...}
        :param str group: the TOML group containing the value referencing the variable
        :returns: value of specified variable
        :rtype: str
        :raises IssaiException: if variable is not defined
        """
        _var_name = variable[2:-1]
        if _var_name == CFG_VAR_CONFIG_ROOT:
            return self.__config_root
        _value = None
        _curr_group = group
        while len(_curr_group) > 0:
            _node = self.get_value(_curr_group)
            _value = _node.get(_var_name)
            if _value is not None:
                return _value
            _last_dot_index = group.rfind('.')
            _curr_group = '' if _last_dot_index < 0 else _curr_group[0:_last_dot_index]
        _value = self.get(_var_name)
        if _value is not None:
            return _value
        raise IssaiException(E_CFG_VAR_NOT_DEFINED, variable, group)


def load_runtime_configs():
    """
    Loads issai runtime configurations for all locally supported products.
    :returns: local runtime configurations, problems
    :rtype: tuple
    :raises IssaiException: if no products available
    """
    _problems = []
    _configs = []
    _products = issai_products()
    _master_cfg = master_config()
    for _p in _products:
        try:
            _configs.append(product_config(_p, _master_cfg))
        except IssaiException as _e:
            _problems.append(str(_e))
    return _configs, _problems


def issai_products():
    """
    :returns: names of all products supported by local Issai installation
    :rtype: list
    :raises IssaiException: if Issai installation is incomplete or no products are configured
    """
    _config_path = _config_root_path()
    _prods = []
    for _node in os.listdir(_config_path):
        if os.path.isdir(os.path.join(_config_path, _node)):
            _prods.append(_node)
    if len(_prods) == 0:
        raise IssaiException(E_CFG_NO_PRODUCTS, _config_path)
    return _prods


def master_config():
    """
    :returns: Issai master configuration from file, if it exists, otherwise None.
    :rtype: LocalConfig
    :raises IssaiException: if Issai installation is incomplete
    """
    _config_path = _config_root_path()
    _file_path = os.path.join(_config_path, _MASTER_CFG_FILE_NAME)
    if not os.path.isfile(_file_path):
        return None
    return LocalConfig.from_file(_file_path, True)


def product_config(product_name, master_cfg):
    """
    Loads Issai product specific configuration from file and merges it into master configuration.
    :param str product_name: Issai product name
    :param LocalConfig master_cfg: Issai master configuration, may be None
    :returns: Issai product specific configuration
    :rtype: LocalConfig
    :raises IssaiException: if no product configuration file exists
    """
    _config_path = _config_root_path()
    _product_config_path = os.path.join(_config_path, product_name)
    if not os.path.isdir(_product_config_path):
        raise IssaiException(E_CFG_PRODUCT_CONFIG_DIR_NOT_FOUND, product_name, _config_path)
    _file_path = os.path.join(_product_config_path, _PRODUCT_CFG_FILE_NAME)
    if not os.path.isfile(_file_path):
        raise IssaiException(E_CFG_PRODUCT_CONFIG_FILE_NOT_FOUND, _file_path)
    _prod_config = LocalConfig.from_file(_file_path)
    if master_cfg is not None:
        _prod_config = master_cfg.merged_copy(_prod_config)
    return _prod_config


def _config_root_path():
    """
    Determines root directory for Issai configuration.
    If environment variable ISSAI_CONFIG_PATH is defined and denotes a directory, that value is returned.
    Otherwise, returns default directory $HOME/.config/issai.
    :returns: configuration root directory
    :rtype: str
    :raises IssaiException: if environment variable ISSAI_CONFIG_PATH is defined and does not denote a directory,
                            or environment variable ISSAI_CONFIG_PATH is **not** defined and default directory does not
                            exist
    """
    _config_path = os.environ.get(ENVA_ISSAI_CONFIG_PATH)
    if _config_path is not None:
        _config_path = full_path_of(_config_path)
        if not os.path.isdir(_config_path):
            raise IssaiException(E_CFG_CUSTOM_CONFIG_ROOT_NOT_FOUND, _config_path, ENVA_ISSAI_CONFIG_PATH)
        return _config_path
    _config_path = full_path_of(_DEFAULT_CONFIG_PATH)
    if not os.path.isdir(_config_path):
        raise IssaiException(E_CFG_DEFAULT_CONFIG_ROOT_NOT_FOUND, _config_path)
    return _config_path
