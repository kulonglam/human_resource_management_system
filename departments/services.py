from django.db.models import Count

from departments.models import Department
from employees.models import Employee


def build_org_chart(organization_id=None):
    dept_qs = Department.objects.select_related('parent').all().order_by('name')
    emp_qs = Employee.objects.filter(is_active=True)
    if organization_id:
        dept_qs = dept_qs.filter(organization_id=organization_id)
        emp_qs = emp_qs.filter(organization_id=organization_id)
    departments = list(dept_qs)
    employee_counts = {
        row['department_id']: row['count']
        for row in emp_qs.filter(department_id__isnull=False)
        .values('department_id')
        .annotate(count=Count('id'))
    }

    nodes = {
        dept.id: {
            'id': dept.id,
            'name': dept.name,
            'location': dept.location,
            'manager_name': dept.manager_name,
            'manager_contact': dept.manager_contact,
            'parent_id': dept.parent_id,
            'employee_count': employee_counts.get(dept.id, 0),
            'children': [],
        }
        for dept in departments
    }

    roots = []
    for dept in departments:
        node = nodes[dept.id]
        if dept.parent_id and dept.parent_id in nodes:
            nodes[dept.parent_id]['children'].append(node)
        else:
            roots.append(node)

    unassigned = emp_qs.filter(department__isnull=True).count()
    return {
        'roots': roots,
        'total_departments': len(departments),
        'unassigned_employees': unassigned,
    }
