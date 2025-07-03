import svgwrite
from lxml import etree
from shapely.geometry import LineString, Point
import math
from geomdl import BSpline
from geomdl import utilities
import numpy as np
import io
import os
import base64

# Color and print styles
from styles import colour_style, print_style

def calculate_edge_offset(line_start, line_end, node_size):
    """Calculate where to start an edge, factoring in the size of the node"""
    node_size = int(node_size)
    p = Point(line_end)
    c = p.buffer(node_size + 8).boundary
    l = LineString([(line_start), (line_end)])
    i = c.intersection(l)
    
    try:
        return i.coords[0]
    except:
        return p.coords[0]

def calculate_control_points(start, end):
    """Calculate control points for curved edges"""
    length = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)
    p1 = Point(start[0], start[1])
    p2 = Point(end[0], end[1])
    
    multiplier = 0.6
    
    c1 = p1.buffer(length * multiplier).boundary
    c2 = p2.buffer(length * multiplier).boundary
    i = c1.intersection(c2)
    
    if hasattr(i, 'geoms') and len(i.geoms) > 0:
        return (i.geoms[0].coords[0], i.geoms[1].coords[0])
    else:
        # Fallback for single geometry
        try:
            coords = list(i.coords)
            if len(coords) >= 2:
                return (coords[0], coords[1])
        except:
            pass
        return (start, end)

def draw_curved_path(dwg, start, end, edge_style):
    """Draw a curved path between two points"""
    start_str = f"{start[0]},{start[1]}"
    end_str = f"{end[0]},{end[1]}"
    
    # Draw stroke case if needed
    case = None
    if edge_style['stroke-case'] > 0:
        case_attrs = {
            'd': f'M{start_str}',
            'stroke': edge_style['stroke-case-color'],
            'fill': 'none',
            'stroke_width': edge_style['stroke-case']
        }
        if edge_style['stroke-dasharray'] is not None:
            case_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
        case = dwg.path(**case_attrs)
    
    # Draw main path
    path_attrs = {
        'd': f'M{start_str}',
        'stroke': edge_style['stroke'],
        'fill': 'none',
        'stroke_width': edge_style['stroke-width']
    }
    if edge_style['stroke-dasharray'] is not None:
        path_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
    path = dwg.path(**path_attrs)
    
    # Calculate control points for curve
    control_points = calculate_control_points(start, end)
    
    # Create B-spline curve
    curve = BSpline.Curve()
    curve.degree = 3
    curve.ctrlpts = [start, control_points[0], control_points[1], end]
    curve.knotvector = utilities.generate_knot_vector(curve.degree, len(curve.ctrlpts))
    curve.sample_size = 100
    curve.evaluate()
    
    # Build path data
    for i, pt in enumerate(curve.evalpts):
        if i == 0:
            continue
        path.push(f'L {pt[0]},{pt[1]}')
        if case:
            case.push(f'L {pt[0]},{pt[1]}')
    
    return case, path

class GraphMLToSVG:
    """Convert GraphML files to SVG visualizations"""
    
    def __init__(self, graphml_file):
        self.tree = etree.parse(graphml_file)
        self.root = self.tree.getroot()
        self.nodes = {}
        self.edges = {}
        self.key = {}
        self._parse_graphml()
    
    def _parse_graphml(self):
        """Parse GraphML file structure"""
        # Parse keys
        for key_item in self.root.iter('{http://graphml.graphdrawing.org/xmlns}key'):
            values = key_item.values()
            self.key[values[3] if len(values) > 3 else values[0]] = {
                'name': values[0],
                'type': values[1] if len(values) > 1 else 'string',
                'for': values[2] if len(values) > 2 else 'node'
            }
        
        # Parse nodes
        for node in self.root.iter('{http://graphml.graphdrawing.org/xmlns}node'):
            node_data = {'id': node.attrib['id']}
            for data in node:
                if 'key' in data.attrib:
                    node_data[data.attrib['key']] = data.text
            self.nodes[node.attrib['id']] = node_data
        
        # Parse edges
        edge_count = 0
        for edge in self.root.iter('{http://graphml.graphdrawing.org/xmlns}edge'):
            edge_id = edge.attrib.get('id', f'e{edge_count}')
            edge_data = {
                'source': edge.attrib['source'],
                'target': edge.attrib['target']
            }
            for data in edge:
                if 'key' in data.attrib:
                    edge_data[data.attrib['key']] = data.text
            
            # Add coordinates
            source = edge_data['source']
            target = edge_data['target']
            if source in self.nodes and target in self.nodes:
                edge_data['start'] = (
                    float(self.nodes[source].get('x', 0)),
                    float(self.nodes[source].get('y', 0))
                )
                edge_data['end'] = (
                    float(self.nodes[target].get('x', 0)),
                    float(self.nodes[target].get('y', 0))
                )
            
            self.edges[edge_id] = edge_data
            edge_count += 1
    
    def generate_svg(self, settings):
        """Generate SVG with given settings"""
        # Extract settings
        size = settings.get('size', 1000)
        scale = settings.get('scale', 1.0)
        curved = settings.get('curved', True)
        label_position = settings.get('label_position', 'below')
        node_scale = settings.get('node_scale', 1.0)
        color_scheme = settings.get('color_scheme', 'color')
        
        # Use appropriate style
        style = colour_style if color_scheme == 'color' else print_style
        
        # Create SVG
        dwg_size = int(size)
        dwg = svgwrite.Drawing(size=(dwg_size, dwg_size))
        
        # Background
        dwg.add(dwg.rect(insert=(0, 0), size=(dwg_size, dwg_size), fill=style['background']['color']))
        
        # Calculate bounds and scale
        if self.nodes:
            x_vals = [float(n.get('x', 0)) for n in self.nodes.values()]
            y_vals = [float(n.get('y', 0)) for n in self.nodes.values()]
            
            if x_vals and y_vals:
                min_x, max_x = min(x_vals), max(x_vals)
                min_y, max_y = min(y_vals), max(y_vals)
                
                # Calculate scale to fit
                graph_width = max_x - min_x
                graph_height = max_y - min_y
                
                if graph_width > 0 and graph_height > 0:
                    scale_factor = min(dwg_size * 0.8 / graph_width, dwg_size * 0.8 / graph_height) * scale
                    
                    # Transform nodes
                    for node_data in self.nodes.values():
                        x = float(node_data.get('x', 0))
                        y = float(node_data.get('y', 0))
                        
                        # Center and scale
                        x = (x - (max_x + min_x) / 2) * scale_factor + dwg_size / 2
                        y = (y - (max_y + min_y) / 2) * scale_factor + dwg_size / 2
                        
                        node_data['x'] = x
                        node_data['y'] = y
        
        # Draw edges
        edges_group = dwg.add(dwg.g())
        for edge_data in self.edges.values():
            if 'start' in edge_data and 'end' in edge_data:
                source_id = edge_data['source']
                target_id = edge_data['target']
                
                if source_id in self.nodes and target_id in self.nodes:
                    start = (self.nodes[source_id]['x'], self.nodes[source_id]['y'])
                    end = (self.nodes[target_id]['x'], self.nodes[target_id]['y'])
                    
                    # Find edge style
                    edge_style = None
                    relation = edge_data.get('relation', edge_data.get('d2', 'none'))
                    
                    for es in style['edges']:
                        if es['label'] == relation:
                            edge_style = es
                            break
                    
                    if not edge_style:
                        for es in style['edges']:
                            if es['label'] is None or es['label'] == 'none':
                                edge_style = es
                                break
                    
                    if edge_style:
                        if curved:
                            case, path = draw_curved_path(dwg, start, end, edge_style)
                            if case:
                                edges_group.add(case)
                            edges_group.add(path)
                        else:
                            # Straight line
                            line_attrs = {
                                'start': start,
                                'end': end,
                                'stroke': edge_style['stroke'],
                                'stroke_width': edge_style['stroke-width']
                            }
                            if edge_style['stroke-dasharray']:
                                line_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
                            edges_group.add(dwg.line(**line_attrs))
        
        # Draw nodes
        nodes_group = dwg.add(dwg.g())
        for node_id, node_data in self.nodes.items():
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            
            # Get node properties
            size_val = float(node_data.get('size', node_data.get('d3', 10))) * node_scale
            
            # Find node style by searching through all node data values
            node_style = None
            for ns in style['nodes']:
                for value in node_data.values():
                    if ns['label'] == value:
                        node_style = ns
                        break
                if node_style:
                    break
            
            if not node_style:
                # Default style
                node_style = {'color': '#cccccc', 'symbol': None}
            
            # Draw node background circle
            nodes_group.add(dwg.circle(
                center=(x, y),
                r=size_val,
                fill=style['background']['color'],
                stroke='none'
            ))
            
            # Draw symbol if available, otherwise draw colored circle
            if node_style.get('symbol'):
                try:
                    symbol_path = os.path.join(os.path.dirname(__file__), node_style['symbol'])
                    with open(symbol_path, 'rb') as file:
                        img = file.read()
                        encoded = base64.b64encode(img).decode()
                        svgdata = f'data:image/svg+xml;base64,{encoded}'
                        nodes_group.add(dwg.image(
                            href=svgdata,
                            insert=(x - size_val, y - size_val),
                            size=(size_val * 2, size_val * 2)
                        ))
                except:
                    # Fallback to colored circle if symbol not found
                    nodes_group.add(dwg.circle(
                        center=(x, y),
                        r=size_val,
                        fill=node_style['color'],
                        stroke='white',
                        stroke_width=2
                    ))
            else:
                # Draw colored circle
                nodes_group.add(dwg.circle(
                    center=(x, y),
                    r=size_val,
                    fill=node_style['color'],
                    stroke='white',
                    stroke_width=2
                ))
            
            # Add label
            label = node_id
            if label_position == 'below':
                label_y = y + size_val + 15
            else:
                label_y = y + 5
            
            nodes_group.add(dwg.text(
                label,
                insert=(x, label_y),
                text_anchor='middle',
                font_family=style['label']['font-family'],
                font_size=f"{style['label']['size']}em",
                fill=style['label']['fill']
            ))
        
        # Return SVG as string
        return dwg.tostring()

def graphml_to_svg(graphml_path, settings):
    """Main function to convert GraphML to SVG"""
    converter = GraphMLToSVG(graphml_path)
    return converter.generate_svg(settings)