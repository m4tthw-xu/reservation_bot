# this file will work with the collection of data from the resy website
# mainly, interfacing the collection of data and tagging the restaurant using AI, then storing
# that information into a csv file

import resy_scraper
# import gpt_test
import asyncio

async def main():
    city_url = "https://resy.com/cities/austin-tx/search?date=2024-05-31&seats=2&facet=cuisine:American"  # Define your city URL
    city = "austin-tx"
    date = "2024-06-01"
    seats = 2

    restaurants = await resy_scraper.scrape_all_restaurant_names_and_links(city_url)
    print(restaurants)

    for res in restaurants:
        print(res['name'])
        desc = await resy_scraper.scrape_restaurant_descriptions(res['link'])
        res['descriptions'] = desc
        print(desc)
        print()

    # print(restaurants)







if __name__ == "__main__":
    asyncio.run(main())