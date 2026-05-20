import qrcode
from PIL import Image

def generate_qr(data, fill_color="black", back_color="white"):
    """
    Generates a QR code from the given data.
    Returns a PIL Image object.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')
    return img
