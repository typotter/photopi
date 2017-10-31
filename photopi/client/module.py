import rpyc

from photopi.core.borg import Borg
from rpyc.utils.server import ThreadedServer
from threading import Thread





class ClientModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        print(args)
        # rpyc client
        conn = rpyc.connect(args['--host'], int(args['--port']))
        c = conn.root

        print(c.timelapse())

def get_module():
    return ClientModule()
