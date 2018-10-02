from django.test import TestCase

from decimal import Decimal

from .models import Grocery

# Create your tests here.
class GroceryModelTests(TestCase):
    def test_division_by_zero(self):
        """
        calculate_unit_cost() called when cost_amount is assigned zero raises ValueError
        """
        a = Grocery(name='Egg', cost=Decimal('1.50'), cost_amount=Decimal(0), units='ct')
        caught = False
        try:
            a.calculate_unit_cost()
        except ValueError:
            caught = True
        self.assertTrue(caught)
    
    def test_calculate_unit_cost_count(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='ct'
        """
        a = Grocery(name='Egg', cost=Decimal('1.50'), cost_amount=Decimal(12), units='ct')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Egg').unit_cost, Decimal('0.125'))
    
    def test_calculate_unit_cost_pinch(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='p'
        """
        a = Grocery(name='Saffron', cost=Decimal(5), cost_amount=Decimal(2), units='p')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Saffron').unit_cost, Decimal(960))
        
    def test_calculate_unit_cost_tsp(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='tsp'
        """
        a = Grocery(name='Vanilla Extract', cost=Decimal('8.98'), cost_amount=Decimal(12), units='tsp')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Vanilla Extract').unit_cost, Decimal('35.92'))
        
    def test_calculate_unit_cost_tbsp(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='tbsp'
        """
        a = Grocery(name='Vanilla Extract', cost=Decimal('8.98'), cost_amount=Decimal(4), units='tbsp')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Vanilla Extract').unit_cost, Decimal('35.92'))
    
    def test_calculate_unit_cost_floz(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='floz'
        """
        a = Grocery(name='Vanilla Extract', cost=Decimal('8.98'), cost_amount=Decimal(2), units='floz')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Vanilla Extract').unit_cost, Decimal('35.92'))
    
    def test_calculate_unit_cost_cup(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='C'
        """
        a = Grocery(name='Sugar, Granulated', cost=Decimal('2.49'), cost_amount=Decimal(9), units='C')
        a.calculate_unit_cost()
        #cannot use a.unit_cost in assert (value is not pulled from database; instead
        #a.unit_cost returns Decimal('0.2766666666666666666666666667')
        self.assertEqual(Grocery.objects.get(name='Sugar, Granulated').unit_cost, Decimal('0.276667'))
        
    def test_calculate_unit_cost_pt(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='pt'
        """
        a = Grocery(name='Milk', cost=Decimal('1.12'), cost_amount=Decimal(1), units='pt')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Milk').unit_cost, Decimal('0.56'))
    
    def test_calculate_unit_cost_qt(self):
        """
        check unit_cost value after calculate_unit_cost() called for units='qt'
        """
        a = Grocery(name='Milk', cost=Decimal('1.12'), cost_amount=Decimal('0.5'), units='qt')
        a.calculate_unit_cost()
        self.assertEqual(Grocery.objects.get(name='Milk').unit_cost, Decimal('0.56'))