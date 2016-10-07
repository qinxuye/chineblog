#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2016 Qin Xuye <qin@qinxuye.me>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'chineblog.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name

from blog.utils import to_text


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        # append an app list module for "Applications"
        self.children.append(modules.AppList(
            _(to_text('应用')),
            collapsible=True,
            column=1,
            css_classes=('collapse',),
            exclude=('django.contrib.*',),
        ))
        
        # append an app list module for "Administration"
        self.children.append(modules.ModelList(
            _(to_text('Admin管理')),
            column=1,
            collapsible=True,
            models=('django.contrib.*',),
        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _(to_text('文件管理')),
            column=2,
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]
        ))

        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            column=2,
            limit=5,
            collapsible=False,
        ))


