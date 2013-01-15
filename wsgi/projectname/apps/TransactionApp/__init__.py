THIS_MONTH = 1
LAST_MONTH = 2
CUSTOM_RANGE = 3
ALL_TIME = 4
TODAY= 5

DEFAULT_START_PAGE = 1
DEFAULT_RPP = 5

# for category model
INCOME = 0
BANK = 1
EXPENSE = 2
CREDIT = 3

# for category model
PRIVATE = 0
PUBLIC = 1


def global_variables_for_templates(request):
    """
    Put selected settings variables into the default template context
    Ensure that these are used only in HTMLs and most of the HTML
    """
    return {
        'CUSTOM_RANGE': CUSTOM_RANGE,
        }
