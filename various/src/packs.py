"""Τα δέκα πακέτα εικονιδίων: γεωμετρία, ονόματα, παλέτες.

ΔΥΟ ΠΟΙΟΤΗΤΕΣ ΠΗΓΗΣ

Όλα τα φύλλα βγήκαν από την ίδια γεννήτρια και έχουν **ίδια διάταξη**: κάρτες
141x141 με βήμα 150, αρχή (24, 90), το εικονίδιο ζωγραφισμένο x3,5 με περιθώριο
14 μέσα στην κάρτα, και η ετικέτα από κάτω. Αλλά έφτασαν σε δύο μεγέθη:

    `full`   1540 px πλάτος — η αυθεντική σελίδα. Η μεγέθυνση είναι
             «πλησιέστερου γείτονα», άρα δειγματοληψία στο κέντρο κάθε κελιού
             επιστρέφει ΑΚΡΙΒΩΣ το αυθεντικό pixel.

    `thumb`   347 px πλάτος — η ίδια σελίδα σμικρυμένη στο 0,2253. Κάθε
             αυθεντικό pixel πιάνει 0,79 pixel, άρα το 32x32 ΔΕΝ υπάρχει πια:
             το εικονίδιο σώζεται σε ~25x25 θολωμένα pixels. Το δείχνει η
             μέτρηση χρωμάτων — 15.000+ χρώματα στο φύλλο αντί για ~750.

Για τα `thumb` η εξαγωγή κάνει δειγματοληψία ΕΠΙΦΑΝΕΙΑΣ και μετά ανάδειγμα στα
32x32. Το Mode 0 (16 στήλες) τα γλιτώνει σχεδόν αλώβητο — χρειάζεται λιγότερη
οριζόντια πληροφορία από όση σώθηκε. Το Mode 1 (32 στήλες) ζητάει περισσότερη
από όση υπάρχει και βγαίνει πιο μαλακό στα περιγράμματα.

    ΑΝ ΒΡΕΘΕΙ ΤΟ ΦΥΛΛΟ ΤΩΝ 1540 px ΓΙΑ ΚΑΠΟΙΟ ΠΑΚΕΤΟ: αντικατέστησε το αρχείο
    και άλλαξε το `kind` σε 'full'. Τίποτα άλλο. Η γεωμετρία είναι ήδη κοινή.

ΟΙ ΠΑΛΕΤΕΣ ΕΙΝΑΙ ΕΠΙΛΕΓΜΕΝΕΣ, ΟΧΙ ΥΠΟΛΟΓΙΣΜΕΝΕΣ

Ο αυτόματος διαλέκτης (`choose_palette`) βρίσκει σχεδόν πάντα παλέτα με λίγο
μικρότερο αριθμητικό σφάλμα, και σχεδόν πάντα χειρότερη στο μάτι: με εκατοντάδες
χρώματα πηγής πάνω σε κύβο 27 χρωμάτων η ομοιόμορφη κατανομή ΕΙΝΑΙ το αριθμητικό
βέλτιστο, οπότε ξοδεύει pens σε αποχρώσεις που καλύπτουν κλάσματα του τοις εκατό
και πέφτουν σκόρπιες πάνω στα περιγράμματα σαν σκόνη. Κάθε παλέτα παρακάτω
γράφτηκε με το λεξιλόγιο του θέματος στο μυαλό. Ο διαλέκτης μένει στον κώδικα
για να ΜΕΤΡΑΕΙ πόσο μακριά είμαστε από το βέλτιστο, όχι για να αποφασίζει.

Στο Mode 1 υπάρχουν μόνο 4 pens: το ένα πάει πάντα στο μαύρο (φόντο και
περιγράμματα) και τα υπόλοιπα τρία πρέπει να χωρίσουν ΤΙ ξεχωρίζει το θέμα.
"""

# Η κοινή γεωμετρία, μετρημένη και όχι υποτιθέμενη.
CARD0 = (24, 90)
CARD_STEP = 150
CARD_IN = 14
SCALE = 3.5
GRID_W = 10
SIZE = 32
FULL_W = 1540

# Το φόντο της κάρτας και της σελίδας. Δεν είναι μέρος των εικονιδίων.
CARD_RGB = (0x38, 0x4C, 0x60)
PAGE_RGB = (0x22, 0x32, 0x42)


class Pack:
    def __init__(self, key, title, src, kind, rows, names, pal0, pal1):
        assert len(set(pal0)) == 16, '%s: το Mode 0 θέλει 16 ΔΙΑΦΟΡΕΤΙΚΑ pens' % key
        assert len(set(pal1)) == 4, '%s: το Mode 1 θέλει 4 ΔΙΑΦΟΡΕΤΙΚΑ pens' % key
        assert all(0 <= f < 27 for f in list(pal0) + list(pal1)), \
            '%s: firmware number εκτός 0-26' % key
        assert len(names) == len(set(names)), '%s: διπλό όνομα' % key
        assert len(names) <= rows * GRID_W, '%s: πιο πολλά ονόματα από κελιά' % key
        self.key, self.title, self.src, self.kind = key, title, src, kind
        self.rows, self.names = rows, names
        self.palettes = {0: list(pal0), 1: list(pal1)}

    @property
    def count(self):
        return len(self.names)


def _n(s):
    return s.split()


# --------------------------------------------------------------- lighthouse
# Η μόνη πηγή σε πλήρες μέγεθος. Τα ονόματα διαβάστηκαν από τις ετικέτες.
LIGHTHOUSE = Pack(
    'lighthouse', 'Lighthouse Harbor', 'lighthouse.png', 'full', 7,
    _n("""
    red_stripe blue_stripe black_stripe green_stripe orange_stripe night_lit
    lantern_room light_beam fresnel_lens keeper_cottage
    rocky_island foghorn signal_flags buoy_light weather_vane spiral_stairs
    lightkeeper_log oil_lamp sailboat_red sailboat_blue
    sailboat_yellow rowboat fishing_trawler tugboat cargo_ship ferry canoe
    dinghy speedboat pirate_ship
    life_raft submarine yacht steering_wheel ship_anchor dock_post wooden_pier
    life_ring life_vest rope_coil
    fishing_net crab_pot telescope binoculars compass sea_chart spyglass_bottle
    message_bottle boat_lantern oar
    harpoon tackle_box captain_hat rain_slicker seagull pelican crab lobster
    starfish seashell
    conch oyster jellyfish wave whale_tail anchor_barnacle driftwood
    sea_buoy_flag
    """),
    # Λιμάνι: νερό, βαμμένο ξύλο, σίδερο, πανί. Το κόκκινο και το λευκό των
    # φάρων πρέπει να ξεχωρίζουν ΚΑΙ τα δύο — είναι η μισή πρώτη σειρά.
    pal0=[0,    # μαύρο — περιγράμματα
          1,    # μπλε νύχτας — βαθύ νερό, σκιά
          3,    # μπορντό — σκούρο κόκκινο βαφής
          12,   # λαδί — σκούρο ξύλο, σχοινί
          9,    # σκούρο πράσινο — φύκια, βρύα
          10,   # σκούρο κυανό — νερό
          13,   # γκρι — σίδερο, βράχος
          15,   # πορτοκαλί — ξύλο, ορείχαλκος, σωσίβιο
          6,    # έντονο κόκκινο — βαμμένες ρίγες
          24,   # έντονο κίτρινο — φως φάρου, μουσαμάς
          2,    # έντονο μπλε — βαμμένες γάστρες
          20,   # έντονο κυανό — ρηχά νερά, γυαλί
          11,   # γαλάζιο — ουρανός, χάρτης
          16,   # ροζ — κοχύλι, σάρκα
          25,   # χλωμό κίτρινο — πανί, άμμος
          26],  # λευκό — αφρός, πανιά, ανταύγειες
    # Φάρος = κόκκινο πάνω σε λευκό πάνω σε μπλε. Χωρίς το μπλε χάνεται η
    # θάλασσα και τα μισά εικονίδια γίνονται αντικείμενα στο κενό.
    pal1=[0,  # μαύρο — περιγράμματα και θάλασσα τη νύχτα
          15, # πορτοκαλί — ξύλο ΚΑΙ βαμμένο κόκκινο μαζί
          13, # γκρι — σίδερο, βράχος, πέτρα
          26],# λευκό — πανιά, αφρός, ρίγες φάρου
)

# ------------------------------------------------------------------- candy
CANDY = Pack(
    'candy', 'Candy Factory', 'candy.png', 'thumb', 7,
    _n("""
    lollipop_pink lollipop_blue lollipop_red candy_cane wrapped_pink wrapped_green
    wrapped_yellow gumball_red gumball_green gumball_blue jelly_orange jelly_purple
    coin_chocolate peppermint gummy_bear gummy_worm rock_candy lollipop_small
    candy_corn candy_bits chocolate_bar chocolate_block truffle bonbon_cherry
    cupcake donut_pink donut_chocolate ice_cream_cone popsicle cookie
    gingerbread_man macaron candy_apple caramel_square fudge_slab wafer_white
    chocolate_bunny popcorn_box candy_jar cauldron mixer_stand chocolate_fountain
    conveyor_candy candy_press oven_candy icing_machine gumball_machine wrapping_machine
    sugar_sack whisk rolling_pin candy_box_blue gift_box candy_bag
    candy_packet candy_heart price_tag candy_sign toffee_gold taffy_pink
    rainbow_bar candy_basket
    """),
    # Ζαχαροπλαστείο: ροζ, κρέμα, σοκολάτα, φρούτο. Τα παστέλ κάνουν τη δουλειά
    # εδώ, όχι τα κορεσμένα — τα μισά εικονίδια είναι γλάσο και κρέμα.
    pal0=[0,    # μαύρο — περιγράμματα
          1,    # μπλε νύχτας — σκιά
          3,    # μπορντό — σκούρα σοκολάτα, κεράσι
          12,   # λαδί — καραμέλα, μπισκότο
          4,    # ματζέντα — σκούρο ροζ γλάσο
          10,   # σκούρο κυανό — μπλε γλάσο
          13,   # γκρι — μέταλλο, φόρμες
          15,   # πορτοκαλί — καραμέλα, βάφλα, μέλι
          6,    # έντονο κόκκινο — ρίγες, φράουλα
          24,   # έντονο κίτρινο — λεμόνι, ζύμη
          8,    # έντονο ματζέντα — ζουμερό ροζ
          2,    # έντονο μπλε — μπλε καραμέλα
          18,   # έντονο πράσινο — μέντα, ζελεδάκι
          16,   # ροζ — ΤΟ χρώμα του πακέτου
          25,   # χλωμό κίτρινο — κρέμα, μαρέγκα
          26],  # λευκό — ζάχαρη, σαντιγί
    # Ροζ γλάσο, σοκολάτα, ζάχαρη. Χωρίς το ροζ δεν υπάρχει ζαχαροπλαστείο.
    pal1=[0,  # μαύρο — περιγράμματα
          3,  # μπορντό — σοκολάτα και μπισκότο
          16, # ροζ — ΤΟ χρώμα: γλάσο και ζαχαρωτά
          26],# λευκό — ζάχαρη, κρέμα, ανταύγειες
)

# ---------------------------------------------------------------- carnival
CARNIVAL = Pack(
    'carnival', 'Carnival', 'carnival.png', 'thumb', 8,
    _n("""
    tent_big tent_striped flag_pole ticket ticket_booth cotton_candy_stand
    ferris_wheel tent_pair hot_air_balloon megaphone entrance_arch prize_booth
    cannon_circus swing_ride circus_wagon ring_toss target_board star_prize
    balloon_red balloon_bunch confetti pennant flag_bunting ride_seat
    stilts bumper_car top_hat magic_wand crystal_ball poster_star
    cotton_candy popcorn_box candy_apple hot_dog corn_dog fried_dough
    donut_carnival juice_box soda_cup ice_cream_cone striped_pole lollipop_purple
    popcorn cotton_candy_blue cookie_carnival carousel target_dart dart
    chocolate_scoop ring_toss_post teddy_bear goldfish_bag shooting_gallery mirror_funny
    strength_test medal_gold trophy rubber_duck prize_ribbon course_flag
    ringmaster clown juggling_balls doll_pink juggler strongman
    musician performer lion_face elephant seal_ball horse_carousel
    monkey macaw cannon tightrope_poles ride_banner fedora
    """),
    # Λούνα παρκ: κορεσμένα, φωτεινά, αντίθετα. Εδώ ΘΕΛΟΥΜΕ τα έντονα —
    # είναι το μόνο πακέτο όπου το αριθμητικό βέλτιστο και το μάτι συμφωνούν.
    pal0=[0,    # μαύρο — περιγράμματα
          1,    # μπλε νύχτας — νυχτερινός ουρανός
          3,    # μπορντό — σκούρο κόκκινο τέντας
          12,   # λαδί — ξύλο, σχοινί
          9,    # σκούρο πράσινο — γρασίδι
          10,   # σκούρο κυανό — σκιά σε μπλε
          13,   # γκρι — μέταλλο, ατσάλι
          15,   # πορτοκαλί — καραμελωμένο, ξύλο
          6,    # έντονο κόκκινο — ρίγες τέντας
          24,   # έντονο κίτρινο — λάμπες, αστέρια
          8,    # έντονο ματζέντα — μαλλί της γριάς
          2,    # έντονο μπλε — βαμμένο μέταλλο
          18,   # έντονο πράσινο — βραβεία, μπαλόνια
          20,   # έντονο κυανό — νέον
          16,   # ροζ — μαλλί της γριάς, βραβεία
          26],  # λευκό — φώτα, ανταύγειες
    # Ρίγες τέντας: κόκκινο και λευκό. Συν κίτρινο για τις λάμπες, που είναι
    # παντού σε αυτό το πακέτο.
    pal1=[0,  # μαύρο — περιγράμματα
          6,  # έντονο κόκκινο — τέντες και βαφή
          24, # έντονο κίτρινο — λάμπες, χρυσό, βραβεία
          26],# λευκό — ρίγες και ανταύγειες
)

# ------------------------------------------------------------------- dwarf
DWARF = Pack(
    'dwarf', 'Dwarven Mine', 'dwarf.png', 'thumb', 7,
    _n("""
    ore_silver ingot_silver ore_copper ingot_copper ore_gold ingot_gold
    ore_stone ingot_iron ore_coal coal_block ore_crystal ingot_crystal
    gem_ruby gem_sapphire gem_emerald gem_amethyst gem_topaz gem_diamond
    geode_purple nuggets_gold pickaxe sledgehammer shovel maul
    chain anvil bellows file_tool crucible ladle
    dynamite cart_gold cart_empty torch cannon sack_coin
    candle helmet_mine helmet_winged axe_double hammer_smith shield_round
    chainmail boot_steel gauntlet banner_orange mug_ale rune_tablet
    crown_gold forge_machine crucible_molten molten_metal coal_pile bucket_water
    barrel_banded stone_wall support_beam ladder_wood mine_entrance chest_treasure
    gold_pile skull mushroom_purple crystal_cluster scroll sword_gold
    key_gold star_gold
    """),
    # Νάνοι: πέτρα, σίδερο, χρυσός, φωτιά στο καμίνι. Σκούρο πακέτο — τα μισά
    # pens πάνε σε γκρι και καφέ γιατί εκεί είναι η μάζα.
    pal0=[0,    # μαύρο — περιγράμματα, σκιά σπηλιάς
          1,    # μπλε νύχτας — κρύα σκιά πέτρας
          3,    # μπορντό — σκούρο δέρμα, αίμα
          12,   # λαδί — σκούρος μπρούντζος, ξύλο
          9,    # σκούρο πράσινο — σμαράγδι, βρύα
          10,   # σκούρο κυανό — ζαφείρι
          13,   # γκρι — ΤΟ χρώμα: πέτρα και σίδερο
          15,   # πορτοκαλί — φωτιά καμινιού, χαλκός
          6,    # έντονο κόκκινο — ρουμπίνι, πυρακτωμένο
          24,   # έντονο κίτρινο — χρυσός
          18,   # έντονο πράσινο — σμαράγδι
          20,   # έντονο κυανό — διαμάντι, πάγος
          14,   # παστέλ μπλε — ατσάλι με φως
          4,    # ματζέντα — αμέθυστος
          25,   # χλωμό κίτρινο — ανταύγεια χρυσού
          26],  # λευκό — ανταύγειες σε μέταλλο
    # Σίδερο και χρυσός πάνω στο μαύρο της σπηλιάς. Το γκρι ΠΡΕΠΕΙ να υπάρχει:
    # χωρίς αυτό κάθε όπλο γίνεται χρυσό.
    pal1=[0,  # μαύρο — σπηλιά και περιγράμματα
          13, # γκρι — ΤΟ χρώμα: πέτρα, σίδερο, ασήμι
          24, # έντονο κίτρινο — χρυσός και χαλκός
          26],# λευκό — κόψη και ανταύγειες
)

# ------------------------------------------------------------------- egypt
EGYPT = Pack(
    'egypt', 'Ancient Egypt', 'egypt.png', 'thumb', 6,
    _n("""
    ankh scarab canopic_jar sarcophagus pharaoh_mask papyrus_scroll
    clay_tablet chalice_gold ring_turquoise shield_blue lotus_flower papyrus_plant
    coin_gold chest_wood eye_of_horus hieroglyph_tablet oil_lamp stone_tablet
    ceremonial_stand crook_and_flail pharaoh_headdress offering_cake throne sun_disc
    winged_scarab horus_statue feather_maat ceremonial_banner standard_pole pyramid
    column_lotus offering_bowl jackal lapis_blocks pyramid_entrance sphinx
    shabti temple_gate tomb_entrance palm_tree boat_reed nile_water
    oasis column_stone stone_blocks shrine bastet anubis_head
    falcon crocodile camel cobra statue_gold mummy
    pharaoh_figure priest_figure worker sack_grain crook_staff bow_arrow
    """),
    # Αίγυπτος: άμμος, χρυσός, λάπις, τιρκουάζ. Τα τρία ορυκτά χρώματα του
    # θέματος είναι όλη η δουλειά — τα υπόλοιπα είναι άμμος σε αποχρώσεις.
    pal0=[0,    # μαύρο — περιγράμματα, κοχλ
          1,    # μπλε νύχτας — λάπις σκούρο
          3,    # μπορντό — σκούρο κόκκινο τοιχογραφίας
          12,   # λαδί — σκούρος χρυσός, λάσπη Νείλου
          9,    # σκούρο πράσινο — μαλαχίτης, παπύρι
          10,   # σκούρο κυανό — τιρκουάζ σκιά
          13,   # γκρι — γρανίτης
          15,   # πορτοκαλί — ψημένος πηλός, άμμος σκιά
          6,    # έντονο κόκκινο — βαφή, αίμα
          24,   # έντονο κίτρινο — ΧΡΥΣΟΣ, το χρώμα του θέματος
          2,    # έντονο μπλε — λάπις λάζουλι
          20,   # έντονο κυανό — τιρκουάζ, φαγεντιανή
          18,   # έντονο πράσινο — παπύρι, σμάραγδος
          16,   # ροζ — δέρμα
          25,   # χλωμό κίτρινο — ΑΜΜΟΣ και ασβεστόλιθος
          26],  # λευκό — λινό, ανταύγειες
    # Χρυσός σε άμμο, με λάπις για αντίθεση. Χωρίς το μπλε όλα γίνονται μια
    # κίτρινη μάζα — είναι το μόνο ψυχρό χρώμα που είχαν.
    pal1=[0,  # μαύρο — περιγράμματα και κοχλ
          10, # σκούρο κυανό — λάπις και τιρκουάζ, το μόνο ψυχρό χρώμα
          24, # έντονο κίτρινο — ΧΡΥΣΟΣ και άμμος
          26],# λευκό — λινό και ανταύγειες
)

# -------------------------------------------------------------------- lava
LAVA = Pack(
    'lava', 'Volcano', 'lava.png', 'thumb', 8,
    _n("""
    gem_fire lava_pool orb_fire volcano_cone potion_fire bucket_lava
    furnace cauldron_molten heart_fire crystal_fire flame ember_bits
    sword_molten stone_disc_fire ingot_molten flask_fire crystal_red ember_core
    torch fire_pit forge_fire obsidian_shard obsidian_chunk rock_grey
    basalt_column basalt_cluster stone_sphere crystal_gold sulphur_mound ash_rock
    lava_rock_disc obsidian_lava rune_stone_fire rock_ember amber_shard gem_ruby
    obelisk_dark stone_round stone_cracked orb_purple helmet_safety goggles
    suit_protective glove_heat pickaxe hammer_geology sample_tube thermometer
    fire_extinguisher bucket_water hazard_crest lava_bomb boot medallion
    field_notes volcano_smoking mountain_dark mountain_snow volcano_erupting rocks_grey
    rocks_dark lava_lake cave_lava island_volcano warning_sign hot_spring
    geyser seismograph lava_wall lava_blob heat_hood imp_face
    fire_beast phoenix_feather
    """),
    # Ηφαίστειο: μαύρο, κόκκινο, πορτοκαλί, κίτρινο. Στενή γκάμα αλλά ΠΥΚΝΗ —
    # η βαθμίδα από πυρακτωμένο σε κρύα πέτρα είναι όλο το πακέτο, οπότε τα
    # pens πυκνώνουν εκεί αντί να απλωθούν σε χρώματα που δεν εμφανίζονται.
    pal0=[0,    # μαύρο — βασάλτης, οψιδιανός, περιγράμματα
          1,    # μπλε νύχτας — κρύα σκιά
          3,    # μπορντό — σκούρο πυρακτωμένο
          12,   # λαδί — καμένο, θειάφι σκιά
          13,   # γκρι — στάχτη, κρύα πέτρα
          6,    # έντονο κόκκινο — λάβα
          15,   # πορτοκαλί — ΤΟ χρώμα: ρέουσα λάβα
          24,   # έντονο κίτρινο — πυρήνας φλόγας
          4,    # ματζέντα — σκούρο πορφυρό καπνού
          7,    # πορφυρό — καπνός με φως
          9,    # σκούρο πράσινο — θειάφι
          21,   # λάιμ — θειάφι φωτεινό
          16,   # ροζ — θερμή ομίχλη
          25,   # χλωμό κίτρινο — λευκοπυρακτωμένο
          14,   # παστέλ μπλε — κρύος καπνός
          26],  # λευκό — πυρήνας, στάχτη φωτεινή
    # Λάβα πάνω σε μαύρη πέτρα. Κόκκινο ΚΑΙ πορτοκαλί — η διαφορά τους είναι
    # η διαφορά ανάμεσα σε «καυτό» και «λιωμένο», και είναι όλο το θέμα.
    pal1=[0,  # μαύρο — βασάλτης, οψιδιανός, περιγράμματα
          6,  # έντονο κόκκινο — λάβα σκούρα, φλόγα
          15, # πορτοκαλί — λάβα φωτεινή, πυρακτωμένο
          13],# γκρι — ΚΡΥΑ πέτρα και ο εξοπλισμός του δεύτερου μισού
)

# ---------------------------------------------------------------- medieval
MEDIEVAL = Pack(
    'medieval', 'Medieval Market', 'medieval.png', 'thumb', 7,
    _n("""
    stall_red stall_blue stall_green stall_yellow crate_wood barrel_banded
    pestle_mortar sign_coin scales_balance fish_stand flag_red sign_blank
    coin_pouch bread_loaf baguette bread_round pie_pastry cheese_wedge
    ham_leg sausage_links fish crate_vegetables pear grapes
    pumpkin cabbage carrots cake_cream jar_honey ale_mug
    bottle_wine mug_ale sack_flour sweet_roll cloth_red cloth_blue
    wool_ball candles jug_clay jug_red quill_feather potion_orange
    potion_purple ink_bottle leather_hide stone_block scroll letter_sealed
    coins_gold silver_plate pouch_leather shield_round sword bow
    fence hatchet hammer key_gold padlock_plate hat_brown
    leather_piece cask trowel
    """),
    # Μεσαίωνας: πέτρα, ατσάλι, ξύλο, οικόσημο. Τα εραλδικά χρώματα (κόκκινο,
    # μπλε, χρυσό) πρέπει να ξεχωρίζουν από το ατσάλι — αλλιώς τα λάβαρα και οι
    # ασπίδες γίνονται γκρι σαν τα όπλα.
    pal0=[0,    # μαύρο — περιγράμματα
          1,    # μπλε νύχτας — εραλδικό μπλε σκούρο
          3,    # μπορντό — εραλδικό κόκκινο σκούρο
          12,   # λαδί — ξύλο, δέρμα, μπρούντζος
          9,    # σκούρο πράσινο — εραλδικό πράσινο
          10,   # σκούρο κυανό — σκιά σε ατσάλι
          13,   # γκρι — ΤΟ χρώμα: ατσάλι και πέτρα
          15,   # πορτοκαλί — ξύλο, χαλκός, φλόγα
          6,    # έντονο κόκκινο — λάβαρα
          24,   # έντονο κίτρινο — χρυσός, στέμμα
          2,    # έντονο μπλε — λάβαρα
          18,   # έντονο πράσινο — ύφασμα
          14,   # παστέλ μπλε — ατσάλι με φως
          16,   # ροζ — δέρμα, σάρκα
          25,   # χλωμό κίτρινο — περγαμηνή, κερί
          26],  # λευκό — ανταύγειες, λινό
    # Ατσάλι, ξύλο, και το κόκκινο του οικοσήμου. Το γκρι κρατάει τα όπλα και
    # την πέτρα· χωρίς το κόκκινο χάνονται όλα τα λάβαρα.
    pal1=[0,  # μαύρο — περιγράμματα
          3,  # μπορντό — κόκκινο ύφασμα ΚΑΙ σκούρο ξύλο μαζί
          13, # γκρι — πέτρα, ατσάλι, ασήμι
          25],# χλωμό κίτρινο — ψωμί, τυρί, περγαμηνή, τέντα
)

# ------------------------------------------------------------------ mining
MINING = Pack(
    'mining', 'Mining', 'mining.png', 'thumb', 8,
    _n("""
    cart_wood cart_copper cart_coal cart_gold cart_crystal cart_blue
    cart_stone cart_red rail_track rail_curve rail_cross rail_buffer
    rail_switch signal_lamp tunnel_frame support_beam arch_wood jack_prop
    mine_mouth cart_dynamite pickaxe_steel pickaxe_gold shovel hammer
    drill_hand chisel helmet_mine battery_lamp goggles dynamite_bundle
    crate_dynamite detonator lantern_gold ore_sample wheelbarrow plumb_bob
    scanner map_mine ore_copper ore_coal ore_copper_rich ore_gold
    ore_silver ore_diamond ore_emerald ore_ruby ore_amethyst ore_sapphire
    stone_grey gravel ingot_silver ingot_gold ingot_copper ingot_steel
    coal_lump gem_diamond gem_emerald gem_ruby gem_amethyst gem_sapphire
    gem_topaz nuggets_gold crystal_cluster sack_ore backpack_orange gold_vein
    boot_leather canister_red flask_blue first_aid toolbox_metal warning_sign
    gold_coin sack_brown chest_wood key_gold blueprint drill_head
    """),
    # Ορυχείο: βράχος, κάρβουνο, μέταλλο, φως λάμπας. Σκούρο και μονόχρωμο
    # πακέτο — το κίτρινο της λάμπας και του χρυσού είναι η μόνη ζεστασιά.
    pal0=[0,    # μαύρο — κάρβουνο, σκοτάδι, περιγράμματα
          1,    # μπλε νύχτας — κρύα σκιά σήραγγας
          3,    # μπορντό — σκουριά
          12,   # λαδί — ξύλο, σκούρος μπρούντζος
          9,    # σκούρο πράσινο — βρύα, οξείδιο
          10,   # σκούρο κυανό — υγρή πέτρα
          13,   # γκρι — ΤΟ χρώμα: βράχος και ατσάλι
          15,   # πορτοκαλί — χαλκός, σκουριά, φως
          6,    # έντονο κόκκινο — δυναμίτης, προειδοποίηση
          24,   # έντονο κίτρινο — λάμπα, χρυσός, κράνος
          18,   # έντονο πράσινο — σμαράγδι
          20,   # έντονο κυανό — κρύσταλλο
          14,   # παστέλ μπλε — ατσάλι με φως
          2,    # έντονο μπλε — ζαφείρι, φόρμα
          25,   # χλωμό κίτρινο — φως λάμπας
          26],  # λευκό — ανταύγειες, σκόνη
    # Βράχος, μέταλλο, φως λάμπας. Το κίτρινο κάνει διπλή δουλειά: κράνος και
    # χρυσός, που είναι τα δύο πράγματα που πρέπει να ξεχωρίζουν στο σκοτάδι.
    pal1=[0,  # μαύρο — κάρβουνο και σκοτάδι
          13, # γκρι — ΤΟ χρώμα: βράχος, ράγες, ατσάλι
          24, # έντονο κίτρινο — χρυσός, λάμπα, κράνος
          26],# λευκό — ανταύγειες που ξεχωρίζουν τον βράχο
)

# ------------------------------------------------------------------ pirate
PIRATE = Pack(
    'pirate', 'Pirate Treasure', 'pirate.png', 'thumb', 7,
    _n("""
    map_treasure scroll_rolled map_torn notice_board map_island map_sea
    parchment_blank map_burnt map_x map_marked map_mountains map_compass_ring
    pin_location parchment_strip parchment_torn map_framed bottle_message globe
    letter_sealed chest_closed chest_gold_open gold_nuggets gold_bars brooch
    crown_gold amulet_blue pearl_white gem_diamond gem_emerald gem_ruby
    gem_sapphire goblet_gold skull_gold ink_pot idol_gold necklace_amethyst
    pearl_large coin_gold urn_orange sack_gold orb_purple compass_gold
    spyglass compass_rose anchor lantern_ship sail hourglass
    telescope_stand compass_blue mirror_hand boat_sail lighthouse bucket_wood
    buoy_red flag_pirate sword_upright pistol_wood hat_pirate cannonball
    skull_crossbones bottle_green parrot bomb_round cannon sword_gold
    hook_hand shovel keg
    """),
    # Πειρατές: ξύλο, πανί, χρυσός, θάλασσα, αίμα. Το χρυσό πρέπει να λάμπει
    # πάνω στο σκούρο ξύλο — είναι η μισή δεύτερη μισή του πακέτου.
    pal0=[0,    # μαύρο — σημαία, περιγράμματα
          1,    # μπλε νύχτας — βαθιά θάλασσα
          3,    # μπορντό — σκούρο ξύλο, αίμα
          12,   # λαδί — ΤΟ χρώμα: ξύλο καταστρώματος
          9,    # σκούρο πράσινο — φύκια, μπουκάλι
          10,   # σκούρο κυανό — θάλασσα
          13,   # γκρι — ατσάλι, κανόνι
          15,   # πορτοκαλί — ξύλο φωτεινό, χαλκός
          6,    # έντονο κόκκινο — μπαντάνα, αίμα
          24,   # έντονο κίτρινο — ΧΡΥΣΟΣ και δουβλόνια
          2,    # έντονο μπλε — θάλασσα, στολή
          20,   # έντονο κυανό — ρηχά νερά
          18,   # έντονο πράσινο — παπαγάλος, νησί
          16,   # ροζ — δέρμα, σάρκα
          25,   # χλωμό κίτρινο — πανί, περγαμηνή, κόκαλο
          26],  # λευκό — κρανίο, πανιά, αφρός
    # Κρανίο σε μαύρη σημαία, χρυσός, ξύλο. Το χλωμό κίτρινο κάνει ΚΑΙ το πανί
    # ΚΑΙ τον χάρτη ΚΑΙ το κόκαλο — τρία πράγματα με ένα pen.
    pal1=[0,  # μαύρο — περιγράμματα και σημαία
          24, # έντονο κίτρινο — ΧΡΥΣΟΣ, το μισό πακέτο
          13, # γκρι — σκίαση περγαμηνής, το άλλο μισό
          26],# λευκό — χάρτες, κρανίο, μαργαριτάρι
)

# ---------------------------------------------------------------- wildwest
WILDWEST = Pack(
    'wildwest', 'Wild West Saloon', 'wildwest.png', 'thumb', 8,
    _n("""
    whiskey_bottle whiskey_glass shot_glass beer_mug bottle_green bottle_wine
    cocktail_glass banjo barrel_wood keg_tap ledger cocktail_pink
    steak_meat can_label bread_loaf pastry biscuits chicken_roast
    pie_slice pot_beans corn_cob apple cheese_wedge card_spades
    card_hearts card_diamonds card_clubs card_back card_joker domino
    chip_red chip_blue chip_black chips_stack roulette_wheel chip_stack_gold
    visor_dealer coin_gold coin_silver banknote banknotes jug_clay
    gold_nuggets gold_bars sack_money safe_dial wanted_poster sign_wood
    saloon_doors stool_red piano spittoon bar_tap stool_gold
    table_wood dice_pair saloon_front chair_wood crate_wood star_sheriff
    revolver bullets signpost rifle dynamite_bundle handcuffs
    hat_cowboy boot_cowboy bandana_red hat_straw spur canteen
    """),
    # Άγρια Δύση: δέρμα, σκόνη, τζιν, σκουριασμένο μέταλλο. Ζεστό και ξεθωριασμένο
    # πακέτο — τα κορεσμένα χρώματα θα το έκαναν κόμικ αντί για ξεραμένη έρημο.
    pal0=[0,    # μαύρο — περιγράμματα
          1,    # μπλε νύχτας — τζιν σκούρο, νύχτα
          3,    # μπορντό — σκούρο δέρμα, κόκκινο μαντήλι
          12,   # λαδί — ΤΟ χρώμα: δέρμα, ξύλο, σκόνη
          9,    # σκούρο πράσινο — κάκτος
          10,   # σκούρο κυανό — τζιν
          13,   # γκρι — ατσάλι, όπλα, βράχος
          15,   # πορτοκαλί — σκουριά, ξύλο, ηλιοβασίλεμα
          6,    # έντονο κόκκινο — μαντήλι, βαγόνι
          24,   # έντονο κίτρινο — χρυσός, αστέρι σερίφη
          2,    # έντονο μπλε — ουρανός, στολή
          18,   # έντονο πράσινο — κάκτος φωτεινός
          16,   # ροζ — δέρμα προσώπου
          4,    # ματζέντα — σκιά σε έρημο
          25,   # χλωμό κίτρινο — ΑΜΜΟΣ, αφίσα, κόκαλο
          26],  # λευκό — πουκάμισο, κρανίο, ανταύγειες
    # Δέρμα και σκόνη, με το ατσάλι των όπλων και τον χρυσό του αστεριού. Το
    # λαδί είναι το χρώμα της Δύσης: δέρμα, ξύλο και χώμα μαζί.
    pal1=[0,  # μαύρο — περιγράμματα
          15, # πορτοκαλί — ουίσκι, ξύλο, δέρμα, φαγητό
          13, # γκρι — χαρτιά, μάρκες, όπλα, ατσάλι
          26],# λευκό — ζάρια, πουκάμισο, ανταύγειες
)

PACKS = [LIGHTHOUSE, CANDY, CARNIVAL, DWARF, EGYPT, LAVA, MEDIEVAL, MINING,
         PIRATE, WILDWEST]

BY_KEY = {p.key: p for p in PACKS}
