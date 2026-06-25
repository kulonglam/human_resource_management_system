import csv
import io
from datetime import datetime

from django.http import HttpResponse
from openpyxl import Workbook


def _filename(prefix, ext):
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{stamp}.{ext}'


def export_rows_csv(rows, columns, filename_prefix='report'):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[c['key'] for c in columns], extrasaction='ignore')
    writer.writeheader()
    for row in rows or []:
        writer.writerow({col['key']: row.get(col['key'], '') for col in columns})
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{_filename(filename_prefix, "csv")}"'
    return response


def export_rows_xlsx(rows, columns, filename_prefix='report', sheet_title='Report'):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    headers = [c['label'] for c in columns]
    keys = [c['key'] for c in columns]
    ws.append(headers)
    for row in rows or []:
        ws.append([row.get(key, '') for key in keys])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_filename(filename_prefix, "xlsx")}"'
    return response


def export_key_value_xlsx(data_dict, filename_prefix='report', sheet_title='Summary'):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    ws.append(['Metric', 'Value'])
    for key, value in data_dict.items():
        ws.append([key, value])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_filename(filename_prefix, "xlsx")}"'
    return response
