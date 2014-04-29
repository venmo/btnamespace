import collections


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
