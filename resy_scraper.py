import asyncio
import datetime
import urllib

from pyppeteer import launch


# this function will take a resy page and get all the names of the restaurants on that page
# input: url of resy page with tiles
# output: a list of restaurant names
async def scrape_all_restaurant_names_and_links(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)  # Replace with the actual URL

    # Wait for the elements containing the restaurant names to be rendered
    await page.waitForSelector('.SearchResult__venue-name')

    # Extract all restaurant names and links
    restaurant_data = await page.evaluate('''() => {
        const elements = document.querySelectorAll('.SearchResult__title--container a');
        return Array.from(elements).map(element => {
            return {
                name: element.querySelector('.SearchResult__venue-name').innerText,
                link: element.href,
                descriptions: ''
            };
        });
    }''')

    await browser.close()

    return restaurant_data

def convert_to_military_time(time_str):
    # Parse the time string with AM/PM format
    time_obj = datetime.datetime.strptime(time_str, '%I:%M %p')
    # Convert to 24-hour format and return as string
    return time_obj.strftime('%H:%M')

# this function will scrape all the reservation buttons on a restaurant's page for the times
# input: url of restaurant page on resy
# output: list of available times that restaurant can be booked for, and their seat types
# NOTE: this function is not headless
async def scrape_reservation_buttons(url):
    browser = await launch(headless=False)  # Set headless=False to see the browser actions
    page = await browser.newPage()
    await page.goto(url)

    # Wait for a specific element that indicates the page has loaded the content

    try:
        await page.waitForSelector('.ShiftInventory__shift', timeout=2000)  # Wait for up to 60 seconds
    except:
        print("Reservation Times: []")
        await browser.close()
        return

    # Extract reservation button details
    reservation_buttons = await page.evaluate('''() => {
        const buttons = document.querySelectorAll('.ReservationButton.Button.Button--primary');
        return Array.from(buttons).map(button => ({
            time: button.querySelector('.ReservationButton__time').innerText,
            type: button.querySelector('.ReservationButton__type').innerText
        }));
    }''')

    # Convert times to military time
    for button in reservation_buttons:
        button['time'] = convert_to_military_time(button['time'])

    # print('Reservation Times:', reservation_buttons)

    await browser.close()

    return reservation_buttons

# this function will take a restaurant name, city-state, date (YYYY-MM-DD), and # of seats,
# and outputs a url to search for
# input: name, city, date, seats
# output: url that has the available seat times for the specific criteria, empty if none
def build_reservation_url(link, restaurant_name, city_state, date, seats):
    """
    Constructs a reservation URL for a specified restaurant, location, date, and party size.

    Args:
        restaurant_name: The name of the restaurant.
        city_state: The city and state abbreviation (e.g., "austin-tx").
        date: The desired reservation date in YYYY-MM-DD format.
        seats: The number of people in the reservation party.

    Returns:
        The fully constructed reservation URL.
    """

    # Handle Restaurant Name (Same as before)
    restaurant_name = restaurant_name.lower().replace("- ", "-")
    restaurant_name = restaurant_name.lower().replace(" -", "-")
    restaurant_name = restaurant_name.lower().replace(" ", "-")
    restaurant_name = restaurant_name.lower().replace("&", "and")
    restaurant_name = restaurant_name.lower().replace("+", "and")
    restaurant_name = restaurant_name.lower().replace("'", "")
    # restaurant_name = urllib.parse.quote(restaurant_name)  # Optional encoding

    # Construct the Base URL
    base_url = f"https://resy.com/cities/{city_state}/venues/{restaurant_name}"

    # Add Query Parameters
    query_params = {
        "date": date,
        "seats": seats
    }

    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[4] = urllib.parse.urlencode(query_params)

    # Assemble the Final URL
    reservation_url = urllib.parse.urlunparse(url_parts)

    return reservation_url


def update_url(url, new_date, new_seats):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parts = new_date.split('/')

    # need YYYY-MM-DD from MM/DD/YYYY

    date = parts[2] + '-' + parts[0] + '-' + parts[1]

    # Parse the URL into components
    parsed_url = urlparse(url)

    # Parse the query parameters
    query_params = parse_qs(parsed_url.query)

    # Update the date and seats parameters
    query_params['date'] = [date]
    query_params['seats'] = [str(new_seats)]

    # Reconstruct the query string
    new_query_string = urlencode(query_params, doseq=True)

    # Construct the new URL
    new_url = urlunparse(parsed_url._replace(query=new_query_string))

    return new_url


# this function will scrape the descriptions of restaurant pages in order to gather data and generate tags
# input: webpage url
# output: a list of size 3 of descriptions about the restaurant
async def scrape_restaurant_descriptions(url):
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.goto(url)

    # Check for error element
    error_selector = ".ErrorView"
    try:
        error_element = await page.waitForSelector(error_selector, timeout=5000)  # Adjust the timeout as needed
        if error_element:
            print("Error page detected. Stopping scraping.")
            await browser.close()
            return []
    except Exception as e:
        # If the error element is not found, continue with scraping
        pass

    description_selectors = [
        ".VenuePage__why-we-like-it__body",
        "#clamped-content-need-to-know",
        "#clamped-content-about-venue"
    ]

    descriptions = []
    for selector in description_selectors:
        try:
            element = await page.waitForSelector(selector, timeout=1000)
            text = await page.evaluate("(element) => element.textContent", element)
            descriptions.append(text.strip())
        except Exception as e:
            print(f"Error getting description for selector '{selector}': {e}")

    await browser.close()
    return descriptions




# miscellaneous testing code below...


# city_search = 'https://resy.com/cities/houston-tx/search?date=2024-05-29&seats=2&activeView=list'
# # rest_info = 'https://resy.com/cities/austin-tx/venues/launderette?date=2024-05-31&seats=2'
#
# # scrapes a page listing a bunch of restaurants in a city
# restaurants = asyncio.get_event_loop().run_until_complete(scrape_all_restaurant_names(city_search))
#
# # print(restaurants)
#
# # scrapes a restaurants page to get available reservations
# # asyncio.get_event_loop().run_until_complete(scrape_reservation_buttons(rest_info))
#
#
# # for name in restaurants:
# #     resy_url = build_reservation_url(name, 'houston-tx', '2024-06-05', 2)
# #     print(resy_url)
#     # asyncio.get_event_loop().run_until_complete(scrape_reservation_buttons(resy_url))
#
# # Example usage (replace with the actual URL):
# url = "https://resy.com/cities/austin-tx/venues/lin-asian-bar-and-dim-sum?date=2024-06-05&seats=2"
# descriptions = asyncio.run(scrape_restaurant_descriptions(url))
#
# # Now, process the 'descriptions' array with your AI model
# print(descriptions)  # Display the extracted descriptions
