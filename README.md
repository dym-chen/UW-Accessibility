# Accessibility & Git Comparison Tool

A Flask-based web application that provides two main functionalities:

1. Website accessibility checking with PDF report generation
2. Git repository comparison between commits

## Features

### Accessibility Checker

- Input any website URL to check for accessibility issues
- Uses Playwright with axe-core for comprehensive accessibility testing
- Generates downloadable PDF reports with screenshots and issue details
- Highlights accessibility violations with visual markers

### Git Repository Comparator

- Compare any Git repository's current state with a previous commit
- Supports custom branch selection
- Optional commit hash specification
- Displays detailed diff information for changed files

## Prerequisites

- Python 3.8 or higher
- Git
- Chrome/Chromium browser (for Playwright)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:

```bash
playwright install chromium
```

## Usage

1. Start the Flask application:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

3. Use the web interface to:
   - Check website accessibility by entering a URL
   - Compare Git repositories by providing the repository URL and optional parameters