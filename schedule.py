from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
from datetime import time
import os
import re
import sys

class Course:
	def __init__(self, abb, sec, cre, day, tfr, tto, enr, cap):
		self.abbreviation = abb
		self.section = sec
		self.credits = cre
		self.days = day
		self.timeFrom = tfr
		self.timeTo = tto
		self.enrolled = enr
		self.capacity = cap

	def __repr__(self):
		return ("{:9}".format(self.abbreviation) + "|" + "{:7}".format(self.section) +
			"| " + str(self.credits) + " |" + "{:7}".format(self.days) + "| " + str(self.timeFrom) +
				" | " + str(self.timeTo) + " | " + "{:3}".format(self.enrolled) + " | " + self.capacity)

class Timetable:
	def __init__(self, name):
		self.name = name
		self.content = [None] * 6
		for i in range(6):
			self.content[i] = [None] * 12 * 24

	def add_course(self, course, operation = 0):
		dayList = course.days.split(' ')[1:-1]
		for d in dayList:
			if d == "M":
				index = 0
			elif d == "T":
				index = 1
			elif d == "W":
				index = 2
			elif d == "R":
				index = 3
			elif d == "F":
				index = 4
			else:
				index = 5

			for x in range(int(course.timeFrom[0:2])*12 + int(course.timeFrom[3:5])/5,
								int(course.timeTo[0:2])*12 + int(course.timeTo[3:5])/5):
				if operation == 0:
					if self.content[index][x] != None:
						return False
				else:
					self.content[index][x] = course.abbreviation
		if operation == 0:	
			return self.add_course(course, 1)
		return True

	def __repr__(self):
		result = "       Monday    Tuesday   Wednesday  Thursday   Friday\n"
		for j in range(12 * 24):
			buf = ""
			empty = True
			for i in range(6):
				if self.content[i][j] != None:
					buf += "{:9}".format(self.content[i][j]) + " "
					empty = False
				else:
					buf += " " * 10
			if not empty:
				if j%12 * 5 >= 10:
					second = ":"
				else:
					second = ":0"
				if j/12 >= 10:
					first = ""
				else:
					first = "0"
				result += first + str(j/12) + second + str(j%12 * 5) + " " + buf + "\n"
		return result


def pdf_to_text(pdfname):

	# PDFMiner boilerplate
	sio = StringIO()
	device = TextConverter(PDFResourceManager(), sio, codec='utf-8', laparams=LAParams())
	interpreter = PDFPageInterpreter(PDFResourceManager(), device)

	# Extract text
	fp = file(pdfname, 'rb')
	x = 1
	y = 19
	for page in PDFPage.get_pages(fp):
		if x <= y:
			interpreter.process_page(page)
		elif x > y:
			break
		x += 1
	fp.close()

	# Get text from StringIO
	text = sio.getvalue()

	# Cleanup
	device.close()
	sio.close()

	return text

def Read_Schedule(filename):

	text = pdf_to_text(filename)
	text = os.linesep.join([s for s in text.splitlines() if s])
	allCourses = []
	savedValues = [0] * 10
	pages = text.split('\x0c')
	text = '\n'.join(pages)
	return text

def Parse_Schedule(schedule):
	abbr = re.compile('[A-Z]{4} \d{3}|[A-Z]{3} \d{3}')
	section = re.compile(' \d+.?Lb | \d+.{2}Lb | \dL | \d{2}L | \d+R | \d+.?S | \d+Wsh')
	credits = re.compile('\d[.]0')
	days = re.compile(' [MTWRFS] [MTWRFS] [MTWRFS] [MTWRFS] [MTWRFS] ' + 
		'| [MTWRFS] [MTWRFS] [MTWRFS] [MTWRFS] | [MTWRFS] [MTWRFS] [MTWRFS] ' +
			'| [MTWRFS] [MTWRFS] | [MTWRFS] ')
	timeFrom = re.compile(' (\d{2}:\d{2} [A|P]M)')
	timeTo = re.compile('-(\d{2}:\d{2} [A|P]M)')
	enr = re.compile('[A|P]M (\d{3}|\d{2}|\d{1})')
	cap = re.compile('^ \d{2}\d? |\d \d{2}\d? ')

	scheduleMatrix = [None] * 8
	for i in range(8):
		scheduleMatrix[i] = []

	linesplit = schedule.splitlines()
	for line in linesplit:
		line = " " + line + " "
		matchAbbr = abbr.findall(line)
		scheduleMatrix[0] += matchAbbr
		matchSection = section.findall(line)
		scheduleMatrix[1] += matchSection
		matchCredits = credits.findall(line)
		scheduleMatrix[2] += matchCredits
		matchDays = days.findall(line)
		scheduleMatrix[3] += matchDays
		matchTimeFrom = timeFrom.findall(line)
		for i in range(len(matchTimeFrom)):
			if matchTimeFrom[i][-2] == "P" and matchTimeFrom[i][0:2] != "12":
				matchTimeFrom[i] = str(int(matchTimeFrom[i][0:2]) + 12) + matchTimeFrom[i][2:5]
			else:
				matchTimeFrom[i] = matchTimeFrom[i][0:5]
		scheduleMatrix[4] += matchTimeFrom
		matchTimeTo = timeTo.findall(line)
		for i in range(len(matchTimeTo)):
			if matchTimeTo[i][-2] == "P" and matchTimeTo[i][0:2] != "12":
				matchTimeTo[i] = str(int(matchTimeTo[i][0:2]) + 12) + matchTimeTo[i][2:5]
			else:
				matchTimeTo[i] = matchTimeTo[i][0:5]
		scheduleMatrix[5] += matchTimeTo
		matchEnr = enr.findall(line)
		scheduleMatrix[6] += matchEnr
		matchCap = cap.findall(line)
		scheduleMatrix[7] += matchCap
	return scheduleMatrix

def Add_To_Class(scheduleMatrix):
	courses = [None] * len(scheduleMatrix[0])
	for i in range(len(scheduleMatrix[0])):
		checking = scheduleMatrix[7][i].split(' ')
		courses[i] = Course(scheduleMatrix[0][i], scheduleMatrix[1][i], scheduleMatrix[2][i],
			scheduleMatrix[3][i], scheduleMatrix[4][i], scheduleMatrix[5][i], scheduleMatrix[6][i],
				checking[1])
	return courses

if __name__ == "__main__":
	schedule = Read_Schedule(sys.argv[1])
	scheduleMatrix = Parse_Schedule(schedule)
	courses = Add_To_Class(scheduleMatrix)
	test = Timetable("Test")
	selectedCources = []
	for i in range(2, len(sys.argv)):
		if len(sys.argv[i].split(' ')) > 1:
			if 'splitSelectedCources' in vars():
				selectedCources.append(splitSelectedCources)
			splitSelectedCources = [sys.argv[i]]
		else:
			splitSelectedCources.append(sys.argv[i])
	selectedCources.append(splitSelectedCources)
	for c in selectedCources:
		for i in range(1, len(c)):
			for c2 in courses:
				if c[0] == c2.abbreviation:
					match = True
					for j in range(len(c[i])):
						if j < len(c2.section) - 2:
							if c[i][j] != c2.section[j+1]:
								match = False
					if match:
						print c[i]