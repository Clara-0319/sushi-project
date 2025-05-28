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
    CUSTOMER_HAPPY_LEAVE_DELAY_MS, CUSTOMER_ANGRY_LEAVE_DELAY_MS # 导入延迟常量
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
        self.current_image = self.images.get(self.state) # 如果是 "empty" 或 "leaving"，current_image 会是 None

        # 如果进入 happy 或 angry 状态，启动离开计时器
        if self.state == "happy":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_HAPPY_LEAVE_DELAY_MS
            print(f"顾客 {self.spot_index+1} 开心，准备在 {self.leave_delay/1000} 秒后离开。")
        elif self.state == "angry":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_ANGRY_LEAVE_DELAY_MS
            print(f"顾客 {self.spot_index+1} 生气，准备在 {self.leave_delay/1000} 秒后离开。")



    def receive_item(self, item_category, item_key):
        if not self.order or self.order_fulfilled or self.state not in ["waiting", "angry_waiting"]: # angry_waiting 可以是收到一个错的但还在等另一个
            print(f"顾客 {self.spot_index+1} 无法接收物品 (状态: {self.state}, 订单完成: {self.order_fulfilled})。")
            return False

        current_sushi_order = self.order["sushi"]
        current_drink_order = self.order["drink"]
        made_change = False

        if item_category == "sushi" and not self.sushi_received_key:
            self.sushi_received_key = item_key
            print(f"顾客 {self.spot_index+1} 收到寿司: {SUSHI_TYPES.get(item_key, {}).get('name', '未知寿司')}")
            made_change = True
        elif item_category == "drink" and not self.drink_received_key:
            self.drink_received_key = item_key
            print(f"顾客 {self.spot_index+1} 收到饮品: {DRINK_TYPES.get(item_key, {}).get('name', '未知饮品')}")
            made_change = True
        else:
            print(f"顾客 {self.spot_index+1} 已收到过 {item_category} 或尝试提供错误类别的物品。")
            return False # 避免重复提交同类物品或逻辑错误

        if made_change and self.sushi_received_key and self.drink_received_key:
            # 两样东西都收到了，现在判断最终状态
            sushi_correct = (self.sushi_received_key == current_sushi_order)
            drink_correct = (self.drink_received_key == current_drink_order)

            if sushi_correct and drink_correct:
                self.order_fulfilled = True
                self.set_state("happy")
                print(f"顾客 {self.spot_index+1} 订单完美完成!")
            elif sushi_correct or drink_correct: # 至少对了一个
                self.order_fulfilled = True # 即使有一个错，也算订单结束了
                self.set_state("happy") # 按你的要求，一对一错也是 happy
                print(f"顾客 {self.spot_index+1} 订单部分完成 (至少一项正确)!")
            else: # 全错
                self.order_fulfilled = True # 订单也结束了
                self.set_state("angry")
                print(f"顾客 {self.spot_index+1} 订单完全错误!")
        elif made_change:
            # 只收到了一部分，继续等待 (保持 waiting 状态)
            print(f"顾客 {self.spot_index+1} 收到部分订单，继续等待。")
            # 如果送错了一个，可以考虑在这里就生气，但按你的最新描述，是等两样都送完再判断
            # 如果希望送错一个就直接生气并离开，需要调整这里的逻辑

        return True


    def update(self):
        current_time = pygame.time.get_ticks()
        if self.state in ["happy", "angry"] and self.departure_timer_start is not None:
            if current_time - self.departure_timer_start >= self.leave_delay:
                print(f"顾客 {self.spot_index+1} 离开。")
                self.state = "empty" # 标记为空位
                self.order = None
                self.order_fulfilled = False
                self.sushi_received_key = None
                self.drink_received_key = None
                self.current_image = None # 清空图片
                self.departure_timer_start = None # 重置计时器
                # 在这里可以返回一个信号或True，告诉main.py该顾客已离开，可以生成新顾客
                return True # 表示顾客已离开
        return False # 表示顾客未离开

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
            item_y_center = bubble_y + ORDER_BUBBLE_SIZE[1] // 2

            # 绘制寿司需求
            sushi_key_ordered = self.order.get("sushi")
            sushi_display_img = None
            if sushi_key_ordered and not self.sushi_received_key: # 只在未收到时显示
                sushi_display_img = self.sushi_item_images.get(sushi_key_ordered)

            if sushi_display_img:
                sushi_img_scaled = pygame.transform.scale(sushi_display_img, ORDER_ITEM_IMAGE_SIZE)
                sushi_rect = sushi_img_scaled.get_rect(centery=item_y_center)
                sushi_rect.left = item_start_x
                surface.blit(sushi_img_scaled, sushi_rect)
                item_start_x += ORDER_ITEM_IMAGE_SIZE[0] + 5
            elif sushi_key_ordered and not self.sushi_received_key:
                sushi_text = self.small_font.render(SUSHI_TYPES.get(sushi_key_ordered, {}).get('name', "寿司"), True, BLACK)
                text_rect = sushi_text.get_rect(centery=item_y_center, left=item_start_x)
                surface.blit(sushi_text, text_rect)
                item_start_x += text_rect.width + 10

            # 只有当寿司和饮品都未收到，或者寿司未收到时才画 "+"
            if sushi_key_ordered and not self.sushi_received_key and \
               self.order.get("drink") and not self.drink_received_key:
                plus_text = self.small_font.render("+", True, BLACK)
                plus_rect = plus_text.get_rect(centery=item_y_center, left=item_start_x)
                surface.blit(plus_text, plus_rect)
                item_start_x += plus_rect.width + 5

            # 绘制饮品需求
            drink_key_ordered = self.order.get("drink")
            drink_display_img = None
            if drink_key_ordered and not self.drink_received_key: # 只在未收到时显示
                drink_display_img = self.drink_item_images.get(drink_key_ordered)

            if drink_display_img:
                drink_img_scaled = pygame.transform.scale(drink_display_img, ORDER_ITEM_IMAGE_SIZE)
                drink_rect = drink_img_scaled.get_rect(centery=item_y_center)
                drink_rect.left = item_start_x
                surface.blit(drink_img_scaled, drink_rect)
            elif drink_key_ordered and not self.drink_received_key:
                drink_text = self.small_font.render(DRINK_TYPES.get(drink_key_ordered, {}).get('name', "饮品"), True, BLACK)
                text_rect = drink_text.get_rect(centery=item_y_center, left=item_start_x)
                surface.blit(drink_text, text_rect)
