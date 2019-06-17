"""
Handle Discord Rich Presence party logic with ease.

Example Usage
=============

.. code-block:: python

    from discord_party import Party
    async def main():
        RPC = Party(client_id)
        await RPC.start()
        RPC.state = 'Looking for Players'
        RPC.id = #get a party ID your way
        RPC.join = #party secret, cannot be party ID
        RPC.size = 1
        RPC.max = 4
        await RPC #send these changes to Discord
        def meanwhile():
            #update the game window, this is called once every v seconds
        secret = await RPC.wait_for_player_join(meanwhile, delay=0.5)
        #join someone else's party with secret
        #...

"""
from __future__ import annotations

__all__ = ['Party']
__version__ = '0.0.0a1'

import sys
import os
from inspect import isawaitable
from functools import wraps
from typing import Union, Callable, Any, Optional
import asyncio
from pypresence import AioClient, Client, InvalidPipe

if sys.platform.startswith('win32'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

#duck-type fix the register_event function
#pylint: disable=protected-access
async def register_event(self, event: str, func: callable, args: dict = None):
    """Subscribe to an event and register a callback for it."""
    if not callable(func):
        raise TypeError
    await self.subscribe(event, args or {})
    self._events[event.lower()] = func

AioClient.on_event = Client.on_event
AioClient.register_event = register_event

#type aliases
Number = Union[int, float]
Identifier = Union[int, str]

def _status_var(dtype, name=None):
    def newfunc(func):
        levar = name or func.__name__
        @property
        @wraps(func)
        def _get(self) -> Optional[dtype]:
            return self._status.get(levar, None)

        @_get.setter
        def _set(self, value: dtype):
            self._status[levar] = value

        @_set.deleter
        def _del(self):
            del self._status[levar]

        return _del
    return newfunc
#pylint: enable=protected-access

class Party:
    """Represents the party."""
    def __init__(
            self,
            client_id: str,
            loop: asyncio.BaseEventLoop = None,
            pipe: int = 0,
            handler: callable = None
    ):
        """Initialize the Party object.

        ``client_id``: the ID of your Discord application.
            https://discordapp.com/developers/applications/me
        ``loop``: the event loop to run with. On Windows, this needs to be a
            ProactorEventLoop, so this module sets the event loop policy as
            such upon import if it detects the platform to be Windows.
        ``pipe``: Pipe that should be used to connect to the Discord client.
            Defaults to 0, can be 0-9
        ``handler``: Passed to pypresence.Client
        """
        self._rpc = AioClient(client_id, loop=loop, pipe=pipe, handler=handler)
        self.loop = self._rpc.loop
        self._status = {'pid': os.getpid()}
        self.updating_loop = None

    async def start(self, raise_on_fail: bool = False) -> None:
        """Attempt to connect to Discord.
        Must be done in order to do anything useful.

        If the connection fails, unless ``raise_on_fail`` is True,
        this method does NOT raise an exception - instead,
        bool(party) will become false and future operations will
        silently become no-ops (in order to cleanly not care
        whether Discord is running or not).
        """
        try:
            await self._rpc.start()
        except InvalidPipe:
            if raise_on_fail:
                raise
            self._rpc = None

    def __bool__(self) -> bool:
        """Returns True if actually connected to Discord's RPC"""
        return self._rpc is not None

    @_status_var(Identifier)
    def party_id(self):
        """ID of the player's party, lobby, or group"""
        pass

    id = party_id

    @_status_var(str)
    def join(self):
        """Unique hashed string for chat invitations and ask to join"""
        pass

    secret = join

    @_status_var(str)
    def spectate(self):
        """Unique hashed string for spectate button"""
        pass

    spectate_secret = spectate

    @_status_var(str)
    def state(self):
        """The user's current status"""
        pass

    @_status_var(str)
    def details(self):
        """What the player is currently doing"""
        pass

    @_status_var(int, 'start')
    def start_time(self):
        """Epoch time for game start"""
        pass

    @_status_var(int, 'end')
    def end_time(self):
        """Epoch time for game end"""
        pass

    @_status_var(str)
    def large_image(self):
        """Name of the uploaded image for the large profile artwork"""
        pass

    @_status_var(str)
    def large_text(self):
        """Tooltip for the large image"""
        pass

    @_status_var(str)
    def small_image(self):
        """Name of the uploaded image for the small profile artwork"""
        pass

    @_status_var(str)
    def small_text(self):
        """Tooltip for the small image"""
        pass

    @property
    def size(self) -> int:
        """The number of players in the player's party, lobby, or group"""
        return self._status['party_size'][0]

    @size.setter
    def size(self, value: int):
        if 'party_size' not in self._status:
            self._status['party_size'] = [value, value]
        else:
            self._status['party_size'][0] = value

    party_size = size

    @property
    def max(self) -> int:
        """The maximum number of players allowed in the player's party"""
        return self._status['party_size'][1]

    @max.setter
    def max(self, value: int):
        if 'party_size' not in self._status:
            self._status['party_size'] = [value, value]
        else:
            self._status['party_size'][1] = value

    party_max = max

    def __await__(self):
        """await party <==> await party.update()"""
        return self.update().__await__()

    async def update(self) -> None:
        """Update party information."""
        if self._rpc is not None:
            await self._rpc.set_activity(**self._status)

    def update_loop(self, delay: Number) -> asyncio.Task:
        """Update party information in a continuous loop."""
        async def leloop():
            try:
                while 1:
                    await self.update()
                    await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        self.updating_loop = self.loop.create_task(leloop())
        return self.updating_loop

    def stop_updating_loop(self) -> None:
        """Stop updating party information."""
        if self.updating_loop is not None:
            self.updating_loop.cancel()

    async def wait_for_player_join(
            self,
            meanwhile: Callable[[], Any] = lambda: None,
            delay: Number = 0.5
    ) -> str:
        """Async block until a player has joined via Discord.
        Call ``meanwhile`` with no arguments every ``delay`` seconds
        in the meantime. Returns the party secret.
        """
        await self.update()
        fut = self.loop.create_future()
        @self.on_player_join
        def handler(secret):
            fut.set_result(secret['secret'])
        assert callable(handler)
        async def meantime():
            try:
                maybeawait = meanwhile()
                if isawaitable(maybeawait):
                    await maybeawait
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        task = self.loop.create_task(meantime())
        secret = await fut
        task.cancel()
        await self._rpc.unregister_event('ACTIVITY_JOIN')
        return secret

    def on_player_join(self, func):
        """Register a callback for when *the current player* joins someone
        else's party.
        """
        self.loop.create_task(self._rpc.register_event('ACTIVITY_JOIN', func))
        return func

    def on_spectate(self, func):
        """Register a callback for when *the current player* spectates someone
        else's game.
        """
        self.loop.create_task(self._rpc.register_event('ACTIVITY_SPECTATE', func))
        return func

    def close(self):
        """Close the connection to Discord. Goodbye.
        Calls stop_updating_loop() as well.
        """
        self.stop_updating_loop()
        if self._rpc is not None:
            self._rpc.close()
            self._rpc = None

    __del__ = close
