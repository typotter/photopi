import time

from photopi.raspistill.spec import RaspistillSpec
from photopi.core.photopi import get_label_or_default, get_base_dir

TEST_FILE="test.jpg"

class RaspistillModule():

    def __init__(self):
        self._threads = []
        pass
    
    def main(self, args):
        if args["test"]:
            spec = RaspistillSpec.Test(path=get_base_dir(args))
       
            spec.start()

            while True:
                time.sleep(1)
                print("still running")

                if not spec.is_alive():
                    break

            print(spec.output)
            print(spec.err)

            return spec.returncode == 0

def get_module():
    return RaspistillModule()
