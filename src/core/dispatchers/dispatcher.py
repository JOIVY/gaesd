#!/usr/bin/env python
# -*- coding: latin-1 -*-

import abc
from collections import namedtuple

import six

PrepData = namedtuple('PrepData', ('url', 'body'))

@six.add_metaclass(abc.ABCMeta)
class Dispatcher(object):
    def __init__(self, sdk=None, auto=True):
        self._sdk = sdk
        self._auto = auto
        self._cache = []

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

    def __call__(self):
        # Call this from the thread of the request handler.
        self._dispatch(self._cache)
        self._cache = []

    @abc.abstractmethod
    def _dispatch(self, traces):
        """
        Override this method to dispatch using your own mechanism.

        :param traces: List of traces to send to StackDriver.
        :type traces: [core.trace.Trace]
        :return: None
        """
        raise NotImplementedError

    def patchTraces(self, trace):
        if self.auto:
            # Dispatch immediately:
            self._dispatch([trace])
        else:
            # Dispatch when called:
            self._cache.append(trace)