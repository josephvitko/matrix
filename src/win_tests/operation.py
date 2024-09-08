import logging
from functools import wraps
from typing import Callable, Any


def operation(fn: Callable) -> Callable:
    """Decorator for file system operations."""
    name = fn.__name__

    @wraps(fn)
    def wrapper(self: 'InMemoryFileSystemOperations', *args: Any, **kwargs: Any) -> Any:
        head = args[0] if args else None
        tail = args[1:] if args else ()
        try:
            with self._thread_lock:
                result = fn(self, *args, **kwargs)
        except Exception as exc:
            logging.info(f" NOK | {name:20} | {head!r:20} | {tail!r:20} | {exc!r}")
            raise
        else:
            logging.info(f" OK! | {name:20} | {head!r:20} | {tail!r:20} | {result!r}")
            return result

    return wrapper
