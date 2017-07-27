#!/usr/bin/env python
# -*- coding: latin-1 -*-

import unittest

import six

from gaesd import Span
from gaesd.sdk import SDK


class DecoratorsCaseBase(object):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK.new(project_id=self.project_id, auto=False)


class TestDecoratorsSDKTraceTestCase(DecoratorsCaseBase, unittest.TestCase):
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


class DecoratorsSpanBase(DecoratorsCaseBase):
    def decorate_no_brackets(self, func):
        """"""

    def decorate_with_brackets(self, func):
        """"""

    def test_no_brackets(self):
        self.sdk.current_trace.root_span_id = 'smith'

        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'z')
            self.assertEqual(c, 2)
            self.assertEqual(d, 'three')
            return 123

        func_a = self.decorate_no_brackets(func_a)
        result = func_a('z', c=2, d='three')
        self.assertEqual(result, 123)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'func_a')
        self.assertEqual(spans[0].parent_span_id, 'smith')

    def test_brackets(self):
        parent_span_id = 789
        self.sdk.current_trace.root_span_id = parent_span_id

        # @current_trace.decorators.span(name='bob', nested=True)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        func_a = self.decorate_with_brackets(func_a, name='bob', nested=True)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'bob')
        self.assertEqual(spans[0].parent_span_id, 789)

    def test_brackets_nested_not_override_default_parent_span(self):
        current_trace = self.sdk.current_trace
        current_trace.root_span_id = 'smith'
        parent_span_id = 1234
        parent_span = Span.new(current_trace, span_id=parent_span_id)

        # @current_trace.decorators.span(name='bob', nested=True, parent_span=parent_span)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        func_a = self.decorate_with_brackets(func_a, name='bob', nested=True,
            parent_span=parent_span)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'bob')
        self.assertEqual(spans[0].parent_span_id, parent_span_id)

    def test_brackets_not_nested_takes_root_span_id(self):
        current_trace = self.sdk.current_trace
        current_trace.root_span_id = 'smith'

        # @current_trace.decorators.span(name='bob', nested=False)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        func_a = self.decorate_with_brackets(func_a, name='bob', nested=False)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'bob')
        self.assertEqual(spans[0].parent_span_id, 'smith')

    def test_brackets_not_nested(self):
        # @current_trace.decorators.span(name='bob', nested=False)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        func_a = self.decorate_with_brackets(func_a, name='bob', nested=False)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, 'bob')
        self.assertIsNone(spans[0].parent_span_id)

    def test_brackets_use_current_span_as_parent_span(self):
        # @current_trace.decorators.span(name='bob', nested=False)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        func_a = self.decorate_with_brackets(func_a, name='bob', nested=False)

        trace = self.sdk.current_trace
        parent_span = trace.span(name='jane')
        parent_span_id = parent_span.span_id
        self.assertIs(self.sdk.current_span, parent_span)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0].name, 'jane')
        self.assertEqual(spans[1].name, 'bob')
        self.assertIsNone(spans[0].parent_span_id)
        self.assertEqual(spans[1].parent_span_id, parent_span_id)


class TestDecoratorsSDKSpanTestCase(DecoratorsSpanBase, unittest.TestCase):
    def decorate_no_brackets(self, func):
        return self.sdk.decorators.span(func)

    def decorate_with_brackets(self, func, **kwargs):
        return self.sdk.decorators.span(**kwargs)(func)


class TestDecoratorsTraceSpanTestCase(DecoratorsSpanBase, unittest.TestCase):
    def decorate_no_brackets(self, func):
        return self.sdk.current_trace.decorators.span(func)

    def decorate_with_brackets(self, func, **kwargs):
        return self.sdk.current_trace.decorators.span(**kwargs)(func)

    def test_trace_trace_raises_NotImplementedError(self):
        self.assertRaises(
            NotImplementedError,
            self.sdk.current_trace.decorators.trace, lambda: None, None,
            parent_span='invalidParentSpan', name='bob', nested=True
        )


class TestDecoratorsSpanSpanTestCase(DecoratorsCaseBase, unittest.TestCase):
    def decorate_no_brackets(self, func, span_id):
        current_span = self.sdk.current_span
        current_span._span_id = span_id
        return current_span.decorators.span(func)

    def decorate_with_brackets(self, func, span_id, **kwargs):
        current_span = self.sdk.current_span
        current_span._span_id = span_id
        return current_span.decorators.span(**kwargs)(func)

    def test_no_brackets(self):
        self.sdk.current_trace.root_span_id = 'nothing'

        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'z')
            self.assertEqual(c, 2)
            self.assertEqual(d, 'three')
            return 123

        func_a = self.decorate_no_brackets(func_a, 'smith')
        result = func_a('z', c=2, d='three')
        self.assertEqual(result, 123)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[1].name, 'func_a')
        self.assertEqual(spans[1].parent_span_id, 'smith')

    def test_brackets(self):
        parent_span_id = 789
        self.sdk.current_trace.root_span_id = parent_span_id

        # @current_trace.decorators.span(name='bob', nested=True)
        def func_a(a, c=1, d='two'):
            self.assertEqual(a, 'y')
            self.assertEqual(c, 3)
            self.assertEqual(d, 'four')
            return 567

        span_id = 789
        func_a = self.decorate_with_brackets(func_a, span_id, name='bob', nested=True)

        result = func_a('y', c=3, d='four')
        self.assertEqual(result, 567)

        traces = self.sdk.dispatcher.traces
        self.assertEqual(len(traces), 1)
        spans = traces[0].spans
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[1].name, 'bob')
        self.assertEqual(spans[1].parent_span_id, span_id)

    def test_parent_span_id_raises_TypeError(self):
        parent_span_id = 789
        self.sdk.current_trace.root_span_id = parent_span_id

        span_id = 789
        self.assertRaises(
            TypeError,
            self.decorate_with_brackets, lambda: None, span_id,
            parent_span='invalidParentSpan', name='bob', nested=True
        )

    def test_span_trace_raises_NotImplementedError(self):
        self.assertRaises(
            NotImplementedError,
            self.sdk.current_span.decorators.trace, lambda: None, None,
            parent_span='invalidParentSpan', name='bob', nested=True
        )


if __name__ == '__main__':
    unittest.main()
