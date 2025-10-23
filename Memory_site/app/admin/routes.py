import os
import fitz  # PyMuPDF
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import mongo
# Import both of your services
from app.services.ai_summarizer import summarize_text_with_bart
from app.services.model_generator import create_text_texture, generate_3d_card

# Blueprint setup remains the same
admin_bp = Blueprint('admin', __name__,
                    template_folder='../templates/admin',
                    static_folder='../static')


@admin_bp.route('/add-new')
@login_required
def add_new():
    try:
        # Fetch all documents from the 'colleges' collection
        colleges_cursor = mongo.db.colleges.find({})

        # Convert the cursor to a list to pass to the template
        colleges_list = list(colleges_cursor)

    except Exception as e:
        flash("Could not connect to the database to fetch college list.")
        print(f"Error fetching college list: {e}")
        colleges_list = []

    return render_template('admin/add_new.html', colleges=colleges_list)

@admin_bp.route('/delete/<college_id>')
@login_required
def delete_college(college_id):
    try:
        # Find the document by its ID and delete it
        result = mongo.db.colleges.delete_one({'_id': ObjectId(college_id)})
        if result.deleted_count == 1:
            flash('College deleted successfully!', 'success')
        else:
            flash('College not found.', 'error')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        print(f"Error deleting college: {e}")

    # Redirect back to the list of colleges
    return redirect(url_for('admin.add_new'))

@admin_bp.route('/edit/<college_id>', methods=['GET', 'POST'])
@login_required
def edit_college(college_id):
    # Convert the string ID from the URL into a MongoDB ObjectId
    college_oid = ObjectId(college_id)

    if request.method == 'POST':
        # This block runs when the user submits the form
        new_name = request.form.get('college_name')
        new_coordinate = request.form.get('coordinate')

        # Update the document in the database
        mongo.db.colleges.update_one(
            {'_id': college_oid},
            {'$set': {
                'college_name': new_name,
                'coordinate': new_coordinate
            }}
        )
        flash('College updated successfully!', 'success')
        return redirect(url_for('admin.add_new'))

    # This block runs when the user first clicks the "Edit" button (a GET request)
    # Find the specific college to pre-populate the form
    college = mongo.db.colleges.find_one_or_404({'_id': college_oid})
    return render_template('admin/edit_college.html', college=college)

@admin_bp.route('/generator')
@login_required
def generator():
    summary = session.pop('summary', None)
    glb_path = session.pop('glb_path', None)

    college_data = {}
    try:
        # Fetch using your field names: 'college_name' and 'coordinate'
        colleges_cursor = mongo.db.colleges.find({}, {'college_name': 1, 'coordinate': 1, '_id': 0})

        # Create a dictionary mapping each college name to its coordinate string
        college_data = {doc['college_name']: doc['coordinate'] for doc in colleges_cursor if 'coordinate' in doc}

    except Exception as e:
        flash("Could not connect to the database to fetch college data.")
        print(f"Error fetching college data: {e}")

    return render_template('admin/generator.html',
                           summary=summary,
                           glb_path=glb_path,
                           college_data=college_data)

@admin_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    uploaded_files = request.files.getlist('files')
    if not uploaded_files or uploaded_files[0].filename == '':
        flash('No files selected!')
        return redirect(url_for('admin.generator'))

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
                    return redirect(url_for('admin.generator'))

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
                    return redirect(url_for('admin.generator'))
                
                print(f"[6] Texture file created successfully. Calling 'generate_3d_card' to save to: {glb_save_path}")
                generate_3d_card(texture_path, glb_save_path)
                
                session['glb_path'] = f'models/{glb_filename}'

                # --- CLEANUP (Temporarily Disabled for Debugging) ---
                # We are commenting this out so the texture file REMAINS for us to inspect.
                # if os.path.exists(texture_path):
                #     os.remove(texture_path)
                print("[7] Process complete. SKIPPING texture cleanup for debugging.")

                flash('PDF processed and 3D model generated successfully!')
                return redirect(url_for('admin.generator'))

            except Exception as e:
                print(f"[FATAL EXCEPTION] An error occurred: {e}")
                import traceback
                traceback.print_exc() # Print the full error stack trace
                flash(f"An error occurred: {e}")
                return redirect(url_for('admin.generator'))

    flash('No valid PDF files were found in your upload.')
    return redirect(url_for('admin.generator'))