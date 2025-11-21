# 📊 EDA Buddy — One-Click Exploratory Data Analysis

**EDA Buddy** is a clean, fast, and beginner-friendly web application that lets you explore any dataset instantly.  
Just upload a CSV file — and the app automatically shows previews, summaries, missing values, data types, and visual insights in a beautifully designed dashboard.

No Jupyter Notebook.  
No repetitive pandas code.  
Just **upload → analyze → understand**.

---

## 🌟 What is EDA Buddy?

Exploratory Data Analysis (EDA) is often the *first step* in any data science or machine learning project.

But doing EDA manually means writing code like:

python
df.head()
df.info()
df.describe()
df.isnull().sum()
Every. Single. Time.

EDA Buddy automates all of this for you.
It gives you a clean UI where you can:

Upload a CSV

Preview rows

View summary stats

Check data types

Detect missing values

See basic visualizations

Clean dataset interactively

All with one click.

🚀 Key Features
🧾 CSV Upload
Safe file validation

Handles large datasets

No backend storage (fully local)

👁 Data Preview
Scrollable, formatted table

View any number of rows

Structured column headers

📐 Dataset Overview
Shape (rows × columns)

Data types

Memory usage

Unique values

🧹 Missing Values
Null count per column

Missing value percentage

Drop-or-fill cleaning options

📊 Visual Insights
Distributions

Correlation heatmap

Count plots

Numeric summaries

🎨 Modern UI
Material-style design

Responsive layout

Smooth user interactions

Backend: Flask (Python)

Data Handling: Pandas, NumPy

Visualization: Matplotlib / Seaborn

Frontend: HTML, CSS (Material UI style), JavaScript

📥 Installation & Running the App
Here’s how anyone can run EDA Buddy locally.

1. Clone the Repository
2. Install Dependencies
Make sure you have Python installed (3.8+ recommended).
pip install -r requirements.txt
3. Run the Flask Server
python app.py
4. Open the App in Browser
Once the server starts, open:
http://127.0.0.1:5000/
Upload a CSV → Explore your dataset → Enjoy one-click EDA!

💡 Why This Project Exists
Every data science student or developer faces the same pain:

Repeating the same EDA code

Looking at unformatted pandas outputs

Struggling with messy datasets

Setting up Jupyter manually every time

EDA Buddy solves this by giving you:

A simple, interactive, beautiful, code-free experience

so you can focus on insights instead of boilerplate.

👤 Who Is It For?
Students learning Data Science

Anyone doing quick dataset validation

Developers testing CSV inputs for ML models

Teachers demonstrating EDA in class

Beginners exploring datasets for the first time
