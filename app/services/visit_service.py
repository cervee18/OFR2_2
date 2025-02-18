from app.models.models import Visit, Client
from app import db
from datetime import datetime

def check_for_overlapping_visits(client_ids, start_date, end_date, current_visit_id=None):
    """
    Check if any clients have overlapping visits for the given date range
    Returns tuple (overlapping_found, message)
    """
    for client_id in client_ids:
        client = Client.query.get(client_id)
        if not client:
            continue
            
        for visit in client.visits:
            # Skip current visit when checking for overlaps
            if visit.id == current_visit_id:
                continue
                
            if (start_date <= visit.end_date) and (end_date >= visit.start_date):
                message = f"Visit for client {client.name} {client.surname} " \
                          f"overlaps with an existing visit from {visit.start_date} " \
                          f"to {visit.end_date}."
                return True, message
                
    return False, None