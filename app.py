# main.py
from flask import Flask, request, redirect, render_template, url_for, jsonify, send_from_directory
from sqlalchemy import func
from datetime import datetime, timezone
import os
from application.database import db

#================================= APP AND DATABASE INITIALISATION ===============================================#
def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'services.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    db.init_app(app) 
    return app

app = create_app()
from application.models import User, Customer, Professional, Service, ServiceRequest, Review

#==================================== LOGIN AND REGISTER FUNCTIONS ===============================================#
@app.route('/', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        return render_template("home.html")  
    elif request.method == 'POST':
        username = request.form.get("username") 
        password = request.form.get("password")
        if username == "Admin" and password == "Pink1819@!":
            return redirect(url_for("admin_dashboard"))
        user = User.query.filter_by(username=username).first()
        print(user)
        if user:
            if user.password_hash == password:
                professional = Professional.query.filter_by(user_id=user.id).first()
                if professional:
                    if professional.is_verified == "Pending":
                        return render_template("verification_pending.html")
                    elif professional.is_verified == "Rejected":
                        return render_template("verification_rejected.html")
                    elif professional.is_blocked:
                        return render_template("account_blocked.html")
                    else:
                        return redirect(url_for("professional_dashboard", professional_id=professional.id))
                customer = Customer.query.filter_by(user_id=user.id).first()
                if customer:
                    if customer.is_blocked:
                        return render_template("account_blocked.html")
                    else:
                        return redirect(url_for("customer_dashboard", customer_id=customer.id))
        return redirect(url_for("login_error"))

@app.route('/professional_register', methods=['GET', 'POST'])
def professional_register():
    services = Service.query.all() 
    if request.method == 'GET':
        return render_template('professional_register.html', services=services, error=None) 
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        service_id = request.form.get('service_id')
        experience_years = request.form.get('experience_years')
        documents = request.files.get('documents')
        description = request.form.get('description')
        phone = request.form.get('phone')
        location = request.form.get('location')
        pincode = request.form.get('pincode')
      
        if not (username and password and name and service_id and experience_years and description and phone):
            return render_template('professional_register.html', services=services)
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('professional_register.html', services=services)
      
        docs_folder = os.path.join(app.root_path, 'professional_docs')
        os.makedirs(docs_folder, exist_ok=True)
        if documents:
            import uuid
            filename = f"{username}_{uuid.uuid4().hex}.pdf"
            documents_path = os.path.join(docs_folder, filename)
            documents.save(documents_path)
        else:
            documents_path = None

        new_user = User(
            username=username,
            password_hash=password,
            user_type='Professional'
        )
        db.session.add(new_user)
        db.session.commit()

        new_professional = Professional(
            user_id=new_user.id,
            service_id=service_id,
            name=name,
            phone=phone,
            experience_years=experience_years,
            description=description,
            is_verified="Pending",
            documents_path=documents_path,
            location = location,
            pincode = pincode
        )
        db.session.add(new_professional)
        db.session.commit()
        return redirect(url_for('user_login'))

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'GET':
        return render_template('customer_register.html')

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone = request.form.get('phone')
        try:
            new_user = User(
                username=username,
                password_hash=password, 
                user_type='Customer'
            )
            db.session.add(new_user)
            db.session.commit()
            new_customer = Customer(
                user_id=new_user.id,
                name=fullname,
                address=address,
                pincode=pincode,
                phone=phone,
                is_blocked=False
            )
            db.session.add(new_customer)
            db.session.commit()
            return redirect(url_for('user_login'))

        except Exception as e:
            db.session.rollback()
            return render_template('customer_register.html')

@app.route('/login_error', methods=['GET'])
def login_error():
    return render_template("login_error.html")

#=========================================== ADMIN FUNCTIONS ===============================================#
@app.route("/admin_dashboard", methods = ['GET'])
def admin_dashboard():
    customers = Customer.query.all()
    services = Service.query.all()
    professionals = Professional.query.all()
    service_requests = ServiceRequest.query.all()
    return render_template("admin_dashboard.html", customers = customers, services = services, professionals = professionals, service_requests = service_requests)

#---------------------------- ADMIN : SERVICE RELATED FUNCTIONS --------------------------------------------#     
@app.route('/service/<int:id>', methods=['GET'])
def service_details(id):
    service = Service.query.filter_by(id=id).first()
    professionals = Professional.query.filter_by(service_id = id, is_verified = "Accepted").all()
    
    if not service:
        return redirect(url_for('admin_dashboard'))
    return render_template('service_details.html', service=service, professionals=professionals)

@app.route("/add_service", methods=["GET","POST"])
def add_service():
    if request.method == "GET":
        return render_template("new_service.html")
    else:
        name = request.form.get("name")
        time_required = request.form.get("time_required")
        base_price = request.form.get("base_price")
        description = request.form.get("description")
        category = request.form.get("category")
        new_service = Service(
            name=name,
            time_required=int(time_required),
            base_price=float(base_price),
            description=description,
            category = category
        )

        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route("/delete_service/<int:service_id>", methods=["GET"])
def delete_service(service_id):
    service = Service.query.get(service_id)
    if service is None:
        return f"Service with ID {service_id} not found.", 404
    try:
        db.session.delete(service)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"An error occurred while deleting the service: {str(e)}", 500
    return redirect(url_for("admin_dashboard"))

@app.route("/edit_service/<int:service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)   
    if request.method == "GET":
        return render_template("edit_service.html", service=service) 
    else:  
        name = request.form.get("name")
        time_required = request.form.get("time_required")
        base_price = request.form.get("base_price")
        description = request.form.get("description")
        category = request.form.get("category")
        try:
            service.name = name
            service.time_required = int(time_required)
            service.base_price = float(base_price)
            service.description = description
            service.category = category

            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template("edit_service.html", service=service)

#---------------------------- ADMIN : CUSTOMER RELATED FUNCTIONS --------------------------------------------#
@app.route('/customer_details/<int:id>')
def customer_details(id):
    customer = Customer.query.get_or_404(id)
    requests = ServiceRequest.query.filter_by(customer_id=id).all()
    return render_template('customer_details.html', customer=customer, requests=requests)

@app.route('/block_customer/<int:id>', methods=['POST'])
def block_customer(id):
    customer = Customer.query.get(id)
    if customer:
        customer.is_blocked = True
        db.session.commit()
    return redirect(url_for('admin_dashboard'))  

@app.route('/unblock_customer/<int:id>', methods=['POST'])
def unblock_customer(id):
    customer = Customer.query.get(id)
    if customer:
        customer.is_blocked = False
        db.session.commit()
    return redirect(url_for('admin_dashboard'))  

@app.route('/delete_customer/<int:id>', methods=['POST'])
def delete_customer(id):
    customer = Customer.query.get(id)
    if customer:
        user = User.query.get(customer.user_id)  
        try:
            db.session.delete(customer)
            if user:
                db.session.delete(user) 
            db.session.commit()  
        except Exception as e:
            db.session.rollback()  
            print(f"Error deleting customer: {e}")  
    return redirect(url_for('admin_dashboard'))  

#---------------------------- ADMIN : PROFESSIONAL RELATED FUNCTIONS --------------------------------------------#
@app.route('/professional_details/<int:id>', methods=['GET', 'POST'])
def professional_details(id):
    professional = Professional.query.get_or_404(id)
    requests = ServiceRequest.query.filter_by(professional_id=id).all()
    if request.method == 'POST':
        new_rating = request.form.get('rating', type=float)
        if new_rating and 1 <= new_rating <= 5: 
            professional.average_rating = new_rating  
            db.session.commit() 
    return render_template('professional_details.html', professional=professional, requests=requests)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    safe_filename = os.path.basename(filename)
    upload_dir = os.path.join(app.root_path, 'professional_docs') 
    return send_from_directory(upload_dir, safe_filename)

@app.route('/approve_professional/<int:id>', methods=['POST'])
def approve_professional(id):
    professional = Professional.query.get_or_404(id) 
    if professional.is_verified == "Pending":
        professional.is_verified = "Accepted"
        db.session.commit()  
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_professional/<int:id>', methods=['POST'])
def reject_professional(id):
    professional = Professional.query.get_or_404(id) 
    if professional.is_verified == "Pending":
        professional.is_verified = "Rejected"
        db.session.commit()  
    return redirect(url_for('admin_dashboard')) 

@app.route('/delete_professional/<int:id>', methods=['POST'])
def delete_professional(id):
    professional = Professional.query.get_or_404(id)
    user = User.query.get(professional.user_id)
    try:
        db.session.delete(professional)
        if user:
            db.session.delete(user) 
        db.session.commit()
    except Exception as e:
        db.session.rollback()  
        print(f"Error deleting professional: {e}") 
    return redirect(url_for('admin_dashboard')) 

@app.route('/block_professional/<int:id>', methods=['POST'])
def block_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.is_blocked = True
        db.session.commit()
    return redirect(url_for('admin_dashboard')) 

@app.route('/unblock_professional/<int:id>', methods=['POST'])
def unblock_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.is_blocked = False
        db.session.commit()
    return redirect(url_for('admin_dashboard')) 

#---------------------------- ADMIN : SERVICE REQUEST RELATED FUNCTIONS --------------------------------------------#
@app.route('/service_request/<int:id>', methods=['GET', 'POST'])
def service_request_details(id):
    request = ServiceRequest.query.filter_by(id=id).first()
    if not request:
        return redirect(url_for('admin_dashboard'))
    print(f"Request Status: {request.status}")
    review = Review.query.filter_by(request_id=id).first()
    print(f"Review or Report: {review}")
    if review:
        print(f"Review/Report ID: {review.id}")
        print(f"Review/Report Rating: {review.rating}")
        print(f"Review/Report Text: {review.review_text}")
    return render_template(
        'service_request_details.html',
        request = request,
        review = review
    )

#------------------------------------------ ADMIN : SEARCH FUNCTION ------------------------------------------------#
@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    services = Service.query.all()
    customers = Customer.query.all()
    professionals = Professional.query.all()
    service_requests = ServiceRequest.query.all()

    results = [] 
    if request.method == 'POST':
        search_criteria = request.form.get('search_criteria')
        search_value = request.form.get('search_value')
        if search_criteria == 'service_category':
            results = Service.query.filter(Service.category.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'customer_location':
            results = Customer.query.filter(Customer.address.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'customer_pincode':
            results = Customer.query.filter(Customer.pincode == search_value).all()
        elif search_criteria == 'customer_account_status':
            results = Customer.query.filter(Customer.is_blocked == (search_value == 'Blocked')).all()
        elif search_criteria == 'professional_service':
            results = Professional.query.filter(Professional.service.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'professional_account_status':
            results = Professional.query.filter(Professional.is_verified.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'professional_status':
            results = Professional.query.filter(Professional.is_blocked == (search_value == 'Blocked')).all()
        elif search_criteria == 'service_request_status':
            results = ServiceRequest.query.filter(ServiceRequest.status.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'service_request_date':
            try:
                search_date = datetime.strptime(search_value, '%Y-%m-%d').date()
                results = ServiceRequest.query.filter(
                    db.func.date(ServiceRequest.request_date) == search_date
                ).all()
            except ValueError:
                results = []  
        else:
            results = [] 
    return render_template(
        'admin_search.html',
        services=services,
        customers=customers,
        professionals=professionals,
        service_requests=service_requests,
        results=results,
        search_criteria=search_criteria if request.method == 'POST' else None
    )

#================================= PROFESSIONAL FUNCTIONS ===============================================#
@app.route('/professional/<int:professional_id>/dashboard')
def professional_dashboard(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    today = datetime.utcnow().date()

    todays_services = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        db.func.date(ServiceRequest.request_date) == today,
        ServiceRequest.status != "Deleted"
    ).all() 
    future_services = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        db.func.date(ServiceRequest.request_date) > today,
        ServiceRequest.status != "Deleted"
    ).all()
    past_services = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        db.func.date(ServiceRequest.request_date) < today,
        ServiceRequest.status != "Deleted"
    ).all()
    return render_template(
        'professional_dashboard.html',
        professional=professional,
        todays_services=todays_services,
        future_services=future_services,
        past_services=past_services
    )

#---------------------------- PROFESSIONAL : DASHBOARD FUNCTIONS --------------------------------------------#  
@app.route('/service-request/<int:request_id>/action', methods=['POST'])
def handle_service_request_action(request_id):
    action = request.form.get('action')
    service_request = ServiceRequest.query.get_or_404(request_id)

    if action == "accept":
        if service_request.status in ["Pending", "Rejected"]:
            service_request.status = "Accepted"
    elif action == "reject":
        if service_request.status in ["Pending", "Accepted"]:
            service_request.status = "Rejected"
    elif action == "delete":
        if service_request.status == "Rejected":
            service_request.status = "Deleted"
    db.session.commit()
    return redirect(url_for('professional_dashboard', professional_id=service_request.professional_id))

@app.route('/view_review_professional/<int:request_id>', methods = ['GET', 'POST'])
def view_review_professional(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    review = Review.query.filter_by(request_id=request_id).first()
    return render_template('view_review_professional.html', service_request=service_request, review=review)

@app.route('/view_report_professional/<int:request_id>', methods=['GET', 'POST'])
def view_report_professional(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    report = Review.query.filter_by(request_id=request_id).first()
    if not report:
        return redirect(url_for('professional_dashboard', professional_id=service_request.professional_id))
    return render_template('view_report_professional.html', service_request=service_request, report=report)

#---------------------------- PROFESSIONAL : PROFILE FUNCTIONS --------------------------------------------# 
@app.route('/professional_profile/<int:professional_id>')
def professional_profile(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    return render_template('professional_profile.html', professional=professional)

@app.route('/edit_professional_profile/<int:professional_id>', methods=['GET', 'POST'])
def edit_professional_profile(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    if request.method == 'POST':
        professional.name = request.form['name']
        professional.phone = request.form['phone']
        professional.experience_years = request.form['experience_years']
        professional.description = request.form['description']
        professional.location = request.form['location']
        professional.pincode = request.form['pincode']
        db.session.commit()
        return redirect(url_for('professional_profile', professional_id=professional.id))   
    return render_template('edit_professional_profile.html', professional=professional)

#---------------------------- PROFESSIONAL : SEARCH FUNCTION --------------------------------------------# 
@app.route('/search_professional/<int:professional_id>', methods=['GET', 'POST'])
def search_professional(professional_id):
    professional = Professional.query.get(professional_id)
    services = Service.query.all()
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()
    if request.method == 'POST':
        search_criteria = request.form.get('search_criteria')
        search_value = request.form.get('search_value')
        if search_criteria == 'location':
            results = (
                ServiceRequest.query
                .join(Customer, Customer.id == ServiceRequest.customer_id) 
                .filter(ServiceRequest.professional_id == professional_id)
                .filter(Customer.address.ilike(f'%{search_value}%'))
                .all()
            )
        elif search_criteria == 'pincode':
            results = (
                ServiceRequest.query
                .join(Customer, Customer.id == ServiceRequest.customer_id)
                .filter(ServiceRequest.professional_id == professional_id)  
                .filter(Customer.pincode == search_value)            
                .all()
            )
        elif search_criteria == 'date':
            try:
                search_date = datetime.strptime(search_value, '%Y-%m-%d').date()
                results = ServiceRequest.query.filter(
                    ServiceRequest.professional_id == professional_id,
                    db.func.date(ServiceRequest.request_date) == search_date
                ).all()
            except ValueError:
                results = [] 
        elif search_criteria == 'status':
            results = ServiceRequest.query.filter(
                ServiceRequest.professional_id == professional_id,
                ServiceRequest.status.ilike(f'%{search_value}%')
            ).all()
        else:
            results = []
        return render_template(
            'search_professional.html',
            professional=professional,
            services=services,
            service_requests=service_requests,
            results=results,
            search_criteria=search_criteria
        )
    return render_template(
        'search_professional.html',
        professional=professional,
        services=services,
        service_requests=service_requests
    )

#================================= CUSTOMER FUNCTIONS ===============================================#
@app.route('/customer/<int:customer_id>/dashboard', methods = ['GET'])
def customer_dashboard(customer_id):
    customer = Customer.query.filter_by(id=customer_id).first()
    if not customer:
        return redirect(url_for('login_error'))  
    categories = db.session.query(Service.category).distinct().all()
    categories = [category[0] for category in categories]
    service_history = ServiceRequest.query.filter_by(customer_id=customer_id)\
        .order_by(ServiceRequest.request_date.desc())\
        .all() 
    return render_template(
        'customer_dashboard.html',
        customer = customer,
        categories=categories,
        service_history=service_history
    )

#---------------------------- CUSTOMER : DASHBOARD FUNCTIONS --------------------------------------------# 
@app.route('/category_details/<int:customer_id>/<string:category>', methods=['GET'])
def category_details(customer_id, category):
    services = Service.query.filter_by(category = category).all()
    return render_template(
        'category_details.html',
        customer_id=customer_id,
        services=services,
        category = category
    )

@app.route('/view_professionals/<int:customer_id>/<int:service_id>', methods=['GET'])
def view_professionals(customer_id, service_id):
    professionals = Professional.query.filter(Professional.service_id == service_id, Professional.is_blocked == False, Professional.is_verified == "Accepted").all()
    service = Service.query.filter_by(id = service_id).first()
    print(service)
    return render_template(
        'view_professionals.html',
        customer_id=customer_id,
        service_id=service_id,
        professionals=professionals,
        service = service
    )

@app.route('/book_service/<int:customer_id>/<int:professional_id>/<int:service_id>', methods=['GET', 'POST'])
def book_service(customer_id, professional_id, service_id):
    professional = Professional.query.get_or_404(professional_id)
    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        booking_datetime_str = request.form['booking_datetime']
        booking_datetime = datetime.strptime(booking_datetime_str, '%Y-%m-%dT%H:%M')
        new_service_request = ServiceRequest(
            customer_id=customer_id,
            service_id=service_id,
            professional_id=professional_id,
            request_date=booking_datetime,
            is_completed_customer=False,
            is_completed_professional=False,
            rating=0,
            status = "Pending",
            completed_date=None
        )
        db.session.add(new_service_request)
        db.session.commit()
        return redirect(url_for('customer_dashboard', customer_id=customer_id))

    return render_template(
        'book_service.html',
        customer_id=customer_id,
        professional=professional,
        service=service
    )

@app.route('/cancel_service/<int:request_id>', methods=['POST'])
def cancel_service(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    db.session.delete(service_request)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/complete_service/<int:request_id>', methods=['GET', 'POST'])
def complete_service(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.completed_date = datetime.utcnow()
    service_request.status = "Completed"
    db.session.commit()
    if request.method == 'POST':
        rating = float(request.form.get('rating', 0))
        review_text = request.form.get('review_text')
        review = Review(
            request_id=service_request.id,
            customer_id=service_request.customer_id,
            professional_id=service_request.professional_id,
            rating=rating,
            review_text=review_text
        )
        db.session.add(review)
        db.session.commit()
        professional = Professional.query.get(service_request.professional_id)
        avg_rating_query = db.session.query(func.avg(Review.rating)).filter(
            Review.professional_id == professional.id,
            Review.rating.isnot(None)
        ).scalar()
        professional.average_rating = round(avg_rating_query or 0.0, 2)
        db.session.commit()
        return redirect(url_for('customer_dashboard', customer_id=service_request.customer_id))
    return render_template('review_form.html', service_request=service_request)

@app.route('/view_review_customer/<int:request_id>', methods = ['GET', 'POST'])
def view_review_customer(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    review = Review.query.filter_by(request_id=request_id).first()
    return render_template('view_review_customer.html', service_request=service_request, review=review)

@app.route('/report_service/<int:request_id>', methods=['GET', 'POST'])
def report_service(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.status = "Reported"
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        report = Review(
            request_id=service_request.id,
            customer_id=service_request.customer_id,
            professional_id=service_request.professional_id,
            rating=0,  
            review_text=f"Reported: {reason}" if reason else "Reported without a reason"
        )
        db.session.add(report)
        db.session.commit()
        return redirect(url_for('customer_dashboard', customer_id=service_request.customer_id))
    return render_template('report_form.html', service_request=service_request)

@app.route('/view_report_customer/<int:request_id>', methods=['GET', 'POST'])
def view_report_customer(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    report = Review.query.filter_by(request_id=request_id).first()
    if not report:
        return redirect(url_for('customer_dashboard', customer_id=service_request.customer_id))
    return render_template('view_report_customer.html', service_request=service_request, report=report)

#---------------------------- CUSTOMER : PROFILE FUNCTIONS --------------------------------------------# 
@app.route('/customer_profile/<int:customer_id>')
def customer_profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('customer_profile.html', customer=customer)

@app.route('/edit_customer_profile/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer_profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        customer.pincode = request.form['pincode']
        db.session.commit()
        return redirect(url_for('customer_profile', customer_id=customer.id)) 
    return render_template('edit_customer_profile.html', customer=customer)

#---------------------------- CUSTOMER : SEARCH FUNCTION --------------------------------------------# 
@app.route('/search_customer/<int:customer_id>', methods=['GET', 'POST'])
def search_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if request.method == 'POST':
        search_criteria = request.form.get('search_criteria')
        search_value = request.form.get('search_value')
        if search_criteria == 'location':
            results = Professional.query.filter(Professional.location.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'pincode':
            results = Professional.query.filter(Professional.pincode == search_value).all()
        elif search_criteria == 'category':
            results = Service.query.filter(Service.category.ilike(f'%{search_value}%')).all()
        elif search_criteria == 'status':
            results = ServiceRequest.query.filter(ServiceRequest.status.ilike(f'%{search_value}%')).all()
        else:
            results = []
        return render_template('search_customer.html', customer=customer, results=results, search_criteria = search_criteria)
    return render_template('search_customer.html', customer=customer)


if __name__ == "__main__":
    app.run(debug = True)