#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2,json
from google.appengine.api import urlfetch, search
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
import jinja2
import os

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates")
)

class Parking(ndb.Model):
    id_parcheggio = ndb.StringProperty()
    id_utente = ndb.StringProperty()
    ora_ingresso = ndb.FloatProperty()
    ora_uscita = ndb.FloatProperty()
    abbonato = ndb.StringProperty()


class MainHandler(webapp2.RequestHandler):
    def get(self):
        p = Parking()
        p.id_parcheggio = None
        p.id_utente = None
        p.ora_ingresso = None
        p.ora_uscita = None
        p.abbonato = None
        key = p.put()  #save entity, mette i nuovi dati nel database
        template = JINJA_ENVIRONMENT.get_template('index.html')
        #self.response.write(key.urlsafe())
        #key = ndb.Key(urlsafe=url_string)
        self.response.out.write(template.render())

class PutData(webapp2.RequestHandler):
    def post(self):
        body = self.request.body  #prende la richiesta ricevuta
        body_dict = json.loads(body) # salva in json e manda dati
        p = Parking()
        p.id_parcheggio= body_dict["id_parcheggio"]
        p.id_utente = body_dict["id_utente"]
        p.ora_ingresso = body_dict["ora_ingresso"]
        p.ora_uscita = body_dict["ora_uscita"]
        p.abbonato = body_dict["abbonato"]
        key = p.put()
        conto_tot = self.conto(p.id_utente, p.ora_uscita, p.ora_ingresso)
        avviso = self.polizia(p.id_utente,p.ora_ingresso)
        risposta = ""
        if ( conto_tot == 0 and avviso == ""):
            risposta = "Ancora in sosta"
        elif(conto_tot == 0 and avviso != ""):
            risposta = avviso
        elif(conto_tot != 0):
            risposta = conto_tot
        self.response.write(risposta)

    def conto(self, utente, orauscita, oraingresso):
         conto_tot = 0
         tariffa = 2
         if (orauscita != None and utente != None):
            if(orauscita <= 20.0):
                uscita = orauscita
                ingresso = oraingresso
                ore_sosta = uscita - ingresso
                conto_ore = ore_sosta//1   #quante ore di sosta
                conto_tot = (conto_ore + 1) * tariffa   #calcolo la tariffa
            else:
                uscita = 20.0
                ingresso = oraingresso
                ore_sosta = uscita - ingresso
                conto_ore = ore_sosta // 1  # quante ore di sosta
                conto_tot = (conto_ore + 1) * tariffa  # calcolo la tariffa
         return conto_tot
    def polizia(self, utente, oraingresso):
        avviso = ""
        if (utente == None and oraingresso != 0 ):
            avviso = "Poliziaaaaaaaaaaaaaaaaaaaa"
        return avviso


class GetHandler(webapp2.RequestHandler):
    def get(self):
        result = Parking.query().fetch()
        dicts = []
        for match in result:
            dicts.append({'id_parcheggio': match.id_parcheggio, 'id_utente': match.id_utente, 'ora_ingresso':match.ora_ingresso, 'ora_uscita': match.ora_uscita, 'abbonato':match.abbonato})
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        resultjson = json.dumps(dicts)
        self.response.write(resultjson)


class DelHandler(webapp2.RequestHandler):
    def post(self):
        key = self.request.get('key')
        entryKey = ndb.Key(urlsafe=key)
        p = entryKey.get()
        p.key.delete()
        self.response.write("deleted")

class DelAllHandler(webapp2.RequestHandler):
    def get(self):
        person = Parking.query(Parking.id_parcheggio=="park03").fetch(keys_only=True)
        ndb.delete_multi(person)
        self.response.write("all done")

class Conto(webapp2.RequestHandler):
    def post(self):
        body = self.request.body
        parcheggio = Parking.query(Parking.id_parcheggio == body).fetch()
        dict = []
        dict.append(parcheggio)
        self.response.write(dict)

class CreateHandler(webapp2.RequestHandler):
    def post(self):
        nickname = self.request.get('nickname')
        description = self.request.get('description')
        d = search.Document(
            fields=[search.TextField(name='author', value=nickname),
                    search.TextField(name='description', value=description),
                    search.DateField(name='date', value=datetime.now().date())])
        results = search.Index(name=_INDEX_NAME).put(d)
        self.response.write(results[0].id)

class SearchHandler(webapp2.RequestHandler):
    def post(self):
        query = self.request.get('query')
        query_obj = search.Query(query_string=query)
        results = search.Index(name=_INDEX_NAME).search(query=query_obj)
        self.response.write(results)

class Mappa(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('map.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/putdata', PutData),
    ('/get', GetHandler),
    ('/delete', DelHandler),
    ('/delall', DelAllHandler),
    ('/createDoc', CreateHandler),
    ('/searchDoc', SearchHandler),
    ('/conto', Conto),
    ('/mappa',Mappa)
], debug=True)
