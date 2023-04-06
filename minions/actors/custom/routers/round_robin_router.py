import asyncio
import itertools

from minions.actors import Router


class RoundRobinRouter(Router):
    """Routes received messages in round robin fashion"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next = self._round_robin_iterator()
    def _route(self, message, sender):
        if self._children:
            return next(self._next)
        else:
            raise Exception(
                "RoundRobinRouter has no children to route to!"
            )

    def _round_robin_iterator(self):
        for item in itertools.cycle(self._children):
            yield item