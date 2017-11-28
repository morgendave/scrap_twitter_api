# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Article(models.Model):
  topic = models.CharField(max_length=50, db_index=True)
  data_type = models.CharField(max_length=32, db_index=True)
  title = models.CharField(max_length=200, db_index=True)
  content = models.TextField(blank=True)

  class Meta:
    unique_together = ('topic', 'data_type', 'title')

class APIDoc(models.Model):
  api_route = models.CharField(max_length=50, blank=True, db_index=True)
  method = models.CharField(max_length=50, blank=True, db_index=True)
  description = models.TextField(blank=True, null=True)
  resource_url = models.URLField(max_length=200, blank=True, null=True)
  example_request = models.TextField(blank=True, null=True)
  example_response = models.TextField(blank=True, null=True)
  response_format = models.CharField(max_length=50, blank=True, null=True)
  authentication_required = models.NullBooleanField()
  rate_limited = models.NullBooleanField()
  limit_user = models.IntegerField(blank=True, null=True)
  limit_app = models.IntegerField(blank=True, null=True)
  parameters = models.TextField(blank=True, null=True)
  title = models.CharField(max_length=50, blank=True, db_index=True)

  article = models.ForeignKey(Article, default=1, null=True)

  class Meta:
    unique_together = ('api_route', 'method', 'title')