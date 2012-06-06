from models import RboxFilePlug
from models import RboxSingleFilePlug
from models import RboxFile

def create_file(**kwargs):
    filepointer = kwargs['filepointer']
    if not 'filename' in kwargs:
        kwargs['filename'] = filepointer.name
    if not 'filesize' in kwargs:
        kwargs['filesize'] = filepointer.size
    rbox_file = RboxFile.objects.create(**kwargs)
    return rbox_file

