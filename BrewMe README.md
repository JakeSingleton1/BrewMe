Jacob Singleton - A0506849
# BrewMe Brewery Batch & Inventory System
## Run main.py to run the app
### Project Structure
#### BrewMe
#### ├── data/
#### │   └── brewme.db  (Created automatically on first run)
#### ├── db.py
#### ├── gui.py
#### ├── main.py
#### ├── models.py
#### └── services.py

1. Business Concept

Company: Lone Man Mountain Brewing (My place of work)

Operations Summary: Lone Man Mountain produces craft beer and sells it through our taproom located at Wimberley Valley Winery. Operations involve complex scaling of over 10 different beer recipes for different batch sizes, requiring precise inventory control.

Problem Solved: The software automates proportional scaling of beer recipes for production. It tracks inventory consumption for our brewer and generates cost-per-barrel (BBL) estimates and scaling factor (new batch volume / original recipe volume), addressing the operational problem of inconsistent batches and ingredient stocking.



2. Classes & Inheritance 

Superclass: Ingredient (models common attributes like name and cost)

Subclasses: Fermentable (inherits from Ingredient, specialized for malt color/SRM) and Hop (inherits from Ingredient, specialized for alpha acid percentage).

Primary Class: Recipe (aggregates ingredients and provides methods for scaling).


3. Database Integration (SQLite3) 

Database File: data/brewme.db (automatically created/opened on startup).

Ingredients: Stores current inventory.

Recipes: Stores the master recipe list.

Recipe_Details: A link table defining quantities of ingredients per recipe.

Batch_Log: Tracks historical brews.


4. GUI (tkinter) 

Simple GUI (gui.py) using tkinter widgets (Label, Entry, Button, Frame, StringVar).

Graceful error handling with try-excepts

5. Business Logic & Advanced Function

Core Logic: Scaling calculations are performed in services.py . Used common measurements used by brewers in the united states such as BBL or beer barrels, which is equivalent to 31 gallons, as well as gallons , pounds and ounces.

6. File I/O 

Added a feature to export the entire brewing batch log to a CSV file for reports. Included a batch number, recipe name, volume, cost and the date of the brew.


7. Recursive Function: The calculate_recipe_cost function in services.py uses recursion to calculate the total estimated cost of all ingredients in a scaled batch.

