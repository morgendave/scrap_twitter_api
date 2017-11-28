# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from api_app.models import Article, APIDoc

class ApiDocumentScrapePipeline(object):
  def process_item(self, item, spider):
  	if item['data_type'] != "api_doc":
  		article = Article(**item)
  		if not Article.objects.filter(title=item["title"]) \
  													.filter(topic=item["topic"]) \
  													.filter(data_type=item["data_type"]) \
  													.count():
  			article.save()
  	else:
  		title = item.get("title")
  		item.pop("data_type")
  		saved_article = list(Article.objects.filter(title=title) \
  																	 			.filter(data_type="api_page"))[0]
  		api_doc = APIDoc(**item)
  		api_doc.article = saved_article if saved_article else None
  		api_doc.save()
