import collections
import importlib.util
import os
import shutil
import sys
import tempfile
import types
import unittest

from unittest import mock


def _load_dataset_module():
    module_path = os.path.join(os.path.dirname(__file__), os.pardir, 'lobster', 'cmssw', 'dataset.py')
    module_path = os.path.normpath(module_path)

    stubs = {}

    def _stub(name, module):
        stubs[name] = sys.modules.get(name)
        sys.modules[name] = module

    retrying = types.ModuleType('retrying')

    def _retry(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    retrying.retry = _retry
    _stub('retrying', retrying)

    _stub('requests', mock.Mock())

    xdg_module = types.ModuleType('xdg')
    basedir_module = types.ModuleType('xdg.BaseDirectory')
    basedir_module.save_cache_path = lambda _: ''
    xdg_module.BaseDirectory = basedir_module
    _stub('xdg', xdg_module)
    _stub('xdg.BaseDirectory', basedir_module)

    dbs_module = types.ModuleType('dbs')
    apis_module = types.ModuleType('dbs.apis')
    dbsclient_module = types.ModuleType('dbs.apis.dbsClient')

    class _DbsApi(object):
        pass

    dbsclient_module.DbsApi = _DbsApi
    apis_module.dbsClient = dbsclient_module
    dbs_module.apis = apis_module

    _stub('dbs', dbs_module)
    _stub('dbs.apis', apis_module)
    _stub('dbs.apis.dbsClient', dbsclient_module)

    wmcore_module = types.ModuleType('WMCore')
    credential_module = types.ModuleType('WMCore.Credential')
    proxy_module = types.ModuleType('WMCore.Credential.Proxy')

    class _Proxy(object):

        def __init__(self, *args, **kwargs):
            pass

        def getProxyFilename(self):
            return ''

    proxy_module.Proxy = _Proxy
    credential_module.Proxy = proxy_module
    wmcore_module.Credential = credential_module

    datastructs_module = types.ModuleType('WMCore.DataStructs')
    lumi_module = types.ModuleType('WMCore.DataStructs.LumiList')

    class _LumiList(object):

        def __init__(self, *args, **kwargs):
            pass

    lumi_module.LumiList = _LumiList
    datastructs_module.LumiList = lumi_module
    wmcore_module.DataStructs = datastructs_module

    _stub('WMCore', wmcore_module)
    _stub('WMCore.Credential', credential_module)
    _stub('WMCore.Credential.Proxy', proxy_module)
    _stub('WMCore.DataStructs', datastructs_module)
    _stub('WMCore.DataStructs.LumiList', lumi_module)

    ndcctools_module = types.ModuleType('ndcctools')
    chirp_module = types.ModuleType('ndcctools.chirp')
    chirp_module.File = object
    chirp_module.connect = mock.Mock()
    chirp_module.CHIRP_OPEN_WRITE = 0
    chirp_module.CHIRP_OPEN_APPEND = 0
    ndcctools_module.chirp = chirp_module
    _stub('ndcctools', ndcctools_module)
    _stub('ndcctools.chirp', chirp_module)

    work_queue_module = mock.Mock()
    work_queue_module.WORK_QUEUE_ALLOCATION_MODE_FIXED = 0
    work_queue_module.WORK_QUEUE_ALLOCATION_MODE_MAX = 0
    work_queue_module.WORK_QUEUE_ALLOCATION_MODE_MIN_WASTE = 0
    work_queue_module.WORK_QUEUE_ALLOCATION_MODE_MAX_THROUGHPUT = 0
    _stub('work_queue', work_queue_module)

    util_module = types.ModuleType('lobster.util')

    class _Configurable(object):
        pass

    util_module.Configurable = _Configurable
    _stub('lobster.util', util_module)

    core_module = types.ModuleType('lobster.core')
    dataset_module = types.ModuleType('lobster.core.dataset')

    class _FileInfo(object):

        def __init__(self):
            self.lumis = []
            self.events = 0
            self.size = 0

    class _DatasetInfo(object):

        def __init__(self):
            self.file_based = False
            self.files = collections.defaultdict(_FileInfo)
            self.stop_on_file_boundary = False
            self.tasksize = 1
            self.total_events = 0
            self.total_units = 0
            self.unmasked_units = 0
            self.masked_units = 0

    dataset_module.DatasetInfo = _DatasetInfo
    core_module.dataset = dataset_module
    _stub('lobster.core', core_module)
    _stub('lobster.core.dataset', dataset_module)

    spec = importlib.util.spec_from_file_location('lobster_cmssw_dataset_for_test', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, original in stubs.items():
        if original is None:
            del sys.modules[name]
        else:
            sys.modules[name] = original

    return module


_DATASET_MODULE = _load_dataset_module()
Cache = _DATASET_MODULE.Cache


class TestCmsswCache(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        patcher = mock.patch.object(_DATASET_MODULE.xdg.BaseDirectory, 'save_cache_path', return_value=self.tempdir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cache = Cache()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_cache_roundtrip_unicode(self):
        name = u'/μ/data'
        mask = u'λmask.json'
        baseinfo = [{'num_lumi': 1, 'num_event': 10}]
        dataset = {'foo': 'bar'}

        self.cache.cache(name, mask, baseinfo, dataset)

        cached_dataset = self.cache.cached(name, mask, baseinfo)

        self.assertEqual(dataset, cached_dataset)

    def test_cache_roundtrip_without_mask(self):
        name = u'/unicode/δataset'
        mask = None
        baseinfo = [{'num_lumi': 2, 'num_event': 20}]
        dataset = {'baz': 'qux'}

        self.cache.cache(name, mask, baseinfo, dataset)

        cached_dataset = self.cache.cached(name, mask, baseinfo)

        self.assertEqual(dataset, cached_dataset)


if __name__ == '__main__':
    unittest.main()
