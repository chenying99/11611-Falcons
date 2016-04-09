__author__ = 'pbamotra'

import warnings


def deprecated(func):
    """
    This is a decorator which can be used to mark functions as deprecated.

    :param func: function to be marked as deprecated
    """

    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)   # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func