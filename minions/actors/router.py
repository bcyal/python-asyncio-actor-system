import asyncio

from minions.actors.actor import Actor
from minions.actors.supervisor import Supervisor


class Router(Supervisor):
    def __call__(
        self, 
        message, 
        sender
        ):
        if self.status is not Actor.RUNNING or self._worker.done():
            raise asyncio.CancelledError()
        if any(
            ch.status is not Actor.RUNNING 
            or ch._worker.done() for ch in self._children
            ):
            raise asyncio.CancelledError()
        self._logger.debug(
            f"{self} received message {message} for routing"
        )        
        try:
            target = self._route(message,sender)
        except Exception as err:
            self._logger.debug(
                f"{self} has failed to route {message} "\
                f"with {err}"
            )
            raise
        self._logger.debug(
            f"{self} is handing the message {message} "\
            f"from {sender} to {target}."
        )
        result = target._loop.create_future()
        target._inbox.put_nowait((message, sender, result))
        return result
    
    def _route(self, message, sender):
        """Override in your own Router subclass"""
        raise NotImplementedError
