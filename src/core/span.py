#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json


class Span(object):
    def __init__(self, trace, span_id, parent_span=None, name='', span_kind=None,
            start_time=None, end_time=None, labels=None):
        self._trace = trace
        self._span_id = span_id
        self._parent_span = parent_span

        self._name = name
        self._span_kind = span_kind
        self._start_time = start_time
        self._end_time = end_time
        self.labels = labels or []

    @property
    def trace(self):
        return self._trace

    @property
    def parent_span(self):
        return self._parent_span

    @property
    def project_id(self):
        return self.trace.project_id

    @property
    def span_id(self):
        return self._span_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name[:128]

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def span_kind(self):
        return self._span_kind

    @span_kind.setter
    def span_kind(self, span_kind):
        # TODO: Validate enum `span_kind`:
        self._span_kind = span_kind

    def export(self):
        # TODO: FIXME: Implement this:

        parent_span_id = str(self.parent_span.span_id) if self.parent_span else None

        return {
            'spanId': self.span_id,
            "kind": self.span_kind,
            "name": self.name,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "parentSpanId": parent_span_id,
            "labels": self.labels,
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        self._start_time = datetime.datetime.utcnow()
        return self

    def __exit__(self, t, val, tb):
        self._end_time = datetime.datetime.utcnow()
