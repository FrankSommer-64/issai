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
import shutil
import threading

from issai.core import *
from issai.core.attachments import download_attachments, list_case_result_files, upload_attachment_file
from issai.core.builtin_runners import builtin_runner
from issai.core.config import LocalConfig
from issai.core.entities import CaseResult, PlanResult, TestPlanEntity, PlanResultEntity
from issai.core.issai_exception import *
from issai.core.messages import *
from issai.core.task import TaskResult
from issai.core.tcms import (create_run_from_plan, create_tcms_object, find_tcms_objects,
                             read_test_entity_with_id, read_product_for_test_entity, read_tcms_cases,
                             read_tcms_executions, read_tcms_plan,
                             read_tcms_run_tree, TcmsInterface, update_execution, update_run)
from issai.core.util import platform_architecture_tag, platform_os_tag, shell_cmd, PropertyMatrix


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
        :param str venv_path: the optional path of virtual Python environment to use
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
        :returns: return code, stdout, stderr
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
        self.__venv_path = local_config.get_value(CFG_PAR_RUNNER_PYTHON_VENV_PATH)
        self.__lock = threading.Lock()

    def executable_for(self, url):
        """
        Returns the function or script matching specified URL.
        :param str url: the executable URL, as defined in test case
        :rtype: Executable
        :raises IssaiException: if URL is malformed or specified function doesn't exist
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
        :raises IssaiException: if URL is malformed or specified function doesn't exist
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
    # noinspection PyBroadException
    task_monitor.check_abort()
    try:
        _working_path = local_config.runner_working_path()
        # create TestPlan entity from TCMS data
        task_monitor.set_dry_run(options.get(OPTION_DRY_RUN))
        _plan_entity = plan_entity_from_tcms(plan, options, task_monitor)
        task_monitor.set_operation_count(_plan_entity.runnable_case_count() + 1)
        task_monitor.operations_processed(1)
        # create initial set of environment variables
        _env_vars = initial_env_vars(local_config, _working_path, TcmsInterface.current_user()[ATTR_USERNAME])
        # download attachments, if applicable
        _attachments = _plan_entity.attachments()
        if len(_attachments) > 0:
            _att_patterns = local_config.get_list_value(CFG_PAR_TCMS_SPEC_ATTACHMENTS)
            if _att_patterns is not None:
                download_attachments(_plan_entity, _working_path, task_monitor, _att_patterns)
        # run test plan
        _plan_result = _run_ancestor_plan(_plan_entity, options, local_config, _env_vars, task_monitor)
        # store test result
        store_plan_results(_plan_result, _plan_entity, options, local_config, _working_path, task_monitor)
        return execution_task_result(plan[ATTR_NAME], _plan_result)
    except BaseException as _e:
        return TaskResult(TASK_FAILED, str(_e))


def run_offline_plan(plan_entity, options, local_config, attachment_path, task_monitor):
    """
    Runs a test plan read from file.
    :param TestPlanEntity | Entity plan_entity: the test plan entity
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
    task_monitor.check_abort()
    # noinspection PyBroadException
    try:
        _working_path = local_config.runner_working_path()
        task_monitor.set_operation_count(plan_entity.runnable_case_count() + 1)
        task_monitor.operations_processed(1)
        task_monitor.set_dry_run(options.get(OPTION_DRY_RUN))
        # create initial set of environment variables
        _users = plan_entity.master_data_of_type(ATTR_TCMS_USERS)
        _user_name = DEFAULT_USER_NAME if len(_users) == 0 else _users[0][ATTR_USERNAME]
        _env_vars = initial_env_vars(local_config, _working_path, _user_name, attachment_path)
        # run test plan
        task_monitor.check_abort()
        _plan_result = _run_ancestor_plan(plan_entity, options, local_config, _env_vars, task_monitor)
        # store test result
        store_plan_results(_plan_result, plan_entity, options, local_config, _working_path, task_monitor)
        return execution_task_result(plan_entity.entity_name(), _plan_result)
    except BaseException as _e:
        return TaskResult(TASK_FAILED, str(_e))


def _run_ancestor_plan(plan_entity, options, local_config, env_vars, task_monitor):
    """
    Runs a top level test plan.
    :param TestPlanEntity plan_entity: the test plan, eventually including descendants
    :param LocalConfig local_config: the local issai product configuration
    :param dict env_vars: the environment variables to use in test execution
    :param TaskMonitor task_monitor: the progress handler
    :returns: execution result; None, if plan is not runnable
    :rtype: PlanResult
    """
    task_monitor.check_abort()
    clear_result_path(local_config)
    _plan_id = plan_entity.entity_id()
    _plan_name = plan_entity.entity_name()
    _version = plan_entity.master_data_of_type(ATTR_PRODUCT_VERSIONS)[0]
    _build = plan_entity.master_data_of_type(ATTR_PRODUCT_BUILDS)[0]
    _exe_table = ExecutableTable(local_config)
    _env_opt = options.get(OPTION_ENVIRONMENT)
    _result = PlanResult.from_entity(plan_entity, _plan_id)
    _result.mark_start()
    # noinspection PyBroadException
    try:
        # skip plan, if not runnable
        if _skip_entity_on_local_machine(plan_entity, ENTITY_TYPE_PLAN, _plan_id, task_monitor):
            return None
        # eventually run initialization for top level plan
        _run_assistant(CFG_PAR_RUNNER_ENTITY_ASSISTANT, ASSISTANT_ACTION_INIT, _plan_name,
                       _exe_table, local_config, env_vars, task_monitor)
        # run plan
        _prop_matrix = PropertyMatrix()
        _env_properties = _read_env_properties(_env_opt)
        for _property in _env_properties:
            _property_name, _property_value = next(iter(_property.items()))
            if isinstance(_property_value, list):
                _prop_matrix.add(_property_name, _property_value)
            else:
                env_vars[_property_name] = _property_value
        if _prop_matrix.is_empty():
            _result = _run_plan(plan_entity, _plan_id, _exe_table, local_config, env_vars, task_monitor, _prop_matrix)
        else:
            for _props in _prop_matrix:
                _prop_infos = []
                for _enva_name, _enva_value in _props:
                    env_vars[_enva_name] = _enva_value
                    _prop_infos.append(f'{_enva_name}="{_enva_value}"')
                task_monitor.log(I_RUN_RUNNING_ENV, ','.join(_prop_infos))
                _res = _run_plan(plan_entity, _plan_id, _exe_table, local_config, env_vars, task_monitor, _prop_matrix)
                _result.merge_matrix_result(_res)
        # eventually run cleanup for top level plan
        _run_assistant(CFG_PAR_RUNNER_ENTITY_ASSISTANT, ASSISTANT_ACTION_CLEANUP, _plan_name,
                       _exe_table, local_config, env_vars, task_monitor)
    except BaseException as _e:
        # we'll land here in case of assistant errors only
        _result.append_attr_value(ATTR_SUMMARY, localized_message(E_RUN_PLAN_FAILED, _plan_name))
        _result.append_attr_value(ATTR_NOTES, str(_e))
    _result.mark_end()
    return _result


def _run_plan(plan_entity, plan_id, executable_table, local_config, env_vars, task_monitor, matrix):
    """
    Runs a test plan.
    :param TestPlanEntity plan_entity: the test plan, eventually including descendants
    :param int plan_id: the TCMS ID of the test plan
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local issai product configuration
    :param dict env_vars: the environment variables to use in test execution
    :param TaskMonitor task_monitor: the progress handler
    :param PropertyMatrix matrix: the permuting properties matrix
    :returns: execution result
    :rtype: PlanResult
    """
    task_monitor.check_abort()
    if plan_id < 0:
        plan_id = plan_entity.entity_id()
    _result = PlanResult.from_entity(plan_entity, plan_id)
    _result.mark_start()
    _plan = plan_entity.get_part(ATTR_TEST_PLANS, plan_id)
    _plan_name = _plan[ATTR_NAME]
    task_monitor.log(I_RUN_RUNNING_PLAN, _plan_name)
    # noinspection PyBroadException
    try:
        # add issai relevant plan properties to runtime environment
        _essential_props = _essential_properties_for(local_config, ENTITY_TYPE_PLAN)
        _plan_env = env_vars.copy()
        for _prop_k, _prop_v in plan_entity.get_plan_properties(_plan, _essential_props).items():
            _plan_env[_prop_k] = str(_prop_v)
        # run initialization for plan
        _run_assistant(CFG_PAR_RUNNER_PLAN_ASSISTANT, ASSISTANT_ACTION_INIT, _plan_name,
                       executable_table, local_config, _plan_env, task_monitor)
        # run all test cases in plan
        for _case_id in _plan[ATTR_CASES]:
            # skip case, if not runnable
            if _skip_entity_on_local_machine(plan_entity, ENTITY_TYPE_CASE, _case_id, task_monitor):
                continue
            _case_result = _run_case(plan_entity, plan_id, _case_id, executable_table, local_config, _plan_env,
                                     task_monitor, matrix)
            _result.add_case_result(_case_result)
        # eventually run child plans
        for _child_id in plan_entity.plan_child_ids(plan_id):
            if _skip_entity_on_local_machine(plan_entity, ENTITY_TYPE_PLAN, _child_id, task_monitor):
                continue
            _child_result = _run_plan(plan_entity, _child_id, executable_table, local_config, _plan_env,
                                      task_monitor, matrix)
            _result.add_plan_result(_child_result)
        # run cleanup for plan
        _run_assistant(CFG_PAR_RUNNER_PLAN_ASSISTANT, ASSISTANT_ACTION_CLEANUP, _plan_name,
                       executable_table, local_config, _plan_env, task_monitor)
    except BaseException as _e:
        _result.append_attr_value(ATTR_SUMMARY, localized_message(E_RUN_PLAN_FAILED, _plan[ATTR_NAME]))
        _result.append_attr_value(ATTR_NOTES, str(_e))
    finally:
        _result.mark_end()
    return _result


def _run_case(plan_entity, plan_id, case_id, executable_table, local_config, runtime_env, task_monitor, matrix):
    """
    Runs a single test case.
    :param TestPlanEntity plan_entity: the test plan, eventually including descendants
    :param int plan_id: the TCMS test plan ID
    :param int case_id: the TCMS test case ID
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local issai product configuration
    :param dict runtime_env: the environment variables to use in test execution
    :param TaskMonitor task_monitor: the progress handler
    :param PropertyMatrix matrix: the permuting properties matrix
    :returns: execution result
    :rtype: CaseResult
    """
    task_monitor.check_abort()
    _case = plan_entity.get_part(ATTR_TEST_CASES, case_id)
    _case_name = _case[ATTR_SUMMARY]
    task_monitor.log(I_RUN_RUNNING_CASE, _case[ATTR_SUMMARY])
    _result = CaseResult(plan_id, case_id, _case_name, matrix.code())
    _result.mark_start()
    # noinspection PyBroadException
    try:
        # skip case, if not runnable
        if _skip_entity_on_local_machine(plan_entity, ENTITY_TYPE_CASE, case_id, task_monitor):
            return
        # automated test case must contain script
        _script = _case[ATTR_SCRIPT]
        if len(_script) == 0:
            raise IssaiException(E_RUN_CASE_SCRIPT_MISSING, _case[ATTR_SUMMARY])
        _executable = executable_table.executable_for(_script)
        # add issai relevant case properties to runtime environment
        _essential_props = _essential_properties_for(local_config, ENTITY_TYPE_CASE)
        _case_env = runtime_env.copy()
        for _prop_k, _prop_v in plan_entity.get_case_properties(case_id, _essential_props).items():
            _case_env[_prop_k] = str(_prop_v)
        # run initialization for case
        _run_assistant(CFG_PAR_RUNNER_CASE_ASSISTANT, ASSISTANT_ACTION_INIT, _case_name,
                       executable_table, local_config, _case_env, task_monitor)
        # run test case
        _args = _case[ATTR_ARGUMENTS]
        task_monitor.log(I_RUN_RUNNING_SCRIPT, _script, f"'{_case_name}' {_args}")
        if not task_monitor.is_dry_run():
            _rc, _stdout, _stderr = _executable.run(runtime_env, f"'{_case_name}'", _args)
            _result.set_attr_value(ATTR_STATUS, result_status_name(_rc))
            # save output to file
            _case = plan_entity.get_part(ATTR_TEST_CASES, case_id)
            _output_path = os.path.join(local_config.get_value(CFG_PAR_RUNNER_WORKING_PATH),
                                        RESULTS_ROOT_DIR, ATTACHMENTS_CASE_DIR, f'{plan_id}_{case_id}')
            os.makedirs(_output_path, exist_ok=True)
            _output_file_path = os.path.join(_output_path, f'{local_config.output_log()}{matrix.suffix_code()}')
            with open(_output_file_path, 'w') as _output_file:
                _output_file.write(_stdout)
                _output_file.write(_stderr)
                _output_file.close()
        # run cleanup for case
        _run_assistant(CFG_PAR_RUNNER_CASE_ASSISTANT, ASSISTANT_ACTION_CLEANUP, _case_name,
                       executable_table, local_config, _case_env, task_monitor)
    except BaseException as _e:
        _result.set_attr_value(ATTR_STATUS, RESULT_STATUS_ERROR)
        _result.append_attr_value(ATTR_COMMENT, localized_message(E_RUN_CASE_FAILED, _case_name))
        _result.append_attr_value(ATTR_COMMENT, str(_e))
    finally:
        _result.set_attr_value(ATTR_TESTER_NAME, runtime_env[ENVA_ISSAI_USERNAME])
        task_monitor.operations_processed(1)
        _result.mark_end()
    return _result


def plan_entity_from_tcms(plan, options, task_monitor):
    """
    Creates TestPlan entity from TCMS.
    :param dict plan: the test plan name and ID
    :param dict options: the run options
    :param TaskMonitor task_monitor: the progress handler
    :returns: test plan entity
    :rtype: TestPlanEntity
    :raises IssaiException: if an error occurs during TCMS access
    """
    _plan_id = plan[ATTR_ID]
    _plan_name = plan[ATTR_NAME]
    task_monitor.log(I_EXP_FETCH_PLAN, _plan_name)
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
    _plan_entity.add_tcms_runs(read_tcms_run_tree(_full_plan, _build))
    task_monitor.log(I_EXP_FETCH_PLAN_CASES, _plan_name)
    _plan_cases = read_tcms_cases(False, _full_plan, True, False)
    _plan_entity.add_tcms_cases(_plan_cases)
    _plan_entity.add_tcms_executions(read_tcms_executions([_build], False, _plan_cases), True)
    _env = options.get(OPTION_ENVIRONMENT)
    if _env is not None:
        _plan_entity.add_environments([_env])
    return _plan_entity


def initial_env_vars(local_config, working_path, user_name, attachment_path=None):
    """
    Creates and returns basic set of environment variables for test execution.
    :param LocalConfig local_config: the local issai product configuration
    :param str working_path: the runner working path
    :param str user_name: name of user executing the test
    :param str attachment_path: root path for attachment files, if test is executed from offline file
    :returns: basic environment variables
    :rtype: MutableMapping
    :raises IssaiException: if local configuration doesn't specify a valid product source path
    """
    _runtime_env = os.environ.copy()
    _enva_mapping = local_config.get_value(CFG_GROUP_ENV)
    if _enva_mapping is not None:
        _runtime_env.update(_enva_mapping)
    _source_path = local_config.get_value(CFG_PAR_PRODUCT_SOURCE_PATH)
    if _source_path is None:
        raise IssaiException(E_RUN_SOURCE_PATH_MISSING, CFG_PAR_PRODUCT_SOURCE_PATH)
    if not os.path.isdir(_source_path):
        raise IssaiException(E_RUN_SOURCE_PATH_INVALID, _source_path)
    _py_path = _runtime_env.get(ENVA_PYTHON_PATH)
    if _py_path is None or len(_py_path) == 0:
        _runtime_env[ENVA_PYTHON_PATH] = _source_path
    else:
        _runtime_env[ENVA_PYTHON_PATH] = f'{_source_path}:{_py_path}'
    _tests_path = local_config.get_value(CFG_PAR_PRODUCT_TEST_PATH)
    if _tests_path is None:
        _tests_path = _source_path
    else:
        if not os.path.isdir(_tests_path):
            raise IssaiException(E_RUN_TEST_PATH_INVALID, _tests_path)
    _runtime_env[ENVA_ISSAI_TESTS_PATH] = _tests_path
    _runtime_env[ENVA_ATTACHMENTS_PATH] = os.path.join(working_path, ATTACHMENTS_ROOT_DIR)
    _runtime_env[ENVA_ISSAI_USERNAME] = user_name
    if attachment_path is not None:
        _runtime_env[ENVA_ATTACHMENTS_PATH] = attachment_path
    return _runtime_env


def clear_result_path(local_config):
    """
    Clears output directory with result files from previous run.
    :param LocalConfig local_config: the local issai product configuration
    """
    _result_path = os.path.join(local_config.runner_working_path(), RESULTS_ROOT_DIR)
    if not os.path.exists(_result_path):
        return
    if os.path.isdir(_result_path):
        shutil.rmtree(_result_path)
    else:
        os.remove(_result_path)
    os.makedirs(_result_path, exist_ok=True)


def store_plan_results_to_tcms(plan_result, plan_entity, options, local_config, working_path, task_monitor):
    """
    Stores plan result in TCMS and eventually uploads output files from test execution.
    :param PlanResult plan_result: the test plan result
    :param TestPlanEntity plan_entity: the test plan entity
    :param dict options: the run options
    :param LocalConfig local_config: the local issai product configuration
    :param str working_path: the runner root path for output files
    :param TaskMonitor task_monitor: the progress handler
    """
    _version = options.get(ATTR_VERSION)
    _build = options.get(ATTR_BUILD)
    _build_id = _build[ATTR_ID]
    _plan_results = plan_result.plan_results()
    for _pr in _plan_results:
        _plan_id = _pr.get_attr_value(ATTR_PLAN)
        _plan = plan_entity.object(TCMS_CLASS_ID_TEST_PLAN, _plan_id)
        _run = _run_for_plan(_plan, _build, plan_entity, task_monitor)
        _run_id = _run[ATTR_ID]
        _vals = {ATTR_START_DATE: _pr.get_attr_value(ATTR_START_DATE),
                 ATTR_STOP_DATE: _pr.get_attr_value(ATTR_STOP_DATE)}
        _notes = _pr.get_attr_value(ATTR_NOTES)
        _summary = _pr.get_attr_value(ATTR_SUMMARY)
        if len(_notes) > 0:
            _vals[ATTR_NOTES] = _notes
        if len(_summary) > 0:
            _vals[ATTR_SUMMARY] = _summary
        if not task_monitor.is_dry_run():
            update_run(_run_id, _vals)
        for _cr in _pr.get_attr_value(ATTR_CASE_RESULTS):
            _case_id = _cr[ATTR_CASE]
            _custom_status_name = local_config.custom_execution_status(_cr.get_attr_value(ATTR_STATUS))
            _status_id = plan_entity.execution_status_id_of(_custom_status_name)
            _execution = _execution_for_case(_cr, _plan, _run_id, _build, plan_entity, task_monitor)
            if task_monitor.is_dry_run():
                continue
            _execution_id = _execution[ATTR_ID]
            _vals = {ATTR_START_DATE: _cr.get_attr_value(ATTR_START_DATE),
                     ATTR_STOP_DATE: _cr.get_attr_value(ATTR_STOP_DATE), ATTR_STATUS: _status_id}
            update_execution(_execution_id, _vals, _cr.get_attr_value(ATTR_COMMENT))
            if local_config.has_upload_patterns():
                for _file_path in list_case_result_files(working_path, _plan_id, _case_id, local_config):
                    _file_name = os.path.basename(_file_path)
                    task_monitor.log(I_UPLOAD_ATTACHMENT, _file_name, _plan[ATTR_NAME], _cr[ATTR_CASE_NAME])
                    _tcms_file_name = f'testexecution_{_execution_id}_{_file_name}'
                    upload_attachment_file(_file_path, _tcms_file_name, TCMS_CLASS_ID_TEST_RUN, _run_id)


def store_plan_results_to_file(plan_result, plan_entity, local_config, working_path):
    """
    Stores plan result in a file.
    :param PlanResult plan_result: the test plan result
    :param TestPlanEntity plan_entity: the test plan entity
    :param LocalConfig local_config: the local issai product configuration
    :param str working_path: the runner root path for output files
    """
    if local_config.has_upload_patterns():
        for _cr in plan_result.case_results():
            _plan_id = _cr.get_attr_value(ATTR_PLAN)
            _case_id = _cr.get_attr_value(ATTR_CASE)
            for _file_path in list_case_result_files(working_path, _plan_id, _case_id, local_config):
                _cr[ATTR_OUTPUT_FILES].append(os.path.basename(_file_path))
    _pr = PlanResultEntity.from_result(plan_result, plan_entity)
    _plan_id = _pr.entity_id()
    _output_file_path = os.path.join(working_path, RESULTS_ROOT_DIR, f'testplan_{_plan_id}.toml')
    _pr.to_file(_output_file_path)


def store_plan_results(plan_result, plan_entity, options, local_config, working_path, task_monitor):
    """
    Stores plan result in a file.
    :param PlanResult plan_result: the test plan result
    :param TestPlanEntity plan_entity: the test plan entity
    :param dict options: the run options
    :param LocalConfig local_config: the local issai product configuration
    :param str working_path: the runner root path for output files
    :param TaskMonitor task_monitor: the progress handler
    """
    task_monitor.check_abort()
    if options.get(OPTION_STORE_RESULT):
        store_plan_results_to_tcms(plan_result, plan_entity, options, local_config, working_path, task_monitor)
        return
    if not task_monitor.is_dry_run():
        store_plan_results_to_file(plan_result, plan_entity, local_config, working_path)


def execution_task_result(plan_name, plan_result):
    """
    :param str plan_name: the test plan name
    :param PlanResult plan_result: the plan result
    :returns: the task result for GUI or CLI
    :rtype: TaskResult
    """
    _rc = plan_result.result_status()
    _summary = plan_result.get_attr_value(ATTR_SUMMARY)
    _notes = plan_result.get_attr_value(ATTR_NOTES)
    if len(_summary) == 0 and len(_notes) == 0:
        _task_summary = localized_message(I_RUN_PLAN_SUCCEEDED, plan_name)
    else:
        _task_summary = '%s%s%s' % (plan_result.get_attr_value(ATTR_SUMMARY), os.linesep,
                                    plan_result.get_attr_value(ATTR_NOTES))
    return TaskResult(_rc, _task_summary)


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


def _skip_entity_on_local_machine(entity, entity_type, entity_id, task_monitor):
    """
    Checks whether given test plan or case is runnable on local machine.
    :param TestPlan entity: the test plan entity
    :param int entity_type: the entity type (test plan or case)
    :param int entity_id: the test plan or test case TCMS ID
    :param TaskMonitor task_monitor: the progress handler
    :returns: True, if entity is not runnable on local machine
    :rtype: bool
    """
    _entity_type_name = entity_type_name(entity_type)
    if entity_type == ENTITY_TYPE_PLAN:
        _plan = entity.get_part(ATTR_TEST_PLANS, entity_id)
        _entity_name = _plan[ATTR_NAME]
        _entity_runnable = _plan[ATTR_IS_ACTIVE]
        _entity_tags = _plan[ATTR_TAGS]
    else:
        _case = entity.get_part(ATTR_TEST_CASES, entity_id)
        _entity_name = _case[ATTR_SUMMARY]
        _entity_runnable = _case[ATTR_IS_AUTOMATED]
        _entity_tags = _case[ATTR_TAGS]
    if not _entity_runnable:
        _reason_id = I_RUN_PLAN_NOT_ACTIVE if entity_type == ENTITY_TYPE_PLAN else I_RUN_CASE_NOT_AUTOMATED
        _reason_msg = localized_message(_reason_id)
        task_monitor.log(I_RUN_ENTITY_SKIPPED, _entity_type_name, _entity_name, _reason_msg)
        return True
    if _tags_exclude_platform_os(_entity_tags):
        _reason_msg = localized_message(I_RUN_ENTITY_NOT_FOR_LOCAL_OS, platform_os_tag())
        task_monitor.log(I_RUN_ENTITY_SKIPPED, _entity_type_name, _entity_name, _reason_msg)
        return True
    if _tags_exclude_platform_arch(_entity_tags):
        _reason_msg = localized_message(I_RUN_ENTITY_NOT_FOR_LOCAL_ARCH, platform_architecture_tag())
        task_monitor.log(I_RUN_ENTITY_SKIPPED, _entity_type_name, _entity_name, _reason_msg)
        return True
    return False


def _run_assistant(assistant_name, action, entity_name, executable_table, local_config, runtime_env, task_monitor):
    """
    Executes test entity initialization or cleanup function/script.
    :param str assistant_name: the assistant's name, i.e. its TOML key in the runner section of product configuration
    :param int action: the action (1 for init, -1 for cleanup)
    :param str entity_name: the assistant's name, i.e. its TOML key in the runner section of product configuration
    :param ExecutableTable executable_table: the table holding the functions and scripts to execute
    :param LocalConfig local_config: the local configuration
    :param dict runtime_env: the runtime environment to use
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if the assistant fails
    """
    task_monitor.check_abort()
    _assistant = local_config.get(assistant_name)
    _dry_run = task_monitor.is_dry_run()
    if _assistant is None:
        return
    _action_name = assistant_action_name(action)
    try:
        _executable = executable_table.executable_for(_assistant)
        if not _dry_run:
            _executable.run(runtime_env, action, entity_name)
        task_monitor.log(I_RUN_ASSISTANT_SUCCEEDED, _assistant, _action_name)
    except IssaiException as _e:
        task_monitor.log(E_RUN_ASSISTANT_FAILED, _assistant, _action_name, str(_e))
        if _dry_run:
            return
        raise


def _run_for_plan(plan, build, plan_entity, task_monitor):
    """
    Returns test run for specified plan and build.
    Test run is searched first in plan entity, then in TCMS. If it doesn't exist it is created in TCMS except when in
    dry run mode.
    :param dict plan: the test plan data
    :param dict build: the build data
    :param Entity plan_entity: the test plan entity
    :param TaskMonitor task_monitor: the progress handler
    :returns: test run for specified plan and build
    :rtype: dict
    """
    _run_id = plan.get(ATTR_RUN)
    if _run_id is not None and _run_id > 0:
        return plan_entity.get_part(ATTR_TEST_RUNS, _run_id)
    _run = find_tcms_objects(TCMS_CLASS_ID_TEST_RUN, {ATTR_PLAN: plan[ATTR_ID], ATTR_BUILD: build[ATTR_ID]})
    if len(_run) == 0:
        task_monitor.log(I_RUN_CREATING_RUN, plan[ATTR_NAME], build[ATTR_NAME])
        return {ATTR_ID: -1} if task_monitor.is_dry_run() else create_run_from_plan(plan, build)
    return _run[0]


def _execution_for_case(case_result, plan, run_id, build, plan_entity, task_monitor):
    """
    Returns test execution for specified plan, case and build.
    Test execution is searched first in plan entity, then in TCMS. If it doesn't exist it is created in TCMS
    except when in dry run mode.
    :param dict case_result: the test case result data
    :param dict plan: the test plan data
    :param dict run_id: the test run data
    :param dict build: the build data
    :param Entity plan_entity: the test plan entity
    :param TaskMonitor task_monitor: the progress handler
    :returns: test execution for specified plan, case and build
    :rtype: dict
    """
    _build_id = build[ATTR_ID]
    _case_id = case_result[ATTR_CASE]
    _case = plan_entity.get_part(ATTR_TEST_CASES, _case_id)
    # look for test execution in plan entity first
    _executions = _case.get(ATTR_EXECUTIONS)
    if _executions is not None:
        for _execution_id in _executions:
            _execution = plan_entity.get_part(ATTR_TEST_EXECUTIONS, _execution_id)
            if _execution[ATTR_BUILD] == _build_id:
                return _execution
    # try to find execution in TCMS
    _execution = find_tcms_objects(TCMS_CLASS_ID_TEST_EXECUTION, {ATTR_CASE: _case_id, ATTR_BUILD: _build_id})
    if len(_execution) == 0:
        task_monitor.log(I_RUN_CREATING_EXECUTION, plan[ATTR_NAME], case_result[ATTR_CASE_NAME], build[ATTR_NAME])
        _execution_attrs = {ATTR_RUN: run_id, ATTR_CASE: _case_id}
        return {ATTR_ID: -1} if task_monitor.is_dry_run() else create_tcms_object(TCMS_CLASS_ID_TEST_EXECUTION,
                                                                                  _execution_attrs)
    return _execution[0]


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


def _read_env_properties(env_opt):
    """
    Reads properties from environment option.
    :param dict env_opt: the environment specification
    :returns: environment properties
    :rtype: list
    """
    if env_opt is None:
        return []
    _props = []
    _prop_names = dict()
    _prop_indexes = dict()
    _index = -1
    for _property in env_opt[ATTR_PROPERTIES]:
        _prop_name, _prop_value = next(iter(_property.items()))
        _val_count = _prop_names.get(_prop_name)
        if _val_count is None:
            _index += 1
            _prop_names[_prop_name] = 1
            _prop_indexes[_prop_name] = _index
            _props.append({_prop_name: _prop_value})
            continue
        _prop_index = _prop_indexes[_prop_name]
        if _val_count == 1:
            _prop_names[_prop_name] += 1
            _props[_prop_index][_prop_name] = [_props[_prop_index][_prop_name], _prop_value]
            continue
        _props[_prop_index][_prop_name].append(_prop_value)
    return _props
