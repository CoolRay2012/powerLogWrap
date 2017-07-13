#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-04
# @Author  : ${author} (${email})
# @Link    : ${link}
# @Version : $Id$

import sys,os,re
from bs4 import BeautifulSoup as bs
from collections import Counter
from markdown import markdown

def dump_clean(obj):
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                dumpclean(v)
            else:
                print '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print v
    else:
        print obj

def _usage():
  print '''
  python logWrap.py [logDir]
  '''

class Cube(object):
  '''pattern object'''
  def __init__(self, pattern, attrs_dict={}):
    self.pattern = pattern
    self.attrs_dict = attrs_dict
    self.ins_list = []
    self.txt_str = ''

  def get_pattern(self):
    return self.pattern

  def get_attrs(self):
    return self.attrs_dict

  def append_list(self,l):
    self.ins_list.append(l)

  def append_str(self,s):
    #self.txt_str += '> ' + ":".join([st.ljust(40) for st in s.split(":")])
    self.txt_str += '> ' + s

  def dump(self):
    if len(self.ins_list) != 0:
      print "- {0:30} ---> {1:5} times".format(self.pattern, len(self.ins_list))
      if u'count' in self.attrs_dict:
        for c in Counter(self.ins_list).most_common():
          print "  > {}".format(c)
    elif len(self.txt_str) != 0:
      print "- {} --->\n {}".format(self.pattern, self.txt_str)
      #pass

class BrLog(object):
  ''' bugreport parser'''
  def __init__(self, file):
    self.file = file
    self.cube_list = []
    self.get = 0
    self.top_tmp = -1

    '''pick up cube'''
    with open(u'msm8998.xml') as f:
      for child in bs(f.read()).find(u'bugreport').findChildren():
        self.cube_list.append(Cube(str(child.string), child.attrs))

    '''parse txt'''
    with open(file) as f:
      for line in f:
        if line.strip() or self.top_tmp > 0: # we include empty line if has attr 'top'
          if self.get == 1 and self.top_tmp != 0:
            c_tmp.append_str(line)
            self.top_tmp -= 1
            continue
          else:
            for c in self.cube_list:
              m = re.search(c.get_pattern(), line)
              if m:
                self.get = 1
                c_tmp = c
                c.append_str(line)
                if 'top' in c.get_attrs():
                  self.top_tmp = int(c.get_attrs()['top'])
                break
        else:
          self.get = 0
          self.top_tmp = -1

  def report(self):
    print "-------"
    print "#### File [{}]({}) report".format(self.file,self.file)
    for c in self.cube_list:
      c.dump()

class KernelLog(object):
  '''
  kernel log parser
  '''
  def __init__(self, file):
    self.file = file
    self.cube_list = []

    with open(u'msm8998.xml') as f:
      for child in bs(f.read()).find(u'kernel').findChildren():
        self.cube_list.append(Cube(child.string, child.attrs))

    with open(file) as f:
      for line in f:
        for c in self.cube_list:
          m = re.search(c.get_pattern(), line)
          if m:
            c.append_list(m.groups())

  def report(self):
    print "-------"
    print "#### File [{}]({}) report".format(self.file,self.file)
    for c in self.cube_list:
      c.dump()

    #dumpclean(self.cube_list)

class LogcatLog(object):
  '''
  logcatmain log parser
  '''
  def __init__(self, file):
    self.file = file

  def report(self):
    print "-------"
    print "#### File [{}]({}) report".format(self.file,self.file)
    print "- Not supported yet\n"

def main():
  logDir = os.path.abspath(sys.argv[1])
  if not os.path.isdir(logDir):
    _usage()
    return 1

  report_md = "powerLogReport_{}.md".format(os.path.split(logDir)[-1])
  f = open(report_md,'w')
  # redirect stdout -- ATTENTION! you can NOT use 'with' like:
  #     with open(outfile, 'w') as f:
  #       sys.stdout = f
  # since 'with' would close f anto in the end, however, the f==sys.stdout which
  # would lead a error closing current process
  __console__, sys.stdout = sys.stdout, f

  for file in os.listdir(logDir):
    filepath = os.path.join(logDir, file)
    if re.search(u'kernel', file):
      KernelLog(filepath).report()
    elif re.search(u'logcat.*main', file):
      LogcatLog(filepath).report()
    elif re.search(u'bugreport', file):
      BrLog(filepath).report()

  # restore stdout, then it's safe to close f
  sys.stdout = __console__
  f.close()

  # ---------------------
  # generate html by text
  report_html = "powerLogReport_{}.html".format(os.path.split(logDir)[-1])
  with open(report_md, 'r') as f:
    with open(report_html, "w") as e:
      # solution 1
#        for line in f:
#            e.write("<p>" + line.strip() + "</p>\n")
      # solution 2
      e.write(r'<link rel="stylesheet" type="text/css" href="css_github.css">')
      e.write(markdown(f.read(), extensions=['markdown.extensions.nl2br']))

  # open html
  import webbrowser
  webbrowser.open(report_html)

if __name__ == "__main__":
  main()
