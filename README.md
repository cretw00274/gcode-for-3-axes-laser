# Various Inkscape extensions
 - 產生雷射機用的PNG圖檔
 - PNG圖檔產生雕刻機路徑
 
#Descriptions
- "產生雷射機用的PNG圖檔" is an extension to generate two PNG images (aligned relief image and marking image)
- "PNG圖檔產生雕刻機路徑" is an extension to generate a Gcode file from two PNG images (the relief file and the marking file) for 3-axes laser engraving


#Installing:

Simply copy all the files in the folder "Extensions" of Inkscape

>Windows ) "C:\<...>\Inkscape\share\extensions"

>Linux ) "/usr/share/inkscape/extensions"

>Mac ) "/Applications/Inkscape.app/Contents/Resources/extensions"


for unix (& mac maybe) change the permission on the file:

>>chmod 755 for all the *.py files

>>chmod 644 for all the *.inx files



#Usage of "Raster 2 Laser GCode generator":

[Required file: png.py / png4laser_gcode.inx / png4laser_gcode.py / png2laser_gcode.inx / png2laser_gcode.py]

- Step 1) Resize the inkscape document to match the dimension of your working area on the laser engraver (Shift+Ctrl+D) 

- Step 2) Draw or import the images, align the relief image and the marking image

- Step 3) To run the extension go to: Extension > 雷射機雕刻 > 1. 產生雷射機用的PNG圖檔 / 2. PNG圖檔產生雕刻機路徑

- Step 4) Play!




#Note
The original code "raster2laser_gcode_cr8" was writed by 305engineering <305engineering@gmail.com>.
I have revision all the file except for png.py for my use case, i.e. add a mark on a relief object.
