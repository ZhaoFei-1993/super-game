from reversion.models import Revision, Version
from .models import Admin_Operation
"""
保存用户操作记录
"""
def save_operation(request):
    revision = [x['id'] for x in Revision.objects.all().values('id')]
    admin_operation = [x['revision'] for x in Admin_Operation.objects.all().values('revision')]
    new_set = list(set(revision)-set(admin_operation))
    version_list = []
    versions = Version.objects.filter(revision_id__in=new_set)
    for version in versions:
        if version not in version_list:
            vs = Version.objects.get_for_object(version.object)
            if len(vs)==1:
                pre_v = mod_v = vs[0]
                save_sql(pre_v, mod_v, request, vs[0].revision)
                version_list.append(version)
            else:
                for index,x in enumerate(vs):
                    if x in versions:
                        if x.revision.comment in ['PATCH', 'PUT', 'DELETE']:
                            if index == len(vs)-1:
                                pre_v=mod_v=x
                            else:
                                pre_v = vs[index+1]
                                mod_v = x
                            save_sql(pre_v, mod_v, request, x.revision)
                            version_list.append(x)
                        else:
                            save_sql(x, x, request, x.revision)
                            version_list.append(x)



        # if x.comment in ['PATCH', 'PUT', 'DELETE']:
        #     version= Version.objects.get(revision_id=x.id)
        #     model = version.object
        #     versions = Version.objects.get_for_object(obj=model)
        #     if len(versions) == 1:
        #         pre_v = mod_v = versions[0]
        #         save_sql(pre_v, mod_v,request,versions[0].revision)
        #         new_add.remove(version[0].revision)
        #     else:
        #         for index, item in enumerate(versions):
        #             if item.id not in version_list and item.revision_id in new_add:
        #                 if index==(len(versions)-1):
        #                     pre_v=mod_v=item
        #                 else:
        #                     pre_v=versions[index+1]
        #                     mod_v=item
        #                 save_sql(pre_v, mod_v, request, item.revision)
        #                 version_list.append(item.id)
        #                 new_add.remove(item.revision_id)
        #
        # else:
        #     if x.id in new_add:
        #         new_add.remove(x.id)
        #         versions = Version.objects.filter(revision_id=x.id)
        #         for v in versions:
        #             if v.id not in version_list:
        #                 save_sql(v, v, request, x)
        #                 version_list.append(v.id)
        #
        #

def save_sql(pre_v,mod_v,request,revision):
    operate_item = Admin_Operation()
    operate_item.pre_version = pre_v
    operate_item.mod_version = mod_v
    operate_item.revision = revision
    operate_item.admin = request.user
    operate_item.save()