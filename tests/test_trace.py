#!/usr/bin/env python
# -*- coding: latin-1 -*-

import json
import operator
import unittest

from mock import patch

from gaesd.core.span import Span
from gaesd.core.trace import Trace
from gaesd.sdk import SDK


class TestTraceCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)

    def test_init(self):
        trace_id = Trace.new_trace_id()

        trace = Trace(self.sdk, trace_id=trace_id, root_span_id=123)

        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(trace.sdk, self.sdk)
        self.assertEqual(trace.spans, [])
        self.assertEqual(self.sdk.project_id, trace.project_id)
        self.assertEqual(trace.root_span_id, 123)

    @patch('gaesd.sdk.SDK.patch_trace')
    def test_patch_trace(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        trace.end()
        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)

    def test_setters(self):
        trace_id = Trace.new_trace_id()

        trace = Trace(self.sdk, trace_id=trace_id, root_span_id=123)
        self.assertEqual(trace.root_span_id, 123)

        trace.root_span_id = 456
        self.assertEqual(trace.root_span_id, 456)

    def test_export_empty_spans(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        for data in [trace.export(), json.loads(trace.json)]:
            self.assertIsInstance(data, {}.__class__)
            self.assertSetEqual(
                set(data.keys()),
                set(['projectId', 'traceId', 'spans'])
            )
            self.assertEqual(data['projectId'], self.sdk.project_id)
            self.assertEqual(data['traceId'], trace_id)
            self.assertEqual(data['spans'], [])

    def test_span_no_parent(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)
        parent_span = None

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertIsNone(span.parent_span_id)

    def test_span_parent(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)
        parent_span = Span(trace, Span.new_span_id())

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertIs(span.parent_span_id, parent_span.span_id)

    @patch('gaesd.sdk.SDK.patch_trace')
    def test_context_manager(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        with trace as t:
            self.assertIs(trace, t)
            mock_patch_trace.assert_not_called()

        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)

    def test_len(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        self.assertEqual(len(trace), 0)
        self.assertFalse(trace)

        l = 10
        trace._spans = range(l)
        self.assertEqual(len(trace), l)

    def test_add_raises_ValueError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        span = trace.span()
        self.assertIn(span, trace.spans)

        self.assertRaises(ValueError, operator.add, trace, span)

    def test_add_raises_TypeError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        self.assertRaises(TypeError, operator.add, trace, 1)

    def test_add_span_adds_at_top_level(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span_a = Span(trace, span_id)

        operator.add(trace, span_a)
        self.assertEqual(len(trace), 1)

        new_span_id = Span.new_span_id()
        span_b = Span(trace, new_span_id)
        operator.add(trace, span_b)
        self.assertEqual(len(trace), 2)

    def test_sub_raises(self):
        trace = self.sdk.current_trace

        self.assertRaises(TypeError, operator.sub, trace, 1)

    def test_sub_not_in_trace_raises(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span = Span(trace, span_id)

        self.assertRaises(ValueError, operator.sub, trace, span)

    def test_sub(self):
        trace = self.sdk.current_trace
        span = trace.span()

        operator.sub(trace, span)
        self.assertNotIn(span, trace.spans)

    def test_iter(self):
        for _ in range(10):
            self.sdk.trace()
        self.assertEqual(len(self.sdk), 10)

        trace_ids = [trace.trace_id for trace in iter(self.sdk)]
        self.assertEqual(self.sdk._trace_ids, trace_ids)

    def test_str(self):
        trace = self.sdk.current_trace
        self.assertIsNotNone(str(trace))


if __name__ == '__main__':
    unittest.main()
