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
Issai entity classes.
The entities model central objects of Issai: products, test plans, test cases and test plan results.
Products and test cases can be exported from and imported to TCMS.
Test plans can be exported from and imported to TCMS, and can be executed.
Test plan results can be imported to TCMS.
"""

import re

from tomlkit import aot, array, dump, inline_table, load, table, TOMLDocument

from issai.core import *
from issai.core.checks import verify_master_data_type
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.results import PlanResult
from issai.core.util import python_value

# Groups with referenced auxiliary data, present for all entity types.
# Modeled as array of inline tables in TOML.
MASTER_DATA_GROUPS = {ATTR_CASE_CATEGORIES, ATTR_CASE_COMPONENTS, ATTR_CASE_PRIORITIES, ATTR_CASE_STATUSES,
                      ATTR_EXECUTION_STATUSES, ATTR_PLAN_TYPES, ATTR_PRODUCT_BUILDS, ATTR_PRODUCT_CLASSIFICATIONS,
                      ATTR_PRODUCT_VERSIONS, ATTR_TCMS_USERS}
RESULT_GROUPS = {ATTR_TEST_CASES, ATTR_TEST_EXECUTIONS, ATTR_TEST_PLANS, ATTR_TEST_RUNS}
RESULT_ARRAYS = {ATTR_TEST_CASE_RESULTS, ATTR_TEST_PLAN_RESULTS}
SPEC_GROUPS = {ATTR_ENVIRONMENTS, ATTR_TEST_CASES, ATTR_TEST_EXECUTIONS, ATTR_TEST_PLANS, ATTR_TEST_RUNS}

_DEP_SORTED_ENTITY_ATTRIBUTES = [ATTR_PRODUCT_CLASSIFICATIONS, ATTR_ENVIRONMENTS, ATTR_CASE_PRIORITIES,
                                 ATTR_CASE_STATUSES, ATTR_EXECUTION_STATUSES, ATTR_TCMS_USERS, ATTR_COMPONENTS,
                                 ATTR_PRODUCT, ATTR_CASE_CATEGORIES, ATTR_PRODUCT_VERSIONS, ATTR_PRODUCT_BUILDS,
                                 ATTR_TEST_CASES, ATTR_TEST_PLANS, ATTR_TEST_RUNS, ATTR_TEST_EXECUTIONS]

_DEP_SORTED_TCMS_CLASS_IDS = [TCMS_CLASS_ID_CLASSIFICATION, TCMS_CLASS_ID_ENVIRONMENT, TCMS_CLASS_ID_PRIORITY,
                              TCMS_CLASS_ID_TEST_CASE_STATUS, TCMS_CLASS_ID_TEST_EXECUTION_STATUS, TCMS_CLASS_ID_USER,
                              TCMS_CLASS_ID_COMPONENT, TCMS_CLASS_ID_PRODUCT, TCMS_CLASS_ID_CATEGORY,
                              TCMS_CLASS_ID_VERSION, TCMS_CLASS_ID_BUILD, TCMS_CLASS_ID_TEST_CASE,
                              TCMS_CLASS_ID_TEST_PLAN, TCMS_CLASS_ID_TEST_RUN, TCMS_CLASS_ID_TEST_EXECUTION]


def class_ids_ordered_by_dependency():
    """
    :returns: Issai relevant TCMS class ID's, classes without references to other classes first
    :rtype: list[int]
    """
    return _DEP_SORTED_TCMS_CLASS_IDS


def entity_attributes_ordered_by_dependency():
    """
    :returns: Issai relevant entity attributes, attributes containing objects without references to other objects first
    :rtype: list[str]
    """
    return _DEP_SORTED_ENTITY_ATTRIBUTES


class IssaiEntity(dict):
    """
    Base class for all types of issai entities.
    Entities consist of four or five parts:
    - header data (entity type, entity ID, entity name)
    - master data (builds, categories, components, versions, ...)
    - product
    - test objects (test plans, test cases, test runs, test executions, test plan results)
    - optional environments
    For product, each master data and test object type there is a corresponding "group" attribute holding the data of
    all objects with that type. Each group attribute is a dictionary with object ID as key.
    """

    def __init__(self, entity_type, entity_id, entity_name):
        """
        Constructor.
        :param str entity_type: the entity type as used in TOML files (product, test-case, test-plan, test-plan-result)
        :param int entity_id: product ID for products, test plan ID for test plans and test plan results,
                              test case ID for test cases
        :param str entity_name: product name for products, test plan name for test plans and test plan results,
                          test case summary for test cases
        """
        super().__init__()
        self[ATTR_ENTITY_TYPE] = entity_type
        self[ATTR_ENTITY_ID] = entity_id
        self[ATTR_ENTITY_NAME] = entity_name
        self[ATTR_PRODUCT] = {}
        for _group in MASTER_DATA_GROUPS:
            self[_group] = {}

    def set_product(self, product):
        """
        Sets entity product data.
        :param dict product: the product
        """
        if isinstance(product, dict):
            self[ATTR_PRODUCT].update(product)

    def add_objects(self, group, objects):
        """
        Adds the specified group objects.
        :param str group: the group name
        :param list[dict] objects: the objects to add
        :raises IssaiException: if group doesn't exist or an object to add is already contained in the entity
        """
        if objects is None:
            return
        if group not in self:
            raise IssaiException(E_INVALID_ENTITY_GROUP, self.entity_name(), group)
        for _object in objects:
            _object_id = _object[ATTR_ID]
            if _object_id in self[group]:
                raise IssaiException(E_ENTITY_OBJECT_EXISTS, self.entity_name(), group, _object_id)
            self[group][_object_id] = _object

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

    def entity_type(self):
        """
        :returns: the entity's type name
        :rtype: str
        """
        return self[ATTR_ENTITY_TYPE]

    # noinspection PyMethodMayBeStatic
    def attachments(self):
        """
        Returns all attachment file URLs referenced by this entity. For products, test plans and test cases these are
        the files to download from TCMS; for test plan results the files to upload to TCMS.
        :returns: attachment file URLs as two-staged dict {class ID: {object ID: [URLs]}}
        :rtype: dict
        """
        # no attachments specific to base class
        return {}

    # noinspection PyMethodMayBeStatic
    def attachment_count(self):
        """
        :returns: number of attachment file references by this entity
        :rtype: int
        """
        # no attachments specific to base class
        return 0

    def object_count(self):
        """
        :returns: number of essential objects in this entity, needed for accurate progress information
        :rtype: int
        """
        # base class responsible for master data only, product always part of entity
        _prod_count = 0 if len(self[ATTR_PRODUCT]) == 0 else 1
        return self.master_data_object_count() + _prod_count

    def master_data_object_count(self):
        """
        :returns: number of master data objects in this entity
        :rtype: int
        """
        return sum([len(self[_group]) for _group in MASTER_DATA_GROUPS])

    def group_objects(self, group):
        """
        :param str group: the desired group name
        :returns: all objects in specified group
        :rtype: list[dict]
        """
        return self[group].values() if group in self else []

    def group_object_count(self, group):
        """
        :param str group: the desired group name
        :returns: number of objects in specified group
        :rtype: int
        """
        return len(self[group]) if group in self else 0

    def group_attachments(self, group, tcms_class_id):
        """
        Returns all attachment file URLs referenced by objects of specified group.
        :param str group: the desired group name
        :param int tcms_class_id: the TCMS class ID of all group objects
        :returns: attachment file URLs as two-staged dict {class ID: {object ID: [URLs]}}
        :rtype: dict
        """
        _group_attachments = {}
        for _object in self[group].values():
            _object_attachments = _object[ATTR_ATTACHMENTS]
            if len(_object_attachments) > 0:
                _group_attachments[_object[ATTR_ID]] = _object_attachments
        return {} if len(_group_attachments) == 0 else {tcms_class_id: _group_attachments}

    def group_attachment_count(self, group):
        """
        :param str group: the desired group name
        :returns: number of attachment files in specified group
        :rtype: int
        """
        return sum([len(_object[ATTR_ATTACHMENTS]) for _object in self[group].values()])

    def to_toml(self):
        """
        Converts this entity to TOML format.
        :returns: entity in TOML format
        :rtype: TOMLDocument
        """
        _toml_data = TOMLDocument()
        _toml_data.append(ATTR_ENTITY_TYPE, self.entity_type())
        _toml_data.append(ATTR_ENTITY_NAME, self.entity_name())
        _toml_data.append(ATTR_ENTITY_ID, self.entity_id())
        _master_data = table()
        for _group in MASTER_DATA_GROUPS:
            _group_data = array()
            for _object in self[_group].values():
                _object_data = inline_table()
                _object_data.update(_object)
                _group_data.append(_object_data)
            _master_data.append(_group, _group_data)
        _toml_data.append(ATTR_MASTER_DATA, _master_data)
        _product_data = table()
        _product_data.update(self[ATTR_PRODUCT])
        _toml_data.append(ATTR_PRODUCT, _product_data)
        return _toml_data

    def to_file(self, file_path):
        """
        Writes TOML data of this entity to file.
        :param str file_path: the full path of the output file
        :raises IssaiException: if the file could not be written
        """
        try:
            _toml_data = self.to_toml()
            with open(file_path, 'w') as _f:
                dump(_toml_data, _f)
        except IssaiException:
            raise
        except Exception as _e:
            raise IssaiException(E_WRITE_FILE_FAILED, file_path, _e)

    def __eq__(self, other):
        if type(other) is type(self):
            return all(k in other and self[k] == other[k] for k in self) \
                and all(k in self and self[k] == other[k] for k in other)
        return False

    @staticmethod
    def from_file(file_path):
        """
        Creates an entity from file.
        :param str file_path: the full path of the file containing the entity's data in TOML format
        :returns: created entity object
        :rtype: IssaiEntity
        :raises IssaiException: if the file could not be read
        """
        try:
            with open(file_path, 'r') as _f:
                return IssaiEntity.from_toml(load(_f))
        except IssaiException:
            raise
        except Exception as _e:
            raise IssaiException(E_READ_FILE_FAILED, file_path, _e)

    @staticmethod
    def from_toml(toml_data):
        """
        Creates an entity from TOML data.
        :param TOMLDocument toml_data: the entity's data in TOML format
        :returns: created entity object
        :rtype: IssaiProductEntity | IssaiCaseEntity | IssaiPlanEntity | IssaiPlanResultEntity
        """
        _entity_id = read_toml_value(toml_data, ATTR_ENTITY_ID, int, True)
        _entity_name = read_toml_value(toml_data, ATTR_ENTITY_NAME, str, True)
        _entity_type = read_toml_value(toml_data, ATTR_ENTITY_TYPE, str, True)
        _master_data = read_toml_value(toml_data, ATTR_MASTER_DATA, dict, True)
        _product_data = read_toml_value(toml_data, ATTR_PRODUCT, dict, True)
        if _entity_type == ENTITY_TYPE_PLAN_RESULT:
            _entity = IssaiPlanResultEntity(_entity_id, _entity_name)
        elif _entity_type == ENTITY_TYPE_PRODUCT:
            _entity = IssaiProductEntity(_entity_id, _entity_name)
        elif _entity_type == ENTITY_TYPE_CASE:
            _entity = IssaiTestCaseEntity(_entity_id, _entity_name)
        elif _entity_type == ENTITY_TYPE_PLAN:
            _entity = IssaiTestPlanEntity(_entity_id, _entity_name)
        else:
            raise IssaiException(E_INVALID_ENTITY_TYPE, _entity_type)
        _entity.set_product(_product_data)
        for _md_group, _md_value in _master_data.items():
            verify_master_data_type(_md_group, _md_value)
            _entity.add_objects(_md_group, read_toml_value(_master_data, _md_group, list, True))
        _entity.add_objects(ATTR_ENVIRONMENTS, read_toml_value(toml_data, ATTR_ENVIRONMENTS, list))
        _entity.add_objects(ATTR_TEST_CASES, read_toml_value(toml_data, ATTR_TEST_CASES, list))
        _entity.add_objects(ATTR_TEST_PLANS, read_toml_value(toml_data, ATTR_TEST_PLANS, list))
        if _entity_type == ENTITY_TYPE_PLAN_RESULT:
            _entity.add_objects(ATTR_TEST_CASE_RESULTS, read_toml_value(toml_data, ATTR_TEST_CASE_RESULTS, list))
            _entity.add_objects(ATTR_TEST_PLAN_RESULTS, read_toml_value(toml_data, ATTR_TEST_PLAN_RESULTS, list))
        else:
            _entity.add_objects(ATTR_TEST_EXECUTIONS, read_toml_value(toml_data, ATTR_TEST_EXECUTIONS, list))
            _entity.add_objects(ATTR_TEST_RUNS, read_toml_value(toml_data, ATTR_TEST_RUNS, list))
        return _entity


class IssaiSpecificationEntity(IssaiEntity):
    """
    Base class for test specification entities (products, test cases and test plans).
    """

    def __init__(self, entity_type, entity_id, entity_name):
        """
        Constructor.
        :param str entity_type: the entity type as used in TOML files (product, test-case, test-plan)
        :param int entity_id: product ID for products, test case ID for test cases, test plan ID for test plans
        :param str entity_name: product name for products, test case summary for test cases,
                                test plan name for test plans
        """
        super().__init__(entity_type, entity_id, entity_name)
        for _group in SPEC_GROUPS:
            self[_group] = {}

    def attachments(self):
        """
        Returns all attachment file URLs referenced by this entity.
        For products, test plans and test cases these are the files to download from TCMS.
        :returns: attachment file URLs as two-staged dict {class ID: {object ID: [URLs]}}
        :rtype: dict
        """
        _attachments = super().attachments()
        _attachments.update(self.group_attachments(ATTR_TEST_CASES, TCMS_CLASS_ID_TEST_CASE))
        _attachments.update(self.group_attachments(ATTR_TEST_PLANS, TCMS_CLASS_ID_TEST_PLAN))
        return _attachments

    def attachment_count(self):
        """
        :returns: number of attachment file references by this entity
        :rtype: int
        """
        return super().attachment_count() + self.group_attachment_count(ATTR_TEST_CASES) + \
            self.group_attachment_count(ATTR_TEST_PLANS)

    def object_count(self):
        """
        :returns: number of essential objects in this entity, needed for accurate progress information
        :rtype: int
        """
        return super().object_count() + sum([len(self[_group]) for _group in SPEC_GROUPS])

    def referenced_ids_for_class(self, tcms_class_id):
        """
        :param int tcms_class_id: the TCMS class
        :returns: TCMS ID's of all objects of specified class referenced by other entity objects
        :rtype: list[int]
        """
        _ref_desc = CLASS_REFERENCES.get(tcms_class_id)
        if _ref_desc is None:
            return []
        _referenced_ids = set()
        for _group, _attrs in _ref_desc.items():
            if _group not in self:
                continue
            for _object in self[_group].values():
                for _attr in _attrs:
                    _referenced_ids.add(_object[_attr])
        return list(_referenced_ids)

    def to_toml(self):
        """
        Converts this entity to TOML format.
        :returns: entity in TOML format
        :rtype: TOMLDocument
        """
        _toml_data = super().to_toml()
        for _group in SPEC_GROUPS:
            _group_data = aot()
            for _object in self[_group].values():
                _group_data.append(_object)
            _toml_data.add(_group, _group_data)
        return _toml_data


class IssaiPlanResultEntity(IssaiEntity):
    """
    Test plan result including results of covered test cases and eventual descendant test plans.
    Test plan results do not have an equivalent in TCMS, there they are part of test runs or test executions.
    They are modeled separately to allow for offline tests, where results can be stored in TCMS on demand.
    """

    def __init__(self, plan_id, plan_name):
        """
        Constructor.
        :param int plan_id: the TCMS ID of the executed top level test plan
        :param str plan_name: the name of the executed top level test plan
        """
        super().__init__(ENTITY_TYPE_PLAN_RESULT, plan_id, plan_name)
        for _group in RESULT_GROUPS:
            self[_group] = {}
        for _group in RESULT_ARRAYS:
            self[_group] = []

    def fill_execution_result(self, plan_result):
        """
        Stores result from test plan execution into this entity.
        :param PlanResult plan_result: result data from execution of top level test plan
        """
        self[ATTR_TEST_PLAN_RESULTS] = plan_result.plan_results()
        self[ATTR_TEST_CASE_RESULTS] = plan_result.case_results()


class IssaiProductEntity(IssaiSpecificationEntity):
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
        Header data, test objects  and environments to be added.
        :param dict product: the plain TCMS product data
        :returns: created entity
        :rtype: IssaiProductEntity
        """
        _product = IssaiProductEntity(product[ATTR_ID], product[ATTR_NAME])
        _product.set_product(product)
        return _product


class IssaiTestCaseEntity(IssaiSpecificationEntity):
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
    def from_tcms(case, product):
        """
        Creates a test case from TCMS.
        Header data, test objects  and environments to be added.
        :param dict case: the plain TCMS test case data
        :param dict product: the plain TCMS product data
        :returns: created entity
        :rtype: IssaiTestCaseEntity
        """
        _case = IssaiTestCaseEntity(case[ATTR_ID], case[ATTR_SUMMARY])
        _case.set_product(product)
        return _case


class IssaiTestPlanEntity(IssaiSpecificationEntity):
    """
    Test plan.
    """

    def __init__(self, plan_id, plan_name):
        """
        Constructor.
        :param int plan_id: the TCMS test case ID
        :param str plan_name: the test plan name
        """
        super().__init__(ENTITY_TYPE_CASE, plan_id, plan_name)

    @staticmethod
    def from_tcms(plan, product):
        """
        Creates a test plan from TCMS.
        Header data, test objects  and environments to be added.
        :param dict plan: the plain TCMS test plan data
        :param dict product: the plain TCMS product data
        :returns: created entity
        :rtype: IssaiTestPlanEntity
        """
        _plan = IssaiTestPlanEntity(plan[ATTR_ID], plan[ATTR_NAME])
        _plan.set_product(product)
        return _plan


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
    :param TOMLDocument toml_data: the TOML object
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


# Descriptor table for object references.
# Outer key TCMS class being referenced, inner key entity group name, inner value list of attribute names
# referencing an object of the TCMS class
CLASS_REFERENCES = {TCMS_CLASS_ID_BUILD: {ATTR_TEST_EXECUTIONS: [ATTR_BUILD],
                                          ATTR_TEST_RUNS: [ATTR_BUILD]},
                    TCMS_CLASS_ID_CATEGORY: {ATTR_TEST_CASES: [ATTR_CATEGORY]},
                    TCMS_CLASS_ID_COMPONENT: {ATTR_TEST_CASES: [ATTR_COMPONENT]},
                    TCMS_CLASS_ID_PLAN_TYPE: {ATTR_TEST_PLANS: [ATTR_TYPE]},
                    TCMS_CLASS_ID_PRIORITY: {ATTR_TEST_CASES: [ATTR_PRIORITY]},
                    TCMS_CLASS_ID_PRODUCT: {ATTR_CASE_CATEGORIES: [ATTR_PRODUCT],
                                            ATTR_CASE_COMPONENTS: [ATTR_PRODUCT],
                                            ATTR_TEST_PLANS: [ATTR_PRODUCT],
                                            ATTR_PRODUCT_VERSIONS: [ATTR_PRODUCT]},
                    TCMS_CLASS_ID_TEST_CASE: {ATTR_TEST_EXECUTIONS: [ATTR_CASE],
                                              ATTR_TEST_PLANS: [ATTR_CASES],
                                              ATTR_TEST_RUNS: [ATTR_CASES]},
                    TCMS_CLASS_ID_TEST_CASE_STATUS: {ATTR_TEST_CASES: [ATTR_CASE_STATUS]},
                    TCMS_CLASS_ID_TEST_EXECUTION: {ATTR_TEST_CASES: [ATTR_EXECUTIONS],
                                                   ATTR_TEST_RUNS: [ATTR_EXECUTIONS]},
                    TCMS_CLASS_ID_TEST_EXECUTION_STATUS: {ATTR_TEST_EXECUTIONS: [ATTR_STATUS]},
                    TCMS_CLASS_ID_TEST_PLAN: {ATTR_TEST_PLANS: [ATTR_PARENT],
                                              ATTR_TEST_RUNS: [ATTR_PLAN]},
                    TCMS_CLASS_ID_TEST_RUN: {ATTR_TEST_EXECUTIONS: [ATTR_RUN],
                                             ATTR_TEST_PLANS: [ATTR_RUNS]},
                    TCMS_CLASS_ID_USER: {ATTR_CASE_COMPONENTS: [ATTR_INITIAL_OWNER, ATTR_INITIAL_QA_CONTACT],
                                         ATTR_TEST_CASES: [ATTR_AUTHOR, ATTR_DEFAULT_TESTER, ATTR_REVIEWER],
                                         ATTR_TEST_EXECUTIONS: [ATTR_ASSIGNEE, ATTR_TESTED_BY],
                                         ATTR_TEST_PLANS: [ATTR_AUTHOR],
                                         ATTR_TEST_RUNS: [ATTR_DEFAULT_TESTER, ATTR_MANAGER]},
                    TCMS_CLASS_ID_VERSION: {ATTR_PRODUCT_BUILDS: [ATTR_VERSION],
                                            ATTR_TEST_PLANS: [ATTR_PRODUCT_VERSION]}}
