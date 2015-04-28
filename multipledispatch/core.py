from contextlib import contextmanager
from warnings import warn
import inspect
from .dispatcher import Dispatcher, MethodDispatcher, ambiguity_warn


global_namespace = dict()

def adispatch(**kwargs):
    """ Dispatch function on the types in annotations.

    Supports dispatch on all non-keyword arguments.
    Сollects implementations based on the function/method name, ignores namespaces.

    If ambiguous type signatures occur a warning is raised when the function is
    defined suggesting the additional method to break the ambiguity.

    Examples
    --------

    >>> @dispatch()
    ... def f(x: int):
    ...     return x + 1

    >>> @dispatch()
    ... def f(x: float):
    ...     return x - 1

    >>> f(3)
    4
    >>> f(3.0)
    2.0

    Specify an isolated namespace with the namespace keyword argument

    >>> my_namespace = dict()
    >>> @dispatch(namespace=my_namespace)
    ... def foo(x: int):
    ...     return x + 1

    Dispatch on instance methods within classes

    >>> class MyClass(object):
    ...     @dispatch()
    ...     def __init__(self, data: list):
    ...         self.data = data
    ...     @dispatch()
    ...     def __init__(self, datum: int):
    ...         self.data = [datum]
    """
    namespace = kwargs.get('namespace', global_namespace)
    on_ambiguity = kwargs.get('on_ambiguity', ambiguity_warn)

    def _(fun: callable) -> callable:
        name = fun.__name__
        faspec = inspect.getfullargspec(fun)
        arg, ann = faspec.args, faspec.annotations
        method = False
        has_ret_ann = False
        types = []
        if arg:
            if arg[0] == 'self':
                method = True
            for a in arg:
                if a in ann:
                    types.append(ann[a])
        if 'return' in ann:
            has_ret_ann = True
            ret = ann['return']
        if method:
            dispatcher = inspect.currentframe().f_back.f_locals.get(name,
                MethodDispatcher(name))
        else:
            if name not in namespace:
                namespace[name] = Dispatcher(name)
            dispatcher = namespace[name]

        dispatcher.add(tuple(types), fun, on_ambiguity=on_ambiguity)
        return dispatcher
    return _

def dispatch(*types, **kwargs):
    """ Dispatch function on the types of the inputs

    Supports dispatch on all non-keyword arguments.

    Collects implementations based on the function name.  Ignores namespaces.

    If ambiguous type signatures occur a warning is raised when the function is
    defined suggesting the additional method to break the ambiguity.

    Examples
    --------

    >>> @dispatch(int)
    ... def f(x):
    ...     return x + 1

    >>> @dispatch(float)
    ... def f(x):
    ...     return x - 1

    >>> f(3)
    4
    >>> f(3.0)
    2.0

    Specify an isolated namespace with the namespace keyword argument

    >>> my_namespace = dict()
    >>> @dispatch(int, namespace=my_namespace)
    ... def foo(x):
    ...     return x + 1

    Dispatch on instance methods within classes

    >>> class MyClass(object):
    ...     @dispatch(list)
    ...     def __init__(self, data):
    ...         self.data = data
    ...     @dispatch(int)
    ...     def __init__(self, datum):
    ...         self.data = [datum]
    """
    namespace = kwargs.get('namespace', global_namespace)
    on_ambiguity = kwargs.get('on_ambiguity', ambiguity_warn)

    types = tuple(types)
    def _(func):
        name = func.__name__

        if ismethod(func):
            dispatcher = inspect.currentframe().f_back.f_locals.get(name,
                MethodDispatcher(name))
        else:
            if name not in namespace:
                namespace[name] = Dispatcher(name)
            dispatcher = namespace[name]

        dispatcher.add(types, func, on_ambiguity=on_ambiguity)
        return dispatcher
    return _

def ismethod(func):
    """ Is func a method?

    Note that this has to work as the method is defined but before the class is
    defined.  At this stage methods look like functions.
    """
    spec = inspect.getfullargspec(func)
    return spec and spec.args and spec.args[0] == 'self'
