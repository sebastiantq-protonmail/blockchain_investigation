import json
import qrcode
import os

def split_data(data, chunk_size):
    """Divide los datos en segmentos de un tamaño dado."""
    return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

def generate_and_save_qrs(data, max_characters=2500):
    """Genera y guarda múltiples QRs si es necesario."""
    for person, keys in data.items():
        for key_type, key in keys.items():
            segments = split_data(key, max_characters)
            for index, segment in enumerate(segments):
                qr = qrcode.QRCode(
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(segment)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                directory = f"qrs/{person}"
                filename = f"{key_type}_{person}_{index}.png"
                os.makedirs(directory, exist_ok=True)
                img.save(os.path.join(directory, filename))
                print(f"Saved QR code to {os.path.join(directory, filename)}")

# Carga de datos y llamada a la función
with open('keypairs.json') as f:
    data = json.load(f)
generate_and_save_qrs(data)
