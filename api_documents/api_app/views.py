# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from models import Article, APIDoc
import json
from django.core import serializers


def api_docs(request):
  '''
  query api docs using doc ids or api route and(or) method 
  '''
  doc_ids = request.GET.get("doc_ids", "")
  api_route = request.GET.get("api_route", "")
  method = request.GET.get("method", "")
  include_article = request.GET.get("include_article", False)
  #print include_article
  api_docs = []

  if doc_ids:
    api_docs = [APIDoc.objects.get(id=doc_id) for doc_id in map(int, doc_ids.split(","))]
  elif api_route or method:
    query = APIDoc.objects.all()
    if api_route:
      query = query.filter(api_route=api_route)
    else:
      query.filter(method=method)
    api_docs = list(query)

  article_dict = {}
  if include_article and api_docs:
    for api_doc in api_docs:
      article_id = api_doc.article.id
      related_article = Article.objects.get(id=article_id)
      article_dict[article_id] = related_article

  output = '''
    <html>
      <head>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
        <title>
          Query for api docs
        </title>
      </head>
      <body>
        <h1>
          Query for api docs
        </h1>
        <div class="container">
        %s
        </div>
      </body>
    </html>''' % "</div><br><br><div class='container'>".join(
        [serializers.serialize('json', [api_doc, article_dict[api_doc.article.id]]) for api_doc in api_docs])

  return HttpResponse(output)