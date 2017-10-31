import os

class RaspistillSpec():

    def Test(path=None):
        spec = RaspistillSpec(output = os.path.join(path, "test.jpg"))
        return spec

    def __init__(self, label=None, output=None):
        self.label = label
        self.output = output

    def __str__(self):
        return str(self.__dict__)

    def call(self):
        print("raspistill cmd")

        print("raspistill -o {}".format(self.output))
