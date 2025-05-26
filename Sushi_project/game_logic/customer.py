# game_logic/customer.py

import pygame
import random
import os
from config import (
    SUSHI_TYPES, DRINK_TYPES, CUSTOMER_IMAGES_DIR, UI_IMAGES_DIR, DRINK_IMAGES_DIR, # 添加 DRINK_IMAGES_DIR
    CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_ANGRY_IMG_FILENAME,
    ORDER_BUBBLE_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, ORDER_BUBBLE_SIZE, ORDER_ITEM_IMAGE_SIZE,
    ORDER_BUBBLE_OFFSET_X, ORDER_BUBBLE_OFFSET_Y, BLACK, SMALL_FONT_SIZE,
    CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE
)

# 确保 load_scaled_image 在这里可用 (如果它不在 utils.py 中)
# (load_scaled_image 函数定义保持不变)
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
        self.spot_index = spot_index
        self.rect = pygame.Rect((0, 0), CUSTOMER_IMAGE_SIZE)
        self.rect.midbottom = (table_spot_rect.centerx,
                               table_spot_rect.top - CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE)

        self.state = "waiting"  # "waiting", "happy", "angry", "leaving", "empty"
        self.order = None      # {"sushi": "sushi_key", "drink": "drink_key"}
        self.order_fulfilled = False

        # +++ 新增：记录已收到的物品 +++
        self.sushi_received_key = None
        self.drink_received_key = None

        self.images = {
            "waiting": load_scaled_image(CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "happy": load_scaled_image(CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "angry": load_scaled_image(CUSTOMER_ANGRY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
        }
        self.current_image = self.images.get(self.state)
        self.order_bubble_image = load_scaled_image(
            ORDER_BUBBLE_IMG_FILENAME, ORDER_BUBBLE_SIZE, directory=UI_IMAGES_DIR)

        self.sushi_item_images = preloaded_sushi_images # 用于订单气泡显示
        self.drink_item_images = preloaded_drink_images # 用于订单气泡显示

        try:
            from config import FONTS_DIR, CUSTOM_FONT_FILENAME
            font_file = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
            if not os.path.exists(font_file):
                font_file = None
            self.small_font = pygame.font.Font(font_file, SMALL_FONT_SIZE)
        except Exception:
            self.small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)

        self.generate_order()

    def generate_order(self):
        sushi_key = random.choice(list(SUSHI_TYPES.keys()))
        drink_key = random.choice(list(DRINK_TYPES.keys()))
        self.order = {"sushi": sushi_key, "drink": drink_key}
        self.order_fulfilled = False
        self.sushi_received_key = None # 重置已收到的物品
        self.drink_received_key = None
        self.set_state("waiting")
        print(
            f"顾客 {self.spot_index+1} 点单: {SUSHI_TYPES[sushi_key]['name']} 和 {DRINK_TYPES[drink_key]['name']}")

    def set_state(self, new_state):
        if new_state in self.images:
            self.state = new_state
            self.current_image = self.images.get(self.state)
        # else: # 允许设置 "leaving" 或 "empty" 等没有对应图片的状态
            # print(f"警告: 顾客状态 '{new_state}' 没有对应的图片。")


    # +++ 新增：接收物品并检查订单的方法 +++
    def receive_item(self, item_category, item_key):
        """顾客接收一个物品（寿司或饮品），并更新状态。"""
        if not self.order or self.order_fulfilled:
            print(f"顾客 {self.spot_index+1} 没有待处理订单或订单已完成。")
            return False # 不能接收物品

        item_correct = False
        if item_category == "sushi":
            if self.order["sushi"] == item_key:
                self.sushi_received_key = item_key
                item_correct = True
                print(f"顾客 {self.spot_index+1} 收到正确的寿司: {SUSHI_TYPES[item_key]['name']}")
            else:
                print(f"顾客 {self.spot_index+1} 收到错误的寿司: {SUSHI_TYPES.get(item_key, {}).get('name', '未知寿司')}")
        elif item_category == "drink":
            if self.order["drink"] == item_key:
                self.drink_received_key = item_key
                item_correct = True
                print(f"顾客 {self.spot_index+1} 收到正确的饮品: {DRINK_TYPES[item_key]['name']}")
            else:
                print(f"顾客 {self.spot_index+1} 收到错误的饮品: {DRINK_TYPES.get(item_key, {}).get('name', '未知饮品')}")

        if not item_correct:
            self.set_state("angry")
            # 错误惩罚：可以考虑是否清空已收到的正确物品，或增加等待时间等
            # self.sushi_received_key = None # 例如，送错一个就得重新送整套
            # self.drink_received_key = None
            return False

        # 检查订单是否完整
        if self.sushi_received_key == self.order["sushi"] and \
           self.drink_received_key == self.order["drink"]:
            self.order_fulfilled = True
            self.set_state("happy")
            print(f"顾客 {self.spot_index+1} 订单完整完成!")
            # TODO: 在这里触发小费计算和顾客离开的逻辑
            return True # 订单完整且正确

        return True # 物品正确，但订单未完整

    def update(self):
        # 可以在这里添加计时器逻辑，例如：
        # 如果生气状态持续过久，顾客离开
        # 如果开心状态（订单完成），一段时间后离开并空出位置
        pass

    def draw(self, surface):
        if self.current_image:
            surface.blit(self.current_image, self.rect)
        else:
            pygame.draw.rect(surface, (0, 255, 0) if self.state != "empty" else (50,50,50), self.rect, 2)


        if self.order and not self.order_fulfilled and self.order_bubble_image: # 只有未完成的订单才显示气泡
            bubble_x = self.rect.centerx - ORDER_BUBBLE_SIZE[0] // 2 + ORDER_BUBBLE_OFFSET_X
            bubble_y = self.rect.top + ORDER_BUBBLE_OFFSET_Y
            surface.blit(self.order_bubble_image, (bubble_x, bubble_y))

            item_start_x = bubble_x + 15  # 气泡内边距调整
            item_y_center = bubble_y + ORDER_BUBBLE_SIZE[1] // 2

            # 绘制寿司需求 (如果未收到或收到的不匹配，则显示；如果已正确收到，可以考虑打勾或变灰)
            sushi_key_ordered = self.order.get("sushi")
            sushi_display_img = None
            if sushi_key_ordered:
                if self.sushi_received_key == sushi_key_ordered: # 如果已正确收到寿司
                    # 可以加载一个“已完成”的标记或者让图片变灰暗
                    # 这里我们还是显示原图，但可以考虑加个对勾图片
                    sushi_display_img = self.sushi_item_images.get(sushi_key_ordered)
                    # pass # 或者不显示，或者显示一个打勾的图标
                else: # 未收到或收到错误的（错误情况由 receive_item 处理状态，这里只管显示需求）
                    sushi_display_img = self.sushi_item_images.get(sushi_key_ordered)

            if sushi_display_img:
                sushi_img_scaled = pygame.transform.scale(sushi_display_img, ORDER_ITEM_IMAGE_SIZE)
                sushi_rect = sushi_img_scaled.get_rect(centery=item_y_center)
                sushi_rect.left = item_start_x
                surface.blit(sushi_img_scaled, sushi_rect)
                item_start_x += ORDER_ITEM_IMAGE_SIZE[0] + 5
            elif sushi_key_ordered: # 图片加载失败，显示文字
                sushi_text = self.small_font.render(SUSHI_TYPES.get(sushi_key_ordered, {}).get('name', "寿司"), True, BLACK)
                text_rect = sushi_text.get_rect(centery=item_y_center, left=item_start_x)
                surface.blit(sushi_text, text_rect)
                item_start_x += text_rect.width + 10


            # 绘制 "+" 文字
            plus_text = self.small_font.render("+", True, BLACK)
            plus_rect = plus_text.get_rect(centery=item_y_center, left=item_start_x)
            surface.blit(plus_text, plus_rect)
            item_start_x += plus_rect.width + 5

            # 绘制饮品需求 (如果未收到或收到的不匹配，则显示)
            drink_key_ordered = self.order.get("drink")
            drink_display_img = None
            if drink_key_ordered:
                if self.drink_received_key == drink_key_ordered: # 如果已正确收到饮品
                    drink_display_img = self.drink_item_images.get(drink_key_ordered)
                    # pass
                else:
                    drink_display_img = self.drink_item_images.get(drink_key_ordered)

            if drink_display_img:
                drink_img_scaled = pygame.transform.scale(drink_display_img, ORDER_ITEM_IMAGE_SIZE) 
                drink_rect = drink_img_scaled.get_rect(centery=item_y_center)
                drink_rect.left = item_start_x
                surface.blit(drink_img_scaled, drink_rect)
            elif drink_key_ordered: # 图片加载失败
                drink_text = self.small_font.render(DRINK_TYPES.get(drink_key_ordered, {}).get('name', "饮品"), True, BLACK)
                text_rect = drink_text.get_rect(centery=item_y_center, left=item_start_x)
                surface.blit(drink_text, text_rect)
