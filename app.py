from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
import base64
from werkzeug.utils import secure_filename
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'uploads'
NOTES_FOLDER = 'notes'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt', 'pdf', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['NOTES_FOLDER'] = NOTES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs('static/plots', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_data_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_data_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash(f'File {filename} uploaded successfully!')
        return redirect(url_for('view_data', filename=filename))
    else:
        flash('Invalid file type. Please upload CSV or Excel files.')
        return redirect(request.url)

@app.route('/data/<filename>')
def view_data(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Read the file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            flash('Unsupported file format')
            return redirect(url_for('upload_page'))
        
        # Get basic info about the dataset
        info = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict()
        }
        
        # Convert DataFrame to HTML
        table_html = df.head(100).to_html(classes='table table-striped', table_id='data-table')
        
        return render_template('view_data.html', 
                             filename=filename, 
                             table_html=table_html, 
                             info=info)
    
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
        return redirect(url_for('upload_page'))

@app.route('/statistics/<filename>')
def statistics(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        
        # Generate statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats = {}
        
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe().to_dict()
        
        # Additional statistics
        additional_stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum(),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns)
        }
        
        return render_template('statistics.html', 
                             filename=filename, 
                             stats=stats, 
                             additional_stats=additional_stats,
                             numeric_cols=numeric_cols.tolist())
    
    except Exception as e:
        flash(f'Error generating statistics: {str(e)}')
        return redirect(url_for('upload_page'))

@app.route('/visualize/<filename>')
def visualize(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        return render_template('visualize.html', 
                             filename=filename,
                             numeric_cols=numeric_cols,
                             categorical_cols=categorical_cols)
    
    except Exception as e:
        flash(f'Error loading visualization page: {str(e)}')
        return redirect(url_for('upload_page'))

@app.route('/generate_plot/<filename>')
def generate_plot(filename):
    try:
        plot_type = request.args.get('type')
        column = request.args.get('column')
        column2 = request.args.get('column2', None)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        
        plt.figure(figsize=(10, 6))
        plt.style.use('default')
        
        if plot_type == 'histogram' and column:
            plt.hist(df[column].dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title(f'Histogram of {column}')
            plt.xlabel(column)
            plt.ylabel('Frequency')
            
        elif plot_type == 'bar' and column:
            value_counts = df[column].value_counts().head(10)
            plt.bar(range(len(value_counts)), value_counts.values, color='lightcoral')
            plt.title(f'Bar Chart of {column}')
            plt.xlabel(column)
            plt.ylabel('Count')
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
            
        elif plot_type == 'pie' and column:
            value_counts = df[column].value_counts().head(8)
            plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            plt.title(f'Pie Chart of {column}')
            
        elif plot_type == 'line' and column:
            if pd.api.types.is_numeric_dtype(df[column]):
                plt.plot(df.index, df[column], marker='o', linewidth=2, markersize=4)
                plt.title(f'Line Plot of {column}')
                plt.xlabel('Index')
                plt.ylabel(column)
            else:
                return jsonify({'error': 'Line plot requires numeric data'})
                
        elif plot_type == 'scatter' and column and column2:
            plt.scatter(df[column], df[column2], alpha=0.6, color='green')
            plt.title(f'Scatter Plot: {column} vs {column2}')
            plt.xlabel(column)
            plt.ylabel(column2)
            
        elif plot_type == 'boxplot' and column:
            plt.boxplot(df[column].dropna())
            plt.title(f'Box Plot of {column}')
            plt.ylabel(column)
        
        plt.tight_layout()
        
        # Save plot to base64 string
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({'plot': img_base64})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/notes')
def notes():
    notes_files = []
    if os.path.exists(app.config['NOTES_FOLDER']):
        for filename in os.listdir(app.config['NOTES_FOLDER']):
            filepath = os.path.join(app.config['NOTES_FOLDER'], filename)
            if os.path.isfile(filepath):
                notes_files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('notes.html', notes_files=notes_files)

@app.route('/upload_note', methods=['POST'])
def upload_note():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('notes'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('notes'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['NOTES_FOLDER'], filename)
        file.save(filepath)
        flash(f'Note {filename} uploaded successfully!')
    else:
        flash('Invalid file type.')
    
    return redirect(url_for('notes'))

@app.route('/download_note/<filename>')
def download_note(filename):
    try:
        return send_file(os.path.join(app.config['NOTES_FOLDER'], filename), as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('notes'))

@app.route('/datasets')
def datasets():
    dataset_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_data_file(filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                dataset_files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('datasets.html', dataset_files=dataset_files)

if __name__ == '__main__':
    app.run(debug=True)
