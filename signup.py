from os import name
import discord, asyncio, datetime, bot, sqlite3, json, pytz, sys, linecache, threading, configparser

from discord import user
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, CheckFailure
from discord.utils import get, parse_time
from discord.ui import *
from discord import ButtonStyle
from datetime import *

signup_ranks = {
    "----------Silver 1-----------": ButtonStyle.grey,
    "----------Silver 2-----------": ButtonStyle.grey,
    "----------Silver 3-----------": ButtonStyle.grey,
    "----------Silver 4-----------": ButtonStyle.grey,
    "--------Silver Elite---------": ButtonStyle.grey,
    "-----Silver Elite Master-----": ButtonStyle.green,
    "---------Gold Nova 1---------": ButtonStyle.green,
    "---------Gold Nova 2---------": ButtonStyle.green,
    "---------Gold Nova 3---------": ButtonStyle.green,
    "---------Gold Nova 4---------": ButtonStyle.green,
    "------Master Guardian 1------": ButtonStyle.blurple,
    "------Master Guardian 2------": ButtonStyle.blurple,
    "----Master Guardian Elite----": ButtonStyle.blurple,
    "Distinguished Master Guardian": ButtonStyle.blurple,
    "-------Legendary Eagle-------": ButtonStyle.blurple,
    "----Legendary Eagle Master---": ButtonStyle.red,
    "--Supreme Master First Class-": ButtonStyle.red,
    "---------Global Elite--------": ButtonStyle.red
}
cs_rank = {
  1: "Silver 1",
  2: "Silver 2",
  3: "Silver 3",
  4: "Silver 4",
  5: "Silver Elite",
  6: "Silver Elite Master",
  7: "Gold Nova 1",
  8: "Gold Nova 2",
  9: "Gold Nova 3",
  10: "Gold Nova 4",
  11: "Master Guardian 1",
  12: "Master Guardian 2",
  13: "Master Guardian Elite",
  14: "Distinguished Master Guardian",
  15: "Legendary Eagle",
  16: "Legendary Eagle Master",
  17: "Supreme Master First Class",
  18: "Global Elite"
}
signup_perms = {'read_messages': True, 'add_reactions': True, 'use_slash_commands': False, 'send_tts_messages': False, 'send_messages': True, 'attach_files': False, 'manage_messages': False, 'manage_roles': False, 'create_instant_invite': False, 'external_emojis': False, 'manage_webhooks': False, 'manage_channels': False, 'read_message_history': True, 'embed_links': False, 'mention_everyone': False}
team_finder = {"title":"How to sign up","description":"1. *Make sure you have direct messages from server members enabled so you can receive notifications about being invited to a team*\n2. *Use the signup button and follow the signup process, and when captains are looking for members you will be sent an automated message from this bot if they invite you*\n3. *Once you receive a message for being invited to try out for a team, you will be informed of the team and the team captain that is adding you*","thumbnail":{"url":"https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"},"author":{"name":"CHAOZ Team finder","icon_url":"https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"},"color":13839167}

datab = 'database.sqlite'

def init():
    global users_signing, server, region_channel, signup_category, signup_message
    users_signing = {}
    server = None
    region_channel = None
    signup_category = None
    signup_message = None

def PrintException():
  exc_type, exc_obj, tb = sys.exc_info()
  f = tb.tb_frame
  lineno = tb.tb_lineno
  filename = f.f_code.co_filename
  linecache.checkcache(filename)
  line = linecache.getline(filename, lineno, f.f_globals)
  print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def signup_embed(title, rank='', steam_link='', faceit_link='', region='', about_me=''):
    embed = discord.Embed(title=title)
    embed.set_author(name="CHAOZ Team Finder", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
    embed.set_thumbnail(url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
    embed.add_field(
        name="**What you'll need to provide to signup**",
        value=f"1. Rank: {rank}\n2. Steam profile: {steam_link}\n3. Faceit profile: {faceit_link}\n4. Region: {region}\n5. About me: \n{about_me}"
    )
    embed.set_footer(text=f"Current step: {title}")
    return embed

async def create_find_embed(user, rank, steam, faceit, region, notes=None):
    try:
        embed = discord.Embed(
            title=f"{str(user)} is looking for a team!",
            description=f"Discord: <@{user.id}>\nRank: {rank}\nSteam: {str(steam)}\nFaceit: {str(faceit)}\nRegion: {str(region)}\nAbout me:\n{str(notes)}"
        )
        embed.set_thumbnail(url=str(user.avatar.url))
        embed.set_author(name="CHAOZ Team Finder", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
        channel = server.get_channel(region_channel[region])
        if channel != None:
            db = sqlite3.connect(datab)
            c = db.cursor()

            #Create embed and send in regional channel
            view = View()
            view.add_item(Button(style=ButtonStyle.blurple, label="Claim member", emoji="✔", custom_id=user.id))
            view.add_item(Button(style=ButtonStyle.green, label="Setup tryout", emoji="🔎", custom_id=f"+{user.id}"))
            message = await channel.send(embed=embed, view=view)
            c.execute(f"UPDATE team_find SET message=? WHERE discord=?", (str(message.id), str(user.id)))
            db.commit()
        else:
            print("Failed to get player-find channel")
    except Exception as e:
        print(e)

class ConfirmSignup(View):
    def __init__(self, ctx, signup_user, rank, steam_link, faceit_link, region, about_me, bot):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.signup_user = signup_user
        self.bot = bot

        #Signup variables
        self.rank = rank
        self.steam_link = steam_link
        self.faceit_link = faceit_link
        self.region = region
        self.about_me = about_me

        #Set region buttons
        self.add_item(Button(style=ButtonStyle.blurple, label="Confirm info", emoji="✔", custom_id="confirm"))
        self.add_item(Button(style=ButtonStyle.red, label="Cancel signup", emoji="❌", custom_id="cancel"))

    async def interaction_check(self, interaction):
        if interaction.user == self.signup_user and interaction.channel == self.ctx:
            if interaction.data["custom_id"] == "confirm":
                db = sqlite3.connect(datab)
                c = db.cursor()
                c.execute("INSERT INTO team_find (discord, steam, rank, region, notes, faceit) VALUES (?, ?, ?, ?, ?, ?)", (str(self.signup_user.id), str(self.steam_link), str(self.rank), str(self.region), str(self.about_me), str(self.faceit_link)))
                db.commit()
                db.close()
                try:
                    await create_find_embed(self.signup_user, self.rank, self.steam_link, self.faceit_link, self.region, self.about_me)
                    await interaction.response.send_message("Finished signup process, deleting channel...")
                except:
                    PrintException()
                    await interaction.response.send_message("Signup process failed please contact an admin, deleting channel...")
                if self.signup_user in users_signing: del users_signing[self.signup_user]
                await asyncio.sleep(5)
                await interaction.channel.delete()
                self.stop()
            else:
                interaction.response.send_message("Canceled signup, deleting channel...")

    async def on_timeout(self):
        await self.ctx.send("**Signup timed out! deleting channel...**")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(3)
        await self.ctx.delete()
        self.stop()

    async def on_error(self, error):
        print(error)
        await self.ctx.send(f"Error: {error}\nDeleting channel...")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(8)
        await self.ctx.delete()
        self.stop()

class RegionSelect(View):
    def __init__(self, ctx, signup_user, rank, steam_link, faceit_link, bot):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.signup_user = signup_user
        self.bot = bot

        #Signup variables
        self.rank = rank
        self.steam_link = steam_link
        self.faceit_link = faceit_link
        self.region = None
        self.about_me = None

        #Set region buttons
        self.add_item(Button(style=ButtonStyle.blurple, label="NA", emoji="🇺🇸", custom_id="NA"))
        self.add_item(Button(style=ButtonStyle.blurple, label="EU", emoji="🇪🇺", custom_id="EU"))
        self.add_item(Button(style=ButtonStyle.blurple, label="South America", emoji="🇧🇷", custom_id="SA"))
        self.add_item(Button(style=ButtonStyle.blurple, label="ASIA", emoji="🇯🇵", custom_id="ASIA"))

    async def interaction_check(self, interaction):
        if interaction.user == self.signup_user and interaction.channel == self.ctx:
            #Remove timeout
            super().__init__(timeout=None)

            #Set region and load new message
            self.region = interaction.data["custom_id"]
            await interaction.response.edit_message(
                embed=signup_embed('Write an "About me" to give a description of yourself', rank=self.rank, steam_link=self.steam_link, faceit_link=self.faceit_link, region=self.region),
                view=None
            )

            #Wait for about me message
            while True:
                try:
                    message = await self.bot.wait_for('message', check=lambda interaction: interaction.channel == users_signing[self.signup_user], timeout=120)
                    if message.author in users_signing:
                        self.about_me = message.content
                        await message.delete()
                        break
                    else:
                        await message.delete()
                except Exception as e:
                    print(e)
                    await interaction.channel.send("**Signup timed out! deleting channel...**")
                    if self.signup_user in users_signing: del users_signing[self.signup_user]
                    await self.ctx.delete()
                    self.stop()
            
            #Start confirmation
            await interaction.message.edit(
                embed=signup_embed("Finished! Confirm your info below", rank=self.rank, steam_link=self.steam_link, faceit_link=self.faceit_link, region=self.region, about_me=self.about_me),
                view=ConfirmSignup(self.ctx, self.signup_user, self.rank, self.steam_link, self.faceit_link, self.region, self.about_me, self.bot)
            )

    async def on_timeout(self):
        await self.ctx.send("**Signup timed out! deleting channel...**")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(3)
        await self.ctx.delete()
        self.stop()

    async def on_error(self, error):
        print(error)
        await self.ctx.send(f"Error: {error}\nDeleting channel...")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(8)
        await self.ctx.delete()
        self.stop()

class RankSelect(View):
    def __init__(self, ctx, signup_user, bot):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.signup_user = signup_user
        self.bot = bot

        #Signup variables
        self.rank = None
        self.steam_link = None
        self.faceit_link = None

        #Load rank buttons
        i = 1
        for rank, style in signup_ranks.items():
            self.add_item(Button(style=style, label=rank, custom_id=f"{i}"))
            i += 1

    #Called when button is selected
    async def interaction_check(self, interaction):
        if interaction.user == self.signup_user and interaction.channel == self.ctx:
            #Remove timeout
            super().__init__(timeout=None)
            
            #Get rank and set new embed title
            self.rank = cs_rank[int(interaction.data['custom_id'])]
            await interaction.response.edit_message(embed=signup_embed("Please supply your steam community profile link", rank=self.rank), view=None)

            #Wait for steam link message
            while True:
                try:
                    message = await self.bot.wait_for('message', check=lambda interaction: interaction.channel == users_signing[self.signup_user], timeout=180)
                    if 'https://steamcommunity.com/id/' in message.content or 'https://steamcommunity.com/profiles/' in message.content and message.author in users_signing:
                        self.steam_link = str(message.content).replace('\n', '')
                        await message.delete()
                        await interaction.message.edit(embed=signup_embed("Please send your faceit profile url, or reply with 'NA' if you have none", rank=self.rank, steam_link=self.steam_link), view=None)
                        break
                    else:
                        if message.author in users_signing: await message.channel.send("Not a valid steam profile link, link should include either 'https://steamcommunity.com/id/' or 'https://steamcommunity.com/profiles/'", delete_after=8); await message.delete()
                except Exception as e:
                    print(e)
                    await interaction.channel.send("**Signup timed out! deleting channel...**")
                    if self.signup_user in users_signing: del users_signing[self.signup_user]
                    await self.ctx.delete()
                    self.stop()
            
            #Wait for faceit link message
            while True:
                try:
                    message = await self.bot.wait_for('message', check=lambda interaction: interaction.channel == users_signing[self.signup_user], timeout=180)
                    if 'https://www.faceit.com/' in message.content and message.author in users_signing:
                        self.faceit_link = str(message.content).replace('\n', '')
                        await message.delete()
                        break
                    elif str(message.content).replace(' ', '').lower() == 'na':
                        self.faceit_link = "N/A"
                        await message.delete()
                        break
                    else:
                        if message.author in users_signing: await message.channel.send("Not a valid faceit profile link, link should include 'https://www.faceit.com/'", delete_after=8); await message.delete()
                except Exception as e:
                    print(e)
                    await interaction.channel.send("**Signup timed out! deleting channel...**")
                    if self.signup_user in users_signing: del users_signing[self.signup_user]
                    await self.ctx.delete()
                    self.stop()
            
            #Start region selection
            await interaction.message.edit(
                embed=signup_embed("Please choose your region", rank=self.rank, steam_link=self.steam_link, faceit_link=self.faceit_link),
                view=RegionSelect(self.ctx, self.signup_user, self.rank, self.steam_link, self.faceit_link, self.bot)
            )

    async def on_timeout(self):
        await self.ctx.send("**Signup timed out! deleting channel...**")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(3)
        await self.ctx.delete()
        self.stop()

    async def on_error(self, error):
        print(error)
        await self.ctx.send(f"Error: {error}\nDeleting channel...")
        if self.signup_user in users_signing: del users_signing[self.signup_user]
        await asyncio.sleep(8)
        await self.ctx.delete()
        self.stop()

async def signup_thread(bot, interaction, signup_user, category):
    #Check if user is already signing up, if not create channel
    if signup_user in users_signing:
        await interaction.response.send_message(content=f"You are already in the signup process, if you think this is wrong contact <@319472584704131074>", ephemeral=True)
        return
    else:
        signup_category = category
        everyone = get(interaction.guild.roles, name='@everyone')
        channel = await signup_category.create_text_channel(name=f"「{str(signup_user.name)}」Signup", overwrites={everyone:  discord.PermissionOverwrite(**{'read_messages': False}), signup_user: discord.PermissionOverwrite(**signup_perms)})
        print(f'{str(signup_user)} is signing up for team finder')
        await interaction.response.send_message(content=f"Go to channel <#{channel.id}> to complete signup", ephemeral=True)
        users_signing[signup_user] = channel

    #Start signup process
    try:
        await channel.send(embed=signup_embed("Please choose your rank"), view=RankSelect(channel, signup_user, bot))
    except Exception as e:
        print(e)