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

seed_users = ['RJ','maguilarrami','tdomhan']

max_num_users_to_visit = 20000

#list of already visited users
try:
  users_notvisited = pickle.load( open( "users_notvisited.p", "rb" ) )
  users_visited = pickle.load( open( "users_visited.p", "rb" ) )
except IOError:
  users_notvisited = set(seed_users)
  users_visited = set()
  pickle.dump(users_notvisited, open("users_notvisited.p", "wb" ))
  pickle.dump(users_visited, open("users_visited.p", "wb" ))


class SongHistoryXMLHandler(xml.sax.ContentHandler):
  def __init__(self):
    xml.sax.ContentHandler.__init__(self)
    self.tracks = []
    self.inMbid = False
    self.inName = False
    self.inTrack = False
    self.inArtist = False
    self.ignoreTrack = False

  def startElement(self, name, attrs):
    if name == 'track':
      self.inTrack = True
    
      self.mbid = ""
    
      if attrs.has_key('nowplaying'):
        self.ignoreTrack = True
      else:
        self.ignoreTrack = False

    elif name == 'artist':
      self.inArtist = True
    elif name == 'mbid':
      self.inMbid = True
    elif  name == 'date':
      self.date = attrs.getValue("uts")
    elif name == 'recenttracks':
      self.totalPages = int(attrs.getValue("totalPages"))

  def endElement(self, name):
    if name == 'track':
      self.inTrack = False
    
      if not self.ignoreTrack and self.mbid != "":
        self.tracks.append((self.mbid, self.date))
    
    elif name == 'artist':
      self.inArtist = False
    elif name == 'mbid':
      self.inMbid = False
    elif  name == 'date':
      pass

  def characters(self, content):
    if self.inMbid and self.inTrack and not self.inArtist:
      self.mbid = content


class LastFMFriendsXMLHandler(xml.sax.ContentHandler):
  def __init__(self):
    xml.sax.ContentHandler.__init__(self)
    self.names = []
    self.inName = False
  
  def startElement(self, name, attrs):
    if name == 'name':
      self.inName = True
    elif name == 'friends':
      self.totalPages = int(attrs.getValue("totalPages"))
  
  def endElement(self, name):
    if name == 'name':
      self.inName = False
  
  def characters(self, content):
    if self.inName:
      self.names.append(content)


recent_tracks_xmlurl = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&api_key=e56ede647f0e1fc43601562aa4d18bd5&limit=200&'

user_friends_xmlurl = 'http://ws.audioscrobbler.com/2.0/?method=user.getfriends&api_key=e56ede647f0e1fc43601562aa4d18bd5&limit=200&user='

MAX_RETRIES_URL_OPEN = 5

output = open("uid-timestamp-mbid.txt", "aw") 

def download_user_history(username):
  currpage = 0
  numPages = 1
  
  numNoMBID = 0
  numTracks = 0
  
  while currpage <= numPages:
    print 'fetching page: ', currpage, ' of ', numPages
    xmlpath = recent_tracks_xmlurl + 'page=' + str(currpage) + '&user=' + str(username)
    try:
      xmldata = urllib.urlopen(xmlpath)
      userhistory = SongHistoryXMLHandler()
      xml.sax.parse(xmldata, userhistory)
      xmldata.close()
      
      for (mbid, date) in userhistory.tracks:
        output.write(username)
        output.write('\t')
        output.write(date)
        output.write('\t')
        output.write(mbid)
        output.write('\n')
      
      numPages = userhistory.totalPages
  
    except Exception as e:
      print(e)
  
    currpage = currpage + 1


def get_user_friends(username):
  xmlpath = user_friends_xmlurl + '&user=' + str(username)
  try:
    xmldata = urllib.urlopen(xmlpath)
    userfriends = LastFMFriendsXMLHandler()
    xml.sax.parse(xmldata, userfriends)
    xmldata.close()
    print userfriends.names
    return userfriends.names
  except Exception as e:
    print(e)
    return set() 

def main():
  while len(users_notvisited)>0:
    user = users_notvisited.pop()
    users_visited.add(user)
    download_user_history(user)
    friends = get_user_friends(user)
    for user in friends:
      if not user in users_visited:
        users_notvisited.add(user)
  
    while(len(users_notvisited)>max_num_users_to_visit):
      users_notvisited.pop()
          
    print "num users %d visited. (%d to go.)" % (len(users_visited), len(users_notvisited))

def save_data():
  pickle.dump(users_notvisited, open("users_notvisited.p", "wb" ))
  pickle.dump(users_visited, open("users_visited.p", "wb" )) 
  output.close()

if __name__ == "__main__":
  try:
    main()
    save_data()
  #except KeyboardInterrupt:
  except:
    print "Exception caught, saving data and quitting..."
    save_data()
