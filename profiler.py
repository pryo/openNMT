from werkzeug.contrib.profiler import ProfilerMiddleware
from main import app

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(host='127.0.0.1', port=5000, debug = True)