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
Central widget panes with functionality to select test entities, specify options and execute actions.
"""

import os.path
import shutil

from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QFileDialog, QFrame, QGroupBox, QWidget, QLabel, QComboBox, QLineEdit, QListWidget,
                               QDialog, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox, QDialogButtonBox,
                               QGridLayout, QFormLayout, QCheckBox)

from issai.core.config import config_root_path, master_config, product_config
from issai.core.tcms import *
from issai.gui.dialogs import ProgressDialog
from issai.gui.settings import GuiSettings


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
        self.__entity_list.setStyleSheet(_ENTITY_LIST_STYLE)
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


class FileActionPane(QGroupBox):
    """
    Central widget pane to run a file based action, i.e. an import or an offline test execution.
    """

    def __init__(self, parent, gui_settings, action, entity, file_path):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param GuiSettings gui_settings: the Issai GUI preferences for the current user
        :param int action: the action to execute
        :param Entity entity: the entity data
        :param str file_path: the path of the file containing the entity data
        """
        super().__init__(parent)
        self.__preferences = gui_settings
        self.__action = action
        self.__entity_data = entity
        self.__entity_type = entity.entity_type_id()
        self.__entity_name = entity.entity_name()
        self.__file_path = file_path

        _pane_layout = FileActionPane._create_layout()

        _pane_layout.addWidget(self._entity_info_box())
        _pane_layout.addWidget(self._options_box())

        if action == ACTION_IMPORT:
            _do_button_label = localized_label(L_IMPORT)
        else:
            _do_button_label = localized_label(L_RUN)
        _do_button = QPushButton(_do_button_label)
        _do_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        _do_button.setStyleSheet(_OPEN_BUTTON_STYLE)
        _do_button.clicked.connect(self._do_action)
        _pane_layout.addWidget(_do_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(_pane_layout)

    @staticmethod
    def _create_layout():
        """
        :returns: the pane's layout
        :rtype: QVBoxLayout
        """
        _layout = QVBoxLayout()
        _layout.setSpacing(20)
        _layout.setContentsMargins(5, 5, 5, 5)
        _layout.setStretch(0, 1)
        _layout.setStretch(1, 1)
        _layout.setStretch(2, 5)
        _layout.setStretch(3, 1)
        return _layout

    def _entity_info_box(self):
        """
        :returns: the upper group box containing entity information
        :rtype: QGroupBox
        """
        _entity_info_box = QGroupBox(localized_label(L_ENTITY), self)
        _entity_info_box.setStyleSheet(_GROUP_BOX_STYLE)
        _box_layout = QFormLayout()
        _box_layout.setContentsMargins(10, 24, 24, 10)
        _box_layout.setSpacing(20)
        _type_caption = QLabel(localized_label(L_TYPE))
        _type_caption.setStyleSheet(_CAPTION_STYLE)
        _type_label = QLabel(entity_type_name(self.__entity_type))
        _box_layout.addRow(_type_caption, _type_label)
        _name_caption = QLabel(localized_label(L_NAME))
        _name_caption.setStyleSheet(_CAPTION_STYLE)
        _name_text = QLineEdit(self.__entity_name)
        _name_text.setReadOnly(True)
        _box_layout.addRow(_name_caption, _name_text)
        _file_caption = QLabel(localized_label(L_FILE))
        _file_caption.setStyleSheet(_CAPTION_STYLE)
        _file_text = QLineEdit(self.__file_path)
        _file_text.setReadOnly(True)
        _box_layout.addRow(_file_caption, _file_text)
        if self.__action == ACTION_RUN_OFFLINE_PLAN:
            _product_caption = QLabel(localized_label(L_PRODUCT))
            _product_caption.setStyleSheet(_CAPTION_STYLE)
            _product = self.__entity_data.objects_of_class(TCMS_CLASS_ID_PRODUCT)
            _product_text = QLineEdit(_product[ATTR_NAME])
            _product_text.setReadOnly(True)
            _box_layout.addRow(_product_caption, _product_text)
            _version_combo_caption, self.__version_combo = _create_combo(self, self._version_selected, L_VERSION_COMBO)
            _box_layout.addRow(_version_combo_caption, self.__version_combo)
            _build_combo_caption, self.__build_combo = _create_combo(self, None, L_BUILD_COMBO)
            _box_layout.addRow(_build_combo_caption, self.__build_combo)
            self._initialize_combos()
        _entity_info_box.setLayout(_box_layout)
        return _entity_info_box

    def _options_box(self):
        """
        :returns: the lower group box containing option settings
        :rtype: QGroupBox
        """
        _options_box = QGroupBox(localized_label(L_OPTIONS), self)
        _options_box.setStyleSheet(_GROUP_BOX_STYLE)
        _options_box_layout = QFormLayout()
        _options_box_layout.setContentsMargins(10, 24, 24, 10)
        _options_box_layout.setSpacing(20)
        _options_box_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        _options_box.setLayout(_options_box_layout)

        if self.__action == ACTION_IMPORT:
            self.__attachments_option = _create_option(_options_box_layout, L_INCLUDE_ATTACHMENTS,
                                                       T_OPT_IMP_ATTACHMENTS, False)
            if self.__entity_type in (ENTITY_TYPE_PRODUCT, ENTITY_TYPE_PLAN):
                self.__env_option = _create_option(_options_box_layout, L_INCLUDE_ENVIRONMENTS,
                                                   T_OPT_IMP_ENVIRONMENTS, False)
            if self.__entity_type in (ENTITY_TYPE_CASE, ENTITY_TYPE_PLAN):
                self.__auto_create_option = _create_option(_options_box_layout, L_AUTO_CREATE_MASTER_DATA,
                                                           T_OPT_AUTO_CREATE_MASTER_DATA, False)
            _user_caption = QLabel(localized_label(L_IMPORT_USER_BEHAVIOUR))
            _user_caption.setStyleSheet(_CAPTION_STYLE)
            self.__user_option = QComboBox(self)
            self.__user_option.addItem(localized_label(L_IMPORT_USER_USE_NEVER), OPTION_VALUE_USER_REF_REPLACE_NEVER)
            self.__user_option.addItem(localized_label(L_IMPORT_USER_USE_MISSING),
                                       OPTION_VALUE_USER_REF_REPLACE_MISSING)
            self.__user_option.addItem(localized_label(L_IMPORT_USER_USE_ALWAYS), OPTION_VALUE_USER_REF_REPLACE_ALWAYS)
            self.__user_option.setToolTip(T_OPT_USER_IMPORT)
            _options_box_layout.addRow(_user_caption, self.__user_option)
            self.__dry_run_option = _create_option(_options_box_layout, L_DRY_RUN, T_OPT_DRY_RUN, False)
        else:
            self.__store_result_option = _create_option(_options_box_layout, L_STORE_RESULT, T_OPT_STORE_RESULT, False)
        return _options_box

    def _version_selected(self, index):
        """
        Called when a version has been selected.
        :param int index: the selected index in the version selection combo
        """
        if index >= 0:
            _version = self.__version_combo.currentData()
            self._fill_build_combo(self.__version_combo.currentData())

    def _initialize_combos(self):
        """
        Initializes version and build combo boxes.
        """
        _versions = self.__entity_data.master_data_of_type(ATTR_PRODUCT_VERSIONS)
        for _v in sorted(_versions, key=lambda _k: _k[ATTR_VALUE]):
            self.__version_combo.addItem(_v[ATTR_VALUE], _v)
        if len(_versions) == 1:
            self.__version_combo.setCurrentIndex(0)
            self._fill_build_combo(_versions[0])
        else:
            self.__version_combo.setCurrentIndex(-1)

    def _fill_build_combo(self, version):
        """
        Initializes build combo box for a product version.
        :param dict version: the selected version
        """
        self.__build_combo.clear()
        _builds = self.__entity_data.master_data_of_type(ATTR_PRODUCT_BUILDS)
        for _b in sorted(_builds, key=lambda _k: _k[ATTR_NAME]):
            if _b[ATTR_VERSION] == version[ATTR_ID]:
                self.__build_combo.addItem(_b[ATTR_NAME], _b)
        if self.__build_combo.count() == 1:
            self.__build_combo.setCurrentIndex(0)
        else:
            self.__build_combo.setCurrentIndex(-1)

    def _do_action(self):
        """
        Called when do button hsa been clicked.
        Starts the import or test execution and shows results in a progress dialog.
        """
        if self.__action == ACTION_IMPORT:
            _options = {OPTION_DRY_RUN: self.__dry_run_option.isChecked(),
                        OPTION_USER_REFERENCES: self.__user_option.currentData(),
                        OPTION_INCLUDE_ATTACHMENTS: self.__attachments_option.isChecked(),
                        OPTION_INCLUDE_ENVIRONMENTS: False,
                        OPTION_AUTO_CREATE: False}
            if self.__entity_type in (ENTITY_TYPE_PRODUCT, ENTITY_TYPE_PLAN):
                _options[OPTION_INCLUDE_ENVIRONMENTS] = self.__env_option.isChecked()
            if self.__entity_type in (ENTITY_TYPE_CASE, ENTITY_TYPE_PLAN):
                _options[OPTION_AUTO_CREATE] = self.__auto_create_option.isChecked()
            elif self.__entity_type == ENTITY_TYPE_PRODUCT:
                _options[OPTION_AUTO_CREATE] = True
            _prog_dlg = ProgressDialog(self, ACTION_IMPORT, self.__entity_data, _options, {}, self.__file_path)
        else:
            _version = self.__version_combo.currentData()
            if _version is None:
                QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                        localized_message(I_GUI_NO_VERSION_SELECTED), QMessageBox.StandardButton.Ok)
                return
            _build = self.__build_combo.currentData()
            if _build is None:
                QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                        localized_message(I_GUI_NO_BUILD_SELECTED), QMessageBox.StandardButton.Ok)
                return
            try:
                _config_path = config_root_path()
                _product = self.__entity_data.objects_of_class(TCMS_CLASS_ID_PRODUCT)
                _local_cfg = product_config(_config_path, _product[ATTR_NAME], master_config(_config_path))
            except IssaiException as _e:
                QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
                return
            _options = {OPTION_STORE_RESULT: self.__store_result_option.isChecked(),
                        OPTION_VERSION: _version, OPTION_BUILD: _build}
            _attachments_path = os.path.join(os.path.dirname(self.__file_path), ATTACHMENTS_ROOT_DIR)
            _prog_dlg = ProgressDialog(self, self.__action, self.__entity_data, _options, _local_cfg, _attachments_path)
        _prog_dlg.exec()


class TcmsActionPane(QGroupBox):
    """
    Central widget pane to run or export a TCMS entity.
    """

    def __init__(self, parent, gui_settings, action, entity_type, products):
        """
        Constructor.
        :param QWidget parent: the parent widget
        :param GuiSettings gui_settings: the Issai GUI preferences for the current user
        :param int action: the action to execute
        :param int entity_type: the test entity type (product, test plan or test case)
        :param list products: the TCMS products data
        """
        super().__init__(parent)
        self.__preferences = gui_settings
        self.__action = action
        self.__entity_type = entity_type
        self.__env_option = None
        self.__runs_option = None
        self.__tree_option = None
        if entity_type == ENTITY_TYPE_PLAN:
            self.__search_button_label = localized_label(L_TEST_PLAN)
            self.__search_tool_tip = localized_label(T_SEARCH_PLAN)
        elif entity_type == ENTITY_TYPE_CASE:
            self.__search_button_label = localized_label(L_TEST_CASE)
            self.__search_tool_tip = localized_label(T_SEARCH_CASE)

        _pane_layout = TcmsActionPane._create_layout()
        if action & ACTION_EXPORT != 0:
            _pane_layout.addWidget(self._output_path_box())
        _pane_layout.addWidget(self._entity_selection_box())
        _pane_layout.addWidget(self._options_box())

        if action & ACTION_EXPORT != 0:
            _do_button = QPushButton(localized_message(L_EXPORT_ENTITY, lower_case_entity_type_name(entity_type)))
            _do_button.clicked.connect(self._export_entity)
        else:
            _do_button = QPushButton(localized_message(L_RUN_ENTITY, lower_case_entity_type_name(entity_type)))
            _do_button.clicked.connect(self._run_entity)
        _do_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        _do_button.setStyleSheet(_OPEN_BUTTON_STYLE)
        _pane_layout.addWidget(_do_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(_pane_layout)
        self._initialize_combos(products)

    @staticmethod
    def _create_layout():
        """
        :returns: the pane's layout
        :rtype: QVBoxLayout
        """
        _layout = QVBoxLayout()
        _layout.setSpacing(20)
        _layout.setContentsMargins(5, 5, 5, 5)
        _layout.setStretch(0, 1)
        _layout.setStretch(1, 1)
        _layout.setStretch(2, 5)
        _layout.setStretch(3, 1)
        return _layout

    def _output_path_box(self):
        """
        :returns: the upper group box containing output path selection
        :rtype: QGroupBox
        """
        _output_selection_box = QGroupBox(localized_label(L_OUTPUT_PATH), self)
        _output_selection_box.setStyleSheet(_GROUP_BOX_STYLE)
        _output_selection_layout = QFormLayout()
        _output_selection_layout.setContentsMargins(10, 24, 24, 10)
        _output_path_button = QPushButton(localized_label(L_SELECT))
        _output_path_button.setStyleSheet(_OUTPUT_PATH_BUTTON_STYLE)
        _output_path_button.clicked.connect(self._select_output_path)
        self.__output_path_text = QLineEdit(self.__preferences.latest_output_dir())
        self.__output_path_text.setReadOnly(True)
        self.__output_path_text.setStyleSheet(_OUTPUT_PATH_TEXT_STYLE)
        _output_selection_layout.addRow(_output_path_button, self.__output_path_text)
        _output_selection_box.setLayout(_output_selection_layout)
        _output_selection_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        return _output_selection_box

    def _entity_selection_box(self):
        """
        :returns: the central group box containing entity selection
        :rtype: QGroupBox
        """
        _entity_selection_box = QGroupBox(localized_label(L_ENTITY), self)
        _entity_selection_box.setStyleSheet(_GROUP_BOX_STYLE)
        if self.__entity_type == ENTITY_TYPE_PRODUCT:
            _entity_selection_box.setLayout(self._product_selection_layout())
        else:
            _entity_selection_box.setLayout(self._test_entity_selection_layout())
        return _entity_selection_box

    def _product_selection_layout(self):
        """
        :returns: layout including widgets for product selection
        :rtype: QFormLayout
        """
        _layout = QFormLayout()
        _layout.setSpacing(20)
        _product_combo_caption, self.__product_combo = _create_combo(self, self._product_selected, L_PRODUCT_COMBO)
        _layout.addRow(_product_combo_caption, self.__product_combo)
        _layout.setAlignment(self.__product_combo, Qt.AlignmentFlag.AlignLeft)
        _layout.setContentsMargins(10, 24, 24, 10)
        return _layout

    def _test_entity_selection_layout(self):
        """
        :returns: layout including widgets for test plan or test case selection
        :rtype: QVBoxLayout
        """
        _layout = QVBoxLayout()

        # upper part with product and optional version selection combos
        _upper_layout = QFormLayout()
        _upper_layout.setSpacing(20)
        _upper_layout.setContentsMargins(10, 24, 24, 10)

        _product_combo_caption, self.__product_combo = _create_combo(self, self._product_selected, L_PRODUCT_COMBO)
        _upper_layout.addRow(_product_combo_caption, self.__product_combo)
        _upper_layout.setAlignment(self.__product_combo, Qt.AlignmentFlag.AlignLeft)
        _version_combo_caption, self.__version_combo = _create_combo(self, self._version_selected, L_VERSION_COMBO)
        _upper_layout.addRow(_version_combo_caption, self.__version_combo)
        _upper_layout.setAlignment(self.__version_combo, Qt.AlignmentFlag.AlignLeft)
        if self.__action == ACTION_RUN_TCMS_PLAN:
            _build_combo_caption, self.__build_combo = _create_combo(self, None, L_BUILD_COMBO)
            _upper_layout.addRow(_build_combo_caption, self.__build_combo)
            _upper_layout.setAlignment(self.__build_combo, Qt.AlignmentFlag.AlignLeft)
        _layout.addLayout(_upper_layout)

        # lower part with test entity selection and result list
        _lower_layout = QGridLayout()
        _search_button = QPushButton(QIcon(f'{ISSAI_ASSETS_DIR}/find-lens.png'), self.__search_button_label)
        _search_button.setStyleSheet(_SELECT_BUTTON_STYLE)
        _search_button.setToolTip(self.__search_tool_tip)
        _search_button.clicked.connect(self._search_button_clicked)
        _lower_layout.addWidget(_search_button, 0, 0)
        self.__search_text = QLineEdit()
        self.__search_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__search_text.setStyleSheet(_INPUT_FIELD_STYLE)
        self.__search_text.setToolTip(self.__search_tool_tip)
        self.__search_text.returnPressed.connect(self._search_button_clicked)
        _lower_layout.addWidget(self.__search_text, 0, 1)
        _sep2 = QFrame(self)
        _sep2.setFrameShape(QFrame.Shape.VLine)
        _lower_layout.addWidget(_sep2, 0, 2)
        _recent_button = QPushButton(localized_label(L_RECENT))
        _recent_button.setStyleSheet(_SELECT_BUTTON_STYLE)
        _recent_button.setToolTip(localized_label(T_SHOW_RECENT))
        _recent_button.clicked.connect(self._recent_button_clicked)
        _lower_layout.addWidget(_recent_button, 0, 3)
        self.__entities = QListWidget()
        self.__entities.setStyleSheet(_ENTITY_LIST_STYLE)
        self.__entities.clicked.connect(self._entity_selected)
        _lower_layout.addWidget(self.__entities, 1, 0, 1, 4)

        _layout.addLayout(_lower_layout)
        return _layout

    def _options_box(self):
        """
        :returns: the lower group box containing option settings
        :rtype: QGroupBox
        """
        _options_box = QGroupBox(localized_label(L_OPTIONS), self)
        _options_box.setStyleSheet(_GROUP_BOX_STYLE)
        _options_box_layout = QFormLayout()
        _options_box_layout.setContentsMargins(10, 24, 24, 10)
        _options_box_layout.setSpacing(20)
        _options_box_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        _options_box.setLayout(_options_box_layout)
        if self.__action == ACTION_RUN_TCMS_PLAN:
            self.__store_result_option = _create_option(_options_box_layout, L_STORE_RESULT, T_OPT_STORE_RESULT, True)
            self.__tree_option = _create_option(_options_box_layout, L_RUN_DESCENDANT_PLANS,
                                                T_OPT_RUN_DESCENDANT_PLANS, True)
            self.__dry_run_option = _create_option(_options_box_layout, L_DRY_RUN, T_OPT_DRY_RUN, False)
            _env_combo_caption, self.__env_combo = _create_combo(self, None, L_ENV_COMBO)
            _options_box_layout.addRow(_env_combo_caption, self.__env_combo)
            _options_box_layout.setAlignment(self.__env_combo, Qt.AlignmentFlag.AlignLeft)
            self.__env_combo.addItem(localized_label(L_NO_ENVIRONMENT), None)
            for _env in find_tcms_objects(TCMS_CLASS_ID_ENVIRONMENT, {}):
                self.__env_combo.addItem(_env[ATTR_NAME], _env)
            self.__env_combo.setCurrentIndex(0)
            return _options_box
        if self.__entity_type == ENTITY_TYPE_PRODUCT:
            _version_combo_caption, self.__version_combo = _create_combo(self, self._version_selected, L_VERSION_COMBO)
            _options_box_layout.addRow(_version_combo_caption, self.__version_combo)
            _options_box_layout.setAlignment(self.__version_combo, Qt.AlignmentFlag.AlignLeft)
        _build_combo_caption, self.__build_combo = _create_combo(self, None, L_BUILD_COMBO)
        _options_box_layout.addRow(_build_combo_caption, self.__build_combo)
        _options_box_layout.setAlignment(self.__build_combo, Qt.AlignmentFlag.AlignLeft)
        if self.__entity_type == ENTITY_TYPE_PLAN:
            self.__tree_option = _create_option(_options_box_layout, L_INCLUDE_PLAN_TREE, T_OPT_EXP_PLAN_TREE, True)
            self.__runs_option = _create_option(_options_box_layout, L_INCLUDE_RUNS, T_OPT_EXP_RUNS, True)
        elif self.__entity_type == ENTITY_TYPE_CASE:
            self.__runs_option = _create_option(_options_box_layout, L_INCLUDE_EXECUTIONS, T_OPT_EXP_EXECUTIONS, True)
        if self.__action == ACTION_EXPORT_PLAN or self.__action == ACTION_EXPORT_PRODUCT:
            self.__env_option = _create_option(_options_box_layout, L_INCLUDE_ENVIRONMENTS, T_OPT_EXP_EXECUTIONS, False)
        self.__history_option = _create_option(_options_box_layout, L_INCLUDE_HISTORY, T_OPT_STORE_RESULT, False)
        self.__attachments_option = _create_option(_options_box_layout, L_INCLUDE_ATTACHMENTS,
                                                   T_OPT_EXP_ATTACHMENTS, False)
        return _options_box

    def _initialize_combos(self, products):
        """
        Initializes product combo box, and version resp. build combo box, if applicable.
        :param list products: the available TCMS products
        """
        for _p in sorted(products, key=lambda _k: _k[ATTR_NAME]):
            self.__product_combo.addItem(_p[ATTR_NAME], _p)
        if len(products) == 1:
            self.__product_combo.setCurrentIndex(0)
            if self.__entity_type == ENTITY_TYPE_PRODUCT:
                self.__selected_entity = products[0]
            self._fill_version_combo(products[0])
        else:
            self.__product_combo.setCurrentIndex(-1)

    def _fill_version_combo(self, product):
        """
        Initializes version combo box for a product, and build combo box, if applicable.
        :param dict product: the selected product
        """
        if product is None:
            return
        _versions = sorted(read_tcms_versions_for_product(product), key=lambda _k: _k[ATTR_VALUE])
        self.__version_combo.clear()
        self.__build_combo.clear()
        for _v in _versions:
            self.__version_combo.addItem(_v[ATTR_VALUE], _v)
        if len(_versions) == 1:
            self.__version_combo.setCurrentIndex(0)
            self._fill_build_combo(_versions[0])
        else:
            self.__version_combo.setCurrentIndex(-1)

    def _fill_build_combo(self, version):
        """
        Initializes build combo box for a product version.
        :param dict version: the selected version
        """
        _active_only = self.__action == ACTION_RUN_TCMS_PLAN
        _builds = sorted(read_tcms_builds_for_version([version], _active_only), key=lambda _k: _k[ATTR_NAME])
        self.__build_combo.clear()
        for _b in _builds:
            self.__build_combo.addItem(_b[ATTR_NAME], _b)
        self.__build_combo.setCurrentIndex(0 if len(_builds) == 1 else -1)

    def _product_selected(self, _index):
        """
        Called, when a product has been selected from the corresponding combo box.
        :param int _index: the selected index in the product selection combo
        """
        _product = self.__product_combo.currentData()
        if self.__entity_type == ENTITY_TYPE_PRODUCT:
            self.__selected_entity = _product
        self._fill_version_combo(_product)

    def _version_selected(self, index):
        """
        Called when a version has been selected.
        :param int index: the selected index in the version selection combo
        """
        if index >= 0:
            _version = self.__version_combo.currentData()
            self._fill_build_combo(self.__version_combo.currentData())

    def _entity_selected(self, item):
        """
        Called when the user clicks on an item in the result list.
        :param QListWidgetItem item: the descriptive text for the item ('ID - name')
        """
        _id = int(item.data().split(' ')[0])
        self.__selected_entity = read_test_entity_with_id(self.__entity_type, _id)

    def _search_entity_by_id(self, tcms_id):
        """
        Search an entity by its TCMS ID and fill result table.
        :param int tcms_id: the TCMS entity ID
        :returns: True, if an entity with specified ID exists
        :rtype: bool
        """
        # noinspection PyBroadException
        try:
            self.__selected_entity = read_test_entity_with_id(self.__entity_type, tcms_id)
            _class_id = TCMS_CLASS_ID_TEST_CASE if self.__entity_type == ENTITY_TYPE_CASE else TCMS_CLASS_ID_TEST_PLAN
            _entity_product = find_product_for_tcms_object(_class_id, self.__selected_entity)
            self.__product_combo.setCurrentText(_entity_product[ATTR_NAME])
            self._fill_version_combo(self.__product_combo.currentData())
            _entity_info = '%d - %s' % (self.__selected_entity[ATTR_ID], self.__selected_entity[ATTR_NAME])
            self.__entities.clear()
            self.__entities.addItem(_entity_info)
            self.__entities.setCurrentRow(0)
            return True
        except Exception as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            return False

    def _search_button_clicked(self):
        """
        Called when the user clicks the search button to find an entity by its ID or name.
        """
        _search_text = self.__search_text.text().strip()
        if _search_text.isdigit():
            # search by ID first
            if self._search_entity_by_id(int(_search_text)):
                return
        # search by name, then product and version are required
        _product = self.__product_combo.currentData()
        _version = self.__version_combo.currentData()
        if _product is None and _version is None:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_GUI_NEITHER_PRODUCT_NOR_VERSION_SELECTED),
                                 QMessageBox.StandardButton.Ok)
            return
        if _product is None:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_GUI_NO_PRODUCT_SELECTED), QMessageBox.StandardButton.Ok)
            return
        if _version is None:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_GUI_NO_VERSION_SELECTED), QMessageBox.StandardButton.Ok)
            return
        _filter = {ATTR_PRODUCT_VERSION: _version[ATTR_ID]}
        try:
            _sorted_entities = []
            if self.__entity_type == ENTITY_TYPE_PLAN:
                _tcms_entities = find_matching_plans(_search_text, _product[ATTR_ID], _version[ATTR_ID])
                [_sorted_entities.append((_e[ATTR_NAME], _e[ATTR_ID])) for _e in _tcms_entities]
            else:
                _tcms_entities = find_matching_cases(_search_text, _product[ATTR_ID])
                [_sorted_entities.append((_e[ATTR_SUMMARY], _e[ATTR_ID])) for _e in _tcms_entities]
            _sorted_entities.sort()
            self.__entities.clear()
            for _name, _id in _sorted_entities:
                _info = '%d - %s' % (_id, _name)
                self.__entities.addItem(_info)
        except Exception as e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(e), QMessageBox.StandardButton.Ok)

    def _recent_button_clicked(self):
        """
        Called when the user clicks the recent button.
        Shows list of recently used entities and loads selected one from TCMS.
        """
        _lru_entities = self.__preferences.lru_entities(self.__entity_type)
        if _lru_entities is None or len(_lru_entities) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_LRU_ENTITIES), QMessageBox.StandardButton.Ok)
            return
        _lru_dlg = RecentEntityDialog(self, _lru_entities)
        if _lru_dlg.exec():
            _lru_entity = _lru_dlg.selected_entity()
            if _lru_entity is not None:
                try:
                    _id = int(_lru_entity.split(' ')[0])
                    if self.__entity_type == ENTITY_TYPE_PLAN:
                        self.__selected_entity = find_tcms_object(TCMS_CLASS_ID_TEST_PLAN, {ATTR_ID: _id})
                        _entity_info = '%d - %s' % (self.__selected_entity[ATTR_ID], self.__selected_entity[ATTR_NAME])
                    else:
                        self.__selected_entity = find_tcms_object(TCMS_CLASS_ID_TEST_CASE, {ATTR_ID: _id})
                        _entity_info = '%d - %s' % (self.__selected_entity[ATTR_ID],
                                                    self.__selected_entity[ATTR_SUMMARY])
                    _class_id = TCMS_CLASS_ID_TEST_CASE if self.__entity_type == ENTITY_TYPE_CASE\
                        else TCMS_CLASS_ID_TEST_PLAN
                    _entity_product = find_product_for_tcms_object(_class_id, self.__selected_entity)
                    self.__product_combo.setCurrentText(_entity_product[ATTR_NAME])
                    self._fill_version_combo(self.__product_combo.currentData())
                    self.__entities.clear()
                    self.__entities.addItem(_entity_info)
                    self.__entities.setCurrentRow(0)
                except Exception as e:
                    QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(e),
                                         QMessageBox.StandardButton.Ok)
        _lru_dlg.close()

    def _select_output_path(self):
        """
        Called by output path selection push button. Shows a file dialog to select the output directory.
        """
        _preferred_path = self.__preferences.latest_output_dir()
        _dlg = QFileDialog(self, localized_label(L_DLG_TITLE_SELECT_EXPORT_OUTPUT_PATH), _preferred_path)
        _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
        _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
        _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        _dlg.setFileMode(QFileDialog.FileMode.Directory)
        if _dlg.exec():
            _selected_path = _dlg.selectedFiles()[0]
            self.__output_path_text.setText(_selected_path)
            self.__preferences.set_latest_output_dir(_selected_path)
        _dlg.close()

    def _export_entity(self):
        """
        Called by export button. Starts the export and shows results in a progress dialog.
        """
        _entity = self._selected_entity()
        if _entity is None:
            return
        _output_path = self._prepare_output_path()
        if _output_path is None:
            return
        _env_option = False if self.__env_option is None else self.__env_option.isChecked()
        _tree_option = False if self.__tree_option is None else self.__tree_option.isChecked()
        _runs_option = True if self.__entity_type == ENTITY_TYPE_PRODUCT else self.__runs_option.isChecked()
        _options = {OPTION_VERSION: self.__version_combo.currentData(), OPTION_BUILD: self.__build_combo.currentData(),
                    OPTION_PLAN_TREE: _tree_option, OPTION_INCLUDE_RUNS: _runs_option,
                    OPTION_INCLUDE_ENVIRONMENTS: _env_option,
                    OPTION_INCLUDE_ATTACHMENTS: self.__attachments_option.isChecked(),
                    OPTION_INCLUDE_HISTORY: self.__history_option.isChecked()}
        _prog_dlg = ProgressDialog(self, self.__action, _entity, _options, {}, _output_path)
        _prog_dlg.exec()

    def _run_entity(self):
        """
        Called by run button. Starts the run and shows results in a progress dialog.
        """
        _entity = self._selected_entity()
        if _entity is None:
            return
        _version = self.__version_combo.currentData()
        if _version is None:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_VERSION_SELECTED), QMessageBox.StandardButton.Ok)
            return
        _build = self.__build_combo.currentData()
        if _build is None:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_BUILD_SELECTED), QMessageBox.StandardButton.Ok)
            return
        try:
            _config_path = config_root_path()
            _local_cfg = product_config(_config_path, self.__product_combo.currentText(), master_config(_config_path))
        except IssaiException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            return
        self.__preferences.entity_used(TCMS_CLASS_ID_TEST_PLAN, _entity[ATTR_ID], _entity[ATTR_NAME])
        _tree_option = self.__tree_option.isChecked() if self.__entity_type == ENTITY_TYPE_PLAN else False
        _options = {OPTION_VERSION: _version, OPTION_BUILD: _build, OPTION_ENVIRONMENT: self.__env_combo.currentData(),
                    OPTION_PLAN_TREE: self.__tree_option.isChecked(),
                    OPTION_STORE_RESULT: self.__store_result_option.isChecked(),
                    OPTION_DRY_RUN: self.__dry_run_option.isChecked()}
        _prog_dlg = ProgressDialog(self, self.__action, _entity, _options, _local_cfg, '')
        _prog_dlg.exec()

    def _prepare_output_path(self):
        """
        Checks and eventually cleans output path for an export.
        :returns: output path in case of success; otherwise None
        :rtype: str
        """
        _output_path = self.__output_path_text.text()
        if not os.path.isdir(_output_path):
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_GUI_OUTPUT_PATH_INVALID, _output_path),
                                 QMessageBox.StandardButton.Ok)
            return None
        _entity_type_name = lower_case_entity_type_name(self.__entity_type)
        _entity_id = self.__selected_entity[ATTR_ID]
        _output_file_path = os.path.join(_output_path, f'{_entity_type_name}_{_entity_id}.toml')
        _output_file_exists = os.path.exists(_output_file_path)
        _attachments_path = os.path.join(_output_path, ATTACHMENTS_ROOT_DIR).encode('utf-8')
        _clear_attachments_required = os.path.isdir(_attachments_path) and any(os.scandir(_attachments_path))
        _confirmation_msg = None
        if _output_file_exists:
            if _clear_attachments_required:
                _confirmation_msg = localized_message(I_CLEAR_EXPORT_OUTPUT, _output_file_path, _attachments_path)
            else:
                _confirmation_msg = localized_message(I_CLEAR_EXPORT_FILE, _output_file_path)
        elif _clear_attachments_required:
            _confirmation_msg = localized_message(I_CLEAR_EXPORT_ATTACHMENTS, _attachments_path)
        if _confirmation_msg is not None:
            _rc = QMessageBox.question(self, localized_label(L_MBOX_TITLE_OUTPUT_EXISTS), _confirmation_msg,
                                       QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
            if _rc == QMessageBox.StandardButton.Cancel:
                return
        if _output_file_exists:
            os.remove(_output_file_path)
        if _clear_attachments_required:
            for _node in os.scandir(_attachments_path):
                if _node.is_dir() and not _node.is_symlink():
                    shutil.rmtree(_node.path)
                else:
                    os.remove(_node.path)
        return _output_path

    def _selected_entity(self):
        """
        Checks selection for an export.
        :returns: entity in case of success; otherwise None
        :rtype: dict
        """
        if self.__entity_type == ENTITY_TYPE_PRODUCT:
            _entity = self.__product_combo.currentData()
            if _entity is None:
                QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                     localized_message(E_GUI_NO_PRODUCT_SELECTED), QMessageBox.StandardButton.Ok)
                return None
            return _entity
        else:
            _selected_item = self.__entities.currentItem()
            if _selected_item is None:
                QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                     localized_message(E_GUI_NO_ENTITY_SELECTED), QMessageBox.StandardButton.Ok)
                return None
            _entity_info = _selected_item.text().split(' - ')
            return {ATTR_ID: int(_entity_info[0]), ATTR_NAME: _entity_info[1]}


def _create_combo(parent, activated_handler, caption_id):
    """
    Creates label and combo box.
    :param QWidget parent: the widget that will own the created combo box
    :param func activated_handler: the method to be called when the combo box is activated
    :returns: caption and combo box widgets
    :rtype: (str, QComboBox)
    """
    _combo_caption = QLabel(localized_label(caption_id))
    _combo_caption.setStyleSheet(_CAPTION_STYLE)
    _combo_box = QComboBox(parent)
    _combo_box.setMinimumWidth(240)
    if activated_handler is not None:
        _combo_box.activated.connect(activated_handler)
    return _combo_caption, _combo_box


def _create_option(layout, caption_id, tooltip_id, initial_state):
    """
    Creates label and check box for an option.
    :param QFormLayout layout: the layout that shall contain the option
    :param str caption_id: the label ID for the caption text
    :param str tooltip_id: the label ID for the tooltip text
    :param bool initial_state: the initial checkbox state
    :returns: the checkbox widget
    :rtype: QCheckBox
    """
    _tooltip = localized_label(tooltip_id)
    _caption = QLabel(localized_label(caption_id))
    _caption.setToolTip(_tooltip)
    _caption.setStyleSheet(_CAPTION_STYLE)
    _check_box = QCheckBox()
    _check_box.setToolTip(_tooltip)
    _check_box.setChecked(initial_state)
    layout.addRow(_caption, _check_box)
    return _check_box


_CAPTION_STYLE = 'color: black; font-weight: bold'
_ENTITY_LIST_STYLE = 'background-color: white'
_EXPORT_BANNER_STYLE = 'background-color: blue; color: white; font-weight: bold'
_GROUP_BOX_STYLE = 'QGroupBox {font: bold; border: 1px solid blue; border-radius: 6px; margin-top: 6px} ' \
                   'QGroupBox::title {color: blue; subcontrol-origin: margin; left: 7px; padding: 0 5px 0 5px;}'
_OPEN_BUTTON_STYLE = 'background-color: green; color: white; font-weight: bold'
_OUTPUT_PATH_BUTTON_STYLE = 'background-color: darkgray; color: black; font-weight: bold'
_OUTPUT_PATH_TEXT_STYLE = 'background-color: lightgray'
_SELECT_BUTTON_STYLE = 'background-color: darkgray; color: black; font-weight: bold'
_INPUT_FIELD_STYLE = 'background-color: #ffffcc'
_ID_FIELD_WIDTH = 60
