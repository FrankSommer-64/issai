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
Functions to import entities from files to TCMS.
"""

from issai.core.attachments import (attachment_file_path, upload_attachment_file, upload_attachment, url_file_name,
                                    url_object_id)
from issai.core.entities import *
from issai.core.task import TaskMonitor, TaskResult
from issai.core.tcms import *


def import_file(entity, options, file_path, task_monitor):
    """
    Imports test entities from file.
    To import attachments, they must be a placed in subdirectory attachments.
    The following options can be specified:
   'auto-create' - automatically creates missing master data
   'dry-run' - logs actions only, no changes in TCMS
   'include_attachments' - uploads existing attachment files
   'user-references' - specifies how to handle references to TCMS users
    :param Entity entity: the data to import
    :param dict options: the import control options
    :param str file_path: the name of the file to import including full path
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _include_attachments = options.get(OPTION_INCLUDE_ATTACHMENTS)
    _attachment_count = entity.attachment_count() if _include_attachments else 0
    _object_count = entity.object_count()
    task_monitor.set_operation_count(_object_count + _attachment_count)
    task_monitor.set_dry_run(options.get(OPTION_DRY_RUN))
    if isinstance(entity, TestCaseEntity):
        _import_case_container(entity, options, task_monitor)
        _result = TaskResult(0, localized_message(I_GUI_IMPORT_CASE_SUCCESSFUL, entity.entity_name()))
        _failure_message = localized_message(E_GUI_IMPORT_CASE_FAILED, entity.entity_name())
    elif isinstance(entity, TestPlanEntity):
        _import_plan_container(entity, options, task_monitor)
        _result = TaskResult(0, localized_message(I_GUI_IMPORT_PLAN_SUCCESSFUL, entity.entity_name()))
        _failure_message = localized_message(E_GUI_IMPORT_PLAN_FAILED, entity.entity_name())
    elif isinstance(entity, ProductEntity):
        _import_product(entity, options, task_monitor)
        _result = TaskResult(0, localized_message(I_GUI_IMPORT_PRODUCT_SUCCESSFUL, entity.entity_name()))
        _failure_message = localized_message(E_GUI_IMPORT_PRODUCT_FAILED, entity.entity_name())
    elif isinstance(entity, PlanResultEntity):
        _result = _import_plan_result_entity(entity, options, task_monitor)
        _failure_message = localized_message(E_GUI_IMPORT_PLAN_RESULT_FAILED, entity.entity_id())
    else:
        _msg = localized_message(E_INVALID_ENTITY_TYPE, entity.entity_type_id())
        raise IssaiException(E_INTERNAL_ERROR, _msg)
    if _include_attachments:
        _dry_run = options.get(OPTION_DRY_RUN)
        _input_path = os.path.dirname(file_path)
        _attachments = entity.attachments()
        for _class_id, _object_infos in _attachments.items():
            _class_name = tcms_class_name_for_id(_class_id)
            task_monitor.operations_processed(1)
            for _object_id, _urls in _object_infos.items():
                for _url in _urls:
                    if isinstance(entity, PlanResultEntity):
                        # separate handling for results
                        _file_path = attachment_file_path(_input_path, _url, TCMS_CLASS_ID_TEST_EXECUTION, _object_id)
                        _tcms_file_name = f'testexecution_{_object_id}_{_url}'
                        _case_result = entity.case_result_for_execution(_object_id)
                        _run_id = _case_result[ATTR_RUN]
                        if _dry_run:
                            if os.path.isfile(_file_path):
                                task_monitor.log(I_DRY_RUN_UPLOAD_ATTACHMENT, _class_name, _file_path)
                            else:
                                task_monitor.log(E_ATTACHMENT_MISSING, _file_path)
                            continue
                        upload_attachment_file(_file_path, _tcms_file_name, TCMS_CLASS_ID_TEST_RUN, _run_id)
                        continue
                    _file_name = url_file_name(_url)
                    _url_id = url_object_id(_url)
                    _file_path = attachment_file_path(_input_path, _file_name, _class_id, _url_id)
                    if _dry_run:
                        if os.path.isfile(_file_path):
                            task_monitor.log(I_UPLOAD_ATTACHMENT, _file_path, '-', '-')
                        else:
                            task_monitor.log(E_ATTACHMENT_MISSING, _file_path)
                        continue
                    upload_attachment(_input_path, _file_name, _url_id, _class_id, _object_id)
                    task_monitor.log(I_GUI_PROGRESS_UPLOAD_FILE, _file_name, _class_name, _object_id)
    if task_monitor.errors_detected():
        _result = TaskResult(1, _failure_message)
    return _result


def _import_plan_result_entity(plan_result, options, task_monitor):
    """
    Imports a test plan result from file.
    :param PlanResultEntity plan_result: the entity to import
    :param dict options: the import control options
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _case_results = plan_result[ATTR_TEST_CASE_RESULTS].values()
    _plan_results = plan_result[ATTR_TEST_PLAN_RESULTS].values()
    for _cr in _case_results:
        _import_case_result(_cr, options, task_monitor)
    for _pr in _plan_results:
        _import_plan_result(_pr, task_monitor)
    return TaskResult(0, localized_message(I_GUI_IMPORT_PLAN_RESULT_SUCCESSFUL, plan_result.entity_id()))


def _import_case_container(container, options, task_monitor):
    """
    Imports a test case from file.
    :param TestCaseEntity container: the entity to import
    :param dict options: the import control options
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _prepare_tcms_for_import(container, options, task_monitor)
    _import_cases(container, True, task_monitor)
    _import_executions(container, True, task_monitor)


def _import_environments(container, options, task_monitor):
    """
    Imports environments from file.
    :param SpecificationEntity container: the container holding the environments data
    :param dict options: the import control options
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    if not options.get(OPTION_INCLUDE_ENVIRONMENTS):
        return
    _container_envs = container[ATTR_ENVIRONMENTS]
    _envs_status = tcms_objects_status(TCMS_CLASS_ID_ENVIRONMENT, _container_envs, [ATTR_NAME])
    for _env_id, _env_status in _envs_status.items():
        _env = _env_status.container_object()
        _env_name = _env[ATTR_NAME]
        if _env_status.is_exact_match():
            task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_ENVIRONMENT, _env_name, _env_id)
        elif _env_status.is_name_match():
            _tcms_env = _env_status.tcms_object()
            container.replace_attribute(TCMS_CLASS_ID_ENVIRONMENT, _env_id, _tcms_env)
            task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_ENVIRONMENT, _env_name, _tcms_env[ATTR_ID])
        else:
            # environment doesn't exist in TCMS
            if not task_monitor.is_dry_run():
                _tcms_env = create_tcms_object(TCMS_CLASS_ID_ENVIRONMENT, _env)
                container.replace_attribute(TCMS_CLASS_ID_ENVIRONMENT, _env_id, _tcms_env)
            task_monitor.log(I_IMP_OBJECT_CREATED, TCMS_CLASS_ENVIRONMENT, _env_name)


def _import_cases(container, product_existed, task_monitor):
    """
    Imports test cases from file.
    :param SpecificationEntity container: the container holding the test cases data
    :param bool product_existed: indicates whether product existed prior to import
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _container_cases = container[ATTR_TEST_CASES]
    if product_existed:
        _cases_status = tcms_objects_status(TCMS_CLASS_ID_TEST_CASE, _container_cases, [ATTR_SUMMARY, ATTR_CATEGORY])
    else:
        _cases_status = {}
        for _case_id, _case in _container_cases.items():
            _cases_status[_case_id] = ObjectStatus(ObjectStatus.NO_MATCH, TCMS_CLASS_ID_TEST_CASE, _case)
    for _case_id, _case_status in _cases_status.items():
        _case = _case_status.container_object()
        _case_name = _case[ATTR_SUMMARY]
        task_monitor.operations_processed(1)
        if _case_status.is_exact_match():
            task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_TEST_CASE, _case_name, _case_id)
        elif _case_status.is_name_match():
            _tcms_case = _case_status.tcms_object()
            container.replace_attribute(TCMS_CLASS_ID_TEST_CASE, _case_id, _tcms_case)
            task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_TEST_CASE, _case_name, _tcms_case[ATTR_ID])
        else:
            # test case doesn't exist in TCMS
            if not task_monitor.is_dry_run():
                _case[ATTR_PRODUCT] = container[ATTR_PRODUCT][ATTR_ID]
                _tcms_case = create_tcms_object(TCMS_CLASS_ID_TEST_CASE, _case)
                container.replace_attribute(TCMS_CLASS_ID_TEST_CASE, _case_id, _tcms_case)
            task_monitor.log(I_IMP_OBJECT_CREATED, TCMS_CLASS_TEST_CASE, _case_name)


def _import_executions(container, product_existed, task_monitor):
    """
    Imports test executions from file.
    :param SpecificationEntity container: the container holding the test executions data
    :param bool product_existed: indicates whether product existed in TCMS prior to import
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _container_cases = container[ATTR_TEST_CASES]
    _container_executions = container[ATTR_TEST_EXECUTIONS]
    if product_existed:
        _executions_status = tcms_objects_status(TCMS_CLASS_ID_TEST_EXECUTION, _container_executions,
                                                 [ATTR_CASE, ATTR_RUN])
    else:
        _executions_status = {}
        for _execution_id, _execution in _container_executions.items():
            _executions_status[_execution_id] = ObjectStatus(ObjectStatus.NO_MATCH, TCMS_CLASS_ID_TEST_EXECUTION,
                                                             _execution)
    for _execution_id, _execution_status in _executions_status.items():
        _execution = _execution_status.container_object()
        _execution_name = _container_cases[_execution[ATTR_CASE]][ATTR_SUMMARY]
        task_monitor.operations_processed(1)
        if _execution_status.is_exact_match():
            task_monitor.log(I_IMP_EXECUTION_SKIPPED, _execution_name, _execution[ATTR_RUN], _execution_id)
        elif _execution_status.is_name_match():
            _tcms_execution = _execution_status.tcms_object()
            container.replace_attribute(TCMS_CLASS_ID_TEST_EXECUTION, _execution_id, _tcms_execution)
            task_monitor.log(I_IMP_EXECUTION_SKIPPED, _execution_name, _execution[ATTR_RUN],
                             _tcms_execution[ATTR_ID])
        else:
            # test execution doesn't exist in TCMS
            if not task_monitor.is_dry_run():
                _tcms_execution = create_tcms_object(TCMS_CLASS_ID_TEST_EXECUTION, _execution)
                container.replace_attribute(TCMS_CLASS_ID_TEST_EXECUTION, _execution_id, _tcms_execution)
            task_monitor.log(I_IMP_EXECUTION_CREATED, _execution_name, _execution[ATTR_RUN])


def _import_plans(container, product_existed, task_monitor):
    """
    Imports test plans and test runs from file.
    :param SpecificationEntity container: the container holding the test plans data to import
    :param bool product_existed: indicates whether product existed in TCMS prior to import
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _parent_ids = set()
    _container_plans = container[ATTR_TEST_PLANS]
    if product_existed:
        _plans_status = tcms_objects_status(TCMS_CLASS_ID_TEST_PLAN, _container_plans,
                                            [ATTR_NAME, ATTR_PRODUCT, ATTR_PRODUCT_VERSION])
    else:
        _plans_status = {}
        for _plan_id, _plan in _container_plans.items():
            _plans_status[_plan_id] = ObjectStatus(ObjectStatus.NO_MATCH, TCMS_CLASS_ID_TEST_PLAN, _plan)
    _plan_ids_processed = set()
    _last_status_count = -1
    while len(_plans_status) != _last_status_count:
        _last_status_count = len(_plans_status)
        for _id in _plan_ids_processed:
            del _plans_status[_id]
        _plan_ids_processed.clear()
        for _plan_id, _plan_status in _plans_status.items():
            task_monitor.operations_processed(1)
            _plan = _plan_status.container_object()
            _parent_plan = _plan.get(ATTR_PARENT)
            if _parent_plan is not None and _parent_plan not in _parent_ids and not task_monitor.is_dry_run():
                # skip child plan
                continue
            _plan_ids_processed.add(_plan_id)
            _plan_name = _plan[ATTR_NAME]
            if _plan_status.is_exact_match():
                _parent_ids.add(_plan_id)
                task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_TEST_PLAN, _plan_name, _plan_id)
                continue
            if _plan_status.is_name_match():
                _tcms_plan = _plan_status.tcms_object()
                container.replace_attribute(TCMS_CLASS_ID_TEST_PLAN, _plan_id, _tcms_plan)
                _parent_ids.add(_tcms_plan[ATTR_ID])
                task_monitor.log(I_IMP_OBJECT_SKIPPED, TCMS_CLASS_TEST_PLAN, _plan_name, _tcms_plan[ATTR_ID])
                continue
            # test plan doesn't exist in TCMS
            if not task_monitor.is_dry_run():
                _tcms_plan = create_tcms_object(TCMS_CLASS_ID_TEST_PLAN, _plan)
                container.replace_attribute(TCMS_CLASS_ID_TEST_PLAN, _plan_id, _tcms_plan)
                _parent_ids.add(_tcms_plan[ATTR_ID])
            task_monitor.log(I_IMP_OBJECT_CREATED, TCMS_CLASS_TEST_PLAN, _plan_name)


def _import_runs(container, product_existed, task_monitor):
    """
    Imports test runs and test executions from file.
    :param SpecificationEntity container: the container holding the test runs and executions data to import
    :param bool product_existed: indicates whether product existed in TCMS prior to import
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _container_plans = container[ATTR_TEST_PLANS]
    _container_runs = container[ATTR_TEST_RUNS]
    if product_existed:
        _runs_status = tcms_objects_status(TCMS_CLASS_ID_TEST_RUN, _container_runs, [ATTR_BUILD, ATTR_PLAN])
    else:
        _runs_status = {}
        for _run_id, _run in _container_runs.items():
            _runs_status[_run_id] = ObjectStatus(ObjectStatus.NO_MATCH, TCMS_CLASS_ID_TEST_RUN, _run)
    for _run_id, _run_status in _runs_status.items():
        _run = _run_status.container_object()
        _run_name = _container_plans[_run[ATTR_PLAN]][ATTR_NAME]
        task_monitor.operations_processed(1)
        if _run_status.is_exact_match():
            task_monitor.log(I_IMP_RUN_SKIPPED, _run_name, _run[ATTR_BUILD], _run_id)
            continue
        if _run_status.is_name_match():
            _tcms_run = _run_status.tcms_object()
            container.replace_attribute(TCMS_CLASS_ID_TEST_RUN, _run_id, _tcms_run)
            task_monitor.log(I_IMP_RUN_SKIPPED, _run_name, _run[ATTR_BUILD], _tcms_run[ATTR_ID])
            continue
        # test run doesn't exist in TCMS
        if not task_monitor.is_dry_run():
            _tcms_run = create_tcms_object(TCMS_CLASS_ID_TEST_RUN, _run)
            container.replace_attribute(TCMS_CLASS_ID_TEST_RUN, _run_id, _tcms_run)
        task_monitor.log(I_IMP_RUN_CREATED, _run_name, _run[ATTR_BUILD])


def _import_case_result(case_result, options, task_monitor):
    """
    Imports a single test case result from file.
    Import of test case execution output files is currently not supported.
    :param dict case_result: the test case result to import
    :param dict options: the import control options, only 'dry-run' supported here
    :param task_monitor: the progress handler
    :returns: TCMS ID of updated test execution
    :rtype: int
    :raises IssaiException: if import fails
    """
    _dry_run = options.get(OPTION_DRY_RUN)
    _case_name = case_result[ATTR_CASE_NAME]
    _execution_id = case_result[ATTR_EXECUTION]
    task_monitor.operations_processed(1)
    try:
        _execution = find_tcms_object(TCMS_CLASS_ID_TEST_EXECUTION, {ATTR_ID: _execution_id})
        if _execution is None:
            raise IssaiException(E_TCMS_SUBORDINATE_OBJECT_NOT_FOUND, TCMS_CLASS_TEST_EXECUTION, _execution_id,
                                 TCMS_CLASS_TEST_CASE, _case_name)
        _case = find_tcms_object(TCMS_CLASS_ID_TEST_CASE, {ATTR_ID: _execution[ATTR_CASE]})
        _tcms_case_name = _case[ATTR_SUMMARY]
        if _tcms_case_name != _case_name:
            raise IssaiException(E_IMP_OWNING_OBJECT_MISMATCH, TCMS_CLASS_TEST_CASE, _case_name,
                                 TCMS_CLASS_TEST_EXECUTION, _execution_id, _tcms_case_name)
        _status_id = TcmsInterface.execution_status_id_for(case_result[ATTR_STATUS])
        if _status_id is None:
            raise IssaiException(E_IMP_TCMS_OBJECT_MISSING, TCMS_CLASS_TEST_EXECUTION_STATUS, case_result[ATTR_STATUS])
        _tester_name = case_result[ATTR_TESTER_NAME]
        _tester = find_tcms_object(TCMS_CLASS_ID_USER, {ATTR_USERNAME: _tester_name})
        _current_user = TcmsInterface.current_user()
        _ref_handling = options.get(OPTION_USER_REFERENCES)
        if _tester is None:
            _tester = _current_user
            if _ref_handling == OPTION_VALUE_USER_REF_REPLACE_NEVER:
                raise IssaiException(E_IMP_USER_NOT_FOUND, _tester_name, _tester[ATTR_USERNAME])
            if _dry_run:
                task_monitor.log(I_IMP_USER_REPL_CURRENT, _tester[ATTR_USERNAME], _tester_name)
        elif _current_user[ATTR_ID] != _tester[ATTR_ID]:
            if _ref_handling == OPTION_VALUE_USER_REF_REPLACE_ALWAYS:
                _tester = _current_user
                task_monitor.log(I_IMP_USER_REPL_CURRENT, _current_user[ATTR_USERNAME], _tester_name)
    except IssaiException as _e:
        raise
    except Exception as _e:
        raise IssaiException(E_IMP_CASE_RESULT_FAILED, _case_name, str(_e))
    _result_values = {ATTR_TESTED_BY: _tester[ATTR_ID], ATTR_STATUS: _status_id,
                      ATTR_START_DATE: case_result[ATTR_START_DATE], ATTR_STOP_DATE: case_result[ATTR_STOP_DATE]}
    if not _dry_run:
        update_execution(_execution_id, _result_values, case_result[ATTR_COMMENT])
    _values = str(_result_values)
    task_monitor.log(I_IMP_EXECUTION_UPDATED, _execution_id, _case_name, _values)
    return _execution_id


def _import_plan_container(container, options, task_monitor):
    """
    Imports a test plan from file.
    :param TestPlanEntity container: the container to import
    :param dict options: the import control options
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _prepare_tcms_for_import(container, options, task_monitor)
    _import_environments(container, options, task_monitor)
    _import_cases(container, True, task_monitor)
    _import_plans(container, True, task_monitor)
    _import_runs(container, True, task_monitor)
    _import_executions(container, True, task_monitor)


def _import_plan_result(plan_result, task_monitor):
    """
    Imports a single test plan result from file.
    :param PlanResultEntity plan_result: the entity to import
    :param TaskMonitor task_monitor: the progress handler
    :returns: TCMS ID of updated test run
    :rtype: int
    :raises IssaiException: if import fails
    """
    _plan_name = plan_result[ATTR_PLAN_NAME]
    _run_id = plan_result[ATTR_RUN]
    task_monitor.operations_processed(1)
    try:
        _run = find_tcms_object(TCMS_CLASS_ID_TEST_RUN, {ATTR_ID: _run_id})
        if _run is None:
            raise IssaiException(E_TCMS_SUBORDINATE_OBJECT_NOT_FOUND, TCMS_CLASS_TEST_RUN, _run_id,
                                 TCMS_CLASS_TEST_PLAN, _plan_name)
        _plan = find_tcms_object(TCMS_CLASS_ID_TEST_PLAN, {ATTR_ID: _run[ATTR_PLAN]})
        _tcms_plan_name = _plan[ATTR_NAME]
        if _tcms_plan_name != _plan_name:
            raise IssaiException(E_IMP_OWNING_OBJECT_MISMATCH, TCMS_CLASS_TEST_PLAN, _plan_name,
                                 TCMS_CLASS_TEST_RUN, _run_id, _tcms_plan_name)
    except IssaiException as _e:
        raise
    except Exception as _e:
        raise IssaiException(E_IMP_PLAN_RESULT_FAILED, _plan_name, str(_e))
    _result_values = {ATTR_START_DATE: plan_result[ATTR_START_DATE],
                      ATTR_STOP_DATE: plan_result[ATTR_STOP_DATE]}
    _notes = plan_result.get(ATTR_NOTES)
    if _notes is not None and len(_notes) > 0:
        _result_values[ATTR_NOTES] = _notes
    _summary = plan_result[ATTR_SUMMARY]
    if _summary is not None and len(_summary) > 0:
        _result_values[ATTR_SUMMARY] = _summary
    if not task_monitor.is_dry_run():
        update_run(_run_id, _result_values)
    _values = str(_result_values)
    task_monitor.log(I_IMP_RUN_UPDATED, _run_id, _plan_name, _values)
    return _run_id


def _import_product(container, options, task_monitor):
    """
    Imports a product from file.
    :param ProductEntity container: the product container to import
    :param dict options: the import control options
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if import fails
    """
    _product_existed = _prepare_tcms_for_import(container, options, task_monitor)
    _import_environments(container, options, task_monitor)
    _import_cases(container, _product_existed, task_monitor)
    _import_plans(container, _product_existed, task_monitor)
    _import_runs(container, _product_existed, task_monitor)
    _import_executions(container, _product_existed, task_monitor)


def _prepare_master_data(container, options, task_monitor):
    """
    Tries to ensure that all TCMS master data objects exist for an import.
    :param SpecificationEntity container: the container to import
    :param dict options: the import options
    :param TaskMonitor task_monitor: the progress handler
    """
    _dry_run = options.get(OPTION_DRY_RUN)
    _auto_create = options.get(OPTION_AUTO_CREATE)
    _product = container[ATTR_PRODUCT]
    _master_data_status = tcms_master_data_status(_product, container[ATTR_MASTER_DATA])
    for _class_id, _class_status in sorted(_master_data_status.items()):
        if _class_id == TCMS_CLASS_ID_USER:
            # users need special treatment and are handled in separate function
            _prepare_user(container, options, _class_status, task_monitor)
            continue
        task_monitor.operations_processed(1)
        _class_name = tcms_class_name_for_id(_class_id)
        _name_attr = name_attribute_for_tcms_class(_class_id)
        for _object_id, _object_status in _class_status.items():
            _object = _object_status.container_object()
            _object_name = _object[_name_attr]
            if _object_status.is_exact_match():
                if _dry_run:
                    task_monitor.log(I_IMP_MD_EXACT_MATCH, _class_name, _object_name, _object_id)
                continue
            if _object_status.is_name_match():
                _tcms_object = _object_status.tcms_object()
                container.replace_attribute(_class_id, _object_id, _tcms_object)
                task_monitor.log(I_IMP_MD_REF_CHANGED, _tcms_object[ATTR_ID], _class_name,
                                 _object_name, _object_id)
                continue
            # object doesn't exist in TCMS
            if _class_id == TCMS_CLASS_ID_PRIORITY:
                # priorities cannot be created using XML-RPC
                if _dry_run:
                    task_monitor.log(E_IMP_OBJECT_MUST_EXIST, _class_name, _object_name)
                    continue
                raise IssaiException(E_IMP_OBJECT_MUST_EXIST, _class_name, _object_name)
            if (_class_id == TCMS_CLASS_ID_BUILD and _object_name == DEFAULT_BUILD) or \
                    (_class_id == TCMS_CLASS_ID_VERSION and _object_name == DEFAULT_VERSION):
                # build/version with name 'unspecified' is automatically created with a version/product
                continue
            if not _auto_create:
                if _dry_run:
                    task_monitor.log(E_IMP_MD_NO_MATCH, _class_name, _object_name)
                    continue
                raise IssaiException(E_IMP_MD_NO_MATCH, _class_name, _object_name)
            if not _dry_run:
                _tcms_object = create_tcms_object(_class_id, _object)
                container.replace_attribute(_class_id, _object_id, _tcms_object)
            task_monitor.log(I_IMP_OBJECT_CREATED, _class_name, _object_name)


def _prepare_user(container, options, user_statuses, task_monitor):
    """
    Tries to ensure that all TCMS master data objects exist for an import.
    :param SpecificationEntity container: the container to import
    :param dict options: the import options
    :param dict user_statuses: the match status of all users
    :param TaskMonitor task_monitor: the progress handler
    """
    _dry_run = options.get(OPTION_DRY_RUN)
    _ref_handling = options.get(OPTION_USER_REFERENCES)
    _replace_always = _ref_handling == OPTION_VALUE_USER_REF_REPLACE_ALWAYS
    _replace_missing = _ref_handling == OPTION_VALUE_USER_REF_REPLACE_MISSING
    _current_user = TcmsInterface.current_user()
    _current_user_id = _current_user[ATTR_ID]
    _current_user_name = _current_user[ATTR_USERNAME]
    for _user_id, _user_status in user_statuses.items():
        _user = _user_status.container_object()
        _user_name = _user[ATTR_USERNAME]
        task_monitor.operations_processed(1)
        if _replace_always:
            if _user_id == _current_user_id and _user_status.is_exact_match():
                if _dry_run:
                    task_monitor.log(I_IMP_USER_EXACT_MATCH, _user_name, _user_id)
            else:
                task_monitor.log(I_IMP_USER_REPL_CURRENT, _current_user_name, _user_name)
                container.replace_attribute(TCMS_CLASS_ID_USER, _user_id, _current_user)
            continue
        if _user_status.is_exact_match():
            if _dry_run:
                task_monitor.log(I_IMP_USER_EXACT_MATCH, _user_name, _user_id)
            continue
        if _user_status.is_name_match():
            _tcms_user = _user_status.tcms_object()
            container.replace_attribute(TCMS_CLASS_ID_USER, _user_id, _tcms_user)
            task_monitor.log(I_IMP_MD_REF_CHANGED, _tcms_user[ATTR_ID], TCMS_CLASS_USER, _user_name, _user_id)
            continue
        # user doesn't exist in TCMS
        if _replace_missing:
            container.replace_attribute(TCMS_CLASS_ID_USER, _user_id, _current_user)
            task_monitor.log(I_IMP_USER_REPL_CURRENT, _current_user_name, _user_name)
            continue
        if _dry_run:
            task_monitor.log(E_IMP_USER_NO_MATCH, _user_name, _current_user_name)
            continue
        raise IssaiException(E_IMP_USER_NO_MATCH, _user_name, _current_user_name)


def _prepare_tcms_for_import(container, options, task_monitor):
    """
    Compares product and master data in specified container against TCMS.
    Creates missing objects, if applicable and adjusts foreign key references.
    :param SpecificationEntity container: the container data
    :param dict options: the import options
    :param TaskMonitor task_monitor: the progress handler
    :returns: True, if product already exists in TCMS; False, if product has been created
    :rtype: bool
    :raises IssaiException: if an uncorrectable mismatch between container data and TCMS was detected
    """
    task_monitor.log(I_GUI_PROGRESS_CONTAINER_STATUS)
    _product_existed = _prepare_product(container, options, task_monitor)
    _prepare_master_data(container, options, task_monitor)
    return _product_existed


def _prepare_product(container, options, task_monitor):
    """
    Compares product data of specified container against TCMS.
    Creates a product, if it doesn't exist in TCMS and imported entity is a complete product.
    Adjust product references, if necessary.
    :param SpecificationEntity container: the container data
    :param dict options: the import options
    :param TaskMonitor task_monitor: the progress handler
    :returns: True, if product already exists in TCMS; False, if product has been created
    :rtype: bool
    :raises IssaiException: if an uncorrectable mismatch between container data and TCMS was detected
    """
    _dry_run = options.get(OPTION_DRY_RUN)
    _product = container[ATTR_PRODUCT]
    _product_id = _product[ATTR_ID]
    _product_name = _product[ATTR_NAME]
    _product_status = tcms_object_status(TCMS_CLASS_ID_PRODUCT, _product)
    if _product_status.is_exact_match():
        if _dry_run:
            task_monitor.log(I_IMP_MD_EXACT_MATCH, TCMS_CLASS_PRODUCT, _product_name, _product_id)
        task_monitor.operations_processed(1)
        return True
    if _product_status.is_name_match():
        _tcms_product = _product_status.tcms_object()
        task_monitor.log(I_IMP_MD_REF_CHANGED, _tcms_product[ATTR_ID], TCMS_CLASS_PRODUCT,
                         _product_name, _product_id)
        container.replace_attribute(TCMS_CLASS_ID_PRODUCT, _product_id, _tcms_product)
        task_monitor.operations_processed(1)
        return True
    # product doesn't exist in TCMS
    if not container.holds_entity_with_type(ENTITY_TYPE_PRODUCT):
        raise IssaiException(E_IMP_TCMS_OBJECT_MISSING, TCMS_CLASS_PRODUCT, _product_name)
    _classification = container.object(TCMS_CLASS_ID_CLASSIFICATION, _product[ATTR_CLASSIFICATION])
    _classification_id = _classification[ATTR_ID]
    _classification_name = _classification[ATTR_NAME]
    _classification_status = tcms_object_status(TCMS_CLASS_ID_CLASSIFICATION, _classification)
    if _classification_status.is_name_match():
        _tcms_classification = _classification_status.tcms_object()
        container.replace_attribute(TCMS_CLASS_ID_CLASSIFICATION, _classification_id, _tcms_classification)
        _product[ATTR_CLASSIFICATION] = _tcms_classification[ATTR_ID]
    elif _classification_status.is_no_match():
        if not _dry_run:
            _tcms_classification = create_tcms_object(TCMS_CLASS_ID_CLASSIFICATION, _classification)
            container.replace_attribute(TCMS_CLASS_ID_CLASSIFICATION, _classification_id, _tcms_classification)
            _product[ATTR_CLASSIFICATION] = _tcms_classification[ATTR_ID]
    if not _dry_run:
        _tcms_product = create_tcms_object(TCMS_CLASS_ID_PRODUCT, _product)
        container.replace_attribute(TCMS_CLASS_ID_PRODUCT, _product_id, _tcms_product)
    task_monitor.log(I_IMP_OBJECT_CREATED, TCMS_CLASS_PRODUCT, _product_name)
    task_monitor.operations_processed(1)
    return False
