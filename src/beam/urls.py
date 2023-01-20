from logging import getLogger
from typing import Callable, Dict, Optional, Union

from django.db.models import Model
from django.http import HttpRequest

logger = getLogger(__name__)


undefined = (
    object()
)  # sentinel value for attributes not defined or overwritten on the viewset


UrlKwargGetter = Callable[[Optional[Model], Optional[HttpRequest]], Optional[str]]
"""
A callable that takes an instance and a request and may return a string
as the value for a url kwarg.
"""


UrlKwargDict = Dict[str, Union[str, UrlKwargGetter]]
"""
A dict used to specify url kwargs
"""


def request_kwarg(name: str) -> UrlKwargGetter:
    """
    Return a getter for use in an url_kwargs dict that retrieves a kwarg
    from the request resolver match.
    """

    def getter(obj=None, request=None):
        if request and request.resolver_match and request.resolver_match.kwargs:
            return request.resolver_match.kwargs.get(name, None)
        return None

    return getter
