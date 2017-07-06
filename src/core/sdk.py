#!/usr/bin/env python
# -*- coding: latin-1 -*-

import threading

from .trace import Trace


class SDK(object):
    _data = threading.local()

    def __init__(self, project_id):
        self._project_id = project_id

        if not hasattr(SDK._data, 'stack'):
            SDK._data.traces = []

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

        return self.trace

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
    def span(self):
        """
        Create a new span under the current trace and span (with auto-generated `trace_id`).

        :return: Span context-manager
        :rtype: core.span.Span
        """
        trace = self.current_trace
        parent_span = trace.spans[-1]
        span = trace.span(parent_span=parent_span)
        return span
