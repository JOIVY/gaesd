#!/usr/bin/env python
# -*- coding: latin-1 -*-

from core.dispatchers.rest_dispatcher import RestDispatcher

try:
    from google.appengine.api import urlfetch
    from google.appengine.ext import ndb
except:
    # URL Fetch not available!
    pass
else:
    try:
        from webapp2_extras import json
    except:
        import json

        json.encode = json.dumps


    class UrlFetchRestDispatcher(RestDispatcher):
        def _dispatch(self, traces):
            """
            Dispatch using non eventloop-friendly urlfetch.
            """
            url, body = self._prep_dispatch(traces)
            json_body = json.encode(body)
            headers = {}

            result = urlfetch.fetch(
                url=url,
                payload=json_body,
                method=urlfetch.PATCH,
                headers=headers,
            )


    class UrlFetchRestDispatcherAsync(RestDispatcher):
        def _dispatch(self, traces):
            """
            Dispatch using eventloop-friendly urlfetch.
            """
            url, body = self._prep_dispatch(traces)
            json_body = json.encode(body)
            headers = {}

            context = ndb.get_context()

            result = yield context.urlfetch(
                url=url,
                payload=json_body,
                method=urlfetch.PATCH,
                headers=headers,
            )
