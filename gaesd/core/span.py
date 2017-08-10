#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import itertools
import json
import operator
from logging import getLogger

from enum import Enum, unique

from gaesd.core.decorators import SpanDecorators
from .utils import (
    DuplicateSpanEntryError, NoDurationError, datetime_to_timestamp,
)

__all__ = ['SpanKind', 'Span']


@unique
class SpanKind(Enum):
    unspecified = 'SPAN_KIND_UNSPECIFIED'
    server = 'RPC_SERVER'
    client = 'RPC_CLIENT'


class Span(object):
    """
    Representation of a StackDriver Span object.
    """
    _span_ids = itertools.count(1)

    def __init__(
        self, trace, span_id, parent_span_id=None, name='', span_kind=None,
        start_time=None, end_time=None, labels=None
    ):
        """
        :param trace: The Trace object containing this Span object
        :type trace: gaesdk.Trace
        :param span_id: StackDriver spanId
        :type span_id: Union[six.str_types(int), int]
        :param parent_span_id: StackDriver parent spanId
        :type parent_span_id: Union[six.str_types(int), int]
        :param name: StackDriver span name
        :type name: six.str_types
        :param span_kind: StackDriver SpanKind
        :type span_kind: Union[SpanKind, six.str_types]
        :param start_time: StackDriver startTime of this span
        :type start_time: datetime.datetime
        :param end_time: StackDriver endTime of this span
        :type end_time: datetime.datetime
        :param labels: labels to associate with this span.
        :type labels: dict
        """
        self._trace = trace
        self._span_id = span_id
        self._parent_span_id = parent_span_id
        self._name = name
        self._start_time = start_time
        self._end_time = end_time
        self._span_kind = SpanKind(
            span_kind) if span_kind is not None else SpanKind.unspecified
        self._labels = labels or {}

    @property
    def logger(self):
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.sdk.loggers.get(logger_name)
        if logger is None:
            self.sdk.loggers[logger_name] = getLogger(
                '{name}'.format(name=logger_name))

        return self.sdk.loggers[logger_name]

    def set_logging_level(self, level):
        return self.sdk.set_logging_level(level, prefix=self.__class__.__name__)

    @classmethod
    def new(cls, *args, **kwargs):
        span = cls(*args, **kwargs)
        span.logger.debug('Created {span}'.format(span=span))
        return span

    def __repr__(self):
        return 'Span({0}<-{1})[({2} - {3}) - {4}]'.format(
            self.span_id, self.parent_span_id, self._start_time, self._end_time,
            self._span_kind.value
        )

    @property
    def sdk(self):
        return self.trace.sdk

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
    def parent_span_id(self):
        return self._parent_span_id

    @parent_span_id.setter
    def parent_span_id(self, parent_span_id):
        self._parent_span_id = parent_span_id

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

    @start_time.setter
    def start_time(self, start_time):
        self._start_time = start_time

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, end_time):
        self._end_time = end_time

    @property
    def duration(self):
        try:
            return self.end_time - self.start_time
        except:
            raise NoDurationError(self)

    @property
    def has_duration(self):
        try:
            _ = self.duration  # NOQA: F841
            return True
        except NoDurationError:
            return False

    @property
    def span_kind(self):
        return self._span_kind

    @span_kind.setter
    def span_kind(self, span_kind):
        self._span_kind = SpanKind(
            span_kind) if span_kind is not None else SpanKind.unspecified

    def export(self):
        parent_span_id = str(
            self.parent_span_id) if self.parent_span_id else None
        labels = dict((str(label), str(label_value)) for label, label_value in
            self.labels.items())

        return {
            'spanId': str(self.span_id),
            "kind": self.span_kind.value,
            "name": self.name,
            "startTime": datetime_to_timestamp(self.start_time),
            "endTime": datetime_to_timestamp(self.end_time),
            "parentSpanId": parent_span_id,
            "labels": labels,
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        if self._start_time is not None:
            raise DuplicateSpanEntryError(self)

        self._start_time = datetime.datetime.utcnow()
        return self

    def __exit__(self, t, val, tb):
        self._end_time = datetime.datetime.utcnow()

        # Fire of this trace:
        self.trace.end(self)

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

    @property
    def decorators(self):
        return SpanDecorators(self)
