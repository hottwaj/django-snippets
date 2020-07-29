# django-snippets

Django app containing a few useful snippets and tools for reducing boilerplate code:

- For Django Admin:
  - a mixin that allows format strings to be used for list_display e.g.
    `list_display = ('id', ('amount', '{:.2f} EUR'), ('interest', '{:.2%}'))`
  - a PercentField that stores percentages on 0-1 scale but displays them in admin as 0-100% with a '%' suffix 
  - tweaks for inputs that display a given prefix/suffix (e.g. '%' or 'GBP')
  - a method for automatically generating most admin model classes, using mixins on models where necessary to overide features
  - a Next/Previous button for viewing models (use NextPreviousMixin in your model base classes)

- For Django Models:
  - a "at least one not null" Mixin for model clean form
  - an AddedByMixin
  - a UniqueNameModel
  
- urls:
  - model instance to admin changeform url 
  
- widgets:
  - read only value/foreign key widgets
  
- forms:
  - workaround for ensuring "extra" fields on a ModelForm are preserved in "initial" when using modelformset_factory
  


