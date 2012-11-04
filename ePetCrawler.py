__author___ = 'Marco Endress'
__version__ = '0.1'
__date__ = '11/01/2012'

import sys, os
import re
import mechanize
from BeautifulSoup import BeautifulSoup

epetitionAccount = { 
        'u'  : 'yourUsername',
        'pw' : 'yourPassword'
    }

class Args:
    """
    command line argumentsn
    """
    def __init__(self, usage='Usage: %(progname)s [opt...] [file...]'):
        "init, usage string: embed program name as %(progname)s"
        self.progname = os.path.basename(sys.argv[0])
        self._argv = sys.argv[1:]
        self._usage = usage
        
    def usage(self):
        "print usage message, and exit"
        print >> sys.stderr
        print >> sys.stderr, self._usage % {'progname': self.progname}
        print >> sys.stderr        
        sys.exit(1)

class EpetitionsCrawler:
    """
    grab epetition data 
    """
    
    def __init__(self, petId):
        "init"
        self._petId = petId
        self.br = None
        self.host = 'https://epetitionen.bundestag.de'
        self.grabUrl = 'mitzeichnungsliste.$$$.a.u.page.\
                        @.batchsize.100.html#pagerbottom'
        self.pageCounter = 0
        self.subscrCount = 0
        
    def grabpetID(self):
        ""
        print "+++++++++++++++++++++++++++++++++++++"
        print "+\tEpetitionsCrawler %s       +" % (__version__)
        print "+++++++++++++++++++++++++++++++++++++"
        self.openBr()
        self.logIn()
        self.br.select_form(name="suchform")
        self.br.form['suchbegriff'] = self._petId
        r = self.br.submit()
        lastLink = list(self.br.links(text_regex=re.compile(self._petId)))[-1]
        html = self.br.open(lastLink.url)
        pattern = r'(\d+)*\n&'
        matches = re.compile(pattern).findall(html.read())
        
        if matches == []:
            self.subscrCount = -1
        else:
            self.subscrCount = matches[0]
            
        self.pageCounter = int(self.subscrCount) / 100
        
        if (int(self.subscrCount) % 100) > 0:
            self.pageCounter += 1
            
        print '%s subscribers(s) -> %i pages to parse' % (self.subscrCount, self.pageCounter)
        s = lastLink.url.split('$$$')[0]
        f = open(self._petId, 'a')

        for i in range(0, self.pageCounter + 1):
            page = self.host + s + self.grabUrl.replace('@', str(i))
            html = self.br.open(page)
            soup = BeautifulSoup(''.join(html))
            table = soup.find('table', id="subscriber")
            f.write(str(table))
            
        self.closeBr()
    
    def openBr(self):
        "open mechanize session"
        self.br = mechanize.Browser()
        self.br.addheaders = [
        ( 'User-agent', 
          'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) \
              Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    
    def closeBr(self):
        "close mechanize session"
        self.br.close()
        
    def logIn(self):
        "login to epetitionen.bundestag.de with username and password"
        try:
            self.br.open("https://epetitionen.bundestag.de/epet/anmelden.html")
            self.br.select_form(nr=1)
            self.br.form['j_username'] = epetitionAccount['u']
            self.br.form['j_password'] = epetitionAccount['pw']
            html = self.br.submit()
            pattern = 'posteingang'
            matches = re.compile(pattern).findall(html.read())
           
            if matches == []:
                raise Exception('login failure!\n\tcheck username and\n\tpassword')
            else:
                print "login okay"
            
        except Exception, ex:
            print "\tError: %s" % ex
            sys.exit(1)

      #def searchpetID(self):

def main():
    """
    """
    a = Args('Usage: %(progname)s [-p petitionId] [-f filename]')
    "ToDo clean up"
    if len(sys.argv) != 3:
        a.usage()
        
    petCrawler = EpetitionsCrawler(sys.argv[2])
    petCrawler.grabpetID()

if __name__ == "__main__":
    main()
