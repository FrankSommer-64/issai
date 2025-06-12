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
Status classes.
"""

from issai.core import *
from issai.core.messages import *


class ContainerStatus(dict):
    """
    Holds information about issues in a TOML container holding an Issai entity.
    """

    INVALID_TYPE = 'invalid-type'
    INVALID_VALUE = 'invalid-value'
    MISMATCH = 'mismatch'
    MISSING = 'missing'
    MULTIPLE = 'multiple'
    UNSUPPORTED = 'unsupported'

    def __init__(self):
        """
        Constructor.
        """
        super().__init__()
        self[ContainerStatus.INVALID_TYPE] = []
        self[ContainerStatus.INVALID_VALUE] = []
        self[ContainerStatus.MISMATCH] = []
        self[ContainerStatus.MISSING] = []
        self[ContainerStatus.MULTIPLE] = []
        self[ContainerStatus.UNSUPPORTED] = []

    def add_issue(self, issue_category, attribute_name, element_nr=-1, attribute_name2=''):
        """
        Adds an issue found during container check.
        :param str issue_category: the issue category
        :param str attribute_name: the name of the attribute causing the issue
        :param int element_nr: the optional number of the array element containing the problematic attribute
        :param str attribute_name2: the mismatching attribute name
        """
        _issue_value = [attribute_name2, attribute_name] if len(attribute_name2) > 0 else [attribute_name]
        if element_nr >= 0:
            _name_qualifier = f'(#{element_nr})'
            _attr_name = _issue_value[0]
            _last_dot_pos = _attr_name.rfind('.')
            if _last_dot_pos < 0:
                _index_attr_name = _attr_name + _name_qualifier
            else:
                _index_attr_name = _attr_name[:_last_dot_pos] + _name_qualifier + _attr_name[_last_dot_pos:]
            _issue_value[0] = _index_attr_name
        self[issue_category].append(_issue_value)

    def is_acceptable(self):
        """
        :returns: True, if container can be processed; False, if there is an uncorrectable problem
        :rtype: bool
        """
        return len(self[ContainerStatus.INVALID_TYPE]) == 0 and len(self[ContainerStatus.INVALID_VALUE]) == 0 and\
            len(self[ContainerStatus.MISMATCH]) == 0 and len(self[ContainerStatus.MISSING]) == 0 and\
            len(self[ContainerStatus.MULTIPLE]) == 0

    def issues(self):
        """
        :returns: all problems from this status
        :rtype: list
        """
        _issues = self.issues_of_category(ContainerStatus.INVALID_TYPE)
        _issues.extend(self.issues_of_category(ContainerStatus.INVALID_VALUE))
        _issues.extend(self.issues_of_category(ContainerStatus.MISMATCH))
        _issues.extend(self.issues_of_category(ContainerStatus.MISSING))
        _issues.extend(self.issues_of_category(ContainerStatus.MULTIPLE))
        _issues.extend(self.issues_of_category(ContainerStatus.UNSUPPORTED))
        return _issues

    def issues_of_category(self, issue_category):
        """
        Returns localized messages for problems with specified category.
        :param str issue_category: the issue category
        :returns: all problems with specified category
        :rtype: list
        """
        _issue_count = len(self[issue_category])
        if _issue_count == 0:
            return []
        _msg_code = ContainerStatus._message_code_for_category(issue_category)
        _issues = []
        for _issue_info in self[issue_category]:
            _issues.append(localized_message(_msg_code, *_issue_info))
        return _issues

    def issues_of_severity(self, issue_severity):
        """
        Returns localized messages for problems with specified severity.
        :param str issue_severity: the issue severity
        :returns: all problems with specified severity
        :rtype: list
        """
        if issue_severity == SEVERITY_WARNING:
            return self.issues_of_category(ContainerStatus.UNSUPPORTED)
        _issues = self.issues_of_category(ContainerStatus.INVALID_TYPE)
        _issues.extend(self.issues_of_category(ContainerStatus.INVALID_VALUE))
        _issues.extend(self.issues_of_category(ContainerStatus.MISMATCH))
        _issues.extend(self.issues_of_category(ContainerStatus.MISSING))
        _issues.extend(self.issues_of_category(ContainerStatus.MULTIPLE))
        return _issues

    @staticmethod
    def _message_code_for_category(issue_category):
        """
        :param str issue_category: the issue category
        :returns: message code for specified issue category
        :rtype: str
        """
        if issue_category == ContainerStatus.INVALID_TYPE:
            return E_IMP_ATTR_TYPE_INVALID
        if issue_category == ContainerStatus.INVALID_VALUE:
            return E_IMP_ATTR_VALUE_INVALID
        if issue_category == ContainerStatus.MISMATCH:
            return E_IMP_ATTR_MISMATCH
        if issue_category == ContainerStatus.MISSING:
            return E_IMP_ATTR_MISSING
        if issue_category == ContainerStatus.MULTIPLE:
            return E_IMP_ATTR_AMBIGUOUS
        return W_IMP_ATTR_NOT_SUPPORTED
