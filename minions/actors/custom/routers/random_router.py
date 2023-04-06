import asyncio
import random

from minions.actors import Router


class RandomRouter(Router):
    """Routes received messages to a random child"""
    def _route(self, message, sender):
        if self._children:
            return random.choice(self._children)
        else:
            raise Exception(
                "RandomRouter has no children to route to!"
            )
