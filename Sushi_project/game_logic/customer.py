# game_logic/customer.py

import pygame
import random
import os  # 确保导入 os
from config import (
    # SUSHI_IMAGES_DIR for items if needed
    SUSHI_TYPES, DRINK_TYPES, CUSTOMER_IMAGES_DIR, UI_IMAGES_DIR,
    CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_ANGRY_IMG_FILENAME,
    ORDER_BUBBLE_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, ORDER_BUBBLE_SIZE, ORDER_ITEM_IMAGE_SIZE,
    ORDER_BUBBLE_OFFSET_X, ORDER_BUBBLE_OFFSET_Y, BLACK, SMALL_FONT_SIZE,
    CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE #<--- 导入新的偏移量常量
)

# 从 sushi_elements.py 导入 load_scaled_image (或者在 utils.py 中定义并导入)
# 为了避免循环导入，如果 sushi_elements.py 也需要这个，最好把它放到一个共享的 utils.py
# 这里为了简单，我们重新定义或假设它可以被访问


def load_scaled_image(image_filename, size=None, directory=UI_IMAGES_DIR):
    if not image_filename:
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


class Customer:
    def __init__(self, spot_index, table_spot_rect, preloaded_sushi_images, preloaded_drink_images):
        self.spot_index = spot_index  # 顾客所在的位置索引
        # 顾客图片的显示矩形
        self.rect = pygame.Rect((0, 0), CUSTOMER_IMAGE_SIZE)  # 先创建正确大小的矩形

        # 定位顾客图片的底部中点 (midbottom)
        # X 坐标：与桌子区的中心 X 坐标对齐
        # Y 坐标：桌子区的顶部 Y 坐标 减去 我们定义的偏移量
        self.rect.midbottom = (table_spot_rect.centerx,
                               table_spot_rect.top - CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE)

        self.state = "waiting"  # "waiting", "happy", "angry", "leaving", "empty"
        self.order = None      # {"sushi": "sushi_key", "drink": "drink_key"}
        self.order_fulfilled = False

        # 加载顾客状态图片 (GIF的第一帧)
        self.images = {
            "waiting": load_scaled_image(CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "happy": load_scaled_image(CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "angry": load_scaled_image(CUSTOMER_ANGRY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
        }
        self.current_image = self.images.get(self.state)

        # 加载订单气泡图片
        self.order_bubble_image = load_scaled_image(
            ORDER_BUBBLE_IMG_FILENAME, ORDER_BUBBLE_SIZE, directory=UI_IMAGES_DIR)

        # 引用预加载的食物和饮品图片 (从main.py传入)
        self.sushi_item_images = preloaded_sushi_images
        self.drink_item_images = preloaded_drink_images

       # 尝试从 config.py 加载字体路径，如果失败则使用系统默认
        font_path_from_config = os.path.join(os.path.dirname(os.path.dirname(
            __file__)), 'assets', 'fonts', 's.ttf')  # 假设config.py在项目根目录的上一级
        # 或者更简单的方式是，如果 small_font 已经在 main.py 中正确加载并可以传递给 Customer
        try:
            # 假设 small_font 已经在 main.py 中正确加载并可以传递给 Customer (或者在这里重新加载)
            from config import FONTS_DIR, CUSTOM_FONT_FILENAME  # 导入字体配置
            font_file = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
            if not os.path.exists(font_file):
                font_file = None  # fallback to sysfont
            self.small_font = pygame.font.Font(font_file, SMALL_FONT_SIZE)
        except Exception:
            self.small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)

        self.generate_order()  # 顾客一出现就生成订单

    def generate_order(self):
        # 从 SUSHI_TYPES 和 DRINK_TYPES 的键中随机选择
        sushi_key = random.choice(list(SUSHI_TYPES.keys()))
        drink_key = random.choice(list(DRINK_TYPES.keys()))
        self.order = {"sushi": sushi_key, "drink": drink_key}
        self.order_fulfilled = False  # 新订单，未完成
        self.set_state("waiting")  # 生成新订单后回到等待状态
        print(
            f"顾客 {self.spot_index+1} 点单: {SUSHI_TYPES[sushi_key]['name']} 和 {DRINK_TYPES[drink_key]['name']}")

    def set_state(self, new_state):
        if new_state in self.images:
            self.state = new_state
            self.current_image = self.images.get(self.state)
        else:
            print(f"警告: 顾客状态 '{new_state}' 没有对应的图片。")

    def check_order(self, served_sushi_key, served_drink_key=None):  # 暂时只处理寿司
        """检查服务是否满足订单，返回True/False"""
        if self.order and not self.order_fulfilled:
            sushi_match = (self.order["sushi"] == served_sushi_key)
            # drink_match = (self.order["drink"] == served_drink_key) # 之后加入饮品判断
            # if sushi_match and drink_match:
            if sushi_match:  # 暂时只看寿司
                self.order_fulfilled = True
                self.set_state("happy")
                print(f"顾客 {self.spot_index+1} 订单完成!")
                # 可以在这里设置一个计时器，一段时间后顾客离开或点新单
                # self.generate_order() # 简单起见，立即生成新订单
                return True
            else:
                self.set_state("angry")
                print(f"顾客 {self.spot_index+1} 订单错误!")
                return False
        return False

    def update(self):
        # 之后可以处理状态转换，例如生气一段时间后离开等
        pass

    def draw(self, surface):
        # 1. 绘制顾客图片
        if self.current_image:
            surface.blit(self.current_image, self.rect)
        else:  # 占位符
            pygame.draw.rect(surface, (0, 255, 0), self.rect, 2)

        # 2. 绘制订单气泡和订单内容 (如果顾客有订单且未完成)
        if self.order and not self.order_fulfilled and self.order_bubble_image:
            bubble_x = self.rect.centerx - \
                ORDER_BUBBLE_SIZE[0] // 2 + ORDER_BUBBLE_OFFSET_X
            bubble_y = self.rect.top + ORDER_BUBBLE_OFFSET_Y
            surface.blit(self.order_bubble_image, (bubble_x, bubble_y))

            # 在气泡内绘制订单项目图片
            item_start_x = bubble_x + 30  # 气泡内边距
            item_y = bubble_y + \
                (ORDER_BUBBLE_SIZE[1] - ORDER_ITEM_IMAGE_SIZE[1]) // 2  # 垂直居中

            # 绘制寿司图片
            sushi_key_ordered = self.order.get("sushi")
            if sushi_key_ordered and sushi_key_ordered in self.sushi_item_images:
                sushi_img = self.sushi_item_images[sushi_key_ordered]
                # 可能需要缩放寿司图片以适应订单气泡中的大小
                sushi_img_scaled = pygame.transform.scale(
                    sushi_img, ORDER_ITEM_IMAGE_SIZE)
                surface.blit(sushi_img_scaled, (item_start_x, item_y))
                item_start_x += ORDER_ITEM_IMAGE_SIZE[0] + 5  # 图片间距
            else:  # 如果图片找不到，显示文字
                sushi_text = self.small_font.render(SUSHI_TYPES.get(
                    sushi_key_ordered, {}).get('name', "未知寿司"), True, BLACK)
                surface.blit(sushi_text, (item_start_x, item_y +
                             ORDER_ITEM_IMAGE_SIZE[1]//2 - sushi_text.get_height()//2))
                item_start_x += sushi_text.get_width() + 10

            # 绘制 "+" 文字 (如果同时有寿司和饮品)
            plus_text = self.small_font.render("+", True, BLACK)
            surface.blit(plus_text, (item_start_x, item_y +
                         ORDER_ITEM_IMAGE_SIZE[1]//2 - plus_text.get_height()//2))
            item_start_x += plus_text.get_width() + 5

            # 绘制饮品图片
            drink_key_ordered = self.order.get("drink")
            if drink_key_ordered and drink_key_ordered in self.drink_item_images:
                drink_img = self.drink_item_images[drink_key_ordered]
                drink_img_scaled = pygame.transform.scale(
                    drink_img, ORDER_ITEM_IMAGE_SIZE)
                surface.blit(drink_img_scaled, (item_start_x, item_y))
            else:  # 如果图片找不到，显示文字
                drink_text = self.small_font.render(DRINK_TYPES.get(
                    drink_key_ordered, {}).get('name', "未知饮品"), True, BLACK)
                surface.blit(drink_text, (item_start_x, item_y +
                             ORDER_ITEM_IMAGE_SIZE[1]//2 - drink_text.get_height()//2))
