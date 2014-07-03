import os

metadata = {
    'parents': ['tek'],
    'files': [os.path.join(os.path.dirname(__file__), 'mod1.conf')],
    'std_files': False,
}


def reset_config():
    return {'sec1': {'key1': 'val1'}}

__all__ = ['reset_config']
