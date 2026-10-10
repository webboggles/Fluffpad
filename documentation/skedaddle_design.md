# La-Fluff-Puff Skedaddle: design brief

> Original design brief. The shipped game implements a subset; see the root README for current controls and [hardware/README.md](../hardware/README.md) for wiring.

## Core Concept
A spin-off from the Chrome T-Rex game featuring a La-Fluff-Puff character that must jump over increasingly bizarre obstacles whilst running through an alien landscape. The game combines the simple mechanics of the original with random character generation and weapon pickups.

## Game Mechanics

### Character Generation
At game start, the system randomly generates a unique La-Fluff-Puff:

**La-Fluff-Puff Colouring Options:**
- Pastel Pink with Rainbow Spots
- Electric Blue with Glitter Patches
- Mint Green with Polka Dots
- Lavender with Star Patterns
- Coral Orange with Stripe Markings
- Sunshine Yellow with Cloud Shapes
- Bubblegum Purple with Heart Motifs
- Seafoam Teal with Wave Designs
- Rose Gold with Diamond Sparkles
- Cotton Candy White with Colour-Changing Tips

**Facial Expression Options:**
- Determined Squint (focused eyebrows, pursed lips)
- Panic Eyes (wide open, mouth agape)
- Cheeky Grin (winking eye, tongue out)
- Sleepy Daze (half-closed eyes, yawning mouth)
- Angry Pout (furrowed brow, grumpy frown)
- Surprised Shock (raised eyebrows, O-shaped mouth)
- Confident Smirk (one raised eyebrow, sly smile)
- Worried Frown (droopy eyes, downturned mouth)
- Excited Beam (sparkling eyes, huge smile)
- Confused Tilt (tilted head, question mark eyes)

### Obstacle System

**Random Obstacle List:**
1. **Giant Rubber Duck** - Yellow bath toy that squeaks when jumped over
2. **Spinning Pizza Slice** - Cheesy triangle rotating as it approaches
3. **Bouncing Marshmallow** - Fluffy white cube that compresses and expands
4. **Rolling Bowling Ball** - Black sphere with finger holes visible
5. **Hopping Toaster** - Chrome appliance with toast popping out
6. **Sliding Banana Peel** - Classic yellow slip hazard
7. **Tumbling Washing Machine** - White appliance spilling soap bubbles
8. **Crawling Giant Spider** - Eight-legged creature with googly eyes
9. **Flying Taco** - Mexican food item with wings flapping
10. **Bouncing Basketball** - Orange sphere with black lines
11. **Rolling Cheese Wheel** - Round yellow cheese with holes
12. **Sliding Ice Cube** - Transparent frozen block leaving water trail
13. **Hopping Mushroom** - Red and white spotted fungus
14. **Spinning Record Player** - Vinyl disc on turntable base
15. **Crawling Vacuum Cleaner** - Robotic cleaning device with cord trailing
16. **Flying Umbrella** - Inside-out brolly caught in wind
17. **Rolling Watermelon** - Green striped fruit leaving juice splashes
18. **Bouncing Trampoline** - Mini version bouncing by itself
19. **Sliding Soap Bar** - Pink slippery rectangle with bubbles
20. **Tumbling Dice** - Oversized gaming cubes showing random numbers
21. **Flying Teapot** - Ceramic pot with steam trailing behind
22. **Rolling Doughnut** - Pink frosted ring with sprinkles
23. **Hopping Cactus** - Green spiky plant in terracotta pot
24. **Spinning Windmill** - Dutch-style with rotating blades
25. **Crawling Suitcase** - Travel case with legs and wheels

**Obstacle Behaviour:**
- Obstacles approach from right side of screen at varying speeds
- Each obstacle type has unique animation (spinning, bouncing, crawling)
- Speed increases gradually as score increases
- Multiple obstacles can appear simultaneously at higher levels
- Some obstacles have different heights requiring different jump timing

### Weapon System

**Weapon Drops (Random Appearance):**
- **Laser Blaster** - Red beam weapon (10 shots)
- **Plasma Cannon** - Blue energy weapon (8 shots)
- **Duck Shooter** - Yellow rubber duck projectiles (15 shots)

**Weapon Mechanics:**
- Weapons drop randomly every 200-500 points
- Limited ammunition displayed on HUD
- Shooting destroys obstacles and awards bonus points
- Different weapons have different projectile speeds and effects
- Ammo counter shows remaining shots

## Environment Design

### Background Layers (Parallax Scrolling)

**Layer 1 (Furthest Background):**
- Alien planet surface with purple mountains
- Twin moons in pink and blue
- Distant crystalline structures
- Nebula clouds in rainbow colours

**Layer 2 (Mid Background):**
- Strange alien trees with spiral trunks
- Floating rock formations
- Glowing mushroom forests
- Energy pylons with crackling electricity

**Layer 3 (Foreground):**
- Metallic ground surface with grid pattern
- Occasional steam vents puffing upwards
- Holographic billboards with alien text
- Scattered alien technology debris

**Ground Surface:**
- Futuristic metal grating with blue energy lines
- Occasional sparks and electrical effects
- Moving conveyor belt sections
- Glowing power conduits beneath transparent panels

### UFO System (Replacing Birds)

**UFO Types:**
1. **Classic Saucer** - Silver disc with rotating lights
2. **Triangular Craft** - Black triangle with corner lights
3. **Cylindrical Ship** - Chrome tube with fins
4. **Organic Vessel** - Bio-mechanical curved design
5. **Cube Ship** - Geometric box with pulsing panels
6. **Ring Craft** - Torus shape with spinning centre

**UFO Behaviour:**
- Fly across screen at various heights
- Different speeds and flight patterns
- Some UFOs pulse with lights
- Occasionally abduct obstacles with tractor beams
- Award bonus points when shot
- Create light trails behind them

## Controls

### Display Module Buttons
- **Display A**: Fire weapon (when available)
- **Display B**: Pause game
- **Display X**: Restart game (when game over)
- **Display Y**: Toggle sound effects

### Qw/ST Pad Controller
- **Controller Y**: Jump (primary action)
- **Controller A**: Fire weapon (alternative to Display A)
- **Controller B**: Duck/slide (future feature)
- **Controller X**: Special ability (future feature)
- **D-Pad**: Menu navigation (game over screen)

## Scoring System

**Point Values:**
- Successfully jumping obstacle: 10 points
- Destroying obstacle with weapon: 25 points
- Shooting UFO: 50 points
- Survival bonus: 1 point per second
- Weapon pickup: 5 points
- Perfect jump (close timing): 15 points

**High Score Features:**
- Local high score storage
- Display best La-Fluff-Puff combination that achieved high score
- Track longest survival time
- Count total obstacles jumped
- Record most accurate shots

## Visual Style

### Art Direction
- Pixel art style optimised for 2.8" display
- Bright, contrasting colours for visibility
- Smooth animations at 30fps
- Particle effects for weapon impacts
- Screen shake for dramatic moments

### La-Fluff-Puff Animation
- Running cycle with bouncing motion
- Jump animation with mid-air spin
- Landing animation with slight compression
- Weapon firing pose with recoil
- Death animation with dramatic fall

### Obstacle Animations
- Each obstacle has unique movement pattern
- Destruction effects when shot
- Particle explosions on impact
- Smooth scaling as they approach
- Shadow effects for depth perception

## Audio Design

### Sound Effects
- **Jump**: Bouncy "boing" sound
- **Weapon Fire**: Sci-fi laser/plasma sounds
- **Obstacle Hit**: Destruction sound per obstacle type
- **UFO**: Hovering/whooshing sounds
- **Pickup**: Positive chime for weapons
- **Game Over**: Dramatic failure sound
- **Background**: Ambient alien atmosphere

### Music
- Upbeat electronic soundtrack
- Tempo increases with game speed
- Layered composition that builds intensity
- Smooth looping for continuous play
- Muted during pause

## Difficulty Progression

### Speed Scaling
- Base speed: 60 pixels/second
- Increases by 5 pixels/second every 100 points
- Maximum speed: 200 pixels/second
- Obstacle spawn rate increases with speed

### Obstacle Complexity
- **0-200 points**: Single obstacles, large gaps
- **200-500 points**: Occasional double obstacles
- **500-1000 points**: Mixed heights, smaller gaps
- **1000+ points**: Rapid succession, multiple types

## Game States

### Start Screen
- Display randomly generated La-Fluff-Puff
- Show controls instructions
- Display current high score
- "Press Y to Start" prompt

### Playing State
- Continuous scrolling background
- Obstacle spawning and movement
- Collision detection
- Score display and weapon ammo counter
- UFO flight patterns

### Game Over Screen
- Final score display
- High score comparison
- La-Fluff-Puff that achieved the score
- Statistics (obstacles jumped, shots fired, etc.)
- "Press X to Restart" prompt

### Pause State
- Freeze all game elements
- Display pause menu
- Resume/restart options
- Sound toggle

## Technical Implementation

### Performance Optimisation
- Sprite pooling for obstacles and effects
- Efficient collision detection using bounding boxes
- Background layer caching
- Smooth frame rate targeting 30fps
- Memory management for continuous play

### Display Considerations
- High contrast colours for outdoor visibility
- Large enough sprites for 2.8" screen
- Clear UI elements
- Readable score display
- Battery level indicator

## Future Enhancements

### Potential Features
- Power-ups (shield, slow motion, double jump)
- Boss obstacles that require multiple hits
- Environmental hazards (meteor showers, energy storms)
- Multiplayer score comparison
- Daily challenges with special obstacles
- La-Fluff-Puff customisation unlocks
- Achievement system
- Photo mode for favourite La-Fluff-Puff combinations

### Expansion Ideas
- Seasonal obstacle themes
- Different alien environments
- Vehicle mode (La-Fluff-Puff on hoverboard)
- Reverse mode (obstacles jump over La-Fluff-Puff)
- Zen mode (no obstacles, just running)