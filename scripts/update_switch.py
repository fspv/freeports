# -*- encoding: utf-8 -*-
import lxml
import lxml.html
import config
from config import DEBUG
import urllib2
import MySQLdb
import re
import time
from lxml import etree
import os
import subprocess
import sys
re_last_seen = re.compile('^(?P<days>[0-9]*) days')
re_switch = re.compile('switch=([0-9]*)')
re_uplink = re.compile(r'включен в ([0-9]{1,2})')
re_ports_count = re.compile(r'([0-9]{1,2})-портовый')
re_title = re.compile(r'коммутатор (.*), который')
#re_ip = re.compile('\(([0-9\.]{7,})\)')
re_tablefix = re.compile(r"</tr>\n<td")
re_td_cut_unused = re.compile(r"<td.*?>")

re_ip = re.compile(r'.*(?P<ip>172.31.0.[0-9]{1,3}).*')
re_info = re.compile(
                'Коммутатор (?P<swname>.*) - это '
                '(?P<portcount>[0-9]{1,2})-портовый '
                'коммутатор (?P<model>.*), который стоит '
                'в (?P<room>.*). Аплинк включен в '
                '(?P<uplink>[0-9]{1,2}) порт.')
re_table_begin = re.compile(r"<table.*>")
re_table_end = re.compile(r"</table>")
re_link = re.compile(
                r'<tr.*><td.*><a href="/cgi-bin/swinfo.pl\?switch=(?P<swid>[0-9]{1,5})">(?P<swname>.*)</a></td>'
                '<td.*>(?P<sector>А|Б|В|Г|Д|Е|Ж|И|К)</td>'
                '<td.*>(?P<room>[0-9]{1,5})</td>'
                '<td.*>(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</td>'
                '<td.*>(?P<port>[0-9]{1,2})</td>'
                '<td.*>(?P<speed>[0-9a-zA-Z\. ]{0,12})</td>'
                '<td.*>(?P<macscurrent>.{0,20})</td>'
                '<td.*>(?P<lastseen>[hrsminsecday0-9 ,]*)')
re_reg = re.compile(
                r'<td.*>(?P<user>[a-z0-9\-_ ]*)</td>'
                r'<td.*>(?P<sector>А|Б|В|Г|Д|Е|Ж|И|К)</td>'
                '<td.*>(?P<room>[0-9\--]{1,5})</td>'
                '<td.*>(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</td>'
                '<td.*>(?P<mac>[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})</td>'
                '<td.*>(?P<port>[0-9]{1,2})</td>'
                '<td.*>(?P<speed>[0-9a-zA-Z\. ]{0,12})</td>'
                '<td.*>(?P<lastseen>[hrsminsecday0-9 ,]*)</td>')
re_unreg = re.compile(
                r"<td.*>(?P<user>Unregistered)</td>"
                "<td.*>(?P<mac>[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})</td>"
                "<td.*>(?P<port>[0-9]{1,2})</td>"
                "<td.*>(?P<speed>[0-9a-zA-Z\. ]{0,12})</td>"
                "<td.*>(?P<lastseen>[hrsminsecday0-9 ,]*)</td>")
def update(sw_url, sw, mode='all'):
    filename = '/tmp/swmap/switch'+sw
    try:
        tmp = '&show=all' if mode!='swonly' else ''
        url = str(config.swmap_location) + str(sw_url) + str(tmp)
        try:
            os.remove(filename)
        except:
            pass
        subprocess.call(['wget', '-T', '300', '-O', filename, '--quiet', '--user=' + config.swmap_username, '--http-passwd=' + config.swmap_password, url])
    except:
        print "Can't load file"
        raise
    try:
        loaded = open(filename, 'r')
    except:
        print "Can't open file"
        raise
    try:
        try:
            conn = MySQLdb.connect(
                    host=config.mysql_host,
                    user=config.mysql_user,
                    passwd=config.mysql_pass,
                    db=config.mysql_dbname)
        except:
            print "Can't connect to MySQL"
            raise

        db = conn.cursor()
        if(mode != 'swonly'):
            db.execute('DELETE FROM clients WHERE sw=\''+sw+'\';')
        # Выключаем индексы, чтобы не было пиздеца при вставке тысяч строк
        db.execute('SET autocommit=0;')
        db.execute('SET unique_checks=0;')
        db.execute('SET foreign_key_checks=0;')
        conn.commit()

        # Переменные ниже понадобятся для определения
        # в какой таблице мы находимся и что делать
        tables_counter = 0
        write_to_table = 0
        first_line = 0
        for line in loaded:
            """
                Построчно читаем файл и думаем, что с этим делать :)
            """
            first_line = 0
            if(re.match(re_table_begin, line)):
                """
                    Если увидели начало таблицы обозначаем, что надо начинать
                    её обрабатывать и обозначаем, что это первая строка,
                    которая нам не нужна, это шапка таблицы
                """
                write_to_table = 1
                first_line = 1  # Первая строка в таблице (шапка), она нам не нужна

            if(re.match(re_table_end, line)):
                """
                    Если увидели конец таблицы, обозначаем, что это конец
                    и увеличиваем количество обработанных таблиц на 1
                """
                tables_counter += 1
                write_to_table = 0

            if(write_to_table and first_line != 1):
                if(tables_counter == 1):
                    """ Таблица с линками до других свитчей """
                    # Проверяем, нпервую строчку на предмер того, что это действительно
                    # нужная таблица. Т.к. может оказаться, что этой таблицы не 
                    # существует и надо сразу же переходить к следующей
                    test_reg = re.match(re_reg, line)
                    test_unreg = re.match(re_unreg, line)
                    if(test_reg or test_unreg):
                        tables_counter = 2
                    link = re.match(re_link, line)
                    if(link and tables_counter == 1):
                        query = 'UPDATE map SET parent=\'' + \
                                    sw+'\',parent_port=\'' + \
                                    link.group('port') + '\'WHERE sw=\'' + \
                                    link.group('swid') + '\';'
                        if(DEBUG):
                            print query

                        db.execute(query)

                if(tables_counter == 2 and None):
                    """ Основная таблица с юзерами """
                    unreg = re.match(re_unreg, line)
                    if(unreg):
                        days = re.match(re_last_seen, unreg.group('lastseen'))
                        if(days):
                            days = days.group('days')
                        else:
                            days = 0
                        query = 'INSERT INTO clients(sw,mac,port,last_seen) VALUES(\'' + \
                                sw + '\',\'' + \
                                unreg.group('mac') + '\',\'' + \
                                unreg.group('port') + '\',\'' + \
                                str(days) + '\');'
                        #print query
                        db.execute(query)
                    else:
                        reg = re.match(re_reg, line)
                        if(reg):
                            days = re.match(re_last_seen, reg.group('lastseen'))
                            if(days):
                                days = days.group('days')
                            else:
                                days = 0
                            query = 'INSERT INTO clients(' + \
                                            'sw,' + \
                                            'username,' + \
                                            'sector,' + \
                                            'room,' + \
                                            'ip,' + \
                                            'mac,' + \
                                            'port,'+ \
                                            'last_seen) VALUES(\'' + \
                                        sw + '\',\'' + \
                                        reg.group('user') + '\',\'' + \
                                        reg.group('sector') + '\',\'' + \
                                        reg.group('room') + '\',\'' + \
                                        reg.group('ip') + '\',\'' + \
                                        reg.group('mac') + '\',\'' + \
                                        reg.group('port') + '\',\'' + \
                                        str(days) + '\');'
                            #print query
                            db.execute(query)
                        else:
                            print "Can't determine type of line"
                            print line
            else:
                if(first_line != 1):
                    info = re.match(re_info, line)
                    ip = re.match(re_ip, line)
                    if(info):
                        query = 'UPDATE map SET uplink_port=\'' + \
                                info.group('uplink') + '\',ports_count=\'' + \
                                info.group('portcount') + '\',model=\'' + \
                                info.group('model') + '\' WHERE sw=' + \
                                sw + ';'
                        if(DEBUG):
                            print query
                        db.execute(query)
                    if(ip):
                        query = 'UPDATE map SET ip=\'' + ip.group('ip') + '\' WHERE sw=' + sw + ';'
                        if(DEBUG):
                            print query
                        db.execute(query)
                    conn.commit()

        conn.commit()

        db.execute('UPDATE map SET updated=\''+str(time.time())+'\',deleted=\'0\' WHERE sw=\''+sw+'\';')

        conn.commit()
        try:
           os.remove(filename)
        except:
           pass
    except:
        raise

if(len(sys.argv)>1):
    print len(sys.argv)
    print sys.argv[1]
    update(sys.argv[1], sys.argv[2])

