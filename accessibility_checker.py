from playwright.sync_api import sync_playwright
from weasyprint import HTML, CSS
import tempfile
import os
from datetime import datetime
import json

def check_accessibility(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Navigate to the URL
        page.goto(url)
        
        # Inject axe-core
        page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js')
        
        # Run accessibility check
        results = page.evaluate('''() => {
            return axe.run(document.body);
        }''')
        
        # Take screenshots of issues
        screenshots = []
        for violation in results.get('violations', []):
            # Take screenshot of the page
            screenshot_path = os.path.join(tempfile.gettempdir(), f'issue_{len(screenshots)}.png')
            page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append({
                'path': screenshot_path,
                'description': violation.get('description', ''),
                'impact': violation.get('impact', '')
            })
        
        browser.close()
        
        # Generate PDF report
        report_html = generate_report_html(url, results, screenshots)
        report_path = os.path.join(tempfile.gettempdir(), f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
        HTML(string=report_html).write_pdf(report_path)
        
        # Clean up screenshots
        for screenshot in screenshots:
            os.remove(screenshot['path'])
        
        return report_path

def generate_report_html(url, results, screenshots):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .issue {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; }}
            .screenshot {{ max-width: 100%; margin-top: 10px; }}
            .timestamp {{ color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Accessibility Report</h1>
            <p>URL: {url}</p>
            <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>Summary</h2>
        <p>Total Issues Found: {len(results.get('violations', []))}</p>
        
        <h2>Issues</h2>
        {generate_issues_html(results.get('violations', []), screenshots)}
    </body>
    </html>
    '''

def generate_issues_html(violations, screenshots):
    html = ''
    for i, violation in enumerate(violations):
        screenshot = screenshots[i] if i < len(screenshots) else None
        html += f'''
        <div class="issue">
            <h3>{violation.get('description', 'Unknown Issue')}</h3>
            <p><strong>Impact:</strong> {violation.get('impact', 'Unknown')}</p>
            <p><strong>Help:</strong> {violation.get('help', 'No help available')}</p>
            {f'<img class="screenshot" src="{screenshot["path"]}" alt="Issue Screenshot">' if screenshot else ''}
        </div>
        '''
    return html 