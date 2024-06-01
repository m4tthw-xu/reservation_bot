import os

from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
MONGO_URL = os.getenv('MONGO_URL')
print(MONGO_URL)

client = MongoClient(MONGO_URL)

# Select the database and collection
db = client["reservation_bot_database"]
restaurants_collection = db["restaurant-data"]

def add_restaurant(name, tags, link):
    """Add a new restaurant to the database"""
    restaurant_doc = {
        "name": name,
        "tags": tags,
        "link": link
    }
    result = restaurants_collection.insert_one(restaurant_doc)
    return result.inserted_id

def update_restaurant(name, updates):
    """Update an existing restaurant document"""
    result = restaurants_collection.update_one({"name": name}, {"$set": updates})
    return result.modified_count

def get_restaurant(name):
    """Retrieve a restaurant document by name"""
    result = restaurants_collection.find_one({"name": name})
    return result

def add_property_to_all_restaurants(property_name, property_value):
    """Add a new property to all existing restaurants"""
    result = restaurants_collection.update_many({}, {"$set": {property_name: property_value}})
    return result.modified_count

def delete_restaurant(name):
    """Delete a restaurant document by name"""
    result = restaurants_collection.delete_one({"name": name})
    return result.deleted_count

def delete_property_from_all_restaurants(property_name):
    """Delete a property from all existing restaurants"""
    result = restaurants_collection.update_many({}, {"$unset": {property_name: ""}})
    return result.modified_count

# Example usage:
restaurant_name = "The Okay Bistro"
restaurant_tags = ["American", "Coarse Dining", "Posh"]
restaurant_link = "https://www.thefancybistro.com"

add_restaurant(restaurant_name, restaurant_tags, restaurant_link)

updates = {"rating": 3.5}
update_restaurant(restaurant_name, updates)
#
# restaurant = get_restaurant(restaurant_name)
# print(restaurant)
#
# add_property_to_all_restaurants("cuisine", "French")

# delete_restaurant("The Fancy Bistro")

# delete_property_from_all_restaurants("cuisine")

# Close the client
client.close()