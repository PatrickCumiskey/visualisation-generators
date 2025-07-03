from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import tempfile
from xml_validator import validate_xml
from svg_generator import graphml_to_svg

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate-xml', methods=['GET', 'POST'])
def validate_xml_page():
    if request.method == 'POST':
        xml_content = request.form.get('xml_content', '')
        if xml_content:
            errors = validate_xml(xml_content)
            return jsonify({'errors': errors})
    return render_template('validate_xml.html')

@app.route('/visualize', methods=['GET', 'POST'])
def visualize_page():
    if request.method == 'POST':
        if 'graphml_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['graphml_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.graphml'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Get settings from form
            settings = {
                'size': float(request.form.get('size', 1000)),
                'scale': float(request.form.get('scale', 1.0)),
                'curved': request.form.get('curved', 'true') == 'true',
                'label_position': request.form.get('label_position', 'below'),
                'node_scale': float(request.form.get('node_scale', 1.0)),
                'color_scheme': request.form.get('color_scheme', 'color')
            }
            
            try:
                svg_content = graphml_to_svg(filepath, settings)
                os.remove(filepath)  # Clean up uploaded file
                return jsonify({'svg': svg_content})
            except Exception as e:
                os.remove(filepath)  # Clean up uploaded file
                return jsonify({'error': str(e)}), 500
                
    return render_template('visualize.html')

if __name__ == '__main__':
    app.run(debug=True)