# -*- coding: utf-8 -*-

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
Wrapper functions around Kiwi TCMS XML-RPC-API.
The XML-RPC communication handle is automatically managed in a thread-safe way.
The module uses dict values for TCMS entities, as the XML-RPC API.
"""

import datetime
import re
import threading
import xmlrpc.client

from tcms_api import TCMS

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.util import full_path_of


class ObjectStatus:
    """
    Provides information about the relation of an object loaded from file to its counterpart in TCMS.
    """

    # TCMS object with identical ID and name exists
    EXACT_MATCH = 1

    # other TCMS object with identical name exists
    OTHER_NAME_MATCH = 2

    # no TCMS object with identical name exists
    NO_MATCH = 3

    def __init__(self, match_status, class_id, container_object, tcms_object=None):
        """
        Constructor.
        :param int match_status: the relation status between container object and its counterpart in TCMS
        :param int class_id: the object's TCMS class ID
        :param dict container_object: the container object
        :param dict tcms_object: the TCMS counterpart of the container object
        """
        self.__match_status = match_status
        self.__class_id = class_id
        self.__container_object = container_object
        self.__tcms_object = tcms_object

    def is_exact_match(self):
        """
        :return: True, if container object exists with same ID and name in TCMS
        :rtype: bool
        """
        return self.__match_status == ObjectStatus.EXACT_MATCH

    def is_name_match(self):
        """
        :return: True, if container object exists with same name, but other ID in TCMS
        :rtype: bool
        """
        return self.__match_status == ObjectStatus.OTHER_NAME_MATCH

    def is_no_match(self):
        """
        :return: True, if a TCMS object with same name as container object doesn't exist
        :rtype: bool
        """
        return self.__match_status == ObjectStatus.NO_MATCH

    def container_object(self):
        """
        :return: container object
        :rtype: dict
        """
        return self.__container_object

    def tcms_object(self):
        """
        :return: TCMS object
        :rtype: dict
        """
        return self.__tcms_object

    def __str__(self):
        _class = tcms_class_name_for_id(self.__class_id)
        _entity_id = self.__container_object[ATTR_ID]
        _tcms_id = -1 if self.__tcms_object is None else self.__tcms_object[ATTR_ID]
        return f'STATUS:{self.__match_status}/CLASS:{_class}/ENTITY-ID:{_entity_id}/TCMS-ID:{_tcms_id}'


class TcmsInterface:
    """
    Manages XML-RPC calls to TCMS.
    """
    _lock = threading.Lock()
    _initialized = False
    _current_user = None
    _server_version = ''
    _case_status_id_confirmed = 0
    _case_statuses_by_id = dict()
    _case_statuses_by_name = dict()
    _execution_statuses_by_id = dict()
    _execution_statuses_by_name = dict()
    _connections = dict()

    @staticmethod
    def confirmed_case_status_id():
        """
        :returns: ID of test case status CONFIRMED
        :rtype: int
        :raises IssaiException: if there is an XML-RPC communication error
        """
        try:
            if TcmsInterface._lock.acquire():
                if not TcmsInterface._initialized:
                    TcmsInterface._connect_to_server()
                return TcmsInterface._case_status_id_confirmed
        except BaseException as _e:
            raise IssaiException(E_TCMS_INIT_FAILED, str(_e))
        finally:
            TcmsInterface._lock.release()

    @staticmethod
    def connection():
        """
        :returns: XML-RPC connection for current thread
        :rtype: tcms_api._ConnectionProxy
        :raises IssaiException: if there is an XML-RPC communication error
        """
        try:
            _thread_id = threading.get_ident()
            if TcmsInterface._lock.acquire():
                if not TcmsInterface._initialized:
                    TcmsInterface._connect_to_server()
                return TcmsInterface._connection_for_thread(_thread_id)
        except BaseException as _e:
            raise IssaiException(E_TCMS_INIT_FAILED, str(_e))
        finally:
            TcmsInterface._lock.release()

    @staticmethod
    def current_user():
        """
        :returns: current TCMS user
        :rtype: dict
        :raises IssaiException: if there is an XML-RPC communication error
        """
        try:
            if TcmsInterface._lock.acquire():
                if not TcmsInterface._initialized:
                    TcmsInterface._connect_to_server()
                return TcmsInterface._current_user
        except BaseException as _e:
            raise IssaiException(E_TCMS_INIT_FAILED, str(_e))
        finally:
            TcmsInterface._lock.release()

    @staticmethod
    def execution_status_id_for(name):
        """
        Returns TCMS ID of execution status with specified name.
        :param str name: the execution status name
        :returns: execution ID; None if no such status exists
        :rtype: int
        :raises IssaiException: if there is an XML-RPC communication error
        """
        try:
            if TcmsInterface._lock.acquire():
                if not TcmsInterface._initialized:
                    TcmsInterface._connect_to_server()
                _execution_status = TcmsInterface._execution_statuses_by_name.get(name)
                return None if _execution_status is None else _execution_status[ATTR_ID]
        except BaseException as _e:
            raise IssaiException(E_TCMS_INIT_FAILED, str(_e))
        finally:
            TcmsInterface._lock.release()

    @staticmethod
    def initialize():
        """
        Initializes the interface to TCMS server.
        :raises IssaiException: if there is an XML-RPC communication error
        """
        try:
            if TcmsInterface._lock.acquire():
                if not TcmsInterface._initialized:
                    TcmsInterface._connect_to_server()
        except BaseException as _e:
            raise IssaiException(E_TCMS_INIT_FAILED, str(_e))
        finally:
            TcmsInterface._lock.release()

    @staticmethod
    def reset():
        """
        Clears all internal data about TCMS server connection.
        To be called a setting in the XML-RPC credentials file was changed.
        """
        if TcmsInterface._lock.acquire():
            if not TcmsInterface._initialized:
                TcmsInterface._lock.release()
                return
            TcmsInterface._initialized = False
            TcmsInterface._current_user = None
            TcmsInterface._server_version = ''
            TcmsInterface._case_status_id_confirmed = 0
            TcmsInterface._connections.clear()
            TcmsInterface._case_statuses_by_id.clear()
            TcmsInterface._case_statuses_by_name.clear()
            TcmsInterface._execution_statuses_by_id.clear()
            TcmsInterface._execution_statuses_by_name.clear()
        TcmsInterface._lock.release()

    @staticmethod
    def _connect_to_server():
        """
        Connects to TCMS server and reads current user, server version, case and execution statuses to internal
        variables. Class lock must have been acquired successfully when calling this function.
        :raises IssaiException: if there is an XML-RPC communication error
        """
        _xml_rpc_cxn = TCMS().exec
        TcmsInterface._connections[threading.get_ident()] = _xml_rpc_cxn
        _credentials_file_path = full_path_of(TCMS_XML_RPC_CREDENTIALS_FILE_PATH)
        with open(_credentials_file_path, 'r') as _f:
            _contents = _f.read()
        _m = re.search(r'^\s*username\s*=\s*(.*?)\s*$', _contents, re.MULTILINE | re.DOTALL)
        _user_name = _m.group(1)
        _user = _xml_rpc_cxn.User.filter({ATTR_USERNAME: _user_name})[0]
        TcmsInterface._current_user = _remove_unsupported_attrs(_user, _SUPPORTED_ATTRS[TCMS_CLASS_USER])
        TcmsInterface._server_version = _xml_rpc_cxn.KiwiTCMS.version()
        _case_statuses = _xml_rpc_cxn.TestCaseStatus.filter({})
        for _case_status in _case_statuses:
            TcmsInterface._case_statuses_by_id[_case_status[ATTR_ID]] = _case_status
            TcmsInterface._case_statuses_by_name[_case_status[ATTR_NAME]] = _case_status
            if _case_status[ATTR_IS_CONFIRMED]:
                TcmsInterface._case_status_id_confirmed = _case_status[ATTR_ID]
        _execution_statuses = _xml_rpc_cxn.TestExecutionStatus.filter({})
        for _execution_status in _execution_statuses:
            TcmsInterface._execution_statuses_by_id[_execution_status[ATTR_ID]] = _execution_status
            TcmsInterface._execution_statuses_by_name[_execution_status[ATTR_NAME]] = _execution_status
        TcmsInterface._initialized = True

    @staticmethod
    def _connection_for_thread(thread_id):
        """
        Returns XML-RPC connection for specified thread. Class lock must have been acquired successfully when calling
        this function.
        :param int thread_id: the thread identifier
        :returns: XML-RPC connection for current thread
        :rtype: TCMS
        :raises IssaiException: if there is an XML-RPC communication error
        """
        _handle = TcmsInterface._connections.get(thread_id)
        if _handle is None:
            _handle = TCMS().exec
            TcmsInterface._connections[thread_id] = _handle
        return _handle


def add_plan_case(plan_id, case_id):
    """
    Adds specified test case to given test plan.
    :param int plan_id: the TCMS test plan ID
    :param int case_id: the TCMS test case ID
    """
    _cxn = TcmsInterface.connection()
    _cxn.TestPlan.add_case(plan_id, case_id)


def create_run_from_plan(plan, build):
    """
    Creates a TCMS test run for given test plan.
    :param dict plan: the TCMS test plan data
    :param dict build: the TCMS build data
    :return: TCMS test run
    :rtype: dict
    :raises IssaiException: if test run cannot be created
    """
    try:
        _cxn = TcmsInterface.connection()
        _manager = TcmsInterface.current_user()[ATTR_ID]
        _attributes = {ATTR_BUILD: build[ATTR_ID], ATTR_MANAGER: TcmsInterface.current_user()[ATTR_ID],
                       ATTR_PLAN: plan[ATTR_ID], ATTR_SUMMARY: plan[ATTR_NAME]}
        _run = _cxn.TestRun.create(_attributes)
        _run[ATTR_EXECUTIONS] = []
        _run[ATTR_TAGS] = []
        _run_id = _run[ATTR_ID]
        for _case_id in plan[ATTR_CASES]:
            _executions = _cxn.TestRun.add_case(_run_id, _case_id)
            for _execution in _executions:
                _run[ATTR_EXECUTIONS].append(_execution[ATTR_ID])
        for _tag in plan[ATTR_TAGS]:
            _cxn.TestRun.add_tag(_run_id, _tag)
            _run[ATTR_TAGS].append(_tag)
        return _run
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_CREATE_OBJECT_FAILED, TCMS_CLASS_TEST_RUN, str(_e))


def create_tcms_object(class_id, container_object):
    """
    Creates a TCMS object from specified container object.
    :param int class_id: the TCMS class ID
    :param dict container_object: the container object
    :return: TCMS object
    :rtype: dict
    :raises IssaiException: if object cannot be created
    """
    try:
        _cxn = TcmsInterface.connection()
        _attributes = container_object.copy()
        if ATTR_ID in _attributes:
            del _attributes[ATTR_ID]
        _remove_unsupported_attrs(_attributes, _SUPPORTED_ATTRS[tcms_class_name_for_id(class_id)])
        if class_id == TCMS_CLASS_ID_BUILD:
            _builds = _cxn.Build.filter({ATTR_NAME: _attributes[ATTR_NAME], ATTR_VERSION: _attributes[ATTR_VERSION]})
            if len(_builds) > 0:
                _object = _builds[0]
            else:
                _object = _cxn.Build.create(_attributes)
        elif class_id == TCMS_CLASS_ID_CATEGORY:
            _object = _cxn.Category.create(_attributes)
        elif class_id == TCMS_CLASS_ID_CLASSIFICATION:
            _object = _cxn.Classification.create(_attributes)
        elif class_id == TCMS_CLASS_ID_COMPONENT:
            del _attributes[ATTR_CASES]
            _object = _cxn.Component.create(_attributes)
        elif class_id == TCMS_CLASS_ID_ENVIRONMENT:
            # not supported prior to TCMS server version 12.1
            _object = _cxn.Environment.create(_attributes)
            _env_id = _object[ATTR_ID]
            for _property in container_object[ATTR_PROPERTIES]:
                for _property_name, _property_value in _property.items():
                    _cxn.Environment.add_property(_env_id, _property_name, _property_value)
        elif class_id == TCMS_CLASS_ID_PLAN_TYPE:
            _object = _cxn.PlanType.create(_attributes)
        elif class_id == TCMS_CLASS_ID_PRODUCT:
            _object = _cxn.Product.create(_attributes)
        elif class_id == TCMS_CLASS_ID_TAG:
            _object = _cxn.Tag.create(_attributes)
        elif class_id == TCMS_CLASS_ID_TEST_CASE:
            _attributes[ATTR_PRODUCT] = container_object[ATTR_PRODUCT]
            _object = _cxn.TestCase.create(_attributes)
            _case_id = _object[ATTR_ID]
            if len(container_object[ATTR_CC_NOTIFICATIONS]) > 0:
                _cxn.TestCase.add_notification_cc(_case_id, container_object[ATTR_CC_NOTIFICATIONS])
            for _comment in container_object[ATTR_COMMENTS]:
                _cxn.TestCase.add_comment(_case_id, _comment)
            for _component in container_object[ATTR_COMPONENTS]:
                _cxn.TestCase.add_component(_case_id, _component)
            for _property in container_object[ATTR_PROPERTIES]:
                for _property_name, _property_value in _property.items():
                    _cxn.TestCase.add_property(_case_id, _property_name, _property_value)
            for _tag in container_object[ATTR_TAGS]:
                _cxn.TestCase.add_tag(_case_id, _tag)
        elif class_id == TCMS_CLASS_ID_TEST_CASE_STATUS:
            _object = _cxn.TestCaseStatus.create(_attributes)
        elif class_id == TCMS_CLASS_ID_TEST_EXECUTION:
            _run_id = _attributes[ATTR_RUN]
            _case_id = _attributes[ATTR_CASE]
            _tcms_execution = _cxn.TestRun.add_case(_run_id, _case_id)[0]
            _object = _cxn.TestExecution.update(_tcms_execution[ATTR_ID], _attributes)
            _execution_id = _object[ATTR_ID]
            for _comment in container_object[ATTR_COMMENTS]:
                _cxn.TestExecution.add_comment(_case_id, _comment)
            for _link in container_object[ATTR_LINKS]:
                _cxn.TestExecution.add_link(_case_id, _link)
        elif class_id == TCMS_CLASS_ID_TEST_EXECUTION_STATUS:
            _object = _cxn.TestExecutionStatus.create(_attributes)
        elif class_id == TCMS_CLASS_ID_TEST_PLAN:
            _object = _cxn.TestPlan.create(_attributes)
            _plan_id = _object[ATTR_ID]
            for _case_id in container_object[ATTR_CASES]:
                _cxn.TestPlan.add_case(_plan_id, _case_id)
            for _tag in container_object[ATTR_TAGS]:
                _cxn.TestPlan.add_tag(_plan_id, _tag)
        elif class_id == TCMS_CLASS_ID_TEST_RUN:
            _object = _cxn.TestRun.create(_attributes)
            _run_id = _object[ATTR_ID]
            for _tag in container_object[ATTR_TAGS]:
                _cxn.TestRun.add_tag(_run_id, _tag)
        elif class_id == TCMS_CLASS_ID_VERSION:
            _object = _cxn.Version.create(_attributes)
        else:
            _msg = localized_message(E_TCMS_INVALID_CLASS_ID, class_id)
            raise IssaiException(E_INTERNAL_ERROR, _msg)
        _object = _remove_unsupported_attrs(_object, _SUPPORTED_ATTRS[tcms_class_name_for_id(class_id)])
        if ATTR_ATTACHMENTS in container_object:
            _object[ATTR_ATTACHMENTS] = container_object[ATTR_ATTACHMENTS]
        return _object
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_CREATE_OBJECT_FAILED, tcms_class_name_for_id(class_id), str(_e))


def find_tcms_objects(class_id, filter_attributes):
    """
    Reads TCMS objects matching specified attributes from TCMS.
    :param int class_id: the TCMS class ID
    :param dict filter_attributes: the filter attributes
    :returns: TCMS objects found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        return _find_tcms_objects(_cxn, class_id, filter_attributes)
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, tcms_class_name_for_id(class_id), str(_e))


def find_tcms_object(class_id, filter_attributes):
    """
    Reads TCMS object matching specified attributes from TCMS.
    :param int class_id: the TCMS class ID
    :param dict filter_attributes: the filter attributes
    :returns: TCMS object; None, if no matching object is found
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS or result is not unique
    """
    try:
        _cxn = TcmsInterface.connection()
        return _find_tcms_object(_cxn, class_id, filter_attributes)
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, tcms_class_name_for_id(class_id), str(_e))


def find_product_for_tcms_object(class_id, tcms_object):
    """
    Reads owning product for specified TCMS object.
    :param int class_id: the TCMS class ID
    :param dict tcms_object: the TCMS object
    :returns: TCMS product; None, if no matching object is found
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS or result is not unique
    """
    try:
        _cxn = TcmsInterface.connection()
        if class_id == TCMS_CLASS_ID_TEST_CASE:
            _category = _cxn.Category.filter({ATTR_ID: tcms_object[ATTR_CATEGORY]})[0]
            _product_id = _category[ATTR_PRODUCT]
        else:
            _version = _cxn.Version.filter({ATTR_ID: tcms_object[ATTR_PRODUCT_VERSION]})[0]
            _product_id = _version[ATTR_PRODUCT]
        return _find_tcms_object(_cxn, TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _product_id})
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, tcms_class_name_for_id(class_id), str(_e))


def read_tcms_environments():
    """
    Reads all environments including their properties from Kiwi TCMS.
    :returns: data of all environments found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _envs = _remove_unsupported_attrs(_cxn.Environment.filter({}), _SUPPORTED_ATTRS[TCMS_CLASS_ENVIRONMENT])
        _envs_dict = dict([(_e[ATTR_ID], _e) for _e in _envs])
        for _e in _envs:
            _e[ATTR_PROPERTIES] = []
        _env_ids = [_e[ATTR_ID] for _e in _envs]
        for _prop in _cxn.Environment.properties({}):
            _envs_dict[_prop[ATTR_ENVIRONMENT]][ATTR_PROPERTIES].append({_prop[ATTR_NAME]: _prop[ATTR_VALUE]})
        return _envs
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_ENVIRONMENT, str(_e))


def read_tcms_versions_for_product(product):
    """
    Reads all software versions of a product from TCMS.
    :param dict product: TCMS product data
    :returns: TCMS data of all software versions for specified product
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _versions = _cxn.Version.filter({ATTR_PRODUCT: product[ATTR_ID]})
        return _remove_unsupported_attrs(_versions, _SUPPORTED_ATTRS[TCMS_CLASS_VERSION])
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_VERSION, str(_e))


def read_tcms_builds_for_version(versions, active_only=False):
    """
    Reads all builds of the specified product versions from TCMS.
    :param list[dict] versions: the product versions to consider
    :param bool active_only: indicates whether to consider active builds only
    :returns: TCMS data of all product builds found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _version_ids = [_v[ATTR_ID] for _v in versions]
        _filter = {f'{ATTR_VERSION}__in': _version_ids}
        if active_only:
            _filter[ATTR_IS_ACTIVE] = True
        _builds = _cxn.Build.filter(_filter)
        return _remove_unsupported_attrs(_builds, _SUPPORTED_ATTRS[TCMS_CLASS_BUILD])
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_BUILD, str(_e))


def read_tcms_plans(versions, consider_runs):
    """
    Reads test plans matching given product versions from Kiwi TCMS.
    Test plan data is enhanced with tags and attachments.
    :param list[dict] versions: the product versions from TCMS
    :param bool consider_runs: indicates whether to add a list of referenced test runs to returned plans
    :returns: data of all test plans found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _version_ids = [_version[ATTR_ID] for _version in versions]
        _filter = {f'{ATTR_PRODUCT_VERSION}__in': _version_ids}
        _plans = _remove_unsupported_attrs(_cxn.TestPlan.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_PLAN])
        for _plan in _plans:
            _plan[ATTR_ATTACHMENTS] = [_a[ATTR_URL] for _a in _cxn.TestPlan.list_attachments(_plan[ATTR_ID])]
            _plan[ATTR_TAGS] = []
            _plan[ATTR_CASES] = [_c[ATTR_ID] for _c in _cxn.TestCase.filter({ATTR_PLAN: _plan[ATTR_ID]})]
            if consider_runs:
                _plan[ATTR_RUNS] = [_r[ATTR_ID] for _r in _cxn.TestRun.filter({ATTR_PLAN: _plan[ATTR_ID]})]
        _plans_dict = dict([(_p[ATTR_ID], _p) for _p in _plans])
        _plan_ids = [_p[ATTR_ID] for _p in _plans]
        for _tag in _cxn.Tag.filter({f'{ATTR_PLAN}__in': _plan_ids}):
            _plans_dict[_tag[ATTR_PLAN]][ATTR_TAGS].append(_tag[ATTR_NAME])
        return _plans
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_PLAN, str(_e))


def read_tcms_runs(builds):
    """
    Reads test runs matching given product versions from Kiwi TCMS.
    Test run data is enhanced with tags and attachments.
    :param list[dict] builds: the product builds from TCMS
    :returns: data of all test runs found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _build_ids = [_build[ATTR_ID] for _build in builds]
        _filter = {f'{ATTR_BUILD}__in': _build_ids}
        _runs = _remove_unsupported_attrs(_cxn.TestRun.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_RUN])
        for _run in _runs:
            _run[ATTR_PROPERTIES] = []
            _run[ATTR_TAGS] = []
            _run[ATTR_EXECUTIONS] = [_e[ATTR_ID] for _e in _cxn.TestExecution.filter({ATTR_RUN: _run[ATTR_ID]})]
        _runs_dict = dict([(_r[ATTR_ID], _r) for _r in _runs])
        _run_ids = [_r[ATTR_ID] for _r in _runs]
        for _prop in _cxn.TestRun.properties({f'{ATTR_RUN}__in': _run_ids}):
            _runs_dict[_prop[ATTR_RUN]][ATTR_PROPERTIES].append({_prop[ATTR_NAME]: _prop[ATTR_VALUE]})
        for _tag in _cxn.Tag.filter({f'{ATTR_RUN}__in': _run_ids}):
            _runs_dict[_tag[ATTR_RUN]][ATTR_TAGS].append(_tag[ATTR_NAME])
        return _runs
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_RUN, str(_e))


def read_tcms_case(case_id, consider_executions, consider_history):
    """
    Reads test case with specified ID from Kiwi TCMS.
    Test case data is enhanced with attachments, comments, components, properties and tags.
    :param int case_id: the TCMS test case ID
    :param bool consider_executions: indicates whether to add a list of referenced test executions to returned case
    :param bool consider_history: indicates whether to add test case history to returned case
    :returns: TCMS test case data
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _case = _remove_unsupported_attrs(_cxn.TestCase.filter({ATTR_ID: case_id}),
                                          _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE])[0]
        _attachments = [_a[ATTR_URL] for _a in _cxn.TestCase.list_attachments(case_id)]
        _case[ATTR_ATTACHMENTS] = _attachments
        _case[ATTR_CC_NOTIFICATIONS] = _cxn.TestCase.get_notification_cc(case_id)
        _case[ATTR_COMMENTS] = _cxn.TestCase.comments(case_id)
        _case[ATTR_COMPONENTS] = [_c[ATTR_ID] for _c in _cxn.Component.filter({ATTR_CASES: case_id})]
        _filter = {ATTR_CASE: case_id}
        _case[ATTR_PROPERTIES] = [{_p[ATTR_NAME]: _p[ATTR_VALUE]} for _p in _cxn.TestCase.properties(_filter)]
        _case[ATTR_TAGS] = [_t[ATTR_NAME] for _t in _cxn.Tag.filter({ATTR_CASE: case_id})]
        if consider_executions:
            _case[ATTR_EXECUTIONS] = [_e[ATTR_ID] for _e in _cxn.TestExecution.filter({ATTR_CASE: case_id})]
        if consider_history:
            _case[ATTR_HISTORY] = _remove_unsupported_attrs(_cxn.TestCase.history(case_id, {}),
                                                            _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE_HISTORY])
        return _case
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_CASE, str(_e))


def read_tcms_cases(all_test_cases, filter_objects, consider_executions, consider_history):
    """
    Reads test runs matching given product versions from Kiwi TCMS.
    Test run data is enhanced with attachments, comments, components, properties and tags.
    :param bool all_test_cases: indicates whether to consider all test cases of a product
    :param list filter_objects: categories, if all test cases shall be considered; otherwise test plans
    :param bool consider_executions: indicates whether to add a list of referenced test executions to returned cases
    :param bool consider_history: indicates whether to add test case history to returned cases
    :returns: data of all test cases found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _filter_ids = [_object[ATTR_ID] for _object in filter_objects]
        _filter = {f'{ATTR_CATEGORY}__in': _filter_ids} if all_test_cases else {f'{ATTR_PLAN}__in': _filter_ids}
        _cases = _remove_unsupported_attrs(_cxn.TestCase.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE])
        for _case in _cases:
            _attachments = [_a[ATTR_URL] for _a in _cxn.TestCase.list_attachments(_case[ATTR_ID])]
            _case[ATTR_ATTACHMENTS] = _attachments
            _case[ATTR_CC_NOTIFICATIONS] = _cxn.TestCase.get_notification_cc(_case[ATTR_ID])
            _case[ATTR_COMMENTS] = _cxn.TestCase.comments(_case[ATTR_ID])
            _case[ATTR_COMPONENTS] = []
            _case[ATTR_PROPERTIES] = []
            _case[ATTR_TAGS] = []
            if consider_executions:
                _filter = {ATTR_CASE: _case[ATTR_ID]}
                _case[ATTR_EXECUTIONS] = [_e[ATTR_ID] for _e in _cxn.TestExecution.filter(_filter)]
            if consider_history:
                _case[ATTR_HISTORY] = _remove_unsupported_attrs(_cxn.TestCase.history(_case[ATTR_ID], {}),
                                                                _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE_HISTORY])
        _cases_dict = dict([(_c[ATTR_ID], _c) for _c in _cases])
        _case_ids = [_c[ATTR_ID] for _c in _cases]
        for _component in _cxn.Component.filter({f'{ATTR_CASES}__in': _case_ids}):
            _cases_dict[_component[ATTR_CASES]][ATTR_COMPONENTS].append(_component[ATTR_ID])
        for _prop in _cxn.TestCase.properties({f'{ATTR_CASE}__in': _case_ids}):
            _cases_dict[_prop[ATTR_CASE]][ATTR_PROPERTIES].append({_prop[ATTR_NAME]: _prop[ATTR_VALUE]})
        for _tag in _cxn.Tag.filter({f'{ATTR_CASE}__in': _case_ids}):
            _cases_dict[_tag[ATTR_CASE]][ATTR_TAGS].append(_tag[ATTR_NAME])
        return _cases
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_CASE, str(_e))


def read_tcms_executions(builds, consider_history, cases=None):
    """
    Reads test executions matching given builds and/or test cases from Kiwi TCMS.
    Test execution data is enhanced with links and properties.
    :param list[dict] builds: the product builds from TCMS; None for all builds
    :param bool consider_history: indicates whether to add test execution history to returned executions
    :param list[dict] cases: the test cases from TCMS; None for ignore
    :returns: data of all test executions found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _filter = {}
        if builds is not None:
            _build_ids = [_build[ATTR_ID] for _build in builds]
            _filter[f'{ATTR_BUILD}__in'] = _build_ids
        if cases is not None:
            _case_ids = [_c[ATTR_ID] for _c in cases]
            _filter[f'{ATTR_CASE}__in'] = _case_ids
        _executions = _remove_unsupported_attrs(_cxn.TestExecution.filter(_filter),
                                                _SUPPORTED_ATTRS[TCMS_CLASS_TEST_EXECUTION])
        _executions_dict = dict([(_e[ATTR_ID], _e) for _e in _executions])
        _executions_ids = [_e[ATTR_ID] for _e in _executions]
        for _exn in _executions:
            _execution_id = _exn[ATTR_ID]
            _exn[ATTR_COMMENTS] = []
            _exn[ATTR_PROPERTIES] = []
            _exn[ATTR_LINKS] = []
            _comments = _remove_unsupported_attrs(_cxn.TestExecution.get_comments(_execution_id),
                                                  _SUPPORTED_ATTRS[TCMS_CLASS_COMMENT])
            for _comment in _comments:
                _executions_dict[_execution_id][ATTR_COMMENTS].append(_comment)
            if consider_history:
                _exn[ATTR_HISTORY] = _remove_unsupported_attrs(_cxn.TestExecution.history(_execution_id),
                                                               _SUPPORTED_ATTRS[TCMS_CLASS_TEST_EXECUTION_HISTORY])
        for _prop in _cxn.TestExecution.properties({f'{ATTR_EXECUTION}__in': _executions_ids}):
            _executions_dict[_prop[ATTR_EXECUTION]][ATTR_PROPERTIES].append({_prop[ATTR_NAME]: _prop[ATTR_VALUE]})
        for _link in _cxn.TestExecution.get_links({f'{ATTR_EXECUTION}__in': _executions_ids}):
            _executions_dict[_link[ATTR_EXECUTION]][ATTR_LINKS].append(_link)
        return _executions
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_EXECUTION, str(_e))


def read_tcms_plan(plan, incl_descendants, incl_runs):
    """
    Reads data of all descendants of specified test plan from Kiwi TCMS.
    :param dict plan: the parent TCMS test plan data
    :param bool incl_descendants: indicates whether to add descendant test plans to returned data
    :param bool incl_runs: indicates whether to add a list of referenced test runs to returned plan
    :returns: data of parent and all descendant test plans found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _ids = [_p[ATTR_ID] for _p in _cxn.TestPlan.tree(plan[ATTR_ID])] if incl_descendants else [plan[ATTR_ID]]
        _family = _remove_unsupported_attrs(_cxn.TestPlan.filter({f'{ATTR_ID}__in': _ids}),
                                            _SUPPORTED_ATTRS[TCMS_CLASS_TEST_PLAN])
        for _plan in _family:
            _attachments = [_a[ATTR_URL] for _a in _cxn.TestPlan.list_attachments(_plan[ATTR_ID])]
            _plan[ATTR_ATTACHMENTS] = _attachments
            _plan[ATTR_TAGS] = []
            _plan[ATTR_CASES] = [_c[ATTR_ID] for _c in _cxn.TestCase.filter({ATTR_PLAN: _plan[ATTR_ID]})]
            if incl_runs:
                _plan[ATTR_RUNS] = [_r[ATTR_ID] for _r in _cxn.TestRun.filter({ATTR_PLAN: _plan[ATTR_ID]})]
        _plans_dict = dict([(_p[ATTR_ID], _p) for _p in _family])
        _plan_ids = [_p[ATTR_ID] for _p in _family]
        for _tag in _cxn.Tag.filter({f'{ATTR_PLAN}__in': _plan_ids}):
            _plans_dict[_tag[ATTR_PLAN]][ATTR_TAGS].append(_tag[ATTR_NAME])
        return _family
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_PLAN, str(_e))


def read_tcms_plan_for_execution(plan, incl_descendants):
    """
    Reads a test plan including covered test cases from TCMS in order to execute it.
    :param dict plan: the TCMS test plan ID and name
    :param bool incl_descendants: indicates whether to include descendant test plans in returned data
    :returns: all TCMS test plan data needed for execution
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _confirmed_status = TcmsInterface.confirmed_case_status_id()
        _ids = [_p[ATTR_ID] for _p in _cxn.TestPlan.tree(plan[ATTR_ID])] if incl_descendants else [plan[ATTR_ID]]
        _full_plan = _remove_unsupported_attrs(_cxn.TestPlan.filter({f'{ATTR_ID}__in': _ids}),
                                               _SUPPORTED_ATTRS[TCMS_CLASS_TEST_PLAN])
        for _plan in _full_plan:
            _plan_id = _plan[ATTR_ID]
            _plan[ATTR_ATTACHMENTS] = [_a[ATTR_URL] for _a in _cxn.TestPlan.list_attachments(_plan_id)]
            _plan[ATTR_TAGS] = [_t[ATTR_NAME] for _t in _cxn.Tag.filter({ATTR_PLAN: _plan_id})]
            _cases_filter = {ATTR_PLAN: _plan_id, ATTR_CASE_STATUS: _confirmed_status, ATTR_IS_AUTOMATED: True}
            _cases = _remove_unsupported_attrs(_cxn.TestCase.filter(_cases_filter),
                                               _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE])
            for _case in _cases:
                _case_id = _case[ATTR_ID]
                _case[ATTR_ATTACHMENTS] = [_a[ATTR_URL] for _a in _cxn.TestCase.list_attachments(_case_id)]
                _case[ATTR_TAGS] = [_t[ATTR_NAME] for _t in _cxn.Tag.filter({ATTR_CASE: _case_id})]
                _case[ATTR_PROPERTIES] = {}
                for _prop in _cxn.TestCase.properties({ATTR_CASE: _case_id}):
                    _case[ATTR_PROPERTIES][_prop[ATTR_NAME]] = _prop[ATTR_VALUE]
            _plan[ATTR_CASES] = _cases
        return _full_plan
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_PLAN, str(_e))


def read_tcms_run_tree(plans, build):
    """
    Reads data of all test runs for specified test plans from Kiwi TCMS.
    :param list[dict] plans: the TCMS test plans data
    :param dict build: the build data; None for all builds
    :returns: data of all test runs found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _filter = {f'{ATTR_PLAN}__in': [_p[ATTR_ID] for _p in plans]}
        if build is not None:
            _filter[ATTR_BUILD] = build[ATTR_ID]
        _runs = _remove_unsupported_attrs(_cxn.TestRun.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_RUN])
        for _run in _runs:
            _run[ATTR_PROPERTIES] = []
            _run[ATTR_TAGS] = []
            _run[ATTR_EXECUTIONS] = [_e[ATTR_ID] for _e in _cxn.TestExecution.filter({ATTR_RUN: _run[ATTR_ID]})]
        _runs_dict = dict([(_r[ATTR_ID], _r) for _r in _runs])
        _run_ids = [_r[ATTR_ID] for _r in _runs]
        for _prop in _cxn.TestRun.properties({f'{ATTR_RUN}__in': _run_ids}):
            _runs_dict[_prop[ATTR_RUN]][ATTR_PROPERTIES].append({_prop[ATTR_NAME]: _prop[ATTR_VALUE]})
        for _tag in _cxn.Tag.filter({f'{ATTR_RUN}__in': _run_ids}):
            _runs_dict[_tag[ATTR_RUN]][ATTR_TAGS].append(_tag[ATTR_NAME])
        return _runs
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_RUN, str(_e))


def read_test_entity_with_id(entity_type, entity_id):
    """
    Reads test case or test plan with specified ID from Kiwi TCMS.
    :param int entity_type: the test entity type (test case or test plan)
    :param int entity_id: the TCMS test entity ID
    :returns: test entity data from TCMS
    :rtype: dict
    :raises IssaiException: if test entity doesn't exist in TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        if entity_type == ENTITY_TYPE_PLAN:
            _plans = _cxn.TestPlan.filter({ATTR_ID: entity_id})
            if len(_plans) == 0:
                raise IssaiException(E_TCMS_PLAN_UNKNOWN, entity_id)
            return _remove_unsupported_attrs(_plans[0], _SUPPORTED_ATTRS[TCMS_CLASS_TEST_PLAN])
        # test case
        _cases = _cxn.TestCase.filter({ATTR_ID: entity_id})
        if len(_cases) == 0:
            raise IssaiException(E_TCMS_TEST_CASE_UNKNOWN, entity_id)
        _case = _remove_unsupported_attrs(_cases[0], _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE])
        _case[ATTR_NAME] = _case[ATTR_SUMMARY]
        return _case
    except Exception as _e:
        _class_name = TCMS_CLASS_TEST_PLAN if entity_type == ENTITY_TYPE_PLAN else TCMS_CLASS_PRODUCT
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, _class_name, str(_e))


def read_product_for_test_entity(entity_type, entity):
    """
    Reads product for specified test case or test plan from TCMS.
    :param int entity_type: the test entity type (test case or test plan)
    :param dict entity: the TCMS test entity data
    :returns: product data from TCMS
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        if entity_type == ENTITY_TYPE_PLAN:
            return _cxn.Product.filter({ATTR_ID: entity[ATTR_PRODUCT]})[0]
        # test case
        _category = _cxn.Category.filter({ATTR_ID: entity[ATTR_CATEGORY]})[0]
        return _cxn.Product.filter({ATTR_ID: _category[ATTR_PRODUCT]})[0]
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_PRODUCT, str(_e))


def read_environment_properties(env):
    """
    Reads all properties defined for specified environment.
    :param dict env: the TCMS environment data
    :returns: environment properties
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    _cxn = TcmsInterface.connection()
    _properties = {}
    for _p in _cxn.Environment.properties({ATTR_ENVIRONMENT: env[ATTR_ID]}):
        _properties[_p[ATTR_NAME]] = _p[ATTR_VALUE]
    return _properties


def tcms_master_data_status(product, master_data):
    """
    Checks the relation of master data objects loaded from file to their counterparts in TCMS
    Returns a dictionary containing the match status.
    :param dict product: the TCMS product
    :param dict master_data: the master data objects to check
    :returns: match results
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _master_data_status = {}
        _cxn = TcmsInterface.connection()
        for _data_type, _objects in master_data.items():
            if len(_objects) == 0:
                continue
            _class_id = tcms_class_id_for_master_data_type(_data_type)
            _class_status = {}
            if _class_id == TCMS_CLASS_ID_BUILD:
                for _build_id, _build in _objects.items():
                    _build_name = _build[ATTR_NAME]
                    _build_version = _build[ATTR_VERSION]
                    _tcms_build = find_tcms_object(TCMS_CLASS_ID_BUILD,
                                                   {ATTR_NAME: _build_name, ATTR_VERSION: _build_version})
                    if _tcms_build is None:
                        _class_status[_build_id] = ObjectStatus(ObjectStatus.NO_MATCH, _class_id, _build)
                    elif _tcms_build[ATTR_ID] == _build_id:
                        _class_status[_build_id] = ObjectStatus(ObjectStatus.EXACT_MATCH, _class_id, _build,
                                                                _tcms_build)
                    else:
                        _class_status[_build_id] = ObjectStatus(ObjectStatus.OTHER_NAME_MATCH, _class_id, _build,
                                                                _tcms_build)
            else:
                _name_attr = name_attribute_for_tcms_class(_class_id)
                _names = [_obj[_name_attr] for _obj in _objects.values()]
                _tcms_objects = _read_objects_by_name(_cxn, product, _class_id, _name_attr, _names)
                for _object_id, _object in _objects.items():
                    _object_name = _object[_name_attr]
                    _tcms_object = _tcms_objects.get(_object_name)
                    if _tcms_object is None:
                        _class_status[_object_id] = ObjectStatus(ObjectStatus.NO_MATCH, _class_id, _object)
                    elif _tcms_object[ATTR_ID] == _object_id:
                        _class_status[_object_id] = ObjectStatus(ObjectStatus.EXACT_MATCH, _class_id, _object,
                                                                 _tcms_object)
                    else:
                        _class_status[_object_id] = ObjectStatus(ObjectStatus.OTHER_NAME_MATCH, _class_id, _object,
                                                                 _tcms_object)
            _master_data_status[_class_id] = _class_status
        return _master_data_status
    except Exception as _e:
        raise IssaiException(E_TCMS_CHECK_MASTER_DATA_STATUS_FAILED, str(_e))


def tcms_object_status(class_id, container_object):
    """
    Checks whether container object matches TCMS object.
    :param int class_id: the container object's TCMS class ID
    :param dict container_object: the container object
    :returns: match result
    :rtype: ObjectStatus
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    _name_attr = name_attribute_for_tcms_class(class_id)
    _object_name = container_object.get(_name_attr)
    try:
        _cxn = TcmsInterface.connection()
        _tcms_objects = _read_objects_by_name(_cxn, container_object, class_id, _name_attr, [_object_name])
        if len(_tcms_objects) == 0:
            return ObjectStatus(ObjectStatus.NO_MATCH, class_id, container_object)
        _tcms_object = next(iter(_tcms_objects.values()))
        if _tcms_object[ATTR_ID] == container_object[ATTR_ID]:
            return ObjectStatus(ObjectStatus.EXACT_MATCH, class_id, container_object, _tcms_object)
        return ObjectStatus(ObjectStatus.OTHER_NAME_MATCH, class_id, container_object, _tcms_object)
    except Exception as _e:
        raise IssaiException(E_TCMS_CHECK_OBJECT_STATUS_FAILED, tcms_class_name_for_id(class_id), _object_name, str(_e))


def tcms_objects_status(class_id, container_objects, filter_attributes):
    """
    Checks whether container objects matches TCMS objects.
    :param int class_id: the TCMS class ID
    :param dict container_objects: the container objects
    :param list filter_attributes: the attribute names to use for filtering
    :returns: match result
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _objects_status = {}
        for _object_id, _object in container_objects.items():
            _filter = {}
            for _attr_name in filter_attributes:
                _filter[_attr_name] = _object[_attr_name]
            _tcms_object = _find_tcms_object(_cxn, class_id, _filter)
            if _tcms_object is None:
                _objects_status[_object_id] = ObjectStatus(ObjectStatus.NO_MATCH, class_id, _object)
                continue
            if _tcms_object[ATTR_ID] == _object_id:
                _objects_status[_object_id] = ObjectStatus(ObjectStatus.EXACT_MATCH, class_id, _object, _tcms_object)
                continue
            _objects_status[_object_id] = ObjectStatus(ObjectStatus.OTHER_NAME_MATCH, class_id, _object, _tcms_object)
        return _objects_status
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_ERROR, str(_e))


def find_matching_cases(pattern, product_id):
    """
    Reads test cases matching given name pattern and product from TCMS.
    :param str pattern: the regular expression for test case summary
    :param int product_id: the TCMS product ID
    :return: matching test cases
    :rtype: list
    """
    try:
        _cxn = TcmsInterface.connection()
        _category_ids = [_c[ATTR_ID] for _c in _cxn.Category.filter({ATTR_PRODUCT: product_id})]
        _filter = {f'{ATTR_CATEGORY}__in': _category_ids, f'{ATTR_SUMMARY}__iregex': pattern}
        return _remove_unsupported_attrs(_cxn.TestCase.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_CASE])
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_CASE, str(_e))


def find_matching_plans(pattern, product_id, version_id):
    """
    Reads test plans matching given product and name pattern from TCMS.
    :param str pattern: the regular expression for test plan name
    :param int product_id: the TCMS product ID
    :param int version_id: the TCMS version ID
    :return: matching test plans
    :rtype: list
    """
    try:
        _cxn = TcmsInterface.connection()
        _filter = {ATTR_PRODUCT: product_id, ATTR_PRODUCT_VERSION: version_id, f'{ATTR_NAME}__iregex': pattern}
        return _remove_unsupported_attrs(_cxn.TestPlan.filter(_filter), _SUPPORTED_ATTRS[TCMS_CLASS_TEST_PLAN])
    except Exception as _e:
        raise IssaiException(E_TCMS_FIND_OBJECT_FAILED, TCMS_CLASS_TEST_PLAN, str(_e))


def update_execution(execution_id, attr_values, comment):
    """
    Updates a test execution in TCMS.
    :param int execution_id: the test execution's TCMS ID
    :param dict attr_values: the test execution's attributes to update
    :param str comment: the execution comment
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _cxn.TestExecution.update(execution_id, attr_values)
        if len(comment) > 0:
            _cxn.TestExecution.add_comment(execution_id, comment)
    except Exception as _e:
        raise IssaiException(E_TCMS_UPDATE_OBJECT_FAILED, TCMS_CLASS_TEST_EXECUTION, execution_id, str(_e))


def update_run(run_id, attr_values):
    """
    Updates a test run in TCMS.
    :param int run_id: the test run's TCMS ID
    :param dict attr_values: the test run's attributes to update
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        _cxn.TestRun.update(run_id, attr_values)
    except Exception as _e:
        raise IssaiException(E_TCMS_UPDATE_OBJECT_FAILED, TCMS_CLASS_TEST_RUN, run_id, str(_e))


def upload_entity_attachment(class_id, entity_id, file_name, file_contents):
    """
    Uploads an attachment for specified TCMS entity.
    :param int class_id: the TCMS entity class ID
    :param int entity_id: the TCMS entity ID
    :param str file_name: the attachment file name without path
    :param str file_contents: the base64 encoded attachment file contents
    :raises IssaiException: if specified entity class cannot hold attachments or an error occurs
                            during communication with TCMS
    """
    try:
        _cxn = TcmsInterface.connection()
        if class_id == TCMS_CLASS_ID_TEST_CASE:
            _cxn.TestCase.add_attachment(entity_id, file_name, file_contents)
        elif class_id == TCMS_CLASS_ID_TEST_PLAN:
            _cxn.TestPlan.add_attachment(entity_id, file_name, file_contents)
        elif class_id == TCMS_CLASS_ID_TEST_RUN:
            _cxn.TestRun.add_attachment(entity_id, file_name, file_contents)
        else:
            raise IssaiException(E_TCMS_ATTACHMENTS_NOT_SUPPORTED, tcms_class_name_for_id(class_id))
    except IssaiException:
        raise
    except Exception as _e:
        raise IssaiException(E_TCMS_UPLOAD_ATTACHMENT_FAILED, file_name, tcms_class_name_for_id(class_id),
                             entity_id, str(_e))


def _find_tcms_object(rpc_cxn, class_id, filter_attributes):
    """
    Reads TCMS object matching specified attributes from TCMS.
    :_param tcms_api._ConnectionProxy rpc_cxn: the XML-RPC connection handle
    :param int class_id: the TCMS class ID
    :param dict filter_attributes: the filter attributes
    :returns: TCMS object; None, if no matching object is found
    :rtype: dict
    :raises IssaiException: if an error occurs during communication with TCMS or result is not unique
    """
    _objects = _find_tcms_objects(rpc_cxn, class_id, filter_attributes)
    _class_name = tcms_class_name_for_id(class_id)
    if len(_objects) == 0:
        return None
    if len(_objects) > 1:
        raise IssaiException(E_TCMS_AMBIGUOUS_RESULT, _class_name, str(filter_attributes))
    return _objects[0]


def _find_tcms_objects(rpc_cxn, class_id, filter_attributes):
    """
    Reads TCMS objects matching specified attributes from TCMS.
    :_param tcms_api._ConnectionProxy rpc_cxn: the XML-RPC connection handle
    :param int class_id: the TCMS class ID
    :param dict filter_attributes: the filter attributes
    :returns: TCMS objects found
    :rtype: list
    :raises IssaiException: if an error occurs during communication with TCMS
    """
    _objects = []
    if class_id == TCMS_CLASS_ID_BUILD:
        _objects = rpc_cxn.Build.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_CATEGORY:
        _objects = rpc_cxn.Category.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_CLASSIFICATION:
        _objects = rpc_cxn.Classification.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_COMPONENT:
        _objects = rpc_cxn.Component.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_ENVIRONMENT:
        # not supported prior to TCMS server version 12.1
        # noinspection PyBroadException
        try:
            _objects = rpc_cxn.Environment.filter(filter_attributes)
        except BaseException:
            return []
    elif class_id == TCMS_CLASS_ID_PLAN_TYPE:
        _objects = rpc_cxn.PlanType.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_PRIORITY:
        _objects = rpc_cxn.Priority.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_PRODUCT:
        _objects = rpc_cxn.Product.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TAG:
        _objects = rpc_cxn.Tag.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_CASE:
        _objects = rpc_cxn.TestCase.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_CASE_STATUS:
        _objects = rpc_cxn.TestCaseStatus.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_EXECUTION:
        _objects = rpc_cxn.TestExecution.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_EXECUTION_STATUS:
        _objects = rpc_cxn.TestExecutionStatus.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_PLAN:
        _objects = rpc_cxn.TestPlan.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_TEST_RUN:
        _objects = rpc_cxn.TestRun.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_USER:
        _objects = rpc_cxn.User.filter(filter_attributes)
    elif class_id == TCMS_CLASS_ID_VERSION:
        _objects = rpc_cxn.Version.filter(filter_attributes)
    else:
        _msg = localized_message(E_TCMS_INVALID_CLASS_ID, class_id)
        raise IssaiException(E_INTERNAL_ERROR, _msg)
    _class_name = tcms_class_name_for_id(class_id)
    return _remove_unsupported_attrs(_objects, _SUPPORTED_ATTRS[_class_name])


def _read_objects_by_name(rpc_cxn, product, class_id, name_attribute, object_names):
    """
    Reads all objects with specified TCMS class and IDs.
    :_param tcms_api._ConnectionProxy rpc_cxn: the XML-RPC connection handle
    :param dict product: the TCMS product
    :param int class_id: the TCMS class ID
    :param str name_attribute: the attribute that holds the name of objects of specified TCMS class
    :param list[str] object_names: the TCMS object names
    :returns: the TCMS objects found
    :rtype: dict
    """
    _filter = {f'{name_attribute}__in': object_names}
    if class_id == TCMS_CLASS_ID_BUILD:
        _versions = read_tcms_versions_for_product(product)
        if len(_versions) == 0:
            return {}
        _filter[f'{ATTR_VERSION}__in'] = [_v[ATTR_ID] for _v in _versions]
        _objects = rpc_cxn.Build.filter(_filter)
    elif class_id == TCMS_CLASS_ID_CATEGORY:
        _filter[ATTR_PRODUCT] = product[ATTR_ID]
        _objects = rpc_cxn.Category.filter(_filter)
    elif class_id == TCMS_CLASS_ID_CLASSIFICATION:
        _objects = rpc_cxn.Classification.filter(_filter)
    elif class_id == TCMS_CLASS_ID_COMPONENT:
        _filter[ATTR_PRODUCT] = product[ATTR_ID]
        _objects = rpc_cxn.Component.filter(_filter)
    elif class_id == TCMS_CLASS_ID_ENVIRONMENT:
        # _objects = _cxn.Environment.filter(_filter)
        _objects = []
    elif class_id == TCMS_CLASS_ID_PLAN_TYPE:
        _objects = rpc_cxn.PlanType.filter(_filter)
    elif class_id == TCMS_CLASS_ID_PRIORITY:
        _objects = rpc_cxn.Priority.filter(_filter)
    elif class_id == TCMS_CLASS_ID_PRODUCT:
        _objects = rpc_cxn.Product.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TAG:
        _objects = rpc_cxn.Tag.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_CASE:
        _objects = rpc_cxn.TestCase.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_CASE_STATUS:
        _objects = rpc_cxn.TestCaseStatus.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_EXECUTION:
        _objects = rpc_cxn.TestExecution.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_EXECUTION_STATUS:
        _objects = rpc_cxn.TestExecutionStatus.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_PLAN:
        _objects = rpc_cxn.TestPlan.filter(_filter)
    elif class_id == TCMS_CLASS_ID_TEST_RUN:
        _objects = rpc_cxn.TestRun.filter(_filter)
    elif class_id == TCMS_CLASS_ID_USER:
        _objects = rpc_cxn.User.filter(_filter)
    elif class_id == TCMS_CLASS_ID_VERSION:
        _filter[ATTR_PRODUCT] = product[ATTR_ID]
        _objects = rpc_cxn.Version.filter(_filter)
    else:
        _msg = localized_message(E_TCMS_INVALID_CLASS_ID, class_id)
        raise IssaiException(E_INTERNAL_ERROR, _msg)
    _result = {}
    for _obj in _objects:
        _result[_obj[name_attribute]] = _obj
    return _result


def _remove_unsupported_attrs(data, supported_attrs):
    """
    Removes attributes not supported by Issai from TCMS object(s) of a specific class.
    Converts XML-RPC datetime values to Python datetime, if applicable.
    :param dict|list|tuple data: the TCMS object(s)
    :param set supported_attrs: the attributes supported for the class
    :return: the object(s) with unsupported attributes removed
    :rtype: dict | list | tuple
    """
    if isinstance(data, dict):
        _unsupported_attrs = set()
        for _k, _v in data.items():
            if _k in supported_attrs:
                if isinstance(_v, xmlrpc.client.DateTime):
                    data[_k] = datetime.datetime.strptime(_v.value, "%Y%m%dT%H:%M:%S")
            else:
                _unsupported_attrs.add(_k)
        for _k in _unsupported_attrs:
            del data[_k]
    elif isinstance(data, (list, tuple)):
        [_remove_unsupported_attrs(_elem, supported_attrs) for _elem in data]
    return data


# Issai supported attributes of objects returned by TCMS API
_SUPPORTED_ATTRS = {
    TCMS_CLASS_BUILD: {ATTR_ID, ATTR_IS_ACTIVE, ATTR_NAME, ATTR_VERSION},
    TCMS_CLASS_CATEGORY: {ATTR_DESCRIPTION, ATTR_ID, ATTR_NAME, ATTR_PRODUCT},
    TCMS_CLASS_CLASSIFICATION: {ATTR_ID, ATTR_NAME},
    TCMS_CLASS_COMMENT: {ATTR_COMMENT, ATTR_ID, ATTR_IS_PUBLIC, ATTR_IS_REMOVED,
                         ATTR_SUBMIT_DATE, ATTR_USER_ID},
    TCMS_CLASS_COMPONENT: {ATTR_CASES, ATTR_DESCRIPTION, ATTR_ID, ATTR_INITIAL_OWNER, ATTR_INITIAL_QA_CONTACT,
                           ATTR_NAME, ATTR_PRODUCT},
    TCMS_CLASS_ENVIRONMENT: {ATTR_DESCRIPTION, ATTR_ID, ATTR_NAME, ATTR_PROPERTIES},
    TCMS_CLASS_PLAN_TYPE: {ATTR_DESCRIPTION, ATTR_ID, ATTR_NAME},
    TCMS_CLASS_PRIORITY: {ATTR_ID, ATTR_IS_ACTIVE, ATTR_VALUE},
    TCMS_CLASS_PRODUCT: {ATTR_DESCRIPTION, ATTR_ID, ATTR_NAME, ATTR_CLASSIFICATION},
    TCMS_CLASS_TAG: {ATTR_BUGS, ATTR_CASE, ATTR_ID, ATTR_NAME, ATTR_PLAN, ATTR_RUN},
    TCMS_CLASS_TEST_CASE: {ATTR_ARGUMENTS, ATTR_AUTHOR, ATTR_CASE_STATUS, ATTR_CATEGORY, ATTR_DEFAULT_TESTER,
                           ATTR_EXPECTED_DURATION, ATTR_EXTRA_LINK, ATTR_ID, ATTR_IS_AUTOMATED, ATTR_NOTES,
                           ATTR_PRIORITY, ATTR_REQUIREMENT, ATTR_REVIEWER, ATTR_SCRIPT, ATTR_SETUP_DURATION,
                           ATTR_SUMMARY, ATTR_TESTING_DURATION, ATTR_TEXT},
    TCMS_CLASS_TEST_CASE_HISTORY: {ATTR_HISTORY_CHANGE_REASON, ATTR_HISTORY_DATE, ATTR_HISTORY_ID,
                                   ATTR_HISTORY_TYPE, ATTR_HISTORY_USER_ID},
    TCMS_CLASS_TEST_CASE_STATUS: {ATTR_DESCRIPTION, ATTR_ID, ATTR_IS_CONFIRMED, ATTR_NAME},
    TCMS_CLASS_TEST_EXECUTION: {ATTR_ACTUAL_DURATION, ATTR_ASSIGNEE, ATTR_BUILD, ATTR_CASE, ATTR_EXPECTED_DURATION,
                                ATTR_ID, ATTR_RUN, ATTR_STATUS, ATTR_START_DATE, ATTR_STOP_DATE, ATTR_TESTED_BY},
    TCMS_CLASS_TEST_EXECUTION_HISTORY: {ATTR_HISTORY_CHANGE_REASON, ATTR_HISTORY_DATE, ATTR_HISTORY_USER_USERNAME},
    TCMS_CLASS_TEST_EXECUTION_STATUS: {ATTR_COLOR, ATTR_ICON, ATTR_ID, ATTR_NAME, ATTR_WEIGHT},
    TCMS_CLASS_TEST_PLAN: {ATTR_AUTHOR, ATTR_EXTRA_LINK, ATTR_ID, ATTR_IS_ACTIVE, ATTR_NAME,
                           ATTR_PARENT, ATTR_PRODUCT, ATTR_PRODUCT_VERSION, ATTR_TEXT, ATTR_TYPE},
    TCMS_CLASS_TEST_RUN: {ATTR_BUILD, ATTR_DEFAULT_TESTER, ATTR_ID, ATTR_MANAGER, ATTR_NOTES, ATTR_PLAN,
                          ATTR_PLANNED_START, ATTR_PLANNED_STOP, ATTR_START_DATE, ATTR_STOP_DATE, ATTR_SUMMARY},
    TCMS_CLASS_USER: {ATTR_EMAIL, ATTR_FIRST_NAME, ATTR_ID, ATTR_IS_ACTIVE, ATTR_IS_STAFF, ATTR_IS_SUPERUSER,
                      ATTR_LAST_NAME, ATTR_USERNAME},
    TCMS_CLASS_VERSION: {ATTR_ID, ATTR_PRODUCT, ATTR_VALUE},
}
