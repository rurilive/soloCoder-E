import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import AddressVerification, User
from app import db

verification = Blueprint('verification', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, subfolder):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    subfolder_path = os.path.join(upload_folder, subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path, exist_ok=True)
    
    file_path = os.path.join(subfolder_path, unique_filename)
    file.save(file_path)
    
    return f"/static/uploads/{subfolder}/{unique_filename}"


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('您没有权限访问此页面', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@verification.route('/address-verification/create', methods=['GET', 'POST'])
@login_required
def create():
    existing_pending = AddressVerification.query.filter_by(
        user_id=current_user.id,
        status=AddressVerification.STATUS_PENDING
    ).first()
    
    if existing_pending:
        flash('您已有一个待审核的地址验证申请，请等待审核完成', 'warning')
        return redirect(url_for('verification.my_verifications'))
    
    if request.method == 'POST':
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        property_address = request.form.get('property_address')
        property_owner_name = request.form.get('property_owner_name')
        id_card_number = request.form.get('id_card_number')
        id_card_name = request.form.get('id_card_name')
        id_card_address = request.form.get('id_card_address')
        additional_documents = request.form.get('additional_documents')
        
        if not document_type:
            flash('请选择证明文件类型', 'error')
            return redirect(url_for('verification.create'))
        
        verification_record = AddressVerification(
            user_id=current_user.id,
            document_type=document_type,
            document_number=document_number,
            property_address=property_address,
            property_owner_name=property_owner_name,
            id_card_number=id_card_number,
            id_card_name=id_card_name,
            id_card_address=id_card_address,
            additional_documents=additional_documents
        )
        
        document_image = request.files.get('document_image')
        if document_image:
            doc_url = save_file(document_image, 'documents')
            if doc_url:
                verification_record.document_image_url = doc_url
        
        id_card_front = request.files.get('id_card_front')
        if id_card_front:
            front_url = save_file(id_card_front, 'id_cards')
            if front_url:
                verification_record.id_card_front_url = front_url
        
        id_card_back = request.files.get('id_card_back')
        if id_card_back:
            back_url = save_file(id_card_back, 'id_cards')
            if back_url:
                verification_record.id_card_back_url = back_url
        
        db.session.add(verification_record)
        db.session.commit()
        
        flash('地址验证申请已提交，请等待管理员审核', 'success')
        return redirect(url_for('verification.my_verifications'))
    
    return render_template('verification/create.html')


@verification.route('/address-verification/my')
@login_required
def my_verifications():
    verifications = AddressVerification.query.filter_by(
        user_id=current_user.id
    ).order_by(AddressVerification.created_at.desc()).all()
    
    return render_template('verification/list_user.html', verifications=verifications)


@verification.route('/address-verification/<int:id>')
@login_required
def detail(id):
    verification_record = AddressVerification.query.get_or_404(id)
    
    if verification_record.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限查看此验证记录', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('verification/detail.html', verification=verification_record)


@verification.route('/admin/verifications')
@login_required
@admin_required
def admin_list():
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = AddressVerification.query
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(
        AddressVerification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'verification/admin_list.html',
        verifications=pagination.items,
        pagination=pagination,
        current_status=status
    )


@verification.route('/admin/verifications/<int:id>/review', methods=['POST'])
@login_required
@admin_required
def admin_review(id):
    verification_record = AddressVerification.query.get_or_404(id)
    
    if verification_record.status != AddressVerification.STATUS_PENDING:
        flash('该验证申请已被审核', 'error')
        return redirect(url_for('verification.admin_list'))
    
    action = request.form.get('action')
    admin_note = request.form.get('admin_note', '')
    
    if action == 'approve':
        verification_record.status = AddressVerification.STATUS_APPROVED
        flash('验证申请已通过', 'success')
        
        user = User.query.get(verification_record.user_id)
        if user:
            user.is_verified = True
            user.verification_status = 'verified'
    elif action == 'reject':
        if not admin_note:
            flash('拒绝审核时需要填写原因', 'error')
            return redirect(url_for('verification.detail', id=id))
        verification_record.status = AddressVerification.STATUS_REJECTED
        verification_record.admin_note = admin_note
        flash('验证申请已拒绝', 'success')
    else:
        flash('无效的操作', 'error')
        return redirect(url_for('verification.detail', id=id))
    
    verification_record.reviewed_by = current_user.id
    verification_record.reviewed_at = datetime.utcnow()
    
    db.session.commit()
    
    return redirect(url_for('verification.admin_list'))


@verification.route('/admin/verifications/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    verification_record = AddressVerification.query.get_or_404(id)
    
    if verification_record.user_id != current_user.id:
        flash('您没有权限取消此验证申请', 'error')
        return redirect(url_for('main.index'))
    
    if verification_record.status != AddressVerification.STATUS_PENDING:
        flash('该验证申请不能取消', 'error')
        return redirect(url_for('verification.my_verifications'))
    
    db.session.delete(verification_record)
    db.session.commit()
    
    flash('验证申请已取消', 'success')
    return redirect(url_for('verification.my_verifications'))
