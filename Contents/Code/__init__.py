import re, datetime

####################################################################################################

VIDEO_PREFIX = "/video/cbs"

NAME          = 'CBS'
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

CBS_LIST         = "http://www.cbs.com/video/"
VICTORIA_SERVER  = "CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash%20Progressive"
HIDDEN_SERVER    = "CBS%20Delivery%20Akamai%20Flash"
DEFAULT_SERVER   = "CBS%20Production%20Delivery%20h264%20Akamai"
CLASSIC_SERVER   = "CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash"
NEWS_SERVER      = "CBS%20Production%20News%20Delivery%20Akamai%20Flash"
SHOWNAME_LIST    = "http://cbs.feeds.theplatform.com/ps/JSON/PortalService/1.6/getReleaseList?PID=GIIJWbEj_zj6weINzALPyoHte4KLYNmp&startIndex=1&endIndex=500%s&query=contentCustomBoolean|EpisodeFlag|%s&query=CustomBoolean|IsLowFLVRelease|false&query=contentCustomText|SeriesTitle|%s&query=servers|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&field=encodingProfile&contentCustomField=label"

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
	dir.Append(Function(DirectoryItem(ShowsPage, "Originals | Movies | Specials"), pageUrl = CBS_LIST, showtime="id('navigation')/li[5]/ul/li/a", category="specials/"))
	dir.Append(PrefsItem(L("Preferences..."), thumb=R('icon-prefs.png')))
	return dir
    
####################################################################################################
def VideoPlayer(sender, pid):
    #pid="OiIhAefdP52uWTbaeI28O_EJUTrTVvk7"
    videosmil = HTTP.Request(CBS_SMIL + pid).content
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
    if(Prefs['hd']):
    	hd = ''
    else:
    	hd = '&query=CustomBoolean|IsHDRelease|false'
    pageUrl = SHOWNAME_LIST % (hd, clips, showname, server)
    feeds = JSON.ObjectFromURL(pageUrl)
    encoding = ''
    for item in feeds['items']:
    	if hd == '':
    		if "HD" in item['encodingProfile']:
    			encoding = " - HD " + item['encodingProfile'][3:8].replace(' ', '')
        	else:
        		encoding = ""
        title = item['contentCustomData'][0]['value'] + str(encoding)
        Log(title)
        pid = item['PID']
        summary = item['description'].replace('In Full:', '')
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
    content = HTML.ElementFromURL(pageUrl)
    #server=DEFAULT_SERVER
    if category == "specials/":
    	dir.Append(Function(DirectoryItem(ClipsPage, "Victoria's Secret"), showname = "Victorias%20Secret", server = DEFAULT_SERVER))
    else:
    	for item in content.xpath(showtime):
    		showname = item.text
        	title = item.text
    		if "The Original Series" in showname:
    			showname = "Star Trek Remastered"  ### THESE ARE HD FEEDS - NEED TO FIND LOWER QUALITY
    			title += " (HD only)"
        	elif "David Letterman" in showname:
        		showname = "Late Show"
        	elif "Craig Ferguson" in showname:
        		showname = "The Late Late Show"
        	if "48 Hours" in showname or "60 Minutes" in showname or "Early Show" in showname:
        		server = NEWS_SERVER
        	elif "Family Ties" in showname or "MacGyver" in showname or "The Love Boat" in showname or "Twin Peaks" in showname or "The Twilight Zone" in showname or "Beverly Hills" in showname or "Dynasty" in showname or "Melrose Place" in showname or "Perry Mason" in showname or "Jericho" in showname:  ### JERICHO NEEDS FURTHER WORK
        		server = CLASSIC_SERVER
        	else:
        		server = DEFAULT_SERVER
        	#Log(server)
        	if "Live on Letterman" in showname or "Homepage" in showname or "Fantasy" in showname or "Ultimate" in showname or "Upload" in showname or "Premieres" in showname or "Cyber" in showname or "WWW" in showname or "Undercover Ops" in showname or "Employee" in showname:
        		continue  ### THESE ARE NOT ACTUAL SHOWS AND ARE EXCLUDED
        	elif "SURVIVOR" in showname:
        		showname = "survivor"  ### FORMATING FIX
        	elif "Crime Scene Investigation" in showname:
        		showname = "CSI:"
        	elif "Bold and the Beautiful" in showname:
        		showname = "Bold and the Beautiful"
        	elif "Young and the Restless" in showname:
        		showname = "Young and the Restless"
        	showname = showname.replace('Mystery', '').replace(' ', '%20').replace('&', '%26')  ### FORMATTING FIX
        	#Log(showname)
        	dir.Append(Function(DirectoryItem(ClipsPage, title), showname=showname, server=server))
        if category == "classics/":  ### THESE ARE HIDDEN FEEDS (MIGHT NEED TO CREATE A SEPARATE CATEGORY SOON)
        	dir.Append(Function(DirectoryItem(ClipsPage, "*The Three Stooges"), showname = "The%20Three%20Stooges%20Show", server = HIDDEN_SERVER))
        	dir.Append(Function(DirectoryItem(VideosPage, "*Robotech"), clips="true", showname = "Robotech", server = HIDDEN_SERVER))
    		dir.Append(Function(DirectoryItem(VideosPage, "*Victoria's Secret"), clips="false", showname = "Victorias%20Secret", server = VICTORIA_SERVER))
    return dir