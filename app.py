import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from models import db, School 
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'change_this_secret_for_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'eduquest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

# ---------------------
# Models
# ---------------------
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)  # Make this required
    email = db.Column(db.String(120), nullable=True)  # Optional but useful for follow-up
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship (optional but handy for easy school access)
     #school = db.relationship('School', backref=db.backref('feedbacks', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "name": self.name,
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
# Database init / seed
# ---------------------
def init_db(seed=True):
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

# Feedback
@app.route('/api/feedback', methods=['POST'])
def post_feedback():
    data = request.json or {}
    f = Feedback(
        school_id=data.get('school_id'),
        name=data.get('name'),
        message=data.get('message', '')
    )
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    fs = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify([f.to_dict() for f in fs]), 200


# SCHOOL DETAILS ROUTE 

@app.route('/school/<int:id>')
def school_details(id):
    school = School.query.get_or_404(id)
    feedbacks = Feedback.query.filter_by(school_id=id).order_by(Feedback.created_at.desc()).all()

    # Optional: If you’ll add principals later
    principal = None
    try:
        principal = Principal.query.filter_by(school_id=id).first()
    except Exception:
        pass  # In case Principal model doesn’t exist yet

    return render_template('school_details.html', school=school, feedbacks=feedbacks, principal=principal)


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
