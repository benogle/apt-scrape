from BeautifulSoup import BeautifulSoup
from BeautifulSoup import Tag

import os
import urllib2
import re
import sys
import datetime
import time
from geopy import geocoders

import MySQLdb

import dateutil

from htmlentitydefs import name2codepoint

devnull = file(os.path.devnull, "w")

verbose = False

def sprint(s):
    print s

def _log(txt):
    if verbose:
        sprint(txt)

#http://localhost:
GMAPS_KEY = 'ABQIAAAAb1JavWJt8ugdUFbKNsotthT2yXp_ZAY8_ufC3CFXhHIE1NvwkxQjiaK47a90Qyf1lzmK80hJSFrdyA'


###
###
###

class Region:
    
    def __init__(self, dbdata):
        self.id, self.name = dbdata

class Area:
    
    def __init__(self, dbdata):
        self.id, self.region_id, self.name = dbdata
        
    def __repr__(self):
        return 'Area name: %s; id: %s; region_id: %s;' % (self.name, self.id, self.region_id)

class Metric:
    def __init__(self, dbdata):
        self.id, self.key, self.value = dbdata

class DB:
    
    DATABASE = 'apts'
    USER = 'lowpriv'
    PASSWORD = 'p@ssw0rd'
    HOST = 'localhost'
    
    def __init__(self):
        self.db = MySQLdb.connect(db=self.DATABASE, host=self.HOST, user=self.USER, passwd=self.PASSWORD, charset='UTF8')
        
    def _cur(self):
        return self.db.cursor()
        
    def commit(self):
        self.db.commit()
    
    def hasApartment(self, cl_id):
        c = self._cur()
        c.execute('SELECT * FROM apartments WHERE cl_id=%s', (cl_id,))
        return c.fetchone() != None
    
    def getArea(self, areaStr, regionStr='sfbay'):
        c = self._cur()
        c.execute('SELECT a.* FROM region r JOIN area a ON a.region_id=r.id WHERE a.name=%s AND r.name=%s', (areaStr,regionStr))
        
        area = c.fetchone()
        if not area: #insert the new area
            
            c.execute('SELECT * FROM region r WHERE r.name=%s', (regionStr,))
            region = c.fetchone()
            if region:
                region = Region(region)
                
                c.execute('INSERT INTO area (id, region_id, name) VALUES (%s, %s, %s)', (None, region.id, areaStr))
                self.commit()
                return self.getArea(areaStr, regionStr=regionStr)
                
        else:
            return Area(area)
            
        return None
    
    def insertApartment(self, args):
        
        keys = []
        values = []
        for k, v in args.items():
            keys.append(k)
            values.append(v)
            
        value_holders = ['%s'] * len(keys)
        sql = 'INSERT INTO apartments (%s) VALUES (%s)' % (','.join(keys), ','.join(value_holders))
        
        c = self._cur()
        c.execute(sql, values)
    
    def getMetric(self, key):
        c = self._cur()
        c.execute('SELECT * FROM metrics m WHERE m.key=%s', (key,))
        kv = c.fetchone()
        if kv:
            return Metric(kv)
        return None
    
    def incrementMetric(self, key):
        c = self._cur()
        metric = self.getMetric(key)
        if metric:
            c.execute('UPDATE metrics m SET m.value=m.value+1 WHERE m.key=%s', (key,))
            self.commit()
        else:
            c.execute('INSERT INTO metrics (id, `key`, `value`) VALUES (%s, %s, %s)', (None, key, 1))
            self.commit()
            metric = self.getMetric(key)
        
        _log("Incrementing metric '%s': %d" % (key, metric.value))
        return metric


class ScrapeException(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return repr(self.message)


class SiteScraper:
    
    ENTITY_RE = re.compile(r'&(?:(#)(\d+));')
    
    def __init__(self):
        pass
    
    def search_url(self, url):
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup(html)
        return soup
    
    #replaces &#34; html garbage with the actual char
    def stripSpecialHTML(self, text):
        
        def _repl_func(match):
            if match.group(1): # Numeric character reference
                return unichr(int(match.group(2)))
            else:
                return unichr(name2codepoint[match.group(3)])
                
        text = text.replace("&amp;", "&") # Must be done first!
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&rdquo;", '"')
        text = text.replace("&ldquo;", '"')
        text = text.replace("&rsquo;", '\'')
        text = text.replace("&lsquo;", '\'')
        text = text.replace("&ndash;", '-')
        text = text.replace("&mdash;", '-')
        
        return self.ENTITY_RE.sub(_repl_func, text) 
        
    #strips all html tags out of a BeautifulSoup tag
    def stripHTML(self, tag):
        if tag == None or not isinstance(tag, Tag): return ''
        
        txt = ''
        for c in tag.contents:
            if isinstance(c, Tag):
                txt += ' ' + stripHTML(c)
            else:
                txt += ' ' + c.string
    
        return stripSpecialHTML(txt)

class PostData:
    def __init__(self, clid, soup, email, url, title, area, postedDate, body):
        self.clid = clid
        self.url = url
        self.title = title
        self.postedDate = postedDate
        self.body = body
        self.email = email
        self.soup = soup
        self.area = area
        
class CraigslistPost:
    
    def __init__(self, db, postData):
        self.clid = postData.clid
        self.url = postData.url
        self.title = postData.title
        self.postedDate = postData.postedDate
        self.body = postData.body
        self.email = postData.email
        self.soup = postData.soup
        self.area = postData.area
        self.db = db
        
    def saveToDB(self):
        pass
    
    def parse(self):
        print self.title
        
        return False

class CraigslistScraper(SiteScraper):
    
    LINK_RE = re.compile(r'(/([0-9]+)\.html)')
    WHITE_RE = re.compile(r'[ \n\r\t]+')
    TIME_RE = re.compile(r'([0-9]+[-][0-9]+[-][0-9]+,[ ]+[0-9]+[:][0-9]+(am|pm))[ ]+(pst|pdt|mst|mdt|cst|cdt|est|edt|akst|akdt|hst|hdt)')
    PHONE_RE = re.compile(r'[(]?([0-9]{3})[)]?[ ]*(-|\.)?[ ]*([0-9]{3})[ ]*(-|\.)[ ]*([0-9]{4})')
    NEXT_PAGE_RE = re.compile(r'^(index[0-9]{3}\.html)$')
    
    #sub is the suburl. i.e. 'spokane' or 'sfbay'
    def __init__(self, sub, dom='org', baseUrl='/sfc/apa', checkDB=True):
        self.dom = dom
        self.baseUrl = baseUrl
        self.checkDB = checkDB
        self.url = 'http://' + sub + '.craigslist.'+ dom
        
        self.lastRefDate = None
        self.sub = sub
        self.db = DB()
    
    def _joinUrl(self, href):
        if href and href.startswith('/'):
            href = self.url + href
        elif href:
            href = self.url + self.baseUrl + '/' + href
        else:
            href = self.url + self.baseUrl
        return href
    
    def _isInDB(self, craigslistId):
        return False
    
    def _createPostObj(self, postData):
        return CraigslistPost(pid, self.db, postData)
        
    def _extractDateTime(self, datestr):
        try:
            date = datestr.lower()
            m = self.TIME_RE.search(date)
            
            tz = dateutil.USTimeZone(str(m.group(3)))
            refdate = dateutil.strToTime(str(m.group(1)), '%Y-%m-%d, %I:%M%p', timezoneinfo=tz)
            
            return dateutil.toUtc(refdate, tz.utcoffset(refdate))
            
        except:
            return datetime.datetime.utcnow();
    
    def _scrapeUrl(self, href, link):
        
        title = link.contents[0].string.strip()
        if not link.nextSibling:
            _log('fail: No area near the link found!')
            return None
        
        area = link.nextSibling.contents[0].string.strip()
        
        pid = self.LINK_RE.search(href).group(2)
            
        if self.checkDB and self._isInDB(pid):
            _log('already in db')
                
            raise ScrapeException('%s already in the db' % pid)
        
        soup = self.search_url(href)
        
        elem = soup.body
        
        date = None
        post = ''
        email = None
        
        while elem != None:
            if not isinstance(elem, Tag):
                txt = elem.string.strip()
                
                if txt.startswith('Date:'):
                    date = txt.replace('Date:', '').strip()
                    date = self._extractDateTime(date)
            
            elif elem.has_key('href') and elem['href'].startswith('mailto:'):
                email = elem.string
            elif elem.has_key('id') and elem['id'] == 'userbody':
                post = u'\n'.join([self.WHITE_RE.sub(u' ', unicode(e)) for e in elem.contents])
                
            elem = elem.next
        
        #print title
        #print loc
        #print post
        
        post = self.stripSpecialHTML(post)
        title = self.stripSpecialHTML(title)
        
        clpost = self._createPostObj(PostData( pid, soup, email, href, title, area, date, post))
        if clpost.parse():
            return clpost
        
        return None
    
    def _scrapeSingle(self, link):
        href = link['href']
        
        href = self._joinUrl(href)
        
        _log('************')
        _log('scraping: %s' % href)
        
        return self._scrapeUrl(href, link)

    def scrapePage(self, page, refPage=None):
        href = self._joinUrl(refPage)
        
        pageRe = re.compile('(%s)' % page)
        
        soup = self.search_url(href)
        links = soup.findAll('a', {'href': pageRe})
        
        for link in links:
            ppost = self._scrapeSingle(link)
    
    def scrape(self, page=None, depth=0, maxDepth=4):
        
        if depth == maxDepth:
            return []
        
        if page:
            _log('#################### NEW PAGE! #######################')
            href = self._joinUrl(page)
            _log('%s\n\n' % href)
        else:
            href = self.url + self.baseUrl
        
        soup = self.search_url(href)
        links = soup.findAll('a', {'href':self.LINK_RE})
        
        nextLink = soup.findAll('a', {'href':self.NEXT_PAGE_RE})
    
        ads = []
        
        #sometimes a few of them will get pushed to the next page, and itll kill the
        #parser, so we'll check up to some number of results in the db.
        pad = 0
        maxPad = 20
        
        try:
            
            for link in links:
                
                try:
                    ppost = self._scrapeSingle(link)
                    
                    self.db.incrementMetric('total_unique')
                    
                    if ppost != None:
                        self.db.incrementMetric('parsed')
                        ads.append(ppost)
                
                except ScrapeException, e:
                    pad += 1
                    _log('Apt in DB check %d of %d' % (pad, maxPad))
                    if pad >= maxPad:
                        raise e
                except KeyboardInterrupt:
                    _log('\n\nKeyboard Exception! Exiting...')
                    sys.exit(0)
                except Exception, e:
                    self.db.incrementMetric('exceptions')
                    sprint('Exception! Fail! %s\n\n%s' % (link['href'], e))
            
            ads = ads + self.scrape(page=nextLink[0]['href'], depth=depth+1)
        
        except ScrapeException, e:
            sprint('Exiting: %s' % e)
        
        self.db.commit()
        
        return ads
    
class CraigslistApartmentPost(CraigslistPost):
    
    PRICE_RE = re.compile(r'^\$([0-9]+)')
    BR_RE = re.compile(r'(([0-9]+)[ ]*(br|bd|bed|bedroom))|(studio|efficiency)|(jr(\.)?[ ]?1?[ ]?(br|bed|bd|bedroom))')
    
    OPEN_HOUSE_RE = re.compile(r'open[ ]+(house|mon|monday|tues|tue|tuesday|wed|wednesday|thu|thurs|thursday|fri|friday|today|tomorrow)')
    
    ENTITY_RE = re.compile(r'(%)([0-9a-fA-F]{2})')
    
    def __init__(self, db, postData):
        CraigslistPost.__init__(self, db, postData)
        
    def saveToDB(self):
        
        area = self.db.getArea(self.area)
        data = {
            'id': None,
            'cl_id': self.clid,
            'area_id': area.id,
            'posted_date': self.postedDate,
            'email': self.email,
            'phone': self.phone,
            'price': self.price,
            'bedrooms': self.bedrooms,
            #'bathrooms': None,
            'title': self.title,
            'body': self.body,
            'is_open_house': self.openhouse,
            'location': self.location,
            'latitude': self.latlon[0],
            'longitude': self.latlon[1],
            'url': self.url
        }
        self.db.insertApartment(data)

    
    def _extractBedrooms(self, fromStr):
        m = self.BR_RE.search(fromStr)
        bedrooms = None
        #print m.groups()
        if m:
            if m.group(2) != None: #numeric
                bedrooms = int(m.group(2))
                
            elif m.group(4) != None: #studio
                bedrooms = 0
                
            elif m.group(5) != None: #jr 1 bed
                bedrooms = 1
                
        return bedrooms
    
    def _geocode(self, location):
        time.sleep(1)
        
        
        if not verbose:
            out = sys.stdout
            sys.stdout = devnull
        
        g = geocoders.Google(GMAPS_KEY)
        locs = list(g.geocode(location, exactly_one=False))
        
        if not verbose:
            sys.stdout = out
        
        if len(locs) > 0:
            place, latlon = locs[0]
        else:
            place, latlon = (None, (None, None))
        
        return place, latlon
    
    def _extractLocation(self, soup):
        link = soup.find('a', href= lambda x: x and x.startswith(u'http://maps.google.com'))
        if not link:
            return None, None
        
        link = link['href'].replace(u'http://maps.google.com/?q=', u'')
        
        def _repl_func(match):
            return unichr(int(match.group(2), 16))
        
        link = self.ENTITY_RE.sub(_repl_func, link) 
        
        link = link.replace(u'+', u' ')
        link = link.replace(u'loc: ', u'')
        
        place, latlon = self._geocode(link)
        
        return place, latlon
    
    def parse(self):
        """
        want to extract
        - location
        - neighborhood
        """
        ltitle = self.title.lower()
        lbody = self.body.lower()
        
        #$$$
        m = self.PRICE_RE.search(ltitle)
        self.price = None
        if m: self.price = m.group(1)
        
        #phone
        m = CraigslistScraper.PHONE_RE.search(lbody)
        self.phone = None
        if m: self.phone = '%s-%s-%s' % (m.group(1), m.group(3), m.group(5))
        
        #bedrooms
        self.bedrooms = self._extractBedrooms(ltitle)
        if self.bedrooms == None:
            self.bedrooms = self._extractBedrooms(lbody)
        
        if self.bedrooms == None:
            sprint('fail: no bedrooms %s' % self.url)
            self.db.incrementMetric('fail_no_bedrooms')
            return False
        
        #is open house
        m = self.OPEN_HOUSE_RE.search(ltitle)
        if m == None:
            m = self.OPEN_HOUSE_RE.search(lbody)
        self.openhouse = m != None
        
        self.location, self.latlon = self._extractLocation(self.soup)
        
        if not self.location:
            sprint('fail: no location %s' % self.url)
            self.db.incrementMetric('fail_no_location')
            return False
        
        self.area = self.area.replace(u'(', u'')
        self.area = self.area.replace(u')', u'')
        
        _log('ok')
        #print self.body
        
        self.saveToDB()
        return True

class ApartmentCraigslistScraper(CraigslistScraper):
    def __init__(self, sub, dom='org', baseUrl='/sfc/apa', checkDB=True):
        CraigslistScraper.__init__(self, sub, dom=dom, baseUrl=baseUrl, checkDB=checkDB)
    
    def _isInDB(self, craigslistId):
        return self.db.hasApartment(craigslistId)
        
    def _createPostObj(self, postData):
        return CraigslistApartmentPost(self.db, postData)
        
    
if __name__ == '__main__':
    import sys
    
    verbose=False
    
    scr = ApartmentCraigslistScraper('sfbay')
    
    import datetime
    sprint('$$ Start %s \n' % datetime.datetime.now())
    
    if len(sys.argv) > 1:
        scr.scrapePage(sys.argv[1])
    else:
        scr.scrape()
    
    