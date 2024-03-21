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
Main window of Issai GUI.
"""

import os.path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMenuBar, QMessageBox, QWidget
from tomlkit import load

from issai.core import *
from issai.core.entities import Entity
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.resourcemanager import container_status
from issai.core.tcms import find_tcms_objects
from issai.gui.dialogs import (AboutDialog, IssaiProductSelectionDialog, NoProductConfiguredDialog,
                               exception_box, select_entity_file, select_output_dir)
from issai.gui.panes import TcmsActionPane, FileActionPane
from issai.gui.settings import GuiSettings
from issai.gui.configeditor import master_config_editor, product_config_editor, xml_rpc_credentials_editor


class MainWindow(QMainWindow):
    """
    Main window.
    """
    def __init__(self, config_path, local_config):
        """
        Constructor.
        :param str config_path: the Issai configuration root path
        :param list local_config: information about products supported on local platform
        """
        super().__init__()
        self.__config_path = config_path
        self.__local_config = local_config
        self.__settings = GuiSettings.load()
        self.setGeometry(self.__settings.win_geometry())
        self.setWindowTitle(localized_label(L_MAIN_WIN_DEFAULT_TITLE))
        # main menu
        self.setMenuBar(self._menu_bar())
        # central widget
        _welcome_pane = QWidget()
        _welcome_pane.setStyleSheet(_MAIN_WINDOW_STYLE)
        self.setCentralWidget(_welcome_pane)
        self.layout().setContentsMargins(_MAIN_WINDOW_MARGIN, _MAIN_WINDOW_MARGIN,
                                         _MAIN_WINDOW_MARGIN, _MAIN_WINDOW_MARGIN)
        self.layout().update()

    def save_settings(self):
        """
        Stores GUI settings to file
        """
        self.__settings.set_win_geometry(self.rect())
        try:
            self.__settings.save()
        except IssaiException as _e:
            QMessageBox.warning(self, localized_label(L_MBOX_TITLE_WARNING), str(_e), QMessageBox.StandardButton.Ok)

    def _menu_bar(self):
        """
        :returns: the main window's menu bar
        :rtype: QMenuBar
        """
        _bar = QMenuBar(self)

        # file menu with settings and exit items
        _file_menu = _bar.addMenu(localized_label(L_MENUBAR_ITEM_FILE))
        _settings_menu = _file_menu.addMenu(localized_label(L_MENU_ITEM_CONFIG))
        _settings_defaults_action = QAction(localized_label(L_ACTION_ITEM_CONFIG_MASTER), self)
        _settings_defaults_action.triggered.connect(self._update_master_config)
        _settings_menu.addAction(_settings_defaults_action)
        _settings_products_action = QAction(localized_label(L_ACTION_ITEM_CONFIG_PRODUCTS), self)
        _settings_products_action.triggered.connect(self._update_product_config)
        _settings_menu.addAction(_settings_products_action)
        _settings_xml_rpc_action = QAction(localized_label(L_ACTION_ITEM_CONFIG_XML_RPC), self)
        _settings_xml_rpc_action.triggered.connect(self._update_xml_rpc_credentials)
        _settings_menu.addAction(_settings_xml_rpc_action)
        _file_menu.addMenu(_settings_menu)
        _exit_action = QAction(localized_label(L_ACTION_ITEM_EXIT), self)
        _exit_action.triggered.connect(QApplication.quit)
        _file_menu.addAction(_exit_action)

        # run menu for test plans, test cases and offline tests from file
        _run_menu = _bar.addMenu(localized_label(L_MENUBAR_ITEM_RUN))
        _run_plan_action = QAction(localized_label(L_ACTION_ITEM_RUN_PLAN), self)
        _run_plan_action.triggered.connect(self._run_test_plan)
        _run_menu.addAction(_run_plan_action)
        _run_file_action = QAction(localized_label(L_ACTION_ITEM_RUN_FILE), self)
        _run_file_action.triggered.connect(self._run_offline_test)
        _run_menu.addAction(_run_file_action)

        # export menu for test plans, test cases and products
        _export_menu = _bar.addMenu(localized_label(L_MENUBAR_ITEM_EXPORT))
        _export_plan_action = QAction(localized_label(L_ACTION_ITEM_EXPORT_PLAN), self)
        _export_plan_action.triggered.connect(self._export_test_plan)
        _export_menu.addAction(_export_plan_action)
        _export_case_action = QAction(localized_label(L_ACTION_ITEM_EXPORT_CASE), self)
        _export_case_action.triggered.connect(self._export_test_case)
        _export_menu.addAction(_export_case_action)
        _export_product_action = QAction(localized_label(L_ACTION_ITEM_EXPORT_PRODUCT), self)
        _export_product_action.triggered.connect(self._export_product)
        _export_menu.addAction(_export_product_action)

        # import menu for files
        _import_action = QAction(localized_label(L_ACTION_ITEM_IMPORT), self)
        _import_action.triggered.connect(self._import_file)
        _bar.addAction(_import_action)

        # help menu with help and about
        _help_menu = _bar.addMenu(localized_label(L_MENUBAR_ITEM_HELP))
        _help_about_action = QAction(localized_label(L_ACTION_ITEM_HELP_ABOUT), self)
        _help_about_action.triggered.connect(self._about_dialog)
        _help_menu.addAction(_help_about_action)
        return _bar

    def _update_master_config(self):
        """
        Update Issai default settings.
        """
        try:
            _dlg = master_config_editor(self, self.__config_path)
            _dlg.exec()
        except IssaiException as _e:
            pass

    def _update_product_config(self):
        """
        Update Issai product settings.
        """
        _products = [f for f in os.scandir(self.__config_path) if os.path.isdir(f)]
        if len(_products) == 0:
            _dlg = NoProductConfiguredDialog(self)
            if _dlg.exec() == QDialog.DialogCode.Accepted:
                _product_name = _dlg.selected_product_name()
                _repo_path = _dlg.selected_repository_path()
                # noinspection PyBroadException
                try:
                    _product_path = os.path.join(self.__config_path, _product_name)
                    _product_config_file_path = os.path.join(_product_path, ISSAI_PRODUCT_CONFIG_FILE_NAME)
                    os.makedirs(_product_path, 0o755, True)
                    _my_path = os.path.dirname(__file__)
                    _product_template = os.path.abspath(os.path.join(_my_path, '..', ISSAI_TEMPLATES_DIR,
                                                                     ISSAI_PRODUCT_CONFIG_FILE_NAME))
                    with open(_product_template, 'r') as _f:
                        _template_data = _f.read()
                    _template_data = _template_data.replace('%PRODUCTNAME%', _product_name)
                    _template_data = _template_data.replace('%REPOSITORYPATH%', _repo_path)
                    with open(_product_config_file_path, 'w') as _f:
                        _f.write(_template_data)
                except BaseException as _e:
                    _mbox = exception_box(QMessageBox.Icon.Critical, _e, '',
                                          QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                    _mbox.exec()
            return
        try:
            _dlg = product_config_editor(self, _products)
            if _dlg is not None:
                _dlg.exec()
        except IssaiException as _e:
            pass

    def _update_xml_rpc_credentials(self):
        """
        Update XML-RPC credentials.
        """
        try:
            _dlg = xml_rpc_credentials_editor(self)
            _dlg.exec()
        except IssaiException as _e:
            pass

    def _run_offline_test(self):
        """
        Run an offline test from file.
        """
        _selected_file_path = select_entity_file(self, self.__settings.latest_input_dir())
        if _selected_file_path is None:
            return
        self.__settings.set_latest_input_dir(os.path.dirname(_selected_file_path))
        try:
            _entity = Entity.from_file(_selected_file_path)
        except BaseException as _e:
            _ie = IssaiException(E_LOAD_CONTAINER_FAILED, _selected_file_path, str(_e))
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_ie))
            return
        if _entity.entity_type_id() != ENTITY_TYPE_PLAN:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_CONTAINER_NOT_RUNNABLE, _selected_file_path))
            return
        try:
            self.setCentralWidget(FileActionPane(self, self.__settings, ACTION_RUN_OFFLINE_PLAN, _entity,
                                                 _selected_file_path))
        except IssaiException as _e:
            pass

    def _run_test_plan(self):
        """
        Run a test plan from TCMS.
        """
        try:
            _products = self._read_tcms_products()
            self.setCentralWidget(TcmsActionPane(self, self.__settings, ACTION_RUN_TCMS_PLAN,
                                                 ENTITY_TYPE_PLAN, _products))
        except IssaiException as _e:
            pass

    def _export_test_plan(self):
        """
        Export a test plan.
        """
        try:
            _products = self._read_tcms_products()
            self.setCentralWidget(TcmsActionPane(self, self.__settings, ACTION_EXPORT_PLAN,
                                                 ENTITY_TYPE_PLAN, _products))
        except IssaiException as _e:
            pass

    def _export_test_case(self):
        """
        Export a test case.
        """
        try:
            _products = self._read_tcms_products()
            self.setCentralWidget(TcmsActionPane(self, self.__settings, ACTION_EXPORT_CASE,
                                                 ENTITY_TYPE_CASE, _products))
        except IssaiException as _e:
            pass

    def _export_product(self):
        """
        Export a product.
        """
        try:
            _products = self._read_tcms_products()
            self.setCentralWidget(TcmsActionPane(self, self.__settings, ACTION_EXPORT_PRODUCT,
                                                 ENTITY_TYPE_PRODUCT, _products))
        except IssaiException as _e:
            pass

    def _import_file(self):
        """
        Import a test specification or result.
        """
        _selected_file_path = select_entity_file(self, self.__settings.latest_input_dir())
        if _selected_file_path is None:
            return
        self.__settings.set_latest_input_dir(os.path.dirname(_selected_file_path))
        try:
            with open(_selected_file_path, 'r') as _f:
                _toml_data = load(_f)
            _container_status = container_status(_toml_data)
            _msgs = ''
            for _msg in _container_status.issues_of_severity(SEVERITY_ERROR):
                _msgs = f'{_msgs}{os.linesep}{_msg}'
            for _msg in _container_status.issues_of_severity(SEVERITY_WARNING):
                _msgs = f'{_msgs}{os.linesep}{_msg}'
            if not _container_status.is_acceptable():
                raise IssaiException(E_LOAD_CONTAINER_FAILED, _selected_file_path, _msgs)
            _entity = Entity.from_toml_entity(_toml_data)
        except BaseException as _e:
            _ie = IssaiException(E_LOAD_CONTAINER_FAILED, _selected_file_path, str(_e))
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_ie))
            return
        try:
            self.setCentralWidget(FileActionPane(self, self.__settings, ACTION_IMPORT, _entity,
                                                 _selected_file_path))
        except IssaiException as _e:
            pass

    def _about_dialog(self):
        """
        Show about dialog.
        """
        _about_dlg = AboutDialog(self)
        _about_dlg.exec()

    def _determine_product_config(self, products):
        """
        Let the user choose a product and determines the appropriate runtime configuration for the selected product.
        :param list products: the Issai names of locally available products
        :returns: configuration of selected product; None, if the selected product is not properly configured or the
                  user aborted the action
        :rtype: LocalConfig
        """
        _sel_dlg = IssaiProductSelectionDialog(self, products)
        if _sel_dlg.exec() == 0:
            return
        _selected_product = _sel_dlg.selected_product_name()
        _product_config = None
        for _p in self.__local_config:
            if _p.issai_name() == _selected_product:
                _product_config = _p
                break
        if _product_config is None:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_CFG_PRODUCT_CONFIG_INVALID, _selected_product),
                                 QMessageBox.StandardButton.Ok)
        return _product_config

    def _determine_empty_output_path(self):
        """
        Let the user choose an empty directory for an action.
        :returns: selected directory including full path; None, if the user aborted the action
        :rtype: str
        """
        _output_path = None
        while True:
            _output_path = select_output_dir(self, self.__settings.latest_output_dir())
            if _output_path is None:
                return None
            if any(os.scandir(_output_path)):
                _dir_name = os.path.basename(_output_path)
                _rc = QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                           localized_message(E_DIR_NOT_EMPTY, _dir_name),
                                           QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel)
                if _rc == QMessageBox.StandardButton.Cancel:
                    return None
                continue
            break
        self.__settings.set_latest_output_dir(os.path.dirname(_output_path))
        return _output_path

    def _read_tcms_products(self):
        """
        Reads all products available in TCMS. Shows an error dialog, if no product is found.
        :returns: TCMS products data
        :rtype: list
        :raises IssaiException: if an error during communication with TCMS occurs or no product is available
        """
        try:
            _products = find_tcms_objects(TCMS_CLASS_ID_PRODUCT, {})
            if len(_products) == 0:
                raise IssaiException(E_TCMS_NO_PRODUCTS)
            return _products
        except Exception as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e))
            raise


_MAIN_WINDOW_MARGIN = 16
_MAIN_WINDOW_STYLE = 'border-image: url(images:issai-aq.jpg)'
