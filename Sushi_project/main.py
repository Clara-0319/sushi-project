# main.py

import pygame
import sys
import os
from config import *
from game_logic.sushi_elements import RiceContainer, ToppingContainer, CuttingBoard, PlayerHand

# --- Pygame 初始化 (不变) ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("我的寿司餐厅 - 已贴图")
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
try:
    font_file_path = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
    if not os.path.exists(font_file_path):
        raise FileNotFoundError(f"字体文件未找到: {font_file_path}")
    custom_font = pygame.font.Font(font_file_path, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.Font(font_file_path, LARGE_FONT_SIZE)
except Exception as e:
    print(f"加载自定义字体失败: {e}. 使用系统字体。")
    custom_font = pygame.font.SysFont(None, DEFAULT_FONT_SIZE)
    custom_font_large = pygame.font.SysFont(None, LARGE_FONT_SIZE)

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

# 存储当前放在“桌上”的寿司 (临时，用于演示放下效果)
# 结构: [(image, rect), (image, rect), ...]
sushi_on_tables = []

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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 鼠标左键

                    # 1. 如果玩家手上有物品，则此次点击是“放下”操作
                    if player_h.is_holding:
                        category, key = player_h.drop_item()
                        if category == "sushi":
                            # 模拟寿司落在桌上：获取放下的寿司图片，并记录其位置
                            # 这个寿司图片应该是完整的寿司图，PlayerHand内部已经处理了
                            # 我们需要从PlayerHand获取这个图片（或者在drop_item时返回）
                            # 为了简单，我们重新从 PlayerHand 的预加载字典里取一次
                            if key in player_h.complete_sushi_images:
                                dropped_sushi_img = player_h.complete_sushi_images[key]
                                # 寿司落在当前鼠标点击的位置
                                table_pos_rect = dropped_sushi_img.get_rect(
                                    center=mouse_pos)
                                sushi_on_tables.append(
                                    (dropped_sushi_img, table_pos_rect))
                                print(
                                    f"寿司 '{key}' 已放置在桌上 {table_pos_rect.topleft} (模拟)。")
                            else:
                                print(f"错误：找不到已放下寿司 '{key}' 的图片用于放置。")

                    # 2. 如果玩家手上没有物品，则此次点击是与场景交互
                    else:
                        clicked_on_ingredient_source = False
                        for element in game_elements:  # 米饭、配料容器
                            if element.is_clicked(mouse_pos):
                                clicked_on_ingredient_source = True
                                if isinstance(element, RiceContainer):
                                    cutting_b.add_rice()
                                elif isinstance(element, ToppingContainer):
                                    cutting_b.add_topping(element.topping_key)
                                # (之后处理饮品机)
                                break

                        # 如果没有点击食材源，再检查是否点击了菜板 (拿起寿司)
                        if not clicked_on_ingredient_source and cutting_b.rect.collidepoint(mouse_pos):
                            if cutting_b.is_complete():
                                sushi_to_pickup = cutting_b.get_sushi_name()
                                if sushi_to_pickup:
                                    if player_h.pickup_sushi(sushi_to_pickup):
                                        cutting_b.clear()
                                    # else: # player_h.pickup_sushi 内部会打印手上已有物品
                            else:
                                print("菜板上的寿司还没做好！")
                                # (可选：如果菜板上有东西但没完成，点击菜板可以清空？)
                                # if cutting_b.has_rice or cutting_b.topping_key:
                                #     cutting_b.clear()

    screen.fill(WHITE)
    if current_game_state == STATE_START_SCREEN:
        screen.blit(start_background_image, (0, 0))
        screen.blit(start_button_image, start_button_rect.topleft)
    elif current_game_state == STATE_GAME_RUNNING:
        screen.blit(restaurant_background_image, (0, 0))
        
        # 绘制场景元素 (容器, 菜板)
        for element in interactive_elements:
            element.draw(screen, custom_font)  # draw 方法现在会处理图片

        # 绘制放在“桌上”的寿司 (临时演示)
        for img, rect in sushi_on_tables:
            screen.blit(img, rect)

        # 绘制玩家手持物品 (图片跟随鼠标, 文字状态在左下角HUD)
        hud_pos = (20, SCREEN_HEIGHT - 40)  # 左下角HUD文字位置
        player_h.draw(screen, mouse_pos, font_for_hud=custom_font,
                      hud_position=hud_pos)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
