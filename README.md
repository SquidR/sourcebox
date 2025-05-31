# sourcebox
python/opengl implementation of interloper's sourcebox
if you want to run the program yourself and edit code, feel free to, if you dont feel like it, pre-packaged exe is in `../dist/sourcebox.exe` (PUT IT IN THE ROOT DIRECTORY OR IT WONT WORK!!! aka. same folder as `/assets`

# Customization
if you want to change the color(s) of the grid texture, go into `gridmaker.py` and edit the colors in the `power_styles` list.
you can also change the image entirely by replacing it with your own, just make sure it has the file name `grid.png`, same goes for any other texture.

# Changelog
* v1.2 - CURRENT
  * added that fuckass cyan cone
  * fixed an issue where text appeared offscreen if monitor was not 1920x1080, should work now for all resolutions
* v1.1
  * made grid look better
  * fixed some bugs
  * added more lore-accurate interactions
  * added floaters and camera focus
* v1.0
  * initial release