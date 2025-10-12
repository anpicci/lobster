import os
import sys
import traceback

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lobster import util

if not hasattr(util.inspect, 'getargspec'):
    util.inspect.getargspec = util.inspect.getfullargspec


class _FailingConfig(util.Configurable):
    _mutable = {}

    def __init__(self):
        self._trigger_failure()

    def _trigger_failure(self):
        raise ValueError('boom')


def test_constructor_exception_preserves_traceback():
    with pytest.raises(ValueError) as excinfo:
        _FailingConfig()

    tb_summary = traceback.extract_tb(excinfo.value.__traceback__)
    frame_names = [frame.name for frame in tb_summary]

    assert '_trigger_failure' in frame_names
    assert frame_names[-1] == '_trigger_failure'


def test_constructor_exception_message_uses_string_representation():
    with pytest.raises(ValueError) as excinfo:
        _FailingConfig()

    assert 'boom' in str(excinfo.value)
