import pytest, asyncio
from minions.actors import Actor, Supervisor


class EchoActor(Actor):
    async def handle_message(self, message, sender):
        return message


class CrashActor(Actor):
    async def handle_message(self, message, sender):
        if message == 'crash':
            exec("crashed")
        else:
            return None


class DelayActor(Actor):
    async def handle_message(self, message, sender):
        await asyncio.sleep(2)
        return message


@pytest.mark.asyncio
async def test_instanciation():
    actor = Actor()
    assert isinstance(actor,Actor)
    await actor.stop()

@pytest.mark.asyncio
async def test_actor_naming():
    actor_1 = Actor(name="Custom Named Actor")
    actor_2 = EchoActor(name="Custom Named Actor 2")
    actor_3 = Actor()
    actor_4 = EchoActor()
    assert actor_1.name == "Custom Named Actor"
    assert actor_2.name == "Custom Named Actor 2"
    assert actor_3.name == "actor-1"
    assert actor_4.name == "actor-2"
    await actor_1.stop()
    await actor_2.stop()
    await actor_3.stop()
    await actor_4.stop()

@pytest.mark.asyncio
async def test_context_initiation():
    val1 = object()
    val2 = object()
    actor = Actor(key1=val1, key2=val2)
    assert actor.context.key1 == val1
    assert actor.context.key2 == val2
    assert val1 != val2
    assert actor.context.key1 != actor.context.key2
    await actor.stop()


@pytest.mark.asyncio
async def test_echo_message():
    message = object()
    echo_actor = EchoActor()
    response = await echo_actor(message, 'me')
    assert message == response
    await echo_actor.stop()


@pytest.mark.asyncio
async def test_message_processing_order():
    messages = [object() for i in range(10)]
    echo_actor = EchoActor()
    responses = await asyncio.gather(*[echo_actor(message, 'me') for message in messages])
    for message, response in zip(messages, responses):
        assert message == response
    await echo_actor.stop()


@pytest.mark.asyncio
async def test_finish_processing_on_stop():
    messages = [object() for i in range(10)]
    echo_actor = EchoActor()
    pending_tasks = [echo_actor(message, 'me') for message in messages]
    await echo_actor.stop()
    responses = await asyncio.gather(*pending_tasks)
    for message, response in zip(messages, responses):
        assert message == response


@pytest.mark.asyncio
async def test_deny_new_messages_on_stop():
    message1 = object()
    message2 = object()
    echo_actor = EchoActor()
    response1 = await echo_actor(message1, 'me')
    assert message1 == response1
    stop_task = echo_actor.stop()
    with pytest.raises(asyncio.CancelledError):
        await echo_actor(message2, 'me')
    await stop_task


@pytest.mark.asyncio
async def test_restart():
    message = object()
    echo_actor = EchoActor()
    await echo_actor.stop()
    echo_actor.start()
    response = await echo_actor(message, 'me')
    assert message == response
    await echo_actor.stop()


@pytest.mark.asyncio
async def test_start_stop_restart_lifecycle():
    message1 = object()
    message2 = object()
    message3 = object()
    echo_actor = EchoActor()
    response1 = await echo_actor(message1, 'me')
    assert message1 == response1
    await echo_actor.stop()
    with pytest.raises(asyncio.CancelledError):
        await echo_actor(message2, 'me')
    echo_actor.start()
    response3 = await echo_actor(message3, 'me')
    assert message3 == response3
    await echo_actor.stop()


@pytest.mark.asyncio
async def test_actor_crash():
    child = CrashActor()
    try:
        result1 = await child('crash', 'me')
    except Exception as err:
        assert isinstance(err, NameError)
    else:
        assert True == False
    await child.stop()


@pytest.mark.asyncio
async def test_actor_restart():
    actor = EchoActor()
    old_worker = actor._worker
    await actor.restart()
    new_worker = actor._worker
    assert old_worker != new_worker
    assert actor.status == Actor.RUNNING
    await actor.stop()
    assert actor.status == Actor.STOPPED


@pytest.mark.asyncio
async def test_actor_timeout():
    actor = DelayActor(actor_timeout=1)
    try:
        result = await actor('hello', 'me')
    except Exception as err:
        assert isinstance(err, asyncio.TimeoutError)
    else:
        assert True == False
    await actor.stop()


# @pytest.mark.asyncio
# async def test_actor_ttl():
#     actor = DelayActor(actor_ttl=1)
#     try:
#         result = await actor('hello', 'me')
#     except Exception as err:
#         assert isinstance(err, asyncio.TimeoutError)
#     else:
#         assert True == False
#     await actor.stop()
