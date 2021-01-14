from django.test import TestCase
from django.db import transaction as db_transaction

from django_snippets.models import get_package_models
from django_snippets.enum_models import EnumModel

from . import models as test_models
    
class EnumModelsNoDataTestCase(TestCase):
    def test_enum_instance_access_when_doesnotexist(self):
        with self.assertRaises(test_models.PizzaBase.DoesNotExist):
            s = test_models.PizzaBase.STANDARD
            
class EnumModelsTestCase(TestCase):
    
    def test_insert_enum_instances(self):
        created_count = test_models.PizzaBase.insert_enum_instances()
        self.assertEqual(created_count, 3)
        
    def test_enum_instance_access(self):
        self.test_insert_enum_instances()
        s = test_models.PizzaBase.STANDARD
        self.assertIsNotNone(s.pk)
        
    def test_multifield_enum_instance_access(self):
        test_models.ChessPiece.insert_enum_instances()
        k = test_models.ChessPiece.KNIGHT
        self.assertIsNotNone(k.pk)
        self.assertEqual(k.points, 3)
        
    def test_create_package_model_instances(self):
        created_count = EnumModel.create_package_model_instances(test_models)
        self.assertEqual(created_count, 6)
        
    def test_enum_models(self):
        self.test_create_package_model_instances()
        
        for model_cls in get_package_models(test_models):
            if issubclass(model_cls, EnumModel):
                for obj_name, key in model_cls.get_enum_instances_map().items():
                    count = model_cls.objects.filter(**key).count()
                    self.assertEqual(count, 1)