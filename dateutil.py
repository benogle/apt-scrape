import datetime


class TimeZone:
    def __init__(self, reprname, abbr, isdst, offset):
        self.reprname = reprname
        self.abbr = abbr
        self.isdst = isdst
        self.offset = datetime.timedelta(hours=offset)
        
class USTimeZone(datetime.tzinfo):

    ZERO = datetime.timedelta(0)
    HOUR = datetime.timedelta(hours=1)
    
    __TZ = {'est':TimeZone('Eastern', 'EST', False, -5),
            'edt':TimeZone('Eastern', 'EDT', True,  -5),
            'cst':TimeZone('Central', 'CST', False, -6),
            'cdt':TimeZone('Central', 'CDT', True,  -6),
            'mst':TimeZone('Mountain','MST', False, -7),
            'mdt':TimeZone('Mountain','MDT', True,  -7),
            'pst':TimeZone('Pacific', 'PST', False, -8),
            'pdt':TimeZone('Pacific', 'PDT', True,  -8),
            'akst':TimeZone('Alaska', 'PST', False, -9),
            'akdt':TimeZone('Alaska', 'PDT', True,  -9),
            'hst':TimeZone('Hawaii', 'PST', False, -10),
            'hdt':TimeZone('Hawaii', 'PDT', True,  -10)}

    def __init__(self, abbr):
        assert isinstance(abbr, str)
        self.timezone = self.__TZ[abbr.lower().strip()]

    def __repr__(self):
        return self.timezone.reprname

    def tzname(self, dt):
        return self.timezone.abbr

    def utcoffsetint(self):
        return self.utcoffset(None).seconds / 3600 - 24
    
    def utcoffset(self, dt):
        return self.timezone.offset + self.dst(dt)

    def dst(self, dt):
        if self.timezone.isdst:
            return self.HOUR
        else:
            return self.ZERO

def timeOffset(t):
    if isinstance(t, datetime.datetime):
        print t.tzinfo
    return None

def localTimeOffset(t=None):
    """Return offset of local zone from GMT, either at present or at time t."""
    # python2.3 localtime() can't take None
    if t is None:
        t = time.time()

    if time.localtime(t).tm_isdst and time.daylight:
        return -(time.altzone/3600)
    else:
        return -(time.timezone/3600)
    
def nowUTCstr():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#offset will be _subtracted_ from the date time object
def _timeUtcCalc(dt, offsetHours, subtract=True):
    utc_offset_minutes = int(offsetHours*60)
    td = datetime.timedelta(minutes=utc_offset_minutes)
    if subtract:
        return dt-td
    else:
        return dt+td
    
def toUtc(dt, offsetHours):
    return _timeUtcCalc(dt,offsetHours)
    
def fromUtc(dt, offsetHours):
    return _timeUtcCalc(dt,offsetHours, subtract=False)
    
#def strToUtcTime( datestring ) :
#    date = toUtc(datetime.datetime(*time.strptime(datestring,"%Y-%m-%d %H:%M:%S")[0:6]))
#    return date

def strToTime( datestring, format="%Y-%m-%d %H:%M:%S", timezoneinfo=None) :
    
    pt = time.strptime(datestring,format)
    date = datetime.datetime(pt[0],pt[1],pt[2],pt[3],pt[4],pt[5], tzinfo=timezoneinfo)

    return date

def _pluralize(string, num):
    if num != 1:
        return string + 's'
    return string

def dateToDBString( date ):
    return date.strftime("%Y-%m-%d %H:%M:%S")

#returns utc time
def concatDateAndTime(dateArr, timeArr, offsetHours):
    if len(dateArr[2]) == 2:
        dateArr[2] = '20' + dateArr[2]
        
    dateArr = '-'.join(dateArr)
    st = dateArr + ' %s:%s %s' % (timeArr[0], timeArr[1], timeArr[2].upper())
    return toUtc(strToTime( st, format="%m-%d-%Y %I:%M %p" ), offsetHours)

def getDateMatches(thedate):
    date = re.compile('^([0-9]?[0-9])[\s]*/[\s]*([0-9]?[0-9])[\s]*/[\s]*(2?0?0[7-9])$')
    datem = date.match(thedate)
    return datem

#this is very specific, it returs a 1 for date time differences
#less that 24 hours but with different dates, otherwise we screw up our
#today, yesterday, tomorrow stuff.
def subDays(date1, date2):
    dates = [date1,date2]
    mind = min(dates)
    maxd = max(dates)
    
    diff = maxd - mind
    
    if diff.days == 0:
        if date1.day != date2.day:
            return 1
    elif diff.days == 1:
        d = mind + datetime.timedelta(days=1)
        if mind.day != maxd.day:
            return 2

    return diff.days

#can be string or datetime. 
#date MUST be utc 
#if its a string, it has to be in DB format
def readableDay( date, offsetHours ):
    if isinstance(date, str):
        date = strToTime(date)
    
    n = datetime.datetime.utcnow()
    if offsetHours != None:
        date = fromUtc(date, offsetHours)
        n = fromUtc(n, offsetHours)
    
    days = subDays(n,date)
    
    if date > n: #our date is in the future...    
        if days == 0:
            return 'Today'
        if days == 1:
            return 'Tomorrow'
        
        days *= -1
        
    else: #in the past        
        if days == 0:
            return 'Today'
        if days == 1:
            return 'Yesterday'
    
    if abs(days) < 7:
        if days > 0:
            pre = 'Last '
        else:
            pre = ''
        return pre + date.strftime('%A (%b %d)')
    
    return date.strftime('%b %d, %Y')

#We dont need to deal with timezones if we do this...
def readableDate( datestring ) :
    datestring = str(datestring)
    
    if datestring == None or datestring == '':
        return ''
    
    utct = strToTime(datestring)
    n = datetime.datetime.utcnow()
    diff = n - utct
    
    if diff.seconds < 60:
        return "just now"
    
    minutes, seconds = divmod(diff.seconds, 60)
    if minutes < 60 and diff.days == 0:
        return str(minutes) + _pluralize(' minute',minutes) + ' ago' #', ' + str(seconds) + _pluralize(' second',seconds) + ' ' + 'ago'
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24 and diff.days == 0:
        st = str(hours) + _pluralize(' hour',hours)
        if minutes > 0:
            st += ', ' + str(minutes) + _pluralize(' minute',minutes)
        st += ' ago'
        return st
    
    days = diff.days
    if days < 365:
        st = str(days) + _pluralize(' day',days)
        if hours > 0:
            st += ', ' + str(hours) + _pluralize(' hour',hours)
        st += ' ago'
        return st

    years, days = divmod(days, 365)
    st = str(years) + _pluralize(' year',years)
    if days > 0:
        st += ', ' + str(days) + _pluralize(' day',days)
    st += ' ago'
    return st