from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import os
import math
import pygame
import importlib
import glob
import requests

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

CURRENT_VERSION = "v0.0.7 alpha"
GITHUB_REPO = "the-bored-one-gtx-1080-titan/different-FPS"

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

# --- SETTINGS FUNCTIONS ---
def set_fullscreen(): window.fullscreen = True; window.borderless = True
def set_windowed(): window.fullscreen = False; window.borderless = True
def set_borderless(): window.fullscreen = False; window.borderless = False

def set_sens_low(): player.mouse_sensitivity = Vec2(20, 20)
def set_sens_med(): player.mouse_sensitivity = Vec2(40, 40)
def set_sens_high(): player.mouse_sensitivity = Vec2(70, 70)

def toggle_sound():
    global sound_enabled
    sound_enabled = not sound_enabled
    print(f"Sound toggled: {sound_enabled}")

def apply_low_end_settings():
    camera.clip_plane_far = 80
    window.fps_counter.enabled = True
    print("[OPTIMIZATION] Low-end settings applied.")

def skin_red(): global gun_skin_color; gun_skin_color = color.red; gun.color = color.red
def skin_blue(): global gun_skin_color; gun_skin_color = color.blue; gun.color = color.blue
def skin_green(): global gun_skin_color; gun_skin_color = color.green; gun.color = color.green
def skin_gold(): global gun_skin_color; gun_skin_color = color.gold; gun.color = color.gold
def skin_black(): global gun_skin_color; gun_skin_color = color.black; gun.color = color.black

# --- 3. MODERN CLEAN UI SYSTEM (v0.0.7) ---
main_menu_panel = Entity(parent=camera.ui, enabled=True)
menu_bg = Entity(parent=main_menu_panel, model='quad', color=color.rgb(15, 15, 20), scale=(2, 2), z=1)

title_text = Text(
    text="DIFFERENT FPS", 
    parent=main_menu_panel, 
    position=(0, 0.35), 
    origin=(0, 0), 
    scale=3, 
    color=color.cyan
)

sub_title = Text(
    text="v0.0.7 alpha - Raspberry Pi & PC Edition", 
    parent=main_menu_panel, 
    position=(0, 0.27), 
    origin=(0, 0), 
    scale=1.2, 
    color=color.gray
)

def create_clean_button(text, position, action, parent=main_menu_panel, color_bg=color.rgb(35, 35, 45)):
    btn = Button(
        text=text,
        parent=parent,
        position=position,
        scale=(0.35, 0.07),
        color=color_bg,
        text_color=color.white,
        highlight_color=color.rgb(55, 120, 200),
        pressed_color=color.rgb(30, 80, 140)
    )
    btn.on_click = action
    return btn

settings_panel = Entity(parent=main_menu_panel, enabled=False)
skins_panel = Entity(parent=main_menu_panel, enabled=False)

Entity(parent=settings_panel, model='quad', color=color.rgb(25, 25, 32), scale=(0.8, 0.7), z=0.1)
Entity(parent=skins_panel, model='quad', color=color.rgb(25, 25, 32), scale=(0.8, 0.7), z=0.1)

Text(text="SETTINGS", parent=settings_panel, position=(0, 0.25), origin=(0,0), scale=1.5, color=color.gold, z=0.0)
Text(text="WEAPON SKINS", parent=skins_panel, position=(0, 0.25), origin=(0,0), scale=1.5, color=color.gold, z=0.0)

def show_main_tab():
    settings_panel.enabled = False
    skins_panel.enabled = False

def show_settings_tab():
    settings_panel.enabled = True
    skins_panel.enabled = False

def show_skins_tab():
    settings_panel.enabled = False
    skins_panel.enabled = True

def start_game():
    global game_started
    game_started = True
    main_menu_panel.enabled = False
    player.enabled = True
    gun.enabled = True
    crosshair.enabled = True
    for e in enemies: e.enabled = True
    for a in allies: a.enabled = True
    mouse.locked = True

btn_start = create_clean_button("PLAY GAME", (0, 0.05), start_game)
btn_open_settings = create_clean_button("SETTINGS", (0, -0.05), show_settings_tab)
btn_open_skins = create_clean_button("SKINS", (0, -0.15), show_skins_tab)
btn_quit = create_clean_button("QUIT", (0, -0.25), application.quit, color_bg=color.rgb(100, 30, 30))

create_clean_button("Fullscreen: Toggle", (-0.18, 0.1), set_fullscreen, parent=settings_panel)
create_clean_button("Low-End Mode", (-0.18, 0.0), apply_low_end_settings, parent=settings_panel)
create_clean_button("Audio Toggle", (-0.18, -0.1), toggle_sound, parent=settings_panel)
create_clean_button("Sens: Low", (0.18, 0.1), set_sens_low, parent=settings_panel)
create_clean_button("Sens: Med", (0.18, 0.0), set_sens_med, parent=settings_panel)
create_clean_button("Sens: High", (0.18, -0.1), set_sens_high, parent=settings_panel)
create_clean_button("<- Back", (0, -0.25), show_main_tab, parent=settings_panel)

create_clean_button("Red Skin", (0, 0.12), skin_red, parent=skins_panel, color_bg=color.rgb(150, 40, 40))
create_clean_button("Blue Skin", (0, 0.04), skin_blue, parent=skins_panel, color_bg=color.rgb(40, 90, 150))
create_clean_button("Green Skin", (0, -0.04), skin_green, parent=skins_panel, color_bg=color.rgb(40, 150, 90))
create_clean_button("Gold Skin", (0, -0.12), skin_gold, parent=skins_panel, color_bg=color.rgb(180, 150, 30))
create_clean_button("<- Back", (0, -0.25), show_main_tab, parent=skins_panel)

game_started = False

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
            except Exception as e:
                print(f"[MOD SYSTEM ERROR] {e}")
load_mods()

# --- 4. WORLD, BOTS, CAR & PHONE ---
floor = Entity(model='cube', texture='white_cube', color=color.rgb(60, 140, 60), scale=(200, 10, 200), position=(0, -5, 0), collider='box', name='floor')

car = Entity(model='cube', color=color.azure, scale=(2.5, 1, 5), collider='box', position=(10, 0.5, 10))
in_car = False
radio_on = False
car_speed = 25
car_ui_text = Text(text="", position=(0, -0.4), origin=(0,0), scale=1.5, color=color.lime, enabled=False, parent=camera.ui)

phone_ui = Entity(parent=camera.ui, enabled=False)
phone_bg = Entity(parent=phone_ui, model='quad', color=color.black90, scale=(0.35, 0.65), position=(0.6, -0.15))
phone_screen = Entity(parent=phone_bg, model='quad', color=color.dark_gray, scale=(0.9, 0.9), position=(0, 0, -0.01))
phone_app_title = Text(parent=phone_bg, text="Lost SMP - v0.0.7 Chat", position=(0, 0.4), origin=(0,0), scale=2, z=-0.02, color=color.cyan)
phone_chat_log = Text(
    parent=phone_bg, 
    text="[Μάνος]: Τσεκάρετε το νέο update v0.0.7!\n\n[Ραφαήλ]: Ωραίο το clean UI!\n\n[System]: Server TPS 20.0 (Optimized)", 
    position=(-0.4, 0.2), 
    scale=1.5, 
    z=-0.02
)

enemies = []
allies = []

def spawn_enemy():
    e = Entity(model='cube', color=color.rgb(150, 90, 60), texture='white_cube', scale=(1, 2, 1), position=(random.randint(-30, 30), 1, random.randint(-30, 30)), collider='box', name='enemy')
    Entity(model='cube', parent=e, color=color.black, texture='white_cube', scale=(1.02, 0.4, 1.02), position=(0, 0.8, 0), collider='box', name='head')
    enemies.append(e)
    e.enabled = False 

def spawn_ally():
    a = Entity(model='cube', color=color.rgb(50, 100, 220), texture='white_cube', scale=(1, 2, 1), position=(random.randint(-10, 10), 1, random.randint(-10, 10)), collider='box', name='ally')
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
    global in_car, radio_on
    if not game_started: return 
    
    if in_car:
        in_car = False
        radio_on = False
        player.enabled = True
        gun.enabled = True
        crosshair.enabled = True
        car_ui_text.enabled = False
        camera.parent = player.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        
    player.position = (0, 10, 0)
    init_game()
    for e in enemies: e.enabled = True
    for a in allies: a.enabled = True
    mouse.locked = True
    phone_ui.enabled = False

# --- 5. SHOOTING ---
def shoot():
    global current_sound, mode, shoot_cooldown, sound_enabled
    if shoot_cooldown > 0 or not game_started: return
        
    if mode == "red": shoot_cooldown = 0.6
    elif mode == "yellow": shoot_cooldown = shoot_speed
    elif mode == "green": shoot_cooldown = 1.2

    if sound_enabled and current_sound and current_sound.clip:
        try: current_sound.time = 0; current_sound.play()
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
    global in_car, car_speed

    phase = (math.sin(time.time() * day_night_speed) + 1) * 0.5
    sky_color = lerp(day_color, night_color, phase)
    camera.clear_color = sky_color
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q: application.quit()
        elif event.type == pygame.JOYBUTTONDOWN:
            if (event.button == 0 or event.button == 7) and not game_started:
                start_game()

    lt_pressed = False
    rt_pressed = False
    
    if xbox_controller:
        try:
            move_x = xbox_controller.get_axis(0)  
            move_y = -xbox_controller.get_axis(1) 
            if abs(move_x) < 0.20: move_x = 0
            if abs(move_y) < 0.20: move_y = 0
            
            if not in_car:
                move_direction = (player.forward * move_y + player.right * move_x)
                player.position += move_direction * gamepad_move_speed * time.dt

            look_x = xbox_controller.get_axis(3)
            look_y = xbox_controller.get_axis(4)
            if abs(look_x) < 0.20: look_x = 0
            if abs(look_y) < 0.20: look_y = 0

            if not in_car:
                player.rotation_y += look_x * gamepad_camera_sensitivity * time.dt
                camera.rotation_x += look_y * gamepad_camera_sensitivity * time.dt
                camera.rotation_x = clamp(camera.rotation_x, -85, 85) 

            if xbox_controller.get_axis(2) > 0.5: lt_pressed = True
            if xbox_controller.get_axis(5) > 0.5: rt_pressed = True
        except: pass

        if game_started and not in_car:
            try:
                weapon_order = ["red", "yellow", "green"]
                if xbox_controller.get_button(5):
                    if not rb_held:
                        current_index = weapon_order.index(mode)
                        next_index = (current_index + 1) % len(weapon_order)
                        apply_weapon_mode(weapon_order[next_index])
                        rb_held = True
                else: rb_held = False

                if xbox_controller.get_button(4):
                    if not lb_held:
                        current_index = weapon_order.index(mode)
                        next_index = (current_index - 1) % len(weapon_order)
                        apply_weapon_mode(weapon_order[next_index])
                        lb_held = True
                else: lb_held = False
            except: pass

    if not game_started:
        mouse.locked = False
        return

    if in_car:
        car.position += car.forward * (held_keys['w'] - held_keys['s']) * car_speed * time.dt
        car.rotation_y += (held_keys['d'] - held_keys['a']) * 70 * time.dt
        camera.world_position = car.world_position + car.up * 4 - car.forward * 8
        camera.look_at(car)
        player.position = car.position

    if shoot_cooldown > 0: shoot_cooldown -= time.dt

    if mouse.locked and not in_car:
        if mode != "green":
            if held_keys['left mouse'] or rt_pressed: shoot()
        else:
            if held_keys['left mouse']: shoot()
            if rt_pressed:
                if not rt_held:
                    shoot(); rt_held = True
            else: rt_held = False
            
    if mode == "green" and mouse.locked and not in_car and (held_keys['right mouse'] or lt_pressed):
        camera.fov = 25
        gun.position = (0.15, -0.1, 0.3)  
        if not was_zoomed:
            if sound_enabled and zoom_sound and zoom_sound.clip:
                try: zoom_sound.time = 0; zoom_sound.play()
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
    global in_car, radio_on

    if key == 'q' or key == 'Q': application.quit()

    if not game_started:
        return 

    if key == 'm' and not in_car:
        phone_ui.enabled = not phone_ui.enabled
        mouse.locked = not phone_ui.enabled
        if phone_ui.enabled:
            player.enabled = False
            gun.enabled = False
            crosshair.enabled = False
        else:
            player.enabled = True
            gun.enabled = True
            crosshair.enabled = True

    if key == 'e' and not phone_ui.enabled:
        if not in_car and distance(car.position, player.position) < 4:
            in_car = True
            player.enabled = False
            gun.enabled = False
            crosshair.enabled = False
            car_ui_text.enabled = True
            car_ui_text.text = "Οδηγείς [v0.0.7]. [E] για Έξοδο | [R] για Ραδιόφωνο"
        elif in_car:
            in_car = False
            player.enabled = True
            gun.enabled = True
            crosshair.enabled = True
            player.position = car.position + (3, 1, 0)
            car_ui_text.enabled = False
            camera.parent = player.camera_pivot
            camera.position = (0, 0, 0)
            camera.rotation = (0, 0, 0)

    if in_car and key == 'r':
        radio_on = not radio_on
        if radio_on: car_ui_text.text = "Ραδιόφωνο: [ON] Παίζει: Piui Tic Tac (Remix)"
        else: car_ui_text.text = "Ραδιόφωνο: [OFF]"

    if key == 'r' and not in_car and not phone_ui.enabled: respawn()
        
    if not in_car and not phone_ui.enabled:
        if key == '1': apply_weapon_mode("red")
        elif key == '2': apply_weapon_mode("yellow")
        elif key == '3': apply_weapon_mode("green")

    if key == 'escape':
        if not phone_ui.enabled: mouse.locked = not mouse.locked

# --- GITHUB UPDATE CHECKER ---
def check_for_updates():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            releases = response.json()
            if not isinstance(releases, list) or not releases: return

            latest_version = releases[0].get('tag_name', '')
            if latest_version and latest_version != CURRENT_VERSION:
                all_notes = ""
                for rel in releases:
                    tag = rel.get('tag_name', 'Unknown')
                    body = rel.get('body', 'Χωρίς σημειώσεις.')
                    all_notes += f"--- {tag} ---\n{body}\n\n"
                    
                show_update_popup(latest_version, all_notes)
    except: pass

def show_update_popup(version, notes):
    mouse.locked = False
    overlay = Entity(model='quad', scale=(2, 2), color=color.rgba(0, 0, 0, 0.7), parent=camera.ui, z=-1)
    popup_panel = Entity(model='quad', scale=(0.85, 0.75), color=color.dark_gray, parent=camera.ui)
    Text(text=f"NEW UPDATE: {version}!", position=(0, 0.3), origin=(0, 0), scale=1.4, color=color.gold, parent=popup_panel)
    clean_notes = notes[:450] + "..." if len(notes) > 450 else notes
    Text(text=clean_notes, position=(0, 0.05), origin=(0, 0), scale=0.8, color=color.white, parent=popup_panel)
    close_btn = Button(text='OK / CLOSE', scale=(0.3, 0.08), position=(0, -0.28), color=color.lime, parent=popup_panel)

    def close_popup():
        destroy(overlay)
        destroy(popup_panel)
    close_btn.on_click = close_popup

check_for_updates()
app.run()
