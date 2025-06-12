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
Issai entity classes.
The entities model central objects of Issai: products, test plans, test cases, test plan results and test case results.
Products can be exported from and imported to TCMS.
Test plans and test cases are also subject to export/import and can be executed.
Test plan results and test case results can be imported to TCMS.
"""

from tomlkit import load, TOMLDocument

from issai.core import *
from issai.core.entities import MasterData, SpecificationEntity, read_toml_value
from issai.core.issai_exception import IssaiException
from issai.core.messages import *


class DataSet(SpecificationEntity):
    """
    Base class for all types of issai entities.
    """
    def __init__(self):
        """
        Constructor.
        """
        super().__init__(ENTITY_TYPE_PRODUCT, 0, '')

    def fill_from_toml(self, toml_data):
        """
        Fills attributes of this entity from TOML.
        :param TOMLDocument toml_data: the TOML data, usually read from file
        """
        self[ATTR_PRODUCT] = read_toml_value(toml_data, 'products', list, True)
        self[ATTR_MASTER_DATA] = MasterData.from_toml(read_toml_value(toml_data, ATTR_MASTER_DATA, dict, True))
        self.add_environments(read_toml_value(toml_data, ATTR_ENVIRONMENTS, list))
        self.add_tcms_cases(read_toml_value(toml_data, ATTR_TEST_CASES, list))
        self.add_tcms_executions(read_toml_value(toml_data, ATTR_TEST_EXECUTIONS, list), True)
        self.add_tcms_plans(read_toml_value(toml_data, ATTR_TEST_PLANS, list))
        self.add_tcms_runs(read_toml_value(toml_data, ATTR_TEST_RUNS, list))

    @staticmethod
    def from_file(file_path):
        """
        Creates a data set from file.
        :param str file_path: the full path of the file containing the data set in TOML format
        :returns: created data set
        :rtype: DataSet
        :raises IssaiException: if the file could not be read
        """
        try:
            with open(file_path, 'r') as _f:
                _data_set = DataSet()
                _data_set.fill_from_toml(load(_f))
                return _data_set
        except IssaiException:
            raise
        except Exception as _e:
            raise IssaiException(E_READ_FILE_FAILED, file_path, _e)
