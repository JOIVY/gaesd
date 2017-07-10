#!/usr/bin/env python
# -*- coding: latin-1 -*-

try:
    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
except ImportError:
    print 'GoogleApiClientDispatcher not available, please vendor-in required package: ' \
          '`google-api-python-client`'
else:
    from core.dispatchers.dispatcher import Dispatcher

    class GoogleApiClientDispatcher(Dispatcher):
        def _dispatch(self, traces):
            body = [trace.export() for trace in traces]

            credentials = GoogleCredentials.get_application_default()
            service = discovery.build('cloudtrace', 'v1', credentials=credentials)

            request = service.projects().patchTraces(
                projectId=self.sdk.project_id,
                body=body,
            )
            return self._emit(request)

        def _emit(self, request):
            return request.execute()


    try:
        from google.appengine.ext import ndb
        from google.appengine.api import urlfetch
    except ImportError:
        print 'GoogleApiClientDispatcherAsync not available, cannot find appengine SDK.'
    else:
        class HttpUrlfetch(object):
            @ndb.synctasklet
            def request(self, uri, method, *args, **kwargs):
                """
                Make the http request in the thread of the event loop.

                :note: args are never used.
                :rtype: tuple(http.HTTPResponse, str(response-body))
                """
                response = yield ndb.get_context().urlfetch(
                    method=method,
                    url=uri,
                    headers=kwargs.get('headers', {}),
                    payload=kwargs.get('body'),
                )

                raise ndb.Return(
                    response, response.body,
                )


        class GoogleApiClientDispatcherAsync(GoogleApiClientDispatcher):
            def _emit(self, request):
                return request.execute(http=HttpUrlfetch())
