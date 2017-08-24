#!/usr/bin/env python
# -*- coding: latin-1 -*-

import operator
import threading
from collections import Callable, MutableSequence
from logging import getLogger

from .core.decorators import Decorators
from .core.dispatchers.google_api_client_dispatcher import (
    GoogleApiClientDispatcher
)
from .core.helpers import Helpers
from .core.span import Span
from .core.trace import Trace

DEFAULT_ENABLER = True

__all__ = ['SDK']


class SDK(Callable, MutableSequence):
    """
    Thread-aware main class controlling writing data to StackDriver.
    """
    _context = threading.local()  # thread-local storage:

    def __init__(
        self, project_id, dispatcher=GoogleApiClientDispatcher, auto=True,
        enabler=DEFAULT_ENABLER,
    ):
        """
        :param project_id: appengine PROJECT id (eg: `joivy-dev5`)
        :type project_id: six.string_types
        :param dispatcher: Dispatcher type to use
        :type dispatcher: type(Dispatcher)
        :param auto: True=dispatch traces immediately upon span completion,
        False=Otherwise. Default=True.
        :type auto: bool
        :param enabler: Global kill switch. True=enabled, False=killed.
            Default=True.
        :type enabler: bool/callable
        """
        self._project_id = project_id
        self.clear()
        self._context.dispatcher = dispatcher(sdk=self, auto=auto)
        self._context.enabler = enabler
        if not hasattr(self._context, 'loggers'):
            self._context.loggers = {}
        self._helpers = Helpers(self)
        self._decorators = Decorators(self)

    @property
    def loggers(self):
        """
        Retrieve all logger instances associated with this SDK.

        :rtype: list
        """
        return self._context.loggers

    @property
    def logger(self):
        """
        Retrieve this SDK's logger instance.
        """
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.loggers.get(logger_name)
        if logger is None:
            logger = getLogger('{name}'.format(name=logger_name))
            self.loggers[logger_name] = logger

        return logger

    @classmethod
    def set_logging_level(cls, level, prefix=None):
        """
        Set the logging level of a logger associated with this SDK, one
        of it's Traces or one of it's Spans, Helpers or Decorators.

        :param int level: New logging level to set.
        :param prefix: All loggers with this prefix will have their levels set.
        :type prefix: Union[None, None, str]
        """
        for logger_name, logger in cls._context.loggers.items():
            if prefix and logger_name.split('.')[0] != prefix:
                continue
            logger.setLevel(level)

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Create a new instance of this SDK.

        :param args: Passed directly through to the SDk.__init__ method.
        :param kwargs: Passed directly through to the SDk.__init__ method.
        :return: A new instance of an SDK class.
        :rtype: SDK
        """
        return cls(*args, **kwargs)

    def __repr__(self):
        return 'Trace-SDK({0})[{1}]'.format(
            self.project_id, [str(i) for i in self._trace_ids])

    @property
    def decorators(self):
        """
        Retrieve the decorators builder.

        :rtype: Decorators
        """
        return self._decorators

    @property
    def helpers(self):
        """
        Retrieve the helpers builder.

        :rtype: Helpers
        """
        return self._helpers

    @property
    def is_enabled(self):
        """
        Determine if the SDK is enabled.
        An enabled SDK is one that will not dispatch traces to StackDriver
        but will still create and capture traces and spans.

        :return: True=Enabled, False=disabled.
        :rtype: bool
        """
        value = self._context.enabler

        try:
            return bool(value())
        except Exception:
            return bool(value)

    @property
    def enabler(self):
        """
        Get the SDK enabler's result.

        :return: The evaluated SDk's enabled.
        :rtype: bool
        """
        return self.is_enabled

    @enabler.setter
    def enabler(self, enabler):
        """
        Set the SDK enabler.

        :param enabler: Something or a callable that evaluated to bool
        :type enabler: Union[function, bool]
        :raises: ValueError
        """
        if enabler is None:
            raise ValueError('enabler cannot be None')

        self._context.enabler = enabler

    @property
    def dispatcher(self):
        """
        Get the current SDK dispatcher in use.

        :rtype: Dispatcher
        """
        return self._context.dispatcher

    @classmethod
    def clear(cls, traces=True, enabler=True, dispatcher=True, loggers=False):
        """
        Clear the current thread's context of the named attributes.
        This will reset them to their default values.
        """
        if traces:
            cls._context.traces = []
        if enabler:
            cls._context.enabler = False
        if dispatcher:
            cls._context.dispatcher = None
        if loggers:
            cls._context.loggers = {}

    @property
    def project_id(self):
        """
        Retrieve the current SDK's project_id

        :rtype: six.string_types
        """
        return self._project_id

    @property
    def current_trace(self):
        """
        Retrieve the current Trace instance.

        :note: This method has side-effects - it will create a new Trace if
        one does not exist.
        :return: The new trace instance.
        :rtype: Trace
        """
        try:
            return self._context.traces[-1]
        except IndexError:
            return self.trace()

    @property
    def _trace_ids(self):
        """
        Retrieve a list of all trace ids in use.

        :return: The trace ids.
        :rtype: list(int)
        """
        return [trace.trace_id for trace in self._context.traces]

    @property
    def traces(self):
        """
        Retrieve a list of the current traces.

        :return: A shallow-copy list of this SDK's traces.
        :rtype: list(Trace)
        """
        return self._context.traces[:]

    def trace(self, **trace_args):
        """
        Create a new Trace instance.

        :param trace_args: kwargs passed directly to the Trace constructor.
        :return: Trace context-manager
        :rtype: core.trace.Trace
        """
        trace = Trace.new(self, **trace_args)
        trace_id = trace.trace_id

        if trace_id in self._trace_ids:
            raise ValueError(
                'duplicate trace_id {trace_id}'.format(trace_id=trace_id))

        self._context.traces.append(trace)
        return trace

    @property
    def new_trace(self):
        """
        Create a new Trace with default parameters.

        :return: The new trace instance
        :rtype: Trace
        """
        return self.trace()

    @property
    def current_span(self):
        """
        Retrieve the current span from the current trace.

        :note: This method has side-effects - it will create a new Trace and
        new Span if they do not exist.

        :return: Span context-manager instance
        :rtype: Span
        """
        trace = self.current_trace
        return trace.current_span

    @property
    def has_current_span(self):
        """
        Determine if a current span exists (without side-effects).

        :return: True=A current span exists.
        :rtype: bool
        """
        traces = self._context.traces
        if traces:
            if self.current_trace.spans:
                return True

    @property
    def new_span(self):
        """
        Create a new Span with default parameters.

        :return: Span context-manager
        :rtype: Span
        """
        return self.span()

    def span(self, parent_span=None, **span_args):
        """
        Create a new span under the current trace and span
            (with auto-generated `trace_id`).

        :param Span parent_span: Parent span to be this span's parent.
        :param span_args: Passed directly to the Trace.span method.
        :return: Span context-manager
        :rtype: Span
        """
        trace = self.current_trace
        parent_span = parent_span if parent_span is not None else \
            trace.spans[-1] if trace.spans else None

        return trace.span(parent_span=parent_span, **span_args)

    def patch_trace(self, trace):
        return self.dispatcher.patch_trace(trace)

    def __call__(self):
        """
        Call the dispatcher.

        :return: Whatever the dispatcher returns.
        """
        return self.dispatcher()

    def __len__(self):
        """
        The number of traces in this sdk instance.

        :rtype: int
        """
        return len(self._context.traces)

    def __add__(self, other):
        """
        Add a trace to the current SDK's context.
        or
        Add a span to the current trace (with side effects).
        """
        if isinstance(other, Trace):
            trace_id = other.trace_id
            if trace_id in self._trace_ids:
                raise ValueError(
                    'invalid trace_id {trace_id}'.format(trace_id=trace_id))
            self._context.traces.append(other)
        elif isinstance(other, Span):
            operator.add(self.current_trace, other)
        else:
            raise TypeError(
                'Expecting type Trace or Span but got {t}'.format(t=other))

    def __iadd__(self, other):  # pragma: no cover
        """
        :see: `__add__`
        :rtype: SDK
        """
        operator.add(self, other)
        return self

    def __lshift__(self, other):  # pragma: no cover
        """
        TODO:
        """
        pass

    def __iter__(self):
        """
        Iterate over all traces within this sdk instance

        :rtype: Trace
        """
        for trace in self._context.traces:
            yield trace

    def __getitem__(self, item):
        """
        Get the item from this sdks traces.

        :rtype: Trace
        """
        return self._context.traces[item]

    def __contains__(self, item):
        """
        Determine if the trace is present in this SDK's traces.
        OR
        Determine if the span is present in any of this SDK's traces.

        :type item: Union[Trace, Span]
        :rtype: bool
        """
        if isinstance(item, Trace):
            return item in self._context.traces
        elif isinstance(item, Span):
            return any([
                item in span for span in
                [trace.spans for trace in self._context.traces]
            ])
        return False

    def __setitem__(self, index, value):
        """
        Insert the trace into this SDK's trace list at the given index.

        :param index: index to insert into
        :type index: int
        :param value: Trace to insert
        :type value: Trace
        """
        if not isinstance(value, Trace):
            raise TypeError('Can only set item of type=Trace')
        self._context.traces[index] = value

    def __delitem__(self, index):
        """
        Delete the trace from the SDK's trace list at the given index.

        :param index: index to delete from
        :type index: int
        """
        del self._context.traces[index]

    def insert(self, index, value):
        'S.insert(index, object) -- insert object before index'
        if not isinstance(value, Trace):
            raise TypeError('Can only insert item of type=Trace')

        self._context.traces.insert(index, value)
