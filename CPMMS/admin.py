from django.contrib import admin
from .models import *


admin.site.register(Account)
admin.site.register(Personnel)
admin.site.register(Worker)
admin.site.register(Attendance)
admin.site.register(Project)
admin.site.register(TaskSchedule)
admin.site.register(Progress)
admin.site.register(Resource)
admin.site.register(ResourceSubType)
admin.site.register(Payroll)
admin.site.register(Payroll_Bonus)
admin.site.register(Payroll_Deduction)

