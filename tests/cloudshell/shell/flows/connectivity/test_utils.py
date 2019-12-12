import sys
from unittest import TestCase

from cloudshell.shell.flows.connectivity.utils import JsonRequestDeserializer

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestJsonRequestDeserializer(TestCase):
    def setUp(self):
        self.tested_class = JsonRequestDeserializer

    def test_init(self):
        """Check that method will attach dictionary attributes to object."""
        some_key_value1 = mock.MagicMock()
        some_key_value2 = "some_str"
        some_nested_value1 = mock.MagicMock()
        some_nested_value2 = [100, "test_strt", mock.MagicMock()]
        test_data = {
            "some_key1": some_key_value1,
            "some_key2": some_key_value2,
            "some_key3": {
                "some_nested_key1": some_nested_value1,
                "some_nested_key2": some_nested_value2,
            },
        }
        req_deserializer = self.tested_class(test_data)

        self.assertIsInstance(req_deserializer, self.tested_class)
        self.assertEqual(req_deserializer.some_key1, some_key_value1)
        self.assertEqual(req_deserializer.some_key2, some_key_value2)
        self.assertIsInstance(req_deserializer.some_key3, self.tested_class)
        self.assertEqual(
            req_deserializer.some_key3.some_nested_key1, some_nested_value1
        )
        self.assertEqual(
            req_deserializer.some_key3.some_nested_key2, some_nested_value2
        )

    def test_is_primitive_returns_true(self):
        """Check that method will return True for all primitive types."""
        for primitive_type in (
            535,
            "test_string",
            False,
            12.45,
            u"test_unicode_stirng",
        ):
            is_primitive = self.tested_class._is_primitive(primitive_type)
            self.assertTrue(is_primitive)

    def test_is_primitive_returns_false(self):
        """Check that method will return False for non-primitive types."""
        TestClass = type("TestClass", (), {})

        for primitive_type in (TestClass(), [], {}):
            is_primitive = self.tested_class._is_primitive(primitive_type)
            self.assertFalse(is_primitive)

    def test_create_obj_by_type(self):
        """Check that method will return same object if it's not some primitive type."""
        test_obj = mock.MagicMock()
        returned_obj = self.tested_class._create_obj_by_type(test_obj)
        self.assertIs(returned_obj, test_obj)

    def test_create_obj_by_type_from_dict(self):
        """Check that method will return DeployDataHolder for the dict object."""
        test_obj = {}
        returned_obj = self.tested_class._create_obj_by_type(test_obj)
        self.assertIsInstance(returned_obj, self.tested_class)

    def test_create_obj_by_type_from_list(self):
        """Check that method will return list with converted instances."""
        test_obj = [mock.MagicMock(), "test_atrt", {}]
        returned_obj = self.tested_class._create_obj_by_type(test_obj)
        self.assertIsInstance(returned_obj, list)
        self.assertIs(returned_obj[0], test_obj[0])
        self.assertEqual(returned_obj[1], test_obj[1])
        self.assertIsInstance(returned_obj[2], self.tested_class)

    def test_create_obj_by_type_from_primitive_type(self):
        """Check that method will return same primitive for the primitive object."""
        test_obj = "test_primitive"
        returned_obj = self.tested_class._create_obj_by_type(test_obj)
        self.assertEqual(returned_obj, test_obj)
