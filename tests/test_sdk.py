#!/usr/bin/env python
# -*- coding: latin-1 -*-

import operator
import unittest
import uuid
from logging import getLogger

from mock import Mock, patch
from nose_parameterized import parameterized

from gaesd import SDK, Span, Trace
from gaesd.core.dispatchers.google_api_client_dispatcher import \
    GoogleApiClientDispatcher
from tests import PROJECT_ID


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
        project_id = PROJECT_ID
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
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

    def test_current_trace_finds(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        new_trace = sdk.current_trace
        self.assertIs(trace, new_trace)

    def test_trace_appends(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        new_trace = sdk.trace(trace_id=Trace.new_trace_id())
        self.assertIsNot(trace, new_trace)
        self.assertEqual(len(sdk._trace_ids), 2)
        self.assertIs(sdk._context.traces[0], trace)
        self.assertIs(sdk._context.traces[1], new_trace)

    def test_new_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = sdk.new_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)
        self.assertTrue(trace in sdk)

    @patch('gaesd.sdk.GoogleApiClientDispatcher.patch_trace')
    def test_patch_trace(self, mock_dispatcher):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace

        sdk.patch_trace(trace)

        mock_dispatcher.assert_called_with(trace)
        mock_dispatcher.assert_called_once()

    def test_duplicate_trace_id(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        trace_id = sdk._trace_ids[0]
        self.assertRaises(ValueError, sdk.trace, trace_id=trace_id)

    def test_span_creates_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

    def test_span_finds_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)
        self.assertIs(span.trace, trace)

    def test_span_uses_parent_span(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        parent_span = Span.new(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(span.parent_span_id, parent_span.span_id)

    def test_nested_span_uses_parent_span_if_provided(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        parent_span = Span.new(sdk.current_trace, Span.new_span_id())

        span = sdk.span(parent_span=parent_span)
        self.assertIsInstance(span, Span)
        self.assertEqual(span.parent_span_id, parent_span.span_id)

        nested_span = sdk.span(parent_span=span)
        self.assertIsInstance(nested_span, Span)
        self.assertEqual(nested_span.parent_span_id, span.span_id)

    def test_nested_span_uses_parent_span_implicitly(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        span = sdk.span()
        self.assertIsInstance(span, Span)
        self.assertIsNone(span.parent_span_id)

        nested_span = sdk.span()
        self.assertIsInstance(nested_span, Span)
        self.assertEqual(nested_span.parent_span_id, span.span_id)

    def test_clear(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._context.traces), 0)

        sdk._context.traces.append(1)
        sdk._context.enabler = 123
        sdk._context.dispatcher = '123'
        sdk._context.loggers = {'a': 1}
        self.assertEqual(len(sdk._context.traces), 1)
        self.assertEqual(sdk._context.loggers, {'a': 1})
        self.assertEqual(sdk._context.enabler, 123)
        self.assertEqual(sdk._context.dispatcher, '123')

        sdk.clear()
        self.assertEqual(len(sdk._context.traces), 0)
        self.assertFalse(sdk._context.enabler)
        self.assertIsNone(sdk._context.dispatcher)
        self.assertEqual(sdk._context.loggers, {'a': 1})

    def test_clear_all_set(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._context.traces), 0)

        sdk._context.traces.append(1)
        sdk._context.enabler = 123
        sdk._context.dispatcher = '123'
        sdk._context.loggers = {'a': 1}

        self.assertEqual(len(sdk._context.traces), 1)
        self.assertEqual(sdk._context.loggers, {'a': 1})
        self.assertEqual(sdk._context.enabler, 123)
        self.assertEqual(sdk._context.dispatcher, '123')

        sdk.clear(traces=True, enabler=True, dispatcher=True, loggers=True)
        self.assertEqual(len(sdk._context.traces), 0)
        self.assertFalse(sdk._context.enabler)
        self.assertIsNone(sdk._context.dispatcher)
        self.assertEqual(sdk._context.loggers, {})

    def test_clear_all_cleared(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._context.traces), 0)

        sdk._context.traces.append(1)
        sdk._context.enabler = 123
        sdk._context.dispatcher = '123'
        sdk._context.loggers = {'a': 1}

        self.assertEqual(len(sdk._context.traces), 1)
        self.assertEqual(sdk._context.loggers, {'a': 1})
        self.assertEqual(sdk._context.enabler, 123)
        self.assertEqual(sdk._context.dispatcher, '123')

        sdk.clear(traces=False, enabler=False, dispatcher=False, loggers=False)
        self.assertEqual(len(sdk._context.traces), 1)
        self.assertEqual(sdk._context.loggers, {'a': 1})
        self.assertEqual(sdk._context.enabler, 123)
        self.assertEqual(sdk._context.dispatcher, '123')

    def test_default_dispatcher(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        self.assertIsInstance(sdk.dispatcher, GoogleApiClientDispatcher)

    def test_current_span_creates_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

    def test_current_span_finds_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)
        self.assertEqual(len(trace.spans), 0)

        span = sdk.current_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)
        self.assertIs(span.trace, trace)
        self.assertEqual(len(trace.spans), 1)

    def test_new_span_creates_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        span = sdk.new_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

    def test_new_span_finds_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk._trace_ids), 0)
        self.assertEqual(len(sdk), 0)

        trace = sdk.current_trace
        self.assertIsInstance(trace, Trace)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)

        span = sdk.new_span
        self.assertIsInstance(span, Span)
        self.assertEqual(len(sdk._trace_ids), 1)
        self.assertEqual(len(sdk), 1)
        self.assertIs(span.trace, trace)

    def test_len(self):
        project_id = PROJECT_ID
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
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        self.assertRaises(TypeError, operator.add, sdk, 123)

    def test_add_span(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)
        trace = sdk.current_trace  # NOQA: F841
        other_trace = sdk.trace()
        span = Span.new(other_trace, Span.new_span_id())

        operator.add(sdk, span)
        self.assertIn(span, other_trace.spans)

    def test_add_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = Trace.new(sdk, uuid.uuid4().hex)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

    def test_add_trace_invalid_trace_id(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace_id = uuid.uuid4().hex
        trace = Trace.new(sdk, trace_id)
        self.assertNotIn(trace, sdk._trace_ids)

        operator.add(sdk, trace)
        self.assertIn(trace.trace_id, sdk._trace_ids)

        self.assertRaises(ValueError, operator.add, sdk, trace)

    def test_str(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertIsNotNone(str(sdk))

    def test_getitem(self):
        project_id = PROJECT_ID
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
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        is_enabled = sdk.is_enabled
        self.assertTrue(is_enabled)
        self.assertTrue(sdk.enabler)

        sdk.enabler = False

        is_enabled = sdk.is_enabled
        self.assertFalse(is_enabled)
        self.assertFalse(sdk.enabler)

        sdk.enabler = enabler

        is_enabled = sdk.is_enabled
        self.assertEqual(e_enabled, is_enabled)
        if isinstance(enabler, Mock):
            enabler.assert_called_once()

    def test_enabler_raise_ValueError(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        def func():
            sdk.enabler = None

        self.assertRaises(ValueError, func)

    def test_call_invokes_dispatcher(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        mock_dispatcher = Mock()
        sdk._context.dispatcher = mock_dispatcher
        sdk()
        mock_dispatcher.assert_called_once_with()

    def test_traces_is_immutable(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        e_traces = [1, 2, 3, 4]
        sdk._context.traces = e_traces
        self.assertEqual(sdk.traces, e_traces)

        traces = sdk.traces
        self.assertIsNot(traces, [1, 2, 3, 4])

        sdk.traces.append(5)
        self.assertEqual(sdk.traces, e_traces)

    def test_insert(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = Trace(sdk, 'my-trace-id')

        sdk.insert(0, trace)
        self.assertEqual(len(sdk), 1)
        self.assertIs(sdk[0], trace)
        self.assertTrue(trace in sdk)

        span = sdk.span()
        self.assertRaises(TypeError, sdk.insert, 0, span)
        self.assertRaises(TypeError, sdk.insert, 0, 1)

    def test_del(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        self.assertRaises(IndexError, operator.__delitem__, sdk, 0)

        trace = sdk.trace()
        self.assertEqual(len(sdk), 1)
        self.assertIs(sdk[0], trace)

        del sdk[0]
        self.assertEqual(len(sdk), 0)
        self.assertFalse(trace in sdk)

    def test_get_and_set_item(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)
        self.assertEqual(len(sdk), 0)

        trace = Trace(sdk, 'my-trace-id')
        self.assertEqual(len(sdk), 0)
        self.assertRaises(IndexError, operator.setitem, sdk, 0, trace)

        trace = sdk.trace()
        self.assertEqual(len(sdk), 1)
        self.assertIs(sdk[0], trace)

        trace_new = Trace(sdk, 'my-trace-id')
        sdk[0] = trace_new
        self.assertIs(sdk[0], trace_new)

        span = sdk.span()
        self.assertRaises(TypeError, operator.setitem, sdk, 0, span)
        self.assertRaises(TypeError, operator.setitem, sdk, 0, 123)
        self.assertRaises(TypeError, operator.setitem, sdk, 0, 'xyz')

    def test_contains_not_span_or_trace(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        for i in [123, None, 'xyz']:
            self.assertFalse(i in sdk)

    def test_contains(self):
        project_id = PROJECT_ID
        sdk = SDK.new(project_id=project_id, auto=False)

        # Create 5 traces each with 10 spans:
        traces = []
        spans = []

        for i in range(5):
            trace = sdk.trace(trace_id='my-trace-id-{i}'.format(i=i))
            spans.extend([trace.span() for _ in range(10)])
            traces.append(trace)

        self.assertEqual(sdk.traces, traces)

        for trace in traces:
            self.assertTrue(trace in sdk)

        for span in spans:
            self.assertTrue(span in sdk)

        # Test for traces and spans not in sdk:
        trace = Trace(sdk, trace_id='my-trace-id')
        self.assertFalse(trace in sdk)

        spans = [trace.span(), Span(trace, span_id=123)]

        for span in spans:
            self.assertFalse(span in sdk)

    def test_set_logging_level(self):
        project_id_1 = 'my-project-1'
        sdk_1 = SDK.new(project_id=project_id_1, auto=False)
        logger_1 = sdk_1.logger

        project_id_2 = 'my-project-2'
        sdk_2 = SDK.new(project_id=project_id_2, auto=False)
        logger_2 = sdk_2.logger

        self.assertNotEqual(logger_1, logger_2)
        self.assertEqual(SDK._context.loggers, sdk_1.loggers)
        self.assertEqual(SDK._context.loggers, sdk_2.loggers)
        self.assertEqual(
            len([i for i in SDK._context.loggers.keys() if
                i.startswith('SDK.')]),
            2)

        new_level = 101
        for logger in SDK._context.loggers.values():
            self.assertNotEqual(logger.level, new_level)

        SDK.set_logging_level(level=new_level)
        for logger in SDK._context.loggers.values():
            self.assertEqual(logger.level, new_level)

    def test_set_logging_level_with_prefix(self):
        project_id_1 = 'my-project-1'
        sdk_1 = SDK.new(project_id=project_id_1, auto=False)
        SDK.clear(loggers=True)
        logger_1 = sdk_1.logger

        project_id_2 = 'my-project-2'
        sdk_2 = SDK.new(project_id=project_id_2, auto=False)
        logger_2 = sdk_2.logger

        self.assertNotEqual(logger_1, logger_2)
        self.assertEqual(SDK._context.loggers, sdk_1.loggers)
        self.assertEqual(SDK._context.loggers, sdk_2.loggers)
        self.assertEqual(
            len([i for i in SDK._context.loggers.keys() if
                i.startswith('SDK.')]),
            2)

        SDK._context.loggers['xxx.yyy'] = getLogger('xxx')
        SDK._context.loggers['xxx.yyy'].setLevel(66)

        new_level = 101
        for logger in SDK._context.loggers.values():
            self.assertNotEqual(logger.level, new_level)

        SDK.set_logging_level(level=new_level, prefix='SDK')
        for logger_name, logger in SDK._context.loggers.items():
            if logger_name.split('.')[0].startswith('SDK'):
                self.assertEqual(logger.level, new_level)
            else:
                self.assertEqual(logger.level, 66)


if __name__ == '__main__':  # pragma: no-cover
    unittest.main()
