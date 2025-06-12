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
Dialog windows for the Issai GUI.
"""

import math
import os.path
from pathlib import Path
import time

from PySide6.QtCore import qVersion, QDir, QThreadPool, Qt, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor, QColorConstants, QPen, QRadialGradient, QPixmap
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QWidget, QLabel, QComboBox, QProgressBar, QListWidget, QDialog, QFileDialog, QPushButton,
                               QMessageBox, QGridLayout, QVBoxLayout, QGroupBox, QListWidgetItem, QLineEdit,
                               QDialogButtonBox, QSizePolicy)

from issai.core.tcms import *
from issai.gui.workers import Worker


class PdfViewerDialog(QDialog):
    """
    Dialog window to show a PDF file.
    """
    def __init__(self, parent, title_id, file_path):
        """
        Constructor
        :param QWidget parent: the parent widget
        :param str title_id: the window title resource ID
        :param str file_path: the PDF file name including full path
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _PDF_VIEWER_OFFSET, _parent_rect.y() + _PDF_VIEWER_OFFSET,
                         _PDF_VIEWER_WIDTH, _PDF_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QVBoxLayout()
        _web_view = QWebEngineView()
        _view_settings = _web_view.settings()
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        _web_view.load(f'file://{file_path}')
        _dlg_layout.addWidget(_web_view)
        self.setLayout(_dlg_layout)


class AboutDialog(QDialog):
    """
    About Issai dialog.
    """
    def __init__(self, parent):
        """
        Constructor
        :param QWidget parent: the parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_ABOUT))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _ABOUT_DIALOG_OFFSET, _parent_rect.y() + _ISSAI_IMAGE_SIZE,
                         _ABOUT_DIALOG_WIDTH, _ABOUT_DIALOG_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QGridLayout()
        _dlg_layout.setSpacing(10)
        self.__issai_image = QLabel()
        _pixmap = QPixmap(_ISSAI_IMAGE_SIZE, _ISSAI_IMAGE_SIZE)
        _pixmap.fill(QColorConstants.White)
        self.__issai_image.setPixmap(_pixmap)
        _dlg_layout.addWidget(self.__issai_image, 0, 0, 4, 1)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_TEXT)), 0, 1,
                              Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_DETAIL_TEXT, VERSION, qVersion())),
                              1, 1, Qt.AlignmentFlag.AlignCenter)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_INFO_TEXT)), 2, 1,
                              Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        _ok_button = QPushButton(localized_label(L_OK))
        _ok_button.clicked.connect(self.close)
        _dlg_layout.addWidget(_ok_button, 3, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(_dlg_layout)
        self._draw_image()

    def _draw_image(self):
        """
        Draws an issai fruit image.
        """
        _pixmap = self.__issai_image.pixmap()
        painter = QPainter(_pixmap)
        _bright_yellow = QColor(0xff, 0xee, 0xcc)
        _rect = _pixmap.rect()
        # draw background regions
        _center = QPoint(_rect.x() + (_rect.width() >> 1), _rect.y() + (_rect.height() >> 1))
        _radius = (min(_rect.width(), _rect.height()) >> 1) - _ISSAI_IMAGE_SPACING
        _gradient = QRadialGradient(_center, _radius)
        _gradient.setColorAt(0.1, _bright_yellow)
        _gradient.setColorAt(0.5, QColorConstants.Yellow)
        _gradient.setColorAt(1.0, QColorConstants.DarkGreen)
        painter.setPen(QPen(QColorConstants.DarkGray, 2, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(_gradient))
        painter.drawEllipse(_center, _radius, _radius)
        # draw beams
        _inner_radius = _radius * 0.3
        _outer_radius = _radius * 0.9
        _step = math.pi / 10.0
        _inner_beam_width = math.pi / 50
        _outer_beam_width = _inner_beam_width / 3
        _angle = 0.0
        painter.setPen(QPen(QColorConstants.Yellow, 1, Qt.PenStyle.SolidLine))
        while _angle < 2 * math.pi:
            _inner_x = int(_center.x() + _inner_radius * math.cos(_angle))
            _inner_y = int(_center.y() + _inner_radius * math.sin(_angle))
            _inner_x1 = int(_center.x() + _inner_radius * math.cos(_angle-_inner_beam_width))
            _inner_y1 = int(_center.y() + _inner_radius * math.sin(_angle-_inner_beam_width))
            _inner_x2 = int(_center.x() + _inner_radius * math.cos(_angle+_inner_beam_width))
            _inner_y2 = int(_center.y() + _inner_radius * math.sin(_angle+_inner_beam_width))
            _outer_x1 = int(_center.x() + _outer_radius * math.cos(_angle-_outer_beam_width))
            _outer_y1 = int(_center.y() + _outer_radius * math.sin(_angle-_outer_beam_width))
            _outer_x2 = int(_center.x() + _outer_radius * math.cos(_angle+_outer_beam_width))
            _outer_y2 = int(_center.y() + _outer_radius * math.sin(_angle+_outer_beam_width))
            _beam_gradient = QRadialGradient(QPoint(_inner_x, _inner_y), _outer_radius - _inner_radius)
            _beam_gradient.setColorAt(0.3, QColorConstants.Yellow)
            _beam_gradient.setColorAt(1.0, _bright_yellow)
            painter.setBrush(QBrush(_beam_gradient))
            painter.drawPolygon([QPoint(_inner_x1, _inner_y1), QPoint(_outer_x1, _outer_y1),
                                 QPoint(_outer_x2, _outer_y2), QPoint(_inner_x2, _inner_y2)])
            _angle += _step
        # draw pits
        _pit_radius = _radius * 0.45
        _pit_width = int(_radius * 0.08)
        _pit_height = int(_pit_width / 4)
        _angle = math.pi / 20.0
        _pit_color = QColor(0x44, 0x22, 0x55)
        painter.setPen(QPen(_pit_color, 1, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(_pit_color))
        while _angle < 2 * math.pi:
            _pit_x = int(_center.x() + _pit_radius * math.cos(_angle))
            _pit_y = int(_center.y() + _pit_radius * math.sin(_angle))
            painter.save()
            painter.translate(QPoint(_pit_x, _pit_y))
            painter.rotate(_angle * 180 / math.pi)
            painter.drawEllipse(QPoint(0, 0), _pit_width, _pit_height)
            painter.restore()
            _angle += _step
        painter.end()
        self.__issai_image.setPixmap(_pixmap)


class IssaiProductSelectionDialog(QDialog):
    """
    Dialog window to select one of the locally available products.
    Needed to edit product settings and export an entire product.
    """
    def __init__(self, parent, products):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param list products: the DirEntry descriptors for all subdirectories containing product configurations
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_PRODUCT_SELECTION))
        _dlg_layout = QGridLayout()
        _dlg_layout.setSpacing(10)
        _products_combo_label = QLabel(localized_label(L_COMBO_AVAILABLE_PRODUCTS))
        _products_combo_label.setStyleSheet(_STYLE_BOLD_TEXT)
        _dlg_layout.addWidget(_products_combo_label, 0, 0)
        self.__products_combo_box = QComboBox(self)
        for _p in products:
            self.__products_combo_box.addItem(_p.name, _p.path)
        _dlg_layout.addWidget(self.__products_combo_box, 0, 1)
        _select_button = QPushButton(localized_label(L_SELECT))
        _select_button.setStyleSheet(_STYLE_BOLD_TEXT)
        _select_button.clicked.connect(self.accept)
        _dlg_layout.addWidget(_select_button, 1, 0)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.setStyleSheet(_STYLE_BOLD_TEXT)
        _cancel_button.clicked.connect(self.reject)
        _dlg_layout.addWidget(_cancel_button, 1, 1)
        self.setLayout(_dlg_layout)

    def selected_product_config_path(self):
        """
        :returns: product configuration directory including full path
        :rtype: str
        """
        return self.__products_combo_box.currentData()

    def selected_product_name(self):
        """
        :returns: Issai name of selected product
        :rtype: str
        """
        return self.__products_combo_box.currentText()


class NoProductConfiguredDialog(QDialog):
    """
    Dialog window to enter name and repository path for the first product.
    """
    def __init__(self, parent):
        """
        Constructor.
        :param QWidget parent: the parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_FIRST_PRODUCT))
        _dlg_layout = QGridLayout()
        _dlg_layout.setSpacing(10)
        _info_label = QLabel(localized_label(I_GUI_CREATE_FIRST_PRODUCT))
        _dlg_layout.addWidget(_info_label, 0, 0, 1, 2)
        _products_name_label = QLabel(localized_label(L_PRODUCT_NAME))
        _products_name_label.setStyleSheet(_STYLE_BOLD_TEXT)
        _dlg_layout.addWidget(_products_name_label, 1, 0)
        self.__product_name = QLineEdit()
        _dlg_layout.addWidget(self.__product_name, 1, 1)
        _repo_path_label = QLabel(localized_label(L_REPOSITORY_PATH))
        _repo_path_label.setStyleSheet(_STYLE_BOLD_TEXT)
        _dlg_layout.addWidget(_repo_path_label, 2, 0)
        self.__path_selection_button = QPushButton(localized_label(L_SELECT_PATH))
        self.__path_selection_button.clicked.connect(self.select_path)
        _dlg_layout.addWidget(self.__path_selection_button, 2, 1)
        self.__create_button = QPushButton(localized_label(L_CREATE))
        self.__create_button.setStyleSheet(_STYLE_BOLD_TEXT)
        self.__create_button.clicked.connect(self.create_product)
        _dlg_layout.addWidget(self.__create_button, 3, 0)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.setStyleSheet(_STYLE_BOLD_TEXT)
        _cancel_button.clicked.connect(self.reject)
        _dlg_layout.addWidget(_cancel_button, 3, 1)
        self.setLayout(_dlg_layout)

    def selected_product_name(self):
        """
        :returns: product name
        :rtype: str
        """
        return self.__product_name.text()

    def selected_repository_path(self):
        """
        :returns: Issai name of selected product
        :rtype: str
        """
        return self.__path_selection_button.text()

    def select_path(self):
        """
        Called when path selection button has been clicked.
        """
        _dlg = QFileDialog(self, localized_label(L_DLG_TITLE_SELECT_PRODUCT_REPO_PATH), str(Path.home()))
        _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
        _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
        _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        _dlg.setFileMode(QFileDialog.FileMode.Directory)
        if _dlg.exec():
            self.__path_selection_button.setText(_dlg.selectedFiles()[0])
        _dlg.close()

    def create_product(self):
        """
        Called when create button has been clicked.
        """
        if len(self.__product_name.text()) == 0:
            return
        if self.__path_selection_button.text() == localized_label(L_SELECT_PATH):
            return
        self.accept()


class ProgressDialog(QDialog):
    """
    Dialog window to show the progress of an asynchronous task.
    """
    def __init__(self, parent, action, entity, options, local_cfg, file_or_working_path):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param int action: the action to monitor
        :param Entity entity: the entity data
        :param dict options: the action specific options
        :param LocalConfiguration local_cfg: the local issai configuration
        :param str file_or_working_path: the output directory for exports, the input file for imports,
                                         the working directory for runs
        """
        super().__init__(parent)
        self.__action_finished = False
        self.__worker = Worker.for_action(action, entity, options, local_cfg, file_or_working_path)
        self.__worker.connect_signals(self._handle_progress, self._handle_finish,
                                      self._handle_result, self._handle_error)
        if action == ACTION_IMPORT:
            _pure_file_name = os.path.basename(file_or_working_path)
            _title = localized_message(L_DLG_TITLE_IMPORT_FILE, _pure_file_name)
        elif action == ACTION_RUN_TCMS_PLAN:
            _title = localized_message(L_DLG_TITLE_RUN_PLAN, entity[ATTR_NAME])
        elif action == ACTION_RUN_OFFLINE_PLAN:
            _title = localized_message(L_DLG_TITLE_RUN_PLAN, entity[ATTR_ENTITY_NAME])
        elif action == ACTION_EXPORT_CASE:
            _title = localized_message(L_DLG_TITLE_EXPORT_PRODUCT, entity[ATTR_NAME])
        elif action == ACTION_EXPORT_PLAN:
            _title = localized_message(L_DLG_TITLE_EXPORT_PLAN, entity[ATTR_NAME])
        else:
            _title = localized_message(L_DLG_TITLE_EXPORT_PRODUCT, entity[ATTR_NAME])
        self.setWindowTitle(_title)
        self.setGeometry(200, 200, 800, 500)
        _dlg_layout = QGridLayout()
        _info_box = QGroupBox(self)
        _info_box_layout = QVBoxLayout()
        self.__progress_bar = QProgressBar(self)
        _info_box_layout.addWidget(self.__progress_bar)
        self.__infos = QListWidget(self)
        self.__infos.setMinimumHeight(250)
        _start_info = localized_message(I_GUI_PROGRESS_TASK_STARTED, time.strftime('%X', time.localtime()))
        self.__infos.addItem(_start_info)
        _info_box_layout.addWidget(self.__infos)
        self.__result = QLabel(localized_message(I_GUI_PROGRESS_TASK_RUNNING))
        _info_box_layout.addWidget(self.__result)
        _info_box.setLayout(_info_box_layout)
        _dlg_layout.addWidget(_info_box, 0, 0, 1, 2)
        self.__cancel_button = QPushButton(localized_label(L_CANCEL))
        self.__cancel_button.clicked.connect(self._cancel_button_clicked)
        _dlg_layout.addWidget(self.__cancel_button, 1, 0, Qt.AlignmentFlag.AlignCenter)
        self.__close_button = QPushButton(localized_label(L_CLOSE))
        self.__close_button.setEnabled(False)
        self.__close_button.clicked.connect(self.close)
        _dlg_layout.addWidget(self.__close_button, 1, 1, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(_dlg_layout)

    def exec(self):
        """
        Instantiates background worker and starts appropriate task.
        """
        QThreadPool.globalInstance().start(self.__worker)
        return super().exec()

    def _cancel_button_clicked(self):
        """
        Called when the user clicked the cancel button. Signals background worker to abort its task.
        """
        if not self.__action_finished:
            self.__worker.abort()

    def _handle_progress(self, progress_info):
        """
        Displays a progress message issued by asynchronous task.
        :param (int, str, str) progress_info: progress value, message severity, localized message
        """
        self.__progress_bar.setValue(progress_info[0])
        self._show_message(progress_info[1], progress_info[2])

    def _handle_finish(self):
        """
        Informs the user that the asynchronous task succeeded and updates the button statuses.
        """
        _info = localized_message(I_GUI_PROGRESS_TASK_FINISHED, time.strftime('%X', time.localtime()))
        self._show_message(SEVERITY_INFO, _info)
        self.__progress_bar.setValue(100)
        self.__cancel_button.setEnabled(False)
        self.__close_button.setEnabled(True)

    def _handle_result(self, result):
        """
        Displays summary of asynchronous task.
        :param TaskResult result: the task result
        """
        self.__result.setText(result.summary())

    def _handle_error(self, exception):
        """
        Informs the user that the asynchronous task fails and updates the button statuses.
        :param Exception exception: the exception causing task failure
        """
        self.__result.setText(localized_message(I_GUI_PROGRESS_TASK_FAILED))
        self._show_message(SEVERITY_ERROR, str(exception))
        self.__progress_bar.setValue(100)
        self.__cancel_button.setEnabled(False)
        self.__close_button.setEnabled(True)

    def _show_message(self, severity, text):
        """
        Displays a message received from asynchronous task. The message text is colored according to severity.
        :param str severity: the severity ('e' for error, 'w' for warning, 'i' for informational)
        :param str text: the localized text
        """
        _info = QListWidgetItem(text)
        if severity == SEVERITY_ERROR:
            _info.setForeground(QBrush(Qt.GlobalColor.red))
        elif severity == SEVERITY_WARNING:
            _info.setForeground(QBrush(Qt.GlobalColor.blue))
        else:
            _info.setForeground(QBrush(Qt.GlobalColor.black))
        self.__infos.addItem(_info)
        self.__infos.scrollToBottom()


class RecentEntityDialog(QDialog):
    """
    Dialog window to select a test entity from a list of recently used ones.
    """

    def __init__(self, parent, entities):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param list entities: recently used entities
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_LRU_ENTITIES))
        _dlg_layout = QVBoxLayout()
        self.__entity_list = QListWidget()
        self.__entity_list.setStyleSheet(_STYLE_WHITE_BG)
        [self.__entity_list.addItem(_e) for _e in entities]
        _dlg_layout.addWidget(self.__entity_list)
        _button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        _button_box.setCenterButtons(True)
        _button_box.accepted.connect(self.accept)
        _button_box.rejected.connect(self.reject)
        _dlg_layout.addWidget(_button_box)
        self.setLayout(_dlg_layout)

    def selected_entity(self):
        """
        :returns: selected entity, None if nothing selected
        :rtype: str
        """
        _selected_entity = self.__entity_list.currentItem()
        return None if _selected_entity is None else _selected_entity.text()


class NameInputDialog(QDialog):
    """
    Dialog window to enter a name for a new software version or build.
    Currently existing names are displayed in a table.
    """

    def __init__(self, parent, title_id, list_id, existing_names):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param str title_id: label ID of window title
        :param str list_id: label ID of list caption for currently existing versions or builds
        :param list existing_names: names of all currently existing versions or builds
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(title_id))
        _dlg_layout = QVBoxLayout()
        _name_list_caption = QLabel(localized_label(list_id))
        _name_list_caption.setStyleSheet(_STYLE_BOLD_TEXT)
        _dlg_layout.addWidget(_name_list_caption)
        _name_list = QListWidget()
        _name_list.setStyleSheet(_STYLE_WHITE_BG)
        [_name_list.addItem(_e) for _e in existing_names]
        _dlg_layout.addWidget(_name_list)
        _name_field_caption = QLabel(localized_label(L_NEW_NAME))
        _name_field_caption.setStyleSheet(_STYLE_BOLD_TEXT)
        _dlg_layout.addWidget(_name_field_caption)
        self.__name_field = QLineEdit()
        self.__name_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__name_field.setStyleSheet(_STYLE_INPUT_FIELD)
        _dlg_layout.addWidget(self.__name_field)
        _button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        _button_box.setCenterButtons(True)
        _button_box.accepted.connect(self.accept)
        _button_box.rejected.connect(self.reject)
        _dlg_layout.addWidget(_button_box)
        self.setLayout(_dlg_layout)

    def name(self):
        """
        :returns: new name
        :rtype: str
        """
        return self.__name_field.text()


def select_output_dir(parent, preferred_dir):
    """
    Dialog window to select an output directory.
    :param QWidget parent: the parent widget
    :param str preferred_dir: the preferred output directory
    :returns: selected output directory including full path; None if dialog was canceled
    :rtype: str
    """
    _selected_file_path = None
    _dlg = QFileDialog(parent, localized_label(L_DLG_TITLE_SELECT_EXPORT_OUTPUT_PATH), preferred_dir)
    _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
    _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
    _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    _dlg.setFileMode(QFileDialog.FileMode.Directory)
    if _dlg.exec():
        _selected_file_path = _dlg.selectedFiles()[0]
    _dlg.close()
    return _selected_file_path


def select_entity_file(parent, preferred_dir):
    """
    Dialog window to select an entity file for import or execution.
    :param QWidget parent: the parent widget
    :param str preferred_dir: the preferred directory to look for import files
    :returns: selected file name including full path; None if dialog was canceled
    :rtype: str
    """
    _selected_file_path = None
    _dlg = QFileDialog(parent, localized_label(L_DLG_TITLE_SELECT_IMPORT_FILE), preferred_dir)
    _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
    _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
    _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    _dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
    _dlg.setNameFilter('*.toml')
    if _dlg.exec():
        _selected_file_path = _dlg.selectedFiles()[0]
    _dlg.close()
    return _selected_file_path


def exception_box(icon, reason, question, buttons, default_button):
    """
    Creates and returns a message box in reaction to an exception.
    :param QMessageBox.Icon icon: the severity icon
    :param BaseException reason: the reason for the message box
    :param str question: the localized question to ask
    :param QMessageBox.StandardButtons buttons: the buttons to choose from
    :param QMessageBox.StandardButton default_button: the default button
    :returns: the message box
    :rtype: QMessageBox
    """
    _msg_box = QMessageBox()
    _msg_box.setIcon(icon)
    if icon == QMessageBox.Icon.Critical:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_ERROR))
    elif icon == QMessageBox.Icon.Information:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_WARNING))
    else:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_INFO))
    _msg_box.setText(str(reason))
    _msg_box.setInformativeText(question)
    _msg_box.setStandardButtons(buttons)
    _msg_box.setDefaultButton(default_button)
    _msg_box.setStyleSheet(_STYLE_EXCEPTION_BOX_INFO)
    return _msg_box


_ABOUT_DIALOG_HEIGHT = 320
_ABOUT_DIALOG_OFFSET = 80
_ABOUT_DIALOG_WIDTH = 560
_ISSAI_IMAGE_SIZE = 256
_ISSAI_IMAGE_SPACING = 16
_PDF_VIEWER_HEIGHT = 720
_PDF_VIEWER_OFFSET = 10
_PDF_VIEWER_WIDTH = 640

_STYLE_INPUT_FIELD = 'background-color: #ffffcc'
_STYLE_WHITE_BG = 'background-color: white'
_STYLE_BOLD_TEXT = 'font-weight: bold'
_STYLE_EXCEPTION_BOX_INFO = 'QLabel#qt_msgbox_informativelabel {font-weight: bold}'
_STYLE_RUN_BUTTON = 'background-color: green; color: white; font-weight: bold'
