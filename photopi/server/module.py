import rpyc, time

from rpyc.utils.server import ThreadedServer
from threading import Thread


from photopi.core.borg import Borg
import photopi.raspistill.module


class MyService(rpyc.Service):
    def on_connect(self):
        pass
    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_raspistill(self, args):
        return photopi.raspistill.module.get_module().main(args)


class ServerModule(Borg):
    def __init__(self):
        Borg.__init__(self)


    def main(self, args):
        print(args)

        # start the rpyc server
        server = ThreadedServer(MyService, port = int(args['--port']))
        t = Thread(target = server.start)
        t.daemon = True
        t.start()

        # the main logic
        while True:
            time.sleep(1)
            print("run")

def get_module():
    return ServerModule()


