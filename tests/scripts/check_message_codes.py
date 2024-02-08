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
- all localized message codes defined in messages_<LANG>.txt must have a definition in messages.py
- all message codes defined in messages.py must be referenced in a source file
- all usages of message codes must supply the needed parameters of the localized text in messages_<LANG>.txt

Exit code is 0 for success, 1 for failed and -1 for error.
Information and error messages are printed to console.
"""

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
IGNORE_FILES = ['issai_exception.py', 'messages.py']
MSG_ID_DEF_PATTERN = r"^([EILTW]_\w+)\s*=\s*'(.*)'"
LOC_TEXT_PATTERN = r"^([eiltw]\-[a-z0-9\-]*?)\s+(.*)$"
MSG_ID_PATTERN = r"\b([EILTW]\_\w+)\b"
LOC_MSG_PATTERN = r"localized_message\((.*)\)"
LOC_LBL_PATTERN = r"localized_label\((.*)\)"
RAISE_PATTERN = r"raise\s+IssaiException\((.*)\)"


def check_localized_messages(messages, loc_messages):
    """
    Checks whether all message IDs are defined for a locale and vice versa.
    :param dict messages: symbolic and string value of all message IDs
    :param dict loc_messages: message ID string value and message text for a locale
    :return: message IDs not defined for locale, non-existent locale message IDs
    :rtype: (list, list)
    """
    _missing = []
    _undefined = []
    _msg_id_strings = set(messages.values())
    for _msg_id in messages.values():
        if _msg_id not in loc_messages:
            _missing.append(_msg_id)
    for _msg_str in loc_messages.keys():
        if _msg_str not in _msg_id_strings:
            _undefined.append(_msg_str)
    return _missing, _undefined


def find_message_issues(source_path):
    """
    Checks all Python source files using localized messages for correct number of message parameters.
    :param str source_path: the root directory to scan
    :returns: message codes referenced in source code, function calls with message codes for each source file
    :rtype: tuple(set, dict)
    """
    _used_ids = set()
    _issues = {}
    for path, subdirs, files in os.walk(source_path):
        for _file_name in files:
            if _file_name in IGNORE_FILES or not _file_name.endswith('.py'):
                continue
            _file_path = os.path.join(path, _file_name)
            _issues[_file_name] = []
            _raise_pattern = re.compile(RAISE_PATTERN)
            _loc_msg_pattern = re.compile(LOC_MSG_PATTERN)
            _loc_lbl_pattern = re.compile(LOC_LBL_PATTERN)
            _msg_id_pattern = re.compile(MSG_ID_PATTERN)
            with open(_file_path, 'r') as _f:
                _line_nr = 0
                _issue_line_nr = 0
                _line = _f.readline()
                while _line:
                    _line_nr += 1
                    _line = _line.strip()
                    if _issue_line_nr > 0:
                        _msg_args.extend(_line.split(','))
                        if _line.endswith(','):
                            _line = _f.readline()
                            continue
                        _issues[_file_name].append((_issue_line_nr, _msg_id, _msg_args))
                        _issue_line_nr = 0
                    if len(_line) == 0 or _line.startswith('#'):
                        _line = _f.readline()
                        continue
                    _match = _raise_pattern.search(_line)
                    if _match:
                        _exception_args = _match.group(1).split(',')
                        _msg_id = _exception_args[0].rstrip(')')
                        _used_ids.add(_msg_id)
                        _msg_args = [] if len(_exception_args) == 1 else _exception_args[1:]
                        if _line.endswith(','):
                            _issue_line_nr = _line_nr
                        else:
                            _issues[_file_name].append((_line_nr, _msg_id, _msg_args))
                        _line = _f.readline()
                        continue
                    _match = _loc_msg_pattern.search(_line)
                    if _match:
                        _msg_args = _match.group(1).split(',')
                        _msg_id = _msg_args[0].rstrip(')')
                        if _msg_id[0] in MSG_SEVS and _msg_id[1] != '_':
                            _used_ids.add(_msg_id)
                            _msg_args = [] if len(_msg_args) == 1 else _msg_args[1:]
                            if _line.endswith(','):
                                _issue_line_nr = _line_nr
                            else:
                                _issues[_file_name].append((_line_nr, _msg_id, _msg_args))
                        _line = _f.readline()
                        continue
                    _match = _loc_lbl_pattern.search(_line)
                    if _match:
                        _msg_args = _match.group(1).split(',')
                        _msg_id = _msg_args[0].rstrip(')')
                        if _msg_id[0] in MSG_SEVS and _msg_id[1] != '_':
                            _used_ids.add(_msg_id)
                            _msg_args = [] if len(_msg_args) == 1 else _msg_args[1:]
                            if _line.endswith(','):
                                _issue_line_nr = _line_nr
                            else:
                                _issues[_file_name].append((_line_nr, _msg_id, _msg_args))
                        _line = _f.readline()
                        continue
                    for _match in _msg_id_pattern.findall(_line):
                        _msg_id = _match.strip()
                        _used_ids.add(_msg_id)
                    _line = _f.readline()
    return _used_ids, _issues


def read_localized_messages(file_path, problems):
    """
    Reads all localized messages defined in specified file.
    :param str file_path: the file name including full path
    :param dict problems: the data structure where problems are collected
    :return: all localized messages found; message code as key, localized message text as value
    :rtype: dict
    """
    _messages = {}
    _locale_problems = []
    _pattern = re.compile(LOC_TEXT_PATTERN)
    with open(file_path, 'r') as _f:
        _line_nr = 0
        _line = _f.readline()
        while _line:
            _line_nr += 1
            _line = _line.strip()
            if len(_line) == 0 or _line.startswith('#'):
                _line = _f.readline()
                continue
            _match = _pattern.search(_line)
            if _match:
                _msg_id = _match.group(1)
                _msg_text = _match.group(2)
                if _msg_id in _messages:
                    _locale_problems.append(f'{_line_nr}: {_msg_id}')
                else:
                    _messages[_msg_id] = _msg_text
            _line = _f.readline()
    problems[DUP_LOC_ID_VALUE] = _locale_problems
    return _messages


def read_message_codes(file_path, problems):
    """
    Reads all message codes defined in specified file.
    :param str file_path: the file name including full path
    :param dict problems: the data structure where problems are collected
    :return: all message codes found; symbolic constant as key, string as value
    :rtype: dict
    """
    _msg_ids = {}
    _str_values = set()
    _pattern = re.compile(MSG_ID_DEF_PATTERN)
    with open(file_path, 'r') as _f:
        _line_nr = 0
        _line = _f.readline()
        while _line:
            _line_nr += 1
            _line = _line.strip()
            if len(_line) == 0 or _line.startswith('#'):
                _line = _f.readline()
                continue
            _match = _pattern.search(_line)
            if _match:
                _sym_value = _match.group(1)
                _str_value = _match.group(2)
                if _str_value in _str_values:
                    problems[DUP_ID_VALUE].append(f'{_line_nr}: {_str_value}')
                if _sym_value in _msg_ids:
                    problems[DUP_ID_SYM].append(f'{_line_nr}: {_sym_value}')
                else:
                    _msg_ids[_sym_value] = _str_value
            _line = _f.readline()
    return _msg_ids


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
        _problems = {DUP_ID_SYM: [], DUP_ID_VALUE: [], DUP_LOC_ID_VALUE: {}, LOC_ID_MISSING: {}, LOC_ID_UNDEFINED: {}}
        # read all message codes from python source file
        _message_codes = read_message_codes(_message_file_path, _problems)
        # read localized message texts from text file
        _localized_messages = read_localized_messages(_localized_message_file_path, _problems)
        # check whether all message codes have a matching text and vice versa
        _codes_not_in_locale, _undefined_codes = check_localized_messages(_message_codes, _localized_messages)
        if len(_codes_not_in_locale) > 0:
            _rc = 1
            _fn = os.path.basename(_localized_message_file_path)
            print(f'Message codes not defined in localized message file{_fn}:')
            print('  %s' % ','.join(_codes_not_in_locale))
        if len(_undefined_codes) > 0:
            _rc = 1
            _fn = os.path.basename(_localized_message_file_path)
            print('Non-existing message codes used in localized message file {_fn}:')
            print('  %s' % ','.join(_undefined_codes))
        # check whether all message codes are referenced in source code
        used_ids, msg_issues = find_message_issues(_source_path)
        for msg_id in _message_codes.keys():
            if msg_id not in used_ids:
                _dry_run_index = msg_id.find('_DRY_RUN')
                if _dry_run_index > 0:
                    _pure_msg_id = msg_id[:2] + msg_id[10:]
                    if _pure_msg_id in used_ids:
                        continue
                _rc = 1
                print(f'Message ID {msg_id} is not used')
        # check whether all usages supply correct number of parameters
        for _file_name, _calls in msg_issues.items():
            for _line_nr, _msg_sym, _msg_args in _calls:
                _msg_code = _message_codes.get(_msg_sym)
                _loc_msg = _localized_messages.get(_msg_code)
                _expected_arg_count = len(re.findall(r'\{\d+\}', _loc_msg))
                _actual_arg_count = len(_msg_args)
                if _expected_arg_count != _actual_arg_count:
                    _rc = 1
                    print(f'{_file_name}:{_line_nr} {_msg_sym} expects {_expected_arg_count} arguments, '
                          'passed are {_actual_arg_count}')
    except Exception as e:
        print(e)
        sys.exit(-1)
    sys.exit(_rc)
