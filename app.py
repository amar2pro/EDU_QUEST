import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, School,Principal,Feedback,MeetingBooking

# ---------------------
# App Configuration
# ---------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'change_this_secret_for_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'eduquest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/schools'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Make sure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
CORS(app)

# ---------------------
# Models
# ---------------------


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



# Database Initialization
def init_db(seed=False):  # Changed to False to prevent auto-seeding
    with app.app_context():
        db.create_all()

    # create default admin only - NO SAMPLE SCHOOLS
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin')
        admin.set_password('admin123')  # change later for production
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created: admin/admin123")
    
    print("✅ Database initialized with NO sample schools")
    


#THIS IS TO FORCE DATABASE OPERATIONS
def force_db_commit():
    try:
        db.session.commit()
        print("✅ DATABASE COMMITTED!")
        return True
    except Exception as e:
        print(f"❌ COMMIT FAILED: {e}")
        db.session.rollback()
        return False
    
# ---------------------
# Frontend routes (templates will be added later)
# ---------------------

@app.route('/')
def home():
    return render_template('index.html')

# ---------------------
# API routes
@app.route('/schools')
def schools_page():
    all_schools = School.query.all()
    return render_template('school.html', schools=all_schools)


@app.route('/api/schools')
def api_schools():
    schools = School.query.all()
    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "region": s.region,
            "level": s.level,
            "contact": s.contact,
            "description": s.description,
            "accessibility": s.accessibility,
            "fee_structure": s.fee_structure,
            "image_url": s.image_url
        } for s in schools
    ])

# Route for the admin dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    schools = School.query.all()  
    return render_template('admin-dashboard.html', schools=schools) 

#ROUTE FOR PRINCIPAL DASHBOARD
@app.route('/principal-dashboard')
def principal_dashboard():
    # Check if principal is logged in
    if not session.get('principal_logged_in'):
        print("❌ Principal not logged in - redirecting to home")
        return redirect('/')
    
    # Get principal and school data
    principal = Principal.query.get(session['principal_id'])
    school = School.query.get(session['principal_school_id'])
    
    print(f"🔍 Debug - Principal ID: {session.get('principal_id')}")
    print(f"🔍 Debug - School ID: {session.get('principal_school_id')}")
    print(f"🔍 Debug - Principal found: {principal is not None}")
    print(f"🔍 Debug - School found: {school is not None}")
    
    if not principal or not school:
        session.clear()
        return redirect('/')
    
    # Get meetings for this principal
    meetings = MeetingBooking.query.filter_by(principal_id=principal.id).order_by(MeetingBooking.created_at.desc()).all()
    
    print(f"🔍 Debug - Meetings found: {len(meetings)}")
    for meeting in meetings:
        print(f"🔍 Meeting: {meeting.id}, Principal ID: {meeting.principal_id}, Status: {meeting.status}")
    
    return render_template('principal-dashboard.html', 
                         principal=principal, 
                         school=school,
                         meetings=meetings)
# ROUTE FOR PRINCIPAL LOGOUT
@app.route('/api/principals/logout', methods=['POST'])
def principal_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# ---------------------
# Admin auth
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    admin = Admin.query.filter_by(username=username).first()
    if admin and admin.check_password(password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@app.route('/api/session', methods=['GET'])
def check_session():
    return jsonify({"admin_logged_in": bool(session.get('admin_logged_in')), "username": session.get('admin_username')}), 200


# Create
@app.route('/api/schools', methods=['POST'])
def add_school():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    s = School(
        name=data.get('name', ''),
        region=data.get('region', ''),
        level=data.get('level'),
        contact=data.get('contact'),
        description=data.get('description'),
        accessibility=data.get('accessibility'),
        fee_structure=data.get('fee_structure'),
        image_url=data.get('image_url')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201

# Read (list with filters)
@app.route('/api/schools', methods=['GET'])
def list_schools():
    q = request.args.get('q', '').strip().lower()
    region = request.args.get('region', '').strip().lower()
    disability = request.args.get('disability', '').strip().lower()
    query = School.query
    if q:
        query = query.filter(School.name.ilike(f'%{q}%'))
    if region:
        query = query.filter(School.region.ilike(f'%{region}%'))
    if disability:
        query = query.filter(School.accessibility.ilike(f'%{disability}%'))
    schools = query.order_by(School.name).all()
    return jsonify([s.to_dict() for s in schools]), 200

@app.route('/api/schools/<int:id>', methods=['GET'])
def get_school(id):
    s = School.query.get_or_404(id)
    return jsonify(s.to_dict()), 200

# Update
@app.route('/api/schools/<int:id>', methods=['PUT'])
def update_school(id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    s = School.query.get_or_404(id)
    data = request.json or {}
    s.name = data.get('name', s.name)
    s.region = data.get('region', s.region)
    s.level = data.get('level', s.level)
    s.contact = data.get('contact', s.contact)
    s.description = data.get('description', s.description)
    s.accessibility = data.get('accessibility', s.accessibility)
    s.fee_structure = data.get('fee_structure', s.fee_structure)
    s.image_url = data.get('image_url', s.image_url)
    db.session.commit()
    return jsonify(s.to_dict()), 200

# DELETE A SCHOOL FROM DATABASE
@app.route('/api/schools/<int:id>', methods=['DELETE'])
def delete_school(id):
    print(f"DELETING SCHOOL ID: {id} - WITH CASCADE")
    
    try:
        school = School.query.get(id)
        if not school:
            print(f"❌ SCHOOL {id} NOT FOUND!")
            return jsonify({"error": "School not found"}), 404
            
        print(f"DELETING SCHOOL: {school.name} (ID: {school.id})")
        print(f"Associated principals: {len(school.principals)}")
        print(f"Associated feedback: {len(school.feedbacks)}")
        print(f"Associated meetings: {len(school.meetings)}")
        
        # Manual cleanup (backup in case cascade doesn't work)
        for principal in school.principals:
            print(f"Deleting principal: {principal.name} (ID: {principal.id})")
        
        for feedback in school.feedbacks:
            print(f"Deleting feedback: {feedback.id}")
            
        for meeting in school.meetings:
            print(f"Deleting meeting: {meeting.id}")
        
        # Delete associated image file if exists
        if school.image_url and school.image_url != "/static/images/default-school.jpg":
            try:
                image_path = school.image_url.replace('/static/', 'static/')
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"DELETED IMAGE FILE: {image_path}")
            except Exception as e:
                print(f"Could not delete image file: {e}")
        
        # Delete the school (should cascade to principals, feedback, meetings)
        db.session.delete(school)
        db.session.commit()
        
        print(f"SCHOOL {id} AND ALL ASSOCIATED DATA DELETED SUCCESSFULLY!")
        return jsonify({"message": "School and all associated data deleted"}), 200
        
    except Exception as e:
        print(f"DELETE ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    


#ROUTE FOR CONFIRMING  PRINCIPAL MODEL EXISTS
@app.route('/update-db', methods=['GET'])
def update_db():
    """Route to update database with new models"""
    try:
        with app.app_context():
            db.create_all()  # This will create any new tables
        return jsonify({"message": "Database updated successfully with Principal model"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#ROUTE FOR CONFIRMING MEETING BOOKING MODEL EXISTS   
@app.route('/update-db-meetings')
def update_db_meetings():
    """Route to update database with MeetingBooking model"""
    try:
        with app.app_context():
            db.create_all()
        return jsonify({"message": "Database updated successfully with MeetingBooking model"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/debug-meetings')
def debug_meetings():
    """Debug route to check all meetings in database"""
    try:
        meetings = MeetingBooking.query.all()
        meetings_data = []
        for meeting in meetings:
            meetings_data.append({
                "id": meeting.id,
                "school_id": meeting.school_id,
                "principal_id": meeting.principal_id,
                "user_name": meeting.user_name,
                "status": meeting.status,
                "preferred_date": meeting.preferred_date.isoformat() if meeting.preferred_date else None
            })
        return jsonify({"meetings": meetings_data, "total": len(meetings)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#ROUTE FOR BOOKING A MEETING
@app.route('/api/meetings/book', methods=['POST'])
def book_meeting():
    try:
        data = request.json or {}
        print(f"📅 Meeting booking attempt: {data}")
        
        # Validation
        required_fields = ['school_id', 'principal_id', 'user_name', 'user_email', 'purpose', 'preferred_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Verify principal exists
        principal = Principal.query.get(data['principal_id'])
        if not principal:
            return jsonify({"error": "Principal not found"}), 404
        
        # Create meeting booking
        meeting = MeetingBooking(
            school_id=data['school_id'],
            principal_id=data['principal_id'],
            user_name=data['user_name'],
            user_email=data['user_email'],
            user_phone=data.get('user_phone'),
            purpose=data['purpose'],
            preferred_date=datetime.fromisoformat(data['preferred_date'].replace('Z', '+00:00')),
            special_requirements=data.get('special_requirements')
        )
        
        db.session.add(meeting)
        db.session.commit()
        
        print(f"✅ Meeting booked: {meeting.id} - {meeting.user_name} with principal {meeting.principal_id}")
        
        return jsonify({
            "message": "Meeting request submitted successfully",
            "meeting_id": meeting.id
        }), 201
        
    except Exception as e:
        print(f"❌ Meeting booking error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
#UPDATE MEETING BOOKING ROUTE ON PRINCIPAL DASHBOARD
@app.route('/api/meetings/<int:meeting_id>/status', methods=['PUT'])
def update_meeting_status(meeting_id):
    try:
        # Check if principal is logged in
        if not session.get('principal_logged_in'):
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json or {}
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        # Get meeting and verify it belongs to this principal
        meeting = MeetingBooking.query.get(meeting_id)
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        if meeting.principal_id != session['principal_id']:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update status
        meeting.status = new_status
        db.session.commit()
        
        print(f"Meeting {meeting_id} status updated to: {new_status}")  # Simulate notification
        
        return jsonify({
            "message": f"Meeting {new_status} successfully",
            "meeting": meeting.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Meeting status update error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

#IMAGES MANAGEMENT
@app.route('/upload-school-image', methods=['POST'])
def upload_school_image():
    if 'school_image' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['school_image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Return the relative URL for the image
        image_url = f"/static/images/schools/{unique_filename}"
        return jsonify({'image_url': image_url})
    
    return jsonify({'error': 'Invalid file type'}), 400


 # DELETE IMAGE FUNCTIONALITY
@app.route('/delete-school-image/<int:school_id>', methods=['DELETE'])
def delete_school_image(school_id):
    try:
        school = School.query.get_or_404(school_id)
        
        if school.image_url:
            # Delete the physical file
            image_path = school.image_url.replace('/static/', 'static/')
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Update the database
            school.image_url = None
            db.session.commit()
            
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    #ROUTE FOR PRINCIPALS
@app.route('/debug-principals')
def debug_principals():
    """Check all principals in database"""
    try:
        principals = Principal.query.all()
        
        principals_data = []
        for principal in principals:
            principals_data.append({
                "id": principal.id,
                "name": principal.name,
                "email": principal.email,
                "school_id": principal.school_id,
                "is_active": principal.is_active,
                "created_at": getattr(principal, 'created_at', 'N/A')
            })
        
        return jsonify({
            "total_principals": len(principals),
            "principals": principals_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/principals/register', methods=['POST'])
def register_principal():
    try:
        data = request.json or {}
        print(f"Registration attempt with data: {data}")
        
        
        # Create principal
        principal = Principal(
            school_id=data['school_id'],
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            verification_token=os.urandom(24).hex(),
            password_hash=generate_password_hash(data['password']),
            is_active=True  # AUTO-ACTIVATE FOR NOW
        )
        
        db.session.add(principal)
        db.session.commit()
        
        print(f"Principal registered successfully: {principal.email}")
        
        # AUTO-LOGIN: Create session immediately
        session['principal_logged_in'] = True
        session['principal_id'] = principal.id
        session['principal_school_id'] = principal.school_id
        session['principal_name'] = principal.name
        
        return jsonify({
            "message": "Registration successful!",
            "principal_id": principal.id
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    #PRINCIPAL LOGIN ROUTE 
@app.route('/api/principals/login', methods=['POST'])
def principal_login():
    try:
        data = request.json or {}
        
        # Validation
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password required"}), 400
        
        # Find principal by email
        principal = Principal.query.filter_by(email=data['email']).first()
        if not principal:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check password
        if not check_password_hash(principal.password_hash, data['password']):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check if account is active
        if not principal.is_active:
            return jsonify({"error": "Account pending admin approval. Please wait for activation."}), 403
        
        # Login successful - create session
        session['principal_logged_in'] = True
        session['principal_id'] = principal.id
        session['principal_school_id'] = principal.school_id
        session['principal_name'] = principal.name
        
        return jsonify({
            "message": "Login successful",
            "principal": principal.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    #PRINCIPAL PROFILE UPDATE ROUTE
@app.route('/api/principals/profile', methods=['POST'])
def update_principal_profile():
    try:
        # Check if principal is logged in
        if not session.get('principal_logged_in'):
            return jsonify({"error": "Unauthorized"}), 401
        
        principal = Principal.query.get(session['principal_id'])
        if not principal:
            return jsonify({"error": "Principal not found"}), 404
        
        # Handle file upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"principal_{principal.id}_{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                principal.image_url = f"/static/images/schools/{unique_filename}"
        
        # Update other fields
        principal.name = request.form.get('name', principal.name)
        principal.email = request.form.get('email', principal.email)
        principal.phone = request.form.get('phone', principal.phone)
        principal.bio = request.form.get('bio', principal.bio)
        principal.qualifications = request.form.get('qualifications', principal.qualifications)
        principal.office_hours = request.form.get('office_hours', principal.office_hours)
        
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "principal": principal.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# FEEDBACK
@app.route('/admin/feedback')
def admin_feedback_page():
    """Render the admin feedback management page"""
    return render_template('admin-feedback.html')

@app.route('/api/all-schools')
def all_schools():
    """Get all schools for feedback filtering"""
    try:
        schools = School.query.all()
        
        schools_data = []
        for school in schools:
            schools_data.append({
                "id": school.id,
                "name": school.name,
                "region": school.region,
                "level": school.level,
                "contact": getattr(school, 'contact', '')
            })
        
        return jsonify(schools_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper function to convert feedback row to dict - KEEP THIS AS IS
def feedback_to_dict(row):
    return {
        'id': row[0],
        'school_id': row[1],
        'name': row[2],
        'email': row[3],
        'message': row[4],
        'created_at': row[5],
        'admin_reply': row[6],
        'reply_date': row[7],
        'school_name': 'School ' + str(row[1])
    }

@app.route('/api/feedback', methods=['POST'])
def post_feedback():
    """Submit new feedback from users"""
    data = request.json or {}
    
    try:
        # USE SQLALCHEMY INSTEAD OF RAW SQLITE
        feedback = Feedback(
            school_id=data.get('school_id'),
            name=data.get('name'),
            email=data.get('email'),
            message=data.get('message'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        print(f"✅ FEEDBACK SUBMITTED: ID {feedback.id}")
        return jsonify({'id': feedback.id, 'message': 'Feedback submitted'}), 201
        
    except Exception as e:
        print(f"❌ FEEDBACK SUBMIT ERROR: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    """Get all feedback for admin dashboard"""
    try:
        print("🔄 GET_FEEDBACKS CALLED")
        
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        print(f"✅ FOUND {len(feedbacks)} FEEDBACK ENTRIES")
        
        # SIMPLIFIED VERSION - Use the model's to_dict method
        feedbacks_data = [f.to_dict() for f in feedbacks]
        
        print("✅ SUCCESS: Returning feedback data")
        return jsonify(feedbacks_data), 200
        
    except Exception as e:
        print(f"❌ GET FEEDBACKS ERROR: {e}")
        import traceback
        print(f"🔍 FULL TRACEBACK: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


#ROUTE TO CONFIRM FEEDBACK MODEL EXISTS
@app.route('/update-feedback-model')
def update_feedback_model():
    """Emergency route to update Feedback model with new fields"""
    try:
        with app.app_context():
            db.create_all()
        return "✅ Feedback model updated with admin_reply and reply_date fields!"
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
#ROUTE FOR REPLYING TO FEEDBACK - FIXED
@app.route('/api/feedback/<int:feedback_id>/reply', methods=['POST'])
def reply_to_feedback(feedback_id):
    """Admin replies to specific feedback"""
    data = request.json
    reply_message = data.get('reply')
    
    print(f"🔄 REPLYING TO FEEDBACK {feedback_id}: {reply_message}")
    
    try:
        # USE SQLALCHEMY INSTEAD OF RAW SQLITE
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            feedback.admin_reply = reply_message
            feedback.reply_date = datetime.utcnow()
            
            db.session.commit()
            print(f"✅ REPLY ADDED TO FEEDBACK {feedback_id}")
            return jsonify({"message": "Reply added successfully"})
        else:
            return jsonify({"error": "Feedback not found"}), 404
            
    except Exception as e:
        print(f"❌ REPLY ERROR: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#ROUTE FOR DELETING FEEDBACK - FIXED
@app.route('/api/feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    """Delete specific feedback"""
    print(f"🔄 DELETING FEEDBACK {feedback_id}")
    
    try:
        # USE SQLALCHEMY INSTEAD OF RAW SQLITE
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            db.session.delete(feedback)
            db.session.commit()
            print(f"✅ FEEDBACK {feedback_id} DELETED")
            return jsonify({"message": "Feedback deleted successfully"})
        else:
            return jsonify({"error": "Feedback not found"}), 404
            
    except Exception as e:
        print(f"❌ DELETE ERROR: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/schools/<int:school_id>/feedback')
def get_school_feedback(school_id):
    """Get feedback for a specific school"""
    try:
        # USE SQLALCHEMY INSTEAD OF RAW SQLITE
        feedbacks = Feedback.query.filter_by(school_id=school_id).order_by(Feedback.created_at.desc()).all()
        feedbacks_data = [{
            'id': f.id,
            'school_id': f.school_id,
            'name': f.name,
            'email': f.email,
            'message': f.message,
            'created_at': f.created_at.isoformat() if f.created_at else None,
            'admin_reply': f.admin_reply,
            'reply_date': f.reply_date.isoformat() if f.reply_date else None,
            'school_name': f.school.name if f.school else f"School {f.school_id}"
        } for f in feedbacks]
        
        return jsonify(feedbacks_data)
        
    except Exception as e:
        print(f"❌ GET SCHOOL FEEDBACK ERROR: {e}")
        return jsonify({"error": str(e)}), 500


#SCHOOL DETAILS ROUTE
@app.route('/school/<int:id>')
def school_details(id):
    school = School.query.get_or_404(id)
    feedbacks = Feedback.query.filter_by(school_id=id).order_by(Feedback.created_at.desc()).all()
    
    # Get principal data directly
    try:
        principal = Principal.query.filter_by(school_id=id).first()
    except Exception:
        principal = None

    return render_template('school_details.html', 
                         school=school, 
                         feedbacks=feedbacks, 
                         principal=principal,
                         now=datetime.now())  

 #ROUTE FOR ADDING SCHOOLS ON THE ADMIN DASHBOARD
@app.route('/add-school', methods=['POST'])
def submit_school_form():
    print("🔄 ADD SCHOOL FORM SUBMITTED!")
    
    # Get form data
    name = request.form.get('name')
    region = request.form.get('region') 
    level = request.form.get('level')
    description = request.form.get('description')
    contact = request.form.get('contact')
    accessibility = request.form.get('accessibility')
    fee_structure = request.form.get('fee_structure')
    
    print(f"📝 FORM DATA: {name}, {region}, {level}")

    # Handle file upload - BACKEND SOLUTION (like principal dashboard)
    image_url = "/static/images/default-school.jpg"  # default
    
    if 'school_image' in request.files:
        file = request.files['school_image']
        if file and file.filename != '' and allowed_file(file.filename):
            print(f"📁 FILE UPLOAD DETECTED: {file.filename}")
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"school_{int(time.time())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file to folder
            file.save(file_path)
            image_url = f"/static/images/schools/{unique_filename}"
            print(f"✅ IMAGE SAVED TO: {image_url}")
        else:
            print("📁 NO VALID FILE UPLOADED, USING DEFAULT IMAGE")

    # Validate required fields
    if not name or not region:
        print("❌ MISSING REQUIRED FIELDS!")
        return redirect('/admin-dashboard')

    try:
        # Create and save new school
        new_school = School(
            name=name,
            region=region,
            level=level,
            description=description,
            contact=contact,
            accessibility=accessibility,
            fee_structure=fee_structure,
            image_url=image_url
        )

        print(f"🎯 CREATING SCHOOL OBJECT: {new_school.name}")
        
        db.session.add(new_school)
        print("✅ SCHOOL ADDED TO SESSION")
        
        # FORCE COMMIT
        db.session.commit()
        print("✅ DATABASE COMMITTED!")
        
        # VERIFY IMMEDIATELY
        saved_school = School.query.get(new_school.id)
        if saved_school:
            print(f"🎉 VERIFICATION SUCCESS: School {saved_school.id} - '{saved_school.name}' saved in database!")
            
            # Check all schools count
            all_schools = School.query.all()
            print(f"📊 TOTAL SCHOOLS IN DATABASE: {len(all_schools)}")
            for s in all_schools:
                print(f"   - {s.id}: {s.name}")
        else:
            print("❌ VERIFICATION FAILED: School not found after commit!")

    except Exception as e:
        print(f"❌ DATABASE ERROR: {str(e)}")
        import traceback
        print(f"🔍 FULL ERROR: {traceback.format_exc()}")
        db.session.rollback()
        return redirect('/admin-dashboard')

    return redirect('/admin-dashboard')

# ADD THIS DEBUG ROUTE TO CHECK SCHOOLS
@app.route('/debug-schools')
def debug_schools():
    """Debug route to check all schools in database"""
    try:
        schools = School.query.all()
        schools_data = []
        for school in schools:
            schools_data.append({
                "id": school.id,
                "name": school.name,
                "region": school.region,
                "level": school.level,
                "contact": school.contact,
                "image_url": school.image_url,
                "created_at": getattr(school, 'created_at', 'N/A')
            })
        return jsonify({
            "total_schools": len(schools),
            "schools": schools_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
          

#ROUTE FOR EDITING SCHOOLS ON THE ADMIN DASHBOARD
@app.route('/admin/edit/<int:id>', methods=['POST'])
def update_school_form(id):
    print(f"🔄 EDITING SCHOOL ID: {id}")
    
    school = School.query.get_or_404(id)
    print(f"📝 FOUND SCHOOL TO EDIT: {school.name}")
    
    # Update fields from form inputs
    school.name = request.form.get('name', school.name)
    school.region = request.form.get('region', school.region)
    school.level = request.form.get('level', school.level)
    school.description = request.form.get('description', school.description)
    school.contact = request.form.get('contact', school.contact)
    school.accessibility = request.form.get('accessibility', school.accessibility)
    school.fee_structure = request.form.get('fee_structure', school.fee_structure)
    
    print(f"UPDATED DATA: {school.name}, {school.region}")

    # Handle image upload for edit
    if 'school_image' in request.files:
        file = request.files['school_image']
        if file and file.filename != '' and allowed_file(file.filename):
            print(f"NEW IMAGE UPLOADED: {file.filename}")
            
            # Delete old image if it exists and isn't default
            if school.image_url and school.image_url != "/static/images/default-school.jpg":
                try:
                    old_image_path = school.image_url.replace('/static/', 'static/')
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        print(f"DELETED OLD IMAGE: {old_image_path}")
                except Exception as e:
                    print(f"Could not delete old image: {e}")
            
            # Save new image
            filename = secure_filename(file.filename)
            unique_filename = f"school_{id}_{int(time.time())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(file_path)
            school.image_url = f"/static/images/schools/{unique_filename}"
            print(f"NEW IMAGE SAVED: {school.image_url}")
    
    try:
        db.session.commit()
        print("SCHOOL UPDATED SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ UPDATE ERROR: {str(e)}")
        db.session.rollback()
    
    return redirect('/admin-dashboard')

# Dev helper: init-db route 
@app.route('/init-db', methods=['GET'])
def init_db_route():
    init_db(seed=False)  # Changed to False
    return jsonify({"message": "Database initialized (NO sample data). Default admin: admin/admin123"}), 200

# ---------------------
# Run
# ---------------------
if __name__ == '__main__':
    # Create DB if missing
    if not os.path.exists(os.path.join(BASE_DIR, 'eduquest.db')):
        with app.app_context():
            init_db(seed=True)
    app.run(debug=True)