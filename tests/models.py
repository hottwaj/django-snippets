from django_snippets.models import *
from django_snippets.status_models import *

from django.db.models import IntegerField


class NamedCompany(UniqueNameModel): pass

class ObjectWithStatus(ObservedModel, UniqueNameModel): pass

class TestStatusModel(*DefaultModelBases, StatusModel):
    OBSERVED_MODEL = ObjectWithStatus
    
    status_value = IntegerField()