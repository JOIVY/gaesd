#!/usr/bin/env python
# -*- coding: latin-1 -*-

import six

__all__ = ['Helpers']


class Helpers(object):
    """
    Encapsulation of helpers functionality.
    """

    def __init__(self, sdk):
        self._sdk = sdk

    @property
    def sdk(self):
        return self._sdk

    def trace_as_span(self, trace_enabler, func, name, nested=True, trace=None, **span_args):
        """
        Execute a function conditionally as a span decorated function.

        :param trace_enabler: Flag to enable tracing for the given function.
        :type trace_enabler: bool
        :param func: The target function to execute
        :type func: Callable
        :param name: StackDriver name of the span. Default=name of decorated method.
        :type name: Union[function, str]
        :type nested: bool
        :param trace: Optional Trace to nest the span under.
        :param span_args: kwargs passed directly to the Span constructor.
        :return: Result from the target function.
        """
        if trace_enabler:
            @self.sdk.decorators.span(name=name, nested=nested, trace=trace, **span_args)
            def _inner():
                return func()

            return _inner()
        else:
            return func()
