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
Unit tests for core.resourcemanager.
"""

import os
import unittest

import tomlkit

from issai.core.issai_exception import IssaiException
from issai.core.status import ContainerStatus
import issai.core.resourcemanager


LOAD_CONTAINER_PR_FILES = {'pr-f-entity-id-mismatch': (False, [], [], [['test-plan-results.run_id', 'entity-id']],
                                                       [], [], []),
                           'pr-f-entity-name-mismatch': (False, [], [],
                                                         [['test-plan-results.plan-name', 'entity-name']], [], [], []),
                           'pr-f-notes-wrong-type': (False, [['test-plan-results(#1).notes']], [], [], [], [], []),
                           'pr-f-output-file-elems-wrong-type': (False,
                                                                 [['test-plan-results(#1).output-files-elements']],
                                                                 [], [], [], [], []),
                           'pr-f-output-files-wrong-type': (False, [['test-plan-results(#1).output-files']],
                                                            [], [], [], [], []),
                           'pr-f-plan-name-missing': (False, [], [], [], [['test-plan-results(#1).plan-name']], [], []),
                           'pr-f-plan-name-wrong-type': (False, [['test-plan-results(#1).plan-name']],
                                                         [], [], [], [], []),
                           'pr-f-results-group-missing': (False, [], [], [], [['test-plan-results']], [], []),
                           'pr-f-run-id-missing': (False, [], [], [], [['test-plan-results(#1).run_id']], [], []),
                           'pr-f-run-id-unknown': (True, [], [], [], [], [], []),
                           'pr-f-run-id-wrong-type': (False, [['test-plan-results(#1).run_id']], [], [], [], [], []),
                           'pr-f-run-plan-mismatch': (True, [], [], [], [], [], []),
                           'pr-f-start-date-missing': (False, [], [], [], [['test-plan-results(#1).start_date']],
                                                       [], []),
                           'pr-f-start-date-wrong-type': (False, [['test-plan-results(#1).start_date']],
                                                          [], [], [], [], []),
                           'pr-f-stop-date-missing': (False, [], [], [], [['test-plan-results(#1).stop_date']], [], []),
                           'pr-f-stop-date-wrong-type': (False, [['test-plan-results(#1).stop_date']],
                                                         [], [], [], [], []),
                           'pr-f-summary-wrong-type': (False, [['test-plan-results(#1).summary']], [], [], [], [], []),
                           'pr-s-family-plan': (True, [], [], [], [], [], []),
                           'pr-s-full-attributes': (True, [], [], [], [], [], []),
                           'pr-s-group-attr-not-supported': (True, [], [], [], [], [],
                                                             [['test-plan-results(#1).superfluous']]),
                           'pr-s-group-not-supported': (True, [], [], [], [], [], [['miscellaneous']]),
                           'pr-s-mandatory-attrs-only': (True, [], [], [], [], [], []),
                           'pr-s-single-plan': (True, [], [], [], [], [], []),
                           'pr-s-top-level-attr-not-supported': (True, [], [], [], [], [], [['priority']]),
                           }

LOAD_CONTAINER_ENTITIES = {'plan_result': LOAD_CONTAINER_PR_FILES}


class TestResourceManager(unittest.TestCase):
    def test_load_container_file(self):
        """
        Tests for function container_status.
        """
        _curr_dir = os.path.dirname(os.path.realpath(__file__))
        _project_root = os.path.abspath('%s%s..%s..' % (_curr_dir, os.sep, os.sep))
        _test_file_root = os.path.join(_project_root, 'tests', 'testdata', 'input')
        self._run_container_checks(_test_file_root, 'plan_result')

    def _run_container_checks(self, root_dir, sub_dir):
        """
        Runs test of function load_container_file for all TOML files in specified subdirectory.
        :param root_dir: the input files root directory
        :param sub_dir: the subdirectory containing the input files to check
        """
        _input_dir = os.path.join(root_dir, sub_dir).encode('utf-8')
        for _file_name in os.listdir(_input_dir):
            _file_path = os.path.join(_input_dir, _file_name)
            if not os.path.isfile(_file_path):
                continue
            self._check_container_file(_file_path)

    def _check_container_file(self, file_path):
        """
        Runs test of function load_container_file for specified TOML file.
        :param bytes|str file_path: the TOML file to check
        """
        _entity_name = os.path.basename(os.path.dirname(file_path)).decode('utf-8')
        _test_descriptors = LOAD_CONTAINER_ENTITIES.get(_entity_name)
        if _test_descriptors is None:
            return
        _file_name = os.path.basename(file_path)[:-5].decode('utf-8')
        # if not _file_name.endswith('not-supported'):
        #    return
        _test_desc = _test_descriptors.get(_file_name)
        if _test_desc is None:
            raise RuntimeError(f'Test descriptor for file {_entity_name}.{_file_name} missing')
        with open(file_path, 'r') as _f:
            _toml_data = tomlkit.load(_f)
        _status = issai.core.resourcemanager.container_status(_toml_data)
        _exp_accept, _exp_inv_types, _exp_inv_values, _exp_mismatch, _exp_missing, _exp_mults, exp_unsupp = _test_desc
        print(f'{_file_name}: {_status}')
        self.assertEqual(_exp_accept, _status.is_acceptable())
        self.assertEqual(_exp_inv_types, _status[ContainerStatus.INVALID_TYPE])
        self.assertEqual(_exp_inv_values, _status[ContainerStatus.INVALID_VALUE])
        self.assertEqual(_exp_mismatch, _status[ContainerStatus.MISMATCH])
        self.assertEqual(_exp_missing, _status[ContainerStatus.MISSING])
        self.assertEqual(_exp_mults, _status[ContainerStatus.MULTIPLE])
        self.assertEqual(exp_unsupp, _status[ContainerStatus.UNSUPPORTED])


if __name__ == '__main__':
    unittest.main()
