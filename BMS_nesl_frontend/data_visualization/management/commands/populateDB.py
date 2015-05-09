from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from data_visualization.models import Path_UUID, Menu_Tree
from optparse import make_option
import urllib, urllib2, json

def get_resp_from_server(url):
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req).read()
    return json.loads(resp)

def find_data_type_by_unit(unit):
    return {
        "Active/Inactive": 1,
        "Open/Close": 1,
        "Present/Absent" : 1
    }.get(unit, 0)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--update',
            action='store_true',
            dest='update',
            default=False,
            help='Update database instead of populate it'),
        )

    args = '<addr:port>'
    help = 'Populate Database with path, UUID and data type information from a sMAP server'

    def handle(self, *args, **options):
        addr = "localhost:8079"
        if len(args) > 0:
            self.stdout.write('Use default address and port -- localhost:8079')
            addr = args[0]

        if options['update']:
            print("Updating Path, UUID, data_type information in django database")
        else:
            print("Populating Path, UUID, data_type information in django database")

        url = "http://"+addr+"/api/query/uuid"
        content = urllib2.urlopen(url).read()
        
        #convert content into lists
        content = content[1:-1]
        content = [uuid.strip().replace('"', '') for uuid in content.split(',')]
        
        #construct menu tree
        menu_tree = {}

        #find corrosponding UUID and save it to database
        url2 = "http://"+addr+"/api/query"
        for uuid in content:
            if options['update']:
                body = "select Path where uuid = '"+uuid+"'"
                req = urllib2.Request(url2, body)
                resp = urllib2.urlopen(req).read()
                resp = json.loads(resp)
                path = str(resp[0]['Path'])
                url = "http://128.97.93.240:8079/api/query/uuid/"+str(uuid)+ "/Properties__UnitofMeasure"
                resp = get_resp_from_server(url)
                unit = resp[0]
                data_type = find_data_type_by_unit(unit)
                print data_type
                p_u = Path_UUID(path=path, uuid=uuid, data_type=data_type)
                p_u.save()
                if path.startswith("/B"): #Path starts with "/NESL" are deprecated 
                    single_path = [tag.strip() for tag in path[1:].split('/')]
                    menu_tree_iterator = menu_tree #dicts are pass by reference
                    for tag in single_path:
                        if tag not in menu_tree_iterator:
                            menu_tree_iterator[tag]= {}
                            menu_tree_iterator = menu_tree_iterator[tag]
                        else:
                            menu_tree_iterator = menu_tree_iterator[tag]
            else:                
                try:
                    Path_UUID.objects.get(uuid=uuid)
                except ObjectDoesNotExist:
                    body = "select Path where uuid = '"+uuid+"'"
                    req = urllib2.Request(url2, body)
                    resp = urllib2.urlopen(req).read()
                    resp = json.loads(resp)
                    path = str(resp[0]['Path'])
                    url = "http://128.97.93.240:8079/api/query/uuid/"+str(uuid)+ "/Properties__UnitofMeasure"
                    resp = get_resp_from_server(url)
                    unit = resp[0]
                    data_type = find_data_type_by_unit(unit)
                    p_u = Path_UUID(path=path, uuid=uuid, data_type=data_type)
                    p_u.save()
                    if path.startswith("/B"): #Path starts with "/NESL" are deprecated 
                        single_path = [tag.strip() for tag in path[1:].split('/')]
                        menu_tree_iterator = menu_tree #dicts are pass by reference
                        for tag in single_path:
                            if tag not in menu_tree_iterator:
                                menu_tree_iterator[tag]= {}
                                menu_tree_iterator = menu_tree_iterator[tag]
                            else:
                                menu_tree_iterator = menu_tree_iterator[tag]

        menu_tree = json.dumps(menu_tree)
        m_t = Menu_Tree(tree_id=1, tree=menu_tree)
        m_t.save()
