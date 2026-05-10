# 🚀 NLytics - AI Business Analytics Assistant

## 📌 Problem Statement

Business users and developers waste time writing SQL queries manually to extract insights from data. 

**NLytics solves this by converting plain English questions into MySQL/SQLite queries instantly, running them live, and visualizing results with AI-generated business insights — making data analytics accessible to everyone.**

---

## ✨ Key Features

✅ **Natural Language to SQL** - Ask questions in English, get SQL queries automatically  
✅ **Live Query Execution** - Run queries on real databases instantly  
✅ **Interactive Visualizations** - Auto-generated Plotly charts for results  
✅ **Query History** - Track and reuse previous queries  
✅ **Data Explorer** - Browse databases, explore tables, inspect schemas  
✅ **CSV Export** - Download query results for further analysis  
✅ **AI Insights** - Get business insights powered by OpenAI  

---

## 🏗️ Project Structure

```
NLytics/
│
├── app.py              # Main Streamlit application (entry point)
├── ai.py               # OpenAI integration (NL → SQL conversion)
├── db.py               # Database connection & query execution
├── schema.py           # Database schema inspector & formatter
├── charts.py           # Plotly visualization & chart rendering
├── load_data.py        # Data loading script (train.xlsx → SQLite)
│
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (API keys)
├── .gitignore         # Git ignore rules (never commit .env!)
├── README.md          # This file
│
└── train.xlsx         # Your dataset (Excel file)
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit |
| **Database** | SQLite / MySQL |
| **AI/LLM** | OpenAI API (GPT-3.5-turbo) |
| **Visualization** | Plotly |
| **Data Processing** | Pandas, NumPy |
| **ORM** | SQLAlchemy |

---

## 🚀 Getting Started

### **Step 1: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 2: Configure OpenAI API Key**

1. Get your API key: https://platform.openai.com/api_keys
2. Edit `.env` file:
   ```
   OPENAI_API_KEY=sk-your_key_here
   ```

### **Step 3: Load Data into Database**

```bash
python load_data.py
```

This will:
- Read `train.xlsx`
- Create SQLite database (`nlytics.db`)
- Create `train` table with your data
- Show a preview

**Output should look like:**
```
📂 Loading train.xlsx...
✅ File loaded: 1000 rows, 15 columns
✅ Data loaded into table 'train'
```

### **Step 4: Start the App**

```bash
streamlit run app.py
```

Then open: http://localhost:8501

---

## 📖 Usage Examples

### **Example 1: Simple Count Query**

**You ask:** "How many records are in the dataset?"

**NLytics generates:** 
```sql
SELECT COUNT(*) as total_records FROM train;
```

**Result:** Shows count + chart

---

### **Example 2: Filtering & Aggregation**

**You ask:** "What are the top 5 categories by total sales?"

**NLytics generates:**
```sql
SELECT category, SUM(sales) as total_sales 
FROM train 
GROUP BY category 
ORDER BY total_sales DESC 
LIMIT 5;
```

**Result:** Table + bar chart visualization

---

### **Example 3: Complex Analysis**

**You ask:** "Show me the monthly revenue trend for the last year"

**NLytics generates:**
```sql
SELECT 
    strftime('%Y-%m', date) as month,
    SUM(revenue) as total_revenue 
FROM train 
WHERE date >= date('now', '-1 year')
GROUP BY month 
ORDER BY month;
```

**Result:** Table + line chart showing trend

---

## 🔍 Features Explained

### **Tab 1: Query (Main Feature)**
- Type your question in plain English
- NLytics converts to SQL automatically
- Shows generated SQL for transparency
- Executes query on live database
- Displays results in table + chart
- Download results as CSV

### **Tab 2: Data Explorer**
- Browse all tables in database
- View table statistics (row count, columns)
- Preview data with configurable row limit
- Inspect column names and data types

### **Tab 3: Query History**
- View all previous queries
- See questions, SQL, and results
- Reuse queries later

### **Tab 4: Settings**
- Check database connection status
- Verify OpenAI API configuration
- View database schema info
- About NLytics

---

## 🛠️ Development & Testing

### **Test AI Module**
```bash
python ai.py
```

Tests OpenAI connection and generates sample SQL.

### **Inspect Database Schema**
```bash
python schema.py
```

Shows all tables, columns, and sample data.

### **Debug Database**
```bash
python -c "from db import get_database_schema; print(get_database_schema())"
```

---

## 📊 Query Capabilities

✅ **Supported:**
- SELECT queries with WHERE, GROUP BY, ORDER BY
- Aggregations: COUNT, SUM, AVG, MIN, MAX
- Joins between tables (if schema allows)
- LIMIT, OFFSET for pagination
- Basic mathematical operations

❌ **Not Supported (by design):**
- INSERT, UPDATE, DELETE (read-only)
- Complex stored procedures
- User-defined functions
- Very large result sets (auto-limited to 100K rows)

---

## 🔐 Security Considerations

- **Never commit `.env` file** - contains API keys
- **Queries are read-only** - no data modification
- **API calls are logged** - review your OpenAI usage regularly
- **Database contains business data** - secure appropriately

---

## 🐛 Troubleshooting

### **Error: "No tables found"**
```
Solution: Run python load_data.py
```

### **Error: "OpenAI API key not found"**
```
1. Edit .env file
2. Add: OPENAI_API_KEY=sk-your_key_here
3. Reload Streamlit (press R)
```

### **Error: "Failed to generate SQL"**
```
1. Check API key is valid
2. Check your OpenAI account has credits
3. Try simpler question first
```

### **Error: "Query execution failed"**
```
1. Check SQL syntax in the SQL display
2. Verify column names exist (use Data Explorer)
3. Try again with clearer question
```

---

## 🚀 Next Steps (Hackathon Phase)

During the hackathon, you can add:

1. **Auto SQL Correction** - If first query fails, AI fixes it
2. **Business Insights** - AI generates insights from results
3. **Query Explanations** - Explain what queries do
4. **Advanced Visualizations** - Heatmaps, advanced charts
5. **Follow-up Questions** - Ask follow-up questions about results
6. **Query Optimization** - AI suggests better queries
7. **Export Reports** - Generate PDF/Excel reports
8. **Scheduled Queries** - Auto-run queries on schedule

---

## 📝 Code Quality

All code follows best practices:
- ✅ Full docstrings on all functions
- ✅ Type hints for parameters
- ✅ Error handling & logging
- ✅ Modular, reusable functions
- ✅ Comments explaining logic
- ✅ Clean, readable naming conventions

---

## 📚 Learning Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **OpenAI API:** https://platform.openai.com/docs
- **SQL Tutorial:** https://www.w3schools.com/sql
- **Plotly Docs:** https://plotly.com/python

---

## 🎯 Success Metrics

Your hackathon project is successful if:

✅ App opens and runs without errors  
✅ Database loads successfully  
✅ Natural language questions convert to SQL  
✅ Queries execute and return results  
✅ Charts visualize results correctly  
✅ User interface is intuitive  
✅ Code is well-documented  

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review error messages carefully
3. Test individual modules: `python db.py`, `python ai.py`
4. Verify `.env` configuration
5. Check Streamlit console for detailed logs

---

## 🎓 Built For Hackathons

This project is designed to be:
- **Quick to setup** - Get running in 10 minutes
- **Hackathon-friendly** - Focus on AI workflow, not infrastructure
- **Portfolio-worthy** - Impressive project for LinkedIn/interviews
- **Extensible** - Easy to add features during hackathon
- **Production-light** - No complex deployment needed

---

**Happy analyzing! 📊✨**
