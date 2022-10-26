import asyncio

from minions.actors.supervisor import Supervisor


class Router(Supervisor):
    
    ## FIXME: NOT WORKING !!!!!!
    ## Router is blocking (Quesize of Router is going up)
    ## and throwing CanceledError after Cancel
    ## probably need to redo the _handle method instead of
    ## handle_message-method
    ## Custom routers are doing what they are supposed to do
    async def handle_message(self, message, sender):
        """
        Router only need this handle_message-method
        """
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
        result = await target(message,sender)
        return result
    
    def _route(self, message, sender):
        """Override in your own Router subclass"""
        raise NotImplementedError