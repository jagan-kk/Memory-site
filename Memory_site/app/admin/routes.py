import os
import fitz  # PyMuPDF
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import mongo
# Import both of your services
from app.services.ai_summarizer import summarize_text_with_bart
from app.services.model_generator import create_text_texture, generate_3d_card
# Import the Google Drive service
from app.services.google_drive import upload_to_drive


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

@admin_bp.route('/add', methods=['POST'])
@login_required
def add_new_college():
    try:
        # Get data from the submitted form
        college_name = request.form.get('college_name')
        coordinate = request.form.get('coordinate')

        if not college_name or not coordinate:
            flash('Both college name and coordinate are required!', 'error')
            return redirect(url_for('admin.add_new'))
        
        # Insert the new document into the 'colleges' collection
        result = mongo.db.colleges.insert_one({
            'college_name': college_name,
            'coordinate': coordinate
        })

        if result.inserted_id:
            flash(f'New college "{college_name}" added successfully!', 'success')
        else:
            flash('Failed to add new college.', 'error')

    except Exception as e:
        flash(f'An error occurred while adding the college: {e}', 'error')
        print(f"Error adding new college: {e}")

    # Redirect back to the college management page
    return redirect(url_for('admin.add_new'))

@admin_bp.route('/edit/<college_id>', methods=['GET', 'POST'])
@login_required
def edit_college(college_id):
    college_oid = ObjectId(college_id)

    if request.method == 'POST':
        # This block runs when the user submits the form to update a college
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

    # Initialize file paths to None for robust cleanup in the 'finally' block
    temp_pdf_path = None
    texture_path = None
    glb_save_path = None
    
    # --- GET FORM DATA ---
    coordinate = request.form.get("coordinate")
    semester = request.form.get("semester") # <--- NEW: Retrieve semester
    # Note: college_name and branch are available but not currently saved to assets collection

    if not coordinate:
        flash('Coordinate is required for asset upload!', 'error')
        return redirect(url_for('admin.generator'))

    for file in uploaded_files:
        if file and file.filename.lower().endswith('.pdf'):
            try:
                # --- SETUP DIRECTORIES & FILE NAMES ---
                temp_dir = 'temp'
                models_dir = os.path.join('app', 'static', 'models')

                os.makedirs(temp_dir, exist_ok=True)
                os.makedirs(models_dir, exist_ok=True)

                file_basename = os.path.splitext(file.filename)[0]
                glb_filename = f"{file_basename}.glb"
                
                temp_pdf_path = os.path.join(temp_dir, file.filename)
                texture_path = os.path.join(temp_dir, 'summary_texture.png')
                glb_save_path = os.path.join(models_dir, glb_filename)

                # --- 1. SAVE PDF TEMPORARILY & EXTRACT TEXT ---
                print(f"[1] Saving PDF locally: {file.filename}")
                # Save the uploaded file locally before processing
                file.save(temp_pdf_path) 
                
                print("[2] Extracting text from PDF...")
                doc = fitz.open(temp_pdf_path)
                full_text = "".join(page.get_text() for page in doc)
                doc.close()

                if not full_text.strip():
                    flash("Could not extract any text from the PDF.")
                    return redirect(url_for('admin.generator'))

                # --- 2. AI SUMMARIZATION ---
                print("[3] Generating summary...")
                summary = summarize_text_with_bart(full_text)
                session['summary'] = summary
                
                # --- 3. CREATE TEXTURE & GENERATE GLB MODEL ---
                print("[4] Creating texture and GLB model...")
                create_text_texture(summary, texture_path)

                # Check if texture was created successfully before proceeding
                if not os.path.exists(texture_path):
                    raise FileNotFoundError("Texture file could not be created by model_generator.")
                    
                generate_3d_card(texture_path, glb_save_path)
                session['glb_path'] = f'models/{glb_filename}'

                # --- 4. UPLOAD FILES TO GOOGLE DRIVE ---
                print("\n[5] Uploading files to Google Drive...")
                
                # Upload PDF
                pdf_drive_url, pdf_drive_id = upload_to_drive(
                    temp_pdf_path, file.filename, "application/pdf"
                )
                
                # Upload GLB (Must be saved to glb_save_path inside app/static/models)
                glb_drive_url, glb_drive_id = upload_to_drive(
                    glb_save_path, glb_filename, "model/gltf-binary"
                )

                if not pdf_drive_id or not glb_drive_id:
                    # Continue execution but warn the user if upload failed
                    flash("Warning: File uploads to Google Drive failed for one or both files. Check console logs for API errors.", 'warning')
                else:
                    print("Uploads successful.")

                # --- 5. SAVE INTO MONGODB ---
                print("[6] Saving asset data to MongoDB...")
                mongo.db.assets.insert_one({
                    "filename": file.filename,
                    "pdf_url": pdf_drive_url, 
                    "glb_url": glb_drive_url, 
                    "pdf_id": pdf_drive_id,   
                    "glb_id": glb_drive_id,   
                    "coordinate": coordinate,
                    "semester": semester # <--- NEW: Save semester
                })
                print("[7] MongoDB asset saved.")

                flash("PDF processed, GLB created, and both files uploaded to Google Drive successfully!")
                return redirect(url_for('admin.generator'))

            except Exception as e:
                print(f"[FATAL EXCEPTION] An error occurred: {e}")
                import traceback
                traceback.print_exc()
                flash(f"An error occurred: {e}", 'error')
                return redirect(url_for('admin.generator'))
            
            finally:
                # --- FINAL CLEANUP (Crucial for temporary files) ---
                print("\n[8] Cleaning up temporary local files...")
                # The 'finally' block ensures cleanup runs even if an exception occurs
                
                # 1. Remove temporary PDF
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
                    print(f"   -> Removed temporary PDF: {temp_pdf_path}")
                
                # 2. Remove temporary texture PNG
                if texture_path and os.path.exists(texture_path):
                    os.remove(texture_path)
                    print(f"   -> Removed temporary texture: {texture_path}")

                # Note: We intentionally keep the generated GLB file in app/static/models 
                # because session['glb_path'] points to it for immediate viewing on the generator page.
    
    flash('No valid PDF files were found in your upload.')
    return redirect(url_for('admin.generator'))