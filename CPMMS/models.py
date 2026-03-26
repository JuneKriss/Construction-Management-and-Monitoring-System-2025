from django.db import models
import qrcode # type: ignore
from io import BytesIO
from django.core.files import File
from PIL import Image # type: ignore
from django.utils import timezone

class Account(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("PM", "Project Manager"),
        ("FM", "Foreman"),
        ("worker", "Worker"),
    ]

    account_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=150)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    status = models.CharField(max_length=50, default="Active")
    date_deactivated = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='CPMMS/Profile_imgs', default='profile.webp')

    def __str__(self):
        return f"{self.account_id} {self.username}"

class Personnel(models.Model):
    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("unavailable", "Unavailable"),
    ]

    personnel_id = models.AutoField(primary_key=True)
    account_id = models.ForeignKey(Account, null=True, on_delete=models.CASCADE, related_name='personal_info')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birthdate = models.DateField(max_length=50)
    gender = models.CharField(max_length=50)
    contact = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    email = models.EmailField(null=True)
    availability = models.CharField(max_length=12, null=True, choices=AVAILABILITY_CHOICES, default="available")
    
    def __str__(self):
        return f"{self.first_name}"

class Worker(models.Model):
    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("unavailable", "Unavailable"),
    ]

    worker_id = models.AutoField(primary_key=True)
    account_id = models.ForeignKey(Account, null=True, on_delete=models.CASCADE, related_name='worker_personal_info')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.IntegerField()
    gender = models.CharField(max_length=50)
    contact = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    availability = models.CharField(max_length=12, null=True, choices=AVAILABILITY_CHOICES, default="available")
    qr_code = models.ImageField(upload_to='CPMMS/QR_codes', blank=True)
    qr_code_text = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.qr_code_text and not self.qr_code:
            qrcode_img = qrcode.make(self.qr_code_text)
            canvas = Image.new('RGB', (300, 300), 'white')
            canvas.paste(qrcode_img)

            fname = f'qr_code-{self.account_id.username}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            self.qr_code.save(fname, File(buffer), save=False)
            buffer.close()
            canvas.close()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker_id} {self.first_name}"
    
class Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=50)
    client = models.CharField(max_length=50)
    description = models.TextField(max_length=100, default="No Description", null=True)
    budget = models.IntegerField()
    start_date = models.DateField()
    due_date = models.DateField()
    contract = models.ImageField(upload_to='CPMMS/Contracts')
    timeframe = models.ImageField(upload_to='CPMMS/Timeframes', null=True)
    project_percent = models.IntegerField(default=0)
    project_status = models.CharField(max_length=50, default="Not Started", null=True)
    date_registered = models.DateTimeField(default=timezone.now)
    project_manager_id = models.ForeignKey(Personnel, null=True, on_delete=models.SET_NULL, related_name='projects_as_manager')
    assigned_foreman = models.ForeignKey(Personnel, null=True, on_delete=models.SET_NULL, related_name='projects_as_foreman')
    isFinished = models.BooleanField(default=False)
    finalization_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Finalizing", "Finalizing"), ("Completed", "Completed")],
        default="Pending",
    )

    def calculate_project_progress(self):
        tasks = self.tasks.all()
        total_weighted_progress = 0
        total_percent_from_project = 0

        for task in tasks:
            progress = task.progress_id.worker_progress
            percent = task.percent_from_project
            print(f"Task: {task.task_name}, Progress: {progress}, Percent: {percent}")

            # Calculate the weighted progress contribution from each task
            weighted_progress = (progress * percent) / 100
            total_weighted_progress += weighted_progress
            total_percent_from_project += percent

        print(f"Total Weighted Progress: {total_weighted_progress}")
        print(f"Total Percent From Project: {total_percent_from_project}")

        if total_percent_from_project > 0:
            self.project_percent = round(total_weighted_progress)
            print(f"Calculated Project Percent: {self.project_percent}")
        else:
            self.project_percent = 0
            print("No tasks or task percentages are 0")

        self.save()

            
    def __str__(self):
        return f"{self.project_name}"
    
class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    worker_id = models.ForeignKey(Worker, null=True, on_delete=models.CASCADE, related_name='attendances')
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    period = models.CharField(max_length=10, choices=[("morning", "Morning"), ("afternoon", "Afternoon")], null=True)
    timeIn_status = models.CharField(max_length=50, null=True)
    project_id = models.ForeignKey(Project, null=True, on_delete=models.CASCADE, related_name="attendances")

    def __str__(self):
        return f"{self.worker_id.first_name}"

class Progress(models.Model):
    progress_id = models.AutoField(primary_key=True)
    worker_progress = models.IntegerField(default=0)
    remarks = models.TextField(max_length=100, default="None")
    date_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.progress_id} {self.worker_progress}"

class TaskSchedule(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('halfway', 'Halfway Completed'),
        ('nearly_completed', 'Nearly Completed'),
        ('completed', 'Completed'),
    ]
    TaskSchedule_id = models.AutoField(primary_key=True)
    foreman_id = models.ForeignKey(Personnel, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(default=timezone.now)
    task_name = models.CharField(max_length=50)
    date_start = models.DateField()
    deadline = models.DateField()
    percent_from_project = models.IntegerField()
    task_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='not_started')
    description = models.TextField(max_length=100, default="None")
    project_id = models.ForeignKey(Project, null=True, on_delete=models.CASCADE, related_name="tasks")
    workers = models.ManyToManyField(Worker, blank=True, related_name="assigned_tasks")
    progress_id = models.ForeignKey(Progress, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.progress_id:
            new_progress = Progress.objects.create()
            self.progress_id = new_progress
        super().save(*args, **kwargs)

        if self.project_id:
            print(f"Triggering project progress update for Project: {self.project_id.project_name}")
            self.project_id.calculate_project_progress()

    def __str__(self):
        return f"{self.TaskSchedule_id} {self.task_name}"
    
class ResourceSubType(models.Model):
    resource_type = models.CharField(max_length=50, choices=[
        ('material', 'Material'),
        ('supply', 'Supply'),
        ('equipment', 'Equipment'),
    ])
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Resource(models.Model):
    TYPE_CHOICES = [
        ('material', 'Material'),
        ('supply', 'Supply'),
        ('equipment', 'Equipment'),
    ]

    resource_id = models.AutoField(primary_key=True)
    project_id = models.ForeignKey(Project, null=True, on_delete=models.CASCADE, related_name="supplies")
    name = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, null=True)
    subtype = models.ForeignKey(ResourceSubType, null=True, blank=True, on_delete=models.SET_NULL)
    cost = models.IntegerField(default=0)
    cost_type = models.CharField(max_length=50, null=True)
    added_by = models.CharField(max_length=50, null=True)

    def __str__(self):
        return f"{self.project_id}"

class Payroll(models.Model):
    payroll_id = models.AutoField(primary_key=True)
    worker_id = models.ForeignKey(Worker, null=True, on_delete=models.CASCADE, related_name="worker_payroll")
    project_id = models.ForeignKey(Project, null=True, on_delete=models.CASCADE, related_name="project_payroll")
    total_amount = models.IntegerField()

    def __str__(self):
        return f"{self.payroll_id} {self.worker_id.last_name}"

class Payroll_Bonus(models.Model):
    bonus_id = models.AutoField(primary_key=True)
    bonus_name = models.CharField(max_length=50)
    bonus_amount = models.IntegerField(default=0)
    payroll_id = models.ForeignKey(Payroll, null=True, on_delete=models.CASCADE, related_name="payroll_bonus")

    def __str__(self):
        return f"{self.payroll_id}"

class Payroll_Deduction(models.Model):
    deduction_id = models.AutoField(primary_key=True)
    deduction_name = models.CharField(max_length=50)
    deduction_amount = models.IntegerField(default=0)
    payroll_id = models.ForeignKey(Payroll, null=True, on_delete=models.CASCADE, related_name="payroll_deductions")

    def __str__(self):
        return f"{self.payroll_id}"
