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


class FastAPI(Starlette):
  def __init__(
    self: AppType,
    *,
    debug: Annotated[bool, Doc(""),] = False,
    routes: Annotated[Optional[List[BaseRoute]], Doc(""),deprecated(),] = None,
    title: Annotated[str, Doc(""),] = "FastAPI",
    summary: Annotated[Optional[str], Doc(""),] = None,
    description: Annotated[str, Doc(""),] = "",
    version: Annotated[str, Doc(""),] = "0.1.0",
    openapi_tags: Annotated[Optional[List[Dict[str, Any]]], Doc(""),] = None,
    servers: Annotated[Optional[List[Dict[str, Union[str, Any]]]], Doc(""),] = None,
    dependencies: Annotated[Optional[Sequence[Depends]], Doc(""),] = None,
    default_response_class: Annotated[Type[Response], Doc(""),] = Default(HSONResponse),
    redirect_slashes: Annotated[bool, Doc(""),] = True,
    docs_url: Annotated[Optional[str], Doc(""),] = "/docs",
    redoc_url: Annotated[Optional[str], Doc(""),] = "/redoc",
    swagger_ui_oauth2_redirect_url: Annotated[Optional[str], Doc(""),] = "/docs/oauth2-redirect",
    swagger_ui_init_oauth: Annotated[Optional[Dict[str, Any]], Doc(""),] = None,
    middleware: Annotated[Optional[Sequence[Middleware]], Doc(""),] = None,
    exception_handlers: Annotated[
            Optional[Dict[Union[int, Type[Exception]],Callable[[Request, Any], Coroutine[Any, Any, Response]],]],Doc(""),] = None,
    on_startup: Annotated[Optional[Sequence[Callable[[], Any]]], Doc(""),] = None,
    on_shutdown: Annotated[Optional[Sequence[Callable[[], Any]]], Doc(""),] = None,
    lifespan: Annotated[Optional[Lifespan[AppType]], Doc(""),] = None,
    terms_of_service: Annotated[Optional[str], Doc(""),] = None,
    contact: Annotated[Optional[Dict[str, Union[str, Any]]],Doc(""),] = None,
    license_info: Annotated[Optional[Dict[str, Union[str, Any]]],Doc(""),] = None,
    openapi_prefix: Annotated[str,Doc(""),deprecated(),] = "",
    root_path: Annotated[str,Doc(""),] = "",
    root_path_in_servers: Annotated[bool, Doc(""),] = True,
    responses: Annotated[Optional[Dict[Union[int, str], Dict[str, Any]]],Doc(""),] = None,
    callbacks: Annotated[Optional[List[BaseRoute]],Doc(""),] = None,
    webhooks: Annotated[Optional[routing.APIRouter],Doc(""),] = None,
    deprecated: Annotated[Optional[bool],Doc(""),] = None,
    include_in_schema: Annotated[bool, Doc(""),] = True,
    swagger_ui_parameters: Annotated[Optional[Dict[str, Any]],Doc(""),] = None,
    generate_unique_id_function: Annotated[Callable[[routing.APIRoute], str],Doc(""),] = Default(generate_unique_id),
    separate_input_output_schemas: Annotated[bool, Doc(""),] = True,
    openapi_external_docs: Annotated[Optional[Dict[str, Any]],Doc(""),] = True,
    **extra: Annotated[Any,Doc(""),],) -> None:
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
