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
Localized message support.
"""

import os

from issai.core import (ASSISTANT_ACTION_INIT, ENTITY_TYPE_CASE, ENTITY_TYPE_CASE_RESULT,
                        ENTITY_TYPE_PLAN, ENTITY_TYPE_PLAN_RESULT)
from issai.core.util import platform_locale


# ===============================================================================================
# error message IDs
# ===============================================================================================

# configuration related messages
E_CFG_READ_FILE_FAILED = 'e-cfg-read-file-failed'
E_CFG_CUSTOM_CONFIG_ROOT_NOT_FOUND = 'e-cfg-custom-config-root-not-found'
E_CFG_CUSTOM_MOD_INVALID = 'e-cfg-custom-mod-invalid'
E_CFG_CUSTOM_MOD_NOT_DEFINED = 'e-cfg-custom-mod-not-defined'
E_CFG_CUSTOM_MOD_NOT_FOUND = 'e-cfg-custom-mod-not-found'
E_CFG_CUSTOM_RUNNER_FN_NOT_FOUND = 'e-cfg-custom-runner-fn-not-found'
E_CFG_GRP_NOT_TABLE = 'e-cfg-group-not-table'
E_CFG_RUNNER_SPEC_INVALID = 'e-cfg-runner-spec-invalid'
E_CFG_CUSTOM_SCRIPT_PATH_NOT_DEFINED = 'e-cfg-custom-script-path-not-defined'
E_CFG_CUSTOM_SCRIPT_PATH_NOT_FOUND = 'e-cfg-custom-script-path-not-found'
E_CFG_CUSTOM_SCRIPT_NOT_FOUND = 'e-cfg-custom-script-not-found'
E_CFG_DEFAULT_CONFIG_ROOT_NOT_FOUND = 'e-cfg-default-config-root-not-found'
E_CFG_ENV_VAR_NOT_DEFINED = 'e-cfg-env-var-not-defined'
E_CFG_PRODUCT_CONFIG_DIR_NOT_FOUND = 'e-cfg-product-config-dir-not-found'
E_CFG_PRODUCT_CONFIG_FILE_NOT_FOUND = 'e-cfg-product-config-file-not-found'
E_CFG_NO_PRODUCTS = 'e-cfg-no-products'
E_CFG_INVALID_DATA_TYPE = 'e-cfg-invalid-data-type'
E_CFG_INVALID_DIR_STRUCTURE = 'e-cfg-invalid-dir-structure'
E_CFG_INVALID_PAR_NAME = 'e-cfg-invalid-par-name'
E_CFG_INVALID_EXECUTION_STATUS = 'e-cfg-invalid-execution-status'
E_CFG_INVALID_PAR_VALUE = 'e-cfg-invalid-par-value'
E_CFG_MANDATORY_PAR_MISSING = 'e-cfg-mandatory-par-missing'
E_CFG_PRODUCT_CONFIG_INVALID = 'e-cfg-product-config-invalid'
E_CFG_VAR_NOT_DEFINED = 'e-cfg-var-not-defined'
E_CFG_VAR_REFERENCE_CYCLE = 'e-cfg-var-reference-cycle'
W_CFG_GRP_IGNORED_IN_MASTER = 'w-cfg-grp-ignored-in-master'
W_CFG_GRP_IGNORED = 'w-cfg-grp-ignored'
W_CFG_PAR_IGNORED = 'w-cfg-par-ignored'
W_CFG_PAR_RESERVED = 'w-cfg-par-reserved'

# General messages
E_ATTACHMENT_MISSING = 'e-attachment-missing'
E_BACKGROUND_TASK_ABORTED = 'e-background-task-aborted'
E_BACKGROUND_TASK_FAILED = 'e-background-task-failed'
E_CONTAINER_NOT_RUNNABLE = 'e-container-not-runnable'
E_DIR_NOT_EMPTY = 'e-dir-not-empty'
I_DOWNLOAD_ATTACHMENT = 'i-download-attachment'
I_DOWNLOAD_ATTACHMENTS = 'i-download-attachments'
I_UPLOAD_ATTACHMENT = 'i-upload-attachment'
E_DOWNLOAD_ATTACHMENT_FAILED = 'e-download-attachment-failed'
E_INTERNAL_ERROR = 'e-internal-error'
E_INVALID_ACTION = 'e-invalid-action'
E_INVALID_ENTITY_TYPE = 'e-invalid-entity-type'
E_LOAD_CONTAINER_FAILED = 'e-load-container-failed'
E_READ_FILE_FAILED = 'e-read-file-failed'
E_WRITE_FILE_FAILED = 'e-write-file-failed'

# export related
I_EXP_FETCH_CASE = 'i-exp-fetch-case'
I_EXP_FETCH_CASES = 'i-exp-fetch-cases'
I_EXP_FETCH_ENVIRONMENTS = 'i-exp-fetch-environments'
I_EXP_FETCH_EXECUTIONS = 'i-exp-fetch-executions'
I_EXP_FETCH_MASTER_DATA = 'i-exp-fetch-master-data'
I_EXP_FETCH_PLAN = 'i-exp-fetch-plan'
I_EXP_FETCH_PLAN_CASES = 'i-exp-fetch-plan-cases'
I_EXP_FETCH_PLANS = 'i-exp-fetch-plans'
I_EXP_FETCH_PRODUCT = 'i-exp-fetch-product'
I_EXP_WRITE_OUTPUT_FILE = 'i-exp-write-output-file'

# import related
E_DRY_RUN_IMP_MD_NO_MATCH = 'e-dry-run-imp-md-no-match'
E_DRY_RUN_IMP_OBJECT_MUST_EXIST = 'e-dry-run-imp-object-must-exist'
E_DRY_RUN_IMP_TCMS_OBJECT_MISSING = 'e-dry-run-imp-tcms-object-missing'
E_DRY_RUN_IMP_USER_NO_MATCH = 'e-dry-run-imp-user-no-match'
E_IMP_ATTR_TYPE_INVALID = 'e-imp-attr-type-invalid'
E_IMP_ATTR_VALUE_INVALID = 'e-imp-attr-value-invalid'
E_IMP_ATTR_MISMATCH = 'e-imp-attr-mismatch'
E_IMP_ATTR_MISSING = 'e-imp-attr-missing'
E_IMP_ATTR_AMBIGUOUS = 'e-imp-attr-ambiguous'
I_IMP_MD_EXACT_MATCH = 'i-imp-md-exact-match'
I_IMP_USER_EXACT_MATCH = 'i-imp-user-exact-match'
W_IMP_ATTR_NOT_SUPPORTED = 'w-imp-attr-not-supported'

E_IMP_MD_NO_MATCH = 'e-imp-md-no-match'
E_IMP_OBJECT_MUST_EXIST = 'e-imp-object-must-exist'
E_IMP_OWNING_OBJECT_MISMATCH = 'e-imp-owning-object-mismatch'
E_IMP_TCMS_OBJECT_MISSING = 'e-imp-tcms-object-missing'
E_IMP_CASE_RESULT_FAILED = 'e-imp-case-result-failed'
E_IMP_PLAN_RESULT_FAILED = 'e-imp-plan-result-failed'
E_IMP_USER_NO_MATCH = 'e-imp-user-no-match'
E_IMP_USER_NOT_FOUND = 'e-imp-user-not-found'

# runner related
E_RUN_ASSISTANT_FAILED = 'e-run-assistant-failed'
E_RUN_CANNOT_CREATE_TEST_RUN = 'e-run-cannot-create-test-run'
E_RUN_CASE_SCRIPT_MISSING = 'e-run-case-script-missing'
E_RUN_INVALID_ENV_PROPERTY_VALUE = 'e-run-invalid-env-property-value'
E_RUN_CASE_FAILED = 'e-run-case-failed'
E_RUN_PLAN_FAILED = 'e-run-plan-failed'
E_RUN_SOURCE_PATH_MISSING = 'e-run-source-path-missing'
E_RUN_SOURCE_PATH_INVALID = 'e-run-source-path-invalid'
E_RUN_WORKING_PATH_MISSING = 'e-run-working-path-missing'
E_RUN_WORKING_PATH_INVALID = 'e-run-working-path-invalid'
I_DRY_RUN_RUN_CREATING_EXECUTION = 'i-dry-run-run-creating-execution'
I_DRY_RUN_RUN_CREATING_RUN = 'i-dry-run-run-creating-run'
I_DRY_RUN_RUN_ENTITY_SKIPPED = 'i-dry-run-run-entity-skipped'
I_DRY_RUN_RUN_RUNNING_CASE = 'i-dry-run-run-running-case'
I_DRY_RUN_RUN_RUNNING_ENV = 'i-dry-run-run-running-env'
I_DRY_RUN_RUN_RUNNING_PLAN = 'i-dry-run-run-running-plan'
I_DRY_RUN_RUN_RUNNING_SCRIPT = 'i-dry-run-run-running-script'
I_RUN_ASSISTANT_SUCCEEDED = 'i-run-assistant-succeeded'
I_RUN_CASE_NOT_AUTOMATED = 'i-run-case-not-automated'
I_RUN_CREATING_EXECUTION = 'i-run-creating-execution'
I_RUN_CREATING_RUN = 'i-run-creating-run'
I_RUN_ENTITY_NOT_FOR_LOCAL_ARCH = 'i-run-entity-not-for-local-arch'
I_RUN_ENTITY_NOT_FOR_LOCAL_OS = 'i-run-entity-not-for-local-os'
I_RUN_ENTITY_SKIPPED = 'i-run-entity-skipped'
I_RUN_MATRIX_RESULT = 'i-run-matrix-result'
I_RUN_PLAN_NOT_ACTIVE = 'i-run-plan-not-active'
I_RUN_PLAN_SUCCEEDED = 'i-run-plan-succeeded'
I_RUN_RUNNING_CASE = 'i-run-running-case'
I_RUN_RUNNING_ENV = 'i-run-running-env'
I_RUN_RUNNING_PLAN = 'i-run-running-plan'
I_RUN_RUNNING_SCRIPT = 'i-run-running-script'

# entity related
E_TOML_ATTRIBUTE_MISSING = 'e-toml-attribute-missing'
E_TOML_ATTRIBUTE_WRONG_TYPE = 'e-toml-attribute-wrong-type'
E_TOML_ENTITY_ATTR_IMMUTABLE = 'e-toml-entity-attr-immutable'
E_TOML_ENTITY_ATTR_INVALID_TYPE = 'e-toml-entity-attr-invalid-type'
E_TOML_ENTITY_ATTR_NAME_INVALID = 'e-toml-entity-attr-name-invalid'
E_TOML_ENTITY_TYPE_INVALID = 'e-toml-entity-type-invalid'
E_TOML_MASTER_DATA_ATTR_INVALID_NAME = 'e-toml-master-data-attr-invalid-name'
E_TOML_MASTER_DATA_ATTR_INVALID_TYPE = 'e-toml-master-data-attr-invalid-type'
E_TOML_MASTER_DATA_TYPE_INVALID = 'e-toml-master-data-type-invalid'
E_TOML_MASTER_DATA_TYPE_NOT_ARRAY = 'e-toml-master-data-type-not-array'

# TCMS related
E_TCMS_AMBIGUOUS_RESULT = 'e-tcms-ambiguous-result'
E_TCMS_CHECK_MASTER_DATA_STATUS_FAILED = 'e-tcms-check-master-data-status-failed'
E_TCMS_CHECK_OBJECT_STATUS_FAILED = 'e-tcms-check-object-status-failed'
E_TCMS_ERROR = 'e-tcms-error'
E_TCMS_SUBORDINATE_OBJECT_NOT_FOUND = 'e-tcms-subordinate-object-not-found'
E_TCMS_FIND_OBJECT_FAILED = 'e-tcms-find-object-failed'
E_TCMS_UPDATE_OBJECT_FAILED = 'e-tcms-update-object-failed'
E_TCMS_UPLOAD_ATTACHMENT_FAILED = 'e-tcms-upload-attachment-failed'

E_INT_UNKNOWN_ENTITY_ATTR = 'e-int-unknown-entity-attr'
E_INT_UNKNOWN_ENTITY_PART = 'e-int-unknown-entity-part'

# OLD
E_READ_ATTACHMENT_FAILED = 'e-read-attachment-failed'
E_TCMS_NO_PRODUCTS = 'e-tcms-no-products'
E_TCMS_PLAN_UNKNOWN = 'e-tcms-plan-unknown'
E_TCMS_INIT_FAILED = 'e-tcms-init-failed'
E_TCMS_TEST_CASE_UNKNOWN = 'e-tcms-test-case-unknown'
E_TCMS_CREATE_OBJECT_FAILED = 'e-tcms-create-object-failed'
E_TCMS_INVALID_CLASS_ID = 'e-tcms-invalid-class-id'
E_TCMS_ATTACHMENTS_NOT_SUPPORTED = 'e-tcms-attachments-not-supported'

# import script related messages
I_IMP_EXECUTION_CREATED = 'i-imp-execution-created'
I_IMP_EXECUTION_SKIPPED = 'i-imp-execution-skipped'
I_IMP_EXECUTION_UPDATED = 'i-imp-execution-updated'
I_IMP_MD_REF_CHANGED = 'i-imp-md-ref-changed'
I_IMP_OBJECT_CREATED = 'i-imp-object-created'
I_IMP_OBJECT_SKIPPED = 'i-imp-object-skipped'
I_IMP_RUN_CREATED = 'i-imp-run-created'
I_IMP_RUN_SKIPPED = 'i-imp-run-skipped'
I_IMP_RUN_UPDATED = 'i-imp-run-updated'
I_IMP_USER_REPL_CURRENT = 'i-imp-user-repl-current'

# ===============================================================================================
# warning message IDs
# ===============================================================================================

# ===============================================================================================
# informational message IDs
# ===============================================================================================

# informational message IDs
I_CLEAR_EXPORT_ATTACHMENTS = 'i-clear-export-attachments'
I_CLEAR_EXPORT_FILE = 'i-clear-export-file'
I_CLEAR_EXPORT_OUTPUT = 'i-clear-export-output'

I_DRY_RUN_DOWNLOAD_ATTACHMENT = 'i-dry-run-download-attachment'
I_DRY_RUN_DOWNLOAD_ATTACHMENTS = 'i-dry-run-download-attachments'
I_DRY_RUN_UPLOAD_ATTACHMENT = 'i-dry-run-upload-attachment'
I_DRY_RUN_IMP_MD_EXACT_MATCH = 'i-dry-run-imp-md-exact-match'
I_DRY_RUN_IMP_MD_REF_CHANGED = 'i-dry-run-imp-md-ref-changed'
I_DRY_RUN_IMP_OBJECT_CREATED = 'i-dry-run-imp-object-created'
I_DRY_RUN_IMP_OBJECT_SKIPPED = 'i-dry-run-imp-object-skipped'
I_DRY_RUN_IMP_EXECUTION_CREATED = 'i-dry-run-imp-execution-created'
I_DRY_RUN_IMP_EXECUTION_SKIPPED = 'i-dry-run-imp-execution-skipped'
I_DRY_RUN_IMP_EXECUTION_UPDATED = 'i-dry-run-imp-execution-updated'
I_DRY_RUN_IMP_RUN_CREATED = 'i-dry-run-imp-run-created'
I_DRY_RUN_IMP_RUN_SKIPPED = 'i-dry-run-imp-run-skipped'
I_DRY_RUN_IMP_RUN_UPDATED = 'i-dry-run-imp-run-updated'
I_DRY_RUN_IMP_USER_EXACT_MATCH = 'i-dry-run-imp-user-exact-match'
I_DRY_RUN_IMP_USER_REPL_CURRENT = 'i-dry-run-imp-user-repl-current'

# GUI
L_ACTION = 'l-action'
L_ADD = 'l-add'
L_ATTRIBUTE = 'l-attribute'
L_AUTO_CREATE_MASTER_DATA = 'l-auto-create-master-data'
L_CANCEL = 'l-cancel'
L_CLEANUP = 'l-cleanup'
L_CLOSE = 'l-close'
L_CREATE = 'l-create'
L_DRY_RUN = 'l-dry-run'
L_FILE = 'l-file'
L_ENTITY = 'l-entity'
L_EXPORT_ENTITY = 'l-export-entity'
L_ID = 'l-id'
L_IMPORT = 'l-import'
L_IMPORT_USER_BEHAVIOUR = 'l-import-user-behaviour'
L_IMPORT_USER_USE_ALWAYS = 'l-import-user-use-always'
L_IMPORT_USER_USE_MISSING = 'l-import-user-use-missing'
L_IMPORT_USER_USE_NEVER = 'l-import-user-use-never'
L_INCLUDE_ATTACHMENTS = 'l-include-attachments'
L_INCLUDE_ENVIRONMENTS = 'l-include-environments'
L_INCLUDE_EXECUTIONS = 'l-include-executions'
L_INCLUDE_HISTORY = 'l-include-history'
L_INCLUDE_PLAN_TREE = 'l-include-plan-tree'
L_INCLUDE_RUNS = 'l-include-runs'
L_INIT = 'l-init'
L_NAME = 'l-name'
L_NO_ENVIRONMENT = 'l-no-environment'
L_OK = 'l-ok'
L_OPTIONS = 'l-options'
L_OUTPUT_PATH = 'l-output-path'
L_PRODUCT = 'l-product'
L_PRODUCT_NAME = 'l-product-name'
L_RECENT = 'l-recent'
L_REPOSITORY_PATH = 'l-repository-path'
L_RUN = 'l-run'
L_RUN_DESCENDANT_PLANS = 'l-run-descendant-plans'
L_RUN_ENTITY = 'l-run-entity'
L_SAVE = 'l-save'
L_SELECT = 'l-select'
L_SELECT_GROUP = 'l-select-group'
L_SELECT_PATH = 'l-select-path'
L_STORE_RESULT = 'l-store-result'
L_SUMMARY = 'l-summary'
L_TEST_CASE = 'l-test-case'
L_TEST_CASE_RESULT = 'l-test-case-result'
L_TEST_PLAN = 'l-test-plan'
L_TEST_PLAN_RESULT = 'l-test-plan-result'
L_TYPE = 'l-type'
L_VALUE = 'l-value'
L_COMBO_AVAILABLE_PRODUCTS = 'l-combo-available-products'
L_DLG_TITLE_ABOUT = 'l-dlg-title-about'
L_DLG_TITLE_EXPORT_PLAN = 'l-dlg-title-export-plan'
L_DLG_TITLE_EXPORT_PRODUCT = 'l-dlg-title-export-product'
L_DLG_TITLE_IMPORT_FILE = 'l-dlg-title-import-file'
L_DLG_TITLE_LRU_ENTITIES = 'l-dlg-title-lru-entities'
L_DLG_TITLE_MASTER_CONFIG_EDITOR = 'l-dlg-title-master-config-editor'
L_DLG_TITLE_FIRST_PRODUCT = 'l-dlg-title-first-product'
L_DLG_TITLE_PRODUCT_CONFIG_EDITOR = 'l-dlg-title-product-config-editor'
L_DLG_TITLE_PRODUCT_SELECTION = 'l-dlg-title-product-selection'
L_DLG_TITLE_RUN_PLAN = 'l-dlg-title-run-plan'
L_DLG_TITLE_SELECT_EXPORT_OUTPUT_PATH = 'l-dlg-title-select-export-output-path'
L_DLG_TITLE_SELECT_IMPORT_FILE = 'l-dlg-title-select-import-file'
L_DLG_TITLE_SELECT_PRODUCT_REPO_PATH = 'l-dlg-title-select-product-repo-path'
L_DLG_TITLE_XML_RPC_EDITOR = 'l-dlg-title-xml-rpc-editor'
L_ENV_COMBO = 'l-env-combo'
L_PRODUCT_COMBO = 'l-product-combo'
L_VERSION_COMBO = 'l-version-combo'
L_BUILD_COMBO = 'l-build-combo'
L_MAIN_WIN_DEFAULT_TITLE = 'l-main-win-default-title'
L_MBOX_INFO_DISCARD_CHANGES = 'l-mbox-info-discard-changes'
L_MBOX_INFO_REMOVE_GROUP = 'l-mbox-info-remove-group'
L_MBOX_INFO_RETRY = 'l-mbox-info-retry'
L_MBOX_INFO_USE_DEFAULT_CONFIG = 'l-mbox-info-use-default-config'
L_MBOX_TITLE_DATA_EDITED = 'l-mbox-title-data-edited'
L_MBOX_TITLE_ERROR = 'l-mbox-title-error'
L_MBOX_TITLE_INFO = 'l-mbox-title-info'
L_MBOX_TITLE_OUTPUT_EXISTS = 'l-mbox-title-output-exists'
L_MBOX_TITLE_WARNING = 'l-mbox-title-warning'
L_ACTION_ITEM_EXIT = 'l-action-item-exit'
L_ACTION_ITEM_EXPORT_CASE = 'l-action-item-export-case'
L_ACTION_ITEM_EXPORT_PLAN = 'l-action-item-export-plan'
L_ACTION_ITEM_EXPORT_PRODUCT = 'l-action-item-export-product'
L_ACTION_ITEM_HELP_ABOUT = 'l-action-item-help-about'
L_ACTION_ITEM_IMPORT = 'l-action-item-import'
L_ACTION_ITEM_RUN_FILE = 'l-action-item-run-file'
L_ACTION_ITEM_RUN_PLAN = 'l-action-item-run-plan'
L_ACTION_ITEM_CONFIG_MASTER = 'l-action-item-config-master'
L_ACTION_ITEM_CONFIG_PRODUCTS = 'l-action-item-config-products'
L_ACTION_ITEM_CONFIG_XML_RPC = 'l-action-item-config-xml-rpc'
L_MENU_ITEM_CONFIG = 'l-menu-item-config'
L_MENUBAR_ITEM_EXPORT = 'l-menubar-item-export'
L_MENUBAR_ITEM_FILE = 'l-menubar-item-file'
L_MENUBAR_ITEM_HELP = 'l-menubar-item-help'
L_MENUBAR_ITEM_RUN = 'l-menubar-item-run'
L_TYPE_LABEL_SCHEME_BUILD = 'l-type-label-scheme-build'
L_TYPE_LABEL_SCHEME_NONE = 'l-type-label-scheme-none'
L_TYPE_LABEL_SCHEME_VERSION = 'l-type-label-scheme-version'

# Configuration parameter comments
L_CFG_PAR_PRODUCT_NAME = 'l-cfg-par-product-name'
L_CFG_PAR_PRODUCT_REPOSITORY_PATH = 'l-cfg-par-product-repository-path'
L_CFG_PAR_PRODUCT_SOURCE_PATH = 'l-cfg-par-product-source-path'
L_CFG_PAR_PRODUCT_TEST_PATH = 'l-cfg-par-product-test-path'
L_CFG_PAR_PRODUCT_TEST_DATA_PATH = 'l-cfg-par-product-test-data-path'
L_CFG_PAR_RUNNER_CASE_ASSISTANT = 'l-cfg-par-runner-case-assistant'
L_CFG_PAR_RUNNER_CUSTOM_MODULE_PATH = 'l-cfg-par-runner-custom-module-path'
L_CFG_PAR_RUNNER_CUSTOM_SCRIPT_PATH = 'l-cfg-par-runner-custom-script-path'
L_CFG_PAR_RUNNER_ENTITY_ASSISTANT = 'l-cfg-par-runner-entity-assistant'
L_CFG_PAR_RUNNER_OUTPUT_LOG = 'l-cfg-par-runner-output-log'
L_CFG_PAR_RUNNER_PLAN_ASSISTANT = 'l-cfg-par-runner-plan-assistant'
L_CFG_PAR_RUNNER_PYTHON_VENV_PATH = 'l-cfg-par-runner-python-venv-path'
L_CFG_PAR_RUNNER_TEST_DRIVER_EXE = 'l-cfg-par-runner-test-driver-exe'
L_CFG_PAR_RUNNER_WORKING_PATH = 'l-cfg-par-runner-working-path'
L_CFG_PAR_TCMS_LABEL_SCHEME = 'l-cfg-par-tcms-label-scheme'
L_CFG_PAR_TCMS_EXECUTION_STATES = 'l-cfg-par-tcms-execution-states'
L_CFG_PAR_TCMS_RESULT_ATTACHMENTS = 'l-cfg-par-tcms-result-attachments'
L_CFG_PAR_TCMS_SPEC_ATTACHMENTS = 'l-cfg-par-tcms-spec-attachments'
L_CFG_PAR_TCMS_XML_RPC_URL = 'l-cfg-par-tcms-xml-rpc-url'
L_CFG_PAR_TCMS_XML_RPC_USERNAME = 'l-cfg-par-tcms-xml-rpc-username'
L_CFG_PAR_TCMS_XML_RPC_PASSWORD = 'l-cfg-par-tcms-xml-rpc-password'
L_CFG_PAR_TCMS_XML_RPC_USE_KERBEROS = 'l-cfg-par-tcms-xml-rpc-use-kerberos'
L_CFG_PAR_TESTING_ROOT_PATH = 'l-cfg-par-testing-root-path'

E_GUI_ID_NOT_NUMERIC = 'e-gui-id-not-numeric'
E_GUI_NEITHER_PRODUCT_NOR_VERSION_SELECTED = 'e-gui-neither-product-nor-version-selected'
E_GUI_NO_ID_SPECIFIED = 'e-gui-no-id-specified'
E_GUI_NO_ENTITY_SELECTED = 'e-gui-no-entity-selected'
E_GUI_NO_PRODUCT_SELECTED = 'e-gui-no-product-selected'
E_GUI_NO_VERSION_SELECTED = 'e-gui-no-version-selected'
E_GUI_WRITE_CONFIG_DATA_FAILED = 'e-gui-write-config-data-failed'
E_GUI_IMPORT_CASE_FAILED = 'e-gui-import-case-failed'
E_GUI_IMPORT_PLAN_FAILED = 'e-gui-import-plan-failed'
E_GUI_IMPORT_PLAN_RESULT_FAILED = 'e-gui-import-plan-result-failed'
E_GUI_IMPORT_PRODUCT_FAILED = 'e-gui-import-product-failed'
E_GUI_LRU_CASE_NO_LONGER_EXISTS = 'e-gui-lru-case-no-longer-exists'
E_GUI_LRU_PLAN_NO_LONGER_EXISTS = 'e-gui-lru-plan-no-longer-exists'
E_GUI_OUTPUT_PATH_INVALID = 'e-gui-output-path-invalid'
I_GUI_NO_LRU_ENTITIES = 'i-gui-no-lru-entities'
I_GUI_ABOUT_TEXT = 'i-gui-about-text'
I_GUI_ABOUT_INFO_TEXT = 'i-gui-about-info-text'
I_GUI_ABOUT_DETAIL_TEXT = 'i-gui-about-detail-text'
I_GUI_ATTRIBUTE_EXISTS = 'i-gui-attribute-exists'
I_GUI_CONFIG_PROBLEM = 'i-gui-config-problem'
I_GUI_CONFIG_WARNING = 'i-gui-config-warning'
I_GUI_CREATE_CONFIG_ROOT = 'i-gui-create-config-root'
I_GUI_CREATE_FIRST_PRODUCT = 'i-gui-create-first-product'
I_GUI_EXPORT_CASE_SUCCESSFUL = 'i-gui-export-case-successful'
I_GUI_EXPORT_PLAN_SUCCESSFUL = 'i-gui-export-plan-successful'
I_GUI_EXPORT_PRODUCT_SUCCESSFUL = 'i-gui-export-product-successful'
I_GUI_IMPORT_CASE_SUCCESSFUL = 'i-gui-import-case-successful'
I_GUI_IMPORT_PLAN_SUCCESSFUL = 'i-gui-import-plan-successful'
I_GUI_IMPORT_PLAN_RESULT_SUCCESSFUL = 'i-gui-import-plan-result-successful'
I_GUI_IMPORT_PRODUCT_SUCCESSFUL = 'i-gui-import-product-successful'
I_GUI_INVALID_ATTRIBUTE_NAME = 'i-gui-invalid-attribute-name'
I_GUI_NO_ATTRIBUTE_NAME = 'i-gui-no-attribute-name'
I_GUI_NO_BUILD_SELECTED = 'i-gui-no-build-selected'
I_GUI_NO_VERSION_SELECTED = 'i-gui-no-version-selected'
I_GUI_PROGRESS_CONTAINER_STATUS = 'i-gui-progress-container-status'
I_GUI_PROGRESS_TASK_FAILED = 'i-gui-progress-task-failed'
I_GUI_PROGRESS_TASK_FINISHED = 'i-gui-progress-task-finished'
I_GUI_PROGRESS_TASK_RUNNING = 'i-gui-progress-task-running'
I_GUI_PROGRESS_TASK_STARTED = 'i-gui-progress-task-started'
I_GUI_PROGRESS_UPLOAD_FILE = 'i-gui-progress-upload-file'
W_GUI_READ_CONFIG_DATA_FAILED = 'w-gui-read-config-data-failed'
W_GUI_WRITE_CONFIG_LOSES_COMMENTS = 'w-gui-write-config-loses-comments'
W_GUI_WRITE_GUI_CONFIGURATION_FAILED = 'w-gui-write-gui-configuration-failed'

# CLI
I_CLI_ISSAI_VERSION = 'i-cli-issai-version'
L_CLI_ARG_BUILD_HELP = 'l-cli-arg-build-help'
L_CLI_ARG_CREATE_MASTER_DATA_HELP = 'l-cli-arg-create-master-data-help'
L_CLI_ARG_DRY_RUN_HELP = 'l-cli-arg-dry-run-help'
L_CLI_ARG_ENTITY_REF_HELP = 'l-cli-arg-entity-ref-help'
L_CLI_ARG_ENVIRONMENT_HELP = 'l-cli-arg-environment-help'
L_CLI_ARG_EXPORT_ENTITY_SPEC_HELP = 'l-cli-arg-export-entity-spec-help'
L_CLI_ARG_INCLUDE_ATTACHMENTS_HELP = 'l-cli-arg-include-attachments-help'
L_CLI_ARG_INCLUDE_DESCENDANTS_HELP = 'l-cli-arg-include-descendants-help'
L_CLI_ARG_INCLUDE_ENVIRONMENTS_HELP = 'l-cli-arg-include-environments-help'
L_CLI_ARG_INCLUDE_EXECUTIONS_HELP = 'l-cli-arg-include-executions-help'
L_CLI_ARG_INCLUDE_HISTORY_HELP = 'l-cli-arg-include-history-help'
L_CLI_ARG_INCLUDE_RUNS_HELP = 'l-cli-arg-include-runs-help'
L_CLI_ARG_INPUT_FILE_HELP = 'l-cli-arg-input-file-help'
L_CLI_ARG_OUTPUT_PATH_HELP = 'l-cli-arg-output-path-help'
L_CLI_ARG_PRODUCT_HELP = 'l-cli-arg-product-help'
L_CLI_ARG_PRODUCT_VERSION_HELP = 'l-cli-arg-product-version-help'
L_CLI_ARG_RUN_ENTITY_SPEC_HELP = 'l-cli-arg-run-entity-spec-help'
L_CLI_ARG_STORE_RESULT_HELP = 'l-cli-arg-store-result-help'
L_CLI_EXPORT_DESCRIPTION = 'l-cli-export-description'
L_CLI_IMPORT_DESCRIPTION = 'l-cli-import-description'
L_CLI_RUN_DESCRIPTION = 'l-cli-run-description'

E_CLI_AMBIGUOUS_BUILD_IN_FILE = 'e-cli-ambiguous-build-in-file'
E_CLI_BUILD_REQUIRED = 'e-cli-build-required'
E_CLI_CASE_ID_REQUIRED = 'e-cli-case-id-required'
E_CLI_INVALID_FILE_ENTITY = 'e-cli-invalid-file-entity'
E_CLI_MISSING_ENV_IN_FILE = 'e-cli-missing-env-in-file'
E_CLI_NO_BUILDS_FOUND = 'e-cli-no-builds-found'
E_CLI_NO_BUILDS_IN_FILE = 'e-cli-no-builds-in-file'
E_CLI_NO_PRODUCTS_FOUND = 'e-cli-no-products-found'
E_CLI_NO_VERSIONS_FOUND = 'e-cli-no-versions-found'
E_CLI_PLAN_ID_REQUIRED = 'e-cli-plan-id-required'
E_CLI_PLAN_NOT_FOUND = 'e-cli-plan-not-found'
E_CLI_PRODUCT_CASE_NOT_FOUND = 'e-cli-product-case-not-found'
E_CLI_PRODUCT_PLAN_NOT_FOUND = 'e-cli-product-plan-not-found'
E_CLI_PRODUCT_REQUIRED = 'e-cli-product-required'
E_CLI_TCMS_OBJECT_NOT_FOUND = 'e-cli-tcms-object-not-found'
E_CLI_TCMS_OBJECT_ID_NOT_FOUND = 'e-cli-tcms-object-id-not-found'
E_CLI_VERSION_PLAN_NOT_FOUND = 'e-cli-version-plan-not-found'
E_CLI_VERSION_REQUIRED = 'e-cli-version-required'

# Tooltips
T_OPT_AUTO_CREATE_MASTER_DATA = 't-opt-auto-create-master-data'
T_OPT_DRY_RUN = 't-opt-dry-run'
T_OPT_EXP_ATTACHMENTS = 't-opt-exp-attachments'
T_OPT_EXP_EXECUTIONS = 't-opt-exp-executions'
T_OPT_EXP_PLAN_TREE = 't-opt-exp-plan-tree'
T_OPT_EXP_RUNS = 't-opt-exp-runs'
T_OPT_IMP_ATTACHMENTS = 't-opt-imp-attachments'
T_OPT_IMP_ENVIRONMENTS = 't-opt-imp-environments'
T_OPT_RUN_DESCENDANT_PLANS = 't-opt-run-descendant-plans'
T_OPT_STORE_RESULT = 't-opt-store-result'
T_OPT_USER_IMPORT = 't-opt-user-import'
T_SEARCH_CASE = 't-search-case'
T_SEARCH_PLAN = 't-search-plan'
T_SHOW_RECENT = 't-show-recent'

# internal
_MSG_FILE_NAME_FMT = 'messages_%s.txt'
_DEFAULT_LOCALE = 'en'
_EMSG_FW_CORRUPT = 'Framework installation is corrupt: %s.'
_EMSG_NO_MSG_FILE_FOUND = 'Could not find localized message definition files'
_EMSG_READ_MSG_FILE_FAILED = 'Could not read localized message definition file %s (%s)'


def message_id_exists(msg_id):
    """
    :param str msg_id: the message ID
    :returns: True, if specified message ID exists
    :rtype: bool
    """
    global _MESSAGE_TABLE
    return msg_id in _MESSAGE_TABLE


def localized_message(msg_id, *args):
    """
    Returns the localized message for given message ID and optional arguments.
    The number of optional arguments must match the number of placeholders used in the message's format string.
    Returns the message ID, if this table doesn't contain an appropriate message or there is a mismatch between
    optional arguments and format string.
    :param str msg_id: the message ID
    :param args: the optional additional arguments
    :returns: the localized message
    :rtype: str
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.message_for(msg_id, *args)


def localized_label(label_id):
    """
    Returns the localized text for given label ID.
    :param str label_id: the label ID
    :rtype: str
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.label_for(label_id)


def entity_type_name(entity_type):
    """
    :param int entity_type: the entity type ID
    :returns: localized lower case name of specified test entity
    :rtype: str
    """
    if entity_type == ENTITY_TYPE_PLAN:
        return localized_label(L_TEST_PLAN)
    elif entity_type == ENTITY_TYPE_CASE:
        return localized_label(L_TEST_CASE)
    elif entity_type == ENTITY_TYPE_PLAN_RESULT:
        return localized_label(L_TEST_PLAN_RESULT)
    elif entity_type == ENTITY_TYPE_CASE_RESULT:
        return localized_label(L_TEST_CASE_RESULT)
    else:
        return localized_label(L_PRODUCT)


def lower_case_entity_type_name(entity_type):
    """
    :param int entity_type: the entity type ID
    :returns: localized lower case name of specified test entity
    :rtype: str
    """
    return entity_type_name(entity_type).lower()


def assistant_action_name(action):
    """
    :param int action: the action ID
    :returns: localized action name
    :rtype: str
    """
    return localized_label(L_INIT) if action == ASSISTANT_ACTION_INIT else localized_label(L_CLEANUP)


class MessageTable(dict):
    def __init__(self, locale, messages):
        """
        Initializes the message table for the specified localized messages.
        Every message must be specified in a line starting with message ID followed by a space character and then
        the format string associated with the message ID. A backslash at the end of a line may be used as
        continuation. Lines starting with a hash mark or not complying with this format are ignored.
        :param str locale: the locale
        :param str messages: the localized messages
        """
        super().__init__()
        self.__locale = locale
        msg_id = None
        msg_text = ''
        msg_list = messages.split(os.linesep)
        for line in msg_list:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                if msg_id is not None:
                    self.update({msg_id: msg_text})
                    msg_id = None
                    msg_text = ''
                continue
            if line.endswith('\\'):
                if msg_id is not None:
                    msg_text = '%s%s' % (msg_text, line[:-1])
                else:
                    space_pos = line.index(' ')
                    msg_id = line[:space_pos]
                    msg_text = line[space_pos + 1:-1]
                continue
            if msg_id is not None:
                msg_text = '%s%s' % (msg_text, line)
            else:
                space_pos = line.index(' ')
                msg_id = line[:space_pos]
                msg_text = line[space_pos + 1:]
            self.update({msg_id: msg_text})
            msg_id = None
            msg_text = ''

    def message_for(self, msg_id, *args):
        """
        Returns the localized message for given message ID and optional arguments.
        The number of optional arguments must match the number of placeholders used in the message's format string.
        Returns the message ID, if this table doesn't contain an appropriate message or there is a mismatch between
        optional arguments and format string.
        :param str msg_id: the message ID
        :param args: the optional additional arguments
        :returns: the localized message
        :rtype: str
        """
        _fmt_str = self.get(msg_id)
        if _fmt_str is None:
            return msg_id
        _fmt_str = _fmt_str.replace(r'\n', os.linesep)
        # noinspection PyBroadException
        try:
            return _fmt_str.format(*args)
        except Exception:
            return msg_id

    def label_for(self, label_id):
        """
        Returns the localized label for given ID.
        :param str label_id: the label ID
        :rtype: str
        """
        _label = self.get(label_id)
        if _label is None:
            return label_id
        return _label

    def locale(self):
        """
        Returns the locale of this message table.
        Used for testing purposes.
        :returns: the locale
        :rtype: str
        """
        return self.__locale

    @staticmethod
    def for_locale(locale):
        """
        Creates a message table for the specified locale.
        Uses default locale, if locale is not supported.
        :param str locale: the locale
        :returns: message table for specified locale
        :rtype: MessageTable
        :raises RuntimeError: if no message definition files exist, i.e. framework has been corrupted
        """
        _locale = _DEFAULT_LOCALE if locale is None else locale
        _msgs_file_name = _MSG_FILE_NAME_FMT % _locale
        _current_dir = os.path.dirname(os.path.abspath(__file__))
        _msgs_file_path = os.path.join(_current_dir, _msgs_file_name)
        if not os.path.isfile(_msgs_file_path):
            _locale = _DEFAULT_LOCALE
            _msgs_file_path = os.path.join(_current_dir, _MSG_FILE_NAME_FMT % _locale)
        if not os.path.isfile(_msgs_file_path):
            raise RuntimeError(_EMSG_FW_CORRUPT % _EMSG_NO_MSG_FILE_FOUND)
        try:
            with open(_msgs_file_path, 'r') as f:
                _msgs = f.read()
            return MessageTable(_locale, _msgs)
        except Exception as e:
            _cause = _EMSG_READ_MSG_FILE_FAILED % (_msgs_file_path, str(e))
            raise RuntimeError(_EMSG_FW_CORRUPT % _cause)


# All localized messages, eventually containing placeholders
_MESSAGE_TABLE = MessageTable.for_locale(platform_locale())
