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

        if args['raspistill']:
            module = c.raspistill()
            module.main(args)

def get_module():
    return ClientModule()
