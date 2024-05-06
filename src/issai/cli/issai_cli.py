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
Issai command line interface.
"""
import os
import sys

from issai.core import *
from issai.cli.common import (CLI_ACTION_EXPORT, CLI_ACTION_IMPORT, CLI_ACTION_RUN, CLI_ENTITY_REF_KIND_FILE,
                              detail_action_for_export, detail_action_for_import, detail_action_for_run,
                              options_for, parse_arguments_for_action)
from issai.core.config import config_root_path, master_config, product_config
from issai.core.exporter import export_case, export_plan, export_product
from issai.core.importer import import_file
from issai.core.runner import run_offline_plan, run_tcms_plan
from issai.core.task import TaskMonitor


def export_main():
    """
    Export a test entity from TCMS to file.
    """
    try:
        _args = parse_arguments_for_action(sys.argv[1:], CLI_ACTION_EXPORT)
        _action = detail_action_for_export(_args)
        _options = options_for(_args, _action)
        _options[OPTION_VERSION] = _action.version()
        _options[OPTION_BUILD] = _action.build()
        _config_path = config_root_path()
        _master_cfg = master_config(_config_path)
        _task_monitor = TaskMonitor()
        _entity_type = _action.entity_type()
        _ref_kind = _action.entity_ref_kind()
        _output_path = os.path.abspath(_args.output_path)
        _local_config = product_config(_config_path, _action.product_name(), _master_cfg)
        if _entity_type == ENTITY_TYPE_PRODUCT:
            _result = export_product(_action.product_name(), _options, _output_path, _task_monitor)
        elif _entity_type == ENTITY_TYPE_PLAN:
            _result = export_plan(_action.entity(), _options, _output_path, _task_monitor)
        else:
            _result = export_case(_action.entity(), _options, _output_path, _task_monitor)
    except Exception as e:
        print()
        print(e)
        sys.exit(1)


def import_main():
    """
    Import a test entity from file to TCMS.
    """
    try:
        _args = parse_arguments_for_action(sys.argv[1:], CLI_ACTION_IMPORT)
        _action = detail_action_for_import(_args)
        _options = options_for(_args, _action)
        _options[OPTION_VERSION] = _action.version()
        _options[OPTION_BUILD] = _action.build()
        _config_path = config_root_path()
        _master_cfg = master_config(_config_path)
        _task_monitor = TaskMonitor()
        _entity_type = _action.entity_type()
        _ref_kind = _action.entity_ref_kind()
        _input_file_path = os.path.abspath(_args.input_file)
        _output_path = os.path.abspath(_args.output_path)
        _local_config = product_config(_config_path, _action.product_name(), _master_cfg)
        _result = import_file(_action.entity(), _options, _input_file_path, _task_monitor)
    except Exception as e:
        print()
        print(e)
        sys.exit(1)


def run_main():
    """
    Run a test plan.
    """
    try:
        _args = parse_arguments_for_action(sys.argv[1:], CLI_ACTION_RUN)
        _action = detail_action_for_run(_args)
        _options = options_for(_args, _action)
        _options[OPTION_VERSION] = _action.version()
        _options[OPTION_BUILD] = _action.build()
        _config_path = config_root_path()
        _master_cfg = master_config(_config_path)
        _task_monitor = TaskMonitor()
        _ref_kind = _action.entity_ref_kind()
        if _ref_kind == CLI_ENTITY_REF_KIND_FILE:
            # test plan specified by name of file containing exported data
            _attachment_path = os.path.join(os.path.dirname(_action.entity_ref()), ATTACHMENTS_ROOT_DIR)
            _local_config = product_config(_config_path, _action.product_name(), _master_cfg)
            _result = run_offline_plan(_action.entity(), _options, _local_config, _attachment_path, _task_monitor)
        else:
            # test plan specified by TCMS ID or name
            _local_config = product_config(_config_path, _action.product_name(), _master_cfg)
            _result = run_tcms_plan(_action.entity(), _options, _local_config, _task_monitor)
    except Exception as e:
        print()
        print(e)
        sys.exit(1)
