import os


def get_current_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_libs_path():
    current_path = get_current_path()
    return os.path.join(current_path, "../../../libs")
