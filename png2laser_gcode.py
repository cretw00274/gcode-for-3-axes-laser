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


class GcodeExport(inkex.Effect):
# Richiamata da _main()
	def __init__(self):
		"""init the effetc library and get options from gui"""
		inkex.Effect.__init__(self)

		# Opzioni di esportazione dell'immagine
		self.OptionParser.add_option("-d", "--directory", action="store", type="string", dest="directory", default="", help="Directory for files") ####check_dir
		self.OptionParser.add_option("-f", "--s_file", action="store", type="string", dest="s_file", default="-1.0", help="")
		self.OptionParser.add_option("", "--z_file", action="store", type="string", dest="z_file", default="", help="")
		self.OptionParser.add_option("", "--z_axis", action="store", type="float", dest="z_axis", default="0", help="")
		self.OptionParser.add_option("", "--g_file", action="store", type="string", dest="g_file", default="", help="")
		self.OptionParser.add_option("", "--resolution", action="store", type="int", dest="resolution", default="5", help="") #Usare il valore su float(xy)/resolution e un case per i DPI dell export

		# Modalita di conversione in Bianco e Nero
		self.OptionParser.add_option("", "--conversion_type", action="store", type="int", dest="conversion_type", default="1", help="")

		# Opzioni modalita
		self.OptionParser.add_option("", "--BW_threshold", action="store", type="int", dest="BW_threshold", default="128", help="")
		self.OptionParser.add_option("", "--grayscale_resolution", action="store", type="int", dest="grayscale_resolution", default="1", help="")

		#add by smat
		self.OptionParser.add_option("", "--active-tab", action="store", type="string", dest="active_tab", default='title', help="Active tab.")
		self.OptionParser.add_option("", "--low_laser_dot", action="store", type="inkbool", dest="low_laser_dot", default=True, help="")
		#self.OptionParser.add_option("","--low_laser_square",action="store", type="inkbool", dest="low_laser_square", default=False,help="")
		self.OptionParser.add_option("", "--low_laser_square", action="store", type="int", dest="low_laser_square", default="0", help="")
		self.OptionParser.add_option("", "--laser_contrast", action="store", type="int", dest="laser_contrast", default="3", help="set 1 to the lightest effect.")

		# Commands
		self.OptionParser.add_option("", "--laseron", action="store", type="string", dest="laseron", default="M3", help="")
		self.OptionParser.add_option("", "--laseroff", action="store", type="string", dest="laseroff", default="M5", help="")
		self.OptionParser.add_option("", "--laser_mini_power", action="store", type="int", dest="laser_mini_power", default="50", help="")
		self.OptionParser.add_option("", "--laser_maxi_power", action="store", type="int", dest="laser_maxi_power", default="50", help="")

		#Velocita Nero e spostamento
		self.OptionParser.add_option("", "--speed_ON", action="store", type="int", dest="speed_ON", default="100", help="")

		# Anteprima = Solo immagine BN
		self.OptionParser.add_option("", "--preview_only", action="store", type="inkbool", dest="preview_only", default=False, help="")

		#inkex.errormsg("BLA BLA BLA Messaggio da visualizzare") #DEBUG

######## 	Richiamata da __init__()
########	Qui si svolge tutto
	def effect(self):

		##Implementare check_dir
		self.options.resolution = 5
		if os.path.isdir(self.options.directory):

			##CODICE SE ESISTE LA DIRECTORY
			#inkex.errormsg("OK") #DEBUG


			#Aggiungo un suffisso al nomefile per non sovrascrivere dei file
			temp_name, fileExtension = os.path.splitext(self.options.g_file)	#modified by smat

			s_file = os.path.join(self.options.directory, self.options.s_file)
			if self.options.z_file != "":
				z_file = os.path.join(self.options.directory, self.options.z_file)
			else:
				z_file = ""
				self.options.z_axis = 0
			preview_file = os.path.join(self.options.directory, temp_name + "_preview.png")
			if self.options.preview_only:
				g_file = ""
			elif fileExtension != "":
				g_file = os.path.join(self.options.directory, temp_name + fileExtension)
			else:
			#pos_file_gcode = os.path.join(self.options.directory,self.options.filename+suffix+"gcode.txt")
			#modified by gsyan : split filename then join root name , suffix and extension
				g_file = os.path.join(self.options.directory, self.options.g_file+".nc")

			#DA FARE
			#Manipolo l'immagine PNG per generare il file Gcode
			self.PNGtoGcode(z_file, s_file, preview_file, g_file)

		else:
			inkex.errormsg("Directory does not exist! Please specify existing directory!")


########	CREA IMMAGINE IN B/N E POI GENERA GCODE
######## 	Richiamata da effect()
	# by gsyan
	def getLaserPowerValue(self, oldValue):
		if self.options.laser_maxi_power - self.options.laser_mini_power < 0:
			return self.options.laser_mini_power
		else:
			#return self.options.laser_mini_power + (self.options.laser_maxi_power - self.options.laser_mini_power)*oldValue/255
			return self.options.laser_mini_power + 8*oldValue/255


	def PNGtoGcode(self, z_file, s_file, preview_file, g_file):

		######## GENERO IMMAGINE IN SCALA DI GRIGI ########
		#Scorro l immagine e la faccio diventare una matrice composta da list

		reader = png.Reader(s_file)#File PNG generato
		w, h, pixels, metadata = reader.read_flat()
		matrice = [[255 for i in range(w)]for j in range(h)]  #List al posto di un array

		if z_file != "":
			reader = png.Reader(z_file)#File PNG generato
			w2, h2, pixels2, metadata2 = reader.read_flat()
			matrice2 = [[255 for i in range(w)] for j in range(h)]


		#Scrivo una nuova immagine in Scala di grigio 8bit
		#copia pixel per pixel

		#Max Color
		for y in range(h): # y varia da 0 a h-1
			for x in range(w): # x varia da 0 a w-1
				pixel_position = (x + y * w)*4 if metadata['alpha'] else (x + y * w)*3
				list_RGB = pixels[pixel_position], pixels[(pixel_position+1)] , pixels[(pixel_position+2)]
				matrice[y][x] = int(max(list_RGB))
				if z_file != "":
					pixel_position = (x + y * w) * 4 if metadata2['alpha'] else (x + y * w) * 3
					list_RGB = pixels2[pixel_position], pixels2[(pixel_position + 1)], pixels2[(pixel_position + 2)]
					matrice2[y][x] = int(max(list_RGB))



		####Ora matrice contiene l'immagine in scala di grigi


		######## GENERO IMMAGINE IN BIANCO E NERO ########
		#Scorro matrice e genero matrice_BN
		B = 255
		N = 0

		matrice_BN = [[255 for i in range(w)]for j in range(h)]

		if self.options.conversion_type == 1:
			#B/W fixed threshold
			soglia = self.options.BW_threshold
			for y in range(h):
				for x in range(w):
					if matrice[y][x] >= soglia :
						matrice_BN[y][x] = B
					else:
						matrice_BN[y][x] = N

		elif self.options.conversion_type == 2:
			#B/W random threshold
			from random import randint
			for y in range(h):
				for x in range(w):
					soglia = randint(20,235)
					if matrice[y][x] >= soglia :
						matrice_BN[y][x] = B
					else:
						matrice_BN[y][x] = N

		elif self.options.conversion_type == 3:
			#Halftone
			Step1 = [[B, B, B, B, B], [B, B, B, B, B], [B, B, N, B, B], [B, B, B, B, B], [B, B, B, B, B]]
			Step2 = [[B, B, B, B, B], [B, B, N, B, B], [B, N, N, N, B], [B, B, N, B, B], [B, B, B, B, B]]
			Step3 = [[B, B, N, B, B], [B, N, N, N, B], [N, N, N, N, N], [B, N, N, N, B], [B, B, N, B, B]]
			Step4 = [[B, N, N, N, B], [N, N, N, N, N], [N, N, N, N, N], [N, N, N, N, N], [B, N, N, N, B]]

			for y in range(h/5):
				for x in range(w/5):
					media = 0
					for y2 in range(5):
						for x2 in range(5):
							media += matrice[y*5+y2][x*5+x2]
					media = media / 25
					for y3 in range(5):
						for x3 in range(5):
							if media >= 250 and media <= 255:
								matrice_BN[y*5+y3][x*5+x3] = B
							if media >= 190 and media < 250:
								matrice_BN[y*5+y3][x*5+x3] = Step1[y3][x3]
							if media >= 130 and media < 190:
								matrice_BN[y*5+y3][x*5+x3] = Step2[y3][x3]
							if media >= 70 and media < 130:
								matrice_BN[y*5+y3][x*5+x3] = Step3[y3][x3]
							if media >= 10 and media < 70:
								matrice_BN[y*5+y3][x*5+x3] = Step4[y3][x3]
							if media >= 0 and media < 10:
								matrice_BN[y*5+y3][x*5+x3] = N

		elif self.options.conversion_type == 4:
			#Halftone row
			Step1r = [B, B, N, B, B]
			Step2r = [B, N, N, B, B]
			Step3r = [B, N, N, N, B]
			Step4r = [N, N, N, N, B]

			for y in range(h):
				for x in range(w/5):
					media = 0
					for x2 in range(5):
						media += matrice[y][x*5+x2]
					media = media/5
					for x3 in range(5):
						if 255 >= media >= 250:
							matrice_BN[y][x*5+x3] = B
						if 250 > media >= 190:
							matrice_BN[y][x*5+x3] = Step1r[x3]
						if 190 > media >= 130:
							matrice_BN[y][x*5+x3] = Step2r[x3]
						if 130 > media >= 70:
							matrice_BN[y][x*5+x3] = Step3r[x3]
						if 70 > media >= 10:
							matrice_BN[y][x*5+x3] = Step4r[x3]
						if 10 > media >= 0:
							matrice_BN[y][x*5+x3] = N

		elif self.options.conversion_type == 5:
			#Halftone column
			Step1c = [B, B, N, B, B]
			Step2c = [B, N, N, B, B]
			Step3c = [B, N, N, N, B]
			Step4c = [N, N, N, N, B]

			for y in range(h/5):
				for x in range(w):
					media = 0
					for y2 in range(5):
						media += matrice[y*5+y2][x]
					media = media /5
					for y3 in range(5):
						if 255 >= media >= 250:
							matrice_BN[y*5+y3][x] = B
						if 250 > media >= 190:
							matrice_BN[y*5+y3][x] = Step1c[y3]
						if 190 > media >= 130:
							matrice_BN[y*5+y3][x] = Step2c[y3]
						if 130 > media >= 70:
							matrice_BN[y*5+y3][x] = Step3c[y3]
						if 70 > media >= 10:
							matrice_BN[y*5+y3][x] = Step4c[y3]
						if 10 > media >= 0:
							matrice_BN[y*5+y3][x] = N

		else:
			#Grayscale
			if self.options.grayscale_resolution == 1:
				matrice_BN = matrice
			else:
				for y in range(h):
					for x in range(w):
						if matrice[y][x] <= 1:
							matrice_BN[y][x] = 0 #Fixed by smat

						if matrice[y][x] >= 254:
							matrice_BN[y][x] = 255 # Fixed by smat

						if 254 > matrice[y][x] > 1:
							matrice_BN[y][x] = (matrice[y][x] // self.options.grayscale_resolution) * self.options.grayscale_resolution

		####Ora matrice_BN contiene l'immagine in Bianco (255) e Nero (0)

		#### SALVO IMMAGINE IN BIANCO E NERO ####

		file_img_BN = open(preview_file, 'wb') #Creo il file
		Costruttore_img = png.Writer(w, h, greyscale=True, bitdepth=8) #Impostazione del file immagine
		Costruttore_img.write(file_img_BN, matrice_BN) #Costruttore del file immagine
		file_img_BN.close()	#Chiudo il file


		#### GENERO IL FILE GCODE ####
		if g_file != "": #Genero Gcode solo se devo
			matrice_BN.reverse()
			matrice2.reverse()
			#if self.options.flip_y == False: #Inverto asse Y solo se flip_y = False
			#	#-> coordinate Cartesiane (False) Coordinate "informatiche" (True)
			#	matrice_BN.reverse()

			### Replace \n to line feed of laseron & laseroff options . add by gsyan ###
			self.options.laseron = re.sub(r"\\n", '\n', self.options.laseron)
			self.options.laseroff = re.sub(r"\\n", '\n', self.options.laseroff)
			### by gsyan End ###

			Laser_ON = False
			F_G01 = self.options.speed_ON
			Scala = 5
			z_axis = self.options.z_axis

			file_gcode = open(g_file, 'w')  #Creo il file

			#Configurazioni iniziali standard Gcode
			file_gcode.write(self.options.laseroff+'\n') # add by smat

			file_gcode.write('G21\n')  # Set units to millimeters
			file_gcode.write('G90\n')  # Use absolute coordinates
			file_gcode.write('G01 F' + str(F_G01) + '\n')  # Default Laser On Speed # add by gsyan

			#add by smat original position
			if self.options.low_laser_dot == True:
				file_gcode.write(self.options.laseron+' S100\nG01 Z1 F12\nG01 Z0 F12\n')
			while self.options.low_laser_square > 0:
				file_gcode.write('G00 X'+str(w/self.options.resolution)+' Y0\n')
				file_gcode.write('G00 X'+str(w/self.options.resolution)+' Y'+str(h/self.options.resolution)+'\n')
				file_gcode.write('G00 X0 Y'+str(h/self.options.resolution)+'\n')
				file_gcode.write('G00 X0 Y0\n')
				file_gcode.write('G01 Z1 F12\nG01 Z0 F12\n')
				self.options.low_laser_square -= 1
			file_gcode.write(self.options.laseroff+'\n')


			#Creazione del Gcode

			#allargo la matrice per lavorare su tutta l'immagine
			for y in range(h):
				matrice_BN[y].append(B)
			w = w+1

			if self.options.conversion_type != 6:
				for y in range(h):
					if y % 2 == 0 :
						for x in range(w):
							if matrice_BN[y][x] == N :
								if Laser_ON == False :
									file_gcode.write('G00 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + '\n')
									if self.options.laseron_delay > 0:
										file_gcode.write('G04 P0\n')
									file_gcode.write(self.options.laseron + '\n')
									if self.options.laseron_delay > 0:
										file_gcode.write('G04 P' + str(self.options.laseron_delay) + '\n')
									Laser_ON = True
								if  Laser_ON == True :   #DEVO evitare di uscire dalla matrice
									if x == w-1 :
										file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) +' F' + str(F_G01) + '\n')
										if self.options.laseron_delay > 0:
											file_gcode.write('G04 P0\n')
										file_gcode.write(self.options.laseroff + '\n')
										Laser_ON = False
									else:
										if matrice_BN[y][x+1] != N :
											file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01) +'\n')
											if self.options.laseron_delay > 0:
												file_gcode.write('G04 P0\n')
											file_gcode.write(self.options.laseroff + '\n')
											Laser_ON = False
					else:
						for x in reversed(range(w)):
							if matrice_BN[y][x] == N :
								if Laser_ON == False :
									file_gcode.write('G00 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + '\n') #tolto il Feed sul G00
									if self.options.laseron_delay > 0:
										file_gcode.write('G04 P0\n')
									file_gcode.write(self.options.laseron + '\n')
									if self.options.laseron_delay > 0:
										file_gcode.write('G04 P' + str(self.options.laseron_delay) + '\n')
									Laser_ON = True
								if  Laser_ON == True :   #DEVO evitare di uscire dalla matrice
									if x == 0 :
										file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) +' F' + str(F_G01) + '\n')
										if self.options.laseron_delay > 0:
											file_gcode.write('G04 P0\n')
										file_gcode.write(self.options.laseroff + '\n')
										Laser_ON = False
									else:
										if matrice_BN[y][x-1] != N :
											file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01) +'\n')
											if self.options.laseron_delay > 0:
												file_gcode.write('G04 P0\n')
											file_gcode.write(self.options.laseroff + '\n')
											Laser_ON = False

			else: ##SCALA DI GRIGI GrayScale
				z = 0 #cre
				for y in range(h):
					if y % 2 == 0:
						for x in range(w):
							if matrice_BN[y][x] != B:
								if not Laser_ON:
									#file_gcode.write('G00 X' + str(float(x) / Scala) + ' Y' + str(float(y) / Scala) + '\n')
									if self.options.z_file != '':
										file_gcode.write('G00 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + ' Z' + str(round(-float(255 - matrice2[y][x])/255*z_axis, 1)) + '\n') #cre
										z = matrice2[y][x]  # cre
									else:
										file_gcode.write('G00 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + '\n')  # cre

									#file_gcode.write(self.options.laseron + ' ' + ' S' + str(self.getLaserPowerValue(255 - matrice_BN[y][x])) + '\n')
									Laser_ON = True

								if Laser_ON:   #DEVO evitare di uscire dalla matrice
									if x == w-1 : #controllo fine riga
										if self.options.z_file != "":
											file_gcode.write(self.options.laseron + ' ' + ' S' + str(min(
												self.getLaserPowerValue(255 - matrice_BN[y][x]) + int(abs(float(
													z - matrice2[y][x]) / 255 * z_axis)*Scala), self.options.laser_maxi_power)) + '\n')
											file_gcode.write(
												'G01 X' + str(float(x) / Scala) + ' Y' + str(float(y) / Scala) + ' Z' + str(
													round(-float(255 - matrice2[y][x]) / 255 * z_axis), 1) + ' F' + str(int(
														F_G01 + self.options.laser_contrast * (
															256 - self.getLaserPowerValue(255 - matrice_BN[y][x])))) + '\n')  # test by cre
											z = matrice2[y][x]  # cre
										else:
											file_gcode.write(self.options.laseron + ' ' + ' S' + str(
												self.getLaserPowerValue(255 - matrice_BN[y][x])) + '\n')
											file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n') #test by smat

										file_gcode.write(self.options.laseroff + '\n')
										Laser_ON = False

									else:
										if self.options.z_file != "":
											file_gcode.write(self.options.laseron + ' ' + ' S' + str(min(
												self.getLaserPowerValue(255 - matrice_BN[y][x]) + int(abs(float(
													z - matrice2[y][x+1]) / 255 * z_axis)*Scala), self.options.laser_maxi_power)) + '\n')
											file_gcode.write('G01 X' + str(float(x+1)/Scala) + ' Y' + str(float(y) / Scala) + ' Z' + str(round(-float(255-matrice2[y][x+1]) / 255 * z_axis, 1)) + ' F' + str(int(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x])))) + '\n')  # test by cre
											z = matrice2[y][x+1]  # cre
										else:
											file_gcode.write(self.options.laseron + ' ' + ' S' + str(
												self.getLaserPowerValue(255 - matrice_BN[y][x])) + '\n')
											file_gcode.write('G01 X' + str(float(x + 1) / Scala) + ' Y' + str(
												float(y) / Scala) + ' F' + str(F_G01 + self.options.laser_contrast * (
													256 - self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n')  # test by smat

										if matrice_BN[y][x+1] == B:
											#file_gcode.write('G01 X' + str(float(x+1)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n')  # test by smat
											file_gcode.write(self.options.laseroff + '\n')
											Laser_ON = False

										#else:
											#file_gcode.write('G01 X' + str(float(x+1)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x]))) +'\n') #test by smat
											# file_gcode.write(self.options.laseron + ' '+ ' S' + str(255 - matrice_BN[y][x+1]) +'\n')
										#	file_gcode.write(self.options.laseron + ' ' + ' S' + str(self.getLaserPowerValue(255 - matrice_BN[y][x+1])) + '\n')
											#if self.options.laseron_delay > 0:
											#	file_gcode.write('G04 P' + str(self.options.laseron_delay) + '\n')

					else:
						for x in reversed(range(w)):
							if matrice_BN[y][x] != B:
								if not Laser_ON:
									if self.options.z_file != '':
										file_gcode.write('G00 X' + str(float(x+1)/Scala) + ' Y' + str(float(y)/Scala) + ' Z' + str(round(-float(255 - matrice2[y][x+1])/255*z_axis, 1)) + '\n')
										z = matrice2[y][x+1]
									else:
										file_gcode.write('G00 X' + str(float(x + 1) / Scala) + ' Y' + str(float(y) / Scala) + '\n')

									#if self.options.laseron_delay > 0:
									#	file_gcode.write('G04 P0\n')
									#file_gcode.write(self.options.laseron + ' '+ ' S' + str(255 - matrice_BN[y][x]) +'\n') #fixed by smat 20170226
#									file_gcode.write(self.options.laseron + ' ' + ' S' + str(self.getLaserPowerValue(255 - matrice_BN[y][x])) + '\n')
									#if self.options.laseron_delay > 0:
									#	file_gcode.write('G04 P' + str(self.options.laseron_delay) + '\n')
									Laser_ON = True

								if Laser_ON:   #DEVO evitare di uscire dalla matrice
									if self.options.z_file != '':
										file_gcode.write(self.options.laseron + ' ' + ' S' + str(min(
											self.getLaserPowerValue(255 - matrice_BN[y][x]) + int(abs(float(
												z - matrice2[y][x]) / 255 * z_axis)*Scala), self.options.laser_maxi_power)) + '\n')
										file_gcode.write(
											'G01 X' + str(float(x) / Scala) + ' Y' + str(float(y) / Scala) + ' Z' + str(round(
												-float(255 - matrice2[y][x]) / 255 * z_axis, 1)) + ' F' + str(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n')  # cre
										z = matrice2[y][x]
									else:
										file_gcode.write(self.options.laseron + ' ' + ' S' + str(
											self.getLaserPowerValue(255 - matrice_BN[y][x])) + '\n')
										file_gcode.write(
											'G01 X' + str(float(x) / Scala) + ' Y' + str(float(y) / Scala) + ' F' + str(
												F_G01 + self.options.laser_contrast * (256 - self.getLaserPowerValue(
													255 - matrice_BN[y][x]))) + '\n')  # test by smat

									if x == 0 : #controllo fine riga ritorno
										#file_gcode.write('G01 X' + str(float(x)/Scala) + ' Y' + str(float(y)/Scala) + ' F' + str(F_G01+self.options.laser_contrast*(256-self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n') # test by smat
										file_gcode.write(self.options.laseroff + '\n')
										Laser_ON = False

									else:
										#file_gcode.write('G01 X' + str(float(x) / Scala) + ' Y' + str(float(y) / Scala) + ' F' + str(F_G01 + self.options.laser_contrast * (256 - self.getLaserPowerValue(255 - matrice_BN[y][x]))) + '\n')  # test by smat
										if matrice_BN[y][x-1] == B :
											file_gcode.write(self.options.laseroff + '\n')
											Laser_ON = False

										#else:
											# file_gcode.write(self.options.laseron + ' '+ ' S' + str(255 - matrice_BN[y][x-1]) +'\n')
											#file_gcode.write(self.options.laseron + ' ' + ' S' + str(self.getLaserPowerValue(255 - matrice_BN[y][x-1])) + '\n')

			#Configurazioni finali standard Gcode
			if self.options.z_file != '':
				file_gcode.write('G00 X0 Y0 Z0\n')
			else:
				file_gcode.write('G00 X0 Y0\n')

			file_gcode.close() #Chiudo il file
######## 	######## 	######## 	######## 	######## 	######## 	######## 	######## 	########


def _main():
	e = GcodeExport()
	e.affect()
	
	exit()


if __name__=="__main__":
	_main()




