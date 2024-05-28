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
Utility functions used throughout the entire framework.
"""

import os
import platform
import re
import subprocess

from issai.core import PLATFORM_ARCH_PREFIX, PLATFORM_OS_PREFIX


_OS_TAG_FMT = '%s%%s' % PLATFORM_OS_PREFIX
_ARCH_TAG_FMT = '%s%%s' % PLATFORM_ARCH_PREFIX


def full_path_of(path_spec):
    """
    Returns full path for given path.
    :param str path_spec: the path
    :returns: full path
    :rtype: str
    """
    if path_spec.startswith('~'):
        return os.path.expanduser(path_spec)
    return os.path.abspath(path_spec)


def shell_cmd(cmd, runtime_env=None):
    """
    Executes the specified command on the operating system shell.
    :param list cmd: the command to execute
    :param dict runtime_env: the optional environment settings
    :returns: return code, stdout, stderr
    :rtype: tuple
    :raises: TimeoutException if pipe command times out
    """
    if runtime_env is None:
        _res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    else:
        _res = subprocess.run(cmd, env=runtime_env, capture_output=True, encoding='utf-8')
    return _res.returncode, _res.stdout, _res.stderr


def platform_architecture_tag():
    """
    Determines tag name for local machine architecture.
    Tag name starts with prefix arch_ followed by architecture (x86_64, aarch64, ...)
    :returns: machine architecture tag
    :rtype: str
    """
    return _ARCH_TAG_FMT % platform.machine().lower()


def platform_os_tag():
    """
    Determines tag name for local operating system.
    Tag name starts with prefix os_ followed by operating system (linux, windows, ...)
    :returns: operating system tag
    :rtype: str
    """
    return _OS_TAG_FMT % platform.system().lower()


def platform_locale():
    """
    Determines locale setting for current platform.
    Returns None, if locale cannot be determined.
    :returns: two-character platform locale (e.g. 'en')
    :rtype: str
    """
    # noinspection PyBroadException
    try:
        _operating_system = platform.system().lower()
        if _operating_system == 'linux':
            _rc, _stdout, _stderr = shell_cmd(['locale'])
            if _rc == 0:
                _m = re.search(r'.*LANG=(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    return _m.group(1)[:2].lower()
                _m = re.search(r'.*LANGUAGE=(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    return _m.group(1)[:2].lower()
        elif _operating_system == 'windows':
            _rc, _stdout, _stderr = shell_cmd(['systeminfo'])
            if _rc == 0:
                _m = re.search(r'.*System\s+Locale:\s+(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    return _m.group(1)[:2].lower()
        else:
            if 'LANG' in os.environ:
                return os.environ['LANG'][:2].lower()
            if 'LANGUAGE' in os.environ:
                return os.environ['LANGUAGE'][:2].lower()
    except Exception:
        pass
    return None


def python_value(value):
    """
    Convert tomlkit item to python value.
    Currently boolean values are not wrapped by Bool by tomlkit.
    :param value: the tomlkit value
    :return: the pure Python value
    """
    try:
        return value.unwrap()
    except AttributeError:
        return value


class PropertyMatrix:
    """
    Iterable for property combinations as used in environments.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.count = 0
        self.names = []
        self.values = []
        self.indexes = []

    def add(self, property_name, property_values):
        """
        Adds a property to the matrix.
        :param str property_name: the property name
        :param list property_values: the property values
        """
        if len(property_values) == 0:
            return
        self.names.append(property_name)
        self.values.append(property_values)
        self.indexes.append(-1)
        self.count += 1

    def is_empty(self):
        """
        :returns: True, if matrix contains no elements
        :rtype: bool
        """
        return self.count == 0

    def code(self):
        """
        :returns: code string of all property values; empty string if empty
        :rtype: str
        """
        if self.is_empty():
            return ''
        return '_'.join([self.values[_i][self.indexes[_i]] for _i in range(0, self.count)])

    def suffix_code(self):
        """
        :returns: code string of all property values, starting with an underscore; empty string if empty
        :rtype: str
        """
        return '' if self.is_empty() else f'_{self.code()}'

    def _increment_index(self, property_nr):
        """
        Increments internal index to access next element.
        :param int property_nr: the property number
        :raises StopIteration: if all elements have been consumed
        """
        _index = self.indexes[property_nr]
        if _index < 0:
            for _i in range(0, self.count):
                self.indexes[_i] = 0
            return
        if _index >= len(self.values[property_nr]) - 1:
            if property_nr == 0:
                raise StopIteration
            self.indexes[property_nr] = 0
            self._increment_index(property_nr - 1)
            return
        self.indexes[property_nr] += 1

    def __iter__(self):
        """
        :returns: Iterator over the matrix
        """
        return self

    def __next__(self):
        """
        :returns: next element
        :rtype: list[tuple]
        :raises StopIteration: if all elements have been consumed
        """
        if self.count == 0:
            raise StopIteration
        self._increment_index(self.count - 1)
        return [(self.names[_i], self.values[_i][self.indexes[_i]]) for _i in range(0, self.count)]
