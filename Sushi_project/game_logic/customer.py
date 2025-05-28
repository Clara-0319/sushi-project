# game_logic/customer.py

import pygame
import random
import os
from config import (
    SUSHI_TYPES, DRINK_TYPES, CUSTOMER_IMAGES_DIR, UI_IMAGES_DIR, DRINK_IMAGES_DIR, # 添加 DRINK_IMAGES_DIR
    CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_ANGRY_IMG_FILENAME,
    ORDER_BUBBLE_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, ORDER_BUBBLE_SIZE, ORDER_ITEM_IMAGE_SIZE,
    ORDER_BUBBLE_OFFSET_X, ORDER_BUBBLE_OFFSET_Y, BLACK, SMALL_FONT_SIZE,
    CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE,
    CUSTOMER_HAPPY_LEAVE_DELAY_MS, CUSTOMER_ANGRY_LEAVE_DELAY_MS, # 导入延迟常量
    TIP_PERFECT_ORDER, TIP_PARTIAL_ORDER, TIP_WRONG_ORDER  # 导入小费常量
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

        self.state = "empty"  # 初始状态可以是 "empty"，由 main.py 决定何时生成第一个订单
        self.order = None      # {"sushi": "sushi_key", "drink": "drink_key"}
        self.order_fulfilled = False

        # +++ 新增：记录已收到的物品 +++
        self.sushi_received_key = None
        self.drink_received_key = None

        self.departure_timer_start = None # 记录开始计时离开的时间点
        self.leave_delay = 0 # 离开前的延迟时间

        self.images = {
            "waiting": load_scaled_image(CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "happy": load_scaled_image(CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "angry": load_scaled_image(CUSTOMER_ANGRY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
        }
        self.current_image = None # 初始为空，在 generate_order 时设置

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

        # 不在初始化时立即生成订单，由 main.py 控制生成时机
        # self.generate_order()

    def generate_order(self):
        if self.state == "empty": # 只有空位时才能生成新订单
            sushi_key = random.choice(list(SUSHI_TYPES.keys()))
            drink_key = random.choice(list(DRINK_TYPES.keys()))
            self.order = {"sushi": sushi_key, "drink": drink_key}
            self.order_fulfilled = False
            self.sushi_received_key = None
            self.drink_received_key = None
            self.departure_timer_start = None # 重置离开计时器
            self.set_state("waiting") # 新订单，进入等待状态
            print(
                f"顾客 {self.spot_index+1} 点单: {SUSHI_TYPES[sushi_key]['name']} 和 {DRINK_TYPES[drink_key]['name']}")
            return True
        return False

    def set_state(self, new_state):
        self.state = new_state
        self.current_image = self.images.get(self.state)
        if self.state == "happy":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_HAPPY_LEAVE_DELAY_MS
            # print(f"顾客 {self.spot_index+1} 开心，准备在 {self.leave_delay/1000} 秒后离开。") # 减少打印
        elif self.state == "angry":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_ANGRY_LEAVE_DELAY_MS
            # print(f"顾客 {self.spot_index+1} 生气，准备在 {self.leave_delay/1000} 秒后离开。") # 减少打印

    def receive_item(self, item_category, item_key):
        """顾客接收一个物品，并检查订单。返回获得的小费金额。"""
        if not self.order or self.order_fulfilled or self.state not in ["waiting"]:
            # print(f"顾客 {self.spot_index+1} 无法接收物品 (状态: {self.state}, 订单完成: {self.order_fulfilled})。")
            return 0  # 没有小费

        current_sushi_order = self.order["sushi"]
        current_drink_order = self.order["drink"]
        made_change = False
        tip_earned = 0  # 初始化本次服务的小费

        if item_category == "sushi" and not self.sushi_received_key:
            self.sushi_received_key = item_key
            # print(f"顾客 {self.spot_index+1} 收到寿司: {SUSHI_TYPES.get(item_key, {}).get('name', '未知寿司')}")
            made_change = True
        elif item_category == "drink" and not self.drink_received_key:
            self.drink_received_key = item_key
            # print(f"顾客 {self.spot_index+1} 收到饮品: {DRINK_TYPES.get(item_key, {}).get('name', '未知饮品')}")
            made_change = True
        else:
            # print(f"顾客 {self.spot_index+1} 已收到过 {item_category} 或尝试提供错误类别的物品。")
            return 0  # 没有小费

        if made_change and self.sushi_received_key and self.drink_received_key:
            # 两样东西都收到了，现在判断最终状态并计算小费
            sushi_correct = (self.sushi_received_key == current_sushi_order)
            drink_correct = (self.drink_received_key == current_drink_order)
            self.order_fulfilled = True  # 订单尝试结束

            if sushi_correct and drink_correct:
                self.set_state("happy")
                tip_earned = TIP_PERFECT_ORDER
                print(f"顾客 {self.spot_index+1} 订单完美完成! 获得小费: {tip_earned}")
            elif sushi_correct or drink_correct:  # 至少对了一个
                self.set_state("happy")  # 按你的要求，一对一错也是 happy
                tip_earned = TIP_PARTIAL_ORDER
                print(f"顾客 {self.spot_index+1} 订单部分完成! 获得小费: {tip_earned}")
            else:  # 全错
                self.set_state("angry")
                tip_earned = TIP_WRONG_ORDER  # 通常是0
                print(f"顾客 {self.spot_index+1} 订单完全错误! 获得小费: {tip_earned}")
        # else:
            # print(f"顾客 {self.spot_index+1} 收到部分订单，继续等待。")

        return tip_earned  # 返回本次服务获得的小费

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.state in ["happy", "angry"] and self.departure_timer_start is not None:
            if current_time - self.departure_timer_start >= self.leave_delay:
                # print(f"顾客 {self.spot_index+1} 离开。")
                self.state = "empty"
                self.order = None
                self.order_fulfilled = False
                self.sushi_received_key = None
                self.drink_received_key = None
                self.current_image = None
                self.departure_timer_start = None
                return True
        return False

    def draw(self, surface):
        if self.state == "empty": # 如果是空位，不绘制顾客和订单气泡
            return

        if self.current_image:
            surface.blit(self.current_image, self.rect)
        else: # 备用绘制，以防图片加载失败但状态不是 empty
            placeholder_color = (128, 128, 128) #灰色
            if self.state == "waiting": placeholder_color = (0,0,200)
            elif self.state == "happy": placeholder_color = (0,200,0)
            elif self.state == "angry": placeholder_color = (200,0,0)
            pygame.draw.rect(surface, placeholder_color, self.rect, 2)

        # 只有在等待状态且有订单时才绘制订单气泡
        if self.state == "waiting" and self.order and self.order_bubble_image:
            bubble_x = self.rect.centerx - ORDER_BUBBLE_SIZE[0] // 2 + ORDER_BUBBLE_OFFSET_X
            bubble_y = self.rect.top + ORDER_BUBBLE_OFFSET_Y
            surface.blit(self.order_bubble_image, (bubble_x, bubble_y))

            item_start_x = bubble_x+23
            item_y_center = bubble_y + ORDER_BUBBLE_SIZE[1] //2
            items_to_draw = []
            
            #绘制寿司
            sushi_key_ordered = self.order.get("sushi")
            if sushi_key_ordered and not self.sushi_received_key:
                items_to_draw.append(
                    {"type": "sushi", "key": sushi_key_ordered})
            
            #绘制饮品
            drink_key_ordered = self.order.get("drink")
            if drink_key_ordered and not self.drink_received_key:
                items_to_draw.append(
                    {"type": "drink", "key": drink_key_ordered})

            for i, item_info in enumerate(items_to_draw):
                img_to_draw = None
                item_name_fallback = "未知"
                if item_info["type"] == "sushi":
                    img_to_draw = self.sushi_item_images.get(item_info["key"])
                    item_name_fallback = SUSHI_TYPES.get(
                        item_info["key"], {}).get('name', "寿司")
                elif item_info["type"] == "drink":
                    img_to_draw = self.drink_item_images.get(item_info["key"])
                    item_name_fallback = DRINK_TYPES.get(
                        item_info["key"], {}).get('name', "饮品")

                if img_to_draw:
                    img_scaled = pygame.transform.scale(
                        img_to_draw, ORDER_ITEM_IMAGE_SIZE)
                    img_rect = img_scaled.get_rect(centery=item_y_center)
                    img_rect.left = item_start_x
                    surface.blit(img_scaled, img_rect)
                    item_start_x += ORDER_ITEM_IMAGE_SIZE[0] + 5
                else:
                    text_surf = self.small_font.render(
                        item_name_fallback, True, BLACK)
                    text_rect = text_surf.get_rect(
                        centery=item_y_center, left=item_start_x)
                    surface.blit(text_surf, text_rect)
                    item_start_x += text_rect.width + 10

                if i < len(items_to_draw) - 1:  # 如果不是最后一个元素，且后面还有元素，则画 "+"
                    plus_text = self.small_font.render("+", True, BLACK)
                    plus_rect = plus_text.get_rect(
                        centery=item_y_center, left=item_start_x)
                    surface.blit(plus_text, plus_rect)
                    item_start_x += plus_rect.width + 5
