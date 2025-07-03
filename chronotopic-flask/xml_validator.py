from lxml import etree
import io

def check_xml_is_well_formed(xml_string):
    """Check if XML is well-formed"""
    try:
        etree.parse(io.StringIO(xml_string))
        return True, "XML is well-formed"
    except etree.XMLSyntaxError as e:
        return False, str(e)

def validate_xml(xml_content):
    """
    Validate Chronotopic Cartographies XML and return list of errors/warnings
    """
    errors = []
    
    # First check if XML is well-formed
    is_valid, message = check_xml_is_well_formed(xml_content)
    if not is_valid:
        errors.append({
            'type': 'error',
            'category': 'syntax',
            'message': f'XML Syntax Error: {message}'
        })
        return errors
    
    # Parse the XML
    try:
        tree = etree.parse(io.StringIO(xml_content))
        xml_element = tree.getroot()
    except Exception as e:
        errors.append({
            'type': 'error',
            'category': 'parsing',
            'message': f'Failed to parse XML: {str(e)}'
        })
        return errors
    
    # Valid chronotope types
    chronotopes = [
        'anti-idyll', 'castle', 'distortion', 'encounter', 
        'idyll', 'metanarrative', 'parlour', 'public square', 
        'road', 'threshold', 'provincial town', 'wilderness'
    ]
    
    # Valid connection relations
    connections = [
        'direct', 'indirect', 'interrupt', 'jump', 
        'charshift', 'projection', 'metatextual', 
        'paratextual', 'intratextual', 'metaphor'
    ]
    
    # Track all node names for reference checking
    node_names = []
    
    # Check topos elements
    for topos in xml_element.iter('topos'):
        line = topos.sourceline
        
        # Check type attribute
        if 'type' not in topos.attrib:
            errors.append({
                'type': 'error',
                'category': 'topos',
                'line': line,
                'message': f'Line {line}: <topos> missing required "type" attribute'
            })
        elif topos.attrib['type'] not in chronotopes:
            errors.append({
                'type': 'warning',
                'category': 'topos',
                'line': line,
                'message': f'Line {line}: Unknown chronotope type "{topos.attrib["type"]}". Valid types: {", ".join(chronotopes)}'
            })
        
        # Check framename attribute
        if 'framename' not in topos.attrib:
            errors.append({
                'type': 'error',
                'category': 'topos',
                'line': line,
                'message': f'Line {line}: <topos> missing required "framename" attribute'
            })
        else:
            node_names.append(topos.attrib['framename'])
    
    # Check connection elements
    for connection in xml_element.iter('connection'):
        line = connection.sourceline
        
        # Check source attribute
        if 'source' not in connection.attrib:
            errors.append({
                'type': 'error',
                'category': 'connection',
                'line': line,
                'message': f'Line {line}: <connection> missing required "source" attribute'
            })
        
        # Check target attribute
        if 'target' not in connection.attrib:
            errors.append({
                'type': 'error',
                'category': 'connection',
                'line': line,
                'message': f'Line {line}: <connection> missing required "target" attribute'
            })
        
        # Check relation attribute
        if 'relation' not in connection.attrib:
            errors.append({
                'type': 'error',
                'category': 'connection',
                'line': line,
                'message': f'Line {line}: <connection> missing required "relation" attribute'
            })
        elif connection.attrib['relation'] not in connections:
            errors.append({
                'type': 'warning',
                'category': 'connection',
                'line': line,
                'message': f'Line {line}: Unknown relation type "{connection.attrib["relation"]}". Valid types: {", ".join(connections)}'
            })
    
    # Check that connection sources and targets exist
    for connection in xml_element.iter('connection'):
        line = connection.sourceline
        
        if 'source' in connection.attrib and connection.attrib['source'] not in node_names:
            errors.append({
                'type': 'error',
                'category': 'reference',
                'line': line,
                'message': f'Line {line}: Connection source "{connection.attrib["source"]}" does not match any topos framename'
            })
        
        if 'target' in connection.attrib and connection.attrib['target'] not in node_names:
            errors.append({
                'type': 'error',
                'category': 'reference',
                'line': line,
                'message': f'Line {line}: Connection target "{connection.attrib["target"]}" does not match any topos framename'
            })
    
    # Check toporef elements
    for toporef in xml_element.iter('toporef'):
        line = toporef.sourceline
        
        # Check role attribute
        if 'role' not in toporef.attrib:
            errors.append({
                'type': 'error',
                'category': 'toporef',
                'line': line,
                'message': f'Line {line}: <toporef> missing required "role" attribute'
            })
        
        # Check relation attribute (optional for toporef unless in sequence)
        if 'sequence' not in toporef.attrib and 'relation' not in toporef.attrib:
            errors.append({
                'type': 'error',
                'category': 'toporef',
                'line': line,
                'message': f'Line {line}: <toporef> missing required "relation" attribute'
            })
        elif 'relation' in toporef.attrib and toporef.attrib['relation'] not in connections:
            errors.append({
                'type': 'warning',
                'category': 'toporef',
                'line': line,
                'message': f'Line {line}: Unknown relation type "{toporef.attrib["relation"]}". Valid types: {", ".join(connections)}'
            })
    
    # Sort errors by line number
    errors.sort(key=lambda x: x.get('line', 0))
    
    return errors