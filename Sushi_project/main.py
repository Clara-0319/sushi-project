# main.py

import pygame
import sys
import os
import random  # 确保导入 random
from config import *
from game_logic.sushi_elements import RiceContainer, ToppingContainer, CuttingBoard, PlayerHand
from game_logic.customer import Customer,load_scaled_image  # <--- 导入 Customer 类

# --- Pygame 初始化 (不变) ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("我的寿司餐厅 - 顾客点餐")
clock = pygame.time.Clock()

# --- 加载背景和按钮图片 (不变) ---
try:
    start_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, START_BG_IMG)
    start_background_image = pygame.image.load(start_bg_path).convert()
    restaurant_bg_path = os.path.join(BACKGROUND_IMAGES_DIR, RESTAURANT_BG_IMG)
    restaurant_background_image = pygame.image.load(
        restaurant_bg_path).convert()
    start_button_path = os.path.join(UI_IMAGES_DIR, START_BUTTON_IMG)
    start_button_image = pygame.image.load(start_button_path).convert_alpha()
    start_button_rect = start_button_image.get_rect()
except pygame.error as e:
    print(f"无法加载背景或按钮图片资源: {e}")
    pygame.quit()
    sys.exit()

# --- 加载字体 (不变) ---
custom_font = None
custom_font_large = None
small_font = None

try:
    font_file_path = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
    sys_font_path = None  # Pygame's default sysfont
    if not os.path.exists(font_file_path):
        print(f"警告: 自定义字体 '{CUSTOM_FONT_FILENAME}' 未找到。将使用系统字体。")
        font_file_path = sys_font_path  # Use None for SysFont

    custom_font = pygame.font.Font(font_file_path, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.Font(font_file_path, LARGE_FONT_SIZE)
    small_font = pygame.font.Font(font_file_path, SMALL_FONT_SIZE)  # For order text

except Exception as e:
    print(f"加载自定义字体失败: {e}. 使用系统字体。")
    custom_font = pygame.font.SysFont(None, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.SysFont(None, LARGE_FONT_SIZE)
    small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)

# --- 游戏对象初始化 (修改以使用图片文件名) ---
game_elements = []
interactive_elements = []

# 米饭容器
rice_cont = RiceContainer(
    RICE_CONTAINER_POS,
    (INGREDIENT_WIDTH, INGREDIENT_HEIGHT),  # 使用 config 中定义的容器尺寸
    RICE_CONTAINER_IMG_FILENAME  # 传入图片文件名
)
game_elements.append(rice_cont)
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
        (INGREDIENT_WIDTH, INGREDIENT_HEIGHT),  # 使用统一的容器尺寸
        config_val["img_file"]  # 传入图片文件名
    )
    game_elements.append(tc)
    interactive_elements.append(tc)

# 菜板
cutting_b = CuttingBoard(
    CUTTING_BOARD_POS,
    (CUTTING_BOARD_IMG_WIDTH, CUTTING_BOARD_IMG_HEIGHT),  # 使用菜板图片的尺寸
    CUTTING_BOARD_IMG_FILENAME  # 传入菜板图片文件名
)
interactive_elements.append(cutting_b)

# 玩家手持物品状态
player_h = PlayerHand()  # PlayerHand 内部加载自己的图片，不需要从外部传入

# --- 预加载饮品图片 ---
preloaded_drink_images_for_order = {}
for key, data in DRINK_TYPES.items():
    # 直接调用导入的 load_scaled_image 函数
    # 并使用 DRINK_IMAGES_DIR
    img = load_scaled_image(data.get("image_file"),
                            ORDER_ITEM_IMAGE_SIZE,
                            directory=DRINK_IMAGES_DIR)  # <--- 修改了这里
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
        i, customer_spot_rects[i], player_h.complete_sushi_images, preloaded_drink_images_for_order)
    customers.append(cust)

# served_sushi_at_spots 不再直接由 main.py 管理显示，由 Customer 对象自己管理和显示其订单满足状态
# 我们可能需要一个方法来获取某个位置的顾客对象
def get_customer_at_spot(spot_index):
    if 0 <= spot_index < len(customers):
        return customers[spot_index]
    return None

# --- 游戏状态初始化 (不变) ---
current_game_state = STATE_START_SCREEN
start_button_rect.centerx = SCREEN_WIDTH // 2
start_button_rect.centery = SCREEN_HEIGHT // 2 + 220

# def draw_text... (不变)

# --- 游戏主循环 (事件处理逻辑不变, 绘制逻辑会自动更新) ---
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

        elif current_game_state == STATE_GAME_RUNNING:
            # 更新顾客逻辑 (如果需要)
            for customer in customers:
                customer.update()  # 目前为空，但可以扩展

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 鼠标左键

                    # 1. 如果玩家手上有物品，则此次点击是“放下”到顾客区操作
                    if player_h.is_holding:
                        item_served_to_spot = False
                        for i, spot_rect in enumerate(customer_spot_rects):
                            if spot_rect.collidepoint(mouse_pos):
                                customer_at_spot = get_customer_at_spot(i)
                                if customer_at_spot and not customer_at_spot.order_fulfilled:  # 确保有顾客且订单未完成
                                    category, key = player_h.drop_item()  # 从手中移除物品
                                    if category == "sushi":
                                        # 调用顾客的 check_order 方法
                                        if customer_at_spot.check_order(served_sushi_key=key):
                                            # 订单正确，顾客变开心
                                            # 可以在这里添加得分等逻辑
                                            # 简单起见，让顾客在满足后一段时间后点新单
                                            # pygame.time.set_timer(pygame.USEREVENT + i, 3000, True) # 3秒后为顾客i生成新订单
                                            pass  # check_order 内部处理了状态
                                        else:
                                            # 订单错误，顾客变生气
                                            pass  # check_order 内部处理了状态
                                    # (之后处理饮品服务)
                                    item_served = True
                                elif customer_at_spot and customer_at_spot.order_fulfilled:
                                    print(f"顾客 {i+1} 的订单已完成，无需重复服务。")
                                    # 阻止玩家放下物品，让其仍在手中 (因为 drop_item 已经被调用了，所以需要重新拿起来)
                                    # 这个逻辑需要优化：应该先检查是否能服务，再drop_item
                                    # 暂时简单处理：如果订单已完成，物品就当“放空”了，没有返还
                                break
                        if not item_served:  # 如果没有点击到有效的、需要服务的顾客区
                            print("未点击到有效的顾客服务区，或该顾客订单已完成。物品仍在手中。")
                            # 为了让物品仍在手中，我们需要在 player_h.drop_item() 之前做判断
                            # 重构这部分逻辑：
                            # 1. 检测点击哪个顾客区
                            # 2. 获取该顾客
                            # 3. 如果顾客存在且订单未完成，才调用 player_h.drop_item() 并服务
                            # 当前的实现是先drop，再判断，如果服务失败，物品就没了。
                            # 这是一个待优化点。目前为了流程，先这样。
                    else:  # 玩家手上没东西，与场景交互
                        clicked_on_ingredient_source = False
                        for element in game_elements:
                            if element.is_clicked(mouse_pos):
                                clicked_on_ingredient_source = True
                                if isinstance(element, RiceContainer):
                                    cutting_b.add_rice()
                                elif isinstance(element, ToppingContainer):
                                    cutting_b.add_topping(element.topping_key)
                                break
                        if not clicked_on_ingredient_source and cutting_b.rect.collidepoint(mouse_pos):
                            if cutting_b.is_complete():
                                sushi_to_pickup = cutting_b.get_sushi_name()
                                if sushi_to_pickup and player_h.pickup_sushi(sushi_to_pickup):
                                    cutting_b.clear()
                            # else: print("菜板上的寿司还没做好！") # 这句可以去掉，因为视觉上能看出来

            # (可选) 处理自定义事件，例如顾客满足后一段时间生成新订单
            # if event.type >= pygame.USEREVENT and event.type < pygame.USEREVENT + NUM_CUSTOMER_SPOTS:
            #     customer_index = event.type - pygame.USEREVENT
            #     customer_to_reorder = get_customer_at_spot(customer_index)
            #     if customer_to_reorder and customer_to_reorder.order_fulfilled:
            #         customer_to_reorder.generate_order()
    screen.fill(WHITE)
    if current_game_state == STATE_START_SCREEN:
        screen.blit(start_background_image, (0, 0))
        screen.blit(start_button_image, start_button_rect.topleft)
    elif current_game_state == STATE_GAME_RUNNING:
        screen.blit(restaurant_background_image, (0, 0))
        
        # 绘制场景元素 (容器, 菜板)
        for element in interactive_elements:
            element.draw(screen, custom_font)  # draw 方法现在会处理图片

        # 绘制顾客区占位符 (可以保留用于调试或作为桌子视觉的一部分)
        for i, spot_rect in enumerate(customer_spot_rects):
            temp_surface = pygame.Surface(spot_rect.size, pygame.SRCALPHA)
            # 根据顾客订单是否完成改变桌子颜色
            customer = get_customer_at_spot(i)
            if customer and customer.order_fulfilled:
                temp_surface.fill(GREEN + (100,))  # 开心绿色
            else:
                temp_surface.fill(CUSTOMER_SPOT_COLOR)
            screen.blit(temp_surface, spot_rect.topleft)
            # index_text = small_font.render(str(i + 1), True, BLACK) # 使用 small_font
            # screen.blit(index_text, index_text.get_rect(center=spot_rect.center))

        # 绘制顾客及其订单
        for customer in customers:
            customer.draw(screen)  # Customer.draw 内部处理订单气泡

        # 绘制玩家手持物品 (图片跟随鼠标, 文字状态在左下角HUD)
        hud_pos = (20, SCREEN_HEIGHT - 40)  # 左下角HUD文字位置
        player_h.draw(screen, mouse_pos, font_for_hud=custom_font,
                      hud_position=hud_pos)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
