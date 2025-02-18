import os
from faker import Faker
from OFR2 import app  # Import the Flask app instance
from models.models import db, Client
from datetime import date, timedelta
import random

fake = Faker()

def create_fake_clients(num_clients):
    with app.app_context(): # Need app context to work with db
        db.create_all() # Ensure tables are created

        for _ in range(num_clients):
            name = fake.first_name()
            surname = fake.last_name()
            email = fake.email()
            phone = fake.phone_number()
            address = fake.address()
            notes = fake.text()
            last_dive_day = fake.date_between(start_date='-5y', end_date='today')
            certification_number = fake.bothify(text='CERT-????-####')
            certification_level = random.choice(['Open Water Diver', 'Advanced Open Water', 'Rescue Diver', 'Divemaster', 'Instructor'])
            nitrox_certification_number = fake.bothify(text='NITROX-####')
            weights_amount = random.randint(2, 12)
            mask_size = random.choice(['adult', 'kid', None])
            bcd_size = random.choice(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', None])
            wetsuit_size = random.choice(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', None])
            fins_size = random.choice(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', None])

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
                nitrox_certification_number=nitrox_certification_number,
                weights_amount=weights_amount,
                mask_size=mask_size,
                bcd_size=bcd_size,
                wetsuit_size=wetsuit_size,
                fins_size=fins_size
            )
            db.session.add(new_client)

        db.session.commit()
        print(f"Successfully added {num_clients} fictional clients to the database.")

if __name__ == "__main__":
    num_clients_to_create = 100 # Define the number of clients to create here
    create_fake_clients(num_clients_to_create)