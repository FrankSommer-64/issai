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
Functions to run a test entity.
"""

import os.path
import threading

from issai.core import *
from issai.core.attachments import download_attachments, list_attachment_files, upload_attachment_file
from issai.core.builtin_runners import builtin_runner
from issai.core.config import LocalConfig
from issai.core.entities import CaseResult, PlanResult, TestPlanEntity, PlanResultEntity
from issai.core.issai_exception import *
from issai.core.messages import *
from issai.core.task import TaskResult
from issai.core.tcms import (create_run_from_plan, find_tcms_objects, read_environment_properties,
                             read_test_entity_with_id, read_product_for_test_entity, read_tcms_cases,
                             read_tcms_executions, read_tcms_plan,
                             read_tcms_run_tree, TcmsInterface, update_execution, update_run)
from issai.core.util import platform_architecture_tag, platform_os_tag, shell_cmd


class Executable:
    """
    Represents a test runner executable, i.e. a Python function or a script.
    """

    TYPE_FUNCTION = 1
    TYPE_SCRIPT = 2

    def __init__(self, url, executable_type, executable_addr, venv_path=None, driver=None):
        """
        :param str url: the executable URL, as defined in test case
        :param int executable_type: the executable type, Python function or script
        :param str | function executable_addr: the function pointer or script name
        :param str venv_path: the optional path of virtual Python ennvironment to use
        :param str driver: the optional driver program to use for execution, for scripts only
        :rtype: Executable
        """
        self.__url = url
        self.__executable_type = executable_type
        self.__executable_addr = executable_addr
        self.__venv_path = venv_path
        self.__driver = driver

    def __str__(self):
        return self.__url

    def function_address(self):
        """
        :rtype: function
        """
        return self.__executable_addr

    def script_address(self, args):
        """
        :rtype: list
        """
        _cmd = []
        if os.path.isdir(self.__venv_path):
            _cmd.append(os.path.join(self.__venv_path, 'bin', 'python'))
        elif self.__driver is not None:
            _cmd.append(self.__driver)
        _cmd.append(self.__executable_addr)
        if len(args) > 0:
            _cmd.extend(args)
        return _cmd

    def run(self, runtime_env, *args):
        """
        Runs this executable.
        :param _Environ runtime_env: the environment variables to add to current mapping
        :param args: the optional arguments when calling the executable
        :returns: return code and stdin/stdout
        :rtype: tuple
        """
        if self.__executable_type == Executable.TYPE_FUNCTION:
            _env = os.environ.copy()
            for _k, _v in runtime_env.items():
                os.environ[_k] = str(_v)
            try:
                _func = self.function_address()
                return _func(runtime_env, self.__venv_path, *args)
            except BaseException as _e:
                return -1, '', str(_e)
            finally:
                os.environ = _env
        # script
        _cmd = self.script_address(args)
        try:
            return shell_cmd(_cmd, runtime_env)
        except BaseException as _e:
            return -1, '', str(_e)


class ExecutableTable(dict):
    """
    Holds all functions and scripts already used.
    """

    def __init__(self, local_config):
        """
        Creates a table for test runner functions and scripts.
        :param LocalConfig local_config: the local issai product configuration
        :rtype: ExecutableTable
        """
        super().__init__()
        self.__local_config = local_config
        self.__venv_path = local_config.get_str_value(CFG_PAR_RUNNER_PY_VENV_PATH)
        self.__lock = threading.Lock()

    def executable_for(self, url):
        """
        Returns the function or script matching specified URL.
        :param str url: the executable URL, as defined in test case
        :rtype: Executable
        """
        self.__lock.acquire()
        try:
            _desc = self.get(url)
            if _desc is None:
                _desc = self._descriptor_for(url)
                self[url] = _desc
            return _desc
        finally:
            self.__lock.release()

    def _descriptor_for(self, url):
        """
        Parses specified URL and returns Executable descriptor of matching function or script.
        Must be invoked holding the internal lock acquired.
        :param str url: the executable URL, as defined in test case
        :rtype: Executable
        """
        if url is None:
            raise IssaiException(E_CFG_RUNNER_SPEC_INVALID, '')
        _colon_index = url.find(':')
        if _colon_index < 0 or _colon_index == len(url) - 1:
            raise IssaiException(E_CFG_RUNNER_SPEC_INVALID, url)
        _runner_type = url[:_colon_index].lower()
        _runner_program = url[_colon_index+1:]
        if _runner_type == RUNNER_TYPE_FUNCTION:
            try:
                _runner_exe = self.__local_config.custom_function(_runner_program)
            except IssaiException as _e:
                _runner_exe = builtin_runner(_runner_program)
                if _runner_exe is None:
                    raise _e
            return Executable(url, Executable.TYPE_FUNCTION, _runner_exe, self.__venv_path)
        if _runner_type == RUNNER_TYPE_SCRIPT:
            _runner_exe = self.__local_config.custom_script(_runner_program)
            _driver = self.__local_config.get(CFG_PAR_RUNNER_TEST_DRIVER_EXE)
            return Executable(url, Executable.TYPE_SCRIPT, _runner_exe, self.__venv_path, _driver)
        raise IssaiException(E_CFG_RUNNER_SPEC_INVALID, url)


def run_tcms_plan(plan, options, local_config, task_monitor):
    """
    Runs a test plan from TCMS.
    :param dict plan: the test plan name and ID
    :param dict options: the run options. Contains the following keys:
                    'version' - the TCMS version data
                    'build' - the TCMS build data
                    'environment' - the environment properties
                    'plan-tree' - indicates whether to run descendant plans too
                    'store-result' - indicates whether to store result automatically in TCMS
                    'dry-run' - indicates whether to simulate test execution only
    :param LocalConfig local_config: the local issai product configuration
    :param TaskMonitor task_monitor: the progress handler
    :returns: execution result
    :rtype: TaskResult
    """
    _working_path = local_config.get_str_value(CFG_PAR_RUNNER_WORKING_PATH)
    if _working_path is None or not os.path.isdir(_working_path):
        raise IssaiException(E_RUN_WORKING_PATH_MISSING, CFG_PAR_RUNNER_WORKING_PATH)
    if not os.path.isdir(_working_path):
        raise IssaiException(E_RUN_WORKING_PATH_INVALID, _working_path)
    _version = options.get(OPTION_VERSION)
    _build = options.get(OPTION_BUILD)
    # create TestPlan entity from TCMS data
    _plan_entity = plan_entity_from_tcms(plan, options, local_config, task_monitor)
    task_monitor.set_operation_count(_plan_entity.runnable_case_count() + 1)
    task_monitor.operations_processed(1)
    # create initial set of environment variables
    _env_vars = initial_env_vars(local_config, options)
    # download attachments, if applicable
    _attachments = _plan_entity.attachments()
    if len(_attachments) > 0:
        _att_patterns = local_config.get_list_value(CFG_PAR_TCMS_SPEC_ATTACHMENTS)
        if _att_patterns is not None:
            download_attachments(_plan_entity, _working_path, task_monitor, _att_patterns)
    _env_vars[ENVA_ATTACHMENTS_PATH] = os.path.join(_working_path, ATTACHMENTS_ROOT_DIR)
    _env_vars[ENVA_ISSAI_USERNAME] = TcmsInterface.current_user()[ATTR_USERNAME]
    # run test plan
    _exe_table = ExecutableTable(local_config)
    _plan_result = _run_plan(_plan_entity, [-1], _exe_table, local_config, _env_vars, task_monitor)[0]
    _att_patterns = local_config.get_list_value(CFG_PAR_TCMS_RESULT_ATTACHMENTS)
    # store test result
    store_plan_results(_plan_result, _plan_entity, local_config, _att_patterns, _working_path,
                       options.get(OPTION_STORE_RESULT))
    _rc = _plan_result.result_status()
    # _summary = localized_message(I_GUI_RUN_PLAN_SUCCESSFUL, _plan_name)
    return TaskResult(_rc, '%s%s%s' % (_plan_result.get_attr_value(ATTR_SUMMARY), os.linesep,
                                       _plan_result.get_attr_value(ATTR_NOTES)))


def run_offline_plan(plan_entity, options, local_config, attachment_path, task_monitor):
    """
    Runs a test plan read from file.
    :param TestPlanEntity plan_entity: the test plan entity
    :param dict options: the run options. Contains the following keys:
                         'version' - the TCMS version data,
                         'build' - the TCMS build data,
                         'store-result' - indicates whether to store result automatically in TCMS
    :param LocalConfig local_config: the local issai product configuration
    :param LiteralString|str|bytes attachment_path: the directory where to look for attachment files
    :param TaskMonitor task_monitor: the progress handler
    :returns: execution result
    :rtype: TaskResult
    """
    _working_path = local_config.get_str_value(CFG_PAR_RUNNER_WORKING_PATH)
    if _working_path is None or not os.path.isdir(_working_path):
        raise IssaiException(E_RUN_WORKING_PATH_MISSING, CFG_PAR_RUNNER_WORKING_PATH)
    if not os.path.isdir(_working_path):
        raise IssaiException(E_RUN_WORKING_PATH_INVALID, _working_path)
    _version = options.get(OPTION_VERSION)
    _build = options.get(OPTION_BUILD)
    task_monitor.set_operation_count(plan_entity.runnable_executions_count() + 1)
    task_monitor.operations_processed(1)
    # create initial set of environment variables
    _env_vars = initial_env_vars(local_config, options)
    _env_vars[ENVA_ATTACHMENTS_PATH] = attachment_path
    _users = plan_entity.master_data_of_type(ATTR_TCMS_USERS)
    _env_vars[ENVA_ISSAI_USERNAME] = DEFAULT_USER_NAME if len(_users) == 0 else _users[0][ATTR_USERNAME]
    # run test plan
    _exe_table = ExecutableTable(local_config)
    _plan_result = _run_plan(plan_entity, [-1], _exe_table, local_config, _env_vars, task_monitor)[0]
    _att_patterns = local_config.get_list_value(CFG_PAR_TCMS_RESULT_ATTACHMENTS)
    # store test result
    store_plan_results(_plan_result, plan_entity, local_config, _att_patterns, _working_path,
                       options.get(OPTION_STORE_RESULT))
    _rc = _plan_result.result_status()
    return TaskResult(_rc, '%s%s%s' % (_plan_result.get_attr_value(ATTR_SUMMARY), os.linesep,
                                       _plan_result.get_attr_value(ATTR_NOTES)))


def _run_plan(plan_entity, plan_ids, executable_table, local_config, env_vars, task_monitor):
    """
    Runs a test plan.
    :param TestPlanEntity plan_entity: the test plan, eventually including descendants
    :param list plan_ids: the TCMS IDs of all siblings in the test plan
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local issai product configuration
    :param dict env_vars: the environment variables to use in test execution
    :param TaskMonitor task_monitor: the progress handler
    :returns: execution results
    :rtype: list
    """
    # run entity assistant for top level test plan
    if len(plan_ids) == 1 and plan_ids[0] == -1:
        _run_assistant(CFG_PAR_RUNNER_ENTITY_ASSISTANT, ASSISTANT_ACTION_INIT, executable_table,
                       local_config, env_vars)
    _results = []
    _child_ids = []
    _essential_props = _essential_properties_for(local_config, ENTITY_TYPE_PLAN)
    for _plan_id in plan_ids:
        if _plan_id < 0:
            _plan_id = plan_entity.entity_id()
        _plan = plan_entity.get_part(ATTR_TEST_PLANS, _plan_id)
        task_monitor.log(False, I_RUN_RUNNING_PLAN, _plan[ATTR_NAME])
        _plan_result = PlanResult(_plan[ATTR_RUN], _plan_id, _plan[ATTR_NAME])
        _results.append(_plan_result)
        _plan_result.mark_start()
        # check whether test plan is runnable on local machine
        if _skip_entity_on_local_machine(ENTITY_TYPE_PLAN, plan_entity.is_plan_active(_plan_id),
                                         plan_entity.get_plan_tags(_plan_id), _plan_result):
            _plan_result.mark_end()
            return _results
        # add plan properties to runtime environment
        _plan_env = env_vars.copy()
        for _prop_k, _prop_v in plan_entity.get_plan_properties(_plan_id, _essential_props).items():
            _plan_env[_prop_k] = str(_prop_v)
        # invoke plan setup function
        _run_assistant(CFG_PAR_RUNNER_PLAN_ASSISTANT, ASSISTANT_ACTION_INIT, executable_table,
                       local_config, _plan_env)
        # run all test cases in plan
        for _case_id in _plan[ATTR_CASES]:
            _case_result = _run_case(plan_entity, _case_id, executable_table, local_config, _plan_env, task_monitor)
            _plan_result.add_case_result(_case_result)
        # invoke plan cleanup function
        _run_assistant(CFG_PAR_RUNNER_PLAN_ASSISTANT, ASSISTANT_ACTION_CLEANUP, executable_table,
                       local_config, _plan_env)
        _child_ids.extend(plan_entity.plan_child_ids(_plan_id))
        _plan_result.mark_end()
    if len(_child_ids) > 0:
        _child_results = _run_plan(plan_entity, _child_ids, executable_table, local_config, env_vars, task_monitor)
        for i in range(0, len(_child_ids)):
            _results[i].add_plan_result(_child_results[i])
    if len(plan_ids) == 1 and plan_ids[0] == -1:
        _run_assistant(CFG_PAR_RUNNER_ENTITY_ASSISTANT, ASSISTANT_ACTION_CLEANUP, executable_table,
                       local_config, env_vars)
    return _results


def _run_case(plan_entity, case_id, executable_table, local_config, runtime_env, task_monitor):
    """
    Runs a single test case.
    :param TestPlanEntity plan_entity: the test plan, eventually including descendants
    :param int case_id: the TCMS test case ID
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local issai product configuration
    :param dict runtime_env: the environment variables to use in test execution
    :param TaskMonitor task_monitor: the progress handler
    :returns: execution result
    :rtype: CaseResult
    """
    _case = plan_entity.get_part(ATTR_TEST_CASES, case_id)
    _execution_id = _case[ATTR_EXECUTION]
    _execution = plan_entity.get_part(ATTR_TEST_EXECUTIONS, _execution_id)
    _run_id = _execution[ATTR_RUN]
    task_monitor.log(False, I_RUN_RUNNING_CASE, _case[ATTR_SUMMARY])
    _case_result = CaseResult(_execution_id, _run_id, case_id, _case[ATTR_SUMMARY])
    _case_result.mark_start()
    # check whether test case is runnable on local machine
    if _skip_entity_on_local_machine(ENTITY_TYPE_CASE, _case[ATTR_IS_AUTOMATED], _case[ATTR_TAGS], _case_result):
        _case_result.mark_end()
        return _case_result
    _script = _case[ATTR_SCRIPT]
    if len(_script) == 0:
        _case_result[ATTR_STATUS] = RESULT_STATUS_ERROR
        _case_result[ATTR_COMMENT] = localized_message(E_RUN_CASE_SCRIPT_MISSING, _case[ATTR_SUMMARY])
        _case_result.mark_end()
        task_monitor.log(False, E_RUN_CASE_SCRIPT_MISSING, _case[ATTR_SUMMARY])
        task_monitor.operations_processed(1)
        return _case_result
    # add case properties to runtime env
    _case_env = runtime_env.copy()
    _essential_props = _essential_properties_for(local_config, ENTITY_TYPE_CASE)
    for _prop_k, _prop_v in plan_entity.get_case_properties(case_id, _essential_props).items():
        _case[_prop_k] = str(_prop_v)
    # run test case
    _args = _case[ATTR_ARGUMENTS]
    _executable = executable_table.executable_for(_script)
    _rc, _stdout, _stderr = _executable.run(runtime_env, _args)
    # save output to file
    _case = plan_entity.get_part(ATTR_TEST_CASES, case_id)
    _output_path = os.path.join(local_config.get_str_value(CFG_PAR_RUNNER_WORKING_PATH),
                                ATTACHMENTS_ROOT_DIR, ATTACHMENTS_EXECUTION_DIR, str(_case[ATTR_EXECUTION]))
    os.makedirs(_output_path, exist_ok=True)
    _output_file_path = os.path.join(_output_path, local_config.output_log())
    with open(_output_file_path, 'w') as _output_file:
        _output_file.write(_stdout)
        _output_file.write(_stderr)
        _output_file.close()
    _result_status = RESULT_STATUS_PASSED if _rc == 0 else RESULT_STATUS_FAILED
    _case_result.mark_end()
    _case_result.set_attr_value(ATTR_STATUS, _result_status)
    _case_result.set_attr_value(ATTR_TESTER_NAME, runtime_env[ENVA_ISSAI_USERNAME])
    return _case_result


def plan_entity_from_tcms(plan, options, local_config, task_monitor):
    """
    Creates TestPlan entity from TCMS.
    :param dict plan: the test plan name and ID
    :param dict options: the run options
    :param LocalConfig local_config: the local issai product configuration
    :param TaskMonitor task_monitor: the progress handler
    :returns: test plan entity
    :rtype: TestPlanEntity
    :raises IssaiException: if an error occurs during TCMS access
    """
    _plan_id = plan[ATTR_ID]
    _plan_name = plan[ATTR_NAME]
    task_monitor.log(False, I_EXP_FETCH_PLAN, _plan_name)
    # read plan and cases from TCMS
    _plan = read_test_entity_with_id(ENTITY_TYPE_PLAN, _plan_id)
    _product = read_product_for_test_entity(ENTITY_TYPE_PLAN, _plan)
    _plan_entity = TestPlanEntity(_plan_id, _plan[ATTR_NAME])
    _plan_entity.fill_product_data(_product)
    _version = options.get(OPTION_VERSION)
    _build = options.get(OPTION_BUILD)
    _classifications = find_tcms_objects(TCMS_CLASS_ID_CLASSIFICATION, {ATTR_ID: _product[ATTR_CLASSIFICATION]})
    _execution_statuses = find_tcms_objects(TCMS_CLASS_ID_TEST_EXECUTION_STATUS, {})
    _plan_entity.add_master_data(ATTR_PRODUCT_CLASSIFICATIONS, _classifications)
    _plan_entity.add_master_data(ATTR_PRODUCT_VERSIONS, _version)
    _plan_entity.add_master_data(ATTR_PRODUCT_BUILDS, _build)
    _plan_entity.add_master_data(ATTR_EXECUTION_STATUSES, _execution_statuses)
    _full_plan = read_tcms_plan(plan, options.get(OPTION_PLAN_TREE), False)
    _plan_entity.add_tcms_plans(_full_plan)
    _runs = read_tcms_run_tree(_full_plan, _build)
    _created_runs = []
    for _plan_member in _full_plan:
        _member_id = _plan_member[ATTR_ID]
        _run_exists = False
        for _run in _runs:
            if _run[ATTR_PLAN] == _member_id:
                _run_exists = True
                break
        if _run_exists:
            continue
        _spec_mgmt = local_config.get_str_value(CFG_PAR_TCMS_SPEC_MANAGEMENT)
        if _spec_mgmt is None or _spec_mgmt != 'auto':
            raise IssaiException(E_RUN_CANNOT_CREATE_TEST_RUN, _plan_member[ATTR_NAME])
        _run = create_run_from_plan(_plan_member, _build)
        _created_runs.append(_run)
    _runs.extend(_created_runs)
    _plan_entity.add_tcms_runs(_runs)
    task_monitor.log(False, I_EXP_FETCH_PLAN_CASES, _plan_name)
    _plan_cases = read_tcms_cases(False, _full_plan, True, False)
    _plan_entity.add_tcms_cases(_plan_cases)
    _plan_entity.add_tcms_executions(read_tcms_executions([_build], False, _plan_cases), True)
    return _plan_entity


def initial_env_vars(local_config, options):
    """
    Creates and returns basic set of environment variables for test execution.
    :param LocalConfig local_config: the local issai product configuration
    :param dict options: the run options
    :returns: basic environment variables
    :rtype: MutableMapping
    :raises IssaiException: if local configuration doesn't specify a valid product source path
    """
    _runtime_env = os.environ.copy()
    _enva_mapping = local_config.get_value(CFG_GROUP_ENV)
    if _enva_mapping is not None:
        for _enva_name, _enva_value in _enva_mapping.items():
            if _enva_value.startswith('{'):
                _cfg_par_name = _enva_value[1:-1]
                _enva_value = local_config.get_str_value(_cfg_par_name)
                if _enva_value is None:
                    continue
            _runtime_env[_enva_name] = _enva_value
    _source_path = local_config.get_str_value(CFG_PAR_PRODUCT_SOURCE_PATH)
    if _source_path is None:
        raise IssaiException(E_RUN_SOURCE_PATH_MISSING, CFG_PAR_PRODUCT_SOURCE_PATH)
    if not os.path.isdir(_source_path):
        raise IssaiException(E_RUN_SOURCE_PATH_INVALID, _source_path)
    _py_path = _runtime_env.get(ENVA_PYTHON_PATH)
    if _py_path is None or len(_py_path) == 0:
        _runtime_env[ENVA_PYTHON_PATH] = _source_path
    else:
        _runtime_env[ENVA_PYTHON_PATH] = f'{_source_path}:{_py_path}'
    _environment = options.get(OPTION_ENVIRONMENT)
    if _environment is not None:
        _env_props = read_environment_properties(_environment)
        for _k, _v in _env_props.items():
            _runtime_env[_k] = str(_v)
    return _runtime_env


def store_plan_results(plan_result, plan_entity, local_config, attachment_patterns, working_path, store_in_tcms):
    if store_in_tcms:
        _plan_results = plan_result.plan_results()
        for _pr in _plan_results:
            _run_id = _pr.get_attr_value(ATTR_RUN)
            _vals = {ATTR_START_DATE: _pr.get_attr_value(ATTR_START_DATE),
                     ATTR_STOP_DATE: _pr.get_attr_value(ATTR_STOP_DATE)}
            _notes = _pr.get_attr_value(ATTR_NOTES)
            _summary = _pr.get_attr_value(ATTR_SUMMARY)
            if len(_notes) > 0:
                _vals[ATTR_NOTES] = _notes
            if len(_summary) > 0:
                _vals[ATTR_SUMMARY] = _summary
            update_run(_run_id, _vals)
            for _cr in _pr.get_attr_value(ATTR_CASE_RESULTS):
                _custom_status_name = local_config.custom_execution_status(_cr.get_attr_value(ATTR_STATUS))
                _status_id = plan_entity.execution_status_id_of(_custom_status_name)
                _exec_id = _cr.get_attr_value(ATTR_EXECUTION)
                _vals = {ATTR_START_DATE: _cr.get_attr_value(ATTR_START_DATE),
                         ATTR_STOP_DATE: _cr.get_attr_value(ATTR_STOP_DATE), ATTR_STATUS: _status_id}
                update_execution(_exec_id, _vals, _cr.get_attr_value(ATTR_COMMENT))
                if attachment_patterns is not None and len(attachment_patterns) > 0:
                    for _file_path in list_attachment_files(working_path, TCMS_CLASS_ID_TEST_EXECUTION, _exec_id):
                        _file_name = os.path.basename(_file_path)
                        _tcms_file_name = f'testexecution_{_exec_id}_{_file_name}'
                        upload_attachment_file(_file_path, _tcms_file_name, TCMS_CLASS_ID_TEST_RUN, _run_id)
    else:
        # export results to working path
        for _cr in plan_result.case_results():
            if attachment_patterns is not None and len(attachment_patterns) > 0:
                _exec_id = _cr.get_attr_value(ATTR_EXECUTION)
                for _file_path in list_attachment_files(working_path, TCMS_CLASS_ID_TEST_EXECUTION, _exec_id):
                    _file_name = os.path.basename(_file_path)
                    if local_config.upload_patterns_match(_file_name):
                        _cr[ATTR_OUTPUT_FILES].append(_file_name)
        _pr = PlanResultEntity.from_result(plan_result, plan_entity)
        _plan_id = _pr.entity_id()
        _output_file_path = os.path.join(working_path, f'testplan_{_plan_id}.toml')
        _pr.to_file(_output_file_path)


def _tags_exclude_platform_os(tags):
    """
    Indicates whether given list of tags contains at least one tag with operating system prefix ('os.') but none
    matching current OS.
    :param list tags: the tags attached to a test plan or case
    :returns: True, if tags prohibit running the test plan or case on local operating system
    :rtype: bool
    """
    _os_tags = [_t for _t in tags if _t.startswith(PLATFORM_OS_PREFIX)]
    if len(_os_tags) == 0:
        return False
    return platform_os_tag() not in _os_tags


def _tags_exclude_platform_arch(tags):
    """
    Indicates whether given list of tags contains at least one tag with CPU architecture prefix ('arch.') but none
    matching current CPU.
    :param list tags: the tags attached to a test plan or case
    :returns: True, if tags prohibit running the test plan or case on local CPU architecture
    :rtype: bool
    """
    _arch_tags = [_t for _t in tags if _t.startswith(PLATFORM_ARCH_PREFIX)]
    if len(_arch_tags) == 0:
        return False
    return platform_architecture_tag() not in _arch_tags


def _skip_entity_on_local_machine(entity_type, runnable_flag, entity_tags, result):
    """
    Checks whether given test plan or case is runnable on local machine. Enters reason into specified result, if entity
    is not runnable.
    :param int entity_type: the entity type (test plan or case)
    :param bool runnable_flag: the entities' active status (for test plans) or automated status (for test cases)
    :param list entity_tags: the entity tags
    :param ResultContainer result: the entity result
    :returns: True, if entity is not runnable on local machine
    :rtype: bool
    """
    _entity_name = entity_type_name(entity_type)
    if not runnable_flag:
        result[ATTR_SUMMARY] = localized_message(I_RUN_ENTITY_SKIPPED, _entity_name)
        if entity_type == ENTITY_TYPE_PLAN:
            result[ATTR_NOTES] = localized_message(I_RUN_PLAN_NOT_ACTIVE)
        else:
            result[ATTR_NOTES] = localized_message(I_RUN_CASE_NOT_AUTOMATED)
        return True
    if _tags_exclude_platform_os(entity_tags):
        result[ATTR_SUMMARY] = localized_message(I_RUN_ENTITY_SKIPPED, _entity_name)
        result[ATTR_NOTES] = localized_message(I_RUN_ENTITY_NOT_FOR_LOCAL_OS, _entity_name)
        return True
    if _tags_exclude_platform_arch(entity_tags):
        result[ATTR_SUMMARY] = localized_message(I_RUN_ENTITY_SKIPPED, _entity_name)
        result[ATTR_NOTES] = localized_message(I_RUN_ENTITY_NOT_FOR_LOCAL_ARCH, _entity_name)
        return True
    return False


def _run_assistant(name, action, executable_table, local_config, runtime_env):
    """
    Executes test entity initialization or cleanup function/script.
    :param str name: the assistant's name, i.e. its TOML key in the runner section of product configuration
    :param int action: the action (1 for init, -1 for cleanup)
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local configuration
    :param dict runtime_env: the runtime environment to use
    :raises IssaiException: if the assistant fails
    """
    _assistant = local_config.get(name)
    if _assistant is None:
        return
    _executable = executable_table.executable_for(_assistant)
    _executable.run(runtime_env, action)


def _essential_properties_for(local_config, entity_type):
    """
    Returns names of entity properties that are transferred to runtime environment during execution.
    Names defined in variable runner.issai-entity-properties are always returned, for test cases variable
    runner.issai-case-properties is evaluated, for test plans runner.issai-plan-properties.
    :param LocalConfig local_config: the local issai configuration
    :param int entity_type: the entity type, test case or test plan
    :returns: name of essential properties
    :rtype: set
    """
    _essential_props = set()
    _fill_essential_props(_essential_props, local_config, CFG_PAR_RUNNER_ISSAI_ENTITY_PROPS)
    if entity_type == ENTITY_TYPE_PLAN:
        _fill_essential_props(_essential_props, local_config, CFG_PAR_RUNNER_ISSAI_PLAN_PROPS)
    else:
        _fill_essential_props(_essential_props, local_config, CFG_PAR_RUNNER_ISSAI_CASE_PROPS)
    return _essential_props


def _fill_essential_props(property_set, local_config, cfg_par):
    """
    Adds names of test case or plan specific properties that are transferred to runtime environment during execution
    to given property set.
    :param set property_set: the set where to store the names found
    :param LocalConfig local_config: the local issai configuration
    :param str cfg_par: the TOML key in the local issai configuration
    """
    _props = local_config.get_value(cfg_par)
    if _props is not None:
        for _p in _props:
            property_set.add(_p)
