"""
Fluffbert's Frozen Dream - A Mayan Ice Cream Adventure
For Pimoroni Pico Plus 2 W with Pico Display Pack 2.8" and Qw/ST Pad.

Copyright (c) 2025-2026 Ilya Titov (https://webboggles.com). PolyForm Noncommercial 1.0.0, see LICENSE.md.
"""

__version__ = "0.5.0"

import time
import gc
import math
import random
from machine import Pin, I2C, PWM
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED, Button
from pimoroni_i2c import PimoroniI2C

# Display setup
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(1.0)  # Set backlight to max brightness
display.set_font("bitmap8")  # Set font for text rendering
WIDTH, HEIGHT = display.get_bounds()  # 320x240

# Hardware setup
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# RGB LED for Pico Display Pack 2.8"
led = RGBLED(26, 27, 28)

# I2C setup for Qw/ST Pad controller
i2c = PimoroniI2C(sda=4, scl=5)

# Buzzer setup (using GPIO 6 for piezo)
buzzer = PWM(Pin(6))
buzzer.duty_u16(0)

# Game constants
MOVE_SPEED = 0.3
SPRITE_SIZE = 16

# Tile map constants
TILE_WIDTH = 32
TILE_HEIGHT = 16
MAP_WIDTH = 25  # In tiles
MAP_HEIGHT = 25 # In tiles

# Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
SKY_BLUE = display.create_pen(135, 206, 235)
GROUND_BROWN = display.create_pen(139, 69, 19)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
YELLOW = display.create_pen(255, 255, 0)
PURPLE = display.create_pen(128, 0, 128)
PINK = display.create_pen(255, 192, 203)

# Note frequencies for tunes
NOTES = {
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 988,
}

# Nyan/Zelda-style tunes (note, duration_ms)
TUNE_SUCCESS = [('G4', 50), ('A4', 50), ('B4', 50), ('C5', 150)] # Zelda "item get" style
TUNE_COLLECT = [('C5', 50), ('E5', 80)] # Quick, happy blip
TUNE_INTERACT = [('E4', 60), ('G4', 100)] # Simple interaction chime

# Sound frequencies (Nyan Cat inspired)
SOUND_JUMP = 440
SOUND_COLLECT = 880
SOUND_MENU = 330
SOUND_HURT = 220
SOUND_SUCCESS = 1047

# Quest states
class QuestState:
    NOT_STARTED = 0
    ACTIVE = 1
    COMPLETED = 2

class Quest:
    def __init__(self, id, name, description, objectives):
        self.id = id
        self.name = name
        self.description = description
        self.objectives = objectives  # List of objective strings
        self.state = QuestState.NOT_STARTED
        self.current_objective = 0
        self.rewards = {'xp': 0, 'coins': 0, 'items': []}
    
    def start(self):
        self.state = QuestState.ACTIVE
        
    def complete_objective(self):
        self.current_objective += 1
        if self.current_objective >= len(self.objectives):
            self.state = QuestState.COMPLETED
            return True
        return False
    
    def is_active(self):
        return self.state == QuestState.ACTIVE
    
    def is_completed(self):
        return self.state == QuestState.COMPLETED

# Game state
class GameState:
    MENU = 0
    PLAYING = 1
    DIALOGUE = 2
    INVENTORY = 3
    MAP = 4
    QUEST = 5
    CHARACTER = 6
    PAUSE_MENU = 7
    WORLD_MAP = 8

class Player:
    def __init__(self):
        self.x = 12  # Starting tile x (center of smaller map)
        self.y = 12  # Starting tile y (center of smaller map)
        self.vx = 0
        self.vy = 0
        self.health = 100
        self.coins = 0
        self.ingredients = []
        self.level = 1
        self.xp = 0
        self.charm = 1
        self.bravery = 1
        self.cleverness = 1
        self.attack_damage = 10
        self.attack_cooldown = 0
        
    def gain_xp(self, amount):
        self.xp += amount
        # Check for level up (100 XP per level)
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1
            self.health = min(100, self.health + 20)  # Heal on level up
            return True  # Leveled up
        return False
        
    def update(self):
        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy
        
        # Map boundaries
        self.x = max(0, min(MAP_WIDTH - 1, self.x))
        self.y = max(0, min(MAP_HEIGHT - 1, self.y))
        
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
    def attack(self):
        """Attack nearby enemies"""
        if self.attack_cooldown > 0:
            return False
            
        attacked = False
        if hasattr(self, 'game_ref'):
            for enemy in self.game_ref.enemies:
                if not enemy.defeated:
                    dx = abs(enemy.x - self.x)
                    dy = abs(enemy.y - self.y)
                    if dx <= 1.5 and dy <= 1.5:  # Attack range
                        if enemy.take_damage(self.attack_damage):
                            # Enemy defeated!
                            self.game_ref.player.gain_xp(10)
                            self.game_ref.player.coins += 5
                            play_tune(TUNE_SUCCESS)
                        else:
                            play_sound(SOUND_HURT, 50)
                        attacked = True
                        self.attack_cooldown = 30  # 0.5 seconds at 60fps
                        break
        return attacked
        
    def interact(self):
        """Interact with nearby objects or NPCs"""
        # Check for nearby interactive objects in the game
        if hasattr(self, 'game_ref'):
            for obj in self.game_ref.interactive_objects:
                # Check distance in grid units
                dx = abs(obj['x'] - self.x)
                dy = abs(obj['y'] - self.y)
                if dx <= 1 and dy <= 1:  # If adjacent or on the same tile
                    if obj['type'] == 'sign':
                        self.game_ref.start_dialogue('sign', obj['text'])
                        play_tune(TUNE_INTERACT)
                    elif obj['type'] == 'chest':
                        if obj.get('opened', False) == False:
                            obj['opened'] = True
                            if obj.get('contains') == 'vanilla_essence':
                                self.ingredients.append('Vanilla Essence')
                                self.game_ref.start_dialogue('chest', "You found Vanilla Essence! The first ingredient!")
                                if 'vanilla_quest' in self.game_ref.active_quests:
                                    self.game_ref.complete_quest_objective('vanilla_quest')
                            else:
                                self.coins += 10
                                self.game_ref.start_dialogue('chest', "You found 10 coins!")
                            play_tune(TUNE_SUCCESS)
                        else:
                            self.game_ref.start_dialogue('chest', "The chest is empty.")
                            play_tune(TUNE_INTERACT)
                    elif obj['type'] == 'npc':
                        if 'dialogue_id' in obj:
                            self.game_ref.start_dialogue(obj['dialogue_id'], obj['name'])
                            play_tune(TUNE_INTERACT)
                    elif obj['type'] == 'travel_point':
                        self.game_ref.state = GameState.WORLD_MAP
                        play_tune(TUNE_SUCCESS)
                    return # Interact with the first object found
        
        print(f"Fluffbert tries to interact at ({self.player.x:.0f}, {self.player.y:.0f}) but finds nothing nearby")
        
    def draw(self, display, screen_x, screen_y):
        # Draw Fluffbert as a detailed labubu-style character
        color = PURPLE
        display.set_pen(color)
        
        # Character dimensions
        head_size = SPRITE_SIZE // 2  # Smaller head
        body_size = int(SPRITE_SIZE * 0.6)  # Body slightly larger than head
        ear_width = 6
        ear_height = 8
        arm_width = 3
        arm_height = 8
        foot_width = 6
        foot_height = 4
        
        # Body positions
        head_x = int(screen_x)
        head_y = int(screen_y - SPRITE_SIZE // 3)  # Head at top
        body_x = int(screen_x)
        body_y = int(screen_y + SPRITE_SIZE // 4)  # Body below head
        
        # Draw vertical oval ears at top of head (2px apart)
        display.set_pen(color)
        left_ear_x = head_x - 1 - ear_width//2  # 2px total gap (1px from center each side)
        right_ear_x = head_x + 1 + ear_width//2  # 2px total gap (1px from center each side)
        ear_y = head_y - head_size // 2 - 2
        # Draw ears as proper vertical ovals
        for dy in range(-ear_height//2, ear_height//2 + 1):
            # Create oval shape by varying width based on distance from center
            oval_width = int(ear_width * math.sqrt(1 - (dy / (ear_height//2))**2)) if ear_height//2 > 0 else ear_width
            oval_width = max(1, oval_width)  # Ensure at least 1 pixel width
            display.rectangle(left_ear_x - oval_width//2, ear_y + dy, oval_width, 1)
            display.rectangle(right_ear_x - oval_width//2, ear_y + dy, oval_width, 1)
        
        # Draw oval arms to the sides (moved down)
        left_arm_x = head_x - head_size - 2
        right_arm_x = head_x + head_size + 2
        arm_y = body_y - body_size // 3  # Moved down to upper body area
        display.rectangle(left_arm_x - arm_width//2, arm_y - arm_height//2, arm_width, arm_height)
        display.rectangle(right_arm_x - arm_width//2, arm_y - arm_height//2, arm_width, arm_height)
        
        # Draw oval feet at the bottom (2px gap between legs)
        left_foot_x = body_x - 1 - foot_width//2  # 2px total gap (1px from center each side)
        right_foot_x = body_x + 1 + foot_width//2  # 2px total gap (1px from center each side)
        foot_y = body_y + body_size // 2 + 8  # Moved further down from body
        display.rectangle(left_foot_x - foot_width//2, foot_y - foot_height//2, foot_width, foot_height)
        display.rectangle(right_foot_x - foot_width//2, foot_y - foot_height//2, foot_width, foot_height)
        
        # Draw head (smaller circle)
        display.circle(head_x, head_y, head_size)
        
        # Draw body circle below head
        display.circle(body_x, body_y, body_size)
        
        # Eyes on the head
        eye_y = head_y - head_size // 4
        eye_x1 = head_x - head_size // 3
        eye_x2 = head_x + head_size // 3
        
        display.set_pen(WHITE)
        display.circle(eye_x1, eye_y, 2)  # Smaller eyes for smaller head
        display.circle(eye_x2, eye_y, 2)
            
        # Pupils (looking forward)
        display.set_pen(BLACK)
        display.circle(eye_x1, eye_y, 1)
        display.circle(eye_x2, eye_y, 1)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 30
        self.max_health = 30
        self.damage = 5
        self.defeated = False
        self.respawn_timer = 0

    def update(self, game):
        # Enemies are now static - no movement animation
        # But they can respawn
        if self.defeated:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.defeated = False
                self.health = self.max_health
        pass

    def take_damage(self, amount):
        if not self.defeated:
            self.health -= amount
            if self.health <= 0:
                self.defeated = True
                self.respawn_timer = 300  # 5 seconds at 60fps
                return True  # Enemy defeated
        return False

    def draw(self, display, screen_x, screen_y):
        if not self.defeated:
            # Draw a simple red circle for the enemy
            display.set_pen(RED)
            display.circle(int(screen_x), int(screen_y), SPRITE_SIZE // 2)
            
            # Draw health bar
            if self.health < self.max_health:
                bar_width = 20
                bar_height = 3
                display.set_pen(BLACK)
                display.rectangle(int(screen_x) - bar_width//2, int(screen_y) - SPRITE_SIZE, bar_width, bar_height)
                display.set_pen(GREEN)
                health_width = int((self.health / self.max_health) * (bar_width - 2))
                display.rectangle(int(screen_x) - bar_width//2 + 1, int(screen_y) - SPRITE_SIZE + 1, health_width, bar_height - 2)

class Game:
    def __init__(self):
        self.state = GameState.MENU
        self.player = Player()
        self.player.game_ref = self # Pass a reference to the game object
        self.camera_x = 0
        self.camera_y = 0
        
        self.collectibles = []
        self.enemies = []
        self.dialogue_options = []
        self.selected_option = 0
        self.current_area = "Sweaty Palms"
        self.frame_count = 0
        self.last_button_press = 0  # Add button debounce timer
        
        # Enhanced dialogue system
        self.current_dialogue = None
        self.dialogue_speaker = ""
        self.dialogue_text = ""
        self.dialogue_choices = []
        self.dialogue_callback = None
        self.dialogue_start_time = 0  # Track when dialogue started
        
        # World Map Data
        self.locations = {
            'Sweaty Palms': {'x': 50, 'y': 100, 'unlocked': True},
            'Vanilla Valley': {'x': 150, 'y': 80, 'unlocked': False},
            'Misty Meadows': {'x': 250, 'y': 120, 'unlocked': False},
        }
        self.selected_location_index = 0
        
        # Quest System
        self.quests = {}
        self.init_quests()
        self.active_quests = []
        
        # Map Data
        self.map_database = {
            'Sweaty Palms': self._generate_sweaty_palms_map(),
            'Vanilla Valley': self._generate_vanilla_valley_map(),
        }
        self.map_data = self.map_database[self.current_area]
        
        # Initialize empty objects list - will be populated by load_location_objects
        self.interactive_objects = []
        
        # Initialize collectibles and enemies
        self.spawn_collectibles()
        self.spawn_enemies()
        self.load_location_objects()
        
    def load_location_objects(self):
        """Load objects specific to the current location"""
        # Clear all objects
        self.interactive_objects = []
        
        if self.current_area == "Sweaty Palms":
            # Sweaty Palms objects
            self.interactive_objects = [
                {'x': 20, 'y': 20, 'type': 'sign', 'text': 'Welcome to Sweaty Palms!'},
                {'x': 18, 'y': 10, 'type': 'chest', 'contains': 'coins', 'opened': False},
                {'x': 10, 'y': 18, 'type': 'npc', 'name': 'Pip the Parrot', 'dialogue_id': 'pip_intro'},
                {'x': 15, 'y': 15, 'type': 'npc', 'name': 'Miguel the Mouse', 'dialogue_id': 'miguel_shop'},
                {'x': 10, 'y': 10, 'type': 'npc', 'name': 'Abuela Howler', 'dialogue_id': 'abuela_wisdom'},
                {'x': 22, 'y': 12, 'type': 'travel_point', 'destination': 'Vanilla Valley'}
            ]
        elif self.current_area == "Vanilla Valley":
            # Vanilla Valley objects
            self.interactive_objects = [
                {'x': 12, 'y': 20, 'type': 'sign', 'text': 'Welcome to Vanilla Valley!'},
                {'x': 15, 'y': 12, 'type': 'npc', 'name': 'Luna the Llama', 'dialogue_id': 'luna_intro'},
                {'x': 20, 'y': 8, 'type': 'chest', 'contains': 'vanilla_essence', 'opened': False},
                {'x': 12, 'y': 5, 'type': 'npc', 'name': 'Grumposaur', 'dialogue_id': 'grumposaur_boss'},
                {'x': 5, 'y': 12, 'type': 'travel_point', 'destination': 'Sweaty Palms'}
            ]
            
        # Respawn collectibles and enemies for the new area
        self.collectibles = []
        self.enemies = []
        self.spawn_collectibles()
        self.spawn_enemies()
        
    def init_quests(self):
        """Initialize all game quests"""
        # Main quest line
        self.quests['find_abuela'] = Quest(
            'find_abuela',
            'Find Abuela Howler',
            'The wise elder knows about the Frozen Cloud Treat',
            ['Talk to villagers about Abuela', 'Find the Great Tree', 'Speak with Abuela Howler']
        )
        self.quests['find_abuela'].rewards = {'xp': 50, 'coins': 10}
        
        self.quests['vanilla_quest'] = Quest(
            'vanilla_quest',
            'The Vanilla Valley Venture',
            'Find the Sacred Vanilla Orchids in Vanilla Valley',
            ['Travel to Vanilla Valley', 'Find the Temple of Tasty Treats', 'Defeat Grumposaur', 'Collect Vanilla Orchid Essence']
        )
        self.quests['vanilla_quest'].rewards = {'xp': 100, 'coins': 25, 'items': ['Vanilla Essence']}
        
        # Side quests
        self.quests['giggle_gang'] = Quest(
            'giggle_gang',
            'Save the Giggle Gang',
            'Three capybara children are stuck in sticky tree sap',
            ['Find the stuck capybaras', 'Defeat 3 Melty Slimes', 'Free the children']
        )
        self.quests['giggle_gang'].rewards = {'xp': 30, 'coins': 15}
        
    def start_quest(self, quest_id):
        """Start a quest if it exists and isn't already active"""
        if quest_id in self.quests and self.quests[quest_id].state == QuestState.NOT_STARTED:
            self.quests[quest_id].start()
            self.active_quests.append(quest_id)
            return True
        return False
        
    def complete_quest_objective(self, quest_id):
        """Complete the current objective of a quest"""
        if quest_id in self.quests and self.quests[quest_id].is_active():
            if self.quests[quest_id].complete_objective():
                # Quest completed!
                rewards = self.quests[quest_id].rewards
                self.player.coins += rewards.get('coins', 0)
                if self.player.gain_xp(rewards.get('xp', 0)):
                    # Player leveled up!
                    play_tune(TUNE_SUCCESS)
                for item in rewards.get('items', []):
                    self.player.ingredients.append(item)
                self.active_quests.remove(quest_id)
                return True
        return False

    def _generate_sweaty_palms_map(self):
        """Generates the map for Sweaty Palms (island shape)"""
        map_data = []
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                # Create a simple island
                distance_to_center = math.sqrt((x - MAP_WIDTH/2)**2 + (y - MAP_HEIGHT/2)**2)
                if distance_to_center < 10:  # Halved radius to match smaller map
                    tile = 1 # Grass
                else:
                    tile = 0 # Water
                row.append(tile)
            map_data.append(row)
        return map_data

    def _generate_vanilla_valley_map(self):
        """Generates the map for Vanilla Valley (valley shape)"""
        map_data = []
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                # Create a valley with water on the sides
                if x > 4 and x < MAP_WIDTH - 5:
                    tile = 1 # Grass
                else:
                    tile = 0 # Water
                row.append(tile)
            map_data.append(row)
        return map_data

    def spawn_collectibles(self):
        # Spawn some coins and ingredients on valid tiles
        for i in range(20):
            x = random.randint(0, MAP_WIDTH - 1)
            y = random.randint(0, MAP_HEIGHT - 1)
            if self.map_data[y][x] != 0: # Ensure it's not water
                self.collectibles.append({
                    'x': x, 'y': y,
                    'type': 'coin' if random.random() < 0.7 else 'ingredient',
                    'collected': False
                })
            
    def spawn_enemies(self):
        """Spawns enemies on the map"""
        for i in range(3): # Spawn 3 slimes instead of 5
            x = random.randint(5, MAP_WIDTH - 5)  # Adjusted for smaller map
            y = random.randint(5, MAP_HEIGHT - 5)  # Adjusted for smaller map
            # Ensure enemy doesn't spawn in water
            if self.map_data[y][x] != 0:
                self.enemies.append(Enemy(x, y))

    def to_iso(self, x, y):
        """Converts map coordinates to isometric screen coordinates"""
        iso_x = (x - y) * (TILE_WIDTH / 2)
        iso_y = (x + y) * (TILE_HEIGHT / 2)
        return iso_x, iso_y

    def update(self):
        if self.state == GameState.PLAYING:
            self.player.update()
            
            # Update enemies
            for enemy in self.enemies:
                enemy.update(self)

            # Update camera to follow player
            target_camera_x, target_camera_y = self.to_iso(self.player.x, self.player.y)
            self.camera_x += (target_camera_x - self.camera_x) * 0.1
            self.camera_y += (target_camera_y - self.camera_y) * 0.1

            # Check for player-enemy collision
            for enemy in self.enemies:
                dx = self.player.x - enemy.x
                dy = self.player.y - enemy.y
                if math.sqrt(dx*dx + dy*dy) < 1.0: # If tiles are close
                    self.player.health -= 1
                    if self.player.health <= 0:
                        self.state = GameState.MENU # Game Over, back to menu
                        
            # Check collectible collisions
            for item in self.collectibles:
                if not item['collected']:
                    # Check distance in grid units for simplicity in isometric view
                    dx = item['x'] - self.player.x
                    dy = item['y'] - self.player.y
                    if abs(dx) < 1.0 and abs(dy) < 1.0: # If on the same tile
                        item['collected'] = True
                        if item['type'] == 'coin':
                            self.player.coins += 1
                            play_tune(TUNE_COLLECT)
                        else:
                            self.player.ingredients.append('Vanilla')
                            play_tune(TUNE_SUCCESS)
                            
        self.frame_count += 1
        
    def can_press_button(self):
        """Check if enough time has passed since last button press"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_button_press) > 2000:  # 2 second input block
            self.last_button_press = current_time
            return True
        return False
    
    def can_show_options(self):
        """Check if enough time has passed since dialogue started to show options"""
        current_time = time.ticks_ms()
        return time.ticks_diff(current_time, self.dialogue_start_time) > 2000
    
    def start_dialogue(self, dialogue_id, speaker_name=""):
        """Start a dialogue sequence"""
        self.dialogue_speaker = speaker_name
        self.current_dialogue = dialogue_id
        self.state = GameState.DIALOGUE
        self.dialogue_start_time = time.ticks_ms()  # Record when dialogue started
        
        # Load dialogue based on ID
        if dialogue_id == 'pip_intro':
            self.dialogue_text = "Squawk! Hello there, fluffy friend! I'm Pip the Parrot. I've been waiting for someone brave enough to help us!"
            self.dialogue_choices = [
                "Help with what?",
                "I'm not brave!",
                "Nice feathers!",
                "Got any ice cream?"
            ]
            self.dialogue_callback = self.handle_pip_intro_response
        elif dialogue_id == 'pip_quest':
            self.dialogue_text = "The village has been sweltering for months! Legend says there's a way to make something called 'ice cream' that can cool everyone down!"
            self.dialogue_choices = [
                "Tell me more!",
                "Sounds impossible",
                "Where do I start?",
                "I'll help you!"
            ]
            self.dialogue_callback = self.handle_pip_quest_response
        elif dialogue_id == 'miguel_shop':
            self.dialogue_text = "¡Hola, amigo! Welcome to Miguel's Marvellous Merchandise! Everything's mice-priced! Need supplies for your adventure?"
            self.dialogue_choices = [
                "What do you sell?",
                "That's a great pun!",
                "Any ice ingredients?",
                "Just browsing!"
            ]
            self.dialogue_callback = self.handle_miguel_shop_response
        elif dialogue_id == 'abuela_wisdom':
            self.dialogue_text = "Ah, little one... You seek the ancient knowledge of the Frozen Cloud Treat, don't you? I can see it in your fuzzy little eyes."
            self.dialogue_choices = [
                "Yes, please help!",
                "Frozen Cloud Treat?",
                "How did you know?",
                "I'm just exploring"
            ]
            self.dialogue_callback = self.handle_abuela_wisdom_response
        else:
            # Default dialogue
            self.dialogue_text = "Hello, Fluffbert!"
            self.dialogue_choices = ["Hello!", "Goodbye", "Who are you?", "Nice day!"]
            self.dialogue_callback = self.handle_default_response
            
        # Vanilla Valley dialogues
        if dialogue_id == 'luna_intro':
            self.dialogue_text = "¡Hola! I'm Luna the Llama! You look like you could use some help jumping around these vanilla fields!"
            self.dialogue_choices = [
                "I'd love to learn!",
                "Nice to meet you!",
                "Have you seen orchids?",
                "Maybe later"
            ]
            self.dialogue_callback = self.handle_luna_response
        elif dialogue_id == 'grumposaur_boss':
            self.dialogue_text = "GRRRR... Who dares disturb my nap? I haven't slept well in AGES because of this heat!"
            self.dialogue_choices = [
                "Sorry to wake you!",
                "I need vanilla orchids",
                "Want some ice cream?",
                "Fight me!"
            ]
            self.dialogue_callback = self.handle_grumposaur_response
    
    def handle_luna_response(self, choice_index):
        """Handle Luna the Llama's responses"""
        if choice_index == 0:  # I'd love to learn!
            self.dialogue_text = "Wonderful! The secret is to believe you can fly! Well, sort of. Here, try this cloud milk!"
            self.dialogue_choices = ["*drinks milk*", "Is it safe?", "Thank you!", "Cloud milk?"]
            self.player.health = min(100, self.player.health + 20)  # Heal player
            self.dialogue_callback = lambda x: self.end_dialogue()
        elif choice_index == 2:  # Have you seen orchids?
            self.dialogue_text = "Oh yes! The singing orchids are in the temple, but Grumposaur guards the entrance. He's very grumpy!"
            self.dialogue_choices = ["Where's the temple?", "Why is he grumpy?", "I'll handle him!", "Thanks for the info!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
        else:
            self.end_dialogue()
            
    def handle_grumposaur_response(self, choice_index):
        """Handle Grumposaur's responses"""
        if choice_index == 2:  # Want some ice cream?
            self.dialogue_text = "Ice... cream? What's that? Something cold and sweet? That sounds... AMAZING! But it doesn't exist!"
            self.dialogue_choices = ["I'm making it!", "Help me and you'll get some!", "It will exist soon!", "Trust me!"]
            self.dialogue_callback = self.handle_grumposaur_convinced
        elif choice_index == 3:  # Fight me!
            self.dialogue_text = "FINE! But I'm too tired to move. If you can make me laugh, I'll let you pass. Deal?"
            self.dialogue_choices = ["*tickle attack*", "Why did the dino cross the road?", "*silly dance*", "Knock knock!"]
            self.dialogue_callback = self.handle_grumposaur_laugh
        else:
            self.dialogue_text = "Zzz... Go away... too hot... too tired..."
            self.dialogue_choices = ["Sorry!", "I'll come back", "Please?", "..."]
            self.dialogue_callback = lambda x: self.end_dialogue()
            
    def handle_grumposaur_convinced(self, choice_index):
        """Handle Grumposaur being convinced about ice cream"""
        self.dialogue_text = "If you really can make this 'ice cream', I'll not only let you pass, I'll be your friend forever!"
        self.dialogue_choices = ["It's a deal!", "Friends forever!", "You won't regret it!", "Let's shake on it!"]
        if 'vanilla_quest' in self.active_quests:
            self.complete_quest_objective('vanilla_quest')  # Defeat Grumposaur objective
        self.dialogue_callback = lambda x: self.end_dialogue()
        
    def handle_grumposaur_laugh(self, choice_index):
        """Handle making Grumposaur laugh"""
        self.dialogue_text = "BAHAHAHA! That's the funniest thing I've seen in centuries! Okay, okay, you can pass!"
        self.dialogue_choices = ["Thanks!", "You have a nice laugh!", "See you later!", "Want to hear another?"]
        if 'vanilla_quest' in self.active_quests:
            self.complete_quest_objective('vanilla_quest')  # Defeat Grumposaur objective
        self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_pip_intro_response(self, choice_index):
        """Handle Pip's intro dialogue responses"""
        if choice_index == 0:  # Help with what?
            self.start_quest('find_abuela')  # Start the main quest
            self.start_dialogue('pip_quest', 'Pip the Parrot')
        elif choice_index == 1:  # I'm not brave!
            self.dialogue_text = "Nonsense! You're the bravest labubu I've ever seen! Plus, you have such adorable paws!"
            self.dialogue_choices = ["Thanks!", "Really?", "What's a labubu?", "Let's go!"]
            self.dialogue_callback = self.handle_pip_encouragement
        elif choice_index == 2:  # Nice feathers!
            self.dialogue_text = "Why thank you! I preen them every morning. Now, about that ice cream quest..."
            self.dialogue_choices = ["Ice cream?", "Tell me more", "Maybe later", "I'm listening"]
            self.dialogue_callback = lambda x: self.start_dialogue('pip_quest', 'Pip the Parrot')
        elif choice_index == 3:  # Got any ice cream?
            self.dialogue_text = "That's exactly the problem! Nobody has ice cream because nobody knows how to make it!"
            self.dialogue_choices = ["I'll learn!", "Too bad", "Teach me!", "Let's find out!"]
            self.dialogue_callback = lambda x: self.start_dialogue('pip_quest', 'Pip the Parrot')
    
    def handle_pip_quest_response(self, choice_index):
        """Handle Pip's quest dialogue responses"""
        if choice_index == 0 or choice_index == 2:  # Tell me more / Where do I start
            self.dialogue_text = "Abuela Howler in the Great Tree knows the ancient legends. Find her first!"
            self.dialogue_choices = ["Got it!", "Where's the tree?", "Who's Abuela?", "Thanks Pip!"]
            self.dialogue_callback = self.handle_pip_directions
        elif choice_index == 1:  # Sounds impossible
            self.dialogue_text = "Nothing's impossible for a determined labubu! Besides, I'll help you every step of the way!"
            self.dialogue_choices = ["Okay, let's try", "I'm scared", "You're right!", "Together we can!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
        elif choice_index == 3:  # I'll help you!
            self.dialogue_text = "Wonderful! You're going to be the hero of Sweaty Palms Village!"
            self.dialogue_choices = ["I hope so!", "No pressure...", "Let's do this!", "Thanks for believing!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_pip_encouragement(self, choice_index):
        """Handle Pip's encouragement responses"""
        self.dialogue_text = "That's the spirit! Now, ready to save the village with the power of ice cream?"
        self.dialogue_choices = ["Yes!", "Maybe...", "Ice cream power!", "Let's go!"]
        self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_pip_directions(self, choice_index):
        """Handle Pip's directions responses"""
        if choice_index == 1:  # Where's the tree?
            self.dialogue_text = "The Great Tree is the biggest tree in the village - you can't miss it! Look for the rope ladder."
            self.dialogue_choices = ["Thanks!", "Got it!", "See you later!", "Wish me luck!"]
        else:
            self.dialogue_text = "Good luck, Fluffbert! I believe in you!"
            self.dialogue_choices = ["Thanks!", "See you soon!", "Wish me luck!", "Ice cream here I come!"]
        self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_miguel_shop_response(self, choice_index):
        """Handle Miguel's shop dialogue responses"""
        if choice_index == 0:  # What do you sell?
            self.dialogue_text = "I have ropes, torches, healing berries, and the finest cheese in all of Sweaty Palms! Perfect for adventurers like you!"
            self.dialogue_choices = ["I'll take some rope", "Got any maps?", "Healing berries?", "Thanks, Miguel!"]
            self.dialogue_callback = self.handle_miguel_items
        elif choice_index == 1:  # That's a great pun!
            self.dialogue_text = "¡Gracias! I have a million of them! Why don't mice ever pay full price? Because they're always looking for a squeak-y deal!"
            self.dialogue_choices = ["Haha!", "Another one!", "You're funny!", "Got any items?"]
            self.dialogue_callback = lambda x: self.handle_miguel_shop_response(0) if x == 3 else self.end_dialogue()
        elif choice_index == 2:  # Any ice ingredients?
            self.dialogue_text = "Ice? In this heat? ¡Imposible! But I hear the Cloud Cows in Misty Moo Meadows have something cold... very cold!"
            self.dialogue_choices = ["Cloud Cows?", "Where's that?", "Interesting...", "Thanks for the tip!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
        elif choice_index == 3:  # Just browsing!
            self.dialogue_text = "¡Por supuesto! Browse all you want, amigo! When you're ready to buy, Miguel's got the best deals in town!"
            self.dialogue_choices = ["Thanks!", "I'll be back!", "Nice shop!", "Goodbye!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_miguel_items(self, choice_index):
        """Handle Miguel's item selection"""
        if choice_index == 0:  # I'll take some rope
            self.player.coins = max(0, self.player.coins - 5)
            self.dialogue_text = "¡Excelente! Here's your rope! That'll be 5 coins. Perfect for climbing and swinging!"
            self.dialogue_choices = ["Thanks!", "Good deal!", "Very useful!", "Goodbye!"]
        elif choice_index == 1:  # Got any maps?
            self.dialogue_text = "Ah, sí! I have this old map of the surrounding areas. Shows Vanilla Valley and the Misty Moo Meadows!"
            self.dialogue_choices = ["I'll take it!", "How much?", "Looks old...", "Maybe later"]
        elif choice_index == 2:  # Healing berries?
            self.dialogue_text = "These purple berries restore health! Very popular with adventurers. Only 3 coins each!"
            self.dialogue_choices = ["I'll take some!", "Good price!", "What do they taste like?", "Not now"]
        else:
            self.dialogue_text = "¡De nada! Come back anytime, amigo! Miguel's always here to help!"
            self.dialogue_choices = ["Will do!", "Thanks!", "See you later!", "Goodbye!"]
        self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_abuela_wisdom_response(self, choice_index):
        """Handle Abuela's wisdom dialogue responses"""
        if choice_index == 0:  # Yes, please help!
            if 'find_abuela' in self.active_quests:
                self.complete_quest_objective('find_abuela')  # Complete Abuela quest
            self.dialogue_text = "Good, good... The legend speaks of four sacred ingredients scattered across the land. The first lies in Vanilla Valley..."
            self.dialogue_choices = ["Four ingredients?", "Vanilla Valley?", "Tell me more!", "I'm ready!"]
            self.dialogue_callback = self.handle_abuela_legend
        elif choice_index == 1:  # Frozen Cloud Treat?
            self.dialogue_text = "That's what we call it now, child. But the ancient name was... ice cream. A magical treat that brings joy and coolness to all who taste it."
            self.dialogue_choices = ["Ice cream!", "Sounds amazing!", "How is it made?", "I want to learn!"]
            self.dialogue_callback = lambda x: self.handle_abuela_wisdom_response(0)
        elif choice_index == 2:  # How did you know?
            self.dialogue_text = "These old eyes have seen many things, little one. I can sense the destiny that flows through your fuzzy paws!"
            self.dialogue_choices = ["Destiny?", "That's amazing!", "What do you see?", "I'm just fluffy!"]
            self.dialogue_callback = lambda x: self.handle_abuela_wisdom_response(0)
        elif choice_index == 3:  # I'm just exploring
            self.dialogue_text = "Ah, but exploration often leads to the greatest discoveries! Perhaps you'll find what you're looking for after all..."
            self.dialogue_choices = ["Maybe you're right", "I'll keep exploring", "Thanks, Abuela!", "Goodbye!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_abuela_legend(self, choice_index):
        """Handle Abuela's legend explanation"""
        if choice_index == 0:  # Four ingredients?
            self.dialogue_text = "Vanilla from the singing orchids, milk from the Cloud Cows, sugar from the crystal shores, and honey from the sky hives."
            self.dialogue_choices = ["Singing orchids?", "Cloud Cows?", "Crystal shores?", "Sky hives?"]
            self.dialogue_callback = self.handle_abuela_ingredients
        elif choice_index == 1:  # Vanilla Valley?
            self.dialogue_text = "A beautiful, sunny valley where the sweetest flowers grow. It is said the first ingredient is protected there by a gentle guardian."
            self.dialogue_choices = ["A guardian?", "I'll go there!", "Where is it?", "Sounds lovely!"]
            self.locations['Vanilla Valley']['unlocked'] = True # Unlock the location
            self.start_quest('vanilla_quest')  # Start the Vanilla Valley quest
            self.dialogue_callback = lambda x: self.end_dialogue()
        else:
            self.dialogue_text = "The path will be long, little one. But I believe in you! Take this wisdom: kindness is stronger than any weapon."
            self.dialogue_choices = ["Thank you!", "I'll remember that", "Wise words!", "I won't let you down!"]
            self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_abuela_ingredients(self, choice_index):
        """Handle Abuela's ingredient explanations"""
        if choice_index == 0:  # Singing orchids?
            self.dialogue_text = "They sing when the wind blows through them. Their essence is the heart of any good ice cream!"
        elif choice_index == 1:  # Cloud Cows?
            self.dialogue_text = "Magical cows that float on clouds. Their milk is lighter than air and sweeter than dreams!"
        elif choice_index == 2:  # Crystal shores?
            self.dialogue_text = "Where the sugar waves crash against candy beaches. The crystals there are pure sweetness!"
        else:  # Sky hives?
            self.dialogue_text = "The bees that live in the clouds make the most golden honey. It never spoils and tastes like sunshine!"
        
        self.dialogue_choices = ["Amazing!", "I'll find them all!", "Thank you, Abuela!", "This is my quest!"]
        self.dialogue_callback = lambda x: self.end_dialogue()
    
    def handle_default_response(self, choice_index):
        """Handle generic dialogue responses"""
        self.end_dialogue()
    
    def end_dialogue(self):
        """End the current dialogue and return to game"""
        self.state = GameState.PLAYING
        self.current_dialogue = None
        self.dialogue_speaker = ""
        self.dialogue_text = ""
        self.dialogue_choices = []
        self.dialogue_callback = None
        self.dialogue_start_time = 0  # Reset dialogue start time
        
    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.DIALOGUE:
            self.draw_dialogue()
        elif self.state == GameState.INVENTORY:
            self.draw_inventory()
        elif self.state == GameState.MAP:
            self.draw_map()
        elif self.state == GameState.QUEST:
            self.draw_quest()
        elif self.state == GameState.CHARACTER:
            self.draw_character_screen()
        elif self.state == GameState.PAUSE_MENU:
            self.draw_pause_menu()
        elif self.state == GameState.WORLD_MAP:
            self.draw_world_map()
        else:
            # Debug: Unknown state
            display.set_pen(RED)
            display.clear()
            display.set_pen(WHITE)
            display.text(f"Unknown state: {self.state}", 10, 10, WIDTH, 2)
            
    def draw_menu(self):
        # Clear screen
        display.set_pen(SKY_BLUE)
        display.clear()
        
        # Title
        display.set_pen(WHITE)
        title = "Fluffbert's Frozen Dream"
        title_width = display.measure_text(title, 2)
        display.text(title, (WIDTH - title_width) // 2, 30, WIDTH, 2)
        
        # Menu options
        options = ["Start Game", "Continue", "Settings", "Credits"]
        for i, option in enumerate(options):
            color = YELLOW if i == self.selected_option else WHITE
            display.set_pen(color)
            display.text(option, 100, 80 + i * 30, WIDTH, 1)
            
        # Instructions
        display.set_pen(WHITE)
        display.text("A: Select  X/Y: Navigate", 50, 200, WIDTH, 1)
        
    def draw_game(self):
        # Clear screen with sky blue (or water color)
        display.set_pen(SKY_BLUE)
        display.clear()

        # Center the camera
        cam_x_offset = WIDTH / 2 - self.camera_x
        cam_y_offset = HEIGHT / 2 - self.camera_y

        # Draw the tile map
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                iso_x, iso_y = self.to_iso(x, y)
                screen_x = int(iso_x + cam_x_offset)
                screen_y = int(iso_y + cam_y_offset)

                # Only draw tiles that are on screen
                if -TILE_WIDTH < screen_x < WIDTH and -TILE_HEIGHT * 2 < screen_y < HEIGHT:
                    if tile == 1: # Grass
                        display.set_pen(GREEN)
                    else: # Water
                        display.set_pen(SKY_BLUE)
                    
                    # Draw diamond shape for isometric tile
                    points = [
                        (screen_x, screen_y + TILE_HEIGHT // 2),
                        (screen_x + TILE_WIDTH // 2, screen_y),
                        (screen_x + TILE_WIDTH, screen_y + TILE_HEIGHT // 2),
                        (screen_x + TILE_WIDTH // 2, screen_y + TILE_HEIGHT)
                    ]
                    display.polygon(points)

        # Draw objects/NPCs
        all_objects = self.interactive_objects + self.collectibles
        # Sort objects by y-position for correct draw order
        all_objects.sort(key=lambda obj: obj['y'])

        for obj in all_objects:
            if obj.get('collected', False): continue

            iso_x, iso_y = self.to_iso(obj['x'], obj['y'])
            screen_x = int(iso_x + cam_x_offset)
            screen_y = int(iso_y + cam_y_offset)

            # Culling
            if -TILE_WIDTH < screen_x < WIDTH and -TILE_HEIGHT * 2 < screen_y < HEIGHT:
                if 'type' in obj:
                    if obj['type'] == 'sign':
                        display.set_pen(GROUND_BROWN)
                        display.rectangle(screen_x, screen_y - 10, 10, 15)
                        display.set_pen(WHITE)
                        display.text("Sign", screen_x - 10, screen_y - 20, WIDTH, 1)
                    elif obj['type'] == 'chest':
                        display.set_pen(YELLOW)
                        display.rectangle(screen_x, screen_y, 15, 10)
                        display.set_pen(WHITE)
                        display.text("Chest", screen_x - 12, screen_y - 10, WIDTH, 1)
                    elif obj['type'] == 'npc':
                        self.draw_npc(obj, screen_x, screen_y)
                    elif obj['type'] == 'coin':
                        display.set_pen(YELLOW)
                        display.circle(screen_x, screen_y, 5)
                    elif obj['type'] == 'ingredient':
                        display.set_pen(PINK)
                        display.rectangle(screen_x - 5, screen_y - 5, 10, 10)
                    elif obj['type'] == 'travel_point':
                        display.set_pen(WHITE)
                        display.circle(screen_x, screen_y, 5)
                        display.text("Travel", screen_x - 10, screen_y - 15, WIDTH, 1)

        # Draw enemies
        for enemy in self.enemies:
            iso_x, iso_y = self.to_iso(enemy.x, enemy.y)
            screen_x = int(iso_x + cam_x_offset)
            screen_y = int(iso_y + cam_y_offset)
            if -TILE_WIDTH < screen_x < WIDTH and -TILE_HEIGHT * 2 < screen_y < HEIGHT:
                enemy.draw(display, screen_x, screen_y)

        # Draw player
        player_iso_x, player_iso_y = self.to_iso(self.player.x, self.player.y)
        self.player.draw(display, int(player_iso_x + cam_x_offset), int(player_iso_y + cam_y_offset))
        
        # Draw HUD
        self.draw_hud()
        
    def draw_npc(self, obj, screen_x, screen_y):
        # Draw different NPCs with unique appearances (static, no animation)
        if obj['name'] == 'Pip the Parrot':
            display.set_pen(GREEN)
            display.circle(screen_x, screen_y, 8)
            display.set_pen(WHITE)
            display.text("Pip", screen_x - 8, screen_y - 15, WIDTH, 1)
        elif obj['name'] == 'Miguel the Mouse':
            display.set_pen(display.create_pen(139, 69, 19))  # Brown
            display.circle(screen_x, screen_y, 6)
            display.set_pen(WHITE)
            display.text("Miguel", screen_x - 15, screen_y - 15, WIDTH, 1)
        elif obj['name'] == 'Abuela Howler':
            display.set_pen(display.create_pen(101, 67, 33))  # Dark brown
            display.circle(screen_x, screen_y, 10)
            display.set_pen(WHITE)
            display.text("Abuela", screen_x - 18, screen_y - 15, WIDTH, 1)
        else:
            display.set_pen(RED)
            display.circle(screen_x, screen_y, 8)
            display.set_pen(WHITE)
            display.text("???", screen_x - 8, screen_y - 15, WIDTH, 1)

    def draw_hud(self):
        # Health bar
        display.set_pen(BLACK)
        display.rectangle(10, 10, 102, 12)
        display.set_pen(RED)
        display.rectangle(11, 11, int(self.player.health), 10)
        
        # Coins
        display.set_pen(YELLOW)
        display.text(f"Coins: {self.player.coins}", 10, 25, WIDTH, 1)
        
        # Level and XP
        display.set_pen(PURPLE)
        display.text(f"Lv.{self.player.level}", 10, 40, WIDTH, 1)
        
        # Current area
        display.set_pen(WHITE)
        display.text(self.current_area, WIDTH - 150, 10, WIDTH, 1)
        
        # Current quest objective
        if self.active_quests:
            quest = self.quests[self.active_quests[0]]
            if quest.current_objective < len(quest.objectives):
                display.set_pen(display.create_pen(200, 200, 200))
                obj_text = quest.objectives[quest.current_objective]
                if len(obj_text) > 40:
                    obj_text = obj_text[:37] + "..."
                display.text(f"Quest: {obj_text}", 10, HEIGHT - 80, WIDTH, 1)
        
        # Button instructions
        display.set_pen(YELLOW)
        display.text("Y: Attack/Talk  A: Interact  B: Inventory", 10, HEIGHT - 25, WIDTH, 1)
        
        # Battery indicator (placeholder)
        display.set_pen(GREEN)
        display.rectangle(WIDTH - 40, 10, 30, 15)
        
    def draw_dialogue(self):
        # Draw game in background (dimmed)
        self.draw_game()
        
        # Dark overlay for dialogue focus
        display.set_pen(display.create_pen(0, 0, 0))  # Black overlay
        display.rectangle(0, 0, WIDTH, HEIGHT//3)  # Top third
        display.rectangle(0, HEIGHT - HEIGHT//3, WIDTH, HEIGHT//3)  # Bottom third
        
        # Main dialogue box
        display.set_pen(BLACK)
        display.rectangle(10, HEIGHT - 120, WIDTH - 20, 110)
        display.set_pen(WHITE)
        display.rectangle(12, HEIGHT - 118, WIDTH - 24, 106)
        
        # Speaker name
        if self.dialogue_speaker:
            display.set_pen(PURPLE)
            display.text(self.dialogue_speaker, 20, HEIGHT - 115, WIDTH - 40, 1)
        
        # Dialogue text (word wrap)
        display.set_pen(BLACK)
        text_lines = self.wrap_text(self.dialogue_text, WIDTH - 60)
        for i, line in enumerate(text_lines[:3]):  # Max 3 lines
            display.text(line, 20, HEIGHT - 100 + i * 12, WIDTH - 40, 1)
        
        # Choice buttons in 2x2 grid - XAYB order
        if self.can_show_options():
            button_labels = ['X', 'A', 'Y', 'B']
            for i, choice in enumerate(self.dialogue_choices):
                if i < 4:  # Max 4 choices
                    x = 20 + (i % 2) * 140
                    y = HEIGHT - 50 + (i // 2) * 20
                    
                    # Button background
                    display.set_pen(YELLOW)
                    display.rectangle(x - 2, y - 2, 12, 12)
                    
                    # Button label
                    display.set_pen(BLACK)
                    display.text(button_labels[i], x, y, WIDTH, 1)
                    
                    # Choice text
                    display.set_pen(BLACK)
                    choice_text = choice[:18] + "..." if len(choice) > 18 else choice
                    display.text(choice_text, x + 15, y, WIDTH, 1)
        else:
            # Show waiting message when options are not available
            display.set_pen(display.create_pen(128, 128, 128))  # Gray text
            display.text("Please wait...", 20, HEIGHT - 40, WIDTH, 1)
    
    def wrap_text(self, text, max_width):
        """Simple text wrapping"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if display.measure_text(test_line, 1) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
            
    def draw_inventory(self):
        display.set_pen(BLACK)
        display.clear()
        
        display.set_pen(WHITE)
        display.text("Inventory", 10, 10, WIDTH, 2)
        
        # Show player stats
        display.set_pen(WHITE)
        display.text(f"Coins: {self.player.coins}", 20, 50, WIDTH, 1)
        display.text(f"Health: {self.player.health}", 20, 70, WIDTH, 1)
        display.text(f"Level: {self.player.level}", 20, 90, WIDTH, 1)
        
        # Show ingredients
        display.text("Ingredients:", 20, 120, WIDTH, 1)
        y = 140
        if self.player.ingredients:
            for ingredient in self.player.ingredients:
                display.text(f"- {ingredient}", 30, y, WIDTH, 1)
                y += 20
        else:
            display.text("  None collected yet", 30, y, WIDTH, 1)
            
        # Instructions
        display.set_pen(YELLOW)
        display.text("B: Back to Game", 10, HEIGHT - 20, WIDTH, 1)
        
    def draw_map(self):
        display.set_pen(BLACK)
        display.clear()
        
        display.set_pen(WHITE)
        display.text("World Map", 10, 10, WIDTH, 2)
        
        # Simple map representation
        locations = [
            ("Sweaty Palms", 50, 100),
            ("Vanilla Valley", 150, 80),
            ("Misty Meadows", 250, 120),
            ("Machu Freeze-chu", 200, 40)
        ]
        
        for name, x, y in locations:
            display.set_pen(YELLOW if name == "Sweaty Palms" else WHITE)
            display.circle(x, y, 5)
            display.text(name, x - 30, y + 10, WIDTH, 1)
            
        display.text("B: Back", 10, HEIGHT - 20, WIDTH, 1)
        
    def draw_quest(self):
        display.set_pen(BLACK)
        display.clear()
        
        display.set_pen(WHITE)
        display.text("Quest Log", 10, 10, WIDTH, 2)
        
        y_pos = 40
        
        # Show active quests
        if self.active_quests:
            display.set_pen(YELLOW)
            display.text("Active Quests:", 20, y_pos, WIDTH, 1)
            y_pos += 20
            
            for quest_id in self.active_quests:
                quest = self.quests[quest_id]
                display.set_pen(WHITE)
                display.text(f"- {quest.name}", 30, y_pos, WIDTH, 1)
                y_pos += 15
                
                # Show current objective
                if quest.current_objective < len(quest.objectives):
                    display.set_pen(display.create_pen(200, 200, 200))  # Light gray
                    obj_text = quest.objectives[quest.current_objective]
                    if len(obj_text) > 35:
                        obj_text = obj_text[:32] + "..."
                    display.text(f"  > {obj_text}", 40, y_pos, WIDTH, 1)
                    y_pos += 20
                else:
                    y_pos += 15
        else:
            display.set_pen(display.create_pen(128, 128, 128))
            display.text("No active quests", 30, y_pos, WIDTH, 1)
            y_pos += 20
            
        # Show completed quests count
        completed_count = sum(1 for q in self.quests.values() if q.is_completed())
        display.set_pen(GREEN)
        display.text(f"Completed: {completed_count}", 20, y_pos + 20, WIDTH, 1)
        
        display.set_pen(YELLOW)
        display.text("B: Back", 10, HEIGHT - 20, WIDTH, 1)

    def draw_character_screen(self):
        display.set_pen(BLACK)
        display.clear()
        display.set_pen(WHITE)
        display.text("Character Screen", 10, 10, WIDTH, 2)
        
        # Player info
        display.set_pen(YELLOW)
        display.text(f"Level {self.player.level} Labubu", 20, 40, WIDTH, 1)
        
        # XP bar
        display.set_pen(WHITE)
        display.text(f"XP: {self.player.xp}/{self.player.level * 100}", 20, 60, WIDTH, 1)
        bar_width = 100
        bar_height = 10
        display.set_pen(BLACK)
        display.rectangle(20, 75, bar_width, bar_height)
        display.set_pen(PURPLE)
        xp_width = int((self.player.xp / (self.player.level * 100)) * (bar_width - 2))
        display.rectangle(21, 76, xp_width, bar_height - 2)
        
        # Stats
        display.set_pen(WHITE)
        display.text("Traits:", 20, 100, WIDTH, 1)
        display.text(f"Charm: {self.player.charm}", 30, 120, WIDTH, 1)
        display.text(f"Bravery: {self.player.bravery}", 30, 140, WIDTH, 1)
        display.text(f"Cleverness: {self.player.cleverness}", 30, 160, WIDTH, 1)
        
        # Combat stats
        display.set_pen(GREEN)
        display.text(f"Health: {self.player.health}/100", 150, 120, WIDTH, 1)
        display.text(f"Attack: {self.player.attack_damage}", 150, 140, WIDTH, 1)
        
        display.set_pen(YELLOW)
        display.text("B: Back to Game", 10, HEIGHT - 20, WIDTH, 1)

    def draw_pause_menu(self):
        display.set_pen(BLACK)
        display.clear()
        display.set_pen(WHITE)
        display.text("Paused", 10, 10, WIDTH, 2)
        display.set_pen(YELLOW)
        display.text("B: Back to Game", 10, HEIGHT - 20, WIDTH, 1)

    def draw_world_map(self):
        display.set_pen(BLACK)
        display.clear()
        display.set_pen(WHITE)
        display.text("World Map", 10, 10, WIDTH, 2)

        location_names = list(self.locations.keys())
        for i, name in enumerate(location_names):
            location_data = self.locations[name]
            if location_data['unlocked']:
                color = YELLOW if i == self.selected_location_index else WHITE
                display.set_pen(color)
                display.circle(location_data['x'], location_data['y'], 5)
                display.text(name, location_data['x'] - 30, location_data['y'] + 10, WIDTH, 1)
            else:
                display.set_pen(display.create_pen(128, 128, 128)) # Gray
                display.circle(location_data['x'], location_data['y'], 5)
                display.text("???", location_data['x'] - 10, location_data['y'] + 10, WIDTH, 1)

        display.set_pen(WHITE)
        display.text("B: Back | A: Travel", 10, HEIGHT - 20, WIDTH, 1)

def play_sound(frequency, duration_ms):
    """Play a simple tone"""
    if frequency > 0:
        buzzer.freq(int(frequency))
        buzzer.duty_u16(1000)
        time.sleep_ms(duration_ms)
        buzzer.duty_u16(0)

def play_tune(tune):
    """Plays a sequence of notes"""
    for note, duration in tune:
        if note in NOTES:
            play_sound(NOTES[note], duration)
        time.sleep_ms(10) # Short pause between notes

def check_qwst_pad():
    """Check if Qw/ST Pad is connected and read inputs"""
    try:
        # Qw/ST Pad uses TCA9555 I/O Expander at address 0x21 (default)
        devices = i2c.scan()
        if 0x21 in devices:
            try:
                # Read both input ports
                port0 = i2c.readfrom_mem(0x21, 0x00, 1)[0]
                port1 = i2c.readfrom_mem(0x21, 0x01, 1)[0]
                
                # Button mapping based on actual hardware testing:
                # Port 0 bits: U=0x02, L=0x04, R=0x08, D=0x10, minus=0x20
                # Port 1 bits: plus=0x08, B=0x10, Y=0x20, A=0x40, X=0x80
                
                return {
                    'up': not bool(port0 & 0x02),      # U - move up
                    'left': not bool(port0 & 0x04),    # L - move left
                    'right': not bool(port0 & 0x08),   # R - move right
                    'down': not bool(port0 & 0x10),    # D - move down
                    'minus': not bool(port0 & 0x20),   # minus - configurable
                    'plus': not bool(port1 & 0x08),    # plus - configurable
                    'b': not bool(port1 & 0x10),       # B - bottom configurable
                    'y': not bool(port1 & 0x20),       # Y - attack/interact
                    'a': not bool(port1 & 0x40),       # A - action/talk/select
                    'x': not bool(port1 & 0x80),       # X - top configurable
                }
            except Exception as e:
                print(f"Error reading Qw/ST Pad: {e}")
                return None
        else:
            return None
    except Exception as e:
        print(f"I2C scan error: {e}")
        return None

# Main game loop
def main():
    print("Starting Fluffbert's Frozen Dream...")
    print(f"Display size: {WIDTH}x{HEIGHT}")
    
    game = Game()
    
    led.set_rgb(0, 255, 0)
    
    print("Game initialized, entering main loop...")
    
    while True:
        try:
            # --- Input Handling & Logging ---
            a_pressed = button_a.read()
            b_pressed = button_b.read()
            x_pressed = button_x.read()
            y_pressed = button_y.read()
            
            qwst_input = check_qwst_pad()

            # --- Game State Input Handling ---
            if game.state == GameState.MENU:
                if x_pressed and game.can_press_button():
                    game.selected_option = (game.selected_option - 1) % 4
                elif y_pressed and game.can_press_button():
                    game.selected_option = (game.selected_option + 1) % 4
                elif (a_pressed or (qwst_input and qwst_input['a'])) and game.can_press_button():
                    if game.selected_option == 0:  # Start Game
                        game.state = GameState.PLAYING
            
            elif game.state == GameState.PLAYING:
                # Screen switching with display buttons
                if a_pressed and game.can_press_button():
                    game.state = GameState.PAUSE_MENU
                if b_pressed and game.can_press_button():
                    game.state = GameState.INVENTORY
                if x_pressed and game.can_press_button():
                    game.state = GameState.CHARACTER
                if y_pressed and game.can_press_button():
                    game.state = GameState.MAP

                # Movement controls from Qw/ST Pad
                move_x, move_y = 0, 0
                if qwst_input:
                    if qwst_input['up']:    # Move up on screen
                        move_y -= 1
                        move_x -= 1
                    if qwst_input['down']:  # Move down on screen
                        move_y += 1
                        move_x += 1
                    if qwst_input['left']:  # Move left on screen
                        move_y += 1
                        move_x -= 1
                    if qwst_input['right']: # Move right on screen
                        move_y -= 1
                        move_x += 1
                
                # Normalize diagonal speed
                if move_x != 0 and move_y != 0:
                    move_x *= 0.707
                    move_y *= 0.707

                # Apply movement
                game.player.vx = move_x * MOVE_SPEED
                game.player.vy = move_y * MOVE_SPEED

                # Interaction from Qw/ST Pad (Y button)
                if (qwst_input and qwst_input['y']) and game.can_press_button():
                    # Try to attack first, then interact if no enemies nearby
                    if not game.player.attack():
                        game.player.interact()
                
                # Action button (A button)
                if (qwst_input and qwst_input['a']) and game.can_press_button():
                    game.player.interact()  # A can also be used for interaction

            elif game.state == GameState.DIALOGUE:
                # Handle dialogue choices with Qw/ST controller buttons in XAYB order
                if qwst_input and game.can_press_button() and game.can_show_options():
                    if qwst_input['x'] and game.dialogue_callback and len(game.dialogue_choices) > 0:
                        game.dialogue_callback(0)
                        game.dialogue_start_time = time.ticks_ms()  # Reset timer after answer
                    elif qwst_input['a'] and game.dialogue_callback and len(game.dialogue_choices) > 1:
                        game.dialogue_callback(1)
                        game.dialogue_start_time = time.ticks_ms()  # Reset timer after answer
                    elif qwst_input['y'] and game.dialogue_callback and len(game.dialogue_choices) > 2:
                        game.dialogue_callback(2)
                        game.dialogue_start_time = time.ticks_ms()  # Reset timer after answer
                    elif qwst_input['b'] and game.dialogue_callback and len(game.dialogue_choices) > 3:
                        game.dialogue_callback(3)
                        game.dialogue_start_time = time.ticks_ms()  # Reset timer after answer

            elif game.state == GameState.WORLD_MAP:
                if qwst_input and game.can_press_button():
                    location_names = list(game.locations.keys())
                    num_locations = len(location_names)
                    
                    if qwst_input['up']:
                        game.selected_location_index = (game.selected_location_index - 1 + num_locations) % num_locations
                    elif qwst_input['down']:
                        game.selected_location_index = (game.selected_location_index + 1) % num_locations
                    elif qwst_input['a']:
                        selected_location_name = location_names[game.selected_location_index]
                        if game.locations[selected_location_name]['unlocked'] and selected_location_name != game.current_area:
                            # Check if we have a map for this location
                            if selected_location_name in game.map_database:
                                print(f"Traveling to {selected_location_name}...")
                                game.current_area = selected_location_name
                                game.map_data = game.map_database[game.current_area] # Load new map
                                game.load_location_objects()  # Load location-specific objects
                                game.player.x = 12
                                game.player.y = 12
                                game.state = GameState.PLAYING
                                play_tune(TUNE_SUCCESS)
                            else:
                                # No map for this location yet
                                print(f"No map data for {selected_location_name}")
                                game.state = GameState.PLAYING

                if b_pressed and game.can_press_button():
                    game.state = GameState.PLAYING

            # Any other state (Inventory, Map, etc.)
            else:
                # B button to return to game from any menu
                if b_pressed and game.can_press_button():
                    game.state = GameState.PLAYING
            
            # --- Game Logic Update ---
            game.update()
            
            # --- Drawing ---
            game.draw()
            display.update()
            
            # --- Frame Rate Limiting ---
            gc.collect()
            time.sleep_ms(16)  # ~60 FPS

        except Exception as e:
            print(f"Error in main loop: {e}")
            # Recovery display
            display.set_pen(RED)
            display.clear()
            display.set_pen(WHITE)
            display.text("ERROR", 10, 10, WIDTH, 2)
            display.text(str(e)[:30], 10, 50, WIDTH, 1)
            display.update()
            time.sleep_ms(1000)

# Run the game
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Clean up
        buzzer.duty_u16(0)
        led.set_rgb(0, 0, 0)
        display.set_pen(BLACK)
        display.clear()
        display.update()

