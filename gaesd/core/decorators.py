#!/usr/bin/env python
# -*- coding: latin-1 -*-

import six

__all__ = ['Decorators', 'TraceDecorators', 'SpanDecorators']


class Decorators(object):
    """
    Encapsulation of decorator functionality.
    """

    def __init__(self, sdk):
        self._sdk = sdk

    def span(self, name=None, nested=True, trace=None, **span_args):
        """
        Decorate a callable so that a new (nested) span context is
        automatically created for it.

        Call with or without brackets.
        If `nested` is True, will set the default span_args['parent_span'] (
        not overriding it).

        :param name: Name of the span. Default=name of decorated method.
        :type name: Union[function, str]
        :param bool nested: True=Create a nested span under the current span.
        :param Trace trace: Optional Trace to nest the span under.
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

                if trace is not None:
                    with trace.span(**span_args) as current_span:
                        return func(*args, **kwargs)

                with self._sdk.span(**span_args):
                    return func(*args, **kwargs)

            return __new_span_decorator_inner

        if callable(name):
            return _new_span_decorator(name)

        return _new_span_decorator

    def trace(
        self, trace_id=None, _create_span=False, _span_args=None, **trace_args
    ):
        """
        Decorate a callable so that a new trace context is automatically
        created for it.

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

                    with trace.span(**_span_args):
                        return func(*args, **kwargs)

            return __new_trace_decorator_inner

        if callable(trace_id):
            return _new_trace_decorator(trace_id)

        return _new_trace_decorator


class TraceDecorators(Decorators):
    def __init__(self, trace):
        super(TraceDecorators, self).__init__(trace.sdk)
        self._trace = trace

    def trace(
        self, trace_id=None, _create_span=False, _span_args=None, **trace_args
    ):
        raise NotImplementedError()

    def span(self, name=None, nested=True, **span_args):
        span_args['trace'] = self._trace
        return super(TraceDecorators, self).span(
            name=name, nested=True, **span_args)


class SpanDecorators(Decorators):
    def __init__(self, span):
        super(SpanDecorators, self).__init__(span.trace.sdk)
        self._span = span

    def trace(
        self, trace_id=None, _create_span=False, _span_args=None, **trace_args
    ):
        raise NotImplementedError()

    def span(self, name=None, nested=True, **span_args):
        span_args['trace'] = self._span.trace
        if 'parent_span' in span_args:
            raise TypeError('parent_span_id is overwritten by this decorator')

        span_args['parent_span'] = self._span
        return super(SpanDecorators, self).span(
            name=name, nested=True, **span_args)
