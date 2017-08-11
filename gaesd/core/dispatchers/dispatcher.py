#!/usr/bin/env python
# -*- coding: latin-1 -*-

import abc
from logging import getLogger

import six

__all__ = ['Dispatcher']


@six.add_metaclass(abc.ABCMeta)
class Dispatcher(object):
    """
    Base dispatcher class.
    """

    def __init__(self, sdk=None, auto=True):
        """
        :param gaesd.SDK sdk: SDK instance to use.
        :param bool auto: True=dispatch traces immediately upon span completion,
            False=Otherwise.
        """
        self._sdk = sdk
        self._auto = auto
        self._traces = []

    @property
    def logger(self):
        """
        Retrieve this dispatchers's logger instance.
        """
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.sdk.loggers.get(logger_name)
        if logger is None:
            self.sdk.loggers[logger_name] = getLogger(
                '{name}'.format(name=logger_name))

        return self.sdk.loggers[logger_name]

    def set_logging_level(self, level):
        """
        Set the logging level of this dispatchers's logger.

        :param int level: New logging level to set.
        """
        return self.sdk.set_logging_level(
            level,
            prefix=self.__class__.__name__,
        )

    @property
    def traces(self):
        """
        Retrieve a list of the cached traces awaiting dispatch.

        :return: A shallow-copy list of this dispatchers traces.
        :rtype: list(gaesd.Trace)
        """
        return self._traces[:]

    @property
    def sdk(self):
        """
        Retrieve the SDK that this dispatcher is associated with.

        :rtype:  gaesd.SDK
        """
        return self._sdk

    @sdk.setter
    def sdk(self, sdk):
        """
        Set the SDK that this dispatcher is associated with
        :param gaesd.SDK sdk: The new dispatcher to use.
        """
        self._sdk = sdk

    @property
    def auto(self):
        """
        Retrieve this dispatcher's `auto` state.

        :rtype: bool
        """
        return self._auto

    @auto.setter
    def auto(self, auto):
        """
        St this dispatcher's `auto` state.

        :param bool auto:
        """
        self._auto = auto

    @property
    def is_enabled(self):
        """
        Determine if this dispatcher is enabled

        :rtype: bool
        """
        return self.sdk.is_enabled

    def __call__(self):
        """
        Dispatch the current trace's based on this dispatcher's enabled
            state.
        :note: Call this from the thread of the request handler.
        :return: This dispatcher's enabled state.
        :rtype: bool
        """
        if self.is_enabled:
            self.logger.debug('Forced immediate dispatch')
            self._dispatch(self.traces)
            dispatched = True
        else:
            dispatched = False

        self._traces = []

        return dispatched

    @abc.abstractmethod
    def _dispatch(self, traces):
        """
        Override this method to dispatch using your own mechanism.

        :param traces: List of traces to send to StackDriver.
        :type traces: [core.Trace]
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def patch_trace(self, trace):
        """
        Ingest a new Trace into this dispatcher.

        If this dispatcher's auto state is enabled, this trace will be
            automatically dispatched, otherwise it will be cached.

        :param gaesd.Trace trace: The trace instance to ingest.
        """
        if self.auto:
            # Dispatch immediately:
            self.logger.debug('Immediate dispatch')
            # Also dispatch any cached traces:
            self._traces.append(trace)
            self._dispatch(self._traces)
        else:
            if trace in self._traces:
                # Trace already cached!
                return
            # Dispatch when called:
            self.logger.debug('Delayed dispatch')
            self._traces.append(trace)
