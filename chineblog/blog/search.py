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
"""
import os

from django.conf import settings
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, NUMERIC, KEYWORD, STORED

from .utils import to_text, strip_html


def index_article(article, index_dir=None):
    index_dir = index_dir or settings.INDEX_DIR
    if not exists_in(index_dir):
        schema = Schema(title=TEXT(stored=True), content=TEXT,
                        id=NUMERIC(stored=True, unique=True), tags=KEYWORD,
                        slug=STORED)
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        idx = create_in(index_dir, schema=schema)
    else:
        idx = open_dir(index_dir)

    writer = idx.writer()
    writer.update_document(title=to_text(article.title),
                           content=strip_html(to_text(article.content)),
                           id=article.pk,
                           tags=[to_text(t.name) for t in article.tags.all()],
                           slug=to_text(article.slug))
    writer.commit()