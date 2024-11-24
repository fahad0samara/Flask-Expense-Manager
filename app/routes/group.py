from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Group, GroupMembership, User
from datetime import datetime

group = Blueprint('group', __name__)

@group.route('/', methods=['GET'])
@login_required
def list_groups():
    groups = Group.query.filter(Group.members.any(id=current_user.id)).all()
    return render_template('groups/list.html', groups=groups)

@group.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        group = Group(
            name=name,
            description=description,
            creator_id=current_user.id
        )
        
        # Add creator as a member and admin
        membership = GroupMembership(user=current_user, group=group, is_admin=True)
        group.members.append(membership)
        
        db.session.add(group)
        db.session.commit()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    return render_template('groups/create.html')

@group.route('/<int:group_id>', methods=['GET'])
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(member.user_id == current_user.id for member in group.members):
        flash('You do not have permission to view this group.', 'error')
        return redirect(url_for('group.list_groups'))
    return render_template('groups/detail.html', group=group)

@group.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.members):
        flash('You do not have permission to edit this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description', '')
        
        db.session.commit()
        flash('Group updated successfully!', 'success')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    return render_template('groups/edit.html', group=group)

@group.route('/<int:group_id>/members/add', methods=['POST'])
@login_required
def add_member(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.members):
        flash('You do not have permission to add members to this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    if any(member.user_id == user.id for member in group.members):
        flash('User is already a member of this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    membership = GroupMembership(user_id=user.id)
    group.members.append(membership)
    db.session.commit()
    
    flash('Member added successfully!', 'success')
    return redirect(url_for('group.view_group', group_id=group.id))

@group.route('/<int:group_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(group_id, user_id):
    group = Group.query.get_or_404(group_id)
    if not any(membership.user_id == current_user.id and membership.is_admin for membership in group.members):
        flash('You do not have permission to remove members from this group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    membership = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first_or_404()
    
    if membership.is_admin and len([m for m in group.members if m.is_admin]) == 1:
        flash('Cannot remove the last admin from the group.', 'error')
        return redirect(url_for('group.view_group', group_id=group.id))
    
    db.session.delete(membership)
    db.session.commit()
    
    flash('Member removed successfully!', 'success')
    return redirect(url_for('group.view_group', group_id=group.id))

@group.route('/api/group/<int:group_id>/members')
@login_required
def get_group_members(group_id):
    group = Group.query.get_or_404(group_id)
    if not any(member.user_id == current_user.id for member in group.members):
        return jsonify({'error': 'Access denied'}), 403
    
    members = []
    for membership in group.members:
        user = membership.user
        members.append({
            'id': user.id,
            'name': user.full_name or user.username,
            'email': user.email
        })
    
    return jsonify(members)
