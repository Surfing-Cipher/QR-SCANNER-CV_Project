# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from pyzbar.pyzbar import decode, ZBarSymbol

def enhance_image(image):
    """
    Apply low-light enhancement to an image to improve scanning accuracy.
    Uses CLAHE (Contrast Limited Adaptive Histogram Equalization).
    """
    # Convert to grayscale if it's not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Create a CLAHE object
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Also add a slight blur to reduce noise
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
    return enhanced

def scan_image(image, enhance=False):
    """
    Scan an OpenCV image (numpy array) for barcodes and QR codes.
    Returns a list of dictionaries containing decoded info and bounding boxes.
    """
    # Create a copy for drawing if needed
    processed_img = image.copy()
    
    if enhance:
        processed_img = enhance_image(processed_img)

    # Decode the image
    decoded_objects = decode(processed_img)
    
    results = []
    for obj in decoded_objects:
        # Extract data and type
        data = obj.data.decode('utf-8')
        barcode_type = obj.type
        
        # Get bounding box coordinates
        rect = obj.rect
        polygon = obj.polygon
        
        results.append({
            'data': data,
            'type': barcode_type,
            'rect': rect,
            'polygon': polygon
        })
        
    return results

def draw_scan_results(image, scan_results):
    """
    Draw bounding boxes and text on the image for visualizations.
    Modifies the image in place.
    """
    for res in scan_results:
        # Draw bounding box
        rect = res['rect']
        x, y, w, h = rect.left, rect.top, rect.width, rect.height
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw text
        text = f"{res['type']}: {res['data']}"
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    return image

def parse_scanned_data(data):
    """
    Parses scanned text to determine its type and extract actionable details.
    Returns a dict with 'type' and 'action_data' (and other specific keys if applicable).
    Types: 'URL', 'WIFI', 'VCARD', 'EMAIL', 'PHONE', 'TEXT'
    """
    data_str = str(data).strip()
    
    if data_str.lower().startswith("http://") or data_str.lower().startswith("https://"):
        return {'type': 'URL', 'action_data': data_str}
        
    if data_str.upper().startswith("WIFI:"):
        # Format: WIFI:T:WPA;S:MyNet;P:Mypass;;
        ssid = ""
        password = ""
        parts = data_str.upper()[5:].split(";")
        for part in parts:
            if part.startswith("S:"):
                # Real SSID is case sensitive, we should extract from original data
                original_parts = data_str[5:].split(";")
                for o_part in original_parts:
                    if o_part.upper().startswith("S:"):
                        ssid = o_part[2:]
                        break
            elif part.startswith("P:"):
                original_parts = data_str[5:].split(";")
                for o_part in original_parts:
                    if o_part.upper().startswith("P:"):
                        password = o_part[2:]
                        break
        return {'type': 'WIFI', 'ssid': ssid, 'password': password, 'action_data': data_str}
        
    if data_str.upper().startswith("BEGIN:VCARD"):
        return {'type': 'VCARD', 'action_data': data_str}
        
    if data_str.lower().startswith("mailto:"):
        return {'type': 'EMAIL', 'action_data': data_str[7:]}
        
    if data_str.lower().startswith("tel:"):
        return {'type': 'PHONE', 'action_data': data_str[4:]}
        
    return {'type': 'TEXT', 'action_data': data_str}
