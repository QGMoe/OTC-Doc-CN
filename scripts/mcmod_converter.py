import requests
from bs4 import BeautifulSoup, NavigableString
import argparse

def build_args():
  parser = argparse.ArgumentParser(description="MC百科 HTML -> AsciiDoc 转换工具")
  parser.add_argument("item_id", help="MC百科 Item ID")
  parser.add_argument("-o", "--output")
  return parser.parse_args();

def fetch_context(item_id):
  url = f"https://www.mcmod.cn/item/{item_id}.html"
  headers = {
    "User-Agent": "Mozilla/5.0"
  }

  r = requests.get(url, headers=headers)
  r.raise_for_status()

  soup = BeautifulSoup(r.text, "html.parser")
  content = soup.select_one(".item-content") # Content Class

  if not content:
    print("Content Not Found")
    return None

  return convert_block(content);

# Convert Core BEGIN

def convert_common(soup,converter):
  result = ""
  
  if isinstance(soup,NavigableString):
    result = soup.get_text();
  elif soup.name == "div":
    result = convert_children(soup,converter)
  elif soup.name == "a":
    href = soup.get("href")
    result = f"link:{href}[{convert_children(soup,converter)}]"
  elif soup.name == "strong":
    result = "**"+convert_children(soup,converter)+"**"
  else:
    result = f"<{soup.name}{" "+" ".join(f'{k}="{" ".join(v) if isinstance(v,list)else v}"' for k,v in soup.attrs.items()) if soup.attrs else ""}>{convert_children(soup,converter)}</{soup.name}>"
  return result

def convert_block(soup):
  result = ""
  this = convert_block;
  
  if soup.name == "p":
    result = "\n"+convert_children(soup,this)+"\n"
  elif is_title(soup):
    level : int
    classes = soup.get("class",[])
    for clas in classes:
      if clas.startswith("common-text-title-"):
        level = int(clas.split("-")[-1])
    prefix = ""
    for i in range(0,level): prefix += "="
    result = f"{prefix} {convert_children(soup,this)}\n"
  elif soup.name == "pre":
    classes = soup.get("class",[])
    lang = None
    for clas in classes:
      if "brush:" in clas:
        lang = clas.split("brush:")[1].split(";")[0]
        break
    result = f"\n[source{f",{lang}" if lang is not None else ""}]\n----\n{convert_children(soup,convert_source)}\n----"
  elif soup.name == "ul":
    result = "\n"+convert_children(soup,convert_list)+"\n"
  else:
    result = convert_common(soup,this)
  return result.replace("\xa0", " ") # Replace 不间断空格
  
def convert_list(soup,depth=1,first_para=True):
  result = ""
  this = convert_list
  stars = ""
  for i in range(0,depth): stars+="*" 
  
  if soup.name == "ul":
    result = convert_children(soup,lambda s: this(s,depth+1))
  elif soup.name == "li":
    result = f"{stars} {convert_children(soup,lambda s: this(s,depth+1))}"
  elif soup.name == "p":
    result = convert_children(soup,lambda s: this(s,depth,False))+"\n" if first_para else f"+\n{convert_children(soup,lambda s: this(s,depth,False))}\n"
  else:
    result = convert_common(soup,lambda s: this(s,depth,first_para))
  return result
  
def convert_source(soup):
  result=""
  this = convert_source
  if soup.name == "br":
    result = "\n"
  else:
    result = soup.get_text()
  return result

def convert_children(soup,converter):
  result = ""
  for node in soup.children:
    result += converter(node)
  return result
  
def is_title(node):
  return node.name == "span" and "common-text-title" in node.get("class", [])

# Convert Core END

def write_to_file(filename,html):
  with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
  print("Written:", filename)

if __name__ == "__main__":
  args = build_args();
  content = fetch_context(args.item_id);
  filename = f"{args.item_id}.adoc" if args.output is None else args.output;
  write_to_file(filename,content);
  