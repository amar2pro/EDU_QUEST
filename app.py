import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, School,Principal,MeetingBooking

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
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to School
    school = db.relationship('School', backref=db.backref('feedbacks', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "name": self.name,
            "email": self.email,
            "message": self.message,
            "created_at": self.created_at.isoformat()
        }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------
# Database Initialization
# ---------------------
def init_db(seed=True):
    with app.app_context():
        db.create_all()


    # create default admin
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin')
        admin.set_password('admin123')  # change later
        db.session.add(admin)
        db.session.commit()

    # seed data if enabled and schools table is empty
    if seed and not School.query.first():
        samples = [
            # --- Nairobi (10 schools) ---
            School(
                name="Holmeside School",
                region="Nairobi",
                level="Primary/Secondary",
                contact="0722123123",
                description="Provides inclusive education for learners with diverse developmental needs.",
                accessibility="Adaptive classrooms, occupational therapy, learning support.",
                fee_structure="KES 35,000–50,000 per term",
                image_url="/static/images/holmeside.jpg"
            ),
            School(
                name="Jacaranda Special School",
                region="Nairobi",
                level="Primary",
                contact="0721998877",
                description="Supports children with physical and hearing disabilities in a nurturing environment.",
                accessibility="Wheelchair ramps, therapy units, sign language instruction.",
                fee_structure="KES 30,000–45,000 per term",
                image_url="/static/images/jacaranda.jpg"
            ),
            School(
                name="Treeside Special School",
                region="Nairobi",
                level="Primary",
                contact="0705123456",
                description="Provides individualized education for children with intellectual disabilities.",
                accessibility="Small class sizes, sensory rooms, trained caregivers.",
                fee_structure="KES 25,000–40,000 per term",
                image_url="/static/images/treeside.jpg"
            ),
            School(
                name="Kenya Community Centre for Learning",
                region="Nairobi",
                level="Primary/Secondary",
                contact="0733123456",
                description="Integrates mainstream and special-needs learners in a supportive environment.",
                accessibility="Assistive technology, inclusive programs, counselor support.",
                fee_structure="KES 45,000–70,000 per term",
                image_url="/static/images/kccl.jpg"
            ),
            School(
                name="Heshima Children Center",
                region="Nairobi",
                level="Primary",
                contact="0704567890",
                description="Focuses on holistic education for children with autism and communication challenges.",
                accessibility="Autism-trained teachers, sensory aids, therapy programs.",
                fee_structure="KES 40,000–55,000 per term",
                image_url="/static/images/heshima.jpg"
            ),
            School(
                name="Inclusive Academy Nairobi",
                region="Nairobi",
                level="Primary",
                contact="0711001100",
                description="Blends inclusive learning strategies with personalized support.",
                accessibility="Braille-friendly materials, low-vision aids, peer mentoring.",
                fee_structure="KES 38,000–60,000 per term",
                image_url="/static/images/inclusive_academy.jpg"
            ),
            School(
                name="Unity Inclusive School Nairobi",
                region="Nairobi",
                level="Secondary",
                contact="0711888999",
                description="Promotes equality and accessible learning for differently-abled learners.",
                accessibility="Hearing devices, tactile maps, accessible labs.",
                fee_structure="KES 50,000–75,000 per term",
                image_url="/static/images/unity_inclusive.jpg"
            ),
            School(
                name="Bright Future Special School Nairobi",
                region="Nairobi",
                level="Primary",
                contact="0709988776",
                description="Specialized programs for children with intellectual and physical disabilities.",
                accessibility="Physiotherapy room, specialized support teachers.",
                fee_structure="KES 35,000–55,000 per term",
                image_url="/static/images/bright_future_nrb.jpg"
            ),
            School(
                name="Adaptive Learning Centre Nairobi",
                region="Nairobi",
                level="Vocational",
                contact="0711445566",
                description="Prepares learners with disabilities for independent and vocational life.",
                accessibility="Vocational units, life-skill workshops, guided learning.",
                fee_structure="KES 40,000–50,000 per term",
                image_url="/static/images/adaptive_centre.jpg"
            ),
            School(
                name="Empower Special Needs School Nairobi",
                region="Nairobi",
                level="Primary/Secondary",
                contact="0799123456",
                description="Dedicated to learners with multiple disabilities.",
                accessibility="Multi-sensory learning materials, accessible transport.",
                fee_structure="KES 45,000–70,000 per term",
                image_url="/static/images/empower_nrb.jpg"
            ),

            # --- Kiambu (10 schools) ---
            School(
                name="PCEA Kambui School for the Deaf",
                region="Kiambu",
                level="Primary/Secondary",
                contact="0712333444",
                description="Caters for hearing-impaired students with a strong academic and vocational focus.",
                accessibility="Sign language curriculum, hearing aids, therapy services.",
                fee_structure="KES 30,000–50,000 per term",
                image_url="/static/images/kambui.jpg"
            ),
            School(
                name="S.A. High School for the Blind",
                region="Kiambu",
                level="Secondary",
                contact="0700112233",
                description="Provides quality education for blind and visually impaired learners.",
                accessibility="Braille materials, tactile teaching aids, mobility training.",
                fee_structure="KES 35,000–60,000 per term",
                image_url="/static/images/sa_high.jpg"
            ),
            School(
                name="Kiambu Inclusive Education School",
                region="Kiambu",
                level="Primary",
                contact="0709445566",
                description="Integrates children with mild disabilities into regular classrooms with support.",
                accessibility="Teaching assistants, adaptive PE programs.",
                fee_structure="KES 25,000–45,000 per term",
                image_url="/static/images/kiambu_inclusive.jpg"
            ),
            School(
                name="Future Steps Special School Kiambu",
                region="Kiambu",
                level="Primary",
                contact="0712003300",
                description="Provides personalized support for learners with developmental delays.",
                accessibility="Therapy sessions, structured classrooms, small groups.",
                fee_structure="KES 30,000–50,000 per term",
                image_url="/static/images/future_steps.jpg"
            ),
            School(
                name="Greenfield Special Centre Kiambu",
                region="Kiambu",
                level="Primary",
                contact="0712333222",
                description="Focus on physical and speech impairments.",
                accessibility="Speech therapy, adapted furniture, sensory play.",
                fee_structure="KES 30,000–55,000 per term",
                image_url="/static/images/greenfield_kiambu.jpg"
            ),
            School(
                name="Support & Inclusion School Kiambu",
                region="Kiambu",
                level="Secondary",
                contact="0712789456",
                description="Committed to inclusive secondary education for learners with disabilities.",
                accessibility="Accessible science labs, counseling, peer mentorship.",
                fee_structure="KES 45,000–70,000 per term",
                image_url="/static/images/support_inclusion.jpg"
            ),
            School(
                name="Accessible Learning School Kiambu",
                region="Kiambu",
                level="Primary/Secondary",
                contact="0709988775",
                description="Promotes accessible education using assistive technology.",
                accessibility="Smartboards, text-to-speech tools, digital learning aids.",
                fee_structure="KES 40,000–60,000 per term",
                image_url="/static/images/accessible_learning.jpg"
            ),
            School(
                name="New Horizons Special School Kiambu",
                region="Kiambu",
                level="Vocational",
                contact="0712888999",
                description="Equips learners with practical skills for independence.",
                accessibility="Vocational training units, accessible workshops.",
                fee_structure="KES 35,000–55,000 per term",
                image_url="/static/images/new_horizons.jpg"
            ),
            School(
                name="Pathway Inclusive School Kiambu",
                region="Kiambu",
                level="Primary",
                contact="0712998877",
                description="Fosters an inclusive environment for all learners.",
                accessibility="Play therapy, sign language sessions, sensory integration.",
                fee_structure="KES 30,000–45,000 per term",
                image_url="/static/images/pathway.jpg"
            ),
            School(
                name="Bright Light Special Needs Centre Kiambu",
                region="Kiambu",
                level="Secondary",
                contact="0712456789",
                description="Supports learners with multiple disabilities through individual plans.",
                accessibility="Occupational therapy, low-vision devices, ramps.",
                fee_structure="KES 40,000–65,000 per term",
                image_url="/static/images/bright_light.jpg"
            ),
        ]

        db.session.bulk_save_objects(samples)
        db.session.commit()

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
# Route for the add-school form
@app.route('/add-school')
def add_school_page():
    return render_template('add-school.html')

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
    # if not session.get('admin_logged_in'):
        # return jsonify({"error": "Unauthorized"}), 401
    s = School.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
    return render_template('admin-feedback.html')

@app.route('/api/all-schools')
def all_schools():
    try:
        schools = School.query.all()  # Or however you query schools
        
        schools_data = []
        for school in schools:
            schools_data.append({
                "id": school.id,
                "name": school.name,
                "region": school.region,
                "level": school.level,
                "contact": getattr(school, 'contact', '')  # Handle optional fields
            })
        
        return jsonify(schools_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper function to convert feedback row to dict
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
        'school_name': 'School ' + str(row[1])  # Simple school name
    }

@app.route('/api/feedback', methods=['POST'])
def post_feedback():
    data = request.json or {}
    conn = sqlite3.connect('eduquest.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO feedback (school_id, name, email, message, created_at) VALUES (?, ?, ?, ?, ?)",
        (data.get('school_id'), data.get('name'), data.get('email'), data.get('message'), datetime.now())
    )
    conn.commit()
    feedback_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': feedback_id, 'message': 'Feedback submitted'}), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    conn = sqlite3.connect('eduquest.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
    feedbacks = [feedback_to_dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(feedbacks), 200

@app.route('/api/feedback/<int:feedback_id>/reply', methods=['POST'])
def reply_to_feedback(feedback_id):
    data = request.json
    reply_message = data.get('reply')
    
    conn = sqlite3.connect('eduquest.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE feedback SET admin_reply = ?, reply_date = ? WHERE id = ?",
        (reply_message, datetime.now(), feedback_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Reply added successfully"})

@app.route('/api/feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    conn = sqlite3.connect('eduquest.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Feedback deleted successfully"})

@app.route('/api/schools/<int:school_id>/feedback')
def get_school_feedback(school_id):
    conn = sqlite3.connect('eduquest.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback WHERE school_id = ? ORDER BY created_at DESC", (school_id,))
    feedbacks = [feedback_to_dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(feedbacks)

# SCHOOL DETAILS ROUTE 
from datetime import datetime  # Make sure this import is at the top

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

 # ADD-SCHOOL ROUTE TO HANDLE FORM SUBMISSION
@app.route('/add-school', methods=['POST'])
def submit_school_form():
    name = request.form.get('name')
    region = request.form.get('region')
    level = request.form.get('level')
    description = request.form.get('description')
    contact = request.form.get('contact')
    accessibility = request.form.get('accessibility')
    fee_structure = request.form.get('fee_structure')
    image_url = request.form.get('image_url')

    # ✅ Create and save new school
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

    db.session.add(new_school)
    db.session.commit()

    # Redirect back to dashboard
    return redirect('/admin-dashboard')

#ROUTE FOR THE ADMIN-DASHBOARD TO REDIRECT TO EDIT-SCHOOLS
@app.route('/admin/edit/<int:id>')
def edit_school_page(id):
    school = School.query.get_or_404(id)
    return render_template('edit-school.html', school=school)

# This updates the changes made to schools to the database
@app.route('/admin/edit/<int:id>', methods=['POST'])
def update_school_form(id):
    school = School.query.get_or_404(id)
    
    # Update fields from form inputs
    school.name = request.form.get('name')
    school.region = request.form.get('region')
    school.level = request.form.get('level')
    school.description = request.form.get('description')
    school.contact = request.form.get('contact')
    school.accessibility = request.form.get('accessibility')
    school.fee_structure = request.form.get('fee_structure')
    school.image_url = request.form.get('image_url')
    
    db.session.commit()
    return redirect('/admin-dashboard')


# Dev helper: init-db route
@app.route('/init-db', methods=['GET'])
def init_db_route():
    init_db(seed=True)
    return jsonify({"message": "Database initialized (seeded). Default admin: admin/admin123"}), 200

# ---------------------
# Run
# ---------------------
if __name__ == '__main__':
    # Create DB if missing
    if not os.path.exists(os.path.join(BASE_DIR, 'eduquest.db')):
        with app.app_context():
            init_db(seed=True)
    app.run(debug=True)