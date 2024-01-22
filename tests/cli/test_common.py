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
Unit tests for cli.common.
The tests will only succeed, if the following preconditions are fulfilled:
- Environment variable TEST_DATA_SET holds the name of the test data set used
- Environment variable TEST_DATA_ROOT holds the name of the directory containing the test data files
- TCMS test server must be running with the appropriate test data set
- ~/.tcms.conf contains URL and login for the TCMS test server
"""
import unittest

from issai.cli.common import *
from tests.cli import test_file_path, test_runs_in_multi_build_dataset, test_runs_in_multi_version_dataset


DUMMY_BUILD = 'unspecified'
DUMMY_BUILD_ID = '1'
DUMMY_CASE = 'Dummy Testcase 1'
DUMMY_CASE_ID = '1'
DUMMY_ENV = 'IssaiUnitTestAll'
DUMMY_ENV_ID = '1'
DUMMY_FN = 'testplan_1.toml'
DUMMY_PATH = '/tmp'
DUMMY_PLAN = 'DummyPlan'
DUMMY_PLAN_ID = '1'
DUMMY_PRODUCT = 'Dummy'
DUMMY_PRODUCT_ID = '1'
DUMMY_VERSION = 'unspecified'
DUMMY_VERSION_ID = '1'
DUP_PLAN = 'NonUniquePlan'
DUP_PLAN_ID_101 = '101'
DUP_PLAN_ID_DUMMY_PROD = '2'
DUP_PLAN_ID_UNIQUE_VER = '103'
DUP_PRODUCT = 'Duplicates'
DUP_PRODUCT_ID = '101'
SIMPLE_PLAN_FN = 'testplan_1.toml'
MULTI_VERSION_PLAN_FN = 'multi_version_testplan_1.toml'
MULTI_BUILD_PLAN_FN = 'multi_build_testplan_1.toml'
NON_EXISTING_BUILD = 'non-existing'
NON_EXISTING_FILE = 'non_existing_file.toml'
NON_EXISTING_PLAN = 'non-existing'
NON_EXISTING_PLAN_ID = '999999'
NON_EXISTING_VERSION = 'non-existing'
UNIQUE_VERSION = 'v0.5'
UNIQUE_VERSION_ID = '102'


# command line arguments
EXP_ARGS_CASE_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_ENVIRONMENTS}',
                     f'--{CLI_ARG_INCLUDE_EXECUTIONS}', f'--{CLI_ARG_INCLUDE_HISTORY}',
                     f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                     f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                     CLI_ARG_VAL_CASE, DUMMY_CASE, DUMMY_PATH]
EXP_ARGS_CASE_MIN = [CLI_ARG_VAL_CASE, DUMMY_CASE, DUMMY_PATH]
EXP_ARGS_CASE_ID_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_EXECUTIONS}',
                        f'--{CLI_ARG_INCLUDE_HISTORY}', f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                        f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                        CLI_ARG_VAL_CASE_ID, DUMMY_CASE_ID, DUMMY_PATH]
EXP_ARGS_CASE_ID_MIN = [CLI_ARG_VAL_CASE_ID, DUMMY_CASE_ID, DUMMY_PATH]
EXP_ARGS_PLAN_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_DESCENDANTS}',
                     f'--{CLI_ARG_INCLUDE_ENVIRONMENTS}', f'--{CLI_ARG_INCLUDE_HISTORY}', f'--{CLI_ARG_INCLUDE_RUNS}',
                     f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                     f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                     CLI_ARG_VAL_PLAN, DUMMY_PLAN, DUMMY_PATH]
EXP_ARGS_PLAN_MIN = [CLI_ARG_VAL_PLAN, DUMMY_PLAN, DUMMY_PATH]
EXP_ARGS_DUP_PROD_PLAN = [CLI_ARG_VAL_PLAN, DUP_PLAN, DUMMY_PATH, f'--{CLI_ARG_PRODUCT}', DUMMY_PRODUCT]
EXP_ARGS_DUP_PROD_VER_PLAN = [CLI_ARG_VAL_PLAN, DUP_PLAN, DUMMY_PATH, f'--{CLI_ARG_PRODUCT}', DUP_PRODUCT,
                              f'--{CLI_ARG_PRODUCT_VERSION}', UNIQUE_VERSION]
EXP_ARGS_PLAN_ID_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_DESCENDANTS}',
                        f'--{CLI_ARG_INCLUDE_HISTORY}', f'--{CLI_ARG_INCLUDE_RUNS}',
                        f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                        f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                        CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID, DUMMY_PATH]
EXP_ARGS_PLAN_ID_MIN = [CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID, DUMMY_PATH]
EXP_ARGS_PROD_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_ENVIRONMENTS}',
                     f'--{CLI_ARG_INCLUDE_HISTORY}', f'--{CLI_ARG_INCLUDE_RUNS}',
                     f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD, f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                     CLI_ARG_VAL_PRODUCT, DUMMY_PRODUCT, DUMMY_PATH]
EXP_ARGS_PROD_MIN = [CLI_ARG_VAL_PRODUCT, DUMMY_PRODUCT, DUMMY_PATH]
EXP_ARGS_PROD_ID_MAX = [f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_HISTORY}', f'--{CLI_ARG_INCLUDE_RUNS}',
                        f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD, f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION,
                        CLI_ARG_VAL_PRODUCT_ID, DUMMY_PRODUCT_ID, DUMMY_PATH]
EXP_ARGS_PROD_ID_MIN = [CLI_ARG_VAL_PRODUCT_ID, DUMMY_PRODUCT_ID, DUMMY_PATH]
# failures
EXP_ARGS_NO_ARGS = []
EXP_ARGS_DUP_PLAN_NO_PRODUCT = [CLI_ARG_VAL_PLAN, DUP_PLAN, DUMMY_PATH]
EXP_ARGS_DUP_PROD_PLAN_NO_VERSION = [CLI_ARG_VAL_PLAN, DUP_PLAN, DUMMY_PATH, f'--{CLI_ARG_PRODUCT}', DUP_PRODUCT]
EXP_ARGS_DUP_VERSION_PLAN = [CLI_ARG_VAL_PLAN, DUP_PLAN, DUMMY_PATH, f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION]
EXP_ARGS_INV_ENTITY_SPEC = ['xyz', DUMMY_PRODUCT, DUMMY_PATH]
EXP_ARGS_INV_OPTION = ['--xyz', CLI_ARG_VAL_PLAN, DUMMY_PLAN, DUMMY_PATH]
EXP_ARGS_NO_ENTITY = [CLI_ARG_VAL_CASE_ID]
EXP_ARGS_NO_OUTPUT_PATH = [CLI_ARG_VAL_CASE, DUMMY_CASE]
IMP_ARGS_MIN = [DUMMY_FN]
IMP_ARGS_MAX = [f'--{CLI_ARG_APPLY_CURRENT_USER}', CLI_ARG_VAL_APPLY_USER_ALWAYS, f'--{CLI_ARG_CREATE_MASTER_DATA}',
                f'--{CLI_ARG_DRY_RUN}', f'--{CLI_ARG_INCLUDE_ATTACHMENTS}', f'--{CLI_ARG_INCLUDE_ENVIRONMENTS}',
                DUMMY_FN]
IMP_ARGS_NO_FILE_NAME = []
IMP_ARGS_NON_EXISTING_FILE = [NON_EXISTING_FILE]
IMP_ARGS_INV_OPTION = ['--xyz', DUMMY_FN]
IMP_ARGS_INV_ACU_VALUE = [f'--{CLI_ARG_APPLY_CURRENT_USER}', 'xyz', DUMMY_FN]
RUN_ARGS_FILE_MAX = [f'--{CLI_ARG_DRY_RUN}', f'--{CLI_ARG_ENVIRONMENT}', DUMMY_ENV, f'--{CLI_ARG_INCLUDE_DESCENDANTS}',
                     f'--{CLI_ARG_PRODUCT}', DUMMY_PRODUCT, f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                     f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION, f'--{CLI_ARG_STORE_RESULT}',
                     CLI_ARG_VAL_INPUT_FILE, DUMMY_FN]
RUN_ARGS_FILE_MIN = [CLI_ARG_VAL_INPUT_FILE, DUMMY_FN]
RUN_ARGS_ID_MAX = [f'--{CLI_ARG_DRY_RUN}', f'--{CLI_ARG_ENVIRONMENT}', DUMMY_ENV, f'--{CLI_ARG_INCLUDE_DESCENDANTS}',
                   f'--{CLI_ARG_PRODUCT}', DUMMY_PRODUCT, f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                   f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION, f'--{CLI_ARG_STORE_RESULT}',
                   CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID]
RUN_ARGS_ID_MIN = [CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID]
RUN_ARGS_NAME_MAX = [f'--{CLI_ARG_DRY_RUN}', f'--{CLI_ARG_ENVIRONMENT}', DUMMY_ENV, f'--{CLI_ARG_INCLUDE_DESCENDANTS}',
                     f'--{CLI_ARG_PRODUCT}', DUMMY_PRODUCT, f'--{CLI_ARG_PRODUCT_BUILD}', DUMMY_BUILD,
                     f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION, f'--{CLI_ARG_STORE_RESULT}',
                     CLI_ARG_VAL_PLAN, DUMMY_PLAN]
RUN_ARGS_NAME_MIN = [CLI_ARG_VAL_PLAN, DUMMY_PLAN]
RUN_ARGS_NO_ARGS = []
RUN_ARGS_INV_ENTITY_SPEC = ['product', DUMMY_PRODUCT]
RUN_ARGS_INV_OPTION = ['--xyz', CLI_ARG_VAL_PLAN, DUMMY_PLAN]
RUN_ARGS_NO_FILE = [CLI_ARG_VAL_INPUT_FILE]
RUN_ARGS_NO_ID = [CLI_ARG_VAL_PLAN_ID]
RUN_ARGS_NO_NAME = [CLI_ARG_VAL_PLAN]
RUN_ARGS_ID_MISSING_BUILD = [CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID, f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION]
RUN_ARGS_ID_NON_EXISTING_BUILD = [CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID, f'--{CLI_ARG_PRODUCT_BUILD}', NON_EXISTING_BUILD]
RUN_ARGS_ID_NON_EXISTING_ID = [CLI_ARG_VAL_PLAN_ID, NON_EXISTING_PLAN_ID]
RUN_ARGS_ID_NON_EXISTING_VERSION = [CLI_ARG_VAL_PLAN_ID, DUMMY_PLAN_ID,
                                    f'--{CLI_ARG_PRODUCT_VERSION}', NON_EXISTING_VERSION]
RUN_ARGS_NAME_MISSING_BUILD = [CLI_ARG_VAL_PLAN, DUMMY_PLAN, f'--{CLI_ARG_PRODUCT_VERSION}', DUMMY_VERSION]
RUN_ARGS_NAME_NON_EXISTING_BUILD = [CLI_ARG_VAL_PLAN, DUMMY_PLAN, f'--{CLI_ARG_PRODUCT_BUILD}', NON_EXISTING_BUILD]
RUN_ARGS_NAME_NON_EXISTING_NAME = [CLI_ARG_VAL_PLAN, NON_EXISTING_PLAN]
RUN_ARGS_NAME_NON_EXISTING_VERSION = [CLI_ARG_VAL_PLAN, DUMMY_PLAN,
                                      f'--{CLI_ARG_PRODUCT_VERSION}', NON_EXISTING_VERSION]

# expected footprint for parsed command line arguments
FP_EXP_ARGS_CASE_MAX = {CLI_ARG_ENTITY_REF: DUMMY_CASE, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_CASE,
                        CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: False,
                        CLI_ARG_INCLUDE_EXECUTIONS: True, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: False,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_CASE_MIN = {CLI_ARG_ENTITY_REF: DUMMY_CASE, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_CASE,
                        CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                        CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False, CLI_ARG_INCLUDE_RUNS: False,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_EXP_ARGS_CASE_ID_MAX = {CLI_ARG_ENTITY_REF: DUMMY_CASE_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_CASE_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: False,
                           CLI_ARG_INCLUDE_EXECUTIONS: True, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: False,
                           CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_CASE_ID_MIN = {CLI_ARG_ENTITY_REF: DUMMY_CASE_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_CASE_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                           CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False,
                           CLI_ARG_INCLUDE_RUNS: False, CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_EXP_ARGS_PLAN_MAX = {CLI_ARG_ENTITY_REF: DUMMY_PLAN, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PLAN,
                        CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: True,
                        CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: True,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_PLAN_MIN = {CLI_ARG_ENTITY_REF: DUMMY_PLAN, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PLAN,
                        CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                        CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False, CLI_ARG_INCLUDE_RUNS: False,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_EXP_ARGS_PLAN_ID_MAX = {CLI_ARG_ENTITY_REF: DUMMY_PLAN_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PLAN_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: True,
                           CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: True,
                           CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_PLAN_ID_MIN = {CLI_ARG_ENTITY_REF: DUMMY_PLAN_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PLAN_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                           CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False,
                           CLI_ARG_INCLUDE_RUNS: False, CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_EXP_ARGS_PROD_MAX = {CLI_ARG_ENTITY_REF: DUMMY_PRODUCT, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PRODUCT,
                        CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: False,
                        CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: True,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_PROD_MIN = {CLI_ARG_ENTITY_REF: DUMMY_PRODUCT, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PRODUCT,
                        CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                        CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False, CLI_ARG_INCLUDE_RUNS: False,
                        CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                        CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_EXP_ARGS_PROD_ID_MAX = {CLI_ARG_ENTITY_REF: DUMMY_PRODUCT_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PRODUCT_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INCLUDE_DESCENDANTS: False,
                           CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: True, CLI_ARG_INCLUDE_RUNS: True,
                           CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION}
FP_EXP_ARGS_PROD_ID_MIN = {CLI_ARG_ENTITY_REF: DUMMY_PRODUCT_ID, CLI_ARG_EXPORT_ENTITY_SPEC: CLI_ARG_VAL_PRODUCT_ID,
                           CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INCLUDE_DESCENDANTS: False,
                           CLI_ARG_INCLUDE_EXECUTIONS: False, CLI_ARG_INCLUDE_HISTORY: False,
                           CLI_ARG_INCLUDE_RUNS: False, CLI_ARG_OUTPUT_PATH: DUMMY_PATH,
                           CLI_ARG_PRODUCT_BUILD: None, CLI_ARG_PRODUCT_VERSION: None}
FP_IMP_ARGS_MIN = {CLI_ARG_APPLY_CURRENT_USER: CLI_ARG_VAL_APPLY_USER_NEVER, CLI_ARG_CREATE_MASTER_DATA: False,
                   CLI_ARG_DRY_RUN: False, CLI_ARG_INCLUDE_ATTACHMENTS: False, CLI_ARG_INPUT_FILE: DUMMY_FN}
FP_IMP_ARGS_MAX = {CLI_ARG_APPLY_CURRENT_USER: CLI_ARG_VAL_APPLY_USER_ALWAYS, CLI_ARG_CREATE_MASTER_DATA: True,
                   CLI_ARG_DRY_RUN: True, CLI_ARG_INCLUDE_ATTACHMENTS: True, CLI_ARG_INPUT_FILE: DUMMY_FN}
FP_RUN_ARGS_FILE_MAX = {CLI_ARG_DRY_RUN: True, CLI_ARG_ENTITY_REF: DUMMY_FN, CLI_ARG_ENVIRONMENT: DUMMY_ENV,
                        CLI_ARG_INCLUDE_DESCENDANTS: True, CLI_ARG_PRODUCT: DUMMY_PRODUCT,
                        CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION,
                        CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_INPUT_FILE, CLI_ARG_STORE_RESULT: True}
FP_RUN_ARGS_FILE_MIN = {CLI_ARG_DRY_RUN: False, CLI_ARG_ENTITY_REF: DUMMY_FN, CLI_ARG_ENVIRONMENT: None,
                        CLI_ARG_INCLUDE_DESCENDANTS: False, CLI_ARG_PRODUCT: None, CLI_ARG_PRODUCT_BUILD: None,
                        CLI_ARG_PRODUCT_VERSION: None, CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_INPUT_FILE,
                        CLI_ARG_STORE_RESULT: False}
FP_RUN_ARGS_ID_MAX = {CLI_ARG_DRY_RUN: True, CLI_ARG_ENTITY_REF: DUMMY_PLAN_ID, CLI_ARG_ENVIRONMENT: DUMMY_ENV,
                      CLI_ARG_INCLUDE_DESCENDANTS: True, CLI_ARG_PRODUCT: DUMMY_PRODUCT,
                      CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION,
                      CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_PLAN_ID, CLI_ARG_STORE_RESULT: True}
FP_RUN_ARGS_ID_MIN = {CLI_ARG_DRY_RUN: False, CLI_ARG_ENTITY_REF: DUMMY_PLAN_ID, CLI_ARG_ENVIRONMENT: None,
                      CLI_ARG_INCLUDE_DESCENDANTS: False, CLI_ARG_PRODUCT: None, CLI_ARG_PRODUCT_BUILD: None,
                      CLI_ARG_PRODUCT_VERSION: None, CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_PLAN_ID,
                      CLI_ARG_STORE_RESULT: False}
FP_RUN_ARGS_NAME_MAX = {CLI_ARG_DRY_RUN: True, CLI_ARG_ENTITY_REF: DUMMY_PLAN, CLI_ARG_ENVIRONMENT: DUMMY_ENV,
                        CLI_ARG_INCLUDE_DESCENDANTS: True, CLI_ARG_PRODUCT: DUMMY_PRODUCT,
                        CLI_ARG_PRODUCT_BUILD: DUMMY_BUILD, CLI_ARG_PRODUCT_VERSION: DUMMY_VERSION,
                        CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_PLAN, CLI_ARG_STORE_RESULT: True}
FP_RUN_ARGS_NAME_MIN = {CLI_ARG_DRY_RUN: False, CLI_ARG_ENTITY_REF: DUMMY_PLAN, CLI_ARG_ENVIRONMENT: None,
                        CLI_ARG_INCLUDE_DESCENDANTS: False, CLI_ARG_PRODUCT: None, CLI_ARG_PRODUCT_BUILD: None,
                        CLI_ARG_PRODUCT_VERSION: None, CLI_ARG_RUN_ENTITY_SPEC: CLI_ARG_VAL_PLAN,
                        CLI_ARG_STORE_RESULT: False}

# expected footprint for detail actions
# [action, entity-type, entity-ref-kind, entity-ref, product-name, entity, version-id, build-id, environment-id]
FP_DA_EXP_ARGS_CASE_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_CASE, CLI_ENTITY_REF_KIND_NAME, DUMMY_CASE, DUMMY_PRODUCT,
                           DUMMY_CASE_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_CASE_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_CASE, CLI_ENTITY_REF_KIND_NAME, DUMMY_CASE, DUMMY_PRODUCT,
                           DUMMY_CASE_ID, None, None, None]
FP_DA_EXP_ARGS_CASE_ID_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_CASE, CLI_ENTITY_REF_KIND_ID, DUMMY_CASE_ID,
                              DUMMY_PRODUCT, DUMMY_CASE_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_CASE_ID_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_CASE, CLI_ENTITY_REF_KIND_ID, DUMMY_CASE_ID,
                              DUMMY_PRODUCT, DUMMY_CASE_ID, None, None, None]
FP_DA_EXP_ARGS_PLAN_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUMMY_PLAN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_PLAN_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUMMY_PLAN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, None, None, None]
FP_DA_EXP_ARGS_DUP_PROD_PLAN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUP_PLAN,
                                DUMMY_PRODUCT, DUP_PLAN_ID_DUMMY_PROD, None, None, None]
FP_DA_EXP_ARGS_DUP_PROD_VER_PLAN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUP_PLAN,
                                    DUP_PRODUCT, DUP_PLAN_ID_UNIQUE_VER, UNIQUE_VERSION_ID, None, None]
FP_DA_EXP_ARGS_PLAN_ID_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_ID, DUMMY_PLAN_ID,
                              DUMMY_PRODUCT, DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_PLAN_ID_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_ID, DUMMY_PLAN_ID,
                              DUMMY_PRODUCT, DUMMY_PLAN_ID, None, None, None]
FP_DA_EXP_ARGS_PROD_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PRODUCT, CLI_ENTITY_REF_KIND_NAME, DUMMY_PRODUCT,
                           DUMMY_PRODUCT, DUMMY_PRODUCT_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_PROD_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PRODUCT, CLI_ENTITY_REF_KIND_NAME, DUMMY_PRODUCT,
                           DUMMY_PRODUCT, DUMMY_PRODUCT_ID, None, None, None]
FP_DA_EXP_ARGS_PROD_ID_MAX = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PRODUCT, CLI_ENTITY_REF_KIND_ID, DUMMY_PRODUCT_ID,
                              DUMMY_PRODUCT, DUMMY_PRODUCT_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_EXP_ARGS_PROD_ID_MIN = [CLI_ACTION_EXPORT, CLI_ENTITY_TYPE_PRODUCT, CLI_ENTITY_REF_KIND_ID, DUMMY_PRODUCT_ID,
                              DUMMY_PRODUCT, DUMMY_PRODUCT_ID, None, None, None]
FP_DA_IMP_ARGS_MAX = [CLI_ACTION_IMPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_FILE, DUMMY_FN, None,
                      DUMMY_PLAN_ID, None, None, None]
FP_DA_IMP_ARGS_MIN = [CLI_ACTION_IMPORT, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_FILE, DUMMY_FN, None,
                      DUMMY_PLAN_ID, None, None, None]
FP_DA_RUN_ARGS_ID_MAX = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_ID, DUMMY_PLAN_ID, DUMMY_PRODUCT,
                         DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_ID_MIN = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_ID, DUMMY_PLAN_ID, DUMMY_PRODUCT,
                         DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_FILE_MAX = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_FILE, DUMMY_FN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_FILE_MIN = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_FILE, DUMMY_FN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_NAME_MAX = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUMMY_PLAN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_NAME_MIN = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUMMY_PLAN, DUMMY_PRODUCT,
                           DUMMY_PLAN_ID, DUMMY_VERSION_ID, DUMMY_BUILD_ID, None]
FP_DA_RUN_ARGS_NAME_NONEXISTING_BUILD = [CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, CLI_ENTITY_REF_KIND_NAME, DUMMY_PLAN,
                                         DUMMY_PRODUCT, DUMMY_PLAN_ID, DUMMY_VERSION_ID, NON_EXISTING_BUILD, None]
FP_OPT_EXP_ARGS_CASE_MAX = {OPTION_BUILD: DUMMY_BUILD_ID, OPTION_INCLUDE_ATTACHMENTS: True,
                            OPTION_INCLUDE_ENVIRONMENTS: True, OPTION_INCLUDE_HISTORY: True, OPTION_INCLUDE_RUNS: True,
                            OPTION_VERSION: DUMMY_VERSION_ID}
FP_OPT_EXP_ARGS_CASE_MIN = {OPTION_BUILD: None, OPTION_INCLUDE_ATTACHMENTS: False, OPTION_INCLUDE_ENVIRONMENTS: False,
                            OPTION_INCLUDE_HISTORY: False, OPTION_INCLUDE_RUNS: False, OPTION_VERSION: None}
FP_OPT_EXP_ARGS_PLAN_MAX = {OPTION_BUILD: DUMMY_BUILD_ID, OPTION_INCLUDE_ATTACHMENTS: True,
                            OPTION_INCLUDE_ENVIRONMENTS: True, OPTION_INCLUDE_HISTORY: True, OPTION_INCLUDE_RUNS: True,
                            OPTION_PLAN_TREE: True, OPTION_VERSION: DUMMY_VERSION_ID}
FP_OPT_EXP_ARGS_PLAN_MIN = {OPTION_BUILD: None, OPTION_INCLUDE_ATTACHMENTS: False, OPTION_INCLUDE_ENVIRONMENTS: False,
                            OPTION_INCLUDE_HISTORY: False, OPTION_INCLUDE_RUNS: False, OPTION_PLAN_TREE: False,
                            OPTION_VERSION: None}
FP_OPT_EXP_ARGS_PROD_MAX = {OPTION_BUILD: DUMMY_BUILD_ID, OPTION_INCLUDE_ATTACHMENTS: True,
                            OPTION_INCLUDE_ENVIRONMENTS: True, OPTION_INCLUDE_HISTORY: True, OPTION_INCLUDE_RUNS: True,
                            OPTION_VERSION: DUMMY_VERSION_ID}
FP_OPT_EXP_ARGS_PROD_MIN = {OPTION_BUILD: None, OPTION_INCLUDE_ATTACHMENTS: False, OPTION_INCLUDE_ENVIRONMENTS: False,
                            OPTION_INCLUDE_HISTORY: False, OPTION_INCLUDE_RUNS: False, OPTION_VERSION: None}
FP_OPT_IMP_ARGS_MAX = {OPTION_AUTO_CREATE: True, OPTION_DRY_RUN: True, OPTION_INCLUDE_ATTACHMENTS: True,
                       OPTION_INCLUDE_ENVIRONMENTS: True, OPTION_USER_REFERENCES: OPTION_VALUE_USER_REF_REPLACE_ALWAYS}
FP_OPT_IMP_ARGS_MIN = {OPTION_AUTO_CREATE: False, OPTION_DRY_RUN: False, OPTION_INCLUDE_ATTACHMENTS: False,
                       OPTION_INCLUDE_ENVIRONMENTS: False, OPTION_USER_REFERENCES: OPTION_VALUE_USER_REF_REPLACE_NEVER}
FP_OPT_RUN_ARGS_NAME_MAX = {OPTION_DRY_RUN: True, OPTION_ENVIRONMENT: DUMMY_ENV_ID, OPTION_PLAN_TREE: True,
                            OPTION_BUILD: DUMMY_BUILD_ID, OPTION_STORE_RESULT: True, OPTION_VERSION: DUMMY_VERSION_ID}
FP_OPT_RUN_ARGS_ID_MIN = {OPTION_DRY_RUN: False, OPTION_ENVIRONMENT: None, OPTION_PLAN_TREE: False,
                          OPTION_BUILD: None, OPTION_STORE_RESULT: False, OPTION_VERSION: None}


class TestCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        IMP_ARGS_MIN[-1] = test_file_path(CLI_ENTITY_TYPE_PLAN, IMP_ARGS_MIN[-1])
        IMP_ARGS_MAX[-1] = test_file_path(CLI_ENTITY_TYPE_PLAN, IMP_ARGS_MAX[-1])
        RUN_ARGS_FILE_MAX[-1] = test_file_path(CLI_ENTITY_TYPE_PLAN, RUN_ARGS_FILE_MAX[-1])
        RUN_ARGS_FILE_MIN[-1] = test_file_path(CLI_ENTITY_TYPE_PLAN, RUN_ARGS_FILE_MIN[-1])
        FP_IMP_ARGS_MAX[CLI_ARG_INPUT_FILE] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_IMP_ARGS_MAX[CLI_ARG_INPUT_FILE])
        FP_IMP_ARGS_MIN[CLI_ARG_INPUT_FILE] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_IMP_ARGS_MIN[CLI_ARG_INPUT_FILE])
        FP_RUN_ARGS_FILE_MAX[CLI_ARG_ENTITY_REF] = test_file_path(CLI_ENTITY_TYPE_PLAN,
                                                                  FP_RUN_ARGS_FILE_MAX[CLI_ARG_ENTITY_REF])
        FP_RUN_ARGS_FILE_MIN[CLI_ARG_ENTITY_REF] = test_file_path(CLI_ENTITY_TYPE_PLAN,
                                                                  FP_RUN_ARGS_FILE_MIN[CLI_ARG_ENTITY_REF])
        FP_DA_IMP_ARGS_MAX[3] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_DA_IMP_ARGS_MAX[3])
        FP_DA_IMP_ARGS_MIN[3] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_DA_IMP_ARGS_MIN[3])
        FP_DA_RUN_ARGS_FILE_MAX[3] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_DA_RUN_ARGS_FILE_MAX[3])
        FP_DA_RUN_ARGS_FILE_MIN[3] = test_file_path(CLI_ENTITY_TYPE_PLAN, FP_DA_RUN_ARGS_FILE_MAX[3])

    def test_parse_arguments_for_action(self):
        """
        Tests plain argument parsing for all actions.
        """
        # export
        self.check_parsed_arguments(EXP_ARGS_CASE_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_CASE_MIN)
        self.check_parsed_arguments(EXP_ARGS_CASE_ID_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_CASE_ID_MIN)
        self.check_parsed_arguments(EXP_ARGS_PLAN_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_PLAN_MIN)
        self.check_parsed_arguments(EXP_ARGS_PLAN_ID_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_PLAN_ID_MIN)
        self.check_parsed_arguments(EXP_ARGS_PROD_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_PROD_MIN)
        self.check_parsed_arguments(EXP_ARGS_PROD_ID_MIN, CLI_ACTION_EXPORT, FP_EXP_ARGS_PROD_ID_MIN)
        self.check_parsed_arguments(EXP_ARGS_CASE_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_CASE_MAX)
        self.check_parsed_arguments(EXP_ARGS_CASE_ID_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_CASE_ID_MAX)
        self.check_parsed_arguments(EXP_ARGS_PLAN_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_PLAN_MAX)
        self.check_parsed_arguments(EXP_ARGS_PLAN_ID_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_PLAN_ID_MAX)
        self.check_parsed_arguments(EXP_ARGS_PROD_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_PROD_MAX)
        self.check_parsed_arguments(EXP_ARGS_PROD_ID_MAX, CLI_ACTION_EXPORT, FP_EXP_ARGS_PROD_ID_MAX)
        self.check_parsed_arguments(EXP_ARGS_NO_ARGS, CLI_ACTION_EXPORT, {}, True)
        self.check_parsed_arguments(EXP_ARGS_INV_ENTITY_SPEC, CLI_ACTION_EXPORT, {}, True)
        self.check_parsed_arguments(EXP_ARGS_INV_OPTION, CLI_ACTION_EXPORT, {}, True)
        self.check_parsed_arguments(EXP_ARGS_NO_ENTITY, CLI_ACTION_EXPORT, {}, True)
        self.check_parsed_arguments(EXP_ARGS_NO_OUTPUT_PATH, CLI_ACTION_EXPORT, {}, True)
        # import
        self.check_parsed_arguments(IMP_ARGS_MIN, CLI_ACTION_IMPORT, FP_IMP_ARGS_MIN)
        self.check_parsed_arguments(IMP_ARGS_MAX, CLI_ACTION_IMPORT, FP_IMP_ARGS_MAX)
        self.check_parsed_arguments(IMP_ARGS_NO_FILE_NAME, CLI_ACTION_IMPORT, {}, True)
        self.check_parsed_arguments(IMP_ARGS_INV_OPTION, CLI_ACTION_IMPORT, {}, True)
        self.check_parsed_arguments(IMP_ARGS_INV_ACU_VALUE, CLI_ACTION_IMPORT, {}, True)
        # run
        self.check_parsed_arguments(RUN_ARGS_FILE_MIN, CLI_ACTION_RUN, FP_RUN_ARGS_FILE_MIN)
        self.check_parsed_arguments(RUN_ARGS_ID_MIN, CLI_ACTION_RUN, FP_RUN_ARGS_ID_MIN)
        self.check_parsed_arguments(RUN_ARGS_NAME_MIN, CLI_ACTION_RUN, FP_RUN_ARGS_NAME_MIN)
        self.check_parsed_arguments(RUN_ARGS_FILE_MAX, CLI_ACTION_RUN, FP_RUN_ARGS_FILE_MAX)
        self.check_parsed_arguments(RUN_ARGS_ID_MAX, CLI_ACTION_RUN, FP_RUN_ARGS_ID_MAX)
        self.check_parsed_arguments(RUN_ARGS_NAME_MAX, CLI_ACTION_RUN, FP_RUN_ARGS_NAME_MAX)
        self.check_parsed_arguments(RUN_ARGS_NO_ARGS, CLI_ACTION_RUN, {}, True)
        self.check_parsed_arguments(RUN_ARGS_INV_ENTITY_SPEC, CLI_ACTION_RUN, {}, True)
        self.check_parsed_arguments(RUN_ARGS_INV_OPTION, CLI_ACTION_RUN, {}, True)
        self.check_parsed_arguments(RUN_ARGS_NO_FILE, CLI_ACTION_RUN, {}, True)
        self.check_parsed_arguments(RUN_ARGS_NO_ID, CLI_ACTION_RUN, {}, True)
        self.check_parsed_arguments(RUN_ARGS_NO_NAME, CLI_ACTION_RUN, {}, True)

    def test_detail_action_for_exp(self):
        """
        Tests detailed argument parsing for action export.
        """
        self.check_detail_action(EXP_ARGS_CASE_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_CASE_MIN)
        self.check_detail_action(EXP_ARGS_CASE_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_CASE_MAX)
        self.check_detail_action(EXP_ARGS_CASE_ID_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_CASE_ID_MIN)
        self.check_detail_action(EXP_ARGS_CASE_ID_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_CASE_ID_MAX)
        self.check_detail_action(EXP_ARGS_PLAN_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PLAN_MIN)
        self.check_detail_action(EXP_ARGS_PLAN_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PLAN_MAX)
        self.check_detail_action(EXP_ARGS_DUP_PROD_PLAN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_DUP_PROD_PLAN)
        self.check_detail_action(EXP_ARGS_DUP_PROD_VER_PLAN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_DUP_PROD_VER_PLAN)
        self.check_detail_action(EXP_ARGS_PLAN_ID_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PLAN_ID_MIN)
        self.check_detail_action(EXP_ARGS_PLAN_ID_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PLAN_ID_MAX)
        self.check_detail_action(EXP_ARGS_PROD_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PROD_MIN)
        self.check_detail_action(EXP_ARGS_PROD_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PROD_MAX)
        self.check_detail_action(EXP_ARGS_PROD_ID_MIN, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PROD_ID_MIN)
        self.check_detail_action(EXP_ARGS_PROD_ID_MAX, CLI_ACTION_EXPORT, FP_DA_EXP_ARGS_PROD_ID_MAX)
        self.check_detail_action(EXP_ARGS_DUP_PLAN_NO_PRODUCT, CLI_ACTION_EXPORT, [], True)
        self.check_detail_action(EXP_ARGS_DUP_PROD_PLAN_NO_VERSION, CLI_ACTION_EXPORT, [], True)
        self.check_detail_action(EXP_ARGS_DUP_VERSION_PLAN, CLI_ACTION_EXPORT, [], True)

    def test_detail_action_for_imp(self):
        """
        Tests detailed argument parsing for action import.
        """
        self.check_detail_action(IMP_ARGS_MIN, CLI_ACTION_IMPORT, FP_DA_IMP_ARGS_MIN)
        self.check_detail_action(IMP_ARGS_MAX, CLI_ACTION_IMPORT, FP_DA_IMP_ARGS_MAX)
        self.check_detail_action(IMP_ARGS_NON_EXISTING_FILE, CLI_ACTION_IMPORT, [], True)

    def test_detail_action_for_run(self):
        """
        Tests detailed argument parsing for action run.
        """
        if test_runs_in_multi_version_dataset():
            # for products with multiple versions, option --product-version must be specified
            self.check_detail_action(RUN_ARGS_ID_MIN, CLI_ACTION_RUN, [], True)
            self.check_detail_action(RUN_ARGS_NAME_MIN, CLI_ACTION_RUN, [], True)
        else:
            self.check_detail_action(RUN_ARGS_ID_MIN, CLI_ACTION_RUN, FP_DA_RUN_ARGS_ID_MIN)
            self.check_detail_action(RUN_ARGS_NAME_MIN, CLI_ACTION_RUN, FP_DA_RUN_ARGS_NAME_MIN)
        if test_runs_in_multi_build_dataset():
            # for products with multiple builds, option --product-build must be specified explicitly
            self.check_detail_action(RUN_ARGS_ID_MISSING_BUILD, CLI_ACTION_RUN, [], True)
            self.check_detail_action(RUN_ARGS_NAME_MISSING_BUILD, CLI_ACTION_RUN, [], True)
        else:
            self.check_detail_action(RUN_ARGS_ID_MISSING_BUILD, CLI_ACTION_RUN, FP_DA_RUN_ARGS_ID_MIN)
            self.check_detail_action(RUN_ARGS_NAME_MISSING_BUILD, CLI_ACTION_RUN,
                                     FP_DA_RUN_ARGS_NAME_NONEXISTING_BUILD)
        self.check_detail_action(RUN_ARGS_ID_MAX, CLI_ACTION_RUN, FP_DA_RUN_ARGS_ID_MAX)
        self.check_detail_action(RUN_ARGS_NAME_NON_EXISTING_BUILD, CLI_ACTION_RUN,
                                 FP_DA_RUN_ARGS_NAME_NONEXISTING_BUILD)
        self.check_detail_action(RUN_ARGS_ID_NON_EXISTING_ID, CLI_ACTION_RUN, [], True)
        self.check_detail_action(RUN_ARGS_ID_NON_EXISTING_VERSION, CLI_ACTION_RUN, [], True)
        self.check_detail_action(RUN_ARGS_FILE_MIN, CLI_ACTION_RUN, FP_DA_RUN_ARGS_FILE_MIN)
        self.check_detail_action(RUN_ARGS_FILE_MAX, CLI_ACTION_RUN, FP_DA_RUN_ARGS_FILE_MAX)
        self.check_detail_action(RUN_ARGS_NAME_MAX, CLI_ACTION_RUN, FP_DA_RUN_ARGS_NAME_MAX)
        self.check_detail_action(RUN_ARGS_NAME_NON_EXISTING_NAME, CLI_ACTION_RUN, [], True)
        self.check_detail_action(RUN_ARGS_NAME_NON_EXISTING_VERSION, CLI_ACTION_RUN, [], True)

    def test_options_for(self):
        """
        Tests option parsing for all actions.
        """
        # export
        self.check_options(EXP_ARGS_CASE_MIN, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_CASE_MIN)
        self.check_options(EXP_ARGS_CASE_MAX, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_CASE_MAX)
        self.check_options(EXP_ARGS_PLAN_MIN, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_PLAN_MIN)
        self.check_options(EXP_ARGS_PLAN_MAX, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_PLAN_MAX)
        self.check_options(EXP_ARGS_PROD_MIN, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_PROD_MIN)
        self.check_options(EXP_ARGS_PROD_MAX, CLI_ACTION_EXPORT, FP_OPT_EXP_ARGS_PROD_MAX)
        # import
        self.check_options(IMP_ARGS_MIN, CLI_ACTION_IMPORT, FP_OPT_IMP_ARGS_MIN)
        self.check_options(IMP_ARGS_MAX, CLI_ACTION_IMPORT, FP_OPT_IMP_ARGS_MAX)
        # run
        # self.check_options(RUN_ARGS_ID_MIN, CLI_ACTION_RUN, FP_OPT_RUN_ARGS_ID_MIN)
        self.check_options(RUN_ARGS_NAME_MAX, CLI_ACTION_RUN, FP_OPT_RUN_ARGS_NAME_MAX)
        # self.check_options(RUN_ARGS_NAME_NON_EXISTING_BUILD, CLI_ACTION_RUN, FP_OPT_RUN_ARGS_NAME_NON_EXISTING_BUILD)

    def check_parsed_arguments(self, args, action, expected_values, error_expected=False):
        """
        Verifies that arguments are parsed with expected values.
        :param list[str] args: the command line arguments
        :param int action: the CLI action
        :param dict expected_values: the expected argument values
        :param bool error_expected: indicates whether an error is expected or not
        """
        if error_expected:
            try:
                _args = parse_arguments_for_action(args, action)
                self.assertTrue(False, 'SystemExit expected')
            except SystemExit:
                return
        _args = parse_arguments_for_action(args, action)
        _args_dict = vars(_args)
        for _k, _v in expected_values.items():
            _arg_name = _k.replace('-', '_')
            self.assertEqual(_v, _args_dict[_arg_name])

    def check_detail_action(self, args, action, expected_values, error_expected=False):
        """
        Verifies that arguments are parsed with expected values.
        :param list[str] args: the command line arguments
        :param int action: the CLI action
        :param list expected_values: the expected action values
        :param bool error_expected: indicates whether an error is expected or not
        """
        if error_expected:
            try:
                _action = TestCommon.parse_detail_action(args, action)
                self.assertTrue(False, 'IssaiException expected')
            except IssaiException:
                return
        _action = TestCommon.parse_detail_action(args, action)
        _expected_action = TestCommon.expected_detail_action_from(expected_values)
        self.assertEqual(_expected_action.base_action(), _action.base_action())
        self.assertEqual(_expected_action.entity_type(), _action.entity_type())
        self.assertEqual(_expected_action.entity_ref_kind(), _action.entity_ref_kind())
        self.assertEqual(_expected_action.entity_ref(), str(_action.entity_ref()))
        self.assertEqual(_expected_action.product_name(), _action.product_name())
        self.verify_object(_expected_action.entity(), _action.entity())
        self.verify_object(_expected_action.version(), _action.version())
        self.verify_object(_expected_action.build(), _action.build())

    def check_options(self, args, action, expected_values, error_expected=False):
        """
        Verifies that options are parsed with expected values.
        :param list[str] args: the command line arguments
        :param int action: the CLI action
        :param dict expected_values: the expected option values
        :param bool error_expected: indicates whether an error is expected or not
        """
        if error_expected:
            try:
                _options = TestCommon.parse_options(args, action)
                self.assertTrue(False, 'IssaiException expected')
            except IssaiException:
                return
        _options = TestCommon.parse_options(args, action)
        self.assertEqual(expected_values.keys(), _options.keys())
        for _k, _v in _options.items():
            if _k == OPTION_VERSION or _k == OPTION_ENVIRONMENT:
                if _v is None:
                    self.assertIsNone(expected_values[_k])
                else:
                    self.assertEqual(int(expected_values[_k]), _v[ATTR_ID])
                continue
            if _k == OPTION_BUILD:
                if _v is None:
                    self.assertIsNone(expected_values[_k])
                    continue
                if isinstance(_v, dict):
                    self.assertEqual(int(expected_values[_k]), _v[ATTR_ID])
                else:
                    self.assertEqual(expected_values[_k], _v)
                continue
            self.assertEqual(expected_values[_k], _v, f'option {_k}')

    def verify_object(self, expected_id, actual_object):
        """
        Verifies that an actual object has expected ID.
        :param str expected_id: the expected ID
        :param dict actual_object: the actual object
        """
        if expected_id is None:
            self.assertIsNone(actual_object)
            return
        if expected_id.isnumeric():
            _actual_id = actual_object.get(ATTR_ID)
            if _actual_id is None:
                _actual_id = actual_object.get(ATTR_ENTITY_ID)
            self.assertEqual(expected_id, str(_actual_id))
            return
        self.assertEqual(expected_id, actual_object)

    @staticmethod
    def parse_detail_action(args, action):
        """
        Combines calls to CLI functions parse_arguments_for_action and detail_action_for.
        :param list[str] args: the command line arguments
        :param int action: the CLI action
        :returns: detailed action
        :rtype: DetailAction
        """
        _parsed_args = parse_arguments_for_action(args, action)
        if action == CLI_ACTION_RUN:
            return detail_action_for_run(_parsed_args)
        if action == CLI_ACTION_IMPORT:
            return detail_action_for_import(_parsed_args)
        return detail_action_for_export(_parsed_args)

    @staticmethod
    def expected_detail_action_from(values):
        """
        Creates an expected detail action from string arguments.
        :param list values: the command line arguments
        :returns: detailed action
        :rtype: DetailAction
        """
        _action = DetailAction(values[0], values[1], values[2], values[3])
        _action.set_product_name(values[4])
        _action.set_entity(values[5])
        _action.set_version(values[6])
        _action.set_build(values[7])
        _action.set_environment(values[8])
        return _action

    @staticmethod
    def parse_options(args, action):
        """
        Combines calls to CLI functions parse_arguments_for_action, detail_action_for and options_for.
        :param list[str] args: the command line arguments
        :param int action: the CLI action
        :returns: options
        :rtype: dict
        """
        _parsed_args = parse_arguments_for_action(args, action)
        _detail_action = TestCommon.parse_detail_action(args, action)
        return options_for(_parsed_args, _detail_action)


if __name__ == '__main__':
    unittest.main()
