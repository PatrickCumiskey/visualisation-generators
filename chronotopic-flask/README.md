# Chronotopic Cartographies Flask App

A streamlined Flask web application for validating Chronotopic Cartographies XML and visualizing GraphML files.

## Features

1. **XML Validator**: Paste XML content and get detailed validation errors and warnings
2. **GraphML Visualizer**: Upload GraphML files from Gephi and generate customizable SVG visualizations

## Installation

```bash
# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## Usage

### XML Validation
1. Navigate to "Validate XML"
2. Paste your XML content into the text area
3. Click "Validate XML"
4. View detailed errors and warnings with line numbers

### GraphML Visualization
1. Navigate to "Visualize GraphML"
2. Upload a GraphML file (drag & drop or click to browse)
3. Adjust visualization settings:
   - Canvas Size: 500-3000px
   - Scale: 0.1-3.0
   - Node Scale: 0.1-3.0
   - Edge Style: Curved or Straight
   - Label Position: Below or Center
   - Color Scheme: Color or Grayscale
4. Click "Generate Visualization"
5. Download the resulting SVG

## Settings

The visualization settings allow real-time customization:
- **Canvas Size**: Overall size of the SVG output
- **Scale**: Zoom level of the graph
- **Node Scale**: Size of individual nodes
- **Edge Style**: Curved (B-spline) or straight connections
- **Label Position**: Text placement relative to nodes
- **Color Scheme**: Full color or grayscale for printing