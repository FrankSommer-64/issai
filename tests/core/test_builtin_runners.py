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
Unit tests for module core.builtin_runners.
"""
import os
import unittest

from issai.core import ENVA_ISSAI_TEST_TEST, ENVA_ISSAI_TESTS_PATH
from issai.core.builtin_runners import builtin_runner


class TestBuiltinRunners(unittest.TestCase):
    def test_py_unit_test(self):
        """
        Tests for function py_unit_test.
        """
        _fn = builtin_runner('py_unit_test')
        self.assertIsNotNone(_fn)
        _env = os.environ.copy()
        _tests_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        _venv_path = os.path.abspath(os.path.join(_tests_path, '..', '.venv'))
        _env[ENVA_ISSAI_TESTS_PATH] = _tests_path
        _env[ENVA_ISSAI_TEST_TEST] = '1'
        _rc, _stdout, _stderr = _fn(_env, _venv_path, '', 'core.test_test')
        self.assertEqual(-1, _rc)


if __name__ == '__main__':
    unittest.main()
