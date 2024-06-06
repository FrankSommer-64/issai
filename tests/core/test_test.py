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
Dummy unit test module for other unit tests.
Tests will always pass, except if environment variable ISSAI_TEST_TEST is set.
"""
import os
import unittest

from issai.core import ENVA_ISSAI_TEST_TEST
from issai.core.issai_exception import IssaiException
from issai.core.messages import E_INTERNAL_ERROR


class TestTest(unittest.TestCase):
    def test_will_succeed(self):
        """
        Successful test.
        """
        pass

    def test_will_fail(self):
        """
        Failed test.
        """
        if os.environ.get(ENVA_ISSAI_TEST_TEST) is None:
            return
        self.assertTrue(False)

    def test_will_raise(self):
        """
        Test raising exception.
        """
        if os.environ.get(ENVA_ISSAI_TEST_TEST) is None:
            return
        raise IssaiException(E_INTERNAL_ERROR, 'Forced failure')


if __name__ == '__main__':
    unittest.main()
