#!/usr/bin/env python
# -*- coding: latin-1 -*-

import operator
import threading

from .core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from .core.span import Span
from .core.trace import Trace

DEFAULT_ENABLER = True


class SDK(object):
    _data = threading.local()

    def __init__(self, project_id, dispatcher=GoogleApiClientDispatcher, auto=True,
            enabler=DEFAULT_ENABLER):
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
        self._dispatcher = dispatcher(sdk=self, auto=auto)
        self.clear()
        self._data.enabler = enabler

    @property
    def is_enabled(self):
        enabler = SDK._data.enabler

        try:
            return bool(enabler())
        except:
            return bool(enabler)

    def set_enabler(self, enabler):
        SDK._data.enabler = enabler

    @property
    def dispatcher(self):
        return self._dispatcher

    @staticmethod
    def clear():
        SDK._data.traces = []
        SDK._data.enabler = False

    @property
    def project_id(self):
        return self._project_id

    @property
    def current_trace(self):
        """
        Return the current trace context-manager.

        :return: Trace context-manager
        :rtype: core.trace.Trace
        """
        traces = self._data.traces
        if traces:
            return traces[-1]

        return self.trace()

    @property
    def _trace_ids(self):
        return [trace.trace_id for trace in self._data.traces]

    def trace(self, **kwargs):
        """
        Return a new trace context-manager.

        kwargs['trace_id'] = new trace_id to use
        :return: Trace context-manager
        :rtype: core.trace.Trace
        """
        trace = Trace(self, **kwargs)
        trace_id = trace.trace_id

        if trace_id in self._trace_ids:
            raise ValueError('invalid trace_id {trace_id}'.format(trace_id=trace_id))

        self._data.traces.append(trace)
        return trace

    @property
    def current_span(self):
        span = self.span()
        return span

    def span(self, parent_span=None):
        """
        Create a new span under the current trace and span (with auto-generated `trace_id`).

        :return: Span context-manager
        :rtype: core.span.Span
        """
        trace = self.current_trace
        parent_span = parent_span if parent_span is not None else trace.spans[-1] if \
            trace.spans else None

        span = trace.span(parent_span=parent_span)
        return span

    def patch_trace(self, trace):
        return self._dispatcher.patch_trace(trace)

    def __call__(self):
        return self._dispatcher()

    def __len__(self):
        return len(self._data.traces)

    def __add__(self, other):
        if isinstance(other, Trace):
            trace_id = other.trace_id
            if trace_id in self._trace_ids:
                raise ValueError('invalid trace_id {trace_id}'.format(trace_id=trace_id))
            self._data.traces.append(other)
        elif isinstance(other, Span):
            operator.add(self.current_trace, other)
        else:
            raise TypeError('{0} is not a Trace or Span'.format(other))

    def __iadd__(self, other):
        operator.add(self, other)
        return self

    # TODO:
    def __lshift__(self, other):
        pass

    def __iter__(self):
        for trace in self._data.traces:
            yield trace
