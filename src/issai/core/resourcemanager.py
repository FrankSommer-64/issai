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
High level interface towards Kiwi TCMS and file system.
"""

from tomlkit.api import TOMLDocument
from tomlkit.items import AoT, Array, DateTime, Float, InlineTable, Integer, String, Table

from issai.core.status import ContainerStatus
from issai.core.tcms import *


def container_status(toml_data):
    """
    Determines status of an issai container in TOML format.
    :param TOMLDocument toml_data: container file name including full path
    :returns: problems
    :rtype: ContainerStatus
    """
    _entity_type = toml_data.get(ATTR_ENTITY_TYPE)
    if _entity_type is None:
        raise IssaiException(E_IMP_ATTR_MISSING, ATTR_ENTITY_TYPE)
    if not isinstance(_entity_type, str):
        raise IssaiException(E_IMP_ATTR_TYPE_INVALID, ATTR_ENTITY_TYPE)
    if _entity_type not in _SUPPORTED_ENTITY_TYPES:
        raise IssaiException(E_IMP_ATTR_VALUE_INVALID, ATTR_ENTITY_TYPE)
    _status = ContainerStatus()
    _top_level_desc = _HEADER_ATTRS.copy()
    _top_level_desc.update(_ENTITY_GROUPS[_entity_type])
    _check_toml_table(_status, toml_data, '', _top_level_desc)
    if _entity_type in (ENTITY_TYPE_NAME_PRODUCT, ENTITY_TYPE_NAME_PLAN):
        _check_toml_table(_status, toml_data.get(ATTR_PRODUCT), ATTR_PRODUCT, _GROUP_PRODUCT_ATTRS)
        _check_master_data(_status, toml_data.get(ATTR_MASTER_DATA))
        _check_toml_aot(_status, toml_data.get(ATTR_ENVIRONMENTS), ATTR_ENVIRONMENTS, _GROUP_ENV_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_PLANS), ATTR_TEST_PLANS, _GROUP_PLAN_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_RUNS), ATTR_TEST_RUNS, _GROUP_RUN_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_CASES), ATTR_TEST_CASES, _GROUP_CASE_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_EXECUTIONS), ATTR_TEST_EXECUTIONS,
                        _GROUP_EXECUTION_ATTRS, True)
    elif _entity_type == ENTITY_TYPE_NAME_CASE:
        _check_toml_table(_status, toml_data.get(ATTR_PRODUCT), ATTR_PRODUCT, _GROUP_PRODUCT_ATTRS)
        _check_master_data(_status, toml_data.get(ATTR_MASTER_DATA))
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_CASES), ATTR_TEST_CASES, _GROUP_CASE_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_EXECUTIONS), ATTR_TEST_EXECUTIONS,
                        _GROUP_EXECUTION_ATTRS, True)
    elif _entity_type == ENTITY_TYPE_NAME_PLAN_RESULT:
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_PLAN_RESULTS), ATTR_TEST_PLAN_RESULTS,
                        _GROUP_PLAN_RESULT_ATTRS, True)
        _check_toml_aot(_status, toml_data.get(ATTR_TEST_CASE_RESULTS), ATTR_TEST_CASE_RESULTS,
                        _GROUP_CASE_RESULT_ATTRS, True)
        _check_attr_match(_status, toml_data, ATTR_ENTITY_ID, ATTR_TEST_PLAN_RESULTS, -1, ATTR_RUN)
        _check_attr_match(_status, toml_data, ATTR_ENTITY_NAME, ATTR_TEST_PLAN_RESULTS, -1, ATTR_PLAN_NAME)
    return _status


def _check_attr_match(status, toml_data, top_level_attr_name, group_name, group_index, group_attr_name):
    """
    Checks whether two TOML attributes have the same value.
    :param ContainerStatus status: the status object receiving check result
    :param TOMLDocument toml_data: the TOML data to check
    :param str top_level_attr_name: the name of the top level attribute holding the first value
    :param str group_name: the TOML group name holding the second attribute
    :param int group_index: the group index number of the second attribute within array of tables; -1,
                            if matching group is not known
    :param str group_attr_name: the name of the attribute holding the second value
    :rtype: None
    """
    _value1 = toml_data.get(top_level_attr_name)
    if _value1 is None:
        return
    _group = toml_data.get(group_name)
    if _group is None:
        return
    if not isinstance(_group, AoT):
        return
    if group_index < 0:
        for _elem in _group.unwrap():
            _value2 = _elem.get(group_attr_name)
            if _value2 is None:
                return
            if type(_value1) is not type(_value2):
                return
            if _value1 == _value2:
                return
        _qualified_group_attr_name = f'{group_name}.{group_attr_name}'
        status.add_issue(ContainerStatus.MISMATCH, top_level_attr_name, -1, _qualified_group_attr_name)
        return
    if len(_group) <= group_index:
        return
    _group_element = _group[group_index]
    _value2 = _group_element.get(group_attr_name)
    if _value2 is None:
        return
    if type(_value1) is not type(_value2):
        return
    if _value1 != _value2:
        _qualified_group_attr_name = f'{group_name}.{group_attr_name}'
        status.add_issue(ContainerStatus.MISMATCH, top_level_attr_name, group_index + 1, _qualified_group_attr_name)


def _check_toml_table(status, toml_table, group_name, group_desc, element_nr=-1):
    """
    Executes syntactic and semantic checks for a TOML table group.
    :param ContainerStatus status: the status object receiving check results
    :param Table toml_table: the TOML table representing the group to check
    :param str group_name: the TOML group name
    :param dict group_desc: the descriptor holding required properties for the TOML group
    :param int element_nr: the optional table number within an array of tables
    :rtype: None
    """
    if toml_table is None:
        status.add_issue(ContainerStatus.MISSING, group_name, element_nr)
        return
    _mandatory_status = {}
    for _attr_name, _attr_desc in group_desc.items():
        if _attr_desc[0]:
            _mandatory_status[_attr_name] = False
    for _attr_name, _attr_value in toml_table.items():
        _qualified_attr_name = _attr_name if len(group_name) == 0 else f'{group_name}.{_attr_name}'
        _attr_desc = group_desc.get(_attr_name)
        if _attr_desc is None:
            status.add_issue(ContainerStatus.UNSUPPORTED, _qualified_attr_name, element_nr)
            continue
        if _attr_desc[0]:
            _mandatory_status[_attr_name] = True
        if type(_attr_value) is not _attr_desc[1]:
            status.add_issue(ContainerStatus.INVALID_TYPE, _qualified_attr_name, element_nr)
            continue
        if type(_attr_value) is Array:
            for _elem in _attr_value:
                if type(_elem) is not _attr_desc[2]:
                    _qualified_attr_name = f'{_qualified_attr_name}-elements'
                    status.add_issue(ContainerStatus.INVALID_TYPE, _qualified_attr_name, element_nr)
                    break
            continue
        if _attr_desc[2] is not None:
            if _attr_value not in _attr_desc[2]:
                status.add_issue(ContainerStatus.INVALID_VALUE, _qualified_attr_name)
    for _attr_name, _status in _mandatory_status.items():
        if not _status:
            _qualified_attr_name = _attr_name if len(group_name) == 0 else f'{group_name}.{_attr_name}'
            status.add_issue(ContainerStatus.MISSING, _qualified_attr_name, element_nr)


def _check_toml_aot(status, toml_data, group_name, group_desc, multiples_allowed):
    """
    Executes syntactic and semantic checks for a TOML array of tables group.
    :param ContainerStatus status: the status object receiving check results
    :param AoT toml_data: the TOML array of tables group to check
    :param str group_name: the TOML group name
    :param dict group_desc: the descriptor holding required properties for the TOML group
    :param bool multiples_allowed: indicates whether the array of tables may hold more than one element
    :rtype: None
    """
    if toml_data is None:
        # if the group is mandatory, that's already covered in top level check
        return
    if not multiples_allowed and len(toml_data) > 1:
        status.add_issue(ContainerStatus.MULTIPLE, group_name)
        return
    _element_nr = 1
    for _attr_value in toml_data.body:
        _check_toml_table(status, _attr_value, group_name, group_desc, _element_nr)
        _element_nr += 1


def _check_master_data(status, toml_data):
    """
    Executes syntactic and semantic checks for master data.
    :param ContainerStatus status: the status object receiving check results
    :param Table toml_data: the TOML table holding the master data
    :rtype: None
    """
    _check_toml_table(status, toml_data, ATTR_MASTER_DATA, _GROUP_MASTER_DATA_ATTRS)
    for _type_name, _type_desc in _MASTER_DATA_ATTRS.items():
        _type_data = toml_data.get(_type_name)
        if _type_data is None:
            continue
        for _elem_nr, _elem in enumerate(_type_data):
            _check_toml_table(status, _elem, _type_name, _type_desc, _elem_nr)


_SUPPORTED_ENTITY_TYPES = (ENTITY_TYPE_NAME_PRODUCT, ENTITY_TYPE_NAME_CASE, ENTITY_TYPE_NAME_PLAN,
                           ENTITY_TYPE_NAME_PLAN_RESULT)

_ENTITY_GROUPS = {ENTITY_TYPE_NAME_PRODUCT: {ATTR_MASTER_DATA: (True, Table, None),
                                             ATTR_ENVIRONMENTS: (False, AoT, None),
                                             ATTR_PRODUCT: (True, Table, None),
                                             ATTR_TEST_CASES: (False, AoT, None),
                                             ATTR_TEST_CASE_RESULTS: (False, AoT, None),
                                             ATTR_TEST_EXECUTIONS: (True, AoT, None),
                                             ATTR_TEST_PLANS: (False, AoT, None),
                                             ATTR_TEST_PLAN_RESULTS: (False, AoT, None),
                                             ATTR_TEST_RUNS: (True, AoT, None)},
                  ENTITY_TYPE_NAME_CASE: {ATTR_MASTER_DATA: (True, Table, None),
                                          ATTR_PRODUCT: (True, Table, None),
                                          ATTR_TEST_CASES: (True, AoT, None)},
                  ENTITY_TYPE_NAME_PLAN: {ATTR_MASTER_DATA: (True, Table, None),
                                          ATTR_ENVIRONMENTS: (False, AoT, None),
                                          ATTR_PRODUCT: (True, Table, None),
                                          ATTR_TEST_CASES: (False, AoT, None),
                                          ATTR_TEST_EXECUTIONS: (True, AoT, None),
                                          ATTR_TEST_PLANS: (True, AoT, None),
                                          ATTR_TEST_RUNS: (True, AoT, None)},
                  ENTITY_TYPE_NAME_PLAN_RESULT: {ATTR_TEST_CASE_RESULTS: (False, AoT, None),
                                                 ATTR_TEST_PLAN_RESULTS: (True, AoT, None)}
                  }

_HEADER_ATTRS = {ATTR_ENTITY_TYPE: (True, String, _SUPPORTED_ENTITY_TYPES),
                 ATTR_ENTITY_ID: (True, Integer, None),
                 ATTR_ENTITY_NAME: (True, String, None)}

_GROUP_CASE_ATTRS = {ATTR_ID: (True, Integer, None),
                     ATTR_CATEGORY: (True, Integer, None),
                     ATTR_PRIORITY: (True, Integer, None),
                     ATTR_SUMMARY: (True, String, None),
                     ATTR_ARGUMENTS: (False, String, None),
                     ATTR_ATTACHMENTS: (False, Array, String),
                     ATTR_AUTHOR: (False, Integer, None),
                     ATTR_CASE_STATUS: (False, Integer, None),
                     ATTR_CC_NOTIFICATIONS: (False, Array, String),
                     ATTR_COMMENTS: (False, Array, String),
                     ATTR_COMPONENTS: (False, Array, Integer),
                     ATTR_DEFAULT_TESTER: (False, Integer, None),
                     ATTR_EXECUTIONS: (False, Array, Integer),
                     ATTR_EXPECTED_DURATION: (False, Float, None),
                     ATTR_EXTRA_LINK: (False, String, None),
                     ATTR_HISTORY: (False, Array, InlineTable),
                     ATTR_IS_AUTOMATED: (False, bool, None),
                     ATTR_NOTES: (False, String, None),
                     ATTR_PROPERTIES: (False, Array, InlineTable),
                     ATTR_REQUIREMENT: (False, String, None),
                     ATTR_REVIEWER: (False, Integer, None),
                     ATTR_SCRIPT: (False, String, None),
                     ATTR_SETUP_DURATION: (False, Float, None),
                     ATTR_TAGS: (False, Array, String),
                     ATTR_TESTING_DURATION: (False, Float, None),
                     ATTR_TEXT: (False, String, None)}

_GROUP_CASE_RESULT_ATTRS = {ATTR_CASE_NAME: (True, String, None),
                            ATTR_COMMENT: (False, String, None),
                            ATTR_EXECUTION: (True, Integer, None),
                            ATTR_OUTPUT_FILES: (False, Array, String),
                            ATTR_START_DATE: (True, DateTime, None),
                            ATTR_STATUS: (True, String, None),
                            ATTR_STOP_DATE: (True, DateTime, None),
                            ATTR_TESTER_NAME: (True, String, None)}

_GROUP_EXECUTION_ATTRS = {ATTR_ID: (True, Integer, None),
                          ATTR_BUILD: (True, Integer, None),
                          ATTR_CASE: (True, Integer, None),
                          ATTR_RUN: (True, Integer, None),
                          ATTR_STATUS: (True, Integer, None),
                          ATTR_ACTUAL_DURATION: (False, Float, None),
                          ATTR_ASSIGNEE: (False, Integer, None),
                          ATTR_COMMENTS: (False, Array, InlineTable),
                          ATTR_EXPECTED_DURATION: (False, Float, None),
                          ATTR_HISTORY: (False, Array, InlineTable),
                          ATTR_LINKS: (False, Array, String),
                          ATTR_PROPERTIES: (False, Array, InlineTable),
                          ATTR_START_DATE: (False, DateTime, None),
                          ATTR_STOP_DATE: (False, DateTime, None),
                          ATTR_TESTED_BY: (False, Integer, None)}

_GROUP_MASTER_DATA_ATTRS = {ATTR_CASE_CATEGORIES: (False, Array, InlineTable),
                            ATTR_CASE_COMPONENTS: (False, Array, InlineTable),
                            ATTR_CASE_PRIORITIES: (False, Array, InlineTable),
                            ATTR_CASE_STATUSES: (False, Array, InlineTable),
                            ATTR_EXECUTION_STATUSES: (False, Array, InlineTable),
                            ATTR_PLAN_TYPES: (False, Array, InlineTable),
                            ATTR_PRODUCT_BUILDS: (False, Array, InlineTable),
                            ATTR_PRODUCT_CLASSIFICATIONS: (False, Array, InlineTable),
                            ATTR_PRODUCT_VERSIONS: (False, Array, InlineTable),
                            ATTR_TCMS_USERS: (False, Array, InlineTable)}

_GROUP_PLAN_ATTRS = {ATTR_ID: (True, Integer, None),
                     ATTR_IS_ACTIVE: (True, bool, None),
                     ATTR_NAME: (True, String, None),
                     ATTR_PRODUCT: (True, Integer, None),
                     ATTR_PRODUCT_VERSION: (True, Integer, None),
                     ATTR_TYPE: (True, Integer, None),
                     ATTR_ATTACHMENTS: (False, Array, String),
                     ATTR_AUTHOR: (False, Integer, None),
                     ATTR_CASES: (False, Array, Integer),
                     ATTR_EXTRA_LINK: (False, String, None),
                     ATTR_PARENT: (False, Integer, None),
                     ATTR_RUNS: (False, Array, Integer),
                     ATTR_TAGS: (False, Array, String),
                     ATTR_TEXT: (False, String, None)}

_GROUP_PLAN_RESULT_ATTRS = {ATTR_NOTES: (False, String, None),
                            ATTR_OUTPUT_FILES: (False, Array, String),
                            ATTR_PLAN_NAME: (True, String, None),
                            ATTR_RUN: (True, Integer, None),
                            ATTR_START_DATE: (True, DateTime, None),
                            ATTR_STOP_DATE: (True, DateTime, None),
                            ATTR_SUMMARY: (False, String, None)}

_GROUP_PRODUCT_ATTRS = {ATTR_ID: (True, Integer, None),
                        ATTR_CLASSIFICATION: (True, Integer, None),
                        ATTR_NAME: (True, String, None),
                        ATTR_DESCRIPTION: (False, String, None)}

_GROUP_ENV_ATTRS = {ATTR_ID: (True, Integer, None),
                    ATTR_NAME: (True, String, None),
                    ATTR_DESCRIPTION: (True, String, None),
                    ATTR_PROPERTIES: (False, Array, InlineTable)}

_GROUP_RUN_ATTRS = {ATTR_ID: (True, Integer, None),
                    ATTR_BUILD: (True, Integer, None),
                    ATTR_MANAGER: (True, Integer, None),
                    ATTR_PLAN: (True, Integer, None),
                    ATTR_SUMMARY: (True, String, None),
                    ATTR_DEFAULT_TESTER: (False, Integer, None),
                    ATTR_EXECUTIONS: (False, Array, Integer),
                    ATTR_NOTES: (False, String, None),
                    ATTR_PROPERTIES: (False, Array, InlineTable),
                    ATTR_START_DATE: (False, DateTime, None),
                    ATTR_STOP_DATE: (False, DateTime, None),
                    ATTR_ACTUAL_DURATION: (False, Float, None),
                    ATTR_TAGS: (False, Array, String)}

_MASTER_DATA_ATTRS = {ATTR_CASE_CATEGORIES: {ATTR_ID: (True, Integer, None),
                                             ATTR_NAME: (True, String, None),
                                             ATTR_PRODUCT: (True, Integer, None),
                                             ATTR_DESCRIPTION: (False, String, None)},
                      ATTR_CASE_COMPONENTS: {ATTR_ID: (True, Integer, None),
                                             ATTR_NAME: (True, String, None),
                                             ATTR_PRODUCT: (True, Integer, None),
                                             ATTR_CASES: (False, Array, Integer),
                                             ATTR_DESCRIPTION: (False, String, None),
                                             ATTR_INITIAL_OWNER: (False, Integer, None),
                                             ATTR_INITIAL_QA_CONTACT: (False, Integer, None)},
                      ATTR_CASE_PRIORITIES: {ATTR_ID: (True, Integer, None),
                                             ATTR_IS_ACTIVE: (True, bool, None),
                                             ATTR_VALUE: (True, String, None)},
                      ATTR_CASE_STATUSES: {ATTR_ID: (True, Integer, None),
                                           ATTR_IS_CONFIRMED: (True, bool, None),
                                           ATTR_NAME: (True, String, None),
                                           ATTR_DESCRIPTION: (False, String, None)},
                      ATTR_EXECUTION_STATUSES: {ATTR_ID: (True, Integer, None),
                                                ATTR_NAME: (True, String, None),
                                                ATTR_COLOR: (False, String, None),
                                                ATTR_ICON: (False, String, None),
                                                ATTR_WEIGHT: (False, Integer, None)},
                      ATTR_PLAN_TYPES: {ATTR_ID: (True, Integer, None),
                                        ATTR_NAME: (True, String, None),
                                        ATTR_DESCRIPTION: (False, String, None)},
                      ATTR_PRODUCT_BUILDS: {ATTR_ID: (True, Integer, None),
                                            ATTR_IS_ACTIVE: (True, bool, None),
                                            ATTR_NAME: (True, String, None),
                                            ATTR_VERSION: (True, Integer, None)},
                      ATTR_PRODUCT_CLASSIFICATIONS: {ATTR_ID: (True, Integer, None),
                                                     ATTR_NAME: (True, String, None)},
                      ATTR_PRODUCT_VERSIONS: {ATTR_ID: (True, Integer, None),
                                              ATTR_PRODUCT: (True, Integer, None),
                                              ATTR_VALUE: (True, String, None)},
                      ATTR_TCMS_USERS: {ATTR_ID: (True, Integer, None),
                                        ATTR_EMAIL: (True, String, None),
                                        ATTR_USERNAME: (True, String, None),
                                        ATTR_FIRST_NAME: (False, String, None),
                                        ATTR_IS_ACTIVE: (False, bool, None),
                                        ATTR_IS_STAFF: (False, bool, None),
                                        ATTR_IS_SUPERUSER: (False, bool, None),
                                        ATTR_LAST_NAME: (False, String, None)},
                      }
