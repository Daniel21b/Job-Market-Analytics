# Job Market Analytics: AI/ML vs General IT Trends

A comprehensive analysis examining the evolution of job postings in the technology sector, comparing AI/Machine Learning roles against traditional General IT positions from October 2023 to October 2024.

## Project Overview

This project analyzes over 4,000 technology job postings to understand market trends, growth patterns, and company positioning in the AI hiring landscape. The analysis addresses the research question: **Is the job market for AI/ML roles growing faster than traditional IT roles?**

## Data Sources

- **Hacker News "Who is hiring?" threads** - Monthly job posting threads from October 2023 to October 2024
- **Adzuna Job Search API** - Technology-related job postings from 2023-2024

Total records analyzed: 4,137 technology job postings after data cleaning and processing.

## Project Structure

```
Job-Market-Analytics/
├── notebooks/
│   ├── 01_scraping_hackernews.ipynb      # Web scraping HN job threads
│   ├── 02_api_data_collection.ipynb      # Adzuna API data collection
│   ├── 03_data_cleaning.ipynb            # Data cleaning and preprocessing
│   ├── 04_company_standardization.ipynb  # Company name standardization
│   ├── 05_job_role_categorization.ipynb  # Job role classification
│   ├── 06_time_series_analysis.ipynb     # Time series and statistical analysis
│   ├── 07_final_report.ipynb             # Comprehensive final report
│   └── data/
│       ├── raw/                          # Raw data files
│       └── processed/                    # Cleaned and processed data
├── index.html                            # HTML version of final report (GitHub Pages)
├── requirements.txt                      # Python dependencies
└── README.md                             # This file
```

## Key Features

- **Web scraping** of Hacker News job threads using BeautifulSoup
- **API integration** with Adzuna job search platform
- **Data cleaning pipeline** with deduplication and standardization
- **Intelligent job categorization** using keyword-based scoring (AI/ML, General IT, Hybrid, Non-Tech)
- **Time series analysis** with statistical validation
- **Company positioning analysis** identifying AI-focused vs traditional IT companies
- **Comprehensive visualizations** and interactive dashboards

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Jupyter Notebook or JupyterLab

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Job-Market-Analytics.git
cd Job-Market-Analytics
```

2. Create a virtual environment (recommended):
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install required packages:
```bash
pip install pandas numpy matplotlib scipy beautifulsoup4 requests jupyter
```

## Usage

### Running the Analysis

Execute the notebooks in sequence:

```bash
jupyter notebook
```

Then run notebooks in order:
1. `01_scraping_hackernews.ipynb` - Scrape job data from Hacker News
2. `02_api_data_collection.ipynb` - Collect data from Adzuna API
3. `03_data_cleaning.ipynb` - Clean and preprocess data
4. `04_company_standardization.ipynb` - Standardize company names
5. `05_job_role_categorization.ipynb` - Categorize jobs by role type
6. `06_time_series_analysis.ipynb` - Perform statistical analysis
7. `07_final_report.ipynb` - View comprehensive final report

### Viewing the Report

The final report is available as an HTML page:

**Online:** Visit the GitHub Pages deployment at `https://yourusername.github.io/Job-Market-Analytics/`

**Locally:** Open `index.html` in your web browser

## Methodology

### Data Collection
- Web scraping using BeautifulSoup for HTML parsing
- API integration with pagination and checkpoint saves
- Date range: October 2023 - October 2024 (13 months)

### Data Cleaning
- Deduplication based on company, role, and location
- Date standardization to unified datetime format
- Missing value handling with strategic dropping
- Text preprocessing and company name standardization

### Job Categorization

Jobs are classified into four categories using a keyword-based scoring system:

- **AI/ML Roles:** Machine learning engineers, data scientists, AI researchers
- **General IT Roles:** Software engineers, DevOps, web developers, cloud engineers
- **Hybrid Roles:** MLOps engineers, AI platform engineers
- **Non-Tech Roles:** Healthcare, retail, administrative positions

Categorization uses 130+ keyword patterns across technologies, frameworks, and role titles.

### Statistical Analysis

- Linear regression for trend analysis
- Mann-Kendall test for monotonic trends
- Pearson correlation coefficients
- T-tests for comparing time periods
- Month-over-month growth rate calculations

## Key Findings

### Market Composition
- AI/ML roles represent a significant portion of the technology job market
- General IT roles continue to dominate overall tech hiring
- Hybrid roles emerging as distinct category bridging both domains

### Trends
- Both AI/ML and General IT show temporal variation over the analysis period
- Clear company stratification between AI-heavy and traditional IT approaches
- Market dynamics remain fluid with month-to-month variation

### Company Positioning
- Identified top companies leading AI/ML talent acquisition
- Clear distinction between AI-first and traditional IT hiring strategies
- Concentration of AI hiring among specific technology companies

### Statistical Validation
- Linear regression analysis reveals growth patterns
- Statistical significance tested at alpha = 0.05
- Comprehensive hypothesis testing for all research questions

## Technologies Used

- **Python 3.11** - Primary programming language
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Matplotlib** - Data visualization
- **Scipy** - Statistical analysis
- **BeautifulSoup** - Web scraping
- **Requests** - HTTP library for API calls
- **Jupyter** - Interactive notebook environment

## Limitations

- 13-month timeframe may not capture long-term trends
- Sample size of 4,137 jobs is representative but not comprehensive
- Data source bias toward tech-forward companies and startups
- Keyword-based categorization may have false positives/negatives
- Geographic focus primarily on US-based postings
- Public job listings only (excludes referrals and private hiring)

## Future Work

Potential areas for expansion:
- Extend data collection to 24-36 months
- Add additional data sources (LinkedIn, Indeed, Glassdoor)
- Implement ML classification using pre-trained language models
- Geographic and regional analysis
- Salary and compensation trend analysis
- Skills demand analysis by technology stack
- Industry-specific comparisons (tech vs healthcare vs finance)

## License

This project is available for educational and research purposes.

## Acknowledgments

- **Hacker News** "Who is hiring?" community for public job postings
- **Adzuna** for providing job search API access
- Open-source Python community for excellent data science tools

## Contact

For questions or feedback about this analysis, please open an issue in this repository.

---

**Last Updated:** October 2024  
**Analysis Period:** October 2023 - October 2024  
**Total Jobs Analyzed:** 4,137

