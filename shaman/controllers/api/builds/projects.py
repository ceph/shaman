import datetime
import smtplib, socket
from email.mime.text import MIMEText
import requests

from pecan import expose, abort, request
from pecan.secure import secure
from pecan import conf

from shaman.models import Project, Build
from shaman.auth import basic_auth
from shaman.controllers.api.builds import refs
from shaman import models


class ProjectAPIController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
        else:
            request.context['project_id'] = self.project.id

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return self.project.build_refs

    #TODO: we need schema validation on this method
    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.project:
            self.project = models.get_or_create(Project, name=self.project_name)
        url = request.json["url"]
        # check if there is an existing build that is queued, where the URL
        # wouldn't match
        queued_build = models.Build.query.filter_by(
            project=self.project,
            sha1=request.json['sha1'],
            ref=request.json['ref'],
            status='queued',
        ).first()
        if queued_build:
            build = queued_build
        else:
            build = models.Build.query.filter_by(url=url, sha1=request.json['sha1']).first()
        data = dict(
            project=self.project,
            ref=request.json["ref"],
            sha1=request.json["sha1"],
            flavor=request.json.get("flavor", "default"),
            extra=request.json.get('extra', dict()),
            distro=request.json.get('distro'),
            distro_version=request.json.get('distro_version'),
            url=request.json.get("url"),
            log_url=request.json.get("log_url"),
            build_id=request.json.get("build_id"),
            status=request.json.get("status"),
            distro_arch=request.json.get("distro_arch"),
        )
        if request.json["status"] == "completed":
            data["completed"] = datetime.datetime.utcnow()
            self._send_build_completion_email(data)
        if not build:
            build = models.get_or_create(Build, **data)
        else:
            build.update_from_json(data)
        return {}

    def _send_build_completion_email(self, data):
        result_sender = getattr(conf, "result_email", "")
        result_receiver = self._get_receiver_email(sha1=data["sha1"])
        if not result_receiver:
            print("Mail not sent! Cannot find commit in ceph/ceph-ci.")
            return
        subject = "Shaman build completed for {project} ({ref}) for {distro}".format(
                project=data['project'].name, ref=data['ref'], distro=data['distro'], flavor=data['flavor'])
    
        msg = MIMEText("Build completed for: \n\n {status} | {project} | {ref} | {distro} | {distro_version} | \
                {flavor} | {distro_arch}".format(status=data["status"], project=data['project'].name, ref=data['ref'], \
                distro=data['distro'], distro_version=data["distro_version"], flavor=data['flavor'], distro_arch=data["distro_arch"]))
        msg['Subject'] = subject
        msg['From'] = result_sender
        msg['To'] = result_receiver
        try:
            smtp = smtplib.SMTP('localhost', 1025)
            smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
            smtp.quit()
        except socket.error:
            print("Failed to connect to mail server!")

    def _get_receiver_email(self, sha1):
        url = "https://api.github.com/repos/ceph/ceph-ci/git/commits/{commit_hash}".format(commit_hash=sha1)
        try:
            data = requests.get(url).json()
            return data["author"]["email"]
        except:
            return ""

    @expose()
    def _lookup(self, ref_name, *remainder):
        return refs.RefAPIController(ref_name), remainder


class ProjectsAPIController(object):

    @expose('json')
    def index(self):
        resp = {}
        for project in Project.query.all():
            resp[project.name] = project.build_refs
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectAPIController(project_name), remainder
