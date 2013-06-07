# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.auth_settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pluggable authentication controller for RhodeCode

    :created_on: Nov 26, 2010
    :author: akesterson
    :copyright: (C) 2012-2013 Andrew Kesterson <andrew@aklabs.net>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sets
import pprint
import logging
import formencode.htmlfill
import traceback

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from sqlalchemy.exc import DatabaseError

from rhodecode.lib import helpers as h
from rhodecode.lib.compat import json, formatted_json
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib import auth_modules
from rhodecode.model.forms import AuthSettingsForm
from rhodecode.model.db import RhodeCodeSetting
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AuthSettingsController(BaseController):

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        super(AuthSettingsController, self).__before__()

    def __load_defaults(self):
        c.available_plugins = [
            'rhodecode.lib.auth_modules.auth_rhodecode',
            'rhodecode.lib.auth_modules.auth_container',
            'rhodecode.lib.auth_modules.auth_ldap',
            'rhodecode.lib.auth_modules.auth_crowd',
        ]
        c.enabled_plugins = RhodeCodeSetting.get_auth_plugins()

    def index(self, defaults=None, errors=None, prefix_error=False):
        self.__load_defaults()
        _defaults = {}
        # default plugins loaded
        formglobals = {
            "auth_plugins": ["rhodecode.lib.auth_modules.auth_rhodecode"]
        }
        formglobals.update(RhodeCodeSetting.get_auth_settings())
        formglobals["plugin_settings"] = {}
        formglobals["auth_plugins_shortnames"] = {}
        _defaults["auth_plugins"] = formglobals["auth_plugins"]

        for module in formglobals["auth_plugins"]:
            plugin = auth_modules.loadplugin(module)
            plugin_name = plugin.name()
            formglobals["auth_plugins_shortnames"][module] = plugin_name
            formglobals["plugin_settings"][module] = plugin.plugin_settings()
            for v in formglobals["plugin_settings"][module]:
                fullname = ("auth_" + plugin_name + "_" + v["name"])
                if "default" in v:
                    _defaults[fullname] = v["default"]
                # Current values will be the default on the form, if there are any
                setting = RhodeCodeSetting.get_by_name(fullname)
                if setting:
                    _defaults[fullname] = setting.app_settings_value
        # we want to show , seperated list of enabled plugins
        _defaults['auth_plugins'] = ','.join(_defaults['auth_plugins'])
        if defaults:
            _defaults.update(defaults)

        formglobals["defaults"] = _defaults
        # set template context variables
        for k, v in formglobals.iteritems():
            setattr(c, k, v)

        log.debug(pprint.pformat(formglobals, indent=4))
        log.debug(formatted_json(defaults))
        return formencode.htmlfill.render(
            render('admin/auth/auth_settings.html'),
            defaults=_defaults,
            errors=errors,
            prefix_error=prefix_error,
            encoding="UTF-8",
            force_defaults=True,
        )

    def auth_settings(self):
        """POST create and store auth settings"""
        self.__load_defaults()
        _form = AuthSettingsForm(c.enabled_plugins)()
        log.debug("POST Result: %s" % formatted_json(dict(request.POST)))

        try:
            form_result = _form.to_python(dict(request.POST))
            for k, v in form_result.items():
                if k == 'auth_plugins':
                    # we want to store it comma separated inside our settings
                    v = ','.join(v)
                log.debug("%s = %s" % (k, str(v)))
                setting = RhodeCodeSetting.get_by_name_or_create(k, v)
                Session().add(setting)
            Session().commit()
            h.flash(_('Auth settings updated successfully'),
                    category='success')
        except formencode.Invalid, errors:
            log.error(traceback.format_exc())
            e = errors.error_dict or {}
            return self.index(
                defaults=errors.value,
                errors=e,
                prefix_error=False)
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of auth settings'),
                    category='error')

        return redirect(url('auth_home'))
