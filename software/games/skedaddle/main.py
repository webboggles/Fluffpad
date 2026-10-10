"""
La-Fluff-Puff Skedaddle - A Pico Adventure
Based on the T-Rex runner concept.
For Pimoroni Pico Plus 2 W with Pico Display Pack 2.8" and Qw/ST Pad.

Copyright (c) 2025-2026 Ilya Titov (https://webboggles.com). PolyForm Noncommercial 1.0.0, see LICENSE.md.
"""

__version__ = "1.0.0"

import time
import gc
import math
import random
from machine import Pin, I2C, PWM
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED, Button
from pimoroni_i2c import PimoroniI2C

# --- Hardware Setup ---
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(1.0)
display.set_font("bitmap8")
WIDTH, HEIGHT = display.get_bounds()  # 320x240

button_a = Button(12) # A: Fire weapon
button_b = Button(13) # B: Pause
button_x = Button(14) # X: Restart
button_y = Button(15) # Y: Toggle sound

led = RGBLED(26, 27, 28)
i2c = PimoroniI2C(sda=4, scl=5)
buzzer = PWM(Pin(6))
buzzer.duty_u16(0)

# --- Game Constants ---
GROUND_Y = HEIGHT - 40
GRAVITY = 1.0
JUMP_STRENGTH = -20
MIN_JUMP_STRENGTH = -10
JUMP_BOOST_RATE = -0.5
MAX_JUMP_HOLD_TIME = 15  # Maximum frames to add velocity
INITIAL_SPEED = 8
MAX_SPEED = 20
SPEED_INCREMENT = 0.003
PROJECTILE_SPEED = 12

# --- Colors ---
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
SKY_BLUE = display.create_pen(135, 206, 235)
GROUND_COLOR = display.create_pen(102, 57, 49) # A darker brown for ground
METAL_GRID = display.create_pen(50, 50, 60)
PURPLE = display.create_pen(128, 0, 128)
DARK_PURPLE = display.create_pen(80, 0, 80)
BLUE = display.create_pen(0, 0, 255)
DARK_BLUE = display.create_pen(0, 0, 139)
RED = display.create_pen(255, 0, 0)
SILVER = display.create_pen(192, 192, 192)
YELLOW = display.create_pen(255, 255, 0)
GREEN = display.create_pen(0, 255, 0)
# Cloud Colors
CLOUD_WHITE = display.create_pen(220, 220, 230)
CLOUD_PINK = display.create_pen(230, 200, 210)
CLOUD_BLUE = display.create_pen(200, 210, 230)

# La-Fluff-Puff coloring options from spec
FLUFF_COLORS = [
    display.create_pen(255, 182, 193), # Pastel Pink
    display.create_pen(0, 191, 255),   # Electric Blue
    display.create_pen(152, 251, 152), # Mint Green
    display.create_pen(230, 230, 250), # Lavender
    display.create_pen(255, 127, 80),  # Coral Orange
    display.create_pen(255, 255, 0),   # Sunshine Yellow
    display.create_pen(221, 160, 221), # Bubblegum Purple
    display.create_pen(0, 128, 128),   # Seafoam Teal
]

# --- Game States ---
class GameState:
    START = 0
    PLAYING = 1
    GAME_OVER = 2
    PAUSE = 3
    SELECTING = 4  # New state for La-Fluff-Puff selection

# --- Sound ---
NOTES = {'C4': 262, 'E4': 330, 'G4': 392, 'C5': 523, 'D5': 587, 'E5': 659, 
         'A4': 440, 'B4': 494, 'F4': 349, 'G5': 784, 'A5': 880, 'B5': 988,
         'D4': 294, 'F5': 698, 'C3': 131, 'G3': 196, 'E3': 165, 'C6': 1047}
SOUND_JUMP = ('E5', 50)
SOUND_GAMEOVER = [('G4', 100), ('E4', 100), ('C4', 200)]
SOUND_RESTART = ('C5', 100)
SOUND_SCORE = ('D5', 50)
SOUND_SHOOT = ('A5', 30)
SOUND_HIT = ('C5', 50)
SOUND_PAUSE = ('G4', 50)
SOUND_WEAPON_GET = [('C5', 80), ('G5', 120)]
SOUND_DRUM = ('C4', 50)  # Drum sound for selection
SOUND_MESSAGE_CHANGE = ('A5', 40)  # Quick blip for message changes

# Enhanced 8-bit adventure theme with rhythm
ADVENTURE_THEME = [
    # Intro - Fast arpeggios (Sonic/Mega Man style)
    ('C5', 60), ('E5', 60), ('G5', 60), ('C6', 60),
    ('G5', 60), ('E5', 60), ('C5', 60), ('G4', 60),
    
    # Main theme - Energetic and heroic
    ('E5', 120), ('E5', 60), ('D5', 60), ('E5', 120), ('G5', 120),
    ('A5', 180), ('G5', 60), ('E5', 120), ('C5', 120),
    
    # Build up
    ('D5', 120), ('D5', 60), ('C5', 60), ('D5', 120), ('F5', 120),
    ('G5', 180), ('F5', 60), ('D5', 120), ('B4', 120),
    
    # Power section
    ('C5', 60), ('D5', 60), ('E5', 60), ('F5', 60),
    ('G5', 120), ('A5', 120), ('B5', 120), ('C6', 240),
    
    # Fast run (Sonic style)
    ('C6', 60), ('B5', 60), ('A5', 60), ('G5', 60),
    ('F5', 60), ('E5', 60), ('D5', 60), ('C5', 60),
    
    # Rhythmic section
    ('G4', 60), ('G4', 60), ('C5', 60), ('G4', 60),
    ('E5', 120), ('D5', 60), ('C5', 60), ('G4', 120),
    
    # Epic climax
    ('E5', 60), ('G5', 60), ('C6', 120), ('B5', 60), ('G5', 60),
    ('A5', 120), ('F5', 60), ('D5', 60), ('G5', 240),
    
    # Resolution and loop
    ('C5', 60), ('E5', 60), ('G5', 60), ('E5', 60),
    ('C5', 120), ('G4', 120), ('C5', 240),
    
    # Bridge before loop
    ('A4', 60), ('B4', 60), ('C5', 60), ('D5', 60),
    ('E5', 60), ('F5', 60), ('G5', 60), ('A5', 60),
]

# Drum roll pattern for selection
DRUM_ROLL_PATTERN = [
    ('C3', 40), ('E3', 40), ('G3', 40), ('C4', 40),  # Fast roll
    ('G3', 60), ('E3', 60), ('C3', 60),  # Slowing
    ('C3', 100), ('C3', 150), ('C3', 200),  # Final hits
    ('C4', 300), ('E4', 100), ('G4', 100), ('C5', 200)  # Fanfare
]


# --- Classes ---
class ParallaxLayer:
    def __init__(self, speed_divisor, pens, size_range, count):
        self.speed_divisor = speed_divisor
        self.x = 0
        self.elements = []
        for _ in range(count):
            cloud_x = random.randint(0, WIDTH)
            cloud_y = random.randint(20, GROUND_Y - 80)
            num_puffs = random.randint(3, 5)
            puffs = []
            base_size = random.randint(size_range[0], size_range[1])
            for _ in range(num_puffs):
                puffs.append({
                    'dx': random.randint(-base_size // 2, base_size // 2),
                    'dy': random.randint(-base_size // 4, base_size // 4),
                    'size': random.randint(base_size // 2, base_size)
                })
            self.elements.append({
                'x': cloud_x,
                'y': cloud_y,
                'pen': random.choice(pens),
                'puffs': puffs
            })

    def update(self, game_speed):
        self.x -= game_speed / self.speed_divisor * 2
        if self.x <= -WIDTH:
            self.x = 0

    def draw(self):
        for element in self.elements:
            display.set_pen(element['pen'])
            for puff in element['puffs']:
                # Draw two sets for seamless looping
                px1 = int(self.x + element['x'] + puff['dx'])
                py = element['y'] + puff['dy']
                display.circle(px1, py, puff['size'])

                px2 = int(self.x + element['x'] + WIDTH + puff['dx'])
                display.circle(px2, py, puff['size'])

class LaFluffPuff:
    def __init__(self):
        self.width = 32
        self.height = 40
        self.x = 50
        self.y = float(GROUND_Y - self.height)  # Store as float for physics
        self.vy = 0.0
        self.is_jumping = False
        self.jump_hold_time = 0
        self.can_boost_jump = False
        self.anim_frame = 0
        self.anim_timer = 0
        # Don't generate appearance yet - will be set during selection
        self.color = FLUFF_COLORS[0]
        self.face = 'determined'

    def _generate_appearance(self):
        self.color = random.choice(FLUFF_COLORS)
        self.face_options = [
            'determined', 'panic', 'cheeky', 'sleepy', 'angry', 'surprised', 'confident', 'worried', 'excited', 'confused'
        ]
        self.face = random.choice(self.face_options)
    
    def set_appearance(self, color_index, face_index):
        """Set specific appearance for selection screen"""
        self.color = FLUFF_COLORS[color_index % len(FLUFF_COLORS)]
        face_options = ['determined', 'panic', 'cheeky', 'sleepy', 'angry', 
                       'surprised', 'confident', 'worried', 'excited', 'confused']
        self.face = face_options[face_index % len(face_options)]

    def start_jump(self):
        """Start jump immediately with minimum strength"""
        if not self.is_jumping:
            self.vy = MIN_JUMP_STRENGTH
            self.is_jumping = True
            self.jump_hold_time = 0
            self.can_boost_jump = True
            return True
        return False
    
    def boost_jump(self):
        """Add upward velocity while jump key is held"""
        if self.can_boost_jump and self.jump_hold_time < MAX_JUMP_HOLD_TIME:
            # Add upward velocity (negative = up)
            self.vy += JUMP_BOOST_RATE
            # Clamp to maximum jump velocity
            self.vy = max(JUMP_STRENGTH, self.vy)
            self.jump_hold_time += 1
            return True
        return False
    
    def end_jump_boost(self):
        """Stop adding upward velocity"""
        self.can_boost_jump = False

    def jump(self):
        """Legacy jump method for compatibility"""
        if not self.is_jumping:
            self.vy = JUMP_STRENGTH
            self.is_jumping = True
            return True
        return False

    def update(self):
        # Animation
        self.anim_timer += 1
        if self.anim_timer > 4: # Slower animation
            self.anim_frame = (self.anim_frame + 1) % 4 # 4 frame running animation
            self.anim_timer = 0
        
        # Physics
        self.y += self.vy
        self.vy += GRAVITY
        
        # Stop boosting if moving downward
        if self.vy > 0:
            self.can_boost_jump = False

        if self.y >= GROUND_Y - self.height:
            self.y = float(GROUND_Y - self.height)
            self.vy = 0.0
            self.is_jumping = False
            self.can_boost_jump = False
            self.jump_hold_time = 0

    def draw(self):
        # Simple running animation using height
        draw_y_offset = 0
        if not self.is_jumping:
            if self.anim_frame in [1, 3]:
                draw_y_offset = -4 # Bob up and down
        
        # Slight squash effect when about to jump (removed charging visual)
        
        # Body
        display.set_pen(self.color)
        body_x = int(self.x + self.width // 2)
        body_y = int(self.y + self.height // 2 + draw_y_offset)
        
        display.circle(body_x, body_y, 15)

        # Head
        head_y = body_y - 15
        display.circle(body_x, head_y, 12)
        
        # Ears (rabbit-like ears)
        ear_height = 10
        ear_width = 4
        ear_offset = 6
        # Left ear
        for i in range(ear_height):
            width = ear_width - (i // 3)  # Taper towards top
            if width > 0:
                display.rectangle(body_x - ear_offset - width//2, head_y - 8 - i, width, 1)
        # Right ear
        for i in range(ear_height):
            width = ear_width - (i // 3)  # Taper towards top
            if width > 0:
                display.rectangle(body_x + ear_offset - width//2, head_y - 8 - i, width, 1)
        
        # Arms
        arm_y = body_y - 5
        # Left arm (back arm when running right)
        display.circle(body_x - 12, arm_y + 2, 4)
        # Right arm (front arm when running right) - slightly forward
        display.circle(body_x - 8, arm_y - 2, 4)

        # Eyes (facing slightly right)
        eye_x1 = body_x - 4  # Shifted right
        eye_x2 = body_x + 3  # Shifted right
        eye_y = head_y

        display.set_pen(WHITE)
        display.circle(eye_x1, eye_y, 4)
        if self.face == 'cheeky': # Wink
             display.line(eye_x2 - 2, eye_y, eye_x2 + 2, eye_y, 2)
        else:
            display.circle(eye_x2, eye_y, 4)
            
        display.set_pen(BLACK)
        # Pupils looking forward/right
        display.circle(eye_x1 + 1, eye_y, 2)  # Shifted right
        if self.face != 'cheeky':
             display.circle(eye_x2 + 1, eye_y, 2)  # Shifted right
        
        # Small nose/mouth (facing right)
        display.set_pen(self.color)
        display.circle(body_x + 4, head_y + 3, 2)

        # Legs (animation)
        leg_y = body_y + 10
        leg_x1 = body_x - 5
        leg_x2 = body_x + 5
        
        # Restore color for legs
        display.set_pen(self.color)
        
        if self.is_jumping:
            # Tucked legs for jump
            display.rectangle(leg_x1 - 2, int(self.y + self.height - 8), 4, 4)
            display.rectangle(leg_x2 - 2, int(self.y + self.height - 8), 4, 4)
        else:
            # Running legs with animation
            anim_offset = self.anim_frame
            if anim_offset == 3: anim_offset = 1
            if anim_offset == 2: anim_offset = 0

            # Back leg
            display.rectangle(leg_x1 - 2, leg_y + anim_offset * 2, 4, 8)
            # Front leg (slightly forward)
            display.rectangle(leg_x2, leg_y + (2 - anim_offset) * 2, 4, 8)

    def get_rect(self):
        # Tighter bounding box for collision - ensure integers
        return int(self.x + 4), int(self.y), self.width - 8, self.height

OBSTACLE_TYPES = {
    'duck': {'color': display.create_pen(255, 255, 0), 'min_h': 30, 'max_h': 30, 'w': 25, 'label': 'DUCK'},
    'pizza': {'color': display.create_pen(255, 215, 0), 'min_h': 25, 'max_h': 25, 'w': 25, 'label': 'PIZZA'},
    'toaster': {'color': display.create_pen(192, 192, 192), 'min_h': 35, 'max_h': 35, 'w': 30, 'label': 'TOAST'},
    'cactus': {'color': display.create_pen(0, 100, 0), 'min_h': 20, 'max_h': 50, 'w': 20, 'label': 'OUCH!'},
    'marshmallow': {'color': display.create_pen(255, 192, 203), 'min_h': 25, 'max_h': 35, 'w': 25, 'label': 'SOFT'},
    'spider': {'color': display.create_pen(64, 64, 64), 'min_h': 20, 'max_h': 30, 'w': 30, 'label': 'SPIDER'},
    'taco': {'color': display.create_pen(255, 140, 0), 'min_h': 20, 'max_h': 25, 'w': 20, 'label': 'TACO'},
    'bowling': {'color': display.create_pen(0, 0, 0), 'min_h': 30, 'max_h': 30, 'w': 30, 'label': 'BOWL'},
}

class Obstacle:
    def __init__(self, speed):
        self.type_name = random.choice(list(OBSTACLE_TYPES.keys()))
        props = OBSTACLE_TYPES[self.type_name]
        
        self.width = props['w']
        self.height = random.randint(props['min_h'], props['max_h'])
        self.x = float(WIDTH)  # Store as float for smooth movement
        self.y = GROUND_Y - self.height
        self.speed = speed
        self.passed = False
        self.color = props['color']
        self.label = props['label']

    def update(self):
        self.x -= self.speed

    def draw(self):
        display.set_pen(self.color)
        display.rectangle(int(self.x), int(self.y), self.width, self.height)
        
        # Add details based on type
        if self.type_name == 'cactus':
            display.set_pen(WHITE)
            display.circle(int(self.x + self.width // 2), int(self.y + 5), 2)
        elif self.type_name == 'duck':
            display.set_pen(BLACK)
            display.circle(int(self.x + self.width - 5), int(self.y + 8), 2)
        elif self.type_name == 'spider':
            # Draw spider legs
            display.set_pen(BLACK)
            for i in range(4):
                display.line(int(self.x), int(self.y + self.height // 2), 
                           int(self.x - 5), int(self.y + i * 5), 1)
                display.line(int(self.x + self.width), int(self.y + self.height // 2), 
                           int(self.x + self.width + 5), int(self.y + i * 5), 1)
        
        # Draw label above obstacle
        display.set_pen(WHITE)
        label_width = display.measure_text(self.label, 1)
        display.text(self.label, int(self.x + (self.width - label_width) // 2), int(self.y - 10), 200, 1)


    def is_offscreen(self):
        return self.x < -self.width

    def get_rect(self):
        return int(self.x), int(self.y), self.width, self.height

class UFO:
    def __init__(self, speed):
        self.width = 30
        self.height = 15
        self.x = float(WIDTH)  # Store as float for smooth movement
        self.y = random.randint(20, 80)
        self.speed = speed * 1.2 # UFOs are a bit faster
    
    def update(self):
        self.x -= self.speed

    def draw(self):
        display.set_pen(SILVER)
        # Draw a classic saucer shape
        display.triangle(int(self.x), int(self.y + self.height), 
                         int(self.x + self.width), int(self.y + self.height), 
                         int(self.x + self.width // 2), int(self.y))
        display.set_pen(WHITE)
        display.circle(int(self.x + self.width // 2), int(self.y + self.height // 2), 3)

    def is_offscreen(self):
        return self.x < -self.width
        
    def get_rect(self):
        return int(self.x), int(self.y), self.width, self.height

class Projectile:
    def __init__(self, x, y):
        self.x = float(x)  # Store as float for smooth movement
        self.y = float(y)
        self.width = 8
        self.height = 4
    
    def update(self):
        self.x += PROJECTILE_SPEED

    def draw(self):
        display.set_pen(RED)
        display.rectangle(int(self.x), int(self.y), self.width, self.height)

    def is_offscreen(self):
        return self.x > WIDTH

    def get_rect(self):
        return int(self.x), int(self.y), self.width, self.height

class Game:
    def __init__(self):
        self._reset()
        self.high_score = 0
        
        # Parallax background layers
        self.bg_layers = [
            # Furthest, slowest layer (distant clouds)
            ParallaxLayer(10, [CLOUD_BLUE, CLOUD_PINK], (15, 25), 2),
            # Mid layer (closer clouds)
            ParallaxLayer(5, [CLOUD_WHITE], (20, 35), 3),
        ]
        
        # Music system
        self.music_index = 0
        self.music_timer = 0
        self.music_playing = False
        
        # Jump tracking
        self.jump_button_pressed = False
        self.jump_button_time = 0
        
        # Selection system
        self.selection_timer = 0
        self.selection_speed = 1  # Start even faster (was 2)
        self.selection_color = 0
        self.selection_face = 0
        self.selection_messages = [
            "Initializing fluffiness...",
            "Reticulating splines...",
            "Applying googly eyes...",
            "Dividing by zero...",
            "Injecting pure whimsy...",
            "Polishing the void...",
            "Summoning from the beyond...",
            "Consulting the chicken...",
            "Herding cosmic kittens...",
            "Assembling pixels...",
            "Cuteness overload imminent!",
            "Don't lick the screen...",
            "Finalizing fluff protocol...",
        ]
        # random.shuffle(self.selection_messages) # Not available in MicroPython
        
        # Manual shuffle (Fisher-Yates algorithm)
        n = len(self.selection_messages)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            self.selection_messages[i], self.selection_messages[j] = self.selection_messages[j], self.selection_messages[i]

        self.selection_messages.append("Maya's La-Fluff-Puff READY!")

        self.selection_message_index = 0
        self.selection_phase = 0  # 0 = spinning, 1 = slowing, 2 = done
        self.drum_timer = 0
        self.drum_pattern_index = 0
        self.last_message_index = -1  # Track message changes
        self.weapon_drop_cooldown = 0

    def _reset(self):
        self.state = GameState.START
        self.player = LaFluffPuff()
        self.obstacles = []
        self.ufos = []
        self.projectiles = []
        self.score = 0
        self.game_speed = INITIAL_SPEED
        self.obstacle_spawn_timer = 0
        self.ufo_spawn_timer = 0
        self.ammo = 0
        self.next_weapon_score = random.randint(200, 500)
        self.sound_on = True
        self.frame_count = 0
        self.music_index = 0
        self.music_timer = 0
        led.set_rgb(0, 0, 255)

    def _spawn_obstacle(self):
        if not self.obstacles or self.obstacles[-1].x < WIDTH - random.randint(200, 500):  # Increased gap from 100-300 to 200-500
            self.obstacles.append(Obstacle(self.game_speed))

    def _spawn_ufo(self):
        self.ufo_spawn_timer -=1
        if self.ufo_spawn_timer <= 0:
            self.ufos.append(UFO(self.game_speed))
            self.ufo_spawn_timer = random.randint(90, 240) # Spawn more frequently

    def _fire_weapon(self):
        if self.ammo > 0:
            self.ammo -= 1
            # Fire from La-Fluff-Puff's position
            proj_x = self.player.x + self.player.width
            proj_y = self.player.y + self.player.height // 2
            self.projectiles.append(Projectile(proj_x, proj_y))
            self.play_sound_tune([SOUND_SHOOT])

    def _check_collisions(self):
        player_rect = self.player.get_rect()
        for obstacle in self.obstacles:
            obs_rect = obstacle.get_rect()
            # Simple AABB collision
            if (player_rect[0] < obs_rect[0] + obs_rect[2] and
                player_rect[0] + player_rect[2] > obs_rect[0] and
                player_rect[1] < obs_rect[1] + obs_rect[3] and
                player_rect[1] + player_rect[3] > obs_rect[1]):
                self.state = GameState.GAME_OVER
                led.set_rgb(255, 0, 0)
                self.play_sound_tune(SOUND_GAMEOVER)
                if self.score > self.high_score:
                    self.high_score = self.score
        
        # Projectile collisions
        for proj in self.projectiles[:]:
            proj_rect = proj.get_rect()
            
            # Vs Obstacles
            for obs in self.obstacles[:]:
                if not obs.passed: # Don't hit obstacles behind player
                    obs_rect = obs.get_rect()
                    if (proj_rect[0] < obs_rect[0] + obs_rect[2] and
                        proj_rect[0] + proj_rect[2] > obs_rect[0] and
                        proj_rect[1] < obs_rect[1] + obs_rect[3] and
                        proj_rect[1] + proj_rect[3] > obs_rect[1]):
                        
                        self.projectiles.remove(proj)
                        self.obstacles.remove(obs)
                        self.score += 25 # Destroy obstacle bonus
                        self.play_sound_tune([SOUND_HIT])
                        break # Go to next projectile
            else: # If projectile wasn't removed, check vs UFOs
                # Vs UFOs
                for ufo in self.ufos[:]:
                    ufo_rect = ufo.get_rect()
                    if (proj_rect[0] < ufo_rect[0] + ufo_rect[2] and
                        proj_rect[0] + proj_rect[2] > ufo_rect[0] and
                        proj_rect[1] < ufo_rect[1] + ufo_rect[3] and
                        proj_rect[1] + proj_rect[3] > ufo_rect[1]):
                        
                        self.projectiles.remove(proj)
                        self.ufos.remove(ufo)
                        self.score += 50 # Destroy UFO bonus
                        self.play_sound_tune([SOUND_HIT])
                        break # Go to next projectile

    def _update_score(self):
        # Survival bonus: 1 point per 10 frames (~6 points per second)
        if self.frame_count % 10 == 0:
            self.score += 1
            
        for obstacle in self.obstacles:
            if not obstacle.passed and obstacle.x + obstacle.width < self.player.x:
                obstacle.passed = True
                self.score += 10 # Bonus for passing
                self.play_sound_tune([SOUND_SCORE])
        
        # Random weapon drop logic
        if self.weapon_drop_cooldown == 0 and self.score > 20:
            # Drop chance triggers around multiples of 25, with randomness.
            if self.score % 25 < random.randint(0, 5):
                self.ammo += 10
                self.score += 5
                self.play_sound_tune(SOUND_WEAPON_GET)
                self.weapon_drop_cooldown = 180 # 3 second cooldown

    def _update_music(self):
        """Update background music"""
        if not self.sound_on or self.state != GameState.PLAYING:
            return
            
        self.music_timer -= 1
        if self.music_timer <= 0:
            if self.music_index < len(ADVENTURE_THEME):
                note, duration = ADVENTURE_THEME[self.music_index]
                if note in NOTES:
                    buzzer.freq(int(NOTES[note]))
                    buzzer.duty_u16(300)  # Slightly louder for epic feel
                self.music_timer = duration // 50  # Even faster tempo (was 30)
                self.music_index += 1
            else:
                # Loop the music with a very brief pause
                self.music_index = 0
                buzzer.duty_u16(0)
                self.music_timer = 5  # Reduced pause (was 10)

    def run(self):
        print("Game starting...")
        while True:
            self.frame_count += 1
            
            # Decrement cooldowns
            if self.weapon_drop_cooldown > 0:
                self.weapon_drop_cooldown -= 1
            
            # --- Input ---
            qwst_input = check_qwst_pad()
            jump_pressed = (qwst_input and qwst_input['y']) if qwst_input else False
            fire_pressed = ((qwst_input and qwst_input['a']) if qwst_input else False) or button_a.read()
            restart_pressed = button_x.read()
            pause_pressed = button_b.read()
            sound_toggle_pressed = button_y.read()
            
            # --- Global Inputs ---
            if sound_toggle_pressed:
                self.sound_on = not self.sound_on
                # Debounce by consuming press
                while button_y.read(): time.sleep_ms(10)

            # --- State Machine ---
            if self.state == GameState.START:
                if jump_pressed:
                    print("Starting selection!")
                    self.state = GameState.SELECTING
                    self.selection_timer = 0
                    self.selection_speed = 1  # Start faster
                    self.selection_phase = 0
                    self.selection_message_index = 0
                    self.drum_timer = 0
                    self.drum_pattern_index = 0
                    led.set_rgb(255, 255, 0)  # Yellow during selection
                    self.last_message_index = -1  # Reset message tracker
            
            elif self.state == GameState.SELECTING:
                # Update selection animation
                self.selection_timer += 1
                
                if self.selection_phase == 0:  # Fast spinning phase
                    if self.selection_timer % self.selection_speed == 0:
                        self.selection_color = (self.selection_color + 1) % len(FLUFF_COLORS)
                        self.selection_face = (self.selection_face + 1) % 10
                        self.player.set_appearance(self.selection_color, self.selection_face)
                        
                        # Play drum pattern
                        if self.sound_on and self.drum_pattern_index < 4:
                            note, duration = DRUM_ROLL_PATTERN[self.drum_pattern_index]
                            buzzer.freq(int(NOTES[note]))
                            buzzer.duty_u16(1200)
                            self.drum_timer = duration // 40
                            self.drum_pattern_index = (self.drum_pattern_index + 1) % 4
                    
                    # Slow down after ~0.3 seconds (20 frames)
                    if self.selection_timer > 20:
                        self.selection_phase = 1
                        self.selection_timer = 0
                
                elif self.selection_phase == 1:  # Slowing down phase
                    # Increase speed over ~0.25 seconds (15 frames) to slow down the visual spin
                    if self.selection_timer > 0:
                         self.selection_speed += 14.0 / 15.0

                    if self.selection_timer % int(self.selection_speed) == 0:
                        self.selection_color = (self.selection_color + 1) % len(FLUFF_COLORS)
                        self.selection_face = (self.selection_face + 1) % 10
                        self.player.set_appearance(self.selection_color, self.selection_face)
                        
                        # Play slowing drum pattern
                        if self.sound_on and 4 <= self.drum_pattern_index < 10:
                            note, duration = DRUM_ROLL_PATTERN[self.drum_pattern_index]
                            buzzer.freq(int(NOTES[note]))
                            buzzer.duty_u16(1000)
                            self.drum_timer = duration // 40
                            self.drum_pattern_index += 1
                    
                    # Transition after 0.25 seconds
                    if self.selection_timer > 15:
                        self.selection_phase = 2
                        self.selection_timer = 0
                        # Play fanfare
                        if self.sound_on:
                            for i in range(10, len(DRUM_ROLL_PATTERN)):
                                note, duration = DRUM_ROLL_PATTERN[i]
                                buzzer.freq(int(NOTES[note]))
                                buzzer.duty_u16(1500)
                                time.sleep_ms(duration)
                            buzzer.duty_u16(0)
                
                elif self.selection_phase == 2:  # Done - wait then start
                    if self.selection_timer > 10:  # ~0.15 second wait
                        self.state = GameState.PLAYING
                        led.set_rgb(0, 255, 0)
                
                # Update message based on total progress
                total_frames_so_far = self.selection_timer
                if self.selection_phase == 1: total_frames_so_far += 20
                
                msg_index = min(total_frames_so_far // 6, len(self.selection_messages) - 1) # 35 frames / 6 messages = ~6 frames/msg
                
                if self.selection_phase == 2:
                    msg_index = len(self.selection_messages) - 1
                
                # Play sound when message changes
                if msg_index != self.last_message_index:
                    self.last_message_index = msg_index
                    if self.sound_on and msg_index < len(self.selection_messages) - 1:
                        # Don't play for the final message (it has its own fanfare)
                        self.play_sound_tune([SOUND_MESSAGE_CHANGE])
                
                self.selection_message_index = msg_index
                
                # Handle drum sound duration
                if self.drum_timer > 0:
                    self.drum_timer -= 1
                    if self.drum_timer == 0:
                        buzzer.duty_u16(0)
            
            elif self.state == GameState.PLAYING:
                if pause_pressed:
                    self.state = GameState.PAUSE
                    self.play_sound_tune([SOUND_PAUSE])
                    buzzer.duty_u16(0)  # Stop music
                    # Debounce
                    while button_b.read(): time.sleep_ms(10)
                else:
                    # Handle variable jump
                    if jump_pressed and not self.jump_button_pressed:
                        # Button just pressed - start jump immediately
                        self.jump_button_pressed = True
                        if self.player.start_jump():
                            self.play_sound_tune([SOUND_JUMP])
                    elif jump_pressed and self.jump_button_pressed:
                        # Button held - boost jump
                        if self.player.boost_jump():
                            # Optional: play a subtle boost sound
                            if self.sound_on and self.player.jump_hold_time % 5 == 0:
                                buzzer.freq(600 + self.player.jump_hold_time * 20)
                                buzzer.duty_u16(200)
                    elif not jump_pressed and self.jump_button_pressed:
                        # Button released - stop boosting
                        self.jump_button_pressed = False
                        self.player.end_jump_boost()
                        buzzer.duty_u16(0)  # Stop any boost sound
                    
                    if fire_pressed:
                        self._fire_weapon()
                    
                    # Update game elements
                    self.player.update()
                    self._spawn_obstacle()
                    self._spawn_ufo()
                    self._update_music()  # Update background music

                    for p in self.projectiles: p.update()
                    for o in self.obstacles: o.update()
                    for u in self.ufos: u.update()
                    
                    # Remove offscreen elements
                    self.obstacles = [obs for obs in self.obstacles if not obs.is_offscreen()]
                    self.ufos = [ufo for ufo in self.ufos if not ufo.is_offscreen()]
                    self.projectiles = [p for p in self.projectiles if not p.is_offscreen()]
                    
                    # Check for game over
                    self._check_collisions()

                    # Update score and speed
                    self._update_score()
                    if self.game_speed < MAX_SPEED:
                        self.game_speed += SPEED_INCREMENT
                    
                    # Update background
                    for layer in self.bg_layers:
                        layer.update(self.game_speed)

            elif self.state == GameState.GAME_OVER:
                buzzer.duty_u16(0)  # Stop any sounds
                # Reset jump state
                self.jump_button_pressed = False
                
                if restart_pressed:
                    self.play_sound_tune([SOUND_RESTART])
                    self._reset()
            
            elif self.state == GameState.PAUSE:
                if pause_pressed:
                    self.state = GameState.PLAYING
                    self.play_sound_tune([SOUND_PAUSE])
                    # Debounce
                    while button_b.read(): time.sleep_ms(10)


            # --- Drawing ---
            self.draw()
            
            # --- Frame Rate ---
            gc.collect()
            time.sleep_ms(16) # Target ~60 fps

    def draw(self):
        # Always clear and update display
        display.set_pen(SKY_BLUE)
        display.clear()

        # Draw Parallax Background
        for layer in self.bg_layers:
            layer.draw()

        # Draw Ground
        display.set_pen(METAL_GRID)
        display.rectangle(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y)
        
        if self.state == GameState.START:
            self._draw_start_screen()
        elif self.state == GameState.PLAYING:
            self._draw_playing_screen()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over_screen()
        elif self.state == GameState.PAUSE:
            self._draw_pause_screen()
        elif self.state == GameState.SELECTING:
            self._draw_selection_screen()

        # Draw Score / HUD
        display.set_pen(WHITE)
        display.text(f"Score: {self.score}", 10, 10, 200, 2)
        display.text(f"Hi: {self.high_score}", WIDTH - 150, 10, 140, 2)
        
        # Draw Ammo
        if self.state != GameState.START:
            display.set_pen(RED)
            display.text(f"Ammo: {self.ammo}", 10, 30, 200, 2)
        
        # Draw Sound Indicator
        sound_text = "Sound: ON" if self.sound_on else "Sound: OFF"
        display.set_pen(WHITE)
        display.text(sound_text, WIDTH - 150, 30, 140, 2)
        
        display.update()

    def _draw_start_screen(self):
        self.player.draw()
        display.set_pen(WHITE)
        
        # Split the long title into two lines and center each
        title_text1 = "Maya's La-Fluff-Puff"
        title_text2 = "Skedaddle"
        
        title_width1 = display.measure_text(title_text1, 3)
        display.text(title_text1, (WIDTH - title_width1) // 2, 30, WIDTH, 3)
        
        title_width2 = display.measure_text(title_text2, 3)
        display.text(title_text2, (WIDTH - title_width2) // 2, 60, WIDTH, 3)
        
        # Split "Press Y" message into two lines and center each
        start_text1 = "Press Y to Select"
        start_text2 = "Your La-Fluff-Puff!"
        
        start_width1 = display.measure_text(start_text1, 2)
        display.text(start_text1, (WIDTH - start_width1) // 2, 110, WIDTH, 2)
        
        start_width2 = display.measure_text(start_text2, 2)
        display.text(start_text2, (WIDTH - start_width2) // 2, 135, WIDTH, 2)

    def _draw_playing_screen(self):
        self.player.draw()
        for obstacle in self.obstacles:
            obstacle.draw()
        for ufo in self.ufos:
            ufo.draw()
        for proj in self.projectiles:
            proj.draw()

    def _draw_game_over_screen(self):
        self._draw_playing_screen() # Show final scene
        display.set_pen(WHITE)
        
        go_text = "GAME OVER"
        go_width = display.measure_text(go_text, 4)
        display.text(go_text, (WIDTH - go_width) // 2, 80, WIDTH, 4)
        
        restart_text = "Press X to Restart"
        restart_width = display.measure_text(restart_text, 2)
        display.text(restart_text, (WIDTH - restart_width) // 2, 130, WIDTH, 2)

    def _draw_pause_screen(self):
        self._draw_playing_screen() # Show final scene
        display.set_pen(WHITE)
        
        pause_text = "PAUSED"
        pause_width = display.measure_text(pause_text, 4)
        display.text(pause_text, (WIDTH - pause_width) // 2, 80, WIDTH, 4)
        
        resume_text = "Press B to Resume"
        resume_width = display.measure_text(resume_text, 2)
        display.text(resume_text, (WIDTH - resume_width) // 2, 130, WIDTH, 2)
        
    def _draw_selection_screen(self):
        # Draw centered La-Fluff-Puff
        temp_x = self.player.x
        temp_y = self.player.y
        self.player.x = WIDTH // 2 - self.player.width // 2
        self.player.y = HEIGHT // 2 - self.player.height // 2
        self.player.draw()
        self.player.x = temp_x
        self.player.y = temp_y
        
        # Draw title
        display.set_pen(WHITE)
        title = "LA-FLUFF-PUFF GENERATOR 3000"
        title_width = display.measure_text(title, 2)
        display.text(title, (WIDTH - title_width) // 2, 20, WIDTH, 2)
        
        # Draw witty message
        message = self.selection_messages[self.selection_message_index]
        msg_width = display.measure_text(message, 2)
        display.set_pen(YELLOW if self.selection_phase < 2 else WHITE)
        display.text(message, (WIDTH - msg_width) // 2, HEIGHT - 60, WIDTH, 2)
        
        # Draw progress bar
        if self.selection_phase < 2:
            display.set_pen(WHITE)
            display.rectangle(40, HEIGHT - 30, WIDTH - 80, 10)
            display.set_pen(GREEN if self.selection_phase == 1 else YELLOW)
            
            total_frames_so_far = self.selection_timer
            if self.selection_phase == 1: total_frames_so_far += 20
            
            progress = min(total_frames_so_far / 35.0, 1.0) # 35 frames total for phases 0 and 1
            display.rectangle(42, HEIGHT - 28, int((WIDTH - 84) * progress), 6)
        
    def play_sound_tune(self, tune):
        if self.sound_on:
            # Temporarily stop background music for sound effects
            buzzer.duty_u16(0)
            play_tune(tune)
            # Music will resume on next update


# --- Helper Functions ---
def play_sound(frequency, duration_ms):
    if frequency > 0:
        buzzer.freq(int(frequency))
        buzzer.duty_u16(1000)
        time.sleep_ms(duration_ms)
        buzzer.duty_u16(0)

def play_tune(tune):
    for note, duration in tune:
        if note in NOTES:
            play_sound(NOTES[note], duration)
            time.sleep_ms(10)

def check_qwst_pad():
    try:
        devices = i2c.scan()
        if 0x21 in devices:
            port0 = i2c.readfrom_mem(0x21, 0x00, 1)[0]
            port1 = i2c.readfrom_mem(0x21, 0x01, 1)[0]
            return {
                'y': not bool(port1 & 0x20),
                'a': not bool(port1 & 0x40)
            }
        return None
    except Exception as e:
        print(f"Qw/ST Pad error: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    try:
        print("Initializing game...")
        game = Game()
        print("Running game loop...")
        game.run()
    except (KeyboardInterrupt, Exception) as e:
        print(f"Exiting game: {e}")
        buzzer.duty_u16(0)
        led.set_rgb(0, 0, 0)
        display.set_pen(BLACK)
        display.clear()
        display.update()



