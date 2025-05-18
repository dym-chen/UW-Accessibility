from flask import Flask, render_template, request, send_file, jsonify
import os
from datetime import datetime
from accessibility_checker import check_accessibility
from git_comparator import compare_commits
from database import Database
import tempfile
from bson import ObjectId
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize database
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reports')
def view_reports():
    reports = db.list_reports()
    # Sort reports by timestamp, most recent first
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('reports.html', reports=reports)

@app.route('/download-report/<file_id>')
def download_report(file_id):
    try:
        pdf_data, filename = db.get_pdf(ObjectId(file_id))
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-accessibility', methods=['POST'])
def accessibility_check():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Generate the accessibility report
        report_path = check_accessibility(url)
        
        # Store the PDF in MongoDB
        file_id = db.store_pdf(report_path, url)
        
        # Send the file to the user
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f'accessibility-report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compare-git', methods=['POST'])
def git_compare():
    repo_url = request.form.get('repo_url')
    branch = request.form.get('branch', 'main')
    commit_hash = request.form.get('commit_hash')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    try:
        diff_results = compare_commits(repo_url, branch, commit_hash)
        return jsonify(diff_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 