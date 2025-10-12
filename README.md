[![Build Status](https://api.travis-ci.org/NDCMS/lobster.svg?branch=master)](https://travis-ci.org/NDCMS/lobster)
[![Documentation Status](https://readthedocs.org/projects/lobster/badge/?version=latest)](http://lobster.readthedocs.org/en/latest/?badge=latest)

# Introduction

Lobster is a workflow management tool running in userspace with no special
privileges, built to harness non-dedicated resources for high-throughput
workloads.  To be used, a head node with access to CMSSW, a proxy server,
and a Condor queue are all that is needed.

It is currently in use at the University of Notre Dame for both Monte-Carlo
event generation and analysis data processing, within the local
[CMS](http://cms.cern.ch) group.

# Read More

See the [documentation](http://lobster.readthedocs.io) for installing and
running Lobster, and the [website](http://lobster.crc.nd.edu) for more
general information.

## Python interpreter selection

Lobster now detects the Python interpreter that should be used inside worker
payloads and helper scripts.  When a job starts the wrapper script will
inspect the environment and pick an interpreter in the following order:

1. The executable name or path configured through
   ``AdvancedOptions(python_interpreter=...)`` in your Lobster configuration.
   If the configured binary cannot be executed on a worker, Lobster falls back
   to the automatic detection steps below.
2. A path provided via the ``LOBSTER_PYTHON`` environment variable.
3. An interpreter discovered on the worker, preferring ``python3`` and then
   ``python`` from ``PATH``.
4. The interpreter shipped with the active CMSSW release (if available).

The chosen executable is exported as ``LOBSTER_PYTHON`` and reused by helper
scripts such as ``autosense.sh``.  This allows heterogeneous worker nodes with
different ``scram_arch`` values to run the same project while still permitting
explicit overrides when required—for example by exporting ``LOBSTER_PYTHON`` in
your job environment or by setting ``python_interpreter`` in the configuration.
