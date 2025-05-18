import cv2
from ultralytics import YOLO
import math
import cvzone
from functools import wraps
from flask import session, redirect,render_template

# Load the YOLO model
model = YOLO("model.pt")
# Define the classes of trash
trash_classes = {'garbage', 'garbage_bag', 'sampah-detection', 'trash'}
                 
def login_required(f):
    """
    Decorator to check if the user is logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    
    return decorated_function


def detect_trash(img):
    results = model(img)
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            if label in trash_classes:
                return True, results  # Trash detected
    return False, results  # No trash detected


def estimate_trash_level(img, results):
    img_area = img.shape[0] * img.shape[1]
    trash_area = 0

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            area = (x2 - x1) * (y2 - y1)
            trash_area += area

            conf = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), t=2)
            cvzone.putTextRect(
                img, f'Conf: {conf}', (x1, y1 - 10), scale=0.8, thickness=1, colorR=(255, 0, 0)
            )

    ratio = trash_area / img_area
    if ratio < 0.01:
        return "None", img
    elif ratio < 0.05:
        return "Low", img
    elif ratio < 0.15:
        return "Medium", img
    else:
        return "High", img


def main(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (700, 500))
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    has_trash, results = detect_trash(img)
    if not has_trash:
        print("No trash detected.")
        cvzone.putTextRect(img, 'No Trash Detected', (20, 40), scale=1.2, thickness=2, colorR=(0, 0, 255))
    else:
        level, img = estimate_trash_level(img, results)
        cvzone.putTextRect(img, f'Trash Level: {level}', (20, 40), scale=1.2, thickness=2, colorR=(0, 255, 0))
        print(f"Trash Level: {level}")

    cv2.imshow("Output", img)
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
