import unicodedata
import re
import os

def load_list_from_file(path):
    cwd = os.getcwd()
    with open(cwd + path, 'rb') as f:
        return [line.strip() for line in
                f.read().decode('utf8').splitlines()
                if line.strip()]

def strip(ls):
    if ls:
        return ls[0].strip()
    else:
        return None

def extract_number(str):
	if str:
		number = ''.join(re.findall(r'\d+', str))
		if number:
			return float(number)

def extract_unit(str):
	if str:
		#TODO: Handle wierd non-letter characters
		return ''.join(re.findall(r'[^0-9]+', str))

def extract_property_id(str):
	if str:
		match = re.search('-pr([0-9]+)', str)
		if match:
			if match.end() == len(str):
				return str[match.start() + 3 :]
			else:
				extract_property_id(str[match.end():])