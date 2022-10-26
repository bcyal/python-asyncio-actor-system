import asyncio

from minions.actors.router import Router


class ShortestQueueRouter(Router):
    """
    Routes received messages to the child
    with the lowest number of enqueued tasks
    """
    def _route(self, message, sender):
        if self._children:
            item = min(
                self._children,
                key=lambda item: item._inbox.qsize()
            )
            return item
        else:
            raise Exception(
                "ShortestQueueRouter has no children!"
            )
