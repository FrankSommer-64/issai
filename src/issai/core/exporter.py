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
Functions to export entities from TCMS to files.
"""

from issai.core.attachments import download_attachments
from issai.core.entities import ProductEntity, TestCaseEntity, TestPlanEntity
from issai.core.task import TaskResult
from issai.core.tcms import *


def export_case(case, options, output_path, task_monitor):
    """
    Exports a test case from TCMS.
    Test entity attributes and metadata like versions, components etc. are directly written to output file named
    'testplan_<testcase-id>.toml'.
    Attachments are stored under subdirectory attachments/case/<testcase-id> for test cases.
    :param dict case: the test case ID and name
    :param dict options: the export control options. May contain the following keys:
                         'version' - the TCMS version data (optional, defaults to all product versions),
                         'build' - the TCMS build data (optional, defaults to all product builds),
                         'include_attachments' - (optional, attachments are not included by default)
                         'include_history' - (optional, test case histories are not included by default)
    :param str output_path: the output directory path, must be empty
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if export fails
    """
    _version = options.get(OPTION_VERSION)
    _build = options.get(OPTION_BUILD)
    _include_history = options.get(OPTION_INCLUDE_HISTORY)
    _include_executions = options.get(OPTION_INCLUDE_RUNS)
    _include_attachments = options.get(OPTION_INCLUDE_ATTACHMENTS)
    # TC 1, MD 10, OUTFILE 1
    _op_count = 13 if _include_executions else 12
    if _include_attachments:
        _op_count += 1
    task_monitor.set_operation_count(_op_count)
    task_monitor.log(I_EXP_FETCH_CASE, case[ATTR_NAME])
    task_monitor.operations_processed(1)
    _case = read_tcms_case(case[ATTR_ID], _include_executions, _include_history)
    _product = read_product_for_test_entity(ENTITY_TYPE_CASE, _case)
    _case_id = _case[ATTR_ID]
    _case_name = _case[ATTR_SUMMARY]
    _export_entity = TestCaseEntity(_case_id, _case_name)
    _export_entity.fill_product_data(_product)
    _classification = find_tcms_object(TCMS_CLASS_ID_CLASSIFICATION, {ATTR_ID: _product[ATTR_CLASSIFICATION]})
    _export_entity.add_master_data(ATTR_PRODUCT_CLASSIFICATIONS, _classification)

    # add test case
    _cases = [_case]
    _export_entity.add_tcms_cases(_cases)
    # eventually fetch test executions
    if _include_executions:
        task_monitor.log(I_EXP_FETCH_EXECUTIONS, _case_name)
        task_monitor.operations_processed(1)
        _builds = None if _build is None else [_build]
        _export_entity.add_tcms_executions(read_tcms_executions(_builds, _include_history, _cases))

    _fetch_referenced_master_data(_export_entity, task_monitor)
    if _include_attachments:
        download_attachments(_export_entity, output_path, task_monitor)
    _write_output_file(_export_entity, os.path.join(output_path, f'testcase_{_case_id}.toml'), task_monitor)

    return TaskResult(0, localized_message(I_GUI_EXPORT_CASE_SUCCESSFUL, _case_name))


def export_plan(plan, options, output_path, task_monitor):
    """
    Exports a test plan from TCMS.
    Test entity attributes and metadata like versions, components etc. are directly written to output file named
    'testplan_<testplan-id>.toml'.
    Attachments are stored under subdirectory attachments/plan/<testplan-id> for test plans, and
    under subdirectory attachments/case/<testcase-id> for test cases.
    :param dict plan: the test plan ID and name
    :param dict options: the export control options. May contain the following keys:
                         'version' - the TCMS version data (optional, defaults to all product versions),
                         'build' - the TCMS build data (optional, defaults to all product builds),
                         'include_attachments' - (optional, attachments are not included by default)
                         'include_history' - (optional, test case histories are not included by default)
    :param str output_path: the output directory path, must be empty
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if export fails
    """
    _version = options.get(OPTION_VERSION)
    _build = options.get(OPTION_BUILD)
    _include_runs = options.get(OPTION_INCLUDE_RUNS)
    _include_tree = options.get(OPTION_PLAN_TREE)
    _include_history = options.get(OPTION_INCLUDE_HISTORY)
    _include_attachments = options.get(OPTION_INCLUDE_ATTACHMENTS)
    # TP 1, TC 5, MD 10, OUTFILE 1
    _op_count = 18 if _include_runs else 17
    if _include_attachments:
        _op_count += 1
    _plan_id = plan[ATTR_ID]
    _plan_name = plan[ATTR_NAME]
    _plan = read_test_entity_with_id(ENTITY_TYPE_PLAN, _plan_id)
    _product = read_product_for_test_entity(ENTITY_TYPE_PLAN, _plan)
    _export_entity = TestPlanEntity(_plan[ATTR_ID], _plan[ATTR_NAME])
    _export_entity.fill_product_data(_product)
    _classification = find_tcms_object(TCMS_CLASS_ID_CLASSIFICATION, {ATTR_ID: _product[ATTR_CLASSIFICATION]})
    _export_entity.add_master_data(ATTR_PRODUCT_CLASSIFICATIONS, _classification)

    # fetch test plans and runs
    task_monitor.log(I_EXP_FETCH_PLAN, _plan_name)
    task_monitor.operations_processed(1)
    _plans = read_tcms_plan(plan, _include_tree, _include_runs)
    _export_entity.add_tcms_plans(_plans)
    if _include_runs:
        _export_entity.add_tcms_runs(read_tcms_run_tree(_plans, _build))

    # fetch test cases and executions
    task_monitor.log(I_EXP_FETCH_PLAN_CASES, _plan_name)
    task_monitor.operations_processed(5)
    _cases = read_tcms_cases(False, _plans, _include_runs, _include_history)
    _export_entity.add_tcms_cases(_cases)
    if _include_runs:
        _builds = None if _build is None else [_build]
        _export_entity.add_tcms_executions(read_tcms_executions(_builds, _include_history, _cases))

    if options.get(OPTION_INCLUDE_ENVIRONMENTS):
        _fetch_environments(_export_entity, task_monitor)

    _fetch_referenced_master_data(_export_entity, task_monitor)
    if _include_attachments:
        download_attachments(_export_entity, output_path, task_monitor)
    _write_output_file(_export_entity, os.path.join(output_path, f'testplan_{_plan_id}.toml'), task_monitor)

    return TaskResult(0, localized_message(I_GUI_EXPORT_PLAN_SUCCESSFUL, _plan_name))


def export_product(product_name, options, output_path, task_monitor):
    """
    Exports a product from TCMS.
    Test entity attributes and metadata like versions, components etc. are directly written to output file named
    '<product-name>.toml'.
    Attachments are stored under subdirectory attachments/plan/<testplan-id> for test plans, and
    under subdirectory attachments/case/<testcase-id> for test cases.
    :param str product_name: the TCMS product name
    :param dict options: the export control options. May contain the following keys:
                         'version' - the TCMS version data (optional, defaults to all product versions),
                         'build' - the TCMS build data (optional, defaults to all product builds),
                         'include_attachments' - (optional, attachments are not included by default)
                         'include_history' - (optional, test case histories are not included by default)
    :param str output_path: the output directory path, must be empty
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if export fails
    """
    _include_history = options.get(OPTION_INCLUDE_HISTORY)
    _include_runs = options.get(OPTION_INCLUDE_RUNS)
    _include_attachments = options.get(OPTION_INCLUDE_ATTACHMENTS)
    # P 1, TP 20, TC 40, MD 5, OUTFILE 1
    _op_count = 68 if _include_runs else 67
    if _include_attachments:
        _op_count += 1
    task_monitor.set_operation_count(_op_count)
    # fetch product specific metadata from TCMS
    task_monitor.log(I_EXP_FETCH_PRODUCT)
    task_monitor.operations_processed(1)
    _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_NAME: product_name})
    _export_entity = ProductEntity.from_tcms(_product)
    _export_all_cases = options.get(OPTION_VERSION) is None
    _fetch_product_master_data(_export_entity, _product, options.get(OPTION_VERSION), options.get(OPTION_BUILD))

    # fetch test plans and runs from TCMS
    task_monitor.log(I_EXP_FETCH_PLANS)
    task_monitor.operations_processed(20)
    _export_entity.add_tcms_plans(read_tcms_plans(_export_entity.master_data_of_type(ATTR_PRODUCT_VERSIONS),
                                                  _include_runs))
    if _include_runs:
        _export_entity.add_tcms_runs(read_tcms_runs(_export_entity.master_data_of_type(ATTR_PRODUCT_BUILDS)))

    # fetch test cases and executions from TCMS
    task_monitor.log(I_EXP_FETCH_CASES)
    task_monitor.operations_processed(40)
    _filter_objects = _export_entity.master_data_of_type(ATTR_CASE_CATEGORIES) if _export_all_cases \
        else _export_entity.test_plans()
    _export_entity.add_tcms_cases(read_tcms_cases(_export_all_cases, _filter_objects,
                                                  _include_runs, _include_history))
    if _include_runs:
        _executions = read_tcms_executions(_export_entity.master_data_of_type(ATTR_PRODUCT_BUILDS),
                                           _include_history)
        _export_entity.add_tcms_executions(_executions)

    if options.get(OPTION_INCLUDE_ENVIRONMENTS):
        _fetch_environments(_export_entity, task_monitor)

    _fetch_referenced_master_data(_export_entity, task_monitor)
    if options.get(OPTION_INCLUDE_ATTACHMENTS):
        download_attachments(_export_entity, output_path, task_monitor)
    _write_output_file(_export_entity, os.path.join(output_path, f'{product_name}.toml'), task_monitor)

    return TaskResult(0, localized_message(I_GUI_EXPORT_PRODUCT_SUCCESSFUL, product_name))


def _fetch_product_master_data(entity, product, version, build):
    """
    Fetches product specific master data for specified product from TCMS and stores the data in the given entity.
    Product specific master data are builds, categories, classifications, components, environments and versions.
    :param Entity entity: the entity
    :param dict product: the TCMS product data
    :param dict version: the TCMS version data; None for all product versions
    :param dict build: the TCMS build data; None for all product builds
    :raises IssaiException: if an error during TCMS communication occurs
    """
    _categories = find_tcms_objects(TCMS_CLASS_ID_CATEGORY, {ATTR_PRODUCT: product[ATTR_ID]})
    entity.add_master_data(ATTR_CASE_CATEGORIES, _categories)
    _classification = find_tcms_object(TCMS_CLASS_ID_CLASSIFICATION, {ATTR_ID: product[ATTR_CLASSIFICATION]})
    entity.add_master_data(ATTR_PRODUCT_CLASSIFICATIONS, _classification)
    _components = find_tcms_objects(TCMS_CLASS_ID_COMPONENT, {ATTR_PRODUCT: product[ATTR_ID]})
    entity.add_master_data(ATTR_CASE_COMPONENTS, _components)
    _versions = read_tcms_versions_for_product(product) if version is None else [version]
    entity.add_master_data(ATTR_PRODUCT_VERSIONS, _versions)
    _builds = read_tcms_builds_for_version(_versions) if build is None else [build]
    entity.add_master_data(ATTR_PRODUCT_BUILDS, _builds)


def _fetch_referenced_master_data(entity, task_monitor):
    """
    Fetches referenced master data and stores the data in the given entity.
    Referenced master data are case-statuses, execution-statuses, plan-types, priorities and users.
    :param Entity entity: the entity
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if an error during TCMS communication occurs
    """
    task_monitor.log(I_EXP_FETCH_MASTER_DATA)
    if not entity.holds_entity_with_type(ENTITY_TYPE_PRODUCT):
        _versions = find_tcms_objects(TCMS_CLASS_ID_VERSION, {'id__in': entity.referenced_version_ids()})
        entity.add_master_data(ATTR_PRODUCT_VERSIONS, _versions)
        _builds = find_tcms_objects(TCMS_CLASS_ID_BUILD, {'id__in': entity.referenced_build_ids()})
        entity.add_master_data(ATTR_PRODUCT_BUILDS, _builds)
        _categories = find_tcms_objects(TCMS_CLASS_ID_CATEGORY, {'id__in': entity.referenced_category_ids()})
        entity.add_master_data(ATTR_CASE_CATEGORIES, _categories)
        _components = find_tcms_objects(TCMS_CLASS_ID_COMPONENT, {'id__in': entity.referenced_component_ids()})
        entity.add_master_data(ATTR_CASE_COMPONENTS, _components)
        task_monitor.operations_processed(5)
    _case_statuses = find_tcms_objects(TCMS_CLASS_ID_TEST_CASE_STATUS, {'id__in': entity.referenced_case_status_ids()})
    entity.add_master_data(ATTR_CASE_STATUSES, _case_statuses)
    _execution_statuses = find_tcms_objects(TCMS_CLASS_ID_TEST_EXECUTION_STATUS,
                                            {'id__in': entity.referenced_execution_status_ids()})
    entity.add_master_data(ATTR_EXECUTION_STATUSES, _execution_statuses)
    _plan_types = find_tcms_objects(TCMS_CLASS_ID_PLAN_TYPE, {'id__in': entity.referenced_plan_type_ids()})
    entity.add_master_data(ATTR_PLAN_TYPES, _plan_types)
    _priorities = find_tcms_objects(TCMS_CLASS_ID_PRIORITY, {'id__in': entity.referenced_priority_ids()})
    entity.add_master_data(ATTR_CASE_PRIORITIES, _priorities)
    _users = find_tcms_objects(TCMS_CLASS_ID_USER, {'id__in': entity.referenced_user_ids()})
    entity.add_master_data(ATTR_TCMS_USERS, _users)
    task_monitor.operations_processed(5)


def _fetch_environments(entity, task_monitor):
    """
    Fetches all environments and stores the data in the given entity.
    :param Entity entity: the entity
    :param issai.core.task.TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if an error during TCMS communication occurs
    """
    task_monitor.log(I_EXP_FETCH_ENVIRONMENTS)
    entity.add_environments(read_tcms_environments())


def _write_output_file(entity, output_file_path, task_monitor):
    """
    Writes data of specified entity to output file.
     "attachments/<entity-type>/<entity-id>".
    Signals a progress event, if a receiver is given.
    :param Entity entity: the entity
    :param str output_file_path: the output file name including path
    :param TaskMonitor task_monitor: the progress handler
    :raises IOException: if write operation fails
    """
    task_monitor.log(I_EXP_WRITE_OUTPUT_FILE, output_file_path)
    entity.to_file(output_file_path)
