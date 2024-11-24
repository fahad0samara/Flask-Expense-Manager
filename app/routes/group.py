from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Group, GroupMembership, User
from datetime import datetime

bp = Blueprint('group', __name__)

@bp.route('/', methods=['GET'])
@login_required
def list_groups():
    groups = Group.query.filter(Group.members.any(id=current_user.id)).all()
    return render_template('group/list.html', groups=groups)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        group = Group(
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        # Add creator as a member
        membership = GroupMembership(user_id=current_user.id, is_admin=True)
        group.memberships.append(membership)
        
        db.session.add(group)
        db.session.commit()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    return render_template('group/create.html')

@bp.route('/<int:group_id>', methods=['GET'])
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(member.id == current_user.id for member in group.members):
        flash('You do not have permission to view this group.', 'error')
        return redirect(url_for('group.list_groups'))
    return render_template('group/detail.html', group=group)

@bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.memberships):
        flash('You do not have permission to edit this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description', '')
        
        db.session.commit()
        flash('Group updated successfully!', 'success')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    return render_template('group/edit.html', group=group)

@bp.route('/<int:group_id>/members/add', methods=['POST'])
@login_required
def add_member(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.memberships):
        flash('You do not have permission to add members to this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    if any(member.id == user.id for member in group.members):
        flash('User is already a member of this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    membership = GroupMembership(user_id=user.id)
    group.memberships.append(membership)
    db.session.commit()
    
    flash('Member added successfully!', 'success')
    return redirect(url_for('group.view_group', group_id=group.id))

@bp.route('/<int:group_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(group_id, user_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.memberships):
        flash('You do not have permission to remove members from this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    membership = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first_or_404()
    
    if membership.is_admin and len([m for m in group.memberships if m.is_admin]) == 1:
        flash('Cannot remove the last admin from the group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    db.session.delete(membership)
    db.session.commit()
    
    flash('Member removed successfully!', 'success')
    return redirect(url_for('group.view_group', group_id=group.id))
