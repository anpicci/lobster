import inspect
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import types as _types

if not hasattr(inspect, 'getargspec'):
    from collections import namedtuple

    ArgSpec = namedtuple('ArgSpec', 'args varargs keywords defaults')

    def _compat_getargspec(func):
        spec = inspect.getfullargspec(func)
        return ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)

    inspect.getargspec = _compat_getargspec

try:
    SimpleNamespace = _types.SimpleNamespace
except AttributeError:  # pragma: no cover - Python 2 fallback
    class SimpleNamespace(object):
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def __repr__(self):
            return 'SimpleNamespace({0})'.format(
                ', '.join('{0}={1!r}'.format(k, v) for k, v in self.__dict__.items())
            )

ModuleType = _types.ModuleType

if 'ndcctools' not in sys.modules:
    sys.modules['ndcctools'] = ModuleType('ndcctools')
if 'ndcctools.chirp' not in sys.modules:
    sys.modules['ndcctools.chirp'] = ModuleType('ndcctools.chirp')
    sys.modules['ndcctools.chirp'].Client = object

import pytest

from lobster.se import XrootD


@pytest.fixture
def xrootd():
    return XrootD('root://server.example.com//')


@pytest.fixture
def target_path():
    return 'root://server.example.com//store/data'


def test_execute_returns_captured_stdout(monkeypatch, xrootd, target_path):
    result = SimpleNamespace(returncode=0, stdout='ok-out', stderr='ignored')

    def fake_run(args, capture_output, text):
        assert args == ['xrdfs', 'server.example.com', 'stat', '//store/data']
        assert capture_output is True
        assert text is True
        return result

    monkeypatch.setattr(subprocess, 'run', fake_run)

    output = xrootd.execute('stat', target_path)
    assert output == 'ok-out'


def test_execute_failure_includes_stderr(monkeypatch, xrootd, target_path):
    result = SimpleNamespace(returncode=1, stdout='bad-out', stderr='bad-err')

    def fake_run(*args, **kwargs):
        return result

    monkeypatch.setattr(subprocess, 'run', fake_run)

    with pytest.raises(IOError) as err:
        xrootd.execute('stat', target_path)

    assert 'bad-err' in str(err.value)


def test_execute_falls_back_to_popen(monkeypatch, xrootd, target_path):
    monkeypatch.delattr(subprocess, 'run', raising=False)

    class DummyProcess(object):
        def __init__(self, stdout, stderr, returncode):
            self._stdout = stdout
            self._stderr = stderr
            self._returncode = returncode

        def communicate(self):
            return self._stdout, self._stderr

        @property
        def returncode(self):
            return self._returncode

    def fake_popen(args, stdout, stderr, universal_newlines):
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        assert universal_newlines is True
        return DummyProcess('legacy-ok', 'legacy-err', 0)

    monkeypatch.setattr(subprocess, 'Popen', fake_popen)

    output = xrootd.execute('stat', target_path)
    assert output == 'legacy-ok'

    def failing_popen(*args, **kwargs):
        return DummyProcess('legacy-out', 'legacy-bad', 1)

    monkeypatch.setattr(subprocess, 'Popen', failing_popen)

    with pytest.raises(IOError) as err:
        xrootd.execute('stat', target_path)

    assert 'legacy-bad' in str(err.value)


@pytest.mark.skipif(sys.version_info[0] < 3, reason='Python 2 only code path tested via fallback')
def test_execute_safe_flag_suppresses_errors(monkeypatch, xrootd, target_path):
    result = SimpleNamespace(returncode=1, stdout='out', stderr='err')

    def fake_run(*args, **kwargs):
        return result

    monkeypatch.setattr(subprocess, 'run', fake_run)

    output = xrootd.execute('stat', target_path, safe=True)
    assert output == 'out'
