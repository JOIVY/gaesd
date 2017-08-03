#!/usr/bin/env python
# -*- coding: latin-1 -*-

import abc
from logging import getLogger

import six

__all__ = ['Dispatcher']


@six.add_metaclass(abc.ABCMeta)
class Dispatcher(object):
    def __init__(self, sdk=None, auto=True):
        """
        :param sdk: SDK instance to use
        :type sdk: gaesd.sdk.SDK
        :param auto: True=dispatch traces immediately upon span completion, False=Otherwise.
        :type auto: bool
        """
        self._sdk = sdk
        self._auto = auto
        self._traces = []

    @property
    def logger(self):
        my_id = id(self)
        name = self.__class__.__name__
        logger_name = '{name}.{my_id}'.format(my_id=my_id, name=name)

        logger = self.sdk.loggers.get(logger_name)
        if logger is None:
            self.sdk.loggers[logger_name] = getLogger('{name}'.format(name=logger_name))

        return self.sdk.loggers[logger_name]

    def set_logging_level(self, level):
        return self.sdk.set_logging_level(level, prefix=self.__class__.__name__)

    @property
    def traces(self):
        return self._traces

    @property
    def sdk(self):
        return self._sdk

    @sdk.setter
    def sdk(self, sdk):
        self._sdk = sdk

    @property
    def auto(self):
        return self._auto

    @auto.setter
    def auto(self, auto):
        self._auto = auto

    @property
    def is_enabled(self):
        return self.sdk.is_enabled

    def __call__(self):
        # Call this from the thread of the request handler.
        if self.is_enabled:
            self.logger.debug('Forced immediate dispatch')
            self._dispatch(self._traces)
        self._traces = []

    @abc.abstractmethod
    def _dispatch(self, traces):
        """
        Override this method to dispatch using your own mechanism.

        :param traces: List of traces to send to StackDriver.
        :type traces: [core.trace.Trace]
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def patch_trace(self, trace):
        if self.auto:
            # Dispatch immediately:
            self.logger.debug('Immediate dispatch')
            self._dispatch([trace])
        else:
            if trace in self._traces:
                # Trace already cached!
                return
            # Dispatch when called:
            self.logger.debug('Delayed dispatch')
            self._traces.append(trace)
