#!/usr/bin/env python
# -*- coding: latin-1 -*-

import itertools
import json
import uuid

from src import Span


class Trace(object):
    def __init__(self, sdk, trace_id=None):
        self._sdk = sdk
        self._spans = []
        self._trace_id = trace_id or uuid.uuid4().hex
        self._span_ids = itertools.count(1)

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

    def span(self, parent_span=None):
        span = Span(self, self._span_ids.next(), parent_span)
        self._spans.append(span)
        return span

    def export(self):
        return {
            'projectId': self.project_id,
            'traceId': self.trace_id,
            'spans': [i for i in [span.json for span in self.spans] if i],
        }

    @property
    def json(self):
        return json.dumps(self.export())

    def __enter__(self):
        return self

    def __exit__(self, t, val, tb):
        # TODO: Fire off this `Trace and it's Spans` to the stack-driver API:
        pass
