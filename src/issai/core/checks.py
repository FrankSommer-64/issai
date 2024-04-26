# -----------------------------------------------------------------------------------------------
# issai - test runner for tests managed by Kiwi test case management system
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
Verification functions for entities.
"""


from datetime import datetime

from tomlkit.items import Array, Table, InlineTable, Bool, Integer, String

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *


def verify_entity_attr_name(entity_type_id, attr_name):
    """
    Asserts that the specified attribute name is valid for given entity type.
    :param int entity_type_id: the entity type ID
    :param str attr_name: the attribute name
    :raises IssaiException: if attribute name is invalid
    """
    if attr_name in _ENTITY_ATTRIBUTES[entity_type_id]:
        return
    raise IssaiException(E_TOML_ENTITY_ATTR_NAME_INVALID, attr_name, entity_type_name(entity_type_id))


def verify_entity_attr_write(entity_type_id, attr_name, attr_value):
    """
    Asserts that the specified attribute can be updated with given value.
    :param int entity_type_id: the entity type ID
    :param str attr_name: the attribute name
    :param attr_value: the attribute value
    :raises IssaiException: if attribute name is invalid, attribute is immutable or value has wrong type
    """
    _attr_desc = _ENTITY_ATTRIBUTES[entity_type_id].get(attr_name)
    if _attr_desc is None:
        raise IssaiException(E_TOML_ENTITY_ATTR_NAME_INVALID, attr_name, entity_type_name(entity_type_id))
    if not isinstance(attr_value, _attr_desc[0]):
        raise IssaiException(E_TOML_ENTITY_ATTR_INVALID_TYPE, attr_name, entity_type_name(entity_type_id),
                             _attr_desc[0])
    if not _attr_desc[1]:
        raise IssaiException(E_TOML_ENTITY_ATTR_IMMUTABLE, entity_type_name(entity_type_id), attr_name)


def verify_master_data_type(data_type, data_value):
    """
    Asserts that the specified data type is valid for master data.
    :param str data_type: the master data's TOML key
    :param list|Array data_value: the master data's TOML value
    :raises IssaiException: if data type is invalid
    """
    if data_type in _MASTER_DATA_TYPES:
        if isinstance(data_value, list) or isinstance(data_value, Array):
            return
        raise IssaiException(E_TOML_MASTER_DATA_TYPE_NOT_ARRAY, data_type)
    raise IssaiException(E_TOML_MASTER_DATA_TYPE_INVALID, data_type)


def verify_master_data_attr(data_type, attr_name, attr_value):
    """
    Asserts that the specified master data attribute is valid.
    :param str data_type: the master data's TOML key
    :param str attr_name: the attribute name
    :param attr_value: the TOML attribute value
    :returns: Python attribute value
    :raises IssaiException: if data type is invalid
    """
    _tcms_class = _MASTER_DATA_TCMS_CLASSES[data_type]
    _attr_desc = _TCMS_ATTRS[_tcms_class].get(attr_name)
    if _attr_desc is None:
        raise IssaiException(E_TOML_MASTER_DATA_ATTR_INVALID_NAME, attr_name, data_type)
    if not isinstance(attr_value, _attr_desc[0]):
        raise IssaiException(E_TOML_MASTER_DATA_ATTR_INVALID_TYPE, attr_name, data_type)
    if isinstance(attr_value, (Array, Table, InlineTable, Bool, Integer, String)):
        return attr_value.unwrap()
    return attr_value


# Attributes of entity objects.
# Keys are attribute names, value indicates the data type and whether the attribute is writable after construction.
_ENTITY_ATTRIBUTES = {
    RESULT_TYPE_CASE_RESULT: {ATTR_CASE: (int, False), ATTR_CASE_NAME: (str, False), ATTR_COMMENT: (str, True),
                              ATTR_EXECUTION: (int, True), ATTR_OUTPUT_FILES: (list, False),
                              ATTR_PLAN: (int, False), ATTR_RUN: (int, True),
                              ATTR_START_DATE: (datetime, True), ATTR_STOP_DATE: (datetime, True),
                              ATTR_STATUS: (str, True), ATTR_TESTER_NAME: (str, True)},
    RESULT_TYPE_PLAN_RESULT: {ATTR_BUILD: (str, False), ATTR_CASE_RESULTS: (list, False),
                              ATTR_CHILD_PLAN_RESULTS: (list, False), ATTR_NOTES: (str, True),
                              ATTR_OUTPUT_FILES: (list, True), ATTR_PLAN: (int, False),
                              ATTR_PLAN_NAME: (str, True), ATTR_RUN: (int, False), ATTR_START_DATE: (datetime, True),
                              ATTR_STOP_DATE: (datetime, True), ATTR_SUMMARY: (str, True), ATTR_VERSION: (str, False)}
}

# TOML master data types
_MASTER_DATA_TYPES = {ATTR_CASE_CATEGORIES, ATTR_CASE_COMPONENTS, ATTR_CASE_PRIORITIES, ATTR_CASE_STATUSES,
                      ATTR_EXECUTION_STATUSES, ATTR_PLAN_TYPES, ATTR_PRODUCT_BUILDS, ATTR_PRODUCT_CLASSIFICATIONS,
                      ATTR_PRODUCT_VERSIONS, ATTR_TCMS_USERS}

# Mapping of master data type to TCMS class
_MASTER_DATA_TCMS_CLASSES = {ATTR_CASE_CATEGORIES: TCMS_CLASS_CATEGORY, ATTR_CASE_COMPONENTS: TCMS_CLASS_COMPONENT,
                             ATTR_CASE_PRIORITIES: TCMS_CLASS_PRIORITY, ATTR_CASE_STATUSES: TCMS_CLASS_TEST_CASE_STATUS,
                             ATTR_EXECUTION_STATUSES: TCMS_CLASS_TEST_EXECUTION_STATUS,
                             ATTR_PLAN_TYPES: TCMS_CLASS_PLAN_TYPE, ATTR_PRODUCT_BUILDS: TCMS_CLASS_BUILD,
                             ATTR_PRODUCT_CLASSIFICATIONS: TCMS_CLASS_CLASSIFICATION,
                             ATTR_PRODUCT_VERSIONS: TCMS_CLASS_VERSION, ATTR_TCMS_USERS: TCMS_CLASS_USER}

# Issai supported attributes of TCMS objects.
# Keys are attribute names, value indicates the data type and whether the attribute is mandatory for usage
# in an Issai entity.
_TCMS_ATTRS = {
    TCMS_CLASS_BUILD: {'id': (int, True), 'is_active': (bool, True), 'name': (str, True), 'version': (int, True)},
    TCMS_CLASS_CATEGORY: {'description': (str, False), 'id': (int, True), 'name': (str, True), 'product': (int, True)},
    TCMS_CLASS_CLASSIFICATION: {'id': (int, True), 'name': (str, True)},
    TCMS_CLASS_COMPONENT: {'cases': (list, False), 'description': (str, False), 'id': (int, True),
                           'initial_owner': (int, False), 'initial_qa_contact': (int, False), 'name': (str, True),
                           'product': (int, True)},
    TCMS_CLASS_ENVIRONMENT: {'description': (str, False), 'id': (int, True), 'name': (str, True)},
    TCMS_CLASS_PLAN_TYPE: {'description': (str, False), 'id': (int, True), 'name': (str, True)},
    TCMS_CLASS_PRIORITY: {'id': (int, True), 'is_active': (bool, True), 'value': (str, True)},
    TCMS_CLASS_PRODUCT: {'description': (str, False), 'id': (int, True), 'name': (str, True),
                         'classification': (int, True)},
    TCMS_CLASS_TAG: {'bugs': (int, False), 'case': (int, False), 'id': (int, True), 'name': (str, True),
                     'plan': (int, False), 'run': (int, False)},
    TCMS_CLASS_TEST_CASE: {'arguments': (str, False), 'author': (int, False), 'case_status': (int, True),
                           'category': (int, True), 'default_tester': (int, False), 'expected_duration': (int, False),
                           'extra_link': (str, False), 'id': (int, True), 'is_automated': (bool, True),
                           'notes': (str, False), 'priority': (int, True), 'requirement': (str, False),
                           'reviewer': (int, False), 'setup_duration': (int, False), 'summary': (str, True),
                           'testing_duration': (int, False), 'text': (str, True)},
    TCMS_CLASS_TEST_CASE_HISTORY: {'history_change_reason': (str, False), 'history_date': (datetime, True),
                                   'history_id': (int, True), 'history_type': (str, True),
                                   'history_user_id': (int, True)},
    TCMS_CLASS_TEST_CASE_STATUS: {'description': (str, False), 'id': (int, True), 'is_confirmed': (bool, True),
                                  'name': (str, True)},
    TCMS_CLASS_TEST_EXECUTION: {'actual_duration': (int, False), 'assignee': (int, False), 'build': (int, True),
                                'case': (int, True), 'expected_duration': (int, False), 'id': (int, True),
                                'run': (int, True), 'status': (int, True), 'start_date': (datetime, False),
                                'stop_date': (datetime, False), 'tested_by': (int, False)},
    TCMS_CLASS_TEST_EXECUTION_HISTORY: {'history_change_reason': (str, False), 'history_date': (datetime, False),
                                        'history_user__username': (str, True)},
    TCMS_CLASS_TEST_EXECUTION_STATUS: {'color': (str, False), 'icon': (str, False), 'id': (int, True),
                                       'name': (str, True), 'weight': (int, False)},
    TCMS_CLASS_TEST_PLAN: {'author': (int, False), 'extra_link': (str, False), 'id': (int, True),
                           'is_active': (bool, True), 'name': (str, True), 'parent': (int, False),
                           'product': (int, True), 'product_version': (int, True), 'text': (str, True),
                           'type': (int, True)},
    TCMS_CLASS_TEST_RUN: {'build': (int, True), 'default_tester': (int, False), 'id': (int, True),
                          'manager': (int, True), 'notes': (str, False), 'plan': (int, True),
                          'planned_start': (datetime, False), 'planned_stop': (datetime, False),
                          'start_date': (datetime, False), 'stop_date': (datetime, False), 'summary': (str, True)},
    TCMS_CLASS_USER: {'email': (str, False), 'first_name': (str, True), 'id': (int, True), 'is_active': (bool, True),
                      'is_staff': (bool, True), 'is_superuser': (bool, True), 'last_name': (str, True),
                      'username': (str, True)},
    TCMS_CLASS_VERSION: {'id': (int, True), 'product': (int, True), 'value': (str, True)},
}
