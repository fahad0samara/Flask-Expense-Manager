from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.settlement import Settlement
from app.models.user import User
from app.models.group import Group
from datetime import datetime

settlements = Blueprint('settlements', __name__)

@settlements.route('/settlements')
@login_required
def list_settlements():
    # Get settlements where user is either payer or receiver
    settlements = Settlement.query.filter(
        (Settlement.payer_id == current_user.id) |
        (Settlement.receiver_id == current_user.id)
    ).order_by(Settlement.date.desc()).all()
    
    return render_template('settlements/list_settlements.html', settlements=settlements)

@settlements.route('/settlements/new', methods=['GET', 'POST'])
@login_required
def create_settlement():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        amount = float(request.form.get('amount'))
        group_id = request.form.get('group_id') or None
        notes = request.form.get('notes')
        
        settlement = Settlement(
            payer_id=current_user.id,
            receiver_id=receiver_id,
            amount=amount,
            group_id=group_id,
            notes=notes
        )
        
        db.session.add(settlement)
        db.session.commit()
        
        flash('Settlement created successfully!', 'success')
        return redirect(url_for('settlements.list_settlements'))
    
    # Get users who owe money to current user or are owed by current user
    users = User.query.join(ExpenseSplit).join(Expense).filter(
        (Expense.payer_id == current_user.id) |
        (ExpenseSplit.user_id == current_user.id)
    ).distinct().all()
    
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    
    return render_template('settlements/create_settlement.html',
                         users=users,
                         groups=groups)

@settlements.route('/settlements/<int:settlement_id>/status', methods=['POST'])
@login_required
def update_settlement_status(settlement_id):
    settlement = Settlement.query.get_or_404(settlement_id)
    
    # Ensure user is involved in the settlement
    if current_user.id not in [settlement.payer_id, settlement.receiver_id]:
        flash('You are not authorized to update this settlement.', 'error')
        return redirect(url_for('settlements.list_settlements'))
    
    new_status = request.form.get('status')
    if new_status in ['completed', 'cancelled']:
        settlement.status = new_status
        db.session.commit()
        flash('Settlement status updated successfully!', 'success')
    
    return redirect(url_for('settlements.list_settlements'))
