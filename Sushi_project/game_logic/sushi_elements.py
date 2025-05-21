# game_logic/sushi_elements.py

import pygame
import os  # 确保 os 被导入
from config import (
    RICE, TOPPINGS, BLACK, SUSHI_TYPES, DRINK_TYPES,
    UI_IMAGES_DIR,  # 默认UI图片目录
    SUSHI_IMAGES_DIR,    # 新增的寿司图片目录
    RICE_BALL_ON_BOARD_SIZE, TOPPING_ON_BOARD_SIZE  # 导入在菜板上显示的大小
)

# --- 辅助函数：加载并缩放图片 (可以放在文件顶部或 utils.py 中) ---


def load_scaled_image(image_filename, size=None, directory=UI_IMAGES_DIR):  # 默认目录是 UI_IMAGES_DIR
    """加载图片，如果提供了size则进行缩放，可以指定目录"""
    if not image_filename:  # 如果文件名为空，直接返回None
        print("警告: load_scaled_image 收到空文件名。")
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


class ClickableElement:
    def __init__(self, name, item_type, position, size, color_placeholder, image_filename=None):  # color_placeholder 改名
        self.name = name
        self.item_type = item_type
        self.rect = pygame.Rect(position, size)
        self.color_placeholder = color_placeholder  # 用于图片加载失败时的备选颜色
        self.image = None
        if image_filename:
            self.image = load_scaled_image(image_filename, size, directory=UI_IMAGES_DIR)  # 使用辅助函数加载并缩放

    def draw(self, surface, font=None):
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        else:  # 图片加载失败，绘制占位符
            pygame.draw.rect(surface, self.color_placeholder, self.rect)
            if font:
                text_surf = font.render(self.name, True, BLACK)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class RiceContainer(ClickableElement):
    def __init__(self, position, size, image_filename):  # 必须传入图片名
        # RICE["color"] 不再需要，因为我们用图片
        super().__init__("米饭", "rice", position, size, (200, 200, 200), image_filename)


class ToppingContainer(ClickableElement):
    def __init__(self, topping_key, position, size, image_filename):  # 必须传入图片名
        # TOPPINGS[topping_key]["color"] 不再需要
        super().__init__(TOPPINGS[topping_key]["name"], topping_key,
                         position, size, (200, 200, 200), image_filename)
        self.topping_key = topping_key

# DrinkDispenser 暂时不变


class CuttingBoard:
    def __init__(self, position, size, image_filename):
        self.rect = pygame.Rect(position, size)
        self.image = load_scaled_image(image_filename, size)  # 加载菜板背景图
        if not self.image:  # 如果菜板图片加载失败，给一个占位颜色
            self.color_placeholder = (210, 180, 140)

        self.has_rice = False
        self.topping_key = None
        self.message = "菜板 (空)"

        # 饭团图片从SUSHI_IMAGES_DIR 加载
        self.rice_ball_image = load_scaled_image(
            RICE["image_file"], RICE_BALL_ON_BOARD_SIZE,directory=SUSHI_IMAGES_DIR)
        
        # 配料片图片从SUSHI_IMAGES_DIR 加载
        self.topping_images = {}
        for key, data in TOPPINGS.items():
            img = load_scaled_image(data["image_file"], TOPPING_ON_BOARD_SIZE,directory=SUSHI_IMAGES_DIR)
            if img:
                self.topping_images[key] = img

    # add_rice, add_topping, get_sushi_name, is_complete, clear 方法保持不变

    def add_rice(self):  # (无变化)
        if not self.has_rice:
            self.has_rice = True
            self.message = "米饭已放上"
            print("菜板：米饭已添加")
            return True
        print("菜板：已经有米饭了")
        return False

    def add_topping(self, topping_key):  # (无变化)
        if self.has_rice and not self.topping_key:
            self.topping_key = topping_key
            self.message = f"米饭 + {TOPPINGS[topping_key]['name']}"
            print(f"菜板：{TOPPINGS[topping_key]['name']} 已添加")
            return True
        elif not self.has_rice:
            print("菜板：请先放米饭")
        elif self.topping_key:
            print("菜板：已经有配料了")
        return False

    def get_sushi_name(self):  # (无变化)
        if self.has_rice and self.topping_key:
            return self.topping_key
        return None

    def is_complete(self):  # (无变化)
        return self.has_rice and self.topping_key is not None

    def clear(self):  # (无变化)
        self.has_rice = False
        self.topping_key = None
        self.message = "菜板 (空)"
        print("菜板：已清空")

    def draw(self, surface, font):
        # 1. 绘制菜板背景图 (或占位符)
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color_placeholder, self.rect)

        # 2. 在菜板上绘制米饭 (如果存在且图片加载成功)
        rice_pos_x = self.rect.centerx - RICE_BALL_ON_BOARD_SIZE[0] // 2
        rice_pos_y = self.rect.centery - \
            RICE_BALL_ON_BOARD_SIZE[1] // 2 - 10  # 稍微偏上一点

        if self.has_rice and self.rice_ball_image:
            surface.blit(self.rice_ball_image, (rice_pos_x, rice_pos_y))

            # 3. 在米饭上绘制配料 (如果存在且图片加载成功)
            if self.topping_key and self.topping_key in self.topping_images:
                topping_image = self.topping_images[self.topping_key]
                # 配料通常在米饭的中心偏上一点点
                topping_pos_x = self.rect.centerx - \
                    TOPPING_ON_BOARD_SIZE[0] // 2
                topping_pos_y = rice_pos_y - \
                    TOPPING_ON_BOARD_SIZE[1] // 2 +25  # 调整这个值使配料在米饭上合适位置
                surface.blit(topping_image, (topping_pos_x, topping_pos_y))

        # 4. 绘制菜板状态文本
        text_surf = font.render(self.message, True, BLACK)
        text_rect = text_surf.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))  # 文本位置调整
        surface.blit(text_surf, text_rect)


class PlayerHand:
    def __init__(self):
        self.held_sushi_type = None  # 例如 "salmon"
        self.held_drink_type = None  # 例如 "sake"

        # 预加载所有完整寿司的图片
        self.complete_sushi_images = {}
        for key, data in SUSHI_TYPES.items():
            # 完整寿司图片大小可以根据需要调整，这里暂时不缩放，用原始大小
            img = load_scaled_image(data["image_file"],directory=SUSHI_IMAGES_DIR)  # 不指定size，用原始大小
            if img:
                self.complete_sushi_images[key] = img

        # (之后会预加载饮品图片)
        self.drink_images = {}

    # pickup_sushi, pickup_drink, clear_sushi, clear_drink, clear_all 方法保持不变

    def pickup_sushi(self, sushi_type):
        if not self.held_sushi_type:
            self.held_sushi_type = sushi_type
            print(
                f"玩家拿起: {SUSHI_TYPES.get(sushi_type, {}).get('name', sushi_type)}")
            return True
        print("玩家手上已经有寿司了!")
        return False

    def pickup_drink(self, drink_type):
        if not self.held_drink_type:
            self.held_drink_type = drink_type
            print(
                f"玩家拿起: {DRINK_TYPES.get(drink_type, {}).get('name', drink_type)}")
            return True
        print("玩家手上已经有饮品了!")
        return False

    def clear_sushi(self): self.held_sushi_type = None
    def clear_drink(self): self.held_drink_type = None

    def clear_all(self):
        self.held_sushi_type = None
        self.held_drink_type = None

    def draw(self, surface, font, position):
        # 绘制手持的寿司图片
        if self.held_sushi_type and self.held_sushi_type in self.complete_sushi_images:
            sushi_img = self.complete_sushi_images[self.held_sushi_type]
            # 图片绘制位置可以基于传入的 position，或者固定在屏幕某处
            # 这里简单地在 position 绘制，可能需要调整图片大小或 position
            surface.blit(sushi_img, position)
            # 如果还想显示文字，可以在图片旁边或下方绘制
            # text_s = f"寿司: {SUSHI_TYPES[self.held_sushi_type]['name']}"
            # text_surf_s = font.render(text_s, True, BLACK)
            # surface.blit(text_surf_s, (position[0] + sushi_img.get_width() + 5, position[1]))

        # (之后绘制手持的饮品图片)

        # 如果什么都没拿，或者只想显示文字状态，可以绘制文字
        elif not self.held_sushi_type and not self.held_drink_type:
            text_surf = font.render("双手空空", True, BLACK)
            text_rect = text_surf.get_rect(topleft=position)
            surface.blit(text_surf, text_rect)

        # 如果只想显示一个总的状态文本（可以替代上面的图片绘制逻辑，如果图片显示复杂）
        # s_name = SUSHI_TYPES.get(self.held_sushi_type, {}).get("name", "") if self.held_sushi_type else ""
        # d_name = DRINK_TYPES.get(self.held_drink_type, {}).get("name", "") if self.held_drink_type else ""
        # parts = []
        # if s_name: parts.append(f"寿司: {s_name}")
        # if d_name: parts.append(f"饮品: {d_name}")
        # display_message = "手持: " + ", ".join(parts) if parts else "双手空空"
        # text_surf = font.render(display_message, True, BLACK)
        # text_rect = text_surf.get_rect(topleft=position)
        # surface.blit(text_surf, text_rect)
