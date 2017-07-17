#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import operator
import unittest

from gaesd import SDK, Span, SpanKind
from gaesd.core.utils import DuplicateSpanEntryError, NoDurationError, datetime_to_timestamp


class TestSpanTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)
        self.trace = self.sdk.current_trace

    def test_init(self):
        span_id = Span.new_span_id()

        span = Span(self.trace, span_id)
        self.assertIs(span.trace, self.trace)
        self.assertEqual(span.span_id, span_id)
        self.assertIsNone(span.parent_span_id)
        self.assertEqual(span.name, '')
        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)
        self.assertEqual(span.span_kind, SpanKind.unspecified)
        self.assertEqual(len(span.labels), 0)
        self.assertEqual(span.project_id, self.project_id)

    def test_setters(self):
        span = Span(self.trace, Span.new_span_id())
        self.assertEqual(span.name, '')

        new_name = '1324'
        span.name = new_name
        self.assertEqual(span.name, new_name)

        new_span_kind = SpanKind.client
        span.span_kind = new_span_kind
        self.assertEqual(span.span_kind, new_span_kind)

        new_span_kind = SpanKind.client.value
        span.span_kind = new_span_kind
        self.assertEqual(span.span_kind, SpanKind.client)

        self.assertIsNone(span.parent_span_id)
        new_span = Span(self.trace, Span.new_span_id())
        span.parent_span_id = new_span.span_id
        self.assertIs(span.parent_span_id, new_span.span_id)

        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)

        start_time = datetime.datetime.utcnow()
        span.start_time = start_time
        self.assertEqual(span.start_time, start_time)

        end_time = datetime.datetime.utcnow()
        span.end_time = end_time
        self.assertEqual(span.end_time, end_time)

    def test_export(self):
        parent_span_id = Span.new_span_id()

        e_labels = {'a': '1', 'b': '2', 'c': 'None'}
        span_kind = SpanKind.server

        start_time = datetime.datetime(2017, 1, 20)
        end_time = datetime.datetime(2017, 1, 23)
        e_start_time = datetime_to_timestamp(start_time)
        e_end_time = datetime_to_timestamp(end_time)

        span_id = Span.new_span_id()
        span = Span(
            self.trace, span_id, parent_span_id=parent_span_id, name='child',
            span_kind=span_kind, start_time=start_time, end_time=end_time, labels=e_labels,
        )

        for data in [span.export(), json.loads(span.json)]:
            self.assertIsInstance(data, {}.__class__)
            self.assertSetEqual(
                set(data.keys()),
                set(['spanId', 'kind', 'name', 'startTime', 'endTime', 'parentSpanId', 'labels'])
            )
            self.assertEqual(data['spanId'], str(span_id))
            self.assertEqual(data['kind'], span_kind.value)
            self.assertEqual(data['name'], 'child')
            self.assertEqual(data['startTime'], e_start_time)
            self.assertEqual(data['endTime'], e_end_time)
            self.assertEqual(data['parentSpanId'], str(parent_span_id))
            self.assertEqual(data['labels'], e_labels)

    def test_context_manager(self):
        parent_span_id = Span.new_span_id()

        span = Span(self.trace, parent_span_id, name='parent')
        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)

        with span as s:
            self.assertIs(span, s)
            start_time = span.start_time
            self.assertIsNotNone(start_time)
            self.assertIsNone(span.end_time)

        self.assertIsNotNone(span.start_time)
        self.assertEqual(span.start_time, start_time)
        self.assertIsNotNone(span.end_time)

    def test_context_manager_raises_DuplicateSpanEntryError(self):
        span = Span(self.trace, Span.new_span_id(), name='bob')

        with span as s:
            try:
                with s:
                    pass
            except DuplicateSpanEntryError as e:
                self.assertIs(e.span, span)
            else:
                self.assertFalse()

    def test_add_raises_ValueError(self):
        span_id = Span.new_span_id()

        span = Span(self.trace, span_id)
        self.assertRaises(TypeError, operator.add, span, 1)

    def test_add_span(self):
        span_id = Span.new_span_id()
        parent_span = Span(self.trace, span_id)

        new_span_id = Span.new_span_id()
        span = Span(self.trace, new_span_id)

        operator.add(parent_span, span)
        self.assertIs(span.parent_span, parent_span)

    def test_rshift_span(self):
        span_id = Span.new_span_id()
        span_a = Span(self.trace, span_id)

        new_span_id = Span.new_span_id()
        span_b = Span(self.trace, new_span_id)

        operator.rshift(span_a, span_b)
        self.assertIs(span_a.parent_span, span_b)

    def test_rshift_trace(self):
        trace = self.sdk.current_trace
        other_trace = self.sdk.current_trace
        span = Span(other_trace, Span.new_span_id())

        operator.rshift(span, trace)
        self.assertIn(span, trace.spans)
        self.assertIn(span.span_id, trace.span_ids)

    def test_rshift_raises(self):
        span_id = Span.new_span_id()
        span_a = Span(self.trace, span_id)

        self.assertRaises(TypeError, operator.rshift, span_a, 1)

    def test_lshift_span(self):
        span_id = Span.new_span_id()
        span_a = Span(self.trace, span_id)

        new_span_id = Span.new_span_id()
        span_b = Span(self.trace, new_span_id)

        operator.lshift(span_b, span_a)
        self.assertIs(span_a.parent_span, span_b)

    def test_lshift_trace(self):
        trace = self.sdk.current_trace
        span = trace.span()

        operator.lshift(span, trace)
        self.assertNotIn(span, trace.spans)
        self.assertNotIn(span.span_id, trace.span_ids)

    def test_lshift_raises(self):
        trace = self.sdk.current_trace
        span = trace.span()

        self.assertRaises(TypeError, operator.lshift, span, 1)

    def test_span(self):
        trace = self.sdk.current_trace
        span = trace.span()
        self.assertIsNone(span.parent_span_id)
        self.assertIn(span, trace.spans)

        nested_span = span.span()
        self.assertEqual(nested_span.parent_span_id, span.span_id)
        self.assertIn(nested_span, trace.spans)

    def test_iter(self):
        trace = self.sdk.current_trace

        e_spans = [trace.span() for _ in range(10)]
        self.assertEqual(len(self.trace), 10)

        spans = [span for span in iter(trace)]
        self.assertEqual(e_spans, spans)

    def test_str(self):
        trace = self.sdk.current_trace
        span = trace.span()
        self.assertIsNotNone(str(span))

    def test_has_duration(self):
        trace = self.sdk.current_trace
        span = trace.span()
        self.assertFalse(span.has_duration)

        span.start_time = datetime.datetime.utcnow()
        self.assertFalse(span.has_duration)

        span.end_time = datetime.datetime.utcnow()
        self.assertTrue(span.has_duration)

        span.start_time = 123
        self.assertFalse(span.has_duration)

        span.start_time = datetime.datetime.utcnow()
        span.end_time = 456
        self.assertFalse(span.has_duration)

    def test_duration_raises(self):
        trace = self.sdk.current_trace
        span = trace.span()
        self.assertRaises(NoDurationError, getattr, span, 'duration')

        span.start_time = datetime.datetime.utcnow()
        self.assertRaises(NoDurationError, getattr, span, 'duration')

        span.end_time = datetime.datetime.utcnow()
        self.assertIsNotNone(span.duration)

        span.start_time = None
        self.assertRaises(NoDurationError, getattr, span, 'duration')


if __name__ == '__main__':
    unittest.main()
