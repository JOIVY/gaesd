#!/usr/bin/env python
# -*- coding: latin-1 -*-

from __future__ import print_function

try:
    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
except ImportError as e:
    print('GoogleApiClientDispatcher not available, please vendor-in required package: ' \
          '`google_api_python_client` and `oauth2client`')
else:
    from gaesd.core.dispatchers.dispatcher import Dispatcher

    __all__ = ['GoogleApiClientDispatcher']


    class GoogleApiClientDispatcher(Dispatcher):
        def _prep(self, traces):
            body = {
                'traces': [trace.export() for trace in traces],
            }

            if not hasattr(self, '__credentials'):
                self.__credentials = GoogleCredentials.get_application_default()
            if not hasattr(self, '__service'):
                self.__service = discovery.build('cloudtrace', 'v1', credentials=self.__credentials)

            project_id = self.sdk.project_id
            print('PROJECT_ID: {0}'.format(project_id))
            print('BODY: {0}'.format(body))

            return self.__service.projects().patchTraces(
                projectId=project_id,
                body=body,
            )

        def _dispatch(self, traces):
            return self._emit(
                self._prep(traces),
            )

        def _emit(self, request):
            return request.execute()
