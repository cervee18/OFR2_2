from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import Client, Visit, Trip, TripClientEquipment
from app import db
from datetime import datetime
from app.services.visit_service import check_for_overlapping_visits

visits = Blueprint('visits', __name__)

@visits.route("/edit_visit/<int:client_id>/<int:visit_id>", methods=['GET', 'POST'])
@visits.route("/edit_visit/<int:client_id>", methods=['GET', 'POST'])
def edit_visit(client_id, visit_id=None):
    leader_client = Client.query.get_or_404(client_id)
    all_clients_objects = Client.query.all()
    
    # Get the trip_id parameter if coming from the trip popup
    trip_id = request.args.get('trip_id')
    return_to_popup = request.args.get('return_to_popup', 'false') == 'true'
    
    # If we have a trip_id, get the trip info for default dates
    trip = None
    if trip_id:
        trip = Trip.query.get_or_404(int(trip_id))

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
                                visit=visit,
                                trip=trip)

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
        
        # If we came from a trip popup, assign the client to the trip and return to popup
        if trip_id:
            try:
                trip = Trip.query.get(int(trip_id))
                leader_client_obj = Client.query.get(client_id)
                
                if leader_client_obj and trip and leader_client_obj not in trip.clients:
                    trip.clients.append(leader_client_obj)
                    
                    # Create equipment assignment
                    last_equipment = TripClientEquipment.query\
                        .filter_by(client_id=client_id)\
                        .order_by(TripClientEquipment.updated_at.desc())\
                        .first()

                    new_equipment = TripClientEquipment(
                        trip_id=int(trip_id),
                        client_id=client_id,
                        mask_size=last_equipment.mask_size if last_equipment else None,
                        bcd_size=last_equipment.bcd_size if last_equipment else None,
                        wetsuit_size=last_equipment.wetsuit_size if last_equipment else None,
                        fins_size=last_equipment.fins_size if last_equipment else None,
                        weights_amount=last_equipment.weights_amount if last_equipment else None
                    )
                    db.session.add(new_equipment)
                    db.session.commit()
                    
                    flash(f"Client {leader_client_obj.name} {leader_client_obj.surname} added to trip.", 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding client to trip: {str(e)}", 'error')
            
            if return_to_popup:
                return redirect(url_for('trips.trips_add_clients', trip_id=trip_id))
        
        return redirect(url_for('clients.client_details', client_id=client_id))

    # Set default dates if trip is provided
    if trip and not visit:
        trip_date = trip.date
        default_visit = {
            'start_date': trip_date,
            'end_date': trip_date,
        }
    else:
        default_visit = None

    return render_template('edit_visit.html', 
                         leader_client_id=client_id, 
                         clients=all_clients, 
                         visit=visit,
                         trip=trip,
                         default_visit=default_visit,
                         return_to_popup=return_to_popup)

@visits.route("/delete_visit/<int:client_id>/<int:visit_id>", methods=['POST'])
def delete_visit(client_id, visit_id):
    visit = Visit.query.get_or_404(visit_id)
    db.session.delete(visit)
    db.session.commit()
    flash('Visit deleted successfully!', 'success')
    return redirect(url_for('clients.client_details', client_id=client_id))