from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
from datetime import datetime
from accessibility_checker import check_accessibility
from git_comparator import compare_commits
from database import Database
from models import User
import tempfile
from bson import ObjectId
import io
from functools import wraps
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production

# Initialize database and user model
db = Database()
user_model = User()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = user_model.authenticate(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        try:
            user_id = user_model.create_user(email, password, name)
            session['user_id'] = user_id
            session['user_name'] = name
            return redirect(url_for('dashboard'))
        except ValueError as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user_name=session.get('user_name'))

@app.route('/reports')
@login_required
def view_reports():
    reports = db.list_reports(session['user_id'])
    # Sort reports by timestamp, most recent first
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('reports.html', reports=reports)

@app.route('/download-report/<file_id>')
@login_required
def download_report(file_id):
    try:
        pdf_data, filename = db.get_pdf(file_id, session['user_id'])
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-accessibility', methods=['POST'])
@login_required
def accessibility_check():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Generate the accessibility report
        report_path = check_accessibility(url)
        
        # Store the PDF in MongoDB
        file_id = db.store_pdf(report_path, url, session['user_id'])
        
        # Send the file to the user
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f'accessibility-report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compare-git', methods=['POST'])
@login_required
def git_compare():
    repo_url = request.form.get('repo_url')
    branch = request.form.get('branch', 'main')
    commit_hash = request.form.get('commit_hash')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    try:
        diff_results = compare_commits(repo_url, branch, commit_hash)
        
        # Store accessibility reports in the database
        for file_path, issues in diff_results.get('accessibility_issues', {}).items():
            if issues.get('has_issues') and issues.get('report_path'):
                try:
                    file_id = db.store_pdf(
                        issues['report_path'],
                        f"Git comparison - {file_path}",
                        session['user_id'],
                        metadata={
                            'type': 'git_accessibility',
                            'file_path': file_path,
                            'commit': diff_results['current_commit']
                        }
                    )
                    issues['report_id'] = file_id
                except Exception as e:
                    issues['error'] = f"Failed to store report: {str(e)}"
        
        return jsonify(diff_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 