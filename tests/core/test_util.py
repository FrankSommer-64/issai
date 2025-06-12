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
Unit tests for core.util.
"""

import unittest

from issai.core.util import *

DUMMY_FILE_PATH = '/tmp/config.toml'
DUMMY_PATH = '/tmp'


class TestUtil(unittest.TestCase):
    def test_property_matrix(self):
        """
        Tests class PropertyMatrix.
        """
        # empty matrix
        _matrix = PropertyMatrix()
        self.assertTrue(_matrix.is_empty())
        self.assertEqual('', _matrix.code())
        self.assertEqual('', _matrix.suffix_code())
        for _ in _matrix:
            self.assertTrue(False)
        # property without values must be ignored
        _matrix.add('NO_VALUE_PROP', [])
        self.assertTrue(_matrix.is_empty())
        self.assertEqual('', _matrix.code())
        self.assertEqual('', _matrix.suffix_code())
        for _ in _matrix:
            self.assertTrue(False)
        # single property
        _matrix = PropertyMatrix()
        _matrix.add('LANG', ['en', 'de', 'fr'])
        self.assertFalse(_matrix.is_empty())
        _res = {}
        _count = 0
        for _props in _matrix:
            _count += 1
            _code_str = ''
            for _n, _v in _props:
                _pstr = f'{_n}={_v}'
                if _n not in _res:
                    _res[_n] = ''
                _res[_n] = f'{_res[_n]}{_pstr}'
                _code_str += f'_{_v}'
            self.assertEqual(_code_str[1:], _matrix.code())
            self.assertEqual(_code_str, _matrix.suffix_code())
        self.assertEqual(3, _count)
        self.assertEqual(1, len(_res))
        self.assertEqual('LANG=enLANG=deLANG=fr', _res['LANG'])
        # two properties
        _matrix = PropertyMatrix()
        _matrix.add('LANG', ['en', 'de', 'fr'])
        _matrix.add('SCHEME', ['none', 'version', 'build'])
        self.assertFalse(_matrix.is_empty())
        _res = {}
        _count = 0
        for _props in _matrix:
            _count += 1
            _code_str = ''
            for _n, _v in _props:
                _pstr = f'{_n}={_v}'
                if _n not in _res:
                    _res[_n] = ''
                _res[_n] = f'{_res[_n]}{_pstr}'
                _code_str += f'_{_v}'
            self.assertEqual(_code_str[1:], _matrix.code())
            self.assertEqual(_code_str, _matrix.suffix_code())
        self.assertEqual(9, _count)
        self.assertEqual(2, len(_res))
        self.assertEqual('LANG=enLANG=enLANG=enLANG=deLANG=deLANG=deLANG=frLANG=frLANG=fr', _res['LANG'])
        self.assertEqual('SCHEME=noneSCHEME=versionSCHEME=buildSCHEME=noneSCHEME=versionSCHEME=build'
                         'SCHEME=noneSCHEME=versionSCHEME=build', _res['SCHEME'])


if __name__ == '__main__':
    unittest.main()
