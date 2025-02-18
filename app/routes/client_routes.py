from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import Client, Visit
from app import db
from app.services.client_service import search_clients, get_client_visits

clients = Blueprint('clients', __name__)

@clients.route("/clients", methods=['GET', 'POST'])
def client_list():
    search_term = request.args.get('search')
    clients_list = []

    if search_term:
        clients_list = search_clients(search_term)

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
        return redirect(url_for('clients.client_details', client_id=new_client.id))

    return render_template('clients.html', clients=clients_list, search_term=search_term)

@clients.route("/client_details/<int:client_id>")
def client_details(client_id):
    client = Client.query.get_or_404(client_id)
    visits_data = get_client_visits(client)
    return render_template('client_details.html', client=client, visits_data=visits_data)

@clients.route("/edit_client/<int:client_id>", methods=['POST'])
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
        from datetime import datetime
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
            print(f"Error updating client: {str(e)}")
            
    return redirect(url_for('clients.client_details', client_id=client.id))

@clients.route("/delete_client/<int:client_id>", methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('clients.client_list'))