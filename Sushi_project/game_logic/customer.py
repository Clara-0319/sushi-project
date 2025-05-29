# game_logic/customer.py

import pygame
import random
import os
# 从 sushi_elements.py 导入新的 load_gif_frames 函数
# 或者直接从 game_logic.sushi_elements 导入
from .sushi_elements import load_gif_frames
from config import (
    SUSHI_TYPES, DRINK_TYPES, CUSTOMER_IMAGES_DIR, UI_IMAGES_DIR, DRINK_IMAGES_DIR, # 添加 DRINK_IMAGES_DIR
    CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_ANGRY_IMG_FILENAME,
    ORDER_BUBBLE_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, ORDER_BUBBLE_SIZE, ORDER_ITEM_IMAGE_SIZE,
    ORDER_BUBBLE_OFFSET_X, ORDER_BUBBLE_OFFSET_Y, BLACK, SMALL_FONT_SIZE,
    CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE,
    CUSTOMER_HAPPY_LEAVE_DELAY_MS, CUSTOMER_ANGRY_LEAVE_DELAY_MS, # 导入延迟常量
    TIP_PERFECT_ORDER, TIP_PARTIAL_ORDER, TIP_WRONG_ORDER,  # 导入小费常量
    ORDER_DURATION_SECONDS, ORDER_TIMER_ICON_SIZE,  # 新增导入
    ORDER_TIMER_OFFSET_X, ORDER_TIMER_OFFSET_Y, ORDER_TIMER_TEXT_COLOR,  # 新增导入
    CUSTOMER_ANIMATION_FRAME_DURATION  # 导入动画帧时长
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
    def __init__(self, spot_index, table_spot_rect, preloaded_sushi_images, preloaded_drink_images, order_timer_icon_surface):
        self.spot_index = spot_index
        self.rect = pygame.Rect((0, 0), CUSTOMER_IMAGE_SIZE)
        self.rect.midbottom = (table_spot_rect.centerx,
                               table_spot_rect.top - CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE)

        self.state = "empty"
        self.order = None
        self.order_fulfilled = False
        self.sushi_received_key = None
        self.drink_received_key = None
        self.departure_timer_start = None
        self.leave_delay = 0
        self.order_timer_start_ticks = None
        self.order_remaining_seconds = ORDER_DURATION_SECONDS
        self.timer_icon_image = order_timer_icon_surface  # 用于订单倒计时

        # +++ 动画相关属性 +++
        self.animation_frames = {  # 存储每个状态的动画帧列表
            "waiting": load_gif_frames(CUSTOMER_WAITING_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "happy": load_gif_frames(CUSTOMER_HAPPY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
            "angry": load_gif_frames(CUSTOMER_ANGRY_IMG_FILENAME, CUSTOMER_IMAGE_SIZE, directory=CUSTOMER_IMAGES_DIR),
        }
        self.current_animation_frame_index = 0
        self.last_animation_update_time = 0
        self.animation_frame_duration = CUSTOMER_ANIMATION_FRAME_DURATION
        self.current_image = None  # 将由动画逻辑更新

        self.order_bubble_image = load_scaled_image(  # 这个是静态图
            ORDER_BUBBLE_IMG_FILENAME, ORDER_BUBBLE_SIZE, directory=UI_IMAGES_DIR)

        self.sushi_item_images = preloaded_sushi_images
        self.drink_item_images = preloaded_drink_images

        try:
            from config import FONTS_DIR, CUSTOM_FONT_FILENAME
            font_file = os.path.join(FONTS_DIR, CUSTOM_FONT_FILENAME)
            if not os.path.exists(font_file):
                font_file = None
            self.small_font = pygame.font.Font(font_file, SMALL_FONT_SIZE)
        except Exception:
            self.small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)

    def generate_order(self):
        if self.state == "empty":
            # ... (订单生成逻辑不变) ...
            sushi_key = random.choice(list(SUSHI_TYPES.keys()))
            drink_key = random.choice(list(DRINK_TYPES.keys()))
            self.order = {"sushi": sushi_key, "drink": drink_key}
            self.order_fulfilled = False
            self.sushi_received_key = None
            self.drink_received_key = None
            self.departure_timer_start = None
            self.set_state("waiting")  # 这会触发动画的重置
            self.order_timer_start_ticks = pygame.time.get_ticks()
            self.order_remaining_seconds = ORDER_DURATION_SECONDS
            # print(f"顾客 {self.spot_index+1} 点单: {SUSHI_TYPES[sushi_key]['name']} 和 {DRINK_TYPES[drink_key]['name']}. 时限: {self.order_remaining_seconds}s")
            return True
        return False

    def set_state(self, new_state):
        previous_state = self.state
        self.state = new_state

        # 重置动画帧索引，以便新状态的动画从头开始
        self.current_animation_frame_index = 0
        self.last_animation_update_time = pygame.time.get_ticks()  # 重置动画更新时间

        # 更新当前图像为新状态的第一帧 (如果动画帧存在)
        if self.state in self.animation_frames and self.animation_frames[self.state]:
            self.current_image = self.animation_frames[self.state][0]
        else:
            self.current_image = None  # 对于 "empty" 或其他无动画状态

        if self.state == "happy":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_HAPPY_LEAVE_DELAY_MS
            self.order_timer_start_ticks = None
        elif self.state == "angry":
            self.departure_timer_start = pygame.time.get_ticks()
            self.leave_delay = CUSTOMER_ANGRY_LEAVE_DELAY_MS
            self.order_timer_start_ticks = None

        if previous_state == "waiting" and self.state == "angry":  # 例如超时
            self.order_timer_start_ticks = None

    def _animate(self, current_ticks):
        """处理顾客动画的帧切换"""
        if self.state in self.animation_frames and self.animation_frames[self.state]:
            frames = self.animation_frames[self.state]
            if not frames:  # 如果某个状态没有动画帧
                self.current_image = None  # 或者设置为一个静态占位图
                return

            if current_ticks - self.last_animation_update_time > self.animation_frame_duration:
                self.last_animation_update_time = current_ticks
                self.current_animation_frame_index = (
                    self.current_animation_frame_index + 1) % len(frames)
                self.current_image = frames[self.current_animation_frame_index]
        elif self.state == "empty":  # 确保空状态没有图像
            self.current_image = None

    def receive_item(self, item_category, item_key):
        if not self.order or self.order_fulfilled or self.state not in ["waiting"]:
            return 0

        current_sushi_order = self.order["sushi"]
        current_drink_order = self.order["drink"]
        made_change = False
        tip_earned = 0

        if item_category == "sushi" and not self.sushi_received_key:
            self.sushi_received_key = item_key
            made_change = True
        elif item_category == "drink" and not self.drink_received_key:
            self.drink_received_key = item_key
            made_change = True
        else:
            return 0

        if made_change and self.sushi_received_key and self.drink_received_key:
            sushi_correct = (self.sushi_received_key == current_sushi_order)
            drink_correct = (self.drink_received_key == current_drink_order)
            self.order_fulfilled = True  # 标记订单已尝试完成

            if sushi_correct and drink_correct:
                self.set_state("happy")
                tip_earned = TIP_PERFECT_ORDER
                #print(f"顾客 {self.spot_index+1} 订单完美完成! 获得小费: {tip_earned}")
            elif sushi_correct or drink_correct:
                self.set_state("happy")
                tip_earned = TIP_PARTIAL_ORDER
                #print(f"顾客 {self.spot_index+1} 订单部分完成! 获得小费: {tip_earned}")
            else:
                self.set_state("angry")
                tip_earned = TIP_WRONG_ORDER
                #print(f"顾客 {self.spot_index+1} 订单完全错误! 获得小费: {tip_earned}")
        return tip_earned

    def update(self):
        current_ticks = pygame.time.get_ticks()

        # +++ 调用动画处理 +++
        self._animate(current_ticks)

        # --- 订单超时检查 ---
        if self.state == "waiting" and self.order and not self.order_fulfilled and self.order_timer_start_ticks is not None:
            elapsed_order_time_ms = current_ticks - self.order_timer_start_ticks
            self.order_remaining_seconds = ORDER_DURATION_SECONDS - (elapsed_order_time_ms // 1000)
            if self.order_remaining_seconds <= 0:
                self.order_remaining_seconds = 0
                #print(f"顾客 {self.spot_index+1} 订单超时!")
                self.set_state("angry") # 顾客生气
                self.order_fulfilled = True # 标记订单结束（虽然是失败的）
                # 生气离开的计时器会在 set_state("angry") 中启动
                # 不需要额外返回小费，因为超时不给小费，receive_item 也不会被调用

        # --- 顾客离开计时 ---
        if self.state in ["happy", "angry"] and self.departure_timer_start is not None:
            if current_ticks - self.departure_timer_start >= self.leave_delay:
                self.state = "empty"
                self.order = None
                self.order_fulfilled = False
                self.sushi_received_key = None
                self.drink_received_key = None
                self.current_image = None
                self.departure_timer_start = None
                self.order_timer_start_ticks = None
                self.order_remaining_seconds = ORDER_DURATION_SECONDS
                self.current_animation_frame_index = 0  # 重置动画状态
                return True
        return False


    def draw(self, surface):
        if self.state == "empty": # 如果是空位，不绘制顾客和订单气泡
            return

        # 绘制顾客 (现在 current_image 会是动画的当前帧)
        if self.current_image:
            surface.blit(self.current_image, self.rect)
        # 如果状态不是 empty 但没有 current_image (例如GIF加载失败)
        elif self.state != "empty":
            # 可以画一个占位符
            pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)
            if self.small_font:
                text_surf = self.small_font.render(self.state, True, BLACK)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)

        # --- 订单气泡绘制逻辑 (保持不变) ---

        bubble_drawn = False
        bubble_base_x = 0
        bubble_base_y = 0

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

        # +++ 绘制订单计时器 +++
        if self.state == "waiting" and self.order_timer_start_ticks is not None and self.timer_icon_image:
            timer_icon_x = self.rect.centerx - \
                ORDER_TIMER_ICON_SIZE[0] // 2 + ORDER_TIMER_OFFSET_X
            if bubble_drawn:  # 如果有气泡，显示在气泡下方
                timer_icon_y = bubble_base_y + ORDER_TIMER_OFFSET_Y
            else:  # 如果没有气泡（例如图片加载失败），显示在顾客头顶一个固定偏移处
                timer_icon_y = self.rect.top - \
                    ORDER_TIMER_ICON_SIZE[1] - 5  # 气泡上方再往上一点

            surface.blit(self.timer_icon_image, (timer_icon_x, timer_icon_y))

            time_text = f"{max(0, self.order_remaining_seconds)}"  # 只显示秒
            time_surf = self.small_font.render(
                time_text, True, ORDER_TIMER_TEXT_COLOR)
            time_rect = time_surf.get_rect(midleft=(timer_icon_x + ORDER_TIMER_ICON_SIZE[0] + 5,
                                                    timer_icon_y + ORDER_TIMER_ICON_SIZE[1] // 2))
            surface.blit(time_surf, time_rect)
