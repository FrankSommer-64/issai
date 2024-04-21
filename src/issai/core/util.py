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
    :returns: two-character platform locale (en, fr, de, ...)
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
