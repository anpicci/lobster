import importlib
import os
import pipes
import shlex
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


def test_shell_quote_matches_shlex_quote():
    value = "foo bar 'baz'"
    expected = shlex.quote(value)

    assert util.shell_quote(value) == expected


def test_shell_quote_falls_back_to_pipes_quote():
    value = "foo bar"
    original = getattr(shlex, 'quote', None)

    try:
        if original is not None:
            del shlex.quote

        importlib.reload(util)
        assert util.shell_quote(value) == pipes.quote(value)
    finally:
        if original is not None:
            shlex.quote = original
        importlib.reload(util)


def test_verify_string_decodes_bytes():
    assert util.verify_string(b'worker-node') == 'worker-node'


def test_verify_string_accepts_ascii_str():
    assert util.verify_string('worker-node') == 'worker-node'


def test_verify_string_rejects_non_ascii():
    assert util.verify_string('node-\u2603') == ''
    assert util.verify_string('node-\u00e9') == ''
    assert util.verify_string(b'node-\xff') == ''


def test_ldd_parses_ssl_libraries(monkeypatch):
    fake_output = (
        b"libssl.so.1.1 => /lib/libssl.so.1.1 (0x00007f)\n"
        b"libcrypto.so.1.1 => /lib/libcrypto.so.1.1 (0x00007f)\n"
        b"linux-vdso.so.1 =>  (0x00007f)\n"
    )

    class DummyPopen(object):
        def __init__(self, cmd, env=None, stdout=None):
            self.cmd = cmd
            self.env = env
            self.stdout = stdout

        def communicate(self):
            return fake_output, b''

    monkeypatch.setattr(util, 'which', lambda name: '/usr/bin/{}'.format(name))
    monkeypatch.setattr(util.subprocess, 'Popen', DummyPopen)

    libs = util.ldd('python')

    assert libs == ['/lib/libssl.so.1.1', '/lib/libcrypto.so.1.1']
    assert all(isinstance(lib, type('')) for lib in libs)
