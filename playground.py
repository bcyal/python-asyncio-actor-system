## overall stuff
import asyncio
import logging

import falcon

from minions.actors.supervisor import Gru, RESUME, RESTART
from minions.actors.actor import Actor
from minions.actors.source import Source
from minions.actors.custom.routers import RandomRouter
from minions.actors.custom.routers import ShortestQueueRouter
from minions.actors.custom.routers import RoundRobinRouter
from minions.actors.custom.sources import ASGIRestApi
from minions.actors.custom.sources import ASGIWebServer


## Rest-Api Example
class TestRestRoot:
    def __init__(
        self,
        handler
    ):
        self._handler = handler
    
    async def on_get(self, req, resp):
        try:
            print(req)
            resp.content_type = falcon.MEDIA_TEXT
            resp.text = (
                'Hello World'
            )
            self._handler(
                "Hi","me"
            )
            print("get done!")
        except Exception as err:
            print(err)
        
        resp.status = falcon.HTTP_200


## Custom While-Loop-Server Example
class WatcherServer:
    def __init__(self, actor):
        self._actor = actor

    def start(self):
        self._loop = asyncio.create_task(
            self.watch()
        )

    async def stop(self):
        if not self._loop.done():
            try:
                self._loop.cancel()
                await self._loop
            except asyncio.CancelledError:
                pass

    async def watch(self):
        print("Staring Server")
        while True:
            await asyncio.sleep(1)
            try:
                print("Saw something!")
                # message = await self._actor._handler(
                #     "Wait for message",
                #     'me'
                # )
                self._actor._handler(
                    "Fire and Forget Message",
                    'me'
                )
                print("after handler")
                await asyncio.sleep(1)
                
            except Exception as err:
                print(
                    f"Stopping Server because:\n{err}"
                )
                break
        await self._actor.stop()
                

class WatcherActor(Source):
    def __init__(
        self,
        handler=None, 
        *args,
        **kwargs
        ):
        self._watcher = WatcherServer(self)
        self._handler = handler
        super().__init__(*args, **kwargs, server=self._watcher)
        if not handler:
            self._logger.warning(
                f"{self}: No handler registered!"
            )
        self._logger.info(
            f"{self} starts watching."
        )
    async def on_stop(self):
        print("in on_stop")


class EchoActor(Actor):
    def __init__(self,echo=None,test=None,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.echo = echo
        self.test = test

    async def handle_message(self, message, sender):
        await asyncio.sleep(1)
        print(f"I, {self.name}, got Message: {message}")
        exec("crash")
        return message


## Main stuff
async def main():

    async with Gru(policy=RESTART) as root:
        ## init router for incoming tests
        router = RoundRobinRouter(
            name="random-router",
            children=[
                EchoActor(
                    name=f"echo-actor-{n}",
                )
                for n in range(3)
            ],
            policy=RESTART
        )
        root.register_child(router)

        # ## test partial
        # partial_echo = EchoActor.prepare(test="TEST 1")
        # root.register_child(partial_echo)
        # print(root._children)
        
        ## test router to route stuff to EchoActor-Class
        # resp = await router("Hi","me")
        # await root.stop()

        # ## test custom while-loop server
        # source = WatcherActor(
        #     name="source-actor-1",
        #     handler=router
        # )
        # root.register_child(source)

        # # test rest-api
        # test_api_root = TestRestRoot(
        #     handler = router
        # )
        # app_rest = ASGIRestApi(
        #     routes={
        #         "/test": test_api_root
        #     }
        # )
        # source_rest = ASGIWebServer(
        #     name="rest-api",
        #     hostname="localhost",
        #     port=5001,
        #     app=app_rest,
        # )
        # root.register_child(source_rest)

        print("End of Gru")

    print("Out of Gru")


if __name__ ==  '__main__':
    asyncio.run(main())
    print("Out of main")
