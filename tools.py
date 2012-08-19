# -*- coding: utf-8 -*-
from django.http import HttpResponse
from swmap.models import Map, Clients, Current
from django.db.models import Q
from time import time
import re
from django.shortcuts import render_to_response

def parse_get(request):
    if 'period' in request.GET:
        last_seen = request.GET['period']
    else:
        last_seen = "365"
    if 'registered' in request.GET:
        registered = request.GET['registered'] if request.GET['registered']=='0' else '1'
    else:
        registered = "1"
    return {'last_seen':last_seen,'registered':registered}

def port_clients(switch,port,last_seen,registered):
    if registered == '1':
        clients = Clients.objects.filter(sw=switch,port=port,last_seen__lt=last_seen,username__isnull=False).extra(order_by=['last_seen'])
    else:
        clients = Clients.objects.filter(sw=switch,port=port,last_seen__lt=last_seen,username__isnull=True).extra(order_by=['last_seen'])
    return clients
def sw():
    switches = Map.objects.all()
    choices = (switches[0].sw,switches[0].name)
    for switch in switches:
        if switch == switches[0]:
            pass
        else:
            choices = choices+((switch.sw,switch.name),)
    return choices
