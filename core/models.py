from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

# Use current logged in user to link model
User = get_user_model()

# Create your models here.
# Extending default User model with foreign key pointing to user
class Profile(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  id_user = models.IntegerField()
  bio = models.TextField(blank=True)
  profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
  location = models.CharField(max_length=100, blank=True)

  def __str__(self):
    return self.user.username # Return username to display

# Model for post
class Post(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4)
  user = models.CharField(max_length=100)
  image = models.ImageField(upload_to='post_images')
  caption = models.TextField()
  created_at = models.DateTimeField(default=datetime.now)
  no_of_likes = models.IntegerField(default=0)

  def __str__(self):
    return self.user

# Model for post likes
class LikePost(models.Model):
  post_id = models.CharField(max_length=100)
  username = models.CharField(max_length=100)

  def __str__(self):
    return self.username

# Model for followers
class Followers(models.Model):
  follower = models.CharField(max_length=100)
  user = models.CharField(max_length=100)

  def __str__(self):
    return self.user
