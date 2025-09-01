import os
import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user

# Import both of your services
from app.services.ai_summarizer import summarize_text_with_bart
from app.services.model_generator import create_text_texture, generate_3d_card

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
    
    # Retrieve both the summary and the model path from the session
    summary = session.pop('summary', None)
    glb_path = session.pop('glb_path', None)
    
    # Pass both variables to the template
    return render_template('dashboard.html', summary=summary, glb_path=glb_path)


@admin_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    uploaded_files = request.files.getlist('files')
    if not uploaded_files or uploaded_files[0].filename == '':
        flash('No files selected!')
        return redirect(url_for('admin.dashboard'))

    print("\n--- STARTING NEW FILE UPLOAD PROCESS ---")

    for file in uploaded_files:
        if file and file.filename.lower().endswith('.pdf'):
            try:
                # --- SETUP DIRECTORIES ---
                temp_dir = 'temp'
                models_dir = os.path.join('app', 'static', 'models')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                if not os.path.exists(models_dir):
                    os.makedirs(models_dir)

                # --- PDF PROCESSING ---
                print(f"[1] Processing PDF: {file.filename}")
                temp_pdf_path = os.path.join(temp_dir, file.filename)
                file.save(temp_pdf_path)

                doc = fitz.open(temp_pdf_path)
                full_text = "".join(page.get_text() for page in doc)
                doc.close()
                os.remove(temp_pdf_path) # We can still clean up the PDF
                
                print(f"[2] Extracted {len(full_text)} characters from PDF.")
                if not full_text.strip():
                    print("[ERROR] PDF text is empty. Aborting.")
                    flash("Could not extract any text from the PDF.")
                    return redirect(url_for('admin.dashboard'))

                # --- AI SUMMARIZATION ---
                print("[3] Summarizing text with AI model...")
                summary = summarize_text_with_bart(full_text)
                session['summary'] = summary
                print(f"[4] Generated Summary: '{summary[:100]}...'") # Print first 100 chars

                # --- 3D MODEL GENERATION ---
                texture_path = os.path.join(temp_dir, 'summary_texture.png')
                file_basename = os.path.splitext(file.filename)[0]
                glb_filename = f"{file_basename}.glb"
                glb_save_path = os.path.join(models_dir, glb_filename)

                print(f"[5] Calling 'create_text_texture' to save to: {texture_path}")
                create_text_texture(summary, texture_path)
                
                # Check if the texture was actually created
                if not os.path.exists(texture_path):
                    print("[FATAL ERROR] 'create_text_texture' did NOT create the image file.")
                    flash("Error: Texture image could not be created.")
                    return redirect(url_for('admin.dashboard'))
                
                print(f"[6] Texture file created successfully. Calling 'generate_3d_card' to save to: {glb_save_path}")
                generate_3d_card(texture_path, glb_save_path)
                
                session['glb_path'] = f'models/{glb_filename}'

                # --- CLEANUP (Temporarily Disabled for Debugging) ---
                # We are commenting this out so the texture file REMAINS for us to inspect.
                # if os.path.exists(texture_path):
                #     os.remove(texture_path)
                print("[7] Process complete. SKIPPING texture cleanup for debugging.")

                flash('PDF processed and 3D model generated successfully!')
                return redirect(url_for('admin.dashboard'))

            except Exception as e:
                print(f"[FATAL EXCEPTION] An error occurred: {e}")
                import traceback
                traceback.print_exc() # Print the full error stack trace
                flash(f"An error occurred: {e}")
                return redirect(url_for('admin.dashboard'))

    flash('No valid PDF files were found in your upload.')
    return redirect(url_for('admin.dashboard'))