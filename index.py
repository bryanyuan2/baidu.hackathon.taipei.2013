import webapp2 
import urllib2 
import sys, httplib 
from bae.core import const
import MySQLdb

def Hourly_OneDay(dtDay): 
    SENDTPL = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Hourly_OneDay xmlns="http://taqm.epa.gov.tw/taqm">
      <returnDataType>csv</returnDataType>
      <dtDay>%s</dtDay>
    </Hourly_OneDay>
  </soap:Body>
</soap:Envelope>'''

    SoapMessage = SENDTPL % dtDay 
    webservice = httplib.HTTP("taqm.epa.gov.tw") 
    webservice.putrequest("POST", "/taqm/DataService.asmx") 
    webservice.putheader("Host", "taqm.epa.gov.tw") 
#    webservice.putheader("User-Agent", "Python Post") 
    webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"") 
    webservice.putheader("Content-length", "%d" % len(SoapMessage)) 
    webservice.putheader("SOAPAction", "http://taqm.epa.gov.tw/taqm/Hourly_OneDay") 
    webservice.endheaders() 
    webservice.send(SoapMessage) 
    # get the response 
    statuscode, statusmessage, header = webservice.getreply() 
    return webservice.getfile().read() 


def SiteList2(): 
    SENDTPL = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SiteList2 xmlns="http://taqm.epa.gov.tw/taqm">
      <returnDataType>csv</returnDataType>
    </SiteList2>
  </soap:Body>
</soap:Envelope>'''

    SoapMessage = SENDTPL 
    webservice = httplib.HTTPConnection("taqm.epa.gov.tw", 80, timeout=100) 
    webservice.putrequest("POST", "/taqm/DataService.asmx") 
    webservice.putheader("Host", "taqm.epa.gov.tw") 
#    webservice.putheader("User-Agent", "Python Post") 
    webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"") 
    webservice.putheader("Content-length", "%d" % len(SoapMessage)) 
    webservice.putheader("SOAPAction", "http://taqm.epa.gov.tw/taqm/SiteList2") 
    webservice.endheaders() 
    webservice.send(SoapMessage) 
    # get the response 
#    statuscode, statusmessage, header = webservice.getreply() 
#    print "Response: ", statuscode, statusmessage 
#    print "headers: ", header 
    return webservice.getresponse().read() 

class Index(webapp2.RequestHandler):
    def get(self):
        self.response.write('index\n')
from bae.api.memcache import BaeMemcache
import md5
import re
class Rank(webapp2.RequestHandler):
    def get(self):
        cache = BaeMemcache()
        ranking = cache.get('ranking')
        ret = []
        self.response.headers['Content-Type'] = 'text/plain'
        c = 0
        self.response.write("[")
        for r in ranking:
            if c != 0:
                self.response.write(",")
            self.response.write("'")
            self.response.write(r[0])
            self.response.write("',")
            self.response.write(r[1])
            c = 1
        self.response.write("]")

            

class Score(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        
        ranking = []

        m = md5.new()
        m.update(self.request.get('p'))
        key = m.digest()
        cache = BaeMemcache()
        if cache.get(key) != None:
            self.response.write(cache.get(key))
            return
        
        if cache.get('ranking') != None :
            ranking = cache.get('ranking')

        lim = dict({'SO2': 2.5, 'CO': 0.25, 'O3': 25, 'PM10': 17, 'NO2': 11})

        mydb = MySQLdb.connect( host = const.MYSQL_HOST,port = int(const.MYSQL_PORT), user = const.MYSQL_USER, passwd = const.MYSQL_PASS, db = '')
        cursor = mydb.cursor()
        cursor.execute('select * from sites')
        rows = cursor.fetchall() 

        if self.request.get('debug') == 'true':
            self.response.write(self.request.get('p'))
        else:
            p = eval(self.request.get('p'))
          
            ret = []

            sum = 0
            for pp in p['checkins']:
                date = pp['date']
                yy = str(date[0:4])
                mm = str(int(date[5:7]))
                dd = str(int(date[8:10]))
                hh = str(int(date[11:13]))
                lat = pp['lat']
                lon = pp['lng']
                
                min = 1111
                id = 1

                for row in rows:
                    x = lat - float(row[1])
                    y = lon - float(row[2])
                    if x < 0:
                        x = x * -1
                    if y < 0:
                        y = y * -1
                    distance = x + y
                    if distance < min:
                        min = distance
                        id = row[0]



                id = str(id)
                cmd = 'select type, val from data2 where id=' + id + ' and yy=' + yy + ' and mm=' + mm + ' and dd=' + dd + ' and hh=' + hh + ' limit 100'
                cursor.execute(cmd)
                vals = cursor.fetchall()
                
                score = 0

                for val in vals:
                    type = val[0]        
                    value = val[1]
                    if type in lim:
                       score = score + value - lim[type]

                ret.append(score*21 + 123)

                sum += score*21 + 123                

            ranking.append((self.request.get('username') , sum))
            ranking = sorted(set(ranking), key=lambda x: x[1], reverse=True)
            cache.set('ranking', ranking)

            if self.request.get('debug') == 'test':
                for r in ranking:
                    self.response.write(r)

            self.response.write(ret) 

            cache.set(key, str(ret))

        mydb.close()


class Now(webapp2.RequestHandler):
    def get(self):
        self.response.write('now')


class Test(webapp2.RequestHandler):
    def get(self):
        mydb = MySQLdb.connect( host = const.MYSQL_HOST,port = int(const.MYSQL_PORT), user = const.MYSQL_USER, passwd = const.MYSQL_PASS, db = '')
        cursor = mydb.cursor()
        cursor.execute('select * from sites')
        rows = cursor.fetchall() 
        
        lat = 25.01123123
        lon = 121.46325325
        min = 11111 
        id = 1
      
        for row in rows:
            x = lat - float(row[1])
            y = lon - float(row[2])
            if x < 0:
                x = x * -1
            if y < 0:
                y = y * -1
            distance = x + y
            if distance < min:
                min = distance
                id = row[0]

        self.response.write(str(id) + ', ' +  str(min) + '')


        mydb.close()


app = webapp2.WSGIApplication([
    ('/', Index),
    ('/score', Score),
    ('/now', Now),
    ('/list', Rank),
    ('/test', Test)
], debug=True)
 
from bae.core.wsgi import WSGIApplication
application = WSGIApplication(app)

