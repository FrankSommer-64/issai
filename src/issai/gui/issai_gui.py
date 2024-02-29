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

from issai.core.messages import (localized_label, localized_message, I_GUI_CONFIG_PROBLEM, I_GUI_CONFIG_WARNING,
                                 L_MBOX_TITLE_INFO, L_MBOX_TITLE_WARNING)
from issai.core.config import load_runtime_configs, master_config
from issai.gui.mainwindow import MainWindow


_IMAGES_DIR = 'images'


def gui_main():
    try:
        _images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _IMAGES_DIR)
        QDir.addSearchPath(_IMAGES_DIR, _images_path)
        app = QApplication(sys.argv)
        _master_config = master_config()
        if _master_config is not None:
            os.environ.update(_master_config.environment_variables())
        _product_configs, _problems, _warnings = load_runtime_configs()
        if len(_problems) > 0 or len(_warnings) > 0:
            if len(_problems) > 0:
                _icon = QMessageBox.Icon.Warning
                _title_id = L_MBOX_TITLE_WARNING
                _info_text_id = I_GUI_CONFIG_PROBLEM
                _text = '%s%s%s%s' % (os.linesep.join(_problems), os.linesep, os.linesep, os.linesep.join(_warnings))
            else:
                _icon = QMessageBox.Icon.Information
                _title_id = L_MBOX_TITLE_INFO
                _info_text_id = I_GUI_CONFIG_WARNING
                _text = os.linesep.join(_warnings)
            mbox = QMessageBox()
            mbox.setIcon(_icon)
            mbox.setWindowTitle(localized_label(_title_id))
            mbox.setText(localized_message(_info_text_id))
            mbox.setInformativeText(_text)
            mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
            mbox.exec()
        main_win = MainWindow(_product_configs)
        main_win.show()
        app.aboutToQuit.connect(main_win.save_settings)
        sys.exit(app.exec())
    except Exception as e:
        print()
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    gui_main()
