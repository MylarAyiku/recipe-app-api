"""
Tests for the User API endpoints.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe.serializers import RecipeSerializer,RecipeDetailSerializer

from core.models import Recipe, Tag, Ingredient

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

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tag"""
        payload = {
            'title': 'Light Soup',
            'time_minutes': 30,
            'price': Decimal('30.0'),
            'tags': [{'name': 'Spicy'}, {'name': 'Swallow'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user= self.user)
        self.assertEqual(recipies.count(), 1)
        recipe = recipies[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists =recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating s recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists= recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_up(self):
        """Test creating  tag when updarting a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
        self.assertEqual(recipe.tags.count(), 1)


    def test_clear_recipe_tags(self):
        """Test clearing a recipe Tag"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_recipe_with_new_ingredeint(self):
        """Test creating recipe with new ingredient"""

        payload = {
            'title': 'Banku',
            'time_minutes': 60,
            'price':Decimal('5.50'),
            'ingredients':[{'name': 'Fermented corn dough'},{'name': 'cassava dough'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_creating_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient """
        ingredient = Ingredient.objects.create(user=self.user, name='Lime')
        payload = {
            'title': 'Lime Juice',
            'time_minutes': 20,
            'price': '3.55',
            'ingredients': [{'name': 'Lime'},{'name': 'Vinegar'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe =recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = Ingredient.objects.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating ingredient when update a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Lime'},{'name': 'Vinegar'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(new_ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            exists = Ingredient.objects.filter(
                user=self.user,
                name =ingredient['name'],
            ).exists()
            self.assertTrue(exists)
        self.assertEqual(recipe.ingredients.count(), 2)

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user,name='Millet')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Milk')
        payload = {'ingredients': [{'name': "Milk"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 1)

    def test_clear_recipe_ingredient(self):
        """Test clearing a recipes ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name='Beans')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(ingredient, recipe.ingredients.all())












