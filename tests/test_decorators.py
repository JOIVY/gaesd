#!/usr/bin/env python
# -*- coding: latin-1 -*-

import unittest

import six

from gaesd.sdk import SDK


#
# class TestDecoratorsSpanTestCase(unittest.TestCase):
#     def setUp(self):
#         self.project_id = 'joivy-dev5'
#         self.sdk = SDK(project_id=self.project_id, auto=False)
#
#     def test_no_brackets(self):
#         self.sdk.current_trace.root_span_id = 'smith'
#
#         @self.sdk.decorators.span
#         def func_a(a, c=1, d='two'):
#             self.assertEqual(a, 'z')
#             self.assertEqual(c, 2)
#             self.assertEqual(d, 'three')
#             return 123
#
#         result = func_a('z', c=2, d='three')
#         self.assertEqual(result, 123)
#
#         traces = self.sdk.dispatcher.traces
#         self.assertEqual(len(traces), 1)
#         spans = traces[0].spans
#         self.assertEqual(len(spans), 1)
#         self.assertEqual(spans[0].name, 'func_a')
#         self.assertEqual(spans[0].parent_span_id, 'smith')
#
#     def test_brackets(self):
#         parent_span_id = 789
#         self.sdk.current_trace.root_span_id = parent_span_id
#
#         @self.sdk.decorators.span(name='bob', nested=True)
#         def func_a(a, c=1, d='two'):
#             self.assertEqual(a, 'y')
#             self.assertEqual(c, 3)
#             self.assertEqual(d, 'four')
#             return 567
#
#         result = func_a('y', c=3, d='four')
#         self.assertEqual(result, 567)
#
#         traces = self.sdk.dispatcher.traces
#         self.assertEqual(len(traces), 1)
#         spans = traces[0].spans
#         self.assertEqual(len(spans), 1)
#         self.assertEqual(spans[0].name, 'bob')
#         self.assertEqual(spans[0].parent_span_id, 789)
#
#     def test_brackets_nested_not_override_default_parent_span(self):
#         self.sdk.current_trace.root_span_id = 'smith'
#         parent_span_id = 1234
#         parent_span = Span(self.sdk.current_trace, span_id=parent_span_id)
#
#         @self.sdk.decorators.span(name='bob', nested=True, parent_span=parent_span)
#         def func_a(a, c=1, d='two'):
#             self.assertEqual(a, 'y')
#             self.assertEqual(c, 3)
#             self.assertEqual(d, 'four')
#             return 567
#
#         result = func_a('y', c=3, d='four')
#         self.assertEqual(result, 567)
#
#         traces = self.sdk.dispatcher.traces
#         self.assertEqual(len(traces), 1)
#         spans = traces[0].spans
#         self.assertEqual(len(spans), 1)
#         self.assertEqual(spans[0].name, 'bob')
#         self.assertEqual(spans[0].parent_span_id, parent_span_id)
#
#     def test_brackets_not_nested_takes_root_span_id(self):
#         self.sdk.current_trace.root_span_id = 'smith'
#
#         @self.sdk.decorators.span(name='bob', nested=False)
#         def func_a(a, c=1, d='two'):
#             self.assertEqual(a, 'y')
#             self.assertEqual(c, 3)
#             self.assertEqual(d, 'four')
#             return 567
#
#         result = func_a('y', c=3, d='four')
#         self.assertEqual(result, 567)
#
#         traces = self.sdk.dispatcher.traces
#         self.assertEqual(len(traces), 1)
#         spans = traces[0].spans
#         self.assertEqual(len(spans), 1)
#         self.assertEqual(spans[0].name, 'bob')
#         self.assertEqual(spans[0].parent_span_id, 'smith')
#
#     def test_brackets_not_nested(self):
#         @self.sdk.decorators.span(name='bob', nested=False)
#         def func_a(a, c=1, d='two'):
#             self.assertEqual(a, 'y')
#             self.assertEqual(c, 3)
#             self.assertEqual(d, 'four')
#             return 567
#
#         result = func_a('y', c=3, d='four')
#         self.assertEqual(result, 567)
#
#         traces = self.sdk.dispatcher.traces
#         self.assertEqual(len(traces), 1)
#         spans = traces[0].spans
#         self.assertEqual(len(spans), 1)
#         self.assertEqual(spans[0].name, 'bob')
#         self.assertIsNone(spans[0].parent_span_id)
#

class TestDecoratorsTraceTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)

    def test_no_brackets_does_not_create_span(self):
        @self.sdk.decorators.trace
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'z')
            self.assertEqual(c, 2)
            self.assertEqual(d, 'three')
            return 123

        result = func_a('z', c=2, d='three')
        self.assertEqual(result, 123)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        self.assertIsInstance(traces[0].trace_id, six.string_types)
        spans = traces[0].spans
        self.assertEqual(len(spans), 0)

    def test_brackets_set_trace_id(self):
        parent_span_id = 789
        self.sdk.current_trace.root_span_id = parent_span_id

        @self.sdk.decorators.trace(trace_id='bob')
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].trace_id, 'bob')
        spans = traces[0].spans
        self.assertEqual(len(spans), 0)

    def test_brackets_creates_span(self):
        parent_span_id = 789
        self.sdk.current_trace.root_span_id = parent_span_id

        @self.sdk.decorators.trace(trace_id='bob', _create_span=True, _span_args={
            'name': 'smith',
        })
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].trace_id, 'bob')
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'smith')


if __name__ == '__main__':
    unittest.main()
