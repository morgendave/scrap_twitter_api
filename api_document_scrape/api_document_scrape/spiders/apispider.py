import scrapy
import json


class TwitterBaseSpider(scrapy.Spider):
  '''
  Spider to grab all api docs and guides/overview
  '''
  name = "twitter_base_spider"
  start_urls = ['https://developer.twitter.com/en/docs']
  visited_urls = set(start_urls)

  def parse(self, response):
    side_navs = response.css('.side-nav__top-level').xpath('//ul[@class="side-nav__second-level"]/li')
    for side_nav in side_navs:
      doc_url = side_nav.select('a/@href').extract_first()
      next_url = response.urljoin(doc_url)
      self.visited_urls.add(next_url)
      yield scrapy.Request(next_url, callback=self.parse_page)

  def parse_page(self, response):
    main_content = response.xpath('//div[@class="main-content column column-9"]')
    api_path = main_content.xpath('//a[text()="API Reference"]')
    overview_path = main_content.xpath('//a[text()="Overview"]')
    guide_path = main_content.xpath('//a[text()="Guide"]')
    self.visited_urls.add(response.url)
    if not api_path and not overview_path and not guide_path or "overview" in response.url or "guides" in response.url:
      article = self.parse_article(main_content, response.url)
      yield article
    if api_path:
      api_reference_url = response.urljoin(api_path.select('@href').extract_first())
      self.visited_urls.add(api_reference_url)
      yield scrapy.Request(api_reference_url, callback=self.parse_apis)
    if overview_path:
      overview_path_url = response.urljoin(overview_path.select('@href').extract_first())
      if overview_path_url not in self.visited_urls:
        self.visited_urls.add(overview_path_url)
        yield scrapy.Request(overview_path_url, callback=self.parse_overviews)
    if guide_path:
      guide_path_url = response.urljoin(guide_path.select('@href').extract_first())
      if guide_path_url not in self.visited_urls:
        self.visited_urls.add(guide_path_url)
        yield scrapy.Request(guide_path_url, callback=self.parse_guides)

  def parse_overviews(self, response):
    overview_sections = response.xpath('//div[@class="tabs-nav__toc__list"]/li/a')
    for overview_section in overview_sections:
      overview_url = response.urljoin(overview_section.select('@href').extract_first())
      if overview_url not in self.visited_urls:
        self.visited_urls.add(overview_url)
        yield scrapy.Request(overview_url, callback=self.parse_page)

  def parse_guides(self, response):
    guide_sections = response.xpath('//div[@class="tabs-nav__toc__list"]/li/a')
    for guide_section in guide_sections:
      guide_url = response.urljoin(guide_section.select('@href').extract_first())
      if guide_url not in self.visited_urls:
        self.visited_urls.add(guide_url)
        yield scrapy.Request(guide_url, callback=self.parse_page)

  def parse_apis(self, response):
    api_sections = response.xpath('//div[@class="tabs-nav__toc__list"]/li/a')
    for api_section in api_sections:
      api_url = response.urljoin(api_section.select('@href').extract_first())
      if api_url not in self.visited_urls:
        self.visited_urls.add(api_url)
        yield scrapy.Request(api_url, callback=self.parse_api)

  def parse_article(self, main_content, response_url):
    url_patterns = response_url.split("/")
    item = {}
    item['topic'] = url_patterns[-3]
    if "overview" in response_url:
      item['data_type'] = "overview"
    elif "guides" in response_url:
      item['data_type'] = "guide"
    else:
      item['data_type'] = "article"
      item['topic'] = url_patterns[-1]

    article_path = main_content.xpath('//div[@class="c01-rich-text-editor"]')
    title_path = article_path.xpath('//h1//text()') or main_content.xpath('//h1//text()')
    title = self._clean_string(title_path.extract_first())
    raw_html_article =  self._clean_string(article_path.extract_first())
    item['content'] = raw_html_article
    item['title'] = title

    return item

  def parse_api(self, response):
    main_content = response.xpath('//div[@class="main-content column column-9"]')
    article_path = main_content.xpath('//div[@class="c01-rich-text-editor"]')
    item = {"data_type": "api_doc"}
    article_item = self.parse_article(main_content, response.url)
    article_item["data_type"] = "api_page"
    yield article_item

    title = article_item["title"]
    api_route_path = article_path.xpath('//span[@class="smaller-h1"]//text()') or \
        article_path.xpath('.//h1//text()')
    api_route_string = api_route_path.extract_first()
    if "POST" in api_route_string or "DELETE" in api_route_string or "PUT" in api_route_string \
        or "GET" in api_route_string:
      method, api_route = self._clean_string(api_route_string).split(" ")
      item['method'] = method
      item['api_route'] = api_route
      description = "".join(
          [self._clean_string(ex_str) for ex_str in article_path.xpath('//h1/../p//text()').extract()])
      item['description'] = description
      item['resource_url'] = self._clean_string(
          article_path.xpath('//div[@id="resource-url"]/p//text()').extract_first())
      self._parse_resource_table(article_path, item)
      self._parse_parameters_table(article_path, item)
      item["example_request"] = "".join(article_path.xpath('//div[@id="example-request"]/h2/..//text()').extract())
      item["example_response"] = "".join(article_path.xpath('//div[@id="example-response"]/h2/..//text()').extract())
      item["title"] = title

      yield item
    else:
      api_sections = article_path.xpath('//h1/../div')
      for api_section in api_sections:
        item = {"data_type": "api_doc"}
        api_route_path = api_section.xpath('.//h2//text()')
        api_route_string = api_route_path.extract_first()
        if "POST" in api_route_string or "DELETE" in api_route_string or "PUT" in api_route_string \
        or "GET" in api_route_string:
          method, api_route = self._clean_string(api_route_string).split(" ")
        else:
          method = "GET" #Default
          api_route = None
        item['method'] = method
        item['api_route'] = api_route
        description = "".join(
            [self._clean_string(ex_str) for ex_str in api_section.xpath('.//h2/../p//text()').extract()])
        item['description'] = description
        item['resource_url'] = self._clean_string(
            api_section.xpath('.//div[h3//text()="Resource URL"]/p//text()').extract_first())
        if not item['api_route']:
          resource_url_patterns = item['resource_url'].split("/")
          item["api_route"] = "/".join(resource_url_patterns[-2:])
        self._parse_resource_table(api_section, item)
        self._parse_parameters_table(api_section, item)
        item["example_request"] = "".join(api_section.xpath('//div[@id="example-request"]/h2/..//text()').extract())
        item["example_response"] = "".join(api_section.xpath('//div[@id="example-response"]/h2/..//text()').extract())
        item["title"] = title

        yield item


  def _parse_resource_table(self, article_path, item):
    resource_table_rows = article_path.xpath('//div[@id="resource-information"]//tr')
    for row in resource_table_rows:
      field, value = row.xpath('td//text()').extract()
      if field == "Response formats" or field == "Response Format":
        item['response_format'] = value
      elif field == "Requires authentication?" or field == "Requires Authentication":
        item['authentication_required'] = True if value.startswith("Yes") else False
      elif field == "Rate limited?" or field == "Rate Limited":
        item['rate_limited'] = True if value.startswith("Yes") else False
      elif field == "Requests / 15-min window (user auth)":
        item['limit_user'] = int(value.strip())
      elif field == "Requests / 15-min window (app auth)" or field == "Requests / 15-min window (per app)":
        item['limit_app'] = int(value.strip())       

    return

  def _parse_parameters_table(self, article_path, item):
    parameter_table_rows = article_path.xpath('//div[@id="parameters"]//tr')
    parameters = []
    if len(parameter_table_rows) > 1:
      for row in parameter_table_rows[1:]:
        parameter_dict = {}
        if len(parameter_table_rows[0].extract()) == 5:
          parameter_dict['name'], parameter_dict['required'], parameter_dict['description'], \
          parameter_dict['default_value'], parameter_dict['example'] = [
              self._clean_string(raw_string) for raw_string in row.xpath('td//text()').extract()
          ]
        elif len(parameter_table_rows[0].extract()) == 2:
          parameter_dict['name'], parameter_dict['description'] = [
              self._clean_string(raw_string) for raw_string in row.xpath('td//text()').extract()
          ]
        parameters.append(parameter_dict)

      item['parameters'] = json.dumps(parameters)

    return

  def _clean_string(self, raw_string):
    return raw_string.replace("\n", " ") \
                     .replace("\t", "") \
                     .replace("\r", "") \
                     .replace(u"\u2018", "'") \
                     .replace(u"\u2019", "'") \
                     .replace(u"\xa0", " ") \
                     .replace(u'\xb6', "")




