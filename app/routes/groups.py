from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.group import Group, GroupMembership
from app.models.user import User

bp = Blueprint('groups', __name__)

@bp.route('/group/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Create new group
        group = Group(name=name, description=description)
        db.session.add(group)
        
        # Add current user as group admin/first member
        membership = GroupMembership(user=current_user, group=group)
        db.session.add(membership)
        
        db.session.commit()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('groups/create_group.html')

@bp.route('/group/<int:group_id>')
@login_required
def group_details(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Ensure user is a member of the group
    if not any(membership.user_id == current_user.id for membership in group.members):
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get group expenses
    expenses = group.expenses
    
    # Get group members
    members = [membership.user for membership in group.members]
    
    return render_template('groups/group_details.html', 
                           group=group, 
                           expenses=expenses, 
                           members=members)

@bp.route('/group/<int:group_id>/add_member', methods=['GET', 'POST'])
@login_required
def add_group_member(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Ensure current user is a member of the group
    if not any(membership.user_id == current_user.id for membership in group.members):
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Find user to add
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('groups.add_group_member', group_id=group_id))
        
        # Check if user is already a member
        if any(membership.user_id == user.id for membership in group.members):
            flash('User is already a member of this group.', 'error')
            return redirect(url_for('groups.group_details', group_id=group_id))
        
        # Add user to group
        membership = GroupMembership(user=user, group=group)
        db.session.add(membership)
        db.session.commit()
        
        flash(f'{username} added to the group successfully!', 'success')
        return redirect(url_for('groups.group_details', group_id=group_id))
    
    return render_template('groups/add_member.html', group=group)
