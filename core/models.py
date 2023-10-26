from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    objects = CustomUserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.username

class Genre(models.Model):
    title = models.CharField(max_length=100)

class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default='')
    genres = models.ManyToManyField(Genre)
    uuid = models.UUIDField()

    @property
    def serialize(self):
        dic = {}
        dic['title'] = self.title
        dic['description'] = self.description
        dic['uuid'] = str(self.uuid)
        dic['genres'] = ','.join([i.title for i in self.genres.all()])
        return dic

class Collection(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(default='')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    movies = models.ManyToManyField(Movie)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    @property
    def serialize_short(self):
        dic = {}
        dic['title'] = self.title
        dic['uuid'] = str(self.uuid)
        dic['description'] = self.description
        return dic

    @property
    def serialize(self):
        dic = {}
        dic['title'] = self.title
        dic['description'] = self.description
        dic['uuid'] = str(self.uuid)
        dic['movies'] = [i.serialize for i in self.movies.all()]
        return dic