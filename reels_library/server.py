"""Serveur de test WSGI. Le lancement applicatif utilise Waitress."""

from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server as wsgi_server

from .web import Application


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class TestServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

    def server_close(self):
        if self.get_app():
            self.get_app().close()
        super().server_close()


def make_server(database_path, port=8765, access_token=None):
    app = Application(database_path, public_url=f"http://127.0.0.1:{port}", access_token=access_token)
    server = wsgi_server("127.0.0.1", port, app, server_class=TestServer, handler_class=QuietHandler)
    app.public_url = f"http://127.0.0.1:{server.server_port}"
    server.library, server.sync = app.library, app.sync
    return server
