from flask import Flask, request, jsonify, send_file, render_template, abort
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import string
import uuid
import time
import io
import base64
from gtts import gTTS
import math
import sqlite3
import os
import json
from collections import Counter

app = Flask(__name__)
CORS(app)

CAPTCHA_EXPIRE = 300
MAX_ATTEMPTS = 5
DB_FILE = "sessions.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captchas (
            id TEXT PRIMARY KEY,
            type TEXT,
            text TEXT,
            correct_answer TEXT,
            expires REAL,
            attempts INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            timestamp REAL,
            valid INTEGER,
            score REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

SENTENCES = [
    "The sun is very bright today.", "She loves to read mystery novels.", "Dogs often bark at strangers.",
    "He runs faster than his friends.", "The cat sleeps on the couch.", "I like eating fresh red apples.",
    "It rains heavily in the summer.", "They sing beautifully in the choir.", "We play board games every weekend.",
    "Birds fly south for the winter.", "The sky looks clear and blue.", "She draws pictures of animals.",
    "Fish swim swiftly in the ocean.", "He eats his food very slowly.", "The book on the table is thick.",
    "I drink cold water every morning.", "It snows a lot in December.", "They laugh at funny jokes.",
    "We walk in the park daily.", "The moon glows in the night.", "She writes neatly in her notebook.",
    "Tall trees grow in the forest.", "He jumps high during basketball games.", "The red car drives very fast.",
    "I watch TV after finishing work.", "It gets dark early in winter.", "They dance happily at the party.",
    "We cook dinner together every evening.", "The baby cries when he's hungry.", "She smiles often at her friends.",
    "Stars twinkle brightly in the sky.", "He drives carefully on icy roads.", "The yellow flower blooms in spring.",
    "I wear comfortable shoes for walking.", "It feels cold outside today.", "They study hard for their exams.",
    "We buy groceries on Saturdays.", "The old door creaks when opened.", "She listens quietly to the teacher.",
    "Wind blows softly through the trees.", "He climbs trees with his brother.", "The phone rings loudly in the kitchen.",
    "I brush my teeth twice daily.", "It smells nice in the bakery.", "They travel often to new places.",
    "We clean the house every Sunday.", "The clock ticks loudly at night.", "She paints beautiful landscapes with watercolors.",
    "Leaves fall down in the autumn.", "He fixes broken things around the house.", "The chocolate cake is very sweet.",
    "I ride my bike to school.", "It tastes good with extra salt.", "They build tall towers with blocks.",
    "We plant flowers in the garden.", "The river flows gently downstream.", "She bakes cookies for her family.",
    "Fire burns wood in the fireplace.", "He catches the ball with ease.", "The bright light shines at night.",
    "I wash my hands before eating.", "It sounds loud in the city.", "They win prizes for their hard work.",
    "We share food with our neighbors.", "The train moves quickly on the tracks.", "She folds clothes after doing laundry.",
    "Ice melts quickly in the sun.", "He carries heavy bags upstairs.", "The dog wags its tail happily.",
    "I open the window for fresh air.", "It looks big from far away.", "They dig deep holes in the sand.",
    "We wait patiently for the bus.", "The baby giggles at funny faces.", "She combs her hair every morning.",
    "Rain falls gently on the roof.", "He kicks the ball very far.", "The cup is full of coffee.",
    "I close the door behind me.", "It seems easy at first glance.", "They push shopping carts in the store.",
    "We wave goodbye to our friends.", "The bee buzzes around the flowers.", "She ties her shoes before running.",
    "Snow covers the ground completely.", "He pulls the rope with strength.", "The hat fits well on his head.",
    "I cut the paper into shapes.", "It appears shiny under the light.", "They lift weights at the gym.",
    "We meet friends at the café.", "The owl hoots in the night.", "She sweeps the floor every afternoon.",
    "White clouds float by slowly.", "He slides down the playground slide.", "The key turns smoothly in the lock.",
    "I fold the map carefully.", "It feels soft to the touch.", "They race cars on the track.",
    "We hug tightly when we meet.",
    "The garden needs watering every morning.", "She whispers secrets to her best friend.", "Children play hide and seek outside.",
    "He fixes computers for a living.", "The airplane lands smoothly on the runway.", "I enjoy listening to jazz music.",
    "It's important to recycle plastic bottles.", "They celebrate birthdays with big parties.", "We take photos of beautiful sunsets.",
    "Bears hibernate during the coldest months.", "The teacher explains the lesson clearly.", "She wears a scarf in winter.",
    "Dolphins leap gracefully out of water.", "He paints his room a new color.", "The library is quiet on weekdays.",
    "I write poems in my spare time.", "It's fun to explore ancient ruins.", "They collect shells at the beach.",
    "We donate clothes to charity shops.", "The spider spins a delicate web.", "She learns how to play guitar.",
    "Mushrooms grow quickly after the rain.", "He builds model airplanes as a hobby.", "The bridge crosses a wide river.",
    "I stir the soup slowly with a spoon.", "It's exciting to watch live concerts.", "They adopt a puppy from the shelter.",
    "We roast marshmallows over the campfire.", "The astronaut floats weightlessly in space.", "She solves difficult math problems easily.",
    "Volcanoes erupt with molten lava.", "He delivers newspapers early in the morning.", "The necklace sparkles under the light.",
    "I organize my books by genre.", "It's relaxing to meditate before bed.", "They carve pumpkins for Halloween.",
    "We paddle the canoe across the lake.", "The scientist discovers a new species.", "She knits sweaters for her grandchildren.",
    "Turtles move slowly on the sand.", "He photographs wild animals in Africa.", "The waiter serves food with a smile.",
    "I lock the door before leaving.", "It's fascinating to study the stars.", "They perform experiments in the lab.",
    "We hike up the mountain trail.", "The mechanic repairs cars efficiently.", "She arranges flowers in a vase.",
    "Butterflies migrate during certain seasons.", "He designs websites for small businesses.", "The judge announces the final verdict.",
    "I water the plants every evening.", "It's refreshing to swim in the ocean.", "They compete in chess tournaments.",
    "We pack lunch for the picnic.", "The actor memorizes all his lines.", "She practices yoga to stay flexible.",
    "Frogs croak loudly near the pond.", "He measures ingredients for the recipe.", "The artist sketches portraits of people.",
    "I recycle old newspapers and magazines.", "It's thrilling to ride roller coasters.", "They install solar panels on rooftops.",
    "We watch documentaries about wildlife.", "The pilot checks the plane's controls.", "She sews buttons onto the shirt.",
    "Crickets chirp on summer nights.", "He programs robots for fun.", "The chef garnishes the dish with herbs.",
    "I feed the ducks at the pond.", "It's peaceful to sit by the fireplace.", "They volunteer at the animal shelter.",
    "We pick strawberries at the farm.", "The drummer keeps the band's rhythm.", "She braids her daughter's hair neatly.",
    "Owls hunt for prey at night.", "He stacks firewood for the winter.", "The gardener trims the hedges carefully.",
    "I bookmark my favorite web pages.", "It's satisfying to finish a puzzle.", "They kayak down the rushing river.",
    "We admire colorful street art.", "The journalist interviews famous celebrities.", "She donates blood to save lives.",
    "Squirrels bury nuts in the ground.", "He translates documents into different languages.", "The baker decorates cakes with icing.",
    "I proofread my essays for errors.", "It's joyful to hear children laughing.", "They skateboard at the new park.",
    "We stargaze with a telescope.", "The fisherman catches a huge salmon.", "She teaches her parrot to talk.",
    "Rabbits hop around the meadow.", "He collects rare coins as an investment.", "The barista makes the best espresso.",
    "I moisturize my skin before bed.", "It's inspiring to read success stories.", "They film a documentary about climate change.",
    "We carve our names into the tree.", "The architect designs eco-friendly buildings.", "She donates books to the local library.",
    "Deer graze quietly in the field.", "He repairs bicycles in his garage.", "The pharmacist fills prescriptions accurately.",
    "I stretch my muscles after exercising.", "It's rewarding to help others in need.", "They invent gadgets to solve everyday problems.",
    "We picnic under the shade of an oak tree.", "The geologist studies rocks and minerals.", "She volunteers at the homeless shelter weekly.",
    "Kangaroos carry their babies in pouches.", "He plays the piano at weddings.", "The tailor alters the suit to fit perfectly.",
    "I journal about my daily thoughts.", "It's exhilarating to zip-line through forests.", "They rescue injured birds and rehabilitate them.",
]

IMAGE_CATEGORIES = {
    "vehicles": ["car", "truck", "bus", "motorcycle", "bicycle", "airplane", "boat", "train"],
    "animals": ["dog", "cat", "bird", "fish", "horse", "elephant", "lion", "tiger"],
    "food": ["apple", "banana", "pizza", "burger", "cake", "bread", "cheese", "ice cream"],
    "nature": ["tree", "flower", "mountain", "ocean", "sun", "moon", "star", "cloud"],
    "objects": ["chair", "table", "lamp", "phone", "computer", "book", "pen", "clock"]
} 

class CaptchaGenerator:
    @staticmethod
    def generate_text(length=6):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def create_image_captcha(text, width=200, height=80): # Currently Broken, Fix it if you want.
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        char_width = width // len(text)
        max_font_size = 36
        min_font_size = 28
        
        # Store character positions for connecting lines
        char_positions = []

        for i, char in enumerate(text):
            font_size = random.randint(min_font_size, max_font_size)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            char_img = Image.new('RGBA', (char_width, height), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)

            bbox = font.getbbox(char)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            x = (char_width - w) // 2
            y = (height - h) // 2
            char_draw.text((x, y), char, font=font, fill=(random.randint(0, 100), 0, 0))
            angle = random.randint(-3, 3)
            rotated_char_img = char_img.rotate(angle, resample=Image.BICUBIC, expand=1)

            offset_x = i * char_width + random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            
            # Store the center position of each character for connecting lines
            char_center_x = offset_x + char_width // 2
            char_center_y = offset_y + height // 2
            char_positions.append((char_center_x, char_center_y))

            image.paste(rotated_char_img, (offset_x, offset_y), rotated_char_img)

        # Add noise dots
        for _ in range(1000):
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            draw.point((x, y), fill=(0, 0, 0))

        # Draw connecting lines between characters
        for i in range(len(char_positions) - 1):
            # Connect current character to next character
            x1, y1 = char_positions[i]
            x2, y2 = char_positions[i + 1]
            
            # Add some randomness to the connection points
            x1 += random.randint(-15, 15)
            y1 += random.randint(-15, 15)
            x2 += random.randint(-15, 15)
            y2 += random.randint(-15, 15)
            
            # Ensure points are within bounds
            x1 = max(0, min(width, x1))
            y1 = max(0, min(height, y1))
            x2 = max(0, min(width, x2))
            y2 = max(0, min(height, y2))
            
            draw.line([x1, y1, x2, y2], fill=(random.randint(0, 50), 0, 0), width=random.randint(1, 4))

        # Add some additional random lines for more distraction
        for _ in range(5):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.line([x1, y1, x2, y2], fill=(0, 0, 0), width=1)

        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        if os.path.exists("anti.png"):
            overlay = Image.open("anti.png").convert("RGBA").resize((width, height))
            r, g, b, a = overlay.split()
            a = a.point(lambda p: int(p * 0.6))
            overlay = Image.merge("RGBA", (r, g, b, a))
            image = image.convert("RGBA")
            image = Image.alpha_composite(image, overlay)

        return image.convert("RGB")

    @staticmethod
    def create_audio_captcha():
        options = random.sample(SENTENCES, 3)
        incomplete_idx = random.randint(0, 2)
        incomplete = ' '.join(options[incomplete_idx].split(' ')[:-1])
        options[incomplete_idx] = incomplete
        audio_text = f"Option 1: {options[0]}. Option 2: {options[1]}. Option 3: {options[2]}. Which option is incomplete? Enter the number."
        tts = gTTS(text=audio_text, lang='en')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return {
            'audio': audio_io,
            'options': options,
            'correct_answer': incomplete_idx + 1
        }

    @staticmethod
    def create_simple_image(text, size=100, bg_color=None, text_color=None):
        """Create a simple image with text for the clicking captcha"""
        if bg_color is None:
            bg_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        if text_color is None:
            text_color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        
        image = Image.new('RGB', (size, size), bg_color)
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Add some simple shapes for variation
        if random.random() > 0.5:
            # Add a circle
            circle_size = random.randint(10, 30)
            circle_x = random.randint(0, size - circle_size)
            circle_y = random.randint(0, size - circle_size)
            draw.ellipse([circle_x, circle_y, circle_x + circle_size, circle_y + circle_size], 
                        fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
        
        return image

    @staticmethod
    def create_image_click_captcha(grid_size=3):
        """Create a grid-based image clicking captcha"""
        # Choose a random category and target
        category = random.choice(list(IMAGE_CATEGORIES.keys()))
        target_items = IMAGE_CATEGORIES[category]
        
        # Select target items (2-4 items to find)
        num_targets = random.randint(2, min(4, len(target_items)))
        targets = random.sample(target_items, num_targets)
        
        # Create grid of images
        total_images = grid_size * grid_size
        image_size = 100
        
        # Fill grid with mix of target and non-target images
        grid_items = []
        target_positions = []
        
        # Add target images
        for target in targets:
            pos = len(grid_items)
            grid_items.append(target)
            target_positions.append(pos)
        
        # Fill remaining spots with non-target images
        non_target_items = []
        for cat, items in IMAGE_CATEGORIES.items():
            if cat != category:
                non_target_items.extend(items)
        
        while len(grid_items) < total_images:
            item = random.choice(non_target_items)
            grid_items.append(item)
        
        # Shuffle the grid
        positions = list(range(total_images))
        random.shuffle(positions)
        
        # Update target positions after shuffle
        new_target_positions = []
        shuffled_items = [''] * total_images
        
        for i, pos in enumerate(positions):
            shuffled_items[pos] = grid_items[i]
            if i in target_positions:
                new_target_positions.append(pos)
        
        # Create images for each grid item
        images = []
        for item in shuffled_items:
            img = CaptchaGenerator.create_simple_image(item, image_size)
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            images.append(f"data:image/png;base64,{img_base64}")
        
        return {
            'images': images,
            'grid_size': grid_size,
            'target_category': category,
            'target_items': targets,
            'correct_positions': new_target_positions,
            'instruction': f"Click on all images that show {category}"
        }

@app.route('/api/captcha/generate', methods=['POST'])
def generate_captcha():
    data = request.json
    captcha_type = data.get('type', 'image')
    captcha_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if captcha_type == 'audio':
        captcha = CaptchaGenerator.create_audio_captcha()
        audio_base64 = base64.b64encode(captcha['audio'].getvalue()).decode('utf-8')
        c.execute("""
            INSERT INTO captchas (id, type, correct_answer, expires)
            VALUES (?, ?, ?, ?)
        """, (captcha_id, 'audio', str(captcha['correct_answer']), time.time() + CAPTCHA_EXPIRE))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'captcha_id': captcha_id,
            'type': 'audio',
            'audio': f"data:audio/mpeg;base64,{audio_base64}",
            'options': captcha['options']
        })
    elif captcha_type == 'image_click':
        captcha = CaptchaGenerator.create_image_click_captcha()
        c.execute("""
            INSERT INTO captchas (id, type, correct_answer, expires)
            VALUES (?, ?, ?, ?)
        """, (captcha_id, 'image_click', json.dumps(captcha['correct_positions']), time.time() + CAPTCHA_EXPIRE))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'captcha_id': captcha_id,
            'type': 'image_click',
            'images': captcha['images'],
            'grid_size': captcha['grid_size'],
            'instruction': captcha['instruction']
        })
    else:
        captcha_text = CaptchaGenerator.generate_text()
        image = CaptchaGenerator.create_image_captcha(captcha_text)
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        c.execute("""
            INSERT INTO captchas (id, type, text, expires)
            VALUES (?, ?, ?, ?)
        """, (captcha_id, 'image', captcha_text, time.time() + CAPTCHA_EXPIRE))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'captcha_id': captcha_id,
            'type': 'image',
            'image': f"data:image/png;base64,{img_base64}"
        })

def calculate_entropy(path):
    if len(path) < 2:
        return 0.0
    deltas = []
    for i in range(1, len(path)):
        dx = path[i]['x'] - path[i-1]['x']
        dy = path[i]['y'] - path[i-1]['y']
        deltas.append((round(dx), round(dy)))
    freq = Counter(deltas)
    total = len(deltas)
    entropy = -sum((count/total)*math.log2(count/total) for count in freq.values())
    return entropy


def score_user_behavior(mouse_path):
    if len(mouse_path) < 5:
        return 0.0

    total_distance = 0
    angles = []
    speeds = []
    jerkiness = 0

    for i in range(1, len(mouse_path)):
        dx = mouse_path[i]['x'] - mouse_path[i - 1]['x']
        dy = mouse_path[i]['y'] - mouse_path[i - 1]['y']
        dt = mouse_path[i]['t'] - mouse_path[i - 1]['t'] + 1e-5
        dist = math.hypot(dx, dy)
        speed = dist / dt
        angle = math.atan2(dy, dx)
        total_distance += dist
        speeds.append(speed)
        angles.append(angle)
        if i >= 2:
            prev_dx = mouse_path[i - 1]['x'] - mouse_path[i - 2]['x']
            prev_dy = mouse_path[i - 1]['y'] - mouse_path[i - 2]['y']
            jerk_dx = abs(dx - prev_dx)
            jerk_dy = abs(dy - prev_dy)
            jerkiness += jerk_dx + jerk_dy

    angle_var = max(angles) - min(angles) if len(angles) > 1 else 0
    speed_var = max(speeds) - min(speeds) if len(speeds) > 1 else 0
    total_time = mouse_path[-1]['t'] - mouse_path[0]['t']
    entropy = calculate_entropy(mouse_path)

    score = 0.0
    if total_distance > 300: score += 0.25
    if angle_var > 0.6: score += 0.2
    if 0.3 < speed_var < 10.0: score += 0.2
    if total_time > 500: score += 0.2
    if jerkiness > 100: score += 0.1
    if entropy > 2.0: score += 0.1

    return min(score, 1.0)


@app.route('/api/verify', methods=['POST'])
def verify_captcha():
    data = request.json
    mouse_movements = data.get('mouse_path', [])
    score = score_user_behavior(mouse_movements)

    if score < 0.5:
        # suspicious: block or redirect
        return jsonify({"success": False, "score": score, "redirect": "https://www.google.com"})

    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token, timestamp, valid, score) VALUES (?, ?, ?, ?)",
              (token, time.time(), 1, score))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "score": score, "token": token})

@app.route('/api/verify_token', methods=['POST'])
def verify_token():
    token = request.json.get('token')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp FROM tokens WHERE token=? AND valid=1", (token,))
    row = c.fetchone()
    conn.close()
    if row and time.time() - row[0] < CAPTCHA_EXPIRE:
        return jsonify({"valid": True})
    return jsonify({"valid": False})

@app.route('/api/captcha/verify_challenge', methods=['POST'])
def verify_challenge():
    data = request.json
    captcha_id = data.get('captcha_id')
    answer = data.get('answer')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT type, text, correct_answer, expires, attempts FROM captchas WHERE id=?", (captcha_id,))
    row = c.fetchone()
    if not row:
        return jsonify({ "success": False })

    captcha_type, text, correct_answer, expires, attempts = row
    if time.time() > expires or attempts >= MAX_ATTEMPTS:
        return jsonify({ "success": False })

    c.execute("UPDATE captchas SET attempts = attempts + 1 WHERE id=?", (captcha_id,))
    conn.commit()
    conn.close()

    if captcha_type == 'image' and text.strip().lower() == str(answer).strip().lower():
        return _generate_success()
    elif captcha_type == 'audio' and int(answer) == int(correct_answer):
        return _generate_success()
    elif captcha_type == 'image_click':
        # Parse the correct answer and user's answer
        correct_positions = json.loads(correct_answer)
        user_positions = answer if isinstance(answer, list) else []
        
        # Check if user selected exactly the right positions
        if set(user_positions) == set(correct_positions):
            return _generate_success()

    return jsonify({ "success": False })

def _generate_success():
    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token, timestamp, valid) VALUES (?, ?, ?)", (token, time.time(), 1))
    conn.commit()
    conn.close()
    return jsonify({ "success": True, "token": token })

@app.route('/debug/captchas')
def debug_captchas():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM captchas")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/captcha")
def captcha():
    return render_template("index.html")

valid_keys = {
    "aK4mN-2pQzX-7eWvR-t9YbC": {"owner": "admin"}
}
@app.route("/api")
def api():
    key = request.args.get('k')
    if not key:
        return abort(400, "Missing API key (?k=...)")

    if key in valid_keys:
        return render_template("captcha-widget.html")
    else:
        return abort(403, "Invalid API key")
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)