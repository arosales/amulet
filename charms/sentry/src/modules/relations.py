
import os
import json
import glob
import json_rpc
import cherrypy
import subprocess


class Module (object):

    @json_rpc.expose_anonymous
    def relations(self):
        if not cherrypy.request.method == "GET":
            raise cherrypy.HTTPError(405)

        if not os.path.exists('/opt/sentry/relations'):
            return {}

        relations = {}
        for relation in glob.glob('/opt/sentry/relations/*'):
            relname = os.path.basename(relation)
            relations[relname] = self.list_units(relname)

        return relations

    @json_rpc.expose_anonymous
    def relation(self, relation=None, unit=None):
        if not cherrypy.request.method == 'GET':
            raise cherrypy.HTTPError(405)

        if not relation:
            raise cherrypy.HTTPError(400)

        if not os.path.exists(os.path.join('/opt/sentry/relations', relation)):
            raise cherrypy.HTTPError(404)

        if not unit:
            return {relation: list_units(relation)}

        if not os.path.exists(os.path.join('/opt/sentry/relations', relation, unit)):
            raise cherrypy.HTTPError(404)

        with open(os.path.join('/opt/sentry/relations', relation, unit), 'r') as u:
            unit_data = json.loads(u.read().decode('UTF-8'))

        return {relation: {unit: unit_data}}

    def list_units(self, relation):
        units = []
        for relunits in glob.glob('/opt/sentry/relations/%s/*' % relation):
            units.append(os.path.basename(relunits))

        return units
