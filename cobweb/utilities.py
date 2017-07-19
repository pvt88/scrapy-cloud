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
		number = ''.join(re.findall(r'\d*\.?\,?\d+', str))
		if number:
			return float(number.replace(',','.'))


def extract_unit(str):
	if str:
		#TODO: Handle wierd non-letter characters
		return ''.join(re.findall(r'[^0-9]+', str))


def extract_property_id(str):
	if str:
		str = rchop(str, '.htm')
		match = re.search('-pr([0-9]+)', str)
		if match:
			if match.end() == len(str):
				return str[match.start() + 3 :]
			else:
				extract_property_id(str[match.end():])

		match = re.search('-ad([0-9]+)', str)
		if match:
			if match.end() == len(str):
				return str[match.start() + 3 :]
			else:
				extract_property_id(str[match.end():])


def extract_listing_type(str):
	if str:
		return str.rsplit('/', 1)[1].rsplit('.',)[0]


def rchop(str, ending):
	if str.endswith(ending):
		return str[:-len(ending)]
	return str

