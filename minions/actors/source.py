from minions.actors.actor import Actor


class SourceDoesntAcceptMessagesError(Exception):
    __str__ = lambda x: "SourceDoesntAcceptMessagesError"


class Source(Actor):
    def __init__(self, server, *args, **kwargs):
        self._server = server
        super().__init__(*args, **kwargs)
        
    def __call__(
        self, 
        message, 
        sender=None
    ):
        raise SourceDoesntAcceptMessagesError        

    def start(self):
        self._server.start()
        self.status = Actor.RUNNING
        self._logger.debug(
            f"{self} has resumed operation."
        )
    
    async def stop(self):
        if self.status is not Actor.STOPPED:
            self._logger.debug(
                f"{self} received order to stop."
            )
            self.status = Actor.STOPPING
            await self._server.stop()
            self.status = Actor.STOPPED
            try:
                await self.on_stop()
            except Exception as err:
                self.status = Actor.CRASHED
                self._logger.error(
                    f"{self} crashed while executing on_stop() with:"\
                    f"\n{err}"
                )
            if hasattr(self, "_parent") and self._parent:
                await self._parent._handle_child(
                    self,
                    "crashed"
                    if self.status is Actor.CRASHED 
                    else "stopped",
                )
        else:
            self._logger.debug(
                f"{self} is already stopped."
            )
