from django.test import TestCase,Client
from django.urls import reverse
from core.models import *
import json

# Create your tests here.
class RegistrationTest(TestCase):
    def test_register_api(self):
        c = Client()
        data = {"username": "yogesh", "password": "yogesh"}
        payload = json.dumps(data)
        response = c.post(reverse("register"), data=payload,
                         content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json())

class MoviesTest(TestCase):
    def setUp(self):
        c = Client()
        data = {"username": "yogesh", "password": "yogesh"}
        payload = json.dumps(data)
        response = c.post(reverse("register"), data=payload,
                          content_type='application/json')
        self.access_token = response.json()['access_token']

    def test_movies_api(self):
        c = Client()
        headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % (self.access_token)}
        response = c.get(reverse('movies'),**headers)
        self.assertEqual(response.status_code, 200)




class CollectionTest(TestCase):
    def setUp(self):
        c = Client()
        data = {"username": "yogesh", "password": "yogesh"}
        payload = json.dumps(data)
        response = c.post(reverse("register"), data=payload,
                          content_type='application/json')
        self.access_token = response.json()['access_token']

    def test_collection_crud_functionality(self):
        #getting movies list for adding to collection list
        c = Client()
        headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % (self.access_token)}
        response = c.get(reverse('movies'), **headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        movie_data = data['results']

        #creating collection
        headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % (self.access_token)}
        data = {
            "title":"Test Collection",
            "description":"Test Description",
            "movies":movie_data[0:4]
        }
        payload = json.dumps(data)
        response = c.post(reverse('collection_list'),data=payload,content_type='application/json', **headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('collection_uuid', response.json())

        #get collection
        response = c.get(reverse('collection_list'), **headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        collections = response_data['data']['collections']
        self.assertTrue(len(collections)>0, '')

        collection_uuid = collections[0]["uuid"]
        #get collection detail
        response = c.get(reverse('collection_detail',args=(collection_uuid,)), **headers)
        self.assertEqual(response.status_code, 200)

        #update collection
        data = {
            "title": "Edited Test Collection",
            "description": "Edited Test Description",
            "movies": movie_data[3:8]
        }
        payload = json.dumps(data)
        response = c.put(reverse('collection_detail', args=(collection_uuid,)),
                         data=payload,content_type='application/json', **headers)
        self.assertEqual(response.status_code, 200)


        #delete collection
        response = c.delete(reverse('collection_detail', args=(collection_uuid,)), **headers)
        self.assertEqual(response.status_code, 204)

        #recheck collection deleted or not
        response = c.get(reverse('collection_detail', args=(collection_uuid,)), **headers)
        self.assertEqual(response.status_code, 404)








