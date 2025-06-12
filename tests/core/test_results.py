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
Unit tests for core.results.
"""
import datetime
import os
import time
import unittest

from issai.core import *
from issai.core.results import CaseResult, PlanResult, Result
from issai.core.issai_exception import IssaiException


DEFAULT_CASE_ID = 23
DEFAULT_CASE_SUMMARY = 'TestCase23'
DEFAULT_PLAN_ID = 18
DEFAULT_PLAN_NAME = 'TestPlan23'
DAUGHTER_CASES_BASE = 20
DAUGHTER_PLAN_ID = DEFAULT_PLAN_ID + 1
DAUGHTER_PLAN_NAME = 'DaughterPlan'
GRAND_CHILD_CASES_BASE = 40
GRAND_CHILD_PLAN_ID = DEFAULT_PLAN_ID + 3
GRAND_CHILD_PLAN_NAME = 'GrandchildPlan'
PARENT_CASES_BASE = 10
SON_CASES_BASE = 30
SON_PLAN_ID = DEFAULT_PLAN_ID + 2
SON_PLAN_NAME = 'SonPlan'


class TestResult(unittest.TestCase):
    """
    Tests for base class Result.
    """
    def test_constructor(self):
        _result = Result(RESULT_TYPE_CASE_RESULT, DEFAULT_PLAN_ID)
        self.assertEqual(RESULT_TYPE_CASE_RESULT, _result.result_type())
        self.assertEqual(DEFAULT_PLAN_ID, _result.get_attr_value(ATTR_PLAN))
        self.assertEqual(-1, _result.duration())
        self.assertEqual(0, len(_result.get_attr_value(ATTR_OUTPUT_FILES)))
        self.assertIsNone(_result.get_attr_value(ATTR_START_DATE))
        self.assertIsNone(_result.get_attr_value(ATTR_STOP_DATE))

    def test_start_stop(self):
        _result = Result(RESULT_TYPE_CASE_RESULT, DEFAULT_PLAN_ID)
        _result.mark_start()
        self.assertIsNone(_result.get_attr_value(ATTR_STOP_DATE))
        self.assertIsNotNone(_result.get_attr_value(ATTR_START_DATE))
        self.assertGreaterEqual(datetime.datetime.now(), _result.get_attr_value(ATTR_START_DATE))
        time.sleep(0.1)
        _result.mark_end()
        self.assertIsNotNone(_result.get_attr_value(ATTR_STOP_DATE))
        self.assertGreaterEqual(datetime.datetime.now(), _result.get_attr_value(ATTR_STOP_DATE))
        self.assertLessEqual(0.1, _result.duration())

    def test_output_files(self):
        _result = Result(RESULT_TYPE_CASE_RESULT, DEFAULT_PLAN_ID)
        _result.add_output_file('file1.log')
        _result.add_output_file('file2.log')
        self.assertEqual(2, len(_result.get_attr_value(ATTR_OUTPUT_FILES)))
        self.assertEqual('file1.log', _result.get_attr_value(ATTR_OUTPUT_FILES)[0])
        self.assertEqual('file2.log', _result.get_attr_value(ATTR_OUTPUT_FILES)[1])


class TestCaseResult(unittest.TestCase):
    """
    Tests for class CaseResult.
    """
    def test_constructor(self):
        _result = CaseResult(DEFAULT_PLAN_ID, DEFAULT_CASE_ID, DEFAULT_CASE_SUMMARY, '')
        self.assertEqual(RESULT_TYPE_CASE_RESULT, _result.result_type())
        self.assertEqual(DEFAULT_PLAN_ID, _result.get_attr_value(ATTR_PLAN))
        self.assertEqual(DEFAULT_CASE_ID, _result.get_attr_value(ATTR_CASE))
        self.assertEqual(DEFAULT_CASE_SUMMARY, _result.get_attr_value(ATTR_CASE_NAME))
        self.assertEqual(RESULT_STATUS_PASSED, _result.get_attr_value(ATTR_STATUS))
        self.assertEqual('', _result.get_attr_value(ATTR_MATRIX_CODE))
        self.assertEqual('', _result.get_attr_value(ATTR_TESTER_NAME))
        self.assertEqual('', _result.get_attr_value(ATTR_COMMENT))

    def test_get_set_attr_value(self):
        _result = CaseResult(DEFAULT_PLAN_ID, DEFAULT_CASE_ID, DEFAULT_CASE_SUMMARY, '')
        # set supported attribute
        _result.set_attr_value(ATTR_COMMENT, 'bla')
        self.assertEqual('bla', _result.get_attr_value(ATTR_COMMENT))
        _result.set_attr_value(ATTR_STATUS, RESULT_STATUS_ERROR)
        self.assertEqual(RESULT_STATUS_ERROR, _result.get_attr_value(ATTR_STATUS))
        _result.set_attr_value(ATTR_TESTER_NAME, 'tester')
        self.assertEqual('tester', _result.get_attr_value(ATTR_TESTER_NAME))
        # get unsupported attribute
        self.assertRaises(IssaiException, _result.get_attr_value, ATTR_RUN)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_RUN, 99)
        # set immutable attribute
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_CASE, 99)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_CASE_NAME, 'bla')
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_MATRIX_CODE, 'en')
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_OUTPUT_FILES, ['test.log'])
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_PLAN, 99)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_START_DATE, datetime.datetime.now())
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_STOP_DATE, datetime.datetime.now())
        # set invalid attribute value
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_COMMENT, True)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_STATUS, -1)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_TESTER_NAME, [])

    def test_append_attr_value(self):
        _result = CaseResult(DEFAULT_PLAN_ID, DEFAULT_CASE_ID, DEFAULT_CASE_SUMMARY, '')
        # append to supported attribute
        _result.append_attr_value(ATTR_COMMENT, 'line1')
        self.assertEqual('line1', _result.get_attr_value(ATTR_COMMENT))
        _result.append_attr_value(ATTR_COMMENT, 'line2')
        _comment_lines = _result.get_attr_value(ATTR_COMMENT).split(os.linesep)
        self.assertEqual(2, len(_comment_lines))
        self.assertEqual('line1', _comment_lines[0])
        self.assertEqual('line2', _comment_lines[1])
        # immutable non-string attributes must ignore appends
        self.verify_append_ignored(_result, ATTR_CASE, 99)
        self.verify_append_ignored(_result, ATTR_OUTPUT_FILES, ['test.log'])
        self.verify_append_ignored(_result, ATTR_PLAN, 99)
        self.verify_append_ignored(_result, ATTR_START_DATE, datetime.datetime.now())
        self.verify_append_ignored(_result, ATTR_STOP_DATE, datetime.datetime.now())
        # immutable string attributes must raise exception
        self.assertRaises(IssaiException, _result.append_attr_value, ATTR_CASE_NAME, 'bla')
        self.assertRaises(IssaiException, _result.append_attr_value, ATTR_MATRIX_CODE, 'en')
        # append invalid attribute value must be ignored
        self.verify_append_ignored(_result, ATTR_COMMENT, True)
        self.verify_append_ignored(_result, ATTR_STATUS, -1)
        self.verify_append_ignored(_result, ATTR_TESTER_NAME, [])

    def test_merge_matrix_result(self):
        self.verify_merge(RESULT_STATUS_PASSED, RESULT_STATUS_PASSED, RESULT_STATUS_PASSED)
        self.verify_merge(RESULT_STATUS_PASSED, RESULT_STATUS_FAILED, RESULT_STATUS_FAILED)
        self.verify_merge(RESULT_STATUS_PASSED, RESULT_STATUS_ERROR, RESULT_STATUS_ERROR)
        self.verify_merge(RESULT_STATUS_FAILED, RESULT_STATUS_PASSED, RESULT_STATUS_FAILED)
        self.verify_merge(RESULT_STATUS_FAILED, RESULT_STATUS_FAILED, RESULT_STATUS_FAILED)
        self.verify_merge(RESULT_STATUS_FAILED, RESULT_STATUS_ERROR, RESULT_STATUS_ERROR)
        self.verify_merge(RESULT_STATUS_ERROR, RESULT_STATUS_PASSED, RESULT_STATUS_ERROR)
        self.verify_merge(RESULT_STATUS_ERROR, RESULT_STATUS_FAILED, RESULT_STATUS_ERROR)
        self.verify_merge(RESULT_STATUS_ERROR, RESULT_STATUS_ERROR, RESULT_STATUS_ERROR)

    def verify_merge(self, status1, status2, expected_merge_status):
        _res1 = TestCaseResult.case_result(DEFAULT_PLAN_ID, DEFAULT_CASE_ID, status1, 'en', True)
        _res2 = TestCaseResult.case_result(DEFAULT_PLAN_ID, DEFAULT_CASE_ID, status2, 'de', True)
        _res1.merge_matrix_result(_res2)
        self.assertEqual(expected_merge_status, _res1.get_attr_value(ATTR_STATUS))
        self.assertEqual(_res2.get_attr_value(ATTR_STOP_DATE), _res1.get_attr_value(ATTR_STOP_DATE))
        _comment_lines = _res1.get_attr_value(ATTR_COMMENT).split(os.linesep)
        self.assertEqual(3, len(_comment_lines))
        self.assertEqual(f'TestCase{DEFAULT_CASE_ID}_en', _comment_lines[0])
        self.assertLessEqual(0, _comment_lines[1].index(" 'de':"))
        self.assertEqual(f'TestCase{DEFAULT_CASE_ID}_de', _comment_lines[2])

    def verify_append_ignored(self, result, attr_name, attr_value):
        _orig_value = result.get_attr_value(attr_name)
        result.append_attr_value(attr_name, attr_value)
        self.assertEqual(_orig_value, result.get_attr_value(attr_name))

    @staticmethod
    def case_result(plan_id, case_id, status, matrix_code, add_comment):
        _res = CaseResult(plan_id, case_id, f'TestCase{case_id}', matrix_code)
        _res.mark_start()
        time.sleep(0.1)
        _res.mark_end()
        _res.set_attr_value(ATTR_STATUS, status)
        if add_comment:
            _res.set_attr_value(ATTR_COMMENT, f'TestCase{case_id}_{matrix_code}')
        return _res


class TestPlanResult(unittest.TestCase):
    """
    Tests for class PlanResult.
    """
    def test_constructor(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        self.assertEqual(RESULT_TYPE_PLAN_RESULT, _result.result_type())
        self.assertEqual(DEFAULT_PLAN_ID, _result.get_attr_value(ATTR_PLAN))
        self.assertEqual(DEFAULT_PLAN_NAME, _result.get_attr_value(ATTR_PLAN_NAME))
        self.assertEqual('', _result.get_attr_value(ATTR_NOTES))
        self.assertEqual('', _result.get_attr_value(ATTR_SUMMARY))
        self.assertEqual(0, len(_result.get_attr_value(ATTR_CHILD_PLAN_RESULTS)))
        self.assertEqual(0, len(_result.get_attr_value(ATTR_CASE_RESULTS)))

    def test_get_set_attr_value(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        # set supported attribute
        _result.set_attr_value(ATTR_NOTES, 'bla')
        self.assertEqual('bla', _result.get_attr_value(ATTR_NOTES))
        _result.set_attr_value(ATTR_SUMMARY, 'bla')
        self.assertEqual('bla', _result.get_attr_value(ATTR_SUMMARY))
        # get unsupported attribute
        self.assertRaises(IssaiException, _result.get_attr_value, ATTR_COMMENT)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_COMMENT, 'bla')
        # set immutable attribute
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_PLAN, 99)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_PLAN_NAME, 'bla')
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_CASE_RESULTS, [])
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_CHILD_PLAN_RESULTS, [])
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_OUTPUT_FILES, ['test.log'])
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_START_DATE, datetime.datetime.now())
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_STOP_DATE, datetime.datetime.now())
        # set invalid attribute value
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_NOTES, True)
        self.assertRaises(IssaiException, _result.set_attr_value, ATTR_SUMMARY, -1)

    def test_append_attr_value(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        # append to supported attribute
        _result.append_attr_value(ATTR_NOTES, 'line1')
        self.assertEqual('line1', _result.get_attr_value(ATTR_NOTES))
        _result.append_attr_value(ATTR_NOTES, 'line2')
        _comment_lines = _result.get_attr_value(ATTR_NOTES).split(os.linesep)
        self.assertEqual(2, len(_comment_lines))
        self.assertEqual('line1', _comment_lines[0])
        self.assertEqual('line2', _comment_lines[1])
        _result.append_attr_value(ATTR_SUMMARY, 'line1')
        self.assertEqual('line1', _result.get_attr_value(ATTR_SUMMARY))
        _result.append_attr_value(ATTR_SUMMARY, 'line2')
        _summary_lines = _result.get_attr_value(ATTR_SUMMARY).split(os.linesep)
        self.assertEqual(2, len(_summary_lines))
        self.assertEqual('line1', _summary_lines[0])
        self.assertEqual('line2', _summary_lines[1])
        # immutable non-string attributes must ignore appends
        self.verify_append_ignored(_result, ATTR_PLAN, 99)
        self.verify_append_ignored(_result, ATTR_CASE_RESULTS, [])
        self.verify_append_ignored(_result, ATTR_CHILD_PLAN_RESULTS, [])
        self.verify_append_ignored(_result, ATTR_OUTPUT_FILES, ['test.log'])
        self.verify_append_ignored(_result, ATTR_START_DATE, datetime.datetime.now())
        self.verify_append_ignored(_result, ATTR_STOP_DATE, datetime.datetime.now())
        # immutable string attributes must raise exception
        self.assertRaises(IssaiException, _result.append_attr_value, ATTR_PLAN_NAME, 'bla')
        # append invalid attribute value
        self.verify_append_ignored(_result, ATTR_NOTES, True)
        self.verify_append_ignored(_result, ATTR_SUMMARY, -1)

    def test_case_results(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        self.assertEqual(0, len(_result.case_results()))
        _result = TestPlanResult.result_family((3, 0, 0), (2, 0, 0), (2, 0, 0), (1, 0, 0), '', False)
        _case_results = _result.case_results()
        self.assertEqual(8, len(_result.case_results()))
        self.assertEqual(PARENT_CASES_BASE, _case_results[0][ATTR_CASE])
        self.assertEqual(PARENT_CASES_BASE+1, _case_results[1][ATTR_CASE])
        self.assertEqual(PARENT_CASES_BASE+2, _case_results[2][ATTR_CASE])
        self.assertEqual(DAUGHTER_CASES_BASE, _case_results[3][ATTR_CASE])
        self.assertEqual(DAUGHTER_CASES_BASE+1, _case_results[4][ATTR_CASE])
        self.assertEqual(GRAND_CHILD_CASES_BASE, _case_results[5][ATTR_CASE])
        self.assertEqual(SON_CASES_BASE, _case_results[6][ATTR_CASE])
        self.assertEqual(SON_CASES_BASE+1, _case_results[7][ATTR_CASE])

    def test_plan_results(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        self.assertEqual(1, len(_result.plan_results()))
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0), '', False)
        _plan_results = _result.plan_results()
        self.assertEqual(4, len(_result.plan_results()))
        self.assertEqual(DEFAULT_PLAN_ID, _plan_results[0][ATTR_PLAN])
        self.assertEqual(DAUGHTER_PLAN_ID, _plan_results[1][ATTR_PLAN])
        self.assertEqual(GRAND_CHILD_PLAN_ID, _plan_results[2][ATTR_PLAN])
        self.assertEqual(SON_PLAN_ID, _plan_results[3][ATTR_PLAN])

    def test_case_result(self):
        _result = TestPlanResult.result_family((3, 0, 0), (2, 0, 0), (2, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(PARENT_CASES_BASE, _result.case_result(PARENT_CASES_BASE)[ATTR_CASE])
        self.assertEqual(PARENT_CASES_BASE+1, _result.case_result(PARENT_CASES_BASE+1)[ATTR_CASE])
        self.assertEqual(PARENT_CASES_BASE+2, _result.case_result(PARENT_CASES_BASE+2)[ATTR_CASE])
        self.assertIsNone(_result.case_result(999))

    def test_child_plan_results(self):
        _result = TestPlanResult.result_family((3, 0, 0), (2, 0, 0), (2, 0, 0), (1, 0, 0), '', False)
        _daughter_result = _result.child_plan_result(DAUGHTER_PLAN_ID)
        self.assertEqual(DAUGHTER_PLAN_ID, _daughter_result[ATTR_PLAN])
        self.assertEqual(SON_PLAN_ID, _result.child_plan_result(SON_PLAN_ID)[ATTR_PLAN])
        self.assertEqual(GRAND_CHILD_PLAN_ID, _daughter_result.child_plan_result(GRAND_CHILD_PLAN_ID)[ATTR_PLAN])
        self.assertIsNone(_result.child_plan_result(DEFAULT_PLAN_ID))
        self.assertIsNone(_result.child_plan_result(GRAND_CHILD_PLAN_ID))
        self.assertIsNone(_daughter_result.child_plan_result(999))

    def test_result_status(self):
        # all test cases PASSED
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_PASSED, _result.result_status())
        # failure in parent
        _result = TestPlanResult.result_family((1, 1, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_FAILED, _result.result_status())
        # error in parent
        _result = TestPlanResult.result_family((1, 1, 1), (1, 0, 0), (1, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in daughter
        _result = TestPlanResult.result_family((1, 0, 0), (1, 1, 0), (1, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_FAILED, _result.result_status())
        # error in daughter
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 1), (1, 0, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in son
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 1, 0), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_FAILED, _result.result_status())
        # error in son
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 0, 1), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in grandchild
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 1, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_FAILED, _result.result_status())
        # error in grandchild
        _result = TestPlanResult.result_family((1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in daughter, error in son
        _result = TestPlanResult.result_family((1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 0, 0), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in daughter, error in grandchild
        _result = TestPlanResult.result_family((1, 0, 0), (1, 1, 0), (1, 0, 0), (1, 0, 1), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())
        # failure in parent and daughter, error in grandchild
        _result = TestPlanResult.result_family((1, 1, 0), (1, 1, 0), (1, 0, 0), (1, 0, 1), '', False)
        self.assertEqual(RESULT_STATUS_ID_ERROR, _result.result_status())

    def test_merge_matrix_result(self):
        _result = PlanResult(DEFAULT_PLAN_ID, DEFAULT_PLAN_NAME)
        # merge first matrix result
        _result_en = TestPlanResult.result_family((2, 0, 0), (2, 0, 0), (2, 0, 0), (2, 0, 0), 'en', True)
        _result.merge_matrix_result(_result_en)
        self.verify_merge(_result, _result_en)
        # merge second matrix result
        _result_de = TestPlanResult.result_family((2, 0, 0), (2, 0, 0), (2, 0, 0), (1, 1, 0), 'de', True)
        _result.merge_matrix_result(_result_de)
        self.verify_merge(_result, _result_de)

    @staticmethod
    def result_family(parent_states, daughter_states, son_states, grandchild_states, matrix_code, add_texts):
        _parent = TestPlanResult.plan_result(DEFAULT_PLAN_ID, PARENT_CASES_BASE, parent_states, matrix_code, add_texts)
        _daughter = TestPlanResult.plan_result(DAUGHTER_PLAN_ID, DAUGHTER_CASES_BASE, daughter_states, matrix_code,
                                               add_texts)
        _son = TestPlanResult.plan_result(SON_PLAN_ID, SON_CASES_BASE, son_states, matrix_code, add_texts)
        _grandchild = TestPlanResult.plan_result(GRAND_CHILD_PLAN_ID, GRAND_CHILD_CASES_BASE, grandchild_states,
                                                 matrix_code, add_texts)
        _daughter.add_plan_result(_grandchild)
        _parent.add_plan_result(_daughter)
        _parent.add_plan_result(_son)
        return _parent

    @staticmethod
    def plan_result(plan_id, base_case_id, case_states, matrix_code, add_texts):
        _res = PlanResult(plan_id, f'TestPlan_{plan_id}')
        if add_texts:
            _matrix_code = '' if len(matrix_code) == 0 else f'_{matrix_code}'
            _res[ATTR_SUMMARY] = f'TestPlan_{plan_id}{_matrix_code}_summary'
            _res[ATTR_NOTES] = f'TestPlan_{plan_id}{_matrix_code}_notes'
        _case_id = base_case_id
        for i in range(0, case_states[0]):
            _res.add_case_result(TestCaseResult.case_result(plan_id, _case_id, RESULT_STATUS_PASSED,
                                                            matrix_code, False))
            _case_id += 1
        for i in range(0, case_states[1]):
            _res.add_case_result(TestCaseResult.case_result(plan_id, _case_id, RESULT_STATUS_FAILED,
                                                            matrix_code, False))
            _case_id += 1
        for i in range(0, case_states[2]):
            _res.add_case_result(TestCaseResult.case_result(plan_id, _case_id, RESULT_STATUS_ERROR,
                                                            matrix_code, False))
            _case_id += 1
        return _res

    def verify_merge(self, overall_result, specific_result):
        self.assertEqual(specific_result.get_attr_value(ATTR_STOP_DATE), overall_result.get_attr_value(ATTR_STOP_DATE))
        _overall_plan_results = overall_result.plan_results()
        _specific_plan_results = specific_result.plan_results()
        self.assertEqual(len(_specific_plan_results), len(_overall_plan_results))
        for i in range(0, len(_overall_plan_results)):
            self.assertEqual(_specific_plan_results[i][ATTR_SUMMARY],
                             _overall_plan_results[i][ATTR_SUMMARY].split(os.linesep)[-1])
            self.assertEqual(_specific_plan_results[i][ATTR_NOTES],
                             _overall_plan_results[i][ATTR_NOTES].split(os.linesep)[-1])
        _overall_case_results = overall_result.case_results()
        _specific_case_results = specific_result.case_results()
        self.assertEqual(len(_specific_case_results), len(_overall_case_results))

    def verify_append_ignored(self, result, attr_name, attr_value):
        _orig_value = result.get_attr_value(attr_name)
        result.append_attr_value(attr_name, attr_value)
        self.assertEqual(_orig_value, result.get_attr_value(attr_name))


if __name__ == '__main__':
    unittest.main()
