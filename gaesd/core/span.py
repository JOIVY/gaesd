#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import itertools
import json
import operator

from enum import Enum, unique

from .utils import datetime_to_timestamp

__all__ = ['SpanKind', 'Span']


@unique
class SpanKind(Enum):
    unspecified = 'SPAN_KIND_UNSPECIFIED'
    server = 'RPC_SERVER'
    client = 'RPC_CLIENT'


class Span(object):
    _span_ids = itertools.count(1)

    def __init__(self, trace, span_id, parent_span=None, name='', span_kind=None, start_time=None,
            end_time=None, labels=None):
        self._trace = trace
        self._span_id = span_id
        self._parent_span = parent_span
        self._name = name
        self._start_time = start_time
        self._end_time = end_time
        self._span_kind = SpanKind(span_kind) if span_kind is not None else SpanKind.unspecified
        self._labels = labels or []

    @classmethod
    def new_span_id(cls):
        return cls._span_ids.next()

    @property
    def labels(self):
        return self._labels

    @property
    def trace(self):
        return self._trace

    @property
    def parent_span(self):
        return self._parent_span

    @parent_span.setter
    def parent_span(self, parent_span):
        self._parent_span = parent_span

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
        self._span_kind = SpanKind(span_kind) if span_kind is not None else SpanKind.unspecified

    def export(self):
        parent_span_id = str(self.parent_span.span_id) if self.parent_span else None

        return {
            'spanId': str(self.span_id),
            "kind": self.span_kind.value,
            "name": self.name,
            "startTime": datetime_to_timestamp(self.start_time),
            "endTime": datetime_to_timestamp(self.end_time),
            "parentSpanId": parent_span_id,
            "labels": [str(label) for label in self.labels],
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        self._start_time = datetime.datetime.utcnow()
        return self

    def __exit__(self, t, val, tb):
        self._end_time = datetime.datetime.utcnow()

    def span(self, **kwargs):
        return self.trace.span(parent_span=self, **kwargs)

    def __add__(self, other):
        operator.add(self.trace, other)
        other.parent_span = self

    def __iadd__(self, other):
        operator.add(self, other)
        return self

    def __rshift__(self, other):
        """
        Make span_a's parent_span = span_b
        span_a >> span_b == span_a.__rshift__(span_b)

        or

        Add span to trace at the top level
        span >> trace == span.__rshift__(trace)
        """
        from trace import Trace

        if isinstance(other, Span):
            self.parent_span = other
        elif isinstance(other, Trace):
            operator.add(other, self)
        else:
            raise TypeError('{0} is not an instance of Span'.format(other))

    def __lshift__(self, other):
        """
        make span_b's parent_span = span_a
        span_a << span_b == span_a.__lshift__(span_b)

        or

        Remove span from trace at the top level
        span << trace == span.__lshift__(trace)
        """
        from trace import Trace

        if isinstance(other, Span):
            other.parent_span = self
        elif isinstance(other, Trace):
            operator.sub(other, self)
        else:
            raise TypeError('{0} is not an instance of Span'.format(other))

    def __irshift__(self, other):
        operator.rshift(self, other)
        return self

    def __ilshift__(self, other):
        operator.lshift(self, other)
        return self
