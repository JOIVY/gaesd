#!/usr/bin/env python
# -*- coding: latin-1 -*-

import logging
import unittest

from mock import MagicMock, patch

from tests import PROJECT_ID

try:
    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials

    canTest = True
except ImportError as e:  # pragma: no cover
    logging.warn(
        'Cannot test GoogleApiClientDispatcher - please pip install `google_api_python_client` '
        'and `oauth2client`'
    )
    canTest = False

from gaesd.core.dispatchers.google_api_client_dispatcher import GoogleApiClientDispatcher
from gaesd.sdk import SDK

PROJECT_ID = 'my-project-id.appspot.com'


class MockTrace(object):
    def __init__(self, e_result):
        self.e_result = e_result

    def export(self):
        return self.e_result


class MockProjects(object):
    def __init__(self, return_value):
        self.patchTraces = MagicMock(return_value=return_value)


class MockService(object):
    def __init__(self, return_value):
        self.projects = MagicMock(
            return_value=MockProjects(return_value=return_value)
        )


class TestDispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = PROJECT_ID
        self.sdk = SDK.new(project_id=self.project_id, auto=False)

    @unittest.skipIf(
        not canTest,
        'Cannot test GoogleApiClientDispatcher - please pip install `google_api_python_client` '
        'and `oauth2client')
    def test(self):
        dispatcher = GoogleApiClientDispatcher(self.sdk)

        e_result = 'e-result'
        e_credentials = 'e-credentials'
        e_trace_result_1 = 'e-result-1'
        e_trace_result_2 = 'e-result-2'
        e_trace_result_3 = 'e-result-3'
        e_traces = [
            e_trace_result_1,
            e_trace_result_2,
            e_trace_result_3,
        ]
        e_body = {
            'traces': e_traces,
        }
        traces = [
            MockTrace(e_trace_result_1),
            MockTrace(e_trace_result_2),
            MockTrace(e_trace_result_3)
        ]

        def run(mb, mgad):
            mgad.return_value = e_credentials
            mock_service = MockService(return_value=e_result)
            mb.return_value = mock_service

            result = dispatcher._prep(traces)
            self.assertEqual(result, e_result)
            mock_service.projects().patchTraces.assert_called_once_with(
                projectId=self.sdk.project_id,
                body=e_body,
            )
            mb.assert_called_once_with(
                'cloudtrace',
                'v1',
                credentials=e_credentials,
            )

        with patch('gaesd.core.dispatchers.google_api_client_dispatcher.discovery.build') as \
            mock_build:
            with patch('gaesd.core.dispatchers.google_api_client_dispatcher.GoogleCredentials'
                       '.get_application_default') as mock_get_application_default:
                run(mock_build, mock_get_application_default)


if __name__ == '__main__':  # pragma: no-cover
    unittest.main()
