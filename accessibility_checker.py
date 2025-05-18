from playwright.sync_api import sync_playwright
from weasyprint import HTML, CSS
from datetime import datetime
import tempfile
import os
import json
import base64

def check_accessibility(url):
    with sync_playwright() as p:
        # Launch browser with optimized settings
        browser = p.chromium.launch(
            headless=True,
        )
        # Create a new context with optimized settings
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            java_script_enabled=True,
            ignore_https_errors=True
        )
        page = context.new_page()
        
        # Navigate to the URL
        page.goto(url)
        
        # Get the path to axe.min.js
        current_dir = os.path.dirname(os.path.abspath(__file__))
        axe_path = os.path.join(current_dir, 'axe.min.js')
        
        # Inject axe-core from local file
        with open(axe_path, 'r') as f:
            axe_script = f.read()
            page.evaluate(axe_script)
        
        # Run accessibility check
        results = page.evaluate('''() => {
            return axe.run(document.body);
        }''')
        
        # Take screenshots of issues
        screenshots = []
        for violation in results.get('violations', []):
            for index, node in enumerate(violation.get('nodes', [])):
                for target in node.get('target', []):
                    target_selector = json.dumps(target)  # safely encode string
                    label_text = json.dumps(str(index + 1))   # safely encode string
                    
                    page.evaluate(f'''
                    (() => {{
                        const elements = document.querySelectorAll({target_selector});
                        elements.forEach(element => {{
                            // Add styles
                            element.style.outline = "4px solid red";
                            element.style.outlineOffset = "2px";
                            element.style.position = "relative";

                            // Add label
                            const label = document.createElement('div');
                            label.innerText = {label_text};
                            label.className = 'axe-violation-label';
                            label.style.position = 'absolute';
                            label.style.top = '0';
                            label.style.left = '0';
                            label.style.transform = 'translate(-100%, -100%)'; 
                            label.style.backgroundColor = 'black';
                            label.style.color = 'white';
                            label.style.zIndex = '9999';
                            label.style.padding = '2px 4px';
                            label.style.fontSize = '12px';
                            label.style.borderRadius = '4px';
                            element.appendChild(label);
                        }});
                    }})();
                    ''')

            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=True)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            screenshots.append({
                'data': screenshot_base64,
                'description': violation.get('description', ''),
                'impact': violation.get('impact', '')
            })

            # Cleanup: remove outlines and labels
            for node in violation.get('nodes', []):
                for target in node.get('target', []):
                    target_selector = json.dumps(target)
                    page.evaluate(f'''
                    (() => {{
                        const elements = document.querySelectorAll({target_selector});
                        elements.forEach(element => {{
                            // Remove outline styles
                            element.style.outline = '';
                            element.style.outlineOffset = '';

                            // Remove the label
                            const label = element.querySelector('.axe-violation-label');
                            if (label) {{
                                element.removeChild(label);
                            }}
                        }});
                    }})();
                    ''')

        browser.close()
        
        # Generate PDF report
        report_html = generate_report_html(url, results, screenshots)
        report_path = os.path.join(tempfile.gettempdir(), f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
        HTML(string=report_html).write_pdf(report_path)
        
        return report_path

def generate_report_html(url, results, screenshots):
    violations = results.get('violations', [])
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: "Arial", sans-serif;
                margin: 0;
                padding: 0;
            }}

            h1, h2, p {{
                width: 100%;
                white-space: nowrap;
            }}

            .title-page {{
                height: 100vh;
                width: 100vw;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                page-break-after: always;
                position: relative;
            }}

            .title-page h1 {{
                font-size: 3em;
                margin-bottom: 0.5em;
            }}

            .title-page h2 {{
                font-size: 1.5em;
                color: #555;
                margin: 0.2em 0;
            }}

            .title-page p {{
                font-size: 1.2em;
                color: #777;
                margin: 0.3em 0;
            }}

            .issue {{
                page-break-before: always;
                padding: 1cm;
                box-sizing: border-box;
                border: 2px solid black;
                border-radius: 10px;
            }}

            .issue h3 {{
                font-size: 1.6em;
                margin-top: 0;
                color: #333;
            }}

            .issue p {{
                font-size: 1em;
                margin: 0.3em 0;
                color: #444;
            }}

            .screenshot-container {{
                margin-top: 1em;
                text-align: center;
            }}

            .screenshot {{
                max-width: 100%;
                max-height: 18cm;
                border: 1px solid #ccc;
                object-fit: contain;
            }}
        </style>
    </head>
    <body>
        <div class="title-page">
            <h1>Accessibility Report</h1>
            <h2>{url}</h2>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <h2>Issues Found: {len(violations)}</h2>
        </div>
        {generate_issues_html(violations, screenshots)}
    </body>
    </html>
    '''

def generate_issues_html(violations, screenshots):
    html = ''
    for i, violation in enumerate(violations):
        screenshot_html = ''
        if i < len(screenshots) and screenshots[i]:
            screenshot_html = f'''
                <div class="screenshot-container">
                    <img class="screenshot" src="data:image/png;base64,{screenshots[i]["data"]}" alt="Issue Screenshot">
                </div>
            '''
        html += f'''
        <div class="issue">
            <h3>{violation.get('description', 'Unknown Issue')}</h3>
            <p><strong>Impact:</strong> {violation.get('impact', 'Unknown')}</p>
            <p><strong>Help:</strong> {violation.get('help', 'No help available')}</p>
            {screenshot_html}
        </div>
        '''
    return html