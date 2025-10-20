#BrewMe Batch & Inventory Optimizer - main.py
#Entry point for the application. Initializes DB and starts the GUI.

import db
import gui
import tkinter as tk

def initialize_application():
    # Establishes DB connection, creates tables, and seeds initial data.
    print("--- Initializing BrewMe Brewer Inventory Management ---")
    conn = db.connect_db()
    if conn:
        print("Database connection successful.")
        
       
        db.create_tables(conn)
        print("Tables checked/created.")
        
        # Seed initial data (Ingredient objects and Recipes)
        db.seed_initial_data(conn)
        print("Initial data seeded.")
        
        db.close_db(conn)
        return True
    else:
        print("ERROR: Could not connect to database.")
        return False

def main():
    # 1. Initialize Database
    if not initialize_application():
        return

    # 2. Start GUI 
    print("Starting GUI...")
    root = tk.Tk()
    app = gui.BreweryApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
