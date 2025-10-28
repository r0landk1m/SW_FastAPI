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
    version: Annotated[str, Doc(""),] = "0.1.0", #1 버전
    openapi_url: Annotated[Optional[str], Doc(""),] = "/openapi.json", #1 API URL 경로
    openapi_tags: Annotated[Optional[List[Dict[str, Any]]], Doc(""),] = None, #1 경로 그룹화 태그 정보
    servers: Annotated[Optional[List[Dict[str, Union[str, Any]]]], Doc(""),] = None, #1 서버 환경의 URL 목록
    dependencies: Annotated[Optional[Sequence[Depends]], Doc(""),] = None, #2 전역 의존성 설정
    default_response_class: Annotated[Type[Response], Doc(""),] = Default(JSONResponse), #2 반환시 사용할 기본 응답 클래스
    redirect_slashes: Annotated[bool, Doc(""),] = True, #2 끝에 "/" 있는 경로에 요청 시 올바른 경로로 리디렉션
    docs_url: Annotated[Optional[str], Doc(""),] = "/docs", #1 문서 페이지 URL
    redoc_url: Annotated[Optional[str], Doc(""),] = "/redoc", #1 다른 스타일의 문서 URL
    swagger_ui_oauth2_redirect_url: Annotated[Optional[str], Doc(""),] = "/docs/oauth2-redirect", #5
    swagger_ui_init_oauth: Annotated[Optional[Dict[str, Any]], Doc(""),] = None, #5
    middleware: Annotated[Optional[Sequence[Middleware]], Doc(""),] = None, #4 미들웨어 목록 지정
    exception_handlers: Annotated[ #4 특정 예외 상황시 사용자 정의 예외 처리 함수 등록
            Optional[Dict[Union[int, Type[Exception]],Callable[[Request, Any], Coroutine[Any, Any, Response]],]],Doc(""),] = None,
    on_startup: Annotated[Optional[Sequence[Callable[[], Any]]], Doc(""),] = None, #3 서버가 실행될 때 실행할 함수
    on_shutdown: Annotated[Optional[Sequence[Callable[[], Any]]], Doc(""),] = None, #3 서버가 종료될 때 실행할 함수
    lifespan: Annotated[Optional[Lifespan[AppType]], Doc(""),] = None, #3 최신 방식의 생명주기 관리자 (위 2개 보완)
    terms_of_service: Annotated[Optional[str], Doc(""),] = None, #1 서비스 이용 약관 페이지 URL
    contact: Annotated[Optional[Dict[str, Union[str, Any]]],Doc(""),] = None, #1 개발자 연락처
    license_info: Annotated[Optional[Dict[str, Union[str, Any]]],Doc(""),] = None, #1 라이선스 정보
    openapi_prefix: Annotated[str,Doc(""),deprecated(),] = "",
    root_path: Annotated[str,Doc(""),] = "", #2 리버스 프록시 뒤에서 실행 시에 경로의 접두사를 알려주는데 사용
    root_path_in_servers: Annotated[bool, Doc(""),] = True,
    responses: Annotated[Optional[Dict[Union[int, str], Dict[str, Any]]],Doc(""),] = None,
    callbacks: Annotated[Optional[List[BaseRoute]],Doc(""),] = None,
    webhooks: Annotated[Optional[routing.APIRouter],Doc(""),] = None,
    deprecated: Annotated[Optional[bool],Doc(""),] = None, #5
    include_in_schema: Annotated[bool, Doc(""),] = True, #5
    swagger_ui_parameters: Annotated[Optional[Dict[str, Any]],Doc(""),] = None, #5
    generate_unique_id_function: Annotated[Callable[[routing.APIRoute], str],Doc(""),] = Default(generate_unique_id), #5
    separate_input_output_schemas: Annotated[bool, Doc(""),] = True,
    openapi_external_docs: Annotated[Optional[Dict[str, Any]],Doc(""),] = True, #6 root_path 로 대체
    **extra: Annotated[Any,Doc(""),],) -> None: #5 커스텀 필드
      self.debug = debug
        self.title = title
        self.summary = summary
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        self.root_path_in_servers = root_path_in_servers
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.swagger_ui_parameters = swagger_ui_parameters
        self.servers = servers or []
        self.separate_input_output_schemas = separate_input_output_schemas
        self.openapi_external_docs = openapi_external_docs
        self.extra = extra
        self.openapi_version: Annotated[str,Doc(""),] = "3.1.0"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        if self.openapi_url:
          assert self.title, "A title must be provided for OpenAPI, e.g.: 'My API'"
          assert self.version, "A version must be provided for OpenAPI, e.g.: '2.1.0'"
        if openapi_prefix:
            logger.warning(
                '"openapi_prefix" has been deprecated in favor of "root_path", which '
                "follows more closely the ASGI standard, is simpler, and more "
                "automatic. Check the docs at "
                "https://fastapi.tiangolo.com/advanced/sub-applications/"
            )
        self.webhooks: Annotated[routing.APIRouter,Doc(""),] = webhooks or routing.APIRouter()
        self.root_path = root_path or openapi_prefix
        self.state: Annotated[State,Doc(""),] = State()
        self.dependency_overrides: Annotated[Dict[Callable[..., Any], Callable[..., Any]],Doc(""),] = {}
        self.router: routing.APIRouter = routing.APIRouter(
            routes=routes,
            redirect_slashes=redirect_slashes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
        )
        self.exception_handlers: Dict[
            Any, Callable[[Request, Any], Union[Response, Awaitable[Response]]]
        ] = {} if exception_handlers is None else dict(exception_handlers)
        self.exception_handlers.setdefault(HTTPException, http_exception_handler)
        self.exception_handlers.setdefault(
            RequestValidationError, request_validation_exception_handler
        )
        self.exception_handlers.setdefault(
            WebSocketRequestValidationError,
            # Starlette still has incorrect type specification for the handlers
            websocket_request_validation_exception_handler,  # type: ignore
        )

        self.user_middleware: List[Middleware] = (
            [] if middleware is None else list(middleware)
        )
        self.middleware_stack: Union[ASGIApp, None] = None
        self.setup()
