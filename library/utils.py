from django.conf import settings


def get_borrow_period_days():
    return getattr(settings, 'LIBRARY_BORROW_PERIOD_DAYS', 14)


def get_max_borrow_limit():
    return getattr(settings, 'LIBRARY_MAX_BORROW_LIMIT', 5)


def get_fine_config():
    return {
        'free_days': getattr(settings, 'LIBRARY_FINE_FREE_DAYS', 7),
        'initial_rate': getattr(settings, 'LIBRARY_FINE_INITIAL_RATE', 5),
        'late_rate': getattr(settings, 'LIBRARY_FINE_LATE_RATE', 10),
    }


def format_currency(amount):
    return f"₹{amount:.2f}"


def validate_isbn(isbn):
    cleaned = isbn.replace('-', '').replace(' ', '')
    if len(cleaned) not in (10, 13):
        return False
    return cleaned.isdigit()
