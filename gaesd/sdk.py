#!/usr/bin/env python
# -*- coding: latin-1 -*-

import operator
import threading
from logging import getLogger

from .core.decorators import Decorators
from .core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from .core.helpers import Helpers
from .core.span import Span
from .core.trace import Trace

DEFAULT_ENABLER = True

__all__ = ['SDK']


class SDK(object):
    """
    Thread-aware main class controlling writing data to StackDriver.
    """
    # thread-local storage:
    _context = threading.local()

    def __init__(
        self, project_id, dispatcher=GoogleApiClientDispatcher, auto=True, enabler=DEFAULT_ENABLER
    ):
        """
        :param project_id: appengine PROJECT id (eg: `joivy-dev5`)
        :type project_id: str
        :param dispatcher: Dispatcher type to use
        :type dispatcher: type(gaesd.core.dispatchers.dispatcher.Dispatcher)
        :param auto: True=dispatch traces immediately upon span completion, False=Otherwise.
        Default=True.
        :type auto: bool
        :param enabler: Global kill switch. True=enabled, Otherwise=killed. Default=True.
        :type enabler: bool/callable
        """
        self._project_id = project_id
        self.clear()
        self._context.dispatcher = dispatcher(sdk=self, auto=auto)
        self._context.enabler = enabler
        self._context.loggers = {}
        self._helpers = Helpers(self)
        self._decorators = Decorators(self)

    @property
    def loggers(self):
        return self._context.loggers

    @property
    def logger(self):
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.loggers.get(logger_name)
        if logger is None:
            self.loggers[logger_name] = getLogger('{name}'.format(name=logger_name))

        return self.loggers[logger_name]

    def set_logging_level(self, level, prefix=None):
        for logger_name, logger in self.loggers.items():
            if prefix:
                if logger_name.split('.')[0] != prefix:
                    continue
            logger.setLevel(level)

    @classmethod
    def new(cls, *args, **kwargs):
        sdk = cls(*args, **kwargs)
        sdk.logger.debug('Created {sdk}'.format(sdk=sdk))
        return sdk

    def __str__(self):
        return 'Trace-SDK({0})[{1}]'.format(
            self.project_id, [str(i) for i in self._trace_ids])

    @property
    def decorators(self):
        """
        Retrieve the decorators builder.

        :rtype: gaesd.decorators.Decorators
        """
        return self._decorators

    @property
    def helpers(self):
        """
        Retrieve the helpers builder.

        :rtype: gaesd.helpers.Helpers
        """
        return self._helpers

    @property
    def is_enabled(self):
        """
        Determine if the SDK is enabled.

        :return: True=Enabled, False=disabled (but still accumulating).
        :rtype: bool
        """
        enabler = SDK._context.enabler

        try:
            return bool(enabler())
        except:
            return bool(enabler)

    @property
    def enabler(self):
        """
        Set the SDK enabler

        :param enabler: Something or a callable that evaluated to bool
        :type enabler: Union[function, bool]
        :raises: ValueError
        """
        return self.is_enabled

    @enabler.setter
    def enabler(self, enabler):
        """
        Set the SDK enabler

        :param enabler: Something or a callable that evaluated to bool
        :type enabler: Union[function, bool]
        :raises: ValueError
        """
        if enabler is None:
            raise ValueError('enabler cannot be None')

        SDK._context.enabler = enabler

    @property
    def dispatcher(self):
        """
        Get the current SDK dispatcher.

        :rtype: gaesd.core.dispatchers.dispatcher.dispatcher.Dispatcher
        """
        return self._context.dispatcher

    @staticmethod
    def clear(traces=True, enabler=True, dispatcher=True, loggers=False):
        """
        Clear the current thread's context of the named attributes (resetting them to default
        values).
        """
        if traces:
            SDK._context.traces = []
        if enabler:
            SDK._context.enabler = False
        if dispatcher:
            SDK._context.dispatcher = None
        if loggers:
            SDK._context.loggers = {}

    @property
    def project_id(self):
        """
        Retrieve the current PROJECT_ID

        :rtype: six.string_types
        """
        return self._project_id

    @property
    def current_trace(self):
        """
        Return the current trace context-manager.

        :note: This method has side-effects - it will create a new Trace if one does not exist.
        :return: Trace context-manager
        :rtype: gaesd.Trace
        """
        try:
            return self._context.traces[-1]
        except IndexError:
            return self.trace()

    @property
    def _trace_ids(self):
        return [trace.trace_id for trace in self._context.traces]

    def trace(self, **trace_args):
        """
        Return a new trace context-manager.

        :param trace_args: kwargs passed directly to the Trace constructor.
        :return: Trace context-manager
        :rtype: core.trace.Trace
        """
        trace = Trace.new(self, **trace_args)
        trace_id = trace.trace_id

        if trace_id in self._trace_ids:
            raise ValueError('invalid trace_id {trace_id}'.format(trace_id=trace_id))

        self._context.traces.append(trace)
        return trace

    @property
    def current_span(self):
        """
        Retrieve the current span from the current trace.

        :note: This method has side-effects - it will create a new Trace and new Span if they do
        not exist.

        :return: Span context-manager
        :rtype: gaesd.Span
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
        :rtype: gaesd.Span
        """
        return self.span()

    def span(self, parent_span=None, **kwargs):
        """
        Create a new span under the current trace and span (with auto-generated `trace_id`).

        :return: Span context-manager
        :rtype: gaesd.Span
        """
        trace = self.current_trace
        parent_span = parent_span if parent_span is not None else trace.spans[-1] if \
            trace.spans else None

        span = trace.span(parent_span=parent_span, **kwargs)
        return span

    def patch_trace(self, trace):
        return self.dispatcher.patch_trace(trace)

    def __call__(self):
        return self.dispatcher()

    def __len__(self):
        return len(self._context.traces)

    def __add__(self, other):
        """
        Add a trace to the current SDK context context.
        or
        Add a span to the current trace (with side effects).
        """
        if isinstance(other, Trace):
            trace_id = other.trace_id
            if trace_id in self._trace_ids:
                raise ValueError('invalid trace_id {trace_id}'.format(trace_id=trace_id))
            self._context.traces.append(other)
        elif isinstance(other, Span):
            operator.add(self.current_trace, other)
        else:
            raise TypeError('{0} is not a Trace or Span'.format(other))

    def __iadd__(self, other):
        # TODO: Test this!
        operator.add(self, other)
        return self

    # def __lshift__(self, other):# pragma: no cover
    #     """
    #     TODO:
    #     """
    #     pass

    def __iter__(self):
        for trace in self._context.traces:
            yield trace

    def __getitem__(self, item):
        return SDK._context.traces[item]
