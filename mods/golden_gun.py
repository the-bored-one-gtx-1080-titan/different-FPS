from ursina import color

def init_mod(app, player, gun):
    gun.color = color.gold
    gun.scale = (0.08, 0.06, 0.5)
    print("[MOD] Golden Gun Skin Loaded")