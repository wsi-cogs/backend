from cogs.common.types import URL
from typing import List, Dict, Optional, Union, Any, NamedTuple, Type, Iterable

from aiohttp.web import Request, Response
import aiohttp.web
import json
from json.decoder import JSONDecodeError


class HTTPError(aiohttp.web.HTTPError):
    def __init__(self, *, status: int, message: str):
        self.status_code = status
        super(HTTPError, self).__init__(body=json.dumps({"status_message": message}, indent=4))


def JSONResonse(*,
                links: Optional[Dict[str, Union[Dict[str, URL], URL]]]=None,
                data: Optional[Dict[str, Any]]=None,
                items: Optional[List[Dict[str, Any]]]=None,
                status: int=200,
                status_message="success") -> Response:
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
                                    indent=4),
                    headers={"Access-Control-Allow-Origin": "*"})


def get_match_info_or_error(request, match_info: Union[str, List[str]], lookup_function):
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


async def get_post(request: Request, params: Dict[str, Type]) -> NamedTuple:
    try:
        post = await request.json()
    except JSONDecodeError:
        raise HTTPError(status=403,
                        message="Invalid JSON")

    if not all(required in post for required in params):
        param_names_types = {k: v.__name__ if isinstance(v, type) else str(v).replace('typing.', '')
                             for k, v in params.items()}
        raise HTTPError(status=400,
                        message=f"Not all required parameters given ({param_names_types}). "
                                f"Received: {', '.join(repr(p) for p in post)}")

    rtn_type = NamedTuple("JSONRequest", params.items())
    rtn = rtn_type(*(post[param] for param in params))
    _check_types(rtn)
    return rtn


def _check_types(named_tuple: NamedTuple):
    def check_iter(params: NamedTuple, types: Iterable[Type]):
        for param, type in zip(params, types):
            if isinstance({}, type) or isinstance([], type):
                args = type.__args__
                name = type._name
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
                else:
                    raise HTTPError(status=500,
                                    message="Only supported `typing` types are `List` and `Dict`")
                new_types = [iter_type for _ in new_params]
                check_iter(new_params, new_types)
            elif isinstance(param, type):
                pass
            else:
                raise HTTPError(status=400,
                                message=f"JSON argument {repr(param)} is not a {repr(type.__name__)}")
    check_iter(named_tuple, named_tuple._field_types.values())
