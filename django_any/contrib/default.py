# -*- coding: utf-8 -*-
from django_any.models import any_model
from django.db.models.fields import NOT_PROVIDED
from inspect import isroutine

def any_model_with_defaults(cls, **attrs):
    """Use model-provided defaults"""

    for field in cls._meta.fields:
        default = field.default
        if default is not NOT_PROVIDED:
            if isroutine(default):
                # for stuff like default=datetime.now
                default = default()
            attrs.setdefault(field.name, default)

    return any_model(cls, **attrs)
