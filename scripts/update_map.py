#import pdb; pdb.set_trace()
import config
import warnings
import urllib2
import html5lib
from html5lib import treebuilders
import MySQLdb
import update_switch
import re
from time import time
import sys
begin = time() #to measure execution time
print "Downloading main page"
try:
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, config.swmap_location, config.swmap_username, config.swmap_password)
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))
    downloaded = urllib2.urlopen("http://phoenix.masterbit.su/map/swmap.html")
except:
    print("Can't download main page")
    exit(1)
print "Initializing parser"
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    swmap = parser.parse(downloaded.read())
    areas = swmap.findAll(name = "area") #finding all <area> tags in downloaded page
#print areas
print "Connecting to MySQL"
try:
    conn = MySQLdb.connect(host = config.mysql_host,user = config.mysql_user,passwd = config.mysql_pass,db = config.mysql_dbname)
except:
    print "Can't connect to MySQL"
    exit(1)
print "mysql connected"
db = conn.cursor()
print "Deleting keys"
db.execute('ALTER TABLE clients DISABLE KEYS;')
conn.commit()
try:
    db.execute('DROP INDEX sw ON clients;')
    db.execute('DROP INDEX port ON clients;')
    db.execute('DROP INDEX username ON clients;')
    db.execute('DROP INDEX last_seen ON clients;')
    db.execute('DROP INDEX room_sector ON clients;')
    db.execute('DROP INDEX ip ON clients;')
    db.execute('DROP INDEX mac ON clients;')
    conn.commit()
except:
    print "Not all keys exists or we can't delete some case because of some strange things"
print "Initializing variables and regexps"
# for showing the progress
count = len(areas)
current = 1
#
re1 = re.compile('^[GDEJBV]')
re2 = re.compile('[0-9]{1,4}')
re3 = re.compile('[lr]$')
#Mark all smart swithches as deleted (we remark them as active again, while updating
db.execute('UPDATE map SET deleted=\'1\' WHERE stupid=\'0\';')
conn.commit()
for i in areas:
    #progress
    print '['+str(current)+'/'+str(count)+']\t'+str(i['title'])+"\t"+ str((time()-begin)/60) + ' minutes from begining of update'
    current += 1
    #getting switch parameters
    sw = str(re.findall(re.compile('[0-9]*$'),i['href'])[0])
    sector = str(re.findall(re1,i['title'])[0]) if len(re.findall(re1,i['title'])) == 1 else ""
    room = str(re.findall(re2,i['title'])[0]) if len(re.findall(re2,i['title'])) == 1 else "999"
    side = str(re.findall(re3,i['title'])[0]) if len(re.findall(re3,i['title'])) == 1 else "NULL"
    stupid = "0"
    deleted = "0"
    # insert on duplicate update (K.O)
    query = 'INSERT INTO map(sw,name,stupid,sector,room,side,deleted) ' + \
                'VALUES(\'' + \
                        sw + '\', \'' + \
                        str(i['title']) + '\',\'' + \
                        stupid + '\',\'' + \
                        sector + '\',\'' + \
                        room + '\',\'' + \
                        side + '\',\'' + \
                        deleted + '\') ' + \
                'ON DUPLICATE KEY UPDATE name=\'' + \
                        str(i['title']) + '\',stupid=\'' + \
                        stupid + '\',sector=\'' + \
                        sector + '\',room=\'' + \
                        room + '\',deleted=\'' + \
                        deleted + '\';'

    if(config.DEBUG):
        print query

    db.execute(query)
    conn.commit()
    # starting of updating this switch (K.O)
    try:
        update_switch.update(i['href'], sw)
    except:
        print "Switch update failed"
        print "Unexpected error:", sys.exc_info()[0]

db.execute('ALTER TABLE clients ENABLE KEYS;')
db.execute('SET autocommit=1;')
db.execute('SET unique_checks=1;')
db.execute('SET foreign_key_checks=1;')
conn.commit()
db.execute('CREATE INDEX sw ON clients (sw,port,username(25),last_seen);')
db.execute('CREATE INDEX port ON clients (port);')
db.execute('CREATE INDEX username ON clients (username(25));')
db.execute('CREATE INDEX last_seen ON clients (last_seen);')
db.execute('CREATE INDEX room_sector ON clients (room(5),sector(1));')
db.execute('CREATE INDEX ip ON clients (ip(15));')
db.execute('CREATE INDEX mac ON clients (mac(17));')
conn.commit()
# Adding index for faster search
#with warnings.catch_warnings():
#    warnings.simplefilter("ignore")
#    conn.commit()
db.close()
conn.close()
print (-begin+time())/60
