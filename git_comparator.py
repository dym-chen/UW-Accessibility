import tempfile
import os
from git import Repo, GitCommandError
import shutil

def compare_commits(repo_url, branch='main', commit_hash=None):
    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repository
        repo = Repo.clone_from(repo_url, temp_dir)
        
        # Fetch all branches
        repo.remotes.origin.fetch()
        
        # Checkout the specified branch
        repo.git.checkout(branch)
        
        # Get the current HEAD commit
        current_commit = repo.head.commit
        
        # If no commit hash is provided, use the previous commit
        if not commit_hash:
            commit_hash = current_commit.parents[0].hexsha if current_commit.parents else current_commit.hexsha
        
        # Get the specified commit
        try:
            old_commit = repo.commit(commit_hash)
        except GitCommandError:
            raise ValueError(f"Invalid commit hash: {commit_hash}")
        
        # Get the diff between commits
        diff = current_commit.diff(old_commit)
        
        # Process the diff results
        results = {
            'current_commit': current_commit.hexsha,
            'old_commit': old_commit.hexsha,
            'changed_files': [],
            'diffs': {}
        }
        
        for item in diff:
            file_path = item.a_path if item.a_path else item.b_path
            results['changed_files'].append(file_path)
            
            # Get the diff content
            try:
                diff_content = repo.git.diff(old_commit.hexsha, current_commit.hexsha, '--', file_path)
                results['diffs'][file_path] = diff_content
            except GitCommandError:
                results['diffs'][file_path] = "Error getting diff content"
        
        return results
    
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True) 