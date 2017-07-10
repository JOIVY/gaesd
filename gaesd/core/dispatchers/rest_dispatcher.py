#!/usr/bin/env python
# -*- coding: latin-1 -*-

from collections import namedtuple

from gaesd.core.dispatchers.dispatcher import Dispatcher

PrepData = namedtuple('PrepData', ('url', 'body'))


class RestDispatcher(Dispatcher):
    _ROOT_URL = 'https://cloudtrace.googleapis.com'
    _PATCH_TRACES_URL = '/v1/projects/{projectId}/traces'

    def _prep_dispatch(self, traces):
        # Dispatch!
        return PrepData(
            ''.join([self._ROOT_URL, self._PATCH_TRACES_URL.format(self.sdk.project_id)]),
            {'traces': [trace.export() for trace in traces]}
        )

    def _dispatch(self, traces):
        """
        Override this method to dispatch using your own mechanism.

        :param traces: List of traces to send to StackDriver.
        :type traces: [core.trace.Trace]
        :return: None
        """
        raise NotImplementedError


class SimpleRestDispatcher(RestDispatcher):
    def _dispatch(self, traces):
        pass
