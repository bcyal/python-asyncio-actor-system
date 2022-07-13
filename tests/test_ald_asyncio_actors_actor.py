import aiounittest, asyncio
from minions.actors import Actor, Supervisor

class EchoActor(Actor):
	async def handle_message(self, message, sender):
		return message

class CrashActor(Actor):
	async def handle_message(self, message, sender):
		if message == 'crash':
			return unknown_result
		else:
			return None

class DelayActor(Actor):
	async def handle_message(self, message, sender):
		await asyncio.sleep(2)
		return message

class BasicTests(aiounittest.AsyncTestCase):
	async def test_instanciation(self):
		actor = Actor()
		self.assertIsInstance(actor, Actor)
		await actor.stop()

	async def test_context_initiation(self):
		val1 = object()
		val2 = object()
		actor = Actor(key1=val1, key2=val2)
		self.assertIs(actor.context.key1, val1)
		self.assertIs(actor.context.key2, val2)
		self.assertIsNot(val1, val2)
		self.assertIsNot(actor.context.key1, actor.context.key2)
		await actor.stop()

	async def test_echo_message(self):
		message = object()
		echo_actor = EchoActor()
		response = await echo_actor(message, 'me')
		self.assertIs(message, response)
		await echo_actor.stop()

	async def test_message_processing_order(self):
		messages = [object() for i in range(10)]
		echo_actor = EchoActor()
		responses = await asyncio.gather(*[echo_actor(message, 'me') for message in messages])
		for message, response in zip(messages, responses):
			self.assertIs(message, response)
		await echo_actor.stop()

	async def test_finish_processing_on_stop(self):
		messages = [object() for i in range(10)]
		echo_actor = EchoActor()
		pending_tasks = [echo_actor(message, 'me') for message in messages]
		await echo_actor.stop()
		responses = await asyncio.gather(*pending_tasks)
		for message, response in zip(messages, responses):
			self.assertIs(message, response)

	async def test_deny_new_messages_on_stop(self):
		message1 = object()
		message2 = object()
		echo_actor = EchoActor()
		response1 = await echo_actor(message1, 'me')
		self.assertIs(message1, response1)
		stop_task = echo_actor.stop()
		with self.assertRaises(asyncio.CancelledError):
			await echo_actor(message2, 'me')
		await stop_task

	async def test_restart(self):
		message = object()
		echo_actor = EchoActor()
		await echo_actor.stop()
		echo_actor.start()
		response = await echo_actor(message, 'me')
		self.assertIs(message, response)
		await echo_actor.stop()

	async def test_start_stop_restart_lifecycle(self):
		message1 = object()
		message2 = object()
		message3 = object()
		echo_actor = EchoActor()
		response1 = await echo_actor(message1, 'me')
		self.assertIs(message1, response1)
		await echo_actor.stop()
		with self.assertRaises(asyncio.CancelledError):
			await echo_actor(message2, 'me')
		echo_actor.start()
		response3 = await echo_actor(message3, 'me')
		self.assertIs(message3, response3)
		await echo_actor.stop()

	async def test_actor_crash(self):
		child = CrashActor()
		try:
			result1 = await child('crash', 'me')
		except Exception as err:
			self.assertIsInstance(err, NameError)
		else:
			self.assertIs(True, False)
		# result2 = await child('dontcrash', 'me')
		# self.assertIs(result2, None)
		await child.stop()

	async def test_actor_restart(self):
		actor = EchoActor()
		old_worker = actor._worker
		await actor.restart()
		new_worker = actor._worker
		self.assertIsNot(old_worker, new_worker)
		self.assertIs(actor.status, Actor.RUNNING)
		await actor.stop()
		self.assertIs(actor.status, Actor.STOPPED)

	async def test_actor_timeout(self):
		actor = DelayActor(actor_timeout=1)
		try:
			result = await actor('hello', 'me')
		except Exception as err:
			self.assertIsInstance(err, asyncio.TimeoutError)
		else:
			self.assertIs(True, False)
		await actor.stop()

	# async def test_actor_ttl(self):
	# 	actor = DelayActor(actor_ttl=1)
	# 	try:
	# 		result = await actor('hello', 'me')
	# 	except Exception as err:
	# 		self.assertIsInstance(err, asyncio.TimeoutError)
	# 	else:
	# 		self.assertIs(True, False)
	# 	await actor.stop()

if __name__ == '__main__':
	unittest.main()
