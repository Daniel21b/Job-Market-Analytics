# GitHub Pages Setup Instructions

## Your Report is Ready!

The file `index.html` in the root directory contains your complete Job Market Analytics report with:
- All markdown content
- All code cells with syntax highlighting
- All code outputs preserved
- No emojis
- Self-contained HTML (no external dependencies needed)

## How to Deploy to GitHub Pages

### Option 1: Deploy from Root Directory

1. **Commit the HTML file:**
   ```bash
   git add index.html
   git commit -m "Add final report HTML for GitHub Pages"
   git push
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Click `Settings` > `Pages`
   - Under "Source", select `Deploy from a branch`
   - Select branch: `main` (or `master`)
   - Select folder: `/ (root)`
   - Click `Save`

3. **Access your page:**
   - Your report will be available at: `https://yourusername.github.io/Job-Market-Analytics/`
   - It may take 1-2 minutes to deploy

### Option 2: Deploy from docs/ Directory (Recommended)

1. **Create docs directory and move HTML:**
   ```bash
   mkdir -p docs
   mv index.html docs/
   git add docs/
   git commit -m "Add final report to docs folder for GitHub Pages"
   git push
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Click `Settings` > `Pages`
   - Under "Source", select `Deploy from a branch`
   - Select branch: `main` (or `master`)
   - Select folder: `/docs`
   - Click `Save`

3. **Access your page:**
   - Your report will be available at: `https://yourusername.github.io/Job-Market-Analytics/`

## Customization (Optional)

### Change the Page Title
The current title is "07_final_report". To change it:
1. Open `index.html` in a text editor
2. Find the `<title>` tag near the top
3. Change it to your preferred title (e.g., "Job Market Analytics Report")
4. Save and commit

### Add Custom CSS
You can add custom styling by inserting CSS in the `<head>` section of the HTML file.

### Troubleshooting

**Issue: Page not loading**
- Wait 2-3 minutes after enabling GitHub Pages
- Check that the file is named `index.html` (lowercase)
- Verify the file is in the correct directory

**Issue: Styles not showing**
- The HTML is self-contained and should work without external resources
- Check browser console for errors (F12)

**Issue: Images not displaying**
- Note: The referenced PNG files (dashboard, charts) don't exist yet
- Run the previous analysis notebooks to generate them
- Or remove those image display cells from the notebook before conversion

## File Information

- **File:** `index.html`
- **Size:** ~326 KB
- **Format:** HTML5 with embedded CSS
- **Dependencies:** None (self-contained)
- **Browser Support:** All modern browsers

## Next Steps

1. Choose deployment option (root or docs/)
2. Commit and push the HTML file
3. Enable GitHub Pages in repository settings
4. Share your report URL!

## Regenerating the HTML

If you need to update the report:

```bash
# Convert notebook to HTML
jupyter nbconvert --to html notebooks/07_final_report.ipynb --output=index.html

# Remove emojis (if needed)
python -c "
import re
with open('notebooks/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
pattern = re.compile('[\\U0001F600-\\U0001F64F\\U0001F300-\\U0001F5FF\\U0001F680-\\U0001F6FF\\U0001F1E0-\\U0001F1FF\\U00002702-\\U000027B0\\U000024C2-\\U0001F251\\U00002190-\\U000021FF\\U00002600-\\U000026FF\\U00002700-\\U000027BF\\U0001F900-\\U0001F9FF\\U0001FA00-\\U0001FA6F\\U0001FA70-\\U0001FAFF\\U00002300-\\U000023FF]+', flags=re.UNICODE)
cleaned = pattern.sub('', content)
with open('notebooks/index.html', 'w', encoding='utf-8') as f:
    f.write(cleaned)
"

# Move to root or docs
mv notebooks/index.html ./
```

