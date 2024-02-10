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
Checks localized messages consistency for a specific locale.
The locale must be defined in environment variable LANG.
The Issai root directory for source files must be defined in environment variable ISSAI_SOURCE_PATH.
In detail, performs the following checks:
- all message codes defined in messages.py must have a localized definition in messages_<LANG>.txt
- all localized message IDs defined in messages_<LANG>.txt must have a definition in messages.py
- all message codes defined in messages.py must be referenced in a source file
- all usages of message codes must supply the needed parameters of the localized text in messages_<LANG>.txt

Message code is the name of the Python constant, e.g. E_INTERNAL_ERROR.
Message ID is the string value of the Python contant, e.g. 'e-internal-error'.
Exit code is 0 for success, 1 for failed and 2 for error.
Information and error messages are printed to console.
"""

import ast
import glob
import os.path
import re
import sys


DUP_ID_SYM = 'duplicate-id-symbol'
DUP_ID_VALUE = 'duplicate-id-value'
DUP_LOC_ID_VALUE = 'duplicate-localized-id-value'
LOC_ID_MISSING = 'localized-id-missing'
LOC_ID_UNDEFINED = 'localized-id-undefined'
MSG_SEVS = ('E', 'I', 'L', 'T', 'W')
MSG_CODE_DEF_PATTERN = r"^([EILTW]_\w+)\s*=\s*'(.*)'"
LOC_TEXT_PATTERN = r"^([eiltw]\-[a-z0-9\-]*?)\s+(.*)$"
MSG_CODE_PATTERN = r"\b([EILTW]\_\w+)\b"
LOC_MSG_PATTERN = r"localized_message\((.*)\)"
LOC_LBL_PATTERN = r"localized_label\((.*)\)"
RAISE_PATTERN = r"raise\s+IssaiException\((.*)\)"


class MessageCodeVisitor(ast.NodeVisitor):
    """
    Finds all calls to function 'localized_text' and raises of 'IssaiException' in a source file.
    Determines used message code and number of arguments.
    Stores found occurrences in lists of tuples (line-number, message-code, argument-count)
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.localized_text_calls = []

    def visit_Call(self, node):
        """
        Function call in source file.
        :param ast.Call node: the function call node in abstract syntax tree
        """
        _func_name = None
        _func_args = []
        for k, v in ast.iter_fields(node):
            if k == 'func':
                if isinstance(v, ast.Name):
                    _func_name = v.id
            if k == 'args':
                _func_args = v
        if _func_name == 'localized_text':
            self.localized_text_calls.append((node.lineno, _func_args[0].id, len(_func_args)))

    def visit_Raise(self, node):
        """
        Raised exception in source file.
        :param ast.Raise node: the raise node in abstract syntax tree
        """
        _exc_type = None
        _exc_args = []
        for k, v in ast.iter_fields(node):
            if k == 'exc' and v is not None:
                for ek, ev in ast.iter_fields(v):
                    if ek == 'func':
                        _exc_type = ev.id
                    if ek == 'args':
                        _exc_args = ev
        if _exc_type == 'IssaiException':
            self.localized_text_calls.append((node.lineno, _exc_args[0].id, len(_exc_args)))


def read_message_codes(file_path):
    """
    Reads all message codes defined in specified file.
    :param str file_path: the file name including full path
    :return: return code and all message codes found; message code as key, message ID as value
    :rtype: tuple[int, dict]
    """
    _msg_codes = {}
    _msg_ids = set()
    _dup_codes = []
    _dup_ids = []
    _pattern = re.compile(MSG_CODE_DEF_PATTERN)
    _file_name = os.path.basename(file_path)
    _rc = 0
    with open(file_path, 'r') as _f:
        _lines = _f.readlines()
    _line_nr = 0
    for _line in _lines:
        _line_nr += 1
        _line = _line.strip()
        if len(_line) == 0 or _line.startswith('#'):
            continue
        _match = _pattern.search(_line)
        if _match:
            _msg_code = _match.group(1)
            _msg_id = _match.group(2)
            if _msg_code in _msg_codes:
                # message code already defined
                _dup_codes.append(f'{_line_nr}: {_msg_code}')
            if _msg_id in _msg_ids:
                # message ID already defined
                _dup_ids.append(f'{_line_nr}: {_msg_id}')
            else:
                _msg_codes[_msg_code] = _msg_id
    if len(_dup_codes) > 0:
        print(f'Duplicate message codes in file {_file_name}:')
        print('  %s' % ','.join(_dup_codes))
        _rc = 1
    if len(_dup_ids) > 0:
        print(f'Duplicate message IDs in file {_file_name}:')
        print('  %s' % ','.join(_dup_ids))
        _rc = 1
    return _rc, _msg_codes


def read_localized_messages(file_path, rc):
    """
    Reads all localized messages defined in specified file.
    :param str file_path: the file name including full path
    :return: return code and all localized messages found; message ID as key, localized message text as value
    :rtype: tuple[int,dict]
    """
    _msgs = {}
    _dup_ids = []
    _file_name = os.path.basename(file_path)
    _pattern = re.compile(LOC_TEXT_PATTERN)
    with open(file_path, 'r') as _f:
        _lines = _f.readlines()
    _line_nr = 0
    for _line in _lines:
        _line_nr += 1
        _line = _line.strip()
        if len(_line) == 0 or _line.startswith('#'):
            continue
        _match = _pattern.search(_line)
        if _match:
            _msg_id = _match.group(1)
            _msg_text = _match.group(2)
            if _msg_id in _msgs:
                _dup_ids.append(f'{_line_nr}: {_msg_id}')
            else:
                _msgs[_msg_id] = _msg_text
    if len(_dup_ids) > 0:
        print(f'Duplicate message IDs in file {_file_name}:')
        print('  %s' % ','.join(_dup_ids))
        rc = 1
    return rc, _msgs


def check_localized_messages(messages, localized_messages, localized_messages_file_path, rc):
    """
    Checks whether all message IDs are defined for a locale and vice versa.
    :param dict messages: symbolic and string value of all message IDs
    :param dict localized_messages: message ID string value and message text for a locale
    :param str localized_messages_file_path: full name of file containing the localized messages
    :param int rc: current overall check status
    :return: rc if check passed, 1 if check failed
    :rtype: int
    """
    _missing = []
    _undefined = []
    _msg_id_strings = set(messages.values())
    _file_name = os.path.basename(localized_messages_file_path)
    for _msg_id in messages.values():
        if _msg_id not in localized_messages:
            _missing.append(_msg_id)
    if len(_missing) > 0:
        rc = 1
        print(f'Message IDs not defined in localized message file {_file_name}:')
        print('  %s' % ','.join(_missing))
    for _msg_id in localized_messages.keys():
        if _msg_id not in _msg_id_strings:
            _undefined.append(_msg_id)
    if len(_undefined) > 0:
        rc = 1
        print(f'Non-existing message IDs used in localized message file {_file_name}:')
        print('  %s' % ','.join(_undefined))
    return rc


def check_message_code_references(source_path, messages, localized_messages, rc):
    """
    Checks all Python source files using localized messages for correct number of message parameters.
    :param str source_path: the root directory to scan
    :param dict messages: symbolic and string value of all message IDs
    :param dict localized_messages: message ID string value and message text for a locale
    :param int rc: current overall check status
    :return: rc if check passed, 1 if check failed
    :rtype: int
    """
    for path, subdirs, files in os.walk(source_path):
        for _file_name in files:
            if not _file_name.endswith('.py'):
                continue
            _file_path = os.path.join(path, _file_name)
            with open(_file_path, 'r') as _f:
                source_code = _f.read()
            _syntax_tree = ast.parse(source_code, _file_path)
            _visitor = MessageCodeVisitor()
            _visitor.visit(_syntax_tree)
            for _call in _visitor.localized_text_calls:
                _line_nr, _msg_code, _actual_arg_count = _call
                _msg_id = messages.get(_msg_code)
                _loc_msg = localized_messages.get(_msg_id)
                _expected_arg_count = len(re.findall(r'\{\d+\}', _loc_msg)) + 1
                if _expected_arg_count != _actual_arg_count:
                    rc = 1
                    print(f'{_file_name}:{_line_nr} {_msg_code} expects {_expected_arg_count} arguments, '
                          f'passed are {_actual_arg_count}')
    return rc


def check_unused_message_codes(source_path, messages, rc):
    """
    Checks whether all message codes are actually referenced in source code.
    :param str source_path: the root directory to scan
    :param dict messages: symbolic and string value of all message IDs
    :param int rc: current overall check status
    :return: rc if check passed, 1 if check failed
    :rtype: int
    """
    _used_msg_codes = set()
    _msg_code_pattern = re.compile(MSG_CODE_PATTERN)
    for path, subdirs, files in os.walk(source_path):
        for _file_name in files:
            if not _file_name.endswith('.py'):
                continue
            _file_path = os.path.join(path, _file_name)
            with open(_file_path, 'r') as f:
                source_code = f.read()
            _msg_code_pattern = re.compile(MSG_CODE_PATTERN)
            _matches = _msg_code_pattern.finditer(source_code)
            for _m in _matches:
                _msg_code = _m.group(1)
                _begin_pos, _end_pos = _m.span()
                _def_pattern = f'{_msg_code}\\s*='
                if re.match(_def_pattern, source_code[_begin_pos:]):
                    # ignore message code definition
                    continue
                _used_msg_codes.add(_msg_code)
    for _msg_code in messages.keys():
        if _msg_code not in _used_msg_codes:
            _dry_run_index = _msg_code.find('_DRY_RUN')
            if _dry_run_index > 0:
                _pure_msg_code = _msg_code[:2] + _msg_code[10:]
                if _pure_msg_code in _used_msg_codes:
                    continue
            rc = 1
            print(f'Message code {_msg_code} is not used')
    return rc


if __name__ == '__main__':
    _rc = 0
    try:
        # read mandatory parameters from OS environment
        _lang = os.environ.get('LANG')
        if _lang is None:
            raise RuntimeError('Environment variable LANG not set')
        _locale = _lang[:2].lower()
        _source_path = os.environ.get('ISSAI_SOURCE_PATH')
        if _source_path is None:
            raise RuntimeError('Environment variable ISSAI_SOURCE_PATH not set')
        _core_package_path = os.path.join(_source_path, 'issai', 'core')
        _message_file_path = os.path.join(_core_package_path, 'messages.py')
        _localized_message_file_path = os.path.join(_core_package_path, f'messages_{_locale}.txt')
        # read all message codes from python source file
        _rc, _message_codes = read_message_codes(_message_file_path)
        # read localized message texts from text file
        _rc, _localized_messages = read_localized_messages(_localized_message_file_path, _rc)
        # check whether all message codes have a matching text and vice versa
        _rc = check_localized_messages(_message_codes, _localized_messages, _localized_message_file_path, _rc)
        # check whether all message codes references supply correct number of parameters
        _rc = check_message_code_references(_source_path, _message_codes, _localized_messages, _rc)
        # check whether all message codes are referenced in source code
        _rc = check_unused_message_codes(_source_path, _message_codes, _rc)
    except Exception as e:
        print(e)
        sys.exit(2)
    if _rc == 0:
        print('No message code issues found.')
    sys.exit(_rc)
