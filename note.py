#!/usr/bin/python3.7
import datetime
from pathlib import Path
import os.path
from os import path
import argparse
import subprocess
import json

html_css="""
<!DOCTYPE html>
<html>
<style>
.filterDiv {
  display: none;
}

.show {
  display: block;
}

.container {
  margin-top: 20px;
  overflow: hidden;
}

/* Style the buttons */
.btn {
  border: none;
  outline: none;
  padding: 12px 16px;
  background-color: #f1f1f1;
  cursor: pointer;
}

.btn:hover {
  background-color: #ddd;
}

.btn.active {
  background-color: #666;
  color: white;
}
</style>
<body>
"""

html_js="""
<script>
filterSelection("all")
function filterSelection(c) {
  var x, i;
  x = document.getElementsByClassName("filterDiv");
  if (c == "all") c = "";
  for (i = 0; i < x.length; i++) {
    w3RemoveClass(x[i], "show");
    if (x[i].dataset.tags.indexOf(c) > -1) w3AddClass(x[i], "show");
  }
}

function w3AddClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {element.className += " " + arr2[i];}
  }
}

function w3RemoveClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);     
    }
  }
  element.className = arr1.join(" ");
}

// Add active class to the current button (highlight it)
var btnContainer = document.getElementById("myBtnContainer");
var btns = btnContainer.getElementsByClassName("btn");
for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function(){
    var current = document.getElementsByClassName("active");
    current[0].className = current[0].className.replace(" active", "");
    this.className += " active";
  });
}
</script>

</body>
</html>
"""


#Config options
# default editor
# open editor at all 
# notes location
#
config_filename = os.path.join(str(Path.home()), "notescfg.json")
config = {
    "timestamp_label" : "EntryTime:",
    "tags_label" : "EntryTags:",
    "note_filename" : os.path.join(str(Path.home()), "notes.txt"),
    "html_filename" : os.path.join(str(Path.home()), "notes.html"),
    "open_editor" : True,
    "default_editor" : 'vim'
}

def build_config(args):
    global config

    if not path.exists(config_filename):
        return

    configfile = open(config_filename)

    config = {**config, **json.load(configfile)}

    if 'add' in args['command']:
        if args['no_editor']:
            config['open_editor'] = False
    

def generate_html(args):
    html_file=open(config['html_filename'], "w+")    
    html_file.write(html_css)

    tags=[]
    entry_divs= "<div class=\"container\">\n"
    with open(config['note_filename'], "r") as note_file:
        lines = note_file.readlines()
        for i in range(len(lines)):
            if config["timestamp_label"] in lines[i]:
                timestamp = lines[i]
                i += 1
                if config['tags_label'] in lines[i]:
                    entry_tags = lines[i].split(' ')[1:] 
                    tags += [e.rstrip("\n\r") for e in entry_tags]
                else:
                    entry_tags = []
                entry_tags_str=','.join(entry_tags).rstrip("\n\r")
                entry_divs += f"<div class=\"filterDiv\" data-timestamp={timestamp[len(config['timestamp_label']):]} data-tags={entry_tags_str}>\n"
                entry_divs += f"<b>{timestamp}</b><br>\n"
                if len(entry_tags) > 0:
                    entry_divs += f"<b>{lines[i]}</b><br>\n"
                    i += 1
                while i < len(lines) and config['timestamp_label'] not in lines[i]:
                   if len(lines[i]) != 0:
                       entry_divs += f"{lines[i]}<br>\n"
                   i += 1 

                entry_divs += "<br></div>\n"
    html_file.write("<div id=\"myBtnContainer\">")
    html_file.write("<button class=\"btn active\" onclick=\"filterSelection('all')\"> Show all</button>")
    tags=list(dict.fromkeys(tags))
    for tag in tags:
        html_file.write(f"<button class=\"btn\" onclick=\"filterSelection('{tag}')\">{tag}</button>")
    html_file.write("</div>")
    html_file.write(entry_divs) 
    html_file.write(html_js)

def open_editor():
    if config['open_editor']:
        subprocess.call([config['default_editor'],'+ normal GA', config['note_filename']])


def add(args, notes):
    with open(config['note_filename'], "a") as note_file:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamp = f"{config['timestamp_label']} {now}\n"
        tags = (f"{config['tags_label']} " + " ".join("#"+e for e in args["tags"]) +"\n") if args["tags"] is not None else ""
        text = "\n".join(notes) 

        if args['append_to_last']:
            new_entry = f"{text}\n"
        else:
            new_entry = f"{timestamp}{tags}{text}\n"

        note_file.write(new_entry)
    open_editor()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='note')
    subparser = parser.add_subparsers(help='sub-command help', dest='command')

    add_parser = subparser.add_parser('add', help='Add a new entry to the note')
    add_parser.add_argument('-t','--tags', help='List of tags to add to note entry', type=lambda s: [item for item in s.split(',')], required=False)
    add_parser.add_argument('-ne','--no_editor', help='Do not open the editor', action='store_true')
    add_parser.add_argument('-ap','--append_to_last', help='Add to the last timestamp', action='store_true')
    add_parser.add_argument('-ml','--multiline_input', help='Multline user input', action='store_true')
    add_parser.add_argument('textentry', help='Text to add to the note', nargs='*')

    gen_parser = subparser.add_parser('gen', help='Generate html page')

    args = vars(parser.parse_args())

    build_config(args)

    if 'add' in args['command']:
        if args['multiline_input']:
            print("Enter/Paste your note. Ctrl-D or Ctrl-Z ( windows ) to save it.")
            notes = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                notes.append(line)
        else:
            notes = [" ".join(args['textentry'])]
        print(notes)
        add(args, notes)
    elif 'gen' in args['command']:
        generate_html(args)
