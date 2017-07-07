#!/usr/bin/env python
# -*- coding: latin-1 -*-

from collections import namedtuple

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from core.dispatchers.dispatcher import Dispatcher

PrepData = namedtuple('PrepData', ('url', 'body'))


class GoogleApiClientDispatcher(Dispatcher):
    def _dispatch(self, traces):
        body = [trace.export() for trace in traces]

        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('cloudtrace', 'v1', credentials=credentials)

        request = service.projects().patchTraces(
            projectId=self.sdk.project_id,
            body=body,
        )
        request.execute()
