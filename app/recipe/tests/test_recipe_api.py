"""
Tests for the User API endpoints.
"""
from decimal import Decimal
from pydoc import describe

from django.template.defaultfilters import title
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe.serializers import RecipeSerializer,RecipeDetailSerializer

from core.models import Recipe


CREATE_USER_URL = reverse('user:create')
RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse('recipe:recipe-detail',args=[recipe_id])


def create_user(**params):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(**params)

def create_recipe(user, **params):
    """Helper function to create a recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)


    return Recipe.objects.create(user=user, **defaults)

def create_user(**params):
    """ create and return users"""
    return get_user_model().objects.create(**params)



class PublicRecipeApiTests(TestCase):
    """Test the recipe API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the recipe API (private)"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='test@example.com',password='test123password')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        #recipe 1
        create_recipe(user=self.user)
        # recipe 2
        create_recipe(user=self.user, title='Another recipe')

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        other_user = create_user(email='other@example.com',password='test123password')
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_details(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)


    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }

        res = self.client.post(RECIPES_URL,payload) # /api/recipes/recipe/

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe """
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link=original_link
        )

        payload = {'title':'New Recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title,payload['title'])
        self.assertEqual(recipe.link,original_link)
        self.assertEqual(recipe.user,self.user)


    def  test_full_update(self):
        """Test Full update of recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample Description',
        )

        payload = {
            'title': 'New Recipe Title',
            'link': 'https://example.com/new_recipe.pdf',
            'description':'New Description',
            'time_minutes':10,
            'price':Decimal('2.50'),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
        self.assertEqual(recipe.user,self.user)

    def test_update_user_return_error(self):
        """Test changing the recipy user results int an error"""
        new_user = create_user(email='test2@example.com',password='test1234')
        recipe = create_recipe(user=self.user)

        payload = {'user':new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url,payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user,self.user)


    def test_delete_recipe(self):
        """Test deleting a recipe successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
        self.assertTrue(get_user_model().objects.filter(id=self.user.id).exists())



    def test_recipe_other_recipe_error(self):
        """Test  tryiong to delete another users recipe error."""
        new_user = create_user(email='users2@example.com',password='myPass1234')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code,status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


