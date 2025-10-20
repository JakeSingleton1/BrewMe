#BrewMe Brewery Inventory Management System - services.py
#Contains core business logic, calculations, and the recursive function.


import db
import os
import csv
import datetime

# Named constant for required data integrity check (BBL)
MIN_VOLUME_BBL = 0.5 # Minimum batch size is half a barrel (approx 15.5 gal)
COST_MARKUP = 1.15 # 15% markup for retail cost estimation

def get_all_recipes_and_ingredients(conn):
    '''Retrieves all recipes and all ingredients for the GUI display.'''
    cursor = conn.cursor()
    
    # Get all master recipes
    cursor.execute('SELECT id, name, target_volume_BBL, base_cost FROM Recipes')
    # Renamed the column alias to match BBL
    recipes = cursor.fetchall()
    
    # Get all ingredients for lookups
    ingredients = db.read_ingredients(conn)
    
    return recipes, ingredients

def scale_recipe(recipe_id, original_volume, new_volume):
    '''
    Core business logic: Scales a recipe proportionally based on the new batch volume (BBL).
    Returns a dictionary of scaled ingredients and the scale factor.
    '''
    # Updated constant usage
    if original_volume <= MIN_VOLUME_BBL or new_volume <= MIN_VOLUME_BBL:
        raise ValueError("Volumes must be greater than zero for scaling.")
        
    scale_factor = new_volume / original_volume
    
    conn = db.connect_db()
    if conn is None: return {}, 0
    
    cursor = conn.cursor()
    
    # Get the original ingredient quantities for the recipe
    cursor.execute('''
        SELECT ingredient_id, quantity FROM Recipe_Details WHERE recipe_id = ?
    ''', (recipe_id,))
    original_quantities = cursor.fetchall()
    
    scaled_ingredients = []
    
    for ing_id, original_qty in original_quantities:
        # Proportional calculation (core logic)
        scaled_qty = original_qty * scale_factor
        
        # Get ingredient name and unit for the output display
        cursor.execute('SELECT name, unit FROM Ingredients WHERE id = ?', (ing_id,))
        ing_name, ing_unit = cursor.fetchone()
        
        scaled_ingredients.append({
            'id': ing_id,
            'name': ing_name,
            'quantity': scaled_qty,
            'unit': ing_unit
        })

    db.close_db(conn)
    return scaled_ingredients, scale_factor


def calculate_recipe_cost(ingredient_list):
    '''
    Advanced function: Calculates the total cost of a list of ingredients recursively.
    This function processes the list by taking the head element and adding its cost to 
    the recursive call on the rest of the list until the base case (empty list) is met.
    '''
    # Base Case : If the list is empty, the cost is 0.0
    if not ingredient_list:
        return 0.0

    # Recursive Case : Process head element and call function on tail.
    
    # Get the cost of the current (head) ingredient
    head_ingredient = ingredient_list[0]
    ing_id = head_ingredient['id']
    qty = head_ingredient['quantity']
    
    conn = db.connect_db()
    if conn is None: return 0.0
    
    cursor = conn.cursor()
    # Fetch the cost per unit from the database
    cursor.execute('SELECT cost FROM Ingredients WHERE id = ?', (ing_id,))
    cost_per_unit = cursor.fetchone()[0]
    
    db.close_db(conn)

    current_cost = cost_per_unit * qty
    
    # Recursive call : Calls itself with the remainder of the list (tail)
    return current_cost + calculate_recipe_cost(ingredient_list[1:])


def calculate_and_log_batch(recipe_name, volume, final_cost, ingredient_list):
    '''
    Finalizes a batch, updates inventory, and logs the entry (CRUD: Update, Create).
    This logic enforces data integrity by only allowing updates if inventory is sufficient.
    '''
    conn = db.connect_db()
    if conn is None: return False, "Database connection failed."

    # 1. Check for sufficient inventory (Business Logic/Data Integrity)
    for ing in ingredient_list:
        ing_id = ing['id']
        qty_needed = ing['quantity']
        
        cursor = conn.cursor()
        cursor.execute('SELECT inventory_qty FROM Ingredients WHERE id = ?', (ing_id,))
        current_qty = cursor.fetchone()[0]
        
        if current_qty < qty_needed:
            db.close_db(conn)
            # F-string usage 
            return False, f"Insufficient inventory of {ing['name']}! Needs {qty_needed:.2f}, has {current_qty:.2f}."

    # 2. Inventory is sufficient, proceed with updates (CRUD: Update)
    for ing in ingredient_list:
        ing_id = ing['id']
        qty_consumed = -ing['quantity'] # Use negative delta for consumption
        # Use parameterized query for update
        db.update_inventory_qty(conn, ing_id, qty_consumed)

    # 3. Log the batch (CRUD: Create)
    date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    db.log_batch(conn, recipe_name, volume, final_cost, date_str)

    db.close_db(conn)
    return True, "Batch successfully logged and inventory updated."


def export_batch_log_to_csv():
    '''
    File I/O: Exports the entire batch log to a CSV file 
    Uses standard library `csv` module for structured file writing.
    '''
    conn = db.connect_db()
    if conn is None:
        return False, "Database connection failed."
        
    log_data = db.get_batch_log(conn)
    db.close_db(conn)

    export_path = os.path.join('data', 'batch_log_export.csv')

    try:
        # File handling with 'w' mode and try/except
        
        with open(export_path, mode='w', newline='') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)
            
            # Write header row (Updated Volume unit to BBL)
            csv_writer.writerow(['Batch ID', 'Recipe Name', 'Volume (BBL)', 'Final Cost ($)', 'Date Brewed'])
            
            # Write data rows
            csv_writer.writerows(log_data)

        #  success message 
        return True, f"Batch log successfully exported to {export_path}"
        
    except IOError as e:
        #  handling file write exceptions 
        return False, f"ERROR: Could not write to file. {e}"

if __name__ == '__main__':
    # Simple test for recursion
    print("\n--- Recursive Cost Calculation Test ---")
    
    # Create mock ingredient list (IDs 1-4 for testing)
    mock_ingredients = [
        {'id': 1, 'name': 'Pale Malt', 'quantity': 10.0, 'unit': 'lb'},
        {'id': 2, 'name': 'Crystal Malt', 'quantity': 1.0, 'unit': 'lb'},
        {'id': 3, 'name': 'Cascade Hops', 'quantity': 100.0, 'unit': 'oz'},
        {'id': 4, 'name': 'Centennial Hops', 'quantity': 50.0, 'unit': 'oz'}
    ]
    
    # Requires a running DB with seeded data for correct cost lookup
    try:
        total_cost = calculate_recipe_cost(mock_ingredients)
        print(f"Total calculated cost recursively: ${total_cost:.2f}")
    except Exception as e:
        print(f"Skipping recursion test due to missing DB/Seed data: {e}")
