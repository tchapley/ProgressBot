import discord
from discord.ext import commands
import asyncio
import logging
import sys
import requests
from bs4 import BeautifulSoup
from params import set_api_key
from wowapi import WowApi

base_wow_progress = "http://www.wowprogress.com"
base_armory = "http://us.battle.net/wow/en/character/{0}/{1}/advanced"
class_array = [ "Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Death Knight",
                "Shaman", "Mage", "Warlock", "Monk", "Druid", "Demon Hunter" ]

set_api_key()

# Logger info
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='progressbot.log', encoding='utf-8', mode='w')
log.addHandler(handler)

bot = commands.Bot(command_prefix='!', description ='WowProgress Bot')



def has_name_header(self, character):
  if (self.name == "h1"):
    print(character)
  return self.name == "h1" and self.get_text().lower() == character.lower()

def get_kill_quantity(json, index):
  return json['statistics'][index]['quantity']

def get_difficulty(raid, bosses):
  difficulty = [ "M", "H", "N" ]
  bosses
  total = 0
  for i in range(3):
    for j in range(bosses):
      current_boss = (i+j)+((bosses-1)*i)
      if (raid[current_boss] > 0):
        total += 1
    if total > 0:
      return "{0}/{1}{2}".format(total, bosses, difficulty[i])
  return "{0}/{1}{2}".format(0, bosses, "N")

def populate_raids(json, raid, bosses, start_index):
  for i in range(3):
    for j in range(bosses):
      raid.append(get_kill_quantity(json, start_index-i+(4*j)))

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def guild(guild="dragon+knight", realm="boulderfist", region="us"):
  try:
    guild = guild.replace("_", "+")

    message = "**{0}** *{1}*".format(guild.replace("+", " "), realm)
    message += "```css\n"

    url = base_wow_progress + "/guild/{0}/{1}/{2}".format(region, realm, guild)
    page = requests.get(url)
    status = page.status_code
    if (status == 200):
      soup = BeautifulSoup(page.content, 'lxml')
      progress = soup.find_all("span", class_="innerLink")
      if not progress:
        raise ValueError("No progress span found")
      else:
        print(progress)
        for b in progress:
          print(b.get_text())
          message += b.get_text()
    elif (status > 400):
      raise HTTPError("URL returned status code {}".format(400))
  except Exception as e:
    logging.exception("Guild progress check failed [args: {0} {1} {2}]".format(guild, realm, region))
    message += "No data found for {0} on {1}-{2}".format(guild, region, realm)

  await bot.say(message+"```")


@bot.command()
async def realm(number=5, realm="connected-boulderfist", region="us"):
  if number > 20:
    number = 20
  elif number < 1:
    number = 1

  message = "```Top {0} guilds on {1}-{2}\n".format(number, region, realm)

  url = base_wow_progress + "/pve/{0}/{1}".format(region, realm)
  page = requests.get(url)
  soup = BeautifulSoup(page.content, "lxml")
  guilds = soup.find_all("a", class_="guild")
  ranks = soup.find_all("span", class_="rank")
  progress = soup.find_all("span", class_="innerLink")

  for i in range(0, number):
    message += "{0}\t{1}\t{2}\t{3}\n".format(i+1, guilds[i].get_text(), ranks[i].get_text(), progress[i].get_text())

  await bot.say(message+"```")

@bot.command()
async def mythic_plus(number=5, classes="", realm="connected-boulderfist", region="us"):
  if number > 20:
    number = 20
  elif number < 1:
    number = 1

  if classes:
    if classes == "death_knight":
      classes = string.replace(classes, "_", "")
    classes = "/class." + classes

  message = "```Top {0} mythic+ scores on {1}-{2}".format(number, region, realm)
  if classes:
    message += " for " + classes + "s"

  message += "\n"

  url = base_wow_progress + "/mythic_plus_score/{0}/{1}{2}".format(region, realm, classes)
  print(url)
  page = requests.get(url)
  soup = BeautifulSoup(page.content, "lxml")
  characters = soup.find_all("a", class_="character")
  guilds = soup.find_all("a", class_="guild")
  scores = soup.find_all("td", class_="center")

  for i in range(0, number):
    message += "{0}\t{1}\t{2}\t{3}\n".format(i+1, characters[i].get_text(), guilds[i].get_text(), scores[i].get_text())

  await bot.say(message+"```")

@bot.command()
async def artifact_power(number=5, classes="", realm="connected-boulderfist", region="us"):
  if number > 20:
    number = 20
  elif number < 1:
    number = 1

  if classes:
    if classes == "death_knight":
      classes = string.replace(classes, "_", "")
    classes = "/class." + classes

  message = "```Artifact power totals on {1}-{2}".format(number, region, realm)
  if classes:
    message += " for " + classes + "s"

  message += "\n"

  url = base_wow_progress + "/artifact_power/{0}/{1}{2}".format(region, realm, classes)
  print(url)

  page = requests.get(url)
  soup = BeautifulSoup(page.content, "lxml")

  characters = soup.find_all("a", class_="character")
  guilds = soup.find_all("a", class_="guild")
  scores = soup.find_all("td", class_="center")

  for i in range(0, number):
    message += "{0}\t{1}\t{2}\t{3}\n".format(i+1, characters[i].get_text(), guilds[i].get_text(), scores[i].get_text())

  await bot.say(message+"```")

@bot.command()
async def whoisyourmaster():
  await bot.reply("you are")

@bot.command()
async def character(name="bresp", realm="boulderfist", region="us"):

  payload = WowApi.get_character_profile(region, realm, name, locale="en_US", fields="achievements,items,statistics")

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

  print("Looking for {0} on {1}-{2}\n".format(name, region, realm))
  print(playerName)
  print(level)
  print(playerClass)
  print("Item Level: {0}".format(itemLevel))
  print("Achievement Points: {0}".format(achievementPoints))
  print("Artifact Power: {0}".format(artifactPoints))
  print("Main Artifact Level: {0}".format(mainLevel))
  print("Alt Artifact Level: {0}".format(altLevel))
  print(mythics)

  message = "**{0}** *{1} {2}*\n".format(playerName, level, playerClass)
  message += "```css\nItem Level: {0}\nAchievement Points: {1}\n".format(itemLevel, achievementPoints)
  message += "Artifact Power: {0}\nMain Artifact Level: {1}\n".format(artifactPoints, mainLevel)
  message += "Alt Artifact Level: {0}\n{1}\n".format(altLevel, mythics)
  message += "Raids:\n\tEmerald Nightmare: {0}\n\tTrial of Valor: {1}\n\tNighthold: {2}\n".format(en, tov, nh)

  await bot.say("{0}```\n<{1}>".format(message, base_armory.format(realm, name)))

@bot.command()
async def exit():
  print('Exiting')
  await bot.say('Exiting')
  await bot.logout()
  sys.exit()

bot.run('MjczNTgyNTAwNTk1MzY3OTM2.C2lq3A.imEczu1BMAqrOYJfZEBTPJavOvc')