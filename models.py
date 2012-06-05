from django.db import models, connection
from django.db.models.query import QuerySet, EmptyQuerySet, insert_query, RawQuerySet
from field import RboxFileField
from field import S3BotoStorage
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.fields.related import RelatedField, Field, ManyToManyRel
from django.conf import settings

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["recruiterbox.filemanager.models.RboxFilePlug"])
add_introspection_rules([], ["recruiterbox.filemanager.models.RboxSingleFilePlug"])

class FileManager(models.Manager):
    def __init__(self, model=None, core_filters=None, instance=None, symmetrical=None,
                 join_table=None, source_col_name=None, target_col_name=None, content_type=None,
                 content_type_field_name=None, object_id_field_name=None, file_field_identifier=None, max_count=None):

        super(FileManager, self).__init__()
        self.core_filters = core_filters or {}
        self.model = model
        self.content_type = content_type
        self.symmetrical = symmetrical
        self.instance = instance
        self.join_table = join_table
        self.join_table = model._meta.db_table
        self.source_col_name = source_col_name
        self.target_col_name = target_col_name
        self.content_type_field_name = content_type_field_name
        self.object_id_field_name = object_id_field_name
        self.pk_val = self.instance._get_pk_val()
        self.file_field_identifier = file_field_identifier
        self.max_count = max_count



        
    def get_query_set(self):
        """Returns a new QuerySet object.  Subclasses can override this method
        to easily customize the behavior of the Manager.
        """
        return QuerySet(RboxFile).filter(rboxfileconnector__content_type=self.content_type,
                                         rboxfileconnector__object_id=self.instance.id,
                                         rboxfileconnector__file_field_identifier=self.file_field_identifier)

    def all(self):                
        if hasattr(self, 'ondelete'):            
            if self.ondelete:
                return self.none()
        return self.get_query_set()

    def create(self, **kwargs):
        if self.max_count and (self.all().count() >= self.max_count):
            raise ValueError("Maximum number of objects already created")
        filepointer = kwargs['filepointer']
        if not 'filename' in kwargs:
            kwargs['filename'] = filepointer.name
        if not 'filesize' in kwargs:
            kwargs['filesize'] = filepointer.size
        rbox_file = self.get_query_set().create(**kwargs)
        rboxfile_connector = RboxFileConnector(rbox_file=rbox_file, content_type=self.content_type,
                                               object_id=self.instance.id, file_field_identifier=self.file_field_identifier)
        rboxfile_connector.save()
        return rbox_file
        
    def add(self, rbox_file):
        if self.max_count and (self.all().count() >= self.max_count):
            raise ValueError("Maximum number of objects already created")

        rboxfile_connector = RboxFileConnector(rbox_file=rbox_file, content_type=self.content_type,
                                               object_id=self.instance.id, file_field_identifier=self.file_field_identifier)
        rboxfile_connector.save()
        return rbox_file

    def remove(self, rbox_file):
        """ Remove doesnot deletes the file only deletes the connector model instance
            rather use delete method for deleting files
        """
        rboxfile_connector = RboxFileConnector.objects.get(rbox_file=rbox_file, content_type=self.content_type,
                                                           object_id=self.instance.id, file_field_identifier=self.file_field_identifier)
        rboxfile_connector.delete()
        return

    def get(self, **kwargs):
        if self.max_count == 1:
            try:
                return self.all()[0]
            except IndexError:
                return None
        else:
            return super(FileManager,self).get(**kwargs)

    def delete(self, **kwargs):
        if self.max_count == 1:
            return self.all().delete()
        else:
            raise AttributeError("'FileManager' object has no attribute 'delete'")
            

            


class FileManagerDescriptor(object):
    """
    This class provides the functionality that makes the related-object
    managers available as attributes on a model class, for fields that have
    multiple "remote" values and have a GenericRelation defined in their model
    (rather than having another model pointed *at* them). In the example
    "article.publications", the publications attribute is a
    ReverseGenericRelatedObjectsDescriptor instance.
    """
    def __init__(self, field, file_field_identifier, max_count):
        self.field = field
        self.file_field_identifier = file_field_identifier
        self.max_count = max_count

    def __get_filemanager(self):
        return FileManager

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        # This import is done here to avoid circular import importing this module
        from django.contrib.contenttypes.models import ContentType

        # Dynamically create a class that subclasses the related model's
        # default manager.
        rel_model = self.field.rel.to
        RelatedManager = self.__get_filemanager()

        qn = connection.ops.quote_name

        manager = RelatedManager(
            model = rel_model,
            instance = instance,
            symmetrical = (self.field.rel.symmetrical and instance.__class__ == rel_model),
            join_table = qn(self.field.m2m_db_table()),
            source_col_name = qn(self.field.m2m_column_name()),
            target_col_name = qn(self.field.m2m_reverse_name()),
            content_type = ContentType.objects.db_manager(instance._state.db).get_for_model(instance),
            content_type_field_name = self.field.content_type_field_name,
            object_id_field_name = self.field.object_id_field_name,
            file_field_identifier = self.file_field_identifier,
            max_count = self.max_count
        )

        return manager

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")

        manager = self.__get__(instance)
        manager.clear()
        for obj in value:
            manager.add(obj)

class CustomFileRelation(generic.GenericRelation):    
    def __get_filemanager_descriptor(self):
        return FileManagerDescriptor

    def contribute_to_class(self, cls, name):
        super(CustomFileRelation, self).contribute_to_class(cls, name)

        # Save a reference to which model this class is on for future use
        self.model = cls
        if not self.file_field_identifier:
            self.file_field_identifier = self.name
        setattr(cls, self.name, self.__get_filemanager_descriptor()(self, self.file_field_identifier, self.max_count))

def get_unique_key():
    return uuid.uuid4().hex
        
class RboxFile(models.Model):
    unique_key = models.CharField('Unique Key', max_length=100, default=get_unique_key, unique=True, db_index=True)
    filename = models.CharField('File Name', max_length=100)
    filelabel = models.CharField('File Type', max_length=50, blank=True, null=True)
    filesize = models.PositiveIntegerField('File Size')
    filepointer = RboxFileField('File Pointer', max_length=200, upload_to='filemanager.rboxfile') #, backup_storage=S3BotoStorage())

class RboxFileConnector(models.Model):
    rbox_file = models.ForeignKey(RboxFile)
    content_type = models.ForeignKey(ContentType)
    file_field_identifier = models.CharField(max_length=100, default="attachments", db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
   

class GenericFilePlug(object):
    def __init__(self,related_name=None, file_field_identifier=None, max_count=None, *args, **kwargs):
        if not related_name:
            related_name = uuid.uuid4().hex
        kwargs['related_name'] = related_name
        kwargs['to'] = RboxFileConnector
        super(GenericFilePlug,self).__init__(**kwargs)
        self.file_field_identifier = file_field_identifier
        self.max_count = max_count

    def value_from_object(self, obj):
        import django
        if django.__dict__['VERSION'] == (1, 2, 3, 'final', 0):
            manager_obj = getattr(obj, self.attname)
            manager_obj.ondelete = True
            return manager_obj
        else:
            return super(GenericFilePlug,self).value_from_object(obj)

class GenericSingleFilePlug(object):
    def __init__(self, *args, **kwargs):
        kwargs['max_count'] = 1
        super(GenericSingleFilePlug,self).__init__(*args, **kwargs)


class RboxFilePlug(GenericFilePlug, CustomFileRelation):
    pass

class RboxSingleFilePlug(GenericSingleFilePlug, RboxFilePlug):
    pass
