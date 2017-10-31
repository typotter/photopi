from photopi.core.borg import Borg

class RaspistillModule(Borg):
    def __init__(self):
        pass
    
    def main(self, args):
        print("RPIstill Module")

def get_module():
    return RaspistillModule()
