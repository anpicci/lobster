import importlib.util
import inspect
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

if 'imp' not in sys.modules:
    imp_stub = types.ModuleType('imp')

    def load_source(name, pathname, file=None):
        spec = importlib.util.spec_from_file_location(name, pathname)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    imp_stub.load_source = load_source
    sys.modules['imp'] = imp_stub

if not hasattr(inspect, 'getargspec'):
    def _getargspec(func):
        signature = inspect.signature(func)
        args = [
            parameter.name for parameter in signature.parameters.values()
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        varargs = next(
            (
                parameter.name for parameter in signature.parameters.values()
                if parameter.kind == inspect.Parameter.VAR_POSITIONAL
            ),
            None,
        )
        keywords = next(
            (
                parameter.name for parameter in signature.parameters.values()
                if parameter.kind == inspect.Parameter.VAR_KEYWORD
            ),
            None,
        )
        defaults = [
            parameter.default
            for parameter in signature.parameters.values()
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
            and parameter.default is not inspect._empty
        ]
        return types.SimpleNamespace(
            args=args,
            varargs=varargs,
            keywords=keywords,
            defaults=tuple(defaults) if defaults else None,
        )

    inspect.getargspec = _getargspec

if 'ndcctools' not in sys.modules:
    ndcctools_stub = types.ModuleType('ndcctools')
    chirp_stub = types.ModuleType('ndcctools.chirp')
    ndcctools_stub.chirp = chirp_stub
    sys.modules['ndcctools'] = ndcctools_stub
    sys.modules['ndcctools.chirp'] = chirp_stub

if 'work_queue' not in sys.modules:
    work_queue_stub = types.ModuleType('work_queue')
    work_queue_stub.WORK_QUEUE_ALLOCATION_MODE_FIXED = 0
    work_queue_stub.WORK_QUEUE_ALLOCATION_MODE_MAX = 1
    work_queue_stub.WORK_QUEUE_ALLOCATION_MODE_MIN_WASTE = 2
    work_queue_stub.WORK_QUEUE_ALLOCATION_MODE_MAX_THROUGHPUT = 3
    sys.modules['work_queue'] = work_queue_stub

if 'retrying' not in sys.modules:
    retrying_stub = types.ModuleType('retrying')

    def _retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    retrying_stub.retry = _retry
    sys.modules['retrying'] = retrying_stub

if 'WMCore' not in sys.modules:
    wmcore_stub = types.ModuleType('WMCore')
    data_structs_stub = types.ModuleType('WMCore.DataStructs')
    lumi_list_stub = types.ModuleType('WMCore.DataStructs.LumiList')

    class _LumiList(object):
        def __init__(self, *args, **kwargs):
            pass

    lumi_list_stub.LumiList = _LumiList
    data_structs_stub.LumiList = lumi_list_stub
    wmcore_stub.DataStructs = data_structs_stub

    sys.modules['WMCore'] = wmcore_stub
    sys.modules['WMCore.DataStructs'] = data_structs_stub
    sys.modules['WMCore.DataStructs.LumiList'] = lumi_list_stub

from lobster.core.dataset import Dataset
from lobster import fs, se, util


os.environ.setdefault('USER', 'lobster')


class TestDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.expandvars(
            os.environ.get('LOBSTER_STORAGE', '/cms/cephfs/data/store/user/') +
            os.environ.get('LOBSTER_USER', os.environ['USER']) + '/')
        if not os.path.exists(path):
            os.makedirs(path)
        cls.workdir = tempfile.mkdtemp(prefix=path)
        os.chmod(cls.workdir, 0o777)
        os.makedirs(os.path.join(cls.workdir, 'eggs'))
        for i in range(10):
            with open(os.path.join(cls.workdir, 'eggs', str(i) + '.txt'), 'w') as f:
                f.write('stir-fry')
        os.makedirs(os.path.join(cls.workdir, 'ham'))
        for i in range(5):
            with open(os.path.join(cls.workdir, 'ham', str(i) + '.txt'), 'w') as f:
                f.write('bacon')
        os.makedirs(os.path.join(cls.workdir, 'spam'))
        os.makedirs(os.path.join(cls.workdir, 'spam', 'log'))
        for i in range(5):
            with open(os.path.join(cls.workdir, 'spam', str(i) + '.txt'), 'w') as f:
                f.write('mail')
        for i in range(2):
            with open(os.path.join(cls.workdir, 'spam', str(i) + '.trash'), 'w') as f:
                f.write('mail')
        for i in range(3):
            with open(os.path.join(cls.workdir, 'spam', 'log', str(i) + '.log'), 'w') as f:
                f.write('thing')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.workdir)

    def test_basics(self):
        with util.PartiallyMutable.unlock():
            s = se.StorageConfiguration(
                output=[], input=['file://' + self.workdir])
            s.activate()

            with fs.alternative():
                info = Dataset(files='eggs').get_info()
                assert len(info.files) == 10

                info = Dataset(files=['eggs', 'ham']).get_info()
                assert len(info.files) == 15

                info = Dataset(files='eggs/1.txt').get_info()
                assert len(info.files) == 1

    def test_flatten(self):
        with util.PartiallyMutable.unlock():
            s = se.StorageConfiguration(
                output=[], input=['file://' + self.workdir])
            s.activate()

            with fs.alternative():
                info = Dataset(files=['spam']).get_info()
                assert len(info.files) == 8

                info = Dataset(files=['spam'], patterns=['*.txt']).get_info()
                assert len(info.files) == 5

                info = Dataset(files=['spam'], patterns=['[12].txt']).get_info()
                assert len(info.files) == 2

    def test_flatten_outage_fallback(self):
        with util.PartiallyMutable.unlock():
            s = se.StorageConfiguration(
                output=[], input=['file://' + self.workdir])
            s.activate()

            with fs.alternative():
                target = os.path.join('spam', '0.txt')

                with mock.patch.object(fs, 'isdir', side_effect=IOError('outage')), \
                     mock.patch.object(fs, 'isfile', side_effect=IOError('outage')):
                    with self.assertLogs('lobster.core.dataset', level='WARNING') as logs:
                        dataset = Dataset(files=[target])
                        assert dataset.validate()
                        info = dataset.get_info()

                    assert len(logs.output) >= 1
                    assert any('Falling back to trusting dataset entry' in message for message in logs.output)
                    assert info.total_units == 1

    def test_flatten_missing_file_rejected(self):
        with util.PartiallyMutable.unlock():
            s = se.StorageConfiguration(
                output=[], input=['file://' + self.workdir])
            s.activate()

            with fs.alternative():
                assert not fs.exists('this_file_does_not_exist.txt')
                dataset = Dataset(files=['this_file_does_not_exist.txt'])
                assert not dataset.validate()
