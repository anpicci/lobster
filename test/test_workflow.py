import importlib
import inspect
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _install_work_queue_stub(monkeypatch):
    module = types.ModuleType("work_queue")
    module.WORK_QUEUE_ALLOCATION_MODE_FIXED = 0
    module.WORK_QUEUE_ALLOCATION_MODE_MAX = 1
    module.WORK_QUEUE_ALLOCATION_MODE_MIN_WASTE = 2
    module.WORK_QUEUE_ALLOCATION_MODE_MAX_THROUGHPUT = 3
    monkeypatch.setitem(sys.modules, "work_queue", module)
    if "imp" not in sys.modules:
        imp_module = types.ModuleType("imp")
        imp_module.load_source = lambda *args, **kwargs: None
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
    if "WMCore" not in sys.modules:
        wmcore_module = types.ModuleType("WMCore")
        datastructs_module = types.ModuleType("WMCore.DataStructs")
        lumilist_module = types.ModuleType("WMCore.DataStructs.LumiList")

        class LumiList(object):
            def __init__(self, *args, **kwargs):
                pass

        lumilist_module.LumiList = LumiList
        datastructs_module.LumiList = LumiList
        wmcore_module.DataStructs = datastructs_module

        monkeypatch.setitem(sys.modules, "WMCore", wmcore_module)
        monkeypatch.setitem(sys.modules, "WMCore.DataStructs", datastructs_module)
        monkeypatch.setitem(sys.modules, "WMCore.DataStructs.LumiList", lumilist_module)
    if not hasattr(inspect, "getargspec"):
        monkeypatch.setattr(inspect, "getargspec", inspect.getfullargspec, raising=False)
    return module


def test_category_fixed_mode_does_not_raise(monkeypatch):
    stub = _install_work_queue_stub(monkeypatch)
    workflow = importlib.reload(importlib.import_module("lobster.core.workflow"))

    category = workflow.Category("default", mode="fixed")

    assert category.mode == stub.WORK_QUEUE_ALLOCATION_MODE_FIXED
