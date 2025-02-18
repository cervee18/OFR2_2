from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.models import Trip, Client, TripClientEquipment, TripClass, Place
from app import db
from datetime import datetime, date
import calendar
from app.services.equipment_service import create_equipment_for_trip, update_future_equipment

trips = Blueprint('trips', __name__)

@trips.route("/trips", methods=['GET', 'POST'])
def trip_list():
    today = date.today()
    selected_date_str = request.args.get('date')
    selected_month_str = request.args.get('month')
    selected_year_str = request.args.get('year')
    selected_trip_id = request.args.get('selected_trip_id')
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

    selected_month = selected_date.month
    selected_year = selected_date.year
    selected_date_str = selected_date.strftime('%Y-%m-%d')

    trips_on_date = Trip.query.filter_by(date=selected_date).all()

    selected_trip = None
    clients_on_trip = []

    if selected_trip_id:
        selected_trip = Trip.query.get(selected_trip_id)
        if selected_trip:
            clients_on_trip = selected_trip.clients

    months = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    current_year = today.year
    years = list(range(current_year - 2, current_year + 3))

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

@trips.route("/edit_trip", methods=['GET', 'POST'])
def edit_trip():
    # Get all available trip classes and places for selection
    trip_classes = TripClass.query.order_by(TripClass.name).all()
    places = Place.query.order_by(Place.name).all()
    
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    if request.method == 'POST':
        trip_class_id = request.form.get('trip_class_id')
        place_id = request.form.get('place_id')
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        max_divers = request.form.get('max_divers')
        name = request.form.get('name', '') 
        assigned_staff = request.form.get('assigned_staff', '')

        try:
            # Get selected trip class
            trip_class = TripClass.query.get_or_404(trip_class_id)
            
            # Parse date
            trip_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Parse start time if provided, otherwise use trip class start time
            if start_time_str:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
            else:
                start_time = trip_class.start_time
            
            # If name not provided, use trip class name + date
            if not name:
                name = f"{trip_class.name} {trip_date.strftime('%Y-%m-%d')}"
                
            # Convert max_divers to int if provided
            max_divers = int(max_divers) if max_divers else None

            new_trip = Trip(
                name=name,
                trip_class_id=trip_class_id,
                place_id=place_id,
                date=trip_date,
                start_time=start_time,
                max_divers=max_divers,
                assigned_staff=assigned_staff
            )
            db.session.add(new_trip)
            db.session.commit()
            
            return redirect(url_for('trips.trip_list', date=trip_date.strftime('%Y-%m-%d')))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating trip: {str(e)}', 'danger')
            return render_template('edit_trip.html', 
                                  trip_classes=trip_classes,
                                  places=places,
                                  selected_date=selected_date)

    return render_template('edit_trip.html', 
                          trip_classes=trip_classes,
                          places=places,
                          selected_date=selected_date)

@trips.route("/get_trip_class_time/<int:class_id>")
def get_trip_class_time(class_id):
    """AJAX endpoint to get the start time for a trip class"""
    trip_class = TripClass.query.get(class_id)
    if trip_class:
        return jsonify({
            'success': True,
            'start_time': trip_class.start_time.strftime('%H:%M')
        })
    return jsonify({'success': False, 'error': 'Trip class not found'})
@trips.route("/trips/add_clients/<int:trip_id>")

def trips_add_clients(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    search_term = request.args.get('search')
    clients_list = []

    if search_term:
        clients_list = Client.query.filter(
            (Client.name.ilike(f"%{search_term}%")) |
            (Client.surname.ilike(f"%{search_term}%")) |
            (Client.email.ilike(f"%{search_term}%"))
        ).all()

    return render_template('add_clients_to_trip.html', trip=trip, clients_list=clients_list, search_term=search_term)

@trips.route("/trips/assign_client/<int:trip_id>/<int:client_id>")
def trips_assign_client(trip_id, client_id):
    selected_trip = Trip.query.get_or_404(trip_id)
    selected_client = Client.query.get_or_404(client_id)
    trip_date = selected_trip.date

    is_in_visit = False
    client_visits = selected_client.visits

    for visit in client_visits:
        if visit.start_date <= trip_date <= visit.end_date:
            is_in_visit = True
            break

    if not is_in_visit:
        flash(f"Client '{selected_client.name} {selected_client.surname}' is not assigned to a visit that overlaps with {trip_date.strftime('%Y-%m-%d')}.", 'warning')
    else:
        if selected_client not in selected_trip.clients:
            selected_trip.clients.append(selected_client)
            
            last_equipment = TripClientEquipment.query\
                .filter_by(client_id=client_id)\
                .order_by(TripClientEquipment.updated_at.desc())\
                .first()

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

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding client to trip: {str(e)}", 'error')

    return redirect(url_for('trips.trips_add_clients', trip_id=trip_id, search=request.args.get('search')))

@trips.route("/trips/save_equipment/<int:trip_id>/<int:client_id>", methods=['POST'])
def save_equipment(trip_id, client_id):
    try:
        data = request.json
        apply_to_future = data.get('applyToFuture', False)
        
        current_trip = Trip.query.get_or_404(trip_id)
        current_date = current_trip.date
        
        # Step 1: Update the current trip's equipment
        current_equipment = TripClientEquipment.query.filter_by(
            trip_id=trip_id, client_id=client_id
        ).first()
        
        if not current_equipment:
            # Use the service function instead of creating directly
            current_equipment = create_equipment_for_trip(trip_id, client_id)
            db.session.add(current_equipment)
        
        # Update equipment fields
        current_equipment.mask_size = data.get('mask_size')
        current_equipment.bcd_size = data.get('bcd_size')
        current_equipment.wetsuit_size = data.get('wetsuit_size')
        current_equipment.fins_size = data.get('fins_size')
        current_equipment.weights_amount = data.get('weights_amount')
        current_equipment.notes = data.get('notes')
        current_equipment.updated_at = datetime.utcnow()
        
        # Step 2: Update nitrox certification for client if needed
        nitrox_value = data.get('nitrox')
        if nitrox_value:
            client = Client.query.get(client_id)
            if client:
                client.nitrox_certification_number = "YES" if nitrox_value == "yes" else None
        
        # Step 3: If requested, update future trips using the service function
        if apply_to_future:
            from app.services.equipment_service import update_future_equipment
            update_future_equipment(client_id, current_date, data)
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
@trips.route("/trips/get_last_equipment/<int:client_id>")
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