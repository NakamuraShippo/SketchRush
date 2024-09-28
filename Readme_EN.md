![SketchRushLogo](https://github.com/NakamuraShippo/SketchRush/blob/main/image/SketchRushLogo.png)

## Overview
SketchRush is a simple drawing tool.  
You can quickly sketch and shape ideas using a pen tablet or mouse.  
It is suitable for applications that do not require advanced editing, such as 30-second drawing, mask, or pose drawing.  
[Demo video on YouTube](https://youtu.be/DLPtTu0L4a0)  

## Main Features
- Sequentially display images in the folder  
- Supported formats: png, gif, bmp, jpeg, jpg, webp  
- Drawing using a mouse  
- Drawing using a pen tablet  
- Change pen color  
- Change background color  
- Save drawings as PNG with transparent background  
- Save image merged with the background  
- Automatically transition to the next image when saving  
- Customizable keyboard shortcuts  

## Installation
Clone or download this repository.  
Make sure Python 3.6 or higher is installed.  

Double-click `install_SketchRush.bat` in the extracted folder to start the installation.  
~~~
# Manual installation is also possible.
python -m venv venv
pip install PyQt5 Pillow PyYAML
~~~
Double-click `boot_SketchRush.bat` to launch the application.  
~~~
# You can also launch it manually.
venv\Scripts\Activate
py main.py
~~~

## Usage
### Mouse Mode  
- You can draw with a left-click.  
- While holding the right-click, it switches to eraser mode.  
- Adjust the pen size with the mouse wheel.  

### Pen Tablet Mode
The eraser tool conforms to the pen tablet operations.  
Other operations are the same as in mouse mode.  

### Settings(設定)
#### Basic Settings
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/BasicSetting.png)  
- Save Name Template: Make sure to include [:03d] and ".png" in the save name. (e.g., SketchRush001.png)  
- Background color: The background color when no image is loaded  
- Canvas Size: Specify the width and height when no image is loaded  
- Pen Tablet Support: Enable/disable pen tablet mode  
- Auto-advance Image on Save: Enable/disable processing when saving  
- Language(言語): Language settings  
- Pen colors: You can add or delete pen colors with "Add Pen Color" or "Delete Selected Color". Click on each color to change it.  

#### Key Config
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/KeyConfig.png)  
| Function | Shortcut Key |
|:---------------|------|
Undo | Z  
Redo | X  
Clear | Delete  
Next Color | C  
Previous Color | V  
Save | Enter  
Next Image | → (Right Arrow Key)  
Previous Image | ← (Left Arrow Key)  
Eraser Tool | E  
Increase Pen Size | +  
Decrease Pen Size | -  
Merge Save (Layer Integration Save) | F1  

| Function | Shortcut Key |
|:---------------|------|
Pen Tool | Left-click  
Eraser Tool (active while holding) | Right-click  
Increase Pen Size | Mouse Wheel Up  
Decrease Pen Size | Mouse Wheel Down  

## Changelog
2024.9.27: v1.0 Released. It might have bugs due to the early-stage release.

## Future Plans (Undecided)
- A function to send painted content via the ComfyUI API to Load Image nodes  
- A function to write prompts and send them to ComfyUI to generate images within SketchRush  

## License
SketchRush is protected by copyright law. Unauthorized reproduction, modification, or redistribution is prohibited.  
Commercial use is allowed, but all responsibility lies with the tool user. The tool creator (Nakamura Shippo) assumes no responsibility.  

## Contact
For bugs, requests, or inquiries, please feel free to contact via issue or through SNS or email from the portal below.  
Nakamura Shippo / [https://lit.link/nakamurashippo](https://lit.link/nakamurashippo)
