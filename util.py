import os
import requests
import datetime

class ArtifactPower(object):
  def __init__(self, rank, name, guild, ap):
    self.rank = rank
    self.name = name
    self.guild = guild
    self.ap = ap

class MythicPlus(object):
  def __init__(self, rank, name, guild, score):
    self.rank = rank
    self.name = name
    self.guild = guild
    self.score = score

class GuildProgress(object):
  def __init__(self, rank, name, world, progress):
    self.rank = rank
    self.name = name
    self.world = world
    self.progress = progress

class Rankings(object):
  def __init__(self, difficulty, kills, best, average, allstar_points):
    self.difficulty = difficulty
    self.kills = kills
    self.best = best
    self.average = average
    self.allstar_points = allstar_points

def set_wow_api_key():
  os.environ['WOWAPI_APIKEY'] = '3tgfhwvjya9h9kpekjdyz45q3uhj2978'

def set_wclogs_api_key():
  os.environ['WCLOG_APIKEY'] = '4e6b85c57f6b99e30c1e296575957e12'

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

def get_current_time():
  return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def get_time(timestamp):
  return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
