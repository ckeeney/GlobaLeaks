# -*- coding: utf-8 -*-
#
#  admlangfiles
#  **************
#
# Backend supports for jQuery File Uploader, and implementation of the
# file language statically uploaded by the Admin

#`This code differs from handlers/file.py because files here are not tracked in the DB

from __future__ import with_statement
import os
import time
import re

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from cyclone.web import StaticFileHandler

from globaleaks.settings import GLSetting
from globaleaks.handlers.admstaticfiles import dump_static_file
from globaleaks.handlers.base import BaseStaticFileHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils.utility import log
from globaleaks.rest import errors

class LanguageFileHandler(BaseStaticFileHandler):
    """
    This class is used to return the custom translation files;
    if the file are not present, default translations are returned
    """
    def langfile_path(self, lang):
        return os.path.abspath(os.path.join(GLSetting.glclient_path, 'l10n', ('%s.json') % lang))

    def custom_langfile_path(self, lang):
        return os.path.abspath(os.path.join(self.root, 'l10n', ('%s.json') % lang))

    @inlineCallbacks
    def post(self, path):
        """
        Upload a custom language file
        """
        lang = os.path.join(self.parse_url_path(path))
        print lang
        start_time = time.time()

        uploaded_file = self.get_uploaded_file()

        try:
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, self.custom_langfile_path(lang))
        except OSError as excpd:
            log.err("OSError while create a new custom lang file [%s]: %s" % (self.custom_langfile_path(lang), excpd))
            raise errors.InternalServerError(excpd.strerror)
        except Exception as excpd:
            log.err("Unexpected exception: %s" % excpd)
            raise errors.InternalServerError(excpd)

        dumped_file['elapsed_time'] = time.time() - start_time

        log.debug("Admin uploaded new lang file: %s" % dumped_file['filename'])

        self.set_status(201) # Created
        self.finish(dumped_file)


    def get(self, path, include_body=True):
        lang = os.path.join(self.parse_url_path(path))
        if os.path.isfile(self.custom_langfile_path(lang)):
            StaticFileHandler.get(self, self.custom_langfile_path(lang), include_body)
        else:
	    # to reuse use the StaticFile handler we need to change the root path
	    self.root = os.path.abspath(os.path.join(GLSetting.glclient_path, 'l10n'))
            StaticFileHandler.get(self, self.langfile_path(lang), include_body)


    def delete(self, path):
        """
        Parameter: filename
        Errors: LangFileNotFound
        """
        lang = os.path.join(self.parse_url_path(path))
        if not os.path.exists(self.custom_langfile_path(lang)):
            raise errors.LangFileNotFound

        os.unlink(self.custom_langfile_path(lang))

        self.set_status(200)
        self.finish()

