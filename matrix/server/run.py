from flask import Flask

from matrix.server.config import endpoint_config
from matrix.server.startup import register_endpoints

app = Flask(__name__)

register_endpoints(app, endpoint_config)

app.run(debug=True, host='0.0.0.0', port=8000)