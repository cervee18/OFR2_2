from app.models.models import TripClientEquipment, Trip, Client, clients_trips_association
from app import db
from datetime import datetime

def get_last_equipment(client_id):
    """Get the most recent equipment used by a client"""
    return TripClientEquipment.query\
        .filter_by(client_id=client_id)\
        .order_by(TripClientEquipment.updated_at.desc())\
        .first()

def create_equipment_for_trip(trip_id, client_id):
    """Create new equipment assignment based on client's last used equipment"""
    last_equipment = get_last_equipment(client_id)
    
    new_equipment = TripClientEquipment(
        trip_id=trip_id,
        client_id=client_id,
        mask_size=last_equipment.mask_size if last_equipment else None,
        bcd_size=last_equipment.bcd_size if last_equipment else None,
        wetsuit_size=last_equipment.wetsuit_size if last_equipment else None,
        fins_size=last_equipment.fins_size if last_equipment else None,
        weights_amount=last_equipment.weights_amount if last_equipment else None
    )
    
    return new_equipment

def update_future_equipment(client_id, current_date, equipment_data):
    """Update equipment for all future trips of a client"""
    client_future_trips = db.session.query(Trip).join(
        clients_trips_association,
        Trip.id == clients_trips_association.c.trip_id
    ).filter(
        clients_trips_association.c.client_id == client_id,
        Trip.date > current_date
    ).all()
    
    for future_trip in client_future_trips:
        future_equipment = TripClientEquipment.query.filter_by(
            trip_id=future_trip.id,
            client_id=client_id
        ).first()
        
        if not future_equipment:
            future_equipment = TripClientEquipment(
                trip_id=future_trip.id,
                client_id=client_id
            )
            db.session.add(future_equipment)
        
        # Copy only equipment fields (not notes)
        future_equipment.mask_size = equipment_data.get('mask_size')
        future_equipment.bcd_size = equipment_data.get('bcd_size')
        future_equipment.wetsuit_size = equipment_data.get('wetsuit_size')
        future_equipment.fins_size = equipment_data.get('fins_size')
        future_equipment.weights_amount = equipment_data.get('weights_amount')
        future_equipment.updated_at = datetime.utcnow()