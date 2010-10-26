import re, datetime
from PMS import *

####################################################################################################

VIDEO_PREFIX = "/video/cbs"

NAME          = 'CBS'
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

CBS_LIST         = "http://www.cbs.com/video/"
HIDDEN_SERVER = "CBS%20Delivery%20Akamai%20Flash"
DEFAULT_SERVER = "CBS%20Production%20Delivery%20h264%20Akamai"
CLASSIC_SERVER   = "CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash"
NEWS_SERVER      = "CBS%20Production%20News%20Delivery%20Akamai%20Flash"
SHOWNAME_LIST    = "http://cbs.feeds.theplatform.com/ps/JSON/PortalService/1.6/getReleaseList?PID=GIIJWbEj_zj6weINzALPyoHte4KLYNmp&startIndex=1&endIndex=500&query=contentCustomBoolean|EpisodeFlag|%s&query=CustomBoolean|IsLowFLVRelease|false&query=CustomBoolean|IsHDRelease|false&query=contentCustomText|SeriesTitle|%s&query=servers|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&field=encodingProfile&contentCustomField=label"

### KEEP THIS IN CASE WE WANT TO CREATE AN "HD" DIRECTORY
HD_LIST = "http://cbs.feeds.theplatform.com/ps/JSON/PortalService/1.6/getReleaseList?PID=GIIJWbEj_zj6weINzALPyoHte4KLYNmp&startIndex=1&endIndex=499&query=CustomBoolean|IsHDRelease|true&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title"

CBS_SITEFEEDS    = "http://www.cbs.com/sitefeeds/"
CBS_SMIL         = "http://release.theplatform.com/content.select?format=SMIL&Tracking=true&balance=true&pid="

####################################################################################################
def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, 'CBS', ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)

####################################################################################################
def MainMenu():
	dir = MediaContainer(viewGroup="List")
	dir.Append(Function(DirectoryItem(ShowsPage, "Primetime"), pageUrl = CBS_LIST, showtime="id('navigation')/li[1]/ul/li/a", category="primetime/"))
	dir.Append(Function(DirectoryItem(ShowsPage, "Daytime"), pageUrl = CBS_LIST, showtime="id('navigation')/li[2]/ul/li/a", category="daytime/"))
	dir.Append(Function(DirectoryItem(ShowsPage, "Late Night"), pageUrl = CBS_LIST, showtime="id('navigation')/li[3]/ul/li/a", category=""))
	dir.Append(Function(DirectoryItem(ShowsPage, "TV Classics"), pageUrl = CBS_LIST, showtime="id('navigation')/li[6]/ul/li/a", category="classics/"))
###  "ORIGINALS | MOVIES | SPECIALS" DOESN'T SEEM TO HAVE MUCH USEFUL (EXCEPT VICTORIA'S SECRET) 
	#dir.Append(Function(DirectoryItem(ShowsPage, "Originals | Movies | Specials"), pageUrl = CBS_LIST, showtime="id('navigation')/li[5]/ul/li/a", category="specials/"))
    
### THE FOLOWING ARE FOUND "HIDDEN" IN THE FEEDS
### MIGHT NEED TO BUILD A "HIDDEN" DIRECTORY OR MOVE INTO "TV CLASSICS"
	dir.Append(Function(DirectoryItem(ClipsPage, "*The Three Stooges"), showname = "The%20Three%20Stooges%20Show", server = HIDDEN_SERVER))
	dir.Append(Function(DirectoryItem(VideosPage, "*Robotech"), clips="true", showname = "Robotech", server = HIDDEN_SERVER))

	return dir
    
####################################################################################################
def VideoPlayer(sender, pid):
    #pid="OiIhAefdP52uWTbaeI28O_EJUTrTVvk7"
    videosmil = HTTP.Request(CBS_SMIL + pid)
    player = videosmil.split("ref src")
    player = player[2].split('"')
    if ".mp4" in player[1]:
        player = player[1].replace(".mp4", "")
        clip = player.split(";")
        clip = "mp4:" + clip[4]
    else:
        player = player[1].replace(".flv", "")
        clip = player.split(";")
        clip = clip[4]
    #Log(player)
    #Log(clip)
    return Redirect(RTMPVideoItem(player, clip))
    
####################################################################################################
def VideosPage(sender, clips, showname, server):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    pageUrl = SHOWNAME_LIST % (clips, showname, server)
    feeds = JSON.ObjectFromURL(pageUrl)
    for item in feeds['items']:
        #encoding = item['encodingProfile']
        title = item['contentCustomData'][0]['value']
        pid = item['PID']
        summary =  item['description'].replace('In Full:', '')
        duration = item['length']
        thumb = item['thumbnailURL']
        airdate = int(item['airdate'])/1000
        subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
        dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid))
    return dir
    
def ClipsPage(sender, showname, server):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    dir.Append(Function(DirectoryItem(VideosPage, "Full Episodes"), clips="true", showname=showname, server=server))
    dir.Append(Function(DirectoryItem(VideosPage, "Clips"), clips="false", showname=showname, server=server))
    return dir
    
####################################################################################################
def ShowsPage(sender, pageUrl, showtime, category):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = XML.ElementFromURL(pageUrl, True)
    #server=DEFAULT_SERVER
    for item in content.xpath(showtime):
        showname = item.text
        if "The Original Series" in showname:
            showname = "Star Trek Remastered"  ### THESE ARE HD FEEDS - NEED TO FIND LOWER QUALITY
        elif "David Letterman" in showname:
            showname = "Late Show"
        elif "Craig Ferguson" in showname:
            showname = "The Late Late Show"
        if "48 Hours" in showname or "60 Minutes" in showname:
            server = NEWS_SERVER
        elif "Family Ties" in showname or "MacGyver" in showname or "The Love Boat" in showname or "Twin Peaks" in showname or "The Twilight Zone" in showname or "Beverly Hills" in showname or "Dynasty" in showname or "Melrose Place" in showname or "Perry Mason" in showname or "Jericho" in showname:  ### JERICHO NEEDS FURTHER WORK
            server = CLASSIC_SERVER
        else:
            server = DEFAULT_SERVER
        Log(server)
        if "Fantasy" in showname or "Ultimate" in showname or "Upload" in showname or "Premieres" in showname or "Cyber" in showname:
            continue  ### THESE ARE NOT ACTUAL SHOWS AND ARE EXCLUDED
        elif "SURVIVOR" in showname:
            showname = "survivor"  ### FORMATING FIX
        elif "Crime Scene Investigation" in showname:
            showname = "CSI:"
        elif "Bold and the Beautiful" in showname:
            showname = "Bold and the Beautiful"
        showname = showname.replace('Mystery', '').replace(' ', '%20').replace('&', '%26')  ### FORMATTING FIX
        Log(showname)
        title = item.text
        dir.Append(Function(DirectoryItem(ClipsPage, title), showname=showname, server=server))
    return dir



    
######  FOLLOWING CODE IS OBSOLETE!!!  ######    
"""    
        #link = CBS_SITEFEEDS + category + showname + "/episodes.js"
        #if "victoria" in showname:
        #	link ="http://cbs.com/" + showname + "/video/"
        #POOR QUALITY IMAGES (SOME BAD LINKS)
        #image = "http://www.cbs.com/" + showname + "/images/common/show_logo.gif"
        #Log(image)
        #Log(link)            #outputs:   primetime/amazing_race
        #if "victoria" in showname:
            #pid = "OmNUN_W97EMlf7_3h6RBc3_AzF4b_AG8"
            #title = "Victoria's Secret"
            #thumb = "http://thumbnails.cbsig.net/CBS_Production_Entertainment/261/795/CBS_2009_VICTORIA_SECRET_KYLIE_IMAGE_CIAN_140x80.jpg"
            #dir.Append(Function(VideoItem(VideoPlayer, title=title, thumb=thumb), pid=pid))
        #elif "_fantasy" not in link or "_ultimate_fan" not in link:
            #dir.Append(Function(DirectoryItem(VideoPage, title=title), pageUrl = link))
        #else:
            #continue
            
####################################################################################################
def VideoPage(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    webpage_content = HTTP.Request(pageUrl)
    m = re.compile('videoProperties(.+?)\r').findall(webpage_content)
    for webpage_content in m:
        item = webpage_content.split("','")
        title = "Season: " + item[4] + " Episode: " + item[6]
        #title = item[1]       #Proper title here, not used for all shows
        pid = item[10]
        thumb = item[12]
        summary = item[5].replace('\\','')
        summary = summary.replace('In Full:', '')
        duration = item[9]
        duration = [int(d) for d in duration.split(':')]
        if len(duration) == 3:
            duration = duration[0]*3600+duration[1]*60+duration[2]
        else:
            duration = duration[0]*60+duration[1]
        duration = duration * 1000
    	#videosmil = HTTP.Request(CBS_SMIL + pid)
    	#player = videosmil.split("ref src")
    	#player = player[2].split('"')
    	#player = player[1].replace(".flv", "").replace(".mp4", "")
    	#clip = player.split(";")
    	#clip = clip[4]
    	#Log(player)
    	#Log(clip)
        dir.Append(Function(VideoItem(VideoPlayer, title=title, thumb=thumb, summary=summary, duration=duration), pid=pid))
    	#dir.Append(RTMPVideoItem(player, clip, title=title, summary=summary, thumb=thumb, duration=duration))
    return dir
"""