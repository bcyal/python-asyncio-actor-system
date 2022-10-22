import asyncio
from types import SimpleNamespace
from contextlib import suppress
from itertools import count
import logging, sys, weakref
from functools import partial


class ActorStatus:
    def __init__(self,identifier):
        self.__ident__ = identifier
    
    def __str__(self):
        return self.__ident__


class Actor:
    id_iter = count()
    
    RUNNING = ActorStatus("RUNNING")
    STOPPING = ActorStatus("STOPPING")
    STOPPED = ActorStatus("STOPPED")
    CRASHED = ActorStatus("CRASHED")

    def __init__(
        self, 
        name=None, 
        actor_ttl=None, 
        actor_timeout=None,
        **kwargs
        ):
        self.context = SimpleNamespace(**kwargs)
        self._logger = logging.getLogger('top')
        self._loop = asyncio.get_event_loop()
        self._inbox = asyncio.Queue()
        self._timeout = actor_timeout
        self._ttl = actor_ttl
        self.name = name if name else f"actor-{next(Actor.id_iter)}"
        self.start()
    
    def __str__(self):
        return f"<{type(self).__name__} \"{self.name}\">"

    def __call__(
        self, 
        message, 
        sender
        ):
        if self.status is not Actor.RUNNING or self._worker.done():
            raise asyncio.CancelledError()
        self._logger.debug(f"{self} received {message}")
        result = self._loop.create_future()
        self._inbox.put_nowait((message, sender, result))
        return result
    
    async def handle_message(self, message, sender):
        """Override in your own Actor subclass"""
        raise NotImplementedError(
            'Please subclass Actor and implement handle_message() method'
            )
    
    async def on_stop(self):
        """Override in your own Actor subclass if needed"""
        pass
    
    @classmethod
    def prepare(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)
    
    def start(self):
        self._worker = self._loop.create_task(self._handle())
        self.status = Actor.RUNNING

    async def _handle(self):
        ## TODO: Create Timer ttl with custom Timeout class
        try:
            while True:
                message, sender, result = await self._inbox.get()
                self._logger.debug(
                    f"{self} took {message} from mailbox"
                    )
                try:
                    self._logger.debug(
                        f"{self} starts handling {message}"
                        )
                    coro = self.handle_message(message, sender)
                    answer = await asyncio.wait_for(
                        coro, 
                        timeout=self._timeout
                        )
                    result.set_result(answer)
                    self._inbox.task_done()
                except asyncio.CancelledError as err:
                    result.set_exception(err)
                    self._inbox.task_done()
                except asyncio.TimeoutError as err:
                    result.set_exception(err)
                    self._inbox.task_done()
        except Exception as err:
            self.status = Actor.CRASHED
            result.set_exception(err)
            self._inbox.task_done()
            self._logger.error(f"{self} crashed with:\n{err}")
        finally:
            self._logger.debug(f"{self} is executing on_stop()")
            try:
                await self.on_stop()
            except Exception as err:
                self.status = Actor.CRASHED
                self._logger.error(
                    f"{self} crashed while executing on_stop() with:"\
                    f"\n{err}"
                )
            self._logger.debug(
                f"{self} has finished on_stop()"
            )
            if self.status is Actor.CRASHED:
                if hasattr(self, "_parent") and self._parent:
                    await self._parent._handle_child(
                        self, 
                        "crashed"
                    )
    
    def stop(self):
        if self.status is not Actor.STOPPED:
            self._logger.debug(f"{self} received order to stop.")
            self.status = Actor.STOPPING
            return self._loop.create_task(self._stop())
        else:
            self._logger.debug(f"{self} is already stopped.")

    async def _stop(self):
        self._logger.debug(
            f"{self} is waiting for remaining messages to be processed."
            )
        await self.join()
        if not self._worker.done():
            try:
                self._worker.cancel()
                await self._worker
            except asyncio.CancelledError:
                pass
        self.status = Actor.STOPPED
        if hasattr(self, "_parent") and self._parent:
            await self._parent._handle_child(
                self, 
                "stopped"
            )
    
    def restart(self):
        return self._loop.create_task(self._restart())

    async def _restart(self):
        if self.status is Actor.RUNNING:
            await self.stop()
        if self.status in [Actor.STOPPED,Actor.CRASHED]:
            self.start()

    def register_parent(self, parent):
        self._parent = weakref.proxy(parent)
        self._logger.debug(
            f"{self} registered {parent} as its parent."
            )
    
    def unregister_parent(self, parent):
        self._parent = None
        self._logger.debug(
            f"{self} unregistered {parent} as its parent."
            )
    
    async def join(self):
        await self._inbox.join()
