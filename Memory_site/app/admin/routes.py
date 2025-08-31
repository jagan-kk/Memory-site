import os
import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.services.ai_summarizer import summarize_text_with_bart

# Blueprint setup remains the same
admin_bp = Blueprint('admin', __name__,
                    template_folder='../templates/admin',
                    static_folder='../static')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("You are not authorized to view this page.")
        return redirect(url_for('auth.login'))
    
    # Retrieve the summary from the session if it exists, then remove it
    summary = session.pop('summary', None)
    
    # Pass the summary to the template
    return render_template('dashboard.html', summary=summary)

@admin_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    uploaded_files = request.files.getlist('files')
    if not uploaded_files or uploaded_files[0].filename == '':
        flash('No files selected!')
        return redirect(url_for('admin.dashboard'))

    summary_generated = False
    
    # We will process the first valid PDF found
    for file in uploaded_files:
        if file and file.filename.lower().endswith('.pdf'):
            try:
                # Ensure the temp directory exists
                if not os.path.exists('temp'):
                    os.makedirs('temp')

                # Create a secure temporary path for the file
                temp_path = os.path.join('temp', file.filename)
                file.save(temp_path)

                # 1. Extract text from the PDF
                doc = fitz.open(temp_path)
                full_text = "".join(page.get_text() for page in doc)
                doc.close()

                # 2. Call the summarizer if text was found
                if full_text.strip():
                    print(f"Summarizing text from {file.filename} with BART model...")
                    summary = summarize_text_with_bart(full_text)
                    
                    # Store the summary in the session to pass to the dashboard
                    session['summary'] = summary
                    summary_generated = True
                
                # Clean up the temporary file
                os.remove(temp_path)

                # We've processed the first PDF, so we break the loop
                break

            except Exception as e:
                flash(f"An error occurred while processing {file.filename}: {e}")
                print(f"Error processing file {file.filename}: {e}")
                return redirect(url_for('admin.dashboard'))

    if summary_generated:
        flash('PDF processed and summarized successfully!')
    else:
        flash('No PDF files were found in your upload to summarize.')

    return redirect(url_for('admin.dashboard'))