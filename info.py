from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from annotated_doc import Doc
from fastapi import routing
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    websocket_request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.logger import logger
from fastapi.middleware.asyncexitstack import AsyncExitStackMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends
from fastapi.types import DecoratedCallable, IncEx
from fastapi.utils import generate_unique_id
from starlette.applications import Starlette
from starlette.datastructures import State
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, ExceptionHandler, Lifespan, Receive, Scope, Send
from typing_extensions import Annotated, deprecated

AppType = TypeVar("AppType", bound="FastAPI")

#1 데이터 설정
#2 핵심 동작
#3 생명 주기
#4 미들웨어 및 예외처리
#5 고급 설정
#6 not use 
class FastAPI(Starlette):
  def __init__(
    self: AppType,
    *,
    debug: Annotated[bool, Doc(""),] = False, #2 디버깅 정보 페이지
    routes: Annotated[Optional[List[BaseRoute]], Doc(""),deprecated(),] = None, #2 초기 라우트 목록 보통 사용x
    title: Annotated[str, Doc(""),] = "FastAPI", #1 API 이름
    summary: Annotated[Optional[str], Doc(""),] = None, #1 API 한 줄 요약
    description: Annotated[str, Doc(""),] = "", #1 상세 설명
    version: Annotated[str, Doc(""),] = "0.분
def get_request_handler(
    dependant: Dependant, #엔드포인트 함수에 대한 모든 정보
    body_field: Optional[ModelField] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    response_field: Optional[ModelField] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    dependency_overrides_provider: Optional[Any] = None,
    embed_body_fields: bool = False,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    assert dependant.call is not None, "dependant.call must be a function" #dependent.call 개발자가 작성한 함수
    is_coroutine = iscoroutinefunction(dependant.call) #async def check
    is_body_form = body_field and isinstance(
        body_field.field_info, (params.Form, temp_pydantic_v1_params.Form)
    )
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

# starlette def 함수 투척
async def run_in_threadpool(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    func = functools.partial(func, *args, **kwargs)
    return await anyio.to_thread.run_sync(func)
