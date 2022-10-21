import asyncio

from minions.actors.supervisor import Supervisor


class Router(Supervisor):
    def _route(self, message, sender):
        """Override in your own Router subclass"""
        raise NotImplementedError
    
    async def handle_message(self, message, sender):
        self._logger.debug(
            f"{self} received message {message} for routing"
        )
        try:
            target = self._route(message,sender)
            self._logger.debug(
                f"{self} is handing the message {message} "\
                f"from {sender} to {target}."
            )
            result = await target(message,sender)
            return result
        except Exception as err:
            self._logger.debug(
                f"{self} has failed to route {message} "\
                f"with {err}"
            )
            raise
    
    async def join(self):
        self._logger.debug(
            f"{self} is waiting for all children to finish"
        )
        for child in self._children:
            await child.join()