from flask import Blueprint, render_template, redirect, url_for, request, flash 
from flask import current_app as app , session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Campaign, AdRequest, Influencer, Sponsor
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('home.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html')

        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        if role == 'sponsor':
            sponsor = Sponsor(user_id=new_user.id)
            db.session.add(sponsor)
        elif role == 'influencer':
            influencer = Influencer(user_id=new_user.id)
            db.session.add(influencer)
        # No additional table needed for admin, just commit user to DB

        db.session.commit()
        login_user(new_user)
        return redirect(url_for('routes.dashboard'))
    
    return render_template('register.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@routes.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('routes.admin_dashboard'))
    elif current_user.role == 'sponsor':
        return redirect(url_for('routes.sponsor_dashboard'))
    elif current_user.role == 'influencer':
        return redirect(url_for('routes.influencer_dashboard'))
    return redirect(url_for('routes.login'))

@routes.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('routes.login'))
    active_users = User.query.count()
    public_campaigns = Campaign.query.filter_by(visibility='public').count()
    private_campaigns = Campaign.query.filter_by(visibility='private').count()
    ad_requests = AdRequest.query.count()
    flagged_users = User.query.filter_by(flagged=True).count()

    return render_template('admin_dashboard.html', 
                            active_users=active_users, 
                            public_campaigns=public_campaigns, 
                            private_campaigns=private_campaigns, 
                            ad_requests=ad_requests, 
                            flagged_users=flagged_users)

@routes.route('/sponsor_dashboard')
@login_required
def sponsor_dashboard():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))
    
    # Retrieve the sponsor details
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Retrieve the campaigns for the sponsor
    campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()

    return render_template('sponsor_dashboard.html', campaigns=campaigns, sponsor=sponsor)

@routes.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))

    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        budget = request.form.get('budget')

        sponsor.company_name = company_name
        sponsor.industry = industry
        sponsor.budget = budget

        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.profile'))

    return render_template('profile.html', sponsor=sponsor)

@routes.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))
    
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        sponsor.company_name = request.form.get('company_name')
        sponsor.industry = request.form.get('industry')
        sponsor.budget = request.form.get('budget')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.sponsor_dashboard'))
    
    return render_template('update_profile.html', sponsor=sponsor)


@routes.route('/influencer_dashboard')
@login_required
def influencer_dashboard():
    if current_user.role != 'influencer':
        return redirect(url_for('routes.login'))
    return render_template('influencer_dashboard.html')

@routes.route('/create_campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        budget = float(request.form['budget'])
        visibility = request.form['visibility']
        goals = request.form['goals']
        
        campaign = Campaign(
            name=name, 
            description=description, 
            start_date=start_date, 
            end_date=end_date, 
            budget=budget, 
            visibility=visibility, 
            goals=goals, 
            sponsor_id=current_user.id
        )
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('routes.sponsor_dashboard'))
    return render_template('create_campaign.html')

@routes.route('/create_ad_request', methods=['GET', 'POST'])
@login_required
def create_ad_request():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))
    
    # Get ongoing campaigns for the dropdown
    ongoing_campaigns = Campaign.query.filter(
        Campaign.sponsor_id == current_user.id,
        Campaign.end_date >= datetime.utcnow().date()
    ).all()

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        influencer_id = request.form.get('influencer_id')
        messages = request.form.get('messages')
        requirements = request.form.get('requirements')
        payment_amount = request.form.get('payment_amount')
        status = 'Pending'

        # Check if the influencer_id is valid
        influencer = User.query.get(influencer_id)
        if not influencer or influencer.role != 'influencer':
            flash('Invalid Influencer ID. Please enter a valid Influencer ID.', 'danger')
            return render_template('create_ad_request.html', campaigns=ongoing_campaigns)

        ad_request = AdRequest(
            campaign_id=campaign_id, 
            influencer_id=influencer_id, 
            sponsor_id=current_user.id, 
            messages=messages, 
            requirements=requirements, 
            payment_amount=payment_amount, 
            status=status
        )
        db.session.add(ad_request)
        db.session.commit()

        flash('Ad request created successfully!', 'success')
        return redirect(url_for('routes.sponsor_dashboard'))
    
    return render_template('create_ad_request.html', campaigns=ongoing_campaigns)


@routes.route('/search_influencers', methods=['GET', 'POST'])
@login_required
def search_influencers():
    if current_user.role != 'sponsor':
        return redirect(url_for('routes.login'))
    
    influencers = []
    if request.method == 'POST':
        niche = request.form.get('niche')
        reach = request.form.get('reach')

        query = Influencer.query

        if niche:
            query = query.filter_by(niche=niche)
        if reach:
            query = query.filter(Influencer.reach >= int(reach))
        
        influencers = query.all()

    return render_template('search_influencers.html', influencers=influencers)

@routes.route('/search_campaigns', methods=['GET', 'POST'])
@login_required
def search_campaigns():
    if current_user.role != 'influencer':
        return redirect(url_for('routes.login'))
    
    campaigns = []
    if request.method == 'POST':
        niche = request.form.get('niche')
        budget = request.form.get('budget')
        campaigns = Campaign.query.filter(Campaign.goals.like(f"%{niche}%"), Campaign.budget <= budget, Campaign.visibility == 'public').all()
    
    return render_template('search_campaigns.html', campaigns=campaigns)

@routes.route('/view_ad_requests')
@login_required
def view_ad_requests():
    app.logger.debug(f"Current user: {current_user.username}, Role: {current_user.role}")
    app.logger.debug(f"Session data: {session}")

    if current_user.role not in ['sponsor', 'influencer']:
        return redirect(url_for('routes.login'))

    if current_user.role == 'influencer':
        # Fetch ad requests where the current user is the influencer
        ad_requests = AdRequest.query.filter_by(influencer_id=current_user.id).order_by(AdRequest.created_at.desc()).all()
    else:
        # Fetch ad requests where the current user is the sponsor and the request was created by an influencer
        ad_requests = (AdRequest.query
                       .join(Campaign)
                       .filter(Campaign.sponsor_id == current_user.id)
                       .filter(AdRequest.influencer_id.isnot(None))  # Ensure the request was created by an influencer
                       .order_by(AdRequest.created_at.desc())
                       .all())

    return render_template('view_ad_requests.html', ad_requests=ad_requests)

@routes.route('/accept_ad_request/<int:ad_request_id>', methods=['GET'])
@login_required
def accept_ad_request(ad_request_id):
    if current_user.role != 'sponsor' and current_user.role != 'influencer':
        return redirect(url_for('routes.login'))
    
    ad_request = AdRequest.query.get(ad_request_id)
    
    if ad_request is None:
        flash('Ad request not found.', 'danger')
        return redirect(url_for('routes.view_ad_requests'))
    
    # Check if the sponsor or influencer is allowed to accept the request
    if (current_user.role == 'sponsor' and current_user.id != ad_request.sponsor_id) or (current_user.role == 'influencer' and current_user.id != ad_request.influencer_id):
        flash('You cannot accept this ad request.', 'danger')
        return redirect(url_for('routes.view_ad_requests'))
    
    ad_request.status = 'Accepted'
    db.session.commit()
    
    flash('Ad request accepted successfully!', 'success')
    return redirect(url_for('routes.view_ad_requests'))

@routes.route('/reject_ad_request/<int:ad_request_id>', methods=['GET'])
@login_required
def reject_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if current_user.role != 'sponsor' and current_user.role != 'influencer':
        return redirect(url_for('routes.login'))

    # Check if the sponsor or influencer is allowed to reject the request
    if (current_user.role == 'sponsor' and current_user.id != ad_request.sponsor_id) or (current_user.role == 'influencer' and current_user.id != ad_request.influencer_id):
        flash('You cannot reject this ad request.', 'danger')
        return redirect(url_for('routes.view_ad_requests'))

    if ad_request.status in ['Accepted', 'Rejected']:
        return redirect(url_for('routes.view_ad_requests'))  # Or handle this case differently if needed
    
    ad_request.status = 'Rejected'
    db.session.commit()
    
    flash('Ad request rejected successfully!', 'success')
    return redirect(url_for('routes.view_ad_requests'))

@routes.route('/negotiate_ad_request/<int:ad_request_id>', methods=['GET', 'POST'])
@login_required
def negotiate_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if current_user.role != 'influencer':
        return redirect(url_for('routes.login'))

    if current_user.id != ad_request.influencer_id:
        flash('You cannot negotiate this ad request.', 'danger')
        return redirect(url_for('routes.view_ad_requests'))
    
    if ad_request.status in ['Accepted', 'Rejected']:
        return redirect(url_for('routes.view_ad_requests'))  # Or handle this case differently if needed
    
    if request.method == 'POST':
        ad_request.payment_amount = request.form.get('payment_amount')
        ad_request.status = 'Pending'
        db.session.commit()
        flash('Ad request negotiated and sent back to sponsor.', 'success')
        return redirect(url_for('routes.view_ad_requests'))

    return render_template('negotiate_ad_request.html', ad_request=ad_request)

@routes.route('/influencer_profile', methods=['GET', 'POST'])
@login_required
def influencer_profile():
    if current_user.role != 'influencer':
        return redirect(url_for('routes.login'))

    influencer = Influencer.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        category = request.form.get('category')
        niche = request.form.get('niche')
        reach = request.form.get('reach')

        influencer.category = category
        influencer.niche = niche
        influencer.reach = reach

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.influencer_profile'))

    return render_template('influencer_profile.html', influencer=influencer)