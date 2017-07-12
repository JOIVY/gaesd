#!/usr/bin/env python
# -*- coding: latin-1 -*-

import unittest

from mock import patch

from gaesd.core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from gaesd.core.dispatchers.rest_dispatcher import SimpleRestDispatcher
from gaesd.core.trace import Trace
from gaesd.sdk import SDK


class TestDispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'joivy-dev5'
        self.sdk = SDK(project_id=self.project_id, auto=False)
        self.assertIsInstance(self.sdk.dispatcher, GoogleApiClientDispatcher)

    def test_init(self):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=True)

        self.assertEqual(dispatcher.sdk, self.sdk)
        self.assertTrue(dispatcher.auto)

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
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_called_once_with([trace])

    @patch('gaesd.core.dispatchers.rest_dispatcher.SimpleRestDispatcher._dispatch')
    def test_auto_dispatch(self, mock_dispatch):
        dispatcher = SimpleRestDispatcher(sdk=self.sdk, auto=False)
        self.assertFalse(dispatcher.auto)

        trace_id = Trace.new_trace_id()
        trace = Trace(self.sdk, trace_id=trace_id)

        dispatcher.patch_trace(trace)
        mock_dispatch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
