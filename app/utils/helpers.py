import calendar
from datetime import date

def get_calendar_data():
    """Get calendar data for current month/year"""
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    months = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    years = list(range(current_year - 2, current_year + 3))
    
    return {
        'today': today,
        'current_month': current_month,
        'current_year': current_year,
        'months': months,
        'years': years,
        'calendar': calendar
    }