from flask import Flask, render_template, request, jsonify, session, send_file
import os
import uuid
import io
import pandas as pd
import numpy as np
from modules.loader import save_uploaded_file, get_session_df, set_session_df, reset_session_df
from modules.summary import generate_summary
from modules.cleaning import clean_dataframe
from modules.visualization import generate_charts
from modules.features import extract_features
import config

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.secret_key = config.SECRET_KEY

# Helper: safe JSON serialization
def safe_serialize(val):
    if isinstance(val, (pd.Timestamp, pd.Period, np.datetime64)):
        return str(val)
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    return val

# Session ID helper
def get_session_id():
    sid = session.get('sid')
    if not sid:
        sid = str(uuid.uuid4())
        session['sid'] = sid
    return sid

@app.route('/')
def landing():
    return render_template('landing_page.html')

@app.route('/dashboard')
def dashboard():
    get_session_id()
    return render_template('dashboard.html')

@app.route('/landing')
def home_landing():
    return render_template('landing_pages.html')

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload():
    try:
        sid = get_session_id()
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not f.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files allowed'}), 400

        path = save_uploaded_file(f, sid, app.config['UPLOAD_FOLDER'])
        df = pd.read_csv(path)
        set_session_df(sid, df, path)

        # Remove any previous cleaned file reference
        session.pop('last_cleaned_path', None)

        return jsonify({
            'success': True,
            'filename': os.path.basename(path),
            'rows': df.shape[0],
            'columns': df.shape[1]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Preview endpoint
@app.route('/preview')
def preview():
    try:
        sid = get_session_id()
        df = get_session_df(sid)
        if df is None:
            return jsonify({'error': 'No data loaded'}), 400
        n = int(request.args.get('n', 10))
        data = df.head(n).to_dict(orient='records')
        # safe serialize
        for row in data:
            for k, v in row.items():
                row[k] = safe_serialize(v)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Summary endpoint
@app.route('/summary')
def summary():
    try:
        sid = get_session_id()
        df = get_session_df(sid)
        if df is None:
            return jsonify({'error': 'No data loaded'}), 400
        summary_obj = generate_summary(df)
        # safe serialize all values
        for k, v in summary_obj.items():
            if isinstance(v, list):
                summary_obj[k] = [safe_serialize(x) for x in v]
            else:
                summary_obj[k] = safe_serialize(v)
        return jsonify(summary_obj)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Extract features
@app.route('/extract-features')
def features():
    try:
        sid = get_session_id()
        df = get_session_df(sid)
        if df is None:
            return jsonify({'error': 'No data loaded'}), 400
        feats = extract_features(df)
        # safe serialize
        for k, v in feats.items():
            feats[k] = safe_serialize(v)
        return jsonify(feats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Clean data
@app.route('/clean', methods=['POST'])
def clean():
    try:
        sid = get_session_id()
        df = get_session_df(sid)
        if df is None:
            return jsonify({'error': 'No data loaded'}), 400
        data = request.get_json() or {}

        cleaned_df, report = clean_dataframe(df.copy(), data)
        set_session_df(sid, cleaned_df)

        cleaned_filename = f"{sid}_cleaned.csv"
        cleaned_path = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
        cleaned_df.to_csv(cleaned_path, index=False, encoding='utf-8')

        session['last_cleaned_path'] = cleaned_path

        # safe serialize report
        for k, v in report.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    v[subk] = safe_serialize(subv)
            elif isinstance(v, list):
                report[k] = [safe_serialize(x) for x in v]

        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Download cleaned file
@app.route('/download-cleaned')
def download_cleaned():
    try:
        cleaned_path = session.get('last_cleaned_path')
        if not cleaned_path:
            return jsonify({'error': 'No cleaned file available'}), 400
        if not os.path.exists(cleaned_path):
            session.pop('last_cleaned_path', None)
            return jsonify({'error': 'Cleaned file not found on server'}), 500
        return send_file(
            cleaned_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=os.path.basename(cleaned_path)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Visualize
@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        sid = get_session_id()
        df = get_session_df(sid)
        if df is None:
            return jsonify({'error': 'No data loaded'}), 400
        opts = request.get_json() or {}
        charts = generate_charts(df, opts)
        # safe serialize chart data
        for chart in charts:
            for k, v in chart.items():
                if isinstance(v, list):
                    chart[k] = [safe_serialize(x) for x in v]
        return jsonify({'success': True, 'charts': charts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Reset
@app.route('/reset', methods=['POST'])
def reset():
    try:
        sid = get_session_id()
        reset_session_df(sid)
        cleaned_path = session.pop('last_cleaned_path', None)
        if cleaned_path and os.path.exists(cleaned_path):
            try: os.remove(cleaned_path)
            except Exception: pass
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
