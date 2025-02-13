from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Client, Visit, Trip, TripClientEquipment
from datetime import datetime, date
import calendar

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/clients", methods=['GET', 'POST'])
def clients():
    search_term = request.args.get('search')
    clients_list = []

    if search_term:
        clients_list = Client.query.filter(
            (Client.name.ilike(f"%{search_term}%")) |
            (Client.surname.ilike(f"%{search_term}%")) |
            (Client.email.ilike(f"%{search_term}%"))
        ).all()

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']

        existing_client = Client.query.filter_by(email=email).first()
        if existing_client:
            flash('Email address is already in use. Please use a different email.', 'warning')
            return render_template('clients.html', clients=clients_list, search_term=search_term)

        new_client = Client(name=name, surname=surname, email=email)
        db.session.add(new_client)
        db.session.commit()
        return redirect(url_for('client_details', client_id=new_client.id))

    return render_template('clients.html', clients=clients_list, search_term=search_term)

@app.route("/client_details/<int:client_id>")
def client_details(client_id):
    client = Client.query.get_or_404(client_id)

    # Fetch visits related to this client using the Many-to-Many relationship
    related_visits = client.visits # Access visits through client.visits relationship

    # Prepare visit data for template - Fetch leader and *all* clients for each visit
    visits_data = []
    if related_visits:
        for visit in related_visits:
            leader_client = Client.query.get(visit.leader_client_id) # Leader Client still fetched using leader_client_id

            # Get *all* clients associated with the visit using the relationship
            other_clients = visit.clients # Access all clients using visit.clients relationship

            visits_data.append({
                'visit': visit,
                'leader_client': leader_client,
                'other_clients': other_clients, # Now 'other_clients' will correctly include all clients from the relationship
        })

    return render_template('client_details.html', client=client, visits_data=visits_data) # Pass visits to template

@app.route("/edit_client/<int:client_id>", methods=['POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.surname = request.form['surname']
        client.email = request.form['email']
        client.phone = request.form['phone']
        client.address = request.form['address']
        client.notes = request.form['notes']
        
        # Handle date field - it might be empty
        last_dive_day = request.form['last_dive_day']
        client.last_dive_day = datetime.strptime(last_dive_day, '%Y-%m-%d').date() if last_dive_day else None
        
        client.certification_number = request.form['certification_number']
        client.certification_level = request.form['certification_level']
        client.nitrox_certification_number = request.form['nitrox_certification_number']

        try:
            db.session.commit()
            flash('Client information updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating client information. Please try again.', 'error')
            print(f"Error updating client: {str(e)}")  # For debugging
            
    return redirect(url_for('client_details', client_id=client.id))
@app.route("/delete_client/<int:client_id>", methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('clients'))

@app.route("/edit_visit/<int:client_id>/<int:visit_id>", methods=['GET', 'POST'])
@app.route("/edit_visit/<int:client_id>", methods=['GET', 'POST'])
def edit_visit(client_id, visit_id=None):
    leader_client = Client.query.get_or_404(client_id)
    all_clients_objects = Client.query.all()

    # Convert Client objects to dictionaries for JSON serialization
    all_clients = []
    for client_obj in all_clients_objects:
        client_dict = {
            'id': client_obj.id,
            'name': client_obj.name,
            'surname': client_obj.surname,
            'email': client_obj.email
        }
        all_clients.append(client_dict)

    visit = None
    if visit_id:  # If visit_id is provided, we are editing an existing visit
        visit = Visit.query.get_or_404(visit_id)

    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        place_of_stay = request.form['place_of_stay']
        selected_client_ids_str = request.form.get('selected_client_ids', '')
        selected_client_ids = [int(id) for id in selected_client_ids_str.split(',') if id]

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Include leader in the list of involved clients
        involved_client_ids = [leader_client.id] + selected_client_ids

        # Check for overlapping visits
        overlapping_visits_found = False
        for client_id_to_check in involved_client_ids:
            client_to_check = Client.query.get(client_id_to_check)
            for existing_visit in client_to_check.visits:
                # Skip current visit when checking for overlaps
                if existing_visit.id != visit_id and \
                   (start_date <= existing_visit.end_date) and \
                   (end_date >= existing_visit.start_date):
                    overlapping_visits_found = True
                    flash(f"Visit for client {client_to_check.name} {client_to_check.surname} "
                          f"overlaps with an existing visit from {existing_visit.start_date} "
                          f"to {existing_visit.end_date}.", 'warning')
                    break
            if overlapping_visits_found:
                break

        if overlapping_visits_found:
            return render_template('edit_visit.html', 
                                leader_client_id=client_id, 
                                clients=all_clients, 
                                visit=visit)

        if visit:  # Editing existing visit
            visit.start_date = start_date
            visit.end_date = end_date
            visit.place_of_stay = place_of_stay
            visit.leader_client_id = client_id
            
            # Clear existing clients and add new ones
            visit.clients = []  # Clear existing relationships
            # Add leader client
            leader = Client.query.get(client_id)
            if leader:
                visit.clients.append(leader)
            # Add selected clients
            for client_id in selected_client_ids:
                client = Client.query.get(client_id)
                if client:
                    visit.clients.append(client)
            
            flash('Visit updated successfully!', 'success')
        else:  # Creating new visit
            visit = Visit(
                start_date=start_date,
                end_date=end_date,
                place_of_stay=place_of_stay,
                leader_client_id=client_id
            )
            db.session.add(visit)
            
            # Add leader client
            leader = Client.query.get(client_id)
            if leader:
                visit.clients.append(leader)
            # Add selected clients
            for client_id in selected_client_ids:
                client = Client.query.get(client_id)
                if client:
                    visit.clients.append(client)

            flash('Visit created successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('client_details', client_id=client_id))

    return render_template('edit_visit.html', 
                         leader_client_id=client_id, 
                         clients=all_clients, 
                         visit=visit)


@app.route("/delete_visit/<int:client_id>/<int:visit_id>", methods=['POST'])
def delete_visit(client_id, visit_id):
    visit = Visit.query.get_or_404(visit_id)
    db.session.delete(visit)
    db.session.commit()
    flash('Visit deleted successfully!', 'success')
    return redirect(url_for('client_details', client_id=client_id)) # Redirect back to client details page


#Trips
@app.route("/trips", methods=['GET', 'POST'])
def trips():
    today = date.today()
    selected_date_str = request.args.get('date')
    selected_month_str = request.args.get('month')
    selected_year_str = request.args.get('year')
    selected_trip_id = request.args.get('selected_trip_id')  # Get selected_trip_id from URL
    print(f"DEBUG: selected_trip_id from URL: {selected_trip_id}") # DEBUG PRINT
    selected_date = today  # Default to today

    if selected_date_str:  # 1. Priority: 'date' parameter (day click)
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'warning')
            selected_date = today  # Fallback to today on invalid date
    elif selected_year_str and selected_month_str:  # 2. 'month' and 'year' parameters (dropdown change)
        try:
            selected_month = int(selected_month_str)
            selected_year = int(selected_year_str)
            selected_date = date(selected_year, selected_month, 1)  # Default to 1st of month for month/year nav
        except ValueError:
            flash('Invalid month or year selected.', 'warning')
            selected_date = today  # Fallback to today on invalid month/year
    # 3. Else: No parameters - default to today (already set as default initially)

    selected_month = selected_date.month  # Ensure selected_month and year are updated
    selected_year = selected_date.year
    selected_date_str = selected_date.strftime('%Y-%m-%d')  # Re-generate selected_date_str

    trips_on_date = Trip.query.filter_by(date=selected_date).all()

    selected_trip = None  # Initialize selected_trip to None
    clients_on_trip = []  # Initialize clients_on_trip to empty list

    if selected_trip_id:  # If a trip is selected
        selected_trip = Trip.query.get(selected_trip_id)  # Fetch selected trip from DB
        print(f"DEBUG: Fetched selected_trip: {selected_trip}") # DEBUG PRINT
        if selected_trip:
            print(f"DEBUG: Clients for selected_trip: {clients_on_trip}") # DEBUG PRINT
            clients_on_trip = selected_trip.clients  # Get clients for selected trip using relationship
        else:
            print("DEBUG: selected_trip NOT FOUND in database") # DEBUG PRINT
    else:
        print("DEBUG: No selected_trip_id in URL") # DEBUG PRINT

    months = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }  # Month dictionary
    current_year = today.year
    years = list(range(current_year - 2, current_year + 3))   # This will give 2 years before and 2 years after current year

    return render_template('trips.html',
                           trips=trips_on_date,
                           selected_date_str=selected_date_str,
                           selected_month=selected_month,
                           selected_year=selected_year,
                           calendar=calendar,
                           months=months,
                           years=years,
                           selected_trip=selected_trip,
                           clients_on_trip=clients_on_trip)

@app.route("/edit_trip", methods=['GET', 'POST'])
def edit_trip():
    trip_classes = [ # Define trip classes
        '2 Tanks', 'One Tank Orientation', 'Dives 1&2', 'Night Dive', 'X-Dive', '3-Stop Snorkel', 'X-snorkel'
    ]
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    if request.method == 'POST': # Form submission handling
        name = request.form.get('name')
        trip_class = request.form.get('trip_class')
        date_str = request.form.get('date') # Get date from form
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        max_divers = request.form.get('max_divers')
        needed_staff = request.form.get('needed_staff')

        try: # Data validation and conversion
            trip_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
            end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None
            max_divers = int(max_divers)
            needed_staff = int(needed_staff)

            new_trip = Trip(
                name=name,
                trip_class=trip_class,
                date=trip_date,
                start_time=start_time,
                end_time=end_time,
                max_divers=max_divers,
                needed_staff=needed_staff
            )
            db.session.add(new_trip)
            db.session.commit()
            return redirect(url_for('trips', date=trip_date.strftime('%Y-%m-%d'))) # Redirect to trips page for the created date

        except ValueError: # Handle validation errors
            flash('Error: Invalid data in form. Please check the inputs.', 'danger') # Flash error message
            return render_template('edit_trip.html', trip_classes=trip_classes, selected_date=selected_date) # Re-render form with error

    return render_template('edit_trip.html', trip_classes=trip_classes, selected_date=selected_date) # Render form for GET request

@app.route("/trips/add_clients/<int:trip_id>")
def trips_add_clients(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    search_term = request.args.get('search')
    clients_list = []

    if search_term: # Basic client search (similar to /clients route)
        clients_list = Client.query.filter(
            (Client.name.ilike(f"%{search_term}%")) |
            (Client.surname.ilike(f"%{search_term}%")) |
            (Client.email.ilike(f"%{search_term}%"))
        ).all()

    return render_template('add_clients_to_trip.html', trip=trip, clients_list=clients_list, search_term=search_term)

@app.route("/trips/assign_client/<int:trip_id>/<int:client_id>")
def trips_assign_client(trip_id, client_id):
    selected_trip = Trip.query.get_or_404(trip_id)
    selected_client = Client.query.get_or_404(client_id)
    trip_date = selected_trip.date

    print("\n--- DEBUG (Visit Check) ---")
    print(f"DEBUG (Visit Check): Trip Date: {trip_date}, Client ID: {client_id}")

    is_in_visit = False
    # Get all visits for the client using the Many-to-Many relationship
    client_visits = selected_client.visits
    print(f"DEBUG (Visit Check): Client Visits Fetched: {client_visits}")

    for visit in client_visits:
        print(f"DEBUG (Visit Check): - Visit ID: {visit.id}, Visit Start Date: {visit.start_date}, Visit End Date: {visit.end_date}")
        if visit.start_date <= trip_date <= visit.end_date:
            is_in_visit = True
            print(f"DEBUG (Visit Check): Date Overlap Found! Visit Start: {visit.start_date}, Visit End: {visit.end_date}, Trip Date: {trip_date}")
            break

    if not is_in_visit:
        print(f"DEBUG (Visit Check): No Visit Overlap found for Trip Date: {trip_date}")
        flash(f"Client '{selected_client.name} {selected_client.surname}' is not assigned to a visit that overlaps with {trip_date.strftime('%Y-%m-%d')}.", 'warning')
    else:
        print(f"DEBUG (Visit Check): Client IS in an Overlapping Visit - Proceeding to add to trip")
        
        # Check if client is already in trip
        if selected_client not in selected_trip.clients:
            selected_trip.clients.append(selected_client)
            
            print("DEBUG (Equipment): Looking for last used equipment")
            # Get last equipment used by this client
            last_equipment = TripClientEquipment.query\
                .filter_by(client_id=client_id)\
                .order_by(TripClientEquipment.updated_at.desc())\
                .first()

            if last_equipment:
                print(f"DEBUG (Equipment): Found last equipment - ID: {last_equipment.id}")
            else:
                print("DEBUG (Equipment): No previous equipment found")

            # Create new equipment assignment
            new_equipment = TripClientEquipment(
                trip_id=trip_id,
                client_id=client_id,
                mask_size=last_equipment.mask_size if last_equipment else None,
                bcd_size=last_equipment.bcd_size if last_equipment else None,
                wetsuit_size=last_equipment.wetsuit_size if last_equipment else None,
                fins_size=last_equipment.fins_size if last_equipment else None,
                weights_amount=last_equipment.weights_amount if last_equipment else None
            )
            db.session.add(new_equipment)
            print("DEBUG (Equipment): Created new equipment assignment")

            try:
                db.session.commit()
                print("DEBUG: Successfully added client to trip and created equipment assignment")
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG (Error): Failed to add client or create equipment - {str(e)}")
                flash(f"Error adding client to trip: {str(e)}", 'error')
        else:
            print("DEBUG: Client already in trip")

    return redirect(url_for('trips_add_clients', trip_id=trip_id, search=request.args.get('search')))

@app.route("/trips/save_equipment/<int:trip_id>/<int:client_id>", methods=['POST'])
def save_equipment(trip_id, client_id):
    try:
        data = request.json
        equipment = TripClientEquipment.query.filter_by(
            trip_id=trip_id, 
            client_id=client_id
        ).first()

        if not equipment:
            # Create new equipment assignment
            equipment = TripClientEquipment(
                trip_id=trip_id,
                client_id=client_id
            )
            db.session.add(equipment)

        # Update equipment fields
        equipment.mask_size = data.get('mask_size')
        equipment.bcd_size = data.get('bcd_size')
        equipment.wetsuit_size = data.get('wetsuit_size')
        equipment.fins_size = data.get('fins_size')
        equipment.weights_amount = data.get('weights_amount')
        equipment.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error saving equipment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route("/trips/get_last_equipment/<int:client_id>")
def get_last_equipment(client_id):
    try:
        # Get the most recent equipment assignment for this client
        last_equipment = TripClientEquipment.query\
            .filter_by(client_id=client_id)\
            .order_by(TripClientEquipment.updated_at.desc())\
            .first()

        if last_equipment:
            return jsonify({
                'success': True,
                'equipment': {
                    'mask_size': last_equipment.mask_size,
                    'bcd_size': last_equipment.bcd_size,
                    'wetsuit_size': last_equipment.wetsuit_size,
                    'fins_size': last_equipment.fins_size,
                    'weights_amount': last_equipment.weights_amount
                }
            })
        return jsonify({'success': True, 'equipment': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)