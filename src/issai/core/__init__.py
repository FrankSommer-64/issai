# -----------------------------------------------------------------------------------------------
# issai - front end to run and export tests managed by Kiwi test case management system
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
Package with core functions
"""

# Package version
VERSION = '0.5'

ATTACHMENTS_CASE_DIR = 'case'
ATTACHMENTS_ENTITY_DIR = 'entity'
ATTACHMENTS_EXECUTION_DIR = 'execution'
ATTACHMENTS_PLAN_DIR = 'plan'
ATTACHMENTS_ROOT_DIR = 'attachments'
ATTACHMENTS_RUN_DIR = 'run'
DEFAULT_OUTPUT_LOG = 'console.log'
DEFAULT_USER_NAME = 'issai'
ISSAI_CONFIG_PATH = '~/.config/issai'
ISSAI_GUI_SETTINGS_FILE_NAME = 'gui_settings.toml'
ISSAI_MASTER_CONFIG_FILE_NAME = 'default.toml'
ISSAI_PRODUCT_CONFIG_FILE_NAME = 'product.toml'
TCMS_XML_RPC_CREDENTIALS_FILE_PATH = '~/.tcms.conf'

# GUI actions
ACTION_NONE = 0
ACTION_RUN_TCMS_PLAN = 0x10
ACTION_RUN_OFFLINE_PLAN = 0x20
ACTION_EXPORT = 0x40
ACTION_EXPORT_CASE = 0x41
ACTION_EXPORT_PLAN = 0x42
ACTION_EXPORT_PRODUCT = 0x43
ACTION_IMPORT = 0x80

# runner assistant actions
ASSISTANT_ACTION_INIT = 1
ASSISTANT_ACTION_CLEANUP = -1

# issai specific entity attributes
ATTR_CASE_CATEGORIES = 'case-categories'
ATTR_CASE_COMPONENTS = 'case-components'
ATTR_CASE_NAME = 'case-name'
ATTR_CASE_PRIORITIES = 'case-priorities'
ATTR_CASE_RESULTS = 'case-results'
ATTR_CASE_STATUSES = 'case-statuses'
ATTR_CHILD_PLAN_RESULTS = 'child-plan-results'
ATTR_ENVIRONMENTS = 'environments'
ATTR_ENTITY_ID = 'entity-id'
ATTR_ENTITY_NAME = 'entity-name'
ATTR_ENTITY_TYPE = 'entity-type'
ATTR_EXECUTION_STATUSES = 'execution-statuses'
ATTR_MASTER_DATA = 'master-data'
ATTR_OUTPUT_FILES = 'output-files'
ATTR_PLAN_NAME = 'plan-name'
ATTR_PLAN_TYPES = 'plan-types'
ATTR_PRODUCT_BUILDS = 'product-builds'
ATTR_PRODUCT_CLASSIFICATIONS = 'product-classifications'
ATTR_PRODUCT_VERSIONS = 'product-versions'
ATTR_TCMS_USERS = 'tcms-users'
ATTR_TEST_CASE_RESULTS = 'test-case-results'
ATTR_TEST_CASES = 'test-cases'
ATTR_TEST_EXECUTIONS = 'test-executions'
ATTR_TESTER_NAME = 'tester-name'
ATTR_TEST_PLAN_RESULTS = 'test-plan-results'
ATTR_TEST_PLANS = 'test-plans'
ATTR_TEST_RUNS = 'test-runs'

# general entity attributes
ATTR_ACTUAL_DURATION = 'actual_duration'
ATTR_ARGUMENTS = 'arguments'
ATTR_ASSIGNEE = 'assignee'
ATTR_ATTACHMENTS = 'attachments'
ATTR_AUTHOR = 'author'
ATTR_DEFAULT_TESTER = 'default_tester'
ATTR_BUGS = 'bugs'
ATTR_BUILD = 'build'
ATTR_CASE = 'case'
ATTR_CASES = 'cases'
ATTR_CASE_STATUS = 'case_status'
ATTR_CATEGORY = 'category'
ATTR_CC_NOTIFICATIONS = 'cc_notifications'
ATTR_CLASSIFICATION = 'classification'
ATTR_COLOR = 'color'
ATTR_COMMENT = 'comment'
ATTR_COMMENTS = 'comments'
ATTR_COMPONENT = 'component'
ATTR_COMPONENTS = 'components'
ATTR_DESCRIPTION = 'description'
ATTR_EMAIL = 'email'
ATTR_ENVIRONMENT = 'environment'
ATTR_EXECUTION = 'execution'
ATTR_EXECUTION_ID = 'execution_id'
ATTR_EXECUTIONS = 'executions'
ATTR_EXPECTED_DURATION = 'expected_duration'
ATTR_EXTRA_LINK = 'extra_link'
ATTR_FIRST_NAME = 'first_name'
ATTR_HISTORY = 'history'
ATTR_HISTORY_CHANGE_REASON = 'history_change_reason'
ATTR_HISTORY_DATE = 'history_date'
ATTR_HISTORY_ID = 'history_id'
ATTR_HISTORY_TYPE = 'history_type'
ATTR_HISTORY_USER_ID = 'history_user_id'
ATTR_HISTORY_USER_USERNAME = 'history_user__username'
ATTR_ICON = 'icon'
ATTR_ID = 'id'
ATTR_INITIAL_OWNER = 'initial_owner'
ATTR_INITIAL_QA_CONTACT = 'initial_qa_contact'
ATTR_IS_ACTIVE = 'is_active'
ATTR_IS_AUTOMATED = 'is_automated'
ATTR_IS_CONFIRMED = 'is_confirmed'
ATTR_IS_PUBLIC = 'is_public'
ATTR_IS_REMOVED = 'is_removed'
ATTR_IS_STAFF = 'is_staff'
ATTR_IS_SUPERUSER = 'is_superuser'
ATTR_LAST_NAME = 'last_name'
ATTR_LINKS = 'links'
ATTR_MANAGER = 'manager'
ATTR_NAME = 'name'
ATTR_NOTES = 'notes'
ATTR_PARENT = 'parent'
ATTR_PLAN = 'plan'
ATTR_PLANNED_START = 'planned_start'
ATTR_PLANNED_STOP = 'planned_stop'
ATTR_PRIORITY = 'priority'
ATTR_PRODUCT = 'product'
ATTR_PRODUCT_VERSION = 'product_version'
ATTR_PROPERTIES = 'properties'
ATTR_REQUIREMENT = 'requirement'
ATTR_REVIEWER = 'reviewer'
ATTR_RUN = 'run'
ATTR_RUN_ID = 'run_id'
ATTR_RUNS = 'runs'
ATTR_SCRIPT = 'script'
ATTR_SETUP_DURATION = 'setup_duration'
ATTR_START_DATE = 'start_date'
ATTR_STATUS = 'status'
ATTR_STOP_DATE = 'stop_date'
ATTR_SUBMIT_DATE = 'submit_date'
ATTR_SUMMARY = 'summary'
ATTR_TAGS = 'tags'
ATTR_TESTED_BY = 'tested_by'
ATTR_TESTING_DURATION = 'testing_duration'
ATTR_TEXT = 'text'
ATTR_TYPE = 'type'
ATTR_URL = 'url'
ATTR_USER_ID = 'user_id'
ATTR_USERNAME = 'username'
ATTR_VALUE = 'value'
ATTR_VERSION = 'version'
ATTR_WEIGHT = 'weight'

# local configuration parameters
CFG_GROUP_ENV = 'env'
CFG_GROUP_PRODUCT = 'product'
CFG_GROUP_TCMS = 'tcms'
CFG_PAR_READ_ONLY_PATH = 'read-only-path'
CFG_PAR_TESTING_ROOT_PATH = 'testing-root-path'
CFG_PAR_PRODUCT_NAME = 'product.name'
CFG_PAR_PRODUCT_NATURE = 'product.nature'
CFG_PAR_PRODUCT_REPOSITORY_PATH = 'product.repository-path'
CFG_PAR_PRODUCT_SOURCE_PATH = 'product.source-path'
CFG_PAR_PRODUCT_TEST_DATA_PATH = 'product.test-data-path'
CFG_PAR_RUNNER_CASE_ASSISTANT = 'runner.case-assistant'
CFG_PAR_RUNNER_CUSTOM_MODULE_PATH = 'runner.custom-module-path'
CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH = 'runner.custom-script-path'
CFG_PAR_RUNNER_ENTITY_ASSISTANT = 'runner.entity-assistant'
CFG_PAR_RUNNER_ISSAI_CASE_PROPS = 'runner.issai-case-properties'
CFG_PAR_RUNNER_ISSAI_ENTITY_PROPS = 'runner.issai-entity-properties'
CFG_PAR_RUNNER_ISSAI_PLAN_PROPS = 'runner.issai-plan-properties'
CFG_PAR_RUNNER_OUTPUT_LOG = 'runner.output-log'
CFG_PAR_RUNNER_PLAN_ASSISTANT = 'runner.plan-assistant'
CFG_PAR_RUNNER_PY_VENV_PATH = 'runner.python-venv-path'
CFG_PAR_RUNNER_TEST_DRIVER_EXE = 'runner.test-driver-executable'
CFG_PAR_RUNNER_WORKING_PATH = 'runner.working-path'
CFG_PAR_TCMS_EXECUTION_STATES = 'tcms.execution-states'
CFG_PAR_TCMS_LABEL_SCHEME = 'tcms.label-scheme'
CFG_PAR_TCMS_RESULT_ATTACHMENTS = 'tcms.result-attachments'
CFG_PAR_TCMS_RESULT_MANAGEMENT = 'tcms.result-management'
CFG_PAR_TCMS_SPEC_ATTACHMENTS = 'tcms.spec-attachments'
CFG_PAR_TCMS_SPEC_MANAGEMENT = 'tcms.spec-management'
CFG_VAR_CONFIG_ROOT = 'config-root'

# entity type IDs
ENTITY_TYPE_PRODUCT = 0
ENTITY_TYPE_CASE = 1
ENTITY_TYPE_PLAN = 2
ENTITY_TYPE_PLAN_RESULT = 3

# entity type names
ENTITY_TYPE_NAME_PRODUCT = 'product'
ENTITY_TYPE_NAME_CASE = 'test-case'
ENTITY_TYPE_NAME_PLAN = 'test-plan'
ENTITY_TYPE_NAME_PLAN_RESULT = 'test-plan-result'

# environment variables
ENVA_ATTACHMENTS_PATH = 'ISSAI_ATTACHMENTS_PATH'
ENVA_ISSAI_CONFIG_PATH = 'ISSAI_CONFIG_PATH'
ENVA_ISSAI_USERNAME = 'ISSAI_USERNAME'
ENVA_PYTHON_PATH = 'PYTHONPATH'
ENVA_PREFIX_ISSAI = 'ISSAI_'

# options
OPTION_AUTO_CREATE = 'auto-create'
OPTION_BUILD = 'build'
OPTION_DRY_RUN = 'dry-run'
OPTION_ENVIRONMENT = 'environment'
OPTION_INCLUDE_ATTACHMENTS = 'include-attachments'
OPTION_INCLUDE_ENVIRONMENTS = 'include-environments'
OPTION_INCLUDE_HISTORY = 'include-history'
OPTION_INCLUDE_RUNS = 'include-runs'
OPTION_PLAN_TREE = 'plan-tree'
OPTION_STORE_RESULT = 'store-result'
OPTION_USER_REFERENCES = 'user-references'
OPTION_VALUE_USER_REF_REPLACE_ALWAYS = 'always'
OPTION_VALUE_USER_REF_REPLACE_MISSING = 'missing'
OPTION_VALUE_USER_REF_REPLACE_NEVER = 'never'
OPTION_VERSION = 'version'

# Platform
PLATFORM_ARCH_PREFIX = 'arch'
PLATFORM_OS_PREFIX = 'os'

# result statuses
RESULT_STATUS_ID_PASSED = 0
RESULT_STATUS_ID_FAILED = 1
RESULT_STATUS_ID_ERROR = 2
RESULT_STATUS_ID_BLOCKED = 3
RESULT_STATUS_ID_IDLE = 4
RESULT_STATUS_IDLE = 'IDLE'
RESULT_STATUS_PASSED = 'PASSED'
RESULT_STATUS_BLOCKED = 'BLOCKED'
RESULT_STATUS_ERROR = 'ERROR'
RESULT_STATUS_FAILED = 'FAILED'

# result types
RESULT_TYPE_CASE_RESULT = 4
RESULT_TYPE_PLAN_RESULT = ENTITY_TYPE_PLAN_RESULT

# runner types
RUNNER_TYPE_FUNCTION = 'function'
RUNNER_TYPE_SCRIPT = 'script'

# message severities
SEVERITY_ERROR = 'e'
SEVERITY_INFO = 'i'
SEVERITY_WARNING = 'w'

# TCMS class names
TCMS_CLASS_BUILD = 'Build'
TCMS_CLASS_CATEGORY = 'Category'
TCMS_CLASS_CLASSIFICATION = 'Classification'
TCMS_CLASS_COMMENT = 'Comment'
TCMS_CLASS_COMPONENT = 'Component'
TCMS_CLASS_ENVIRONMENT = 'Environment'
TCMS_CLASS_PLAN_TYPE = 'PlanType'
TCMS_CLASS_PRIORITY = 'Priority'
TCMS_CLASS_PRODUCT = 'Product'
TCMS_CLASS_TAG = 'Tag'
TCMS_CLASS_TEST_CASE = 'TestCase'
TCMS_CLASS_TEST_CASE_HISTORY = 'TestCaseHistory'
TCMS_CLASS_TEST_CASE_STATUS = 'TestCaseStatus'
TCMS_CLASS_TEST_EXECUTION = 'TestExecution'
TCMS_CLASS_TEST_EXECUTION_HISTORY = 'TestExecutionHistory'
TCMS_CLASS_TEST_EXECUTION_STATUS = 'TestExecutionStatus'
TCMS_CLASS_TEST_PLAN = 'TestPlan'
TCMS_CLASS_TEST_RUN = 'TestRun'
TCMS_CLASS_USER = 'User'
TCMS_CLASS_VERSION = 'Version'

# TCMS class IDs, sorted according to independency
TCMS_CLASS_ID_CLASSIFICATION = 1
TCMS_CLASS_ID_ENVIRONMENT = 2
TCMS_CLASS_ID_PLAN_TYPE = 3
TCMS_CLASS_ID_PRIORITY = 4
TCMS_CLASS_ID_TAG = 5
TCMS_CLASS_ID_TEST_CASE_STATUS = 6
TCMS_CLASS_ID_TEST_EXECUTION_STATUS = 7
TCMS_CLASS_ID_USER = 8
TCMS_CLASS_ID_PRODUCT = 9
TCMS_CLASS_ID_CATEGORY = 10
TCMS_CLASS_ID_TEST_CASE_HISTORY = 11
TCMS_CLASS_ID_TEST_EXECUTION_HISTORY = 12
TCMS_CLASS_ID_VERSION = 13
TCMS_CLASS_ID_BUILD = 14
TCMS_CLASS_ID_TEST_PLAN = 15
TCMS_CLASS_ID_TEST_RUN = 16
TCMS_CLASS_ID_TEST_CASE = 17
TCMS_CLASS_ID_TEST_EXECUTION = 18
TCMS_CLASS_ID_COMPONENT = 19
TCMS_CLASS_ID_COMMENT = 20
TCMS_CLASS_ID_MIN = 1
TCMS_CLASS_ID_MAX = 20

# task result codes
TASK_SUCCEEDED = 0
TASK_FAILED = 1

# test execution result codes
TEST_SUCCEEDED = 0
TEST_FAILED = 1
TEST_CRASHED = -1


def data_type_for_tcms_class(class_id):
    """
    :param int class_id: the TCMS class ID
    :returns: entity element name matching TCMS class ID
    :rtype: str
    """
    return _TCMS_CLASS_DATA_TYPES.get(class_id)


def tcms_class_id_for_master_data_type(data_type):
    """
    :param str data_type: the element's name
    :returns: TCMS class ID matching entity element name
    :rtype: int
    """
    return _MASTER_DATA_TYPE_TCMS_CLASS_IDS.get(data_type)


def master_data_type_for_tcms_class(class_id):
    """
    :param int class_id: the TCMS class ID
    :returns: master data element name matching TCMS class ID
    :rtype: str
    """
    return _MASTER_DATA_CLASS_DATA_TYPES.get(class_id)


def is_master_data_tcms_class(class_id):
    """
    :param int class_id: the TCMS class ID
    :returns: True, if specified TCMS class ID is part of entity master data
    :rtype: bool
    """
    return class_id in _MASTER_DATA_CLASS_DATA_TYPES.keys()


def tcms_class_name_for_id(tcms_class_id):
    """
    :param int tcms_class_id: the TCMS class ID
    :returns: TCMS class name for specified ID
    :rtype: str
    """
    if TCMS_CLASS_ID_MIN <= tcms_class_id <= TCMS_CLASS_ID_MAX:
        return _TCMS_CLASS_NAMES[tcms_class_id - 1]
    return ''


def name_attribute_for_tcms_class(tcms_class_id):
    """
    :param int tcms_class_id: the TCMS class ID
    :returns: name attribute for specified ID (usually 'name', but test case uses 'summary' and version uses 'value')
    :rtype: str
    """
    if TCMS_CLASS_ID_MIN <= tcms_class_id <= TCMS_CLASS_ID_MAX:
        return _TCMS_CLASS_NAME_ATTRIBUTES[tcms_class_id]
    return ''


_DATA_TYPE_TCMS_CLASS_IDS = {ATTR_CASE_CATEGORIES: TCMS_CLASS_ID_CATEGORY,
                             ATTR_CASE_COMPONENTS: TCMS_CLASS_ID_COMPONENT,
                             ATTR_CASE_PRIORITIES: TCMS_CLASS_ID_PRIORITY,
                             ATTR_CASE_STATUSES: TCMS_CLASS_ID_TEST_CASE_STATUS,
                             ATTR_EXECUTION_STATUSES: TCMS_CLASS_ID_TEST_EXECUTION_STATUS,
                             ATTR_PLAN_TYPES: TCMS_CLASS_ID_PLAN_TYPE,
                             ATTR_PRODUCT: TCMS_CLASS_ID_PRODUCT,
                             ATTR_PRODUCT_BUILDS: TCMS_CLASS_ID_BUILD,
                             ATTR_PRODUCT_CLASSIFICATIONS: TCMS_CLASS_ID_CLASSIFICATION,
                             ATTR_PRODUCT_VERSIONS: TCMS_CLASS_ID_VERSION,
                             ATTR_ENVIRONMENTS: TCMS_CLASS_ID_ENVIRONMENT,
                             ATTR_TCMS_USERS: TCMS_CLASS_ID_USER,
                             ATTR_TEST_CASES: TCMS_CLASS_TEST_CASE,
                             ATTR_TEST_EXECUTIONS: TCMS_CLASS_TEST_EXECUTION,
                             ATTR_TEST_PLANS: TCMS_CLASS_TEST_PLAN,
                             ATTR_TEST_RUNS: TCMS_CLASS_TEST_RUN}

_MASTER_DATA_TYPE_TCMS_CLASS_IDS = {ATTR_CASE_CATEGORIES: TCMS_CLASS_ID_CATEGORY,
                                    ATTR_CASE_COMPONENTS: TCMS_CLASS_ID_COMPONENT,
                                    ATTR_CASE_PRIORITIES: TCMS_CLASS_ID_PRIORITY,
                                    ATTR_CASE_STATUSES: TCMS_CLASS_ID_TEST_CASE_STATUS,
                                    ATTR_EXECUTION_STATUSES: TCMS_CLASS_ID_TEST_EXECUTION_STATUS,
                                    ATTR_PLAN_TYPES: TCMS_CLASS_ID_PLAN_TYPE,
                                    ATTR_PRODUCT_BUILDS: TCMS_CLASS_ID_BUILD,
                                    ATTR_PRODUCT_CLASSIFICATIONS: TCMS_CLASS_ID_CLASSIFICATION,
                                    ATTR_PRODUCT_VERSIONS: TCMS_CLASS_ID_VERSION,
                                    ATTR_TCMS_USERS: TCMS_CLASS_ID_USER}

_MASTER_DATA_CLASS_DATA_TYPES = {TCMS_CLASS_ID_CATEGORY: ATTR_CASE_CATEGORIES,
                                 TCMS_CLASS_ID_COMPONENT: ATTR_CASE_COMPONENTS,
                                 TCMS_CLASS_ID_PRIORITY: ATTR_CASE_PRIORITIES,
                                 TCMS_CLASS_ID_TEST_CASE_STATUS: ATTR_CASE_STATUSES,
                                 TCMS_CLASS_ID_TEST_EXECUTION_STATUS: ATTR_EXECUTION_STATUSES,
                                 TCMS_CLASS_ID_PLAN_TYPE: ATTR_PLAN_TYPES,
                                 TCMS_CLASS_ID_BUILD: ATTR_PRODUCT_BUILDS,
                                 TCMS_CLASS_ID_CLASSIFICATION: ATTR_PRODUCT_CLASSIFICATIONS,
                                 TCMS_CLASS_ID_VERSION: ATTR_PRODUCT_VERSIONS,
                                 TCMS_CLASS_ID_USER: ATTR_TCMS_USERS}

_TCMS_CLASS_DATA_TYPES = {TCMS_CLASS_ID_PRODUCT: ATTR_PRODUCT, TCMS_CLASS_ID_ENVIRONMENT: ATTR_ENVIRONMENTS,
                          TCMS_CLASS_ID_TEST_CASE: ATTR_TEST_CASES, TCMS_CLASS_ID_TEST_EXECUTION: ATTR_TEST_EXECUTIONS,
                          TCMS_CLASS_ID_TEST_PLAN: ATTR_TEST_PLANS, TCMS_CLASS_ID_TEST_RUN: ATTR_TEST_RUNS}

_TCMS_CLASS_NAMES = (TCMS_CLASS_CLASSIFICATION, TCMS_CLASS_ENVIRONMENT, TCMS_CLASS_PLAN_TYPE, TCMS_CLASS_PRIORITY,
                     TCMS_CLASS_TAG, TCMS_CLASS_TEST_CASE_STATUS, TCMS_CLASS_TEST_EXECUTION_STATUS, TCMS_CLASS_USER,
                     TCMS_CLASS_PRODUCT, TCMS_CLASS_CATEGORY, TCMS_CLASS_TEST_CASE_HISTORY,
                     TCMS_CLASS_TEST_EXECUTION_HISTORY, TCMS_CLASS_VERSION, TCMS_CLASS_BUILD, TCMS_CLASS_TEST_PLAN,
                     TCMS_CLASS_TEST_RUN, TCMS_CLASS_TEST_CASE, TCMS_CLASS_TEST_EXECUTION, TCMS_CLASS_COMPONENT)

_TCMS_CLASS_NAME_ATTRIBUTES = {TCMS_CLASS_ID_BUILD: ATTR_NAME, TCMS_CLASS_ID_CATEGORY: ATTR_NAME,
                               TCMS_CLASS_ID_CLASSIFICATION: ATTR_NAME, TCMS_CLASS_ID_COMPONENT: ATTR_NAME,
                               TCMS_CLASS_ID_ENVIRONMENT: ATTR_NAME, TCMS_CLASS_ID_PLAN_TYPE: ATTR_NAME,
                               TCMS_CLASS_ID_PRIORITY: ATTR_VALUE, TCMS_CLASS_ID_PRODUCT: ATTR_NAME,
                               TCMS_CLASS_ID_TAG: ATTR_NAME, TCMS_CLASS_ID_TEST_CASE: ATTR_SUMMARY,
                               TCMS_CLASS_ID_TEST_CASE_HISTORY: None, TCMS_CLASS_ID_TEST_CASE_STATUS: ATTR_NAME,
                               TCMS_CLASS_ID_TEST_EXECUTION: None, TCMS_CLASS_ID_TEST_EXECUTION_HISTORY: None,
                               TCMS_CLASS_ID_TEST_EXECUTION_STATUS: ATTR_NAME, TCMS_CLASS_ID_TEST_PLAN: ATTR_NAME,
                               TCMS_CLASS_ID_TEST_RUN: None, TCMS_CLASS_ID_USER: ATTR_USERNAME,
                               TCMS_CLASS_ID_VERSION: ATTR_VALUE}
