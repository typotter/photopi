import os

from photopi.raspistill.spec import RaspistillSpec
from photopi.core.photopi import get_label_or_default, get_base_dir

TEST_FILE="test.jpg"

class RaspistillModule():
    def __init__(self):
        pass
    
    def main(self, args):
        print(args)

        if args["test"]:
            spec = RaspistillSpec.Test(path=get_base_dir(args))
       
            print(spec)

            spec.call()
            #spec = RaspistillSpec(label=get_label_or_default(args))
 
def get_module():
    return RaspistillModule()
