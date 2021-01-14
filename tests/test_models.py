from django.test import TestCase

from .models import *

from django.db import IntegrityError
    
class UniqueNameModelTests(TestCase):
    def test_creation(self):
        acme = NamedCompany(name = 'ACME')
        acme.save()
        self.assertIsNotNone(acme.pk)
        return acme
        
    def test_unique_constraint(self):
        self.test_creation()
        with self.assertRaises(IntegrityError):
            self.test_creation()
            
    def test_get_by_natural_key(self):
        acme = self.test_creation()
        acme_copy = NamedCompany.objects.get_by_natural_key('ACME')
        self.assertEqual(acme, acme_copy)