from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Community(db.Model):
    __tablename__ = 'communities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='community', lazy=True)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')
    
    is_admin = db.Column(db.Boolean, default=False)
    
    points = db.Column(db.Integer, default=100)
    reputation_score = db.Column(db.Float, default=5.0)
    total_helps = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group_buys = db.relationship('GroupBuy', backref='creator', lazy=True, foreign_keys='GroupBuy.creator_id')
    group_buy_participants = db.relationship('GroupBuyParticipant', backref='user', lazy=True, foreign_keys='GroupBuyParticipant.user_id')
    tools = db.relationship('Tool', backref='owner', lazy=True, foreign_keys='Tool.owner_id')
    borrowed_tools = db.relationship('Tool', backref='current_borrower', lazy=True, foreign_keys='Tool.current_borrower_id')
    tool_loans = db.relationship('ToolLoan', backref='borrower', lazy=True, foreign_keys='ToolLoan.borrower_id')
    dog_walks = db.relationship('DogWalk', backref='creator', lazy=True, foreign_keys='DogWalk.creator_id')
    helped_dog_walks = db.relationship('DogWalk', backref='helper', lazy=True, foreign_keys='DogWalk.helper_id')
    points_logs = db.relationship('PointsLog', backref='user', lazy=True, foreign_keys='PointsLog.user_id')
    address_verifications = db.relationship('AddressVerification', backref='user', lazy=True, foreign_keys='AddressVerification.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AddressVerification(db.Model):
    __tablename__ = 'address_verifications'
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    DOCUMENT_TYPE_ID_CARD = 'id_card'
    DOCUMENT_TYPE_PROPERTY_CERT = 'property_certificate'
    DOCUMENT_TYPE_RENTAL_CONTRACT = 'rental_contract'
    DOCUMENT_TYPE_UTILITY_BILL = 'utility_bill'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    document_type = db.Column(db.String(50), nullable=False)
    document_number = db.Column(db.String(100), nullable=True)
    document_image_url = db.Column(db.String(255), nullable=True)
    
    property_address = db.Column(db.String(255), nullable=True)
    property_owner_name = db.Column(db.String(100), nullable=True)
    
    id_card_number = db.Column(db.String(20), nullable=True)
    id_card_name = db.Column(db.String(100), nullable=True)
    id_card_address = db.Column(db.String(255), nullable=True)
    id_card_front_url = db.Column(db.String(255), nullable=True)
    id_card_back_url = db.Column(db.String(255), nullable=True)
    
    additional_documents = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default=STATUS_PENDING)
    admin_note = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviewer = db.relationship('User', backref='reviews', lazy=True, foreign_keys='AddressVerification.reviewed_by')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class GroupBuy(db.Model):
    __tablename__ = 'group_buys'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    category = db.Column(db.String(50), default='生鲜蔬菜')
    min_participants = db.Column(db.Integer, default=5)
    max_participants = db.Column(db.Integer, nullable=True)
    current_participants = db.Column(db.Integer, default=0)
    
    price_per_person = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    delivery_date = db.Column(db.DateTime, nullable=True)
    
    status = db.Column(db.String(20), default='recruiting')
    
    image_url = db.Column(db.String(255), nullable=True)
    pickup_location = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    participants = db.relationship('GroupBuyParticipant', backref='group_buy', lazy=True)


class GroupBuyParticipant(db.Model):
    __tablename__ = 'group_buy_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    group_buy_id = db.Column(db.Integer, db.ForeignKey('group_buys.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    
    is_paid = db.Column(db.Boolean, default=False)
    is_received = db.Column(db.Boolean, default=False)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('group_buy_id', 'user_id'),)


class Tool(db.Model):
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default='家用工具')
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    
    deposit = db.Column(db.Float, default=0)
    points_required = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default='available')
    current_borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    image_url = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    loans = db.relationship('ToolLoan', backref='tool', lazy=True)


class ToolLoan(db.Model):
    __tablename__ = 'tool_loans'
    
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_return_date = db.Column(db.DateTime, nullable=False)
    actual_return_date = db.Column(db.DateTime, nullable=True)
    
    status = db.Column(db.String(20), default='active')
    
    borrower_rating = db.Column(db.Integer, nullable=True)
    borrower_comment = db.Column(db.Text, nullable=True)
    
    owner_rating = db.Column(db.Integer, nullable=True)
    owner_comment = db.Column(db.Text, nullable=True)
    
    points_transferred = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DogWalk(db.Model):
    __tablename__ = 'dog_walks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    
    dog_name = db.Column(db.String(50), nullable=True)
    dog_breed = db.Column(db.String(50), nullable=True)
    dog_age = db.Column(db.Integer, nullable=True)
    dog_size = db.Column(db.String(20), default='medium')
    
    walk_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    meeting_location = db.Column(db.String(200), nullable=True)
    
    points_reward = db.Column(db.Integer, default=10)
    
    status = db.Column(db.String(20), default='open')
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    creator_rating = db.Column(db.Integer, nullable=True)
    creator_comment = db.Column(db.Text, nullable=True)
    
    helper_rating = db.Column(db.Integer, nullable=True)
    helper_comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointsLog(db.Model):
    __tablename__ = 'points_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    points_change = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    
    reason = db.Column(db.String(100), nullable=False)
    related_type = db.Column(db.String(50), nullable=True)
    related_id = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
