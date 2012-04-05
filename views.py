# -*- coding: utf-8 -*-
from django.http import HttpResponse
from swmap.models import Map, Clients, Current, Contacts, ContactsForm, StupidMapForm, AddStupidMapForm, SmartMapForm, Comments, CommentsForm, Reserves, ReservesForm
from django.db.models import Q,Max
from time import time
import re
from django.db import connection
from django.shortcuts import render_to_response,get_object_or_404,get_list_or_404,redirect
from tools import parse_get, port_clients
def big_swmap(request):
    return render_to_response('main.html')
def switch(request,offset):
    swinfo = get_object_or_404(Map,sw=offset)
    ports = []
    last_seen = parse_get(request)['last_seen']
    registered = parse_get(request)['registered']
    if swinfo.stupid:
        return render_to_response('stupid_switch.html',{'switch':swinfo,'clients':port_clients(swinfo.parent,swinfo.parent_port,last_seen,registered),'registered':registered,'period':last_seen,'request':request,'ip':request.META['REMOTE_ADDR']})
    else:
        for i in range(1,swinfo.ports_count+1):
            reg = Clients.objects.filter(sw=swinfo.sw,port=i,last_seen__lt=last_seen,username__isnull=False).count()
            unreg = Clients.objects.filter(sw=swinfo.sw,port=i,username__isnull=True,last_seen__lt=last_seen).count()
            current = Current.objects.get(sw=swinfo.sw,port=i)
            ports.append({'port':i,'reg':reg,'unreg':unreg,'total':(reg+unreg), 'state':current.port_state, 'updated':current.updated, 'uplink':(1 if i==swinfo.uplink_port else 0)})
        return render_to_response('smart_switch.html',{'switch':swinfo,'ports':ports,'period':last_seen,'request':request})

def port(request,switch,port):
    swinfo = Map.objects.filter(sw=switch)[0]
    last_seen = parse_get(request)['last_seen']
    registered = parse_get(request)['registered']
    values = {'switch':swinfo,'clients':port_clients(switch,port,last_seen,registered),'period':last_seen,'request':request,'port':port,'registered':registered,'ip':request.META['REMOTE_ADDR']}
    if registered=='1':
        return render_to_response('port_reg.html',values)
    else:
        return render_to_response('port_unreg.html',values)
def admin(request):
    return render_to_response('admin/main.html')
def admin_swlist(request):
    switches = Map.objects.filter(stupid='1')
    return render_to_response('admin/swlist.html',{'switches':switches})
def admin_swadd(request):
    switch_form = ''
    switch = Map(sw=(Map.objects.all().order_by('-sw')[0].sw+1))
    switch.stupid = "1"
    switch.deleted = "0"
    if request.method == "POST":
        switch_form = AddStupidMapForm(request.POST, instance=switch)
        if switch_form.is_valid():
            switch_form.save()
            return redirect('/admin/switches/')
    else:
        switch_form = AddStupidMapForm()
    return render_to_response('admin/swadd.html',{'switch_form':switch_form})
def admin_swdel(request,switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 1
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')
def admin_reservelist(request):
    reserves = Reserves.objects.all()
    return render_to_response('admin/reservelist.html',{'reserves':reserves})
def admin_reserveadd(request):
    reserve_form = ''
    reserve = Reserves()
    reserve.deleted = 0
    if request.method == "POST":
        reserve_form = ReservesForm(request.POST, instance=reserve)
        if reserve_form.is_valid():
            reserve_form.save()
            return redirect('/admin/reserves/')
    else:
        reserve_form = ReservesForm()
    return render_to_response('admin/reserveadd.html',{'reserve_form':reserve_form})
def admin_swdel(request,switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 1
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')
def admin_reservedel(request,reserveid):
    reserve = get_object_or_404(Reserves,id=reserveid)
    try:
        reserve.deleted = 1
        reserve.save()
        #return render_to_response('debug.html')
        return redirect('/admin/reserves/')
    except:
        return render_to_response('hui.html')
def admin_reserverestore(request,reserveid):
    reserve = get_object_or_404(Reserves,id=reserveid)
    try:
        reserve.deleted = 0
        reserve.save()
        return redirect('/admin/reserves/')
    except:
        return render_to_response('hui.html')
def admin_swrestore(request,switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 0
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')
def swinfo(request,offset):
    swinfo = Map.objects.filter(sw=offset)[0]
    if swinfo.stupid == 1:
        parent = Map.objects.filter(sw=swinfo.parent)[0]
        swinfo.updated = parent.updated
    check = Contacts.objects.filter(sw=swinfo.sw).count()
    if check:
        contacts = Contacts.objects.filter(sw=swinfo.sw)[0]
    else:
        contacts = {}
    return render_to_response('swinfo.html',{'switch':swinfo,'check':check,'contacts':contacts,'ip':request.META['REMOTE_ADDR']})
def swedit(request,offset):
    swinfo = Map.objects.filter(sw=offset)[0]
    if swinfo.stupid == 1:
        parent = Map.objects.filter(sw=swinfo.parent)[0]
        swinfo.updated = parent.updated
    contacts = ''
    contacts_form = ''
    switch_form = ''
    try:
        contacts = Contacts.objects.get(sw=swinfo.sw)
    except Contacts.DoesNotExist:
        #newcontact = Contacts(sw=swinfo.sw)
        #newcontact.save()
        contacts = Contacts(sw=swinfo.sw)
    if request.method == "POST" and "contacts" in request.POST:
        contacts_form = ContactsForm(request.POST, instance=contacts)
        if contacts_form.is_valid():
            contacts_form.save()
    else:
        contacts_form = ContactsForm(instance=contacts)
    try:
        switch = Map.objects.get(sw=swinfo.sw)
        if switch.stupid:
            if request.method == "POST" and "switch" in request.POST:
                switch_form = StupidMapForm(request.POST, instance=switch,parent_id=swinfo.parent,sw_id=swinfo.sw)
                if switch_form.is_valid():
                    switch_form.save()
            switch_form = StupidMapForm(instance=switch,parent_id=swinfo.parent,sw_id=swinfo.sw)
        else:
            if request.method == "POST" and "switch" in request.POST:
                switch_form = SmartMapForm(request.POST, instance=switch)
                if switch_form.is_valid():
                    switch_form.save()
            switch_form = SmartMapForm(instance=switch)
    except Map.DoesNotExist:
        switch_form = "Something strange is going there, report to site administrator via email"
    return render_to_response('swedit.html',{'switch':swinfo,'contacts_form':contacts_form,'switch_form':switch_form})
def comments(request,offset):
    comments = ''
    try:
        comments = Comments.objects.filter(switch=offset).order_by('-time')
    except:
        pass
    return render_to_response('comments.html',{'request':request,'comments':comments,'swid':offset})
def comment_add(request,offset):
    comment_form = ''
    swid = offset
    comment = Comments(switch=str(swid), ip=str(request.META['REMOTE_ADDR']))
    if request.method == "POST":
        comment_form = CommentsForm(request.POST, instance=comment)
        if comment_form.is_valid():
            comment_form.save()
            return redirect('/switch-'+str(swid)+"/comments/")
    else:
        comment_form = CommentsForm()
    return render_to_response('comment_add.html',{'swid':swid,'comment_form':comment_form})
def comment_delete(request,switch,comment):
    try:
        comment = Comments(id=comment)
        comment.delete()
        return redirect('/switch-'+str(switch)+"/comments/")
    except:
        return render_to_response('hui.html')
def comment_edit(request, switch, comment):
    commid = comment
    swid = switch;
    comment = get_object_or_404(Comments, id=commid)
    if request.method == "POST":
        comment_form = CommentsForm(request.POST, instance = comment)
        if comment_form.is_valid():
            comment_form.save()
            return redirect('/switch-'+str(swid)+"/comments/")
        return render_to_response('comment_edit.html',{'swid':switch,'commid':commid,'comment_form':comment_form})
    else:
        comment_form = CommentsForm(instance = comment)
        return render_to_response('comment_edit.html',{'swid':switch,'commid':commid,'comment_form':comment_form})
def ext_map(request):
    return render_to_response('extended.html')
def ext_map_sector(request,offset):
    return render_to_response('extended_sector.html',{'sector':offset})
def faq(request):
    return render_to_response('faq.html')
