#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import operator
import uuid
from collections import MutableSequence
from logging import getLogger
from types import NoneType

from gaesd.core.decorators import TraceDecorators
from .span import Span
from .utils import InvalidSliceError, find_spans_in_datetime_range, find_spans_in_float_range, \
    find_spans_with_duration_less_than

__all__ = ['Trace']


class Trace(MutableSequence):
    """
    Representation of a StackDriver Trace object.
    """

    def __init__(self, sdk, trace_id=None, root_span_id=None):
        """
        :param sdk: Instance of SDK.
        :type sdk: gaesd.SDK
        :param trace_id: TraceId
        :type trace_id: str
        :param root_span_id: Default span_id to give a trace's top level spans.
        :type root_span_id: str/int
        """
        super(Trace, self).__init__()
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id if trace_id is not None else self.new_trace_id()
        self._root_span_id = root_span_id
        self._span_tree = []

    @property
    def logger(self):
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.sdk.loggers.get(logger_name)
        if logger is None:
            self.sdk.loggers[logger_name] = getLogger('{name}'.format(name=logger_name))

        return self.sdk.loggers[logger_name]

    def set_logging_level(self, level):
        return self.sdk.set_logging_level(level, prefix=self.__class__.__name__)

    @classmethod
    def new(cls, *args, **kwargs):
        trace = cls(*args, **kwargs)
        trace.logger.debug('Created {trace}'.format(trace=trace))
        return trace

    def __repr__(self):
        return 'Trace({0} with root {2})[{1}]'.format(
            self.trace_id, ', '.join([str(i) for i in self.spans]), self._root_span_id)

    @property
    def root_span_id(self):
        return self._root_span_id

    @root_span_id.setter
    def root_span_id(self, span_id):
        self._root_span_id = span_id

    @staticmethod
    def new_trace_id():
        return uuid.uuid4().hex

    @property
    def trace_id(self):
        return self._trace_id

    @trace_id.setter
    def trace_id(self, trace_id):
        self._trace_id = trace_id

    @property
    def sdk(self):
        return self._sdk

    @property
    def spans(self):
        return self._spans[:]

    def set_default(self, **kwargs):
        if 'trace_id' in kwargs:
            self._trace_id = kwargs['trace_id']
        if 'root_span_id' in kwargs:
            self._root_span_id = kwargs['root_span_id']

    @property
    def current_span(self):
        """
        Get the current span for this trace.

        :note: Has side effects!
        :return: The span
        :rtype: gaesd.Span
        """
        return self._span_tree[-1] if self._span_tree else self.sdk.new_span

    @property
    def span_ids(self):
        """
        Retrieve the current span_ids in this Trace

        :return: span ids
        :rtype: list(str(int)/int)
        """
        return [span.span_id for span in self._spans]

    @property
    def project_id(self):
        return self.sdk.project_id

    def _add_new_span_to_span_tree(self, new_span):
        if not self._span_tree:
            self._span_tree.append(new_span)
        else:
            if self.spans and new_span:
                if self._span_tree[-1].span_id == new_span.parent_span_id:
                    self._span_tree.append(new_span)

    def _remove_span_from_span_tree(self, span):
        if self._span_tree:
            if self._span_tree[-1] is span:
                self._span_tree.pop(-1)

    def span(self, parent_span=None, **span_args):
        """
        Create a new span for this trace and make it the current_span.

        :param parent_span: Optional parent span
        :type parent_span: gaesd.Span
        :param span_args: Passed directly to the Span constructor.
        :return: The new span
        :rtype: gaesd.Span
        """
        parent_span_id = parent_span.span_id if parent_span is not None else self.root_span_id

        span = Span.new(
            trace=self,
            span_id=Span.new_span_id(),
            parent_span_id=parent_span_id,
            **span_args
        )

        self._spans.append(span)
        self._add_new_span_to_span_tree(span)
        return span

    def export(self):
        return {
            'projectId': str(self.project_id),
            'traceId': str(self.trace_id),
            'spans': [i.export() for i in self.spans if i is not None],
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        return self

    def __exit__(self, t, val, tb):
        self.end()

    def end(self, span=None):
        self._remove_span_from_span_tree(span)
        self.sdk.patch_trace(self)

    def __add__(self, other):
        """
        Add a span to the current Trace and make it the current_span.

        :param other: The span to add.
        :type other: gaesd.Span
        """
        if not isinstance(other, Span):
            raise TypeError('{0} is not an instance of Span'.format(other))

        span_id = other.span_id
        if span_id in self.span_ids:
            raise ValueError('span_id {0} already present in this Trace'.format(span_id))

        self._spans.append(other)
        self._add_new_span_to_span_tree(other)

    def __iadd__(self, other):
        operator.add(self, other)
        return self

    def __len__(self):
        return len(self.spans)

    def __sub__(self, other):
        """
        Remove the span from the current Trace and attempt to make it not the current_span.

        :param other: The span to remove.
        :type other: gaesd.Span
        """
        if not isinstance(other, Span):
            raise TypeError('{0} is not an instance of Span'.format(other))

        self._spans.remove(other)
        self._remove_span_from_span_tree(other)

    def __isub__(self, other):
        operator.sub(self, other)
        return self

    def __iter__(self):
        for span in self.spans:
            yield span

    def __getitem__(self, item):
        """
        Get a span from this trace based on various criteria:

        1. slice(datetime.datetime/None, datetime.datetime/None, whatever):
            Find spans contained entirely within the date range. None = ignore.
        2. slice(float, float):
            Find spans contained entirely within the floating point timestamp range. None = ignore.
        3.  datetime.timedelta:
            Find spans with a duration <= this timedelta.
        """
        if isinstance(item, slice):
            # Get spans that filter as the slice:
            start = item.start
            step = item.step
            stop = item.stop

            if all([isinstance(i, (datetime.datetime, NoneType)) for i in [start, stop]]):
                # Find all spans where (span.start>=start) and (stop<span.stop)
                spans = find_spans_in_datetime_range(self.spans, start, stop)
                return spans[::step]
            if all([isinstance(i, float) for i in [start, stop]]):
                spans = find_spans_in_float_range(self.spans, start, stop)
                return spans[::step]
            if not all([isinstance(i, (int, NoneType)) for i in [start, stop, step]]):
                raise InvalidSliceError('Invalid slice {slice}'.format(slice=slice))
        elif isinstance(item, datetime.timedelta):
            # Find all spans that have a duration `<` item
            spans = find_spans_with_duration_less_than(self.spans, item)
            return spans

        return self._spans[item]

    @property
    def decorators(self):
        return TraceDecorators(self)

    def __setitem__(self, index, value):
        if not isinstance(value, Span):
            raise TypeError('Can only insert item of type=Span')
        self._spans[index] = value

    def __delitem__(self, index):
        del self._spans[index]

    def insert(self, index, value):
        'S.insert(index, object) -- insert object before index'
        if not isinstance(value, Span):
            raise TypeError('Can only insert item of type=Span')
        self._spans.insert(index, value)
