import config
import MySQLdb
import urllib2
import html5lib
import re
import time
import thread
from urlgrabber.keepalive import HTTPHandler
begin = time.time()
conn = MySQLdb.connect(\
                host = config.mysql_host,\
                user = config.mysql_user,\
                passwd = config.mysql_pass,\
                db = config.mysql_dbname\
)
db = conn.cursor()
# if this is first use of this script
db.execute('CREATE TABLE IF NOT EXISTS current(\
		    id BIGINT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,\
		    sw SMALLINT UNSIGNED,\
		    port SMALLINT UNSIGNED,\
		    port_state SMALLINT,\
		    updated TINYTEXT\
	    );')
conn.commit()
db.execute('SELECT sw FROM map WHERE stupid=0;')
raws = db.fetchall()
# initializing parameters needed to download map pages
passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
passman.add_password(None, config.swmap_location, config.swmap_username, config.swmap_password)
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))
parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
# regexp for port state
re_port_state = re.compile('alt=\"(10 |100 |1\.0 |down|disabled)')
for row in raws:
    # downloading switch page
    page = urllib2.urlopen(config.swmap_location+"cgi-bin/swinfo.pl?switch="+str(row[0]))
    switch = parser.parse(page.read())
    # findig table with current port state (on main map this table has attribute 'border=0px')
    table = switch.findAll(name = "table", border = "0px")
    # separate every (of 4) rows of table (1,4 - port numbers, 2,3 - por states)
    rows = table[0].findAll(name = "tr")
    # separating columns
    port_num_up = rows[0].findAll("td")
    port_state_up = rows[1].findAll("td")
    port_state_down = rows[2].findAll("td")
    port_num_down = rows[3].findAll("td")
    # deleting old switch info
    db.execute('DELETE FROM current WHERE sw='+str(row[0])+';')
    conn.commit()
    # adding current port states to mysql
    for i in range(0,len(port_num_up)):
        db.execute('INSERT INTO current(sw,port,port_state,updated) VALUES('+str(row[0])+','+\
	str(port_num_up[i].contents[0])+','\
	+re.findall(re_port_state,str(port_state_up[i].contents[0]))[0].replace('10 ','10').replace('100 ','100').replace('1.0 ','1000').replace('down','0').replace('disabled','-1')+','+str(time.time())+');')
        db.execute('INSERT INTO current(sw,port,port_state,updated) VALUES('+str(row[0])+','+\
	str(port_num_down[i].contents[0])+','+\
	re.findall(re_port_state,str(port_state_down[i].contents[0]))[0].replace('10 ','10').replace('100 ','100').replace('1.0 ','1000').replace('down','0').replace('disabled','-1')+','+str(time.time())+');')
conn.commit()
db.close()
conn.close()
print('running time:\t'+str((-begin+time.time())/60))
