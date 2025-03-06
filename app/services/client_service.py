from app.models.models import Client, Visit, Trip, clients_trips_association
from app import db
from sqlalchemy import and_

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
            
            # Get trips related to this visit that the client is participating in
            client_trips = [trip for trip in visit.trips if client in trip.clients]
            
            # Sort trips by date and time
            client_trips.sort(key=lambda trip: (trip.date, trip.start_time or "00:00"))
            
            visits_data.append({
                'visit': visit,
                'leader_client': leader_client,
                'other_clients': other_clients,
                'trips': client_trips
            })
            
    return visits_data