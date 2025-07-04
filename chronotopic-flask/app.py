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
                'color_scheme': request.form.get('color_scheme', 'color'),
                'edge_width': float(request.form.get('edge_width', 1.0)),
                'show_arrows': request.form.get('show_arrows', 'false') == 'true',
                'node_opacity': float(request.form.get('node_opacity', 1.0)),
                'edge_opacity': float(request.form.get('edge_opacity', 1.0)),
                'label_size': float(request.form.get('label_size', 0.6)),
                'background_color': request.form.get('background_color', '#525252'),
                'node_stroke_width': int(request.form.get('node_stroke_width', 2)),
                'node_stroke_color': request.form.get('node_stroke_color', '#ffffff'),
                'label_color': request.form.get('label_color', '#dbdbdb'),
                'show_shadows': request.form.get('show_shadows', 'false') == 'true',
                'show_grid': request.form.get('show_grid', 'false') == 'true',
                'grid_size': int(request.form.get('grid_size', 50)),
                'export_scale': float(request.form.get('export_scale', 1.0)),
                'curve_strength': float(request.form.get('curve_strength', 0.6)),
                'node_shape': request.form.get('node_shape', 'circle'),
                'symbol_color': request.form.get('symbol_color', '#000000')
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