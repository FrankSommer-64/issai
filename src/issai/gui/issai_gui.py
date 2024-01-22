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
Main module of Issai GUI.
"""

import os
import sys

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QApplication, QMessageBox

from issai.core.messages import localized_label, localized_message, I_GUI_CONFIG_PROBLEM, L_MBOX_TITLE_INFO
from issai.core.config import load_runtime_configs
from issai.gui.mainwindow import MainWindow


_IMAGES_DIR = 'images'


if __name__ == '__main__':
    try:
        _images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _IMAGES_DIR)
        QDir.addSearchPath(_IMAGES_DIR, _images_path)
        app = QApplication(sys.argv)
        product_configs, problems = load_runtime_configs()
        if len(problems) > 0:
            mbox = QMessageBox()
            mbox.setIcon(QMessageBox.Icon.Information)
            mbox.setWindowTitle(localized_label(L_MBOX_TITLE_INFO))
            mbox.setText(localized_message(I_GUI_CONFIG_PROBLEM))
            mbox.setInformativeText(os.linesep.join(problems))
            mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
            mbox.exec()
        main_win = MainWindow(product_configs)
        main_win.show()
        app.aboutToQuit.connect(main_win.save_settings)
        sys.exit(app.exec())
    except Exception as e:
        print()
        print(e)
        sys.exit(1)
