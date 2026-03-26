from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.db.models.functions import TruncMonth
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import datetime, timedelta, time, date
from django.db.models import Count, Sum, Prefetch
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_date
from .models import *
import json
from collections import defaultdict

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render(request=request))

def validate(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = Account.objects.get(username=username)

            if user.status != "Active":
                messages.error(request, 'This account has been deactivated. Please contact support.')
                return redirect('index')

            if check_password(password, user.password):
                request.session['user_id'] = user.account_id
                request.session['role'] = user.role

                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'worker':
                    return redirect('worker_home')
                elif user.role == 'PM':
                    return redirect('project_manager_home')
                elif user.role == 'FM':
                    return redirect('foreman_home')
                else:
                    messages.error(request, 'Unexpected role encountered. Please contact support.')
                    return redirect('index')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
                return redirect('index')

        except Account.DoesNotExist:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('index')

    return render(request, 'index.html')

def logout_user(request):
    logout(request)
    return redirect('index')

#WORKER VIEWS--------------------------------------------------------------------------------------------------------
def worker_home(request):
    account_id = request.session.get('user_id')
    if not account_id:
        return HttpResponse("Unauthorized", status=401)

    worker = get_object_or_404(Worker, account_id=account_id)

    assigned_tasks = TaskSchedule.objects.filter(workers=worker)

    assigned_projects = Project.objects.filter(
        project_id__in={task.project_id.project_id for task in assigned_tasks}
    ).exclude(finalization_status="Completed", project_status="Finished").order_by('-date_registered')

    project_ids = [project.project_id for project in assigned_projects]

    days_worked = Attendance.objects.filter(worker_id=worker, project_id__in=project_ids) \
        .values('recorded_at__date').distinct().count()

    template = loader.get_template('worker/worker.html')
    context = {
        'worker': worker,
        'assigned_projects': assigned_projects,
        'days_worked': days_worked,
    }

    return HttpResponse(template.render(context, request))

#WORKER PROFILE VIEWS--------------------------------------------------------------------------------------------------------
def worker_profile(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Worker.objects.filter(account_id=account_id).first()

    template = loader.get_template('worker/worker_profile.html')
    context = {
        'account': details,
    }
    return HttpResponse(template.render(context, request))

def update_worker_account(request):
    account_id = request.session.get('user_id')
    if not account_id:
        messages.error(request, "Account not found.")
        return redirect('worker_profile')

    try:
        account = Account.objects.get(account_id=account_id)
        worker = Worker.objects.filter(account_id=account).first()

        if request.method == 'POST':
            username = request.POST.get('username')
            if username:
                account.username = username

            if 'image' in request.FILES:
                image = request.FILES['image']

                if image.size > 15 * 1024 * 1024:
                    messages.error(request, "The uploaded image exceeds the 15MB limit.")
                else:
                    if account.image and account.image.name != 'profile.webp':
                        account.image.delete(save=False)
                    account.image = image

            worker.first_name = request.POST.get('f_name') or "Not Provided"
            worker.last_name = request.POST.get('l_name') or "Not Provided"
            worker.contact = request.POST.get('phone') or '000-000-0000'
            worker.address = request.POST.get('address') or 'Unknown Address'
            worker.gender = request.POST.get('gender') or 'Not specified'

            birthdate = request.POST.get('birthdate')
            if birthdate:
                try:
                    worker.birthdate = birthdate
                    # Calculate age
                    birth_date = datetime.strptime(birthdate, "%Y-%m-%d").date()
                    today = datetime.today().date()
                    worker.age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                except ValueError:
                    messages.error(request, "Invalid birthdate format.")
                    return redirect('worker_profile')

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')

            if new_password and not current_password:
                messages.error(request, "Please enter your current password to set a new one.")
                return redirect('worker_profile')

            if current_password and new_password:
                if check_password(current_password, account.password):
                    account.password = make_password(new_password)
                else:
                    messages.error(request, "Current password is incorrect. Password update failed.")
                    return redirect('worker_profile')
            elif current_password:
                messages.error(request, "New password is required.")
                return redirect('worker_profile')

            account.save()
            worker.save()

            messages.success(request, "Worker account updated successfully.")
            return redirect('worker_profile')

    except ObjectDoesNotExist:
        messages.error(request, "Account does not exist.")
        return redirect('worker_profile')

    context = {
        'account': worker,
    }
    return render(request, 'worker/worker_profile.html', context)
#WORKER PROFILE VIEWS--------------------------------------------------------------------------------------------------------END

#WORKER SCHEDULE VIEWS--------------------------------------------------------------------------------------------------------
def worker_schedule(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Worker.objects.filter(account_id=account_id).first()
    
    template = loader.get_template('worker/worker_schedule.html')
    context = {
        'account': details,
    }
    return HttpResponse(template.render(context, request))

def get_worker_schedules(request):
    try:
        account_id = request.session.get('user_id')
        worker = Worker.objects.get(account_id=account_id)
        tasks = TaskSchedule.objects.filter(workers=worker)

        colors = [
            "#FF6F61", "#6A1B9A", "#0277BD", "#43A047", "#FB8C00",
            "#C2185B", "#8E24AA", "#3949AB", "#D81B60", "#009688"
        ]
        num_colors = len(colors)
        events = []
        for task in tasks:
            progress = task.progress_id.worker_progress if task.progress_id else 0

            if progress == 100:
                color = "#B0B0B0"
                task_title = f"{task.task_name} (Completed)"
            else:
                color = colors[hash(task.TaskSchedule_id) % num_colors]
                task_title = task.task_name

            events.append({
                'title': task_title,
                'progress': task.progress_id.worker_progress,
                'start': task.date_start.isoformat(),
                'end': task.deadline.isoformat(),
                'description': task.description,
                'status': task.task_status,
                'backgroundColor': color,
                'borderColor': color,
                "textColor": "#FFFFFF",
            })
        return JsonResponse(events, safe=False)
    except Worker.DoesNotExist:
        return JsonResponse({'error': 'Worker not found'}, status=404)  

#WORKER SCHEDULE VIEWS--------------------------------------------------------------------------------------------------------END

#WORKER ATTENDANCE VIEWS--------------------------------------------------------------------------------------------------------
def worker_attendance(request):
    account_id = request.session.get('user_id')

    if not account_id:
        return render(request, 'worker/worker_attendance.html', {
            'worker': None,
            'project_attendance_map': {},
            'projects': [],
        })

    worker = Worker.objects.filter(account_id=account_id).first()
    if not worker:
        return render(request, 'worker/worker_attendance.html', {
            'worker': None,
            'project_attendance_map': {},
            'projects': [],
        })

    attendance_records = Attendance.objects.filter(worker_id=worker).select_related('project_id').order_by('-recorded_at')

    project_attendance_map = defaultdict(list)
    for attendance in attendance_records:
        if attendance.project_id:
            project_attendance_map[attendance.project_id].append(attendance)

    sorted_projects = sorted(project_attendance_map.keys(), key=lambda p: p.date_registered, reverse=True)
    sorted_project_attendance_map = {
        project: project_attendance_map[project]
        for project in sorted_projects
    }

    filter_project = request.GET.get('filter_project')
    if filter_project:
        filtered_project = next((p for p in sorted_projects if str(p.project_id) == filter_project), None)
        if filtered_project:
            project_attendance_map = {
                filtered_project: project_attendance_map[filtered_project]
            }

    context = {
        'worker': worker,
        'project_attendance_map': sorted_project_attendance_map,
        'projects': sorted_projects,
    }

    return render(request, 'worker/worker_attendance.html', context)

def search_attendance(request):
    attendance_records = None 

    if request.method == 'GET':
        search_date = request.GET.get('search_date')

        if search_date:
            search_date = parse_date(search_date)
            if search_date:
                start_datetime = datetime.combine(search_date, datetime.min.time())
                end_datetime = datetime.combine(search_date, datetime.max.time())

                attendance_records = Attendance.objects.filter(recorded_at__range=(start_datetime, end_datetime))
            else:
                attendance_records = None

    context = {
        'attendance_records': attendance_records,
    }

    return render(request, 'worker/worker_attendance.html', context)

#WORKER ATTENDANCE VIEWS--------------------------------------------------------------------------------------------------------END

#WORKER PAYROLL VIEWS--------------------------------------------------------------------------------------------------------
def worker_payroll(request):
    account_id = request.session.get('user_id') 
    if account_id:
        account = Account.objects.filter(account_id=account_id).first()
        worker = account.worker_personal_info.first() if account else None
        worker_id = worker.worker_id if worker else None
    else:
        account = None
        worker = None
        worker_id = None

    current_week = None
    payroll = None
    combined_data = []
    bonuses = []
    deductions = []

    if worker_id:
        worker_tasks = TaskSchedule.objects.filter(workers__worker_id=worker_id)
        if worker_tasks.exists():
            project = worker_tasks.first().project_id
            payroll = Payroll.objects.filter(worker_id=worker_id, project_id=project).first()

            if payroll:
                bonuses = list(Payroll_Bonus.objects.filter(payroll_id=payroll).values("bonus_name", "bonus_amount"))
                deductions = list(Payroll_Deduction.objects.filter(payroll_id=payroll).values("deduction_name", "deduction_amount"))

                max_len = max(len(bonuses), len(deductions))
                bonuses += [{}] * (max_len - len(bonuses))
                deductions += [{}] * (max_len - len(deductions))

                combined_data = zip(bonuses, deductions)

            start_date = project.start_date
            end_date = project.due_date
            total_weeks = []
            current_date = start_date

            while current_date <= end_date:
                week_end = current_date + timedelta(days=6)
                if week_end > end_date:
                    week_end = end_date
                total_weeks.append((current_date, week_end))
                current_date += timedelta(days=7)

            today = datetime.today().date()
            for week_start, week_end in total_weeks:
                if week_start <= today <= week_end:
                    current_week = (week_start, week_end)
                    break

    context = {
        'current_week': current_week,
        'account': account,
        'worker': worker,
        'total_payroll': payroll,
        'bonuses': bonuses,
        'deductions': deductions,
        'combined_data': combined_data, 
        'total_bonus': sum(b.get("bonus_amount", 0) for b in bonuses) if payroll else 0,
        'total_deduction': sum(d.get("deduction_amount", 0) for d in deductions) if payroll else 0,
        'net_salary': payroll.total_amount if payroll else 0,
    }
    
    return render(request, "worker/worker_payroll.html", context)


#WORKER PAYROLL VIEWS--------------------------------------------------------------------------------------------------------END

#WORKER VIEWS--------------------------------------------------------------------------------------------------------END

#ADMIN VIEWS--------------------------------------------------------------------------------------------------------

#ADMIN DASHBOARD--------------------------------------------------------------------------------------------

# --------------------  Helper Functions --------------------
def process_person_details(person):
    if not person:
        return "Not Assigned"
    
    name_parts = [
        person.first_name.strip() if person.first_name and person.first_name != "Not Provided" else "",
        person.last_name.strip() if person.last_name and person.last_name != "Not Provided" else "",
    ]
    full_name = " ".join(filter(None, name_parts))
    return full_name if full_name else f"Names not provided ({person.account_id.username.strip() if person.account_id else 'Unknown'})"

def calculate_minutes_late(time_in, period):
    if not time_in:
        return 0

    shift_start = datetime.strptime("08:00", "%H:%M").time() if period == "morning" else datetime.strptime("13:00", "%H:%M").time()
    time_in_dt = datetime.combine(datetime.today(), time_in)
    shift_start_dt = datetime.combine(datetime.today(), shift_start)
    return max((time_in_dt - shift_start_dt).total_seconds() // 60, 0)

def format_late_time(minutes_late):
    late_hours = int(minutes_late // 60)  # Convert to integer
    late_minutes = int(minutes_late % 60)  # Convert to integer
    return f"{late_hours} hour/s {late_minutes} minute/s" if minutes_late > 0 else "0 minutes"

def calculate_total_hours(time_in, time_out):
    if not time_in or not time_out:
        return "-"
    total_seconds = (datetime.combine(datetime.today(), time_out) - datetime.combine(datetime.today(), time_in)).total_seconds()
    return round(total_seconds / 3600, 2)

def format_date(date):
    return date.strftime("%B %d, %Y") if date else "N/A"

def get_status_label(status_key):
    return dict(TaskSchedule.STATUS_CHOICES).get(status_key, "Unknown Status")

def admin_dashboard(request):
    total_accounts = Account.objects.count()
    total_foreman_accounts = Account.objects.filter(role="FM").count()
    total_pm_accounts = Account.objects.filter(role="PM").count()
    total_worker_accounts = Account.objects.filter(role="worker").count()

    active_count = Account.objects.filter(status="Active").count()
    deactivated_count = Account.objects.filter(status="Deactivated").count()
    finished_projects = Project.objects.filter(project_percent=100).count()
    ongoing_projects = Project.objects.filter(project_percent__lt=100).count()

    projects_per_month = Project.objects.annotate(month=TruncMonth('date_registered')) \
    .values('month') \
    .annotate(count=Count('project_id')) \
    .order_by('month')

    labels = []
    data = []
    for project in projects_per_month:
        labels.append(project['month'].strftime('%B'))
        data.append(project['count'])

    all_months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    data_dict = dict(zip(labels, data))
    final_data = [data_dict.get(month, 0) for month in all_months]

    recent_projects = Project.objects.order_by('-date_registered')[:5]
    project_names = []
    payroll_costs = []
    resource_costs = []
    overall_expenditures = []
    
    for project in recent_projects:
        project_names.append(project.project_name)

        payroll_cost = Payroll.objects.filter(project_id=project).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        payroll_costs.append(payroll_cost)

        total_cost = 0
        for supply in project.supplies.all():
            if supply.cost_type == "Per Unit":
                total_cost += supply.cost * supply.quantity
            else:
                total_cost += supply.cost
        resource_costs.append(total_cost)

        overall_expenditures.append(payroll_cost + total_cost)
    
    projects = Project.objects.filter(project_percent__lt=100).order_by('-date_registered')

    context = {
        "total_accounts": total_accounts,
        "total_foreman_accounts": total_foreman_accounts,
        "total_pm_accounts": total_pm_accounts,
        "total_worker_accounts": total_worker_accounts,
        'active_count': active_count,
        'deactivated_count': deactivated_count,
        'ongoing_projects': ongoing_projects,
        'finished_projects': finished_projects,
        'labels': all_months,
        'data': final_data,
        'recent_project_names': project_names,
        'payroll_costs': payroll_costs,
        'resource_costs': resource_costs,
        'overall_expenditures': overall_expenditures,
        'projects': projects,
    }

    return render(request, 'admin/home.html', context)

def project_report_view(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    current_date = date.today() 

    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)  
    task_schedules = TaskSchedule.objects.filter(
        project_id=project,
        date_created__date__range=(start_of_week, end_of_week)
    )

    resources = Resource.objects.filter(project_id=project)
    materials = resources.filter(type='material')
    supplies = resources.filter(type='supply')
    equipment = resources.filter(type='equipment')

    context = {
        'project': project,
        'current_date': current_date,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'task_schedules': task_schedules,
        'materials': materials,
        'supplies': supplies,
        'equipment': equipment,
    }

    return render(request, 'admin/weekly_report.html', context)

def attendance_report(request, project_id):
    if request.GET.get("category") != "attendance":
        return JsonResponse({"error": "Invalid request"}, status=400)

    project = get_object_or_404(Project, pk=project_id)
    attendances = project.attendances.all()

    project_manager = process_person_details(project.project_manager_id)
    foreman = process_person_details(project.assigned_foreman)

    report_data = [
        {
            "employee_name": process_person_details(attendance.worker_id),
            "time_in": attendance.time_in.strftime("%H:%M") if attendance.time_in else "-",
            "time_out": attendance.time_out.strftime("%H:%M") if attendance.time_out else "-",
            "total_hours": calculate_total_hours(attendance.time_in, attendance.time_out),
            "minutes_late": format_late_time(calculate_minutes_late(attendance.time_in, attendance.period))
        }
        for attendance in attendances
    ]

    return JsonResponse({
        "project_name": project.project_name,
        "attendance": report_data,
        "project_manager": project_manager,
        "foreman": foreman
    })

def attendance_report_all(request):
    if request.GET.get("category") != "attendance":
        return JsonResponse({"error": "Invalid request"}, status=400)

    projects = Project.objects.all()
    all_reports = []

    for project in projects:
        attendances = project.attendances.all()
        report_data = [
            {
                "employee_name": process_person_details(attendance.worker_id),
                "time_in": attendance.time_in.strftime("%H:%M") if attendance.time_in else "-",
                "time_out": attendance.time_out.strftime("%H:%M") if attendance.time_out else "-",
                "total_hours": calculate_total_hours(attendance.time_in, attendance.time_out),
                "minutes_late": format_late_time(calculate_minutes_late(attendance.time_in, attendance.period))
            }
            for attendance in attendances
        ]

        all_reports.append({
            "project_name": project.project_name,
            "attendance": report_data,
            "project_manager": process_person_details(project.project_manager_id),
            "foreman": process_person_details(project.assigned_foreman)
        })

    return JsonResponse({"projects": all_reports})

def payroll_report(request, project_id):
    if request.GET.get("category") != "payroll":
        return JsonResponse({"error": "Invalid request"}, status=400)

    project = get_object_or_404(Project, pk=project_id)
    payrolls = Payroll.objects.filter(project_id=project)

    workers_data = []
    total_bonuses_sum = 0
    total_deductions_sum = 0
    total_amount_sum = 0

    for payroll in payrolls:
        bonuses = Payroll_Bonus.objects.filter(payroll_id=payroll)
        deductions = Payroll_Deduction.objects.filter(payroll_id=payroll)

        bonus_list = [{"name": bonus.bonus_name, "amount": bonus.bonus_amount} for bonus in bonuses]
        deduction_list = [{"name": deduction.deduction_name, "amount": deduction.deduction_amount} for deduction in deductions]

        worker_total_bonus = sum(bonus["amount"] for bonus in bonus_list)
        worker_total_deduction = sum(deduction["amount"] for deduction in deduction_list)

        workers_data.append({
            "worker_name": process_person_details(payroll.worker_id),
            "bonuses": bonus_list,
            "deductions": deduction_list,
            "total_amount": payroll.total_amount,
            "total_bonus": worker_total_bonus,
            "total_deduction": worker_total_deduction
        })

        total_bonuses_sum += worker_total_bonus
        total_deductions_sum += worker_total_deduction
        total_amount_sum += payroll.total_amount

    return JsonResponse({
        "project_name": project.project_name,
        "workers": workers_data,
        "totals": {
            "total_bonuses": total_bonuses_sum,
            "total_deductions": total_deductions_sum,
            "total_amount": total_amount_sum
        }
    })

def payroll_report_all(request):
    if request.GET.get("category") != "payroll":
        return JsonResponse({"error": "Invalid request"}, status=400)

    projects = Project.objects.all()
    all_reports = []
    grand_total_bonuses = 0
    grand_total_deductions = 0
    grand_total_amount = 0

    for project in projects:
        payrolls = Payroll.objects.filter(project_id=project)
        if not payrolls.exists():
            continue

        workers_data = []
        project_total_bonuses = 0
        project_total_deductions = 0
        project_total_amount = 0

        for payroll in payrolls:
            bonuses = Payroll_Bonus.objects.filter(payroll_id=payroll)
            deductions = Payroll_Deduction.objects.filter(payroll_id=payroll)

            bonus_list = [{"name": bonus.bonus_name, "amount": bonus.bonus_amount} for bonus in bonuses]
            deduction_list = [{"name": deduction.deduction_name, "amount": deduction.deduction_amount} for deduction in deductions]

            worker_total_bonus = sum(bonus["amount"] for bonus in bonus_list)
            worker_total_deduction = sum(deduction["amount"] for deduction in deduction_list)

            workers_data.append({
                "worker_name": process_person_details(payroll.worker_id),
                "bonuses": bonus_list,
                "deductions": deduction_list,
                "total_amount": payroll.total_amount,
                "total_bonus": worker_total_bonus,
                "total_deduction": worker_total_deduction
            })

            project_total_bonuses += worker_total_bonus
            project_total_deductions += worker_total_deduction
            project_total_amount += payroll.total_amount

        all_reports.append({
            "project_name": project.project_name,
            "workers": workers_data,
            "totals": {
                "total_bonuses": project_total_bonuses,
                "total_deductions": project_total_deductions,
                "total_amount": project_total_amount
            }
        })

        grand_total_bonuses += project_total_bonuses
        grand_total_deductions += project_total_deductions
        grand_total_amount += project_total_amount

    return JsonResponse({
        "projects": all_reports,
        "grand_totals": {
            "total_bonuses": grand_total_bonuses,
            "total_deductions": grand_total_deductions,
            "total_amount": grand_total_amount
        }
    })

def get_overall_project_report(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)

    # Fetch workers involved in the project
    worker_ids = TaskSchedule.objects.filter(project_id=project).values_list("workers", flat=True)
    workers = Worker.objects.filter(worker_id__in=worker_ids)

    worker_data = []
    for worker in workers:
        attendance = Attendance.objects.filter(worker_id=worker, project_id=project).values("recorded_at", "timeIn_status", "time_in", "time_out")
        payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()

        total_late_time = sum([calculate_minutes_late(entry["time_in"], "morning") for entry in attendance if entry["time_in"]])

        total_hours = sum([
            calculate_total_hours(entry["time_in"], entry["time_out"]) 
            for entry in attendance if entry["time_in"] and entry["time_out"]
        ])

        bonuses = Payroll_Bonus.objects.filter(payroll_id=payroll).values("bonus_name", "bonus_amount") if payroll else []
        deductions = Payroll_Deduction.objects.filter(payroll_id=payroll).values("deduction_name", "deduction_amount") if payroll else []
        total_bonus = sum([bonus["bonus_amount"] for bonus in bonuses])
        total_deduction = sum([deduction["deduction_amount"] for deduction in deductions])
        net_salary = (payroll.total_amount if payroll else 0) + total_bonus - total_deduction

        worker_data.append({
            "id": worker.worker_id,
            "employee_name": process_person_details(worker),
            "attendance": list(attendance),
            "total_late_time": format_late_time(total_late_time),
            "total_hours": total_hours if total_hours else "-",
            "salary": payroll.total_amount if payroll else 0,
            "bonuses": list(bonuses),
            "deductions": list(deductions),
            "net_salary": net_salary
        })

    # Fetch project resources
    resources = Resource.objects.filter(project_id=project).values(
        "name", "quantity", "type", "cost", "subtype__name", "added_by"
    )

    # Fetch project tasks and progress
    tasks = TaskSchedule.objects.filter(project_id=project).select_related("progress_id")
    
    task_data = []
    for task in tasks:
        # Get assigned worker names using process_person_details
        assigned_workers = ", ".join([process_person_details(worker) for worker in task.workers.all()]) if task.workers.exists() else "No Workers Assigned"

        task_data.append({
            "task_id": task.TaskSchedule_id,
            "task_name": task.task_name,
            "start_date": format_date(task.date_start),
            "due_date": format_date(task.deadline),
            "status": get_status_label(task.task_status),
            "percent_from_project": task.percent_from_project,
            "progress": task.progress_id.worker_progress if task.progress_id else 0,
            "assigned_worker": assigned_workers,  # Assigned worker names
            "description": task.description,
        })

    data = {
        "project": {
            "project_name": project.project_name,
            "project_manager": process_person_details(project.project_manager_id),
            "foreman": process_person_details(project.assigned_foreman),
            "budget": project.budget,
            "start_date": project.start_date.strftime("%Y-%m-%d"),
            "due_date": project.due_date.strftime("%Y-%m-%d"),
            "progress": project.project_percent,
            "status": project.project_status,
        },
        "workers": worker_data,
        "resources": list(resources),
        "tasks": task_data,  # Include task data
    }

    return JsonResponse(data)



#ADMIN DASHBOARD--------------------------------------------------------------------------------------------END

#ADMIN MANAGE ACCOUNTS--------------------------------------------------------------------------------------------
def admin_accounts(request):
    accounts = Account.objects.exclude(role='admin').exclude(status='Deactivated').order_by('-date_created')
    projects = Project.objects.all()

    template = loader.get_template('admin/manage_accounts.html')
    context = {
        'accounts': accounts,
        'projects': projects,
    }
    return HttpResponse(template.render(context, request))

def add_accountPage(request):
    return render(request, 'admin/add_account.html')

def check_username(request):
    username = request.GET.get('username', '')
    exists = Account.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def add_account(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        addAccount = Account(username=username, password=make_password(password), role=role)
        addAccount.save()

        if 'submit' in request.POST:
            return redirect('admin_accounts')
        elif 'submit_another' in request.POST:
            messages.success(request, 'Account Successfully Added!')
            return redirect('add_account')
        
    return render(request, 'admin/add_account.html')

def accountDetails_page(request, id):
    account = get_object_or_404(Account, account_id=id)
    personnel = Personnel.objects.filter(account_id=account).first()
    worker = Worker.objects.filter(account_id=account).first()

    template = loader.get_template('admin/account_details.html')
    context = {
        'account': account,
        'personnel': personnel,
        'worker': worker,
    }
    return HttpResponse(template.render(context, request))

def search_accounts(request):
    query = request.GET.get('query', '')
    accounts = Account.objects.filter(username__icontains=query).exclude(role='admin')
    
    data = {
        'accounts': [
            {
                'account_id': account.account_id,
                'username': account.username,
                'password': account.password,
                'role': account.get_role_display(),
                'profile_image': '/static/images/profile.webp'
            }
            for account in accounts
        ]
    }
    return JsonResponse(data)

def filter_accounts(request):
    role = request.GET.get('role', '')

    if role:
        accounts = Account.objects.filter(role=role).exclude(role='admin')
    else:
        accounts = Account.objects.all().exclude(role='admin')

    data = {
        'accounts': [
            {
                'account_id': account.account_id,
                'username': account.username,
                'password': account.password,
                'role': account.get_role_display(),
                'profile_image': '/static/images/profile.webp'
            }
            for account in accounts
        ]
    }
    return JsonResponse(data)

def deactivate_account(request, account_id):
    account = get_object_or_404(Account, account_id=account_id)
    if account.status == "Active":
        account.status = "Deactivated"
        account.date_deactivated = timezone.now() 
        account.save()
        messages.success(request, f"Account '{account.username}' has been deactivated.")
    else:
        messages.error(request, f"Account '{account.username}' is already deactivated.")
    return redirect('admin_accounts')

def account_history(request):
    deactivated_accounts = Account.objects.filter(status='Deactivated').order_by('-date_deactivated')
    template = loader.get_template('admin/accounts_history.html')
    context = {
        'accounts': deactivated_accounts,
    }
    return HttpResponse(template.render(context, request))

def activate_account(request, account_id):
    account = get_object_or_404(Account, account_id=account_id)
    if account.status == "Deactivated":
        account.status = "Active"
        account.save()
        messages.success(request, f"Account '{account.username}' has been activated.")
    else:
        messages.error(request, f"Account '{account.username}' is already activated.")
    return redirect('admin_accounts')

#ADMIN MANAGE ACCOUNTS--------------------------------------------------------------------------------------------END

#ADMIN MANAGE PROJECTS--------------------------------------------------------------------------------------------
def admin_projects(request):
    projects = Project.objects.all().order_by('-date_registered')
    template = loader.get_template('admin/manage_projects.html')
    context = {
        'projects': projects,
    }
    return HttpResponse(template.render(context, request))

def admin_project_details(request, id):
    project = get_object_or_404(Project, project_id=id)
    task = TaskSchedule.objects.filter(project_id=id).first()

    foreman = task.foreman_id if task and task.foreman_id else None
    workers = task.workers.all() if task else []
    pm = Personnel.objects.get(personnel_id=project.project_manager_id.personnel_id)

    resources = Resource.objects.filter(project_id=project)

    template = loader.get_template('admin/project_details.html')
    context = {
        'project': project,
        'foreman': foreman,
        'workers': workers,
        'manager': pm,
        'resources': resources,
    }
    return HttpResponse(template.render(context, request))

def update_project(request, id):
    project = get_object_or_404(Project, pk=id)
    personnels = Personnel.objects.filter(account_id__role="PM")

    if request.method == 'POST':
        project.project_name = request.POST.get('project_name', project.project_name)
        project.client = request.POST.get('client', project.client)
        project.description = request.POST.get('description', project.description)
        project.budget = int(request.POST.get('budget', project.budget))
        project.start_date = request.POST.get('start', project.start_date)
        project.due_date = request.POST.get('due', project.due_date)

        if 'image' in request.FILES:
            project.contract = request.FILES['image']
        
        project.save()

        return JsonResponse({
            'success': True,
            'message': "Project updated successfully!"
        })
    
    return render(request, 'project_details.html', {
        'project': project,
        'personnels': personnels,
    })

def search_projects(request):
    query = request.GET.get('query', '')
    
    if query:
        projects = Project.objects.filter(
            models.Q(project_name__icontains=query) | 
            models.Q(client__icontains=query)
        )
    else:
        projects = Project.objects.all().order_by('-date_registered')

    data = {
        'projects': [
            {
                'project_name': project.project_name,
                'client': project.client,
                'start_date': project.start_date,
                'due_date': project.due_date,
                'project_percent': project.project_percent,
            }
            for project in projects
        ]
    }
    return JsonResponse(data)

def create_Projectpage(request):
    personnels = Personnel.objects.filter(account_id__role="PM", availability="available")
    template = loader.get_template('admin/create_project.html')
    context = {
        'personnels': personnels,
    }
    return HttpResponse(template.render(context, request))

def registerProject(request):
    if request.method == 'POST':
        try:
            project_name = request.POST.get('project_name')
            client = request.POST.get('client')
            budget = request.POST.get('budget')
            description = request.POST.get('description')
            start = request.POST.get('start')
            end = request.POST.get('end')
            image = request.FILES.get('contract')
            personnel_id = request.POST.get('personnel')

            personnel = Personnel.objects.get(personnel_id=personnel_id)
            personnel.availability = 'unavailable'
            personnel.save()

            addProject = Project(
                project_name=project_name,
                client=client,
                budget=budget,
                description = description,
                start_date=start,
                due_date=end,
                contract=image,
                project_manager_id = personnel
            )
            addProject.save()

            return JsonResponse({"success": True, "message": "Project registered successfully."})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

#ADMIN MANAGE PROJECTS--------------------------------------------------------------------------------------------END

#END ADMIN VIEWS--------------------------------------------------------------------------------------------------------

#FOREMAN VIEWS--------------------------------------------------------------------------------------------------------
def foreman_home(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        assigned_projects = Project.objects.filter(
            assigned_foreman=details,
        ).exclude(finalization_status="Completed", project_status="Finished")

        workers = Worker.objects.filter(
            assigned_tasks__project_id__in=assigned_projects.values_list('project_id', flat=True)
        ).distinct()

        resources = Resource.objects.filter(
            project_id__in=assigned_projects.values_list('project_id', flat=True)
        )
    else:
        details = None
        assigned_projects = []
        workers = []
        resources = []

    template = loader.get_template('foreman/home.html')
    context = {
        'account': details,
        'assigned_projects': assigned_projects,
        'workers': workers,
        'resources': resources, 
    }
    return HttpResponse(template.render(context, request))

#FOREMAN MANAGE ATTENDANCE--------------------------------------------------------------------------------------------
def foreman_attendance(request):
    account_id = request.session.get('user_id')
    filtered_projects = Project.objects.none()
    workers_with_attendance = []

    if account_id:
        foreman_details = Personnel.objects.filter(account_id=account_id).first()

        if foreman_details:
            filtered_projects = Project.objects.filter(
                assigned_foreman=foreman_details.personnel_id,
                project_percent__lt=100
            ).distinct()

            task_schedules = TaskSchedule.objects.filter(project_id__in=filtered_projects)

            workers_with_attendance = Worker.objects.filter(
                assigned_tasks__in=task_schedules
            ).distinct().prefetch_related(
                Prefetch(
                    'attendances',
                    queryset=Attendance.objects.filter(project_id__in=filtered_projects).distinct(),
                    to_attr='filtered_attendances'
                )
            ).filter(attendances__isnull=False)
            for worker in workers_with_attendance:
                worker.filtered_attendances = list(
                    {attendance.project_id: attendance for attendance in worker.filtered_attendances}.values()
                )

    template = loader.get_template('foreman/attendance.html')
    context = {
        'account': foreman_details,
        'workers_with_attendance': workers_with_attendance,
        'filtered_projects': filtered_projects,
    }
    return HttpResponse(template.render(context, request))

def get_attendance_data(request, worker_id):
    worker = Worker.objects.get(worker_id=worker_id)
    attendances = Attendance.objects.filter(worker_id=worker).order_by('-recorded_at').values(
        'time_in', 'time_out', 'period', 'timeIn_status', 'recorded_at'
    )

    if worker.first_name != 'Not Provided' and worker.last_name == 'Not Provided':
        worker_name = worker.first_name
    elif worker.last_name != 'Not Provided' and worker.first_name == 'Not Provided':
        worker_name = worker.last_name
    elif worker.first_name == 'Not Provided' and worker.last_name == 'Not Provided':
        worker_name = 'Names Not Provided'
    else:
        worker_name = f"{worker.first_name} {worker.last_name}"
        
    period_choices = dict(Attendance._meta.get_field('period').choices)

    for attendance in attendances:
        recorded_at = attendance['recorded_at']
        formatted_date = recorded_at.strftime('%b. %d, %Y')
        attendance['recorded_at'] = formatted_date

        if attendance['time_in']:
            time_in = attendance['time_in']
            attendance['time_in'] = time_in.strftime('%H:%M')
        else:
            attendance['time_in'] = '---'

        if attendance['time_out']:
            time_out = attendance['time_out']
            attendance['time_out'] = time_out.strftime('%H:%M')
        else:
            attendance['time_out'] = '---'

        if attendance['timeIn_status'] == 'Late':
            attendance['timeIn_status_class'] = 'late'
        else:
            attendance['timeIn_status_class'] = 'present'
        
        period = attendance['period']
        if period:
            attendance['period'] = period_choices.get(period, 'N/A')
        else:
            attendance['period'] = 'N/A'

    attendance_data = list(attendances)

    return JsonResponse({
        'workerName': worker_name,
        'attendances': attendance_data
    })

def foreman_QRcamera(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()
    
    template = loader.get_template('foreman/QR_camera.html')
    context = {
        'account': details,
    }
    return HttpResponse(template.render(context, request))

def get_worker_info(request, account_id):
    try:
        worker = Worker.objects.get(account_id=account_id)
        data = {
            'success': True,
            'first_name': worker.first_name,
            'last_name': worker.last_name,
            'age': worker.age,
            'gender': worker.gender,
            'contact': worker.contact,
            'address': worker.address,
        }
        return JsonResponse(data)
    except Worker.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Worker not found'}, status=404)

def record_attendance(request, account_id):
    try:
        if request.method == 'GET':
            foreman_account_id = request.session.get('user_id')
            if not foreman_account_id:
                return JsonResponse({"success": False, "message": "You are not logged in as a foreman."}, status=403)

            foreman = get_object_or_404(Personnel, account_id=foreman_account_id, account_id__role="FM")

            worker = get_object_or_404(Worker, account_id=account_id)

            assigned_task = (
                TaskSchedule.objects.filter(
                    foreman_id=foreman,
                    workers=worker,
                    project_id__project_percent__lt=100,  # Ensure project progress is not 100%
                    progress_id__worker_progress__lt=100  # Ensure task progress is not 100%
                )
                .values('project_id', 'project_id__project_name', 'task_name')
                .first()
            )

            if not assigned_task:
                return JsonResponse({"success": False, "message": "Worker is not assigned to this project or task."}, status=400)

            project_id = assigned_task['project_id']
            project_name = assigned_task['project_id__project_name']
            task_name = assigned_task['task_name']

            # Proceed with attendance recording logic
            now = timezone.localtime()
            current_time = time(8, 0) # example time: time(8, 0), datetime.now().time()
            today = now.date()

            # Define attendance periods
            periods = {
                "morning": {"start": time(8, 0), "end": time(12, 0)},
                "afternoon": {"start": time(13, 0), "end": time(17, 0)},
            }

            # Grace periods
            time_in_grace_start = {
                "morning": (datetime.combine(today, periods["morning"]["start"]) - timedelta(minutes=10)).time(),
                "afternoon": (datetime.combine(today, periods["afternoon"]["start"]) - timedelta(minutes=10)).time(),
            }
            time_out_grace_start = {
                "morning": (datetime.combine(today, periods["morning"]["end"]) - timedelta(minutes=10)).time(),
                "afternoon": (datetime.combine(today, periods["afternoon"]["end"]) - timedelta(minutes=10)).time(),
            }
            time_out_cutoff = {
                "afternoon": (datetime.combine(today, periods["afternoon"]["end"]) + timedelta(hours=1)).time(),
            }

            # Determine the attendance period
            period_name, period_start, period_end = None, None, None
            for name, period in periods.items():
                if time_in_grace_start[name] <= current_time < period["end"] or \
                   time_out_grace_start[name] <= current_time <= time_out_cutoff.get(name, period["end"]):
                    period_name, period_start, period_end = name, period["start"], period["end"]
                    break

            if not period_name:
                return JsonResponse({"success": False, "message": "Attendance not allowed at this time."}, status=400)

            # Check for existing attendance record
            attendance = Attendance.objects.filter(worker_id=worker, recorded_at__date=today, period=period_name).first()
            if not attendance:
                attendance = Attendance(worker_id=worker, period=period_name, project_id_id=project_id)

            # Handle time-in logic
            if not attendance.time_in:
                if time_in_grace_start[period_name] <= current_time <= period_end:
                    status = "Present" if current_time <= period_start else "Late"
                    attendance.time_in = current_time
                    attendance.timeIn_status = status
                    attendance.save()

                    daily_pay = 400
                    period_pay = daily_pay / 2
                    pay = period_pay if status == "Present" else period_pay / 2

                    payroll, _ = Payroll.objects.get_or_create(
                        worker_id=worker, project_id_id=project_id, defaults={'total_amount': 0}
                    )
                    payroll.total_amount += pay
                    payroll.save()

                    return JsonResponse({
                        "success": True,
                        "message": "Time-in recorded successfully.",
                        "timeIn_status": status,
                        "project": project_name,
                        "task": task_name
                    })
                else:
                    return JsonResponse({"success": False, "message": "Time-in not allowed at this time."}, status=400)

            # Handle time-out logic
            elif not attendance.time_out:
                if period_name == "morning":
                    if time_out_grace_start["morning"] <= current_time < periods["afternoon"]["start"]:
                        attendance.time_out = current_time
                        attendance.save()
                        return JsonResponse({
                            "success": True,
                            "message": "Time-out recorded successfully.",
                            "project": project_name,
                            "task": task_name
                        })
                elif period_name == "afternoon":
                    if time_out_grace_start["afternoon"] <= current_time <= time_out_cutoff.get("afternoon", period_end):
                        attendance.time_out = current_time
                        attendance.save()
                        return JsonResponse({
                            "success": True,
                            "message": "Time-out recorded successfully.",
                            "project": project_name,
                            "task": task_name
                        })
                else:
                    return JsonResponse({"success": False, "message": "Time-out not allowed at this time."}, status=400)

            # Both time-in and time-out are recorded
            return JsonResponse({"success": False, "message": f"Attendance already completed for {period_name} period."}, status=400)

        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    except Exception as e:
        print("Error in record_attendance:", e)
        return JsonResponse({"success": False, "message": "Internal server error."}, status=500)


def filter_attendance(request):
    project_id = request.GET.get('project_id')
    
    if project_id:
        attendance_list = Attendance.objects.filter(
            worker_id__assigned_tasks__project_id=project_id
        ).values('worker_id', 'recorded_at').annotate(
            attendance_count=Count('attendance_id')
        ).filter(attendance_count=1)
        
        attendance_list = Attendance.objects.filter(
            worker_id__in=[attendance['worker_id'] for attendance in attendance_list]
        ).select_related('worker_id__account_id') 

    else:
        attendance_list = Attendance.objects.all().select_related('worker_id__account_id')

    context = {'attendance_list': attendance_list}
    html = render_to_string('foreman/components/attendance_table.html', context)
    
    return JsonResponse({'html': html})

#FOREMAN MANAGE ATTENDANCE--------------------------------------------------------------------------------------------END

#FOREMAN MANAGE PROGRESS--------------------------------------------------------------------------------------------
def foreman_progress(request):
    account_id = request.session.get('user_id')
    filtered_projects = Project.objects.none()

    if account_id:
        foreman_details = Personnel.objects.filter(account_id=account_id).first()

        if foreman_details:
            filtered_projects = Project.objects.filter(tasks__foreman_id=foreman_details).distinct()
            tasks = TaskSchedule.objects.filter(foreman_id=foreman_details.personnel_id).order_by('-date_created')
    
    template = loader.get_template('foreman/progress.html')
    context = {
        'account': foreman_details,
        'tasks': tasks,
        'projects': filtered_projects,
    }
    return HttpResponse(template.render(context, request))

def search_tasks(request):
    query = request.GET.get('query', '').strip()
    tasks = TaskSchedule.objects.filter(task_name__icontains=query) if query else TaskSchedule.objects.all()

    results = [
        {
            'task_name': task.task_name,
            'progress_status': get_task_progress_status(task),
            'deadline': task.deadline,
            'worker_progress': task.progress_id.worker_progress if task.progress_id else 0,
            'workers': [
                {'first_name': worker.first_name, 'last_name': worker.last_name}
                for worker in task.workers.all()
            ]
        }
        for task in tasks
    ]

    return JsonResponse({'tasks': results})

def get_task_progress_status(task):
    if task.progress_id:
        progress = task.progress_id.worker_progress
        if progress == 0:
            return '<span class="status-circle status-not-started"></span><p class="not-started-text">Not Started</p>'
        elif 0 < progress <= 49:
            return '<span class="status-circle status-in-progress"></span><p class="in-progress-text">In Progress</p>'
        elif progress == 50:
            return '<span class="status-circle status-halfway"></span><p class="halfway-text">Halfway Completed</p>'
        elif 50 < progress <= 99:
            return '<span class="status-circle status-nearly-completed"></span><p class="nearly-completed-text">Nearly Completed</p>'
        elif progress == 100:
            return '<span class="status-circle status-completed"></span><p class="completed-text">Completed</p>'
    return ''

def get_task_details(request, task_id):
    task = get_object_or_404(TaskSchedule, pk=task_id)

    task_details = {
        'task_name': task.task_name,
        'task_status': task.task_status,
        'start_date': task.date_start.isoformat(),
        'deadline': task.deadline.isoformat(),
        'worker_progress': task.progress_id.worker_progress,
        'percent_from': task.percent_from_project,
        'remarks': task.progress_id.remarks if task.progress_id.remarks not in [None, "None"] else 'None',
        'can_edit': task.progress_id.worker_progress < 100, 
        'workers': [
            {
                "Fname": f"{worker.first_name}",
                "Lname": f"{worker.last_name}",
                "account_name": worker.account_id.username,
                'role': 'Worker'
            }
            for worker in task.workers.all()
        ]
    }

    return JsonResponse(task_details)

def update_progress(request, task_id):
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)
    
    data = json.loads(request.body)

    worker_progress = int(data.get('worker_progress'))
    percent_from_project = int(data.get("percentage_from_project"))
    remarks = data.get('remarks') or 'None'

    task = get_object_or_404(TaskSchedule, pk=task_id)
    progress = task.progress_id

    progress.worker_progress = worker_progress
    progress.remarks = remarks
    progress.date_updated = timezone.now()
    progress.save()

    task.percent_from_project = percent_from_project
    task.save()
    
    if worker_progress == 0:
        task.task_status = 'not_started'
    elif 0 < worker_progress <= 49:
        task.task_status = 'in_progress'
    elif worker_progress == 50:
        task.task_status = 'halfway'
    elif 50 < worker_progress <= 99:
        task.task_status = 'nearly_completed'
    elif worker_progress == 100:
        task.task_status = 'completed'

        for worker in task.workers.all():
            worker.availability = 'available'
            worker.save()

            start_date = task.date_start
            end_date = task.deadline

            attendances = Attendance.objects.filter(
                worker_id=worker,
                project_id=task.project_id,
                recorded_at__date__range=(start_date, end_date)
            )

            attendance_payment = 0
            for attendance in attendances:
                if attendance.period == "morning":
                    attendance_payment += 200
                elif attendance.period == "afternoon":
                    attendance_payment += 200

            payroll, created = Payroll.objects.get_or_create(
                worker_id=worker,
                project_id=task.project_id,
                defaults={
                    'bonus': "0",
                    'deductions': "0",
                    'total_amount': 0
                }
            )

            payroll.total_amount = attendance_payment
            payroll.save()
    
    if task.project_id.project_status == "Not Started" and any(t.progress_id.worker_progress > 0 for t in task.project_id.tasks.all()):
        task.project_id.project_status = "Ongoing"
        task.project_id.save()

    task.save()

    return JsonResponse({"message": "Progress updated successfully!"})


def filter_task(request):
    account_id = request.session.get('user_id')
    foreman = Personnel.objects.get(account_id = account_id)
    project_id = request.GET.get('project_id')
    tasks = TaskSchedule.objects.all()
    project_progress = None

    if project_id:
        tasks = tasks.filter(project_id__project_id=project_id).order_by('-date_created')
        
        try:
            project = Project.objects.get(project_id=project_id)
            project_progress = project.project_percent
        except Project.DoesNotExist:
            project_progress = None
    else:
        tasks = TaskSchedule.objects.filter(foreman_id=foreman.personnel_id).order_by('-date_created')

    rendered_table = render(request, 'foreman/components/task_table.html', {'tasks': tasks}).content.decode('utf-8')

    return JsonResponse({
        'html': rendered_table,
        'progress': project_progress
    })

def update_progress_after_completed(request, task_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            worker_progress = int(data.get("worker_progress"))
            percent_from_project = int(data.get("percentage_from_project"))
            remarks = data.get("remarks") or "None"

            # Get the task and progress instance
            task = get_object_or_404(TaskSchedule, TaskSchedule_id=task_id)
            progress = task.progress_id  # Use progress_id instead of progress

            if not progress:
                return JsonResponse({"success": False, "error": "Progress record not found"})

            # Debugging Logs
            print(f"Updating Progress for Task: {task.task_name}")
            print(f"Worker Progress: {worker_progress}, Percent from Project: {percent_from_project}, Remarks: {remarks}")

            # Update progress
            progress.worker_progress = worker_progress
            progress.remarks = remarks
            progress.date_updated = timezone.now()
            progress.save()

            # Update task status based on progress
            if worker_progress == 0:
                task.task_status = "not_started"
            elif 0 < worker_progress <= 49:
                task.task_status = "in_progress"
            elif worker_progress == 50:
                task.task_status = "halfway"
            elif 50 < worker_progress <= 99:
                task.task_status = "nearly_completed"
            elif worker_progress == 100:
                task.task_status = "completed"

            # Update percent from project
            task.percent_from_project = percent_from_project
            task.save()

            # Debugging Logs
            print(f"Task status updated to: {task.task_status}")
            print(f"Task percent from project updated to: {task.percent_from_project}")

            # Update worker availability
            worker_availability = "available" if worker_progress == 100 else "not available"

            for worker in task.workers.all():
                worker.availability = worker_availability
                worker.save()
                print(f"Worker {worker} availability set to {worker_availability}")

            # Update project progress
            if task.project_id:
                task.project_id.calculate_project_progress()
                print(f"Project progress recalculated for {task.project_id.project_name}")

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error updating progress: {e}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

#FOREMAN MANAGE PROGRESS--------------------------------------------------------------------------------------------END

#FOREMAN MANAGE ACCOUNT--------------------------------------------------------------------------------------------
def foreman_account(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()
    
    template = loader.get_template('foreman/foreman_account.html')
    context = {
        'account': details,
    }
    return HttpResponse(template.render(context, request))

def update_foreman_account(request):
    account_id = request.session.get('user_id')
    if not account_id:
        messages.error(request, "Account not found.")
        return redirect('foreman_account')

    try:
        account = Account.objects.get(account_id=account_id)
        personnel = Personnel.objects.filter(account_id=account).first()

        if request.method == 'POST':
            username = request.POST.get('username')
            if username: 
                account.username = username
            
            if 'image' in request.FILES:
                image = request.FILES['image']

                if image.size > 15 * 1024 * 1024:
                    messages.error(request, "The uploaded image exceeds the 15MB limit.")
                else:
                    if account.image and account.image.name != 'profile.webp':
                        account.image.delete(save=False)
                    account.image = image

            personnel.first_name = request.POST.get('f_name') or "Not Provided"
            personnel.last_name = request.POST.get('l_name') or "Not Provided"
            personnel.contact = request.POST.get('phone') or '000-000-0000'
            personnel.address = request.POST.get('address') or 'Unknown Address'
            personnel.email = request.POST.get('email') or 'Not Provided'
            personnel.gender = request.POST.get('gender') or 'Not specified'
            personnel.birthdate = request.POST.get('birthdate') or '1998-01-01'

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')

            if new_password and not current_password:
                messages.error(request, "Please enter your current password to set a new one.")
                return redirect('foreman_account')

            if current_password and new_password:
                if check_password(current_password, account.password):
                    account.password = make_password(new_password)
                else:
                    messages.error(request, "Current password is incorrect. Password update failed.")
                    return redirect('foreman_account')
            elif current_password:
                messages.error(request, "New password is required.")
                return redirect('foreman_account')

            account.save()
            personnel.save()

            messages.success(request, "Account updated successfully.")
            return redirect('foreman_account')

    except ObjectDoesNotExist:
        messages.error(request, "Account does not exist.")
        return redirect('foreman_account')

    context = {
        'account': personnel,
    }
    return render(request, 'foreman/foreman_account.html', context)

#FOREMAN MANAGE ACCOUNT--------------------------------------------------------------------------------------------END

#FOREMAN MANAGE PROJECTS--------------------------------------------------------------------------------------------
def foreman_project(request):
    account_id = request.session.get('user_id')
    
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        projects = Project.objects.filter(assigned_foreman=details.personnel_id).distinct().order_by('-date_registered')
    
    template = loader.get_template('foreman/project.html')
    context = {
        'account': details,
        'projects': projects,
        'messages': messages.get_messages(request),
    }
    return HttpResponse(template.render(context, request))

def foreman_search_projects(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '').strip()

        if query:
            projects = Project.objects.filter(project_name__icontains=query)
        else:
            account_id = request.session.get('user_id')
            details = Personnel.objects.filter(account_id=account_id).first()

            projects = Project.objects.filter(tasks__foreman_id=details.personnel_id).distinct().order_by('-date_registered')

        project_list = [{
            'project_name': project.project_name,
            'client': project.client,
            'due_date': project.due_date.strftime('%B %d, %Y') if project.due_date else "N/A",
            'project_percent': project.project_percent,
            'project_status': project.project_status
        } for project in projects]

        return JsonResponse({'projects': project_list}, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def foreman_get_project_details(request, id):
    project = get_object_or_404(Project, project_id=id)
    
    project_manager = project.project_manager_id
    foreman = project.assigned_foreman
    workers = Worker.objects.filter(assigned_tasks__project_id=project.project_id).distinct()
    tasks = TaskSchedule.objects.filter(project_id=project.project_id)
    resources = Resource.objects.filter(project_id=project.project_id)

    data = {
        "project_name": project.project_name,
        "client": project.client,
        "progress": project.project_percent,
        "project_status": project.project_status,
        "budget": project.budget,
        "description": project.description,
        "start_date": project.start_date.strftime("%Y-%m-%d"),
        "due_date": project.due_date.strftime("%Y-%m-%d"),
        "contract_url": project.contract.url if project.contract else "",
        "isFinished": project.isFinished, 
        "finalization_status": project.finalization_status,
        "project_manager": {
            "first_name": project_manager.first_name,
            "last_name": project_manager.last_name,
            "role": "Project Manager"
        },
        "foreman": {
            "first_name": foreman.first_name,
            "last_name": foreman.last_name,
            "role": "Foreman"
        },
        "workers": [
            {
                "first_name": worker.first_name, 
                "last_name": worker.last_name,
                "account": worker.account_id.username,
                "role": "Worker"
            }
            for worker in workers
        ],
        "tasks": [
            {
                "task_name": task.task_name,
                "date_start": task.date_start.strftime("%b. %d, %Y"),
                "deadline": task.deadline.strftime("%b. %d, %Y"),
                "progress": task.progress_id.worker_progress,
                "percent_from_project": task.percent_from_project
            }
            for task in tasks
        ],
        "resources": [
            {
                "resource_id": resource.resource_id,
                "name": resource.name,
                "quantity": resource.quantity,
                "resource_type_display": resource.get_type_display(),
                "resource_type": resource.type,
                "resource_subtype": resource.subtype.name if resource.subtype else None,
                "cost": resource.cost,
                "cost_type": resource.cost_type,
                "added_by": resource.added_by,
            }
            for resource in resources
        ],
    }

    return JsonResponse(data)

def foreman_add_resource(request, id):
    project = get_object_or_404(Project, project_id=id)
    account_id = request.session.get('user_id')
    account = Account.objects.get(account_id=account_id)

    if request.method == 'POST':
        resource_name = request.POST.get('resource_name')
        quantity = request.POST.get('quantity')
        resource_type = request.POST.get('type')
        resource_subtype = request.POST.get('subType')
        cost = request.POST.get('cost')
        cost_type = request.POST.get('cost_type')

        if not all([resource_name, quantity, resource_type, resource_subtype, cost, cost_type]):
            messages.error(request, 'Missing required fields')
            return JsonResponse({'redirect': False, 'message': 'Missing required fields'}, status=400)

        try:
            subtype_obj = get_object_or_404(ResourceSubType, name=resource_subtype, resource_type=resource_type)
            resource = Resource.objects.create(
                project_id=project,
                name=resource_name,
                quantity=quantity,
                type=resource_type,
                subtype=subtype_obj,
                cost=cost,
                cost_type=cost_type,
                added_by=account.role,
            )

            messages.success(request, 'Resource Added Successfully.')
            return JsonResponse({'redirect': True, 'message': 'Resource Added Successfully.'})

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return JsonResponse({'redirect': False, 'message': f'Error: {str(e)}'}, status=400)

    return JsonResponse({'redirect': False, 'message': 'Invalid method.'}, status=400)

def foreman_update_resource(request):
    if request.method == "POST":
        try:
            resource_id = request.POST.get("resource_id")
            name = request.POST.get("updateResource_name")
            quantity = request.POST.get("updateQuantity")
            resource_type = request.POST.get("updateType")
            resource_subtype_name = request.POST.get("updateSubType")
            cost = request.POST.get("updateCost")
            cost_type = request.POST.get("updateCostType")

            if not all([resource_id, name, quantity, resource_type, resource_subtype_name, cost, cost_type]):
                return JsonResponse({
                    "status": "error",
                    "message": "All fields are required."
                }, status=400)

            resource = get_object_or_404(Resource, resource_id=resource_id)
            resource.name = name
            resource.quantity = int(quantity)
            resource.type = resource_type
            resource.cost = int(cost)
            resource.cost_type = cost_type
            
            if resource_subtype_name:
                resource.subtype = get_object_or_404(ResourceSubType, name=resource_subtype_name)
            else:
                resource.subtype = None
            
            resource.save()

            return JsonResponse({
                "status": "success",
                "message": "Resource updated successfully."
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e) or "An error occurred while updating the resource."
            }, status=500)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid request method."
        }, status=405)
    
def foreman_delete_resource(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            resource_id = body.get("resource_id")

            if not resource_id:
                return JsonResponse({"status": "error", "message": "Resource ID is required"}, status=400)

            resource = Resource.objects.get(resource_id=resource_id)
            resource.delete()

            return JsonResponse({"status": "success", "message": "Resource deleted successfully"})

        except Resource.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Resource not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

def mark_project_finished(request, project_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            project = get_object_or_404(Project, pk=project_id)

            # Update isFinished status
            project.isFinished = data.get("isFinished", False)

            # Update finalization_status
            if project.isFinished:
                project.finalization_status = "Finalizing"
            else:
                project.finalization_status = "Pending"

            project.save()

            return JsonResponse({
                "success": True,
                "isFinished": project.isFinished,
                "finalization_status": project.finalization_status
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

#FOREMAN MANAGE PROJECTS--------------------------------------------------------------------------------------------END

#FOREMAN MANAGE TASK SCHEDULES--------------------------------------------------------------------------------------------
def foreman_task_schedule(request):
    account_id = request.session.get('user_id')
    details = None
    filtered_projects = Project.objects.none()

    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        filtered_projects = Project.objects.filter(assigned_foreman=details.personnel_id).distinct()

    foreman_id = details.personnel_id if details else None

    tasks = TaskSchedule.objects.filter(foreman_id=foreman_id)

    assigned_projects = Project.objects.filter(assigned_foreman=foreman_id)


    workers = Worker.objects.filter(availability="available")

    colors = [
        "#FF6F61", "#6A1B9A", "#0277BD", "#43A047", "#FB8C00",
        "#C2185B", "#8E24AA", "#3949AB", "#D81B60", "#009688"
    ]
    num_colors = len(colors)

    tasks_data = [
        {
            "task_id": task.TaskSchedule_id,
            "title": f"{task.task_name} - {task.project_id.project_name}",
            "task_name": task.task_name,
            "start": task.date_start.strftime("%Y-%m-%d"),
            "end": task.deadline.strftime("%Y-%m-%d"),
            "progress": task.progress_id.worker_progress if task.progress_id else 0,
            "backgroundColor": colors[hash(task.TaskSchedule_id) % num_colors],
            "textColor": "#FFFFFF",
            "description": task.description or "No description",
            "percent_from": task.percent_from_project,
            "project_manager_fname": task.project_id.project_manager_id.first_name,
            "project_manager_lname": task.project_id.project_manager_id.last_name,
            "project_id": task.project_id.project_id,
            "workers": [
                {
                    "worker_id": worker.worker_id,
                    "Fname": worker.first_name if worker.first_name else "Not Provided",
                    "Lname": worker.last_name if worker.last_name else "Not Provided",
                    "role": worker.account_id.get_role_display(),
                }
                for worker in task.workers.all()
            ],
            "classNames": ["event-style"],
        }
        for task in tasks
    ]
    tasks_json = json.dumps(tasks_data)

    storage = get_messages(request)
    success_message = None
    for message in storage:
        if message.level_tag == 'success':
            success_message = message.message

    template = loader.get_template('foreman/task_schedule.html')
    context = {
        'account': details,
        'projects': assigned_projects,
        'workers': workers,
        'tasks_json': tasks_json,
        'success_message': success_message,
        'filtered_projects': filtered_projects,
    }
    return HttpResponse(template.render(context, request))

def add_taskSchedule(request):
    if request.method == "POST":
        foreman_id = request.POST.get("foreman_id")
        task_name = request.POST.get("taskName")
        date_start = request.POST.get("taskStart")
        deadline = request.POST.get("taskEnd")
        project_id = request.POST.get("project")
        percent_from_project = request.POST.get("taskPercentage")
        description = request.POST.get("description")
        task_assignees = request.POST.getlist("taskAssignee[]")

        foreman = get_object_or_404(Personnel, account_id=foreman_id)
        project = get_object_or_404(Project, pk=project_id)

        task_schedule = TaskSchedule(
            foreman_id=foreman,
            task_name=task_name,
            date_start=date_start,
            deadline=deadline,
            project_id=project,
            percent_from_project=percent_from_project,
            description=description or "None",
            date_created=timezone.now()
        )
        task_schedule.save()

        workers = Worker.objects.filter(worker_id__in=task_assignees)
        task_schedule.workers.set(workers)

        workers.update(availability="unavailable")

        return redirect("foreman_task_schedule")

    return render(request, "foreman/task_schedule.html", {"projects": Project.objects.all(), "workers": Worker.objects.all()})


def get_project_percentage(request, project_id):
    project = Project.objects.get(pk=project_id)
    total_percentage = sum(task.percent_from_project for task in project.tasks.all())
    return JsonResponse({'total_percentage': total_percentage})

def update_taskSchedule(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        task = get_object_or_404(TaskSchedule, TaskSchedule_id=task_id)

        task.task_name = request.POST.get('detailsTaskName', task.task_name)
        start_date = task.date_start = request.POST.get('detailsStart_date', task.date_start)
        deadline = task.deadline = request.POST.get('detailsDeadline', task.deadline)
        task.description = request.POST.get('detailsDescription', task.description)
        task.estimated_payment = request.POST.get('detailsPay', task.estimated_payment)
        task.percent_from_project = request.POST.get('detailsTaskPercentageFrom', task.percent_from_project)
        worker_ids = request.POST.getlist('detailsTaskAssignee[]')

        removed_worker_ids = request.POST.get('removed_workers', '').split(',')
        removed_worker_ids = [worker_id for worker_id in removed_worker_ids if worker_id.isdigit()]

        if removed_worker_ids:
            removed_workers = Worker.objects.filter(worker_id__in=removed_worker_ids)
            removed_workers.update(availability="available")
            task.workers.remove(*removed_worker_ids)

        if worker_ids:
            new_workers = Worker.objects.filter(worker_id__in=worker_ids)
            new_workers.update(availability="unavailable")
            task.workers.add(*worker_ids)

        if deadline < start_date:
            messages.error(request, 'Deadline cannot be before the start date.')
            return redirect('foreman_task_schedule')

        task.save()

        messages.success(request, 'Task information updated successfully!')
        return redirect('foreman_task_schedule')

    workers = Worker.objects.all()
    context = {
        'task': task,
        'workers': workers
    }
    return render(request, 'update_task.html', context)


#FOREMAN MANAGE TASK SCHEDULES--------------------------------------------------------------------------------------------END

#PROJECT MANAGER VIEWS--------------------------------------------------------------------------------------------------------
def project_manager_home(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        assigned_projects = Project.objects.filter(
            project_manager_id=details
        ).exclude(finalization_status="Completed", project_status="Finished")

        workers = Worker.objects.filter(
            assigned_tasks__project_id__in=assigned_projects.values_list('project_id', flat=True)
        ).distinct()

        resources = Resource.objects.filter(
            project_id__in=assigned_projects.values_list('project_id', flat=True)
        )
    else:
        details = None
        assigned_projects = []
        workers = []
        resources = []

    template = loader.get_template('project_manager/home.html')
    context = {
        'account': details,
        'assigned_projects': assigned_projects,
        'workers': workers,
        'resources': resources,
    }
    return HttpResponse(template.render(context, request))


#PROJECT MANAGER MANAGE ACCOUNT--------------------------------------------------------------------------------------------
def PM_account(request):
    account_id = request.session.get('user_id')
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()
    
    template = loader.get_template('project_manager/account.html')
    context = {
        'account': details,
    }
    return HttpResponse(template.render(context, request))

def update_PM_account(request):
    account_id = request.session.get('user_id')
    if not account_id:
        messages.error(request, "Account not found.")
        return redirect('PM_account')

    try:
        account = Account.objects.get(account_id=account_id)
        personnel = Personnel.objects.filter(account_id=account).first()

        if request.method == 'POST':
            username = request.POST.get('username')
            if username: 
                account.username = username
            
            if 'image' in request.FILES:
                image = request.FILES['image']

                if image.size > 15 * 1024 * 1024:
                    messages.error(request, "The uploaded image exceeds the 15MB limit.")
                else:
                    if account.image and account.image.name != 'profile.webp':
                        account.image.delete(save=False)
                    account.image = image

            personnel.first_name = request.POST.get('f_name') or "Not Provided"
            personnel.last_name = request.POST.get('l_name') or "Not Provided"
            personnel.contact = request.POST.get('phone') or '000-000-0000'
            personnel.address = request.POST.get('address') or 'Unknown Address'
            personnel.email = request.POST.get('email') or 'Not Provided'
            personnel.gender = request.POST.get('gender') or 'Not specified'
            personnel.birthdate = request.POST.get('birthdate') or '1998-01-01'

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')

            if new_password and not current_password:
                messages.error(request, "Please enter your current password to set a new one.")
                return redirect('PM_account')

            if current_password and new_password:
                if check_password(current_password, account.password):
                    account.password = make_password(new_password)
                else:
                    messages.error(request, "Current password is incorrect. Password update failed.")
                    return redirect('PM_account')
            elif current_password:
                messages.error(request, "New password is required.")
                return redirect('PM_account')

            account.save()
            personnel.save()

            messages.success(request, "Account updated successfully.")
            return redirect('PM_account')

    except ObjectDoesNotExist:
        messages.error(request, "Account does not exist.")
        return redirect('PM_account')

    context = {
        'account': personnel,
    }
    return render(request, 'foreman/PM_account.html', context)

#PROJECT MANAGER MANAGE ACCOUNT--------------------------------------------------------------------------------------------END

#PROJECT MANAGER MANAGE TEAM--------------------------------------------------------------------------------------------
def PM_manageTeam(request):
    account_id = request.session.get('user_id')
    
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()
        projects = Project.objects.filter(project_manager_id=details).order_by('-date_registered')
        
        project_data = []
        for project in projects:
            foreman_info = TaskSchedule.objects.filter(project_id=project).values(
                'foreman_id__account_id__image', 
                'foreman_id__account_id__username',
                'foreman_id__first_name', 
                'foreman_id__last_name',
                'foreman_id__email'
            ).first() 

            workers = Worker.objects.filter(assigned_tasks__project_id=project).distinct()

            if foreman_info:
                foreman_image_url = default_storage.url(foreman_info['foreman_id__account_id__image'])
                foreman = {
                    "foreman_image": foreman_image_url, 
                    "first_name": foreman_info['foreman_id__first_name'], 
                    "last_name": foreman_info['foreman_id__last_name'],
                    "role": "Foreman",
                    "email": foreman_info.get('foreman_id__email'),
                    "account": foreman_info['foreman_id__account_id__username'],
                }
            else:
                foreman = None
            
            worker_info = [
                {
                    "worker_id": worker.worker_id,
                    "worker_image": worker.account_id.image,
                    "first_name": worker.first_name,
                    "last_name": worker.last_name,
                    "account": worker.account_id.username,
                    "role": "Worker",
                    "contact": worker.contact,  
                } for worker in workers
            ]
            
            project_data.append({
                "project_id": project.project_id,
                "project_name": project.project_name,
                "client": project.client,
                "description": project.description,
                "foreman": foreman,
                "workers": worker_info,
            })
    else:
        details = None
        project_data = []
    
    template = loader.get_template('project_manager/team.html')
    context = {
        'account': details,
        'project_data': project_data,
    }
    return HttpResponse(template.render(context, request))

def fetch_worker_details(request, project_id, worker_id):
    try:
        project = get_object_or_404(Project, project_id=project_id) 
        worker = get_object_or_404(Worker, worker_id=worker_id) 

        project_tasks = TaskSchedule.objects.filter(project_id=project)
        worker_tasks = project_tasks.filter(workers=worker)

        tasks_data = [
            {
                "task_name": task.task_name,
                "task_status": task.task_status,
                "start_date": task.date_start.strftime("%b. %d, %Y"),
                "deadline": task.deadline.strftime("%b. %d, %Y"),
            }
            for task in worker_tasks
        ]

        attendances = Attendance.objects.filter(
            worker_id=worker,
            project_id=project
        ).distinct().order_by('-recorded_at')

        attendance_data = [
            {
                "time_in": att.time_in.strftime("%I:%M %p") if att.time_in else "---",
                "time_out": att.time_out.strftime("%I:%M %p") if att.time_out else "---",
                "date": att.recorded_at.strftime("%b. %d, %Y"),
                "time_in_status": att.timeIn_status if att.timeIn_status else "Unknown",
            }
            for att in attendances
        ]

        payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()
        payroll_data = {
            "total_amount": payroll.total_amount if payroll else 0,
        }

        data = {
            "worker": {
                "first_name": worker.first_name,
                "last_name": worker.last_name,
                "account": worker.account_id.username,
                "role": "Worker",
                "address": worker.address,
                "contact": worker.contact,
                "attendance": attendance_data,
                "tasks": tasks_data, 
                "payroll": payroll_data,
            },
            "project": {
                "name": project.project_name,
                "client": project.client,
                "finalization_status": project.finalization_status,
                "isFinished": project.isFinished,
            },
        }

        return JsonResponse(data)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

def add_bonus(request, project_id, worker_id):
    if request.method == "POST":
        bonus_name = request.POST.get("payrollTotalAmountBonus")
        bonus_amount = request.POST.get("payrollBonus")

        if not bonus_name or not bonus_amount:
            return JsonResponse({"success": False, "message": "All fields are required"}, status=400)

        try:
            worker = get_object_or_404(Worker, worker_id=worker_id)
            project = get_object_or_404(Project, project_id=project_id)
            payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()

            if not payroll:
                return JsonResponse({"success": False, "message": "Payroll record not found"}, status=404)

            bonus = Payroll_Bonus.objects.create(
                bonus_name=bonus_name,
                bonus_amount=int(bonus_amount),
                payroll_id=payroll
            )

            payroll.total_amount += int(bonus_amount)
            payroll.save()

            return JsonResponse({"success": True, "message": "Bonus added successfully", "new_total": payroll.total_amount})
        
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

def add_deduction(request, project_id, worker_id):
    if request.method == "POST":
        deduction_name = request.POST.get("payrollTotalAmountDeduction")
        deduction_amount = request.POST.get("payrollDeduction")

        if not deduction_name or not deduction_amount:
            return JsonResponse({"success": False, "message": "All fields are required"}, status=400)

        try:
            worker = get_object_or_404(Worker, worker_id=worker_id)
            project = get_object_or_404(Project, project_id=project_id)
            payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()

            if not payroll:
                return JsonResponse({"success": False, "message": "Payroll record not found"}, status=404)

            # Create and save deduction record
            deduction = Payroll_Deduction.objects.create(
                deduction_name=deduction_name,
                deduction_amount=int(deduction_amount),
                payroll_id=payroll
            )

            # Update the total payroll amount
            payroll.total_amount -= int(deduction_amount)
            payroll.save()

            return JsonResponse({"success": True, "message": "Deduction applied successfully", "new_total": payroll.total_amount})
        
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

"""
def fetch_payroll_details(request, worker_id, project_id):
    try:
        worker = get_object_or_404(Worker, worker_id=worker_id)
        project = get_object_or_404(Project, project_id=project_id)


        payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()

        if payroll:
            payroll_data = {
                "total_amount": payroll.total_amount,
            }
        else:
            payroll_data = {
                "total_amount": 0,
            }

        return JsonResponse(payroll_data)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

def update_payroll(request, worker_id, project_id):
    if request.method == "POST":
        worker = get_object_or_404(Worker, worker_id=worker_id)
        project = get_object_or_404(Project, project_id=project_id)

        try:
            bonus = request.POST.get('updatePayrollBonus', None)
            deductions = request.POST.get('updatePayrollDeductions', None)

            bonus = float(bonus) if bonus else None
            deductions = float(deductions) if deductions else None

            payroll = Payroll.objects.filter(worker_id=worker, project_id=project).first()
            
            if payroll:
                if bonus is not None:
                    payroll.bonus = bonus
                if deductions is not None:
                    payroll.deductions = deductions

                payroll.total_amount = payroll.total_amount + (bonus or 0) - (deductions or 0)
                payroll.save()
            else:
                Payroll.objects.create(
                    worker_id=worker,
                    project_id=project,
                    bonus=bonus or 0,
                    deductions=deductions or 0,
                    total_amount=(bonus or 0) - (deductions or 0)
                )

            return JsonResponse({
                "message": "Payroll updated successfully",
                "total_amount": payroll.total_amount,
                "bonus": payroll.bonus,
                "deductions": payroll.deductions
            })
        except ValueError as e:
            return JsonResponse({"error": "Invalid input: Bonus and Deductions must be numbers."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

"""
def search_projects(request):
    query = request.GET.get('q', '')
    account_id = request.session.get('user_id')
    
    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()
        projects = Project.objects.filter(
            project_manager_id=details, 
            project_name__icontains=query
        ).order_by('-date_registered')

        if projects.exists():
            project_data = []
            for project in projects:
                foreman_info = TaskSchedule.objects.filter(project_id=project).values(
                    'foreman_id__account_id__image', 
                    'foreman_id__first_name', 
                    'foreman_id__last_name',
                    'foreman_id__email'
                ).first()

                workers = Worker.objects.filter(assigned_tasks__project_id=project).distinct()

                if foreman_info:
                    foreman_image_url = default_storage.url(foreman_info['foreman_id__account_id__image'])
                    foreman = {
                        "foreman_image": foreman_image_url, 
                        "first_name": foreman_info['foreman_id__first_name'], 
                        "last_name": foreman_info['foreman_id__last_name'],
                        "role": "Foreman",
                        "email": foreman_info.get('foreman_id__email'),
                    }
                else:
                    foreman = None
                
                worker_info = [
                    {
                        "worker_image": worker.account_id.image,
                        "first_name": worker.first_name,
                        "last_name": worker.last_name,
                        "role": "Worker",
                        "contact": worker.contact,  
                    } for worker in workers
                ]

                project_data.append({
                    "project_name": project.project_name,
                    "client": project.client,
                    "description": project.description,
                    "foreman": foreman,
                    "workers": worker_info,
                })

            html = render_to_string('project_manager/components/team_box.html', {'project_data': project_data})
            return JsonResponse({'html': html, 'empty': False})
        else:
            no_results_html = "<p>No projects found matching your search.</p>"
            return JsonResponse({'html': no_results_html, 'empty': True})
    
    return JsonResponse({'html': "<p>No data available.</p>", 'empty': True})

#PROJECT MANAGER MANAGE TEAM--------------------------------------------------------------------------------------------END

#PROJECT MANAGER MANAGE PROJECTS--------------------------------------------------------------------------------------------
def PM_manageProject(request):
    account_id = request.session.get('user_id')

    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        if details:
            projects = Project.objects.filter(project_manager_id=details).order_by('-date_registered')

    template = loader.get_template('project_manager/projects.html')
    context = {
        'account': details,
        'projects': projects,
    }
    return HttpResponse(template.render(context, request))

def PM_search_projects(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'query' in request.GET:
        query = request.GET.get('query', '').strip()
        account_id = request.session.get('user_id')

        personnel = Personnel.objects.filter(account_id=account_id).first()
        if not personnel:
            return JsonResponse({"error": "Personnel not found"}, status=404)

        projects = Project.objects.filter(
            project_manager_id=personnel,
            project_name__icontains=query
        )

        project_data = [
            {
                "name": project.project_name,
                "client": project.client,
                "progress": project.project_percent,
                "status": project.project_status,
            }
            for project in projects
        ]

        return JsonResponse({"projects": project_data}, safe=False)
    return JsonResponse({"error": "Invalid request"}, status=400)

def PM_edit_project(request, id):
    account_id = request.session.get('user_id')
    project = get_object_or_404(Project, project_id=id)

    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

    unassigned_foremen = Personnel.objects.filter(
        account_id__role="FM",
        availability="available"
    ).exclude(
        projects_as_manager__isnull=False
    ).distinct()

    resources = Resource.objects.filter(project_id=project)

    template = loader.get_template('project_manager/edit_project.html')
    context = {
        'account': details,
        'project': project,
        'foremen': unassigned_foremen,
        'resources': resources,
    }
    return HttpResponse(template.render(context, request))


def PM_update_project(request, id):
    project = get_object_or_404(Project, project_id=id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        foreman_id = request.POST.get('foreman')
        timeframe_image = request.FILES.get('timeframe')

        project.project_status = status

        if foreman_id:
            foreman = Personnel.objects.get(personnel_id=foreman_id)
            project.assigned_foreman = foreman

            foreman.availability = 'unavailable'
            foreman.save()
        
        if timeframe_image:
            if not timeframe_image.name.endswith(('.png', '.jpeg', '.jpg')):
                 return JsonResponse({'success': False, 'message': 'Invalid file format. Please upload a PNG or JPEG image.'})  
            
            project.timeframe = timeframe_image

        project.save()

        return JsonResponse({'success': True, 'message': 'Project updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def PM_finalize_project(request, id):
    project = get_object_or_404(Project, project_id=id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get("action", "")

            if action == "finalize":
                project.project_status = "Finished"
                project.finalization_status = "Completed"
                project.isFinished = True

                # Fetch all workers assigned to tasks in this project
                assigned_workers = Worker.objects.filter(assigned_tasks__project_id=project).distinct()

                # Update availability of workers
                assigned_workers.update(availability="available")

                # Update availability of project manager and foreman if they exist
                if project.project_manager_id:
                    project.project_manager_id.availability = "available"
                    project.project_manager_id.save()
                
                if project.assigned_foreman:
                    project.assigned_foreman.availability = "available"
                    project.assigned_foreman.save()

            elif action == "undo":
                project.project_status = "Ongoing"
                project.finalization_status = "Finalizing"
                project.isFinished = False

                # Restore previous availability for project manager and foreman
                if project.project_manager_id:
                    project.project_manager_id.availability = "unavailable"
                    project.project_manager_id.save()
                
                if project.assigned_foreman:
                    project.assigned_foreman.availability = "unavailable"
                    project.assigned_foreman.save()

            project.save()

            return JsonResponse({
                'success': True,
                'message': 'Project successfully updated.',
                'finalization_status': project.finalization_status,
                'isFinished': project.isFinished
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

#PROJECT MANAGER MANAGE PROJECTS--------------------------------------------------------------------------------------------END

#PROJECT MANAGER MANAGE RESOURCES--------------------------------------------------------------------------------------------

def PM_manageResources(request):
    account_id = request.session.get('user_id')

    projects = []
    details = None

    if account_id:
        details = Personnel.objects.filter(account_id=account_id).first()

        if details:
            projects = Project.objects.filter(project_manager_id=details)

            for project in projects:
                total_cost = 0
                for supply in project.supplies.all():
                    if supply.cost_type == "Per Unit":
                        total_cost += supply.cost * supply.quantity
                    else:
                        total_cost += supply.cost

                project.total_cost = total_cost
                project.remaining_budget = project.budget - total_cost

    template = loader.get_template('project_manager/resources.html')
    context = {
        'account': details,
        'projects': projects,
    }
    return HttpResponse(template.render(context, request))

def PM_add_resource(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    account_id = request.session.get('user_id')
    account = Account.objects.get(account_id=account_id)

    if request.method == 'POST':
        resource_name = request.POST.get('resource_name')
        quantity = request.POST.get('quantity')
        resource_type = request.POST.get('type')
        resource_subtype = request.POST.get('subType')
        cost = request.POST.get('cost')
        cost_type = request.POST.get('cost_type')

        if resource_name and quantity and resource_type and cost and cost_type:
            try:
                resource_subtype_obj = ResourceSubType.objects.get(
                    name=resource_subtype, 
                    resource_type=resource_type
                )
                print(resource_subtype_obj.id)
                resource = Resource.objects.create(
                    project_id=project,
                    name=resource_name,
                    quantity=int(quantity),
                    type=resource_type,
                    subtype=resource_subtype_obj,
                    cost=int(cost),
                    cost_type=cost_type,
                    added_by=account.role
                )
                response = {
                    'success': True,
                    'message': f'Resource "{resource_name}" added successfully!',
                }
            except Exception as e:
                response = {
                    'success': False,
                    'message': 'An error occurred while adding the resource.',
                    'error': str(e),
                }
                print(str(e))
        else:
            response = {
                'success': False,
                'message': 'Please fill out all fields correctly.',
            }

        return JsonResponse(response)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def PM_update_resource(request, resource_id):
    if request.method == 'POST':
        try:
            resource_name = request.POST.get('updateResource_name')
            quantity = request.POST.get('updateQuantity')
            resource_type = request.POST.get('updateType')
            resource_subtype_name = request.POST.get('updateSubType')
            cost = request.POST.get('updateCost')
            cost_type = request.POST.get('updateCostType')

            resource = get_object_or_404(Resource, pk=resource_id)
            resource_subtype = get_object_or_404(ResourceSubType, name=resource_subtype_name)

            resource.name = resource_name
            resource.quantity = quantity
            resource.type = resource_type
            resource.subtype = resource_subtype
            resource.cost = cost
            resource.cost_type = cost_type

            resource.save()

            return JsonResponse({
                'success': True,
                'message': 'Resource updated successfully'
            })

        except Exception as e:
            print(f"Error updating resource: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error updating resource'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })

def PM_delete_resource(request, resource_id):
    if request.method == 'POST':
        try:
            resource = get_object_or_404(Resource, resource_id=resource_id)
            resource_name = resource.name 
            resource.delete()
            return JsonResponse({'success': True, 'message': f'Resource "{resource_name}" deleted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'An error occurred while deleting the resource.', 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

#PROJECT MANAGER MANAGE RESOURCES--------------------------------------------------------------------------------------------END


#END PROJECT MANAGER VIEWS--------------------------------------------------------------------------------------------------------