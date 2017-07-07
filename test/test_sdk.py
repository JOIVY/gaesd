#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import json
import unittest
from types import DictType

from mock import patch

from core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from core.dispatchers.rest_dispatcher import SimpleRestDispatcher
from core.span import Span, SpanKind
from core.trace import Trace
from core.utils import datetime_to_timestamp
from sdk import SDK


class TestDispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)

    def test_init(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)

        self.assertEqual(dispatcher.sdk, self.sdk)
        self.assertTrue(dispatcher.auto)

    def test_setters(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        dispatcher.auto = False
        self.assertFalse(dispatcher.auto)

    @patch('core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patchTraces(trace)
        mock_dispatch.assert_called_once_with([trace])

    @patch('core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=False)
        self.assertFalse(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patchTraces(trace)
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

    @patch('sdk.SDK.patch_trace')
    def test_patch_trace(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        trace.end()
        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)

    def test_export_empty_spans(self):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        for data in [trace.export(), json.loads(trace.json)]:
            self.assertIsInstance(data, DictType)
            self.assertSetEqual(
                set(data.keys()),
                {'projectId', 'traceId', 'spans'}
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

    @patch('sdk.SDK.patch_trace')
    def test_context_manager(self, mock_patch_trace):
        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        with trace as t:
            self.assertIs(trace, t)
            mock_patch_trace.assert_not_called()

        mock_patch_trace.assert_called_once()
        mock_patch_trace.assert_called_with(trace)


class TestSpanCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        sdk = SDK(project_id=self.project_id, auto=False)
        self.trace = sdk.current_trace

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

    def test_export(self):
        parent_span_id = Span.new_span_id()
        parent_span = Span(self.trace, parent_span_id, name='parent')

        e_labels = [1, 2, 3]
        span_kind = SpanKind.server

        start_time = datetime.datetime(2017, 1, 20)
        end_time = datetime.datetime(2017, 1, 23)
        e_start_time = datetime_to_timestamp(start_time)
        e_end_time = datetime_to_timestamp(end_time)

        span_id = Span.new_span_id()
        span = Span(self.trace, span_id, parent_span=parent_span, name='child',
            span_kind=span_kind, start_time=start_time, end_time=end_time, labels=e_labels)

        for data in [span.export(), json.loads(span.json)]:
            self.assertIsInstance(data, DictType)
            self.assertSetEqual(
                set(data.keys()),
                {'spanId', 'kind', 'name', 'startTime', 'endTime', 'parentSpanId', 'labels'}
            )
            self.assertEqual(data['spanId'], span_id)
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


if __name__ == '__main__':
    unittest.main()
