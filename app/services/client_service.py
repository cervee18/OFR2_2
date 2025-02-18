from app.models.models import Client, Visit

def search_clients(search_term):
    """Search for clients by name, surname or email"""
    return Client.query.filter(
        (Client.name.ilike(f"%{search_term}%")) |
        (Client.surname.ilike(f"%{search_term}%")) |
        (Client.email.ilike(f"%{search_term}%"))
    ).all()

def get_client_visits(client):
    """Get all visits for a client with additional data"""
    related_visits = client.visits
    visits_data = []
    
    if related_visits:
        for visit in related_visits:
            leader_client = Client.query.get(visit.leader_client_id)
            other_clients = visit.clients
            
            visits_data.append({
                'visit': visit,
                'leader_client': leader_client,
                'other_clients': other_clients,
            })
            
    return visits_data