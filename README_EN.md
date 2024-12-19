# Image Watermark Tool

A modern image watermarking tool that supports batch processing with text or image watermarks, featuring real-time preview and intelligent color adaptation.

English | [简体中文](./README.md)

![Preview](./screenshots/preview.png)

## ✨ Features

- 🖼️ Support for text and image watermarks
- 👀 Real-time preview
- 🎨 Intelligent color adaptation
- 📦 Batch processing
- 🎯 9 fixed positions + custom positioning
- 📝 Multi-line text support
- 🔄 Rotation and transparency adjustment
- 📋 Multiple format support (PNG, JPG, JPEG, BMP, TIFF, WEBP)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Karry-Almond/image-watermark-tool.git

# Install dependencies
pip install -r requirements.txt
```

Or download the pre-built executable: [Releases](https://github.com/yourusername/image-watermark-tool/releases)

### Usage

1. Run the program
```bash
python watermark.py
```

2. Steps:
   - Select input folder
   - Select output folder
   - Choose watermark type (text/image)
   - Adjust watermark parameters
   - Preview effect
   - Start processing

## 🛠️ Features

### Watermark Types
- **Text Watermark**
  - Multi-line text support
  - Auto font size adjustment
  - Smart color adaptation
  
- **Image Watermark**
  - Transparent PNG support
  - Aspect ratio preservation
  - Auto position adjustment

### Parameters
- Size: 1%-50%
- Opacity: 0-100%
- Rotation: 0-360°
- Position: 9 fixed positions
- Color: Smart adaptation/Manual RGB

## 📸 Preview Features

- Real-time watermark preview
- Preview image switching
- Zoom and pan support
- Auto-fit preview area

## 🔧 Technical Features

- Modern UI based on CustomTkinter
- Multi-threaded processing
- Smart background color analysis
- Memory-optimized image processing
- High DPI display support

## 📋 System Requirements

- Windows 7+
- macOS 10.12+
- Linux (GTK 3)
- Python 3.6+ (for source code)

## 📦 Dependencies

```txt
customtkinter>=5.2.0
Pillow>=9.0.0
numpy>=1.19.0
```

## 🤝 Contributing

Contributions are welcome! Before submitting a PR, please:

1. Update test cases
2. Update relevant documentation
3. Follow existing code style

## 📄 License

[MIT](./LICENSE) © [Your Name]

## 🙏 Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [Pillow](https://python-pillow.org/)

## 📞 Contact

- Author: [Your Name]
- Email: [your.email@example.com]
- Blog: [your-blog-url]

---

If this project helps you, please give it a star ⭐️ 