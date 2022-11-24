from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from itertools import chain
import random

from .models import Profile, Post, LikePost, Followers

# Create your views here.

# View for home page
# Use decorator to force user to login to see content
# Redirect user to login page if not logged in
@login_required(login_url='signin')
def index(request):
  user_object = User.objects.get(username = request.user.username) # Get user object
  user_profile = Profile.objects.get(user=user_object) # Use user object to get the profile object

  # Filter posts that come from the following accounts
  user_following_list = []
  feed = []

  user_followings = Followers.objects.filter(follower = request.user.username)

  for users in user_followings:
    user_following_list.append(users.user)

  for username in user_following_list:
    posts = Post.objects.filter(user = username)
    feed.append(posts)

  # Convert Query list to normal list
  feed_list = list(chain(*feed))

  # User suggestions
  all_users = User.objects.all()
  user_following_all = []

  for user in user_followings:
    user_list = User.objects.get(username = user.user)
    user_following_all.append(user_list)

  suggestion_list = [x for x in list(all_users) if x not in list(user_following_all)]
  current_user = User.objects.filter(username = request.user.username)
  final_suggetion_list = [x for x in list(suggestion_list) if x not in list(current_user)]
  random.shuffle(final_suggetion_list)

  username_profile = []
  username_profile_list = []

  for users in final_suggetion_list:
    username_profile.append(users.id)

  for ids in username_profile:
    profile_list = Profile.objects.filter(id_user = ids)
    username_profile_list.append(profile_list)

  suggestions_username_profile_list = list(chain(*username_profile_list))[:4] if len(list(chain(*username_profile_list))) > 4 else list(chain(*username_profile_list))

  return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list})

# View for sign up page
def signup(request):
  if request.method == 'POST': # If a form is submitted
    # Get all values from the form
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    password2 = request.POST['password2']

    if password == password2: # Check password
      if User.objects.filter(email=email).exists(): # Check email
        messages.info(request, "Email is already used")
        return redirect('signup')
      elif User.objects.filter(username=username).exists(): # Check username
        print(User.objects.filter(username=username))
        messages.info(request, "User already exists")
        return redirect('signup')
      else: # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Redirect user to settings for optional profile settings
        user_login = auth.authenticate(username = username, password = password)
        auth.login(request, user_login)

        # Create Profile object for user
        user_model = User.objects.get(username=username)
        new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
        new_profile.save()

        return redirect('settings')
    else:
      messages.info(request, "Passwords must match")
      return redirect('signup')
  else:
    return render(request, 'signup.html')

# View for sign in page
def signin(request):
  if request.method == 'POST': # If a form is submitted
    # Get all values from the form
    username = request.POST['username']
    password = request.POST['password']

    # Authenticate user
    user = auth.authenticate(username = username, password = password)

    if user is not None:
      auth.login(request, user)
      return redirect('/')
    else:
      messages.info(request, 'Invalid username and/or password')
      return render(request, 'signin.html')
  else: # On load
    return render(request, 'signin.html')

# Function for logout
# Use decorator to ensure user is logged in to be able to log out
# Redirect user to login page if not logged in
@login_required(login_url='signin')
def logout(request):
  auth.logout(request)
  return render(request, 'signin.html')

# View for settings page
@login_required(login_url='signin')
def settings(request):
  user_profile = Profile.objects.get(user = request.user)

  if request.method == 'POST':
    user_profile.profileimg = user_profile.profileimg if request.FILES.get('image') == None else request.FILES.get('image')
    user_profile.bio = request.POST['bio']
    user_profile.location = request.POST['location']
    user_profile.save()

    return redirect(reverse('index'))
  else: 
    return render(request, 'settings.html', {'user_profile': user_profile})

# Function for uploading posts
@login_required(login_url='signin')
def upload(request):
  if request.method == 'POST':
    user = request.user.username
    image = request.FILES.get('image_upload')
    caption = request.POST['caption']

    new_post = Post.objects.create(user=user, image=image, caption=caption)
    new_post.save()

  return redirect(reverse('index'))

# Function for like posts
@login_required(login_url='signin')
def like_post(request):
  username = request.user.username
  post_id = request.GET.get('post_id')
  post = Post.objects.get(id=post_id)

  # Get first and only Like object that matches criteria instead of get to avoid error if not exists
  has_liked = LikePost.objects.filter(post_id=post_id, username=username).first() 

  if has_liked == None:
    new_like = LikePost.objects.create(post_id=post_id, username=username)
    new_like.save()

    post.no_of_likes += 1
    post.save()
  else:
    has_liked.delete()

    post.no_of_likes -= 1
    post.save()

  return redirect(reverse('index'))

# View for profile page
def profile(request, pk):
  user_object = User.objects.get(username=pk)
  user_profile = Profile.objects.get(user=user_object)
  user_posts = Post.objects.filter(user=pk)

  follower = request.user.username
  user = pk

  context = {
    'user_object': user_object,
    'user_profile': user_profile,
    'user_posts': user_posts,
    'user_post_length': len(user_posts),
    'button_text': 'Unfollow' if Followers.objects.filter(follower=follower, user=user).first() else 'Follow',
    'user_followers': len(Followers.objects.filter(user=pk)),
    'user_following': len(Followers.objects.filter(follower=pk)),
  }

  return render(request, 'profile.html', context)

# Function for following user
@login_required(login_url='signin')
def follow(request):
  if request.method == 'POST':
    follower = request.POST['follower']
    user = request.POST['user']

    if Followers.objects.filter(follower=follower, user=user).first(): # Unfollow
      follower_to_delete = Followers.objects.get(follower=follower, user=user)
      follower_to_delete.delete()
    else: # Follow
      follower_to_create = Followers.objects.create(follower=follower, user=user)
      follower_to_create.save()

    return redirect('/profile/' + user)
  else:
    return redirect(reverse('index'))

# Function for user search
@login_required(login_url='signin')
def search(request):
  user_object = User.objects.get(username = request.user.username)
  user_profile = Profile.objects.get(user=user_object)

  if request.method == 'POST':
    username = request.POST['username']
    username_object = User.objects.filter(username__icontains = username) # Look up every match

    username_profile = []
    username_profile_list = []

    for users in username_object:
      username_profile.append(users.id)

    for ids in username_profile:
      profile_list = Profile.objects.filter(id_user = ids)
      username_profile_list.append(profile_list)

    username_profile_list = list(chain(*username_profile_list))

  return render(request, 'search.html', {'username_profile_list': username_profile_list, 'user_profile': user_profile})
