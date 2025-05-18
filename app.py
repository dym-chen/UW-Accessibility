from flask import Flask, render_template, request, send_file, jsonify
import os
from datetime import datetime
from accessibility_checker import check_accessibility
from git_comparator import compare_commits
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-accessibility', methods=['POST'])
def accessibility_check():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        report_path = check_accessibility(url)
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