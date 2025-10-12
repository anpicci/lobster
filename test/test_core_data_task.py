import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from string import Template

try:
    from unittest.mock import Mock
except ImportError:  # pragma: no cover
    from mock import Mock

sys.modules['ROOT'] = Mock()
sys.modules['WMCore'] = Mock()
sys.modules['WMCore.DataStructs'] = Mock()
sys.modules['WMCore.DataStructs.LumiList'] = Mock(LumiList=Mock())
sys.modules['WMCore.FwkJobReport'] = Mock()
sys.modules['WMCore.FwkJobReport.Report'] = Mock(Report=Mock())

import pytest


def _load_task_module():
    module_path = os.path.join(os.path.dirname(__file__), os.pardir, 'lobster', 'core', 'data', 'task.py')
    module_path = os.path.normpath(module_path)
    spec = importlib.util.spec_from_file_location('lobster.core.data.task', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


task = _load_task_module()


class TestCommands(object):

    def test_expansion(self):
        cmd = ["foo", "@inputfiles", "--some-flag"]
        args = ["-a"]
        infiles = ["bar", "baz"]
        outfiles = []
        result = ["foo", "bar", "baz", "--some-flag"]
        assert task.expand_command(cmd, args, infiles, outfiles) == result


class TestDiscovery(object):

    def test_xrootd_server(self):
        fn = os.path.join(os.path.dirname(__file__), 'data', 'siteconf', 'PhEDEx', 'storage.xml')
        assert task.find_xrootd_server(fn) == 'root://ndcms.crc.nd.edu/'


REPRESENTATIVE_RELEASE = 'CMSSW_10_6_4'


def _write_fragment_script():
    fragment = task.fragment.format(events=1)
    template = Template(
        """
import os
import sys
import types

os.environ['CMSSW_VERSION'] = '$release'

fwcore = types.ModuleType('FWCore')
sys.modules['FWCore'] = fwcore
sys.modules['FWCore.ParameterSet'] = types.ModuleType('FWCore.ParameterSet')
config = types.ModuleType('FWCore.ParameterSet.Config')


class _Untracked(object):

    def bool(self, value):
        return value

    def PSet(self, **kwargs):
        return kwargs

    def int32(self, value):
        return value

    def uint32(self, value):
        return value


def _service(*args, **kwargs):
    return (args, kwargs)


def _vstring(*args):
    return list(args)


config.Service = _service
config.untracked = _Untracked()
config.vstring = _vstring

sys.modules['FWCore.ParameterSet.Config'] = config


class DummyProcess(object):

    def __init__(self):
        self.producers = {}
        self.options = type('Options', (), {})()

    def add_(self, service):
        self.added = service


process = DummyProcess()

$fragment
"""
    )

    script = template.substitute(fragment=fragment, release=REPRESENTATIVE_RELEASE)
    handle = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False)
    try:
        handle.write(script)
        handle.flush()
    finally:
        handle.close()

    return handle.name


@pytest.mark.parametrize('python_executable', ['python2', 'python3'])
def test_fragment_executes_under_supported_pythons(python_executable):
    interpreter = shutil.which(python_executable)
    if interpreter is None:
        pytest.skip('{} not available'.format(python_executable))

    script_path = _write_fragment_script()
    try:
        subprocess.check_call([interpreter, script_path])
    finally:
        os.unlink(script_path)
