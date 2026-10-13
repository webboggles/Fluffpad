"""All the words. British English, PG. Lore lives with its room in the zone files."""
from . import world_data

TITLE = "LA-FLUFF-PUFF"
SUBTITLE = "and the JADE SUN"

PROLOGUE = (
    "Long ago, K'uk'ulkan the Feathered Serpent hung the Jade Sun above the rainforest.",
    "Its green light kept the Night Lords of Xibalba fast asleep beneath the pyramids.",
    "But tonight Camazotz, the Bat King, crept out of the underworld...",
    "...and shattered the Jade Sun into four Sun Glyphs, hidden in the deepest places of the world.",
    "The jungle is growing dark. The Mountain Spirit has fallen silent. The drums are calling.",
    "And in Ceiba Village, a very small, very fluffy hero opens one eye.",
)

FORM_MESSAGES = (
    "Waking the Ceiba spirit...", "Counting the 260 days...", "Polishing obsidian...",
    "Asking the jaguar nicely...", "Applying googly eyes...", "Consulting the howler monkeys...",
    "Untangling the vines...", "Feeding the quetzal...", "Warming up the drums...",
    "Fluffing to maximum...",
)

# speaker, text. Lines starting with '!' are actions: !give:<item>
DIALOGUE = {
    "ceiba_first": (
        ("ceiba", "Ah, little Fluff-Puff. So you heard the drums too."),
        ("ceiba", "Camazotz has stolen the Jade Sun and broken it into four glyphs. Without it the Night Lords will wake."),
        ("fluff", "...!"),
        ("ceiba", "Brave face. Good. Take this blade of obsidian. It is older than the mountain, and it likes you."),
        ("!", "give:blade"),
        ("ceiba", "The cenote lies beneath the canopy to the east, under Fern Gully. Chaac, the Rain Lord, sleeps in its drowned gallery far to the west."),
        ("ceiba", "And little one... if the water grows dark and something stares back, do not stop moving."),
    ),
    "ek": (
        ("ek", "Cacao for courage! Cacao for hearts! Everything has a price, small one. Even bravery."),
        ("!", "shop"),
    ),
    "chaac_first": (
        ("chaac", "Who disturbs the Rain Lord's dream? ...A Fluff-Puff? How unexpected."),
        ("chaac", "Xoc the Deep Serpent swallowed my thunder and coils in the abyss below. You met its shadow, I think."),
        ("chaac", "Take my Rain Pearl. With it, the water will carry you instead of pulling you down."),
        ("!", "give:pearl"),
        ("chaac", "The rain doors will open for one who carries the storm. Even the sluice beneath the cenote mouth."),
    ),
    "chaac": (
        ("chaac", "Swim deep, little storm. Down the Flooded Stair, through the abyss. Xoc coils past the Sunken Ossuary."),
    ),
    "balam_first": (
        ("balam", "So. The little one survived the halls. The Watcher has hunted heroes here for a thousand years."),
        ("balam", "Camazotz stole my shadow and sat it on my throne. Take my speed. Take back my throne."),
        ("!", "give:dash"),
        ("balam", "Cracked stone will shatter before you now. And Fluff-Puff..."),
        ("balam", "RUN. West through the dark, then dash through the old sluice wall. It has heard us."),
        ("!", "watcher"),
    ),
    "balam": (
        ("balam", "My throne lies past the cracked wall of the Calendar Court. Dash, little one."),
    ),
    "witz_first": (
        ("witz", "......"),
        ("witz", "I have been silent so long, I forgot the sound of my own voice."),
        ("witz", "You climbed me, small one. No hero has done that since the first sunrise."),
        ("witz", "Take the Sun Spear. Hold it steady, let it drink the light, and even stone will remember fear."),
        ("!", "give:spear"),
        ("witz", "The Watcher in the temple was carved from my own rock. Set it free. Its heart holds the last glyph."),
    ),
    "witz": (
        ("witz", "Hold the spear until it shines. Golden seals and stubborn stone will crack."),
    ),
    "gate_closed": (
        ("stone", "A great sun gate with four empty sockets. It hums when you come near, then goes quiet."),
    ),
    "rain_closed": (
        ("stone", "A stone door carved with raindrops. It is bone dry."),
    ),
    "seal_closed": (
        ("stone", "A golden seal shaped like the sun. Something bright might break it."),
    ),
    "gate_open": (
        ("ceiba", "The four glyphs sing together! The Sun Gate opens. Camazotz waits below, little one."),
        ("ceiba", "Hold DOWN and press B to drop through the old planks inside the pyramid."),
    ),
    "watcher_dead": (
        ("witz", "The Watcher crumbles... and is free. Inside its stone heart, a glyph glows."),
    ),
    "shrine": (
        ("fluff", "The jade shrine hums. Your hearts are mended and your journey is remembered."),
    ),
}

LORE = world_data.LORE

ITEMS = {
    "blade": ("OBSIDIAN BLADE", "Press Y to slash. Hold UP or DOWN for high and pogo strikes."),
    "pearl": ("RAIN PEARL", "Tap B in water to swim. Rain doors open for you."),
    "dash": ("JAGUAR DASH", "Press A to dash through danger. Smashes cracked stone."),
    "feather": ("QUETZAL FEATHER", "Press B in mid-air to jump again."),
    "spear": ("SUN SPEAR", "Tap X to throw light. Hold X to charge a sunbeam."),
    "heart1": ("JADE HEART", "Your maximum hearts grow by one."),
    "heart2": ("JADE HEART", "Your maximum hearts grow by one."),
    "heart3": ("JADE HEART", "Your maximum hearts grow by one."),
    "heart4": ("JADE HEART", "Your maximum hearts grow by one."),
    "g_water": ("GLYPH OF WATER", "The first piece of the Jade Sun. One pad light glows."),
    "g_jaguar": ("GLYPH OF THE JAGUAR", "The second piece of the Jade Sun."),
    "g_sky": ("GLYPH OF THE SKY", "The third piece of the Jade Sun."),
    "g_stone": ("GLYPH OF STONE", "The final glyph! The Sun Gate awaits at the Great Pyramid."),
}
SHARDS = tuple("shard%d" % i for i in range(1, 13))
for _k in SHARDS:
    ITEMS[_k] = ("JADE SHARD", "Four shards fuse into a new Jade Heart.")

ITEM_ICON = {
    "blade": "blade", "pearl": "pearl", "dash": "dash", "feather": "feather", "spear": "spear",
    "heart1": "heart", "heart2": "heart", "heart3": "heart", "heart4": "heart",
    "g_water": "glyph", "g_jaguar": "glyph", "g_sky": "glyph", "g_stone": "glyph",
}
for _k in SHARDS:
    ITEM_ICON[_k] = "shard"

BOSS_LINES = {
    "xoc": "Ssss... a morsel with fur. The abyss is HUNGRY.",
    "jaguar": "The shadow stretches, yawns with your own face... and pounces!",
    "eagle": "SKREEEE! The sky belongs to ME, puffball!",
    "camazotz": "You carry the light of a broken sun? How delicious. I shall put it out.",
}

SHOP = (
    ("shop_heart", "Jade Heart Shard", "+1 max heart", 60),
    ("shop_edge", "Obsidian Edge", "+1 blade damage", 90),
    ("refill", "Cacao Feast", "Mend all hearts", 10),
)

ZONE_TITLES = {
    "jungle": "THE RAINFOREST", "cenote": "THE SACRED CENOTE", "temple": "TEMPLE OF THE JAGUAR",
    "dread": "THE DREAD HALLS", "mountain": "MOUNTAIN OF WITZ", "xibalba": "XIBALBA",
}

ENDING = (
    "Camazotz tumbles into the dark, shrieking like a kettle.",
    "The four glyphs rise, spin, and click together. The Jade Sun is whole again!",
    "Green light spills over the rainforest. Monkeys cheer. Frogs sing. Somewhere, a jaguar purrs.",
    "Witz speaks across the valley: 'Little one, the mountain will remember your name.'",
    "Grandmother Ceiba smiles: 'Rest now, Fluff-Puff. Even heroes need a nap.'",
)


def hint(g):
    h = g.has
    if not h("blade"):
        return "Talk to Grandmother Ceiba under the great tree."
    if not h("pearl"):
        return "Go east through the Cacao Grove, drop into the cenote at Fern Gully, then head west to the Drowned Gallery."
    if not h("g_water"):
        return "With the Rain Pearl, swim down the Flooded Stair into the abyss. Xoc coils past the Sunken Ossuary."
    if not h("dash"):
        return "The rain door at the Temple Approach is open. Take the Sunken Stair down to Balam. Hide from the Watcher."
    if not h("g_jaguar"):
        return "Dash through the cracked wall of the Calendar Court to reach the Jaguar Throne."
    if not h("feather"):
        return "Dash across the chasm at the Temple Approach, climb the Misty Ascent and search the Wind Caves."
    if not h("g_sky"):
        return "Double jump up the Eagle Cliffs to reach Storm Peak."
    if not h("spear"):
        return "Witz, the Mountain Spirit, waits on the summit east of Storm Peak."
    if not h("g_stone"):
        return "Return to the Dread Halls. Charge the Sun Spear and free the Watcher."
    return "All four glyphs shine! Open the Sun Gate inside the Great Pyramid, west of the village."
