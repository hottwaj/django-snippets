from django.test import TestCase
from django.db import IntegrityError, transaction as db_transaction

import datetime

from .models import *

from django.db.models import Q

class StatusModelsTestCase(TestCase):
    models = [ObjectWithStatus, TestStatusModel]
    
    def get_or_create_obj_w_status(self, name):
        obj, created = ObjectWithStatus.objects.get_or_create(name = name)
        return obj

    @property
    def base_obj(self):
        return self.get_or_create_obj_w_status('Test Intermediary')
    
    def add_initial_status(self):
        status = TestStatusModel(observed_obj = self.base_obj,
                             applies_from = datetime.date(2020, 1, 1),
                             applies_to = None,
                             status_value = 10)
        
        TestStatusModel.add_status(status)
        return status
    
    def test_add_initial_status(self):
        status = self.add_initial_status()
        self.assertIsNotNone(status.pk)
        self.assertEqual(self.base_obj.current_status.pk, status.pk)
        self.assertEqual(TestStatusModel.objects.count(), 1)
        
    def test_add_status_with_not_null_to_date_fails(self):
        status = TestStatusModel(observed_obj = self.base_obj,
                             applies_from = datetime.date(2020, 1, 1),
                             applies_to = datetime.date(2020, 1, 5),
                             status_value = 10)
        
        with self.assertRaises(StatusCreationError):
            TestStatusModel.add_status(status)
            
        self.assertEqual(TestStatusModel.objects.count(), 0)
            
    def add_initial_and_subsequent_status(self, subsequent_status_days_gap = 31):
        status_1 = self.add_initial_status()
        
        status_2 = TestStatusModel(observed_obj = self.base_obj,
                               applies_from = status_1.applies_from + datetime.timedelta(days = subsequent_status_days_gap),
                               applies_to = None,
                               status_value = 20)
        
        TestStatusModel.add_status(status_2)
        status_1 = TestStatusModel.objects.get(pk = status_1.pk) # re-fetch
        return status_1, status_2
        
    def test_add_subsequent_status(self):
        status_1, status_2 = self.add_initial_and_subsequent_status()
        
        self.assertIsNotNone(status_2.pk)
        self.assertEqual(self.base_obj.current_status.pk, status_2.pk)
        self.assertEqual(TestStatusModel.objects.count(), 2)
        self.assertEqual(status_1.applies_to, status_2.applies_from)
        
    def test_overwrite_first_status(self):
        status_1 = self.add_initial_status()
        
        status_2 = TestStatusModel(observed_obj = self.base_obj,
                               applies_from = status_1.applies_from,
                               applies_to = None,
                               status_value = 20)
        
        TestStatusModel.add_status(status_2)
        
        self.assertIsNotNone(status_2.pk)
        self.assertEqual(self.base_obj.current_status.pk, status_2.pk)
        self.assertEqual(TestStatusModel.objects.count(), 1)
        with self.assertRaises(TestStatusModel.DoesNotExist):
            TestStatusModel.objects.get(pk = status_1.pk)
            
    def test_splitting_terminated_status_fails(self):
        status_1, status_2 = self.add_initial_and_subsequent_status()
        
        status_3 = TestStatusModel(observed_obj = self.base_obj,
                               applies_from = datetime.date(2020, 1, 10),
                               applies_to = None,
                               status_value = 30)
        
        with self.assertRaises(StatusCreationError):
            TestStatusModel.add_status(status_3)
        
        self.assertIsNotNone(status_2.pk)
        self.assertEqual(self.base_obj.current_status.pk, status_2.pk)
        self.assertEqual(set(TestStatusModel.objects.values_list('pk', flat=True)), 
                         set([status_1.pk, status_2.pk]))
        
    def test_adding_prior_status_fails(self):
        status_1 = self.add_initial_status()
        
        status_2 = TestStatusModel(observed_obj = self.base_obj,
                               applies_from = datetime.date(2019, 1, 1),
                               applies_to = None,
                               status_value = 20)
        
        with db_transaction.atomic():
            with self.assertRaises(IntegrityError):
                TestStatusModel.add_status(status_2)
        
        self.assertIsNone(status_2.pk)
        self.assertEqual(self.base_obj.current_status.pk, status_1.pk)
        self.assertEqual(TestStatusModel.objects.count(), 1)
        
    def test_retrieve_status(self):
        status_1, status_2 = self.add_initial_and_subsequent_status()
        base_obj = self.base_obj
        
        self.assertEqual(status_1,
                         base_obj.get_status_as_of(status_1.applies_from))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_1.applies_to))
        self.assertEqual(status_1,
                         base_obj.get_status_as_of(status_1.applies_to - datetime.timedelta(days=1)))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_2.applies_from))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_2.applies_from + datetime.timedelta(days=3650)))
        
        with self.assertRaises(TestStatusModel.DoesNotExist):
            base_obj.get_status_as_of(status_1.applies_from - datetime.timedelta(days=1))
            
    def test_retrieve_status_one_day_gap(self):
        status_1, status_2 = self.add_initial_and_subsequent_status(subsequent_status_days_gap = 1)
        base_obj = self.base_obj
        
        self.assertEqual(status_1,
                         base_obj.get_status_as_of(status_1.applies_from))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_1.applies_to))
        self.assertEqual(status_1,
                         base_obj.get_status_as_of(status_1.applies_to - datetime.timedelta(days=1)))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_2.applies_from))
        self.assertEqual(status_2,
                         base_obj.get_status_as_of(status_2.applies_from + datetime.timedelta(days=3650)))
        
        with self.assertRaises(TestStatusModel.DoesNotExist):
            base_obj.get_status_as_of(status_1.applies_from - datetime.timedelta(days=1))