import asyncio
from collections.abc import Mapping
import logging

import falcon
import falcon.asgi
import uvicorn

from minions.actors.source import Source


## disable ctrl + c for uvicorn
class CustomUvicornServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        pass


class ASGIRestApi(falcon.asgi.App):
    def __init__(
        self,
        routes: Mapping={},
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger('top')
        self._routes = routes
        self.add_routes()

    def add_routes(self):
        for route, handler in self._routes.items()\
        if isinstance(self._routes, Mapping)\
        else {}:
            self.add_route(route, handler)
            self._logger.info(
                f"{self} has registered {handler}"\
                f" as handler for route '{route}'"
            )


class ASGIWebSession:
    def __init__(
        self,
        actor: Source,
        hostname: str,
        port: int,
        app: ASGIRestApi
    ) -> None:
        self._logger = logging.getLogger('top')
        self._actor = actor
        self._hostname = hostname
        self._port = port
        self._app = app
    
    def start(self):
        self._server = asyncio.create_task(
            self.serve()
        )
        
    async def serve(self):
        try:
            config = uvicorn.Config(
                self._app,
                host=self._hostname,
                port=self._port,
            )
            server = CustomUvicornServer(config)
            await server.serve()
        except Exception as err:
            self._logger.error(
                f"ASGIWebSession-Server crashed, because {err}."
            )
            await asyncio.sleep(1)
            await self._actor.stop()

    async def stop(self):
        if not self._server.done():
            try:
                self._server.cancel()
                await self._server
            except asyncio.CancelledError:
                pass


class ASGIWebServer(Source):
    def __init__(
        self,
        hostname: str,
        port: int,
        app: ASGIRestApi,
        *args,
        **kwargs
    ):
        self._hostname = hostname
        self._port = port
        self._app = app
        self._session = ASGIWebSession(
            actor=self,
            hostname=self._hostname,
            port=self._port,
            app=self._app,
        )
        super().__init__(
            *args,
            **kwargs,
            server=self._session
        )

    async def on_stop(self):
        self._logger.info(
            f"{self}: Entering on_stop."
        )
