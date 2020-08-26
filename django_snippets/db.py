from django.db.transaction import get_autocommit

def in_db_transaction(using = None):
    # returns True when in a DB transaction. see:
    # https://code.djangoproject.com/ticket/21004
    # https://stackoverflow.com/questions/36686867/check-for-atomic-context
    # https://docs.djangoproject.com/en/3.1/topics/db/transactions/#django.db.transaction.get_autocommit
    return not get_autocommit(using)