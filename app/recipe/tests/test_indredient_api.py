"""
Test  fro the ingredients API
"""
from django.contrib.auth import get_user_model
from django.core.serializers import serialize
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def create_user(email='test@example.com', password='myPassword1234'):
    """Create and return user."""
    return get_user_model().objects.create(email=email,password=password)

def detail_url(ingredient_id):
    """Fetch details of specific ingredient"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

class PublicIngredientAPITest(TestCase):
    """test unauthenticated api request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required in retrieving ingredient  """
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Test authenticated api request"""

    def setUp(self):
        self.user = create_user()
        self.client =APIClient()
        self.client.force_authenticate(self.user )

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Ingredient2'
        )

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer =  IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 2)

    def test_ingredient_limited_user(self):
        """Test ingredeint is limited to user"""
        user2 = create_user(email='user2@gmail.com', password='User2Password')
        Ingredient.objects.create(user=user2, name='Sugar')
        ingredeint = Ingredient.objects.create(user=self.user, name='Carrot')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredeint.name)
        self.assertEqual(res.data[0]['id'], ingredeint.id)

    def test_update_an_ingredient(self):
        """Update the details of an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Milk')

        payload = {
            'name':'Cheese'
        }
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name ,payload['name'])

    def test_delete_an_ingredeint(self):
        """Delete an Ingredient"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Cheese'
        )

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists ())