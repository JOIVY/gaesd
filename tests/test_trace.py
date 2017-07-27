#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import itertools
import json
import operator
import unittest

from mock import patch

from gaesd import InvalidSliceError, SDK, Span, Trace
from gaesd.core.utils import datetime_to_float


class TestTraceTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK.new(project_id=self.project_id, auto=False)

    def test_init(self):
        trace_id = Trace.new_trace_id()

        trace = Trace.new(self.sdk, trace_id=trace_id, root_span_id=123)

        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(trace.sdk, self.sdk)
        self.assertEqual(trace.spans, [])
        self.assertEqual(self.sdk.project_id, trace.project_id)
        self.assertEqual(trace.root_span_id, 123)

    @patch('gaesd.sdk.SDK.patch_trace')
    def test_patch_trace(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        trace.end()
        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)

    def test_setters(self):
        trace_id = Trace.new_trace_id()

        trace = Trace.new(self.sdk, trace_id=trace_id, root_span_id=123)
        self.assertEqual(trace.root_span_id, 123)

        trace.root_span_id = 456
        self.assertEqual(trace.root_span_id, 456)

        trace.trace_id = 789
        self.assertEqual(trace.trace_id, 789)

    def test_set_default(self):
        current_trace = self.sdk.current_trace
        self.assertNotEqual(current_trace.trace_id, 123)
        self.assertNotEqual(current_trace.root_span_id, 456)

        self.sdk.current_trace.set_default(trace_id=123, root_span_id=456)
        self.assertIs(current_trace, self.sdk.current_trace)
        self.assertEqual(self.sdk.current_trace.trace_id, 123)
        self.assertEqual(self.sdk.current_trace.root_span_id, 456)

    def test_export_empty_spans(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

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
        trace = Trace.new(self.sdk, trace_id=trace_id)
        parent_span = None

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertIsNone(span.parent_span_id)

    def test_span_no_parent_with_root_span_id(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id, root_span_id=123)
        parent_span = None

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertEqual(span.parent_span_id, 123)

    def test_span_parent(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)
        parent_span = Span.new(trace, Span.new_span_id())

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertIs(span.parent_span_id, parent_span.span_id)

    @patch('gaesd.sdk.SDK.patch_trace')
    def test_context_manager(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        with trace as t:
            self.assertIs(trace, t)
            mock_patch_trace.assert_not_called()

        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)

    def test_len(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        self.assertEqual(len(trace), 0)
        self.assertFalse(trace)

        l = 10
        trace._spans = range(l)
        self.assertEqual(len(trace), l)

    def test_add_raises_ValueError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        span = trace.span()
        self.assertIn(span, trace.spans)

        self.assertRaises(ValueError, operator.add, trace, span)

    def test_add_raises_TypeError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        self.assertRaises(TypeError, operator.add, trace, 1)

    def test_add_span_adds_at_top_level(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span_a = Span.new(trace, span_id)

        operator.add(trace, span_a)
        self.assertEqual(len(trace), 1)

        new_span_id = Span.new_span_id()
        span_b = Span.new(trace, new_span_id)
        operator.add(trace, span_b)
        self.assertEqual(len(trace), 2)

    def test_sub_raises(self):
        trace = self.sdk.current_trace

        self.assertRaises(TypeError, operator.sub, trace, 1)

    def test_sub_not_in_trace_raises(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span = Span.new(trace, span_id)

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

    def test_getitem_integer(self):
        trace = self.sdk.current_trace
        self.assertRaises(IndexError, operator.getitem, trace, 0)

        current_span = trace.current_span
        self.assertIs(operator.getitem(trace, 0), current_span)

        spans = [current_span] + [trace.span() for _ in range(9)]
        trace_spans = [trace[i] for i in range(10)]

        self.assertEqual(spans, trace_spans)
        self.assertRaises(IndexError, operator.getitem, trace, 11)

    def test_getitem_timedelta(self):
        trace = self.sdk.current_trace
        td = datetime.timedelta(seconds=1)
        self.assertEqual(operator.getitem(trace, td), [])

        start_time = datetime.datetime.utcnow()

        spans = []

        for index, _ in enumerate(range(10)):
            end_time = start_time + datetime.timedelta(seconds=index + 1)
            spans.append(trace.span(start_time=start_time, end_time=end_time))

        for t in range(10):
            trace_spans = trace[datetime.timedelta(seconds=t)]
            self.assertEqual(spans[:t], trace_spans)

    def test_getitem_float(self):
        trace = self.sdk.current_trace
        td = datetime.timedelta(seconds=1)
        self.assertEqual(operator.getitem(trace, td), [])

        start_time = datetime.datetime.utcnow()

        spans = []
        end_times = []

        for index, _ in enumerate(range(10)):
            end_time = start_time + datetime.timedelta(seconds=index + 1)
            end_times.append(datetime_to_float(end_time))
            spans.append(trace.span(start_time=start_time, end_time=end_time))

        start = datetime_to_float(start_time)

        for t in range(10):
            stop = end_times[t]
            trace_spans = trace[start:stop]
            self.assertEqual(spans[:t], trace_spans)

    def test_getitem_slice_raises(self):
        trace = self.sdk.current_trace
        self.assertRaises(InvalidSliceError, operator.getitem, trace, slice(1.0, 2, 3))
        self.assertRaises(InvalidSliceError, operator.getitem, trace, slice('x', 1, 2))
        self.assertRaises(InvalidSliceError, operator.getitem, trace, slice(0, 'y', 2))

    def test_getitem_datetime_only_upper_bound(self):
        trace = self.sdk.current_trace
        all_start_time = datetime.datetime.utcnow()

        all_spans = []
        start_times = []
        end_times = []

        for index, _ in enumerate(range(10)):
            start_time = all_start_time + datetime.timedelta(seconds=index)
            start_times.append(start_time)
            end_time = start_time + datetime.timedelta(seconds=5)
            end_times.append(end_time)
            all_spans.append(trace.span(start_time=start_time, end_time=end_time))

        for i in range(10):
            traces = trace[None: end_times[i]]
            self.assertEqual(len(traces), i)
            self.assertEqual(traces, all_spans[:i])

        traces = trace[None: end_times[i] + datetime.timedelta(seconds=11)]
        self.assertEqual(len(traces), 10)

    def test_getitem_datetime_only_lower_bound(self):
        trace = self.sdk.current_trace

        all_start_time = datetime.datetime.utcnow()
        all_spans = []
        start_times = []
        end_times = []

        for index, _ in enumerate(range(10)):
            start_time = all_start_time + datetime.timedelta(seconds=index)
            start_times.append(start_time)
            end_time = start_time + datetime.timedelta(seconds=5)
            end_times.append(end_time)
            all_spans.append(trace.span(start_time=start_time, end_time=end_time))

        for i in range(10):
            traces = trace[start_times[i]:]
            self.assertEqual(len(traces), 10 - i)

    def test_getitem_datetime_both_bounds(self):
        trace = self.sdk.current_trace

        all_start_time = datetime.datetime.utcnow()
        all_spans = []
        start_times = []
        end_times = []

        for index, _ in enumerate(range(10)):
            start_time = all_start_time + datetime.timedelta(seconds=index)
            start_times.append(start_time)
            end_time = start_time + datetime.timedelta(seconds=5)
            end_times.append(end_time)
            all_spans.append(trace.span(start_time=start_time, end_time=end_time))

        index_permutations = list(itertools.permutations(range(10), 2))
        for start, stop in index_permutations:
            expected_spans = all_spans[start:stop]
            vector_start = start_times[start]
            vector_end = end_times[stop]
            found_spans = trace[vector_start:vector_end]

            self.assertEqual(expected_spans, found_spans)

    def test_iadd_raises_ValueError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        span = trace.span()
        self.assertIn(span, trace.spans)

        self.assertRaises(ValueError, operator.iadd, trace, span)

    def test_iadd_raises_TypeError(self):
        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        self.assertRaises(TypeError, operator.iadd, trace, 1)

    def test_iadd_span_adds_at_top_level(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span_a = Span.new(trace, span_id)

        result = operator.iadd(trace, span_a)
        self.assertEqual(len(trace), 1)
        self.assertIsInstance(result, Trace)

        new_span_id = Span.new_span_id()
        span_b = Span.new(trace, new_span_id)

        operator.iadd(trace, span_b)
        self.assertEqual(len(trace), 2)
        self.assertIsInstance(result, Trace)

    def test_isub_raises(self):
        trace = self.sdk.current_trace

        self.assertRaises(TypeError, operator.isub, trace, 1)

    def test_isub_not_in_trace_raises(self):
        trace = self.sdk.current_trace

        span_id = Span.new_span_id()
        span = Span.new(trace, span_id)

        self.assertRaises(ValueError, operator.isub, trace, span)

    def test_isub(self):
        trace = self.sdk.current_trace
        span = trace.span()

        result = operator.isub(trace, span)
        self.assertNotIn(span, trace.spans)
        self.assertIsInstance(result, Trace)


if __name__ == '__main__':
    unittest.main()
