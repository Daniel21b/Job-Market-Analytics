# 🚀 Streamlit Quick Start Guide

## Run Your Dashboard Locally

```bash
# Step 1: Activate your virtual environment
source env/bin/activate  # macOS/Linux
# OR
env\Scripts\activate     # Windows

# Step 2: Install new Streamlit dependencies
pip install -r requirements.txt

# Step 3: Run your dashboard
streamlit run dashboard.py
```

Your dashboard will open automatically at **http://localhost:8501** 🎉

---

## 📁 What Was Created

```
Job-Market-Analytics/
├── 📊 dashboard.py                    # ← YOUR EMPTY STREAMLIT APP (ready for code!)
├── 📁 .streamlit/
│   └── config.toml                    # Streamlit theme & settings
├── 📋 requirements.txt                # Updated with Streamlit dependencies
├── 🔧 .gitignore                      # Git ignore for Streamlit cache
├── 🚀 Procfile                        # For Heroku deployment
├── ⚙️  setup.sh                        # Setup script for cloud deployment
├── 📖 STREAMLIT_DEPLOYMENT.md         # Full deployment guide
└── 📖 QUICKSTART.md                   # This file!
```

---

## ✅ Next Steps

### 1. Build Your Dashboard
Open `dashboard.py` and start coding! Here's a starter template:

```python
import streamlit as st
import pandas as pd

st.title("🔍 Job Market Analytics Dashboard")

# Load your data
df = pd.read_csv("notebooks/data/processed/jobs_cleaned.csv")

# Display insights
st.write(f"Total Jobs Analyzed: {len(df):,}")
st.dataframe(df.head())
```

### 2. Test Locally
```bash
streamlit run dashboard.py
```

### 3. Deploy to Cloud
Choose your platform:
- **Streamlit Cloud** (Easiest): [share.streamlit.io](https://share.streamlit.io)
- **Heroku**: Use the included `Procfile`
- **Docker**: See `STREAMLIT_DEPLOYMENT.md`

---

## 🎨 Customize Your Theme

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#0052CC"        # Change to your brand color
backgroundColor = "#FFFFFF"
textColor = "#262730"
```

---

## 📚 Helpful Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Plotly Charts](https://plotly.com/python/)

---

## 🐛 Common Issues

**Port already in use?**
```bash
streamlit run dashboard.py --server.port=8502
```

**Module not found?**
```bash
pip install -r requirements.txt --upgrade
```

**Need to clear cache?**
```bash
streamlit cache clear
```

---

**Happy coding! 🎉**

