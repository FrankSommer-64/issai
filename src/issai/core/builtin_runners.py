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
Built-in functions to run a test case.
"""

from os.path import isdir, isfile, join
import re
import subprocess

from issai.core.messages import *


def builtin_runner(function_name):
    if function_name == 'py_unit_test':
        return py_unit_test
    return None


def py_unit_test(runtime_env, venv_path, *modules):
    """
    Runs Python unit tests for specified module(s) and/or package(s).
    :param mapping runtime_env: the local issai runtime environment
    :param str venv_path: the path to virtual Python environment, may be None
    :param tuple modules: the modules/packages to test
    :returns: execution result
    :rtype: tuple
    """
    _source_files_path = runtime_env['PYTHONPATH'].split(':')[0]
    _overall_rc = 0
    _overall_stdout = ''
    _overall_stderr = ''
    if venv_path is None:
        _act_cmd = ''
        _deact_cmd = ''
    else:
        _act_cmd = 'source %s; ' % os.path.join(venv_path, 'bin', 'activate')
        _deact_cmd = '; deactivate'
    if len(modules) == 0:
        pass
    else:
        for _m in modules:
            _module_path = os.path.join(_source_files_path, str(_m))
            ut_cmd = f'python3 -m unittest discover {_module_path}'
            cmd = 'bash -c "%s%s%s"' % (_act_cmd, ut_cmd, _deact_cmd)
            _result = subprocess.run(cmd, capture_output=True, env=runtime_env, shell=True)
            if _result.returncode != 0:
                _overall_rc = -1
            _overall_stdout = '%s%s' % (_overall_stdout, _result.stdout.decode('utf-8'))
            _overall_stderr = '%s%s' % (_overall_stderr, _result.stderr.decode('utf-8'))
    if re.search('^FAILED', _overall_stderr, re.MULTILINE|re.DOTALL):
        _overall_rc = -1
    return _overall_rc, _overall_stdout, _overall_stderr


def _find_py_unit_test_files(node, modules):
    if isfile(node):
        return [node]
    _files = []
    if len(modules) == 0:
        _files.extend([join(node, f) for f in os.listdir(node) if _is_py_unit_test_file(join(node, f))])
        _node_dirs = [d for d in os.listdir(node) if isdir(join(node, d))]
        for d in _node_dirs:
            if d == '__pycache__':
                continue
            _files.extend(_find_py_unit_test_files(join(node, d), ()))
    else:
        for _m in modules:
            _files.extend(_find_py_unit_test_files(join(node, _m), ()))
    return _files


def _is_py_unit_test_file(file_path):
    if not file_path.endswith('.py'):
        return False
    if not isfile(file_path):
        return False
    with open(file_path, 'r') as f:
        return 'import unittest' in f.read()
