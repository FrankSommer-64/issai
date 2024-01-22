import os
import re


def test_file_path(entity_type, file_name):
    """
    :param str file_name: name and path of test data file under test data root directory
    :returns: full path for specified test data file
    :rtype: str
    """
    return os.path.join(os.environ['TEST_DATA_ROOT'], 'input', _ENTITY_TYPE_NAMES[entity_type], file_name)


def test_runs_in_multi_version_dataset():
    """
    :returns: True, if a test runs against a test server using a product with multiple versions.
    :rtype: bool
    """
    return _dataset_marker(3) == 'm'


def test_runs_in_multi_build_dataset():
    """
    :returns: True, if a test runs against a test server using a product with multiple builds.
    :rtype: bool
    """
    return _dataset_marker(4) == 'm'


def _dataset_marker(index):
    _data_set = os.environ.get('TEST_DATA_SET')
    if _data_set is None:
        return ''
    _m = re.match(r'^s_(.*)-p_(.*)-v_(.)-b_(.)$', _data_set)
    if _m:
        return _m.group(index)
    return ''


_ENTITY_TYPE_NAMES = {1: 'case', 2: 'plan', 3: 'product'}
