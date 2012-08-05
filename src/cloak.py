def path2list(path):
    """
        Convert a cloak path to a list representing
        the path.

        >>> path2list("/a/b/c/d/e/f/great")
        ['a', 'b', 'c', 'd', 'e', 'f', 'great']
    """
    if path[0] == '/':
        path = path[1:]
    return path.split("/")

def list2path(pathlist):
    """
        Convert a list into a cloak path

        >>> list2path(["a", "b", "c", "drive"])
        'a/b/c/drive'
    """
    return '/'.join(pathlist)




class DoesNotExist(Exception):
    """
        Exception to be raised when a handler does not exist
    """
    pass


class Handler:
    """
        Default cloak handler, which raises an exception
        Extend this class to implement your own handlers
    """

    def handle(self, requested, attrs):
        raise DoesNotExist(requested)

    def setManager(self, manager):
        self.manager = manager


class NullHandler(Handler):
    """
        Null handler, which returns None

        >>> handler = NullHandler()
        >>> print handler.handle(["anything"], None)
        None
    """

    def handle(self, requested, attrs):
        return None

class LambdaHandler(Handler):
    """
        Handler whose handle function calls the
        lambda function passed in at creation.

        >>> lh = LambdaHandler(lambda x,y: x[-1])
        >>> lh.handle(['hi','you'], None)
        'you'
    """

    def __init__(self, fn):
        self.fn = fn

    def handle(self, requested, attrs):
        return self.fn(requested, attrs)


# Cloak Resource Manager Interface
class Manager:
    """
        Main cloak class
        This is the main class for the cloak library.

        This class maps strings such as "/art/ball.jpg" to
        handlers which can construct the object that is described by
        the string.

        Handlers may be registered under specific paths such as
        "/art/ball.jpg" or they may have wildcards such as "/art/*".

        The most specific handler which matches the given string will be used.
        If handler A is mapped under "/art/*" and handler B is mapped under
        "/art/ball.jpg" then calling get("/art/ball.jpg") will use B while
        get("/art/other.jpg") will use A.

        >>> man = Manager()
        >>> man.addHandler("*", NullHandler())
        >>> handle = LambdaHandler(lambda x, y: x[1])
        >>> handle.handle(['letters', 'a'], None)
        'a'
        >>> man.addHandler("/letters/*", handle)
        >>> man.addHandler("/letters", LambdaHandler(lambda x,y: 1))
        >>> man.get("/letters/b")
        'b'
        >>> man.get("/letters")
        1
        >>> man.addHandler("/numbers", LambdaHandler(lambda x,y: 2))
        >>> print man.get("/numbers/4")
        None
        >>> print man.get("/numbers")
        2
        >>> man.addHandler("/attrtest", LambdaHandler(lambda x,y: y['name']))
        >>> print man.get("/attrtest", {'name': 'testme'})
        testme

    """

    handlers = dict()


    def __init__(self):
        self.addHandler("*", Handler())


    def addHandler(self, path, handler):
        pathlist = path2list(path)
        self.handlers[list2path(pathlist)] = handler
        handler.setManager(self)

    def get(self, path, attrs = None):
        pathlist = path2list(path)

        # Try a perfect match
        handler = self.handlers.get(list2path(pathlist))

        if not handler:
            # Perfect match failed, try wildcards
            for index in xrange(len(pathlist)):
                pathlist[-1] = "*"
                handler = self.handlers.get(list2path(pathlist))
                if handler:
                    break
                else:
                    pathlist = pathlist[:-1]

        if handler:
            return handler.handle(path2list(path), attrs)
        else:
            raise DoesNotExist(path)



if __name__ in ["__main__"]:
    import doctest
    print "Running doctest"
    doctest.testmod()

    print "Do comprehensive test"

    man = Manager()
    man.addHandler("/letters/*", LambdaHandler(
            lambda x,y:
                x[1] if len(x) == 2
                                   and len(x[1]) == 1
                                else
                                   None))

    lh = LambdaHandler(lambda x,y:
                            lh.manager.get("/letters/a") +
                            lh.manager.get("/letters/b") +
                            lh.manager.get("/letters/c"))

    man.addHandler("/string", lh)

    if man.get("/string") == "abc":
        print "Passed"
    else:
        print "Failed"




    print "Done"
