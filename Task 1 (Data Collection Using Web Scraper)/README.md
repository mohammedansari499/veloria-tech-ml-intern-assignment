# Cricket Match Data Scraper – HowStat.com

## Project Overview

This project was made as an assesment to the assesment for the Internship at Veloria Tech ML internship position to collect cricket Test match data from HowStat.com and generate a structured dataset for further analysis and machine learning applications.

The main goal was to automatically retrieve the latest completed Test matches, extract important match information, identify the highest scorer in each match, and store the results in a clean CSV format.

The final resulted output of this project is:

**match_data.csv**

which contains match's information such as teams, venue, match result, and top scorer details.

---

# About This Project

I built this project as a practical web scraping and data collection exercise. The task initially seemed straightforward, but it quickly became more challenging due to website structure changes, scorecard formatting differences, and Cloudflare protection firewalls.

Throughout development, I created multiple versions of the scraper, tested different approaches, debugged numerous parsing issues, and gradually improved the extraction logic until the final dataset was generated successfully.

I used AI tools primarily as a reference and debugging assistant. 
it helped me:
* Understand unfamiliar HTML structures
* Identify flaws in parsing logic
* Suggest alternative scraping approaches
* Debug errors and exceptions
* Improve code organization
* Generate boilerplate and template structures

However, the actual implementation, testing, troubleshooting, and iterative improvements was performed throughout the development process by repeatedly analyzing outputs, validating results, and refining the scraper.

---

# Project Objective

The objective was to:

* Access match data from HowStat.com
* Retrieve the most recent completed Test matches
* Open individual scorecards
* Extract match information
* Determine the highest run scorer in each match
* Generate a structured CSV dataset

---

# Final Deliverable

## match_data.csv

This is the primary output produced by the project.

The dataset contains:

| Column           | Description                   |
| ---------------- | ----------------------------- |
| Sl No.           | Match number                  |
| Match Date       | Date of match                 |
| Team 1           | First team                    |
| Team 2           | Second team                   |
| Stadium Name     | Venue name                    |
| Stadium Location | Venue location                |
| Match Result     | Final result                  |
| Top Scorer Name  | Highest scorer in the match   |
| Top Scorer Runs  | Runs scored by the top scorer |

This dataset can be used for:

* Cricket analytics
* Exploratory data analysis
* Visualization projects
* Machine learning experiments
* Sports data research

---

# Development Process

## Understanding the Website

Before writing the scraper, I explored HowStat's structure to understand:

* Match listing pages
* Scorecard pages
* Country filters
* Venue information
* Batting scorecards

During this stage I inspected page source code, analyzed HTML elements, and experimented with different extraction techniques.

---

## Initial Scraper Development

The first versions used:

* Requests
* BeautifulSoup

The goal was to retrieve match lists and parse scorecard information directly from HTML.

Although basic extraction worked, several issues appeared:

* Missing scorecard data
* Incorrect match filtering
* Parsing failures
* Unexpected page structures

---

## Cloudflare and Access Issues

One of the biggest challenges was dealing with website protection mechanisms.

To investigate the problem, I created several helper and testing scripts that allowed me to:

* Capture raw responses
* Save HTML pages locally
* Inspect returned content
* Compare expected vs actual page output

This helped identify situations where the website was returning protection pages instead of cricket data.

---

## Browser Automation Experiments

To overcome some access issues, I developed a Selenium-based scraper.

This version automated browser actions such as:

* Opening the website
* Selecting countries from dropdown menus
* Submitting forms
* Navigating scorecards

While effective, Selenium increased complexity and execution time, so I continued exploring alternative approaches.

---

## Cloudscraper Implementation

After testing multiple methods, I experimented with Cloudscraper.

This approach provided:

* Better compatibility with protected pages
* Faster execution
* Reduced dependency on browser automation
* Simpler deployment

Several versions of the scraper were developed and tested before reaching a stable implementation.

---

## – Match Filtering Logic

A significant portion of the project involved ensuring that only valid completed matches were collected.

The scraper was designed to include:

* Matches won by either team
* Drawn matches
* Tied matches

And exclude:

* Future matches
* Scheduled matches
* Live matches
* In-progress matches
* Abandoned matches
* No-result matches

This ensured that the final dataset only contained completed Test matches.

---

## Scorecard Parsing

The scorecard extraction process required extensive testing.

The scraper was enhanced to identify:

* Team names
* Match dates
* Stadium names
* Stadium locations
* Match results
* Batting records

Since scorecards contained multiple innings and different layouts, several parsing strategies were tested and refined.

---

## Top Scorer Extraction

One of the most important features of the project was determining the highest scorer in a match.

To achieve this, the scraper:

1. Reads batting tables from all innings.
2. Extracts player names and runs scored.
3. Ignores non-player rows.
4. Compares scores across all innings.
5. Selects the highest individual score.

Rows such as the following were excluded:

* Extras
* Total
* Did Not Bat
* Fall of Wickets
* Yet To Bat

The final result is stored in:

* Top Scorer Name
* Top Scorer Runs

within the dataset.

---

# Project Files

## Task 1 files

### match_data.csv

The final dataset generated by the scraper.

### scraper.py

The primary scraper implementation used to generate the final dataset.

Features include:

* Country filtering
* Match extraction
* Scorecard parsing
* Top scorer detection
* CSV generation

---

## Development and Experimental Files

Several files were created during development for testing, experimentation, and debugging purposes.

### howstat_scraper.py

Selenium-based implementation used for browser automation experiments.

### scraper_fewerrors.py

Intermediate version containing improvements and fixes over earlier implementations.

### scrapertest.py

Used to inspect tables and verify HTML parsing logic.

### inspecter1.py

Utility script used to inspect responses and troubleshoot extraction issues.

### test1.py

Small testing script used for request validation and debugging.

### response.html

Saved webpage response used to manually inspect returned HTML.

### scloud scaper.py

Experimental Cloudscraper-based implementation used during Cloudflare testing.

---

# Technologies Used

* Python
* BeautifulSoup
* Requests
* Cloudscraper
* Selenium
* Pandas

---

# Key Challenges Encountered

During development I encountered several challenges:

* Website protection mechanisms
* Inconsistent HTML structures
* Different scorecard layouts
* Match filtering accuracy
* Extracting batting information correctly
* Identifying the actual top scorer across multiple innings
* Debugging incomplete or unexpected responses

Each challenge required experimentation, testing, and multiple revisions before arriving at a reliable solution.

---

# What I Learned

This project helped me strengthen my understanding of:

* Web scraping
* HTML parsing
* Browser automation
* Data cleaning
* CSV dataset generation
* Error handling
* Logging and debugging
* Sports analytics data collection
* Iterative software development

More importantly, it showed me that real world scraping projects often require much more than simply sending requests and extracting text. 
Understanding website behavior, validating data, and repeatedly refining extraction logic were critical parts of the process.

---

# Acknowledgement

AI tools were used as a development aid for reference, debugging support, code reviews, and template generation. They helped identify flaws, suggest improvements, and accelerate troubleshooting.

All testing, validation, experimentation, implementation decisions, and iterative development were carried out throughout the project workflow to achieve the final working solution.