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
except pygame.error as e:
    print(f"无法加载背景或按钮图片资源: {e}")
    pygame.quit()
    sys.exit()

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
    cust = Customer(i,
                    customer_spot_rects[i],
                    preloaded_sushi_images_for_order, # 传递预加载的寿司图片
                    preloaded_drink_images_for_order) # 传递预加载的饮品图片
    customers.append(cust)

def get_customer_at_spot(spot_index):
    if 0 <= spot_index < len(customers):
        return customers[spot_index]
    return None

# --- 游戏状态初始化 ---
current_game_state = STATE_START_SCREEN
start_button_rect.centerx = SCREEN_WIDTH // 2
start_button_rect.centery = SCREEN_HEIGHT // 2 + 220


# --- 游戏主循环 ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_game_state == STATE_START_SCREEN:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if start_button_rect.collidepoint(mouse_pos):
                        current_game_state = STATE_GAME_RUNNING
                        # TODO: 初始化游戏计时器等逻辑

        elif current_game_state == STATE_GAME_RUNNING:
            for customer in customers:
                customer.update()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 鼠标左键

                    # 1. 如果玩家手上有物品，则此次点击是“放下”到顾客区操作
                    if player_h.is_holding:
                        served_to_customer = False
                        for i, spot_rect in enumerate(customer_spot_rects):
                            if spot_rect.collidepoint(mouse_pos):
                                customer_at_spot = get_customer_at_spot(i)
                                if customer_at_spot and not customer_at_spot.order_fulfilled:
                                    category, key = player_h.drop_item() # 从手中移除物品
                                    if category and key: # 确保成功放下了物品
                                        # 调用顾客的 receive_item 方法
                                        customer_at_spot.receive_item(item_category=category, item_key=key)
                                        # receive_item 内部会处理状态和订单完成情况
                                    served_to_customer = True
                                elif customer_at_spot and customer_at_spot.order_fulfilled:
                                    print(f"顾客 {i+1} 的订单已完成。")
                                    # 物品仍在手中，因为没有调用 drop_item
                                else:
                                    print(f"顾客位 {i+1} 没有顾客或无法服务。")
                                break # 处理完一个顾客区点击就够了

                        if not served_to_customer:
                            # 如果点击的不是有效的顾客区，或者顾客已满足，可以选择让玩家“扔掉”物品或继续持有
                            # 当前 player_h.drop_item() 已经被调用（如果上面逻辑触发了）
                            # 为了避免物品丢失，如果没服务成功，应该让玩家重新拿起来，
                            # 或者在 drop_item 前就判断好。
                            # 一个简单的处理：如果没成功服务，就当是误操作，物品还在手上（除非上面已经drop了）
                            # 这部分逻辑在之前已经指出需要优化，我们先假设如果点击了非顾客区，物品就“放空”了
                            # player_h.drop_item() # 如果希望点击空白处放下物品，则取消注释
                            print("未点击到有效的顾客服务区，或该顾客订单已完成。")


                    # 2. 玩家手上没东西，与场景交互 (食材容器、饮品机、菜板)
                    else:
                        clicked_on_interactive = False
                        for element in interactive_elements: # 包含食材容器和饮品机
                            if element.is_clicked(mouse_pos):
                                clicked_on_interactive = True
                                if isinstance(element, RiceContainer):
                                    cutting_b.add_rice()
                                elif isinstance(element, ToppingContainer):
                                    cutting_b.add_topping(element.topping_key)
                                # +++ 处理点击饮品机 +++
                                elif isinstance(element, DrinkDispenser):
                                    player_h.pickup_drink(element.drink_key)
                                break # 点击了一个元素后就停止检查其他元素

                        if not clicked_on_interactive: # 如果没点到容器或饮品机，再检查菜板
                            if cutting_b.rect.collidepoint(mouse_pos):
                                if cutting_b.is_complete():
                                    sushi_to_pickup = cutting_b.get_sushi_name() # 这是 topping_key
                                    if sushi_to_pickup: # 确保 sushi_to_pickup 不是 None
                                        # PlayerHand 的 pickup_sushi 需要的是 SUSHI_TYPES 中的 key
                                        # 而 cutting_b.get_sushi_name() 返回的是 TOPPINGS 中的 key
                                        # 假设 topping_key 和 sushi_type_key 是一致的 (例如 "salmon")
                                        if player_h.pickup_sushi(sushi_to_pickup):
                                            cutting_b.clear()
                                # else: print("菜板上的寿司还没做好！")

    # --- 绘制阶段 ---
    screen.fill(WHITE) # 清屏
    if current_game_state == STATE_START_SCREEN:
        screen.blit(start_background_image, (0, 0))
        screen.blit(start_button_image, start_button_rect.topleft)

    elif current_game_state == STATE_GAME_RUNNING:
        screen.blit(restaurant_background_image, (0, 0))

        # 绘制所有可交互的UI元素 (米饭、配料、饮品机)
        for element in interactive_elements:
            element.draw(screen, custom_font)

        # 绘制菜板 (菜板有自己的 draw 方法，因为它比较特殊)
        cutting_b.draw(screen, custom_font)

        # 绘制顾客区占位符/桌子 (可选)
        for i, spot_rect in enumerate(customer_spot_rects):
            temp_surface = pygame.Surface(spot_rect.size, pygame.SRCALPHA)
            customer = get_customer_at_spot(i)
            color_to_fill = CUSTOMER_SPOT_COLOR # 默认颜色
            if customer:
                if customer.order_fulfilled:
                    color_to_fill = GREEN + (100,) # 开心绿色 (半透明)
                elif customer.sushi_received_key and customer.drink_received_key: # 都收到了但还没判断完成 (理论上不应该到这)
                    pass
                elif customer.sushi_received_key or customer.drink_received_key: # 收到一部分
                    color_to_fill = (255, 255, 0, 100) # 黄色提示 (半透明)

            temp_surface.fill(color_to_fill)
            screen.blit(temp_surface, spot_rect.topleft)
            # index_text = small_font.render(str(i + 1), True, BLACK)
            # screen.blit(index_text, index_text.get_rect(center=spot_rect.center))


        # 绘制顾客及其订单
        for customer in customers:
            if customer.state != "empty": # 假设 "empty" 状态的顾客不绘制
                customer.draw(screen)

        # 绘制玩家手持物品
        hud_pos = (20, SCREEN_HEIGHT - 50) # HUD文字位置调整
        player_h.draw(screen, mouse_pos, font_for_hud=small_font, hud_position=hud_pos)


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
