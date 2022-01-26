import datetime as dt


def year(request):
    today = dt.date.today()
    return {
        'year': today.year
    }
