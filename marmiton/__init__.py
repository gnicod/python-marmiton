# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import urllib.parse
import urllib.request

import re
import json


class RecipeNotFound(Exception):
	pass


class Marmiton(object):

	@staticmethod
	def search(query_dict):
		"""
		Search recipes parsing the returned html data.
		Options:
		'aqt': string of keywords separated by a white space  (query search)
		Optional options :
		'dt': "entree" | "platprincipal" | "accompagnement" | "amusegueule" | "sauce"  (plate type)
		'exp': 1 | 2 | 3  (plate expense 1: cheap, 3: expensive)
		'dif': 1 | 2 | 3 | 4  (recipe difficultie 1: easy, 4: advanced)
		'veg': 0 | 1  (vegetarien only: 1)
		'rct': 0 | 1  (without cook: 1)
		'sort': "markdesc" (rate) | "popularitydesc" (popularity) | "" (empty for relevance)
		"""
		base_url = "http://www.marmiton.org/recettes/recherche.aspx?"
		query_url = urllib.parse.urlencode(query_dict)

		url = base_url + query_url

		html_content = urllib.request.urlopen(url).read()
		soup = BeautifulSoup(html_content, 'html.parser')

		search_data = []

		articles = soup.find_all("a", href=re.compile("^\/recettes\/recette_"))

		iterarticles = iter(articles)
		for article in iterarticles:
			data = {}
			try:
				data["name"] = article.find("h4").get_text().strip(' \t\n\r')
				data["description"] = ""
				data["url"] = article['href']
				data["rate"] = article.find("span").text.strip(' \t\n\r')
				try:
					data["image"] = article.find('img')['src']
				except Exception as e1:
					pass
			except Exception as e2:
				pass
			if data:
				search_data.append(data)

		return search_data

	@staticmethod
	def __clean_text(element):
		return element.text.replace("\n", "").strip()

	@staticmethod
	def get(uri):
		"""
		'url' from 'search' method.
		 ex. "/recettes/recette_wraps-de-poulet-et-sauce-au-curry_337319.aspx"
		"""
		data = {}

		base_url = "https://www.marmiton.org"
		url = base_url + ("" if uri.startswith("/") else "/") + uri

		try:
			html_content = urllib.request.urlopen(url).read()
		except urllib.error.HTTPError as e:
			raise RecipeNotFound if e.code == 404 else e

		soup = BeautifulSoup(html_content, 'html.parser')

		main_data = soup.find("div", {"class": "m_content_recette_main"})
		d = json.loads(soup.find('script', type='application/json').string)
		recipe = d['props']['pageProps']['recipeData']['recipe']
		
		tmp_ingredients = recipe['ingredientGroups'][0]['items']
		keys = ['name', 'unitName', 'ingredientQuantity']
		ingredients = []
		for ing in tmp_ingredients:
			ingredient = { k: ing[k] for k in keys }
			ingredients.append(ingredient)

		tmp_steps = recipe['steps']
		steps = []
		for step in tmp_steps:
			steps.append(step['text'])

		tags = []
		for t in recipe['categories']:
			tags.append(t['name'])

		images = []
		for t in recipe['picturesPreview']:
			images.append(t['pictureUrls']['main'])

		data.update({
			"ingredients": ingredients,
			"steps": steps,
			"name": recipe['title'],
			"tags": tags,
			"images": images,
			"cook_time": recipe['cookingTime'],
			"preparation_time": recipe['preparationTime']
		})

		return data

