import importlib
import importlib.util
import inspect
import logging
import os
import sys
import types


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _install_work_queue_stub(monkeypatch):
    module = types.ModuleType("work_queue")
    module.WORK_QUEUE_ALLOCATION_MODE_FIXED = 0
    module.WORK_QUEUE_ALLOCATION_MODE_MAX = 1
    module.WORK_QUEUE_ALLOCATION_MODE_MIN_WASTE = 2
    module.WORK_QUEUE_ALLOCATION_MODE_MAX_THROUGHPUT = 3
    module.WORK_QUEUE_CACHE = 4
    module.WORK_QUEUE_NOCACHE = 5
    module.WORK_QUEUE_SCHEDULE_RAND = 6
    module.WORK_QUEUE_RESULT_SUCCESS = 0
    module.WORK_QUEUE_RESULT_OUTPUT_MISSING = 1
    module.WORK_QUEUE_RESULT_MAX_RETRIES = 2
    module.WORK_QUEUE_RESULT_TASK_MAX_RUN_TIME = 3
    module.WORK_QUEUE_RESULT_TASK_TIMEOUT = 4
    module.WORK_QUEUE_RESULT_RESOURCE_EXHAUSTION = 5
    module.WORK_QUEUE_RESULT_INPUT_MISSING = 6
    module.WORK_QUEUE_RESULT_STDOUT_MISSING = 7
    module.WORK_QUEUE_RESULT_SIGNAL = 8
    module.WORK_QUEUE_RESULT_UNKNOWN = 9
    module.WORK_QUEUE_RESULT_FORSAKEN = 10

    def _noop(*args, **kwargs):
        return None

    module.cctools_debug_flags_set = _noop
    module.cctools_debug_config_file = _noop
    module.cctools_debug_config_file_size = _noop

    class _StubQueue(object):

        def __init__(self, *args, **kwargs):
            pass

        def specify_min_taskid(self, *args, **kwargs):
            pass

        def specify_log(self, *args, **kwargs):
            pass

        def specify_transactions_log(self, *args, **kwargs):
            pass

        def specify_name(self, *args, **kwargs):
            pass

        def specify_keepalive_timeout(self, *args, **kwargs):
            pass

        def tune(self, *args, **kwargs):
            pass

        def specify_algorithm(self, *args, **kwargs):
            pass

        def enable_monitoring_full(self, *args, **kwargs):
            pass

        def enable_monitoring(self, *args, **kwargs):
            pass

        def stats_hierarchy(self):
            return types.SimpleNamespace()

        def stats_category(self, *args, **kwargs):
            return types.SimpleNamespace()

    module.WorkQueue = _StubQueue

    monkeypatch.setitem(sys.modules, "work_queue", module)
    if "imp" not in sys.modules:
        imp_module = types.ModuleType("imp")

        def _load_source(name, pathname):
            spec = importlib.util.spec_from_file_location(name, pathname)
            loaded = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loaded)
            sys.modules[name] = loaded
            return loaded

        imp_module.load_source = _load_source
        monkeypatch.setitem(sys.modules, "imp", imp_module)
    if "ndcctools" not in sys.modules:
        ndcctools_module = types.ModuleType("ndcctools")
        chirp_module = types.ModuleType("ndcctools.chirp")
        ndcctools_module.chirp = chirp_module
        monkeypatch.setitem(sys.modules, "ndcctools", ndcctools_module)
        monkeypatch.setitem(sys.modules, "ndcctools.chirp", chirp_module)
    if "retrying" not in sys.modules:
        retrying_module = types.ModuleType("retrying")
        retrying_module.retry = lambda *args, **kwargs: (lambda func: func)
        monkeypatch.setitem(sys.modules, "retrying", retrying_module)
    if "daemon" not in sys.modules:
        daemon_module = types.ModuleType("daemon")

        class _Context(object):

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        daemon_module.daemon = types.SimpleNamespace(make_default_signal_map=lambda: {})
        daemon_module.DaemonContext = _Context
        monkeypatch.setitem(sys.modules, "daemon", daemon_module)
    if "psutil" not in sys.modules:
        psutil_module = types.ModuleType("psutil")

        class _Process(object):

            def open_files(self):
                return []

            def connections(self):
                return []

        psutil_module.Process = lambda *args, **kwargs: _Process()
        monkeypatch.setitem(sys.modules, "psutil", psutil_module)
    if "lobster.commands.plot" not in sys.modules:
        plot_module = types.ModuleType("lobster.commands.plot")

        class _Plotter(object):

            def __init__(self, *args, **kwargs):
                pass

            def make_plots(self, *args, **kwargs):
                pass

        plot_module.Plotter = _Plotter
        monkeypatch.setitem(sys.modules, "lobster.commands.plot", plot_module)
    if "WMCore" not in sys.modules:
        wmcore_module = types.ModuleType("WMCore")
        datastructs_module = types.ModuleType("WMCore.DataStructs")
        lumilist_module = types.ModuleType("WMCore.DataStructs.LumiList")
        storage_module = types.ModuleType("WMCore.Storage")
        site_local_module = types.ModuleType("WMCore.Storage.SiteLocalConfig")

        class LumiList(object):
            def __init__(self, *args, **kwargs):
                pass

        class _SiteConf(object):
            siteName = "TSTUB"

            def localStageOutPNN(self):
                return "TSTUB_PNN"

            frontierProxies = ["http://proxy"]

        class SiteConfigError(Exception):
            pass

        def loadSiteLocalConfig(*args, **kwargs):
            return _SiteConf()

        site_local_module.loadSiteLocalConfig = loadSiteLocalConfig
        site_local_module.SiteConfigError = SiteConfigError
        storage_module.SiteLocalConfig = site_local_module

        lumilist_module.LumiList = LumiList
        datastructs_module.LumiList = LumiList
        wmcore_module.DataStructs = datastructs_module
        wmcore_module.Storage = storage_module

        monkeypatch.setitem(sys.modules, "WMCore", wmcore_module)
        monkeypatch.setitem(sys.modules, "WMCore.DataStructs", datastructs_module)
        monkeypatch.setitem(sys.modules, "WMCore.DataStructs.LumiList", lumilist_module)
        monkeypatch.setitem(sys.modules, "WMCore.Storage", storage_module)
        monkeypatch.setitem(sys.modules, "WMCore.Storage.SiteLocalConfig", site_local_module)
    if not hasattr(inspect, "getargspec"):
        monkeypatch.setattr(inspect, "getargspec", inspect.getfullargspec, raising=False)
    return module


def test_process_preserves_unexpected_open_files(monkeypatch, tmp_path, caplog):
    _install_work_queue_stub(monkeypatch)

    captured_context = {}
    daemon_module = sys.modules["daemon"]

    class RecordingDaemonContext(object):

        def __init__(self, *args, **kwargs):
            captured_context['kwargs'] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(daemon_module, "DaemonContext", RecordingDaemonContext)

    process_module = importlib.import_module("lobster.commands.process")
    process_module = importlib.reload(process_module)
    monkeypatch.setattr(process_module, "wq", sys.modules["work_queue"])

    monkeypatch.setattr(process_module.Process, "sprint", lambda self: None)
    monkeypatch.setattr(process_module.Status, "run", lambda self, args: None)

    monkeypatch.setattr(process_module.util, "checkpoint", lambda *args, **kwargs: False)
    monkeypatch.setattr(process_module.util, "register_checkpoint", lambda *args, **kwargs: None)
    monkeypatch.setattr(process_module.util, "verify", lambda *args, **kwargs: None)
    monkeypatch.setattr(process_module.util, "get_version", lambda: "testing")
    monkeypatch.setattr(process_module.util, "get_lock", lambda *args, **kwargs: None)

    open_file = types.SimpleNamespace(path="/usr/lib/locale/locale-archive", fd=42)

    class DummyProcess(object):

        def open_files(self):
            return [open_file]

        def connections(self):
            return []

    monkeypatch.setattr(process_module.psutil, "Process", lambda: DummyProcess())

    class DummyAdvanced(object):
        dump_core = False
        threshold_for_failure = 1
        threshold_for_skipping = 1
        wq_port = 9123
        full_monitoring = False

    class DummyConfig(object):

        def __init__(self, workdir):
            self.workdir = workdir
            self.advanced = DummyAdvanced()
            self.label = "test"

    args = types.SimpleNamespace(
        config=DummyConfig(str(tmp_path)),
        finalize=False,
        foreground=True,
        force=False,
        preserve=[],
    )

    caplog.set_level(logging.WARNING, logger="lobster.core")

    process_command = process_module.Process()
    process_command.run(args)

    files_preserve = captured_context['kwargs']["files_preserve"]
    assert 42 in files_preserve
    assert 42 in args.preserve

    messages = [record.message for record in caplog.records if record.levelno >= logging.WARNING]
    assert any("/usr/lib/locale/locale-archive" in message for message in messages)
