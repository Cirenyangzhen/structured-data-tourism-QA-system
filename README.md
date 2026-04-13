# Smart Tourism QA System (Text-to-SQL with LLM)

An intelligent question-answering system that allows users to query tourism information using natural language.
This project integrates large language models (LLMs) with structured databases to convert user queries into executable SQL statements.

---

## Project Overview

Tourism information is often scattered across multiple platforms, making it difficult for users to quickly find accurate and structured answers.

This project solves the problem by building an **end-to-end Text-to-SQL system** that:

* Understands natural language questions
* Converts them into SQL queries using an LLM
* Retrieves structured results from a database
* Displays answers through an interactive web interface

---

## Tech Stack

* **Python**
* **SQLite** (structured database)
* **OpenAI GPT-4 API** (Text-to-SQL generation)
* **Streamlit** (web interface)
* **Scrapy** (data collection & crawling)

---

## System Architecture

The system consists of four main components:

1. **Data Layer**

   * Tourism data collected via web scraping (Scrapy)
   * Cleaned and stored in SQLite database

2. **LLM Layer**

   * GPT-4 generates SQL queries from natural language
   * Prompt engineering + few-shot learning used to improve accuracy

3. **Backend Logic**

   * SQL execution
   * Database connection and query handling

4. **Frontend Interface**

   * Built with Streamlit
   * Users input questions and receive real-time results
<img width="1024" height="1536" alt="86b374ff-555a-4852-903e-6ab780f9dedf" src="https://github.com/user-attachments/assets/11d519b8-d237-433b-96a0-cb84ac4effae" />

---

## Example

**User Input:**

> "What are the top-rated attractions in Linzhi?"

**Generated SQL:**

```sql
SELECT name, rating
FROM attractions
WHERE rating > 4.5
ORDER BY rating DESC;
```

**Output:**

* List of high-rated tourist attractions

---

## Dataset

* Data collected from tourism platforms (e.g., Ctrip)
* Includes:

  * Attractions
  * Ratings
  * Opening hours
  * User reviews

---

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/Cirenyangzhen/structured-data-tourism-QA-system.git
cd structured-data-tourism-QA-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the app

```bash
streamlit run src/codexdb/gui.py YOUR_OPENAI_API_KEY YOUR_DATA_DIR
```

---

## Demo
## Homepage
The system provides an intuitive web-based interface built with Streamlit.  
Users can input natural language questions related to tourism, and the system will automatically generate SQL queries and return structured results.
![c8cf381a9989644167038bbe400aeff2](https://github.com/user-attachments/assets/fb8ffd2a-4746-41eb-931f-3c6fcad729e7)

> Note: The current interface is displayed in Chinese, but the system logic and functionality are language-independent. 

---

## Example Query
Below is an example of how the system processes a user query:

- **User Question:**  
  "Which attractions in Linzhi have a rating above 4.5?"

- **System Process:**  
  The system converts the natural language question into a SQL query using GPT-4.

- **Output:**  
  A list of attractions that satisfy the condition is returned from the SQLite database.
![87fbf9387681d9aea26750e6ddc3eb37.bmp](https://github.com/user-attachments/files/26677295/87fbf9387681d9aea26750e6ddc3eb37.bmp)

---

## Key Features

* Natural Language → SQL (Text-to-SQL)
* LLM-powered query generation
* Structured tourism database
* Interactive web interface
* Prompt engineering optimization

---

## Future Improvements

* Multi-turn conversational queries
* RAG (Retrieval-Augmented Generation)
* Cloud deployment (AWS / Docker)
* Support for multiple cities

---

## Author

* CIRENYANGZHEN
* BSc Computer Science, Wuhan University

---

## Notes

This project is adapted from CodexDB and extended for a smart tourism QA use case.

Key improvements include:
- Integration of tourism dataset (Linzhi, Tibet)
- Prompt engineering for Text-to-SQL tasks
- Streamlit-based user interface
- SQLite-based structured query system
