from django import template
from swmap.models import Map,Comments
import time
import datetime
import ipaddr
register = template.Library()
WHITELIST = (
    '10.0.0.0/8',
    '89.249.160.0/20',
    '93.180.0.0/18',
    '172.16.0.0/12',
    '188.44.32.0/19'
)
def ip_in_whitelist(request_ip):
    # the long int version of the ip address
    try:
        user_ip = ipaddr.IPv4Address(request_ip)
        for whitelist_ip in WHITELIST:
            w_ip = ipaddr.IPv4Network(whitelist_ip)
            # if ip == the network's base IP (which is the case if we're giving it a straight IP with
            # no range suffix) OR if ip is within the subnet for the given range
            # (a machine's address in a subnet can't ever be the broadcast address so it's < not <=)
            if ((user_ip > w_ip.network) and (user_ip < w_ip.broadcast)):
                # if match, return true (short circuits the rest of the function)
                return True
        return False
    except:
        return False
@register.filter
def comments_number(value):
    try:
        return str(Comments.objects.filter(switch=value).count())
    except:
        return "0"
@register.filter
def months(value):
    return "%d" % (int(value)/30)
@register.filter
def lithium(value):
    if ip_in_whitelist(value):
        return "local"
    else:
        return "union-msu.net"
@register.filter
def gender(value):
    if value == "f":
        return "female"
    else:
        return "male"
@register.filter
def downlink(value,arg):
    try:
        downlink = Map.objects.get(parent=value,parent_port=arg,deleted=0)
        return downlink.sw
    except:
        return False
@register.filter
def secToHuman(seconds,arg="hms"):
    seconds = int('%d' % (float(time.time()-float(seconds))))
    hours = int(seconds/3600)
    seconds -= 3600*hours
    minutes = int(seconds / 60)
    seconds -= int(60*minutes)
    if arg == "hm":
        if hours == 0:
            return "%02d min." % (minutes)
        return "%2d hours %2d min." % (hours,minutes)
    if hours == 0:
        if minutes == 0:
            return "%2d sec." % (seconds)
        return "%2d min. %2d sec." % (minutes, seconds)
    return "%2d hours %2d min. %2d sec." % (hours, minutes, seconds)
@register.filter
def getSwNameByID(value):
    try:
        switch = Map.objects.get(sw=value)
        return switch.name
    except:
        return None
@register.filter
def getSwPortsCountByID(value):
    switch = Map.objects.filter(sw=value)[0]
    return switch.ports_count
@register.filter
def yesno(value):
    return "yes" if value else "no"
@register.filter
def leftright(value):
    if value == "l":
        return "left"
    elif value == "r":
        return "right"
    else:
        return "unknown"
@register.filter
def timetohuman(value):
    return time.strftime("%d %b %Y (%A) %H:%M:%S MSK", time.localtime(float(value)))+" (elapsed "+str(datetime.timedelta(seconds=int(-float(value)+time.time())))+")"
@register.filter
def check(value,arg):
    try:
        return getattr(value,arg)
    except KeyError:
        return ''
@register.filter
def allswitches(value):
    return Map.objects.filter(stupid="0").order_by("name")
@register.filter
def get_range(value):
    return range(1,value+1)

##### debug mysql
@register.inclusion_tag('orm_debug.html')
def orm_debug():
    import re
    try:
        from pygments import highlight
        from pygments.lexers import SqlLexer
        from pygments.formatters import HtmlFormatter
        pygments_installed = True
    except ImportError:
        pygments_installed = False

    from django.db import connection
    queries = connection.queries
    query_time = 0
    query_count = 0
    for query in queries:
        query_time += float(query['time'])
        query_count += int(1)
        query['sql'] = re.sub(r'(FROM|WHERE)', '\n\\1', query['sql'])
        query['sql'] = re.sub(r'((?:[^,]+,){3})', '\\1\n    ', query['sql'])
        if pygments_installed:
            formatter = HtmlFormatter()
            query['sql'] = highlight(query['sql'], SqlLexer(), formatter)
            pygments_css = formatter.get_style_defs()
        else:
            pygments_css = ''
    return {
        'pygments_css': pygments_css,
        'pygments_installed': pygments_installed,
        'query_time': query_time,
        'query_count': query_count,
        'queries': queries}
