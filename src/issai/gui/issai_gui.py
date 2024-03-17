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

from issai.core import ISSAI_IMAGES_DIR
from issai.core.messages import (localized_label, localized_message, I_GUI_CONFIG_PROBLEM, I_GUI_CONFIG_WARNING,
                                 I_GUI_CREATE_CONFIG_ROOT, L_MBOX_TITLE_INFO, L_MBOX_TITLE_WARNING)
from issai.core.config import config_root_path, create_config_root, load_runtime_configs
from issai.core.issai_exception import IssaiException
from issai.gui.mainwindow import MainWindow


def gui_main():
    """
    Main function for Issai GUI.
    """
    try:
        _images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ISSAI_IMAGES_DIR)
        QDir.addSearchPath(ISSAI_IMAGES_DIR, _images_path)
        app = QApplication(sys.argv)
        try:
            _config_root_path = config_root_path()
        except IssaiException as _e:
            _buttons = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            _text = localized_message(I_GUI_CREATE_CONFIG_ROOT)
            _rc = _show_mbox(QMessageBox.Icon.Information, L_MBOX_TITLE_INFO, str(_e), _text, _buttons)
            if _rc == QMessageBox.StandardButton.Cancel:
                return
            _config_root_path = create_config_root()
        _master_config, _product_configs, _problems, _warnings = load_runtime_configs(_config_root_path)
        if _master_config is not None:
            os.environ.update(_master_config.environment_variables())
        if len(_problems) > 0 or len(_warnings) > 0:
            if len(_problems) > 0:
                _text = '%s%s%s%s' % (os.linesep.join(_problems), os.linesep, os.linesep, os.linesep.join(_warnings))
                _show_mbox(QMessageBox.Icon.Warning, L_MBOX_TITLE_WARNING, I_GUI_CONFIG_PROBLEM,
                           _text, QMessageBox.StandardButton.Ok)
            else:
                _show_mbox(QMessageBox.Icon.Information, L_MBOX_TITLE_INFO, I_GUI_CONFIG_WARNING,
                           os.linesep.join(_warnings), QMessageBox.StandardButton.Ok)
        main_win = MainWindow(_product_configs)
        main_win.show()
        app.aboutToQuit.connect(main_win.save_settings)
        sys.exit(app.exec())
    except Exception as e:
        print()
        print(e)
        sys.exit(1)


def _show_mbox(icon, title_id, info_text_id, text, buttons):
    """
    Shows message box.
    """
    _mbox = QMessageBox()
    _mbox.setIcon(icon)
    _mbox.setWindowTitle(localized_label(title_id))
    _mbox.setText(localized_message(info_text_id))
    _mbox.setInformativeText(text)
    _mbox.setStandardButtons(buttons)
    return _mbox.exec()


if __name__ == "__main__":
    gui_main()
