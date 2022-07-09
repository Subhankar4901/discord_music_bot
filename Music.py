import discord
from discord.ext import commands
import youtube_dl
import asyncio
class music(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.song_queue={}
        self.setup()
    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id]=[]
    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel, please connect to the channel you want me to join.")

        if ctx.voice_client is not None:
            if ctx.author.voice.channel.id == ctx.voice_client.channel.id:
                await ctx.send("I am alredy in the voice channel")
            else:
                await ctx.send("Sorry, I am in a different voice channel.")
        else:
            await ctx.author.voice.channel.connect()
    @commands.command()
    async def leave(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not in any voice channel")
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()
        await ctx.send("I am not connected to a voice channel.")
    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
    async def play_song(self, ctx, song):
        ffmpeg={'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
        with youtube_dl.YoutubeDL({"format":"bestaudio"}) as ydl:
            info=ydl.extract_info(song,download=False)
            url2=info["formats"][0]["url"] 
        source=await discord.FFmpegOpusAudio.from_probe(url2,**ffmpeg)
        ctx.voice_client.play(source,after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))        
        ctx.voice_client.source.volume = 0.5
    @commands.command()
    async def play(self,ctx,song):
        if song is None:
            return await ctx.send("You must include a song to play.")
        if ctx.author.voice is None:
            return await ctx.send("You must join a voice channel to play")
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            await ctx.send("I am alredy in a different voice channel")
        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"I am currently playing a song, this song has been added to the queue at position: {queue_len+1}.")

            else:
                return await ctx.send("Sorry, I can only queue up to 10 songs, please wait for the current song to finish.")
        await self.play_song(ctx, song)
        await ctx.send(f"Now playing: {song}")
    @commands.command()
    async def queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text="Thanks for using me!")
        await ctx.send(embed=embed)
    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}", description="**80% of the voice channel must vote to skip for it to pass.**", colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("I am already paused.")

        ctx.voice_client.pause()
        await ctx.send("The current song has been paused.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("I am already playing a song.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.")
        