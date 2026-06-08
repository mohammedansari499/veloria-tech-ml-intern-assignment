# Task 2 – Cricket Match Winner Prediction Using Machine Learning

## Overview

For Task 2 of the Veloria Tech AI/ML Internship Assignment, I built a machine learning model that predicts the winning team of a cricket match using historical cricket match data.

The purpose of this task was not simply to train a model, but to demonstrate an understanding of the complete machine learning workflow:

* Loading and understanding data
* Cleaning and preparing datasets
* Creating meaningful features
* Selecting an appropriate algorithm
* Training and evaluating a model
* Interpreting results

The final implementation uses a **Random Forest Classifier** built using Scikit-Learn.

---

# Assignment Objective

According to the assignment brief, the goal was to use cricket match data and build a model capable of predicting the winner of a match based on historical patterns. The assignment specifically required:

* Data preparation and cleaning
* Feature selection
* Model building
* Accuracy evaluation
* F1 score evaluation
* Confusion matrix generation

This project was developed to satisfy all of those requirements while maintaining readability and clear documentation.

---

# Dataset Used

The dataset used for this task is:

**cricket_data.csv**

The dataset contains historical cricket match information collected from publicly available cricket records.

The data includes both categorical and numerical information related to match progression and match outcomes.

Examples of available information include:

* Batting team
* Bowling team
* Venue
* Toss winner
* Toss decision
* Innings number
* Runs scored
* Wickets lost
* Balls faced
* Match winner

---

# My Approach

## Step 1 – Data Loading

The project begins by loading the dataset using Pandas.

During development I encountered several issues involving:

* Incorrect file paths
* Dataset location mismatches
* CSV loading errors

These problems were resolved by verifying project structure and ensuring the dataset was loaded correctly before training.

---

## Step 2 – Data Cleaning

Real-world datasets are rarely perfect.

Before training the model, I performed several cleaning operations.

### Removing Invalid Match Results

Rows containing missing winner information were removed.

Examples included:

* Empty values
* NA
* N/A
* Null-like records

This ensured that every training example had a valid target value.

### Handling Missing Numerical Values

For numerical columns, missing values were replaced using the median value of the respective column.

I chose median replacement because it is generally less affected by extreme values than the mean.

### Handling Missing Categorical Values

For categorical fields, missing entries were replaced with:

"Unknown"

This allowed me to preserve potentially useful records rather than dropping them entirely.

---

## Step 3 – Feature Selection

The next step was deciding which information should be provided to the model.

I selected the following features:

### Team Information

* Batting Team
* Bowling Team

### Venue Information

* Match Venue

### Toss Information

* Toss Winner
* Toss Decision

### Match Progress Information

* Innings
* Over
* Total Runs
* Team Runs
* Team Wickets
* Balls Faced

I selected these features because they capture both:

* Pre-match context
* Match progression information

which can influence match outcomes.

---

## Step 4 – Feature Encoding

Machine learning models cannot directly process text values.

Several columns contained textual information such as:

* Team names
* Venue names
* Toss decisions

To convert these into numerical form, I used:

**LabelEncoder**

This transformed categorical values into integer representations while preserving consistency across the dataset.

The target variable (match winner) was also encoded before training.

---

# Why I Chose Random Forest

The assignment allowed the use of:

* Logistic Regression
* Random Forest
* XGBoost

After researching the strengths of each algorithm, I decided to use:

## Random Forest Classifier

Reasons for choosing Random Forest:

* Works well on structured tabular datasets
* Handles mixed numerical and categorical features
* Generally performs well without extensive tuning
* Reduces overfitting compared to a single decision tree
* Provides feature importance scores
* Easy to interpret and explain

Since this project involved a mixture of cricket statistics and categorical match information, Random Forest was a suitable choice.

---

# Model Configuration

The model was configured using:

* 200 Decision Trees
* Maximum Depth = 15
* Minimum Samples per Leaf = 5
* Balanced Class Weights
* Random State = 42

I also enabled multi-core processing to improve training speed.

The goal was to balance:

* Accuracy
* Training efficiency
* Generalization

rather than aggressively tuning the model for maximum performance.

---

# Train-Test Split

To evaluate performance fairly, the dataset was divided into:

### Training Set

80% of the data

Used for learning patterns.

### Testing Set

20% of the data

Used only for evaluation.

I used a stratified split so that class distributions remained similar across both datasets.

---

# Model Evaluation

After training, the model was evaluated using three metrics required by the assignment.

---

## Accuracy Score

Accuracy measures the percentage of predictions that were correct.

This provides a straightforward indication of overall model performance.

---

## F1 Score

F1 Score balances:

* Precision
* Recall

This metric is particularly useful when class distributions are not perfectly balanced.

---

## Confusion Matrix

The confusion matrix shows:

* Correct predictions
* Incorrect predictions
* Team-specific prediction behavior

This provides deeper insight than accuracy alone.

---

## Classification Report

A full classification report was generated including:

* Precision
* Recall
* F1 Score
* Support

for every team in the dataset.

This helped identify strengths and weaknesses of the model across different classes.

---

# Feature Importance Analysis

One advantage of Random Forest is that it provides feature importance scores.

After training, the model calculates how much each feature contributes to prediction decisions.

This helped answer questions such as:

* Which match factors influence outcomes most?
* Does venue have a strong impact?
* How important is toss information?
* Do runs and wickets contribute more than pre-match features?

The feature importance output provided valuable insight beyond simple prediction accuracy.

---

# Challenges I Faced

This project involved several practical challenges.

### Dataset Integration

The dataset structure did not perfectly align with initial assumptions, requiring adjustments to preprocessing logic.

### Missing Data

Some records contained incomplete information that needed to be handled carefully.

### Feature Selection

Choosing useful features required experimentation and understanding of cricket match dynamics.

### Path and Environment Issues

During development I encountered:

* CSV path errors
* Package installation issues
* Virtual environment setup problems

These issues required debugging before model training could proceed successfully.

### Understanding Model Outputs

Interpreting confusion matrices and classification reports was an important part of the learning process.

---

# Use of AI and External Resources

Throughout this project I used AI tools, documentation, and online references as learning resources and development in the building process.

AI was primarily used for:

* Understanding unfamiliar machine learning concepts
* Reviewing preprocessing logic
* Debugging errors
* Explaining model evaluation metrics
* Identifying potential flaws in implementation
* Generating starter templates and examples

However, the project required significant manual work involving:

* Reading assignment requirements
* Preparing the dataset
* Running experiments
* Troubleshooting errors
* Validating outputs
* Adjusting the workflow
* Interpreting results

The final implementation reflects both independent development effort and responsible use of available learning resources.

---

# Skills Demonstrated

This project demonstrates practical experience with:

* Python
* Pandas
* NumPy
* Scikit-Learn
* Data Cleaning
* Data Preprocessing
* Feature Engineering
* Machine Learning Classification
* Random Forest Models
* Model Evaluation
* Confusion Matrix Analysis
* F1 Score Evaluation
* Debugging
* Problem Solving

---

# Conclusion

This task provided valuable hands-on experience in applying machine learning concepts to a real sports dataset.

Rather than focusing solely on building a model, the project emphasized understanding the entire machine learning pipeline—from data preparation and feature engineering to model training, evaluation, and interpretation.

The experience reinforced the importance of clean data, thoughtful feature selection, systematic debugging, and clear documentation when developing practical machine learning solutions.