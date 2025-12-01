# game_logic/sushi_elements.py

import pygame
import os
from PIL import Image  # +++ 导入 Pillow 库的 Image 模块 +++
from config import (
    RICE, TOPPINGS, BLACK, SUSHI_TYPES, DRINK_TYPES,
    UI_IMAGES_DIR, SUSHI_IMAGES_DIR, DRINK_IMAGES_DIR, # 添加 DRINK_IMAGES_DIR
    RICE_BALL_ON_BOARD_SIZE, TOPPING_ON_BOARD_SIZE,
    HELD_ITEM_IMAGE_SIZE # 导入手持物品大小
)

# --- 辅助函数：加载并缩放图片 (保持不变) ---
def load_scaled_image(image_filename, size=None, directory=UI_IMAGES_DIR):
    """加载图片，如果提供了size则进行缩放，可以指定目录"""
    if not image_filename:
        print(f"警告: load_scaled_image 收到空文件名。")
        return None
    path = os.path.join(directory, image_filename)
    try:
        image = pygame.image.load(path)
        if image.get_alpha() is None:
            image = image.convert()
        else:
            image = image.convert_alpha()

        if size:
            image = pygame.transform.scale(image, size)
        return image
    except pygame.error as e:
        print(f"无法加载或缩放图片 {path}: {e}")
        return None

# +++ 新增辅助函数：加载 GIF 动画帧 +++
def load_gif_frames(gif_filename, target_size, directory=UI_IMAGES_DIR):
    """加载GIF文件并返回一个包含所有帧的Pygame Surface列表。"""
    if not gif_filename:
        print("警告: load_gif_frames 收到空文件名。")
        return []
    path = os.path.join(directory, gif_filename)
    frames = []
    try:
        with Image.open(path) as img:
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                # 将Pillow帧转换为RGBA（如果不是）以确保与Pygame兼容性好
                pil_frame = img.convert('RGBA')
                pygame_surface = pygame.image.fromstring(
                    pil_frame.tobytes(), pil_frame.size, pil_frame.mode
                )
                if target_size:
                    pygame_surface = pygame.transform.scale(
                        pygame_surface, target_size)
                frames.append(pygame_surface)
        if not frames:
            print(f"警告: 未能从 {path} 加载任何帧。")
        return frames
    except FileNotFoundError:
        print(f"GIF 文件未找到: {path}")
        return []
    except Exception as e:
        print(f"加载或处理GIF {path} 时出错: {e}")
        return []

class ClickableElement:
    # ... (保持不变) ...
    def __init__(self, name, item_type, position, size, color_placeholder, image_filename=None, directory=UI_IMAGES_DIR): # 添加 directory 参数
        self.name = name
        self.item_type = item_type # "rice", "topping", "drink_dispenser"
        self.rect = pygame.Rect(position, size)
        self.color_placeholder = color_placeholder
        self.image = None
        if image_filename:
            self.image = load_scaled_image(image_filename, size, directory=directory) # 使用传入的 directory

    def draw(self, surface, font=None):
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color_placeholder, self.rect)
            if font:
                text_surf = font.render(self.name, True, BLACK)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class RiceContainer(ClickableElement):
    # ... (保持不变，确保构造函数调用 super 时传递 UI_IMAGES_DIR) ...
    def __init__(self, position, size, image_filename):
        super().__init__("米饭", "rice", position, size, (200, 200, 200), image_filename, directory=UI_IMAGES_DIR)


class ToppingContainer(ClickableElement):
    # ... (保持不变，确保构造函数调用 super 时传递 UI_IMAGES_DIR) ...
    def __init__(self, topping_key, position, size, image_filename):
        super().__init__(TOPPINGS[topping_key]["name"], topping_key, # item_type 将是 topping_key
                         position, size, (200, 200, 200), image_filename, directory=UI_IMAGES_DIR)
        self.topping_key = topping_key # 保留这个用于特定逻辑


# +++ 新增 DrinkDispenser 类 +++
class DrinkDispenser(ClickableElement):
    def __init__(self, drink_key, position, size, image_filename):
        # item_type 设置为 "drink_dispenser" 用于区分，或者直接用 drink_key
        super().__init__(DRINK_TYPES[drink_key]["name"], drink_key, # item_type 现在是 drink_key
                         position, size, (100, 100, 255), image_filename, directory=UI_IMAGES_DIR)
        self.drink_key = drink_key # 这是该饮品机提供的饮品类型


class CuttingBoard:
    def __init__(self, position, size, image_filename):
        self.rect = pygame.Rect(position, size)
        self.image = load_scaled_image(image_filename, size, directory=UI_IMAGES_DIR) # 指定菜板图片目录
        if not self.image:
            self.color_placeholder = (210, 180, 140)

        self.has_rice = False
        self.topping_key = None
        self.message = "菜板 (空)"

        self.rice_ball_image = load_scaled_image(
            RICE["image_file"], RICE_BALL_ON_BOARD_SIZE, directory=SUSHI_IMAGES_DIR)

        self.topping_images = {}
        for key, data in TOPPINGS.items():
            img = load_scaled_image(data["image_file"], TOPPING_ON_BOARD_SIZE, directory=SUSHI_IMAGES_DIR)
            if img:
                self.topping_images[key] = img

    def add_rice(self):
        if not self.has_rice:
            self.has_rice = True
            self.message = "米饭已放上"
            #print("菜板：米饭已添加")
            return True
        #print("菜板：已经有米饭了")
        return False

    def add_topping(self, topping_key):
        if self.has_rice and not self.topping_key:
            self.topping_key = topping_key
            self.message = f"米饭 + {TOPPINGS[topping_key]['name']}"
            #print(f"菜板：{TOPPINGS[topping_key]['name']} 已添加")
            return True
        elif not self.has_rice:
            print("菜板：请先放米饭")
        elif self.topping_key:
            print("菜板：已经有配料了")
        return False

    def get_sushi_name(self):
        if self.has_rice and self.topping_key:
            return self.topping_key # 返回的是 topping_key, 例如 "salmon"
        return None

    def is_complete(self):
        return self.has_rice and self.topping_key is not None

    def clear(self):
        self.has_rice = False
        self.topping_key = None
        self.message = "菜板 (空)"
        #print("菜板：已清空")

    def draw(self, surface, font):
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color_placeholder, self.rect)

        rice_pos_x = self.rect.centerx - RICE_BALL_ON_BOARD_SIZE[0] // 2
        rice_pos_y = self.rect.centery - \
            RICE_BALL_ON_BOARD_SIZE[1] // 2 - 10

        if self.has_rice and self.rice_ball_image:
            surface.blit(self.rice_ball_image, (rice_pos_x, rice_pos_y))

            if self.topping_key and self.topping_key in self.topping_images:
                topping_image = self.topping_images[self.topping_key]
                topping_pos_x = self.rect.centerx - \
                    TOPPING_ON_BOARD_SIZE[0] // 2
                topping_pos_y = rice_pos_y - \
                    TOPPING_ON_BOARD_SIZE[1] // 2 + 25
                surface.blit(topping_image, (topping_pos_x, topping_pos_y))

        text_surf = font.render(self.message, True, BLACK)
        text_rect = text_surf.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))
        surface.blit(text_surf, text_rect)


class PlayerHand:
    def __init__(self):
        self.held_item_category = None  # "sushi" 或 "drink"
        self.held_item_key = None       # 例如 "salmon" (寿司类型), "sake" (饮品类型)
        self.held_item_image = None     # 当前手持物品的 pygame.Surface 对象
        self.is_holding = False

        self.complete_sushi_images = {}
        for key, data in SUSHI_TYPES.items():
            img = load_scaled_image(data["image_file"], HELD_ITEM_IMAGE_SIZE, directory=SUSHI_IMAGES_DIR) # 使用 HELD_ITEM_IMAGE_SIZE
            if img:
                self.complete_sushi_images[key] = img
            else:
                print(f"警告: 玩家手持寿司图片 '{data['image_file']}' 加载失败 for key '{key}'")


        # +++ 预加载饮品图片 (用于手持) +++
        self.drink_images = {}
        for key, data in DRINK_TYPES.items():
            # 饮品图片从 DRINK_IMAGES_DIR 加载
            img = load_scaled_image(data["image_file"], HELD_ITEM_IMAGE_SIZE, directory=DRINK_IMAGES_DIR) # 使用 HELD_ITEM_IMAGE_SIZE
            if img:
                self.drink_images[key] = img
            else:
                print(f"警告: 玩家手持饮品图片 '{data['image_file']}' 加载失败 for key '{key}'")


    def pickup_sushi(self, sushi_key):
        if not self.is_holding:
            if sushi_key in self.complete_sushi_images:
                self.held_item_category = "sushi"
                self.held_item_key = sushi_key
                self.held_item_image = self.complete_sushi_images[sushi_key]
                self.is_holding = True
                #print(f"玩家拿起: {SUSHI_TYPES.get(sushi_key, {}).get('name', sushi_key)}")
                return True
            else:
                print(f"错误：无法找到寿司 '{sushi_key}' 的完整图片。")
        else:
            print("玩家手上已经有东西了！")
        return False

    # +++ 修改 pickup_drink 方法 +++
    def pickup_drink(self, drink_key):
        if not self.is_holding:
            if drink_key in self.drink_images:
                self.held_item_category = "drink"
                self.held_item_key = drink_key
                self.held_item_image = self.drink_images[drink_key]
                self.is_holding = True
                #print(f"玩家拿起: {DRINK_TYPES.get(drink_key, {}).get('name', drink_key)}")
                return True
            else:
                print(f"错误：无法找到饮品 '{drink_key}' 的手持图片。")
                # 打印 self.drink_images 帮助调试
                print(f"当前已加载的饮品图片: {list(self.drink_images.keys())}")
                print(f"尝试加载的饮品key: {drink_key}")
                # 检查 DRINK_TYPES 中是否有此 key 且 image_file 是否正确
                if drink_key in DRINK_TYPES:
                    print(f"DRINK_TYPES 中的图片文件名: {DRINK_TYPES[drink_key].get('image_file')}")
                else:
                    print(f"DRINK_TYPES 中不存在 key: {drink_key}")

        else:
            print("玩家手上已经有东西了！")
        return False

    def drop_item(self):
        if self.is_holding:
            category = self.held_item_category
            key = self.held_item_key
            #print(f"玩家放下: {key} ({category})")
            self.held_item_category = None
            self.held_item_key = None
            self.held_item_image = None
            self.is_holding = False
            return category, key
        return None, None

    def get_held_item_info(self):
        if self.is_holding:
            return self.held_item_category, self.held_item_key, self.held_item_image
        return None, None, None

    def draw(self, surface, mouse_pos, font_for_hud=None, hud_position=None):
        if self.is_holding and self.held_item_image:
            img_rect = self.held_item_image.get_rect(center=mouse_pos)
            surface.blit(self.held_item_image, img_rect)

        if font_for_hud and hud_position:
            message = "双手空空"
            if self.is_holding and self.held_item_key:
                item_name = ""
                if self.held_item_category == "sushi":
                    item_name = SUSHI_TYPES.get(self.held_item_key, {}).get('name', self.held_item_key)
                elif self.held_item_category == "drink":
                    item_name = DRINK_TYPES.get(self.held_item_key, {}).get('name', self.held_item_key)
                message = f"手持: {item_name}"
            text_surf = font_for_hud.render(message, True, BLACK)
            text_rect = text_surf.get_rect(topleft=hud_position)
            surface.blit(text_surf, text_rect)