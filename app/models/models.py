from app import db


clients_trips_association = db.Table('clients_trips',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True)
)

# --- New Association Table for Client-Visit (Many-to-Many) ---
client_visits_association = db.Table('client_visits',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('visit_id', db.Integer, db.ForeignKey('visit.id'), primary_key=True)
)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    last_dive_day = db.Column(db.Date)
    certification_number = db.Column(db.String(50))
    certification_level = db.Column(db.String(50))
    nitrox_certification_number = db.Column(db.String(50))
    # --- Many-to-Many Relationship with Visit and Trips ---
    visits = db.relationship('Visit', secondary=client_visits_association)
    trips = db.relationship('Trip', secondary=clients_trips_association, back_populates='clients')
    def __repr__(self):
        return f"<Client {self.name} {self.surname}>"

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    place_of_stay = db.Column(db.String(100))
    leader_client_id = db.Column(db.Integer)
    
    # Add this relationship if it's not already there
    clients = db.relationship('Client', 
                            secondary=client_visits_association,
                            back_populates='visits')

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    trip_class_id = db.Column(db.Integer, db.ForeignKey('trip_class.id'), nullable=False)
    start_time = db.Column(db.Time)  # Can be overridden from the trip class default
    assigned_staff = db.Column(db.Text)  # Store staff IDs as comma-separated values
    max_divers = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))

    # Relationship to TripClass
    trip_class = db.relationship('TripClass', backref='trips', lazy=True)
    
    # Keep existing relationships
    clients = db.relationship('Client',
                            secondary=clients_trips_association,
                            back_populates='trips')
    
    def __repr__(self):
        return f"Trip('{self.name}', '{self.trip_class.name if self.trip_class else 'No Class'}', '{self.date}')"

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, unique=True, nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    staff_surname = db.Column(db.String(100), nullable=False)
    staff_initials = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<Staff {self.staff_name} {self.staff_surname}>"
    
from datetime import datetime

class TripClientEquipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    mask_size = db.Column(db.String(20))
    bcd_size = db.Column(db.String(20))
    wetsuit_size = db.Column(db.String(20))
    fins_size = db.Column(db.String(20))
    weights_amount = db.Column(db.Integer)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trip = db.relationship('Trip', backref='equipment_assignments')
    client = db.relationship('Client', backref='equipment_assignments')

    __table_args__ = (
        db.UniqueConstraint('trip_id', 'client_id', name='unique_trip_client_equipment'),
    )

class TripClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    start_time = db.Column(db.Time, nullable=False)
    
    def __repr__(self):
        return f"TripClass('{self.name}', '{self.start_time}')"
    
class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    is_boat = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text)
    
    # Relationship with trips
    trips = db.relationship('Trip', backref='place', lazy=True)
    
    def __repr__(self):
        place_type = "Boat" if self.is_boat else "Shore"
        return f"Place('{self.name}', Type: {place_type})"