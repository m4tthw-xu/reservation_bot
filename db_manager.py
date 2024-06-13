import os
import gpt_test
import resy_scraper

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

    if restaurants_collection.find_one({"name": name}):
        print(f"Error: {name} already exists in the database.")
        return

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

def add_links(restaurants):
    for restaurant in restaurants:
        add_restaurant(name=restaurant['name'], tags=[], link=restaurant['link'])

def delete_all_restaurants():
    """Delete all documents from the restaurant collection"""
    result = restaurants_collection.delete_many({})
    print(f"{result.deleted_count} entries deleted")
    return

async def populate_descriptions():
    cursor = restaurants_collection.find({})
    for document in cursor:
        print(document['name'])
        print(document['link'])

        if (document['description'] != []):
            print(document['description'])
            continue

        desc = await resy_scraper.scrape_restaurant_descriptions(document['link'])
        print(desc)

        updates = {"description": desc}
        update_restaurant(document['name'], updates)

        print()


# NOTE: running this function calls the OpenAI API, which costs money lol
async def create_tags():
    cursor = restaurants_collection.find({})

    for document in cursor:
        print(document['name'])

        if (document['description'] == [] or document['tags'] != []):
            print('either there are already tags, or no description data')
            continue

        # print(document['description'])
        desc = ''
        for segment in document['description']:
            # print(segment)
            desc = desc + " " + segment

        # the desc has all the description data for that particular restaurant
        # we can feed this description into the OpenAI assistant and get tags for each description

        tags = gpt_test.get_tags(desc)
        # tags = "Texas Seasonal Farm-to-table Sustainable Locally-sourced Shareable Craft-beer Wine Cocktails Creative Valet"

        tags_arr = tags.split(" ")
        print(tags_arr)

        updates = {"tags": tags_arr}
        update_restaurant(document['name'], updates)


# Example usage:

# rest1 = get_restaurant('Lenoir')
# rest2 = get_restaurant('Kinfolk')
#
# print(rest1['tags'])
# print(rest2['tags'])

# delete_all_restaurants()


# restaurant_name = "Odd Duck"
# restaurant_tags = ["American", "Coarse Dining", "Posh"]
# restaurant_link = "https://www.thefancybistro.com"
#
# add_restaurant(restaurant_name, restaurant_tags, restaurant_link)
#
# updates = {"rating": 3.5}
# update_restaurant(restaurant_name, updates)
# #
# # restaurant = get_restaurant(restaurant_name)
# # print(restaurant)
# #
# # add_property_to_all_restaurants("cuisine", "French")
#
# # delete_restaurant("The Fancy Bistro")
#
# # delete_property_from_all_restaurants("cuisine")
#
# # Close the client
# client.close()