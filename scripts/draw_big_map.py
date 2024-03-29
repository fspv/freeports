# -*- coding: utf-8 -*-
import config
import pygraphviz as pgv
import MySQLdb
import os
# Создаем новый граф G
G = pgv.AGraph(rankdir = 'LR',name='G',overlap = 'false')

# Кластеры для секторов Б,В,Г,Д,Е,Ж
subg = {'cluster_B':[],'cluster_V':[],'cluster_G':[],'cluster_D':[],'cluster_E':[],'cluster_J':[]}
# Аттрибуты кластера для каждого из секторов
for i in ['B','V','G','D','E','J']:
    attributes={}
    attributes.update(style='dotted',label='Sector '+i)
    subg['cluster_'+i] = G.subgraph('',name='cluster_'+i,**attributes)

# Коннект к базе
conn = MySQLdb.connect(\
                host = config.mysql_host,\
                user = config.mysql_user,\
                passwd = config.mysql_pass,\
                db = config.mysql_dbname\
)
db = conn.cursor(MySQLdb.cursors.DictCursor)
db.execute('SELECT sw,name,stupid,sector,parent,parent_port,uplink_port,state FROM map WHERE deleted=0;')
switches = db.fetchall()
db.execute('SELECT * FROM reserves WHERE deleted=0;')
reserves = db.fetchall()
def check_state(switch):
    db.execute('SELECT * FROM map WHERE sw='+str(switch)+';')
    sw = db.fetchall()[0]
    #print sw['state']
    if sw['state'] == 0 or sw['state'] == -1:
        return 1
    else:
        if sw['parent']:
            return check_state(sw['parent'])
        else:
            return 0
# Каждый свитч добавляется на граф
for row in switches:
	# Добавляем свитч в кластер, если он принадлежит какому-нибудь из секторов
    if str(row['sector'])!='NULL' and str(row['sector'])!='None' and str(row['sector'])!='none' and str(row['sector'])!='':
		subg['cluster_'+row['sector']].add_node(row["sw"])
		node = subg['cluster_'+row['sector']].get_node(row["sw"])
    else:
		G.add_node(row["sw"])
		node = G.get_node(row["sw"])
	# Аттрибуты свитча
    node.attr['style'] = 'filled'
    node.attr['label'] = row["name"]
    node.attr['URL'] = config.website_location+'switch-'+str(row['sw'])+'/'
    if check_state(row['sw']):
        node.attr['fillcolor'] = 'yellow'
    else:
        #print row['name']+" deleted"+row['deleted']
        if row['stupid'] == 0 or row['stupid'] == 'NULL':
            node.attr['fillcolor'] = 'cyan'
        else:
            node.attr['fillcolor'] = 'deeppink'
    # Если имеется родительский свитч - добавляем ребро графа    
    if row["parent"]:
        G.add_edge(row["parent"],row["sw"])
        edge = G.get_edge(row["parent"],row["sw"])
        parent_port_state = ''
        uplink_port_state = ''
        # Выясняем состояние линка на основе состояний даунлинка родительского свитча и аплинка
        if row["parent_port"]:
            db.execute('SELECT port_state FROM current WHERE sw='+str(row["parent"])+' and port='+str(row["parent_port"])+';')
            parent_port_state = str(db.fetchall()[0]['port_state'])
        if row["uplink_port"]:
            if row['stupid']!=1:
                db.execute('SELECT port_state FROM current WHERE sw='+str(row["sw"])+' and port='+str(row["uplink_port"])+';')
                uplink_port_state = str(db.fetchall()[0]['port_state'])
        if parent_port_state and uplink_port_state:
            link_state = min(int(parent_port_state),int(uplink_port_state))
        elif parent_port_state:
            link_state = int(parent_port_state)
        states={'-1':'disabled','0':'down','10':'10Mbps','100':'100Mbps','1000':'1Gbps'}
        # Форматирование ребра в зависимости от состояния линка
        edge.attr['fontsize'] = '8'
        edge.attr['fontcolor'] = '#0000ff'
        downlink_port = str(row['parent_port']) if row['parent_port'] else '??'
        uplink_port = str(row['uplink_port']) if row['uplink_port'] else '??'
        edge.attr['label'] = downlink_port + '-' + uplink_port
        if link_state == -1:
            edge.attr['style'] = 'dotted'
            edge.attr['color'] = 'red'
        elif link_state == 0:
            edge.attr['style'] = 'dotted'
        elif link_state == 10:
            edge.attr['color'] = 'yellow'
        elif link_state == 100:
            pass
        elif link_state == 1000:
            edge.attr['style'] = 'bold'
        if str(link_state) != str(row['state']):
            if(config.DEBUG):
                print 'UPDATE map SET state='+str(link_state)+' WHERE sw='+str(row['sw'])+';'
            db.execute('UPDATE map SET state='+str(link_state)+' WHERE sw='+str(row['sw'])+';')
            conn.commit()
            #if str(row['stupid'])=='1':
            #    os.system('python2 ' + config.map_dir + \
            #           'scripts/google-sms.py --title="Состояние линка до ' + row['name'] + \
            #            ' изменилось на '+states[str(link_state)]+'" --location="Аплинк на свитче '+row['name']+'"')
for reserve in reserves:
    G.add_edge(reserve['sw1'],reserve['sw2'])
    edge = G.get_edge(reserve['sw1'],reserve['sw2'])
    edge.attr['style'] = 'dotted'
    edge.attr['color'] = 'green'
    edge.attr['fontsize'] = '12'
    edge.attr['fontcolor'] = '#0000ff'
    edge.attr['constraint'] = 'false'
G.draw(config.map_dir+"static/images/big_swmap.png",prog="dot")
G.write("/tmp/big_swmap.dot")
os.system('dot /tmp/big_swmap.dot -Tgif -o '+config.map_dir+'static/images/big_swmap.gif -Tcmapx -o '+config.map_dir+'templates/big_swmap.html')

db.close()
conn.close()
