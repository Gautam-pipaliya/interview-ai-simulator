from os import environ

from interview_simulator import create_app, socketio

app = create_app()

if __name__ == "__main__":
    debug = environ.get("FLASK_DEBUG", "0").strip() in ("1", "true", "True", "yes")
    host = environ.get("FLASK_HOST", "127.0.0.1")
    port = int(environ.get("FLASK_PORT", "5000"))
    socketio.run(app, host=host, port=port, debug=debug)
