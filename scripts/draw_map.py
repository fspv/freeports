# -*- coding: utf-8 -*-
# 01-03 - *1
# 28-40 - *2
# 24-16 - *3
# 15-11 - *4
# 11-05-10 - *5
import pygraphviz as pgv
import config
import MySQLdb
import re
import os
"""
def sides():
    for sector in ['G','D','E','J']:
        view[sector][1] = [[str(j)+(str(i) if len(str(i)) == 2 else '0'+str(i)) for i in range(1,4)] for j in range(1,10)]
        j[2] = [[str(j)+(str(i) if len(str(i)) == 2 else '0'+str(i)) for i in range(28,41)] for j in range(1,10)]
        j[3] = [[str(j)+(str(i) if len(str(i)) == 2 else '0'+str(i)) for i in range(16,25)] for j in range(1,10)]
        j[4] = [[str(j)+(str(i) if len(str(i)) == 2 else '0'+str(i)) for i in range(11,16)] for j in range(1,10)]
        tmp = [[str(j)+(str(i) if len(str(i)) == 2 else '0'+str(i)) for i in range(5,11)] for j in range(1,10)]
        it=0
        for i in tmp:
            jt=0
        for j in i:
            if int(j[0])<5 and int(j[2])!=5:
                tmp[it][jt]=''
                jt+=1
            tmp[it].insert(0,'')
            tmp[it].insert(0,str(it+1)+'11')
            it+=1
        j[5] = tmp
"""

def sector_net(sector="J"):
    rooms = []
    fill = []
    for room in range(1,4):
        rooms.append([room,[6,room+3]])
    for room in range(5,11):
        rooms.append([room,[11-room,8]])
    for room in range(11,15):
        rooms.append([room,[8,19-room]])
    for room in range(16,21):
        rooms.append([room,[-7+room,3]])
    for room in range(22,25):
        rooms.append([room,[-6+room,3]])
    for room in range(28,41):
        rooms.append([room,[28+18-room,1]])
    for x in range(1,19):
        for y in range(1,9):
            if (x in range(1,8) and y==7) or (x==7 and y in range(2,9)) or (x in range(6,19) and y==2) or (x in range(6,9) and y==3) or (x in range(14,16) and y==3) or (x==8 and y==4):
                fill.append([str(x)+","+str(y),[x,y]])
    return [rooms,fill]
conn = MySQLdb.connect(\
                host = config.mysql_host,\
                user = config.mysql_user,\
                passwd = config.mysql_pass,\
                db = config.mysql_dbname\
)
db = conn.cursor(MySQLdb.cursors.DictCursor)
re_room = re.compile('^[1-9]{1,1}([0-4]{1,1}[0-9]{1,1})$')
class SectorError(Exception):
    pass
def position_node(G,switch,positions,additional,parent=0):
    try:
            if switch['sector'] in ['G','D','E','J']:
                pass
            else:
                raise IndexError
            subroom =  re.findall(re_room,str(switch['room']))[0]
            try:
                node = G.get_node(switch['sw'])
                return {'G':G,'positions':positions,'additional':additional}
            except:
                G.add_node(switch['sw'])
                #print switch['name']
                node = G.get_node(switch['sw'])
                node.attr['label'] = switch['name']
                node.attr['style'] = 'filled'
                node.attr['URL'] = config.website_location+'switch-'+str(switch['sw'])+'/'
                if switch['stupid'] == 1:
                    node.attr['fillcolor'] = 'deeppink'
                else:
                    node.attr['fillcolor'] = 'cyan'
                positions[int(subroom)-1]+=1
            #print switch['name']+"["+str(switch['sw'])+"]"+":"+str(positions[int(subroom)-1])
            subroompos = G.get_node(int(re.findall(re_room,str(switch['room']))[0])).attr['pos'].split(',')
            if (int(subroom) in range(1,12)) or (int(subroom) in range(16,25)):
                x = int(subroompos[0])
                y = int(subroompos[1])+positions[int(subroom)-1]
                node.attr['pos'] = str(x)+","+str(y)
                node.attr['pin'] = "true"
            if (int(subroom) in range(28,41)):
                x = int(subroompos[0])
                y = int(subroompos[1])-positions[int(subroom)-1]
                node.attr['pos'] = str(x)+","+str(y)
                node.attr['pin'] = "true"
            if (int(subroom) in range(1,4)):
                y = int(subroompos[1])
                x = int(subroompos[0])-positions[int(subroom)-1]
                node.attr['pos'] = str(x)+","+str(y)
                node.attr['pin'] = "true"
            if (int(subroom) in range(12,15)):
                y = int(subroompos[1])
                x = int(subroompos[0])+positions[int(subroom)-1]
                node.attr['pos'] = str(x)+","+str(y)
                node.attr['pin'] = "true"
            #if parent==0:
                #try:
                #G.get_node(switch['parent'])
                #G.add_edge(switch['sw'],switch['parent'])
                #except:
                #    temp = position_node(Gswitch['parent']
                #    G.add_edge(switch['sw'],switch['parent'])
    except IndexError,SectorError:
        try:
            node = G.get_node(switch['sw'])
        except:
            G.add_node(switch['sw'])
            node = G.get_node(switch['sw'])
            node.attr['pos'] = "1,"+str(7-additional)
            node.attr['pin'] = "true"
            node.attr['style'] = 'filled'
            node.attr['URL'] = config.website_location+'switch-'+str(switch['sw'])+'/'
            if switch['stupid'] == 1:
                node.attr['fillcolor'] = 'deeppink'
            else:
                node.attr['fillcolor'] = 'cyan'
            additional+=1
        node.attr['label'] = switch['name']
    return {'G':G,'positions':positions,'additional':additional}
for sector in ['G','D','E','J']:
    net = sector_net()
    db.execute('SELECT sw,name,stupid,sector,room,parent,parent_port,uplink_port FROM map WHERE deleted=0 and sector=\''+sector+'\';')
    #print net[1]
    G = pgv.AGraph(name=sector,splines="true",rotation="180")
    #print G
    for room in net[0]:
        G.add_node(room[0])
        node = G.get_node(room[0])
        node.attr['pos'] = str(room[1][0])+","+str(room[1][1])+""
        node.attr['pin'] = "true"
        node.attr['shape'] = "box"
    for empty in net[1]:
        G.add_node(empty[0])
        node = G.get_node(empty[0])
        node.attr['pos'] = str(empty[1][0])+","+str(empty[1][1])+""
        node.attr['pin'] = "true"
        node.attr['label'] = ''
        node.attr['shape'] = "box"
        node.attr['color'] = 'grey'
    positions = []
    for i in range(1,41):
        positions.append(0)
    additional = 1
    switches = db.fetchall()
    for switch in switches:
        temp = position_node(G,switch,positions,additional)
        G = temp['G']
        positions = temp['positions']
        additional = temp['additional']
        db.execute('SELECT * FROM map WHERE sw=\'' + str(switch['parent'])+'\'')
        switch = db.fetchall()[0]
        temp = position_node(G,switch,positions,additional,1)
        G = temp['G']
        positions = temp['positions']
        additional = temp['additional']
    for switch in switches:
        G.add_edge(switch['sw'],switch['parent'])
        edge = G.get_edge(switch["parent"],switch["sw"])
        parent_port_state = ''
        uplink_port_state = ''
        # Выясняем состояние линка на основе состояний даунлинка родительского свитча и аплинка
        if switch["parent_port"]:
            db.execute('SELECT port_state FROM current WHERE sw='+str(switch["parent"])+' and port='+str(switch["parent_port"])+';')
            parent_port_state = str(db.fetchall()[0]['port_state'])
        if switch["uplink_port"]:
            if switch['stupid']!=1:
                db.execute('SELECT port_state FROM current WHERE sw='+str(switch["sw"])+' and port='+str(switch["uplink_port"])+';')
                uplink_port_state = str(db.fetchall()[0]['port_state'])
        if parent_port_state and uplink_port_state:
            link_state = min(int(parent_port_state),int(uplink_port_state))
        elif parent_port_state:
            link_state = int(parent_port_state)
        # Форматирование ребра в зависимости от состояния линка
        edge.attr['fontsize'] = '8'
        edge.attr['fontcolor'] = '#0000ff'
        #edge.attr['label'] = str(switch['parent_port'])+'-'+str(switch['uplink_port'])
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
    if sector in ['E','D']:
        for node in G.nodes():
            pos = node.attr['pos'].split(",")
            node.attr['pos'] = pos[0]+","+str(-int(pos[1]))
    if sector in ['G','J']:
        for node in G.nodes():
            pos = node.attr['pos'].split(",")
            node.attr['pos'] = str(-int(pos[0]))+","+str(-int(pos[1]))
    #G.draw(sector+"_main.png",prog="neato")
    G.write("/tmp/"+sector+".dot")
    os.system('neato /tmp/'+sector+'.dot -Tgif -o '+config.map_dir+'static/images/'+sector+'.gif -Tcmapx -o '+config.map_dir+'templates/'+sector)
