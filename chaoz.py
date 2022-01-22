import discord
import asyncio
import sqlite3
import pytz
import sys
import linecache
import threading
import configparser
import signup
from discord.ext import commands
from discord.utils import get
from discord import ButtonStyle
from signup import signup_thread

datab = 'database.sqlite'

db = sqlite3.connect(datab)
c = db.cursor()

timez = pytz.timezone("US/Eastern")

config = configparser.ConfigParser()
config.read('config.ini')

signup.init()

# Lists/Dicts
team_finder = [
    {"title": "How to sign up", "description": "1. *Make sure you have direct messages from server members enabled so you can receive notifications about being invited to a team*\n2. *Use the signup button and follow the signup process, and when captains are looking for members you will be sent an automated message from this bot if they invite you*\n3. *Once you receive a message for being invited to try out for a team, you will be informed of the team and the team captain that is adding you*",
        "thumbnail": {"url": "https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"}, "author": {"name": "CHAOZ Team finder", "icon_url": "https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"}, "color": 13839167},
    {"title": "", "description": "", "thumbnail": {"url": "https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"}, "color": 13839167}
]

# Global variables
panel_users = list(config['Panel Users'])
panel_users = [int(i) for i in panel_users]
authed_servers = list(config['Authed Servers'])
authed_servers = [int(i) for i in authed_servers]
player_find_channels = config['Player Find']
gVars = config['Global']
users_signing = []
server = int(gVars['server'])
signup_category = int(gVars['signup_category'])
signup_embed = int(gVars['signup_embed'])
log_channel = int(gVars['log_channel'])
role_placeholder = int(gVars['role_placeholder'])
captain_role = int(gVars['captain_role'])
admin_role = int(gVars['admin_role'])
signup.signup_message = signup_embed

region_channel = {
    "NA": int(player_find_channels['NA']),
    "EU": int(player_find_channels['EU']),
    "SA": int(player_find_channels['SA']),
    "ASIA": int(player_find_channels['ASIA'])
}
signup.region_channel = region_channel


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


def embed_tool():
    None


async def get_dm(member):
    dm = member.dm_channel
    if member.dm_channel == None:
        await discord.User.create_dm(member)
        dm = member.dm_channel
    return dm


def team_find_embed(title, description, thumbnail="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"):
    embed = discord.Embed(
        title=title,
        description=description
    ).set_thumbnail(url=thumbnail)
    embed.set_author(name="CHAOZ Team Finder", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
    return embed


class ConsentForm(View):
    def __init__(self, member, captain, team_role, captain_dm, member_dm):
        super().__init__(timeout=30)
        self.member = member
        self.captain = captain
        self.team_role = team_role
        self.captain_dm = captain_dm
        self.member_dm = member_dm

        self.add_item(Button(style=ButtonStyle.blurple, label="Accept", emoji="✔", custom_id="consent_accept"))
        self.add_item(Button(style=ButtonStyle.red, label="Decline", emoji="❌", custom_id="consent_decline"))

    async def interaction_check(self, interaction):
        if interaction.data["custom_id"] == "consent_accept":
            # Give team role to member
            try:
                await self.member.add_roles(self.team_role)
            except:
                PrintException()
                await interaction.response.edit_message(embed=team_find_embed("Failed to give you the team role", "please contact an admin for support"), view=None, delete_after=10)
                self.stop()
                return

            # Captain embed notification
            await self.captain_dm.send(embed=team_find_embed(f"You claimed user {str(self.member)}", f"Their team role should be automatically applied", f"{str(self.member.avatar.url)}"))

            # Remove member for team find
            c.execute("SELECT * FROM team_find WHERE discord=?", (str(self.member.id),))
            data = c.fetchone()
            c.execute("DELETE FROM team_find WHERE discord=?", (str(self.member.id),))
            db.commit()
            try:
                for channel_id in player_find_channels:
                    channel = server.get_channel(int(player_find_channels[channel_id]))
                    try:
                        message = await channel.fetch_message(int(data[6]))
                        if message != None:
                            await message.delete()
                            break
                    except:
                        None
            except:
                None

            # Member embed notification
            await interaction.response.edit_message(embed=team_find_embed(f"{str(self.captain)} claimed you!", f"You have been removed from the team finder and added to the team {self.team_role.name}", f"{str(self.captain.avatar.url)}"), view=None, delete_after=8)
            self.stop()
        else:
            await interaction.response.edit_message(embed=team_find_embed(f"You declined {str(self.captain)} invitation to their team", "You will not receive their team role", f"{str(self.captain.avatar.url)}"), delete_after=8)
            await self.captain_dm.send(embed=team_find_embed(f"{str(self.member)} did not wish to be added to your team", f"They will not receive your team role", f"{str(self.member.avatar.url)}"))
            self.stop()

    async def on_timeout(self):
        await self.member_dm.send("**You did not respond to the claim in time**")
        await self.captain_dm.send(embed=team_find_embed(f"{str(self.member)} did not respond to your claim in time", f"Try again when they are online\nThey will not receive your team role", f"{str(self.member.avatar.url)}"), delete_after=15)
        self.stop()

    async def on_error(self, error):
        print(error)
        self.stop()


async def claim_member(member, interaction):
    role = get(interaction.guild.roles, id=captain_role)
    captain = get(interaction.guild.members, id=int(interaction.user.id))
    if role in captain.roles:
        # Get user's dms
        member_dm = await get_dm(member)
        captain_dm = await get_dm(captain)

        # Get captains data
        team_role = None
        c.execute("SELECT * FROM teams")
        data = c.fetchall()
        for team_info in data:
            team_role = get(interaction.guild.roles, id=int(team_info[4]))
            if team_role in captain.roles:
                break
        if team_role != None:
            await interaction.response.send_message(content=f"Sending consent form to member", ephemeral=True)
            await member_dm.send(embed=team_find_embed(f'{str(interaction.user)} From team "{team_role.name}" wants to claim you!', "Please respond to their offer", f"{interaction.user.avatar.url}"), view=ConsentForm(member, captain, team_role, captain_dm, member_dm))
        else:
            await interaction.response.send_message(content=f"Could not find your team role, please contact an admin", ephemeral=True)
    else:
        await interaction.response.send_message(content="You do not have permission to do this", ephemeral=True)


async def set_signup_count():
    # Retrieve currently signed up
    c.execute("SELECT * FROM team_find")
    data = c.fetchall()
    regions = {"NA": 0, "EU": 0, "SA": 0, "ASIA": 0}
    for entry in data:
        regions[entry[3]] += 1
    embed = discord.Embed().from_dict(team_finder[0])
    embed.add_field(name="**Members currently signed up:**", value=f"NA:〔{regions['NA']}〕EU:〔{regions['EU']}〕SA:〔{regions['SA']}〕ASIA:〔{regions['ASIA']}〕")

    # Get signup embed and set new name
    print("Updating embed")
    for channel in signup_category.channels:
        try:
            message = await channel.fetch_message(signup_embed)
            if message != None:
                await message.edit(embed=embed)
        except:
            None

    # Update number of members in regional channel
    # print("update channel")
    # for region in regions:
    #   channel = server.get_channel(region_channel[region])
    #   await channel.edit(name=f"💢│{str(region)}-players〔{str(regions[region])}〕")


class Signoff(View):
    def __init__(self, user, bot, data):
        super().__init__(timeout=15)
        self.user = user
        self.bot = bot
        self.data = data

        # Add confirmation button
        self.add_item(Button(style=ButtonStyle.green, emoji="✔", custom_id="signoff_accept"))

    async def interaction_check(self, interaction):
        if interaction.data["custom_id"] == "signoff_accept" and interaction.user == self.user:
            c.execute("DELETE FROM team_find WHERE discord=?", (str(interaction.user.id),))
            db.commit()
            try:
                for channel_id in player_find_channels:
                    channel = server.get_channel(int(player_find_channels[channel_id]))
                    try:
                        message = await channel.fetch_message(int(self.data[6]))
                        if message != None:
                            await message.delete()
                            break
                    except:
                        None
            except:
                None
            await interaction.response.edit_message(content="You have been removed from the team finder", view=None)

            await set_signup_count()

    async def on_timeout(self):
        self.stop()

    async def on_error(self, error):
        print(error)
        self.stop()


class MyClient(commands.Bot):
    async def on_connect(self):
        print("Bot connected")
        self.add_cog(MyCommands(self))

    async def on_ready(self):
        global server, log_channel, role_placeholder, signup_category
        print(f"Logged on as {str(self.user)}")
        server = self.get_guild(server)
        signup.server = server
        log_channel = server.get_channel(log_channel)
        role_placeholder = get(server.roles, id=role_placeholder)
        signup_category = get(server.channels, id=signup_category)
        signup.signup_category = signup_category
        for guild in self.guilds:
            if guild.id not in authed_servers:
                await guild.leave()
        # await self.clear_dm(server.get_member(319472584704131074))

    async def clear_dm(self, user):
        dm = await get_dm(user)
        async for message in dm.history(limit=100):
            if message.author == self.user:
                try:
                    await message.delete()
                except:
                    None

    async def on_message(self, ctx):
        if ctx.channel in list(signup.users_signing.values()) and ctx.author != self.user:
            await asyncio.sleep(1)
            try:
                await ctx.delete()
            except:
                None
        else:
            await self.process_commands(ctx)
            if ctx.channel in signup_category.channels:
                await set_signup_count()

    async def on_interaction(self, interaction):
        if interaction.data['custom_id'] == 'team_signup':
            try:
                c.execute("SELECT * FROM team_find WHERE discord=?", (str(interaction.user.id),))
                if c.fetchone() == None:
                    try:
                        asyncio.create_task(signup_thread(self, interaction, interaction.user, signup_category))
                        print(f"Active threads: {str(threading.active_count())}")
                    except:
                        PrintException()
                else:
                    await interaction.response.send_message(content="You are already signed up for the team finder, if you wish to be removed or want to make changes contact an Admin", ephemeral=True)
            except:
                await interaction.response.send_message(content="Please enable direct messages from members on this server!", ephemeral=True)
        elif interaction.data['custom_id'] == 'team_signoff':
            try:
                user = interaction.user
                c.execute("SELECT * FROM team_find WHERE discord=?", (str(user.id),))
                data = c.fetchone()
                if data != None:
                    await interaction.response.send_message(content="Are you sure you wish to remove your self from the team finder?", view=Signoff(user, self, data), ephemeral=True)
                else:
                    await interaction.response.send_message(content='You are not signed up for the team finder', ephemeral=True)
            except:
                PrintException()
        elif str(interaction.channel.id) in list(player_find_channels.values()):
            if '+' in interaction.data["custom_id"]:
                member = get(server.members, id=int(str(interaction.data["custom_id"]).replace('+', '')))
                member_dm = await get_dm(member)
                captain = interaction.user
                c.execute("SELECT * FROM teams")
                data = c.fetchall()
                team_role = None
                for team_info in data:
                    team_role = get(interaction.guild.roles, id=int(team_info[4]))
                    if team_role in captain.roles:
                        break
                await member_dm.send(embed=team_find_embed(f'{str(captain)} from team "{team_role.name}"" wants to setup a tryout', f"Add <@{captain.id}> and discuss a time for your tryout", f"{captain.avatar.url}"))
                await interaction.response.send_message(f"Sent notification to <@{member.id}> to setup a tryout\nAdd them and discuss a time for their tryout", ephemeral=True)
            else:
                member = get(server.members, id=int(interaction.data["custom_id"]))
                await claim_member(member, interaction)


class MyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def teamfind(self, ctx):
        await ctx.message.delete()
        view = View()
        view.add_item(Button(style=ButtonStyle.green, label="Signup", emoji="📩", custom_id="team_signup"))
        view.add_item(Button(style=ButtonStyle.red, label="Sign off", emoji="📤", custom_id="team_signoff"))
        c.execute("SELECT * FROM team_find")
        data = c.fetchall()
        regions = {"NA": 0, "EU": 0, "SA": 0, "ASIA": 0}
        for entry in data:
            regions[entry[3]] += 1
        embed = discord.Embed().from_dict(team_finder[0])
        embed.add_field(name="**Members currently signed up:**", value=f"NA:〔{regions['NA']}〕EU:〔{regions['EU']}〕SA:〔{regions['SA']}〕ASIA:〔{regions['ASIA']}〕")
        await ctx.channel.send(embed=embed, view=view)

# region Basic commands
    @commands.command()
    async def clear(self, ctx, count=5):
        await ctx.channel.purge(limit=count+1)
        await ctx.channel.send(f"Deleted {count} messages", delete_after=3)
# endregion


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    client = MyClient(command_prefix='>', intents=discord.Intents.all())
    loop.create_task(client.start(bot.chaoz_bot().token))
    loop.run_forever()
