#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import operator
import unittest
import uuid

from mock import patch

from gaesd.core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from gaesd.core.dispatchers.rest_dispatcher import SimpleRestDispatcher
from gaesd.core.span import Span, SpanKind
from gaesd.core.trace import Trace
from gaesd.core.utils import datetime_to_timestamp
from gaesd.sdk import SDK


class TestDispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)
        self.assertIsInstance(self.sdk.dispatcher, GoogleApiClientDispatcher)

    def test_init(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)

        self.assertEqual(dispatcher.sdk, self.sdk)
        self.assertTrue(dispatcher.auto)

    def test_setters(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        dispatcher.auto = False
        self.assertFalse(dispatcher.auto)

    @patch('gaesd.core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_called_once_with([trace])

    @patch('gaesd.core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=False)
        self.assertFalse(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_not_called()


class TestTraceCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)

    def test_init(self):
        trace_id = Trace.new_trace_id()

        trace = Trace(self.sdk, trace_id=trace_id)

        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(trace.sdk, self.sdk)
        self.assertEqual(trace.spans, [])
        self.assertEqual(self.sdk.project_id, trace.project_id)
        self.assertIsNone(trace.root_span_id)

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
        self.assertIs(span.parent_span, parent_span)

    def test_span_parent(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)
        parent_span = Span(trace, Span.new_span_id())

        span = trace.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(trace.spans, [span])
        self.assertIs(span.parent_span, parent_span)

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

        span = trace.span(trace)
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


class TestSpanCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)
        self.trace = self.sdk.current_trace

    def test_init(self):
        span_id = Span.new_span_id()

        span = Span(self.trace, span_id)
        self.assertIs(span.trace, self.trace)
        self.assertEqual(span.span_id, span_id)
        self.assertIsNone(span.parent_span)
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

        self.assertIsNone(span.parent_span)
        new_span = Span(self.trace, Span.new_span_id())
        span.parent_span = new_span
        self.assertIs(span.parent_span, new_span)

    def test_export(self):
        parent_span_id = Span.new_span_id()
        parent_span = Span(self.trace, parent_span_id, name='parent')

        e_labels = ['1', '2', '3']
        span_kind = SpanKind.server

        start_time = datetime.datetime(2017, 1, 20)
        end_time = datetime.datetime(2017, 1, 23)
        e_start_time = datetime_to_timestamp(start_time)
        e_end_time = datetime_to_timestamp(end_time)

        span_id = Span.new_span_id()
        span = Span(self.trace, span_id, parent_span=parent_span, name='child',
            span_kind=span_kind, start_time=start_time, end_time=end_time, labels=e_labels)

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
        self.assertIsNone(span.parent_span)
        self.assertIn(span, trace.spans)

        nested_span = span.span()
        self.assertEqual(nested_span.parent_span, span)
        self.assertIn(nested_span, trace.spans)

    def test_iter(self):
        trace = self.sdk.current_trace

        e_spans = [trace.span() for _ in range(10)]
        self.assertEqual(len(self.trace), 10)

        spans = [span for span in iter(trace)]
        self.assertEqual(e_spans, spans)


class TestSDKTestCase(unittest.TestCase):
    def tearDown(self):
        SDK.clear()

    def test_init(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(sdk.project_id, project_id)
        self.assertEqual(len(sdk._trace_ids), 0)

    def test_current_trace_creates(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_current_trace_finds(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        new_trace = sdk.current_trace
        self.assertIs(trace, new_trace)

    def test_trace_appends(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        new_trace = sdk.trace(trace_id=Trace.new_trace_id())
        self.assertIsNot(trace, new_trace)
        self.assertEqual(len(sdk._trace_ids), 2)
        self.assertIs(sdk._data.traces[0], trace)
        self.assertIs(sdk._data.traces[1], new_trace)

    @patch('gaesd.sdk.GoogleApiClientDispatcher.patch_trace')
    def test_patch_trace(self, mock_dispatcher):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        trace = sdk.current_trace

        sdk.patch_trace(trace)

        mock_dispatcher.assert_called_with(trace)
        mock_dispatcher.assert_called_once()

    def test_duplicate_trace_id(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        trace_id = sdk._trace_ids[0]
        self.assertRaises(ValueError, sdk.trace, trace_id=trace_id)

    def test_span_creates_trace(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_span_finds_trace(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertIs(span.trace, trace)

    def test_span_uses_parent_span(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        parent_span = Span(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertIs(span.parent_span, parent_span)

    def test_nested_span_uses_parent_span_if_provided(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        parent_span = Span(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertIs(span.parent_span, parent_span)

        nested_span = sdk.span(parent_span=span)
        self.assertIsInstance(nested_span, Span)
        self.assertIs(nested_span.parent_span, span)

    def test_nested_span_uses_parent_span_implicitly(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertIsNone(span.parent_span)

        nested_span = sdk.span()
        self.assertIsInstance(nested_span, Span)
        self.assertIs(nested_span.parent_span, span)

    def test_clear(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._data.traces), 0)

        sdk._data.traces.append(1)
        self.assertEqual(len(sdk._data.traces), 1)

        sdk.clear()
        self.assertEqual(len(sdk._data.traces), 0)

    def test_default_dispatcher(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)

        self.assertIsInstance(sdk._dispatcher, GoogleApiClientDispatcher)

    def test_current_span_creates_trace(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_current_span_finds_trace(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertIs(span.trace, trace)

    def test_len(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        for _ in range(10):
            sdk.trace()
        self.assertEqual(len(sdk), 11)

    def test_add_raises(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        self.assertRaises(TypeError, operator.add, sdk, 123)

    def test_add_span(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        other_trace = sdk.trace()
        span = Span(other_trace, Span.new_span_id())

        operator.add(sdk, span)
        self.assertIn(span, other_trace.spans)

    def test_add_trace(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = Trace(sdk, uuid.uuid4().hex)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

    def test_add_trace_invalid_trace_id(self):
        project_id = 'joivy-dev5'
        sdk = SDK(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace_id = uuid.uuid4().hex
        trace = Trace(sdk, trace_id)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

        self.assertRaises(ValueError, operator.add,sdk, trace)


if __name__ == '__main__':
    unittest.main()
