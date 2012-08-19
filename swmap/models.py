# -*- coding: utf-8 -*-
from django.db import models
from django.forms import ModelForm,Select,Textarea
from django import forms
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
#re_sector = re.compile('^[ABVGDEJIK]{1,1}$')
validate_sector = RegexValidator('^[ABVGDEJIK]{1,1}$',u'Неправильно указано название сектора, это должна быть латинская буква A, B, V, G, D, E или J')
validate_sector_ru = RegexValidator(u'^[АБВГДЕЖ]{1,1}$',u'Неправильно указано название сектора, это должна быть русская буква А, Б, В, Г, Д или Ж')
validate_swname = RegexValidator('^[a-zA-Z0-9]*$',u'Неправильно указано название свитча, оно может состоять из латинских букв в любом регистре и цифр')
validate_model = RegexValidator('^[a-zA-Z0-9 -/]*$',u'Неправильно указана модель свитча, это значение может состоять из латинских букв (в любом регистре), цифр, пробелов и символов "-", "/", "\\"')
validate_room = RegexValidator('^[0-9]{3,4}$',u'Неправильно указан номер комнаты , он может состоять из 3х или 4х цифр')
validate_name = RegexValidator(u'^[A-ZА-Я][a-zA-ZА-ЯЁа-яё \-\.]*$',u'Неправильно указано имя/фамилия/отчество, оно должно начинаться с большой буквы, и может состоять из русских и латинских букв в любом регистре, пробелов, и символов "." и "-"')
validate_comments_name = validate_name
validate_phone = RegexValidator('^\+7[0-9]{10}$',u'Неправильно указан телефон, он должен иметь формат +79991234567, скобочки, тире и пробелы не допускаются')
validate_username = RegexValidator('^[a-z]{1,1}[a-z0-9_-]{3,}$',u'Неправильно указано имя пользователя, выдержка из signup.local:  Это имя должно состоять из строчных латинских букв, цифр и подчёркиваний, быть не короче 4 символов и начинаться с буквы.')
validate_hostname = RegexValidator('^[a-z0-9-]{3,}$',u'Имя хоста может состоять из латинских букв, в нижнем регистре, цифр и тире. Должно быть указано как минимум 3 символа.')
validate_ip = RegexValidator("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",u'Неправильный формат ip-адреса. Пример: 127.0.0.1')
validate_mac = RegexValidator('([a-fA-F0-9]{2}[:]?){6}',u'Неправильный формат mac-адреса. Пример: 9e:ed:34:5d:30:34')
validate_port = RegexValidator('^[1-9][0-9]{0,1}$',u'Номер порта - это 1 или 2 цифры. Номер порта не может начинаться с нуля')
def ports_number():
    choices = ((2,2),)
    for i in [5,8,12,16,20,22,24,26,28,44,48]:
        choices = choices+((i,str(i)),)
    return choices
class Map(models.Model):
    sw = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=50,blank=False,validators=[validate_swname],verbose_name="Имя свитча на карте")
    stupid = models.IntegerField(blank=False)
    model = models.CharField(max_length=50,blank=True,validators=[validate_model],verbose_name="Модель")
    sector = models.CharField(max_length=2,blank=False,validators=[validate_sector],verbose_name="Сектор")
    room = models.PositiveIntegerField(blank=False,validators=[validate_room],verbose_name="Комната")
    side = models.CharField(max_length=2,blank=True,choices=(('l','left'),('r','right')),verbose_name="Левая/правая")
    parent = models.PositiveIntegerField(blank=False,verbose_name="Аплинк из")
    parent_port = models.PositiveIntegerField(blank=False,verbose_name="Даунлинк до этого свитча включен в порт")
    ports_count = models.PositiveIntegerField(blank=True,null=True,choices=ports_number(),verbose_name="Количество портов")
    uplink_port = models.PositiveIntegerField(blank=True,verbose_name="Аплинк включен в порт")
    ip = models.CharField(max_length=30,blank=True,verbose_name="IP")
    updated = models.CharField(max_length=50,blank=True,verbose_name="Обновлен")
    deleted = models.PositiveIntegerField(blank=False)
    class Meta:
        db_table = 'map'
class Comments(models.Model):
    switch = models.PositiveIntegerField(blank=False)
    name = models.CharField(max_length=50,blank=False,validators=[validate_comments_name])
    ip = models.IPAddressField(blank=True)
    comment = models.CharField(max_length=500,blank=False)
    time = models.CharField(max_length=50,blank=True, null=True)
    class Meta:
        db_table = 'comments'
        ordering = ["-time"]
class CommentsForm(ModelForm):
    #comment = forms.CharField(widget=forms.Textarea,required=True)
    class Meta:
        model = Comments
        exclude = ('switch','ip','time',)
        widgets = {
            'comment': Textarea(attrs={'cols': 80, 'rows': 20}),
        }
def swchoise():
    switches = Map.objects.filter(stupid=0, deleted=0).order_by("name")
    choices = ((switches[0].sw,switches[0].name),)
    for switch in switches:
        if switch == switches[0]:
            pass
        else:
            choices = choices+((switch.sw,switch.name),)
    return choices
class Clients(models.Model):
    #id = models.PositiveIntegerField(primary_key=True)
    sw = models.PositiveIntegerField()
    username = models.CharField(max_length=50,blank=True,verbose_name="Имя компьютера",validators=[validate_hostname])
    sector = models.CharField(max_length=2,blank=True,verbose_name="Сектор",validators=[validate_sector_ru])
    room = models.CharField(max_length=10,blank=True,verbose_name="Комната",validators=[validate_room])
    ip = models.CharField(max_length=30,blank=True,verbose_name="IP",validators=[validate_ip])
    mac = models.CharField(max_length=60,blank=True,verbose_name="MAC",validators=[validate_mac])
    port = models.PositiveIntegerField(verbose_name="Порт")
    last_seen = models.PositiveIntegerField(verbose_name="Был в сети")
    class Meta:
        db_table = 'clients'
        ordering = ["-last_seen"]
class ClientsSearchForm(ModelForm):
    class Meta:
        model = Clients
        fields = ('username','sector','room','ip','mac',)
class Current(models.Model):
    sw = models.PositiveIntegerField()
    port = models.PositiveIntegerField()
    port_state = models.IntegerField()
    updated = models.CharField(max_length=100)
    class Meta:
        db_table = 'current'
class Contacts(models.Model):
    sw = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100,blank=True,validators=[validate_name],verbose_name="Имя")
    last_name = models.CharField(max_length=100,blank=True,validators=[validate_name],verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100,blank=True,validators=[validate_name],verbose_name="Отчество")
    age = models.CharField(max_length=20,blank=True,verbose_name="Возраст")
    gender = models.CharField(max_length=2,blank=True,choices=(('m','Male'),('f','Female')),verbose_name="Пол")
    phone = models.CharField(max_length=30,blank=True,validators=[validate_phone],verbose_name="Телефон")
    profile = models.CharField(max_length=50,blank=True,validators=[validate_username],verbose_name="Профиль в lithium")
    comment = models.CharField(max_length=500,blank=True,verbose_name="Комментарий")
    class Meta:
        db_table = 'contacts'
class ContactsForm(ModelForm):
    #comment = forms.CharField(widget=forms.Textarea,required=False)
    class Meta:
        model = Contacts
        exclude = ('sw',)
        widgets = {
            'comment': Textarea(attrs={'cols': 50, 'rows': 10}),
        }
def ports_choise(swid=0,includeempty=1):
    ports_count = 0
    if swid == 0:
        ports_count = 48
    else:
        switch = Map.objects.get(sw=swid)
        if switch.ports_count:
            ports_count = int(switch.ports_count)
        else:
            ports_count = 0
    if includeempty:
        choices = (('','---------'),)
        for i in range(1,ports_count+1):
            choices = choices+((i,i),)
        return choices
    else:
        choices = ((1,u'1'),)
        for i in range(2,ports_count+1):
            choices = choices+((i,str(i)),)
        return choices
class Reserves(models.Model):
    sw1 = models.PositiveIntegerField(blank=False,choices=swchoise(),verbose_name="Свитч #1")
    sw1_port = models.PositiveIntegerField(blank=True,null=True,choices=ports_choise(0,0),verbose_name="Порт в свитче #1")
    sw2 = models.PositiveIntegerField(blank=False,choices=swchoise(),verbose_name="Свитч #2")
    sw2_port = models.PositiveIntegerField(blank=True,null=True,choices=ports_choise(0,0),verbose_name="Порт в свитче #2")
    deleted = models.PositiveIntegerField()
    class Meta:
        db_table = 'reserves'
class ReservesForm(ModelForm):
    class Meta:
        model = Reserves
        exclude = ('deleted',)
class StupidMapForm(ModelForm):
    parent = forms.CharField(max_length=12,widget=forms.Select(choices=swchoise()),required=False)
    def __init__(self, *args, **kwargs):
        sw_id = kwargs.pop('sw_id')
        parent_id = kwargs.pop('parent_id')
        super(StupidMapForm, self).__init__(*args, **kwargs)
        self.fields['parent_port'].widget = forms.Select(choices=ports_choise(parent_id))
        self.fields['parent_port'].required = False
        self.fields['uplink_port'].widget = forms.Select(choices=ports_choise(sw_id))
        self.fields['uplink_port'].required = False
    class Meta:
        model = Map
        exclude = ("sw","stupid","ip","updated","deleted",)
class AddStupidMapForm(ModelForm):
    parent = forms.CharField(max_length=12,widget=forms.Select(choices=swchoise()),required=False)
    def __init__(self, *args, **kwargs):
        #sw_id = kwargs.pop('sw_id')
        #parent_id = kwargs.pop('parent_id')
        super(AddStupidMapForm, self).__init__(*args, **kwargs)
        self.fields['parent_port'].widget = forms.Select(choices=ports_choise(0))
        self.fields['parent_port'].required = False
        self.fields['uplink_port'].widget = forms.Select(choices=ports_choise(0))
        self.fields['uplink_port'].required = False
    class Meta:
        model = Map
        exclude = ("sw","stupid","ip","updated","deleted",)
class SmartMapForm(ModelForm):
    #side = forms.CharField(max_length=2,widget=forms.Select(choices=(('l','left'),('r','right'))),required=False)
    class Meta:
        model = Map
        fields = ('side',)
