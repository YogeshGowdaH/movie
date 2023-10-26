from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
import json
import jwt
import datetime
import requests
from requests.auth import HTTPBasicAuth
from django.db.models import Count
from django.conf import settings
from core.models import *




@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username',None)
        password = data.get('password',None)
        if username in (None,''):
            return JsonResponse({"error": "bad request"}, status=400)
        if password in (None,''):
            return JsonResponse({"error": "bad request"}, status=400)
        if UserProfile.objects.filter(username=username).exists():
            user = UserProfile.objects.get(username=username)
            if not check_password(password, user.password):
                return JsonResponse({"error": "Incorrect password."}, status=400)
        else:
            user = UserProfile.objects.create_user(username=username, password=password)

        payload = {
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        jwt_token = jwt.encode(payload,settings.JWT_SECRET, algorithm='HS256')
        return JsonResponse({"access_token": jwt_token})
    else:
        return JsonResponse({"error": "method not allowed"},status=405)


def jwt_token_required(view_func):
    def inner(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return JsonResponse({'message': 'Unauthorized'}, status=401)
        token = token.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            user_id = payload['user_id']
            try:
                user = UserProfile.objects.get(id=user_id)
                request.user = user
            except UserProfile.DoesNotExist:
                return JsonResponse({'message': 'Invalid token'}, status=401)
            return view_func(request, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'message': 'Token expired'}, status=401)
        except jwt.DecodeError:
            return JsonResponse({'message': 'Invalid token'}, status=401)
        except:
            return JsonResponse({'message': 'Invalid token'}, status=401)
    return inner


@jwt_token_required
def movies_list(request):
    if request.method == 'GET':
        page = request.GET.get("page", 1)
        url = "https://demo.credy.in/api/v1/maya/movies/"
        params = {
            "page": page,
        }
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, params=params, timeout=5,verify=False,
                                        auth=HTTPBasicAuth(settings.API_USER_NAME, settings.API_PASSWORD))
                if response.status_code == 200:
                    data = response.json()
                    if data['next']:
                        data['next'] = "/movies/?page=%s" % (int(page)+1,)
                    if data['previous']:
                        data['previous'] = "/movies/?page=%s" % (int(page)-1,)
                    return JsonResponse(data)
                else:
                    retries += 1
            except:
                retries += 1
        return JsonResponse({"error": "Failed to retrieve movie data"},
                            status=500)
    else:
        return JsonResponse({"error": "method not allowed"}, status=405)

@csrf_exempt
@jwt_token_required
def collections(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)

        title = data.get('title', '')
        description = data.get('description', '')
        movies = data.get('movies', [])

        if title in (None,''):
            return JsonResponse({"error": "bad request"}, status=400)

        new_collection = Collection.objects.create(
            title=title,
            description=description,
            user=user
        )

        for movie_data in movies:
            title = movie_data.get('title', '')
            description = movie_data.get('description', '')
            genres = movie_data.get('genres', '')
            uuid = movie_data.get('uuid', '')

            if title in (None,''):
                continue

            movie,_ = Movie.objects.get_or_create(
                title=title,
                description=description,
                uuid=uuid
            )
            genres_list = genres.split(",")
            for genre in genres_list:
                if genre not in ('',None):
                    genre_obj,_ = Genre.objects.get_or_create(title=genre)
                    movie.genres.add(genre_obj)
            new_collection.movies.add(movie)
        return JsonResponse({"collection_uuid": str(new_collection.uuid)}, status=201)
    elif request.method == 'GET':
        user = request.user
        collections = Collection.objects.filter(user=user)
        top_genres = Genre.objects.filter(movie__collection__user=user).annotate(
            genre_count=Count('movie')
        ).order_by('-genre_count')[:3]
        favourite_genres = ",".join([i.title for i in top_genres])
        data = {
            "is_success":True,
            "data":{
                "collections" : [i.serialize_short for i in collections]
            },
            "favourite_genres":favourite_genres
        }
        return JsonResponse(data, status=200)
    else:
        return JsonResponse({"error": "method not allowed"}, status=405)

@csrf_exempt
@jwt_token_required
def collection_detail(request, collection_uuid):
    user = request.user
    if request.method == 'PUT':
        try:
            collection = Collection.objects.get(uuid=collection_uuid)
            if user != collection.user:
                return JsonResponse({'message': 'Unauthorized'}, status=401)
            data = json.loads(request.body)
            title = data.get('title', None)
            description = data.get('description', None)
            movies = data.get('movies', None)
            if title not in ('',None):
                collection.title = title
            if description not in ('',None):
                collection.description = description
            if movies not in ('',None):
                collection.movies.clear()
                for movie in movies:
                    title = movie.get('title', '')
                    description = movie.get('description', '')
                    genres = movie.get('genres', '')
                    uuid = movie.get('uuid', '')
                    movie, created = Movie.objects.get_or_create(
                        title=title,
                        description=description,
                        uuid=uuid
                    )
                    if created:
                        genres_list = genres.split(",")
                        for genre in genres_list:
                            if genre not in ('', None):
                                genre_obj, _ = Genre.objects.get_or_create(title=genre)
                                movie.genres.add(genre_obj)
                    collection.movies.add(movie)
            collection.save()
            return JsonResponse({"msg": "collection updated successfully"}, status=200)
        except:
            return JsonResponse({"error": "collection does exists"}, status=404)
    elif request.method == 'GET':
        try:
            collection = Collection.objects.get(uuid=collection_uuid)
            if user != collection.user:
                return JsonResponse({'message': 'Unauthorized'}, status=401)
            data = collection.serialize
            return JsonResponse(data, status=200)
        except:
            return JsonResponse({"error": "collection does exists"}, status=404)
    elif request.method == 'DELETE':
        try:
            collection = Collection.objects.get(uuid=collection_uuid)
            if user != collection.user:
                return JsonResponse({'message': 'Unauthorized'}, status=401)
            collection.delete()
            return JsonResponse({'msg':"deleted"},status=204)
        except:
            return JsonResponse({"error": "collection does not exists"}, status=404)
    else:
        return JsonResponse({"error": "method not allowed"}, status=405)


from requestmiddleware import lock,RequestMiddleware

def get_request_count(request):
    return JsonResponse({'requests': RequestMiddleware.request_count})

def reset_request_count(request):
    with lock:
        RequestMiddleware.request_count = 0
    return JsonResponse({'message': 'Request count reset successfully'})







