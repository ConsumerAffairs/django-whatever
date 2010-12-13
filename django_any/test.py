# -*- coding: utf-8 -*-
import time, random
from unittest import TestCase, _strclass
from django import forms
from django_any import any_form
from django.test.client import Client as DjangoClient
from django_any.contrib.auth import any_user
from django.contrib.admin.helpers import AdminForm
from django_any import xunit

def _request_context_forms(context):
    """
    Lookup all stored in context froms instance
    """
    if isinstance(context, list):
        dicts = context[0].dicts
    else:
        dicts = context.dicts

    for context in dicts:
        for _, inst in context.items():
            if isinstance(inst, forms.Form):
                yield inst
            elif isinstance(inst, AdminForm):
                yield inst.form


class Client(DjangoClient):
    def login_as(self, **kwargs):
        password = xunit.any_string()
        user = any_user(password=password, **kwargs)

        if self.login(username=user.username, password=password):
            return user
        raise AssertionError('Can''t login with autogenerated user')

    def post_any_data(self, url, extra=None, context_forms=_request_context_forms, **kwargs):
        request = self.get(url)

        post_data = {}

        #TODO support string and list of strings as forms names in context
        for form in context_forms(request.context):
            form_data, form_files = any_form(form.__class__) #TODO support form instance

            if form.prefix:
                form_data = dict([('%s-%s' % (form.prefix, key), value) for key, value in form_data.items()])

            post_data.update(form_data)

        if extra:
            post_data.update(extra)

        return self.post(url, post_data)


def without_random_seed(func):
    """
    Marks that test method do not need to be started with random seed
    """
    func.__django_any_without_random_seed = True
    return func


def with_seed(seed):
    """
    Marks that test method do not need to be started with specific seed
    """
    def _wrapper(func):
        seeds = getattr(func, '__django_any_with_seed', [])
        seeds.append(seed)
        func.__django_any_with_seed = seeds
        return func
    return _wrapper


def set_seed(func, seed=None):
    """
    Set randon seed before executing function. If seed is 
    not provided current timestamp used
    """
    def _wrapper(self, seed=seed, *args, **kwargs):
        self.__django_any_seed = seed if seed else int(time.time()*1000)
        random.seed(self.__django_any_seed)
        return func(self, *args, **kwargs)
    return _wrapper


class WithTestDataSeed(type):
    """
    Metaclass for TestCases, manages random tests run
    """
    def __new__(cls, cls_name, bases, attrs):
        attrs['__django_any_seed'] = 0

        def shortDescription(self):            
            return "%s (%s) With seed %s" % (self._testMethodName,  _strclass(self.__class__), getattr(self, '__django_any_seed'))

        for name, func in attrs.items():
            if name.startswith('test') and hasattr(func, '__call__'):
                if getattr(func, '__django_any_without_random_seed', False):
                    del attrs[name]
                else:
                    attrs[name] = set_seed(func)

                for seed in getattr(func, '__django_any_with_seed', []):
                    attrs['%s_%d' % (name, seed)] = set_seed(func, seed)
                
        testcase = super(WithTestDataSeed, cls).__new__(cls, cls_name, bases, attrs)
        testcase.shortDescription = shortDescription
        return testcase
    
