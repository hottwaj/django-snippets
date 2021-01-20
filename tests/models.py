from django_snippets.models import *
from django_snippets.status_models import *
from django_snippets.enum_models import *

from django.db.models import IntegerField


class NamedCompany(UniqueNameModel): pass

class ObjectWithStatus(ObservedModel, UniqueNameModel): pass

class StatusTestModel(StatusModel):
    OBSERVED_MODEL = ObjectWithStatus
    
    status_value = IntegerField()
    
class PizzaBase(UniqueNameModel, EnumModel): 
    class EnumInstances:
        WHITE = 'No tomato'
        RED = 'No cheese'
        STANDARD = 'Tomato+Cheese'
        
class ChessPiece(UniqueNameModel, EnumModel): 
    points = IntegerField()
    
    class EnumInstances:
        PAWN = {'name': 'Pawn', 'points': 1}
        KNIGHT = {'name': 'Knight', 'points': 3}
        QUEEN = {'name': 'Queend', 'points': 9}