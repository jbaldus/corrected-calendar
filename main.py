import flask
import re
import requests
from threading import Thread

app = flask.Flask('')


# This function will return a regex that will match a 
# chunk of text from START to STOP if it contains MIDDLE
# This took a long time to figure out how to make this work
# and I'm writing this comment afterwords. If you need to
# figure out how it works, good luck.
def regex_chunk(start, middle, stop):
  dot = f'(?:.(?!{stop}))'
  mid = re.sub('\.\*(?=[^?])|\.\*$', f'{dot}*?', middle)
  return f'{start}{dot}*?{mid}.*?{stop}'


def event_regex(match):
  start = 'BEGIN:VEVENT'
  stop = 'END:VEVENT'
  return regex_chunk(start, match, stop)


def remove_off_events(text):
  return re.sub(event_regex('SUMMARY:.*(?:OFF|Off)'), '', text, flags = re.DOTALL)


def remove_cancelled_appointments(text):
  return re.sub(event_regex('SUMMARY:.*\(C\)'), '', text, flags = re.DOTALL)


def sanitizer(text):
  # Change Client Code to BUSY
  sanitizer = r'SUMMARY:(?:.(?!\\(non-patient\\)))*?$'
  text = re.sub(sanitizer, 'SUMMARY:BUSY', text, re.M)
  # Clear description
  description = r'(?<=DESCRIPTION:)(.*\n [^\r]*)'
  text = re.sub(description, '', text)
  #text = remove_off_events(text)
  return text


def get_and_modify_ical(options):
  resp = requests.get(options.get('url'))
  text = resp.text

  if not options.get('keep_canceled'):
    text = remove_cancelled_appointments(text)
  if options.get('removeOffs', False):
    text = remove_off_events(text)
  if options.get('sanitize', False):
    text = sanitizer(text)
  if options.get('tz'):
    regex = re.compile(r'DT(END|START):(\d+T\d+)[^Z]')
    replacement = f"DT\\1;TZID={options.get('tz')}:\\2"
    text = re.sub(regex, replacement, text)
  return text


@app.route('/')
def main():
  url = flask.request.args.get('url')
  tz = flask.request.args.get('tz')
  remove_offs = flask.request.args.get('removeOffs') is not None
  sanitize = flask.request.args.get('sanitize') is not None
  
  if url is None or tz is None:
    return home()
  
  return get_and_modify_ical(flask.request.args)


def home():
    return "I'm alive"


def run():
  app.run(host='0.0.0.0',port=8080)


def keep_alive():  
    t = Thread(target=run)
    t.start()


keep_alive()
