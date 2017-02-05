import discord
from discord.ext import commands
import asyncio
import logging
import sys
import requests
from bs4 import BeautifulSoup
from util import *
from wowapi import WowApi, WowApiException, WowApiConfigException
import datetime
from killpoints import KillPoints

base_wow_progress = "http://www.wowprogress.com"
base_wow_armory = "http://us.battle.net/wow/en/character/{0}/{1}/advanced"
base_wc_logs = "https://www.warcraftlogs.com:443/v1"
class_array = [ "Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Death Knight",
                "Shaman", "Mage", "Warlock", "Monk", "Druid", "Demon Hunter" ]
race_map = {
  1: "Human", 2: "Orc", 3: "Dwarf", 4: "Night Elf", 5: "Undead", 6: "Tauren",  7: "Gnome",
  8: "Troll", 9: "Goblin", 10: "Blood Elf", 11: "Draenei", 22: "Worgen",
  24:"Pandaren", 25:"Pandaren", 26:"Pandaren"
}

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
"""
@bot.command()
async def ap(classes="", realm="connected-boulderfist", region="us"):

  print("\n%s***COMMAND***: artifact power command with arguments class=%s realm=%s region=%s"%(get_current_time(),classes, realm, region))

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

  print("\n%s***COMMAND***: character command with arguments name=%s realm=%s region=%s"%(get_current_time(), name, realm, region))

  payload = ""
  try:
    payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="achievements,items,statistics")
  except WowApiException as ex:
    print(ex)
    await bot.say(str(ex))
    return

  playerName = payload['name']
  level = payload['level']
  race = race_map[payload['race']]
  playerClass = class_array[payload['class']-1]

  playerRealm = payload['realm']
  battlegroup = payload['battlegroup']
  itemLevel = payload['items']['averageItemLevelEquipped']
  achievementPoints = payload['achievementPoints']
  artifactPoints = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(30103)]
  mainLevel = payload['achievements']['criteriaQuantity'][payload['achievements']['criteria'].index(29395)]
  lastModified = get_time(payload['lastModified'] / 1000)

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

  message = "**{0}** *{1} {2} {3}*\n".format(playerName, level, race, playerClass)
  message += "```css\n"
  message += "Realm: {0}\n".format(playerRealm)
  message += "Battlegroup: {0}\n".format(battlegroup)
  message += "Item Level: {0}\n".format(itemLevel)
  message += "Achievement Points: {0}\n".format(achievementPoints)
  message += "Artifact Power: {0}\n".format(artifactPoints)
  message += "Main Artifact Level: {0}\n".format(mainLevel)
  message += "{0}\n".format(mythics)
  message += "Raids:\n\tEmerald Nightmare: {0}\n\tTrial of Valor: {1}\n\tNighthold: {2}\n".format(en, tov, nh)

  await bot.say("{0}```\nLast Updated: {1}\n<{2}>".format(message, lastModified, base_wow_armory.format(realm, playerName)))

@bot.command()
async def guild(guild="dragon+knight", realm="boulderfist", region="us"):

  print("\n%s***COMMAND***: guild command with arguments guild=%s realm=%s region=%s"%(get_current_time(), guild, realm, region))

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
async def legendary(name="bresp", realm="boulderfist", region="us"):

  print("\n%s***COMMAND***: legendary command with arguments name=%s realm=%s region=%s"%(get_current_time(),name, realm, region))

  payload = ""
  try:
    payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="achievements,progression")
  except WowApiException as ex:
    print(ex)
    await bot.say(str(ex))
    return

  kp = KillPoints(payload)
  killpoints = kp.get_total_points()
  legendaries = kp.get_legendary_count(killpoints)
  till_next = kp.get_points_till_next(killpoints)
  percent_till_next = kp.get_percent_till_next()
  message = "**{0}** has **{1}** kill points.\n".format(payload['name'], killpoints)
  message += "They should have **{0} legendaries**\n".format(legendaries)
  message += "They have **{0} points** until their next legendary\n".format(till_next)
  message += "They have completed **{0}%** of the progress towards their next legendary".format(percent_till_next)


  await bot.say(message)

@bot.command()
async def mounts(name="bresp", mount="", realm="boulderfist", region="us"):

  print("\n%s***COMMAND***: mount command with arguments name=%s mount=%s realm=%s region=%s"%(get_current_time(), name, mount, realm, region))

  payload = ""
  try:
    payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="mounts")
  except WowApiException as ex:
    print(ex)
    await bot.say(str(ex))
    return
  playerName = payload['name']

  if not mount:
    collected = payload['mounts']['numCollected']
    await bot.say("**{0}** has collected **{1} mounts**".format(playerName, collected))
  else:
    mount.replace("\"", "")
    for m in payload['mounts']['collected']:
      if m['name'] == mount:
        await bot.say("**{0}** has collected **{1}**".format(playerName, m['name']))
        return
    else:
      await bot.say("**{0}** has *not* collected **{1}**".format(playerName, mount))


@bot.command()
async def mp(classes="", realm="connected-boulderfist", region="us"):

  print("\n%s***COMMAND***: mythic plus command with arguments class=%s realm=%s region=%s"%(get_current_time(),classes, realm, region))

  url_class = ""
  if classes:
    if classes == "death_knight":
      classes = classes.replace("_", "")
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
async def pvp(name="", realm="boulderfist", region="us"):

  print("\n%s***COMMAND***: pvp command with arguments name=%s realm=%s region=%s"%(get_current_time(), name, realm, region))

  payload = ""
  try:
    payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="pvp")
  except WowApiException as ex:
    print(ex)
    await bot.say(str(ex))
    return

  playerName = payload['name']
  level = payload['level']
  race = race_map[payload['race']]
  playerClass = class_array[payload['class']-1]
  lastModified = get_time(payload['lastModified'] / 1000)

  playerRealm = payload['realm']
  battlegroup = payload['battlegroup']

  honorableKills = payload['totalHonorableKills']
  rbgRating = payload['pvp']['brackets']['ARENA_BRACKET_RBG']['rating']
  twosRating = payload['pvp']['brackets']['ARENA_BRACKET_2v2']['rating']
  threesRating = payload['pvp']['brackets']['ARENA_BRACKET_3v3']['rating']

  message = "**{0}** *{1} {2} {3}*\n".format(playerName, level, race, playerClass)
  message += "```css\n"
  message += "Realm: {0}\n".format(playerRealm)
  message += "Battlegroup: {0}\n".format(battlegroup)
  message += "Honorable Kills: {0}\n".format(honorableKills)
  message += "Rated BG Rating: {0}\n".format(rbgRating)
  message += "Twos Rating: {0}\n".format(twosRating)
  message += "Threes Rating: {0}\n".format(threesRating)

  await bot.say("{0}```\nLast Updated: {1}\n<{2}>".format(message, lastModified, base_wow_armory.format(realm, playerName)))

@bot.command()
async def rank(name="", spec="", role="dps", realm="boulderfist", region="us"):

  print("\n%s***COMMAND***: rank command with arguments name=%s spec=%s role=%s realm=%s region=%s"%(get_current_time(), name, spec, role, realm, region))

  if not spec:
    await bot.say("Please provide a spec to check ranks for")
    return

  if role not in [ 'dps', 'hps', 'krsi' ]:
    await bot.say("Please provide a valid role. Your options are hps, dps, or krsi")
    return

  stats = {
    5: { 'kills': 0, 'best': 0, 'average': 0, 'allstar_points': 0, 'size': 0},
    4: { 'kills': 0, 'best': 0, 'average': 0, 'allstar_points': 0, 'size': 0},
    3: { 'kills': 0, 'best': 0, 'average': 0, 'allstar_points': 0, 'size': 0}
  }
  character_id = ""

  url = base_wc_logs + "/parses/character/{0}/{1}/{2}".format(name, realm, region)
  page = requests.get(url, { 'metric': role, 'api_key': os.environ['WCLOG_APIKEY'] })
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
          stats[difficulty]['kills'] += len(i['specs'][j]['data'])
          historical_percent = i['specs'][j]['best_historical_percent']
          if historical_percent > stats[difficulty]['best']:
            stats[difficulty]['best'] = historical_percent
          stats[difficulty]['average'] += historical_percent
          stats[difficulty]['allstar_points'] += i['specs'][j]['best_allstar_points']



    items = []
    for key in stats:
      difficulty = ""
      if key == 5: difficulty = "Mythic"
      elif key == 4: difficulty = "Heroic"
      elif key == 3: difficulty = "Normal"
      kills = stats[key]['kills']
      best = stats[key]['best']
      average = stats[key]['average']
      size = stats[key]['size']
      if size != 0:
        average = round(average / size)
      allstar_points = round(stats[key]['allstar_points'])
      items.append(Rankings(difficulty, kills, best, average, allstar_points))

    headers = ['difficulty', 'kills', 'best', 'average', 'allstar_points']
    item_lens = [[getattr(item, x) for x in headers] for item in items]
    max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in zip(*[headers] + item_lens)]


    message = "```css\nLatest rankings for {0} (spec={1} role={2}) on {3}-{4}\n".format(name, spec, role, region, realm)
    message += "\t".join('{0:{width}}'.format(x, width=y) for x, y in zip(headers, max_lens)) + '\n'
    for i in items:
      message += "\t".join('{0:{width}}'.format(x, width=y) for x, y in zip([getattr(i, x) for x in headers], max_lens)) + "\n"

    url = "https://www.warcraftlogs.com/rankings/character/{0}/latest".format(character_id)
    await bot.say("{0}\n```<{1}>".format(message, url))

@bot.command()
async def realm(realm="connected-boulderfist", region="us"):

  print("\n%s***COMMAND***: realm command with arguments realm=%s region=%s"%(get_current_time(), realm, region))

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