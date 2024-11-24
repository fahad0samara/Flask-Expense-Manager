from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Settlement, Group, User, ExpenseSplit
from sqlalchemy import and_, or_
from datetime import datetime

bp = Blueprint('settlement', __name__)

@bp.route('/group/<int:group_id>', methods=['GET'])
@login_required
def group_settlements(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(member.id == current_user.id for member in group.members):
        flash('You do not have permission to view settlements for this group.', 'error')
        return redirect(url_for('group.list_groups'))
    
    # Get all settlements for the group
    settlements = Settlement.query.filter_by(group_id=group_id).order_by(Settlement.date.desc()).all()
    
    # Calculate current balances
    balances = {}
    for member in group.members:
        # Amount user owes to others
        owed = db.session.query(db.func.sum(ExpenseSplit.amount)).filter(
            ExpenseSplit.user_id == member.id,
            ExpenseSplit.expense.has(group_id=group_id)
        ).scalar() or 0
        
        # Amount others owe to user
        owed_to = db.session.query(db.func.sum(ExpenseSplit.amount)).filter(
            ExpenseSplit.expense.has(
                and_(Group.id == group_id, Group.creator_id == member.id)
            )
        ).scalar() or 0
        
        balances[member.id] = owed_to - owed
    
    return render_template('settlement/group.html', 
                         group=group, 
                         settlements=settlements,
                         balances=balances)

@bp.route('/create/<int:group_id>', methods=['POST'])
@login_required
def create_settlement(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(member.id == current_user.id for member in group.members):
        flash('You do not have permission to create settlements for this group.', 'error')
        return redirect(url_for('group.list_groups'))
    
    payer_id = request.form.get('payer_id', type=int)
    receiver_id = request.form.get('receiver_id', type=int)
    amount = request.form.get('amount', type=float)
    
    if not all([payer_id, receiver_id, amount]):
        flash('Invalid settlement data provided.', 'error')
        return redirect(url_for('settlement.group_settlements', group_id=group_id))
    
    settlement = Settlement(
        group_id=group_id,
        payer_id=payer_id,
        receiver_id=receiver_id,
        amount=amount,
        date=datetime.utcnow(),
        status='completed'
    )
    
    db.session.add(settlement)
    db.session.commit()
    
    flash('Settlement recorded successfully!', 'success')
    return redirect(url_for('settlement.group_settlements', group_id=group_id))

@bp.route('/<int:settlement_id>/cancel', methods=['POST'])
@login_required
def cancel_settlement(settlement_id):
    settlement = Settlement.query.get_or_404(settlement_id)
    
    if not any(member.id == current_user.id for member in settlement.group.members):
        flash('You do not have permission to cancel this settlement.', 'error')
        return redirect(url_for('group.list_groups'))
    
    if settlement.status == 'cancelled':
        flash('Settlement is already cancelled.', 'error')
        return redirect(url_for('settlement.group_settlements', group_id=settlement.group_id))
    
    settlement.status = 'cancelled'
    db.session.commit()
    
    flash('Settlement cancelled successfully!', 'success')
    return redirect(url_for('settlement.group_settlements', group_id=settlement.group_id))
