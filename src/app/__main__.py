"""Serve the dash web app locally."""

import sys

from .app import init_dash_app

if __name__ == "__main__":
    check_per_s = int(sys.argv[1])
    app = init_dash_app(1 / check_per_s)
    app.run_server(port=8050, debug=True)
