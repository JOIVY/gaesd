#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import itertools
import json
import operator
from logging import getLogger

import six
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
    Representation of a StackDriver Span object. Can be used as a context-manager.
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
        :type span_id: Union[six.string_types(int), int]
        :param parent_span_id: StackDriver parent spanId
        :type parent_span_id: Union[six.string_types(int), int]
        :param name: StackDriver span name
        :type name: six.string_types
        :param span_kind: StackDriver SpanKind
        :type span_kind: Union[SpanKind, six.string_types]
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
        """
        Retrieve this Span's logger instance.
        """
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.sdk.loggers.get(logger_name)
        if logger is None:
            self.sdk.loggers[logger_name] = getLogger(
                '{name}'.format(name=logger_name))

        return self.sdk.loggers[logger_name]

    def set_logging_level(self, level):
        """
        Set the logging level of this span's logger.

        :param int level: New logging level to set.
        """
        return self.sdk.set_logging_level(
            level, prefix=self.__class__.__name__)

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Create a new instance of this Span.

        :param args: Passed directly through to the Span.__init__ method.
        :param kwargs: Passed directly through to the Span.__init__ method.
        :return: A new instance of an Span class.
        :rtype: Span
        """
        span = cls(*args, **kwargs)
        span.logger.debug('Created {span}'.format(span=span))
        return span

    def __repr__(self):
        return 'Span({0}<-{1})[({2} - {3}) - {4}]'.format(
            self.span_id,
            self.parent_span_id,
            self._start_time,
            self._end_time,
            self._span_kind.value,
        )

    @property
    def sdk(self):
        """
        Retrieve the SDK that this Span is associated with.

        :rtype:  SDK
        """
        return self.trace.sdk

    @classmethod
    def new_span_id(cls):
        """
        Create a new unique Span id.

        :rtype: int
        """
        if six.PY2:
            return cls._span_ids.next()
        else:
            return cls._span_ids.__next__()

    @property
    def labels(self):
        """
        Retrieve the labels associated with this Span.

        :rtype: dict
        """
        return self._labels

    @property
    def trace(self):
        """
        Retrieve the trace that this span is associated with.

        :rtype: Trace
        """
        return self._trace

    @property
    def parent_span_id(self):
        """
        Retrieve this span's span id.

        :rtype: int
        """
        return self._parent_span_id

    @parent_span_id.setter
    def parent_span_id(self, parent_span_id):
        """
        Set this span's parent span id.

        :param int parent_span_id:
        """
        self._parent_span_id = parent_span_id

    @property
    def project_id(self):
        """
        Retrieve the project id associated with the SDK associated with this
            span.

        :rtype: six.string_types
        """
        return self.sdk.project_id

    @property
    def span_id(self):
        """
        Retrieve this span's span id.

        :rtype: int
        """
        return self._span_id

    @property
    def name(self):
        """
        Retrieve this span's name.
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        Set this span's name.

        :param six.string_types name: The new name to use.
        """
        self._name = name[:128]

    @property
    def start_time(self):
        """
        Retrieve this span's start time.

        :rtype: float
        """
        return self._start_time

    @start_time.setter
    def start_time(self, start_time):
        """
        Set this span's start time

        :param datetime.datetime end_time: The new start time.
        """
        self._start_time = start_time

    @property
    def end_time(self):
        """
        Retrieve this span's end time.

        :rtype: float
        """
        return self._end_time

    @end_time.setter
    def end_time(self, end_time):
        """
        Set this span's end time

        :param datetime.datetime end_time: The new end time.
        """
        self._end_time = end_time

    @property
    def duration(self):
        """
        Retrieve this span's duration

        :rtype: float
        :raises: NoDurationError
        """
        try:
            return self.end_time - self.start_time
        except:
            raise NoDurationError(self)

    @property
    def has_duration(self):
        """
        Determine if this span has a duration.

        :rtype: bool
        """
        try:
            _ = self.duration  # NOQA: F841
            return True
        except NoDurationError:
            return False

    @property
    def span_kind(self):
        """
        Retrieve this span instance's SpanKind.

        rtype: SpanKind
        """
        return self._span_kind

    @span_kind.setter
    def span_kind(self, span_kind):
        """
        Set this span instance's SpanKind.

        :param SpanKind span_kind: The new span kind.
        """
        self._span_kind = SpanKind(
            span_kind) if span_kind is not None else SpanKind.unspecified

    def export(self):
        """
        Export this span instance as a dict.

        :return: This exported Span's data.
        :rtype: Dict[str, str]
        """
        parent_span_id = str(
            self.parent_span_id) if self.parent_span_id else None
        labels = dict(
            (str(label), str(label_value))
                for label, label_value in self.labels.items()
        )

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
        """
        Export this span instance as json.

        :return: This exported Span's data.
        :rtype: six.string_types
        """
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
        """
        Create a new nested Span instance on this span's associated trace
            with this span's span_id as the nested span's parent_span_id.
        :param kwargs: Passed directly through to Trace.span.
        :rtype: Span
        """
        return self.trace.span(parent_span=self, **kwargs)

    def __add__(self, other):
        """
        Add a span to this span's associated trace instance.

        :param other: The span to add
        :type other: Span
        """
        operator.add(self.trace, other)
        other.parent_span_id = self.span_id

    def __iadd__(self, other):
        """
        :see: `__add__`
        :rtype: Span
        """
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
        from gaesd.core.trace import Trace

        if isinstance(other, Span):
            self._parent_span_id = other.span_id
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
        from gaesd.core.trace import Trace

        if isinstance(other, Span):
            other.parent_span = self
        elif isinstance(other, Trace):
            operator.sub(other, self)
        else:
            raise TypeError('{0} is not an instance of Span'.format(other))

    def __irshift__(self, other):
        """
        :see: `__rshift__`
        :rtype: Span
        """
        operator.rshift(self, other)
        return self

    def __ilshift__(self, other):
        """
        :see: `__lshift__`
        :rtype: Span
        """
        operator.lshift(self, other)
        return self

    @property
    def decorators(self):
        """
        Retrieve a SpanDecorators instance associated to this instance.

        :return: A new Decorators instance.
        :rtype: SpanDecorators
        """
        return SpanDecorators(self)
