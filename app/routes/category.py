from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, ExpenseCategory

bp = Blueprint('category', __name__)

@bp.route('/', methods=['GET'])
@login_required
def list_categories():
    categories = ExpenseCategory.query.all()
    return render_template('category/list.html', categories=categories)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        color = request.form.get('color', '#000000')
        description = request.form.get('description')

        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('category.add_category'))

        category = ExpenseCategory(
            name=name,
            icon=icon,
            color=color,
            description=description
        )

        try:
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('category.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding category. Please try again.', 'error')
            return redirect(url_for('category.add_category'))

    return render_template('category/add.html')

@bp.route('/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = ExpenseCategory.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        color = request.form.get('color')
        description = request.form.get('description')

        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('category.edit_category', category_id=category_id))

        try:
            category.name = name
            category.icon = icon
            category.color = color
            category.description = description
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('category.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating category. Please try again.', 'error')
            return redirect(url_for('category.edit_category', category_id=category_id))

    return render_template('category/edit.html', category=category)

@bp.route('/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = ExpenseCategory.query.get_or_404(category_id)
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category. Please try again.', 'error')
    
    return redirect(url_for('category.list_categories'))
