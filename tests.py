"""
A variety of tests to cover the majority of the functionality
in mogo. I'd really like to get this to 100% code coverage...

NOTES:
I use safe=True for most of the save operations because sometimes
it was too quick and a find or search operation performed immediately
afterwards would not return the new object.

You need to have mongod running on the local machine for this
to run. Will probably add config options later for testing
remote machines.

If for some reason you have a database named "_mogotest", you will
probably want to change DBNAME. :)
"""

import unittest
from mogo import Model, connect, Field, ReferenceField
from mogo.connection import Connection
import pymongo
import pymongo.objectid
import time
import hashlib
import sys

DBNAME = '_mogotest'
DELETE = True

class Foo(Model):
    bar = Field()
    ref = Field()
    
class Company(Model):
    name = Field()
    
    @property
    def people(self):
        return Person.search(company=self)
    
class Person(Model):
    company = ReferenceField(Company)
    name = Field()
    email = Field()
    
class MogoTests(unittest.TestCase):
        
    def test_connect(self):
        conn = connect(DBNAME)
        self.assertTrue(isinstance(conn, pymongo.Connection))
        connection = Connection.instance()
        self.assertTrue(Connection.instance()._database == DBNAME)
        conn.disconnect()
        
    def test_model(self):
        foo = Foo(bar='cheese')
        self.assertTrue(foo.bar == 'cheese')
        foo.bar = 'model'
        self.assertTrue(foo.bar == 'model')
        
    def test_create_delete(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = 'create_delete'
        idval = foo.save(safe=True)
        try:
            self.assertTrue(type(idval) is pymongo.objectid.ObjectId)
            self.assertTrue(foo.id == idval)
        finally:
            foo.delete()
            conn.disconnect()
        
    def test_find_one(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = 'find_one'
        idval = foo.save(safe=True)
        foo2 = Foo.find_one({'bar':'find_one'})
        try:
            self.assertTrue(foo2._get_id() == idval)
            self.assertTrue(foo2 == foo)
        finally:
            foo.delete()
            conn.disconnect()
            
    def test_count(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = 'count'
        idval = foo.save(safe=True)
        count = Foo.count()
        try:
            self.assertTrue(count == 1)
        finally:
            foo.delete()
            conn.disconnect()
        
    def test_find(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = 'find'
        foo.save(safe=True)
        foo2 = Foo()
        foo2.bar = 'find'
        foo2.save()
        result = Foo.find({'bar':'find'})
        self.assertTrue(result.count() == 2)
        f = result[0] # should be first one
        try:
            self.assertTrue(type(f) is Foo)
            self.assertTrue(f.bar == 'find')
            for f in result:
                self.assertTrue(type(f) is Foo)
        finally:
            foo.delete()
            foo2.delete()
            conn.disconnect()
        
    def test_update(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = 'update'
        foo.save(safe=True)
        result = Foo.find_one({'bar':'update'})
        result.bar = "new update"
        result.save(safe=True)
        result2 = Foo.find_one({'bar': 'new update'})
        try:
            self.assertTrue(result == result2)
            self.assertTrue(result2.bar == 'new update')
            self.assertTrue(result.bar == 'new update')
        finally:
            foo.delete()
            conn.disconnect()
        
    def test_ref(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = "ref"
        foo.save(safe=True)
        #result = Foo.find_one({"bar": "ref"})
        new = Foo.find_one({"bar": "ref"})
        #new.bar = "Testing"
        new.ref = foo
        new.save(safe=True)
        result2 = Foo.find_one({"bar": "ref"})
        try:
            self.assertTrue(result2.ref == foo)
        finally:
            result2.delete()
            conn.disconnect()
        
    def test_search(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = "search"
        foo.save(safe=True)
        result = foo.search(bar="search")
        try:
            self.assertTrue(result.count() == 1)
            self.assertTrue(result.first() == foo)
        finally:
            foo.delete()
            conn.disconnect()
    
    def test_bad_remove(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = "bad_remove"
        foo.save(safe=True)
        try:
            self.assertRaises(TypeError, getattr, args=(foo, 'remove'))
        finally:
            foo.delete()
            conn.disconnect()
            
    def test_bad_drop(self):
        conn = connect(DBNAME)
        foo = Foo()
        foo.bar = "bad_drop"
        foo.save(safe=True)
        try:
            self.assertRaises(TypeError, getattr, args=(foo, "drop"))
        finally:
            foo.delete()
            conn.disconnect()
        
    def test_search_ref(self):
        conn = connect(DBNAME)
        company = Company(name="Foo, Inc.")
        company.save()
        user = Person(name="Test", email="whatever@whatever.com")
        user.company = company
        user.save(safe=True)
        try:
            self.assertTrue(company.people.count() == 1)
        finally:
            user.delete()
            company.delete()
            conn.disconnect()
    
    def tearDown(self):
        conn = pymongo.Connection()
        db = conn[DBNAME]
        if DELETE:
            for coll in [Foo, Person, Company]:
                coll.remove()
                coll.drop()
        
if __name__ == '__main__':
    if '--no-drop' in sys.argv:
        DELETE = False
        sys.argv.remove('--no-drop')
    unittest.main()
