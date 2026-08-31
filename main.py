from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import os
import math
import pygame
import importlib
import glob

# --- PYGAME JOYSTICK INITIALIZATION ---
pygame.init()
pygame.joystick.init()
xbox_controller = None
controller_msg = "No controller detected. Playing with Mouse/Keyboard."

if pygame.joystick.get_count() > 0:
    xbox_controller = pygame.joystick.Joystick(0)
    xbox_controller.init()
    controller_msg = f"Controller Connected: {xbox_controller.get_name()}"
    print(controller_msg)
else:
    print(controller_msg)

# --- URSINA INITIALIZATION & WINDOW ---
app = Ursina()
window.fullscreen = True
window.fps_counter.enabled = True
window.exit_button.visible = False

# --- DAY / NIGHT SKY CYCLE ---
day_color = color.rgb(100, 180, 255)
night_color = color.rgb(10, 20, 45)
day_night_speed = 0.25

# --- CONTROLLER NOTIFICATION BANNER ---
notification = Text(
    text=controller_msg,
    position=(0, 0.4),
    origin=(0, 0),
    scale=1.2,
    color=color.lime if xbox_controller else color.yellow,
    parent=camera.ui
)
destroy(notification, delay=4.0)

# --- 1. SOUND MANAGEMENT ---
sounds = {}
sound_enabled = True
zoom_sound = None

try:
    sounds['red'] = Audio('assets/sounds/gunshot_red.wav', autoplay=False, loop=False)
    sounds['yellow'] = Audio('assets/sounds/gunshot_yellow.wav', autoplay=False, loop=False)
    sounds['green'] = Audio('assets/sounds/gunshot_green.wav', autoplay=False, loop=False)
    current_sound = sounds['red']
    zoom_sound = Audio('assets/sounds/zoom.wav', autoplay=False, loop=False)
except:
    print("Sound files not found.")
    sounds['red'] = None; sounds['yellow'] = None; sounds['green'] = None
    current_sound = None; zoom_sound = None

# --- 2. PLAYER, GUN & CROSSHAIR ---
player = FirstPersonController()
player.y = 10
player.enabled = False 
player.mouse_sensitivity = Vec2(40, 40)

gamepad_move_speed = 7.0
gamepad_camera_sensitivity = 80.0

gun = Entity(parent=camera, model='cube', color=color.red, scale=(0.05, 0.04, 0.3), position=(0.25, -0.2, 0.5))
gun.enabled = False 

crosshair = Entity(parent=camera.ui, model='quad', color=color.yellow, scale=(0.02, 0.003))
crosshair_vertical = Entity(parent=crosshair, model='quad', color=color.yellow, scale=(0.15, 6.0))
crosshair.enabled = False  

mode = "red"
shoot_cooldown = 0.0
shoot_speed = 0.1
gun_skin_color = color.red  
was_zoomed = False  

# States for buttons
lb_held = False
rb_held = False
rt_held = False

def apply_weapon_mode(new_mode):
    global mode, current_sound
    mode = new_mode
    if mode == "red":
        gun.color = gun_skin_color
        current_sound = sounds.get('red')
    elif mode == "yellow":
        gun.color = color.yellow
        current_sound = sounds.get('yellow')
    elif mode == "green":
        gun.color = color.green
        current_sound = sounds.get('green')

# --- 3. MENU & BACKGROUND ---
menu_bg = Entity(parent=camera, model='quad', color=color.black, scale=(20, 20), position=(0, 0, 1), always_on_top=True)
title_screen = Entity(parent=camera, model='quad', texture='assets/title.png', scale=(1.6, 0.9, 1), position=(0, 0, 0.85), always_on_top=True)

# --- START / ENTER UI ---
start_instruction=Entity(
    model='quad',
    texture='assets/press_start.png',
    scale=(0.4, 0.15),
    position=(0, -0.3, 0.8),
    always_on_top=True
)

start_btn_touch = Button(
    scale=(0.4, 0.15),
    position=(0, -0.3),
    color=color.clear,
    parent=camera.ui
)

game_started = False

def set_fullscreen(): window.fullscreen = True; window.borderless = True
def set_windowed(): window.fullscreen = False; window.borderless = True
def set_borderless(): window.fullscreen = False; window.borderless = False

def set_sens_low(): player.mouse_sensitivity = Vec2(20, 20)
def set_sens_med(): player.mouse_sensitivity = Vec2(40, 40)
def set_sens_high(): player.mouse_sensitivity = Vec2(70, 70)

def toggle_sound():
    global sound_enabled
    sound_enabled = not sound_enabled
    if not sound_btn.texture:
        sound_btn.color = color.lime if sound_enabled else color.maroon

def skin_red(): gun.color = color.red; global gun_skin_color; gun_skin_color = color.red
def skin_blue(): gun.color = color.blue; global gun_skin_color; gun_skin_color = color.blue
def skin_green(): gun.color = color.green; global gun_skin_color; gun_skin_color = color.green
def skin_gold(): gun.color = color.gold; global gun_skin_color; gun_skin_color = color.gold
def skin_black(): gun.color = color.black; global gun_skin_color; gun_skin_color = color.black

def open_settings():
    close_all_tabs()
    btn_full.enabled = True; btn_win.enabled = True; btn_bord.enabled = True
    btn_slow.enabled = True; btn_med.enabled = True; btn_high.enabled = True
    sound_btn.enabled = True
    if not btn_settings_tab.texture: btn_settings_tab.color = color.white

def open_skins():
    close_all_tabs()
    sk_red.enabled = True; sk_blue.enabled = True; sk_green.enabled = True
    sk_gold.enabled = True; sk_black.enabled = True
    if not btn_skins_tab.texture: btn_skins_tab.color = color.white

def close_all_tabs():
    btn_full.enabled = False; btn_win.enabled = False; btn_bord.enabled = False
    btn_slow.enabled = False; btn_med.enabled = False; btn_high.enabled = False
    sound_btn.enabled = False
    sk_red.enabled = False; sk_blue.enabled = False; sk_green.enabled = False
    sk_gold.enabled = False; sk_black.enabled = False
    if not btn_settings_tab.texture: btn_settings_tab.color = color.gray
    if not btn_skins_tab.texture: btn_skins_tab.color = color.lime

def create_menu_button(img_name, default_color, scale, position):
    full_path = f'assets/menu/{img_name}'
    if os.path.exists(full_path):
        return Button(texture=full_path, scale=scale, position=position, parent=camera.ui, color=color.white)
    else:
        return Button(color=default_color, scale=scale, position=position, parent=camera.ui)

btn_settings_tab = create_menu_button('settings_tab.png', color.gray, (0.16, 0.05), (-0.55, -0.4))
btn_settings_tab.on_click = open_settings

btn_skins_tab = create_menu_button('skins_tab.png', color.lime, (0.16, 0.05), (0.55, -0.4))
btn_skins_tab.on_click = open_skins

btn_full = create_menu_button('full.png', color.dark_gray, (0.16, 0.04), (-0.55, 0.3))
btn_win = create_menu_button('win.png', color.dark_gray, (0.16, 0.04), (-0.55, 0.23))
btn_bord = create_menu_button('bord.png', color.dark_gray, (0.16, 0.04), (-0.55, 0.16))

btn_full.on_click = set_fullscreen
btn_win.on_click = set_windowed
btn_bord.on_click = set_borderless

btn_slow = create_menu_button('slow.png', color.dark_gray, (0.16, 0.04), (-0.55, -0.05))
btn_med = create_menu_button('med.png', color.dark_gray, (0.16, 0.04), (-0.55, -0.12))
btn_high = create_menu_button('high.png', color.dark_gray, (0.16, 0.04), (-0.55, -0.19))

btn_slow.on_click = set_sens_low
btn_med.on_click = set_sens_med
btn_high.on_click = set_sens_high

sound_btn = create_menu_button('sound.png', color.lime, (0.16, 0.04), (-0.55, -0.31))
sound_btn.on_click = toggle_sound

sk_red = create_menu_button('skin_red_btn.png', color.red, (0.16, 0.04), (0.55, 0.3))
sk_blue = create_menu_button('skin_blue_btn.png', color.blue, (0.16, 0.04), (0.55, 0.23))
sk_green = create_menu_button('skin_green_btn.png', color.green, (0.16, 0.04), (0.55, 0.16))
sk_gold = create_menu_button('skin_gold_btn.png', color.gold, (0.16, 0.04), (0.55, 0.09))
sk_black = create_menu_button('skin_black_btn.png', color.black, (0.16, 0.04), (0.55, 0.02))

sk_red.on_click = skin_red
sk_blue.on_click = skin_blue
sk_green.on_click = skin_green
sk_gold.on_click = skin_gold
sk_black.on_click = skin_black

close_all_tabs()

# --- MOD LOADING SYSTEM ---
def load_mods():
    if not os.path.exists('mods'):
        os.makedirs('mods')

    mod_files = glob.glob("mods/*.py")
    for mod_path in mod_files:
        mod_name = os.path.basename(mod_path)[:-3]
        if mod_name != "__init__":
            try:
                spec = importlib.util.spec_from_file_location(mod_name, mod_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                if hasattr(mod, 'init_mod'):
                    mod.init_mod(app, player, gun)
                print(f"[MOD SYSTEM] Loaded mod: {mod_name}")
            except Exception as e:
                print(f"[MOD SYSTEM] Error loading mod {mod_name}: {e}")

load_mods()

# --- 4. WORLD & BOTS ---
floor = Entity(model='cube', texture='white_cube', color=color.green, scale=(200, 10, 200), position=(0, -5, 0), collider='box', name='floor')
enemies = []
allies = []

def spawn_enemy():
    e = Entity(model='cube', color=color.rgb(139, 115, 85), texture='white_cube', scale=(1, 2, 1), position=(random.randint(-30, 30), 1, random.randint(-30, 30)), collider='box', name='enemy')
    Entity(model='cube', parent=e, color=color.black, texture='white_cube', scale=(1.02, 0.4, 1.02), position=(0, 0.8, 0), collider='box', name='head')
    enemies.append(e)
    e.enabled = False 

def spawn_ally():
    a = Entity(model='cube', color=color.blue, texture='white_cube', scale=(1, 2, 1), position=(random.randint(-10, 10), 1, random.randint(-10, 10)), collider='box', name='ally')
    Entity(model='cube', parent=a, color=color.dark_gray, texture='white_cube', scale=(1.1, 0.3, 1.1), position=(0, 0.9, 0))
    allies.append(a)
    a.enabled = False 

def init_game():
    for e in enemies: destroy(e)
    for a in allies: destroy(a)
    enemies.clear(); allies.clear()
    for i in range(8): spawn_enemy()
    for i in range(3): spawn_ally()

init_game()

def respawn():
    if not game_started: return 
    player.position = (0, 10, 0)
    init_game()
    for e in enemies: e.enabled = True
    for a in allies: a.enabled = True
    mouse.locked = True

def start_game():
    global game_started
    game_started = True
    
    destroy(menu_bg); destroy(title_screen)
    destroy(btn_full); destroy(btn_win); destroy(btn_bord)
    destroy(btn_slow); destroy(btn_med); destroy(btn_high); destroy(sound_btn)
    destroy(sk_red); destroy(sk_blue); destroy(sk_green); destroy(sk_gold); destroy(sk_black)
    destroy(btn_settings_tab); destroy(btn_skins_tab)
    
    player.enabled = True; gun.enabled = True; crosshair.enabled = True  
    for e in enemies: e.enabled = True
    for a in allies: a.enabled = True
    mouse.locked = True

# --- 5. SHOOTING ---
def shoot():
    global current_sound, mode, shoot_cooldown, sound_enabled
    if shoot_cooldown > 0 or not game_started: return
        
    if mode == "red": shoot_cooldown = 0.6
    elif mode == "yellow": shoot_cooldown = shoot_speed
    elif mode == "green": shoot_cooldown = 1.2

    if sound_enabled and current_sound and current_sound.clip:
        try:
            current_sound.time = 0; current_sound.play()
        except: pass
    
    count = 5 if mode == "red" else 1
    for i in range(count):
        spread = 0.1 if mode == "red" else (0.02 if mode == "yellow" else 0.0)
        direction = camera.forward + Vec3(random.uniform(-spread, spread), random.uniform(-spread, spread), random.uniform(-spread, spread))
        bullet_ray = raycast(camera.world_position, direction, distance=150)
        
        dist = bullet_ray.distance if bullet_ray.hit else 150
        tracer = Entity(model='cube', color=color.yellow, scale=(0.01, 0.01, dist), position=camera.world_position + direction * (dist/2 + 0.5), rotation=camera.world_rotation, always_on_top=True)
        destroy(tracer, delay=0.05)

        if bullet_ray.hit and bullet_ray.entity.name != 'floor':
            hit_entity = bullet_ray.entity
            if hit_entity.name == 'head':
                parent_enemy = hit_entity.parent
                if parent_enemy in enemies: enemies.remove(parent_enemy)
                destroy(parent_enemy); spawn_enemy()
                if game_started: enemies[-1].enabled = True
            elif hit_entity in enemies:
                enemies.remove(hit_entity)
                destroy(hit_entity); spawn_enemy()
                if game_started: enemies[-1].enabled = True

# --- 6. UPDATE ---
def update():
    global mode, current_sound, shoot_cooldown, game_started, was_zoomed, sound_enabled, zoom_sound, xbox_controller
    global gamepad_move_speed, gamepad_camera_sensitivity, lb_held, rb_held, rt_held

    # 0. DAY / NIGHT CYCLE
    phase = (math.sin(time.time() * day_night_speed) + 1) * 0.5
    sky_color = lerp(day_color, night_color, phase)
    camera.clear_color = sky_color
    if 'menu_bg' in globals():
        try:
            menu_bg.color = sky_color
        except:
            pass
    
    # 1. PROCESS PYGAME EVENTS (KEEPING 'Q' UNLOCKED)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                application.quit()
        elif event.type == pygame.JOYBUTTONDOWN:
            if (event.button == 0 or event.button == 7) and not game_started: # A button or Start to launch
                start_game()

    lt_pressed = False
    rt_pressed = False
    
    if xbox_controller:
        # 2. STICKS MOVEMENT
        try:
            move_x = xbox_controller.get_axis(0)  
            move_y = -xbox_controller.get_axis(1) 
            if abs(move_x) < 0.20: move_x = 0
            if abs(move_y) < 0.20: move_y = 0
            
            move_direction = (player.forward * move_y + player.right * move_x)
            player.position += move_direction * gamepad_move_speed * time.dt

            look_x = xbox_controller.get_axis(3)
            look_y = xbox_controller.get_axis(4)
            if abs(look_x) < 0.20: look_x = 0
            if abs(look_y) < 0.20: look_y = 0

            player.rotation_y += look_x * gamepad_camera_sensitivity * time.dt
            camera.rotation_x += look_y * gamepad_camera_sensitivity * time.dt
            camera.rotation_x = clamp(camera.rotation_x, -85, 85) 

            # 3. REAL LINUX PYGAME TRIGGERS MAPPING (AXIS 2 AND AXIS 5)
            # When resting, axes are -1.0. When fully pressed, they go to 1.0.
            if xbox_controller.get_axis(2) > 0.5:  # Left Trigger (Scope)
                lt_pressed = True
            if xbox_controller.get_axis(5) > 0.5:  # Right Trigger (Shoot)
                rt_pressed = True
        except:
            pass

        # 4. WEAPON CHANGE (LB / RB)
        if game_started:
            try:
                weapon_order = ["red", "yellow", "green"]
                if xbox_controller.get_button(5): # RB
                    if not rb_held:
                        current_index = weapon_order.index(mode)
                        next_index = (current_index + 1) % len(weapon_order)
                        apply_weapon_mode(weapon_order[next_index])
                        rb_held = True
                else:
                    rb_held = False

                if xbox_controller.get_button(4): # LB
                    if not lb_held:
                        current_index = weapon_order.index(mode)
                        next_index = (current_index - 1) % len(weapon_order)
                        apply_weapon_mode(weapon_order[next_index])
                        lb_held = True
                else:
                    lb_held = False
            except:
                pass

    if not game_started:
        mouse.locked = False
        return

    if shoot_cooldown > 0: shoot_cooldown -= time.dt

    # --- SHOOT DETECTIONS ---
    if mouse.locked:
        if mode != "green":
            if held_keys['left mouse'] or rt_pressed:
                shoot()
        else:
            if held_keys['left mouse']:
                shoot()
            if rt_pressed:
                if not rt_held:
                    shoot()
                    rt_held = True
            else:
                rt_held = False
            
    # --- SNIPER ZOOM ---
    if mode == "green" and mouse.locked and (held_keys['right mouse'] or lt_pressed):
        camera.fov = 25
        gun.position = (0.15, -0.1, 0.3)  
        if not was_zoomed:
            if sound_enabled and zoom_sound and zoom_sound.clip:
                try:
                    zoom_sound.time = 0; zoom_sound.play()
                except: pass
            was_zoomed = True
    else:
        camera.fov = 90
        if mode == "red": gun.color = gun_skin_color
        elif mode == "yellow": gun.color = color.yellow
        elif mode == "green": gun.color = color.green
            
        gun.position = (0.25, -0.2, 0.5)
        was_zoomed = False
    
    for e in enemies:
        e.look_at(player.position)
        e.position += e.forward * time.dt * 1.5
    for a in allies:
        if enemies:
            target = min(enemies, key=lambda e: distance(a, e))
            a.look_at(target)
            a.position += a.forward * time.dt * 2
            if distance(a, target) < 1.5:
                if target in enemies: enemies.remove(target)
                destroy(target); spawn_enemy()
                if game_started: enemies[-1].enabled = True

# --- 7. INPUT ---
def input(key):
    global mode, current_sound, game_started, gun_skin_color
    
    if key == 'q' or key == 'Q':
        application.quit()

    if not game_started:
        if key == 'space': start_game()
        return 

    if key == 'r': respawn()
        
    if key == '1': apply_weapon_mode("red")
    elif key == '2': apply_weapon_mode("yellow")
    elif key == '3': apply_weapon_mode("green")

    if key == 'escape': mouse.locked = not mouse.locked

app.run()