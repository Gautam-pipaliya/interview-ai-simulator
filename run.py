from os import environ

from interview_simulator import create_app

app = create_app()

if __name__ == "__main__":
    debug = environ.get("FLASK_DEBUG", "0").strip() in ("1", "true", "True", "yes")
    host = environ.get("FLASK_HOST", "127.0.0.1")
    port = int(environ.get("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
