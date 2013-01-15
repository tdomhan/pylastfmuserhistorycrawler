#author: Tobias Domhan

#TODO: if connection fails: retry!

import pickle
import codecs
import signal
import sys
from xml.dom.minidom import parse
import xml.sax
import urllib
from os.path import basename
import random
from time import sleep

class SongHistoryXMLHandler(xml.sax.ContentHandler):
  def __init__(self):
    xml.sax.ContentHandler.__init__(self)
    self.tracks = []
    self.inMbid = False
    self.inName = False
    self.inTrack = False
    self.inArtist = False
    self.ignoreTrack = False
    self.totalPages = 1

  def startElement(self, name, attrs):
    if name == 'track':
      self.inTrack = True
    
      self.mbid = ""
      
      self.artistmbid = ""
      
      self.artistname = ""
      
      self.name = ""
    
      if attrs.has_key('nowplaying'):
        self.ignoreTrack = True
      else:
        self.ignoreTrack = False

    elif name == 'artist':
      self.inArtist = True
      if attrs.has_key("mbid"):
        self.artistmbid = attrs.getValue("mbid")
    elif name == 'name':
        self.inName = True
    elif name == 'mbid':
      self.inMbid = True
    elif  name == 'date':
      self.date = attrs.getValue("uts")
    elif name == 'recenttracks':
      self.totalPages = int(attrs.getValue("totalPages"))

  def endElement(self, name):
    if name == 'track':
      self.inTrack = False
    
      if not self.ignoreTrack:
        self.tracks.append((self.name, self.mbid, self.date, self.artistname, self.artistmbid))
    
    elif name == 'artist':
      self.inArtist = False
    elif name == 'name':
      self.inName = False
    elif name == 'mbid':
      self.inMbid = False
    elif  name == 'date':
      pass

  def characters(self, content):
    if self.inMbid and self.inTrack and not self.inArtist:
      self.mbid = content
    if self.inName and self.inTrack:
      self.name = content
    if self.inTrack and self.inArtist:
      self.artistname = content


recent_tracks_xmlurl = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&api_key=e56ede647f0e1fc43601562aa4d18bd5&limit=200&'

MAX_RETRIES_URL_OPEN = 5

outname = "uid-timestamp-mbid-artistmbid-trackname-artistname%s.txt" % basename(sys.argv[1])
output = codecs.open(outname, "w", "utf-8")

def download_user_history(username):
  currpage = 0
  numPages = 1
  
  numNoMBID = 0
  numTracks = 0
  
  while currpage <= numPages:
    print 'fetching page: ', currpage, ' of ', numPages
    xmlpath = recent_tracks_xmlurl + 'page=' + str(currpage) + '&user=' + str(username)
    
    tries = 0
    success = False
    
    while tries < MAX_RETRIES_URL_OPEN and not success:
      try:
        if tries > 0:
          print "retrying after failed attempt"
        xmldata = urllib.urlopen(xmlpath)
        userhistory = SongHistoryXMLHandler()
        xml.sax.parse(xmldata, userhistory)
        xmldata.close()
      
        numPages = userhistory.totalPages
  
        success = True
  
      except Exception, e:
        tries += 1
        print "exception while fetching user history", e
  
      if success:
        for (name, mbid, date, artistname, artistmbid) in userhistory.tracks:
          output.write(username)
          output.write('\t')
          output.write(date)
          output.write('\t')
          output.write(mbid)
          output.write('\t')
          output.write(artistmbid)
          output.write('\t')
          output.write(name)
          output.write('\t')
          output.write(artistname)
          output.write('\n')
  
    currpage = currpage + 1


def main(userfile):
  num_users_visited = 0
  userfile = open(userfile, 'r')
  userlines = userfile.readlines()
  random.shuffle(userlines)
  for line in userlines:
    (user,age,gender,country) = line.split(',')
    
    download_user_history(user)
    num_users_visited = num_users_visited + 1
          
    print "num users %d visited." % num_users_visited

def save_data():
  output.close()

if __name__ == "__main__":
  try:
    main(sys.argv[1])
    save_data()
  #except KeyboardInterrupt:
  except Exception, e:
    print e
    print "Exception caught, saving data and quitting..."
    save_data()
