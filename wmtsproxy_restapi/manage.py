import logging

from flask.ext.script import Manager, Server

from wmtsproxy_restapi.app import create_app

app = create_app()

logging_handler = logging.StreamHandler()
logging_handler.setLevel(logging.DEBUG)
app.logger.addHandler(logging_handler)

manager = Manager(app)
manager.add_command("runserver", Server(threaded=True, port=9091))

if __name__ == '__main__':
    manager.run()
