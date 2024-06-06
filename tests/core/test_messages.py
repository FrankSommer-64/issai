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
Unit tests for core.messages.
"""

import os
import unittest

import issai.core.messages


EMPTY_MSGS = ['#####', '# no messages', '#####']
DEFAULT_MSGS = ['e-id-0 Internal error.', 'e-id-1 File {0} not found.', 'e-id-2 Failure for {0}: {1}.']


class TestMessages(unittest.TestCase):
    def test_init(self):
        msgs = os.linesep.join(EMPTY_MSGS)
        mt = issai.core.messages.MessageTable('en', msgs)
        self.assertEqual(0, len(mt), 'comment only definition')
        msgs = os.linesep.join(DEFAULT_MSGS)
        mt = issai.core.messages.MessageTable('en', msgs)
        self.assertEqual(len(DEFAULT_MSGS), len(mt), 'default definition')

    def test_message_for(self):
        msgs = os.linesep.join(DEFAULT_MSGS)
        mt = issai.core.messages.MessageTable('en', msgs)
        self.assertEqual('Internal error.', mt.message_for('e-id-0'), 'no args message')
        self.assertEqual('File x.txt not found.', mt.message_for('e-id-1', 'x.txt'), 'one arg message')
        self.assertEqual('Failure for x.txt: 999.', mt.message_for('e-id-2', 'x.txt', 999), 'two args message')
        self.assertEqual('e-id-1', mt.message_for('e-id-1'), 'arg missing')
        self.assertEqual('e-invalid', mt.message_for('e-invalid'), 'non-existing message ID')

    def test_for_locale(self):
        mt = issai.core.messages.MessageTable.for_locale('en')
        self.assertEqual('en', mt.locale(), 'default locale')
        mt = issai.core.messages.MessageTable.for_locale('de')
        self.assertEqual('de', mt.locale(), 'non default locale')
        mt = issai.core.messages.MessageTable.for_locale('xx')
        self.assertEqual('en', mt.locale(), 'unsupported locale')
        issai.core.messages._DEFAULT_LOCALE = 'yy'
        self.assertRaises(RuntimeError, issai.core.messages.MessageTable.for_locale, 'xx locale')


if __name__ == '__main__':
    unittest.main()
