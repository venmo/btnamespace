import collections
import inspect


ResourceId = collections.namedtuple('ResourceId', ['bt_class', 'action'])
CallSchema = collections.namedtuple('CallSchema', ['bt_class', 'method_name',
                                                   'start_hook', 'params'])


class NamespaceError(Exception):
    pass


class UnsupportedSearchNode(object):
    def __eq__(*_):
        raise NamespaceError("Advanced search on ids or tokens not allowed.")

    def __ne__(*_):
        raise NamespaceError("Advanced search on ids or tokens not allowed.")

    def __getattribute__(*_):
        raise NamespaceError("Advanced search on ids or tokens not allowed.")


def get_caller_args(stack_level=2):
    """Return a tuple containing a dictionary of named arguments
    and a list of unnamed positional arguments.

    :attr stack_level: determine how far up to traverse the stack,
      eg 1 == the caller of this function, 2 == the caller of that caller, etc.

    source: http://kbyanc.blogspot.com/2007/07/python-aggregating-function-arguments.html
    """

    posname, kwname, args = inspect.getargvalues(inspect.stack()[stack_level][0])[-3:]
    posargs = args.pop(posname, [])
    args.update(args.pop(kwname, []))

    return args, posargs
