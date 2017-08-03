#!/usr/bin/env python
# -*- coding: latin-1 -*-

import operator
import unittest
import uuid

from mock import Mock, patch
from nose_parameterized import parameterized

from gaesd import SDK, Span, Trace
from gaesd.core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher


def raise_exc():
    raise Exception('bang!')


class TestSDKTestCase(unittest.TestCase):
    def tearDown(self):
        SDK.clear()

    @parameterized.expand([
        (True, False),
        (True, True),
        (True, lambda: True),
        (True, lambda: False),
        (True, lambda: raise_exc()),
        (False, False),
        (False, True),
        (False, lambda: True),
        (False, lambda: False),
        (False, lambda: raise_exc()),
    ])
    def test_init(self, auto, enabler):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=auto, enabler=enabler)
        self.assertEqual(sdk.project_id, project_id)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(sdk.dispatcher.auto, auto)

        def is_enabled(e):
            try:
                return bool(e())
            except:
                return bool(e)

        self.assertEqual(sdk.is_enabled, is_enabled(enabler))

    def test_current_trace_creates(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_current_trace_finds(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        new_trace = sdk.current_trace
        self.assertIs(trace, new_trace)

    def test_trace_appends(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        new_trace = sdk.trace(trace_id=Trace.new_trace_id())
        self.assertIsNot(trace, new_trace)
        self.assertEqual(len(sdk._trace_ids), 2)
        self.assertIs(sdk._context.traces[0], trace)
        self.assertIs(sdk._context.traces[1], new_trace)

    @patch('gaesd.sdk.GoogleApiClientDispatcher.patch_trace')
    def test_patch_trace(self, mock_dispatcher):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace

        sdk.patch_trace(trace)

        mock_dispatcher.assert_called_with(trace)
        mock_dispatcher.assert_called_once()

    def test_duplicate_trace_id(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        trace_id = sdk._trace_ids[0]
        self.assertRaises(ValueError, sdk.trace, trace_id=trace_id)

    def test_span_creates_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_span_finds_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertIs(span.trace, trace)

    def test_span_uses_parent_span(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        parent_span = Span.new(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(span.parent_span_id, parent_span.span_id)

    def test_nested_span_uses_parent_span_if_provided(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        parent_span = Span.new(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(span.parent_span_id, parent_span.span_id)

        nested_span = sdk.span(parent_span=span)
        self.assertIsInstance(nested_span, Span)
        self.assertEqual(nested_span.parent_span_id, span.span_id)

    def test_nested_span_uses_parent_span_implicitly(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertIsNone(span.parent_span_id)

        nested_span = sdk.span()
        self.assertIsInstance(nested_span, Span)
        self.assertEqual(nested_span.parent_span_id, span.span_id)

    def test_clear(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._context.traces), 0)

        sdk._context.traces.append(1)
        self.assertEqual(len(sdk._context.traces), 1)

        sdk.clear()
        self.assertEqual(len(sdk._context.traces), 0)

    def test_default_dispatcher(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        self.assertIsInstance(sdk.dispatcher, GoogleApiClientDispatcher)

    def test_current_span_creates_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_current_span_finds_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(trace.spans), 0)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertIs(span.trace, trace)
        self.assertEqual(len(trace.spans), 1)

    def test_new_span_creates_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        span = sdk.new_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)

    def test_new_span_finds_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)

        span = sdk.new_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertIs(span.trace, trace)

    def test_len(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
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
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        self.assertRaises(TypeError, operator.add, sdk, 123)

    def test_add_span(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)
        trace = sdk.current_trace  # NOQA: F841
        other_trace = sdk.trace()
        span = Span.new(other_trace, Span.new_span_id())

        operator.add(sdk, span)
        self.assertIn(span, other_trace.spans)

    def test_add_trace(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = Trace.new(sdk, uuid.uuid4().hex)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

    def test_add_trace_invalid_trace_id(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace_id = uuid.uuid4().hex
        trace = Trace.new(sdk, trace_id)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

        self.assertRaises(ValueError, operator.add, sdk, trace)

    def test_str(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertIsNotNone(str(sdk))

    def test_getitem(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertRaises(IndexError, operator.getitem, sdk, 0)

        current_trace = sdk.current_trace
        self.assertIs(operator.getitem(sdk, 0), current_trace)

    @parameterized.expand([
        (True, True),
        (False, False),
        (Mock(return_value=True), True),
        (Mock(return_value=False), False)
    ])
    def test_enabler(self, enabler, e_enabled):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        is_enabled = sdk.is_enabled
        self.assertTrue(is_enabled)

        sdk.set_enabler(False)

        is_enabled = sdk.is_enabled
        self.assertFalse(is_enabled)

        sdk.set_enabler(enabler)

        is_enabled = sdk.is_enabled
        self.assertEqual(e_enabled, is_enabled)
        if isinstance(enabler, Mock):
            enabler.assert_called_once()

    def test_enabler_raise_ValueError(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)

        self.assertRaises(ValueError, sdk.set_enabler, None)

    def test_call_invokes_dispatcher(self):
        project_id = 'my-project'
        sdk = SDK.new(project_id=project_id, auto=False)
        mock_dispatcher = Mock()
        sdk._context.dispatcher = mock_dispatcher
        sdk()
        mock_dispatcher.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
