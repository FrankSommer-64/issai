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
Issai runtime configuration.
The framework is configured by files located under Issai configuration directory. This directory
can be specified in environment variable ISSAI_CONFIG_PATH, it defaults to $HOME/.config/issai.
If there is a file named master.toml, it is considered as master configuration for all products.
For each product, there must be a subdirectory with the Issai product name and inside the subdirectory
a file product.toml containing product specific configuration.
During test execution, the configuration may be updated from attachment files contained in test plans
or test cases.
"""

import importlib
import importlib.util
import os.path
import re
import shutil
import sys

import tomlkit
import tomlkit.items

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.util import full_path_of


class LocalConfig(dict):
    """
    Holds attributes specific to local environment.
    """
    def __init__(self, file_path, warnings, is_product_config=True):
        """
        Constructor.
        :param str file_path: the configuration file name including full path
        :param list[str] warnings: the warning messages from preceding check
        :param bool is_product_config: indicates whether this object denotes a product configuration (True) or
                                       a master configuration (False)
        """
        super().__init__()
        self.__file_path = file_path
        self.__is_product_config = is_product_config
        self.__custom_module = None
        self.__custom_script_path = None
        if is_product_config:
            self[CFG_VAR_CONFIG_ROOT] = os.path.dirname(os.path.dirname(file_path))
        else:
            self[CFG_VAR_CONFIG_ROOT] = os.path.dirname(file_path)
        self.__warnings = warnings

    def warnings(self):
        """
        :returns: localized warnings that occurred during parse of configuration
        :rtype: list[str]
        """
        return self.__warnings

    def attribute_names(self):
        """
        :returns: qualified names of all attributes defined in the configuration
        :rtype: set
        """
        _names = set()
        for _k, _v in self.items():
            if isinstance(_v, tomlkit.items.Table):
                _grp_names = [f'{_k}.{_gk}' for _gk in _v.keys()]
                _names.update(_grp_names)
            else:
                _names.add(_k)
        return _names

    def group_names(self):
        """
        :returns: names of all TOML groups defined in the configuration
        :rtype: list[str]
        """
        return [_k for _k, _v in self.items() if isinstance(_v, tomlkit.items.Table)]

    def environment_variables(self):
        """
        :returns: all environment variables defined in the configuration
        :rtype: dict
        """
        _env_grp = self.get(CFG_GROUP_ENV)
        _env_vars = {} if _env_grp is None else _env_grp.unwrap()
        return _env_vars

    def download_patterns_match(self, file_name):
        """
        :param str file_name: the pure file name
        :returns: True, if specified attachment file name must be downloaded before test execution
        :rtype: bool
        """
        return self.attachment_patterns_match(CFG_PAR_TCMS_SPEC_ATTACHMENTS, file_name)

    def upload_patterns_match(self, file_name):
        """
        :param str file_name: the pure file name
        :returns: True, if specified attachment file name must be uploaded after test execution
        :rtype: bool
        """
        return self.attachment_patterns_match(CFG_PAR_TCMS_RESULT_ATTACHMENTS, file_name)

    def has_upload_patterns(self):
        """
        :returns: True, if patterns for upload of attachment files are defined in the configuration
        :rtype: bool
        """
        _patterns = self.get_list_value(CFG_PAR_TCMS_RESULT_ATTACHMENTS)
        return _patterns is not None and len(_patterns) > 0

    def attachment_patterns_match(self, cfg_par, file_name):
        """
        Indicates whether patterns defined for TCMS attachments match given pure file name.
        :param str cfg_par: the qualified name of configuration parameter containing the pattern list
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

    def runner_working_path(self):
        """
        :returns: working path for test runner
        :rtype: str
        :raises IssaiException: if working path is not defined or doesn't exist
        """
        _working_path = self.get_value(CFG_PAR_RUNNER_WORKING_PATH)
        if _working_path is None or not os.path.isdir(_working_path):
            raise IssaiException(E_RUN_WORKING_PATH_MISSING, CFG_PAR_RUNNER_WORKING_PATH)
        if not os.path.isdir(_working_path):
            raise IssaiException(E_RUN_WORKING_PATH_INVALID, _working_path)
        return _working_path

    def custom_function(self, function_name):
        """
        Returns pointer to custom function with specified name.
        :param str function_name: the name of the function
        :returns: custom function pointer
        :rtype: function
        :raises IssaiException: if custom module path is not defined or function doesn't exist in module
        """
        if self.__custom_module is None:
            _mod_path = self.get_value(CFG_PAR_RUNNER_CUSTOM_MODULE_PATH)
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
            _script_dir = self.get_value(CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH)
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
        return self.get_value(CFG_PAR_RUNNER_OUTPUT_LOG, DEFAULT_OUTPUT_LOG)

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

    def merge(self, master_cfg):
        """
        Merges attributes from given master configuration merged, i.e. only those items not present in this
        configuration are added.
        :param LocalConfig master_cfg: the master configuration to merge
        """
        for _group_name in master_cfg.group_names():
            self.setdefault(_group_name, {})
        for _attr_name in master_cfg.attribute_names():
            _dot_pos = _attr_name.find('.')
            if _dot_pos < 0:
                self.setdefault(_attr_name, master_cfg[_attr_name])
            else:
                _group = _attr_name[:_dot_pos]
                _plain_attr_name = _attr_name[_dot_pos+1:]
                self[_group].setdefault(_plain_attr_name, master_cfg[_group][_plain_attr_name])

    def validate(self):
        """
        Makes sure this configuration is usable.
        Resolves references to environment variables and other attributes.
        Stores warnings in local object.
        :raises IssaiException: if configuration contains errors
        """
        _file_name = os.path.basename(self.__file_path)
        if self.__is_product_config:
            _file_name = os.path.join(os.path.basename(os.path.dirname(self.__file_path)), _file_name)
        if self.__is_product_config and self[CFG_VAR_CONFIG_ROOT] == os.path.dirname(self.__file_path):
            # product configuration must be located in a subdirectory
            raise IssaiException(E_CFG_INVALID_DIR_STRUCTURE, _file_name)
        # check whether mandatory attribute is missing
        if self.__is_product_config:
            _defined_attrs = self.attribute_names()
            for _mk in mandatory_attrs():
                if _mk not in _defined_attrs:
                    raise IssaiException(E_CFG_MANDATORY_PAR_MISSING, _mk, _file_name)
        self.resolve_references()

    def resolve_references(self):
        """
        Replaces references to variables with their actual values.
        Stores warnings in local object.
        :raises IssaiException: if cycles or undefined references are detected
        """
        self.resolve_references_in_group('', self)
        for _k, _v in self.items():
            if isinstance(_v, tomlkit.items.Table) and _k in _META_CFG:
                self.resolve_references_in_group(_k, _v)

    def resolve_references_in_group(self, group_name, group):
        """
        Replaces references to variables with their actual values.
        :param str group_name: the name of the TOML group to process, empty string for root
        :param LocalConfig | tomlkit.items.Table group: the TOML group to process
        Stores warnings in local object.
        :raises IssaiException: if cycles or undefined references are detected
        """
        for _k, _v in group.items():
            if isinstance(_v, str):
                _qualified_attr_name = qualified_attr_name_for(group_name, _k)
                group[_k] = self.literal_value_of(group_name, _v, {_k, _qualified_attr_name})
                continue
            if isinstance(_v, tomlkit.items.Array):
                for i in range(0, len(_v)):
                    _v[i] = self.literal_value_of(group_name, _v[i], set())
                continue
            if isinstance(_v, tomlkit.items.InlineTable):
                for _tk, _tv in _v.items():
                    _v[_tk] = self.literal_value_of(group_name, _tv, set())

    def literal_value_of(self, group_name, attr_value, referenced_vars):
        """
        Returns literal value of an attribute. Replaces any existing variable references in string values by the
        actual variable values.
        Stores warnings in local object.
        :param str group_name: the TOML group where the attribute resides, empty string for root
        :param attr_value: the attribute value
        :param set referenced_vars: all variable names replaced up to now; needed to detect cycles
        :returns: literal attribute value
        :raises IssaiException: if cycles or undefined references are detected
        """
        if not isinstance(attr_value, str):
            return attr_value
        _ref_exists = attr_value.find('${') >= 0 or attr_value.find('$env[') >= 0
        if not _ref_exists:
            return attr_value
        _literal_value = attr_value
        while _ref_exists:
            _toml_refs = set(TOML_VAR_PATTERN.findall(_literal_value))
            for _var_name in _toml_refs:
                if _var_name in referenced_vars:
                    raise IssaiException(E_CFG_VAR_REFERENCE_CYCLE, _var_name)
                if _var_name == CFG_VAR_CONFIG_ROOT:
                    _var_value = self[CFG_VAR_CONFIG_ROOT]
                else:
                    _var_value = self.get_var_value(_var_name, group_name)
                    if _var_value is None:
                        raise IssaiException(E_CFG_VAR_NOT_DEFINED, _var_name)
                _literal_value = _literal_value.replace(f'${{{_var_name}}}', _var_value)
            referenced_vars.update(_toml_refs)
            _m = ENV_VAR_PATTERN.search(_literal_value)
            while _m:
                _var_name = _m.group(1)
                _var_value = os.environ.get(_var_name)
                if _var_value is None:
                    raise IssaiException(E_CFG_ENV_VAR_NOT_DEFINED, _var_name)
                _literal_value = _literal_value.replace(f'$env[{_var_name}]', _var_value)
                _m = ENV_VAR_PATTERN.search(_literal_value)
            _ref_exists = _literal_value.find('${') >= 0 or _literal_value.find('$env[') >= 0
        return _literal_value

    def get_var_value(self, var_name, group_name):
        """
        Returns value of a variable.
        :param str var_name: the variable name
        :param str group_name: the TOML group name referencing the variable
        :returns: value of referenced variable, may itself contain references. None, if variable is not defined.
        """
        if var_name.find('.') > 0:
            # qualified variable name
            return self.get_value(var_name)
        # plain variable name
        _qualified_var_name = qualified_attr_name_for(group_name, var_name)
        _group_value = self.get_value(_qualified_var_name)
        return self.get_value(var_name) if _group_value is None else _group_value

    @staticmethod
    def from_file(file_path, is_product_config):
        """
        Creates local configuration from TOML file.
        :param str file_path: name of configuration file including full path
        :param bool is_product_config: indicates whether a product configuration shall be read (True) or
                                       a master configuration (False)
        :returns: local configuration
        :rtype: LocalConfig
        :raises IssaiException: if file cannot be processed
        """
        _file_contents = ''
        _file_path = os.path.abspath(file_path)
        try:
            with open(_file_path, 'r') as _f:
                _file_contents = _f.read()
        except Exception as e:
            raise IssaiException(E_CFG_READ_FILE_FAILED, _file_path, e)
        return LocalConfig.from_str(_file_contents, _file_path, is_product_config)

    @staticmethod
    def from_str(data, file_path, is_product_config):
        """
        Creates local configuration from TOML string.
        :param str data: the TOML data
        :param str file_path: name of configuration file including full path
        :param bool is_product_config: indicates whether a product configuration shall be read (True) or
                                       a master configuration (False)
        :returns: local configuration
        :rtype: LocalConfig
        :raises IssaiException: if string cannot be processed
        """
        try:
            _toml_data = tomlkit.loads(data) 
            _warnings = validate_config_structure(_toml_data, file_path, is_product_config)
            _cfg = LocalConfig(file_path, _warnings, is_product_config)
            _cfg.update(_toml_data.items())
            return _cfg
        except Exception as e:
            raise IssaiException(E_CFG_READ_FILE_FAILED, file_path, e)

    def __lt__(self, other):
        """
        :param LocalConfig other: the local configuration to compare with this one
        :returns: True, if this local configuration's Issai name is less than the specified other configuration's
        :rtype: bool
        """
        return self.get_value(CFG_PAR_PRODUCT_NAME, '') < other.get_value(CFG_PAR_PRODUCT_NAME, '')

    def get_value(self, dotted_key, default_value=None):
        """
        Returns the value associated with the specified key. Dotted keys are automatically converted to tree.
        :param str dotted_key: the dotted key
        :param default_value: the value to return, if key is not defined
        :returns: value associated with key; None, if key is not defined
        :rtype: str|bool|dict|list
        """
        if dotted_key.find('.') < 0:
            _val = self.get(dotted_key)
            return default_value if _val is None else _val.unwrap()
        _node = self
        _key_parts = dotted_key.split('.')
        for _key_part in _key_parts:
            if _key_part not in _node:
                return default_value
            _node = _node[_key_part]
        return _node.unwrap()

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
            raise IssaiException(E_CFG_INVALID_DATA_TYPE, dotted_key, 'list or str')
        return _value


def load_runtime_configs(config_path):
    """
    Loads issai runtime configurations for all locally supported products.
    :param str config_path: the Issai configuration root directory
    :returns: master configuration, product configurations, problems, warnings
    :rtype: tuple
    :raises IssaiException: if no products available
    """
    _product_configs = []
    _problems = []
    _warnings = []
    _master_cfg = master_config(config_path)
    _products = issai_products(config_path)
    if len(_products) == 0:
        _problems.append(localized_message(E_CFG_NO_PRODUCTS, config_root_path()))
    else:
        for _p in _products:
            try:
                _product_cfg = product_config(config_path, _p, _master_cfg)
                _warnings.extend(_product_cfg.warnings())
                _product_configs.append(_product_cfg)
            except IssaiException as _e:
                _problems.append(str(_e))
    return _master_cfg, _product_configs, _problems, _warnings


def issai_products(config_path):
    """
    :param str config_path: the Issai configuration root directory
    :returns: names of all products supported by local Issai installation
    :rtype: list
    """
    _products = []
    for _node in os.listdir(config_path):
        if os.path.isdir(os.path.join(config_path, _node)):
            _products.append(_node)
    return _products


def master_config(config_path):
    """
    :param str config_path: the Issai configuration root directory
    :returns: Issai master configuration from file, if it exists, otherwise None.
    :rtype: LocalConfig
    """
    _file_path = os.path.join(config_path, ISSAI_MASTER_CONFIG_FILE_NAME)
    if not os.path.isfile(_file_path):
        return None
    return LocalConfig.from_file(_file_path, False)


def product_config(config_path, product_name, master_cfg):
    """
    Loads Issai product specific configuration from file and merges it into master configuration.
    :param str config_path: the Issai configuration root directory
    :param str product_name: Issai product name
    :param LocalConfig master_cfg: Issai master configuration, may be None
    :returns: Issai product specific configuration
    :rtype: LocalConfig
    :raises IssaiException: if no product configuration file exists
    """
    _product_config_path = os.path.join(config_path, product_name)
    if not os.path.isdir(_product_config_path):
        raise IssaiException(E_CFG_PRODUCT_CONFIG_DIR_NOT_FOUND, product_name, config_path)
    _file_path = os.path.join(_product_config_path, ISSAI_PRODUCT_CONFIG_FILE_NAME)
    if not os.path.isfile(_file_path):
        raise IssaiException(E_CFG_PRODUCT_CONFIG_FILE_NOT_FOUND, _file_path)
    _prod_config = LocalConfig.from_file(_file_path, True)
    if master_cfg is not None:
        _prod_config.merge(master_cfg)
    _prod_config.validate()
    return _prod_config


def config_root_path():
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
    _config_path = full_path_of(ISSAI_CONFIG_PATH)
    if not os.path.isdir(_config_path):
        raise IssaiException(E_CFG_DEFAULT_CONFIG_ROOT_NOT_FOUND, _config_path)
    return _config_path


def create_config_root():
    """
    Creates root directory for Issai configuration and a default master configuration file.
    If defined, directory path is taken from environment variable ISSAI_CONFIG_PATH,
    otherwise creates default directory $HOME/.config/issai.
    :returns: full path of configuration root directory
    :rtype: str
    """
    _config_path = os.environ.get(ENVA_ISSAI_CONFIG_PATH)
    if _config_path is None:
        _config_path = ISSAI_CONFIG_PATH
    _config_path = full_path_of(_config_path)
    os.makedirs(_config_path, 0o755, True)
    _my_path = os.path.dirname(__file__)
    _master_template = os.path.abspath(os.path.join(_my_path, '..', ISSAI_TEMPLATES_DIR, ISSAI_MASTER_CONFIG_FILE_NAME))
    shutil.copy(_master_template, _config_path)
    return _config_path


def validate_config_structure(data, file_path, is_product_config):
    """
    Checks structure of specified local Issai configuration.
    :param tomlkit.TOMLDocument data: the configuration TOML data
    :param str file_path: the full file name of the configuration
    :param bool is_product_config: indicates whether a product configuration shall be read (True) or
                                   a master configuration (False)
    :returns: localized warning messages
    :rtype: list[str]
    :raises IssaiException: if configuration is not valid
    """
    _warnings = []
    _unsupported_items = []
    _file_name = os.path.basename(file_path)
    if is_product_config:
        _file_name = os.path.join(os.path.basename(os.path.dirname(file_path)), _file_name)
    for _k, _v in data.items():
        if not isinstance(_v, tomlkit.items.Table):
            # root level attribute
            if _k in _META_CFG:
                raise IssaiException(E_CFG_GRP_NOT_TABLE, _k, _file_name)
            if _k == CFG_VAR_CONFIG_ROOT:
                _warnings.append(localized_message(W_CFG_PAR_RESERVED, _k, _file_name))
                _unsupported_items.append(_k)
                continue
            if not check_attr('', _k, _v, _file_name):
                _warnings.append(localized_message(W_CFG_PAR_IGNORED, _k, _file_name))
                _unsupported_items.append(_k)
                continue
            continue
        # TOML group
        _group_desc = _META_CFG.get(_k)
        if _group_desc is None:
            # unsupported group
            _warnings.append(localized_message(W_CFG_GRP_IGNORED, _k, _file_name))
            _unsupported_items.append(_k)
            continue
        if not _group_desc[META_KEY_ALLOWED_IN_MASTER] and not is_product_config:
            _warnings.append(localized_message(W_CFG_GRP_IGNORED_IN_MASTER, _k, _file_name))
            _unsupported_items.append(_k)
            continue
        # check all attributes in group
        for _ak, _av in _v.items():
            _qualified_ak = f'{_k}.{_ak}'
            _value_type = _group_desc[META_KEY_VALUE_TYPE]
            if _value_type is not None:
                if not isinstance(_av, _value_type):
                    raise IssaiException(E_CFG_INVALID_PAR_VALUE, _ak, _value_type.__name__, _file_name)
            _name_pattern = _group_desc[META_KEY_NAME_PATTERN]
            if _name_pattern is not None and not _name_pattern.match(_ak):
                raise IssaiException(E_CFG_INVALID_PAR_NAME, _ak, _file_name)
            if not check_attr(_k, _ak, _av, _file_name):
                _warnings.append(localized_message(W_CFG_PAR_IGNORED, _qualified_ak, _file_name))
                _unsupported_items.append(_k)
                continue
    # remove unsupported attributes and groups, if any
    for _item in _unsupported_items:
        _dot_pos = _item.find('.')
        if _dot_pos < 0:
            del data[_item]
        else:
            _group_name = _item[:_dot_pos]
            _attr_name = _item[_dot_pos+1:]
            del data[_group_name][_attr_name]
    return _warnings


def mandatory_attrs():
    """
    :returns: names of all mandatory attributes for an Issai configuration
    :rtype: list[str]
    """
    _attrs = []
    for _gv in _META_CFG.values():
        for _attrs_meta in _gv[META_KEY_ATTRS]:
            if not _attrs_meta[META_KEY_OPT]:
                _attrs.append(_attrs_meta[META_KEY_ATTR_QUALIFIED_NAME])
    return _attrs


def check_attr(group_name, attr_name, attr_value, file_name):
    if len(_META_CFG[group_name][META_KEY_ATTRS]) == 0:
        # group where arbitrary attributes are allowed
        return True
    _attr_desc = attr_desc_for(group_name, attr_name)
    if _attr_desc is None:
        # unsupported attribute
        return False
    _expected_type = _attr_desc[META_KEY_ATTR_TOML_TYPE]
    if not isinstance(attr_value, _expected_type):
        _qualified_attr_name = qualified_attr_name_for(group_name, attr_name)
        raise IssaiException(E_CFG_INVALID_PAR_VALUE, _qualified_attr_name, _expected_type.__name__, file_name)
    return True


def config_meta_data():
    """
    :returns: descriptor with configuration metadata
    """
    return _META_CFG


def attr_desc_for(group_name, attr_name):
    for _attr_desc in _META_CFG[group_name][META_KEY_ATTRS]:
        if _attr_desc[META_KEY_ATTR_NAME] == attr_name:
            return _attr_desc
    return None


def group_data_of(config_data, group_name):
    """
    :param tomlkit.TOMLDocument config_data: whole configuration data
    :param str group_name: name of desired TOML group, '' for root
    :returns: data of specified TOML group
    :rtype: tomlkit.items.Table
    """
    if len(group_name) > 0:
        return config_data.get(group_name)
    _group_data = tomlkit.table()
    for _k, _v in config_data.items():
        if isinstance(_v, tomlkit.items.Table):
            continue
        _group_data.append(_k, _v)
    return _group_data


def qualified_attr_name_for(group_name, attr_name):
    """
    :param str group_name: name of TOML group the attribute belongs to, '' for root
    :param str attr_name: attribute name
    :returns: qualified attribute name
    :rtype: str
    """
    if len(group_name) == 0 or attr_name.find('.') >= 0:
        return attr_name
    return f'{group_name}.{attr_name}'


ENV_VAR_PATTERN = re.compile(r'\$env\[([A-Z0-9_]+)]')
ENV_VAR_NAME_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
TOML_VAR_PATTERN = re.compile(r'\$\{(.*?)}')

META_KEY_ALLOWED_IN_MASTER = 'allowed-in-master'
META_KEY_ATTR_DEFAULT_VALUE = 'default'
META_KEY_ATTR_NAME = 'name'
META_KEY_ATTR_QUALIFIED_NAME = 'qualified-name'
META_KEY_ATTR_TOML_TYPE = 'toml-type'
META_KEY_ATTR_TYPE = 'type'
META_KEY_ATTRS = 'attributes'
META_KEY_COMMENT = 'comment'
META_KEY_NAME_PATTERN = 'name-pattern'
META_KEY_OPT = 'is-optional'
META_KEY_UNQUOTED_STR_VALUES = 'unquoted-str-values'
META_KEY_VALUE_TYPE = 'value-type'

META_TYPE_BOOLEAN = 'b'
META_TYPE_ENUM = 'e'
META_TYPE_INT = 'i'
META_TYPE_LIST = 'l'
META_TYPE_LIST_OF_INT = 'l:i'
META_TYPE_LIST_OF_STR = 'l:s'
META_TYPE_MAPPING = 'm'
META_TYPE_MAPPING_OF_EXECUTION_STATES = 'm:IDLE,PASSED,FAILED,ERROR'
META_TYPE_STR = 's'
META_TYPE_STR_DIR_PATH = 's:d'
META_TYPE_STR_FILE_PATH = 's:f'
META_TYPE_STR_NORMAL = 's:n'
META_TYPE_STR_PASSWORD = 's:p'

# description for group custom
_META_CUSTOM = {META_KEY_ALLOWED_IN_MASTER: True,
                META_KEY_NAME_PATTERN: None,
                META_KEY_OPT: True,
                META_KEY_UNQUOTED_STR_VALUES: False,
                META_KEY_VALUE_TYPE: None,
                META_KEY_ATTRS: [],
                }

# description for group env
_META_ENV = {META_KEY_ALLOWED_IN_MASTER: True,
             META_KEY_NAME_PATTERN: ENV_VAR_NAME_PATTERN,
             META_KEY_OPT: True,
             META_KEY_UNQUOTED_STR_VALUES: False,
             META_KEY_VALUE_TYPE: str,
             META_KEY_ATTRS: []
             }

# description for group product
_META_PRODUCT = {META_KEY_ALLOWED_IN_MASTER: False,
                 META_KEY_NAME_PATTERN: None,
                 META_KEY_OPT: False,
                 META_KEY_UNQUOTED_STR_VALUES: False,
                 META_KEY_VALUE_TYPE: None,
                 META_KEY_ATTRS: [
                      {META_KEY_ATTR_DEFAULT_VALUE: '',
                       META_KEY_ATTR_NAME: CFG_PAR_PRODUCT_NAME[len(CFG_GROUP_PRODUCT)+1:],
                       META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_PRODUCT_NAME,
                       META_KEY_ATTR_TOML_TYPE: str,
                       META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                       META_KEY_COMMENT: L_CFG_PAR_PRODUCT_NAME,
                       META_KEY_OPT: False},
                      {META_KEY_ATTR_DEFAULT_VALUE: '',
                       META_KEY_ATTR_NAME: CFG_PAR_PRODUCT_REPOSITORY_PATH[len(CFG_GROUP_PRODUCT)+1:],
                       META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_PRODUCT_REPOSITORY_PATH,
                       META_KEY_ATTR_TOML_TYPE: str,
                       META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                       META_KEY_COMMENT: L_CFG_PAR_PRODUCT_REPOSITORY_PATH,
                       META_KEY_OPT: False},
                      {META_KEY_ATTR_DEFAULT_VALUE: '',
                       META_KEY_ATTR_NAME: CFG_PAR_PRODUCT_SOURCE_PATH[len(CFG_GROUP_PRODUCT)+1:],
                       META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_PRODUCT_SOURCE_PATH,
                       META_KEY_ATTR_TOML_TYPE: str,
                       META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                       META_KEY_COMMENT: L_CFG_PAR_PRODUCT_SOURCE_PATH,
                       META_KEY_OPT: True},
                      {META_KEY_ATTR_DEFAULT_VALUE: '',
                       META_KEY_ATTR_NAME: CFG_PAR_PRODUCT_TEST_PATH[len(CFG_GROUP_PRODUCT)+1:],
                       META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_PRODUCT_TEST_PATH,
                       META_KEY_ATTR_TOML_TYPE: str,
                       META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                       META_KEY_COMMENT: L_CFG_PAR_PRODUCT_TEST_PATH,
                       META_KEY_OPT: True},
                      {META_KEY_ATTR_DEFAULT_VALUE: '',
                       META_KEY_ATTR_NAME: CFG_PAR_PRODUCT_TEST_DATA_PATH[len(CFG_GROUP_PRODUCT)+1:],
                       META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_PRODUCT_TEST_DATA_PATH,
                       META_KEY_ATTR_TOML_TYPE: str,
                       META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                       META_KEY_COMMENT: L_CFG_PAR_PRODUCT_TEST_DATA_PATH,
                       META_KEY_OPT: True}
                  ]
                 }

# description for root group
_META_ROOT = {META_KEY_ALLOWED_IN_MASTER: True,
              META_KEY_NAME_PATTERN: None,
              META_KEY_OPT: True,
              META_KEY_UNQUOTED_STR_VALUES: False,
              META_KEY_VALUE_TYPE: None,
              META_KEY_ATTRS: [
                     {META_KEY_ATTR_DEFAULT_VALUE: '',
                      META_KEY_ATTR_NAME: CFG_PAR_TESTING_ROOT_PATH,
                      META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TESTING_ROOT_PATH,
                      META_KEY_ATTR_TOML_TYPE: str,
                      META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                      META_KEY_COMMENT: L_CFG_PAR_TESTING_ROOT_PATH,
                      META_KEY_OPT: True}
                 ]
              }

# description for group runner
_META_RUNNER = {META_KEY_ALLOWED_IN_MASTER: True,
                META_KEY_NAME_PATTERN: None,
                META_KEY_OPT: True,
                META_KEY_UNQUOTED_STR_VALUES: False,
                META_KEY_VALUE_TYPE: None,
                META_KEY_ATTRS: [
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_CASE_ASSISTANT[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_CASE_ASSISTANT,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_CASE_ASSISTANT,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_CUSTOM_MODULE_PATH[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_CUSTOM_MODULE_PATH,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_FILE_PATH,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_CUSTOM_MODULE_PATH,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_ENTITY_ASSISTANT[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_ENTITY_ASSISTANT,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_ENTITY_ASSISTANT,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: 'console.log',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_OUTPUT_LOG[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_OUTPUT_LOG,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_OUTPUT_LOG,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_PLAN_ASSISTANT[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_PLAN_ASSISTANT,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_NORMAL,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_PLAN_ASSISTANT,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_PYTHON_VENV_PATH[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_PYTHON_VENV_PATH,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_PYTHON_VENV_PATH,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_TEST_DRIVER_EXE[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_TEST_DRIVER_EXE,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_FILE_PATH,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_TEST_DRIVER_EXE,
                     META_KEY_OPT: True},
                    {META_KEY_ATTR_DEFAULT_VALUE: '${testing-root-path}/${product.name}',
                     META_KEY_ATTR_NAME: CFG_PAR_RUNNER_WORKING_PATH[len(CFG_GROUP_RUNNER)+1:],
                     META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_RUNNER_WORKING_PATH,
                     META_KEY_ATTR_TOML_TYPE: str,
                     META_KEY_ATTR_TYPE: META_TYPE_STR_DIR_PATH,
                     META_KEY_COMMENT: L_CFG_PAR_RUNNER_WORKING_PATH,
                     META_KEY_OPT: True},
                ]
                }

# description for group tcms
_META_TCMS = {META_KEY_ALLOWED_IN_MASTER: True,
              META_KEY_NAME_PATTERN: None,
              META_KEY_OPT: True,
              META_KEY_UNQUOTED_STR_VALUES: False,
              META_KEY_VALUE_TYPE: None,
              META_KEY_ATTRS: [
                  {META_KEY_ATTR_DEFAULT_VALUE: {},
                   META_KEY_ATTR_NAME: CFG_PAR_TCMS_EXECUTION_STATES[len(CFG_GROUP_TCMS)+1:],
                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_EXECUTION_STATES,
                   META_KEY_ATTR_TOML_TYPE: tomlkit.items.InlineTable,
                   META_KEY_ATTR_TYPE: META_TYPE_MAPPING_OF_EXECUTION_STATES,
                   META_KEY_COMMENT: L_CFG_PAR_TCMS_EXECUTION_STATES,
                   META_KEY_OPT: True},
                  {META_KEY_ATTR_DEFAULT_VALUE: [],
                   META_KEY_ATTR_NAME: CFG_PAR_TCMS_RESULT_ATTACHMENTS[len(CFG_GROUP_TCMS)+1:],
                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_RESULT_ATTACHMENTS,
                   META_KEY_ATTR_TOML_TYPE: tomlkit.items.Array,
                   META_KEY_ATTR_TYPE: META_TYPE_LIST_OF_STR,
                   META_KEY_COMMENT: L_CFG_PAR_TCMS_RESULT_ATTACHMENTS,
                   META_KEY_OPT: True},
                  {META_KEY_ATTR_DEFAULT_VALUE: [],
                   META_KEY_ATTR_NAME: CFG_PAR_TCMS_SPEC_ATTACHMENTS[len(CFG_GROUP_TCMS)+1:],
                   META_KEY_ATTR_QUALIFIED_NAME: CFG_PAR_TCMS_SPEC_ATTACHMENTS,
                   META_KEY_ATTR_TOML_TYPE: tomlkit.items.Array,
                   META_KEY_ATTR_TYPE: META_TYPE_LIST_OF_STR,
                   META_KEY_COMMENT: L_CFG_PAR_TCMS_SPEC_ATTACHMENTS,
                   META_KEY_OPT: True}
                  ]
              }

_META_CFG = {'': _META_ROOT, CFG_GROUP_CUSTOM: _META_CUSTOM, CFG_GROUP_ENV: _META_ENV,
             CFG_GROUP_PRODUCT: _META_PRODUCT, CFG_GROUP_RUNNER: _META_RUNNER, CFG_GROUP_TCMS: _META_TCMS}
