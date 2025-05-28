# main.py
import pygame
import sys
import os
import random
from config import *
# 从 sushi_elements 导入 DrinkDispenser
from game_logic.sushi_elements import RiceContainer, ToppingContainer, CuttingBoard, PlayerHand, DrinkDispenser
from game_logic.customer import Customer, load_scaled_image

# --- Pygame 初始化 (不变) ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("我的寿司餐厅 - 饮品服务")
clock = pygame.time.Clock()

# --- 加载资源 (大部分不变) ---
try:
    start_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, START_BG_IMG)
    start_background_image = pygame.image.load(start_bg_path).convert()
    restaurant_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, RESTAURANT_BG_IMG)
    restaurant_background_image = pygame.image.load(restaurant_bg_path).convert()
    start_button_path = os.path.join(UI_IMAGES_DIR, START_BUTTON_IMG)
    start_button_image = pygame.image.load(start_button_path).convert_alpha()
    start_button_rect = start_button_image.get_rect()

    # +++ 加载计时器和时间到图片 +++
    timer_icon_image = load_scaled_image(
        TIMER_ICON_FILENAME, TIMER_ICON_SIZE, directory=UI_IMAGES_DIR)
    times_up_image = load_scaled_image(
        TIMES_UP_IMG_FILENAME, TIMES_UP_IMAGE_SIZE, directory=UI_IMAGES_DIR)
    if times_up_image:  # 确保图片加载成功再获取rect
        times_up_rect = times_up_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    else:
        times_up_rect = None  # 或者设置一个默认的rect

except pygame.error as e:
    print(f"无法加载背景或按钮图片资源: {e}")
    pygame.quit()
    sys.exit()
except Exception as e:  # 捕获其他可能的加载错误
    print(f"加载资源时发生错误: {e}")
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
        i, customer_spot_rects[i], preloaded_sushi_images_for_order, preloaded_drink_images_for_order)
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
game_start_time = 0  # 游戏开始的时刻 (pygame.time.get_ticks())
remaining_time = GAME_DURATION_SECONDS  # 剩余时间（秒）

start_button_rect.centerx = SCREEN_WIDTH // 2
start_button_rect.centery = SCREEN_HEIGHT // 2 + 220


def reset_game_state():
    """重置游戏到初始运行状态"""
    global game_start_time, remaining_time
    game_start_time = pygame.time.get_ticks()
    remaining_time = GAME_DURATION_SECONDS
    player_h.drop_item()  # 清空玩家手中的物品
    cutting_b.clear()    # 清空菜板

    current_ticks = pygame.time.get_ticks()
    for i, customer in enumerate(customers):
        customer.state = "empty"  # 将所有顾客设置为空位
        customer.order = None
        customer.order_fulfilled = False
        customer.sushi_received_key = None
        customer.drink_received_key = None
        customer.departure_timer_start = None
        last_customer_spawn_time[i] = current_ticks - random.randint(
            0, NEW_CUSTOMER_SPAWN_DELAY_MAX_MS // 2)  # 错开初始生成时间

    # (可选) 清空小费等其他游戏变量
    print("游戏状态已重置")


# --- 游戏主循环 ---
running = True
while running:
    current_time_ticks = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_game_state == STATE_START_SCREEN:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if start_button_rect.collidepoint(mouse_pos):
                        current_game_state = STATE_GAME_RUNNING
                        reset_game_state()  # 重置游戏状态并开始计时
                        # 初始顾客生成现在由 reset_game_state 和后续的 update 循环处理

        elif current_game_state == STATE_GAME_RUNNING:
            # --- 计时器更新 ---
            if game_start_time > 0:  # 确保计时器已启动
                elapsed_seconds = (current_time_ticks -
                                   game_start_time) // 1000
                remaining_time = GAME_DURATION_SECONDS - elapsed_seconds
                if remaining_time <= 0:
                    remaining_time = 0
                    current_game_state = STATE_GAME_OVER
                    print("时间到! 游戏结束。")
                    # 可以在这里播放一个音效等

            # --- 顾客逻辑更新 ---
            for i, customer in enumerate(customers):
                if customer.state != "empty":
                    if customer.update():  # customer.update() 返回 True 表示顾客刚离开
                        print(f"座位 {i+1} 空出来了。")
                        last_customer_spawn_time[i] = current_time_ticks

            # --- 新顾客生成逻辑 ---
            for i, customer in enumerate(customers):
                if customer.state == "empty":
                    spawn_delay = random.randint(
                        NEW_CUSTOMER_SPAWN_DELAY_MIN_MS, NEW_CUSTOMER_SPAWN_DELAY_MAX_MS)
                    if current_time_ticks - last_customer_spawn_time[i] > spawn_delay:
                        if customer.generate_order():
                           last_customer_spawn_time[i] = current_time_ticks

            # --- 鼠标点击事件处理 ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if player_h.is_holding:
                        # ... (服务顾客逻辑，保持不变) ...
                        served_to_customer_this_click = False
                        for i, spot_rect in enumerate(customer_spot_rects):
                            if spot_rect.collidepoint(mouse_pos):
                                customer_at_spot = get_customer_at_spot(i)
                                if customer_at_spot and customer_at_spot.state == "waiting":
                                    category, key = player_h.drop_item()
                                    if category and key:
                                        customer_at_spot.receive_item(
                                            item_category=category, item_key=key)
                                    served_to_customer_this_click = True
                                elif customer_at_spot and customer_at_spot.order_fulfilled:
                                    print(f"顾客 {i+1} 的订单已处理。")
                                elif customer_at_spot and customer_at_spot.state != "waiting":
                                    print(
                                        f"顾客 {i+1} 当前不接受服务 (状态: {customer_at_spot.state})。")
                                break
                    else:  # 玩家手上没东西
                        # ... (与食材、饮品机、菜板交互的逻辑，保持不变) ...
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    current_game_state = STATE_START_SCREEN  # 点击后返回开始界面

    # --- 绘制阶段 ---
    screen.fill(WHITE)

    if current_game_state == STATE_START_SCREEN:
        screen.blit(start_background_image, (0, 0))
        screen.blit(start_button_image, start_button_rect.topleft)

    elif current_game_state == STATE_GAME_RUNNING:
        screen.blit(restaurant_background_image, (0, 0))

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
        player_h.draw(screen, mouse_pos, font_for_hud=small_font,
                      hud_position=hud_pos)

        # +++ 绘制计时器 +++
        if timer_icon_image:
            screen.blit(timer_icon_image, TIMER_ICON_POS)

        minutes = max(0, remaining_time // 60)  # 确保不显示负数
        seconds = max(0, remaining_time % 60)
        timer_text_str = f"{minutes:02}:{seconds:02}"
        timer_surf = small_font.render(timer_text_str, True, BLACK)
        # 文本位置在图标右侧，垂直居中对齐图标
        timer_text_rect = timer_surf.get_rect(midleft=(TIMER_ICON_POS[0] + TIMER_ICON_SIZE[0] + TIMER_TEXT_OFFSET_X,
                                                       TIMER_ICON_POS[1] + TIMER_ICON_SIZE[1] // 2))
        screen.blit(timer_surf, timer_text_rect)

    elif current_game_state == STATE_GAME_OVER:
        # 可以选择绘制游戏运行时的最后一帧，或者一个特定的游戏结束背景
        # 或者 game_over_background_image
        screen.blit(restaurant_background_image, (0, 0))

        if times_up_image and times_up_rect:
            screen.blit(times_up_image, times_up_rect)

        # 提示信息
        game_over_msg = "时间到! 点击任意位置返回主菜单"
        msg_surf = custom_font.render(game_over_msg, True, BLACK)
        msg_rect = msg_surf.get_rect(center=(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + times_up_rect.height // 2 + 40))  # 在图片下方
        screen.blit(msg_surf, msg_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

