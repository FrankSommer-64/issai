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
Common functionality for Issai command line interface.
"""
import argparse

from issai.core import *
from issai.core.entities import Entity
from issai.core.messages import *
from issai.core.issai_exception import IssaiException
from issai.core.tcms import find_tcms_object, find_tcms_objects

CLI_ACTION_RUN = 1
CLI_ACTION_EXPORT = 2
CLI_ACTION_IMPORT = 3

CLI_ENTITY_TYPE_CASE = ENTITY_TYPE_CASE
CLI_ENTITY_TYPE_PLAN = ENTITY_TYPE_PLAN
CLI_ENTITY_TYPE_PRODUCT = ENTITY_TYPE_PRODUCT

CLI_ENTITY_REF_KIND_ID = 1
CLI_ENTITY_REF_KIND_NAME = 2
CLI_ENTITY_REF_KIND_FILE = 3

CLI_ARG_APPLY_CURRENT_USER = 'apply-current-user'
CLI_ARG_CREATE_MASTER_DATA = 'create-master-data'
CLI_ARG_DRY_RUN = 'dry-run'
CLI_ARG_ENTITY_REF = 'entity_ref'
CLI_ARG_ENVIRONMENT = 'environment'
CLI_ARG_EXPORT_ENTITY_SPEC = 'export_entity_spec'
CLI_ARG_INCLUDE_ATTACHMENTS = 'include-attachments'
CLI_ARG_INCLUDE_DESCENDANTS = 'include-descendants'
CLI_ARG_INCLUDE_ENVIRONMENTS = 'include-environments'
CLI_ARG_INCLUDE_EXECUTIONS = 'include-executions'
CLI_ARG_INCLUDE_HISTORY = 'include-history'
CLI_ARG_INCLUDE_RUNS = 'include-runs'
CLI_ARG_INPUT_FILE = 'input_file'
CLI_ARG_OUTPUT_PATH = 'output_path'
CLI_ARG_PRODUCT = 'product'
CLI_ARG_PRODUCT_BUILD = 'product-build'
CLI_ARG_PRODUCT_VERSION = 'product-version'
CLI_ARG_RUN_ENTITY_SPEC = 'run_entity_spec'
CLI_ARG_STORE_RESULT = 'store-result'
CLI_ARG_VERSION = 'version'

CLI_ARG_ACTION_STORE_TRUE = 'store_true'
CLI_ARG_VAL_APPLY_USER_ALWAYS = OPTION_VALUE_USER_REF_REPLACE_ALWAYS
CLI_ARG_VAL_APPLY_USER_MISSING = OPTION_VALUE_USER_REF_REPLACE_MISSING
CLI_ARG_VAL_APPLY_USER_NEVER = OPTION_VALUE_USER_REF_REPLACE_NEVER
CLI_ARG_VAL_CASE = 'case'
CLI_ARG_VAL_CASE_ID = 'case-id'
CLI_ARG_VAL_INPUT_FILE = 'input-file'
CLI_ARG_VAL_PLAN = 'plan'
CLI_ARG_VAL_PLAN_ID = 'plan-id'
CLI_ARG_VAL_PRODUCT = 'product'
CLI_ARG_VAL_PRODUCT_ID = 'product-id'
CLI_ARG_CHOICES_APPLY_USER = [CLI_ARG_VAL_APPLY_USER_ALWAYS, CLI_ARG_VAL_APPLY_USER_NEVER,
                              CLI_ARG_VAL_APPLY_USER_MISSING]
CLI_ARG_CHOICES_EXPORT_ENTITY_SPEC = [CLI_ARG_VAL_CASE, CLI_ARG_VAL_CASE_ID, CLI_ARG_VAL_PLAN, CLI_ARG_VAL_PLAN_ID,
                                      CLI_ARG_VAL_PRODUCT, CLI_ARG_VAL_PRODUCT_ID]
CLI_ARG_CHOICES_RUN_ENTITY_SPEC = [CLI_ARG_VAL_PLAN, CLI_ARG_VAL_PLAN_ID, CLI_ARG_VAL_INPUT_FILE]


class DetailAction:
    """
    Represents the detail action to execute by command line interface.
    """
    def __init__(self, base_action, entity_type, entity_ref_kind, entity_ref):
        """
        Constructor.
        :param int base_action: the basic action (run, export, import)
        :param int entity_type: the entity type (product, test plan, test case)
        :param int entity_ref_kind: the way how the entity is specified (by TCMS ID, by TCMS name, by file name)
        :param int|str entity_ref: the entity specifier (TCMS ID, TCMS name, file name)
        """
        self.__base_action = base_action
        self.__entity_type = entity_type
        self.__entity_ref_kind = entity_ref_kind
        self.__entity_ref = entity_ref
        self.__entity = None
        self.__product_name = None
        self.__version = None
        self.__build = None
        self.__environment = None

    def base_action(self):
        """
        :returns: basic action (run, export, import)
        :rtype: int
        """
        return self.__base_action

    def entity_type(self):
        """
        :returns: entity type (product, test plan, test case)
        :rtype: int
        """
        return self.__entity_type

    def entity_ref_kind(self):
        """
        :returns: way how the entity is specified (by TCMS ID, by TCMS name, by file name)
        :rtype: int
        """
        return self.__entity_ref_kind

    def entity_ref(self):
        """
        :returns: entity specifier (TCMS ID, TCMS name, file name)
        :rtype: int|str
        """
        return self.__entity_ref

    def entity(self):
        """
        :returns: entity data
        :rtype: str | Entity
        """
        return self.__entity

    def product_name(self):
        """
        :returns: product name
        :rtype: str
        """
        return self.__product_name

    def version(self):
        """
        :returns: product version data, may be None
        :rtype: str | dict
        """
        return self.__version

    def build(self):
        """
        :returns: build data, may be None
        :rtype: str | dict
        """
        return self.__build

    def environment(self):
        """
        :returns: environment data
        :rtype: str | Entity
        """
        return self.__environment

    def set_entity(self, entity):
        """
        :param Entity entity: the entity data
        """
        self.__entity = entity

    def set_product_name(self, product_name):
        """
        :param str product_name: the product name
        """
        self.__product_name = product_name

    def set_version(self, version):
        """
        :param dict version: the version data
        """
        self.__version = version

    def set_build(self, build):
        """
        :param dict build: the build data
        """
        self.__build = build

    def set_environment(self, env):
        """
        :param dict env: the environment data
        """
        self.__environment = env

    def __str__(self):
        """
        :returns: string representation of object
        :rtype: str
        """
        return str(vars(self))


def parse_arguments_for_action(cmdline_args, base_action):
    """
    Parses and checks command line arguments for specified base action.
    :param int base_action: the basic action (run, export, import)
    :param list[str] cmdline_args: the command line arguments
    :returns: parsed arguments
    :rtype: argparse.Namespace
    """
    _arg_parser = argparse.ArgumentParser(description=localized_label(_ARG_DESCRIPTION[base_action]))
    _issai_version = localized_message(I_CLI_ISSAI_VERSION, VERSION)
    _arg_parser.add_argument(f'--{CLI_ARG_VERSION}', action=CLI_ARG_VERSION, version=_issai_version)
    for _arg_name in _POS_ARGS[base_action]:
        _arg_help, _, _arg_choices, _ = _ARG_DESCRIPTOR[_arg_name]
        if _arg_choices is not None:
            _arg_parser.add_argument(_arg_name, help=localized_label(_arg_help), choices=_arg_choices)
        else:
            _arg_parser.add_argument(_arg_name, help=localized_label(_arg_help))
    for _arg_name in _OPTION_ARGS[base_action]:
        _arg_help, _arg_action, _arg_choices, _arg_default = _ARG_DESCRIPTOR[_arg_name]
        if _arg_action is not None:
            _arg_parser.add_argument(f'--{_arg_name}', help=localized_label(_arg_help),
                                     action=_arg_action, default=_arg_default)
        elif _arg_choices is not None:
            _arg_parser.add_argument(f'--{_arg_name}', help=localized_label(_arg_help),
                                     choices=_arg_choices, default=_arg_default)
        else:
            _arg_parser.add_argument(f'--{_arg_name}', help=localized_label(_arg_help), default=_arg_default)
    return _arg_parser.parse_args(cmdline_args)


def detail_action_for_export(parsed_args):
    """
    Processes parsed command line arguments for base action 'export'.
    :param argparse.Namespace parsed_args: the parsed command line arguments
    :returns: detailed action
    :rtype: DetailAction
    """
    if parsed_args.export_entity_spec == CLI_ARG_VAL_CASE:
        # export test case specified by name (= summary)
        _ref_kind = CLI_ENTITY_REF_KIND_NAME
        _ref = parsed_args.entity_ref
        _entity_type = CLI_ENTITY_TYPE_CASE
        _entity, _product = load_tcms_case(_ref, parsed_args.product)
    elif parsed_args.export_entity_spec == CLI_ARG_VAL_CASE_ID:
        # export test case specified by TCMS ID
        _ref_kind = CLI_ENTITY_REF_KIND_ID
        _ref = int(parsed_args.entity_ref)
        _entity_type = CLI_ENTITY_TYPE_CASE
        _entity = find_tcms_object(TCMS_CLASS_ID_TEST_CASE, {ATTR_ID: _ref})
        if _entity is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_ID_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_CASE), _ref)
        _category = find_tcms_object(TCMS_CLASS_ID_CATEGORY, {ATTR_ID: _entity[ATTR_CATEGORY]})
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _category[ATTR_PRODUCT]})
    elif parsed_args.export_entity_spec == CLI_ARG_VAL_PLAN:
        # export test plan specified by name
        _ref_kind = CLI_ENTITY_REF_KIND_NAME
        _ref = parsed_args.entity_ref
        _entity_type = CLI_ENTITY_TYPE_PLAN
        _entity, _product = load_tcms_plan(_ref, parsed_args.product, parsed_args.product_version)
    elif parsed_args.export_entity_spec == CLI_ARG_VAL_PLAN_ID:
        # export test plan specified by TCMS ID
        _ref_kind = CLI_ENTITY_REF_KIND_ID
        _ref = int(parsed_args.entity_ref)
        _entity_type = CLI_ENTITY_TYPE_PLAN
        _entity = find_tcms_object(TCMS_CLASS_ID_TEST_PLAN, {ATTR_ID: _ref})
        if _entity is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_ID_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_PLAN), _ref)
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _entity[ATTR_PRODUCT]})
    elif parsed_args.export_entity_spec == CLI_ARG_VAL_PRODUCT:
        # export product specified by name
        _ref_kind = CLI_ENTITY_REF_KIND_NAME
        _ref = parsed_args.entity_ref
        _entity_type = CLI_ENTITY_TYPE_PRODUCT
        _entity = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_NAME: _ref})
        if _entity is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT), _ref)
        _product = _entity
    else:
        # export product specified by TCMS ID
        _ref_kind = CLI_ENTITY_REF_KIND_ID
        _ref = int(parsed_args.entity_ref)
        _entity_type = CLI_ENTITY_TYPE_PRODUCT
        _entity = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _ref})
        if _entity is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_ID_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT), _ref)
        _product = _entity
    _detail_action = DetailAction(CLI_ACTION_EXPORT, _entity_type, _ref_kind, _ref)
    _detail_action.set_entity(_entity)
    _detail_action.set_product_name(_product[ATTR_NAME])
    if parsed_args.product_version is not None:
        _version = load_tcms_version(parsed_args.product_version, _product)
        _detail_action.set_version(_version)
        if parsed_args.product_build is not None:
            _detail_action.set_build(load_tcms_build(parsed_args.product_build, _product[ATTR_NAME], _version))
    return _detail_action


def detail_action_for_import(parsed_args):
    """
    Processes parsed command line arguments for base action 'import'.
    :param argparse.Namespace parsed_args: the parsed command line arguments
    :returns: detailed action
    :rtype: DetailAction
    """
    _entity = Entity.from_file(parsed_args.input_file)
    _detail_action = DetailAction(CLI_ACTION_IMPORT, _entity.entity_type_id(), CLI_ENTITY_REF_KIND_FILE,
                                  parsed_args.input_file)
    _detail_action.set_entity(_entity)
    return _detail_action


def detail_action_for_run(parsed_args):
    """
    Processes parsed command line arguments for base action 'run'.
    :param argparse.Namespace parsed_args: the parsed command line arguments
    :returns: detailed action
    :rtype: DetailAction
    """
    if parsed_args.run_entity_spec == CLI_ARG_VAL_PLAN_ID:
        # make sure arguments refer to a specific build
        _ref_kind = CLI_ENTITY_REF_KIND_ID
        _ref = int(parsed_args.entity_ref)
        _plan = find_tcms_object(TCMS_CLASS_ID_TEST_PLAN, {ATTR_ID: _ref})
        if _plan is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_PLAN),
                                 _ref)
        _product = load_tcms_product(parsed_args.product, _plan[ATTR_PRODUCT])
        _version = find_tcms_object(TCMS_CLASS_ID_VERSION, {ATTR_ID: _plan[ATTR_PRODUCT_VERSION]})
        _build = load_tcms_build(parsed_args.product_build, _product[ATTR_NAME], _version, True)
        _env = load_tcms_environment(parsed_args.environment)
    elif parsed_args.run_entity_spec == CLI_ARG_VAL_PLAN:
        _ref_kind = CLI_ENTITY_REF_KIND_NAME
        _ref = parsed_args.entity_ref
        _plans = find_tcms_objects(TCMS_CLASS_ID_TEST_PLAN, {ATTR_NAME: _ref})
        if len(_plans) == 0:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_PLAN), _ref)
        _product_ids = set()
        for _p in _plans:
            _product_ids.add(_p[ATTR_PRODUCT])
        if parsed_args.product is None:
            if len(_product_ids) > 1:
                raise IssaiException(E_CLI_PRODUCT_REQUIRED)
            _product_id = _product_ids.pop()
            _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _product_id})
        else:
            _product = load_tcms_product(parsed_args.product)
            _product_id = _product[ATTR_ID]
        _product_plans = [_p for _p in _plans if _p[ATTR_PRODUCT] == _product_id]
        _version_ids = set()
        for _p in _product_plans:
            _version_ids.add(_p[ATTR_PRODUCT_VERSION])
        if parsed_args.product_version is None:
            if len(_version_ids) > 1:
                raise IssaiException(E_CLI_VERSION_REQUIRED, _product[ATTR_NAME])
            _version_id = _version_ids.pop()
            _version = find_tcms_object(TCMS_CLASS_ID_VERSION, {ATTR_ID: _version_id})
        else:
            _version = load_tcms_version(parsed_args.product_version, _product)
            _version_id = _version[ATTR_ID]
        _plans = [_p for _p in _plans if _p[ATTR_PRODUCT_VERSION] == _version_id]
        if len(_plans) == 0:
            raise IssaiException(E_CLI_PLAN_NOT_FOUND, _ref, _product[ATTR_NAME], _version[ATTR_VALUE])
        _plan = _plans[0]
        _build = load_tcms_build(parsed_args.product_build, _product[ATTR_NAME], _version, True)
        _env = load_tcms_environment(parsed_args.environment)
    else:
        _plan = Entity.from_file(parsed_args.entity_ref)
        if ENTITY_TYPE_PLAN != _plan.entity_type_id():
            raise IssaiException(E_CLI_INVALID_FILE_ENTITY, parsed_args.entity_ref,
                                 entity_type_name(_plan.entity_type_id()))
        _ref_kind = CLI_ENTITY_REF_KIND_FILE
        _ref = parsed_args.entity_ref
        _plan_data = _plan.get_part(ATTR_TEST_PLANS, -1)
        _product_attr = _plan.get(ATTR_PRODUCT)
        _product = _plan.get(ATTR_PRODUCT)
        _version = _plan.master_data_object(ATTR_PRODUCT_VERSIONS, _plan_data[ATTR_PRODUCT_VERSION])
        _build = load_entity_build(_plan, parsed_args.product_build, _version, parsed_args.entity_ref)
        _env = load_entity_environment(_plan, parsed_args.environment, parsed_args.entity_ref)
    _detail_action = DetailAction(CLI_ACTION_RUN, CLI_ENTITY_TYPE_PLAN, _ref_kind, _ref)
    _detail_action.set_entity(_plan)
    _detail_action.set_product_name(_product[ATTR_NAME])
    _detail_action.set_version(_version)
    _detail_action.set_build(_build)
    _detail_action.set_environment(_env)
    return _detail_action


def options_for(args, detail_action):
    """
    Extracts options from command line arguments.
    :param argparse.Namespace args: the parsed command line arguments
    :param DetailAction detail_action: the detailed action to perform
    :returns: the extracted options
    :rtype: dict
    :raises IssaiException: if the command line argument specification is invalid or an error during TCMS communication
                            occurs
    """
    if detail_action.base_action() == CLI_ACTION_RUN:
        return {OPTION_BUILD: detail_action.build(),
                OPTION_DRY_RUN: args.dry_run,
                OPTION_ENVIRONMENT: detail_action.environment(),
                OPTION_PLAN_TREE: args.include_descendants,
                OPTION_STORE_RESULT: args.store_result,
                OPTION_VERSION: detail_action.version()
                }
    if detail_action.base_action() == CLI_ACTION_IMPORT:
        _user_refs = OPTION_VALUE_USER_REF_REPLACE_NEVER if args.apply_current_user is None else args.apply_current_user
        return {OPTION_USER_REFERENCES: _user_refs,
                OPTION_AUTO_CREATE: args.create_master_data,
                OPTION_DRY_RUN: args.dry_run,
                OPTION_INCLUDE_ATTACHMENTS: args.include_attachments,
                OPTION_INCLUDE_ENVIRONMENTS: args.include_environments
                }
    # EXPORT
    _opts = {OPTION_BUILD: detail_action.build(),
             OPTION_INCLUDE_ATTACHMENTS: args.include_attachments,
             OPTION_INCLUDE_ENVIRONMENTS: args.include_environments,
             OPTION_INCLUDE_HISTORY: args.include_history,
             OPTION_INCLUDE_RUNS: args.include_runs or args.include_executions,
             OPTION_VERSION: detail_action.version()
             }
    if detail_action.entity_type() == CLI_ENTITY_TYPE_PLAN:
        _opts[OPTION_PLAN_TREE] = args.include_descendants
    return _opts


def load_tcms_case(case_summary, product_name):
    """
    Reads test case and associated product from TCMS.
    :param str case_summary: the test case summary to search for
    :param str product_name: the desired product name, may be None
    :returns: selected test case and associated product
    :rtype: tuple[dict,dict]
    :raises IssaiException: if specified product doesn't exist or unique test case can't be determined
    """
    _cases = find_tcms_objects(TCMS_CLASS_ID_TEST_CASE, {ATTR_SUMMARY: case_summary})
    if len(_cases) == 0:
        raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_CASE), case_summary)
    if len(_cases) == 1:
        _case = _cases[0]
        _category = find_tcms_object(TCMS_CLASS_ID_CATEGORY, {ATTR_ID: _case[ATTR_CATEGORY]})
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _category[ATTR_PRODUCT]})
        return _case, _product
    # more than one test case with specified summary exists
    _category_ids = set()
    for _c in _cases:
        _category_ids.add(_c[ATTR_CATEGORY])
    if product_name is None:
        if len(_category_ids) > 1:
            # test case with same summary exists in multiple projects
            raise IssaiException(E_CLI_PRODUCT_REQUIRED)
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_CATEGORY: _category_ids.pop()})
        # no need to check for missing product, it must exist due to database constraints
    else:
        _product = load_tcms_product(product_name)
        if _product is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT),
                                 product_name)
    _category_id = _product[ATTR_CATEGORY]
    _product_name = _product[ATTR_NAME]
    _product_cases = [_c for _c in _cases if _c[ATTR_CATEGORY] == _category_id]
    if len(_product_cases) == 0:
        # no test cases with specified summary in product
        raise IssaiException(E_CLI_PRODUCT_CASE_NOT_FOUND, case_summary, _product_name)
    if len(_product_cases) > 1:
        # multiple test cases with specified summary in product
        raise IssaiException(E_CLI_CASE_ID_REQUIRED, case_summary, _product_name)
    return _product_cases[0], _product


def load_tcms_plan(plan_name, product_name, version_value):
    """
    Reads test plan and associated product from TCMS.
    :param str plan_name: the test plan name to search for
    :param str product_name: the desired product name, may be None
    :param str version_value: the desired product version value, may be None
    :returns: selected test plan and associated product
    :rtype: tuple[dict,dict]
    :raises IssaiException: if specified product or version doesn't exist or unique test plan can't be determined
    """
    _plans = find_tcms_objects(TCMS_CLASS_ID_TEST_PLAN, {ATTR_NAME: plan_name})
    if len(_plans) == 0:
        raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_TEST_PLAN), plan_name)
    if len(_plans) == 1:
        _plan = _plans[0]
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _plan[ATTR_PRODUCT]})
        return _plan, _product
    # more than one test plan with specified name exists
    _product_ids = set()
    for _p in _plans:
        _product_ids.add(_p[ATTR_PRODUCT])
    if product_name is None:
        if len(_product_ids) > 1:
            # test plan with same name exists in multiple projects
            raise IssaiException(E_CLI_PRODUCT_REQUIRED)
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: _product_ids.pop()})
        # no need to check for missing product, it must exist due to database constraints
    else:
        _product = load_tcms_product(product_name)
        if _product is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT),
                                 product_name)
    _product_id = _product[ATTR_ID]
    _product_name = _product[ATTR_NAME]
    _product_plans = [_p for _p in _plans if _p[ATTR_PRODUCT] == _product_id]
    if len(_product_plans) == 0:
        # no test plans with specified name in product
        raise IssaiException(E_CLI_PRODUCT_PLAN_NOT_FOUND, plan_name, _product_name)
    if len(_product_plans) == 1:
        return _product_plans[0], _product
    # multiple test plans with specified name in product
    if version_value is None:
        raise IssaiException(E_CLI_VERSION_REQUIRED, _product_name)
    _version = find_tcms_object(TCMS_CLASS_ID_VERSION, {ATTR_PRODUCT: _product_id, ATTR_VALUE: version_value})
    if _version is None:
        raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_VERSION),
                             version_value)
    _version_id = _version[ATTR_ID]
    _version_plans = [_p for _p in _product_plans if _p[ATTR_PRODUCT_VERSION] == _version_id]
    if len(_version_plans) == 0:
        # no test plans with specified version
        raise IssaiException(E_CLI_VERSION_PLAN_NOT_FOUND, plan_name, _product_name, version_value)
    if len(_version_plans) == 1:
        return _version_plans[0], _product
    # multiple test plans with specified name, product and version exist
    raise IssaiException(E_CLI_PLAN_ID_REQUIRED, plan_name, version_value, _product_name)


def load_tcms_product(product_arg, product_id=None):
    """
    Reads product from TCMS.
    :param str product_arg: the product name, as specified on command line; may be None
    :param int product_id: the optional TCMS product ID; may be None
    :returns: product data found
    :rtype: dict
    :raises IssaiException: if unique product cannot be determined
    """
    if product_id is not None:
        _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_ID: product_id})
        if _product is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT),
                                 product_id)
        return _product
    if product_arg is None:
        _products = find_tcms_objects(TCMS_CLASS_ID_PRODUCT, {})
        if len(_products) == 0:
            raise IssaiException(E_CLI_NO_PRODUCTS_FOUND)
        elif len(_products) > 1:
            raise IssaiException(E_CLI_PRODUCT_REQUIRED)
        return _products[0]
    _product = find_tcms_object(TCMS_CLASS_ID_PRODUCT, {ATTR_NAME: product_arg})
    if _product is None:
        raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_PRODUCT),
                             product_arg)
    return _product


def load_tcms_version(version_arg, product):
    """
    Reads product version from TCMS.
    :param str version_arg: the version value, as specified on command line; may be None
    :param dict product: the TCMS product data
    :returns: version data found
    :rtype: dict
    :raises IssaiException: if unique version cannot be determined
    """
    if version_arg is None:
        _versions = find_tcms_objects(TCMS_CLASS_ID_VERSION, {ATTR_PRODUCT: product[ATTR_ID]})
        if len(_versions) == 0:
            raise IssaiException(E_CLI_NO_VERSIONS_FOUND, product[ATTR_NAME])
        elif len(_versions) > 1:
            raise IssaiException(E_CLI_VERSION_REQUIRED, product[ATTR_NAME])
        _version = _versions[0]
    else:
        _filter = {ATTR_VALUE: version_arg, ATTR_PRODUCT: product[ATTR_ID]}
        _version = find_tcms_object(TCMS_CLASS_ID_VERSION, _filter)
        if _version is None:
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_VERSION),
                                 version_arg)
    return _version


def load_tcms_build(build_arg, product_name, version, accept_missing=False):
    """
    Reads build from TCMS.
    :param str build_arg: the build value, as specified on command line; may be None
    :param str product_name: the product name
    :param dict version: the TCMS version data
    :param bool accept_missing: indicates whether to accept non-existing build name
    :returns: build data found or build name
    :rtype: dict|str
    :raises IssaiException: if unique build cannot be determined
    """
    if build_arg is None:
        _builds = find_tcms_objects(TCMS_CLASS_ID_BUILD, {ATTR_VERSION: version[ATTR_ID]})
        if len(_builds) == 0:
            raise IssaiException(E_CLI_NO_BUILDS_FOUND, product_name, version[ATTR_VALUE])
        elif len(_builds) > 1:
            raise IssaiException(E_CLI_BUILD_REQUIRED, product_name, version[ATTR_VALUE])
        _build = _builds[0]
    else:
        _filter = {ATTR_NAME: build_arg, ATTR_VERSION: version[ATTR_ID]}
        _build = find_tcms_object(TCMS_CLASS_ID_BUILD, _filter)
        if _build is None:
            if accept_missing:
                return build_arg
            raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_BUILD),
                                 build_arg)
    return _build


def load_tcms_environment(env_arg):
    """
    Reads environment from TCMS.
    :param str env_arg: the environment name, as specified on command line; may be None
    :returns: environment data found
    :rtype: dict
    :raises IssaiException: if environment doesn't exist
    """
    if env_arg is None:
        return None
    _env = find_tcms_object(TCMS_CLASS_ID_ENVIRONMENT, {ATTR_NAME: env_arg})
    if _env is None:
        raise IssaiException(E_CLI_TCMS_OBJECT_NOT_FOUND, tcms_class_name_for_id(TCMS_CLASS_ID_ENVIRONMENT),
                             env_arg)
    return _env


def load_entity_build(entity, build_arg, version, file_path):
    """
    Reads build from exported file.
    Function called for action run only, where a non-existing build is accepted in CLI.
    :param str build_arg: the build value, as specified on command line; may be None
    :param Entity entity: the entity data
    :param dict version: the version data
    :param str file_path: the file name including full path
    :returns: build data found or passed build name
    :rtype: dict|str
    :raises IssaiException: if unique build cannot be determined
    """
    _builds = entity.master_data_of_type(ATTR_PRODUCT_BUILDS)
    if len(_builds) == 0:
        if build_arg is None:
            raise IssaiException(E_CLI_NO_BUILDS_IN_FILE, file_path)
        return build_arg
    _version_builds = [_b for _b in _builds if _b[ATTR_VERSION] == version[ATTR_ID]]
    if build_arg is None:
        if len(_version_builds) == 1:
            return _version_builds[0]
        raise IssaiException(E_CLI_AMBIGUOUS_BUILD_IN_FILE, file_path, version[ATTR_VALUE])
    for _build in _version_builds:
        if _build[ATTR_NAME] == build_arg:
            return _build
    return build_arg


def load_entity_environment(entity, env_arg, file_path):
    """
    Reads environment from exported file.
    :param SpecificationEntity entity: the entity data
    :param str env_arg: the environment name, as specified on command line; may be None
    :param str file_path: the file name including full path
    :returns: environment data found
    :rtype: dict
    :raises IssaiException: if environment doesn't exist
    """
    if env_arg is None:
        return None
    for _env in entity.environments():
        if _env[ATTR_NAME] == env_arg:
            return _env
    raise IssaiException(E_CLI_MISSING_ENV_IN_FILE, env_arg, file_path)


_ARG_DESCRIPTION = {CLI_ACTION_EXPORT: L_CLI_EXPORT_DESCRIPTION, CLI_ACTION_IMPORT: L_CLI_IMPORT_DESCRIPTION,
                    CLI_ACTION_RUN: L_CLI_RUN_DESCRIPTION}

# positional arguments
_POS_ARGS = {CLI_ACTION_EXPORT: [CLI_ARG_EXPORT_ENTITY_SPEC, CLI_ARG_ENTITY_REF, CLI_ARG_OUTPUT_PATH],
             CLI_ACTION_IMPORT: [CLI_ARG_INPUT_FILE],
             CLI_ACTION_RUN: [CLI_ARG_RUN_ENTITY_SPEC, CLI_ARG_ENTITY_REF]
             }

# option arguments
_OPTION_ARGS = {CLI_ACTION_EXPORT: (CLI_ARG_INCLUDE_ATTACHMENTS, CLI_ARG_INCLUDE_DESCENDANTS, CLI_ARG_PRODUCT_BUILD,
                                    CLI_ARG_INCLUDE_ENVIRONMENTS, CLI_ARG_INCLUDE_EXECUTIONS, CLI_ARG_INCLUDE_HISTORY,
                                    CLI_ARG_INCLUDE_RUNS, CLI_ARG_PRODUCT, CLI_ARG_PRODUCT_VERSION),
                CLI_ACTION_IMPORT: (CLI_ARG_APPLY_CURRENT_USER, CLI_ARG_CREATE_MASTER_DATA, CLI_ARG_DRY_RUN,
                                    CLI_ARG_INCLUDE_ATTACHMENTS, CLI_ARG_INCLUDE_ENVIRONMENTS),
                CLI_ACTION_RUN: (CLI_ARG_PRODUCT, CLI_ARG_PRODUCT_VERSION, CLI_ARG_PRODUCT_BUILD, CLI_ARG_ENVIRONMENT,
                                 CLI_ARG_STORE_RESULT, CLI_ARG_INCLUDE_DESCENDANTS, CLI_ARG_DRY_RUN)
                }

# argument descriptors (help text, action, choices, default value)
_ARG_DESCRIPTOR = {CLI_ARG_APPLY_CURRENT_USER: (L_CLI_ARG_DRY_RUN_HELP, None,
                                                CLI_ARG_CHOICES_APPLY_USER, CLI_ARG_VAL_APPLY_USER_NEVER),
                   CLI_ARG_PRODUCT_BUILD: (L_CLI_ARG_BUILD_HELP, None, None, None),
                   CLI_ARG_CREATE_MASTER_DATA: (L_CLI_ARG_CREATE_MASTER_DATA_HELP, CLI_ARG_ACTION_STORE_TRUE,
                                                None, False),
                   CLI_ARG_DRY_RUN: (L_CLI_ARG_DRY_RUN_HELP, CLI_ARG_ACTION_STORE_TRUE, None, False),
                   CLI_ARG_ENVIRONMENT: (L_CLI_ARG_ENVIRONMENT_HELP, None, None, None),
                   CLI_ARG_ENTITY_REF: (L_CLI_ARG_ENTITY_REF_HELP, None, None, None),
                   CLI_ARG_EXPORT_ENTITY_SPEC: (L_CLI_ARG_EXPORT_ENTITY_SPEC_HELP, None,
                                                CLI_ARG_CHOICES_EXPORT_ENTITY_SPEC, None),
                   CLI_ARG_INCLUDE_ATTACHMENTS: (L_CLI_ARG_INCLUDE_ATTACHMENTS_HELP, CLI_ARG_ACTION_STORE_TRUE,
                                                 None, False),
                   CLI_ARG_INCLUDE_DESCENDANTS: (L_CLI_ARG_INCLUDE_DESCENDANTS_HELP, CLI_ARG_ACTION_STORE_TRUE,
                                                 None, False),
                   CLI_ARG_INCLUDE_ENVIRONMENTS: (L_CLI_ARG_INCLUDE_ENVIRONMENTS_HELP, CLI_ARG_ACTION_STORE_TRUE,
                                                  None, False),
                   CLI_ARG_INCLUDE_EXECUTIONS: (L_CLI_ARG_INCLUDE_EXECUTIONS_HELP, CLI_ARG_ACTION_STORE_TRUE,
                                                None, False),
                   CLI_ARG_INCLUDE_HISTORY: (L_CLI_ARG_INCLUDE_HISTORY_HELP, CLI_ARG_ACTION_STORE_TRUE, None, False),
                   CLI_ARG_INCLUDE_RUNS: (L_CLI_ARG_INCLUDE_RUNS_HELP, CLI_ARG_ACTION_STORE_TRUE, None, False),
                   CLI_ARG_INPUT_FILE: (L_CLI_ARG_INPUT_FILE_HELP, None, None, None),
                   CLI_ARG_OUTPUT_PATH: (L_CLI_ARG_OUTPUT_PATH_HELP, None, None, None),
                   CLI_ARG_PRODUCT: (L_CLI_ARG_PRODUCT_HELP, None, None, None),
                   CLI_ARG_PRODUCT_VERSION: (L_CLI_ARG_PRODUCT_VERSION_HELP, None, None, None),
                   CLI_ARG_RUN_ENTITY_SPEC: (L_CLI_ARG_RUN_ENTITY_SPEC_HELP, None,
                                             CLI_ARG_CHOICES_RUN_ENTITY_SPEC, None),
                   CLI_ARG_STORE_RESULT: (L_CLI_ARG_STORE_RESULT_HELP, CLI_ARG_ACTION_STORE_TRUE, None, False)
                   }
