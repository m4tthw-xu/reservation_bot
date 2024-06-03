# this file will work with the collection of data from the resy website
# mainly, interfacing the collection of data and tagging the restaurant using AI, then storing
# that information into a csv file

import resy_scraper
# import gpt_test
import asyncio
import db_manager

async def main():
    city_url = "https://resy.com/cities/austin-tx/search?date=2024-06-05&seats=2&facet=cuisine:New%20American"  # Define your city URL
    city = "austin-tx"
    date = "2024-06-07"
    seats = 2

    # restaurants = await resy_scraper.scrape_all_restaurant_names_and_links(city_url)
    # print(restaurants)

    await db_manager.create_tags()


if __name__ == "__main__":
    asyncio.run(main())