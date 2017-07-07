
**Python StackDriver SDK for AppEngine and non-AppEngine environments**

**How to use**

1.  Create a global SDK instance.
    ```
    from google.appengine.api.app_identity import app_identity
    
    app_id = app_identity.get_application_id()
    sdk = SDK(project_id=app_id)
    ```

2.  In the application's request handler, get the request context:
    ```
    from webapp2 import get_request
    
    def get_default_trace_context(self):
        return get_request().headers.get('X-Cloud-Trace-Context') or 'NNNN/NNNN;xxxxx'
    ```

3.  Get the default trace_id and root_span_id from the request:
    ```
    context = get_default_trace-context()
    root_trace_id, root_span_id = context.split(';')[0].split('/')
    ```

4.  Create the root trace:
    ```
    trace = sdk.trace(trace_id=root_trace_id)
    ```
   
5.  Set the trace's root span_id for all top-level spans:
    ```
    trace.root_span_id = root_span_id
    ```

6.  Set the request handler to dispatch the trace data at the end of the request:
    ```
    class handler(webapp2.RequestHandler):
        def get(self):
            ...
            sdk.dispatcher()        # Dispatches to StackDriver API.
    ```

7.  Use the sdk api:
    ```
    top_level_trace = sdk.current_trace
    current_span_tree = sdk.current_span
    
    with current_span_tree:
        ...
    
    or
    
    current_span_tree.name = 'a'
    with current_span_tree.span(name='b') as span_b:
        with spanb_b.span(name='c') as span_c:
            ...
    
    or
    
    with top_level_trace.span(name='a'):
        ...
    ```
