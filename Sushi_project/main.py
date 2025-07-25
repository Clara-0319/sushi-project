# main.py
import pygame
import sys
import os
import random
from config import *
# 从 sushi_elements 导入 DrinkDispenser
from game_logic.sushi_elements import RiceContainer, ToppingContainer, CuttingBoard, PlayerHand, DrinkDispenser
from game_logic.customer import Customer, load_scaled_image

# --- Pygame 初始化  ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("我的寿司餐厅")
clock = pygame.time.Clock()
pygame.mixer.init() # 初始化混音器模块

# --- 关卡存档读写函数 ---
def save_level(level):
    """将当前关卡数保存到文件"""
    try:
        with open(SAVE_FILE_NAME, "w") as f:
            f.write(str(level))
    except Exception as e:
        print(f"无法保存关卡数据到 {SAVE_FILE_NAME}: {e}")


def load_level():
    """从文件加载关卡数，如果文件不存在或无效则返回1"""
    if not os.path.exists(SAVE_FILE_NAME):
        return 1
    try:
        with open(SAVE_FILE_NAME, "r") as f:
            level = int(f.read().strip())
            return level if level > 0 else 1
    except (ValueError, IOError) as e:
        print(f"无法读取关卡数据或数据无效，从第一关开始: {e}")
        return 1

# --- 加载资源  ---
try:
    start_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, START_BG_IMG)
    start_background_image = pygame.image.load(start_bg_path).convert()
    restaurant_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, RESTAURANT_BG_IMG)
    restaurant_background_image = pygame.image.load(restaurant_bg_path).convert()
    start_button_path = os.path.join(UI_IMAGES_DIR, START_BUTTON_IMG)
    start_button_image = pygame.image.load(start_button_path).convert_alpha()
    start_button_rect = start_button_image.get_rect()
    reset_button_image = load_scaled_image(RESET_BUTTON_IMG, start_button_image.get_size(), directory=UI_IMAGES_DIR)
    reset_button_rect = reset_button_image.get_rect() if reset_button_image else pygame.Rect(0,0,0,0)
    
    # 全局计时器图标
    global_timer_icon_image = load_scaled_image(
        GLOBAL_TIMER_ICON_FILENAME, TIMER_ICON_SIZE, directory=UI_IMAGES_DIR)
    # 订单计时器图标 (传递给顾客)
    customer_order_timer_icon = load_scaled_image(
        ORDER_TIMER_ICON_FILENAME, ORDER_TIMER_ICON_SIZE, directory=UI_IMAGES_DIR)  # 使用新的常量

    times_up_image = load_scaled_image(
        TIMES_UP_IMG_FILENAME, TIMES_UP_IMAGE_SIZE, directory=UI_IMAGES_DIR)
    if times_up_image:
        times_up_rect = times_up_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    else:
        times_up_rect = pygame.Rect(0, 0, 0, 0)

    # +++ 加载小费、胜利、失败图片 +++
    tip_icon_image = load_scaled_image(
        TIP_ICON_FILENAME, TIP_ICON_SIZE, directory=UI_IMAGES_DIR)
    win_image = load_scaled_image(
        WIN_IMG_FILENAME, WIN_LOSE_IMAGE_SIZE, directory=UI_IMAGES_DIR)
    lose_image = load_scaled_image(
        LOSE_IMG_FILENAME, WIN_LOSE_IMAGE_SIZE, directory=UI_IMAGES_DIR)

    if win_image:
        win_rect = win_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    else:
        win_rect = pygame.Rect(0, 0, 0, 0)
    if lose_image:
        lose_rect = lose_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    else:
        lose_rect = pygame.Rect(0, 0, 0, 0)

    # +++ 加载背景音乐 +++
    try:
        start_bgm_path = os.path.join(SOUNDS_DIR, START_SCREEN_BGM)
        pygame.mixer.music.load(start_bgm_path)  # 先加载开始界面的音乐
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        # 注意：这里只是加载，不在初始化时播放，播放由状态切换控制
    except pygame.error as e:
        print(f"无法加载背景音乐 {START_SCREEN_BGM}: {e}")
        # 可以选择不退出，让游戏无背景音乐运行

    # 游戏运行时的BGM我们稍后在状态切换时加载和播放

    # +++ 加载音效 +++
    click_sound = None
    time_over_sound = None
    win_sound = None
    lose_sound = None
    try:
        # 点击音效
        click_sound_path = os.path.join(SOUNDS_DIR, CLICK_SOUND_FILENAME)
        if os.path.exists(click_sound_path):
            click_sound = pygame.mixer.Sound(click_sound_path)
            click_sound.set_volume(SFX_VOLUME)
        else:
            print(f"警告: 点击音效文件未找到: {click_sound_path}")

        # 时间到音效
        time_over_sound_path = os.path.join(
            SOUNDS_DIR, TIME_OVER_SOUND_FILENAME)
        if os.path.exists(time_over_sound_path):
            time_over_sound = pygame.mixer.Sound(time_over_sound_path)
            time_over_sound.set_volume(SFX_VOLUME)
        else:
            print(f"警告: 时间到音效文件未找到: {time_over_sound_path}")

        # 胜利音效
        win_sound_path = os.path.join(SOUNDS_DIR, WIN_SOUND_FILENAME)
        if os.path.exists(win_sound_path):
            win_sound = pygame.mixer.Sound(win_sound_path)
            win_sound.set_volume(SFX_VOLUME)
        else:
            print(f"警告: 胜利音效文件未找到: {win_sound_path}")

        # 失败音效
        lose_sound_path = os.path.join(SOUNDS_DIR, LOSE_SOUND_FILENAME)
        if os.path.exists(lose_sound_path):
            lose_sound = pygame.mixer.Sound(lose_sound_path)
            lose_sound.set_volume(SFX_VOLUME)
        else:
            print(f"警告: 失败音效文件未找到: {lose_sound_path}")

    except pygame.error as e:
        print(f"无法加载音效: {e}")
    except Exception as e:
        print(f"加载音效时发生未知错误: {e}")

except pygame.error as e:  # Pygame 特有的加载错误
    print(f"Pygame 资源加载错误: {e}")
    pygame.quit()
    sys.exit()
except FileNotFoundError as e:  # 文件未找到错误
    print(f"资源文件未找到: {e}")
    pygame.quit()
    sys.exit()


# --- 加载字体 ---
custom_font = None
custom_font_large = None
small_font = None
try:
    font_file_path = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
    if not os.path.exists(font_file_path):
        print(f"警告: 自定义字体 '{CUSTOM_FONT_FILENAME}' 未找到。将使用系统字体。")
        font_file_path = None
    custom_font = pygame.font.Font(font_file_path, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.Font(font_file_path, LARGE_FONT_SIZE)
    small_font = pygame.font.Font(font_file_path, SMALL_FONT_SIZE)
except Exception as e:
    print(f"加载自定义字体失败: {e}. 使用系统字体。")
    custom_font = pygame.font.SysFont(None, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.SysFont(None, LARGE_FONT_SIZE)
    small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)

# --- 游戏对象初始化 ---
game_elements = []  # 所有可绘制的场景元素（不一定可交互）
interactive_elements = [] # 所有可点击的元素

# 米饭容器
rice_cont = RiceContainer(
    RICE_CONTAINER_POS,
    (INGREDIENT_WIDTH, INGREDIENT_HEIGHT),
    RICE_CONTAINER_IMG_FILENAME
)
# game_elements.append(rice_cont) # ClickableElement 会被加入 interactive_elements
interactive_elements.append(rice_cont)

# 配料容器
topping_configs = {
    "octopus": {"pos": TOPPING_OCTOPUS_POS, "img_file": OCTOPUS_CONTAINER_IMG_FILENAME},
    "scallop": {"pos": TOPPING_SCALLOP_POS, "img_file": SCALLOP_CONTAINER_IMG_FILENAME},
    "salmon": {"pos": TOPPING_SALMON_POS, "img_file": SALMON_CONTAINER_IMG_FILENAME},
    "tuna": {"pos": TOPPING_TUNA_POS, "img_file": TUNA_CONTAINER_IMG_FILENAME},
}
for key, config_val in topping_configs.items():
    tc = ToppingContainer(
        key,
        config_val["pos"],
        (INGREDIENT_WIDTH, INGREDIENT_HEIGHT),
        config_val["img_file"]
    )
    # game_elements.append(tc)
    interactive_elements.append(tc)

# +++ 饮品机初始化 +++
drink_dispensers = []
for drink_key, drink_data in DRINK_TYPES.items():
    dispenser = DrinkDispenser(
        drink_key,
        drink_data["dispenser_pos"],
        (DRINK_DISPENSER_WIDTH, DRINK_DISPENSER_HEIGHT),
        drink_data["dispenser_img"] # 使用 config.py 中为饮品机定义的图片
    )
    drink_dispensers.append(dispenser)
    interactive_elements.append(dispenser) # 加入可交互列表

# 菜板
cutting_b = CuttingBoard(
    CUTTING_BOARD_POS,
    (CUTTING_BOARD_IMG_WIDTH, CUTTING_BOARD_IMG_HEIGHT),
    CUTTING_BOARD_IMG_FILENAME
)
# cutting_b 不是直接的 ClickableElement，但它的 rect 用于检测点击
# game_elements.append(cutting_b) # CuttingBoard 有自己的 draw，不通过 game_elements 列表

# 玩家手持物品状态
player_h = PlayerHand()

# --- 预加载饮品图片 (用于订单气泡和手持) ---
# PlayerHand 内部已经加载了手持寿司和饮品图片
# Customer 构造时需要订单气泡用的图片
preloaded_sushi_images_for_order = {} # 用于订单气泡的寿司图片
for key, data in SUSHI_TYPES.items():
    img = load_scaled_image(data["image_file"], ORDER_ITEM_IMAGE_SIZE, directory=SUSHI_IMAGES_DIR)
    if img:
        preloaded_sushi_images_for_order[key] = img
    else:
        print(f"警告: 寿司图片 '{data['image_file']}' 加载失败，用于订单 {key}")

preloaded_drink_images_for_order = {} # 用于订单气泡的饮品图片
for key, data in DRINK_TYPES.items():
    img = load_scaled_image(data.get("image_file"), ORDER_ITEM_IMAGE_SIZE, directory=DRINK_IMAGES_DIR)
    if img:
        preloaded_drink_images_for_order[key] = img
    else:
        print(f"警告: 饮品图片 '{data.get('image_file')}' 加载失败，用于订单 {key}")


# --- 顾客区初始化 ---
customer_spot_rects = []
for pos in CUSTOMER_SPOT_POSITIONS:
    rect = pygame.Rect(pos, (CUSTOMER_SPOT_WIDTH, CUSTOMER_SPOT_HEIGHT))
    customer_spot_rects.append(rect)

customers = []
for i in range(NUM_CUSTOMER_SPOTS):
    cust = Customer(
        i,
        customer_spot_rects[i],
        preloaded_sushi_images_for_order,
        preloaded_drink_images_for_order,
        customer_order_timer_icon  # +++ 传递正确的订单计时器图标 +++
    )
    customers.append(cust)

last_customer_spawn_time = {}
for i in range(NUM_CUSTOMER_SPOTS):
    last_customer_spawn_time[i] = 0  # 初始化为0，确保游戏开始时可以生成


def get_customer_at_spot(spot_index):
    if 0 <= spot_index < len(customers):
        return customers[spot_index]
    return None


# --- 游戏状态和计时器变量 ---
current_game_state = STATE_START_SCREEN
current_level = load_level()  # +++ 游戏启动时加载关卡 +++
current_target_tips = 0  # 当前关卡的目标金额，将在 reset_game_state 中设置
game_start_time = 0  # 游戏开始的时刻 (pygame.time.get_ticks())
remaining_time = GAME_DURATION_SECONDS  # 剩余时间（秒）
total_tips = 0  # 新增：总小费
game_over_phase = ""  # 用于游戏结束时的阶段控制: "showing_times_up", "showing_result"
game_over_transition_timer = 0  # 用于 "Time's Up" 显示后的延迟
result_sound_played = False  # 确保胜利/失败音效只播放一次

# --- 按钮位置 ---
start_button_rect.centerx = SCREEN_WIDTH // 4
start_button_rect.centery = SCREEN_HEIGHT // 2 + 220
reset_button_rect.centerx = 3*SCREEN_WIDTH // 4
reset_button_rect.centery = SCREEN_HEIGHT // 2 + 220

# --- BGM 函数 ---
current_bgm = None  # 用于跟踪当前播放的BGM，避免重复加载


def play_bgm(bgm_filename, loops=-1):
    """播放指定的背景音乐"""
    global current_bgm
    if current_bgm == bgm_filename:  # 如果已经在播放同一首音乐，则不操作
        if not pygame.mixer.music.get_busy():  # 但如果停止了，就重新播放
            pygame.mixer.music.play(loops)
        return

    try:
        full_path = os.path.join(SOUNDS_DIR, bgm_filename)
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        pygame.mixer.music.play(loops)  # loops=-1 表示无限循环
        current_bgm = bgm_filename
        print(f"正在播放背景音乐: {bgm_filename}")
    except pygame.error as e:
        print(f"无法加载或播放背景音乐 {bgm_filename}: {e}")
        current_bgm = None  # 加载失败，清除当前BGM记录


def stop_bgm():
    """停止当前播放的背景音乐"""
    global current_bgm
    pygame.mixer.music.stop()
    current_bgm = None
    print("背景音乐已停止。")

# --- 游戏重置函数 (修改) ---


def reset_game_state():
    """重置游戏到当前关卡的初始状态"""
    global game_start_time, remaining_time, total_tips, game_over_phase, game_over_transition_timer, result_sound_played, current_target_tips

    # +++ 根据当前关卡计算目标金额 +++
    current_target_tips = INITIAL_TARGET_TIPS + \
        (current_level - 1) * TARGET_TIPS_INCREMENT

    game_start_time = pygame.time.get_ticks()
    remaining_time = GAME_DURATION_SECONDS
    total_tips = 0
    game_over_phase = ""
    game_over_transition_timer = 0
    result_sound_played = False
    player_h.drop_item()
    cutting_b.clear()
    current_ticks = pygame.time.get_ticks()
    for i, customer in enumerate(customers):
        customer.state = "empty"
        customer.order = None
        customer.order_fulfilled = False
        customer.sushi_received_key = None
        customer.drink_received_key = None
        customer.departure_timer_start = None
        customer.order_timer_start_ticks = None
        customer.order_remaining_seconds = ORDER_DURATION_SECONDS
        customer.current_animation_frame_index = 0
        customer.current_image = None
        last_customer_spawn_time[i] = current_ticks - \
            random.randint(0, NEW_CUSTOMER_SPAWN_DELAY_MAX_MS // 2)
    play_bgm(GAME_RUNNING_BGM)


# --- 游戏主循环 (完整替换) ---
play_bgm(START_SCREEN_BGM)
running = True
while running:
    current_time_ticks = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    # 1. 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if click_sound:
                    click_sound.play()

                if current_game_state == STATE_START_SCREEN:
                    # 点击 "开始" 按钮
                    if start_button_rect.collidepoint(mouse_pos):
                        reset_game_state()
                        current_game_state = STATE_GAME_RUNNING
                    # +++ 点击 "重置" 按钮 +++
                    elif reset_button_rect and reset_button_rect.collidepoint(mouse_pos):
                        current_level = 1
                        save_level(current_level)
                        reset_game_state()
                        current_game_state = STATE_GAME_RUNNING

                elif current_game_state == STATE_GAME_RUNNING:
                    # ... (游戏中的点击逻辑保持不变) ...
                    if player_h.is_holding:
                        served_to_customer_this_click = False
                        for i, spot_rect in enumerate(customer_spot_rects):
                            if spot_rect.collidepoint(mouse_pos):
                                customer_at_spot = get_customer_at_spot(i)
                                if customer_at_spot and customer_at_spot.state == "waiting" and not customer_at_spot.order_fulfilled:
                                    category, key = player_h.drop_item()
                                    if category and key:
                                        tip_from_customer = customer_at_spot.receive_item(
                                            item_category=category, item_key=key)
                                        total_tips += tip_from_customer
                                    served_to_customer_this_click = True
                                break
                    else:
                        clicked_on_interactive = False
                        for element in interactive_elements:
                            if element.is_clicked(mouse_pos):
                                clicked_on_interactive = True
                                if isinstance(element, RiceContainer):
                                    cutting_b.add_rice()
                                elif isinstance(element, ToppingContainer):
                                    cutting_b.add_topping(element.topping_key)
                                elif isinstance(element, DrinkDispenser):
                                    player_h.pickup_drink(element.drink_key)
                                break
                        if not clicked_on_interactive and cutting_b.rect.collidepoint(mouse_pos):
                            if cutting_b.is_complete():
                                sushi_to_pickup = cutting_b.get_sushi_name()
                                if sushi_to_pickup and player_h.pickup_sushi(sushi_to_pickup):
                                    cutting_b.clear()

                elif current_game_state == STATE_GAME_OVER:
                    if game_over_phase == "showing_result":
                        current_game_state = STATE_START_SCREEN
                        play_bgm(START_SCREEN_BGM)
                        result_sound_played = False

    # 2. 游戏逻辑更新
    if current_game_state == STATE_GAME_RUNNING:
        if game_start_time > 0:
            elapsed_seconds = (current_time_ticks - game_start_time) // 1000
            remaining_time = GAME_DURATION_SECONDS - elapsed_seconds
            if remaining_time <= 0:
                remaining_time = 0
                if current_game_state == STATE_GAME_RUNNING:
                    current_game_state = STATE_GAME_OVER
                    game_over_phase = "showing_times_up"
                    game_over_transition_timer = current_time_ticks
                    stop_bgm()
                    if time_over_sound:
                        time_over_sound.play()

        for i, customer in enumerate(customers):
            if customer.state != "empty":
                if customer.update():
                    if current_game_state == STATE_GAME_RUNNING:
                        last_customer_spawn_time[i] = current_time_ticks

        if current_game_state == STATE_GAME_RUNNING:
            for i, customer in enumerate(customers):
                if customer.state == "empty":
                    spawn_delay = random.randint(
                        NEW_CUSTOMER_SPAWN_DELAY_MIN_MS, NEW_CUSTOMER_SPAWN_DELAY_MAX_MS)
                    if current_time_ticks - last_customer_spawn_time[i] > spawn_delay:
                        if customer.generate_order():
                           last_customer_spawn_time[i] = current_time_ticks

    elif current_game_state == STATE_GAME_OVER:
        if game_over_phase == "showing_times_up":
            if current_time_ticks - game_over_transition_timer > TIMES_UP_DISPLAY_DURATION_MS:
                game_over_phase = "showing_result"
                if not result_sound_played:
                    # +++ 检查胜利条件并更新关卡 +++
                    if total_tips >= current_target_tips:
                        if win_sound:
                            win_sound.play()
                        current_level += 1  # 胜利，关卡+1
                        save_level(current_level)  # 保存新关卡
                    else:
                        if lose_sound:
                            lose_sound.play()
                        # 失败，关卡不变
                    result_sound_played = True

    # 3. 绘制阶段
    screen.fill(WHITE)

    if current_game_state == STATE_START_SCREEN:
        screen.blit(start_background_image, (0, 0))
        screen.blit(start_button_image, start_button_rect)
        if reset_button_image:
            screen.blit(reset_button_image, reset_button_rect)

        # 在开始界面也显示当前关卡
        level_text_start = custom_font.render(
            f"当前挑战: 第 {current_level} 关", True, BLACK)
        level_rect_start = level_text_start.get_rect(
            center=(SCREEN_WIDTH // 2, start_button_rect.top+130))
        screen.blit(level_text_start, level_rect_start)

    elif current_game_state == STATE_GAME_RUNNING or \
            (current_game_state == STATE_GAME_OVER and game_over_phase == "showing_times_up"):
        screen.blit(restaurant_background_image, (0, 0))

        if current_game_state == STATE_GAME_RUNNING:
            # ... (绘制游戏元素) ...
            for element in interactive_elements:
                element.draw(screen, custom_font)
            cutting_b.draw(screen, custom_font)
            for i, spot_rect in enumerate(customer_spot_rects):
                temp_surface = pygame.Surface(spot_rect.size, pygame.SRCALPHA)
                customer = get_customer_at_spot(i)
                color_to_fill = CUSTOMER_SPOT_COLOR_DEFAULT
                if customer:
                    if customer.state == "empty":
                        color_to_fill = CUSTOMER_SPOT_COLOR_EMPTY
                    elif customer.state == "waiting":
                        color_to_fill = CUSTOMER_SPOT_COLOR_WAITING
                    elif customer.state == "happy":
                        color_to_fill = CUSTOMER_SPOT_COLOR_HAPPY
                    elif customer.state == "angry":
                        color_to_fill = CUSTOMER_SPOT_COLOR_ANGRY
                temp_surface.fill(color_to_fill)
                screen.blit(temp_surface, spot_rect.topleft)
            for customer in customers:
                customer.draw(screen)
            hud_pos = (20, SCREEN_HEIGHT - 50)
            player_h.draw(screen, mouse_pos,
                          font_for_hud=small_font, hud_position=hud_pos)

        # HUD
        if global_timer_icon_image:
            screen.blit(global_timer_icon_image, TIMER_ICON_POS)
        minutes = max(0, remaining_time // 60)
        seconds = max(0, remaining_time % 60)
        timer_text_str = f"{minutes:02}:{seconds:02}"
        timer_surf = small_font.render(timer_text_str, True, BLACK)
        timer_text_rect = timer_surf.get_rect(midleft=(
            TIMER_ICON_POS[0] + TIMER_ICON_SIZE[0] + TIMER_TEXT_OFFSET_X, TIMER_ICON_POS[1] + TIMER_ICON_SIZE[1] // 2))
        screen.blit(timer_surf, timer_text_rect)

        if tip_icon_image:
            screen.blit(tip_icon_image, TIP_ICON_POS)
        # +++ 使用动态目标金额 +++
        tip_text_str = f"{total_tips} / {current_target_tips}"
        tip_surf = small_font.render(tip_text_str, True, GOLD)
        tip_text_rect = tip_surf.get_rect(midleft=(
            TIP_ICON_POS[0] + TIP_ICON_SIZE[0] + TIP_TEXT_OFFSET_X, TIP_ICON_POS[1] + TIP_ICON_SIZE[1] // 2))
        screen.blit(tip_surf, tip_text_rect)

        # +++ 绘制当前关卡数 +++
        level_text_surf = custom_font.render(
            f"关卡: {current_level}", True, BLACK)
        level_text_rect = level_text_surf.get_rect(
            center=(SCREEN_WIDTH // 2, 40))
        screen.blit(level_text_surf, level_text_rect)

        if current_game_state == STATE_GAME_OVER and game_over_phase == "showing_times_up":
            if times_up_image and times_up_rect:
                screen.blit(times_up_image, times_up_rect)
            wait_text = small_font.render("计算结果中...", True, BLACK)
            wait_rect = wait_text.get_rect(center=(
                SCREEN_WIDTH // 2, times_up_rect.bottom + 30 if times_up_rect.height > 0 else SCREEN_HEIGHT // 2 + 50))
            screen.blit(wait_text, wait_rect)

    elif current_game_state == STATE_GAME_OVER and game_over_phase == "showing_result":
        screen.blit(restaurant_background_image, (0, 0))
        result_image_to_blit, result_rect_to_use, message = None, None, ""

        if total_tips >= current_target_tips:
            result_image_to_blit, result_rect_to_use = win_image, win_rect
            message = f"胜利! 进入第 {current_level} 关! 点击继续."
        else:
            result_image_to_blit, result_rect_to_use = lose_image, lose_rect
            message = f"失败! 再挑战一次第 {current_level} 关. 点击重试."

        if result_image_to_blit and result_rect_to_use:
            screen.blit(result_image_to_blit, result_rect_to_use)
            msg_surf = custom_font.render(message, True, BLACK)
            msg_rect = msg_surf.get_rect(
                center=(SCREEN_WIDTH // 2, result_rect_to_use.bottom + 40))
            screen.blit(msg_surf, msg_rect)
        else:
            msg_surf = custom_font.render(message, True, BLACK)
            msg_rect = msg_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            screen.blit(msg_surf, msg_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

