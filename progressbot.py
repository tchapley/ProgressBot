import discord
from discord.ext import commands
import asyncio
import logging
import sys
import requests
from bs4 import BeautifulSoup
from util import *
from wowapi import WowApi
from wowapi import WowApi, WowApiException, WowApiConfigException
import datetime

base_wow_progress = "http://www.wowprogress.com"
base_wow_armory = "http://us.battle.net/wow/en/character/{0}/{1}/advanced"
base_wc_logs = "https://www.warcraftlogs.com:443/v1"
class_array = [ "Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Death Knight",
                "Shaman", "Mage", "Warlock", "Monk", "Druid", "Demon Hunter" ]

set_wow_api_key()
set_wclogs_api_key()

# Logger info
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

bot = commands.Bot(command_prefix='!', description ='Progress Bot')

"""
  Events Region
"""
@bot.event
async def on_ready():
  print("Logged in as {0} with ID {1}".format(bot.user.name, bot.user.id));

@bot.command()
async def exit():
  print('Exiting')
  # await bot.say('This conversation can serve no purpose anymore. Goodbye.')
  await bot.logout()

"""
  Commands Region

  TODO:
    Figure out how to get "connected" realms from wowprogress
"""
@bot.command()
async def ap(classes="", realm="connected-boulderfist", region="us"):
  print("\n%s***COMMAND***: artifact power command with arguments class=%s realm=%s region=%s"%(get_time(),classes, realm, region))

  url_class = ""
  if classes:
    if classes == "death_knight":
      classes = string.replace(classes, "_", "")
    url_class = "class." + classes

  url = base_wow_progress + "/artifact_power/{0}/{1}/{2}".format(region, realm, url_class)
  page = requests.get(url)
  print("URL: {0} Status: {1}".format(url, page.status_code))

  try:
    soup = BeautifulSoup(page.content, "lxml", from_encoding="UTF")
    table = soup.find("table").find_all("td")
    values = []
    for i in table:
      values.append(i.get_text().encode("UTF"))

    characters = []
    for rank, name, guild, ap in zip(values[0::4], values[1::4], values[2::4], values[3::4]):
      characters.append(ArtifactPower(rank.decode("unicode_escape"), name.decode("unicode_escape"), guild.decode("unicode_escape"), ap.decode("unicode_escape")))

    headers = ['rank', 'name', 'guild', 'ap']
    item_lens = [[getattr(character, x) for x in headers] for character in characters]
    max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in zip(*[headers] + item_lens)]

    message = "```css\nArtifact power rankings for {0}-{1}".format(region, realm)
    if classes:
      message += " for " + classes + "s"
    message += "\n"

    for i in characters:
      message += '\t'.join('{0:{width}}'.format(x, width=y) for x, y in zip([getattr(i, x) for x in headers], max_lens)) + "\n"

    await bot.say("{0}\n```<{1}>".format(message, url))
  except Exception as ex:
    print(ex)
    await bot.say("{0}\n<{1}>".format(str(ex), url))

@bot.command()
async def character(name="bresp", realm="boulderfist", region="us"):
  print("\n%s***COMMAND***: charater command with arguments name=%s realm=%s region=%s"%(get_time(), name, realm, region))
  payload = ""
  try:
    payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="achievements,items,statistics")
  except WowApiException as ex:
    print(ex)
    await bot.say(str(ex))
    return

  playerName = payload['name']
  level = payload['level']
  playerClass = class_array[payload['class']-1]
  itemLevel = payload['items']['averageItemLevelEquipped']
  achievementPoints = payload['achievementPoints']
  artifactPoints = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(30103)]
  mainLevel = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(29395)]
  altLevel = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(31466)]

  fifteen = 0
  ten = 0
  five = 0
  two = 0
  if 32028 in payload['achievements']['criteria']:
    fifteen = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(32028)]

  if 33098 in payload['achievements']['criteria']:
    ten += payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(33098)]

  if 33097 in payload['achievements']['criteria']:
    five += payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(33097)]

  if 33096 in payload['achievements']['criteria']:
    two += payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(33096)]

  mythics = "Mythics: #fifteen: {0} #ten: {1} #five: {2} #two: {3}".format(fifteen, ten, five, two)

  EN = []
  TOV = []
  NH = []
  for x in payload['statistics']['subCategories']:
    if x['name'] == "Dungeons & Raids":
      for y in x['subCategories']:
        if y['name'] == "Legion":
          populate_raids(y, EN, 7, 33)
          populate_raids(y, TOV, 3, 61)
          populate_raids(y, NH, 10, 73)

  en = get_difficulty(EN, 7)
  tov = get_difficulty(TOV, 3)
  nh = get_difficulty(NH, 10)

  print("Looking for {0} on {1}-{2}".format(name, region, realm))

  message = "**{0}** *{1} {2}*\n".format(playerName, level, playerClass)
  message += "```css\nItem Level: {0}\nAchievement Points: {1}\n".format(itemLevel, achievementPoints)
  message += "Artifact Power: {0}\nMain Artifact Level: {1}\n".format(artifactPoints, mainLevel)
  message += "Alt Artifact Level: {0}\n{1}\n".format(altLevel, mythics)
  message += "Raids:\n\tEmerald Nightmare: {0}\n\tTrial of Valor: {1}\n\tNighthold: {2}\n".format(en, tov, nh)

  await bot.say("{0}```\n<{1}>".format(message, base_wow_armory.format(realm, name)))

@bot.command()
async def guild(guild="dragon+knight", realm="boulderfist", region="us"):
  print("\n%s***COMMAND***: guild command with arguments guild=%s realm=%s region=%s"%(get_time(), guild, realm, region))

  guild = guild.replace("_", "+")

  url = base_wow_progress + "/guild/{0}/{1}/{2}".format(region, realm, guild)
  page = requests.get(url)
  print("URL: {0} Status: {1}".format(url, page.status_code))

  try:
    soup = BeautifulSoup(page.content, "lxml", from_encoding="UTF")
    progress = soup.find_all("span", class_="innerLink")
    if not progress: raise ValueError("No progress found\n<{0}>".format(url))
    print("Looking for %s on %s-%s"%(guild, region, realm))

    message = "**{0}** *{1}*".format(guild.replace("+", " "), realm)
    message += "```css\n"
    for b in progress:
      message += b.get_text()
    await bot.say("{0}\n```<{1}>".format(message, url))
  except Exception as ex:
    print(str(ex))
    await bot.say(str(ex))

@bot.command()
async def mp(classes="demon_hunter", realm="connected-boulderfist", region="us"):
  print("\n%s***COMMAND***: mythic plus command with arguments class=%s realm=%s region=%s"%(get_time(),classes, realm, region))

  url_class = ""
  if classes:
    if classes == "death_knight":
      classes = string.replace(classes, "_", "")
    url_class = "class." + classes

  url = base_wow_progress + "/mythic_plus_score/{0}/{1}/{2}".format(region, realm, url_class)
  page = requests.get(url)
  print("URL: {0} Status: {1}".format(url, page.status_code))

  try:
    soup = BeautifulSoup(page.content, "lxml", from_encoding="UTF")
    table = soup.find("table").find_all("td")

    values = []
    for i in table:
      values.append(i.get_text().encode("UTF"))

    characters = []
    for rank, name, guild, score in zip(values[0::4], values[1::4], values[2::4], values[3::4]):
      characters.append(MythicPlus(rank.decode("unicode_escape"), name.decode("unicode_escape"), guild.decode("unicode_escape"), score.decode("unicode_escape")))

    headers = ['rank', 'name', 'guild', 'score']
    item_lens = [[getattr(character, x) for x in headers] for character in characters]
    max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in zip(*[headers] + item_lens)]

    message = "```css\nMythic plus rankings for {0}-{1}".format(region, realm)
    if classes:
      message += " for " + classes + "s"
    message += "\n"

    for i in characters:
      message += "\t".join('{0:{width}}'.format(x, width=y) for x, y in zip([getattr(i, x) for x in headers], max_lens)) + "\n"

    await bot.say("{0}\n```<{1}>".format(message, url))
  except Exception as ex:
    print(ex)
    await bot.say("{0}\n<{1}>".format(str(ex), url))

@bot.command()
async def rank(name="bresp", spec="vengeance", realm="boulderfist", region="us"):
  print("\n%s***COMMAND***: rank command with arguments name=%s spec=%s realm=%s region=%s"%(get_time(), name, spec, realm, region))

  stats = {
    5: { 'kill': 0, 'allstar': 0, 'perf': 0, 'size': 0, 'median': 0},
    4: { 'kill': 0, 'allstar': 0, 'perf': 0, 'size': 0, 'median': 0},
    3: { 'kill': 0, 'allstar': 0, 'perf': 0, 'size': 0, 'median': 0}
  }
  character_id = ""

  url = base_wc_logs + "/parses/character/{0}/{1}/{2}".format(name, realm, region)
  page = requests.get(url, {'api_key': os.environ['WCLOG_APIKEY'] })
  print("URL: {0} Status: {1}".format(url, page.status_code))

  if page.status_code != 200:
    await bot.say("No rankings found\n<{0}>".format(url))
    return
  else:
    payload = page.json()
    for i in payload:
      difficulty = i['difficulty']
      stats[difficulty]['size'] += 1

      for j in range(0, len(i['specs'])):
        character_id = i['specs'][j]['data'][0]['character_id']
        if i['specs'][j]['spec'].lower() == spec.lower():
          stats[difficulty]['kill'] += len(i['specs'][j]['data'])
          stats[difficulty]['allstar'] += i['specs'][j]['best_allstar_points']
          stats[difficulty]['perf'] += i['specs'][j]['best_historical_percent']
          stats[difficulty]['median'] += i['specs'][j]['historical_median']



    items = []
    for key in stats:
      difficulty = ""
      if key == 5: difficulty = "Mythic"
      elif key == 4: difficulty = "Heroic"
      elif key == 3: difficulty = "Normal"
      kills = stats[key]['kill']
      allstar = round(stats[key]['allstar'])
      size = stats[key]['size']
      perf = stats[key]['perf']
      median = stats[key]['median']
      if size != 0:
        perf = round(perf / size)
        median = round(median / size)
      items.append(Rankings(difficulty, perf, median, kills, allstar))

    headers = ['difficulty', 'best', 'median', 'kills', 'points']
    item_lens = [[getattr(item, x) for x in headers] for item in items]
    max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in zip(*[headers] + item_lens)]


    message = "```css\nLatest rankings for {0} (spec={1}) on {2}-{3}\n".format(name, spec, region, realm)
    message += "\t".join('{0:{width}}'.format(x, width=y) for x, y in zip(headers, max_lens)) + '\n'
    for i in items:
      message += "\t".join('{0:{width}}'.format(x, width=y) for x, y in zip([getattr(i, x) for x in headers], max_lens)) + "\n"

    url = "https://www.warcraftlogs.com/rankings/character/{0}/latest".format(character_id)
    await bot.say("{0}\n```<{1}>".format(message, url))

@bot.command()
async def realm(realm="connected-boulderfist", region="us"):
  print("\n%s***COMMAND***: realm command with arguments realm=%s region=%s"%(get_time(), realm, region))

  url = base_wow_progress + "/pve/{0}/{1}".format(region, realm)
  page = requests.get(url)
  print("URL: {0} Status: {1}".format(url, page.status_code))

  try:
    soup = BeautifulSoup(page.content, "lxml", from_encoding="UTF")

    guilds = soup.find_all("a", class_="guild")
    ranks = soup.find_all("span", class_="rank")
    progress = soup.find_all("span", class_="ratingProgress")

    items = []
    for i in range(0, len(guilds)):
      items.append(GuildProgress(i+1, guilds[i].get_text(), ranks[i].get_text(), progress[i].get_text()))

    headers = ['rank', 'name', 'world', 'progress']
    item_lens = [[getattr(guild, x) for x in headers] for guild in items]
    max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in zip(*[headers] + item_lens)]

    message = "```css\nGuild progress rankings for {0}-{1}\n".format(region, realm)
    for i in items:
      message += '\t'.join('{0:{width}}'.format(x, width=y) for x, y in zip([getattr(i, x) for x in headers], max_lens)) + "\n"

    await bot.say("{0}\n```<{1}>".format(message, url))
  except Exception as ex:
    print(ex)
    await bot.say("{0}\n<{1}>".format(str(ex), url))

@bot.command()
async def whoisyourmaster():
  await bot.reply("you are")

bot.run('MjczNTgyNTAwNTk1MzY3OTM2.C2lq3A.imEczu1BMAqrOYJfZEBTPJavOvc')