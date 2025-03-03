from app import create_app, db
from populate_debug_data import populate_debug_data

app = create_app()

if __name__ == '__main__':
    import argparse
    
    # Add command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--populate-debug', action='store_true', 
                      help='Populate database with debug data (trip classes, places, and clients)')
    parser.add_argument('--num-clients', type=int, default=100,
                      help='Number of fake clients to create (default: 100)')
    parser.add_argument('--num-staff', type=int, default=10,
                  help='Number of fake staff members to create (default: 10)')
    args = parser.parse_args()
    
    with app.app_context():
        db.create_all()
        
        # Populate debug data if flag is set
        if args.populate_debug:
            populate_debug_data(db, num_clients=args.num_clients, num_staff=args.num_staff)
    
    app.run(debug=True)