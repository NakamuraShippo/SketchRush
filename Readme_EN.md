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
- Path tool (B-Spline)/Pen tool  
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
pip install PyQt5 Pillow PyYAML scipy shapely numpy
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
- Change the pen color using C (next color) and V (previous color) keys based on the configured colors.

### Path Mode
- The path uses B-Spline.
- Draw by left-clicking and dragging the mouse button. (Releasing the button finalizes the path)
- You can select a confirmed path by switching to selection mode with the Q key (default setting).
  - Dragging within the selection area moves the path.
  - Selecting a path displays its control points, which can be dragged to alter the shape of the line segments.
  - Add control points by holding CTRL (modifiable) and left-clicking.
  - Remove control points by holding ALT (modifiable) and left-clicking.

### Pen Tablet Mode
The eraser tool can be used with the pen tablet's eraser tool or by pressing the E key (modifiable).  
All other operations are the same as in mouse mode.  
  
## Settings(設定)
### Basic Settings
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/BasicSetting_EN.png)  
- Save Name Template: Make sure to include [:03d] and ".png" in the save name. (e.g., SketchRush001.png)  
- Background color: The background color when no image is loaded  
- Canvas Size: Specify the width and height when no image is loaded  
- Pen Tablet Support: Enable/disable pen tablet mode  
- Auto-advance Image on Save: Enable/disable processing when saving  
- Language(言語): Language settings  
- Pen colors: You can add or delete pen colors with "Add Pen Color" or "Delete Selected Color". Click on each color to change it.  
- Stabilization Degree: The strength of the pen tool's stabilization to reduce hand shake.
- Delete Mode: Configure the behavior when the Delete key is pressed.
- Save Mode: Configure the behavior when the Save key is pressed.
- Path Simplification Tolerance: The intensity of path simplification applied when finalizing a path.
  - Higher values reduce the number of control points, making processing lighter.
- Path Smoothing Strength: The intensity of path smoothing applied when finalizing a path.
  - Higher values result in stronger curve adjustments, making control more difficult when set to the maximum.
- Path Selection Hit Detection Range: Adjust the hit detection range for selecting paths.
  - Higher values make selection easier. A minimum of 10 is recommended to avoid difficulty in selection.

### Key Config
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/KeyConfig_EN.png)  
#### Shortcut Keys
| Function |  Key |
|:---------------|------|
Undo | Z  
Redo | X  
Clear | Delete  
Next Color | C  
Previous Color | V  
Save | S  
Next Image | → (Right Arrow Key)  
Previous Image | ← (Left Arrow Key)  
Eraser Tool | E  
Increase Pen Size | +  
Decrease Pen Size | -  
Merge Save (Layer Integration Save) | F1  
oggle Tool	| Tab
Toggle Fill (Path Tool) | F
Toggle Path Mode | Q

#### Mouse Settings
| Function | Key |
|:---------------|------|
Pen Tool | Left-click  
Eraser Tool (active while holding) | Right-click  
Increase Pen Size | Mouse Wheel Up  
Decrease Pen Size | Mouse Wheel Down  

#### Modifier Keys for Path Tool
| Function | Key |
|:---------------|------|
Add Control Point | CTRL
Remove Control Point | ALT
## Changelog
2024.9.27: v1.0 Released. It might have bugs due to the early-stage release.  
2024.10.16: v1.1 Added stabilization and path tool.  

## Future Plans (Undecided)
- A function to send painted content via the ComfyUI API to Load Image nodes  
- A function to write prompts and send them to ComfyUI to generate images within SketchRush  

## License
SketchRush is licensed under the GNU General Public License version 3 (GPLv3).  
  
Under the GPLv3 license, the following rights are granted:  

- Reproduction and Distribution: You are free to reproduce and distribute this software.
- Modification: You can modify the source code and redistribute it.
However, modified versions must also be released under GPLv3.
- Commercial Use: You can use this software for commercial purposes.
  
## Disclaimer
This software is provided “as is,” without any express or implied warranties, including but not limited to suitability for a particular purpose or non-infringement.  
Users use the tool at their own risk.   The tool’s creator (Nakamura Shippo) is not responsible for any consequences arising from its use.  
  
## Copyright
Copyright (C) 2024 Nakamura Shippo
This program is free software.  
Users can redistribute and/or modify it under the terms of the GNU General Public License version 3 (GPLv3).  
  
## Contact
For bugs, requests, or inquiries, please feel free to contact via issue or through SNS or email from the portal below.  
Nakamura Shippo / [https://lit.link/nakamurashippo](https://lit.link/nakamurashippo)
