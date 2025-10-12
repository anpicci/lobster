import importlib.util
import inspect
import os
import pickle
import sys
import types
import tempfile

if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Provide lightweight fallbacks for optional runtime dependencies so the
# modules under test can be imported in isolation.
if 'imp' not in sys.modules:
    imp_module = types.ModuleType('imp')

    def load_source(name, pathname, file=None):
        spec = importlib.util.spec_from_file_location(name, pathname)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    imp_module.load_source = load_source
    sys.modules['imp'] = imp_module

if 'ndcctools' not in sys.modules:
    ndcctools = types.ModuleType('ndcctools')
    chirp_module = types.ModuleType('ndcctools.chirp')

    class _StubChirpClient(object):

        def __init__(self, *args, **kwargs):
            raise RuntimeError('ndcctools.chirp client is not available in tests')

    class _StubChirpError(Exception):
        pass

    chirp_module.Client = _StubChirpClient
    chirp_module.AuthenticationFailure = _StubChirpError

    ndcctools.chirp = chirp_module
    sys.modules['ndcctools'] = ndcctools
    sys.modules['ndcctools.chirp'] = chirp_module

if 'work_queue' not in sys.modules:
    work_queue = types.ModuleType('work_queue')

    work_queue.WORK_QUEUE_ALLOCATION_MODE_FIXED = 1
    work_queue.WORK_QUEUE_ALLOCATION_MODE_MAX = 2
    work_queue.WORK_QUEUE_ALLOCATION_MODE_MIN_WASTE = 3
    work_queue.WORK_QUEUE_ALLOCATION_MODE_MAX_THROUGHPUT = 4
    work_queue.WORK_QUEUE_CACHE = 5
    work_queue.WORK_QUEUE_NOCACHE = 6
    work_queue.WORK_QUEUE_SCHEDULE_RAND = 7

    work_queue.WORK_QUEUE_RESULT_SUCCESS = 0
    work_queue.WORK_QUEUE_RESULT_OUTPUT_MISSING = 2
    work_queue.WORK_QUEUE_RESULT_MAX_RETRIES = 256
    work_queue.WORK_QUEUE_RESULT_TASK_MAX_RUN_TIME = 512
    work_queue.WORK_QUEUE_RESULT_TASK_TIMEOUT = 32
    work_queue.WORK_QUEUE_RESULT_RESOURCE_EXHAUSTION = 16
    work_queue.WORK_QUEUE_RESULT_INPUT_MISSING = 1
    work_queue.WORK_QUEUE_RESULT_STDOUT_MISSING = 4
    work_queue.WORK_QUEUE_RESULT_SIGNAL = 8
    work_queue.WORK_QUEUE_RESULT_UNKNOWN = 64
    work_queue.WORK_QUEUE_RESULT_FORSAKEN = 128

    sys.modules['work_queue'] = work_queue

if 'retrying' not in sys.modules:
    retrying = types.ModuleType('retrying')

    def _retry(*args, **kwargs):
        def decorator(func):
            return func

        if args and callable(args[0]):
            func = args[0]
            return decorator(func)

        return decorator

    retrying.retry = _retry
    sys.modules['retrying'] = retrying

if 'WMCore' not in sys.modules:
    wmcore = types.ModuleType('WMCore')

    credential_module = types.ModuleType('WMCore.Credential')
    proxy_module = types.ModuleType('WMCore.Credential.Proxy')

    class _StubProxy(object):

        def __init__(self, *args, **kwargs):
            pass

        def getProxyFilename(self):
            return 'proxy'

    proxy_module.Proxy = _StubProxy
    credential_module.Proxy = proxy_module

    data_structs_module = types.ModuleType('WMCore.DataStructs')
    lumilist_module = types.ModuleType('WMCore.DataStructs.LumiList')

    class _StubLumiList(object):

        def __init__(self, filename=None, lumis=None):
            self._lumis = lumis or []

        def __contains__(self, item):
            return False

        def getCompactList(self):
            return []

    lumilist_module.LumiList = _StubLumiList
    data_structs_module.LumiList = lumilist_module

    wmcore.Credential = credential_module
    wmcore.DataStructs = data_structs_module

    sys.modules['WMCore'] = wmcore
    sys.modules['WMCore.Credential'] = credential_module
    sys.modules['WMCore.Credential.Proxy'] = proxy_module
    sys.modules['WMCore.DataStructs'] = data_structs_module
    sys.modules['WMCore.DataStructs.LumiList'] = lumilist_module

if 'dbs' not in sys.modules:
    dbs = types.ModuleType('dbs')
    apis_module = types.ModuleType('dbs.apis')
    dbs_client_module = types.ModuleType('dbs.apis.dbsClient')

    class _StubDbsApi(object):

        def __init__(self, *args, **kwargs):
            pass

    dbs_client_module.DbsApi = _StubDbsApi
    apis_module.dbsClient = dbs_client_module
    dbs.apis = apis_module

    sys.modules['dbs'] = dbs
    sys.modules['dbs.apis'] = apis_module
    sys.modules['dbs.apis.dbsClient'] = dbs_client_module

if 'xdg' not in sys.modules:
    xdg_module = types.ModuleType('xdg')
    base_directory_module = types.ModuleType('xdg.BaseDirectory')

    def _save_cache_path(appname):
        return tempfile.mkdtemp(prefix='lobster-cache-')

    base_directory_module.save_cache_path = _save_cache_path
    xdg_module.BaseDirectory = base_directory_module

    sys.modules['xdg'] = xdg_module
    sys.modules['xdg.BaseDirectory'] = base_directory_module

if 'lobster.core.workflow' not in sys.modules:
    workflow_module = types.ModuleType('lobster.core.workflow')

    class _StubCategory(object):

        def __init__(self, name, cores=1, mode='fixed'):
            self.name = name
            self.cores = cores
            self.mode = mode

    class _StubWorkflow(object):

        def __init__(self, *args, **kwargs):
            self.category = kwargs.get('category', _StubCategory('default'))

    workflow_module.Category = _StubCategory
    workflow_module.Workflow = _StubWorkflow
    sys.modules['lobster.core.workflow'] = workflow_module

if 'requests' not in sys.modules:
    requests_module = types.ModuleType('requests')

    class _StubResponse(object):

        ok = True

        def __init__(self, text=''):
            self.text = text

    def _stub_get(url):
        return _StubResponse()

    requests_module.get = _stub_get
    sys.modules['requests'] = requests_module

from lobster.core import Config
from lobster.cmssw.dataset import Cache
from lobster.util import PICKLE_PROTOCOL


def test_config_save_uses_python2_compatible_protocol(tmp_path, monkeypatch):
    captured = {}

    def fake_dump(obj, file_obj, protocol=None):
        captured['protocol'] = protocol

    monkeypatch.setattr(pickle, 'dump', fake_dump)

    config = Config.__new__(Config)
    config.workdir = str(tmp_path)

    config.save()

    assert captured['protocol'] == PICKLE_PROTOCOL


def test_dataset_cache_uses_python2_compatible_protocol(tmp_path, monkeypatch):
    captured = {}

    def fake_dump(obj, file_obj, protocol=None):
        captured['protocol'] = protocol

    monkeypatch.setattr(pickle, 'dump', fake_dump)

    cache = Cache()
    cache.cachedir = str(tmp_path)

    cache.cache('dataset', mask=None, baseinfo={'info': 1}, dataset={'data': 2})

    assert captured['protocol'] == PICKLE_PROTOCOL
