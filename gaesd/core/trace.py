#!/usr/bin/env python
# -*- coding: latin-1 -*-

import json
import operator
import uuid

from .span import Span

__all__ = ['Trace']


class Trace(object):
    def __init__(self, sdk, trace_id=None, root_span_id=None):
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id if trace_id is not None else self.new_trace_id()
        self._root_span_id = root_span_id

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

    @property
    def sdk(self):
        return self._sdk

    @property
    def spans(self):
        return self._spans

    @property
    def current_span(self):
        return self.spans[-1] if self.spans else self.sdk.new_span

    @property
    def span_ids(self):
        return [span.span_id for span in self._spans]

    @property
    def project_id(self):
        return self.sdk.project_id

    def span(self, parent_span=None, **kwargs):
        default_parent_span_id = self.root_span_id if not self.spans else None
        parent_span_id = parent_span.span_id if parent_span is not None else default_parent_span_id

        span = Span(self, Span.new_span_id(), parent_span_id, **kwargs)
        self._spans.append(span)
        return span

    def export(self):
        return {
            'projectId': str(self.project_id),
            'traceId': str(self.trace_id),
            'spans': [i for i in self.spans if i is not None],
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        return self

    def __exit__(self, t, val, tb):
        self.end()

    def end(self):
        self.sdk.patch_trace(self)

    def __add__(self, other):
        if not isinstance(other, Span):
            raise TypeError('{0} is not an instance of Span'.format(other))

        span_id = other.span_id
        if span_id in self.span_ids:
            raise ValueError('span_id {0} already present in this Trace'.format(span_id))

        self._spans.append(other)

    def __iadd__(self, other):
        operator.add(self, other)
        return self

    def __len__(self):
        return len(self.spans)

    def __sub__(self, other):
        if not isinstance(other, Span):
            raise TypeError('{0} is not an instance of Span'.format(other))

        self._spans.remove(other)

    def __isub__(self, other):
        operator.sub(self, other)
        return self

    def __iter__(self):
        for span in self.spans:
            yield span
