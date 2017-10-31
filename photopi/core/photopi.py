from datetime import datetime

def get_label_or_default(args):
    label = args['--label']
    if not label:
        label = datetime.now().strftime("%Y-%m-%d")
    return label
