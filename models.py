from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
clients_trips_association = db.Table('clients_trips',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True)
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
    weights_amount = db.Column(db.Integer)
    # Modified fields to be nullable and reflect new options
    mask_size = db.Column(db.String(20), nullable=True) # Optional, can be 'adult' or 'kid' or None
    bcd_size = db.Column(db.String(20), nullable=True)  # Optional, size from XXS to XXL or None
    wetsuit_size = db.Column(db.String(20), nullable=True) # Optional, size from XXS to XXL or None
    fins_size = db.Column(db.String(20), nullable=True)   # Optional, size from XXS to XXL or None
    trips = db.relationship('Trip', secondary=clients_trips_association, backref=db.backref('clients', lazy='dynamic'))

    def __repr__(self):
        return f"<Client {self.name} {self.surname}>"

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    place_of_stay = db.Column(db.String(100))
    client_ids = db.Column(db.String(200)) # Storing as comma-separated string for now
    leader_client_id = db.Column(db.Integer)

    def __repr__(self):
        return f"<Visit {self.visit_id}>"

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    trip_class = db.Column(db.String(50)) # New field for trip class
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    max_divers = db.Column(db.Integer)
    needed_staff = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False) # Date when the trip takes place

    def __repr__(self):
        return f"Trip('{self.name}', '{self.trip_class}', '{self.date}')"

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, unique=True, nullable=False) # Same consideration as client_id
    staff_name = db.Column(db.String(100), nullable=False)
    staff_surname = db.Column(db.String(100), nullable=False)
    staff_initials = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<Staff {self.staff_name} {self.staff_surname}>"