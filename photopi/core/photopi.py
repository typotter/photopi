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

def get_remote_dir(args):
    rem = None
    if 'PHOTOPI_REMOTE_TIMELAPSE' in os.environ:
        rem = os.environ['PHOTOPI_REMOTE_TIMELAPSE']
    elif args['--remote']:
        rem = args['--remote']
    else:
        return None

    if ";" in rem:
        return rem.split(";")
    else:
        return rem
