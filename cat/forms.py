from django import forms
from django.forms.widgets import PasswordInput
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from DBManagement.models import *

