#!/usr/bin/env python
# -*- coding: latin-1 -*-

import six

__all__ = ['Decorators']


class Decorators(object):
    """
    Controls decorator creation.
    """

    def __init__(self, sdk):
        self._sdk = sdk

    def span(self, name=None, nested=True, **span_args):
        """
        Decorate a callable so that a new (nested) span context is automatically created for it.
        Decorator.
        Call with or without brackets.
        If `nested` is True, will set the default span_args['parent_span'] (not overriding it).

        :param name: Name of the span. Default=None.
        :type name: Union[function, str]
        :param nested: True=Create a nested span under the current span.
        :type nested: bool
        :param span_args: kwargs passed directly to the Span constructor.
        :return: Decorated function.
        :rtype: function
        """

        def _new_span_decorator(func):
            @six.wraps(func)
            def __new_span_decorator_inner(*args, **kwargs):
                span_name = name
                if callable(name):
                    span_name = func.__name__
                span_args.setdefault('name', span_name)

                if nested:
                    # Guard against creating a current_span:
                    if self._sdk.has_current_span:
                        parent_span = self._sdk.current_span
                        span_args.setdefault('parent_span', parent_span)

                with self._sdk.span(**span_args):
                    return func(*args, **kwargs)

            return __new_span_decorator_inner

        if callable(name):
            return _new_span_decorator(name)
        else:
            return _new_span_decorator

    def trace(self, trace_id=None, _create_span=False, _span_args=None, **trace_args):
        """
        Decorate a callable so that a new trace context is automatically created for it.
        Decorator.
        Call with or without brackets.
        If `_create_span` is True, will create a new span context.

        :param trace_id: Optional id of the trace to provide.
        :type trace_id: Union[function, str]
        :param _create_span: True: Create a new span context.
        :type _create_span: bool
        :param _span_args: kwargs passed directly to the Span constructor.
        :param trace_args: kwargs passed directly to the Trace constructor.
        :return: Decorated function.
        :rtype: function
        """

        def _new_trace_decorator(func):
            @six.wraps(func)
            def __new_trace_decorator_inner(*args, **kwargs):
                if not callable(trace_id):
                    trace_args.setdefault('trace_id', trace_id)

                with self._sdk.trace(**trace_args) as trace:
                    if not _create_span:
                        return func(*args, **kwargs)
                    else:
                        with trace.span(**_span_args):
                            return func(*args, **kwargs)

            return __new_trace_decorator_inner

        if callable(trace_id):
            return _new_trace_decorator(trace_id)
        else:
            return _new_trace_decorator
