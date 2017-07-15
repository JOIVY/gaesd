
**Python StackDriver SDK for AppEngine and non-AppEngine environments**

<br>
<br>
<u>WARNING</u>: <b>Sending traces to the StackDriver Trace API takes approx 200 ms !!!!</b>
<br>
<br>
<br>
<br>


**How to use**

1.  Create a global SDK instance.
    ```
    from google.appengine.api.app_identity import app_identity
    from gaesd import SDK

    app_id = app_identity.get_application_id()
    auto = False   # Requires a call to manually send the results to StackDriver.
    sdk = SDK(
        project_id=app_id, 
        auto=auto,
    )
    ```

2.  In the application's request handler, get the request context:
    ```
    from webapp2 import get_request
    
    def get_default_trace_context(self):
        return get_request().headers.get('X-Cloud-Trace-Context') or 'NNNN/NNNN;xxxxx'
    ```

3.  Get the default trace_id and root_span_id from the request:
    ```
    context = get_default_trace_context()
    root_trace_id, root_span_id = context.split(';')[0].split('/')
    ```

4.  Create the root trace with the `root_trace_id` and set the trace's `root_span_id` for all 
top-level spans:
    ```
    trace = sdk.current_trace.set_default(trace_id=root_trace_id, root_span_id=root_span_id)
    ```
   
5.  Set the request handler to dispatch the trace data at the end of the request:
    ```
    # webapp2 example:
    class handler(webapp2.RequestHandler):
        def get(self):
            ...
            sdk()        # Dispatches to StackDriver API.
    ```

6.  Use the sdk api where you want to trace the code:
    ```
    top_level_trace = sdk.current_trace             # Get the current trace
    current_span_tree = sdk.current_span            # Get the current span
    
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
        
        
    or (TODO):
    
    @gaesd.decorators.span(name='func_name')
    def func(x, y, z=1):
        nested_func()
        
    @gaesd.decorators.sub_span(name='nested_func_name')
    def nested_func(a, b, c=2):
        ...    
    ```


***TODO***

1.  Create decorators so we can automatically trace methods.
