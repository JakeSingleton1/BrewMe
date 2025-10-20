#BrewMe Batch & Inventory Optimizer - models.py
#Defines the core classes for ingredients and recipes.


class Ingredient:
    '''
    Superclass modeling generic ingredient properties.
    All ingredients must have a name, unit, and cost per unit.
    '''
    #  attributes are hidden/private with '__' prefix 
    
    def __init__(self, name, unit_type, cost_per_unit):
        '''Constructor to initialize the ingredient.'''
        self.__name = name
        self.__unit = unit_type 
        self.__cost_per_unit = cost_per_unit

    def get_name(self):
        '''Accessor: returns the ingredient's name.'''
        return self.__name

    def get_unit(self):
        '''Accessor: returns the unit of measure (e.g., 'lb', 'oz', 'packet').'''
        return self.__unit
    
    def get_cost(self):
        '''Accessor: returns the cost per standard unit.'''
        return self.__cost_per_unit
    
    def set_cost(self, new_cost):
        '''Mutator: sets a new cost per unit .'''
        self.__cost_per_unit = new_cost

    def get_details(self):
        '''Returns basic details for database storage or display.'''
        return [self.__name, 'Base', self.__cost_per_unit, 0.0, self.__unit]
    
    def __str__(self):
        '''Returns a formatted string of the object's state '''
        return f"Ingredient: {self.__name} | Cost: ${self.__cost_per_unit:.2f}/{self.__unit}"


class Fermentable(Ingredient):
    '''
    Subclass for fermentable materials (like malt).
    Specialized by adding a color attribute (SRM).
    '''
    def __init__(self, name, unit_type, cost_per_unit, color_srm):
        '''Constructor: calls superclass __init__ and initializes subclass attribute.'''
        # explicit superclass __init__ call.
        Ingredient.__init__(self, name, unit_type, cost_per_unit)
        self.__color_srm = color_srm 

    def get_color(self):
        '''Accessor: returns the color value (SRM).'''
        return self.__color_srm
    
    def get_details(self):
        '''Overrides superclass method to include specialized attribute.'''
        return [self.get_name(), 'Fermentable', self.get_cost(), self.__color_srm, self.get_unit()]


class Hop(Ingredient):
    '''
    Subclass for hop varieties.
    Specialized by adding an alpha acid attribute.
    '''
    def __init__(self, name, unit_type, cost_per_unit, alpha_acid):
        '''Constructor: calls superclass __init__ and initializes specialized attribute.'''
        Ingredient.__init__(self, name, unit_type, cost_per_unit)
        self.__alpha_acid = alpha_acid

    def get_alpha_acid(self):
        '''Accessor: returns the alpha acid percentage.'''
        return self.__alpha_acid

    def get_details(self):
        '''Overrides superclass method to include specialized attribute.'''
        return [self.get_name(), 'Hop', self.get_cost(), self.__alpha_acid, self.get_unit()]


class Recipe:
    '''
    Models a master beer recipe, aggregating ingredients and volumes.
    This class demonstrates composition (holding Ingredient objects).
    '''
    def __init__(self, name, target_volume_BBL, ingredients_list):
        '''Constructor for a recipe object.'''
        self.__name = name
        self.__target_volume_BBL = target_volume_BBL # The base volume for the recipe
        # Ingredients stored as: {Ingredient_ID: quantity_needed}
        self.__ingredients = ingredients_list 

    def get_name(self):
        '''Accessor: returns the recipe name.'''
        return self.__name

    def get_target_volume(self):
        '''Accessor: returns the planned volume (in BBL).'''
        return self.__target_volume_BBL

    def get_ingredients(self):
        '''Accessor: returns the dictionary of ingredients (for details/DB access).'''
        return self.__ingredients
    
    def set_target_volume(self, new_volume):
        '''Mutator: sets a new target volume.'''
        self.__target_volume_BBL = new_volume

# --- Helper function to instantiate and seed initial data ---
def create_initial_ingredients():
    '''Creates initial Ingredient objects (Fermentable, Hop, etc.) for database seeding.'''
    # Adjusted units/costs for US brewing standards: Fermentables in lb, Hops/Spices in oz.
    return [
        Fermentable('Pilsner Malt', 'lb', 1.00, 2.0),
        Fermentable('Pale Malt', 'lb', 1.10, 4.0),
        Fermentable('Munich Malt', 'lb', 1.20, 10.0),
        Fermentable('Crystal Malt 40L', 'lb', 1.30, 40.0),
        Fermentable('Chocolate Malt', 'lb', 1.50, 350.0), 
        Fermentable('Pumpkin Puree', 'lb', 0.75, 0.0), 
        Fermentable('Oats', 'lb', 0.90, 1.0), 
        Fermentable('Wheat Malt', 'lb', 1.15, 2.5), 
        Fermentable('Flaked Barley', 'lb', 0.95, 1.0), 
        Fermentable('Lactose', 'lb', 1.80, 0.0), 
        
        Hop('Saaz Hops', 'oz', 0.50, 3.0), 
        Hop('Magnum Hops', 'oz', 0.45, 12.0), 
        Hop('Cascade Hops', 'oz', 0.40, 5.5), 
        Hop('Centennial Hops', 'oz', 0.55, 10.0), 
        Hop('Citra Hops', 'oz', 0.60, 12.0), 
        Hop('Willamette Hops', 'oz', 0.48, 5.0), 
        Hop('Coriander', 'oz', 0.30, 0.0), 
        Hop('Orange Peel', 'oz', 0.35, 0.0), 
        
        Ingredient('Lager Yeast', 'packet', 5.50),
        Ingredient('Ale Yeast', 'packet', 5.00),
        Ingredient('Belgian Yeast', 'packet', 6.00),
        Ingredient('Coffee Beans', 'oz', 0.15), 
        Ingredient('Pumpkin Spice Blend', 'oz', 0.10), 
        Ingredient('Mango Puree', 'gal', 12.00) # Puree often measured in gallons for commercial use
    ]

def create_initial_recipes(ingredient_id_map):
    '''
    Creates initial Recipe objects based on the menu using BBLs and lbs/oz.
    Ingredient IDs are mapped from the database after seeding.
    '''
    recipes = []
    base_volume = 15.0 # Example: 15 Barrel (BBL) batch size for a standard tank

    # 1. Bohemian Pilsner
    recipes.append(Recipe('Bohemian Pilsner', base_volume, {
        ingredient_id_map['Pilsner Malt']: 600.0, # lb
        ingredient_id_map['Saaz Hops']: 15.0,    # oz
        ingredient_id_map['Lager Yeast']: 4.0    # packet
    }))

    # 2. American Lager
    recipes.append(Recipe('American Lager', base_volume, {
        ingredient_id_map['Pale Malt']: 550.0,     # lb
        ingredient_id_map['Magnum Hops']: 5.0,     # oz (bittering)
        ingredient_id_map['Cascade Hops']: 8.0,    # oz (flavor/aroma)
        ingredient_id_map['Lager Yeast']: 4.0      # packet
    }))

    # 3. Imperial Pumpkin Ale
    recipes.append(Recipe('Imperial Pumpkin Ale', base_volume, {
        ingredient_id_map['Pale Malt']: 800.0,          # lb
        ingredient_id_map['Munich Malt']: 120.0,        # lb
        ingredient_id_map['Pumpkin Puree']: 25.0,       # lb
        ingredient_id_map['Magnum Hops']: 10.0,         # oz
        ingredient_id_map['Willamette Hops']: 15.0,     # oz
        ingredient_id_map['Lactose']: 30.0,             # lb
        ingredient_id_map['Pumpkin Spice Blend']: 5.0,  # oz
        ingredient_id_map['Ale Yeast']: 4.0             # packet
    }))

    # 4. IPA
    recipes.append(Recipe('IPA', base_volume, {
        ingredient_id_map['Pale Malt']: 750.0,         # lb
        ingredient_id_map['Crystal Malt 40L']: 40.0,   # lb
        ingredient_id_map['Magnum Hops']: 8.0,         # oz (bittering)
        ingredient_id_map['Centennial Hops']: 30.0,     # oz
        ingredient_id_map['Citra Hops']: 20.0,          # oz
        ingredient_id_map['Ale Yeast']: 4.0             # packet
    }))

    # 5. Belgian Witbier
    recipes.append(Recipe('Belgian Witbier', base_volume, {
        ingredient_id_map['Wheat Malt']: 400.0,     # lb
        ingredient_id_map['Pale Malt']: 250.0,      # lb
        ingredient_id_map['Coriander']: 3.0,        # oz
        ingredient_id_map['Orange Peel']: 3.0,      # oz
        ingredient_id_map['Magnum Hops']: 3.0,      # oz (light bittering)
        ingredient_id_map['Belgian Yeast']: 4.0     # packet
    }))

    # 6. Imperial Stout-Nitro
    recipes.append(Recipe('Imperial Stout-Nitro', base_volume, {
        ingredient_id_map['Pale Malt']: 1000.0,       # lb
        ingredient_id_map['Chocolate Malt']: 150.0,     # lb
        ingredient_id_map['Flaked Barley']: 75.0,      # lb
        ingredient_id_map['Magnum Hops']: 15.0,       # oz
        ingredient_id_map['Ale Yeast']: 5.0           # packet
    }))
    
    # 7. Coffee Stout-Nitro
    recipes.append(Recipe('Coffee Stout-Nitro', base_volume, {
        ingredient_id_map['Pale Malt']: 700.0,          # lb
        ingredient_id_map['Oats']: 70.0,               # lb
        ingredient_id_map['Chocolate Malt']: 100.0,     # lb
        ingredient_id_map['Lactose']: 20.0,             # lb
        ingredient_id_map['Magnum Hops']: 6.0,          # oz
        ingredient_id_map['Coffee Beans']: 10.0,       # oz (10 oz post-fermentation)
        ingredient_id_map['Ale Yeast']: 4.0             # packet
    }))

    # 8. Oktoberfest
    recipes.append(Recipe('Oktoberfest', base_volume, {
        ingredient_id_map['Munich Malt']: 750.0,        # lb
        ingredient_id_map['Pilsner Malt']: 150.0,       # lb
        ingredient_id_map['Magnum Hops']: 8.0,          # oz
        ingredient_id_map['Saaz Hops']: 5.0,            # oz
        ingredient_id_map['Lager Yeast']: 4.0           # packet
    }))

    # 9. Mango Wheat
    recipes.append(Recipe('Mango Wheat', base_volume, {
        ingredient_id_map['Wheat Malt']: 400.0,         # lb
        ingredient_id_map['Pale Malt']: 300.0,          # lb
        ingredient_id_map['Citra Hops']: 12.0,          # oz
        ingredient_id_map['Mango Puree']: 1.5,          # gal (added post-fermentation)
        ingredient_id_map['Ale Yeast']: 4.0             # packet
    }))
    
    # 10. Bomb Pop Blonde
    recipes.append(Recipe('Bomb Pop Blonde', base_volume, {
        ingredient_id_map['Pale Malt']: 650.0,          # lb
        ingredient_id_map['Wheat Malt']: 70.0,          # lb
        ingredient_id_map['Cascade Hops']: 10.0,        # oz
        ingredient_id_map['Ale Yeast']: 3.0             # packet
    }))
    
    # Coming Soon: Schwarzbier (Placeholder)
    recipes.append(Recipe('Schwarzbier (Coming Soon)', base_volume, {
        ingredient_id_map['Pilsner Malt']: 450.0,       # lb
        ingredient_id_map['Munich Malt']: 200.0,        # lb
        ingredient_id_map['Chocolate Malt']: 50.0,      # lb
        ingredient_id_map['Magnum Hops']: 7.0,          # oz
        ingredient_id_map['Lager Yeast']: 4.0           # packet
    }))

    return recipes

if __name__ == '__main__':
    # Simple test for class creation and inheritance output
    pale_malt = Fermentable('2-Row Pale Malt', 'lb', 1.50, 3.5)
    cascade = Hop('Cascade', 'oz', 0.12, 6.0)
    
    print(pale_malt)
    print(f"Color: {pale_malt.get_color()}")
    print(cascade)
    print(f"Alpha Acid: {cascade.get_alpha_acid()}%")
