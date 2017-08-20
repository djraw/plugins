# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook
from module.lib import feedparser
from time import mktime, time


class DirectDownloadFetcher(Hook):
    __name__ = "DirectDownloadFetcher"
    __version__ = "1.1"
    __description__ = "Checks your personal Newsfeed on DirectDownload.tv for new episodes. "
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("rssnumber", "str", "Your personal RSS identifier (subscribe on directdownload.tv and enter the feednumber)", "0"),
                  ("interval", "int", "Check interval in minutes", "120"),    
                  ("queue", "bool", "Move new shows directly to Queue", "True"),
                  ("hoster", "str", "Hoster to use (comma seperated)", "FilefactoryCom,Keep2ShareCc")]
    __author_name__ = ("wongdong")
    __author_mail__ = ("wongdong@gmx.net")

    def setup(self):
        self.interval = self.getConfig("interval") * 60
      
    def filterLinks(self, links):
        results = self.core.pluginManager.parseUrls(links)
        sortedLinks = {}
        
        for url, hoster in results:
            if hoster not in sortedLinks:
                sortedLinks[hoster] = []
            sortedLinks[hoster].append(url)

        for h in self.getConfig("hoster").split(","):
            try:
                if (len(sortedLinks[h.strip()]) > 0) : return sortedLinks[h.strip()]                   # returns the first hoster with links in it (a bit hardcore but whatever...)
            except:
                continue
        return []
    
    def periodical(self):
        self.interval = self.getConfig("interval") * 60                                                # Re-set the interval if it has changed (need to restart pyload otherwise)
        feed = feedparser.parse("http://directdownload.tv/rss/"+self.getConfig("rssnumber"))           # This is your personal feed Number from directdownload.tv
        
        lastupdate = 0                  # The last timestamp of a downloaded file
        try:
            lastupdate = int(self.getStorage("lastupdate", 0))  # Try to load the last updated timestamp   
        except:
            pass
        
        
        maxtime =lastupdate 
        for item in feed['entries']:                                                                                # Thats a single Episode item in the feed
            currenttime = int(mktime(item['updated_parsed']))
            if ( currenttime > lastupdate):                                                                         # Take only those not already parsed                                                                            
                self.setStorage("debug_currenttime",currenttime)
                links = str(item['summary'].replace("\n","").replace("<br /><br />","<br />")).split("<br />")      # Get all links (first element is the name)
                title = links.pop(0).strip()                                                                        # strip first item to leave links only
                title = str(item['releasename'])                                                                    # set releasename as package title 
                links = filter (lambda x:x.startswith("http") , links)                                           # remove all non-links (Empty lines, and whatnot)
                self.core.log.info("DDFetcher: New Episode found: %s" % (title))
                if (len(self.filterLinks(links)) > 0) :
                    self.core.api.addPackage(title.encode("utf-8"), self.filterLinks(links), 1 if self.getConfig("queue") else 0) 
                    maxtime = max(maxtime, currenttime)                                                             # no links found. Try again next time.
                else:
                    self.core.log.info("DDFetcher: Couldn't parse any valid links from this episode. Check allowed hosters. Available links are: %s" % (links))

        if (maxtime == lastupdate):
            self.core.log.debug("DDFetcher: No new Episodes found")
        else:
            self.setStorage("lastupdate",int(maxtime))
