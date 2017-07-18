#!/usr/bin/env python
# -*- coding: latin-1 -*-

import unittest

from mock import patch
from nose_parameterized import parameterized

from gaesd.core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from gaesd.core.dispatchers.rest_dispatcher import SimpleRestDispatcher
from gaesd.core.trace import Trace
from gaesd.sdk import SDK


class TestDispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK.new(project_id=self.project_id, auto=False)
        self.assertIsInstance(self.sdk.dispatcher, GoogleApiClientDispatcher)

    @parameterized.expand([
        (True, True),
        (True, False),
    ])
    def test_init(self, auto, enabler):
        sdk = SDK.new(project_id=self.project_id, auto=auto, enabler=enabler)
        dispatcher = SimpleRestDispatcher(sdk=sdk, auto=auto)

        self.assertEqual(dispatcher.sdk, sdk)
        self.assertIs(dispatcher.auto, auto)
        self.assertIs(dispatcher.is_enabled, enabler)

    def test_setters(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        dispatcher.auto = False
        self.assertFalse(dispatcher.auto)

    @patch('gaesd.core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)
        self.assertTrue(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_called_once_with([trace])

    @patch('gaesd.core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_non_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=False)
        self.assertFalse(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace.new(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
