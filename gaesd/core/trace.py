#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import operator
import uuid
from collections import MutableSequence
from logging import getLogger

from gaesd.core.decorators import TraceDecorators
from .span import Span
from .utils import (
    InvalidSliceError, find_spans_in_datetime_range, find_spans_in_float_range,
    find_spans_with_duration_less_than,
)

__all__ = ['Trace']


class Trace(MutableSequence):
    """
    Representation of a StackDriver Trace object. Can be used as a context-manager.
    """

    def __init__(self, sdk, trace_id=None, root_span_id=None):
        """
        :param SDK sdk: Instance of SDK this trace belongs to.
        :param six.string_types trace_id: TraceId
        :param str/int root_span_id: Default span_id to give a trace's top
            level spans.
        """
        super(Trace, self).__init__()
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id if trace_id is not None else \
            self.new_trace_id()
        self._root_span_id = root_span_id
        self._span_tree = []

    @property
    def logger(self):
        """
        Retrieve this trace's logger instance.
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
        Set the logging level of this trace's logger.

        :param int level: New logging level to set.
        """
        return self.sdk.set_logging_level(
            level,
            prefix=self.__class__.__name__,
        )

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Create a new instance of this Trace.

        :param args: Passed directly through to the Trace.__init__ method.
        :param kwargs: Passed directly through to the Trace.__init__ method.
        :return: A new instance of an Trace class.
        :rtype: Trace
        """
        trace = cls(*args, **kwargs)
        trace.logger.debug('Created {trace}'.format(trace=trace))
        return trace

    def __repr__(self):
        return 'Trace({0} with root {2})[{1}]'.format(
            self.trace_id, ', '.join([str(i) for i in self.spans]),
            self._root_span_id)

    @property
    def root_span_id(self):
        """
        Retrieve the default root_span_id for this Trace instance.

        :return: Span Id
        :rtype: int
        """
        return self._root_span_id

    @root_span_id.setter
    def root_span_id(self, span_id):
        """
        Set the default root_span_id for this Trace instance.

        :param span_id: The new span id to use.
        :type span_id: int
        """
        self._root_span_id = span_id

    @staticmethod
    def new_trace_id():
        """
        Create a new unique Trace id.

        :rtype: six.string_types
        """
        return uuid.uuid4().hex

    @property
    def trace_id(self):
        """
        Retrieve this trace's trace id.

        :rtype: six.string_types
        """
        return self._trace_id

    @trace_id.setter
    def trace_id(self, trace_id):
        """
        Set this trace's trace id.

        :param trace_id: The new trace id to use
        :type trace_id: six.string_types
        """
        self._trace_id = trace_id

    @property
    def sdk(self):
        """
        Retrieve the SDK that this Trace is associated with.

        :rtype:  SDK
        """
        return self._sdk

    @property
    def spans(self):
        """
        Retrieve a list of this trace's spans.

        :return: A shallow-copy list of this Trace's spans.
        :rtype: list(Span)
        """
        return self._spans[:]

    def set_default(self, **kwargs):
        """
        Set the default trace_id and root_span_id for this Trace instane.
        """
        if 'trace_id' in kwargs:
            self._trace_id = kwargs['trace_id']
        if 'root_span_id' in kwargs:
            self._root_span_id = kwargs['root_span_id']

    @property
    def current_span(self):
        """
        Get the current span for this trace.

        :note: Has side effects
            A new Span may be created if one does not exist.
        :return: The span
        :rtype: Span
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
        """
        Retrieve the project_id associated with the SDK's associated with this
        trace instance.

        :rtype: six.string_types
        """
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
        :type parent_span: Span
        :param span_args: Passed directly to the Span constructor.
        :return: The new span
        :rtype: Span
        """
        parent_span_id = parent_span.span_id if parent_span is not None else \
            self.root_span_id

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
        """
        Export this trace instance as a dict.

        :return: This exported Trace's data.
        :rtype: Dict[str, str]
        """
        return {
            'projectId': str(self.project_id),
            'traceId': str(self.trace_id),
            'spans': [i.export() for i in self.spans if i is not None],
        }

    @property
    def json(self):
        """
        Export this trace instance as json.

        :return: This exported Trace's data.
        :rtype: six.string_types
        """
        return json.dumps(self.export())

    def __enter__(self):
        return self

    def __exit__(self, t, val, tb):
        self.end()

    def end(self, span=None):
        """
        Notify this Trace that it has completed.

        :param Span span: The final span.
        """
        self._remove_span_from_span_tree(span)
        self.sdk.patch_trace(self)

    def __add__(self, other):
        """
        Add a span to the current Trace and make it the current_span.

        :param other: The span to add.
        :type other: Span
        """
        if not isinstance(other, Span):
            raise TypeError('{0} is not an instance of Span'.format(other))

        span_id = other.span_id
        if span_id in self.span_ids:
            raise ValueError(
                'span_id {0} already present in this Trace'.format(span_id))

        self._spans.append(other)
        self._add_new_span_to_span_tree(other)

    def __iadd__(self, other):
        """
        :see: `__add__`
        :rtype: Trace
        """
        operator.add(self, other)
        return self

    def __len__(self):
        """
        The number of spans in this trace instance.

        :rtype: int
        """
        return len(self.spans)

    def __sub__(self, other):
        """
        Remove the span from the current Trace and attempt to make it not the
            current_span.

        :param other: The span to remove.
        :type other: Span
        """
        if not isinstance(other, Span):
            raise TypeError('{other} is not an instance of Span'.format(
                other=other))

        self._spans.remove(other)
        self._remove_span_from_span_tree(other)

    def __isub__(self, other):
        """
        :see: `__sub__`
        :rtype: Trace
        """
        operator.sub(self, other)
        return self

    def __iter__(self):
        """
        Iterate over all spans within this trace instance

        :rtype: Trace
        """
        for span in self.spans:
            yield span

    def __getitem__(self, item):
        """
        Get a span from this trace based on various criteria:

        1. slice(datetime.datetime/None, datetime.datetime/None, whatever):
            Find spans contained entirely within the date range. None = ignore.
        2. slice(float, float):
            Find spans contained entirely within the floating point timestamp
            range. None = ignore.
        3.  datetime.timedelta:
            Find spans with a duration <= this timedelta.
        """
        if isinstance(item, slice):
            # Get spans that filter as the slice:
            start = item.start
            step = item.step
            stop = item.stop

            if all([
                isinstance(i, (datetime.datetime, type(None)))
                for i in [start, stop]]
            ):
                # Find all spans where (span.start>=start) and (stop<span.stop)
                spans = find_spans_in_datetime_range(self.spans, from_=start, to_=stop)
                return spans[::step]
            if all([isinstance(i, float) for i in [start, stop]]):
                spans = find_spans_in_float_range(self.spans, from_=start, to_=stop)
                return spans[::step]
            if not all([
                isinstance(i, (int, type(None)))
                for i in [start, stop, step]]
            ):
                raise InvalidSliceError(
                    'Invalid slice {slice}'.format(slice=slice))
        elif isinstance(item, datetime.timedelta):
            # Find all spans that have a duration `<` item
            return find_spans_with_duration_less_than(self.spans, item)

        return self._spans[item]

    @property
    def decorators(self):
        """
        Retrieve a TraceDecorators instance associated to this instance.

        :return: A new Decorators instance.
        :rtype: TraceDecorators
        """
        return TraceDecorators(self)

    def __setitem__(self, index, value):
        """
        Insert the span into this trace's list of spans.

        :param index: index to insert into
        :type index: int
        :param value: Span to insert
        :type value: Span
        """
        if not isinstance(value, Span):
            raise TypeError('Can only insert item of type=Span')
        self._spans[index] = value

    def __delitem__(self, index):
        """
        Delete the span from this trace's list at the given index.

        :param index: index to delete from
        :type index: int
        """
        del self._spans[index]

    def insert(self, index, value):
        'S.insert(index, object) -- insert object before index'
        if not isinstance(value, Span):
            raise TypeError('Can only insert item of type=Span')
        self._spans.insert(index, value)
