from datetime import time
from faker import Faker
from app.models.models import TripClass, Place, Client
import random
from datetime import datetime

fake = Faker()

def populate_trip_classes(db):
    """Populate TripClass table with initial debug data if empty"""
    if TripClass.query.first() is None:
        trip_classes = [
            TripClass(name='AM 2Tank', start_time=time(7, 45)),
            TripClass(name='PM 2Tank', start_time=time(13, 0)),
            TripClass(name='Night Dive', start_time=time(18, 30)),
            TripClass(name='StingrayCity', start_time=time(9, 0))
        ]
        
        for trip_class in trip_classes:
            db.session.add(trip_class)
        
        print("Debug data added: Trip Classes")
        return True
    return False

def populate_places(db):
    """Populate Place table with initial debug data if empty"""
    if Place.query.first() is None:
        places = [
            Place(name='GunBay Diver', is_boat=True, description='48ft Newton Dive Special'),
            Place(name='HalfMoon Diver', is_boat=True, description='36ft Island Hopper'),
            Place(name='TopCat', is_boat=False, description='Shore diving site with easy entry'),
            Place(name='Pelican', is_boat=False, description='Popular shore diving location')
        ]
        
        for place in places:
            db.session.add(place)
            
        print("Debug data added: Places")
        return True
    return False

def add_specific_clients(db):
    """Add specific real clients"""
    specific_clients = [
        {
            'name': 'Guillermo',
            'surname': 'Cervero',
            'email': 'cervee18@gmail.com',
            'certification_level': 'Instructor',
            'nitrox_certification_number': 'NITROX-1234'
        },
        {
            'name': 'Amanda',
            'surname': 'Dornelas',
            'email': 'amandahc@hotmail.com',
            'certification_level': 'Instructor',
            'nitrox_certification_number': 'NITROX-5678'
        }
    ]

    data_added = False
    for client_data in specific_clients:
        # Check if client already exists
        existing_client = Client.query.filter_by(email=client_data['email']).first()
        if not existing_client:
            new_client = Client(
                name=client_data['name'],
                surname=client_data['surname'],
                email=client_data['email'],
                certification_level=client_data['certification_level'],
                nitrox_certification_number=client_data['nitrox_certification_number'],
                certification_number=fake.bothify(text='CERT-????-####'),
                last_dive_day=datetime.now().date()
            )
            db.session.add(new_client)
            data_added = True

    if data_added:
        print("Added specific clients: Guillermo Cervero and Amanda Dornelas")
    return data_added

def create_fake_clients(db, num_clients):
    """Create specified number of fake clients"""
    if Client.query.first() is None:  # Only populate if no clients exist
        for _ in range(num_clients):
            name = fake.first_name()
            surname = fake.last_name()
            email = fake.email()
            phone = fake.phone_number()
            address = fake.address()
            notes = fake.text()
            last_dive_day = fake.date_between(start_date='-5y', end_date='today')
            certification_number = fake.bothify(text='CERT-????-####')
            certification_level = random.choice([
                'Open Water Diver', 
                'Advanced Open Water', 
                'Rescue Diver', 
                'Divemaster', 
                'Instructor'
            ])
            nitrox_certification_number = fake.bothify(text='NITROX-####') if random.choice([True, False]) else None

            new_client = Client(
                name=name,
                surname=surname,
                email=email,
                phone=phone,
                address=address,
                notes=notes,
                last_dive_day=last_dive_day,
                certification_number=certification_number,
                certification_level=certification_level,
                nitrox_certification_number=nitrox_certification_number
            )
            db.session.add(new_client)

        print(f"Debug data added: {num_clients} fake clients")
        return True
    return False

def populate_staff(db):
    """Populate Staff table with initial debug data if empty"""
    from app.models.models import Staff
    
    if Staff.query.first() is None:
        staff_members = [
            {"name": "John", "surname": "Smith", "initials": "JS"},
            {"name": "Emma", "surname": "Johnson", "initials": "EJ"},
            {"name": "Michael", "surname": "Davis", "initials": "MD"},
            {"name": "Laura", "surname": "Wilson", "initials": "LW"},
            {"name": "Robert", "surname": "Brown", "initials": "RB"},
            {"name": "Sarah", "surname": "Miller", "initials": "SM"},
        ]
        
        for staff_data in staff_members:
            staff = Staff(
                staff_name=staff_data["name"],
                staff_surname=staff_data["surname"],
                staff_initials=staff_data["initials"]
            )
            db.session.add(staff)
        
        print("Debug data added: Staff Members")
        return True
    return False

def create_fake_staff(db, num_staff):
    """Create specified number of fake staff members"""
    from app.models.models import Staff
    import random
    from faker import Faker
    fake = Faker()
    
    data_added = False
    for _ in range(num_staff):
        name = fake.first_name()
        surname = fake.last_name()
        # Generate initials from the first letter of first name and last name
        initials = f"{name[0]}{surname[0]}"
        
        # Check if initials already exist, append a number if they do
        existing_initials = [s.staff_initials for s in Staff.query.all()]
        if initials in existing_initials:
            initials = f"{initials}{random.randint(1, 9)}"
        
        staff = Staff(
            staff_name=name,
            staff_surname=surname,
            staff_initials=initials
        )
        db.session.add(staff)
        data_added = True
    
    if data_added:
        print(f"Debug data added: {num_staff} fake staff members")
    
    return data_added

def populate_debug_data(db, num_clients=100, num_staff=10):
    """
    Main function to populate all tables with debug data if they are empty
    Returns True if any data was added, False if all tables were already populated
    """
    data_added = False
    
    try:
        # Try to populate each table
        data_added |= populate_trip_classes(db)
        data_added |= populate_places(db)
        data_added |= populate_staff(db)  # Add predefined staff
        data_added |= create_fake_staff(db, num_staff)  # Add random staff
        data_added |= create_fake_clients(db, num_clients)
        
        # Always try to add specific clients
        data_added |= add_specific_clients(db)
        
        if data_added:
            db.session.commit()
            print("All debug data committed successfully")
        else:
            print("No debug data added - tables already contained data")
            
    except Exception as e:
        db.session.rollback()
        print(f"Error adding debug data: {str(e)}")
        raise

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        populate_debug_data(db)