#!/usr/bin/env python
# -*- coding: latin-1 -*-

import unittest

import six

from gaesd.core.helpers import Helpers
from gaesd.sdk import SDK

PROJECT_ID = 'my-project-id.appspot.com'


class HelpersCaseBase(object):
    def setUp(self):
        self.project_id = PROJECT_ID
        self.sdk = SDK.new(project_id=self.project_id, auto=False)


class TestHelpersSDKTraceTestCase(HelpersCaseBase, unittest.TestCase):
    def test_span_trace_raises_NotImplementedError(self):
        helpers = self.sdk.helpers
        self.assertIsInstance(helpers, Helpers)
        self.assertIs(helpers.sdk, self.sdk)

    def test_trace_as_span_disabled(self):
        e_result = 'a result !'

        def func(*args, **kwargs):
            return args, kwargs, e_result

        enabler = False
        e_name = 'my-name'
        helpers = self.sdk.helpers
        f_args = (1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        f_kwargs = {'x': 'xx', '55': None}

        result = helpers.trace_as_span(
            trace_enabler=enabler,
            name=e_name,
            func=func,
            nested=False,
            trace=123,
            span_args={
                'a': 1,
            },
            func_args=f_args,
            func_kwargs=f_kwargs,
        )
        self.assertEqual(result, (f_args, f_kwargs, e_result))

    def test_trace_as_span_enabled(self):
        e_result = 'a result !'
        called_with = []

        def func(*args, **kwargs):
            return args, kwargs, e_result

        def decorator(name=None, nested=True, trace=None, **span_args):
            called_with.append((name, nested, trace, span_args))

            def _inner(fn):
                @six.wraps(fn)
                def __inner(*args, **kwargs):
                    return fn(*args, **kwargs)

                return __inner

            return _inner

        self.sdk.decorators.span = decorator
        enabler = True
        e_name = 'my-name'
        nested = True
        span_args = {'a': 1}
        helpers = self.sdk.helpers
        f_args = (1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        f_kwargs = {'x': 'xx', '55': None}

        result = helpers.trace_as_span(
            trace_enabler=enabler,
            name=e_name,
            func=func,
            nested=nested,
            trace=123,
            span_args=span_args,
            func_args=f_args,
            func_kwargs=f_kwargs,
        )
        self.assertEqual(result, (f_args, f_kwargs, e_result))
        self.assertEqual(called_with, [(e_name, nested, 123, span_args)])


if __name__ == '__main__':  # pragma: no-cover
    unittest.main()
