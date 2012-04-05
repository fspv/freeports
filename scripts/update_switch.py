# -*- encoding: utf-8 -*-
import lxml
import lxml.html
import config
import urllib2
import MySQLdb
import re
import time
from lxml import etree
re_last_seen = re.compile('(^[0-9]*) days')
re_switch = re.compile('switch=([0-9]*)')
re_uplink = re.compile(r'включен в ([0-9]{1,2})')
re_ports_count = re.compile(r'([0-9]{1,2})-портовый')
re_title = re.compile(r'коммутатор (.*), который')
re_ip = re.compile('\(([0-9\.]{7,})\)')
re_tablefix = re.compile(r"</tr>\n<td")
re_td_cut_unused = re.compile(r"<td.*?>")
def update(sw_url,sw,mode='all'):
    try:
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, config.swmap_location, config.swmap_username, config.swmap_password)
        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))
        tmp = '&show=all' if mode!='swonly' else ''
        loaded = urllib2.urlopen(config.swmap_location + sw_url + tmp)
    except:
        print "Can't load switch page"
        raise
    try:
        conn=MySQLdb.connect(host=config.mysql_host,user=config.mysql_user,passwd=config.mysql_pass,db=config.mysql_dbname)
    except:
        print "Can't connect to MySQL"
        raise
    db = conn.cursor()
    db.execute('DELETE FROM clients WHERE sw=\''+sw+'\';')
    conn.commit()

    loaded_read = loaded.read()
    # fixing the invalid html on switch page
    loaded_read = re_tablefix.sub('</tr>\n<tr><td',loaded_read)
    loaded_read = re_td_cut_unused.sub('<td>',loaded_read)
    switch = lxml.html.document_fromstring(loaded_read)
    # getting all tables from html page
    tables = switch.xpath("//body/table")
    tables=tables[1:(len(tables)-1)] # we need all tables except first and last
    # getting swith parameters from switch page
    uplink = re.findall(re_uplink,loaded_read)[0]
    ports_count = re.findall(re_ports_count,loaded_read)[0]
    model = re.findall(re_title,loaded_read)[0]
    ip = re.findall(re_ip,loaded_read)[0]
    # updating database (K.O.)
    db.execute('UPDATE map SET uplink_port=\''+uplink+'\',ports_count=\''+ports_count+'\',model=\''+model+'\',ip=\''+ip+'\' WHERE sw='+sw+';')
    conn.commit()
    for table in tables:
        rows = table.xpath("./tr")
        rows = rows[1:len(rows)]
        for it in rows:
            cols = it.xpath("./td")
            isswitch = len(cols[0].xpath("./a"))
            if (cols[0].text_content() == 'Unregistered'):
                tmp = re.findall(re_last_seen,str(cols[4].text_content()))
                last_seen = str(tmp[0]) if tmp else "0"
                query='INSERT INTO clients(sw,mac,port,last_seen) VALUES(\''+sw+'\',\''+cols[1].text_content()+'\',\''+cols[2].text_content()+'\',\''+last_seen+'\');'
                #print query
                db.execute(query)
            elif isswitch:
                query = 'UPDATE map SET parent=\''+sw+'\',parent_port=\''+cols[4].text_content()+'\'WHERE sw=\''+re.findall(re_switch,str(cols[0].xpath("./a")[0].get('href')))[0]+'\''
                #print query
                db.execute(query)
            else:
                tmp = re.findall(re_last_seen,str(cols[7].text_content()))
                last_seen = str(tmp[0]) if tmp else "0"
                query = 'INSERT INTO clients(sw,username,sector,room,ip,mac,port,last_seen) VALUES(\'' + sw + '\',\'' + cols[0].text_content() + '\',\'' + cols[1].text_content() + '\',\'' + cols[2].text_content() + '\',\'' + cols[3].text_content() + '\',\'' + cols[4].text_content() + '\',\'' + cols[5].text_content() + '\',\'' + last_seen + '\');'
                #print query
                db.execute(query)
        db.execute('UPDATE map SET updated=\''+str(time.time())+'\',deleted=\'0\' WHERE sw=\''+sw+'\';')
        conn.commit()
    db.close()
    conn.close()
