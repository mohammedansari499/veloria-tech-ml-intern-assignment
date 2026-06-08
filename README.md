# veloria-tech-ml-intern-assignment
Veloria Tech Internship Tasks 1 and 2


# Overall Tasks Conclusion

This assignment provided me with an opportunity to work through two important areas of data driven software development: **data collection** and **machine learning**.

---

## Task 1 Summary – Cricket Data Collection

In Task 1, I developed a web scraping solution to collect cricket match information from publicly available sources.

The objective was to retrieve the latest completed Test matches for selected teams and extract important information such as:

* Match date
* Team names
* Stadium details
* Match results
* Top scorer information

Although the final output appears simple, the development process involved significant experimentation and troubleshooting.

During implementation, I explored multiple approaches including:

* Requests
* BeautifulSoup
* Cloudscraper
* Selenium

I encountered several real-world challenges such as:

* Website protection mechanisms
* Cloudflare responses
* Dynamic page structures
* Inconsistent scorecard layouts
* Data extraction failures

To solve these issues, I created multiple test scripts, inspected HTML responses, validated extracted data, and refined parsing logic until the scraper produced reliable results.

The final result was a structured dataset stored in:

**match_data.csv**

which serves as the foundation for further analysis and machine learning applications.

---

## Task 2 Summary – Match Winner Prediction Model

In Task 2, I used cricket match data to build a machine learning model capable of predicting match winners.

The goal was not simply to train a classifier, but to demonstrate an understanding of the complete machine learning pipeline.

The workflow included:

* Data loading
* Data cleaning
* Feature selection
* Feature encoding
* Model training
* Performance evaluation
* Result interpretation

I selected a **Random Forest Classifier** because it performs well on structured datasets, handles mixed feature types effectively, and provides feature importance information that helps explain model behavior.

The model was trained using cricket-related features such as:

* Batting team
* Bowling team
* Venue
* Toss winner
* Toss decision
* Match progression statistics

The final implementation generates:

* Accuracy Score
* F1 Score
* Confusion Matrix
* Classification Report
* Feature Importance Analysis

This allowed me not only to measure predictive performance but also to better understand which factors contribute most to match outcomes.

---

## Challenges Faced Across Both Tasks

One of the biggest lessons from this assignment was understanding that real-world projects rarely work perfectly on the first attempt.

Throughout development I encountered challenges involving:

### Data Collection

* Website protection systems
* Parsing inconsistencies
* Missing data
* HTML structure changes

### Machine Learning

* Dataset cleaning
* Missing values
* Feature preparation
* Environment setup
* Package installation issues
* File path problems
* Model evaluation interpretation

Many of these issues required repeated testing, debugging, and refinement before arriving at a working solution.

---

## Use of AI and Learning Resources

During this assignment I used AI tools, documentation, and online resources as development aids.

AI was primarily used for:

* Understanding unfamiliar concepts
* Reviewing logic
* Debugging errors
* Explaining machine learning metrics
* Suggesting alternative approaches
* Providing template structures

However, AI was not used as a replacement for understanding the work.

A significant amount of time was spent:

* Reading documentation
* Testing different implementations
* Investigating errors
* Comparing outputs
* Verifying results
* Improving code quality

The final project reflects both independent problem-solving and responsible use of modern development tools.

---

## Technical Skills Applied

This assignment allowed me to apply and strengthen practical skills in:

### Programming

* Python

### Data Collection

* Web Scraping
* HTML Parsing
* Browser Automation

### Data Processing

* Pandas
* NumPy
* CSV Handling

### Machine Learning

* Scikit-Learn
* Feature Engineering
* Random Forest Classification
* Model Evaluation

### Software Development

* Debugging
* Logging
* Error Handling
* Project Documentation
* Iterative Development

---

## Key Takeaways

The most valuable aspect of this assignment was learning how different stages of a data project connect together.

I started by collecting raw data from the web, transformed it into a structured dataset, and then used that data to train and evaluate a machine learning model.

This process demonstrated that successful machine learning projects depend not only on model selection but also on:

* Data quality
* Reliable data collection
* Proper preprocessing
* Careful validation
* Clear documentation

---

## Final Reflection

This assignment provided practical exposure to both data engineering and machine learning workflows.

From building a scraper capable of navigating real-world website challenges to developing a predictive model using historical cricket data, the project reinforced the importance of persistence, experimentation, and systematic problem-solving.

More importantly, it showed me that developing effective software solutions is often an iterative process involving continuous learning, debugging, and improvement.

And I chose not to attempt Task 3 as I am currently learning Retrieval-Augmented Generation (RAG), vector embeddings, and semantic search concepts from the ground up. While I understand the basic idea behind embeddings and vector databases, I do not yet feel confident enough to build and submit a solution that I cannot fully explain or justify during evaluation.

Rather than producing a partially understood implementation, I decided to focus on completing Tasks 1 and 2 to the best of my ability while continuing to study RAG concepts independently. Once I have a stronger understanding of vector embeddings, semantic retrieval, and tools such as Sentence Transformers and ChromaDB, I intend to revisit this task and build a complete solution with a clear understanding of how each component works.

Overall, this project helped strengthen both my technical skills and my confidence in approaching real-world AI and data-related problems independently.