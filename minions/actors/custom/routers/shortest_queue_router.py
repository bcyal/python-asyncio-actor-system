import asyncio

from minions.actors.router import Router


class ShortestQueueRouter(Router):
    """
    Routes received messages to the child
    with the lowest number of enqueued tasks
    """
    def _route(self, message, sender):
        item = min(
            self._children,
            key=lambda item: len(item._inbox)
        )
        return item
