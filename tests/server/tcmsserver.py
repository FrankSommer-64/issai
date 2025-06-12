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
XML-RPC Server mocking a TCMS instance.
"""

from argparse import ArgumentParser
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
import re
import sys
import time
from issai.core import *
from dataset import DataSet


KIWI_TCMS_VERSION = '12.7'


class XmlRpcHandler:
    def __init__(self):
        super().__init__()
        self.__objects = {}

    def dispatch(self, method_name, args):
        _method = getattr(self, method_name)
        if not callable(_method):
            print(f'No such method: {self.__class__.__name__}.{method_name}')
            raise RuntimeError(f'No such method: {self.__class__.__name__}.{method_name}')
        return _method(*args)

    def filter(self, attr_filter):
        _result = []
        for _u in self.__objects.values():
            _match = True
            for _k, _fv in attr_filter.items():
                if _k.endswith('__in'):
                    _k = _k[:-4]
                    _uv = _u.get(_k)
                    if _uv is None:
                        print(f'1 Unknown filter attribute {self.__class__.__name__}.{_k}')
                        print(f'Attributes are: {_u.keys()}')
                        _match = False
                        break
                    if _uv not in _fv:
                        _match = False
                        break
                    continue
                if _k.endswith('__iregex'):
                    _k = _k[:-8]
                    _uv = _u.get(_k)
                    if _uv is None:
                        print(f'1 Unknown filter attribute {self.__class__.__name__}.{_k}')
                        print(f'Attributes are: {_u.keys()}')
                        _match = False
                        break
                    if _uv not in _fv:
                        _match = False
                        break
                    if re.search(_fv, _uv, re.IGNORECASE) is None:
                        _match = False
                        break
                    continue
                _uv = _u.get(_k)
                if _uv is None:
                    print(f'3 Unknown filter attribute {self.__class__.__name__}.{_k}')
                    print(_k)
                    print(f'Attributes are: {_u.keys()}')
                if _uv != _fv:
                    _match = False
                    break
            if _match:
                _result.append(_u)
        print(_result)
        return _result


class Auth(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _u in data_set.master_data_of_type(ATTR_TCMS_USERS):
            self._XmlRpcHandler__objects[_u[ATTR_ID]] = _u

    def login(self, username, _password):
        for _u in self._XmlRpcHandler__objects.values():
            print(_u)
            if username == _u[ATTR_USERNAME]:
                return str(time.perf_counter_ns())
        raise RuntimeError('access denied')


class Build(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _b in data_set.master_data_of_type(ATTR_PRODUCT_BUILDS):
            self._XmlRpcHandler__objects[_b[ATTR_ID]] = _b


class Category(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _c in data_set.master_data_of_type(ATTR_CASE_CATEGORIES):
            self._XmlRpcHandler__objects[_c[ATTR_ID]] = _c


class Classification(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _c in data_set.master_data_of_type(ATTR_PRODUCT_CLASSIFICATIONS):
            self._XmlRpcHandler__objects[_c[ATTR_ID]] = _c


class Environment(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        self._XmlRpcHandler__objects.update(data_set.objects_of_class(TCMS_CLASS_ID_ENVIRONMENT))


class KiwiTCMS(XmlRpcHandler):
    def version(self):
        return KIWI_TCMS_VERSION


class Product(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _prod in data_set[ATTR_PRODUCT]:
            _prod_id = _prod[ATTR_ID]
            self._XmlRpcHandler__objects[_prod_id] = _prod


class TestCase(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        self._XmlRpcHandler__objects.update(data_set.objects_of_class(TCMS_CLASS_ID_TEST_CASE))


class TestPlan(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        self._XmlRpcHandler__objects.update(data_set.objects_of_class(TCMS_CLASS_ID_TEST_PLAN))

    def list_attachments(self, plan_id):
        # not yet supported
        return []

    def tree(self, plan_id):
        result = []
        _parent = self._XmlRpcHandler__objects.get(plan_id)
        if _parent is None:
            raise RuntimeError(f"TestPlan {plan_id} doesn't exist")
        result.append(_parent)
        _generation = [plan_id]
        while len(_generation) > 0:
            _next_generation = []
            for _p_id, _p in self._XmlRpcHandler__objects.items():
                _parent_id = _p.get(ATTR_PARENT)
                if _parent_id is None:
                    _parent_id = -1
                if _parent_id in _generation:
                    result.append(_p)
                    _next_generation.append(_p_id)
            _generation = _next_generation
        return result


class TestCaseStatus(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _u in data_set.master_data_of_type(ATTR_CASE_STATUSES):
            self._XmlRpcHandler__objects[_u[ATTR_ID]] = _u


class TestExecutionStatus(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _s in data_set.master_data_of_type(ATTR_EXECUTION_STATUSES):
            self._XmlRpcHandler__objects[_s[ATTR_ID]] = _s


class User(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _u in data_set.master_data_of_type(ATTR_TCMS_USERS):
            self._XmlRpcHandler__objects[_u[ATTR_ID]] = _u


class Version(XmlRpcHandler):
    def __init__(self, data_set):
        super().__init__()
        for _v in data_set.master_data_of_type(ATTR_PRODUCT_VERSIONS):
            self._XmlRpcHandler__objects[_v[ATTR_ID]] = _v


class XmlRpcDispatcher:
    def __init__(self, input_file):
        """
        Constructor
        :param str input_file: the file containing TCMS data for the server
        """
        super().__init__()
        self.__data_set = DataSet.from_file(input_file)
        self.__handlers = {'Auth': Auth(self.__data_set),
                           'Build': Build(self.__data_set),
                           'Category': Category(self.__data_set),
                           'Classification': Classification(self.__data_set),
                           'Environment': Environment(self.__data_set),
                           'KiwiTCMS': KiwiTCMS(),
                           'Product': Product(self.__data_set),
                           'TestCase': TestCase(self.__data_set),
                           'TestCaseStatus': TestCaseStatus(self.__data_set),
                           'TestExecutionStatus': TestExecutionStatus(self.__data_set),
                           'TestPlan': TestPlan(self.__data_set),
                           'Version': Version(self.__data_set),
                           'User': User(self.__data_set)}

    def _dispatch(self, method, args):
        _handler_name, _method = method.split('.')
        _handler = self.__handlers.get(_handler_name)
        if _handler is None:
            print(f'No such method: {method}')
            raise RuntimeError(f'No such method: {method}')
        return _handler.dispatch(_method, args)


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/xml-rpc/',)


if __name__ == '__main__':
    _argp = ArgumentParser()
    _argp.add_argument('--port', type=int, default=9622)
    _argp.add_argument('input_file')
    _args = _argp.parse_args(sys.argv[1:])
    with SimpleXMLRPCServer(("localhost", _args.port),
                            requestHandler=RequestHandler) as server:
        server.register_introspection_functions()
        server.register_instance(XmlRpcDispatcher(_args.input_file))

        # Run the server's main loop
        server.serve_forever()
