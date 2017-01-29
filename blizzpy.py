import os
from requests.exceptions import RequestException
from wowapi import WowApi
from params import set_api_key
import json

set_api_key()

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
      return "{0}/{1} {2}".format(total, bosses, difficulty[i])
  return "{0}/{1} {2}".format(0, bosses, "N")

def populate_raids(json, raid, bosses, start_index):
  for i in range(3):
    for j in range(bosses):
      raid.append(get_kill_quantity(json, start_index-i+(4*j)))


payload = WowApi.get_guild_profile('us', 'boulderfist', 'Dragon Knight', locale="en_US", fields="achievements")

print(payload)

# EN = []
# TOV = []
# NH = []
# for x in payload['statistics']['subCategories']:
#   if x['name'] == "Dungeons & Raids":
#     for y in x['subCategories']:
#       if y['name'] == "Legion":
#         populate_raids(y, EN, 7, 33)
#         populate_raids(y, TOV, 3, 61)
#         populate_raids(y, NH, 10, 73)
#         # EN.extend([get_kill_quantity(y, 33), get_kill_quantity(y, 37), get_kill_quantity(y, 41), get_kill_quantity(y, 45), get_kill_quantity(y, 49), get_kill_quantity(y, 53), get_kill_quantity(y, 57)])
#         # EN.extend([get_kill_quantity(y, 32), get_kill_quantity(y, 36), get_kill_quantity(y, 40), get_kill_quantity(y, 44), get_kill_quantity(y, 48), get_kill_quantity(y, 52), get_kill_quantity(y, 56)])
#         # EN.extend([get_kill_quantity(y, 31), get_kill_quantity(y, 35), get_kill_quantity(y, 39), get_kill_quantity(y, 43), get_kill_quantity(y, 47), get_kill_quantity(y, 51), get_kill_quantity(y, 55)])
#         # TOV.extend([get_kill_quantity(y, 61), get_kill_quantity(y, 65), get_kill_quantity(y, 69)])
#         # TOV.extend([get_kill_quantity(y, 60), get_kill_quantity(y, 64), get_kill_quantity(y, 68)])
#         # TOV.extend([get_kill_quantity(y, 59), get_kill_quantity(y, 63), get_kill_quantity(y, 67)])
#         # NH.extend([get_kill_quantity(y, 73), get_kill_quantity(y, 77), get_kill_quantity(y, 81), get_kill_quantity(y, 85), get_kill_quantity(y, 89), get_kill_quantity(y, 93), get_kill_quantity(y, 97), get_kill_quantity(y, 101), get_kill_quantity(y, 105), get_kill_quantity(y, 109)])
#         # NH.extend([get_kill_quantity(y, 72), get_kill_quantity(y, 76), get_kill_quantity(y, 80), get_kill_quantity(y, 84), get_kill_quantity(y, 88), get_kill_quantity(y, 92), get_kill_quantity(y, 96), get_kill_quantity(y, 100), get_kill_quantity(y, 104), get_kill_quantity(y, 108)])
#         # NH.extend([get_kill_quantity(y, 71), get_kill_quantity(y, 75), get_kill_quantity(y, 79), get_kill_quantity(y, 83), get_kill_quantity(y, 87), get_kill_quantity(y, 91), get_kill_quantity(y, 95), get_kill_quantity(y, 99), get_kill_quantity(y, 103), get_kill_quantity(y, 107)])



# print(get_difficulty(EN, 7))
# print(get_difficulty(TOV, 3))
# print(get_difficulty(NH, 10))


# total = get_difficulty(mEN)
# if (total == 0):
#   total = get_difficulty(hEN)
#   if (total == 0):
#     get_difficulty(nEN)
#     if (total)
#   else:
#     progressEN = progressEN.format(total, "H")
# else
#   progressEN = progressEN.format(total, "M")
