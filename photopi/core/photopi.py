import os

from datetime import datetime

def get_label_or_default(args):
    label = args['--label']
    if not label:
        label = datetime.now().strftime("%Y-%m-%d")
    return label

def get_base_dir(args):
    if 'PHOTOPI_LOCAL_TIMELAPSE' in os.environ:
        return os.environ['PHOTOPI_LOCAL_TIMELAPSE']
    elif args['--base']:
        return args['--base']
    else:
        return os.getcwd()
