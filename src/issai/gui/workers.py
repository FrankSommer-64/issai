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
Worker class to execute asynchronous tasks in the background.
"""

from PySide6.QtCore import QObject, QRunnable, Signal

from issai.core import *
from issai.core.exporter import export_case, export_plan, export_product
from issai.core.importer import import_file
from issai.core.issai_exception import IssaiException
from issai.core.messages import E_BACKGROUND_TASK_FAILED, E_INTERNAL_ERROR, E_INVALID_ACTION, localized_message
from issai.core.runner import run_offline_plan, run_tcms_plan
from issai.core.task import TaskMonitor, TaskResult


class WorkerSignals(QObject):
    """
    Signals that can be used with the workers.
    """
    finished = Signal()
    error = Signal(IssaiException)
    result = Signal(TaskResult)
    progress = Signal(tuple)

    def __init__(self):
        """
        Constructor
        """
        super().__init__()


class Worker(QRunnable):
    """
    Worker class to execute a task in the background.
    """
    def __init__(self, worker_fn, *args):
        """
        Constructor
        :param function worker_fn: the main worker routine
        :param args: the arguments for the main worker function
        """
        super().__init__()
        self.__fn = worker_fn
        self.__args = args
        self.__signals = WorkerSignals()
        self.__task_monitor = TaskMonitor(self)

    def abort(self):
        """
        Aborts task processing.
        """
        self.__task_monitor.request_abort()

    def connect_signals(self, progress_slot, finished_slot, result_slot, error_slot):
        """
        Connects signals to custom slots.
        :param function progress_slot: the slot to handle progress signal
        :param function finished_slot: the slot to handle finished signal
        :param function result_slot: the slot to handle result signal
        :param function error_slot: the slot to handle error signal
        """
        if progress_slot is not None:
            self.__signals.progress.connect(progress_slot)
        if finished_slot is not None:
            self.__signals.finished.connect(finished_slot)
        if result_slot is not None:
            self.__signals.result.connect(result_slot)
        if error_slot is not None:
            self.__signals.error.connect(error_slot)

    def run(self):
        """
        Main thread function.
        Executes custom function specified in the constructor and signals appropriate events.
        """
        try:
            _result = self.__fn(*self.__args, self.__task_monitor)
            self.__signals.result.emit(_result)
        except IssaiException as _e:
            self.__signals.error.emit(_e)
        except BaseException as _e:
            _ex = IssaiException(E_BACKGROUND_TASK_FAILED, str(_e))
            self.__signals.error.emit(_ex)
        self.__signals.finished.emit()

    def emit_progress(self, progress_data):
        """
        Signals a progress event to the associated slot.
        Progress events are tuples (progress percentage value, message severity, progress message), with message
        severities one of 'e' for error, 'i' for informational and 'w' for warning messages.
        :param (int,str,str) progress_data: the progress information (progress value, severity, message text)
        """
        self.__signals.progress.emit(progress_data)

    @staticmethod
    def for_action(action, entity, options, local_cfg, file_or_working_path):
        """
        Creates a worker for specified action.
        :param int action: the action to execute by the worker
        :param Entity entity: the entity data
        :param dict options: the action specific options
        :param LocalConfig local_cfg: the local runtime configuration
        :param str file_or_working_path: the output directory for exports, the input file for imports,
                                         the working directory for runs
        :returns: the worker created
        :rtype: Worker
        """
        if action == ACTION_EXPORT_PRODUCT:
            return Worker(export_product, entity[ATTR_NAME], options, file_or_working_path)
        elif action == ACTION_EXPORT_PLAN:
            return Worker(export_plan, entity, options, file_or_working_path)
        elif action == ACTION_EXPORT_CASE:
            return Worker(export_case, entity, options, file_or_working_path)
        elif action == ACTION_IMPORT:
            return Worker(import_file, entity, options, file_or_working_path)
        elif action == ACTION_RUN_TCMS_PLAN:
            return Worker(run_tcms_plan, entity, options, local_cfg)
        elif action == ACTION_RUN_OFFLINE_PLAN:
            return Worker(run_offline_plan, entity, options, local_cfg, file_or_working_path)
        _emsg = localized_message(E_INVALID_ACTION, action)
        raise IssaiException(E_INTERNAL_ERROR, _emsg)
