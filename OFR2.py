from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Client, Visit, Trip
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

    # Fetch visits related to this client
    related_visits = Visit.query.filter(
        (Visit.leader_client_id == client_id) | # Client is the leader
        (Visit.client_ids.like(f"%{client_id}%")) # Client is in client_ids string (needs careful parsing)
    ).all()

    # Prepare visit data for template - Fetch leader and other clients for each visit
    visits_data = []
    for visit in related_visits:
        leader_client = Client.query.get(visit.leader_client_id)

        other_clients = []
        if visit.client_ids:
            client_id_list = visit.client_ids.split(',')
            for other_client_id in client_id_list:
                other_client = Client.query.get(other_client_id)
                if other_client:  # Ensure client exists
                    other_clients.append(other_client)

        visits_data.append({
            'visit': visit,
            'leader_client': leader_client,
            'other_clients': other_clients,
        })

    return render_template('client_details.html', client=client, visits_data=visits_data) # Pass visits to template

@app.route("/edit_client/<int:client_id>", methods=['POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        # ... (rest of the edit_client function is the same) ...
        pass
    return render_template('client_details.html', client=client) # Modified for simplicity - visits not re-fetched on GET for edit page.

@app.route("/delete_client/<int:client_id>", methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('clients'))

@app.route("/edit_visit/<int:client_id>/<int:visit_id>", methods=['GET', 'POST']) # Route for editing existing visit
@app.route("/edit_visit/<int:client_id>", methods=['GET', 'POST'])         # Route for creating new visit
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

    visit = None # Initialize visit as None, will be fetched if editing
    if visit_id: # If visit_id is provided, we are editing an existing visit
        visit = Visit.query.get_or_404(visit_id) # **Verify this line is correctly fetching the visit**


    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        place_of_stay = request.form['place_of_stay']
        selected_client_ids_str = request.form.get('selected_client_ids', '')
        selected_client_ids = [int(id) for id in selected_client_ids_str.split(',') if id]

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        involved_client_ids = [leader_client.id] + selected_client_ids

        overlapping_visits_found = False
        for client_id_to_check in involved_client_ids:
            existing_visits = Visit.query.filter(
                Visit.client_ids.like(f"%{client_id_to_check}%") | (Visit.leader_client_id == client_id_to_check)
            ).all()
            for existing_visit in existing_visits:
                if existing_visit.id != visit_id and (start_date <= existing_visit.end_date) and (end_date >= existing_visit.start_date): # Exclude current visit being edited from overlap check
                    overlapping_visits_found = True
                    overlapping_client = Client.query.get(client_id_to_check)
                    flash(f"Visit for client {overlapping_client.name} {overlapping_client.surname} overlaps with an existing visit from {existing_visit.start_date} to {existing_visit.end_date}.", 'warning')
                    break
            if overlapping_visits_found:
                break

        if overlapping_visits_found:
            return render_template('edit_visit.html', leader_client_id=client_id, clients=all_clients, visit=visit) # Pass visit back to template to pre-fill form
        else:
            if visit: # Editing existing visit
                visit.start_date = start_date
                visit.end_date = end_date
                visit.place_of_stay = place_of_stay
                visit.client_ids = ','.join(map(str, selected_client_ids))
                db.session.commit()
                flash('Visit updated successfully!', 'success')
            else: # Creating new visit
                visit = Visit(
                    start_date=start_date,
                    end_date=end_date,
                    place_of_stay=place_of_stay,
                    leader_client_id=client_id,
                    client_ids=','.join(map(str, selected_client_ids))
                )
                db.session.add(visit)
                db.session.commit()
                flash('Visit created successfully!', 'success')
            return redirect(url_for('client_details', client_id=client_id))

    return render_template('edit_visit.html', leader_client_id=client_id, clients=all_clients, visit=visit) # Pass visit to template

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
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)