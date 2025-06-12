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
Unit tests for core.config.
"""

from pathlib import Path
import os.path
import unittest

from issai.core.config import *

DUMMY_FILE_PATH = '/tmp/config.toml'
DUMMY_PATH = '/tmp'

DL_PATTERN1 = []
DL_PATTERN2 = ['issai\\\\.toml']
DL_PATTERN3 = ['issai\\\\.toml', '.*\\\\.cfg']
DL_PATTERN4 = ['mytest.*']
DL_ATT_FILE1 = 'issai\\\\.toml'
DL_ATT_FILE2 = 'mytest_23\\\\.cfg'
UL_PATTERN1 = []
UL_PATTERN2 = ['console\\\\.log']
UL_PATTERN3 = ['console\\\\.log', 'mytest.*']
UL_PATTERN4 = ['.*\\\\.log']
UL_ATT_FILE1 = 'console\\\\.log'
UL_ATT_FILE2 = 'mytest_23\\\\.txt'

EMPTY_CFG = ''
MINIMAL_CFG = f'[product]{os.linesep}name="Issai"{os.linesep}repository-path="{DUMMY_PATH}"'
UNSUPPORTED_GRP_CFG = f'[xyz]{os.linesep}name="Issai"{os.linesep}repository-path="{DUMMY_PATH}"'
WRONG_TYPED_GRP_CFG = 'env = []'
UNSUPPORTED_ROOT_PAR_CFG = 'xyz = 123'
WRONG_TYPED_ROOT_PAR_CFG = 'testing-root-path = true'
UNSUPPORTED_PROD_PAR_CFG = f'[product]{os.linesep}name="Issai"{os.linesep}repository-path="{DUMMY_PATH}"{os.linesep}x=1'
WRONG_TYPED_PROD_PAR_CFG = f'[product]{os.linesep}name="Issai"{os.linesep}repository-path=false'
UNSUPPORTED_RUNNER_PAR_CFG = f'[runner]{os.linesep}xyz = 123'
WRONG_TYPED_RUNNER_PAR_CFG = f'[runner]{os.linesep}output-log = false'
UNSUPPORTED_TCMS_PAR_CFG = f'[tcms]{os.linesep}xyz = 123'
WRONG_TYPED_TCMS_PAR_CFG = f'[tcms]{os.linesep}execution-states = 2'
ENVA_NAME_LC_CFG = f'[env]{os.linesep}env_var="value"'
ENVA_NAME_LC_START_CFG = f'[env]{os.linesep}aVAR="value"'
ENVA_NAME_US_START_CFG = f'[env]{os.linesep}_VAR="value"'
ENVA_NAME_INV_CHAR_CFG = f'[env]{os.linesep}"A+B"="value"'
ENVA_VALUE_NOT_STR_CFG = f'[env]{os.linesep}TEST_TYPE=3'

PLAIN_VALUES_CFG = f'testing-root-path = "/tmp"'
SINGLE_ENV_VALUES_CFG = 'testing-root-path = "$env[HOME]/issai"'
MULTI_ENV_VALUES_CFG = 'testing-root-path = "/var/$env[USER]/issai/$env[USER]"'
SIMPLE_REF_CFG = f'testing-root-path = "/test"{os.linesep}[custom]{os.linesep}a = "${{testing-root-path}}/ro"'
DOUBLE_REF_CFG = f'testing-root-path="/test"{os.linesep}[custom]{os.linesep}'\
                 f'a="${{testing-root-path}}${{testing-root-path}}"'
INDIRECT_REF_CFG = f'[custom]{os.linesep}a="${{b}}"{os.linesep}b="prefix-${{c}}-suffix"{os.linesep}c="xyz"'
ROOT_REF_CFG = f'testing-root-path="/test"{os.linesep}[custom]{os.linesep}a="${{testing-root-path}}"'
DUP_ATTR1_CFG = f'testing-root-path="/test"{os.linesep}[custom]{os.linesep}testing-root-path="myroot"{os.linesep}'\
                f'a="${{testing-root-path}}"'
DUP_ATTR2_CFG = f'testing-root-path="/test"{os.linesep}[custom]{os.linesep}testing-root-path="myroot"{os.linesep}'\
                f'a="${{custom.testing-root-path}}"'
DIRECT_CYCLE_CFG = f'testing-root-path = "/tmp/${{testing-root-path}}"'
INDIRECT_CYCLE1_CFG = f'[custom]{os.linesep}a="${{b}}"{os.linesep}b="${{c}}"{os.linesep}c="${{a}}"'
INDIRECT_CYCLE2_CFG = f'[custom]{os.linesep}a="${{custom.b}}"{os.linesep}b="${{custom.c}}"{os.linesep}c="${{custom.a}}"'
INDIRECT_CYCLE3_CFG = f'[custom]{os.linesep}a="${{b}}"{os.linesep}b="${{c}}"{os.linesep}c="${{b}}"'
INDIRECT_CYCLE4_CFG = f'[custom]{os.linesep}a="${{b}}"{os.linesep}b="${{c}}"{os.linesep}c="${{custom.b}}"'
GROUP_REF_CFG = f'[product]{os.linesep}name="Issai"{os.linesep}repository-path="{DUMMY_PATH}"{os.linesep}'\
                f'[custom]{os.linesep}a="${{product}}"'


class TestConfig(unittest.TestCase):
    def test_config_root_path(self):
        """
        Tests determination of Issai configuration root directory.
        """
        _orig_home_dir = os.environ['HOME']
        try:
            # test default config root
            self.assertEqual(os.path.expanduser(ISSAI_CONFIG_PATH), config_root_path())
            # test custom config root
            _custom_root = TestConfig.custom_root_path()
            os.environ[ENVA_ISSAI_CONFIG_PATH] = _custom_root
            self.assertEqual(_custom_root, config_root_path())
            # test non-existing custom config root
            os.environ[ENVA_ISSAI_CONFIG_PATH] = os.path.join(Path.home(), 'nonexisting')
            self.assertRaises(IssaiException, config_root_path)
            # test non-existing default config root
            os.environ['HOME'] = os.path.join(Path.home(), 'nonexisting')
            self.assertRaises(IssaiException, config_root_path)
        finally:
            os.environ['HOME'] = _orig_home_dir
            del os.environ[ENVA_ISSAI_CONFIG_PATH]

    def test_check_config_structure(self):
        """
        Test configuration file structure validation.
        """
        # master configuration
        self._check_master_config_structure(EMPTY_CFG, 0)
        self._check_master_config_structure(MINIMAL_CFG, 1)
        self._check_master_config_structure(UNSUPPORTED_GRP_CFG, 1)
        self._check_master_config_structure(WRONG_TYPED_GRP_CFG, -1)
        self._check_master_config_structure(UNSUPPORTED_ROOT_PAR_CFG, 1)
        self._check_master_config_structure(WRONG_TYPED_ROOT_PAR_CFG, -1)
        self._check_master_config_structure(UNSUPPORTED_PROD_PAR_CFG, 1)
        self._check_master_config_structure(WRONG_TYPED_PROD_PAR_CFG, 1)
        self._check_master_config_structure(UNSUPPORTED_RUNNER_PAR_CFG, 1)
        self._check_master_config_structure(WRONG_TYPED_RUNNER_PAR_CFG, -1)
        self._check_master_config_structure(UNSUPPORTED_TCMS_PAR_CFG, 1)
        self._check_master_config_structure(WRONG_TYPED_TCMS_PAR_CFG, -1)
        self._check_master_config_structure(ENVA_NAME_LC_CFG, -1)
        self._check_master_config_structure(ENVA_NAME_LC_START_CFG, -1)
        self._check_master_config_structure(ENVA_NAME_US_START_CFG, -1)
        self._check_master_config_structure(ENVA_NAME_INV_CHAR_CFG, -1)
        self._check_master_config_structure(ENVA_VALUE_NOT_STR_CFG, -1)
        # product configuration
        self._check_product_config_structure(EMPTY_CFG, EMPTY_CFG, 0)
        self._check_product_config_structure(MINIMAL_CFG, EMPTY_CFG, 0)
        self._check_product_config_structure(UNSUPPORTED_GRP_CFG, EMPTY_CFG, 1, MINIMAL_CFG)
        self._check_product_config_structure(WRONG_TYPED_GRP_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(UNSUPPORTED_ROOT_PAR_CFG, EMPTY_CFG, 1, MINIMAL_CFG)
        self._check_product_config_structure(WRONG_TYPED_ROOT_PAR_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(UNSUPPORTED_PROD_PAR_CFG, EMPTY_CFG, 1)
        self._check_product_config_structure(WRONG_TYPED_PROD_PAR_CFG, EMPTY_CFG, -1)
        self._check_product_config_structure(UNSUPPORTED_RUNNER_PAR_CFG, EMPTY_CFG, 1, MINIMAL_CFG)
        self._check_product_config_structure(WRONG_TYPED_RUNNER_PAR_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(UNSUPPORTED_TCMS_PAR_CFG, EMPTY_CFG, 1, MINIMAL_CFG)
        self._check_product_config_structure(WRONG_TYPED_TCMS_PAR_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(ENVA_NAME_LC_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(ENVA_NAME_LC_START_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(ENVA_NAME_US_START_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(ENVA_NAME_INV_CHAR_CFG, EMPTY_CFG, -1, MINIMAL_CFG)
        self._check_product_config_structure(ENVA_VALUE_NOT_STR_CFG, EMPTY_CFG, -1, MINIMAL_CFG)

    def test_literal_value_of(self):
        _home = os.environ["HOME"]
        _user = os.environ["USER"]
        _cfg = LocalConfig.from_str(PLAIN_VALUES_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual("/tmp", _cfg.literal_value_of('',
                         _cfg['testing-root-path'], {'testing-root-path'}))
        _cfg = LocalConfig.from_str(SINGLE_ENV_VALUES_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual(f'{_home}/issai', _cfg.literal_value_of('',
                         _cfg['testing-root-path'], {'testing-root-path'}))
        _cfg = LocalConfig.from_str(MULTI_ENV_VALUES_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual(f'/var/{_user}/issai/{_user}', _cfg.literal_value_of('',
                         _cfg['testing-root-path'], {'testing-root-path'}))
        _cfg = LocalConfig.from_str(SIMPLE_REF_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('/test/ro', _cfg.literal_value_of('', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(DOUBLE_REF_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('/test/test', _cfg.literal_value_of('', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(INDIRECT_REF_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('prefix-xyz-suffix', _cfg.literal_value_of('custom', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(ROOT_REF_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('/test', _cfg.literal_value_of('custom', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(DUP_ATTR1_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('myroot', _cfg.literal_value_of('custom', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(DUP_ATTR2_CFG, DUMMY_FILE_PATH, False)
        self.assertEqual('myroot', _cfg.literal_value_of('custom', _cfg['custom']['a'], {'a', 'custom.a'}))
        _cfg = LocalConfig.from_str(DIRECT_CYCLE_CFG, DUMMY_FILE_PATH, False)
        self.assertRaises(IssaiException, _cfg.literal_value_of, '', _cfg['testing-root-path'], {'testing-root-path'})
        _cfg = LocalConfig.from_str(INDIRECT_CYCLE1_CFG, DUMMY_FILE_PATH, False)
        self.assertRaises(IssaiException, _cfg.literal_value_of, 'custom', _cfg['custom']['a'], {'a', 'custom.a'})
        _cfg = LocalConfig.from_str(INDIRECT_CYCLE2_CFG, DUMMY_FILE_PATH, False)
        self.assertRaises(IssaiException, _cfg.literal_value_of, 'custom', _cfg['custom']['a'], {'a', 'custom.a'})
        _cfg = LocalConfig.from_str(INDIRECT_CYCLE3_CFG, DUMMY_FILE_PATH, False)
        self.assertRaises(IssaiException, _cfg.literal_value_of, 'custom', _cfg['custom']['a'], {'a', 'custom.a'})
        _cfg = LocalConfig.from_str(INDIRECT_CYCLE4_CFG, DUMMY_FILE_PATH, False)
        self.assertRaises(IssaiException, _cfg.literal_value_of, 'custom', _cfg['custom']['a'], {'a', 'custom.a'})

    def test_unittest_config(self):
        _cfg = TestConfig.unittest_configuration()
        _repo_path = _cfg.get_value('product.repository-path')
        _src_path = f'{_repo_path}/src'
        self.assertEqual('/var/testing', _cfg.get_value('testing-root-path'))
        self.assertEqual('/usr/local/share/ca-certificates/myCA.crt', _cfg.get_value('env.SSL_CERT_FILE'))
        self.assertEqual(_repo_path, _cfg.get_value('env.ISSAI_REPOSITORY_PATH'))
        self.assertEqual(_src_path, _cfg.get_value('env.ISSAI_SOURCE_PATH'))

    def test_attachment_matching(self):
        """
        Test attachment file name pattern matching.
        """
        # check download patterns
        self._check_dl_pattern_match(None, DL_ATT_FILE1, False)
        self._check_dl_pattern_match(None, DL_ATT_FILE2, False)
        self._check_dl_pattern_match(DL_PATTERN1, DL_ATT_FILE1, False)
        self._check_dl_pattern_match(DL_PATTERN1, DL_ATT_FILE2, False)
        self._check_dl_pattern_match(DL_PATTERN2, DL_ATT_FILE1, True)
        self._check_dl_pattern_match(DL_PATTERN2, DL_ATT_FILE2, False)
        self._check_dl_pattern_match(DL_PATTERN3, DL_ATT_FILE1, True)
        self._check_dl_pattern_match(DL_PATTERN3, DL_ATT_FILE2, True)
        self._check_dl_pattern_match(DL_PATTERN4, DL_ATT_FILE1, False)
        self._check_dl_pattern_match(DL_PATTERN4, DL_ATT_FILE2, True)
        # check upload patterns
        self._check_ul_pattern_match(None, UL_ATT_FILE1, False)
        self._check_ul_pattern_match(None, UL_ATT_FILE2, False)
        self._check_ul_pattern_match(UL_PATTERN1, UL_ATT_FILE1, False)
        self._check_ul_pattern_match(UL_PATTERN1, UL_ATT_FILE2, False)
        self._check_ul_pattern_match(UL_PATTERN2, UL_ATT_FILE1, True)
        self._check_ul_pattern_match(UL_PATTERN2, UL_ATT_FILE2, False)
        self._check_ul_pattern_match(UL_PATTERN3, UL_ATT_FILE1, True)
        self._check_ul_pattern_match(UL_PATTERN3, UL_ATT_FILE2, True)
        self._check_ul_pattern_match(UL_PATTERN4, UL_ATT_FILE1, True)
        self._check_ul_pattern_match(UL_PATTERN4, UL_ATT_FILE2, False)

    def _check_master_config_structure(self, master_data, expected_result):
        _cfg = tomlkit.loads(master_data)
        try:
            _warnings = validate_config_structure(_cfg, DUMMY_FILE_PATH, False)
            self.assertEqual(expected_result, len(_warnings))
        except IssaiException:
            self.assertTrue(expected_result < 0)

    def _check_product_config_structure(self, prod_data, master_data, expected_result, default_data=''):
        _master_cfg = tomlkit.loads(master_data)
        _prod_cfg = tomlkit.loads(f'{prod_data}{os.linesep}{default_data}')
        _cfg = _master_cfg.copy()
        _cfg.update(_prod_cfg)
        try:
            _warnings = validate_config_structure(_cfg, DUMMY_FILE_PATH, True)
            self.assertEqual(expected_result, len(_warnings))
        except IssaiException:
            self.assertTrue(expected_result < 0)

    def _check_dl_pattern_match(self, pattern, file_name, expected_result):
        _cfg = TestConfig.att_pattern_configuration(CFG_PAR_TCMS_SPEC_ATTACHMENTS, pattern)
        self.assertEqual(expected_result, _cfg.download_patterns_match(file_name))

    def _check_ul_pattern_match(self, pattern, file_name, expected_result):
        _cfg = TestConfig.att_pattern_configuration(CFG_PAR_TCMS_RESULT_ATTACHMENTS, pattern)
        self.assertEqual(expected_result, _cfg.upload_patterns_match(file_name))

    @staticmethod
    def att_pattern_configuration(qualified_attr_name, patterns):
        _attr_name = qualified_attr_name.split('.')[1]
        _cfg_data = MINIMAL_CFG
        if patterns is not None:
            _cfg_data = f'{MINIMAL_CFG}{os.linesep}[tcms]{os.linesep}{_attr_name}={str(patterns)}{os.linesep}'
        return LocalConfig.from_str(_cfg_data, DUMMY_FILE_PATH, True)

    @staticmethod
    def unittest_configuration():
        """
        Reads unit test configuration from test data.
        """
        _cfgs_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'config')
        _master_cfg_file_path = os.path.join(_cfgs_path, 'unittest_master.toml')
        _product_cfg_file_path = os.path.join(_cfgs_path, 'unittest_product.toml')
        _master_cfg = LocalConfig.from_file(_master_cfg_file_path, False)
        _product_cfg = LocalConfig.from_file(_product_cfg_file_path, True)
        _product_cfg.merge(_master_cfg)
        _product_cfg.validate()
        return _product_cfg

    @staticmethod
    def unit_test_home():
        """
        :returns: "home" directory to test default Issai config root path
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testdata', 'config'))

    @staticmethod
    def custom_root_path():
        """
        :returns: custom Issai config root path for unit tests
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testdata', 'config'))


if __name__ == '__main__':
    unittest.main()
