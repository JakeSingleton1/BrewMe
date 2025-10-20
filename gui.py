#Implements tkinter GUI and handles user interaction.


import tkinter as tk
from tkinter import ttk, messagebox
import db
import services

class BreweryApp:
    '''
    Main GUI application class built on tkinter 
    '''
    # Named constants for padding 
    PADX = 10
    PADY = 5

    def __init__(self, master):
        '''Constructor to initialize the GUI and load initial data.'''
        self.master = master
        master.title("BrewMe Brewer Inventory Management - Lone Man Mountain Brewing")
        
        # --- Data Storage ---
        # StringVar objects for dynamic output 
        self.output_cost_var = tk.StringVar(value="--")
        self.output_cost_var.set("Final Cost: $0.00")
        self.output_scale_factor_var = tk.StringVar(value="--")
        self.output_scaling_details = tk.StringVar(value="Select a recipe and enter a volume to scale.")
        
        # Containers for fetched data
        self.recipes = []
        self.ingredients = []
        self.ingredient_map = {} # Map ID to name
        self.current_recipe_id = None
        self.current_recipe_volume = None
        
        # --- GUI Setup ---
        self._load_data()
        self._setup_tabs()

    def _load_data(self):
        '''Connects to DB and loads initial recipe/ingredient data.'''
        conn = db.connect_db()
        if conn:
            #Loading data via module functions 
            self.recipes, self.ingredients = services.get_all_recipes_and_ingredients(conn)
            self.ingredient_map = {ing[0]: ing[1] for ing in self.ingredients}
            db.close_db(conn)

    def _setup_tabs(self):
        '''Creates the notebook and adds tabs for application sections .'''
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(pady=self.PADY, padx=self.PADX, fill="both", expand=True)

        # 1. Recipe Scaling Tab (Core Functionality)
        self.scale_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.scale_frame, text="Recipe Scaling & Costing")
        self._build_scale_tab()

        # 2. Inventory Management Tab (CRUD)
        self.inventory_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.inventory_frame, text="Inventory Manager")
        self._build_inventory_tab()
        
        # 3. Batch Log/Export Tab (File I/O)
        self.log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.log_frame, text="Batch Log")
        self._build_log_tab()
        
        # Quit Button for clean exit 
        quit_button = tk.Button(self.master, text="Quit", command=self.master.destroy, bg="#cf0e28", fg="white", activebackground="#a60b20")
        quit_button.pack(pady=self.PADY)


    # -------------------- TAB 1: RECIPE SCALING & COSTING --------------------
    def _build_scale_tab(self):
        '''Builds the Recipe Scaling tab UI.'''
        # Label to select recipe
        tk.Label(self.scale_frame, text="1. Select Recipe:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, self.PADY))
        
        # Dropdown for recipes (uses tkinter widgets)
        recipe_names = [r[1] for r in self.recipes]
        self.recipe_var = tk.StringVar(self.scale_frame)
        self.recipe_var.set(recipe_names[0] if recipe_names else "No Recipes Loaded")
        self.recipe_menu = tk.OptionMenu(self.scale_frame, self.recipe_var, *recipe_names, command=self._on_recipe_select)
        self.recipe_menu.config(width=30)
        self.recipe_menu.pack(pady=self.PADY, padx=self.PADX)
        
        # Entry for new volume (Updated label for BBL)
        tk.Label(self.scale_frame, text="2. Enter New Batch Volume (BBL):", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(self.PADY*2, 0))
        self.volume_entry = tk.Entry(self.scale_frame, width=10)
        self.volume_entry.pack(pady=self.PADY, padx=self.PADX, anchor='w')
        
        # Scale/Cost Button
        scale_button = tk.Button(self.scale_frame, text="Scale & Estimate Cost", command=self._scale_and_cost, bg="#0e99cf", fg="white", activebackground="#0b729e")
        scale_button.pack(pady=self.PADY*2)

        # Output Labels (uses StringVar for dynamic output, 
        tk.Label(self.scale_frame, textvariable=self.output_cost_var, font=('Arial', 12, 'bold')).pack(pady=self.PADY)
        tk.Label(self.scale_frame, textvariable=self.output_scale_factor_var, font=('Arial', 10)).pack(pady=self.PADY)
        
        # Batch Log Button
        log_button = tk.Button(self.scale_frame, text="Log as Completed Batch", command=self._log_batch, bg="#0ecf32", fg="white", activebackground="#0b9e26")
        log_button.pack(pady=self.PADY*2)
        
        # Scaled Ingredient List Output (using a Label for simplicity)
        tk.Label(self.scale_frame, text="Ingredient Requirements:").pack(anchor='w', pady=(self.PADY*2, 0))
        # Updated output message to show BBL
        self.output_scaling_details.set("Select a recipe and enter a volume in BBL to scale.")
        tk.Label(self.scale_frame, textvariable=self.output_scaling_details, justify=tk.LEFT, relief=tk.SUNKEN, borderwidth=1, width=50).pack(pady=self.PADY)


    def _on_recipe_select(self, selected_recipe_name):
        '''Updates internal state when a new recipe is selected.'''
        for r in self.recipes:
            if r[1] == selected_recipe_name:
                self.current_recipe_id = r[0]
                self.current_recipe_volume = r[2]
                # Updated output message to show BBL
                self.output_scaling_details.set(f"Base Volume: {r[2]} BBL\nBase Cost: ${r[3]:.2f}")
                self.output_cost_var.set("Final Cost: $0.00")
                self.output_scale_factor_var.set("--")
                break

    def _scale_and_cost(self):
        '''Callback function: executes core business logic on button click .'''
        if not self.current_recipe_id:
            messagebox.showerror("Error", "Please select a recipe first.")
            return

        try:
            # Input Validation : Ensures volume is numeric and positive
            new_volume = float(self.volume_entry.get())
            if new_volume <= services.MIN_VOLUME_BBL:
                 # Updated message to reflect BBL
                 messagebox.showerror("Error", f"New volume must be greater than {services.MIN_VOLUME_BBL} BBL.")
                 return
            
            # --- Business Logic Execution ---
            # 1. Scale the recipe
            scaled_ingredients, scale_factor = services.scale_recipe(
                self.current_recipe_id, self.current_recipe_volume, new_volume)
            
            # 2. Calculate Cost (Recursive function call
            total_cost = services.calculate_recipe_cost(scaled_ingredients)
            
            # 3. Update Output
            cost_with_markup = total_cost * services.COST_MARKUP
            
            details_str = f"Scaling Factor: {scale_factor:.2f}\n"
            requirements_str = "Ingredient Requirements:\n"
            
            # f-string formatting 
            for ing in scaled_ingredients:
                requirements_str += f"- {ing['name']}: {ing['quantity']:.2f} {ing['unit']}\n"

            self.output_cost_var.set(f"Final Estimated Cost: ${cost_with_markup:.2f}")
            self.output_scale_factor_var.set(f"Scaling Factor: {scale_factor:.2f} | Raw Ingredient Cost: ${total_cost:.2f}")
            self.output_scaling_details.set(requirements_str)
            self.scaled_ingredients = scaled_ingredients # Store for logging

        except ValueError:
            #  Graceful error handling for invalid input 
            messagebox.showerror("Input Error", "Please enter a valid numeric value for volume.")
        except Exception as e:
            messagebox.showerror("Process Error", f"An unexpected error occurred: {e}")

    def _log_batch(self):
        '''Attempts to log the current scaled recipe as a completed batch.'''
        if not hasattr(self, 'scaled_ingredients'):
            messagebox.showerror("Error", "Please scale a recipe before logging a batch.")
            return

        recipe_name = self.recipe_var.get()
        volume = float(self.volume_entry.get())
        
        # Get cost without currency symbol for storage
        final_cost_str = self.output_cost_var.get().replace('Final Estimated Cost: $', '').replace(',', '')
        final_cost = float(final_cost_str)
        
        # Execute business logic to update inventory and log batch (CRUD: Update/Create)
        success, message = services.calculate_and_log_batch(
            recipe_name, volume, final_cost, self.scaled_ingredients)
        
        if success:
            messagebox.showinfo("Success", message)
            # Refresh log view after successful logging
            self._display_batch_log()
            self._load_data() # Refresh ingredient inventory levels
        else:
            # Failure message (e.g., Insufficient Inventory)
            messagebox.showerror("Batch Failed", message)


    # -------------------- TAB 2: INVENTORY MANAGER (CRUD) --------------------
    def _build_inventory_tab(self):
        '''Builds the Inventory Management tab UI (CRUD operations).'''
        
        # --- Listbox to display current inventory ---
        tk.Label(self.inventory_frame, text="Current Inventory (Double-click to Edit):", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, self.PADY))
        
        # Frame for Listbox and Scrollbar 
        listbox_frame = tk.Frame(self.inventory_frame)
        listbox_frame.pack(fill="x", pady=self.PADY)
        
        # Scrollbar 
        self.inv_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.inv_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox 
        self.inventory_listbox = tk.Listbox(listbox_frame, yscrollcommand=self.inv_scrollbar.set, selectmode=tk.SINGLE, height=10)
        self.inventory_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        self.inv_scrollbar.config(command=self.inventory_listbox.yview)
        
        self.inventory_listbox.bind('<Double-1>', self._on_inventory_edit)

        # Buttons for CRUD operations (Create/Delete)
        button_frame = tk.Frame(self.inventory_frame)
        button_frame.pack(pady=self.PADY*2)

        tk.Button(button_frame, text="Add New Ingredient", command=self._show_add_ingredient_dialog).pack(side=tk.LEFT, padx=self.PADX)
        tk.Button(button_frame, text="Delete Selected Ingredient", command=self._delete_selected_ingredient).pack(side=tk.LEFT, padx=self.PADX)

        self._display_inventory()
        
    def _display_inventory(self):
        '''Populates the inventory listbox with current data from DB.'''
        self.inventory_listbox.delete(0, tk.END) # Clear existing data
        conn = db.connect_db()
        if conn:
            # Read from DB (CRUD: Read)
            inventory = db.read_ingredients(conn)
            db.close_db(conn)
            
            for ing in inventory:
                ing_id, name, type_str, cost, detail, unit, qty = ing
                # F-string and alignment for presentation 
                display_str = f"ID:{ing_id:<3} | {name:<20} ({type_str}) | Cost: ${cost:.2f}/{unit:<4} | Stock: {qty:.2f} {unit}"
                self.inventory_listbox.insert(tk.END, display_str)

    def _show_add_ingredient_dialog(self):
        '''Shows a dialog for adding a new ingredient (CRUD: Create).'''
        AddDialog(self.master, self._display_inventory)

    def _on_inventory_edit(self, event):
        '''Handles double-click on listbox item to show edit dialog (CRUD: Update).'''
        try:
            # Get the index of the selected item
            selection = self.inventory_listbox.curselection()
            if not selection:
                return

            # Get the full string
            selected_item_str = self.inventory_listbox.get(selection[0])
            
            # Extract the ingredient ID using string slicing/splitting 
            ing_id = int(selected_item_str.split('|')[0].replace('ID:', '').strip())

            EditDialog(self.master, ing_id, self._display_inventory)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open edit dialog: {e}")

    def _delete_selected_ingredient(self):
        '''Deletes the currently selected ingredient (CRUD: Delete).'''
        try:
            selection = self.inventory_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an ingredient to delete.")
                return

            selected_item_str = self.inventory_listbox.get(selection[0])
            ing_id = int(selected_item_str.split('|')[0].replace('ID:', '').strip())
            ing_name = selected_item_str.split('|')[1].strip().split('(')[0].strip()

            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {ing_name} (ID: {ing_id})?"):
                conn = db.connect_db()
                if conn:
                    # Execute DB Delete operation
                    rows_deleted = db.delete_ingredient(conn, ing_id)
                    db.close_db(conn)
                    
                    if rows_deleted > 0:
                        messagebox.showinfo("Success", f"{ing_name} deleted successfully.")
                        self._display_inventory() # Refresh list
                    else:
                        messagebox.showwarning("Failed", "Ingredient not found or could not be deleted.")
                else:
                    messagebox.showerror("Error", "Database connection failed.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during deletion: {e}")


    # -------------------- TAB 3: BATCH LOG & EXPORT --------------------
    def _build_log_tab(self):
        '''Builds the Batch Log/Export tab UI (File I/O).'''
        
        tk.Label(self.log_frame, text="Completed Batch Log:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, self.PADY))

        # Frame for Listbox and Scrollbar 
        listbox_frame = tk.Frame(self.log_frame)
        listbox_frame.pack(fill="x", pady=self.PADY)
        
        self.log_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_listbox = tk.Listbox(listbox_frame, yscrollcommand=self.log_scrollbar.set, selectmode=tk.SINGLE, height=10)
        self.log_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        self.log_scrollbar.config(command=self.log_listbox.yview)

        # Export Button (File I/O)
        tk.Button(self.log_frame, text="Export Log to CSV", command=self._export_log, bg="#008080", fg="white", activebackground="#006666").pack(pady=self.PADY*2)

        self._display_batch_log()
        
    def _display_batch_log(self):
        '''Populates the log listbox with records from DB.'''
        self.log_listbox.delete(0, tk.END)
        conn = db.connect_db()
        if conn:
            log_data = db.get_batch_log(conn)
            db.close_db(conn)
            
            for batch in log_data:
                batch_id, name, volume, cost, date_str = batch
                # Updated volume display to BBL
                display_str = f"ID:{batch_id:<3} | {date_str} | {name:<20} | {volume:.1f} BBL | Cost: ${cost:.2f}"
                self.log_listbox.insert(tk.END, display_str)

    def _export_log(self):
        '''Callback: Calls the service function to export the log .'''
        success, message = services.export_batch_log_to_csv()
        if success:
            messagebox.showinfo("Export Success", message)
        else:
            messagebox.showerror("Export Failed", message)


# -------------------- CHILD DIALOGS FOR CRUD --------------------

class AddDialog(tk.Toplevel):
    '''A Toplevel window for adding new ingredients (CRUD: Create).'''
    def __init__(self, master, refresh_callback):
        tk.Toplevel.__init__(self, master)
        self.title("Add New Ingredient")
        self.refresh_callback = refresh_callback
        self.transient(master) # Keep dialog modal
        
        self.grab_set() # grab focus
        self.main_frame = tk.Frame(self, padx=10, pady=10)
        self.main_frame.pack()
        
        # Setup input fields. Updated units in labels.
        fields = ['Name', 'Cost (per unit, REAL)', 'Unit Type (lb, oz, packet, gal)', 'Type (Fermentable, Hop, or Other)', 'Special Detail (SRM or Alpha Acid, 0 if N/A)', 'Initial Stock Qty (REAL)']
        self.entries = {}
        for i, label in enumerate(fields):
            tk.Label(self.main_frame, text=label).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(self.main_frame, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry

        # Action Buttons
        tk.Button(self.main_frame, text="Save", command=self._save_ingredient).grid(row=len(fields), column=0, pady=10)
        tk.Button(self.main_frame, text="Cancel", command=self.destroy).grid(row=len(fields), column=1, pady=10)

        self.master.wait_window(self)

    def _save_ingredient(self):
        '''Collects and validates input, then saves to DB (Business Logic).'''
        try:
            # Input Validation 
            name = self.entries['Name'].get().strip()
            cost = float(self.entries['Cost (per unit, REAL)'].get())
            unit = self.entries['Unit Type (lb, oz, packet, gal)'].get().strip()
            ing_type = self.entries['Type (Fermentable, Hop, or Other)'].get().strip()
            detail = float(self.entries['Special Detail (SRM or Alpha Acid, 0 if N/A)'].get())
            qty = float(self.entries['Initial Stock Qty (REAL)'].get())
            
            if not name or not unit or not ing_type:
                 messagebox.showerror("Validation Error", "Name, Unit, and Type are required fields.")
                 return
            if cost <= 0 or qty < 0:
                 messagebox.showerror("Validation Error", "Cost must be positive and Quantity cannot be negative.")
                 return
            
            # Ensure type is normalized
            ing_type = ing_type.lower().capitalize()
            if ing_type not in ['Fermentable', 'Hop', 'Other']:
                messagebox.showerror("Validation Error", "Type must be 'Fermentable', 'Hop', or 'Other'.")
                return

            # Execute DB Create operation
            conn = db.connect_db()
            if conn:
                result = db.add_ingredient(conn, name, ing_type, cost, detail, unit, qty)
                db.close_db(conn)
                
                if result == "DUPLICATE_NAME":
                    messagebox.showerror("Database Error", f"Ingredient '{name}' already exists.")
                elif isinstance(result, int):
                    messagebox.showinfo("Success", f"Ingredient '{name}' added successfully.")
                    self.refresh_callback()
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save ingredient.")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for Cost, Detail, and Quantity.")
        except sqlite3.Error as e:
            # General DB error handling
            messagebox.showerror("Database Error", f"DB operation failed: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


class EditDialog(tk.Toplevel):
    '''A Toplevel window for editing ingredient inventory/cost (CRUD: Update).'''
    def __init__(self, master, ing_id, refresh_callback):
        tk.Toplevel.__init__(self, master)
        self.title(f"Edit Ingredient ID: {ing_id}")
        self.refresh_callback = refresh_callback
        self.ing_id = ing_id
        
        self.grab_set()
        self.main_frame = tk.Frame(self, padx=10, pady=10)
        self.main_frame.pack()
        
        self.current_data = self._load_current_data()
        if not self.current_data:
            messagebox.showerror("Error", "Could not load ingredient details.")
            self.destroy()
            return
            
        self._build_ui()
        self.master.wait_window(self)

    def _load_current_data(self):
        '''Reads the current data for the selected ID (CRUD: Read).'''
        conn = db.connect_db()
        if conn:
            cursor = conn.cursor()
            # Select by PK 
            cursor.execute('SELECT id, name, cost, unit, inventory_qty FROM Ingredients WHERE id = ?', (self.ing_id,))
            data = cursor.fetchone()
            db.close_db(conn)
            return data
        return None

    def _build_ui(self):
        '''Sets up the fields for editing.'''
        # Display Static Info
        unit = self.current_data[3]
        tk.Label(self.main_frame, text=f"Ingredient Name: {self.current_data[1]}", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        tk.Label(self.main_frame, text=f"Unit: {unit}", font=('Arial', 10)).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        # Fields for dynamic update
        tk.Label(self.main_frame, text="New Cost Per Unit (REAL)").grid(row=2, column=0, sticky="w")
        self.cost_entry = tk.Entry(self.main_frame, width=20)
        self.cost_entry.insert(0, str(self.current_data[2]))
        self.cost_entry.grid(row=2, column=1, padx=5, pady=5)

        # Updated label for U.S. units
        tk.Label(self.main_frame, text=f"Adjust Inventory Stock (Add/Subtract {unit})").grid(row=3, column=0, sticky="w")
        self.delta_entry = tk.Entry(self.main_frame, width=20)
        self.delta_entry.insert(0, "0.0")
        self.delta_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Display current stock
        tk.Label(self.main_frame, text=f"Current Stock: {self.current_data[4]:.2f} {unit}").grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        # Action Button
        tk.Button(self.main_frame, text="Update Inventory & Cost", command=self._update_ingredient).grid(row=5, column=0, columnspan=2, pady=10)

    def _update_ingredient(self):
        '''Executes the updates to the database (CRUD: Update).'''
        try:
            # Input Validation 
            new_cost = float(self.cost_entry.get())
            delta_qty = float(self.delta_entry.get())

            if new_cost <= 0:
                 messagebox.showerror("Validation Error", "New cost must be positive.")
                 return

            conn = db.connect_db()
            if conn:
                # Update cost (mutator equivalent)
                cursor = conn.cursor()
                cursor.execute('UPDATE Ingredients SET cost = ? WHERE id = ?', (new_cost, self.ing_id))
                conn.commit()
                
                # Update quantity (mutator equivalent)
                rows_updated = db.update_inventory_qty(conn, self.ing_id, delta_qty)
                db.close_db(conn)
                
                if rows_updated > 0:
                    messagebox.showinfo("Success", f"Ingredient ID {self.ing_id} updated successfully.")
                    self.refresh_callback()
                    self.destroy()
                else:
                    messagebox.showwarning("Failed", "Ingredient could not be updated.")
            else:
                messagebox.showerror("Error", "Database connection failed.")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for cost and stock adjustment.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
