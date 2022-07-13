import asyncio
from types import SimpleNamespace
from contextlib import suppress
from itertools import count
import logging, sys


class Actor:
	RUNNING = object()
	STOPPING = object()
	STOPPED = object()
	CRASHED = object()

	def __init__(self, actor_max_idle=None, actor_ttl=None, actor_timeout=None, **kwargs):
		self.context = SimpleNamespace(**kwargs)
		self._loop = asyncio.get_event_loop()
		self._inbox = asyncio.Queue()
		self._timeout = actor_timeout
		self._max_idle = actor_max_idle
		self._ttl = actor_ttl
		self.start()

	async def handle_message(self, message, sender):
		raise NotImplementedError

	async def _handle(self):
		while True:
			message, sender, result = await self._inbox.get()
			try:
				coro = self.handle_message(message, sender)
				answer = await asyncio.wait_for(coro, timeout=self._timeout)
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
				break

	def __call__(self, message, sender):
		if self.status is not Actor.RUNNING or self._worker.done():
			raise asyncio.CancelledError()
		result = self._loop.create_future()
		self._inbox.put_nowait((message, sender, result))
		return result

	def start(self):
		self._worker = self._loop.create_task(self._handle())
		self.status = Actor.RUNNING

	def stop(self):
		self.status = Actor.STOPPING
		return self._loop.create_task(self._stop())

	def restart(self):
		return self._restart()

	async def _restart(self):
		if self.status is Actor.RUNNING:
			await self.stop()
		if self.status in [Actor.STOPPED, Actor.CRASHED]:
			self.start()

	async def _stop(self):
		await self._inbox.join()
		if not self._worker.done():
			try:
				self._worker.cancel()
				await self._worker
			except asyncio.CancelledError:
				pass
		self.status = Actor.STOPPED

	def __str__(self):
		return "Clint Eastwood"


class Supervisor(Actor):
	def __init__(self, children=None, **kwargs):
		self._children = []
		for child in children:
			self.register_child(child)
		return super().__init__(**kwargs)

	def register_child(self, child):
		self._children.append(child)
