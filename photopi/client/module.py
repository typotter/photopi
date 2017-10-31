import rpyc

from photopi.core.borg import Borg
from rpyc.utils.server import ThreadedServer
from threading import Thread

class ClientModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        print("Client Module")
        print(args)
        # rpyc client
        conn = rpyc.connect(args['--host'], int(args['--port']))
        c = conn.root

        if args['--module'] == "raspistill":
            module = c.raspistill()
            args[args['action']] = True
            module.main(args)

def get_module():
    return ClientModule()
