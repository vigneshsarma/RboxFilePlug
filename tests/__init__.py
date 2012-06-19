"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.utils import unittest
import os
from filemanager.field.models import *
from django.core.files import File
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

class RboxFilePlugTest(unittest.TestCase):
    
    def setUp(self):
        """ Setup the objects need for running the tests"""
        
        class Message(models.Model):
            docs = RboxFilePlug()        
        from django.core import management
        management.call_command('syncdb', verbosity=0, interactive=False)
        self.message_class = Message
        self.message = Message.objects.create()
        self.message_2 = Message.objects.create()
        self.filename =  os.path.dirname(__file__) + "/" + "text.txt"
                  


    def get_file_obj(self, filename):
        f = open(filename, 'r')
        return File(f)
        
    def test_create_rbox_file(self):
        """  Check the proper creation of rboxfile when only
             filepointer is passed
        """
        file_obj = self.get_file_obj(self.filename)
        rbox_file = self.message.docs.create(filepointer=file_obj)
        self.assertEqual(file_obj.size, rbox_file.filesize)
        self.assertEqual(file_obj.name, rbox_file.filename)
        file_obj = self.get_file_obj(self.filename)
        self.assertEqual(file_obj.read(), rbox_file.filepointer.read())

    def test_create_rbox_file_2(self):
        """ Check the proper creation of rboxfile when
            complete parameters are passed
        """
        file_obj = self.get_file_obj(self.filename)
        rbox_file = self.message.docs.create(filename=file_obj.name, filesize=file_obj.size, filepointer=file_obj)
        self.assertEqual(file_obj.size, rbox_file.filesize)
        self.assertEqual(file_obj.name, rbox_file.filename)
        file_obj = self.get_file_obj(self.filename)
        self.assertEqual(file_obj.read(), rbox_file.filepointer.read())
        

    def test_add_rbox_file(self):
        """ Check the addition of an existing
            rboxfile instance to a model instance
        """        
        file_obj=self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        rbox_file = self.message.docs.add(rb)
        self.assertEqual(rb.id, rbox_file.id)

    def test_delete_rbox_file_2(self):
        """ Check if deleting the files associated with multiple instances of file
            should reflect in all the instances 
        """
        file_obj=self.get_file_obj(self.filename)

        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        self.message.docs.add(rb)
        self.message_2.docs.add(rb)
        self.message.docs.all().delete()
        self.assertFalse(rb in self.message_2.docs.all())
        self.assertFalse(rb in self.message.docs.all())

    def test_remove_rbox_file(self):
        """ Check the removal of an rbox_file instance from a model instance"""        
        file_obj=self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        rbox_file = self.message.docs.add(rb)
        rbox_file = self.message_2.docs.add(rb)
        self.message.docs.remove(rbox_file=rbox_file)
        self.assertFalse(rbox_file in self.message.docs.all())
        self.assertTrue(rbox_file in self.message_2.docs.all())

    def test_get_rbox_file(self):
        """ Check if the same file is retrieved after creation"""        
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123,
                                     filelabel="afa", filepointer=file_obj)
        self.message.docs.add(rb)
        self.assertRaises(self.message.docs.FileDoesNotExist, self.message.docs.get, id=343)
        file_obj = self.get_file_obj(self.filename)
        self.assertEqual(file_obj.read(), self.message.docs.get(id=rb.id).filepointer.read())

    def test_delete_model_instance(self):
        """ Check that rboxfile associated with a model instance
            doesnt gets deleted while when the instance is deleted
        """
        self.new_message = self.message_class.objects.create()
        file_obj = self.get_file_obj(self.filename)
        rbox_file = RboxFile.objects.create(filename="lkdfjla", filesize=123,
                                     filelabel="afa", filepointer=file_obj)
        rbox_file_id = rbox_file.id
        new_rbox_file = self.new_message.docs.add(rbox_file=rbox_file)
        self.new_message.delete()
        self.assertTrue(new_rbox_file, RboxFile.objects.get(id=rbox_file_id))        
        

    def test_filter_rbox_file(self):
        """ Check the filter method to ensure that it doesnot
            return more objects than what are created
        """
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        self.message.docs.add(rb)
        self.assertEqual(1, self.message.docs.filter().count())        
        
        
class RboxSingleFilePlugTest(unittest.TestCase):
    def setUp(self):        
        class Candidate(models.Model):
            resume = RboxSingleFilePlug()
        from django.core import management
        management.call_command('syncdb', verbosity=0, interactive=False)
        self.candidate = Candidate.objects.create()
        self.filename = 'file_manager.txt'
        f = open(self.filename, 'w')
        f.write("this is the file")
        f.close()

    def get_file_obj(self, filename):
        f = open(filename, 'rb')
        file_obj = File(f)
        return file_obj
        

    def test_add_single_rbox_file(self):
        """ Check the proper addition of a rboxfile to instance"""
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        rbox_file = self.candidate.resume.add(rb)
        self.assertEqual(rbox_file.id, self.candidate.resume.get().id)

    def test_add_single_rbox_file_1(self):
        """Check adding more than 1 rboxfile instance throws error"""        
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        self.candidate.resume.add(rb)
        self.assertRaises(self.candidate.resume.MaximumNumberofObjectsAlreadyCreated,
                          self.candidate.resume.add, rb)

    def test_delete_single_rbox_file(self):
        """ Check the deletion of rbox file"""
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        self.candidate.resume.add(rb)
        self.candidate.resume.delete()
        self.assertTrue(rb not in RboxFile.objects.all())

    def test_get_single_rbox_file(self):
        """Check the retrieval of single rbox file"""
        file_obj = self.get_file_obj(self.filename)
        rb = RboxFile.objects.create(filename="lkdfjla", filesize=123, filelabel="afa", filepointer=file_obj)
        self.candidate.resume.add(rb)
        self.assertEqual(rb, self.candidate.resume.get())