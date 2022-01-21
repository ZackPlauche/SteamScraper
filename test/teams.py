from os import remove
import discord, sqlite3, sys, linecache, asyncio, pytz
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, CheckFailure
from discord.team import Team
from discord.utils import get, parse_time
from discord.ui import *
from discord import ButtonStyle
from datetime import *

datab = 'database.sqlite'

db = sqlite3.connect(datab)
c = db.cursor()

timez = pytz.timezone("US/Eastern")

#region Functions
def init():
  global team_find_embed, panel_users, captain_role, admin_role, role_placeholder, operator_role
  team_find_embed = None
  panel_users = None
  captain_role = None
  admin_role = None
  operator_role = None
  role_placeholder = None

def PrintException():
  exc_type, exc_obj, tb = sys.exc_info()
  f = tb.tb_frame
  lineno = tb.tb_lineno
  filename = f.f_code.co_filename
  linecache.checkcache(filename)
  line = linecache.getline(filename, lineno, f.f_globals)
  print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def teams_panel_embed(title, description=None, thumbnail="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png"):
  embed = discord.Embed(
    title=title,
    description=description
  ).set_thumbnail(url=thumbnail)
  embed.set_author(name="CHAOZ Teams Panel", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
  return embed

async def send_signup_embed(channel):
  view = View()
  view.add_item(Button(style=ButtonStyle.green, label="Signup", emoji="📩", custom_id="team_signup"))
  view.add_item(Button(style=ButtonStyle.red, label="Sign off", emoji="📤", custom_id="team_signoff"))
  c.execute("SELECT * FROM team_find")
  data = c.fetchall()
  regions = {"NA": 0, "EU": 0, "SA": 0, "ASIA": 0}
  for entry in data:
    regions[entry[3]] += 1
  embed = discord.Embed().from_dict(team_find_embed)
  embed.add_field(name="**Members currently signed up:**", value=f"NA:〔{regions['NA']}〕EU:〔{regions['EU']}〕SA:〔{regions['SA']}〕ASIA:〔{regions['ASIA']}〕")
  await channel.send(embed=embed, view=view)

def team_create_embed(title, team_name='', team_region='', team_captain=''):
  embed = discord.Embed(title=f"**{title}**")
  embed.set_author(name="CHAOZ Team Creator", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
  embed.set_thumbnail(url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
  embed.add_field(
      name="**What you'll need to provide**",
      value=f"1. Team Name: {team_name}\n2. Team Region: {team_region}\n3. Team Captain: {team_captain}"
  )
  embed.set_footer(text=f"Current step: {title}")
  return embed

def team_edit_embed(title, description=''):
  embed = discord.Embed(title=f"**{title}**", description=description)
  embed.set_author(name="CHAOZ Team Editor", icon_url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
  embed.set_thumbnail(url="https://www.chaoz.gg/wp-content/uploads/2021/12/ChaoZ-Discord-Bot-min.png")
  embed.set_footer(text=f"Current step: {title}")
  return embed

async def create_team_category(server, name, captain=None):
  role = await server.create_role(name=name)
  role.hoist = True
  await role.edit(position=int(role_placeholder.position))
  if captain != None:
    await captain.add_roles(role)
  length = round((29 - (len(name) + 4)) / 2)
  cat_name = f'{"-"*length}[ {name} ]{"-"*length}'
  overwrites = {'@everyone': {'read_message_history': False, 'manage_webhooks': False, 'manage_roles': False, 'manage_guild': None, 'view_guild_insights': None, 'speak': True, 'send_messages': False, 'send_tts_messages': False, 'connect': False, 'move_members': False, 'create_instant_invite': False, 'mute_members': False, 'deafen_members': False, 'use_slash_commands': False, 'view_audit_log': None, 'manage_channels': False, 'manage_emojis': None, 'manage_messages': False, 'embed_links': False, 'attach_files': False, 'administrator': None, 'kick_members': None, 'external_emojis': False, 'read_messages': False, 'add_reactions': False, 'use_voice_activation': True, 'request_to_speak': None, 'mention_everyone': False, 'manage_nicknames': None, 'ban_members': None, 'change_nickname': None, 'stream': True, 
'priority_speaker': False}, f'{name}': {'read_message_history': True, 'manage_webhooks': False, 'manage_roles': False, 'manage_guild': None, 'view_guild_insights': None, 'speak': True, 'send_messages': True, 'send_tts_messages': False, 'connect': True, 'move_members': False, 'create_instant_invite': False, 'mute_members': False, 'deafen_members': False, 'use_slash_commands': False, 'view_audit_log': None, 'manage_channels': False, 'manage_emojis': None, 'manage_messages': False, 'embed_links': True, 'attach_files': True, 'administrator': None, 'kick_members': None, 'external_emojis': True, 'read_messages': True, 'add_reactions': True, 'use_voice_activation': True, 'request_to_speak': None, 'mention_everyone': True, 'manage_nicknames': None, 'ban_members': None, 'change_nickname': None, 'stream': True, 'priority_speaker': False}}
  overwrite = {}
  for rolename in overwrites:
    role = get(server.roles, name=rolename)
    if role != None: overwrite[role] = discord.PermissionOverwrite(**overwrites[rolename])
  category = await server.create_category(name=cat_name, overwrites=overwrite)
  await category.create_text_channel(name=f"{'-'.join(name.split(' '))}-chat")
  await category.create_voice_channel(name=f"{name} Voice")
  c.execute("UPDATE teams SET category=?, role=? WHERE team_name=?", (str(category.id), str(role.id), str(name)))
  db.commit()
#endregion

#region Team creation
class TeamChannels(View):
  def __init__(self, ctx, bot, author, team_name, team_captain):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author
    self.name = team_name
    self.captain = team_captain

    self.add_item(Button(style=ButtonStyle.blurple, label="Yes", emoji="✅", custom_id="yes"))
    self.add_item(Button(style=ButtonStyle.blurple, label="No", emoji="❌", custom_id="no"))

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
      if interaction.data["custom_id"] == "yes":
        await self.ctx.delete()
        await create_team_category(self.ctx.guild, self.name, self.captain)
        self.stop()
      else:
        await self.ctx.delete()
        self.stop()

  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()

class TeamCreate(View):
  def __init__(self, ctx, bot, author, team_name):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author

    # Team data
    self.team_name = team_name
    self.team_region = None
    self.team_captain = None

    self.add_item(Button(style=ButtonStyle.blurple, label="NA", emoji="🇺🇸", custom_id="NA"))
    self.add_item(Button(style=ButtonStyle.green, label="EU", emoji="🇪🇺", custom_id="EU"))
    self.add_item(Button(style=ButtonStyle.red, label="South America", emoji="🇧🇷", custom_id="SA"))
    self.add_item(Button(style=ButtonStyle.grey, label="ASIA", emoji="🇯🇵", custom_id="ASIA"))

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
      self.team_region = interaction.data["custom_id"]

      c.execute("INSERT INTO teams (team_name, team_region) VALUES (?, ?)", (str(self.team_name), str(self.team_region)))
      db.commit()

      # Wait for captains id
      await interaction.response.edit_message(embed=team_create_embed("Send team captains discord id", self.team_name, self.team_region), view=None)
      while True:
        try:
          message = await self.bot.wait_for('message', check=lambda interaction: interaction.author == self.author, timeout=60)
          if str(message.content).isnumeric():
            self.team_captain = self.ctx.guild.get_member(int(message.content))
            role = get(self.ctx.guild.roles, id=int(captain_role))
            await self.team_captain.add_roles(role)
            await message.delete()
            await self.ctx.edit(embed=team_create_embed("Create team channels and role?", self.team_name, self.team_region, self.team_captain), view=TeamChannels(self.ctx, self.bot, self.author, self.team_name, self.team_captain))
            self.stop()
            break
          else:
            await self.ctx.channel.send("Incorrect value sent, please copy users id and send it", delete_after=5)
        except Exception as e:
          print(e)
          await interaction.channel.send("**Setup timed out! deleting message...**", delete_after=3)
          await asyncio.sleep(3)
          await self.ctx.delete()
          self.stop()

  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()
#endregion

#region Team edit
class TeamSelect(View):
  def __init__(self, ctx, bot, author, index_s=0, team_list=[], rem=False):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author
    self.rem = rem

    self.button_left = Button(style=ButtonStyle.blurple, emoji="◀", custom_id="select_left")
    self.button_right = Button(style=ButtonStyle.blurple, emoji="▶", custom_id="select_right")

    self.team_list = team_list
    self.index_s, self.index_e = index_s, index_s + 5

    if team_list == []:
      c.execute("SELECT * FROM teams")
      data = c.fetchall()
      for entry in data:
        if str(entry[4]).isnumeric():
          if get(ctx.guild.roles, id=int(entry[4])) in self.author.roles or self.author.id in panel_users or admin_role in self.author.roles or operator_role in self.author.roles:
            self.team_list.append(Button(style=ButtonStyle.green, label=entry[0], custom_id=entry[0]))
    
    if self.index_e > len(self.team_list):
      self.index_e = len(self.team_list)

    self.get_team_list(self.index_s, self.index_e, self.team_list)

  def get_team_list(self, index_s, index_e, team_list):
    self.clear_items()
    if index_e > len(team_list):
      index_e = len(team_list)
    for button in team_list[index_s:index_e]:
      self.add_item(button)
    if len(team_list) > 5:
      self.add_item(self.button_left)
      self.add_item(self.button_right)

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
      #Remove timeout
      super().__init__(timeout=None)

      if interaction.data["custom_id"] == "select_left":
        if self.index_s > 0:
          self.index_s -= 5; self.index_e -= 5
          if self.index_s < 0: self.index_s = 0; self.index_e = 5
        await interaction.response.edit_message(embed=team_edit_embed("Choose team to edit"), view=TeamSelect(self.ctx, self.bot, self.author, self.index_s, self.team_list, rem=self.rem))
      elif interaction.data["custom_id"] == "select_right":
        if self.index_e < len(self.team_list):
          self.index_s += 5; self.index_e += 5
          if self.index_e > len(self.team_list): self.index_e = len(self.team_list)
        await interaction.response.edit_message(embed=team_edit_embed("Choose team to edit"), view=TeamSelect(self.ctx, self.bot, self.author, self.index_s, self.team_list, rem=self.rem))
      else:
        if self.rem == False:
          await interaction.response.edit_message(embed=team_edit_embed("Choose action"), view=TeamEdit(self.ctx, self.bot, self.author, interaction.data["custom_id"]))
        else:
          c.execute("DELETE FROM teams WHERE team_name=?", (str(interaction.data["custom_id"]),))
          db.commit()
          await interaction.response.edit_message(embed=team_edit_embed("Team removed"), view=None)
          await asyncio.sleep(3)
          await self.ctx.delete()
      self.stop()

  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()

class TeamEdit(View):
  def __init__(self, ctx, bot, author, team):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author
    self.team = team

    self.add_item(Button(style=ButtonStyle.blurple, label="Add member", emoji="➕", custom_id="edit_add"))
    self.add_item(Button(style=ButtonStyle.blurple, label="Remove member", emoji="❌", custom_id="edit_remove"))

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
      #Remove timeout
      super().__init__(timeout=None)

      c.execute("SELECT * FROM teams WHERE team_name=?", (str(self.team),))
      data = c.fetchone()
      if interaction.data["custom_id"] == "edit_add":
        await interaction.response.edit_message(embed=team_edit_embed(title='Send player info', description='ex. "__discord-id__**;**__steam-profile-link__**;**__region(NA, EU, etc.)__"\n**Seperate with ;**'), view=None)
        while True:
          player_info = await self.bot.wait_for('message', check=lambda interaction: interaction.author == self.author, timeout=180)
          if ';' not in player_info.content: await interaction.channel.send("Please seperate each field with ';'", delete_after=4)
          try:
            player_data = player_info.content.split(';')
            await player_info.delete()
            try:
              player = get(self.ctx.guild.members, id=int(player_data[0]))
              player_data.append(str(datetime.now(timez)))
              if data[1] != None:
                member_data = data[1].split('|')
                c.execute('UPDATE teams SET team_players=? WHERE team_name=?', (str(f'{"|".join(member_data)}|{";".join(player_data)}'), str(self.team)))
              else:
                c.execute('UPDATE teams SET team_players=? WHERE team_name=?', (str(";".join(player_data)), str(self.team)))
              db.commit()
              try:
                role = get(self.ctx.guild.roles, id=int(data[4]))
                await player.add_roles(role)
              except:
                await self.ctx.channel.send("Could not give user team role", delete_after=4)
              await self.ctx.channel.send(f'**Player: {str(player)} has been added to team {self.team}**', delete_after=4)
              await self.ctx.delete()
              self.stop()
              break
            except:
              await self.ctx.channel.send('Invalid discord id passed canceling proccess', delete_after=3)
              await self.ctx.delete()
              self.stop()
              break
          except Exception as e:
            PrintException()
            await self.ctx.channel.send('Bad player fields passed canceling proccess', delete_after=3)
            await self.ctx.delete()
            self.stop()
            break
      elif interaction.data["custom_id"] == "edit_remove":
        try:
          players = None
          player_list = {}
          if '|' in data[1]:
            players = data[1].split('|')
            for player in players:
              player_id, player_steam, player_region, player_time = player.split(';')
              player_list[player_id] = [player_steam, player_region, player_time]
          else:
            player_id, player_steam, player_region, player_time = data[1].split(';')
            player_list[player_id] = [player_steam, player_region, player_time]
          await interaction.response.edit_message(embed=team_edit_embed(title="Choose member to remove"), view=TeamMemberRemove(self.ctx, self.bot, self.author, player_list, self.team))
        except:
          PrintException()
          await self.ctx.channel.send("No members in this team!", delete_after=4)
          await self.ctx.delete()
          self.stop()

  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()

class TeamMemberRemove(View):
  def __init__(self, ctx, bot, author, player_list, team, index_s=0):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author
    self.player_list = player_list
    self.team = team

    self.button_left = Button(style=ButtonStyle.blurple, emoji="◀", custom_id="select_left")
    self.button_right = Button(style=ButtonStyle.blurple, emoji="▶", custom_id="select_right")

    self.index_s, self.index_e = index_s, index_s + 5

    self.get_member_list(self.index_s, self.index_e, self.player_list)

  def get_member_list(self, index_s, index_e, member_list):
    self.clear_items()
    if index_e > len(member_list):
      index_e = len(member_list)
    for player_id in list(member_list.keys())[index_s:index_e]:
      player_name = self.ctx.guild.get_member(int(player_id))
      self.add_item(Button(style=ButtonStyle.green, label=str(player_name), custom_id=player_id))
    if len(member_list) > 5:
      self.add_item(self.button_left)
      self.add_item(self.button_right)

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
      #Remove timeout
      super().__init__(timeout=None)

      if interaction.data["custom_id"] == "select_left":
        if self.index_s > 0:
          self.index_s -= 5; self.index_e -= 5
          if self.index_s < 0: self.index_s = 0; self.index_e = 5
        await interaction.response.edit_message(embed=team_edit_embed("Choose player to remove"), view=TeamSelect(self.ctx, self.bot, self.author, self.player_list, self.team, self.index_s))
      elif interaction.data["custom_id"] == "select_right":
        if self.index_e < len(self.player_list):
          self.index_s += 5; self.index_e += 5
          if self.index_e > len(self.player_list): self.index_e = len(self.player_list)
        await interaction.response.edit_message(embed=team_edit_embed("Choose player to remove"), view=TeamSelect(self.ctx, self.bot, self.author, self.player_list, self.team, self.index_s))
      else:
          players_data = []
          for player in self.player_list:
            if int(player) != int(interaction.data["custom_id"]):
              players_data.append(f"{player};{self.player_list[player][0]};{self.player_list[player][1]};{self.player_list[player][2]}")
          if len(players_data) == 1:
            c.execute("UPDATE teams SET team_players=? WHERE team_name=?", (str(players_data[0]), str(self.team)))
          else:
            c.execute("UPDATE teams SET team_players=? WHERE team_name=?", (str("|".join(players_data)), str(self.team)))
          db.commit()
          await interaction.response.edit_message(embed=team_edit_embed('Member removed successfully'), view=None)
          await asyncio.sleep(4)
          await self.ctx.delete()
          self.stop()
  
  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()
#endregion

class PanelView(View):
  def __init__(self, ctx, bot, author):
    super().__init__(timeout=30)
    self.ctx = ctx
    self.bot = bot
    self.author = author

    if self.author.id in panel_users or admin_role in self.author.roles or operator_role in self.author.roles:
      self.add_item(Button(style=ButtonStyle.blurple, label="Send teamfinder embed", custom_id="team_embed"))
      self.add_item(Button(style=ButtonStyle.green, label="Add team", emoji="🥇", custom_id="team_create"))
      self.add_item(Button(style=ButtonStyle.red, label="Remove team", emoji="🧧", custom_id="team_delete"))
    role = get(self.ctx.guild.roles, id=911235622319034368)
    if role in self.author.roles or admin_role in self.author.roles or operator_role in self.author.roles:
      self.add_item(Button(style=ButtonStyle.blurple, label="Edit members", emoji="📄", custom_id="team_edit"))
    self.add_item(Button(style=ButtonStyle.red, label="View teams", emoji="🎫", custom_id="team_view"))

  async def interaction_check(self, interaction):
    if interaction.user == self.author and interaction.message == self.ctx:
        #Remove timeout
        super().__init__(timeout=None)

        if interaction.data["custom_id"] == "team_embed":
          await send_signup_embed(self.ctx.channel)
          await self.ctx.delete()
        elif interaction.data["custom_id"] == "team_create":
          await interaction.response.edit_message(embed=team_create_embed("Send team name"), view=None)
          try:
              message = await self.bot.wait_for('message', check=lambda interaction: interaction.author == self.author, timeout=60)
              team_name = message.content
              await message.delete()
              await self.ctx.edit(embed=team_create_embed("**Choose team region**", team_name), view=TeamCreate(self.ctx, self.bot, self.author, team_name))
          except Exception as e:
              print(e)
              await interaction.channel.send("**Setup timed out! deleting message...**", delete_after=3)
              await asyncio.sleep(3)
              await self.ctx.delete()
          self.stop()
        elif interaction.data["custom_id"] == "team_delete":
          await interaction.response.edit_message(embed=team_edit_embed("Choose team to remove"), view=TeamSelect(self.ctx, self.bot, self.author, rem=True))
          self.stop()
        elif interaction.data["custom_id"] == "team_edit":
          await interaction.response.edit_message(embed=team_edit_embed("Choose team to edit"), view=TeamSelect(self.ctx, self.bot, self.author))
          self.stop()
        elif interaction.data["custom_id"] == "team_view":
          await self.ctx.delete()
          self.stop()
          c.execute("SELECT * FROM teams")
          data = c.fetchall()
          output = ["```diff", "Teams"]
          for team in data:
            output.append(f"+{team[0]}")
            if team[1] != None and team[1] != '':
              if '|' in team[1]:
                for member in team[1].split('|'):
                  if ';' in member:
                    try:
                      disc, steam, region, date_added = member.split(';')
                      date_added = date_added.split(' ')[0]
                      member = get(self.ctx.guild.members, id=int(disc))
                      if get(self.ctx.guild.roles, id=captain_role) in member.roles:
                        output.append(f"+ Captain discord: {str(member)}, steam: {steam}, region: {region}, date added: {date_added}")
                      else:
                        output.append(f"- discord: {str(member)}, steam: {steam}, region: {region}, date added: {date_added}")
                    except:
                      None
                  else:
                    output.append("- No members")
              elif ';' in team[1]:
                member = team[1]
                try:
                  disc, steam, region, date_added = member.split(';')
                  date_added = date_added.split(' ')[0]
                  member = get(self.ctx.guild.members, id=int(disc))
                  if get(self.ctx.guild.roles, id=captain_role) in member.roles:
                    output.append(f"+ Captain discord: {str(member)}, steam: {steam}, region: {region}, date added: {date_added}")
                  else:
                    output.append(f"- discord: {str(member)}, steam: {steam}, region: {region}, date added: {date_added}")
                except:
                  None
              else:
                output.append("- No members")
            else:
              output.append("- No members")
          output.append("```")
          await self.ctx.channel.send(str("\n".join(output)))

        self.stop()

  async def on_timeout(self):
    await self.ctx.channel.send("**Panel timed out! deleting message...**", delete_after=3)
    await asyncio.sleep(3)
    await self.ctx.delete()
    self.stop()