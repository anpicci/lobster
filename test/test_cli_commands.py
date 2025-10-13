import importlib.util
import inspect
import os
import sys
import types

from argparse import ArgumentParser, _SubParsersAction


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


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
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module
            return module

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


def test_cli_command_registration(monkeypatch):
    _install_work_queue_stub(monkeypatch)

    import lobster.ui  # noqa: F401 - ensure module import side-effects occur
    from lobster.core import command, workflow
    import lobster.commands as commands_pkg

    parser = ArgumentParser()
    command.Command.plugins.clear()

    commands_dir = os.path.dirname(commands_pkg.__file__)
    monkeypatch.setattr(
        command.glob,
        "glob",
        lambda pattern: [
            os.path.join(commands_dir, basename)
            for basename in ("process.py", "status.py")
        ],
    )
    command.Command.register([commands_dir], parser)

    assert "process" in command.Command.plugins
    assert "status" in command.Command.plugins

    subparser_actions = [
        action for action in parser._actions if isinstance(action, _SubParsersAction)
    ]
    assert subparser_actions, "expected parser to expose subparser actions"
    choices = subparser_actions[0].choices
    assert "process" in choices
    assert "status" in choices

    category = workflow.Category("default")
    assert hasattr(category, "_store")
    assert callable(category._store)
