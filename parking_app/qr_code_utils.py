import qrcode
import io
import base64
from io import BytesIO
from django.core.files.base import ContentFile


def generate_qr_code(data, size=10, border=2):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None


def generate_qr_code_base64(data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None


def generate_qr_code_svg(data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        module_count = qr.modules_count
        scale = 8
        border = 4
        size = (module_count + 2 * border) * scale
        
        svg_parts = [
            f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{size}" height="{size}" fill="white"/>',
        ]
        
        for r in range(module_count):
            for c in range(module_count):
                if qr.modules[r][c]:
                    x = (c + border) * scale
                    y = (r + border) * scale
                    svg_parts.append(f'<rect x="{x}" y="{y}" width="{scale}" height="{scale}" fill="black"/>')
        
        svg_parts.append('</svg>')
        return ''.join(svg_parts)
    except Exception as e:
        print(f"Error generating QR code SVG: {e}")
        return None


def generate_check_in_qr_code(reservation):
    data = f"checkin:{reservation.id}:{reservation.slot_number}"
    return generate_qr_code_base64(data)


def generate_check_out_qr_code(reservation):
    data = f"checkout:{reservation.id}:{reservation.slot_number}"
    return generate_qr_code_base64(data)


def parse_qr_code(qr_string):
    try:
        if qr_string.startswith('checkin:'):
            parts = qr_string.split(':')
            return {
                'action': 'checkin',
                'reservation_id': int(parts[1]),
                'slot_number': int(parts[2])
            }
        elif qr_string.startswith('checkout:'):
            parts = qr_string.split(':')
            return {
                'action': 'checkout',
                'reservation_id': int(parts[1]),
                'slot_number': int(parts[2])
            }
        else:
            return None
    except Exception as e:
        print(f"Error parsing QR code: {e}")
        return None


def generate_booking_check_in_qr(booking):
    data = f"booking_checkin:{booking.id}:{booking.slot.slot_number}:{booking.user.id}"
    qr_code = generate_qr_code_base64(data)
    return qr_code


def generate_booking_check_out_qr(booking):
    data = f"booking_checkout:{booking.id}:{booking.slot.slot_number}:{booking.user.id}"
    qr_code = generate_qr_code_base64(data)
    return qr_code


def parse_booking_qr_code(qr_string):
    try:
        if qr_string.startswith('booking_checkin:'):
            parts = qr_string.split(':')
            return {
                'action': 'booking_checkin',
                'booking_id': int(parts[1]),
                'slot_number': int(parts[2]),
                'user_id': int(parts[3])
            }
        elif qr_string.startswith('booking_checkout:'):
            parts = qr_string.split(':')
            return {
                'action': 'booking_checkout',
                'booking_id': int(parts[1]),
                'slot_number': int(parts[2]),
                'user_id': int(parts[3])
            }
        else:
            return None
    except Exception as e:
        print(f"Error parsing booking QR code: {e}")
        return None
