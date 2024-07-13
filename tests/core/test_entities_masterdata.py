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
Unit tests for class MasterData in module core.entities.
"""
import unittest

from issai.core import *
from issai.core.entities import MasterData, CLASS_REFERENCES, MASTER_DATA_TYPES
from issai.core.issai_exception import IssaiException


# TEST DATA
DEFAULT_CASE_ID = 23
DEFAULT_CASE_SUMMARY = 'TestCase23'
DEFAULT_PLAN_ID = 18


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
   'description': 'Configuration handling', 'cases': [84]},
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
T_NEW_PRODUCT = {'id': 22, 'name': "SimpleIssai", 'classification': 1,
                 'description': "Product for test of issai without versions and builds."}
T_DB_USER_TMADMIN = {'id': 4, 'email': "tmadmin@issai.local", 'first_name': "Master", 'is_active': True,
                     'is_staff': True, 'is_superuser': True, 'last_name': "OfDesaster", 'username': "tmadmin"}


class TestEntitiesMasterData(unittest.TestCase):
    def test_add_object(self):
        _master_data = MasterData()
        # TODO

    def test_object_count(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        self.assertEqual(15, _master_data.object_count())

    def test_object(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        self.assertIsNotNone(_master_data.object(ATTR_CASE_CATEGORIES, 20))
        self.assertIsNone(_master_data.object(ATTR_CASE_CATEGORIES, 99))
        self.assertRaises(IssaiException, _master_data.object, 'XYZ', 0)

    def test_objects_of_type(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        self.assertEqual(2, len(_master_data.objects_of_type(ATTR_TCMS_USERS)))
        self.assertRaises(IssaiException, _master_data.objects_of_type, 'XYZ')

    def test_objects_of_class(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        self.assertEqual(1, len(_master_data.objects_of_class(TCMS_CLASS_ID_VERSION)))
        self.assertRaises(IssaiException, _master_data.objects_of_class, 999)

    def test_users(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        _default_user_ids = sorted([u[ATTR_ID] for u in T_USERS])
        self.assertEqual(_default_user_ids, sorted(_master_data.user_ids()))
        _default_user_names = sorted([u[ATTR_USERNAME] for u in T_USERS])
        self.assertEqual(_default_user_names, sorted(_master_data.user_names()))
        _ref_users = set()
        for _comp in T_COMPONENTS:
            _ref_users.add(_comp[ATTR_INITIAL_OWNER])
            _ref_users.add(_comp[ATTR_INITIAL_QA_CONTACT])
        self.assertEqual(sorted(_ref_users), sorted(_master_data.referenced_user_ids()))

    def test_execution_status_id_of(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        for _status in T_EXECUTION_STATUSES:
            self.assertEqual(_status[ATTR_ID], _master_data.execution_status_id_of(_status[ATTR_NAME]))
        self.assertRaises(IssaiException, _master_data.execution_status_id_of, 'XYZ')

    def test_replace_object(self):
        _default_master_data = TestEntitiesMasterData._default_master_data()
        _master_data = TestEntitiesMasterData._default_master_data()
        _master_data.replace_object(TCMS_CLASS_ID_USER, 5, T_DB_USER_TMADMIN)
        self._verify_replace(_default_master_data, _master_data, TCMS_CLASS_ID_USER, 5, T_DB_USER_TMADMIN[ATTR_ID])
        # TODO

    def test_toml_conversion(self):
        _master_data = TestEntitiesMasterData._default_master_data()
        _toml_data = _master_data.to_toml()
        _clone = MasterData.from_toml(_toml_data)
        self._verify_master_data(_master_data, _clone)

    @staticmethod
    def _default_master_data():
        """
        :returns: default master data
        :rtype: MasterData
        """
        _master_data = MasterData()
        _master_data.add_object(ATTR_PRODUCT_BUILDS, T_BUILDS)
        _master_data.add_object(ATTR_CASE_STATUSES, T_CASE_STATUSES)
        _master_data.add_object(ATTR_CASE_CATEGORIES, T_CATEGORIES)
        _master_data.add_object(ATTR_PRODUCT_CLASSIFICATIONS, T_CLASSIFICATIONS)
        _master_data.add_object(ATTR_CASE_COMPONENTS, T_COMPONENTS)
        _master_data.add_object(ATTR_EXECUTION_STATUSES, T_EXECUTION_STATUSES)
        _master_data.add_object(ATTR_PLAN_TYPES, T_PLAN_TYPES)
        _master_data.add_object(ATTR_CASE_PRIORITIES, T_PRIORITIES)
        _master_data.add_object(ATTR_TCMS_USERS, T_USERS)
        _master_data.add_object(ATTR_PRODUCT_VERSIONS, T_VERSIONS)
        return _master_data

    def _verify_master_data(self, md1, md2):
        """
        Makes sure specified master data objects are equal.
        :param MasterData md1: expected master data
        :param MasterData md2: actual master data
        """
        self.assertIsInstance(md2, MasterData)
        for _data_type in MASTER_DATA_TYPES:
            if _data_type == ATTR_CASE_COMPONENTS:
                _components1 = md1.objects_of_type(ATTR_CASE_COMPONENTS).copy()
                for _c in _components1:
                    for _k, _v in _c.items():
                        if _k == ATTR_CASES:
                            _c[_k] = list(_v)
                self.assertEqual(_components1, md2.objects_of_type(ATTR_CASE_COMPONENTS))
            else:
                self.assertEqual(md1.objects_of_type(_data_type), md2.objects_of_type(_data_type))

    def _verify_replace(self, orig_md, md, class_id, object_id, new_object_id):
        """
        Makes sure a replace operation on master data was successful.
        :param MasterData orig_md: master data before replace operation
        :param MasterData md: actual master data after replace operation
        :param int class_id: TCMS class ID of object to replace
        :param int object_id: TCMS ID of object to replace
        :param int new_object_id: TCMS ID of new object
        """
        if class_id in MASTER_DATA_CLASS_DATA_TYPES:
            # master class object itself must have been replaced
            _affected_objects = md.objects_of_class(class_id)
            self.assertIsNone(_affected_objects.get(object_id))
            self.assertIsNotNone(_affected_objects.get(new_object_id))
        # all references must have been replaced
        _change_classes = CLASS_REFERENCES.get(class_id)
        if _change_classes is None:
            # changed object is not referenced
            return
        for _ref_class_id, _ref_attrs in _change_classes.items():
            if _ref_class_id not in MASTER_DATA_CLASS_DATA_TYPES:
                continue
            _ref_data_type = MASTER_DATA_CLASS_DATA_TYPES[_ref_class_id]
            for _orig_md_object in orig_md.objects_of_class(_ref_class_id).values():
                for _attr in _ref_attrs:
                    if _orig_md_object[_attr] == object_id:
                        _ref_object = md.object(_ref_data_type, _orig_md_object[ATTR_ID])
                        self.assertEqual(new_object_id, _ref_object[_attr])


if __name__ == '__main__':
    unittest.main()
