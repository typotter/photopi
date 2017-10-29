from setuptools import setup, find_packages
# pylint: disable=no-name-in-module,F0401,W0232,C0111,R0201
import photopi

def readme():
    "Returns the contents of the README.md file"
    with open("README.md") as f:
        return f.read()

setup(
    name='photopi',
    version=photopi.__version__,
    description='Command line client for photopi',
    long_description=readme(),
    author='Tyler Potter',
    author_email='tyler.john.potter@gmail.com',
    url='http://github.com/typotter/photopi',
    packages=find_packages(),
    install_requires=[
        'setuptools',
        'docopt',
        'PyYAML'
    ],
    scripts=[
        'bin/photopi'
    ],
    test_suite="nose.collector",
)
