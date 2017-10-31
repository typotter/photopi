import rpyc

from photopi.core.borg import Borg
from rpyc.utils.server import ThreadedServer
from threading import Thread

class ClientModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        print("Connecting to remote PHOTOPI")
        # rpyc client
        conn = rpyc.connect(args['--host'], int(args['--port']))
        c = conn.root

        if args['--module'] == "raspistill":
            args[args['--action']] = True
            print(c.raspistill(args))

def get_module():
    return ClientModule()
