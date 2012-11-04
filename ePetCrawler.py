__author___ = 'Marco Endress'
__version__ = '0.2'
__date__    = '11/04/2012'
__progname__= 'ePetGrabber'

import sys, os, time
import re
import mechanize
import Queue
from BeautifulSoup import BeautifulSoup
import threading
"""
epetitionAccount = { 
        'u'  : 'yourUsername',
        'pw' : 'yourPassword'
    }
    """

########################################################################
class Args:
    """ command line arguments """
    #----------------------------------------------------------------------
    def __init__(self, usage='Usage: %(progname)s [opt...] [file...]'):
        "init, usage string: embed program name as %(progname)s"
        self.progname = os.path.basename(sys.argv[0])
        self._argv = sys.argv[1:]
        self._usage = usage
        
    #----------------------------------------------------------------------
    def usage(self):
        """ print usage message, and exit """
        print >> sys.stderr
        print >> sys.stderr, self._usage % {'progname': self.progname}
        print >> sys.stderr        
        sys.exit(1)
        
########################################################################
class SideDownloader(threading.Thread):
    """ Threaded Side Downloader """
 
    #----------------------------------------------------------------------
    def __init__(self, queue, cookie):
        """ init Side Downloader """
        threading.Thread.__init__(self)
        self.queue = queue
        self.threadBrowser = mechanize.Browser()
        self.threadBrowser._ua_handlers['_cookies'].cookiejar = cookie
 
    #----------------------------------------------------------------------
    def run(self):
        """"""
        while True:
            url = self.queue.get()
            self.download_side(url)
            self.queue.task_done()
 
    #----------------------------------------------------------------------
    def download_side(self, url):
        """"""
        try:
            side = self.threadBrowser.open(url)
            html = side.read()
            fname = os.path.basename(url)
            with open(fname, "wb") as f:
                f.write(html)
            
        except Exception, ex:
            print ex
            
########################################################################
class EpetitionsGrabber:
    """ grab epetition data """
    #----------------------------------------------------------------------
    def __init__(self, petId):
        """ init EpetitionsGrabber """
        self._petId = petId
        self._br = None
        self._host = 'https://epetitionen.bundestag.de'
        self._grabUrl = 'mitzeichnungsliste.$$$.a.u.page.@.batchsize.100.html#pagerbottom'
        
    #----------------------------------------------------------------------
    def grabpetID(self):
        """"""
        self.printMsg(__progname__ + " " + __version__, 1)
        self.openBr()
        self.login()
        self._br.select_form(name="suchform")
        self._br.form['suchbegriff'] = self._petId
        r = self._br.submit()
        lastLink = list(self._br.links(text_regex=re.compile(self._petId)))[-1]
        self._grabUrl = lastLink.url.split('$$$')[0] + self._grabUrl
        html = self._br.open(lastLink.url)
        pattern = r'(\d+)*\n&'
        matches = re.compile(pattern).findall(html.read())
        
        if matches == []:
            subscrCount = -1
            #raise
        else:
            subscrCount = matches[0]
            pageCounter = self.calcPages(subscrCount)
        
        self.printMsg("Petition %s:\n%s subscribers(s)\n-> %i sides to parsing " % (self._petId, subscrCount , pageCounter), 0)
        start_timer = time.time()
        
        queue = Queue.Queue()
        fileList = []
        cookie = self._br._ua_handlers['_cookies'].cookiejar
 
        # create a thread pool and give them a queue
        for i in xrange(15):
            threadLocal = SideDownloader(queue, cookie)
            threadLocal.setDaemon(True)
            threadLocal.start()

        for i in xrange(0, pageCounter):
            url = self._grabUrl.replace('@', str(i))
            queue.put(self._host + url)
            fileList.append(url)
       
        queue.join()
        self.writeOut(fileList)
        latency = time.time() - start_timer
        self.printMsg("time left: %s" % str(latency), 0)
        self.printMsg("all done ;-)", 2)
        self.closeBr()
    #----------------------------------------------------------------------
    def openBr(self):
        """ open mechanize session """
        self._br = mechanize.Browser()
        self._br.addheaders = [
        ( 'User-agent', 
          'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) \
              Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
              
    #----------------------------------------------------------------------
    def closeBr(self):
        """ close mechanize session """
        self._br.close()
    
    #----------------------------------------------------------------------
    def login(self):
        """ login to epetitionen.bundestag.de with username and password """
        try:
            self._br.open("https://epetitionen.bundestag.de/epet/anmelden.html")
            self._br.select_form(nr=1)
            self._br.form['j_username'] = epetitionAccount['u']
            self._br.form['j_password'] = epetitionAccount['pw']
            html = self._br.submit()
            pattern = 'posteingang'
            matches = re.compile(pattern).findall(html.read())
           
            if matches == []:
                raise Exception('login failure!\ncheck username and\npassword')
            else:
                self.printMsg("login okay", 0)
            
        except Exception, ex:
            #print "\tError: %s" % ex
            self.printMsg(str(ex), 0)
            sys.exit(1)
      
    #----------------------------------------------------------------------
    def calcPages(self, subscribers):
        """ calculate number of sides to parsing """
        pageCounter = int(subscribers) / 100
        
        if (int(subscribers) % 100) > 0:
            pageCounter += 1
            
        return pageCounter
        
    #----------------------------------------------------------------------
    def writeOut(self, fileList):
        """ parse html files and write output file """
        table = ''
        for item in fileList:
            fhandler = open(os.path.basename(item), "r")
            raw_html = fhandler.read()
            soup = BeautifulSoup(''.join(raw_html))
            table += str(soup.find('table', id="subscriber"))
      
        filename = self._petId + '.html'
        with open(filename, 'w') as f:
            f.write(table)
    
    #----------------------------------------------------------------------
    def printMsg(self, msg, outBorder):
        """ print nice output """
        try:
            border = "+++++++++++++++++++++++++++++++++++++++"
            if outBorder == 1:
                print border
            
            if len(msg) <= len(border):
                borderRight = "+"
                borderRight = borderRight.rjust(len(border) - len(msg) - 2)
                print "+ %s"  % (msg + borderRight)
            else:
                newlines = msg.count('\n')
                for i in xrange(newlines + 1):
                      borderRight = "+"
                      borderRight = borderRight.rjust(len(border) - len(msg.split('\n')[i]) - 2)
                      print "+ %s"  % (msg.split('\n')[i] + borderRight)
                
            if outBorder == 2:
                print border
            else:
                print "---------------------------------------"
                
        except Exception, ex:
            print ex
#--------------------------------------------------------------------------
def main():
    """"""
    a = Args('Usage: %(progname)s [-p petitionId] [-f filename]')
    "ToDo clean up"
    if len(sys.argv) != 3:
        a.usage()
        
    petGrabber = EpetitionsGrabber(sys.argv[2])
    petGrabber.grabpetID()

if __name__ == "__main__":
    main()
