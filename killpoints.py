import datetime

class KillPoints(object):

  chest_available = datetime.datetime(2016, 9, 21)
  breakpoints = [194, 578, 1225, 2181, 4800, 9600]

  def __init__(self, json):
    self.json = json

  def get_legendary_count(self, killpoints):
    for i in range(0, len(self.breakpoints)):
      if self.breakpoints[i] > killpoints:
        return i

  def get_points_till_next(self, killpoints):
    for i in range(0, len(self.breakpoints)):
      if self.breakpoints[i] > killpoints:
        return self.breakpoints[i] - killpoints

  def get_timed_points(self):
    killpoints = 0

    if 10671 in self.json['achievements']['achievementsCompleted']:
      index = self.json['achievements']['achievementsCompleted'].index(10671)
      timestamp = self.json['achievements']['achievementsCompletedTimestamp'][index] / 1000.0
      epoch = datetime.datetime.fromtimestamp(timestamp)
      days = (datetime.datetime.now()-epoch).days
      youngest = max(self.chest_available, epoch)
      weeks = ((datetime.datetime.now()-youngest).days)/7.0
      killpoints = days * 2.0
      killpoints += weeks * 11.0

    return round(killpoints)

  def get_mythic_plus_points(self):
    keystones = [
      33096, # Initiate
      33097, # Challenger
      33098, # Conqueror
      32028  # Master
    ]

    killpoints = 0;

    for keystone in keystones:
      if keystone in self.json['achievements']['criteria']:
        index = self.json['achievements']['criteria'].index(keystone)
        killpoints += self.json['achievements']['criteriaQuantity'][index] * 3.5

    return round(killpoints);

  def get_raid_points(self):
    raids = [
      8440,
      8025,
      8026
    ]

    killpoints = 0;

    for raid in self.json['progression']['raids']:
      if raid['id'] in raids:
        for boss in raid['bosses']:
          killpoints += boss['lfrKills'] * 2
          killpoints += boss['normalKills'] * 3
          killpoints += boss['heroicKills'] * 4
          killpoints += boss['mythicKills'] * 6

    return round(killpoints)

  def get_total_points(self):
    return self.get_timed_points() + self.get_mythic_plus_points() + self.get_raid_points()







