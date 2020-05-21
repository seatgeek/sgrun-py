"""
Code for instrumenting our python applications.
"""
import atexit
import os
import sys
from typing import Callable, NamedTuple, Optional

import ddtrace
from ddtrace.filters import FilterRequestsOnUrl

from sgrun.log import get_logger


DD_SERVICE = os.getenv("DD_SERVICE", "")
NOMAD_JOB_NAME = os.getenv("NOMAD_JOB_NAME", "")
NOOP = lambda *args: None

logger = get_logger("sgrun.instrument")


def instrument_application():  # type: () -> None
    """
    Top-level function called at the start of any python application that's been bootstrapped with sgrun.
    """
    _ddtrace_run()
    _customize_ddtrace()
    _instrument_batch_application()


def _customize_ddtrace():
    """
    Adds general seatgeek customizations to the default ddtrace setup.
    """
    ddtrace.tracer.configure(
        settings={
            "FILTERS": [
                # don't send status handler tracers to DD APM
                FilterRequestsOnUrl(r".*/(_)?status$")
            ]
        }
    )


def _instrument_batch_application():  # type: () -> None
    """
    If the current application is a batch job, starts a datadog trace for the batch run.
    """
    batch_info = _batch_job_info(NOMAD_JOB_NAME)
    if not batch_info:
        return

    tornado_fix_cleanup = _tornado_fix()
    span = ddtrace.tracer.trace(
        "batch.{}".format(batch_info.batch_type), service=DD_SERVICE
    )
    atexit.register(tornado_fix_cleanup)
    atexit.register(span.finish)


def _tornado_fix():  # type: () -> Callable
    """
    If tornado is patched, ddtrace.tracer will run with the TracerStackContext context_provider:
    https://github.com/DataDog/dd-trace-py/blob/3129a400d1fee2c544408318f6819c5485ed39a8/ddtrace/contrib/tornado/patch.py#L36

    Due to a bug in ddtrace-py (https://github.com/DataDog/dd-trace-py/issues/1353) we need to do
    some extra overhead to get the TracerStackContext set up (and cleaned up) correctly.

    This function performs necessary setup and returns a cleanup function that should be run atexit.
    If tornado isn't patched, this function (and returned cleanup functions) are noops.
    """
    # check if tornado is installed *and* patched by ddtrace
    try:
        import tornado
        from ddtrace.contrib.tornado import TracerStackContext

        tornado_patched = getattr(tornado, "__datadog_patch", False)
    except Exception:
        tornado_patched = False

    if not tornado_patched:
        return NOOP

    # setup
    # just *creating* an ioloop makes ddtrace think we're inside a running event loop (see issue in function's docstring)

    tornado.ioloop.IOLoop().current()
    tracer_stack_context = TracerStackContext()
    tracer_stack_context.__enter__()

    # cleanup
    def cleanup():
        tracer_stack_context.__exit__(None, None, None)

    return cleanup


def _ddtrace_run():  # type: () -> None
    """
    Runs the ddtrace-run bootstrap code by importing its sitecustomize directory.
    """
    from ddtrace.bootstrap import sitecustomize


_BatchJobInfo = NamedTuple("_BatchJobInfo", [("batch_type", str), ("batch_id", str)])


def _batch_job_info(job_name):  # type: (str) -> Optional[_BatchJobInfo]
    """
    Takes a nomad job name and returns a _BatchJobInfo if the job is a batch job. Otherwise
    returns None.

    # periodic job
    >>> _batch_job_info("alerts-cron-send-cart-abandonment-email/periodic-1586336400")
    _BatchJobInfo(batch_type='periodic', batch_id='1586336400')

    # dispatch job
    >>> _batch_job_info("seamstress-command/dispatch-1586337244-6e228427")
    _BatchJobInfo(batch_type='dispatch', batch_id='1586337244-6e228427')

    # non-batch job
    >>> _batch_job_info("api-9423") is None
    True
    """
    batch_suffix_parts = job_name.split("/")[-1].split("-", 1)
    if not batch_suffix_parts[0] in ("periodic", "dispatch"):
        return None

    return _BatchJobInfo(
        batch_type=batch_suffix_parts[0], batch_id=batch_suffix_parts[1]
    )
