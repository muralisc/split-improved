THIS_MONTH = 1
LAST_MONTH = 2
CUSTOM_RANGE = 3
DEFAULT_START_PAGE = 1
DEFAULT_RPP = 5


def global_variables_for_templates(request):
    """
    Put selected settings variables into the default template context
    """
    return {
    'THIS_MONTH': THIS_MONTH,
    'LAST_MONTH': LAST_MONTH,
    'CUSTOM_RANGE': CUSTOM_RANGE,
    }
