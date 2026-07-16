from .base import HRAPITestCase


class SavedReportTests(HRAPITestCase):
    def test_manager_saves_and_runs_report(self):
        self.login('manager', 'ManagerPass123!')
        create = self.client.post(
            '/api/v1/saved-reports/',
            {
                'name': 'July attendance',
                'report_type': 'attendance',
                'filters': {'date_range': 'this_month'},
                'is_public': False,
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        report_id = create.data['id']

        run = self.client.post(f'/api/v1/saved-reports/{report_id}/run/', {}, format='json')
        self.assertEqual(run.status_code, 200)
        self.assertEqual(run.data['report_type'], 'attendance')

    def test_employee_cannot_create_saved_report(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.post(
            '/api/v1/saved-reports/',
            {'name': 'Test', 'report_type': 'leave', 'filters': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 403)
