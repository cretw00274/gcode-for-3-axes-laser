'''
# ----------------------------------------------------------------------------
# Copyright (C) 2014 305engineering <305engineering@gmail.com>
# Original concept by 305engineering.
#
# "THE MODIFIED BEER-WARE LICENSE" (Revision: my own :P):
# <305engineering@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff (except sell). If we meet some day, 
# and you think this stuff is worth it, you can buy me a beer in return.
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ----------------------------------------------------------------------------
'''


import sys
import os
import re

sys.path.append('/usr/share/inkscape/extensions')
sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions') 

import subprocess
import math

import inkex
import png
import array


class PNG4laserExport(inkex.Effect):

######## 	Richiamata da _main()
	def __init__(self):
		"""init the effetc library and get options from gui"""
		inkex.Effect.__init__(self)
		
		# Opzioni di esportazione dell'immagine
		self.OptionParser.add_option("-d", "--directory",action="store", type="string", dest="directory", default="",help="Directory for files") ####check_dir
		self.OptionParser.add_option("-f", "--filename", action="store", type="string", dest="filename", default="-1.0", help="File name")            
		self.OptionParser.add_option("","--add-numeric-suffix-to-filename", action="store", type="inkbool", dest="add_numeric_suffix_to_filename", default=True,help="Add numeric suffix to filename")            
		self.OptionParser.add_option("","--bg_color",action="store",type="string",dest="bg_color",default="",help="")

		
		# Come convertire in scala di grigi
		self.OptionParser.add_option("","--grayscale_type",action="store", type="int", dest="grayscale_type", default="1",help="") 
		
		# Modalita di conversione in Bianco e Nero 
		self.OptionParser.add_option("","--conversion_type",action="store", type="int", dest="conversion_type", default="1",help="") 
		
		# Opzioni modalita 
		self.OptionParser.add_option("","--BW_threshold",action="store", type="int", dest="BW_threshold", default="128",help="") 
		self.OptionParser.add_option("","--grayscale_resolution",action="store", type="int", dest="grayscale_resolution", default="1",help="") 
		
		#Velocita Nero e spostamento
		self.OptionParser.add_option("","--speed_ON",action="store", type="int", dest="speed_ON", default="500", help="")
		self.OptionParser.add_option("", "--z_file", action="store", type="string", dest="z_file", default="", help="")
		self.OptionParser.add_option("", "--z_axis", action="store", type="float", dest="z_axis", default="0", help="")

		# Mirror Y
		self.OptionParser.add_option("","--flip_y",action="store", type="inkbool", dest="flip_y", default=False,help="")
		
		# Homing
		self.OptionParser.add_option("","--homing",action="store", type="int", dest="homing", default="1",help="")

		#add by smat
		self.OptionParser.add_option("","--active-tab",action="store", type="string",dest="active_tab", default='title', help="Active tab.")# use a legitmate default
		self.OptionParser.add_option("","--x_adjust",action="store", type="string", dest="x_adjust", default="45",help="") 
		self.OptionParser.add_option("","--y_adjust",action="store", type="string", dest="y_adjust", default="10",help="") 
		self.OptionParser.add_option("","--z_adjust",action="store", type="string", dest="z_focus", default="50",help="") 
		self.OptionParser.add_option("","--laser_contrast",action="store", type="int", dest="laser_contrast", default="3",help="set 1 to the lightest effect.") 
		self.OptionParser.add_option("","--low_laser_dot",action="store", type="inkbool", dest="low_laser_dot", default=True,help="")
		#self.OptionParser.add_option("","--low_laser_square",action="store", type="inkbool", dest="low_laser_square", default=False,help="")
		self.OptionParser.add_option("","--low_laser_square",action="store", type="int", dest="low_laser_square", default="0",help="")
		

		# Commands
		self.OptionParser.add_option("","--laseron", action="store", type="string", dest="laseron", default="M3", help="")
		self.OptionParser.add_option("","--laseroff", action="store", type="string", dest="laseroff", default="M5", help="")

		self.OptionParser.add_option("","--laseron_delay", action="store", type="int", dest="laseron_delay", default="0", help="")
		self.OptionParser.add_option("","--laser_mini_power", action="store", type="int", dest="laser_mini_power", default="50", help="")
		self.OptionParser.add_option("", "--laser_maxi_power", action="store", type="int", dest="laser_maxi_power", default="50", help="")
		
		# Anteprima = Solo immagine BN 
		self.OptionParser.add_option("","--preview_only",action="store", type="inkbool", dest="preview_only", default=False,help="") 

		#inkex.errormsg("BLA BLA BLA Messaggio da visualizzare") #DEBUG


		
		
######## 	Richiamata da __init__()
########	Qui si svolge tutto
	def effect(self):


		current_file = self.args[-1]
		bg_color = self.options.bg_color

		
		##Implementare check_dir
		
		if (os.path.isdir(self.options.directory)) == True:					
			
			##CODICE SE ESISTE LA DIRECTORY
			#inkex.errormsg("OK") #DEBUG

			
			#Aggiungo un suffisso al nomefile per non sovrascrivere dei file
			temp_name,fileExtension = os.path.splitext(self.options.filename)	#modified by smat
			if self.options.add_numeric_suffix_to_filename :
				self.options.filename = temp_name + "_z"
			else:
				self.options.filename = temp_name + "_s"

			pos_file_png_exported = os.path.join(self.options.directory,self.options.filename+".png")
			pos_file_png_BW = os.path.join(self.options.directory,self.options.filename+"_preview.png")
			#pos_file_gcode = os.path.join(self.options.directory,self.options.filename+suffix+"gcode.txt") 
			#modified by gsyan : split filename then join root name , suffix and extension
			if fileExtension != '':
				pos_file_gcode = os.path.join(self.options.directory,self.options.filename+suffix[:-1]+fileExtension)
			else:
				if self.options.add_numeric_suffix_to_filename:
					pos_file_gcode = os.path.join(self.options.directory,self.options.filename+"_z.nc")
				else:
					pos_file_gcode = os.path.join(self.options.directory,self.options.filename+"_s.nc")


			#Esporto l'immagine in PNG
			self.exportPage(pos_file_png_exported,current_file,bg_color)

		else:
			inkex.errormsg("Directory does not exist! Please specify existing directory!")


########	ESPORTA L IMMAGINE IN PNG		
######## 	Richiamata da effect()
		
	def exportPage(self,pos_file_png_exported,current_file,bg_color):
		######## CREAZIONE DEL FILE PNG ########
		#Crea l'immagine dentro la cartella indicata  da "pos_file_png_exported"
		# -d 127 = risoluzione 127DPI  =>  5 pixel/mm  1pixel = 0.2mm
		###command="inkscape -C -e \"%s\" -b\"%s\" %s -d 127" % (pos_file_png_exported,bg_color,current_file) 

		#if self.options.resolution == 1:
		#	DPI = 25.4
		#elif self.options.resolution == 2:
		#	DPI = 50.8
		#elif self.options.resolution == 5:
		DPI = 127
		#elif self.options.resolution == 10:
		#	DPI = 254
		#else:
		#	DPI = 25.4*self.options.resolution

		command="inkscape -C -e \"%s\" -b\"%s\" %s -d %s" % (pos_file_png_exported,bg_color,current_file,DPI) #Comando da linea di comando per esportare in PNG
					
		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return_code = p.wait()
		f = p.stdout
		err = p.stderr


######## 	######## 	######## 	######## 	######## 	######## 	######## 	######## 	########


def _main():
	e=PNG4laserExport()
	e.affect()
	
	exit()

if __name__=="__main__":
	_main()




