#BrewMe Batch & Inventory Optimizer - db.py
#Handles SQLite setup, table creation, and core SQL operations.


import sqlite3
import os

#  database path
DB_FILE = os.path.join('data', 'brewme.db')

def connect_db():
    '''Establishes and returns a database connection '''
    conn = None
    try:
        #check if directory exists
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        # Enable foreign key enforcement for data integrity
        conn.execute('PRAGMA foreign_keys=ON') 
        return conn
    except sqlite3.Error as e:
        #exception handling for DB connection
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

def close_db(conn):
    '''Closes the database connection '''
    if conn:
        conn.close()

def create_tables(conn):
    '''Creates the necessary database tables on first run .'''
    if conn is None: return

    cursor = conn.cursor()
    
    # --- Table Creation Block ---
    
    try:
        # 1. Ingredients Table: (No FKs here)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Ingredients (
                id INTEGER PRIMARY KEY NOT NULL,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                cost REAL NOT NULL, 
                detail1 REAL,
                unit TEXT NOT NULL,
                inventory_qty REAL DEFAULT 0 
            )
        ''')
        
        # 2. Recipes Table
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Recipes (
                id INTEGER PRIMARY KEY NOT NULL,
                name TEXT NOT NULL UNIQUE,
                target_volume_BBL REAL NOT NULL, 
                base_cost REAL DEFAULT 0.0
            )
        ''')
        
        # 3. Recipe_Details Table (Uses Foreign Keys)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Recipe_Details (
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                PRIMARY KEY (recipe_id, ingredient_id),
                FOREIGN KEY (recipe_id) REFERENCES Recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (ingredient_id) REFERENCES Ingredients(id) ON DELETE RESTRICT
            )
        ''')
        
        # 4. Batch_Log Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Batch_Log (
                id INTEGER PRIMARY KEY NOT NULL,
                recipe_name TEXT NOT NULL,
                volume_BBL REAL NOT NULL, 
                final_cost REAL NOT NULL,
                date_brewed TEXT NOT NULL
            )
        ''')
        
        conn.commit()

    except sqlite3.Error as e:
        print(f"FATAL ERROR during table creation: {e}")
        raise e
        
    return cursor

def add_ingredient(conn, name, ingredient_type, cost, detail, unit, qty):
    '''CRUD: Create - Inserts a new ingredient row .'''
    cursor = conn.cursor()
    try:
        # SQL Injection prevention
        cursor.execute('''
            INSERT INTO Ingredients (name, type, cost, detail1, unit, inventory_qty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, ingredient_type, cost, detail, unit, qty))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed: Ingredients.name' in str(e):
            return "DUPLICATE_NAME"
        # Handle specific DB error 
        raise e

def read_ingredients(conn):
    '''CRUD: Read - Retrieves all ingredients and their current inventory .'''
    cursor = conn.cursor()
    #  SELECT statement 
    cursor.execute('SELECT id, name, type, cost, detail1, unit, inventory_qty FROM Ingredients ORDER BY name')
    return cursor.fetchall()

def update_inventory_qty(conn, ingredient_id, delta_qty):
    '''CRUD: Update - Adjusts inventory level for an ingredient .'''
    cursor = conn.cursor()
    # Use MAX(0, ...) to ensure we never go below zero, preserving integrity 
    cursor.execute('''
        UPDATE Ingredients 
        SET inventory_qty = MAX(0, inventory_qty + ?) 
        WHERE id = ?
    ''', (delta_qty, ingredient_id))
    conn.commit()
    return cursor.rowcount

def delete_ingredient(conn, ingredient_id):
    '''CRUD: Delete - Removes an ingredient by ID.'''
    cursor = conn.cursor()
    #DELETE statement 
    cursor.execute('DELETE FROM Ingredients WHERE id = ?', (ingredient_id,))
    conn.commit()
    return cursor.rowcount

def add_recipe(conn, name, volume, base_cost, ingredient_details):
    '''Creates a recipe and its details in a transaction.'''
    cursor = conn.cursor()
    try:
        # Insert master recipe data
        
        cursor.execute('''
            INSERT INTO Recipes (name, target_volume_BBL, base_cost)
            VALUES (?, ?, ?)
        ''', (name, volume, base_cost))
        recipe_id = cursor.lastrowid
        
        # Insert associated ingredients (Recipe_Details table)
        for ing_id, qty in ingredient_details.items():
            cursor.execute('''
                INSERT INTO Recipe_Details (recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            ''', (recipe_id, ing_id, qty))
            
        conn.commit()
        return recipe_id
    except sqlite3.Error as e:
        conn.rollback()
        raise e

def log_batch(conn, recipe_name, volume, final_cost, date_brewed):
    '''Records a completed batch into the Batch_Log table.'''
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Batch_Log (recipe_name, volume_BBL, final_cost, date_brewed)
        VALUES (?, ?, ?, ?)
    ''', (recipe_name, volume, final_cost, date_brewed))
    conn.commit()
    return cursor.lastrowid

def get_batch_log(conn):
    '''Reads all records from the Batch Log (File I/O source).'''
    cursor = conn.cursor()
    cursor.execute('SELECT id, recipe_name, volume_BBL, final_cost, date_brewed FROM Batch_Log ORDER BY id DESC')
    return cursor.fetchall()

# --- Utility to seed the database with initial data ---
def seed_initial_data(conn):
    '''Seeds database with initial ingredients and recipes if not already seeded.'''
    # Use existing read function to check if data exists
    ingredients = read_ingredients(conn)
    if ingredients:
        # Data already exists, skip seeding
        return
        
    from models import create_initial_ingredients, create_initial_recipes
    
    # 1. Seed Ingredients
    initial_ingredients = create_initial_ingredients()
    ingredient_id_map = {} # Map name to newly assigned ID

    for ing in initial_ingredients:
        # Use get_details method from object hierarchy to get data consistently
        name, type_str, cost, detail, unit = ing.get_details()
        # Initial quantity is 10 for Fermentables/Hops, 20 for Yeast (for simulation)
        initial_qty = 10.0
        if type_str == 'Base': # Yeast
            initial_qty = 20.0
        
        ing_id = add_ingredient(conn, name, type_str, cost, detail, unit, initial_qty)
        if ing_id != "DUPLICATE_NAME":
            ingredient_id_map[name] = ing_id

    # 2. Seed Recipes
    initial_recipes = create_initial_recipes(ingredient_id_map)
    for recipe in initial_recipes:
        # Calculate a base cost for initial seed data display
        base_cost = 0 
        for ing_id, qty in recipe.get_ingredients().items():
            # Get cost from DB (assuming costs are seeded)
            cursor = conn.cursor()
            cursor.execute('SELECT cost FROM Ingredients WHERE id = ?', (ing_id,))
            ing_cost = cursor.fetchone()[0] 
            base_cost += ing_cost * qty
            
        add_recipe(conn, recipe.get_name(), recipe.get_target_volume(), base_cost, recipe.get_ingredients())
        
    conn.commit()

# Ensure the database is initialized if run directly for testing
if __name__ == '__main__':
    conn = connect_db()
    if conn:
        print("Database connected. Creating tables...")
        cursor = create_tables(conn)
        
        try:
            print("Seeding initial data...")
            seed_initial_data(conn)
        except Exception as e:
            print(f"Error during seeding: {e}")

        
        # Simple read test (CRUD: Read)
        print("\nCurrent Ingredients:")
        for row in read_ingredients(conn):
            print(row)
            
        close_db(conn)
