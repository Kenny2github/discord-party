
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

