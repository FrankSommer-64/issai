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
Unit tests for module core.status.
"""

import unittest

from issai.core import *
from issai.core.messages import *
from issai.core.status import ContainerStatus


INV_TYPE_ATTR = 'invalid-type-attr'
INV_VALUE_ATTR = 'invalid-value-attr'
MISMATCH_ATTR_1 = 'entity-name'
MISMATCH_ATTR_2 = 'test-cases.case-name'
MISSING_ATTR = 'test-cases.missing'
QUALIFIED_MISMATCH_ATTR2 = 'test-cases(#1).case-name'
QUALIFIED_MISSING_ATTR = 'test-cases(#2).missing'
MULTIPLE_ATTR = 'duplicate'
UNSUPPORTED_ATTR = 'unsupported'


class TestStatus(unittest.TestCase):
    def test_container_status(self):
        """
        Tests for class ContainerStatus.
        """
        _cs = ContainerStatus()
        self._verify_container_status(_cs, True, 0, 0, 0, 0, 0, 0)
        _cs.add_issue(ContainerStatus.UNSUPPORTED, UNSUPPORTED_ATTR)
        self._verify_container_status(_cs, True, 0, 0, 0, 0, 0, 1)
        _cs.add_issue(ContainerStatus.INVALID_TYPE, INV_TYPE_ATTR)
        _cs.add_issue(ContainerStatus.INVALID_VALUE, INV_VALUE_ATTR)
        _cs.add_issue(ContainerStatus.MISMATCH, MISMATCH_ATTR_1, 1, MISMATCH_ATTR_2)
        _cs.add_issue(ContainerStatus.MISSING, MISSING_ATTR, 2)
        _cs.add_issue(ContainerStatus.MULTIPLE, MULTIPLE_ATTR)
        self._verify_container_status(_cs, False, 1, 1, 1, 1, 1, 1)
        _expected_issue = localized_message(E_IMP_ATTR_TYPE_INVALID, INV_TYPE_ATTR)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.INVALID_TYPE)[0])
        _expected_issue = localized_message(E_IMP_ATTR_VALUE_INVALID, INV_VALUE_ATTR)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.INVALID_VALUE)[0])
        _expected_issue = localized_message(E_IMP_ATTR_MISMATCH, QUALIFIED_MISMATCH_ATTR2, MISMATCH_ATTR_1)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.MISMATCH)[0])
        _expected_issue = localized_message(E_IMP_ATTR_MISSING, QUALIFIED_MISSING_ATTR)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.MISSING)[0])
        _expected_issue = localized_message(E_IMP_ATTR_AMBIGUOUS, MULTIPLE_ATTR)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.MULTIPLE)[0])
        _expected_issue = localized_message(W_IMP_ATTR_NOT_SUPPORTED, UNSUPPORTED_ATTR)
        self.assertEqual(_expected_issue, _cs.issues_of_category(ContainerStatus.UNSUPPORTED)[0])

    def _verify_container_status(self, status, acceptable, inv_type_count, inv_value_count, mismatch_count,
                                 missing_count, multiple_count, unsupported_count):
        """
        Verifies ContainerStatus object
        :param ContainerStatus status: the object to verify
        :param bool acceptable: expected value for method is_acceptable
        :param int inv_type_count: expected number of issues of category 'invalid type'
        :param int inv_value_count: expected number of issues of category 'invalid value'
        :param int mismatch_count: expected number of issues of category 'mismatch'
        :param int missing_count: expected number of issues of category 'missing'
        :param int multiple_count: expected number of issues of category 'multiple'
        :param int unsupported_count: expected number of issues of category 'unsupported'
        """
        self.assertEqual(acceptable, status.is_acceptable())
        self.assertEqual(inv_type_count, len(status.issues_of_category(ContainerStatus.INVALID_TYPE)))
        self.assertEqual(inv_value_count, len(status.issues_of_category(ContainerStatus.INVALID_VALUE)))
        self.assertEqual(mismatch_count, len(status.issues_of_category(ContainerStatus.MISMATCH)))
        self.assertEqual(missing_count, len(status.issues_of_category(ContainerStatus.MISSING)))
        self.assertEqual(multiple_count, len(status.issues_of_category(ContainerStatus.MULTIPLE)))
        self.assertEqual(unsupported_count, len(status.issues_of_category(ContainerStatus.UNSUPPORTED)))
        _sev_e_count = inv_type_count + inv_value_count + mismatch_count + missing_count + multiple_count
        self.assertEqual(_sev_e_count, len(status.issues_of_severity(SEVERITY_ERROR)))
        self.assertEqual(unsupported_count, len(status.issues_of_severity(SEVERITY_WARNING)))


if __name__ == '__main__':
    unittest.main()
