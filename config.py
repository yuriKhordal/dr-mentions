from typing import Tuple

def _parseError(path: str, line: str, linenum: int):
   line = line.removesuffix('\n')
   error = f"Failed to parse '{path}' at line {linenum}:\n> {line}"
   return RuntimeError(error)

def _get_key_pair(line: str) -> Tuple[str, str] | None:
   kv = line.split('=')
   if (len(kv) != 2): return None
   kv[0] = kv[0].strip()
   kv[1] = kv[1].strip()
   return (kv[0], kv[1])

def _isEmptyOrSpace(string: str) -> bool:
   return string == None or string == '' or string.isspace()

def initConfig(path: str, user: str, subscribes: list[str]) -> None:
   with open(path, "w") as conf:
      conf.write(f"User={user}\n")
      conf.write(f"LastMention=\n")
      for sub in subscribes:
         conf.write(f"Subscribe={sub}\n")

def getConfig(path: str):
   config = {}
   with open(path) as file:
      count = 1
      for line in file:
         if _isEmptyOrSpace(line):
            count += 1
            continue
         kv = _get_key_pair(line)
         if (kv == None):
            raise _parseError(path, line, count)
         if (kv[0] == 'User'):
            if _isEmptyOrSpace(kv[1]):
               raise _parseError(path, line, count)
            config['User'] = kv[1]
         elif (kv[0] == 'LastMention'):
            config['LastMention'] = kv[1]
         elif (kv[0] == 'Subscribe'):
            if 'Subscribe' not in config:
               config['Subscribe'] = [kv[1]]
            else:
               config['Subscribe'].append(kv[1])
         else: raise _parseError(path, line, count)
         count += 1
   if 'User' not in config:
      raise RuntimeError(f"Missing 'User=' field in '{path}'.")
   if 'Subscribe' not in config:
      config['Subscribe'] = []
   return config

def updateMention(path: str, date: str) -> None:
   with open(path, "r+") as file:
      text = file.read()

      start = text.find('=', text.find('LastMention')) + 1
      if (start == 0):
         text += '\nLastMention=' + date
      else:
         # if the syntax is 'LastMention = Date' with spaces, leave the spaces after the '='
         while (start < len(text) and text[start] != '\n' and text[start].isspace()):
            start += 1
         end = text.find('\n', start)
         if (end == -1): end = len(text)
         text = text[:start] + date + text[end:]

      file.seek(0)
      file.write(text)
      file.truncate()