# config.py

import os

# --- 屏幕和显示 ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# --- 颜色定义 (部分颜色仍可用于文本或调试) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)  # Added GREEN for happy order
# ... 其他颜色 ...
LIGHT_BLUE = (173, 216, 230)  # 米饭占位符颜色 (可能不再需要)
SALMON_PINK = (250, 128, 114)  # 三文鱼占位符颜色 (可能不再需要)


# --- 资源路径 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
BACKGROUND_IMAGES_DIR = os.path.join(IMAGES_DIR, "background")
UI_IMAGES_DIR = os.path.join(IMAGES_DIR, "ui")  # 所有UI和物品小图都放这里
SUSHI_IMAGES_DIR = os.path.join(IMAGES_DIR, "sushi")
DRINK_IMAGES_DIR = os.path.join(IMAGES_DIR, "drinks")
CUSTOMER_IMAGES_DIR = os.path.join(IMAGES_DIR, "customer")  # <--- 新增顾客图片目录
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# --- 背景和通用UI图片文件名 ---
START_BG_IMG = "start_bg.png"
RESTAURANT_BG_IMG = "restaurant_bg.png"
START_BUTTON_IMG = "start_button.png"

# --- 食材容器和工作台图片文件名 ---
# 请确保这些文件名与你放在 assets/images/ui/ 目录下的文件名完全一致
RICE_CONTAINER_IMG_FILENAME = "rice_container.png"
OCTOPUS_CONTAINER_IMG_FILENAME = "octopus_container.png"
SCALLOP_CONTAINER_IMG_FILENAME = "scallop_container.png"
SALMON_CONTAINER_IMG_FILENAME = "salmon_container.png"
TUNA_CONTAINER_IMG_FILENAME = "tuna_container.png"
CUTTING_BOARD_IMG_FILENAME = "cutting_board.png"

# --- 单独的食材/寿司组件图片文件名 ---
RICE_BALL_IMG_FILENAME = "rice_ball.png"  # 放在菜板上的饭团

OCTOPUS_TOPPING_IMG_FILENAME = "octopus.png"  # 章鱼配料片 (在饭团上)
SCALLOP_TOPPING_IMG_FILENAME = "scallop.png"  # 扇贝配料片
SALMON_TOPPING_IMG_FILENAME = "salmon.png"   # 三文鱼配料片
TUNA_TOPPING_IMG_FILENAME = "tuna.png"       # 金枪鱼配料片

# --- 完整寿司图片文件名 ---
OCTOPUS_SUSHI_IMG_FILENAME = "octopus_sushi.png"  # 完成的章鱼寿司
SCALLOP_SUSHI_IMG_FILENAME = "scallop_sushi.png"  # 完成的扇贝寿司
SALMON_SUSHI_IMG_FILENAME = "salmon_sushi.png"   # 完成的三文鱼寿司
TUNA_SUSHI_IMG_FILENAME = "tuna_sushi.png"       # 完成的金枪鱼寿司

# --- Customer and Order Image Filenames ---
CUSTOMER_WAITING_IMG_FILENAME = "customer_waiting.gif"
CUSTOMER_HAPPY_IMG_FILENAME = "customer_happy.gif"
CUSTOMER_ANGRY_IMG_FILENAME = "customer_angry.gif"
ORDER_BUBBLE_IMG_FILENAME = "order_bubble.png"

# --- Drink Image Filenames (add these if you have them) ---
SAKE_IMG_FILENAME = "sake.png"  # 示例，请替换为你的文件名
BEER_IMG_FILENAME = "beer.png"
MISO_SOUP_IMG_FILENAME = "miso_soup.png"


# --- 字体文件名和大小 ---
CUSTOM_FONT_FILENAME = "s.ttf"
DEFAULT_FONT_SIZE = 28
LARGE_FONT_SIZE = 40
SMALL_FONT_SIZE = 18  # For order text

# --- 游戏状态常量 ---
STATE_START_SCREEN = "start_screen"
STATE_GAME_RUNNING = "game_running"

# --- 食材和饮品定义 (更新以包含图片信息) ---
# RICE 定义现在也包含其在菜板上的图片
RICE = {"name": "米饭", "image_file": RICE_BALL_IMG_FILENAME}

# TOPPINGS 定义现在包含其在菜板上作为配料片的图片
TOPPINGS = {
    "octopus": {"name": "章鱼", "image_file": OCTOPUS_TOPPING_IMG_FILENAME},
    "scallop": {"name": "扇贝", "image_file": SCALLOP_TOPPING_IMG_FILENAME},
    "salmon": {"name": "三文鱼", "image_file": SALMON_TOPPING_IMG_FILENAME},
    "tuna": {"name": "金枪鱼", "image_file": TUNA_TOPPING_IMG_FILENAME}
}

# SUSHI_TYPES 定义现在主要用于名称和“完整寿司”的图片 (当被拿起或在订单中显示时)
SUSHI_TYPES = {
    "octopus": {"name": "章鱼寿司", "image_file": OCTOPUS_SUSHI_IMG_FILENAME},
    "scallop": {"name": "扇贝寿司", "image_file": SCALLOP_SUSHI_IMG_FILENAME},
    "salmon": {"name": "三文鱼寿司", "image_file": SALMON_SUSHI_IMG_FILENAME},
    "tuna": {"name": "金枪鱼寿司", "image_file": TUNA_SUSHI_IMG_FILENAME}
}

DRINK_TYPES = {  # 饮品暂时不变，后续添加图片
    "sake": {"name": "清酒", "image_file": SAKE_IMG_FILENAME},
    "beer": {"name": "啤酒", "image_file": BEER_IMG_FILENAME},
    "miso_soup": {"name": "味增汤", "image_file": MISO_SOUP_IMG_FILENAME}
}

# --- 游戏元素尺寸和位置 (这些可能需要根据你的图片实际大小进行调整) ---
INGREDIENT_AREA_Y = 500
INGREDIENT_WIDTH = 75  # 容器图片的宽度
INGREDIENT_HEIGHT = 90  # 容器图片的高度 (假设是方形，如果不是请调整)
RICE_CONTAINER_POS = (700, INGREDIENT_AREA_Y)
TOPPING_OCTOPUS_POS = (
    RICE_CONTAINER_POS[0] + INGREDIENT_WIDTH + 20, INGREDIENT_AREA_Y)
TOPPING_SCALLOP_POS = (
    RICE_CONTAINER_POS[0], INGREDIENT_AREA_Y+INGREDIENT_HEIGHT+10)
TOPPING_SALMON_POS = (
    RICE_CONTAINER_POS[0] + INGREDIENT_WIDTH + 20, INGREDIENT_AREA_Y+INGREDIENT_HEIGHT+10)
TOPPING_TUNA_POS = (
    TOPPING_OCTOPUS_POS[0] + INGREDIENT_WIDTH + 20, INGREDIENT_AREA_Y)

# 菜板 (尺寸应接近菜板图片的实际大小)
CUTTING_BOARD_IMG_WIDTH = 216  # 假设菜板图片的宽度
CUTTING_BOARD_IMG_HEIGHT = 180  # 假设菜板图片的高度
CUTTING_BOARD_POS = (SCREEN_WIDTH // 2-CUTTING_BOARD_IMG_WIDTH // 2, 510)

# 饭团和配料在菜板上的显示大小（增大）
RICE_BALL_ON_BOARD_SIZE = (80, 67)
TOPPING_ON_BOARD_SIZE = (80, 67)

# --- 顾客区定义 ---
NUM_CUSTOMER_SPOTS = 3
CUSTOMER_SPOT_WIDTH = 150  # 每个顾客“桌子”的宽度
CUSTOMER_SPOT_HEIGHT = 100  # 每个顾客“桌子”的高度
CUSTOMER_SPOT_COLOR = (0, 0, 255, 100)  # 半透明蓝色作为占位符 (R, G, B, Alpha)

# 顾客区位置 (需要根据你的屏幕布局仔细调整)
# 假设它们在屏幕上半部分，水平排列
CUSTOMER_AREA_Y_OFFSET = 300  # 离屏幕顶部的距离
CUSTOMER_AREA_PADDING = 180   # 顾客区之间的间隔以及与屏幕边缘的间隔

start_x_customer_area=100
# 例如，对于3个顾客区，它们的位置可能是：
CUSTOMER_SPOT_POSITIONS = [
    (start_x_customer_area, CUSTOMER_AREA_Y_OFFSET),
    (start_x_customer_area + CUSTOMER_SPOT_WIDTH +
     CUSTOMER_AREA_PADDING, CUSTOMER_AREA_Y_OFFSET),
    (start_x_customer_area + 2 * (CUSTOMER_SPOT_WIDTH +
     CUSTOMER_AREA_PADDING), CUSTOMER_AREA_Y_OFFSET)
]

# --- Customer Visuals & Order Bubble ---
CUSTOMER_IMAGE_SIZE = (120, 180)  # 顾客图片显示大小 (需要根据你的GIF调整)
# 新增：顾客图片底部相对于其桌子区顶部的垂直偏移量
# 正值表示顾客图片的底部在桌子区顶部之上多少像素 (即两者间的空隙)
# 负值表示顾客图片的底部会进入桌子区 (重叠)
CUSTOMER_IMAGE_BOTTOM_Y_OFFSET_ABOVE_TABLE = -10  # 例如，顾客图片的脚部比桌子顶部高10像素
ORDER_BUBBLE_SIZE = (150, 120)   # 订单气泡图片显示大小
ORDER_ITEM_IMAGE_SIZE = (50, 50)  # 订单中寿司/饮品小图的显示大小
ORDER_BUBBLE_OFFSET_X = 30     # 气泡相对于顾客位置的X偏移
ORDER_BUBBLE_OFFSET_Y = -ORDER_BUBBLE_SIZE[1]  # 气泡在顾客头顶上方一点

