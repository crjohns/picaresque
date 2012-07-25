class DoesNotExist(Exception):
    pass


class Handler:
    """
        Default cloak handler, which raises an exception
    """

    def handle(self, requested):
        raise DoesNotExist(requested)


class NullHandler(Handler):
    """
        Null handler, which returns None

        >>> handler = NullHandler()
        >>> print handler.handle("anything")
        None
    """

    def handle(self, requested):
        return None


# Cloak Resource Manager Interface
class Manager:

    handlers = dict()

    def pathtolist_(self, path):
        if path[0] == '/':
            path = path[1:]
        return path.split("/")

    def pathcatter_(self, pathlist):
        return '/'.join(pathlist)


    def addHandler(self, path, handler):
        pathlist = self.pathtolist_(path)
        self.handlers[self.pathcatter_(pathlist)] = handler

    def get(self, path):
        pathlist = self.pathtolist_(path)

        for index in xrange(len(pathlist)):
            for i2 in xrange(2):
                print "Trying", pathlist
                handler = self.handlers.get(self.pathcatter_(pathlist))
                if handler:
                    return handler.handle(path)
                pathlist[-1] = "*"
            pathlist = pathlist[:-1]

        raise DoesNotExist(path)






if __name__ in ["__builtin__", "__main__"]:
    import doctest
    doctest.testmod()
