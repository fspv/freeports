# -*- coding: utf-8 -*-
from django.core.context_processors import csrf
from django.http import HttpResponse
from swmap.models import Map, Clients, Current, Contacts, ContactsForm,\
                        StupidMapForm, AddStupidMapForm, SmartMapForm,\
                        Comments, CommentsForm, Reserves, ReservesForm,\
                        ClientsSearchForm
from django.db.models import Q, Max
from time import time
import re
import logging
from django.db import connection
from django.shortcuts import render_to_response,\
                            get_object_or_404, get_list_or_404,\
                            redirect
from tools import parse_get, port_clients
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView


def big_swmap(request):
    """Показывает главную страницу, определенную в шаблоне main.html
    """
    return render_to_response('main.html')


def search(request):
    """Поиск по всем клиентам. В GET запросе возможно 4 вида
    комбинаций параметров.
    Приоритет обработки этих комбинаций:
    1. Имя комьпютера (можно неполное)
    2. Сектор и комната (только если заданы оба значения)
    3. IP-адрес (полностью)
    4. MAC-адрес.
    То есть, если в запросе обнаружились параметры 2 и 3,
    то обработается только 2.
    """
    results = ''
    ind = 1
    if len(request.GET):
        search_form = ClientsSearchForm(request.GET)
        if search_form.is_valid():
            if len(request.GET['username']):
                results = Clients.objects.filter(
                                username__icontains=request.GET['username'])\
                            .order_by('last_seen')
            elif len(request.GET['sector']) and request.GET['room']:
                results = Clients.objects.filter(
                                        sector__iexact=request.GET['sector'],
                                        room=request.GET['room'])
            elif len(request.GET['sector']):
                results = Clients.objects.filter(
                                        sector__iexact=request.GET['sector'])
            elif len(request.GET['ip']):
                results = Clients.objects.filter(ip__exact=request.GET['ip'])
            elif len(request.GET['mac']):
                results = Clients.objects.filter(
                                                mac__iexact=request.GET['mac'])
    else:
        search_form = ClientsSearchForm()
        ind = 0
    template_values = {
                        'search_form':search_form,
                        'results':results,
                        'request':request.GET,
                        'ip':request.META['REMOTE_ADDR']
                    }
    return render_to_response('search.html', template_values)


def switch(request, offset):
    """Показывает информацию о свитче.
    """
    swinfo = get_object_or_404(Map, sw=offset)
    ports = []
    last_seen = parse_get(request)['last_seen']
    registered = parse_get(request)['registered']
    template_values = {'switch':swinfo}
    template_values['registered'] = registered
    template_values['period'] = last_seen
    template_values['request'] = request
    """Для того, чтобы выяснить, из инета пришел человек
    или из локалки и дать ему правильную ссылку на lithium
    передаем шаблону ip-адрес клиента. (должно быть добавлено
    middleware для выделения адреса в случае, если человек за
    прокси
    """
    template_values['ip'] = request.META['REMOTE_ADDR']
    if swinfo.stupid:
        template_values['clients'] = port_clients(swinfo.parent,
                                                swinfo.parent_port,
                                                last_seen,
                                                registered)
        return render_to_response('stupid_switch.html', template_values)
    else:
        for i in range(1, swinfo.ports_count + 1):
            """ Для каждого порта выясняем количество
            клиентов и состояние порта.
            Самое узкое место в коде.
            """
            reg = Clients.objects.filter(
                                        sw=swinfo.sw,
                                        port=i,
                                        last_seen__lt=last_seen,
                                        username__isnull=False).count()
            unreg = Clients.objects.filter(
                                        sw=swinfo.sw,
                                        port=i,
                                        username__isnull=True,
                                        last_seen__lt=last_seen).count()
            try:
                current = Current.objects.get(sw=swinfo.sw, port=i)
                port_state = current.port_state
                updated = current.updated
            except:
                """ Если вдруг по каким-то причинам
                записи в базе не оказалось.
                """
                port_state = 'Unknown'
                updated = time()
            ports.append(
                    {
                        'port':i,
                        'reg':reg,
                        'unreg':unreg,
                        'total':(reg + unreg),
                        'state':port_state,
                        'updated':updated,
                        'uplink':(1 if i == swinfo.uplink_port else 0)
                    }
                )
        template_values['ports'] = ports
        return render_to_response('smart_switch.html', template_values)


def port(request, switch, port):
    """ Показывает клиентов на порту
    """
    swinfo = Map.objects.filter(sw=switch)[0]
    last_seen = parse_get(request)['last_seen']
    registered = parse_get(request)['registered']
    template_values = {
                        'switch':swinfo,
                        'clients':port_clients(switch,
                                            port,
                                            last_seen,
                                            registered),
                        'period':last_seen,
                        'request':request,
                        'port':port,
                        'registered':registered,
                        'ip':request.META['REMOTE_ADDR']
                    }
    if registered == '1':
        return render_to_response('port_reg.html', template_values)
    else:
        return render_to_response('port_unreg.html', template_values)


@login_required
def admin(request):
    """ Главная страница админки
    """
    return render_to_response('admin/main.html')


@login_required
def admin_swlist(request):
    """ Страница со списком тупых свитчей
    """
    switches = Map.objects.filter(stupid='1')
    return render_to_response('admin/swlist.html', {'switches':switches})


@login_required
def admin_swadd(request):
    switch_form = ''
    switch = Map(sw=(Map.objects.all().order_by('-sw')[0].sw + 1))
    switch.stupid = "1"
    switch.deleted = "0"
    if request.method == "POST":
        switch_form = AddStupidMapForm(request.POST, instance=switch)
        if switch_form.is_valid():
            switch_form.save()
            return redirect('/admin/switches/')
    else:
        switch_form = AddStupidMapForm()
    values = {'switch_form':switch_form}
    values.update(csrf(request))
    return render_to_response('admin/swadd.html', values)


@login_required
def admin_swdel(request, switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 1
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')


@login_required
def admin_reservelist(request):
    reserves = Reserves.objects.all()
    return render_to_response('admin/reservelist.html', {'reserves':reserves})


@login_required
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
    values = {'reserve_form':reserve_form}
    values.update(csrf(request))
    return render_to_response('admin/reserveadd.html', values)


@login_required
def admin_swdel(request, switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 1
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')


@login_required
def admin_reservedel(request, reserveid):
    reserve = get_object_or_404(Reserves, id=reserveid)
    try:
        reserve.deleted = 1
        reserve.save()
        #return render_to_response('debug.html')
        return redirect('/admin/reserves/')
    except:
        return render_to_response('hui.html')


@login_required
def admin_reserverestore(request, reserveid):
    reserve = get_object_or_404(Reserves, id=reserveid)
    try:
        reserve.deleted = 0
        reserve.save()
        return redirect('/admin/reserves/')
    except:
        return render_to_response('hui.html')


@login_required
def admin_swrestore(request, switch):
    sw = get_object_or_404(Map, sw=switch)
    try:
        sw.deleted = 0
        sw.save()
        return redirect('/admin/switches/')
    except:
        return render_to_response('hui.html')


def swinfo(request, offset):
    swinfo = Map.objects.filter(sw=offset)[0]
    if swinfo.stupid == 1:
        parent = Map.objects.filter(sw=swinfo.parent)[0]
        swinfo.updated = parent.updated
    check = Contacts.objects.filter(sw=swinfo.sw).count()
    if check:
        contacts = Contacts.objects.filter(sw=swinfo.sw)[0]
    else:
        contacts = {}
    template_values = {}
    template_values['switch'] = swinfo
    template_values['check'] = check
    template_values['contacts'] = contacts
    template_values['ip'] = request.META['REMOTE_ADDR']
    return render_to_response('swinfo.html', template_values)


def swedit(request, offset):
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
                switch_form = StupidMapForm(request.POST,
                                            instance=switch,
                                            parent_id=swinfo.parent,
                                            sw_id=swinfo.sw)
                if switch_form.is_valid():
                    switch_form.save()
            switch_form = StupidMapForm(instance=switch,
                                        parent_id=swinfo.parent,
                                        sw_id=swinfo.sw)
        else:
            if request.method == "POST" and "switch" in request.POST:
                switch_form = SmartMapForm(request.POST, instance=switch)
                if switch_form.is_valid():
                    switch_form.save()
            switch_form = SmartMapForm(instance=switch)
    except Map.DoesNotExist:
        switch_form = """Something strange is going there,
                        report to site administrator via email"""
    values = {
                'switch':swinfo,
                'contacts_form':contacts_form,
                'switch_form':switch_form
            }
    values.update(csrf(request))
    return render_to_response('swedit.html', values)
logger = logging.getLogger(__name__)


class CommentList(ListView):
    """Show all comments for given sw_id"""
    template_name = 'comments.html'

    def get_queryset(self):
        return Comments.objects.filter(switch=self.kwargs['switch_id'])

    def get_context_data(self, **kwargs):
        """Add kwargs to context to pass them to template"""
        context = super(CommentList, self).get_context_data(**kwargs)
        context.update(self.kwargs)
        return context


class CommentAdd(CreateView):
    """Add comment"""
    form_class = CommentsForm
    template_name = 'comment_add.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.ip = self.request.META['REMOTE_ADDR']
        instance.switch = self.kwargs['switch_id']
        instance.save()
        return redirect('/switch-' + str(self.kwargs['switch_id']) + \
                        "/comments/")

    def get_context_data(self, **kwargs):
        """Add kwargs and csrf token to context to pass them to template"""
        context = super(CommentAdd, self).get_context_data(**kwargs)
        context.update(self.kwargs)
        context.update(csrf(self.request))
        return context


class CommentEdit(UpdateView):
    """Edit comment"""
    form_class = CommentsForm
    template_name = 'comment_edit.html'

    def get_success_url(self):
        return "/switch-" + str(self.kwargs['switch_id']) + "/comments/"

    def get_object(self):
        return get_object_or_404(Comments, id=self.kwargs['comment_id'])

    def get_context_data(self, **kwargs):
        """Add kwargs and csrf token to context to pass them to template"""
        context = super(CommentEdit, self).get_context_data(**kwargs)
        context.update(self.kwargs)
        context.update(csrf(self.request))
        return context


class CommentDelete(DeleteView):
    """Delete comment"""
    form_class = CommentsForm
    template_name = 'comment_confirm_delete.html'

    def get_success_url(self):
        return "/switch-" + str(self.kwargs['switch_id']) + "/comments/"

    def get_object(self):
        return get_object_or_404(Comments, id=self.kwargs['comment_id'])

    def get_context_data(self, **kwargs):
        """Add kwargs and csrf token to context to pass them to template"""
        context = super(CommentDelete, self).get_context_data(**kwargs)
        context.update(self.kwargs)
        context.update(csrf(self.request))
        return context


def ext_map(request):
    return render_to_response('extended.html')


def ext_map_sector(request, offset):
    return render_to_response('extended_sector.html', {'sector':offset})
