#!/usr/bin/env python
# -*- coding: latin-1 -*-


__all__ = ['Helpers']


class Helpers(object):
    """
    Encapsulation of helpers functionality.
    """

    def __init__(self, sdk):
        """
        :param gaesd.SDK sdk: SDK this Helpers belongs to.
        """
        self._sdk = sdk

    @property
    def sdk(self):
        """
        Retrieve the SDK instance associated with this Helpers instance.

        :rtype: gaesd.SDK
        """
        return self._sdk

    def trace_as_span(
        self, trace_enabler, name, func, func_args=None, func_kwargs=None,
        nested=True, trace=None, span_args=None,
    ):
        """
        Execute a function conditionally as a span decorated function.

        :param bool trace_enabler: Flag to enable tracing for the given
        function.
        :param name: StackDriver name of the span. Default=name of decorated
        method.
        :type name: Union[function, str]
        :param Callable func: The target function to execute
        :param bool nested: True=Make this span nested.
        :param Trace trace: Optional Trace to nest the span under.
        :param span_args: kwargs passed directly to the Span constructor.
        :return: Result from the target function.
        """
        func_args = func_args or []
        func_kwargs = func_kwargs or {}

        if trace_enabler:
            @self.sdk.decorators.span(
                name=name,
                nested=nested,
                trace=trace,
                **(span_args or {})
            )
            def _inner(*args, **kwargs):
                return func(*args, **kwargs)

            return _inner(*func_args, **func_kwargs)

        return func(*func_args, **func_kwargs)
