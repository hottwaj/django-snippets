from __future__ import annotations

from django.db.models import \
    Model, QuerySet, Manager, DateField, ForeignKey, OneToOneField, UniqueConstraint, CheckConstraint, SET_NULL, Q

from django.db import transaction as db_transaction

from contextlib import nullcontext

from django_snippets.models import DefaultModelBases, ForeignKey_CD
from django_snippets.db import in_db_transaction

import datetime

class ObservedModel():
    """Mixin for models that have dynamic status, stored as a separate StatusModel instance.
    
    Note that StatusModel takes care of adding a 'current_status' field to subclasses of ObservedModel"""
    def get_status_as_of(self, status_date: datetime.date) -> StatusModel:
        return self.STATUS_MODEL.objects.get_status_as_of(self, status_date)
    
class StatusCreationError(RuntimeError): pass

from django.db.models.base import ModelBase

# see https://stackoverflow.com/questions/56858765/dynamically-extending-django-models-using-a-metaclass
class StatusModelMetaclass(ModelBase):
    def __new__(cls, name, bases, attrs):
        attrs = {**attrs} # take a copy for safety
        if 'OBSERVED_MODEL' in attrs:
            observed_model = attrs['OBSERVED_MODEL']
            attrs['observed_obj'] = ForeignKey_CD(observed_model, related_name = 'historical_status')

            if 'Meta' not in attrs:
                class Meta: pass
                attrs['Meta'] = Meta
            metacls = attrs['Meta']
            metacls.unique_together = getattr(metacls, 'unique_together', [])
            metacls.unique_together.extend([('observed_obj', 'applies_from'),
                                            ('observed_obj', 'applies_to')])
            
            metacls.constraints = getattr(metacls, 'constraints', [])
            metacls.constraints.extend([
                UniqueConstraint(fields=['observed_obj'], condition=Q(applies_to__isnull=True), name='%(app_label)s_%(class)s_unique_current_status')
            ])
            
            newcls = super().__new__(cls, name, bases, attrs)
            current_status_field = OneToOneField(newcls, on_delete = SET_NULL, related_name = '_observed', null=True, blank=True)
            current_status_field.contribute_to_class(observed_model, 'current_status')
            observed_model.STATUS_MODEL = newcls
            return newcls
        else:
            # OBSERVED_MODEL not present - raise an error if not an abstract model
            if 'Meta' not in attrs or not getattr(attrs['Meta'], 'abstract'):
                raise AttributeError('Subclasses of StatusModel require the attribute "OBSERVED_MODEL" which should point to an observed django Model')
            else:
                return super().__new__(cls, name, bases, attrs)

class StatusModel(Model, metaclass=StatusModelMetaclass):
    applies_from = DateField(help_text = "Status valid from this date")
    applies_to = DateField(help_text = "Status valid up to *day before* this date", null=True, blank=True)

    class Meta:
        abstract = True
        
    @classmethod
    def _filter_queryset_status_as_of(cls, queryset: QuerySet, status_date: datetime.date, status_model_path: str = '') -> QuerySet:
        """Filter queryset to select status objects as of status_date.
        
        Can be used on querysets where the base object is not a subclass of StatusModel, 
        in which case the django model path to the relevant StatusModel subclass should be provided in 'status_model_path'.
        e.g. StatusModel._filter_queryset_status_as_of(queryset = Invoice.objects.all(),
                                                       status_date = selected_date,
                                                       status_object_path = 'historical_status')
        """
        if status_model_path != '':
            status_model_path += '__' # append this to get to fields of status_obj
            
        return queryset.filter(Q(**{status_model_path + 'applies_to__isnull': True})
                               | Q(**{status_model_path + 'applies_to__gt': status_date}),
                               **{status_model_path + 'applies_from__lte': status_date})
    
    @classmethod
    def add_status(cls, new_status: StatusModel):
        """Add a new StatusModel record for an observed object.
        
        Any previously 'current' status (if one exists) is marked as ending the day prior to the new status, and the new status is added with no end date.
        - If the prior status starts on the same day as the new status, the prior status is removed completely.
        
        StatusModel instances for the same observed object can only be added consecutively i.e. we always add a new 'current' status. To enforce this:
        - Statuses with a defined end date are not allowed. (StatusCreationError)
        - Statuses that precede the first existing status are not allowed. (IntegrityError)
        - Statuses that split the from/to dates of an existing status are not allowed. (StatusCreationError)"""
        
        # start or ensure we're in a transaction
        transaction_context = db_transaction.atomic if not in_db_transaction() else nullcontext
        with transaction_context():
            if new_status.applies_to is not None:
                raise StatusCreationError('Inserting a new status with non-blank "applies_to" not yet implemented')

            # get current status applicable
            try:
                prev_status = cls.objects.get_status_as_of(new_status.observed_obj, new_status.applies_from)
            except cls.DoesNotExist as ex:
                # this appears to be the first status for this object
                pass
            else:
                if prev_status.applies_to is not None:
                    raise StatusCreationError('Splitting interval of existing status that has a defined end date by inserting a new status is not yet implemented')

                if prev_status.applies_from == new_status.applies_from:
                    # remove the previous status, as new status needs to start on same date
                    prev_status.delete()
                else:
                    # adjust previous status to end when new status starts
                    prev_status.applies_to = new_status.applies_from
                    prev_status.save()

            new_status.save()
            new_status.observed_obj.current_status = new_status
            new_status.observed_obj.save()

    class StatusModelQueryset(QuerySet):
        def filter_status_as_of(self, status_date: datetime.date) -> QuerySet:
            """Filter this queryset to select status objects as of status_date."""
            return self.model._filter_queryset_status_as_of(self, status_date)

        def get_status_as_of(self, observed_obj: self.model, status_date: datetime.date) -> StatusModel:
            "Get status of observed_obj as of status_date"
            return self.filter_status_as_of(status_date).get(observed_obj = observed_obj)

    objects = StatusModelQueryset.as_manager()