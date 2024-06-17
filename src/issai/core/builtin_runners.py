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
import os.path
import sys
import unittest

from issai.core import ENVA_ISSAI_TESTS_PATH
from issai.core.messages import *


def builtin_runner(function_name):
    """
    :param str function_name: the desired builtin runner function name
    :returns: function corresponding to specified name
    :rtype: function
    """
    if function_name == 'py_unit_test':
        return py_unit_test
    return None


def py_unit_test(runtime_env, venv_path, _case_name, modules):
    """
    Runs Python unit tests for specified module(s) and/or package(s).
    :param os._Environ runtime_env: the local issai runtime environment
    :param str venv_path: the path to virtual Python environment, may be None
    :param str _case_name: the test case name
    :param str modules: the module(s) to test, separated by comma
    :returns: execution result
    :rtype: tuple
    """
    _overall_rc = 0
    _overall_stdout = []
    _overall_stderr = []
    modules = modules.strip()
    _orig_sys_path = sys.path
    _orig_sys_prefix = sys.prefix
    _orig_env = os.environ.copy()
    os.environ = runtime_env.copy()
    try:
        if venv_path is not None:
            _activate_file_path = os.path.join(venv_path, 'bin', 'activate_this.py')
            exec(open(_activate_file_path).read(), {'__file__': _activate_file_path})
        _ut_runtime_env = runtime_env.copy()
        _tests_path = runtime_env[ENVA_ISSAI_TESTS_PATH]
        _test_loader = unittest.defaultTestLoader
        _test_runner = unittest.TextTestRunner()
        _test_runner.buffer = True
        if len(modules) == 0:
            # run all tests underneath test path using discover
            _test_suite = _test_loader.discover(_tests_path)
            _test_result = _test_runner.run(_test_suite)
        else:
            # run tests for one or more modules
            for _m in modules.split(','):
                _m_parts = _m.split('.')
                _m_path = os.path.join(_tests_path, os.path.sep.join(_m_parts))
                if os.path.isdir(_m_path):
                    _test_suite = _test_loader.discover(_m_path)
                else:
                    _test_suite = _test_loader.loadTestsFromName(_m)
                _test_result = _test_runner.run(_test_suite)
                _error_count = len(_test_result.errors)
                if _error_count == 0:
                    _overall_stdout.append(localized_message(I_RUN_PY_UNIT_TEST_PASSED, _test_result.testsRun, _m))
                else:
                    _overall_rc = 1
                    _overall_stdout.append(localized_message(I_RUN_PY_UNIT_TEST_FAILED,
                                                             _error_count, _test_result.testsRun, _m))
                    _err_msg = _test_runner.stream.read()
                    _overall_stderr.extend(_test_result.errors[1])
    except BaseException as _e:
        _overall_rc = -1
        _overall_stderr.append(str(_e))
    finally:
        os.environ = _orig_env
        if venv_path is not None:
            sys.path = _orig_sys_path
            sys.prefix = _orig_sys_prefix
    return _overall_rc, os.linesep.join(_overall_stdout), os.linesep.join(_overall_stderr)
