
# Juilliard Event Scraper

## Overview

This project consists of a simple Python script designed to scrape event data from [The Juilliard School&#39;s performance calendar](https://www.juilliard.edu/stage-beyond/performance/calendar). It's configured to interact with a Supabase Postgres database instance, enabling efficient storage and retrieval of event information.

## Features

- Scrapes event details from The Juilliard School's official performance calendar webpage.
- Stores event data in a structured format in a Supabase Postgres database.
- Offers customization options for targeting specific event types or dates.

## Requirements

Before running the script, ensure you have the following installed:

- Python 3.6 or later
- `requests` for making HTTP requests
- `beautifulsoup4` for parsing HTML content
- `supabase` Python client for interacting with the Supabase database

You can install these dependencies via pip:

```bash
pip install requests beautifulsoup4 supabase
```
