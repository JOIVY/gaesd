#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import operator
import uuid
from types import NoneType

from .span import Span
from .utils import InvalidSliceError, find_spans_in_datetime_range, find_spans_in_float_range, \
    find_spans_with_duration

__all__ = ['Trace']


class Trace(object):
    def __init__(self, sdk, trace_id=None, root_span_id=None):
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id if trace_id is not None else self.new_trace_id()
        self._root_span_id = root_span_id
        self._span_tree = []

    def __str__(self):
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
        return self._spans

    def set_default(self, **kwargs):
        if 'trace_id' in kwargs:
            self._trace_id = kwargs['trace_id']
        if 'root_span_id' in kwargs:
            self._root_span_id = kwargs['root_span_id']

    @property
    def current_span(self):
        return self._span_tree[-1] if self._span_tree else self.sdk.new_span

    @property
    def span_ids(self):
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

    def span(self, parent_span=None, **kwargs):
        parent_span_id = parent_span.span_id if parent_span is not None else self.root_span_id

        span = Span(self, Span.new_span_id(), parent_span_id, **kwargs)
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
        self.sdk.patch_trace(self)
        self._remove_span_from_span_tree(span)

    def __add__(self, other):
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
            if not all([isinstance(i, int) for i in [start, stop, step]]):
                raise InvalidSliceError('Invalid slice {slice}'.format(slice=slice))
        elif isinstance(item, datetime.timedelta):
            # Find all spans that have a duration less than item
            spans = find_spans_with_duration(self.spans, item)
            return spans

        return self._spans[item]
