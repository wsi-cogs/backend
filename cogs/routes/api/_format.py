from collections import namedtuple
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Type, TypeVar, Union

from aiohttp.web import Request, Response
import aiohttp.web
import json
from json.decoder import JSONDecodeError

from cogs.common.types import URL


class HTTPError(aiohttp.web.HTTPError):
    def __init__(self, *, status: int, message: str):
        self.status_code = status
        super(HTTPError, self).__init__(body=json.dumps({"status_message": message}, indent=4))


# Since even typing.Mapping is invariant in the key type, there's no good way
# to type-hint this, unfortunately.
def JSONResonse(*,
                links: Any = None,
                data: Any = None,
                items: Any = None,
                status: int=200,
                status_message="success") -> Response:
    if status == 204:
        # Returning a request body with a 204 (No Content) is invalid and leads
        # to subtle and hard-to-diagnose issues!
        assert all(x is None for x in [data, items, links])
        return Response(status=status)
    body: Dict[str, Any]
    if data is not None:
        body = {"links": links or {},
                "data": data}
    elif items is not None:
        body = {"links": links or {},
                "items": items}
    elif links is not None:
        body = {"links": links}
    elif status != 200:
        body = {}
    else:
        body = {"error": "Internal API error",
                "details": "Neither 'items' nor 'data' nor 'links' received"}
        status = 500
    body["status_message"] = status_message
    return Response(status=status,
                    body=json.dumps(body,
                                    indent=4))

T = TypeVar("T")


def get_match_info_or_error(request, match_info: Union[str, List[str]], lookup_function: Callable[..., T]) -> T:
    object_id: Union[int, List[int]]
    if isinstance(match_info, str):
        object_id = match_info_to_id(request, match_info)
        database_model = lookup_function(object_id)
    else:
        object_id = [match_info_to_id(request, match) for match in match_info]
        database_model = lookup_function(*object_id)

    if database_model is None:
        raise HTTPError(status=404,
                        message=f"The specified {match_info} ({object_id}) does not exist")
    return database_model


def match_info_to_id(request: Request, match_info: str) -> int:
    try:
        return int(request.match_info[match_info])
    except ValueError:
        raise HTTPError(status=404,
                        message=f"{match_info} ({request.match_info[match_info]}) not an integer")


# TODO: can the types for this be made any better?
async def get_params(request: Request, params: Dict[str, Type]) -> Any:
    if request.method in ["POST", "PUT"]:
        try:
            post = await request.json()
        except JSONDecodeError:
            raise HTTPError(status=403,
                            message="Invalid JSON")
    elif request.method in ["GET"]:
        query = request.rel_url.query
        post = {}
        for key in query.keys():
            post[key.rstrip("[]")] = query.getall(key)

    if not all(required in post for required in params):
        param_names_types = {k: v.__name__ if isinstance(v, type) else str(v).replace('typing.', '')
                             for k, v in params.items()}
        raise HTTPError(status=400,
                        message=f"Not all required parameters given ({param_names_types}). "
                                f"Received: {', '.join(repr(p) for p in post)}")

    rtn_type = NamedTuple("JSONRequest", params.items())  # type: ignore
    rtn: NamedTuple = rtn_type(*(post[param] for param in params))  # type: ignore
    _check_types(rtn)
    return rtn


# TODO: this should be rewritten to use typing-inspect rather than
# relying on the internals of the typing module.
def _check_types(named_tuple: NamedTuple):
    def check_iter(params: Union[NamedTuple, Iterable], types: Iterable[Type]):
        for param, type in zip(params, types):
            try:
                args = type.__args__
                name = type._name
            except AttributeError:
                if not isinstance(param, type):
                    type_name = getattr(type, "__name__", type)
                    raise HTTPError(status=400,
                                    message=f"JSON argument {repr(param)} is not a {repr(type_name)}")
            else:
                new_params: Iterable
                if name == "List":
                    if len(args) != 1:
                        raise HTTPError(status=500,
                                        message="Type checking lists only supports 1 argument (parsing JSON)")
                    if not isinstance(param, list):
                        raise HTTPError(status=400,
                                        message=f"JSON argument {repr(param)} is not a list")
                    iter_type = args[0]
                    new_params = param
                elif name == "Dict":
                    if len(args) != 2:
                        raise HTTPError(status=500,
                                        message="Type checking dicts only supports 2 arguments (parsing JSON)")
                    if args[0] is not str:
                        raise HTTPError(status=500,
                                        message="Type checking dicts only supports a string key (parsing JSON)")
                    if not isinstance(param, dict):
                        raise HTTPError(status=400,
                                        message=f"JSON argument {repr(param)} is not a dict")
                    iter_type = args[1]
                    new_params = param.values()
                elif name is None:
                    # Should be `Optional` only.
                    check_iter([param], [args])
                else:
                    raise HTTPError(status=500,
                                    message=f"Only supported `typing` types are `List` and `Dict`. Got {name}[{args}]")
                if name is not None:
                    new_types = [iter_type for _ in new_params]
                    check_iter(new_params, new_types)
    check_iter(named_tuple, named_tuple._field_types.values())
