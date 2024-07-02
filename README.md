# Resy Reservation Assistant

An automated tool that simplifies the process of making restaurant reservations on Resy based on natural language user input.

## Features

- Natural language processing of user prompts
- Integration with OpenAI for prompt interpretation
- Automated web navigation using Selenium
- Calendar integration for checking user availability
- Automated reservation booking on Resy

## How It Works

1. User inputs a reservation request in natural language
2. The input is processed by an OpenAI assistant and converted to JSON format
3. Selenium-based automation searches for available reservation times on Resy
4. The tool checks the user's calendar for availability
5. If a suitable time is found, the reservation is automatically booked
