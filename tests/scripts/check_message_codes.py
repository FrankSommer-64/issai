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
Checks localized messages consistency.
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
MSG_ID_DEF_PATTERN = r"^([EILW]_\w+)\s*=\s*'(.*)'"
LOC_TEXT_PATTERN = r"^([a-z0-9\-]*?)\s+(.*)$"
MSG_ID_PATTERN = r"\b([EILW]\_\w+)\b"
LOC_MSG_PATTERN = r"localized_message\((.*)\)"
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


def find_message_issues(directories):
    """
    Checks all Python source files using localized messages for correct number of message parameters.
    :param tuple directories: the full path of all directories to scan
    """
    _used_ids = set()
    _issues = {}
    _file_name_pattern = '*.py'
    for _dir in directories:
        _source_files = glob.glob(os.path.join(_dir, _file_name_pattern))
        for _file_path in _source_files:
            _file_name = os.path.basename(_file_path)
            if _file_name == 'messages.py':
                continue
            _issues[_file_name] = []
            _raise_pattern = re.compile(RAISE_PATTERN)
            _loc_msg_pattern = re.compile(LOC_MSG_PATTERN)
            _msg_id_pattern = re.compile(MSG_ID_PATTERN)
            with open(_file_path, 'r') as _f:
                _line_nr = 0
                _line = _f.readline()
                while _line:
                    _line_nr += 1
                    _line = _line.strip()
                    if len(_line) == 0 or _line.startswith('#'):
                        _line = _f.readline()
                        continue
                    _match = _raise_pattern.search(_line)
                    if _match:
                        _exception_args = _match.group(1).split(',')
                        _msg_id = _exception_args[0].rstrip(')')
                        _used_ids.add(_msg_id)
                        _msg_args = [] if len(_exception_args) == 1 else _exception_args[1:]
                        _issues[_file_name].append((_line_nr, _msg_id, _msg_args))
                        _line = _f.readline()
                        continue
                    _match = _loc_msg_pattern.search(_line)
                    if _match:
                        _exception_args = _match.group(1).split(',')
                        _msg_id = _exception_args[0].rstrip(')')
                        _used_ids.add(_msg_id)
                        _msg_args = [] if len(_exception_args) == 1 else _exception_args[1:]
                        _issues[_file_name].append((_line_nr, _msg_id, _msg_args))
                        _line = _f.readline()
                        continue
                    _match = _msg_id_pattern.search(_line)
                    if _match:
                        _msg_id = _match.group(1).strip()
                        _used_ids.add(_msg_id)
                    _line = _f.readline()
    return _used_ids, _issues


def read_localized_messages(file_path, locale_code, problems):
    """
    Reads all localized messages defined in specified file.
    :param str file_path: the file name including full path
    :param str locale_code: the two-character locale code
    :param dict problems: the data structure where problems are collected
    :return: all localized messages found; id string as key, localized message text as value
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
    problems[DUP_LOC_ID_VALUE][locale_code] = _locale_problems
    return _messages


def read_message_ids(file_path, problems):
    """
    Reads all message ID's defined in specified file.
    :param str file_path: the file name including full path
    :param dict problems: the data structure where problems are collected
    :return: all message ID's found; symbolic constant as key, string as value
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
    try:
        project_root_path = sys.argv[1]
        source_path = os.path.join(project_root_path, 'issai')
        core_package_path = os.path.join(source_path, 'core')
        gui_package_path = os.path.join(source_path, 'gui')
        message_file_path = os.path.join(core_package_path, 'messages.py')
        locale_files_pattern = 'messages_*.txt'
        locale_files = glob.glob(os.path.join(core_package_path, locale_files_pattern))
        _problems = {DUP_ID_SYM: [], DUP_ID_VALUE: [], DUP_LOC_ID_VALUE: {}, LOC_ID_MISSING: {}, LOC_ID_UNDEFINED: {}}
        message_ids = read_message_ids(message_file_path, _problems)
        localized_messages = {}
        for locale_file in locale_files:
            locale = os.path.basename(locale_file)[-6:-4]
            localized_messages[locale] = read_localized_messages(locale_file, locale, _problems)
            ids_not_in_locale, undefined_ids = check_localized_messages(message_ids, localized_messages[locale])
            if len(ids_not_in_locale) > 0:
                print('Message IDs not defined in localized message file %s:' % os.path.basename(locale_file))
                print('  %s' % ','.join(ids_not_in_locale))
            if len(undefined_ids) > 0:
                print('Non-existing message IDs used in localized message file %s:' % os.path.basename(locale_file))
                print('  %s' % ','.join(undefined_ids))
        used_ids, msg_issues = find_message_issues((core_package_path, gui_package_path))
        for msg_id in message_ids.keys():
            if msg_id not in used_ids:
                _dry_run_index = msg_id.find('_DRY_RUN')
                if _dry_run_index > 0:
                    _pure_msg_id = msg_id[:2] + msg_id[10:]
                    if _pure_msg_id in used_ids:
                        continue
                print(f'Message ID {msg_id} is not used')
    except Exception as e:
        print(e)
        sys.exit(1)
