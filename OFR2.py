from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Client, Visit
from datetime import datetime

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



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)