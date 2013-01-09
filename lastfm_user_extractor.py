#author: Tobias Domhan

#TODO: if connection fails: retry!
#TODO: limit maximum number of non-visited users
#TODO: filter out currently playing tracks
#TODO: create unique ID for each track that doesn't have a mbid?

import pickle
import signal
import sys
from xml.dom.minidom import parse
import xml.sax
import urllib
from time import sleep
import random
import codecs

#taken from http://www.last.fm/community/users/active
seed_users = ['RJ','V-34', 'Hello_Suckers', 'Anarchnophobia', 'Shaynstein', 'MaryWentz', 'MrMetroid', 'TamuraKafka', 'sweettvirginia', 'jobarruiz', 'MargaritaHell', 'LonelyEstate', 'stripedcat', 'Hammerfall314', 'spoil3r', 'joaotsantos', 'Liberation-FM', 'nightclusing', 'DaysoftheGun', 'forestasunder', 'Foresthrone', 'NorgeAllStar', 'HenkeRock', 'MerryMaenad', 'Harry_01', 'Steban14', 'Cysquatch193', 'Vallychen', 'Lisa_Westfall', 'richardestrada7', 'vividserenity']
#'maguilarrami','tdomhan',

total_users = 100000

users_to_sample = set()
users = set()

user_details = {}

class LastFMFriendsXMLHandler(xml.sax.ContentHandler):
  def __init__(self):
    xml.sax.ContentHandler.__init__(self)
    self.names = []
    self.inName = False
    self.inGender = False
    self.inCountry = False
    self.inAge = False
  
  def startElement(self, name, attrs):
    if name == 'user':
      self.name = ''
      self.age = ''
      self.gender = ''
      self.country = ''
    elif name == 'name':
      self.inName = True
    elif name == 'age':
      self.inAge = True
    elif name == 'gender':
      self.inGender = True
    elif name == 'country':
      self.inCountry = True
    elif name == 'friends':
      self.totalPages = int(attrs.getValue("totalPages"))
  
  def endElement(self, name):
    if name == 'name':
      self.inName = False
    elif name == 'age':
      self.inAge = False
    elif name == 'gender':
      self.inGender = False
    elif name == 'country':
      self.inCountry = False
    elif name == 'user':
      self.names.append((self.name, self.age, self.gender, self.country))

  def characters(self, content):
    if self.inName:
      self.name = content
    elif self.inAge:
      self.age = content
    elif self.inGender:
      self.gender = content
    elif self.inCountry:
      self.country = content

user_friends_xmlurl = 'http://ws.audioscrobbler.com/2.0/?method=user.getfriends&api_key=e56ede647f0e1fc43601562aa4d18bd5&limit=200&user='

def get_user_friends(username):
  xmlpath = user_friends_xmlurl + '&user=' + str(username)
  try:
    xmldata = urllib.urlopen(xmlpath)
    userfriends = LastFMFriendsXMLHandler()
    xml.sax.parse(xmldata, userfriends)
    xmldata.close()
    return userfriends.names
  except KeyboardInterrupt, e:
    raise e
  except:
    print "exception in get_user_friends"
    return set()


def main():
  while len(users)<total_users:
    for userindex, user in enumerate(seed_users):
      print "fetching user %s" % user
      #users.add(user) #we don't have details like country, age gender about them, so let's not add them
      friends = get_user_friends(user)
      friends = set(friends) - users_to_sample
      
      for (friend, age, gender, country) in friends:
        user_details[friend] = (age, gender, country)
        users_to_sample.add(friend)
          
      friends = [friend for (friend, age, gender, country) in friends]
    
      if len(friends) == 0:
        print "no unseen friends filling slot with random backup"
        friends = list(users_to_sample)
      else:
        friends = list(friends)
      friend  = random.choice(friends)
  
      users.add(friend)
      seed_users[userindex] = friend
          
      print "num users %d. (%d as backup.)" % (len(users), len(users_to_sample))
      if len(users) % 100 == 0:
        save_data()

def save_data():
  outputs = [codecs.open(x, 'w', 'utf-8') for x in ['users1.txt', 'users2.txt', 'users3.txt']]
  outputall = codecs.open('users.txt', 'w', 'utf-8')

  index = 0
  outputs[index%len(outputs)].write('tdomhan,,,')
  outputs[index%len(outputs)].write('\n')
  outputs[index%len(outputs)].write('RJ,,,')
  outputs[index%len(outputs)].write('\n')
  outputs[index%len(outputs)].write('maguilarrami,,,')
  outputs[index%len(outputs)].write('\n')

  skiplist = ['tdomhan', 'RJ', 'maguilarrami']
  
  for user in users:
    if user in skiplist:
      continue
    (age, gender, country) = user_details[user]
    userstring = "%s,%s,%s,%s" % (user, age, gender, country)
    outputs[index%len(outputs)].write(userstring)
    outputs[index%len(outputs)].write('\n')
    index = index + 1

  for user in users_to_sample:
    if user in skiplist:
      continue
    (age, gender, country) = user_details[user]
    userstring = "%s,%s,%s,%s" % (user, age, gender, country)
    outputall.write(userstring)
    outputall.write('\n')

if __name__ == "__main__":
  main()
  try:
    main()
    save_data()
  #except KeyboardInterrupt:
  except:
    print "Exception caught, saving data and quitting..."
    save_data()
