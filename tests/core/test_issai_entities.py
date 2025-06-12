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
Unit tests for core.entities.
"""
import ast
import datetime
import os
import time
import unittest

from issai.core import *
from issai.core.issai_entities import IssaiEntity, IssaiProductEntity, MASTER_DATA_GROUPS
from issai.core.results import CaseResult, PlanResult


# TEST DATA
DEFAULT_CASE_ID = 23
DEFAULT_CASE_SUMMARY = 'TestCase23'
DEFAULT_PLAN_ID = 18
DEFAULT_PRODUCT = 'SimpleIssai'
DEFAULT_PRODUCT_ID = 8


T_BUILDS = [
  {'id': 13, 'name': 'unspecified', 'version': 12, 'is_active': True}
]
T_CASE_STATUSES = [
  {'id': 2, 'name': 'CONFIRMED', 'description': '', 'is_confirmed': True},
]
T_CATEGORIES = [
  {'id': 19, 'name': '--default--', 'product': 8, 'description': ''},
  {'id': 20, 'name': 'manual', 'product': 8, 'description': 'Executions and result managed by user'},
  {'id': 21, 'name': 'managed', 'product': 8, 'description': 'Executions and result managed by script'},
]
T_CLASSIFICATIONS = [
  {'id': 1, 'name': 'Application'},
]
T_COMPONENTS = [
  {'id': 9, 'name': 'Configuration', 'product': 8, 'initial_owner': 5, 'initial_qa_contact': 4,
   'description': 'Configuration handling', 'cases': 84},
]
T_EXECUTION_STATUSES = [
  {'id': 1, 'name': 'IDLE', 'weight': 0, 'icon': 'fa fa-question-circle-o', 'color': '#72767b'},
  {'id': 4, 'name': 'PASSED', 'weight': 20, 'icon': 'fa fa-check-circle-o', 'color': '#92d400'},
]
T_PLAN_TYPES = [
  {'id': 1, 'name': "Unit", 'description': ""},
  {'id': 5, 'name': "Acceptance", 'description': ""},
]
T_PRIORITIES = [
  {'id': 2, 'value': "high", 'is_active': True},
]
T_USERS = [
  {'id': 4, 'email': "tester@issai.local", 'first_name': "Manual", 'is_active': True, 'is_staff': True,
   'is_superuser': False, 'last_name': "Tester", 'username': "tester"},
  {'id': 5, 'email': "tmadmin@issai.local", 'first_name': "Master", 'is_active': True, 'is_staff': True,
   'is_superuser': True, 'last_name': "OfDesaster", 'username': "tmadmin"},
]
T_VERSIONS = [
  {'id': 12, 'value': "unspecified", 'product': 8},
]

DEFAULT_MASTER_DATA_COUNT = (len(T_BUILDS) + len(T_CASE_STATUSES) + len(T_CATEGORIES) + len(T_CLASSIFICATIONS) +
                             len(T_COMPONENTS) + len(T_EXECUTION_STATUSES) + len(T_PLAN_TYPES) + len(T_PRIORITIES) +
                             len(T_USERS) + len(T_VERSIONS))

T_PRODUCT = {'id': 8, 'name': "SimpleIssai", 'classification': 1,
             'description': "Product for test of issai without versions and builds."}
T_TEST_CASE = {'id': 84, 'is_automated': True, 'arguments': "tc112",
               'extra_link': "https://server.issai.local/company_rules.html",
               'summary': "SimpleIssai-ExclusiveCaseWithoutExecutions010",
               'requirement': "RQ-112", 'notes': "First test case",
               'text': "Test case used by exactly one test plan.\nNo test executions exist.",
               'case_status': 2, 'category': 21, 'priority': 2, 'author': 5, 'default_tester': 5, 'reviewer': 4,
               'expected_duration': 0.0,
               'attachments': ["https://server.issai.local/uploads/attachments/testcases_testcase/84/issai.toml"],
               'cc_notifications': [], 'comments': [], 'components': [9], 'properties': [{'test': "true"}],
               'tags': ["oslinux"], 'executions': []}
T_TEST_PLAN = {'id': 18, 'is_active': True, 'name': 'DummyPlan', 'text': 'Top level test plan',
               'product_version': 12, 'product': 8, 'author': 4, 'type': 5, 'attachments': [],
               'tags': [], 'cases': [84], 'runs': []}
T_NEW_PRODUCT = {'id': 23, 'name': "SimpleIssai", 'classification': 1,
                 'description': "Product for test of issai without versions and builds."}
IMP_FILE_DEFAULT = '''{
"product-classifications": {1: {"id": 1, "name": "Application"}},
"product": {"id": 5, "name": "IssaiTest", "classification": 1},
"product-versions": {6: {"id": 6, "value": "unspecified", "product": 5},
                     7: {"id": 7, "value": "v0.7", "product": 5}},
"product-builds": {10: {"id": 10, "name": "unspecified", "version": 6},
                   11: {"id": 11, "name": "unspecified", "version": 7}}
}'''


class TestIssaiEntity(unittest.TestCase):
    """
    Tests for base class IssaiEntity.
    """
    def test_constructor(self):
        """
        Test object state after construction.
        """
        _entity = IssaiEntity(ENTITY_TYPE_PRODUCT, DEFAULT_PRODUCT_ID, DEFAULT_PRODUCT)
        self.assertEqual(ENTITY_TYPE_PRODUCT, _entity.entity_type())
        self.assertEqual(DEFAULT_PRODUCT_ID, _entity.entity_id())
        self.assertEqual(DEFAULT_PRODUCT, _entity.entity_name())
        self.assertEqual(0, len(_entity[ATTR_PRODUCT]))
        self.assertEqual(0, len(_entity.attachments()))
        self.assertEqual(0, _entity.attachment_count())
        self.assertEqual(0, _entity.object_count())
        self.assertEqual(0, _entity.master_data_object_count())
        for _group in MASTER_DATA_GROUPS:
            self.assertEqual(0, len(_entity.group_objects(_group)))
            self.assertEqual(0, _entity.group_object_count(_group))
            self.assertEqual(0, _entity.group_attachment_count(_group))

    def test_base_data_filled(self):
        """
        Test object state with all base class attributes set to a custom value.
        """
        _entity = TestIssaiEntity.default_entity(ENTITY_TYPE_PRODUCT)
        self.verify_default_entity(_entity)

    @staticmethod
    def default_entity(entity_type):
        if entity_type == ENTITY_TYPE_PRODUCT:
            _entity = IssaiEntity(ENTITY_TYPE_PRODUCT, DEFAULT_PRODUCT_ID, DEFAULT_PRODUCT)
        else:
            return None
        _entity.set_product(T_PRODUCT)
        _entity.add_objects(ATTR_PRODUCT_BUILDS, T_BUILDS)
        _entity.add_objects(ATTR_CASE_STATUSES, T_CASE_STATUSES)
        _entity.add_objects(ATTR_CASE_CATEGORIES, T_CATEGORIES)
        _entity.add_objects(ATTR_PRODUCT_CLASSIFICATIONS, T_CLASSIFICATIONS)
        _entity.add_objects(ATTR_CASE_COMPONENTS, T_COMPONENTS)
        _entity.add_objects(ATTR_EXECUTION_STATUSES, T_EXECUTION_STATUSES)
        _entity.add_objects(ATTR_PLAN_TYPES, T_PLAN_TYPES)
        _entity.add_objects(ATTR_CASE_PRIORITIES, T_PRIORITIES)
        _entity.add_objects(ATTR_TCMS_USERS, T_USERS)
        _entity.add_objects(ATTR_PRODUCT_VERSIONS, T_VERSIONS)
        return _entity

    def verify_group_objects(self, expected_values, entity, group):
        _objects = entity.group_objects(group)
        self.assertEqual(len(expected_values), len(_objects))
        self.assertEqual(len(expected_values), entity.group_object_count(group))
        _sorted_objects = sorted(_objects, key=lambda obj: obj[ATTR_ID])
        _sorted_expected_values = sorted(expected_values, key=lambda obj: obj[ATTR_ID])
        self.assertEqual(_sorted_expected_values, _sorted_objects)

    def verify_default_entity(self, entity):
        self.assertIsNotNone(entity)
        self.assertEqual(T_PRODUCT, entity[ATTR_PRODUCT])
        self.verify_group_objects(T_BUILDS, entity, ATTR_PRODUCT_BUILDS)
        self.verify_group_objects(T_CASE_STATUSES, entity, ATTR_CASE_STATUSES)
        self.verify_group_objects(T_CATEGORIES, entity, ATTR_CASE_CATEGORIES)
        self.verify_group_objects(T_CLASSIFICATIONS, entity, ATTR_PRODUCT_CLASSIFICATIONS)
        self.verify_group_objects(T_COMPONENTS, entity, ATTR_CASE_COMPONENTS)
        self.verify_group_objects(T_EXECUTION_STATUSES, entity, ATTR_EXECUTION_STATUSES)
        self.verify_group_objects(T_PLAN_TYPES, entity, ATTR_PLAN_TYPES)
        self.verify_group_objects(T_PRIORITIES, entity, ATTR_CASE_PRIORITIES)
        self.verify_group_objects(T_USERS, entity, ATTR_TCMS_USERS)
        self.verify_group_objects(T_VERSIONS, entity, ATTR_PRODUCT_VERSIONS)
        self.assertEqual(DEFAULT_MASTER_DATA_COUNT, entity.master_data_object_count())
        self.assertEqual(DEFAULT_MASTER_DATA_COUNT + 1, entity.object_count())
        self.assertEqual(0, entity.attachment_count())
        self.assertEqual({}, entity.attachments())


class TestIssaiProductEntity(unittest.TestCase):
    """
    Tests for class IssaiProductEntity.
    """
    def test_constructor(self):
        """
        Test object state after construction.
        """
        _entity = IssaiProductEntity(DEFAULT_PRODUCT_ID, DEFAULT_PRODUCT)

    def test_toml_conversion(self):
        """
        Test object state with all attributes set to a custom value.
        """
        _entity = TestIssaiProductEntity.default_product()
        _toml_data = _entity.to_toml()
        print(_toml_data)
        _clone = IssaiEntity.from_toml(_toml_data)
        self.assertEqual(_entity, _clone)

    @staticmethod
    def default_product():
        s = ast.literal_eval(IMP_FILE_DEFAULT)
        print(s)
        _entity = IssaiProductEntity(DEFAULT_PRODUCT_ID, DEFAULT_PRODUCT)
        _entity.set_product(T_PRODUCT)
        _entity.add_objects(ATTR_PRODUCT_BUILDS, T_BUILDS)
        _entity.add_objects(ATTR_CASE_STATUSES, T_CASE_STATUSES)
        _entity.add_objects(ATTR_CASE_CATEGORIES, T_CATEGORIES)
        _entity.add_objects(ATTR_PRODUCT_CLASSIFICATIONS, T_CLASSIFICATIONS)
        _entity.add_objects(ATTR_CASE_COMPONENTS, T_COMPONENTS)
        _entity.add_objects(ATTR_EXECUTION_STATUSES, T_EXECUTION_STATUSES)
        _entity.add_objects(ATTR_PLAN_TYPES, T_PLAN_TYPES)
        _entity.add_objects(ATTR_CASE_PRIORITIES, T_PRIORITIES)
        _entity.add_objects(ATTR_TCMS_USERS, T_USERS)
        _entity.add_objects(ATTR_PRODUCT_VERSIONS, T_VERSIONS)
        _entity.add_objects(ATTR_TEST_CASES, [T_TEST_CASE])
        _entity.add_objects(ATTR_TEST_PLANS, [T_TEST_PLAN])
        return _entity


"""
    def test_case(self):
        #Test TestCase.
        _tc = self._custom_case(84)
        _toml_tc = _tc.as_toml_entity()
        print(_tc)
        _clone = Entity.from_toml_entity(_toml_tc)
        print(_clone)

    def test_plain_test_plan_result(self):
        #Test plain TestPlanResult.
        # Empty TestplanResult with default values
        _default_tpr = PlanResultEntity(1, 'MyPlan')
        _toml_tpr = _default_tpr.to_toml()
        _plain_toml_tpr = _toml_tpr[ATTR_TEST_PLAN_RESULTS][0]
        _clone = PlanResultEntity.from_toml(10, 'MyPlan', _plain_toml_tpr)
        self._verify_test_plan_results(_default_tpr, _clone)
        # TestPlanResult without child plans
        _single_tpr = TestEntities._custom_plan_result(10, 1, 3)
        _toml_tpr = _single_tpr.to_toml()
        _plain_toml_tpr = _toml_tpr[ATTR_TEST_PLAN_RESULTS][0]
        _clone = PlanResultEntity.from_toml(_plain_toml_tpr)
        self._verify_test_plan_results(_single_tpr, _clone)
        # nested TestPlanResult
        _family_tpr = TestEntities._custom_plan_result(10, 1, 3)
        _grand_child_tpr = TestEntities._custom_plan_result(40, 1, 3)
        _daughter_tpr = TestEntities._custom_plan_result(30, 1, 3)
        _daughter_tpr.add_plan_result(_grand_child_tpr)
        _son_tpr = TestEntities._custom_plan_result(20, 1, 3)
        _family_tpr.add_plan_result(_daughter_tpr)
        _family_tpr.add_plan_result(_son_tpr)
        _toml_tpr = _family_tpr.to_toml()
        _plain_toml_tpr = _toml_tpr[ATTR_TEST_PLAN_RESULTS][0]
        _clone = PlanResultEntity.from_toml(_plain_toml_tpr)
        self._verify_test_plan_results(_family_tpr, _clone)

    @staticmethod
    def _custom_case(case_id):
        _tc = TestCaseEntity.from_tcms(case_id, T_PRODUCT)
        _tc.add_tcms_cases([T_TEST_CASE])
        _tc.add_master_data(ATTR_PRODUCT_BUILDS, T_BUILDS)
        _tc.add_master_data(ATTR_CASE_STATUSES, T_CASE_STATUSES)
        _tc.add_master_data(ATTR_CASE_CATEGORIES, T_CATEGORIES)
        _tc.add_master_data(ATTR_PRODUCT_CLASSIFICATIONS, T_CLASSIFICATIONS)
        _tc.add_master_data(ATTR_CASE_COMPONENTS, T_COMPONENTS)
        _tc.add_master_data(ATTR_EXECUTION_STATUSES, T_EXECUTION_STATUSES)
        _tc.add_master_data(ATTR_PLAN_TYPES, T_PLAN_TYPES)
        _tc.add_master_data(ATTR_CASE_PRIORITIES, T_PRIORITIES)
        _tc.add_master_data(ATTR_TCMS_USERS, T_USERS)
        _tc.add_master_data(ATTR_PRODUCT_VERSIONS, T_VERSIONS)
        return _tc

    @staticmethod
    def _custom_case_result(execution_id, case_id, summary):
        _tcr = CaseResult(execution_id, case_id, summary)
        _tcr.mark_start()
        _tcr.mark_end()
        _tcr.add_output_file('/tmp/tc.log')
        _tcr.set_attr_value(ATTR_STATUS, 2)
        _tcr.set_attr_value(ATTR_TESTER_NAME, 'tester')
        _tcr.set_attr_value(ATTR_COMMENT, 'bla')
        return _tcr

    @staticmethod
    def _custom_plan_result(run_id, plan_id, plan_name, f_count=1, tc_count=1):
        _tpr = PlanResult(plan_id, plan_name)
        _tpr.mark_start()
        _tpr.mark_end()
        for _i in range(0, f_count):
            _tpr.add_output_file('/tmp/tp%i.log' % (_i+1))
        for _i in range(0, tc_count):
            _execution_id = run_id + _i + 1
            _case_id = plan_id + _i + 1
            _case_summary = 'TestCase_{_case_id}'
            _tpr.add_case_result(TestEntities._custom_case_result(_execution_id, _case_id, _case_summary))
        return _tpr

    def _verify_master_data(self, md1, md2):
        self.assertIsInstance(md2, MasterData)
        self.assertEqual(md1.objects_of_type(ATTR_PRODUCT_BUILDS), md2.objects_of_type(ATTR_PRODUCT_BUILDS))
        self.assertEqual(md1.objects_of_type(ATTR_CASE_STATUSES), md2.objects_of_type(ATTR_CASE_STATUSES))
        self.assertEqual(md1.objects_of_type(ATTR_CASE_CATEGORIES), md2.objects_of_type(ATTR_CASE_CATEGORIES))
        self.assertEqual(md1.objects_of_type(ATTR_PRODUCT_CLASSIFICATIONS),
                         md2.objects_of_type(ATTR_PRODUCT_CLASSIFICATIONS))
        self.assertEqual(md1.objects_of_type(ATTR_EXECUTION_STATUSES),
                         md2.objects_of_type(ATTR_EXECUTION_STATUSES))
        self.assertEqual(md1.objects_of_type(ATTR_PLAN_TYPES), md2.objects_of_type(ATTR_PLAN_TYPES))
        self.assertEqual(md1.objects_of_type(ATTR_CASE_PRIORITIES), md2.objects_of_type(ATTR_CASE_PRIORITIES))
        self.assertEqual(md1.objects_of_type(ATTR_TCMS_USERS), md2.objects_of_type(ATTR_TCMS_USERS))
        self.assertEqual(md1.objects_of_type(ATTR_PRODUCT_VERSIONS), md2.objects_of_type(ATTR_PRODUCT_VERSIONS))
        _components1 = md1.objects_of_type(ATTR_CASE_COMPONENTS)
        _components2 = md2.objects_of_type(ATTR_CASE_COMPONENTS)
        for _c in _components1:
            for _k, _v in _c.items():
                if _k == ATTR_CASES:
                    _c[_k] = list(_v)
        self.assertEqual(_components1, _components2)

    def _verify_test_case_results(self, res1, res2):
        self.assertIsInstance(res2, CaseResult)
        self.assertEqual(res1.entity_type_toml_name(), res2.entity_type_toml_name())
        self.assertEqual(res1.attribute_value(ATTR_EXECUTION_ID), res2.attribute_value(ATTR_EXECUTION_ID))
        self.assertEqual(res1.attribute_value(ATTR_START_DATE), res2.attribute_value(ATTR_START_DATE))
        self.assertEqual(res1.attribute_value(ATTR_STOP_DATE), res2.attribute_value(ATTR_STOP_DATE))
        self.assertEqual(len(res1.attribute_value(ATTR_OUTPUT_FILES)), len(res2.attribute_value(ATTR_OUTPUT_FILES)))
        self.assertEqual(res1.attribute_value(ATTR_STATUS), res2.attribute_value(ATTR_STATUS))
        self.assertEqual(res1.attribute_value(ATTR_TESTER_NAME), res2.attribute_value(ATTR_TESTER_NAME))
        self.assertEqual(res1.attribute_value(ATTR_COMMENT), res2.attribute_value(ATTR_COMMENT))

    def _verify_test_plan_results(self, res1, res2):
        self.assertIsInstance(res2, PlanResultEntity)
        self.assertEqual(res1.entity_type_toml_name(), res2.entity_type_toml_name())
        self.assertEqual(res1.attribute_value(ATTR_RUN_ID), res2.attribute_value(ATTR_RUN_ID))
        self.assertEqual(res1.attribute_value(ATTR_START_DATE), res2.attribute_value(ATTR_START_DATE))
        self.assertEqual(res1.attribute_value(ATTR_STOP_DATE), res2.attribute_value(ATTR_STOP_DATE))
        self.assertEqual(len(res1.attribute_value(ATTR_OUTPUT_FILES)), len(res2.attribute_value(ATTR_OUTPUT_FILES)))
        res1_case_results = res1.attribute_value(ATTR_CASE_RESULTS)
        res2_case_results = res2.attribute_value(ATTR_CASE_RESULTS)
        self.assertEqual(len(res1_case_results), len(res1_case_results))
        for _i in range(0, len(res1_case_results)):
            self._verify_test_case_results(res1_case_results[_i], res2_case_results[_i])
        res1_plan_results = res1.attribute_value(ATTR_CHILD_PLAN_RESULTS)
        res2_plan_results = res2.attribute_value(ATTR_CHILD_PLAN_RESULTS)
        self.assertEqual(len(res1_plan_results), len(res2_plan_results))
        for _i in range(0, len(res1_plan_results)):
            self._verify_test_plan_results(res1_plan_results[_i], res2_plan_results[_i])
"""

if __name__ == '__main__':
    unittest.main()
