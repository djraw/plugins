# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: wongdong  thanks to mkaay for Ev0-fetcher
"""

from module.plugins.internal.Addon import Addon
from module.lib import feedparser
from time import mktime, time

class DirectDownloadFetcher(Addon):
    __name__ = "DirectDownloadFetcher"
    __type__ = "hook"
    __version__ = "1.2"
    __status__  = "testing"
    __description__ = "Checks your personal Newsfeed on DirectDownload.tv for new episodes. "
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("rssnumber", "str", "Your personal RSS identifier (subscribe on directdownload.tv and enter the feednumber)", "0"),
                  ("interval", "int", "Check interval in minutes", "120"),    
                  ("queue", "bool", "Move new shows directly to Queue", "False"),
                  ("hoster", "str", "Hoster to use (comma seperated)", "FilesonicCom,UploadStationCom,FilejungleCom,DepositfilesCom,FileserveCom,FilefactoryCom")]
    __author_name__ = ("wongdong, djraw1")
    __author_mail__ = ("wongdong@gmx.net, raw1@gmx.de")
    
    def activate(self):
        self.periodical.start(self.config.get('interval') * 60)
    
    def filterLinks(self, links):
        results = self.pyload.pluginManager.parseUrls(links)
        sortedLinks = {}
        
        for url, hoster in results:
            if hoster not in sortedLinks:
                sortedLinks[hoster] = []
            sortedLinks[hoster].append(url)

        for h in self.config.get("hoster").split(","):
            try:
                if (len(sortedLinks[h.strip()]) > 0) : return sortedLinks[h.strip()]                   # returns the first hoster with links in it (a bit hardcore but whatever...)
            except:
                continue
        return []
    
    def periodical_task(self):
        self.interval = self.periodical.start(self.config.get('interval') * 60)                         # Re-set the interval if it has changed (need to restart pyload otherwise)
        feed = feedparser.parse("https://directdownload.tv/rss/"+self.config.get("rssnumber"))           # This is your personal feed Number from directdownload.tv
#        feed = feedparser.parse("http://dropatista.de/ddtv/ddtv-rss.php")     # PHP script to redirect HTTPS ddtv feed to HTTP
#        feed = feedparser.parse("http://192.168.0.211:800/ddtv/ddtv-rss.php")     # PHP script to redirect HTTPS ddtv feed to HTTP
#        self.log_info("DDFetcher: RSS feed - https://directdownload.tv/rss/"+self.config.get("rssnumber"))
        self.log_debug(str(feed['entries']))
        lastupdate = 0                  # The last timestamp of a downloaded file
        try:
            lastupdate = int(self.db.retrieve("lastupdate", 0))  # Try to load the last updated timestamp   
        except:
            pass
        
        
        maxtime =lastupdate 
        for item in feed['entries']:                                                                                # Thats a single Episode item in the feed
            currenttime = int(mktime(item['updated_parsed']))
            self.db.store("debug_currenttime",currenttime)
            if ( currenttime > lastupdate):                                                                         # Take only those not already parsed                                                                            
                links = str(item['summary'].replace("\n","").replace("<br /><br />","<br />")).split("<br />")      # Get all links (first element is the name)
                title = links.pop(0).strip()                                                                        # strip first item to leave links only
                self.log_info("DDFetcher: New Episode found: %s" % (title))
                title = str(item['title'].strip())                                                            # set releasename as package title 
                links = filter (lambda x:x.startswith("http") , links)                                           # remove all non-links (Empty lines, and whatnot)
                if (len(self.filterLinks(links)) > 0) :
                    self.pyload.api.addPackage(title.encode("utf-8"), self.filterLinks(links), 1 if self.config.get("queue") else 0) 
                    maxtime = max(maxtime, currenttime)                                                             # no links found. Try again next time.
                else:
                    self.log_info("DDFetcher: Couldn't parse any valid links from this episode. Check allowed hosters. Available links are: %s" % (links))

        if (maxtime == lastupdate):
            self.log_debug("DDFetcher: No new Episodes found")
        else:
            self.db.store("lastupdate",int(maxtime))
