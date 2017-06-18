import unicodedata
import re

def strip(ls):
    if ls:
        return ls[0].strip()
    else:
        return None

def extract_number(str):
	if str: 
		return ''.join(re.findall(r'\d+', str))

def extract_unit(str):
	if str:
		#TODO: Handle wierd non-letter characters
		return ''.join(re.findall(r'[^0-9]+', str))