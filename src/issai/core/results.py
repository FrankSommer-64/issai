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
Issai core result classes.
Used by runner only, the classes don't have a corresponding in TCMS.
"""

from datetime import datetime

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.util import python_value


class Result(dict):
    """
    Base class for test results used within test runner.
    """
    def __init__(self, type_id, plan_id):
        """
        Constructor.
        :param int type_id: the result object type (test case result or test plan result)
        :param int plan_id: the TCMS test plan ID
        """
        super().__init__()
        self.__result_type = type_id
        self[ATTR_PLAN] = plan_id
        self[ATTR_START_DATE] = None
        self[ATTR_STOP_DATE] = None
        self[ATTR_OUTPUT_FILES] = []

    def result_type(self):
        """
        :returns: result object type
        :rtype: int
        """
        return self.__result_type

    def get_attr_value(self, attribute_name):
        """
        :param str attribute_name: the attribute name
        :returns: value of attribute with specified name
        :rtype: Any
        """
        if attribute_name not in _CORE_RESULT_ATTRIBUTES[self.__result_type]:
            raise IssaiException(E_TOML_ENTITY_ATTR_NAME_INVALID, attribute_name, entity_type_name(self.__result_type))
        return python_value(self.get(attribute_name))

    def set_attr_value(self, attribute_name, attribute_value):
        """
        Sets value for specified attribute name.
        :param str attribute_name: the attribute name
        :param Any attribute_value: the attribute value
        """
        _verify_attr_write(self.__result_type, attribute_name, attribute_value)
        self[attribute_name] = attribute_value

    def append_attr_value(self, attribute_name, attribute_value):
        """
        Appends value for specified attribute name.
        :param str attribute_name: the attribute name
        :param Any attribute_value: the attribute value
        """
        _verify_attr_write(self.__result_type, attribute_name, attribute_value, True)
        _current_value = self.get(attribute_name)
        if _current_value is None or len(_current_value) == 0:
            self[attribute_name] = attribute_value
        else:
            self[attribute_name] = f'{_current_value}{os.linesep}{attribute_value}'

    def mark_start(self):
        """
        Marks the timestamp when the execution of the entity was started.
        """
        self[ATTR_START_DATE] = datetime.now()

    def mark_end(self):
        """
        Marks the timestamp when the execution of the entity was finished.
        """
        self[ATTR_STOP_DATE] = datetime.now()

    def add_output_file(self, file_path):
        """
        Adds an output file from test execution.
        :param str file_path: the full path of the output file
        """
        self[ATTR_OUTPUT_FILES].append(file_path)

    def duration(self):
        """
        :returns: test duration in seconds; -1 if either start or end timestamp are not set
        :rtype: int
        """
        if self[ATTR_START_DATE] is None or self[ATTR_STOP_DATE] is None:
            return -1
        _duration = self[ATTR_STOP_DATE] - self[ATTR_START_DATE]
        return _duration.total_seconds()


class CaseResult(Result):
    """
    Test case result used within test runner.
    """
    def __init__(self, plan_id, case_id, case_summary, matrix_code):
        """
        Constructor.
        :param int plan_id: the TCMS test plan ID
        :param int case_id: the TCMS test case ID
        :param str case_summary: the test case summary
        :param str matrix_code: the permuting properties code
        """
        super().__init__(RESULT_TYPE_CASE_RESULT, plan_id)
        self[ATTR_CASE] = case_id
        self[ATTR_CASE_NAME] = case_summary
        self[ATTR_MATRIX_CODE] = matrix_code
        self[ATTR_STATUS] = RESULT_STATUS_PASSED
        self[ATTR_TESTER_NAME] = ''
        self[ATTR_COMMENT] = ''

    def id_str(self):
        """
        :returns: identification based on plan ID and case ID
        :rtype: str
        """
        return f'{self[ATTR_PLAN]}.{self[ATTR_CASE]}'

    def merge_matrix_result(self, case_result):
        """
        Merges the result of a test plan execution for a specific matrix code.
        :param CaseResult case_result: the test case result
        """
        _new_matrix_code = case_result[ATTR_MATRIX_CODE]
        _new_status = case_result[ATTR_STATUS]
        self.append_attr_value(ATTR_COMMENT, localized_message(I_RUN_MATRIX_RESULT, _new_matrix_code, _new_status))
        self.append_attr_value(ATTR_COMMENT, case_result[ATTR_COMMENT])
        if _new_status == RESULT_STATUS_ERROR or (_new_status == RESULT_STATUS_FAILED and
                                                  self[ATTR_STATUS] == RESULT_STATUS_PASSED):
            self[ATTR_STATUS] = _new_status
        self[ATTR_STOP_DATE] = case_result[ATTR_STOP_DATE]


class PlanResult(Result):
    """
    Test plan result used within test runner.
    """

    def __init__(self, plan_id, plan_name):
        """
        Constructor.
        :param int plan_id: the test plan TCMS ID
        :param str plan_name: the test plan name
        """
        super().__init__(RESULT_TYPE_PLAN_RESULT, plan_id)
        self[ATTR_PLAN_NAME] = plan_name
        self[ATTR_NOTES] = ''
        self[ATTR_SUMMARY] = ''
        self[ATTR_CHILD_PLAN_RESULTS] = []
        self[ATTR_CASE_RESULTS] = []

    def add_case_result(self, case_result):
        """
        Adds the result of a test case contained in the test plan.
        :param CaseResult case_result: the test case result
        """
        self[ATTR_CASE_RESULTS].append(case_result)

    def add_plan_result(self, plan_result):
        """
        Adds the result of a child test plan.
        :param PlanResult plan_result: the test plan result
        """
        self[ATTR_CHILD_PLAN_RESULTS].append(plan_result)

    def merge_matrix_result(self, plan_result):
        """
        Merges the result of a test plan execution for a specific matrix code.
        :param PlanResult plan_result: the test plan result
        """
        self[ATTR_STOP_DATE] = plan_result[ATTR_STOP_DATE]
        self.append_attr_value(ATTR_NOTES, plan_result[ATTR_NOTES])
        _overall_case_results = {}
        for _cr in self.case_results():
            _overall_case_results[_cr.id_str()] = _cr
        _new_case_results = {}
        for _cr in plan_result.case_results():
            _new_case_results[_cr.id_str()] = _cr
        for _cr_id, _cr in _new_case_results.items():
            _overall_cr = _overall_case_results.get(_cr_id)
            if _overall_cr is None:
                _cr_status = _cr[ATTR_STATUS]
                _cr_code = _cr[ATTR_MATRIX_CODE]
                _cr.append_attr_value(ATTR_COMMENT, localized_message(I_RUN_MATRIX_RESULT, _cr_code, _cr_status))
                self.add_case_result(_cr)
                continue
            _overall_cr.merge_matrix_result(_cr)

    def case_results(self):
        """
        :returns: test case results of this plan and all descendants
        :rtype: list
        """
        _results = [_cr for _cr in self.get_attr_value(ATTR_CASE_RESULTS)]
        for _child_plan in self.get_attr_value(ATTR_CHILD_PLAN_RESULTS):
            _results.extend(_child_plan.case_results())
        return _results

    def plan_results(self):
        """
        :returns: results of this plan and all descendants
        :rtype: list
        """
        _results = [self]
        for _child_plan in self.get_attr_value(ATTR_CHILD_PLAN_RESULTS):
            _results.extend(_child_plan.plan_results())
        return _results

    def result_status(self):
        """
        Returns test plan execution status. Data type is int since it's used to indicate the task result code.
        :returns: overall execution status for all contained test cases
        :rtype: int
        """
        _overall_status = RESULT_STATUS_ID_PASSED
        for _pr in self.plan_results():
            for _cr in _pr.get_attr_value(ATTR_CASE_RESULTS):
                _case_status = _cr[ATTR_STATUS]
                if _case_status == RESULT_STATUS_ERROR:
                    return RESULT_STATUS_ID_ERROR
                if _case_status == RESULT_STATUS_FAILED:
                    _overall_status = RESULT_STATUS_ID_FAILED
        return _overall_status


def _verify_attr_write(result_type_id, attr_name, attr_value, append_allowed=False):
    """
    Asserts that the specified attribute can be updated with given value.
    :param int result_type_id: the result type ID
    :param str attr_name: the attribute name
    :param attr_value: the attribute value
    :param bool append_allowed: indicates whether attribute allows a value to be appended
    :raises IssaiException: if attribute name is invalid, attribute is immutable or value has wrong type
    """
    _attr_desc = _CORE_RESULT_ATTRIBUTES[result_type_id].get(attr_name)
    if _attr_desc is None:
        raise IssaiException(E_TOML_ENTITY_ATTR_NAME_INVALID, attr_name, entity_type_name(result_type_id))
    if not isinstance(attr_value, _attr_desc[0]):
        raise IssaiException(E_TOML_ENTITY_ATTR_INVALID_TYPE, attr_name, entity_type_name(result_type_id),
                             _attr_desc[0])
    if append_allowed and not isinstance(attr_value, str):
        raise IssaiException(E_TOML_ENTITY_ATTR_INVALID_TYPE, attr_name, entity_type_name(result_type_id),
                             _attr_desc[0])
    if not _attr_desc[1]:
        raise IssaiException(E_TOML_ENTITY_ATTR_IMMUTABLE, entity_type_name(result_type_id), attr_name)


# Descriptors for attributes of core result objects.
# Keys are attribute names, value indicates the data type and whether the attribute is writable by methods
# set_attr_value or append_attr_value.
_CORE_RESULT_ATTRIBUTES = {
    RESULT_TYPE_CASE_RESULT: {ATTR_CASE: (int, False), ATTR_CASE_NAME: (str, False), ATTR_COMMENT: (str, True),
                              ATTR_MATRIX_CODE: (str, False), ATTR_OUTPUT_FILES: (list, False),
                              ATTR_PLAN: (int, False), ATTR_START_DATE: (datetime, False), ATTR_STATUS: (str, True),
                              ATTR_STOP_DATE: (datetime, False), ATTR_TESTER_NAME: (str, True)},
    RESULT_TYPE_PLAN_RESULT: {ATTR_CASE_RESULTS: (list, False), ATTR_CHILD_PLAN_RESULTS: (list, False),
                              ATTR_NOTES: (str, True), ATTR_OUTPUT_FILES: (list, False), ATTR_PLAN: (int, False),
                              ATTR_PLAN_NAME: (str, False), ATTR_START_DATE: (datetime, False),
                              ATTR_STOP_DATE: (datetime, False), ATTR_SUMMARY: (str, True)}
}
