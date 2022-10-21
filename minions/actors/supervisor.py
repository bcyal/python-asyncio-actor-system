from functools import partial
import signal
import asyncio

from minions.actors.actor import Actor


class ExitPolicy:
    def __init__(self, identifier):
        self.__ident__ = identifier
    def __str__(self):
        return self.__ident__


## ignore child crashes
IGNORE = ExitPolicy("IGNORE")
## resume the exited child
RESUME = ExitPolicy("RESUME")
## restart the exited child
RESTART = ExitPolicy("RESTART")
## if a child stops,
## stop all children and yourself
ESCALATE = ExitPolicy("ESCALATE")
## if the last child stops, stop yourself
DEPLETE = ExitPolicy("DEPLETE")
## shutdown crashed children
SHUTDOWN = ExitPolicy("SHUTDOWN")


class Supervisor(Actor):
    def __init__(
        self, 
        policy=RESTART, 
        children=[], 
        *args,
        **kwargs
        ):
        super().__init__(*args,**kwargs)
        self._root_idle = asyncio.Event()
        self._policy = policy
        self._children = []
        for child in children:
            self.register_child(child)

    async def _handle_child(self, child, state):
        self._logger.debug(
            f"{child}, a child of {self}, stopped, "\
            f"policy is {self._policy}"
        )
        if self._policy == RESTART:
            await child.restart()

        elif self._policy == RESUME:
            child.start()
        
        elif self._policy == SHUTDOWN:
            self._logger.info(
                f"{self} has shutdown {child}"
            )
            self.unregister_child(child)
            # if state == "crashed":
            #     child.clear()
    
    def spawn_child(self, cls, *args, **kwargs):
        """Start an instance of cls(*args, **kwargs) as child"""
        child = cls(*args, **kwargs)
        self._logger.debug(f"{self} spawned new child {child}")
        self.register_child(child)
    
    def register_child(self, child):
        """Register an already running Actor as child"""
        if isinstance(child, partial):
            child = child()
        self._children.append(child)
        child.register_parent(self)
        self._logger.debug(
            f"{child} registered as child of {self}."
        )
    
    def unregister_child(self, child):
        """Unregister a running Actor from the list of children"""
        try:
            child.unregister_parent(self)
            self._children.remove(child)
            self._logger.debug(
                f"{child} unregistered as child of {self}."
            )
        except ValueError:
            self._logger.debug(
                f"Unregistering {child} as child of {self} failed."
            )
    
    async def stop(self):
        self._policy = SHUTDOWN
        self._logger.debug(
            f"{self} is in controlled shutdown, "\
            f"changing restart policy to {self._policy}"
        )
        for child in list(self._children):
            await child.stop()
        
        self._logger.debug(
            f"All children of {self} unregistered."
        )
        await super().stop()
        self._root_idle.set()


class Gru(Supervisor):
    def __init__(
        self,
        join=True,
        tracebacks=False,
        *args,
        **kwargs
        ):
        super().__init__(*args, **kwargs)
        self._signals = (
            signal.SIGTERM,
            signal.SIGINT,
            signal.SIGHUP,
        )
        self.register_signals()
        self.tracebacks = tracebacks
        self._auto_join = join

    def register_signals(self):
        for s in self._signals:
            self._loop.add_signal_handler(
                s,
                lambda s=s: asyncio.create_task(self.stop())
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if all(v is None for v in [exc_type,exc_val,exc_tb]):
            if self._auto_join:
                await self._root_idle.wait()
                await self.join()
            self._logger.info(
                f"{self} was shutdown, properly"
            )
        else:
            self._logger.error(
                f"{self} crashed with {exc_val}"
            )
            await self.stop()
            return not self.tracebacks
