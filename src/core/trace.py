#!/usr/bin/env python
# -*- coding: latin-1 -*-

import json
import uuid

from .span import Span


class Trace(object):
    def __init__(self, sdk, trace_id=None):
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id if trace_id is not None else self.new_trace_id
        self._root_span_id = None

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
    def project_id(self):
        return self.sdk.project_id

    def span(self, parent_span=None, **kwargs):
        if not self.spans:
            parent_span = parent_span or self.root_span_id

        span = Span(self, Span.new_span_id(), parent_span, **kwargs)
        self._spans.append(span)
        return span

    def export(self):
        return {
            'projectId': str(self.project_id),
            'traceId': str(self.trace_id),
            'spans': [i for i in [span.json for span in self.spans] if i],
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        return self

    def __exit__(self, t, val, tb):
        # TODO: Fire off this `Trace and it's Spans` to the stack-driver API:
        self.end()

    def end(self):
        self.sdk.patch_trace(self)
