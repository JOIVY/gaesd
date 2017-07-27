#!/usr/bin/env python
# -*- coding: latin-1 -*-

from __future__ import print_function

try:
    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
except ImportError as e:  # pragma: no cover
    print('GoogleApiClientDispatcher not available, please vendor-in required package: '
          '`google_api_python_client` and `oauth2client`')
else:
    from gaesd.core.dispatchers.dispatcher import Dispatcher

    __all__ = ['GoogleApiClientDispatcher']


    class GoogleApiClientDispatcher(Dispatcher):
        def _prep(self, traces):
            if not hasattr(self, '__credentials'):
                self.__credentials = GoogleCredentials.get_application_default()
            if not hasattr(self, '__service'):
                self.__service = discovery.build('cloudtrace', 'v1', credentials=self.__credentials)

            return self.__service.projects().patchTraces(
                projectId=self.sdk.project_id,
                body={
                    'traces': [trace.export() for trace in traces],
                },
            )

        def _dispatch(self, traces):
            return self._emit(
                self._prep(traces),
            )

        def _emit(self, request):
            return request.execute()
