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
Issai entity classes.
The entities model central objects of Issai: products, test plans, test cases, test plan results and test case results.
Products can be exported from and imported to TCMS.
Test plans and test cases are also subject to export/import and can be executed.
Test plan results and test case results can be imported to TCMS.
"""

import copy
import re

from tomlkit import aot, array, dump, inline_table, integer, load, table, TOMLDocument
from tomlkit.items import Table

from issai.core import *
from issai.core.checks import verify_entity_attr_name, verify_master_data_attr, verify_master_data_type
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.util import python_value


class Entity(dict):
    """
    Base class for all types of issai entities.
    """
    def __init__(self, type_id, entity_id, entity_name):
        """
        Constructor.
        :param int type_id: the entity type (product, test-case, test-plan, test-case-result or test-plan-result)
        :param entity_id: ID of entity (for product, test-case and test-plan), ID of test execution
                          (for test-case-result), ID of test run (for test-plan-result)
        :param str entity_name: entity name (for product and test-plan), test case summary
                                (for test-case and test-case-result), test plan name (for test-plan-result)
        """
        super().__init__()
        self[ATTR_ENTITY_TYPE] = type_id
        self[ATTR_ENTITY_ID] = entity_id
        self[ATTR_ENTITY_NAME] = entity_name
        self[ATTR_PRODUCT] = {}
        self[ATTR_MASTER_DATA] = MasterData()

    def holds_entity_with_type(self, type_id):
        """
        Indicates whether this container holds an entity of specified type.
        :param int type_id: the entity type ID
        :returns: True, if contained entity has given type
        :rtype: bool
        """
        return self[ATTR_ENTITY_TYPE] == type_id

    def entity_id(self):
        """
        :returns: the entity's ID
        :rtype: int
        """
        return self[ATTR_ENTITY_ID]

    def entity_name(self):
        """
        :returns: the entity's name
        :rtype: str
        """
        return self[ATTR_ENTITY_NAME]

    def entity_type_id(self):
        """
        :returns: the entity's type ID
        :rtype: int
        """
        return self[ATTR_ENTITY_TYPE]

    def entity_type_toml_name(self):
        """
        :returns: the entity type name used in TOML files
        :rtype: str
        """
        if self[ATTR_ENTITY_TYPE] == ENTITY_TYPE_PRODUCT:
            return ENTITY_TYPE_NAME_PRODUCT
        elif self[ATTR_ENTITY_TYPE] == ENTITY_TYPE_CASE:
            return ENTITY_TYPE_NAME_CASE
        elif self[ATTR_ENTITY_TYPE] == ENTITY_TYPE_PLAN:
            return ENTITY_TYPE_NAME_PLAN
        return ENTITY_TYPE_NAME_PLAN_RESULT

    def attachments(self):
        """
        :returns: all attachment file URLs referenced by this container, as two-staged dict class ID, object ID
        :rtype: dict
        """
        _attachments = {}
        _attachments.update(self._attachments_for_part(TCMS_CLASS_ID_TEST_CASE, ATTR_TEST_CASES, ATTR_ATTACHMENTS))
        _attachments.update(self._attachments_for_part(TCMS_CLASS_ID_TEST_PLAN, ATTR_TEST_PLANS, ATTR_ATTACHMENTS))
        _attachments.update(self._attachments_for_part(TCMS_CLASS_ID_TEST_RUN, ATTR_TEST_RUNS, ATTR_ATTACHMENTS))
        _attachments.update(self._attachments_for_part(TCMS_CLASS_ID_TEST_CASE, ATTR_TEST_CASE_RESULTS,
                                                       ATTR_OUTPUT_FILES))
        _attachments.update(self._attachments_for_part(TCMS_CLASS_ID_TEST_RUN, ATTR_TEST_PLAN_RESULTS,
                                                       ATTR_OUTPUT_FILES))
        return _attachments

    def attachment_count(self):
        """
        :returns: number of attachment file references in this container
        :rtype: int
        """
        _attachment_count = self._attachment_count_for_part(ATTR_TEST_CASES, ATTR_ATTACHMENTS)
        _attachment_count += self._attachment_count_for_part(ATTR_TEST_PLANS, ATTR_ATTACHMENTS)
        _attachment_count += self._attachment_count_for_part(ATTR_TEST_RUNS, ATTR_ATTACHMENTS)
        _attachment_count += self._attachment_count_for_part(ATTR_TEST_CASE_RESULTS, ATTR_OUTPUT_FILES)
        _attachment_count += self._attachment_count_for_part(ATTR_TEST_PLAN_RESULTS, ATTR_OUTPUT_FILES)
        return _attachment_count

    def get_part(self, attr_name, attr_id):
        """
        Returns part with given attribute name and ID.
        :param str attr_name: the name of the attribute holding the desired part
        :param int attr_id: the ID of the desired part; -1 for entity ID
        :returns: data of desired element
        :rtype: dict
        :raises IssaiException: if there is no part that matches specified parameters
        """
        _attr = self.get(attr_name)
        if _attr is None:
            raise IssaiException(E_UNKNOWN_ENTITY_ATTR, self.entity_name(), attr_name)
        if attr_id < 0:
            attr_id = self.entity_id()
        _part_data = _attr.get(attr_id)
        if _part_data is None:
            raise IssaiException(E_UNKNOWN_ENTITY_PART, self.entity_name(), attr_name, attr_id)
        return _part_data

    def object_count(self):
        """
        :returns: number of essential objects in this container
        :rtype: int
        """
        _count = 1 if ATTR_PRODUCT in self else 0
        if ATTR_MASTER_DATA in self:
            _count += self[ATTR_MASTER_DATA].object_count()
        for _attr in (ATTR_TEST_CASES, ATTR_TEST_EXECUTIONS, ATTR_TEST_PLANS, ATTR_TEST_RUNS,
                      ATTR_TEST_CASE_RESULTS, ATTR_TEST_PLAN_RESULTS):
            if _attr in self:
                _count += len(self[_attr])
        return _count

    def attribute_value(self, attribute_name):
        """
        :param str attribute_name: the attribute name
        :returns: value of attribute with specified name
        """
        verify_entity_attr_name(self[ATTR_ENTITY_TYPE], attribute_name)
        return python_value(self[attribute_name])

    def object(self, class_id, object_id):
        """
        Returns the container object with given TCMS class and object ID.
        :param int class_id: the TCMS class ID
        :param int object_id: TCMS object ID
        :returns: the object or None
        :rtype: dict
        """
        if is_master_data_tcms_class(class_id):
            _data_type = master_data_type_for_tcms_class(class_id)
            return self[ATTR_MASTER_DATA].object(_data_type, object_id)
        _data_type = data_type_for_tcms_class(class_id)
        return self[_data_type].get(object_id)

    def add_master_data(self, data_type, value):
        """
        Adds the specified attribute(s) to the entity's master data.
        :param str data_type: the master data type
        :param dict|list value: the attribute value(s)
        """
        self[ATTR_MASTER_DATA].add_object(data_type, value)

    def master_data_object(self, data_type, object_id):
        """
        Returns master data object with specified type and ID.
        :param str data_type: the master data type
        :param int object_id: the object's TCMS ID
        :returns: the object found or None, if no such object exists
        :rtype: dict
        """
        return self[ATTR_MASTER_DATA].object(data_type, object_id)

    def master_data_of_type(self, data_type):
        """
        :param str data_type: the master data type
        :returns: the master data objects
        :rtype: list
        """
        return self[ATTR_MASTER_DATA].objects_of_type(data_type)

    def objects_of_class(self, class_id):
        """
        Returns all objects of specified type.
        :param int class_id: the TCMS class ID
        :returns: the objects; None, if specified class is not applicable
        :rtype: dict
        """
        _data_type = data_type_for_tcms_class(class_id)
        return None if _data_type is None or _data_type not in self else self[_data_type]

    def as_toml_entity(self):
        """
        Converts this entity to TOML format. The TOML entity includes entity type information and referenced master
        data like versions or builds.
        :returns: entity in TOML format
        :rtype: TOMLDocument
        """
        _toml_data = TOMLDocument()
        _toml_data.append(ATTR_ENTITY_TYPE, self.entity_type_toml_name())
        _toml_data.append(ATTR_ENTITY_NAME, self.entity_name())
        _toml_data.append(ATTR_ENTITY_ID, integer(self.entity_id()))
        return _merge_toml(_toml_data, self.to_toml(True))

    def to_toml(self, include_references=False):
        """
        Converts this entity to TOML format.
        :param bool include_references: indicates whether to include references master data like versions or builds
        :returns: entity in TOML format
        :rtype: dict
        """
        # nothing relevant in base class
        return {}

    def to_file(self, file_path):
        """
        Writes TOML data of this entity to file.
        :param str file_path: the full path of the output file
        :raises IssaiException: if the file could not be written
        """
        try:
            _toml_data = self.as_toml_entity()
            with open(file_path, 'w') as _f:
                dump(_toml_data, _f)
        except IssaiException:
            raise
        except Exception as _e:
            raise IssaiException(E_WRITE_FILE_FAILED, file_path, _e)

    @staticmethod
    def from_file(file_path):
        """
        Creates an entity from file.
        :param str file_path: the full path of the file containing the entity's data in TOML format
        :returns: created entity object
        :rtype: Entity
        :raises IssaiException: if the file could not be read
        """
        try:
            with open(file_path, 'r') as _f:
                return Entity.from_toml_entity(load(_f))
        except IssaiException:
            raise
        except Exception as _e:
            raise IssaiException(E_READ_FILE_FAILED, file_path, _e)

    @staticmethod
    def from_toml_entity(toml_data):
        """
        Creates an entity from TOML data.
        :param TOMLDocument toml_data: the entity's data in TOML format
        :returns: created entity object
        :rtype: Entity
        """
        _entity_id = read_toml_value(toml_data, ATTR_ENTITY_ID, int, True)
        _entity_name = read_toml_value(toml_data, ATTR_ENTITY_NAME, str, True)
        _entity_type = read_toml_value(toml_data, ATTR_ENTITY_TYPE, str, True)
        _entity_type_id = Entity.id_of_type_name(_entity_type)
        if _entity_type_id == ENTITY_TYPE_PRODUCT:
            return ProductEntity.from_toml(_entity_id, _entity_name, toml_data)
        elif _entity_type_id == ENTITY_TYPE_CASE:
            return TestCaseEntity.from_toml(_entity_id, _entity_name, toml_data)
        elif _entity_type_id == ENTITY_TYPE_PLAN:
            return TestPlanEntity.from_toml(_entity_id, _entity_name, toml_data)
        else:
            # test plan result
            return PlanResultEntity.from_toml(_entity_id, _entity_name, toml_data)

    @staticmethod
    def id_of_type_name(type_name):
        """
        :param str type_name: the entity type name
        :returns: entity type ID
        :rtype: int
        :raises IssaiException: if the type name is invalid
        """
        if type_name == ENTITY_TYPE_NAME_PRODUCT:
            return ENTITY_TYPE_PRODUCT
        elif type_name == ENTITY_TYPE_NAME_CASE:
            return ENTITY_TYPE_CASE
        elif type_name == ENTITY_TYPE_NAME_PLAN:
            return ENTITY_TYPE_PLAN
        elif type_name == ENTITY_TYPE_NAME_PLAN_RESULT:
            return ENTITY_TYPE_PLAN_RESULT
        raise IssaiException(E_TOML_ENTITY_TYPE_INVALID, type_name)

    def fill_test_objects_data(self, test_object_type):
        _toml_data = aot()
        for _obj in self[test_object_type].values():
            _valid_obj_data = table()
            for _k, _v in _obj.items():
                if _v is None:
                    continue
                if isinstance(_v, list):
                    _make_inline = False
                    for _elem in _v:
                        if isinstance(_elem, dict):
                            _make_inline = True
                            for _elem_k, _elem_v in list(_elem.items()):
                                if _elem_v is None:
                                    del _elem[_elem_k]
                    if _make_inline:
                        _a = array()
                        for _elem in _v:
                            _t = inline_table()
                            _t.update(_elem)
                            _a.append(_t)
                        _valid_obj_data[_k] = _a
                        continue
                _valid_obj_data[_k] = _v
            _toml_data.append(_valid_obj_data)
        return _toml_data

    def _attachments_for_part(self, class_id, part_name, attachment_attr_name):
        """
        Returns all attachment file URLs for a container part.
        :param int class_id: the TCMS class ID
        :param str part_name: the container part name
        :param str attachment_attr_name: the name of the attribute holding attachment file URLs
        :returns: all attachment file URLs referenced by this container part
        :rtype: dict
        """
        _attachments = {}
        _part_objects = self.get(part_name)
        if _part_objects is not None:
            for _object_id, _object in _part_objects.items():
                _object_attachments = _object.get(attachment_attr_name)
                if isinstance(_object_attachments, list):
                    _attachments[_object_id] = _object_attachments
        return {} if len(_attachments) == 0 else {class_id: _attachments}

    def _attachment_count_for_part(self, part_name, attachment_attr_name):
        """
        Returns number of attachment files for a container part.
        :param str part_name: the container part name
        :param str attachment_attr_name: the name of the attribute holding attachment file URLs
        :returns: number of attachment files
        :rtype: int
        """
        if part_name not in self:
            return 0
        _attachment_count = 0
        for _object_id, _object in self[part_name].items():
            _object_attachments = _object.get(attachment_attr_name)
            if isinstance(_object_attachments, list):
                _attachment_count += len(_object_attachments)
        return _attachment_count


class SpecificationEntity(Entity):
    """
    Base class for test specification entities (products, test plans and test cases).
    """
    def __init__(self, type_id, entity_id, entity_name):
        """
        Constructor.
        :param int type_id: the specification entity type (product, test plan or test case)
        :param int entity_id: the TCMS entity ID
        :param str entity_name: the specification entity name
        """
        super().__init__(type_id, entity_id, entity_name)
        self[ATTR_ENVIRONMENTS] = {}
        self[ATTR_TEST_PLANS] = {}
        self[ATTR_TEST_RUNS] = {}
        self[ATTR_TEST_CASES] = {}
        self[ATTR_TEST_EXECUTIONS] = {}

    def get_case_properties(self, case_id, property_patterns):
        """
        Returns properties of test case with given ID that match one of the patterns specified
        :param int case_id: the test case ID; -1 for entity ID
        :param set property_patterns: the tag name
        :returns: test case properties matching one of specified patterns
        :rtype: dict
        :raises IssaiException: if there is no test case with specified ID
        """
        _case_data = self.get_part(ATTR_TEST_CASES, case_id)
        _properties = _case_data.get(ATTR_PROPERTIES)
        if _properties is None:
            return {}
        return _matching_properties(_case_data.get(ATTR_PROPERTIES), property_patterns)

    def attachments(self):
        """
        Returns all attachment file URLs referenced by this entity. Returned is a dictionary with TCMS class ID as
        top level key, followed by sub-key entity ID, then list of file names.
        :returns: all attachment file URLs referenced by this entity
        :rtype: dict
        """
        _attachments = super().attachments()
        for _a in self[ATTR_TEST_CASES].values():
            _case_attachments = _a[ATTR_ATTACHMENTS]
            if len(_case_attachments) > 0:
                _class_dict = _attachments.get(TCMS_CLASS_ID_TEST_CASE)
                if _class_dict is None:
                    _attachments[TCMS_CLASS_ID_TEST_CASE] = {}
                    _attachments[TCMS_CLASS_ID_TEST_CASE][_a[ATTR_ID]] = _case_attachments
                else:
                    _class_dict[_a[ATTR_ID]] = _case_attachments
        for _a in self[ATTR_TEST_PLANS].values():
            _plan_attachments = _a[ATTR_ATTACHMENTS]
            if len(_plan_attachments) > 0:
                _class_dict = _attachments.get(TCMS_CLASS_ID_TEST_PLAN)
                if _class_dict is None:
                    _attachments[TCMS_CLASS_ID_TEST_PLAN] = {}
                    _attachments[TCMS_CLASS_ID_TEST_PLAN][_a[ATTR_ID]] = _plan_attachments
                else:
                    _class_dict[_a[ATTR_ID]] = _plan_attachments
        return _attachments

    def referenced_build_ids(self):
        """
        :returns: TCMS ID's of all builds used by test runs and executions
        :rtype: list
        """
        _build_ids = set()
        for _run in self[ATTR_TEST_RUNS].values():
            _build_ids.add(_run[ATTR_BUILD])
        for _execution in self[ATTR_TEST_EXECUTIONS].values():
            _build_ids.add(_execution[ATTR_BUILD])
        return list(_build_ids)

    def referenced_case_status_ids(self):
        """
        :returns: TCMS ID's of all case statuses used by test cases
        :rtype: list
        """
        _status_ids = set()
        for _case in self[ATTR_TEST_CASES].values():
            _status_ids.add(_case[ATTR_CASE_STATUS])
        return list(_status_ids)

    def referenced_category_ids(self):
        """
        :returns: TCMS ID's of all categories used by test cases
        :rtype: list
        """
        _category_ids = set()
        for _case in self[ATTR_TEST_CASES].values():
            _category_ids.add(_case[ATTR_CATEGORY])
        return list(_category_ids)

    def referenced_component_ids(self):
        """
        :returns: TCMS ID's of all components used by test cases
        :rtype: list
        """
        _component_ids = set()
        for _case in self[ATTR_TEST_CASES].values():
            for _c in _case[ATTR_COMPONENTS]:
                _component_ids.add(_c)
        return list(_component_ids)

    def referenced_execution_status_ids(self):
        """
        :returns: TCMS ID's of all execution statuses used by test executions
        :rtype: list
        """
        _status_ids = set()
        for _execution in self[ATTR_TEST_EXECUTIONS].values():
            _status_ids.add(_execution[ATTR_STATUS])
        return list(_status_ids)

    def referenced_plan_type_ids(self):
        """
        :returns: TCMS ID's of all plan types used by test plans
        :rtype: list
        """
        _type_ids = set()
        for _plan in self[ATTR_TEST_PLANS].values():
            _type_ids.add(_plan[ATTR_TYPE])
        return list(_type_ids)

    def referenced_priority_ids(self):
        """
        :returns: TCMS ID's of all priorities used by test cases
        :rtype: list
        """
        _priority_ids = set()
        for _case in self[ATTR_TEST_CASES].values():
            _priority_ids.add(_case[ATTR_PRIORITY])
        return list(_priority_ids)

    def referenced_user_ids(self):
        """
        Make sure referenced components are already stored in master data prior to calling this method.
        :returns: TCMS ID's of all users referenced by this entity
        :rtype: list
        """
        _user_ids = set(self[ATTR_MASTER_DATA].referenced_user_ids())
        for _case in self[ATTR_TEST_CASES].values():
            _add_referenced_ids(_user_ids, _case, [ATTR_AUTHOR, ATTR_DEFAULT_TESTER, ATTR_REVIEWER])
            _case_hist = _case.get(ATTR_HISTORY)
            if _case_hist is not None:
                for _hist_entry in _case_hist:
                    _add_referenced_ids(_user_ids, _hist_entry, [ATTR_HISTORY_USER_ID])
        for _execution in self[ATTR_TEST_EXECUTIONS].values():
            _add_referenced_ids(_user_ids, _execution, [ATTR_ASSIGNEE, ATTR_TESTED_BY])
        for _plan in self[ATTR_TEST_PLANS].values():
            _add_referenced_ids(_user_ids, _plan, [ATTR_AUTHOR])
        for _run in self[ATTR_TEST_RUNS].values():
            _add_referenced_ids(_user_ids, _run, [ATTR_DEFAULT_TESTER, ATTR_MANAGER])
        return list(_user_ids)

    def referenced_version_ids(self):
        """
        :returns: TCMS ID's of all versions used by test plans
        :rtype: list
        """
        _version_ids = set()
        for _plan in self[ATTR_TEST_PLANS].values():
            _version_ids.add(_plan[ATTR_PRODUCT_VERSION])
        return list(_version_ids)

    def environments(self):
        """
        :returns: TCMS environments data stored in this entity
        :rtype: list
        """
        return [_env for _env in self[ATTR_ENVIRONMENTS].values()]

    def test_plans(self):
        """
        :returns: TCMS test plans data stored in this entity
        :rtype: list
        """
        return [_plan for _plan in self[ATTR_TEST_PLANS].values()]

    def execution_status_id_of(self, status_name):
        """
        Returns TCMS execution status ID for specified status name.
        :param str status_name: the status name
        :returns: TCMS status ID
        :rtype: int
        :raises IssaiException: if status name is unknown
        """
        return self[ATTR_MASTER_DATA].execution_status_id_of(status_name)

    def add_environments(self, envs):
        """
        Adds the specified environments.
        :param list envs: the TCMS environments data
        """
        if envs is not None:
            for _env in envs:
                self[ATTR_ENVIRONMENTS][_env[ATTR_ID]] = _env

    def add_tcms_cases(self, cases):
        """
        Adds the specified test cases.
        :param list cases: the TCMS test cases data
        """
        if cases is not None:
            for _case in cases:
                self[ATTR_TEST_CASES][_case[ATTR_ID]] = _case

    def add_tcms_executions(self, executions, update_cases=False):
        """
        Adds the specified test executions.
        :param list executions: the TCMS test executions data
        :param bool update_cases: indicates whether to update test case data from executions
        """
        if executions is not None:
            for _execution in executions:
                _execution_id = _execution[ATTR_ID]
                _case_id = _execution[ATTR_CASE]
                if _case_id not in self[ATTR_TEST_CASES]:
                    print(f'Test case {_case_id} for execution {_execution_id} not found, execution ignored')
                    continue
                self[ATTR_TEST_EXECUTIONS][_execution_id] = _execution
                if update_cases:
                    _run_id = _execution[ATTR_RUN]
                    self[ATTR_TEST_CASES][_case_id][ATTR_RUN] = _run_id
                    self[ATTR_TEST_CASES][_case_id][ATTR_EXECUTION] = _execution_id

    def add_tcms_plans(self, plans):
        """
        Adds the specified test plans.
        :param list plans: the TCMS test plans data
        """
        if plans is not None:
            for _plan in plans:
                self[ATTR_TEST_PLANS][_plan[ATTR_ID]] = _plan

    def add_tcms_runs(self, runs):
        """
        Adds the specified test runs.
        :param list runs: the TCMS test runs data
        """
        if runs is not None:
            for _run in runs:
                _run_id = _run[ATTR_ID]
                _plan_id = _run[ATTR_PLAN]
                self[ATTR_TEST_RUNS][_run_id] = _run
                self[ATTR_TEST_PLANS][_plan_id][ATTR_RUN] = _run_id

    def replace_attribute(self, class_id, object_id, replacement_value):
        """
        Replaces an attribute, because it doesn't exist in TCMS or another object shall be used instead.
        Updates all references to the replaced object to match the replacement.
        :param int class_id: the TCMS class ID
        :param int object_id: the TCMS object ID
        :param dict replacement_value: the new attribute value
        """
        _new_object_id = replacement_value[ATTR_ID]
        # eventually update object in data type
        if class_id == TCMS_CLASS_ID_PRODUCT:
            self[ATTR_PRODUCT] = replacement_value
        else:
            _objects = self.objects_of_class(class_id)
            if _objects is not None:
                if object_id in _objects.keys():
                    del _objects[object_id]
                _objects[_new_object_id] = replacement_value
        # eventually update references
        _references_desc = CLASS_REFERENCES.get(class_id)
        if _references_desc is not None:
            for _tcms_class_id, _attrs in _references_desc.items():
                _entity_data_type = data_type_for_tcms_class(_tcms_class_id)
                if _entity_data_type is None:
                    continue
                _entity_objects = self.get(_entity_data_type)
                if _entity_objects is None:
                    continue
                _replace_references(_entity_objects, _attrs, object_id, _new_object_id)
        self[ATTR_MASTER_DATA].replace_object(class_id, object_id, replacement_value)

    def fill_product_data(self, product):
        for _k, _v in product.items():
            self[ATTR_PRODUCT][_k] = _v

    def to_toml(self, include_references=False):
        """
        Converts this entity to TOML format.
        :param bool include_references: indicates whether to include references master data like versions or builds
        :returns: entity in TOML format
        :rtype: dict
        """
        _entity_data = table()
        _entity_data.append(ATTR_MASTER_DATA, self[ATTR_MASTER_DATA].to_toml())
        _entity_data[ATTR_PRODUCT] = _merge_toml(table(), self[ATTR_PRODUCT])
        if len(self[ATTR_ENVIRONMENTS]) > 0:
            _entity_data[ATTR_ENVIRONMENTS] = self.fill_test_objects_data(ATTR_ENVIRONMENTS)
        if len(self[ATTR_TEST_PLANS]) > 0:
            _entity_data[ATTR_TEST_PLANS] = self.fill_test_objects_data(ATTR_TEST_PLANS)
        if len(self[ATTR_TEST_RUNS]) > 0:
            _entity_data[ATTR_TEST_RUNS] = self.fill_test_objects_data(ATTR_TEST_RUNS)
        if len(self[ATTR_TEST_CASES]) > 0:
            _entity_data[ATTR_TEST_CASES] = self.fill_test_objects_data(ATTR_TEST_CASES)
        if len(self[ATTR_TEST_EXECUTIONS]) > 0:
            _entity_data[ATTR_TEST_EXECUTIONS] = self.fill_test_objects_data(ATTR_TEST_EXECUTIONS)
        return _entity_data

    def fill_from_toml(self, toml_data):
        """
        Fills attributes of this entity from TOML.
        :param TOMLDocument toml_data: the TOML data, usually read from file
        """
        self[ATTR_PRODUCT] = read_toml_value(toml_data, ATTR_PRODUCT, dict, True)
        self[ATTR_MASTER_DATA] = MasterData.from_toml(read_toml_value(toml_data, ATTR_MASTER_DATA, dict, True))
        self.add_environments(read_toml_value(toml_data, ATTR_ENVIRONMENTS, list))
        self.add_tcms_cases(read_toml_value(toml_data, ATTR_TEST_CASES, list))
        self.add_tcms_executions(read_toml_value(toml_data, ATTR_TEST_EXECUTIONS, list), True)
        self.add_tcms_plans(read_toml_value(toml_data, ATTR_TEST_PLANS, list))
        self.add_tcms_runs(read_toml_value(toml_data, ATTR_TEST_RUNS, list))


class ProductEntity(SpecificationEntity):
    """
    Complete product.
    """
    def __init__(self, product_id, product_name):
        """
        Constructor.
        :param int product_id: the TCMS product ID
        :param str product_name: the product name
        """
        super().__init__(ENTITY_TYPE_PRODUCT, product_id, product_name)

    @staticmethod
    def from_tcms(product):
        """
        Creates a product from TCMS.
        :param dict product: the TCMS product ID and name
        :returns: created entity
        :rtype: ProductEntity
        """
        _product = ProductEntity(product[ATTR_ID], product[ATTR_NAME])
        _product.fill_product_data(product)
        return _product

    @staticmethod
    def from_toml(product_id, product_name, toml_data):
        """
        Creates a product from TOML data.
        :param int product_id: the TCMS product ID
        :param str product_name: the product name
        :param TOMLDocument toml_data: the product data in TOML format
        :returns: created entity
        :rtype: ProductEntity
        """
        _product = ProductEntity(product_id, product_name)
        _product.fill_from_toml(toml_data)
        return _product


class TestCaseEntity(SpecificationEntity):
    """
    Test case.
    """
    def __init__(self, case_id, case_summary):
        """
        Constructor.
        :param int case_id: the TCMS test case ID
        :param str case_summary: the test case summary
        """
        super().__init__(ENTITY_TYPE_CASE, case_id, case_summary)

    @staticmethod
    def from_toml(case_id, case_summary, toml_data):
        """
        Creates a test case from TOML data.
        :param int case_id: the TCMS test case ID
        :param str case_summary: the test case summary
        :param TOMLDocument toml_data: the test case data in TOML format
        :returns: created test case
        :rtype: TestCaseEntity
        """
        _case = TestCaseEntity(case_id, case_summary)
        _case.fill_from_toml(toml_data)
        return _case


class TestPlanEntity(SpecificationEntity):
    """
    Test plan.
    """
    def __init__(self, plan_id, plan_name):
        """
        Constructor.
        :param int plan_id: the TCMS test plan ID
        :param str plan_name: the test plan name
        """
        super().__init__(ENTITY_TYPE_PLAN, plan_id, plan_name)

    def plan_child_ids(self, plan_id):
        """
        Returns all direct children of test plan with given ID.
        :param int plan_id: the test plan ID; -1 for entity ID
        :returns: IDs of all child test plans
        :rtype: list
        :raises IssaiException: if entity data is inconsistent
        """
        _parent_id = self.entity_id() if plan_id < 0 else plan_id
        return [_c[ATTR_ID] for _c in self[ATTR_TEST_PLANS].values() if _c.get(ATTR_PARENT) == _parent_id]

    def runnable_case_count(self):
        """
        Returns number of all automated test cases in active test plans of this entity.
        :returns: number of runnable test cases
        :rtype: int
        """
        _case_count = 0
        for _plan in self[ATTR_TEST_PLANS].values():
            if not _plan[ATTR_IS_ACTIVE]:
                continue
            for _case_id in _plan[ATTR_CASES]:
                if not self[ATTR_TEST_CASES][_case_id][ATTR_IS_AUTOMATED]:
                    continue
                _case_count += 1
        return _case_count

    def get_plan_properties(self, plan, property_patterns):
        """
        Returns properties of test plan with given ID that match one of the patterns specified
        :param dict plan: the test plan data
        :param set property_patterns: the regular expression patterns
        :returns: properties of test plan matching one of specified patterns
        :rtype: dict
        :raises IssaiException: if there is no test plan with specified ID
        """
        _run_id = plan.get(ATTR_RUN)
        if _run_id is None:
            return {}
        _run_data = self._run_for_plan_id(plan[ATTR_ID])
        _properties = _run_data.get(ATTR_PROPERTIES)
        if _properties is None:
            return {}
        return _matching_properties(_run_data.get(ATTR_PROPERTIES), property_patterns)

    @staticmethod
    def from_toml(plan_id, plan_name, toml_data):
        """
        Creates a test plan from TOML data.
        :param int plan_id: the TCMS test plan ID
        :param str plan_name: the test plan name
        :param TOMLDocument toml_data: the test plan data in TOML format
        :returns: created test plan
        :rtype: TestPlanEntity
        """
        _plan = TestPlanEntity(plan_id, plan_name)
        _plan.fill_from_toml(toml_data)
        return _plan

    def _run_for_plan_id(self, plan_id):
        """
        Returns data of test run associated with specified test plan.
        :param int plan_id: the test plan ID
        :returns: test run data
        :rtype: dict
        :raises IssaiException: if there is no associated test run
        """
        _plan_data = self.get_part(ATTR_TEST_PLANS, plan_id)
        _run_id = _plan_data.get(ATTR_RUN)
        _run_data = self.get_part(ATTR_TEST_RUNS, _run_id)
        if _run_data is None:
            raise IssaiException(E_UNKNOWN_ENTITY_PART, self.entity_name(), ATTR_TEST_RUNS, _run_id)
        return _run_data


class ResultEntity(Entity):
    """
    Base class for test results.
    Test results do not have an equivalent in TCMS, there they are part of test runs or test executions.
    They are modeled separately to allow for offline tests, where results can be stored in TCMS on demand.
    """
    def __init__(self, type_id, entities_attr_name, entity_id, parent_entity_name):
        """
        Constructor.
        :param int type_id: the result entity type (test case result or test plan result)
        :param str entities_attr_name: the attribute name for the result objects
        :param int entity_id: the TCMS entity ID of test plan or case
        :param str parent_entity_name: the name of parent entity (test plan name for test plan results,
                                       test case summary for test case results)
        """
        super().__init__(type_id, entity_id, parent_entity_name)
        self.__entities_attr_name = entities_attr_name
        _entity_attrs = {ATTR_START_DATE: None, ATTR_STOP_DATE: None, ATTR_OUTPUT_FILES: []}
        self[entities_attr_name] = {entity_id: _entity_attrs}

    def load_toml_group(self, toml_data, group_name, object_key):
        """
        Loads array of tables with specified key.
        :param table toml_data: the TOML data
        :param str group_name: the group name
        :param str object_key: the attribute name identifying an object
        :return:
        """
        _objects = toml_data.get(group_name)
        if _objects is None:
            return
        for _object in _objects:
            _object_id = _object[object_key]
            # TODO check attribute names and types
            if _object_id not in self[group_name]:
                self[group_name][_object_id] = {}
            for _k, _v in _object.items():
                self[group_name][_object_id][_k] = python_value(_v)


class PlanResultEntity(ResultEntity):
    """
    Result of a test plan execution.
    """
    def __init__(self, plan_id, plan_name):
        """
        Constructor.
        :param int plan_id: the TCMS test plan ID
        :param str plan_name: the test plan name
        """
        super().__init__(ENTITY_TYPE_PLAN_RESULT, ATTR_TEST_PLAN_RESULTS, plan_id, plan_name)
        _attrs = self[ATTR_TEST_PLAN_RESULTS][self.entity_id()]
        _attrs.update({ATTR_PLAN: plan_id, ATTR_CASE_RESULTS: [], ATTR_CHILD_PLAN_RESULTS: [],
                       ATTR_NOTES: '', ATTR_SUMMARY: ''})
        self[ATTR_TEST_CASE_RESULTS] = {}

    def attachments(self):
        """
        Returns all attachment file URLs referenced by this entity. Returned is a dictionary with TCMS class ID as
        top level key, followed by sub-key entity ID, then list of file names.
        :returns: all attachment file URLs referenced by this entity
        :rtype: dict
        """
        _attachments = super().attachments()
        _attachments[TCMS_CLASS_ID_TEST_RUN] = {}
        _attachments[TCMS_CLASS_ID_TEST_RUN][self.entity_id()] = self.output_files()
        return _attachments

    def output_files(self):
        """
        :returns: all output files associated with any test plan result; key test run ID, value file names
        :rtype: dict
        """
        _files = {}
        for _run_id, _plan_result in self[ATTR_TEST_PLAN_RESULTS].items():
            _run_files = _plan_result.get(ATTR_OUTPUT_FILES)
            if _run_files is not None and len(_run_files) > 0:
                _files[_run_id] = _run_files
        return _files

    def to_toml(self, include_references=False):
        """
        Converts this test plan result to TOML format.
        The returned dictionary contains two items, key 'test-case-result' holds an array of tables with all test
        case results in this test plan result, key 'test-plan-result' holds an array of tables with the attributes of
        this test plan result (first array element) and the attributes of all direct child test plan results.
        :param bool include_references: indicates whether to include references master data like versions or builds;
                                        ignored for result entities
        :returns: entity in TOML format
        :rtype: dict
        """
        _entity_data = table()
        _entity_data[ATTR_MASTER_DATA] = self[ATTR_MASTER_DATA].to_toml()
        _entity_data[ATTR_PRODUCT] = _merge_toml(table(), self[ATTR_PRODUCT])
        if len(self[ATTR_TEST_CASE_RESULTS]) > 0:
            _entity_data[ATTR_TEST_CASE_RESULTS] = self.fill_test_objects_data(ATTR_TEST_CASE_RESULTS)
        if len(self[ATTR_TEST_PLAN_RESULTS]) > 0:
            _entity_data[ATTR_TEST_PLAN_RESULTS] = self.fill_test_objects_data(ATTR_TEST_PLAN_RESULTS)
        return _entity_data

    @staticmethod
    def from_toml(run_id, plan_name, toml_data):
        """
        Creates a test plan result entity from TOML data.
        :param int run_id: the TCMS ID of the test run associated with the test plan
        :param str plan_name: the test plan name
        :param Table toml_data: the entity's data in TOML format
        :returns: created test plan result
        :rtype: PlanResultEntity
        """
        _plan_result = PlanResultEntity(run_id, plan_name)
        _plan_result.load_toml_group(toml_data, ATTR_TEST_PLAN_RESULTS, ATTR_RUN)
        _plan_result.load_toml_group(toml_data, ATTR_TEST_CASE_RESULTS, ATTR_EXECUTION)
        return _plan_result

    @staticmethod
    def from_result(core_result, plan_entity):
        """
        Creates a test plan result entity from TOML data.
        :param PlanResult core_result: the core test plan result from test execution
        :param TestPlanEntity plan_entity: the executed test plan entity
        :returns: created test plan result
        :rtype: PlanResultEntity
        """
        _plan_entity_id = core_result.get_attr_value(ATTR_PLAN)
        _plan_name = plan_entity.entity_name()
        _plan_result_entity = PlanResultEntity(_plan_entity_id, _plan_name)
        _plan_result_entity[ATTR_PRODUCT] = plan_entity[ATTR_PRODUCT].copy()
        _plan_result_entity[ATTR_MASTER_DATA] = plan_entity[ATTR_MASTER_DATA]
        for _pr in core_result.plan_results():
            _plan_id = _pr[ATTR_PLAN]
            _epr = _pr.copy()
            _epr[ATTR_CASE_RESULTS] = []
            for _cr in _pr[ATTR_CASE_RESULTS]:
                del _cr[ATTR_MATRIX_CODE]
                _case_id = _cr[ATTR_CASE]
                _plan_result_entity[ATTR_TEST_CASE_RESULTS][_case_id] = _cr.copy()
                _epr[ATTR_CASE_RESULTS].append(_case_id)
            _epr[ATTR_CHILD_PLAN_RESULTS] = [_cpr[ATTR_PLAN] for _cpr in _pr[ATTR_CHILD_PLAN_RESULTS]]
            _plan_result_entity[ATTR_TEST_PLAN_RESULTS][_plan_id] = _epr
        return _plan_result_entity


class MasterData(dict):
    """
    Master data for test specification entities like builds, versions or categories.
    """

    def __init__(self):
        """
        Constructor.
        """
        super().__init__()
        for _mtype in MASTER_DATA_TYPES:
            self[_mtype] = {}

    def object_count(self):
        """
        :returns: number of essential objects in master data
        :rtype: int
        """
        return sum([len(_object) for _object in self.values()])

    def object(self, data_type, object_id):
        """
        Returns master data object with specified type and ID.
        :param str data_type: the master data type
        :param int object_id: the object's TCMS ID
        :returns: the object found or None, if no such object exists
        :rtype: dict
        :raises IssaiException: if specified data type is not allowed
        """
        _objects = self.get(data_type)
        if _objects is None:
            raise IssaiException(E_INTERNAL_ERROR, localized_message(E_NOT_MASTER_DATA_CLASS, data_type))
        return _objects.get(object_id)

    def objects_of_type(self, data_type):
        """
        Returns all master data objects of specified type.
        :param str data_type: the master data type
        :returns: the attributes
        :rtype: list
        :raises IssaiException: if specified data type is not allowed
        """
        if data_type not in MASTER_DATA_TYPES:
            raise IssaiException(E_INTERNAL_ERROR, localized_message(E_NOT_MASTER_DATA_CLASS, data_type))
        return [_obj for _obj in self[data_type].values()]

    def objects_of_class(self, class_id):
        """
        Returns all master data objects of specified type.
        :param int class_id: the TCMS class ID
        :returns: the objects, None, if class is not a master data type
        :rtype: dict
        :raises IssaiException: if specified TCMS class ID is not allowed
        """
        _data_type = master_data_type_for_tcms_class(class_id)
        if _data_type is None:
            raise IssaiException(E_INTERNAL_ERROR, localized_message(E_NOT_MASTER_DATA_CLASS, class_id))
        return self[_data_type]

    def add_object(self, data_type, value):
        """
        Adds the specified object.
        :param str data_type: the master data type
        :param dict|list value: the object value(s)
        :raises IssaiException: if specified data type is not allowed
        """
        value = copy.deepcopy(value)
        if data_type == ATTR_CASE_COMPONENTS:
            # special case components, where attribute cases is a set
            # no need to distinguish value type here, always called with a list
            for _component in value:
                _component_id = _component[ATTR_ID]
                _case_ids = _component[ATTR_CASES]
                _stored_component = self[ATTR_CASE_COMPONENTS].get(_component_id)
                if _stored_component is None:
                    _component[ATTR_CASES] = set(_component[ATTR_CASES])
                    self[ATTR_CASE_COMPONENTS][_component_id] = _component
                else:
                    for _case_id in _case_ids:
                        if _case_id is not None:
                            _stored_component[ATTR_CASES].add(_case_id)
            return
        if data_type in MASTER_DATA_TYPES:
            if isinstance(value, dict):
                self[data_type][value[ATTR_ID]] = value
            else:
                for _v in value:
                    self[data_type][_v[ATTR_ID]] = _v
            return
        raise IssaiException(E_INTERNAL_ERROR, localized_message(E_NOT_MASTER_DATA_CLASS, data_type))

    def replace_object(self, class_id, object_id, replacement_value):
        """
        Replaces an object, because it doesn't exist in TCMS or another object shall be used instead.
        Updates all references to the replaced object to match the replacement.
        :param int class_id: the TCMS class ID
        :param int object_id: the TCMS object ID
        :param dict replacement_value: the new object value
        :raises IssaiException: if specified TCMS class ID is not allowed
        """
        _new_object_id = replacement_value[ATTR_ID]
        # eventually update object in data type
        # TODO check whether another object with new_object_id already exists !
        if class_id in MASTER_DATA_TYPE_TCMS_CLASS_IDS:
            # object is part of master data
            _objects = self.objects_of_class(class_id)
            if object_id in _objects:
                del _objects[object_id]
            _objects[_new_object_id] = replacement_value
        # eventually update references
        _references_desc = CLASS_REFERENCES.get(class_id)
        if _references_desc is not None:
            for _tcms_class_id, _attrs in _references_desc.items():
                _entity_data_type = master_data_type_for_tcms_class(_tcms_class_id)
                if _entity_data_type is None:
                    # referencing class is not a master data class
                    continue
                _entity_objects = self.get(_entity_data_type)
                _replace_references(_entity_objects, _attrs, object_id, _new_object_id)

    def user_ids(self):
        """
        :returns: all TCMS user IDs contained in master data
        :rtype: list
        """
        return list(self[ATTR_TCMS_USERS].keys())

    def user_names(self):
        """
        :returns: all TCMS usernames contained in master data
        :rtype: list
        """
        return [_u[ATTR_USERNAME] for _u in self[ATTR_TCMS_USERS].values()]

    def referenced_user_ids(self):
        """
        :returns: TCMS ID's of all users referenced by master data
        :rtype: list
        """
        _user_ids = set()
        for _component in self[ATTR_CASE_COMPONENTS].values():
            _add_referenced_ids(_user_ids, _component, [ATTR_INITIAL_OWNER, ATTR_INITIAL_QA_CONTACT])
        return list(_user_ids)

    def execution_status_id_of(self, status_name):
        """
        Returns TCMS execution status ID for specified status name.
        :param str status_name: the status name
        :returns: TCMS status ID
        :rtype: int
        :raises IssaiException: if status name is unknown
        """
        _lower_status_name = status_name.lower()
        for _es in self[ATTR_EXECUTION_STATUSES].values():
            if _lower_status_name == _es[ATTR_NAME].lower():
                return _es[ATTR_ID]
        raise IssaiException(E_CFG_INVALID_EXECUTION_STATUS, status_name)

    def to_toml(self):
        """
        :returns: master data in TOML format
        :rtype: Table
        """
        _master_data = table()
        for _type_key, _type_values in self.items():
            if len(_type_values) > 0:
                _values_data = array().multiline(True)
                for _elem in _type_values.values():
                    _elem_data = inline_table()
                    for _elem_key, _elem_value in _elem.items():
                        if isinstance(_elem_value, set):
                            _elem_data.append(_elem_key, list(_elem_value))
                        else:
                            _elem_data.append(_elem_key, _elem_value)
                    _values_data.append(_elem_data)
                _master_data.append(_type_key, _values_data)
        return _master_data

    @staticmethod
    def from_toml(toml_data):
        """
        Creates master data from TOML data.
        :param Table toml_data: the master data in TOML format
        :returns: created master data
        :rtype: MasterData
        :raises IssaiException: if TOML data is invalid
        """
        _master_data = MasterData()
        for _md_type, _md_value in toml_data.items():
            verify_master_data_type(_md_type, _md_value)
            _master_data[_md_type] = {}
            for _elem in _md_value:
                _elem_value = {}
                for _attr_name, _attr_value in _elem.items():
                    _elem_value[_attr_name] = verify_master_data_attr(_md_type, _attr_name, _attr_value)
                _master_data[_md_type][_elem_value[ATTR_ID]] = _elem_value
        return _master_data


def _add_referenced_ids(id_set, entity, attribute_names):
    """
    Adds IDs of referenced objects to given set, if the referencing attribute exists in the specified entity and has
    a value.
    :param set id_set: the result receiving all IDs found
    :param dict entity: the entity that may hold references
    :param list[str] attribute_names: names of all attributes in the entity that can hold references
    """
    for _a in attribute_names:
        _v = entity.get(_a)
        if _v is not None:
            id_set.add(_v)


def _replace_references(_entity_objects, _attrs, object_id, _new_object_id):
    for _object_value in _entity_objects.values():
        for _attr in _attrs:
            _ref_value = _object_value.get(_attr)
            if _ref_value is None:
                continue
            if isinstance(_ref_value, int):
                if _ref_value == object_id:
                    _object_value[_attr] = _new_object_id
                continue
            if isinstance(_ref_value, list):
                try:
                    _list_index = _ref_value.index(object_id)
                    _object_value[_attr][_list_index] = _new_object_id
                except ValueError:
                    pass


def _merge_toml(ensemble, part):
    """
    Merges specified part into given whole object.
    :param Entity ensemble: the whole object
    :param dict part: the part to merge into the ensemble
    :returns: whole object
    :rtype: Entity
    """
    if part is not None:
        _valid_parts = {}
        for _k, _v in part.items():
            if _v is not None:
                _valid_parts[_k] = _v
        for _k, _v in _valid_parts.items():
            _ensemble_value = ensemble.get(_k)
            if _ensemble_value is None:
                ensemble[_k] = _v
            else:
                _ensemble_value.append(_v)
    return ensemble


def read_toml_value(toml_data, key, required_data_type, mandatory=False):
    """
    Reads value with specified key from TOML object.
    :param Entity toml_data: the TOML object
    :param str key: the TOML key
    :param required_data_type: the TOML value's expected data type
    :param bool mandatory: indicates, whether the attribute for the key is mandatory
    :returns: TOML value
    :raises IssaiException: if key is not present or has wrong type
    """
    _entity_value = toml_data.get(key)
    if _entity_value is None:
        if mandatory:
            raise IssaiException(E_TOML_ATTRIBUTE_MISSING, key)
        return None
    if not isinstance(_entity_value, required_data_type):
        raise IssaiException(E_TOML_ATTRIBUTE_WRONG_TYPE, key, str(required_data_type))
    return python_value(_entity_value)


def _matching_properties(properties, property_patterns):
    """
    Returns all properties from a list that match one or more regular expression patterns.
    :param list properties: the properties
    :param set property_patterns: the patterns indicating desired properties; empty set means no properties
    :returns: all matching properties
    :rtype: dict
    """
    if len(property_patterns) == 0 or properties is None:
        return {}
    _matches = {}
    for _prop in properties:
        for _k in _prop.keys():
            if property_patterns is None:
                _matches[_k] = _prop.get(_k)
                continue
            for _pattern in property_patterns:
                if re.match(_k, _pattern) is None:
                    continue
                _matches[_k] = _prop.get(_k)
                break
    return _matches


CLASS_REFERENCES = {TCMS_CLASS_ID_BUILD: {TCMS_CLASS_ID_TEST_EXECUTION: [ATTR_BUILD],
                                          TCMS_CLASS_ID_TEST_RUN: [ATTR_BUILD]},
                    TCMS_CLASS_ID_CATEGORY: {TCMS_CLASS_ID_TEST_CASE: [ATTR_CATEGORY]},
                    TCMS_CLASS_ID_COMPONENT: {TCMS_CLASS_ID_TEST_CASE: [ATTR_COMPONENT]},
                    TCMS_CLASS_ID_PLAN_TYPE: {TCMS_CLASS_ID_TEST_PLAN: [ATTR_TYPE]},
                    TCMS_CLASS_ID_PRIORITY: {TCMS_CLASS_ID_TEST_CASE: [ATTR_PRIORITY]},
                    TCMS_CLASS_ID_PRODUCT: {TCMS_CLASS_ID_CATEGORY: [ATTR_PRODUCT],
                                            TCMS_CLASS_ID_COMPONENT: [ATTR_PRODUCT],
                                            TCMS_CLASS_ID_TEST_PLAN: [ATTR_PRODUCT],
                                            TCMS_CLASS_ID_VERSION: [ATTR_PRODUCT]},
                    TCMS_CLASS_ID_TEST_CASE: {TCMS_CLASS_ID_TEST_EXECUTION: [ATTR_CASE],
                                              TCMS_CLASS_ID_TEST_PLAN: [ATTR_CASES],
                                              TCMS_CLASS_ID_TEST_RUN: [ATTR_CASES]},
                    TCMS_CLASS_ID_TEST_CASE_STATUS: {TCMS_CLASS_ID_TEST_CASE: [ATTR_CASE_STATUS]},
                    TCMS_CLASS_ID_TEST_EXECUTION: {TCMS_CLASS_ID_TEST_CASE: [ATTR_EXECUTIONS],
                                                   TCMS_CLASS_ID_TEST_RUN: [ATTR_EXECUTIONS]},
                    TCMS_CLASS_ID_TEST_EXECUTION_STATUS: {TCMS_CLASS_ID_TEST_EXECUTION: [ATTR_STATUS]},
                    TCMS_CLASS_ID_TEST_PLAN: {TCMS_CLASS_ID_TEST_PLAN: [ATTR_PARENT],
                                              TCMS_CLASS_ID_TEST_RUN: [ATTR_PLAN]},
                    TCMS_CLASS_ID_TEST_RUN: {TCMS_CLASS_ID_TEST_EXECUTION: [ATTR_RUN],
                                             TCMS_CLASS_ID_TEST_PLAN: [ATTR_RUNS]},
                    TCMS_CLASS_ID_USER: {TCMS_CLASS_ID_COMPONENT: [ATTR_INITIAL_OWNER, ATTR_INITIAL_QA_CONTACT],
                                         TCMS_CLASS_ID_TEST_CASE: [ATTR_AUTHOR, ATTR_DEFAULT_TESTER, ATTR_REVIEWER],
                                         TCMS_CLASS_ID_TEST_EXECUTION: [ATTR_ASSIGNEE, ATTR_TESTED_BY],
                                         TCMS_CLASS_ID_TEST_PLAN: [ATTR_AUTHOR],
                                         TCMS_CLASS_ID_TEST_RUN: [ATTR_DEFAULT_TESTER, ATTR_MANAGER]},
                    TCMS_CLASS_ID_VERSION: {TCMS_CLASS_ID_BUILD: [ATTR_VERSION],
                                            TCMS_CLASS_ID_TEST_PLAN: [ATTR_PRODUCT_VERSION]}}

MASTER_DATA_TYPES = {ATTR_CASE_CATEGORIES, ATTR_CASE_COMPONENTS, ATTR_CASE_PRIORITIES, ATTR_CASE_STATUSES,
                     ATTR_EXECUTION_STATUSES, ATTR_PLAN_TYPES, ATTR_PRODUCT_BUILDS, ATTR_PRODUCT_CLASSIFICATIONS,
                     ATTR_PRODUCT_VERSIONS, ATTR_TCMS_USERS}
