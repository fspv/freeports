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
    downloaded = urllib2.urlopen(config.swmap_location + "map/swmap.html")
except:
    print("Can't download main page")
    exit(1)
print "Initializing parser"
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    swmap = parser.parse(downloaded.read())
    areas = swmap.findAll(name = "area") #finding all <area> tags in downloaded page
print "Connecting to MySQL"
try:
    conn = MySQLdb.connect(host = config.mysql_host,user = config.mysql_user,passwd = config.mysql_pass,db = config.mysql_dbname)
except:
    print "Can't connect to MySQL"
    exit(1)
db = conn.cursor()
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    db.execute('CREATE TABLE IF NOT EXISTS map(\
					    sw SMALLINT UNSIGNED PRIMARY KEY,\
					    name TINYTEXT,\
					    stupid SMALLINT(1),\
					    model TINYTEXT,\
					    sector TINYTEXT,\
					    room SMALLINT UNSIGNED,\
					    side TINYTEXT,\
					    parent SMALLINT UNSIGNED,\
					    parent_port SMALLINT(2) UNSIGNED,\
					    ports_count SMALLINT(2) UNSIGNED,\
					    uplink_port SMALLINT(2) UNSIGNED,\
					    ip TINYTEXT,\
					    updated TINYTEXT,\
					    deleted SMALLINT(1),\
                        state SMALLINT\
	    );')
    db.execute('CREATE TABLE IF NOT EXISTS clients(\
						id INT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,\
						sw SMALLINT UNSIGNED,\
						username TINYTEXT,\
						sector TINYTEXT,\
						room TINYTEXT,\
						ip TINYTEXT,\
						mac TINYTEXT,\
						port SMALLINT UNSIGNED,\
						last_seen SMALLINT UNSIGNED\
	    );')
    conn.commit()
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
    sector = str(re.findall(re1,i['title'])[0]) if len(re.findall(re1,i['title'])) == 1 else "NULL"
    room = str(re.findall(re2,i['title'])[0]) if len(re.findall(re2,i['title'])) == 1 else "999"
    side = str(re.findall(re3,i['title'])[0]) if len(re.findall(re3,i['title'])) == 1 else "NULL"
    stupid = "0"
    deleted = "0"
    # insert on duplicate update (K.O)
    db.execute('INSERT INTO map(sw,name,stupid,sector,room,side,deleted) VALUES(\''+sw+'\',name=\''+str(i['title'])+'\',\''+stupid+'\',\''+sector+'\',\''+room+'\',\''+side+'\',\''+deleted+'\') ON DUPLICATE KEY UPDATE name=\''+str(i['title'])+'\',stupid=\''+stupid+'\',sector=\''+sector+'\',room=\''+room+'\',deleted=\''+deleted+'\';')
    conn.commit()
    # starting of updating this switch (K.O)
    try:
        update_switch.update(i['href'],sw)
    except:
        print "Switch update failed"
conn.commit()
# Adding index for faster search
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    db.execute('ALTER TABLE clients DROP INDEX i_name;')
    db.execute('ALTER TABLE clients ADD INDEX i_name (sw, port);')
    conn.commit()
db.close()
conn.close()
print (-begin+time())/60
