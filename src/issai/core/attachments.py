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
Functions to handle attachments of TCMS objects.
"""

from base64 import b64encode
import re

import requests
import urllib3

from issai.core import *
from issai.core.issai_exception import IssaiException
from issai.core.messages import *
from issai.core.tcms import upload_entity_attachment


def attachment_file_path(root_path, file_name, tcms_class_id, tcms_entity_id):
    """
    Returns full path for an attachment file of specified TCMS class and ID.
    :param str root_path: the root path
    :param str file_name: the pure attachment file name
    :param int tcms_class_id: the TCMS entity class ID
    :param int tcms_entity_id: the TCMS entity ID
    :return: full path for attachment file
    """
    _subdir = _attachment_dir_for_class(tcms_class_id)
    return os.path.join(root_path, ATTACHMENTS_ROOT_DIR, _subdir, str(tcms_entity_id), file_name)


def download_attachment(file_name_patterns, root_path, url, tcms_class_id, tcms_entity_id, task_monitor):
    """
    Downloads a file attached to a test entity from TCMS.
    :param list[str] file_name_patterns: regular expression patterns attachment files must match to be downloaded
    :param str root_path: the root path for attachments
    :param str url: the attachment URL in TCMS
    :param int tcms_class_id: the TCMS entity class ID
    :param int tcms_entity_id: the TCMS entity ID
    :param TaskMonitor task_monitor: the progress handler
    :raises IssaiException: if download failed
    """
    try:
        _url_parts = urllib3.util.parse_url(url)
        _file_name = os.path.basename(_url_parts.path)
        if len(file_name_patterns) > 0:
            for _pattern in file_name_patterns:
                if re.match(_pattern, _file_name):
                    break
            return
        _full_file_path = attachment_file_path(root_path, _file_name, tcms_class_id, tcms_entity_id)
        task_monitor.log(I_DOWNLOAD_ATTACHMENT, _full_file_path)
        if task_monitor.is_dry_run():
            return
        os.makedirs(os.path.dirname(_full_file_path), exist_ok=True)
        r = requests.get(url)
        with open(_full_file_path, 'w') as f:
            f.write(r.text)
    except Exception as _e:
        raise IssaiException(E_DOWNLOAD_ATTACHMENT_FAILED, url, _e)


def download_attachments(entity, output_path, task_monitor, file_name_patterns=()):
    """
    Downloads all attachments of specified entity. Files are stored under subdirectory
     "attachments/<entity-type>/<entity-id>".
    Signals a progress event, if a receiver is given.
    :param Entity entity: the entity
    :param str output_path: the output path
    :param TaskMonitor task_monitor: the progress handler
    :param list[str] file_name_patterns: regular expression patterns attachment files must match to be downloaded
    :raises IssaiException: if download operation fails
    """
    task_monitor.log(I_DOWNLOAD_ATTACHMENTS, entity.entity_name())
    task_monitor.operations_processed(1)
    _attachments_path = os.path.join(output_path, ATTACHMENTS_ROOT_DIR)
    for _class_id, _objects in entity.attachments().items():
        for _object_id, _urls in _objects.items():
            for _url in _urls:
                if not task_monitor.is_dry_run():
                    download_attachment(file_name_patterns, output_path, _url, _class_id, _object_id, task_monitor)


def upload_attachment(root_path, file_name, file_entity_id, tcms_class_id, tcms_entity_id):
    """
    Uploads an attachment to TCMS.
    :param str root_path: the root path
    :param str file_name: the pure attachment file name
    :param int file_entity_id: the entity ID from the attachment's URL
    :param int tcms_class_id: the TCMS entity class ID
    :param int tcms_entity_id: the TCMS entity ID
    :rtype: None
    :raises IssaiException: if attachment file doesn't exist or an error during TCMS access occurs
    """
    _file_path = attachment_file_path(root_path, file_name, tcms_class_id, file_entity_id)
    try:
        with open(_file_path, 'rb') as _f:
            _contents = _f.read()
    except Exception as _e:
        raise IssaiException(E_READ_ATTACHMENT_FAILED, _file_path, str(_e))
    _file_contents = b64encode(_contents).decode('utf-8')
    upload_entity_attachment(tcms_class_id, tcms_entity_id, file_name, _file_contents)


def upload_attachment_file(file_path, tcms_file_name, tcms_class_id, tcms_entity_id):
    """
    Uploads an attachment file to TCMS.
    :param str file_path: the file name including path
    :param str tcms_file_name: the file name to use in TCMS
    :param int tcms_class_id: the TCMS entity class ID
    :param int tcms_entity_id: the TCMS entity ID
    :rtype: None
    :raises IssaiException: if attachment file doesn't exist or an error during TCMS access occurs
    """
    try:
        with open(file_path, 'rb') as _f:
            _contents = _f.read()
    except Exception as _e:
        raise IssaiException(E_READ_ATTACHMENT_FAILED, file_path, str(_e))
    _contents = _contents.replace(b'AssertionError', b'AssertionFailed')
    _file_contents = b64encode(_contents).decode('utf-8')
    upload_entity_attachment(tcms_class_id, tcms_entity_id, tcms_file_name, _file_contents)


def list_attachment_files(root_path, tcms_class_id, tcms_entity_id):
    """
    Lists all files in subdirectory of specified test entity.
    :param str root_path: the root path
    :param int tcms_class_id: the TCMS entity class ID
    :param int tcms_entity_id: the TCMS entity ID
    :returns: names of all files found including path
    :rtype: list
    """
    _class_subdir = _attachment_dir_for_class(tcms_class_id)
    _entity_subdir = os.path.join(root_path, ATTACHMENTS_ROOT_DIR, _class_subdir, str(tcms_entity_id))
    return [os.path.join(_entity_subdir, _f) for _f in os.listdir(_entity_subdir)
            if os.path.isfile(os.path.join(_entity_subdir, _f))]


def url_file_name(url):
    """
    :param str url: the URL
    :returns: the pure file name of given URL
    :rtype: str
    """
    _url_parts = urllib3.util.parse_url(url)
    return os.path.basename(_url_parts.path)


def url_object_id(url):
    """
    :param str url: the URL
    :returns: object ID part of URL
    :rtype: int
    """
    _url_parts = urllib3.util.parse_url(url)
    return int(os.path.basename(os.path.dirname(_url_parts.path)))


def _attachment_dir_for_class(tcms_class_id):
    """
    Returns subdirectory name for attachment files of specified TCMS class.
    :param int tcms_class_id: the TCMS entity class ID
    :returns: class specific directory name, default 'entity', if class is not treated specially by issai
    :rtype: str
    """
    if tcms_class_id == TCMS_CLASS_ID_TEST_CASE:
        return ATTACHMENTS_CASE_DIR
    elif tcms_class_id == TCMS_CLASS_ID_TEST_EXECUTION:
        return ATTACHMENTS_EXECUTION_DIR
    elif tcms_class_id == TCMS_CLASS_ID_TEST_PLAN:
        return ATTACHMENTS_PLAN_DIR
    elif tcms_class_id == TCMS_CLASS_ID_TEST_RUN:
        return ATTACHMENTS_RUN_DIR
    else:
        return ATTACHMENTS_ENTITY_DIR
