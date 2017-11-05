import os, time

from photopi.raspistill.cmd import RaspistillCmd
from photopi.core.photopi import get_label_or_default, get_base_dir

class RaspistillModule():

    def __init__(self):
        self._threads = []
        pass
    
    def main(self, args):
        if args["test"]:
            return self._do_test(args)
        if args["tl"]:
           return self._do_timelapse(args)


    def _do_timelapse(self, args):
        spec = RaspistillCmd.Timelapse(
            label=get_label_or_default(args),
            path=get_base_dir(args),
            interval=args['--interval'],
            timeout=args['--timeout'])

        os.makedirs(spec.path, exist_ok=True)
  
        return self._run_spec(spec)


    def _do_test(self, args):
        spec = RaspistillCmd.Test(path=get_base_dir(args))

        return self._run_spec(spec)

    def _run_spec(self, spec):
        spec.start()

        while True:
            time.sleep(1)
            if not spec.is_alive():
                break

        print(str(spec.output))
        print(str(spec.err))

        return spec.returncode == 0

def get_module():
    return RaspistillModule()
