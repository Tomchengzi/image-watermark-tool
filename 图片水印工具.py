import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageChops
import numpy as np
from threading import Thread
import os
from tkinter import filedialog, messagebox, Canvas
import sys
import math

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 优化主题和窗口设置
        self._setup_window()
        
        # 初始化变量和状态
        self._init_variables()
        
        # 创建UI布局
        self._create_layout()
        
        # 绑定事件
        self.bind("<Configure>", self.on_window_resize)
        
    def _setup_window(self):
        """窗口初始化设置"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("图片水印工具")
        self.geometry("750x750")  # 增加默认窗口大小
        self.minsize(300, 300)     # 调整最小窗口大小
        
        # 设置全局字体
        self.default_font = ("Microsoft YaHei UI", 12)
        self.title_font = ("Microsoft YaHei UI", 14, "bold")
        
        # 设置全局���题
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#3b8ed0',
            'hover': '#36719f',
            'border': '#3f3f3f'
        }
        
        # 优化网格布局
        self.grid_rowconfigure(0, weight=1)  # 增加预览区域比重
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        
        # 平滑窗口显示
        self.attributes('-alpha', 0.0)
        self.update_idletasks()
        self.attributes('-alpha', 1.0)

    def _init_variables(self):
        """初始化变量"""
        self.folder_path = ""
        self.output_folder = ""
        self.processing = False
        self.watermark_image_path = None
        self.current_preview = None
        self.current_preview_index = 0
        self.supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
        
        # 创建控制变量
        self.watermark_type = ctk.StringVar(value="text")
        self.position_var = ctk.StringVar(value="center")
        self.auto_color = ctk.BooleanVar(value=True)
        self.progress_var = ctk.StringVar(value="准备就绪")

    def _create_layout(self):
        """创建主布局"""
        # 创建预览区域
        self.create_preview_panel()
        
        # 创建可滚动的控制面板容器
        control_container = ctk.CTkFrame(self)
        control_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        control_container.grid_columnconfigure(0, weight=1)
        control_container.grid_rowconfigure(0, weight=1)
        
        # 创建滚动框架并保存为实例属性
        self.control_scroll = ctk.CTkScrollableFrame(
            control_container,
            orientation="vertical",
            height=300  # 设置初始高度
        )
        self.control_scroll.grid(row=0, column=0, sticky="nsew")
        
        # 在滚动框架中创建控制面板
        self.create_control_panel()

    def create_preview_panel(self):
        """改进的预览面板，添加缩放控制"""
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # 预览标题和缩放控制
        title_frame = ctk.CTkFrame(preview_frame)
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(
            title_frame, 
            text="预览区域",
            font=self.title_font
        ).pack(side="left", padx=10)
        
        # 添加缩放控制按钮
        zoom_frame = ctk.CTkFrame(title_frame)
        zoom_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            zoom_frame,
            text="放大",
            width=60,
            command=lambda: self.zoom_preview(1.2)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            zoom_frame,
            text="缩小",
            width=60,
            command=lambda: self.zoom_preview(0.8)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            zoom_frame,
            text="重置",
            width=60,
            command=self.reset_preview
        ).pack(side="left", padx=5)
        
        # 预览画布
        self.preview_canvas = Canvas(
            preview_frame, 
            bg='#1e1e1e',
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            width=150,
            height=200
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # 绑定鼠标事件用于拖动
        self.preview_canvas.bind("<ButtonPress-1>", self.start_move)
        self.preview_canvas.bind("<B1-Motion>", self.move_preview)
        self.preview_canvas.bind("<MouseWheel>", self.mouse_wheel)
        
        # 初始化缩放比例
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0

    def create_control_panel(self):
        """改进的控制面板布局"""
        # 创建左右分栏的容器
        panel_container = ctk.CTkFrame(self.control_scroll)
        panel_container.pack(fill="both", expand=True)
        
        # 左右分栏
        left_frame = ctk.CTkFrame(panel_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        right_frame = ctk.CTkFrame(panel_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 左侧控件
        self.create_file_selection(left_frame)         # 文件选择
        self.create_watermark_input(left_frame)        # 水印输入区域
        self.create_progress_buttons(left_frame)       # 预览和操作按钮
        
        # 右侧控件
        self.create_watermark_settings(right_frame)    # 水印设置（大小、透明度、角度等）
        self.create_position_controls(right_frame)     # 位置控制

    def create_file_selection(self, parent):
        """创建文件选择区域"""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", pady=5)
        
        # 使用grid布局使界面更紧凑
        file_frame.grid_columnconfigure(1, weight=1)
        
        # 输入文件夹
        ctk.CTkLabel(file_frame, text="输入:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.input_entry = ctk.CTkEntry(file_frame)
        self.input_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(file_frame, text="选择", width=60, 
                     command=self.select_input).grid(row=0, column=2, padx=5, pady=2)
        
        # 输出文件夹
        ctk.CTkLabel(file_frame, text="输出:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.output_entry = ctk.CTkEntry(file_frame)
        self.output_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(file_frame, text="选择", width=60, 
                     command=self.select_output).grid(row=1, column=2, padx=5, pady=2)

    def create_watermark_input(self, parent):
        """水印输入区域（文本框和图片选择）"""
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", pady=5)
        
        # 水印类型选择
        type_selection = ctk.CTkFrame(input_frame)
        type_selection.pack(fill="x", pady=5)
        
        ctk.CTkRadioButton(
            type_selection,
            text="文字水印",
            variable=self.watermark_type,
            value="text",
            command=self.on_watermark_type_change
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            type_selection,
            text="图片水印",
            variable=self.watermark_type,
            value="image",
            command=self.on_watermark_type_change
        ).pack(side="left", padx=10)
        
        # 文字水印输入框
        self.text_entry = ctk.CTkTextbox(
            input_frame,
            height=60,
            wrap="word"
        )
        self.text_entry.pack(fill="x", padx=5, pady=5)
        
        # 图片水印选择按钮
        self.watermark_image_button = ctk.CTkButton(
            input_frame,
            text="选择水印图片",
            command=self.select_watermark_image,
            state="disabled"
        )
        self.watermark_image_button.pack(fill="x", padx=5, pady=5)

    def create_position_controls(self, parent):
        """位置控制布局"""
        position_frame = ctk.CTkFrame(parent)
        position_frame.pack(fill="x", pady=5)
        
        # 智能颜色选项
        ctk.CTkCheckBox(
            position_frame,
            text="智能颜色",
            variable=self.auto_color,
            command=self.toggle_color_controls
        ).pack(anchor="w", padx=5, pady=5)
        
        # 位置选择网格
        positions_grid = ctk.CTkFrame(position_frame)
        positions_grid.pack(fill="x", padx=5, pady=5)
        
        # 创建3x3网格的位置选择
        for i in range(3):
            row_frame = ctk.CTkFrame(positions_grid)
            row_frame.pack(fill="x", pady=2)
            
            positions = [
                ("左上", "top_left"), ("中上", "top_center"), ("右上", "top_right"),
                ("左中", "middle_left"), ("居中", "center"), ("右中", "middle_right"),
                ("左下", "bottom_left"), ("中下", "bottom_center"), ("右下", "bottom_right")
            ]
            
            for j in range(3):
                idx = i * 3 + j
                text, value = positions[idx]
                ctk.CTkRadioButton(
                    row_frame,
                    text=text,
                    variable=self.position_var,
                    value=value,
                    command=self.preview_watermark
                ).pack(side="left", expand=True, padx=10)

    def create_progress_buttons(self, parent):
        """预览和操作按钮布局"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", pady=5)
        
        # 预览导航按钮
        nav_frame = ctk.CTkFrame(progress_frame)
        nav_frame.pack(fill="x", pady=5)
        
        nav_buttons = ctk.CTkFrame(nav_frame)
        nav_buttons.pack(fill="x", padx=5)
        
        ctk.CTkButton(
            nav_buttons,
            text="上一张",
            width=80,
            command=lambda: self.change_preview(-1)
        ).pack(side="left", padx=5)
        
        self.preview_index = ctk.CTkLabel(nav_buttons, text="0/0")
        self.preview_index.pack(side="left", expand=True)
        
        ctk.CTkButton(
            nav_buttons,
            text="下一张",
            width=80,
            command=lambda: self.change_preview(1)
        ).pack(side="right", padx=5)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(progress_frame)
        button_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="预览水印",
            command=self.preview_watermark
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="开始添加水印",
            command=self.start_watermark
        ).pack(side="right", fill="x", expand=True, padx=5)

    def create_watermark_settings(self, parent):
        """创建水印设置区域"""
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=5)
        
        # 创建滑块控件
        self.size_slider = self.create_slider_with_label(
            settings_frame, 
            "大小:", 
            0.01, 0.5, 0.1
        )
        
        self.alpha_slider = self.create_slider_with_label(
            settings_frame, 
            "透明度:", 
            0.0, 1.0, 0.7
        )
        
        self.angle_slider = self.create_slider_with_label(
            settings_frame, 
            "角度:", 
            0, 360, 0
        )
        
        # 创建颜色控制区域
        color_frame = ctk.CTkFrame(settings_frame)
        color_frame.pack(fill="x", pady=5)
        
        # 智能颜色选项
        ctk.CTkCheckBox(
            color_frame,
            text="智能颜色",
            variable=self.auto_color,
            command=self.toggle_color_controls,
            font=self.default_font
        ).pack(pady=5)
        
        # RGB颜色控制
        rgb_frame = ctk.CTkFrame(color_frame)
        rgb_frame.pack(fill="x", pady=5)
        
        # 创建RGB滑块
        self.color_r = self.create_color_slider(rgb_frame, "R", 0)
        self.color_g = self.create_color_slider(rgb_frame, "G", 1)
        self.color_b = self.create_color_slider(rgb_frame, "B", 2)
        
        
        # 初始状态设置
        self.toggle_color_controls()

    def create_slider_with_label(self, parent, text, from_, to, default):
        """创建带标签的滑块"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            frame,
            text=text,
            font=self.default_font
        ).pack(side="left", padx=10)
        
        slider = ctk.CTkSlider(
            frame,
            from_=from_,
            to=to,
            number_of_steps=100,
            command=self.preview_watermark
        )
        slider.pack(side="left", fill="x", expand=True, padx=10)
        slider.set(default)
        
        value_label = ctk.CTkLabel(
            frame,
            text=f"{default:.2f}",
            width=50,
            font=self.default_font
        )
        value_label.pack(side="left", padx=5)
        
        # 添加值更新回调
        slider.configure(
            command=lambda v: (
                value_label.configure(text=f"{float(v):.2f}"),
                self.preview_watermark()
            )
        )
        
        return slider

    def create_color_slider(self, parent, color_name, row):
        """创建颜色滑块"""
        ctk.CTkLabel(
            parent,
            text=f"{color_name}:",
            font=self.default_font
        ).grid(row=row, column=0, padx=5)
        
        slider = ctk.CTkSlider(
            parent,
            from_=0,
            to=255,
            number_of_steps=255,
            command=lambda v: self.update_color_preview()
        )
        slider.grid(row=row, column=1, padx=10, pady=2, sticky="ew")
        slider.set(0)
        
        value_label = ctk.CTkLabel(
            parent,
            text="0",
            width=30,
            font=self.default_font
        )
        value_label.grid(row=row, column=2, padx=5)
        
        # 添加值更新回调
        slider.configure(
            command=lambda v: (
                value_label.configure(text=str(int(v))),
                self.update_color_preview()
            )
        )
        
        return slider

    def update_color_preview(self):
        """更新颜色预览"""
        if not self.auto_color.get():
            r = int(self.color_r.get())
            g = int(self.color_g.get())
            b = int(self.color_b.get())
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.configure(fg_color=color)
            
            # 更新预览
            self.preview_watermark()

    def analyze_background(self, image):
        """分析图片背景颜色并返回合适的水印颜色"""
        try:
            # 转换图片为RGB模式进行分析
            img_rgb = image.convert('RGB')
            img_array = np.array(img_rgb)
            
            # 获取图片的高度和宽度
            height, width = img_array.shape[:2]
            
            # 采样点：四个角落和中心区域
            sample_regions = [
                img_array[0:height//10, 0:width//10],          # 左上
                img_array[0:height//10, -width//10:],          # 右上
                img_array[-height//10:, 0:width//10],          # 左下
                img_array[-height//10:, -width//10:],          # 右下
                img_array[height//3:2*height//3, width//3:2*width//3]  # 中心区域
            ]
            
            # 计算每个区域的平均颜色
            region_colors = []
            for region in sample_regions:
                avg_color = np.mean(region, axis=(0,1))
                region_colors.append(avg_color)
            
            # 计算整体平均颜色
            avg_color = np.mean(region_colors, axis=0)
            
            # 计算亮度
            brightness = np.mean(avg_color)
            
            # 根据背景亮度选择水印颜色
            if brightness < 128:
                # 深色背景，使用浅色水印
                watermark_color = (255, 255, 255)
                is_dark = True
            else:
                # 浅色背景，使用深色水印
                watermark_color = (0, 0, 0)
                is_dark = False
            
            # 如果背景接近灰色，则使用对比度更强的颜色
            color_std = np.std(avg_color)
            if color_std < 20:  # 如果颜色标准差小，说明近灰色
                if is_dark:
                    watermark_color = (255, 255, 200)  # 淡黄色
                else:
                    watermark_color = (0, 0, 100)      # 深蓝色
            
            return watermark_color, is_dark
            
        except Exception as e:
            print(f"分析背景颜色时出错: {str(e)}")
            # 出错时返回默认值：黑色水印
            return (0, 0, 0), False
        
    def preview_watermark(self, *args):
        """预览水印效果"""
        if not self.folder_path:
            messagebox.showwarning("警告", "请先选择输入文件夹")
            return
        
        image_files = [f for f in os.listdir(self.folder_path) 
                       if f.lower().endswith(self.supported_formats)]
        
        if not image_files:
            messagebox.showwarning("警告", "输入文件夹中没有支持的图片文件")
            return
        
        # 获取当前预览图片路径
        current_image = os.path.join(
            self.folder_path, 
            image_files[self.current_preview_index]
        )
        
        # 创建预览图
        watermarked = self.create_watermarked_image(current_image)
        if watermarked:
            self.update_preview(watermarked)

    def update_preview(self, image):
        """更新预览图片，支持缩放和平移"""
        if not image:
            return
        
        self.current_preview = image
        
        # 获取画布尺寸
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # 计算基础缩放比例
        width_ratio = canvas_width / image.width
        height_ratio = canvas_height / image.height
        base_scale = min(width_ratio, height_ratio) * 0.8  # 留出边距
        
        # 应用用户缩放
        final_scale = base_scale * self.zoom_scale
        
        # 计算新尺寸
        new_size = (
            int(image.width * final_scale),
            int(image.height * final_scale)
        )
        
        # 缩放图片
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(resized)
        
        # 清除画布
        self.preview_canvas.delete("preview_image")
        
        # 计算居中位置，考虑平移偏移
        x = (canvas_width - new_size[0]) // 2 + self.pan_x
        y = (canvas_height - new_size[1]) // 2 + self.pan_y
        
        # 显示图片
        self.preview_canvas.create_image(
            x, y,
            image=self.preview_photo,
            anchor="nw",
            tags="preview_image"
        )

    def create_watermarked_image(self, image_path):
        """创建水印图片"""
        try:
            image = Image.open(image_path).convert("RGBA")
            
            if self.watermark_type.get() == "text":
                return self.add_text_watermark(image)
            else:
                return self.add_image_watermark(image)
            
        except Exception as e:
            print(f"创建水印图片时出错: {str(e)}")
            return None

    def calculate_position(self, base_size, watermark_size):
        """计算水印位置"""
        position = self.position_var.get()
        x, y = 0, 0
        
        # 水平位置
        if "_left" in position:
            x = 20  # 左边距
        elif "_right" in position:
            x = base_size[0] - watermark_size[0] - 20  # 右边距
        else:  # center
            x = (base_size[0] - watermark_size[0]) // 2
        
        # 垂直位置
        if position.startswith("top"):
            y = 20  # 上边距
        elif position.startswith("bottom"):
            y = base_size[1] - watermark_size[1] - 20  # 下边距
        else:  # center
            y = (base_size[1] - watermark_size[1]) // 2
        
        return x, y

    def add_text_watermark(self, image):
        """添加文字水印"""
        try:
            # 创建一个与原图相同大小的透明图层
            watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            # 计算字体大小
            font_size = self.calculate_watermark_size(image.size)
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # 获取水印文本
            watermark_text = self.text_entry.get("1.0", "end-1c").strip()
            if not watermark_text:
                return image
            
            # 计算文本大小和位置
            lines = watermark_text.split('\n')
            line_heights = []
            total_height = 0
            max_width = 0
            
            # 计算每行文本的尺寸
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                line_heights.append(line_height)
                total_height += line_height
                max_width = max(max_width, line_width)
            
            # 使用新的位置计算方法
            x, y = self.calculate_position(
                image.size,
                (max_width, total_height)
            )
            
            # 设置水印颜色和透明度
            alpha = int(255 * self.alpha_slider.get())
            if self.auto_color.get():
                watermark_color, _ = self.analyze_background(image)
            else:
                watermark_color = (
                    int(self.color_r.get()),
                    int(self.color_g.get()),
                    int(self.color_b.get())
                )
            
            # 绘制每行文本
            current_y = y
            for i, line in enumerate(lines):
                draw.text((x, current_y), line, font=font, fill=(*watermark_color, alpha))
                current_y += line_heights[i]
            
            # 旋转水印
            angle = self.angle_slider.get()
            if angle != 0:
                # 创建更大的画布进行旋转
                rotate_size = (int(image.size[0] * 1.5), int(image.size[1] * 1.5))
                rotate_layer = Image.new('RGBA', rotate_size, (0, 0, 0, 0))
                
                # 将水印层粘贴到旋转画��中心
                paste_x = (rotate_size[0] - watermark_layer.size[0]) // 2
                paste_y = (rotate_size[1] - watermark_layer.size[1]) // 2
                rotate_layer.paste(watermark_layer, (paste_x, paste_y))
                
                # 旋转并裁剪回原始大小
                rotate_layer = rotate_layer.rotate(angle, expand=False, resample=Image.Resampling.BICUBIC)
                watermark_layer = rotate_layer.crop((
                    (rotate_size[0] - image.size[0]) // 2,
                    (rotate_size[1] - image.size[1]) // 2,
                    (rotate_size[0] + image.size[0]) // 2,
                    (rotate_size[1] + image.size[1]) // 2
                ))
            
            # 合成水印
            return Image.alpha_composite(image, watermark_layer)
            
        except Exception as e:
            print(f"添加文字水印时出错: {str(e)}")
            return image
        
    def add_image_watermark(self, base_image):
        """添加图片水印"""
        try:
            if not self.watermark_image_path:
                return base_image
            
            # 打开并处理水印图片
            watermark = Image.open(self.watermark_image_path).convert("RGBA")
            
            # 计算水印大小
            base_size = min(base_image.size)
            scale = self.size_slider.get()
            watermark_size = int(base_size * scale)
            
            # 保持宽高比缩放
            ratio = watermark_size / max(watermark.size)
            new_size = tuple(int(dim * ratio) for dim in watermark.size)
            watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
            
            # 创建透明图层
            watermark_layer = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            
            # 计算居中位置
            paste_x = (base_image.size[0] - watermark.size[0]) // 2
            paste_y = (base_image.size[1] - watermark.size[1]) // 2
            
            # 调整透明度
            alpha = int(255 * self.alpha_slider.get())
            watermark.putalpha(ImageChops.multiply(
                watermark.getchannel('A'),
                Image.new('L', watermark.size, alpha)
            ))
            
            # 粘贴水印
            watermark_layer.paste(watermark, (paste_x, paste_y), watermark)
            
            # 旋转水印
            angle = self.angle_slider.get()
            if angle != 0:
                # 创建更大的画布进行旋转
                rotate_size = [int(s * 1.5) for s in base_image.size]
                rotate_layer = Image.new('RGBA', rotate_size, (0, 0, 0, 0))
                
                # 将水印层粘贴到旋转画布中心
                paste_x = (rotate_size[0] - watermark_layer.size[0]) // 2
                paste_y = (rotate_size[1] - watermark_layer.size[1]) // 2
                rotate_layer.paste(watermark_layer, (paste_x, paste_y))
                
                # 旋转并裁剪
                rotate_layer = rotate_layer.rotate(angle, expand=False, resample=Image.Resampling.BICUBIC)
                watermark_layer = rotate_layer.crop((
                    (rotate_size[0] - base_image.size[0]) // 2,
                    (rotate_size[1] - base_image.size[1]) // 2,
                    (rotate_size[0] + base_image.size[0]) // 2,
                    (rotate_size[1] + base_image.size[1]) // 2
                ))
            
            # 合成最终图片
            return Image.alpha_composite(base_image, watermark_layer)
            
        except Exception as e:
            print(f"添加图片水印时出错: {str(e)}")
            return base_image
        
    def process_images(self):
        """处理所有图片"""
        try:
            folder = self.folder_path
            output_folder = self.output_folder
            
            # 创建输出文件夹
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # 获取所有支持的图片文件
            image_files = [f for f in os.listdir(folder) if f.lower().endswith(self.supported_formats)]
            total_files = len(image_files)
            
            if total_files == 0:
                messagebox.showinfo("提示", "没有找到支持的图片文件")
                self.processing = False
                return
            
            for i, filename in enumerate(image_files, 1):
                try:
                    input_path = os.path.join(folder, filename)
                    output_path = os.path.join(output_folder, filename)  # 保持原文件名
                    
                    # 更新进度
                    self.progress_var.set(f"处理中... ({i}/{total_files})")
                    self.progress_bar.set(i/total_files)
                    self.update()
                    
                    # 处理图片
                    image = Image.open(input_path).convert("RGBA")
                    watermarked = None
                    
                    if self.watermark_type.get() == "text":
                        watermarked = self.add_text_watermark(image)
                    else:
                        watermarked = self.add_image_watermark(image)
                    
                    if watermarked:
                        # 保存时转换回RGB模式
                        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                            watermarked = watermarked.convert('RGB')
                        watermarked.save(output_path, quality=95)
                    
                except Exception as e:
                    messagebox.showerror("错误", f"处理文件 {filename} 时出错：{str(e)}")
                    continue
            
            self.progress_var.set("处理完成！")
            self.progress_bar.set(1)
            self.processing = False
            messagebox.showinfo("完成", f"所有图片处理完成！\n输出目录：{output_folder}")
            
        except Exception as e:
            messagebox.showerror("错误", f"处理过程出错：{str(e)}")
            self.processing = False
        finally:
            self.progress_var.set("准备就绪")
            self.progress_bar.set(0)
            self.processing = False
    
    def start_process(self):
        """开始处理图片"""
        if self.processing:
            return
        
        if not self.folder_path or not self.output_folder:
            messagebox.showerror("错误", "请选择输入和输出文件夹")
            return
        
        if self.watermark_type.get() == "text" and not self.text_entry.get("1.0", "end-1c").strip():
            messagebox.showerror("错误", "请输入水印文本")
            return
        
        if self.watermark_type.get() == "image" and not self.watermark_image_path:
            messagebox.showerror("错误", "请选择水印图片")
            return
        
        self.processing = True
        Thread(target=self.process_images).start()

    # 加一个新的方法来计算标准化的水印尺寸
    def calculate_watermark_size(self, image_size):
        """
        计算水印的标准化尺寸
        基于图片对角线长度计算，确保水印大小在视觉上保持一致
        """
        # 计算图片对角线长度
        diagonal = math.sqrt(image_size[0]**2 + image_size[1]**2)
        # 基于对角线长度计算基准字体大小
        base_size = diagonal * self.size_slider.get()
        # 设置最小和最大限制
        min_size = 24  # 最小字体大小
        max_size = diagonal * 0.2  # 最大不超过对角线的20%
        return int(max(min_size, min(base_size, max_size)))

    def on_window_resize(self, event=None):
        """窗口大小改变时更新预览"""
        if hasattr(self, 'current_preview') and self.current_preview:
            self.update_preview(self.current_preview)

    def select_input(self):
        """选择输入文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.input_entry.delete(0, 'end')
            self.input_entry.insert(0, folder)
            
            # 自动创建输出文件夹
            output_folder = os.path.join(os.path.dirname(folder), "watermarked_" + os.path.basename(folder))
            self.output_folder = output_folder
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, output_folder)
            
            # 如果文件夹不存在，创建它
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

    def select_output(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, folder)

    def select_watermark_image(self):
        """选择水印图片"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.watermark_image_path = file_path
            self.preview_watermark()

    def toggle_color_controls(self):
        """切换颜色控制的启用状态"""
        state = "disabled" if self.auto_color.get() else "normal"
        if hasattr(self, 'color_r_slider'):
            self.color_r_slider.configure(state=state)
            self.color_g_slider.configure(state=state)
            self.color_b_slider.configure(state=state)

    def create_slider(self, from_, to, default):
        """创建统一样式的滑块"""
        slider = ctk.CTkSlider(
            None,  # parent will be set when using
            from_=from_,
            to=to,
            number_of_steps=100,
            command=self.preview_watermark
        )
        slider.set(default)
        return slider

    def change_preview(self, direction):
        """切换预览图片"""
        if not self.folder_path:
            return
        
        image_files = [f for f in os.listdir(self.folder_path) 
                       if f.lower().endswith(self.supported_formats)]
        
        if not image_files:
            return
        
        # 计算新的索引
        total = len(image_files)
        new_index = (self.current_preview_index + direction) % total
        self.current_preview_index = new_index
        
        # 更新索引显示
        self.preview_index.configure(text=f"{new_index + 1}/{total}")
        
        # 更新预览
        self.preview_watermark()

    def update_color_value(self, value, label, color):
        """更新颜色值显示"""
        label.configure(text=f"{int(value)}")
        self.update_color_preview()

    def update_color_preview(self, *args):
        """更新颜色预览"""
        if not self.auto_color.get():
            r = int(self.color_r.get())
            g = int(self.color_g.get())
            b = int(self.color_b.get())
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview_frame.configure(fg_color=color)
            
            # 更新颜色代码显示
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            rgb_color = f"RGB({r},{g},{b})"
            self.color_preview_frame.configure(
                text=f"{hex_color}\n{rgb_color}",
                font=self.default_font
            )

    def on_watermark_type_change(self):
        """处理水印类型切换"""
        if self.watermark_type.get() == "text":
            self.text_entry.configure(state="normal")
            self.watermark_image_button.configure(state="disabled")
            # 清空图片水印路径
            self.watermark_image_path = None
        else:
            self.text_entry.configure(state="disabled")
            self.watermark_image_button.configure(state="normal")
            # 清空文字水印内容
            self.text_entry.delete("1.0", "end")
        
        # 更新预览
        self.preview_watermark()

    def zoom_preview(self, factor):
        """缩放预览图片"""
        if not hasattr(self, 'current_preview') or not self.current_preview:
            return
        
        self.zoom_scale *= factor
        # 限制缩放范围
        self.zoom_scale = max(0.1, min(5.0, self.zoom_scale))
        self.update_preview(self.current_preview)

    def reset_preview(self):
        """重置预览状态"""
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        if hasattr(self, 'current_preview'):
            self.update_preview(self.current_preview)

    def start_move(self, event):
        """开始移动预览图片"""
        self.preview_canvas.scan_mark(event.x, event.y)

    def move_preview(self, event):
        """移动预览图片"""
        self.preview_canvas.scan_dragto(event.x, event.y, gain=1)
        # 更新平移位置
        self.pan_x += (event.x - self._last_x) if hasattr(self, '_last_x') else 0
        self.pan_y += (event.y - self._last_y) if hasattr(self, '_last_y') else 0
        self._last_x = event.x
        self._last_y = event.y

    def mouse_wheel(self, event):
        """鼠标滚轮缩放"""
        if event.delta > 0:
            self.zoom_preview(1.1)
        else:
            self.zoom_preview(0.9)

    def start_watermark(self):
        """开始添加水印"""
        if not self.folder_path or not self.output_folder:
            messagebox.showwarning("警告", "请先选择输入和输出文件夹")
            return
        
        # 获取所有支持的图片文件
        image_files = [f for f in os.listdir(self.folder_path) 
                       if f.lower().endswith(self.supported_formats)]
        
        if not image_files:
            messagebox.showwarning("警告", "输入文件夹中没有支持的图片文件")
            return
        
        try:
            # 开始处理
            self.processing = True
            total = len(image_files)
            
            for i, filename in enumerate(image_files, 1):
                # 更新进度
                self.progress_var.set(f"处理中... {i}/{total}")
                self.update_idletasks()
                
                # 处理单个图片
                input_path = os.path.join(self.folder_path, filename)
                output_path = os.path.join(self.output_folder, filename)
                
                # 创建水印图片
                watermarked = self.create_watermarked_image(input_path)
                if watermarked:
                    # 保存图片
                    watermarked.save(output_path, quality=95)
            
            # 完成处理
            self.processing = False
            self.progress_var.set("处理完成")
            messagebox.showinfo("完成", f"已处理 {total} 张图片")
            
        except Exception as e:
            self.processing = False
            self.progress_var.set("处理出错")
            messagebox.showerror("错误", f"处理图片时出错：{str(e)}")

if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()