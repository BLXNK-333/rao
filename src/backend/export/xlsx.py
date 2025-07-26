from typing import List, Union, Any
import datetime
import calendar
from pathlib import Path

import xlsxwriter


def _get_russian_period_text(month: int, year: int) -> str:
    month_names = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    from_day = 1
    to_day = calendar.monthrange(year, month)[1]
    month_name = month_names[month]

    return f"с {from_day} {month_name} {year} по {to_day} {month_name} {year}"


def _calculate_total_play_time(data: List[List[Any]]) -> str:
    """
    Calculates the total play time from a list of rows,
    where the 6th column (index 5) contains datetime.time values.

    :param data: List of rows, each containing a datetime.time object at index 5
    :return: String in format 'X час. Y мин. Z сек.'
    """

    def time_to_timedelta(t: datetime.time) -> datetime.timedelta:
        return datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    total_duration = sum(
        (time_to_timedelta(i[5]) for i in data),
        start=datetime.timedelta()
    )

    total_seconds = int(total_duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    result_string = f"{hours} час. {minutes} мин. {seconds} сек."
    return result_string


def generate_xlsx_month_report(
    month: int,
    year: int,
    data: List[List[str]],
    save_path: Union[str, Path],
    table_headers: List[str]
):
    save_path = Path(save_path)
    workbook = xlsxwriter.Workbook(save_path)
    worksheet = workbook.add_worksheet("Отчет")

    # ── column widths ────────────────────────────────────────────────
    col_widths = [48.71, 47.14, 44.14, 5.71, 44.0, 65.71]
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)

    # ── formats ──────────────────────────────────────────────────────
    f_header = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 14, 'bold': True,
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True
    })

    f_subheader = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 12, 'bold': True,
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
    })

    f_body = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 12,
        'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })

    f_body_center = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 12,
        'valign': 'vcenter', 'text_wrap': True, 'border': 1,
        'align': 'center'
    })

    f_footer = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 12,
        'valign': 'vcenter', 'text_wrap': True
    })

    f_sign = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 14,
        'bold': True, 'align': 'center', 'valign': 'bottom'
    })

    f_sign_underline = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 14,
        'bold': True, 'underline': True, 'align': 'center', 'valign': 'bottom'
    })

    f_explain = workbook.add_format({
        'font_name': 'Times New Roman', 'font_size': 8,
        'align': 'center', 'valign': 'top'
    })

    # ── header row ───────────────────────────────────────────────────
    header_text = (
        f"Отчет  об использованных фонограммах за период {_get_russian_period_text(month, year)} "
        "в эфире радиоканала « Радио России Астрахань » - город федерального, регионального, "
        "республиканского либо краевого значения осуществляющего трансляцию"
    )
    worksheet.merge_range("A1:F1", header_text, f_header)
    worksheet.set_row(0, 52.5)

    # ── table headers ────────────────────────────────────────────────
    for col, title in enumerate(table_headers):
        worksheet.write(1, col, title, f_subheader)
    worksheet.set_row(1, 61.5)

    # ── table data ───────────────────────────────────────────────────
    for row_idx, row_data in enumerate(data, start=2):
        worksheet.set_row(row_idx, 31.5)
        for col_idx, val in enumerate(row_data):
            fmt = f_body_center if col_idx == 3 else f_body
            worksheet.write(row_idx, col_idx, val, fmt)

    # ── empty row after table ────────────────────────────────────────
    footer_start = len(data) + 2
    worksheet.set_row(footer_start, 31.5)

    # ── footer lines ─────────────────────────────────────────────────
    footer_lines = [
        "* ВГТРК ГТРК «Культура» (правопреемник Государственного дома радиовещания и звукозаписи ГДРЗ)",
        "* Self - Release –  творческая продукция исполнителя, доступная для продаж или распространения"
    ]
    for i, line in enumerate(footer_lines):
        worksheet.merge_range(footer_start + 1 + i, 0, footer_start + 1 + i, 5, line, f_footer)
        worksheet.set_row(footer_start + 1 + i, 21)

    # ── 2 empty rows ────────────────────────────────────────────────
    worksheet.set_row(footer_start + 3, 21)
    worksheet.set_row(footer_start + 4, 21)

    # ── signature row ────────────────────────────────────────────────
    sign_row = footer_start + 5
    worksheet.merge_range(sign_row, 0, sign_row, 2, "М.П.    _________________________   ", f_sign)
    worksheet.merge_range(sign_row, 3, sign_row, 5, "Директор ГТРК" + " " * 42, f_sign_underline)
    worksheet.set_row(sign_row, 21)

    # ── signature explain ────────────────────────────────────────────
    explain_row = sign_row + 1
    worksheet.merge_range(explain_row, 0, explain_row, 2, "(подпись)", f_explain)
    worksheet.merge_range(explain_row, 3, explain_row, 5, "(должность,  ФИО руководителя)", f_explain)
    worksheet.set_row(explain_row, 21)

    workbook.close()



def _get_quarter_period_string(quarter: int, year: int) -> str:
    start_month = 3 * (quarter - 1) + 1
    end_month = start_month + 2
    start_date = datetime.date(year, start_month, 1)
    end_date = datetime.date(year, end_month, 1).replace(day=28) + datetime.timedelta(days=4)
    end_date = end_date - datetime.timedelta(days=end_date.day)
    return f"{start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')} года"


def generate_xlsx_quarter_report(
    quarter: int,
    year: int,
    data: List[List],
    save_path: Union[str, Path],
    table_headers: List[str]
):

    save_path = Path(save_path)
    workbook = xlsxwriter.Workbook(save_path)
    worksheet = workbook.add_worksheet("Отчет для РАО (ТВ Радио).rdl"[:31])  # Max 31 chars

    # ── ширины колонок ────────────────────────────────────────────────
    col_widths = [18.86, 17.29, 34.14, 40, 41.43, 10, 5.71, 8.43, 11.29, 43.14]
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)

    # ── стили ─────────────────────────────────────────────────────────
    base_font = {'font_name': 'Tahoma', 'font_size': 10, 'border': 1, 'valign': 'top'}
    fmt_datetime = workbook.add_format(
        {**base_font, 'align': 'right', 'num_format': 'dd.mm.yyyy h:mm'})
    fmt_duration = workbook.add_format(
        {**base_font, 'align': 'center', 'num_format': 'm:ss'})

    formats = [
        workbook.add_format({**base_font, 'align': 'left'}),  # 0
        fmt_datetime,  # 1 ← дата+время
        workbook.add_format({**base_font, 'align': 'left'}),  # 2
        workbook.add_format({**base_font, 'align': 'left'}),  # 3
        workbook.add_format({**base_font, 'align': 'left'}),  # 4
        fmt_duration,  # 5 ← продолжительность
        workbook.add_format({**base_font, 'align': 'center'}),  # 6
        fmt_duration,  # 7 ← продолжительность
        workbook.add_format({**base_font, 'align': 'center'}),  # 8
        workbook.add_format({**base_font, 'align': 'left'}),  # 9
    ]

    fmt_title = workbook.add_format({
        'font_name': 'Arial', 'font_size': 10, 'bold': True,
        'align': 'center', 'valign': 'top'
    })
    fmt_subtitle_bold = workbook.add_format({
        'font_name': 'Arial', 'font_size': 10, 'bold': True, 'valign': 'vcenter'
    })
    fmt_subtitle_normal = workbook.add_format({
        'font_name': 'Arial', 'font_size': 10, 'valign': 'vcenter'
    })
    fmt_header = workbook.add_format({
        'font_name': 'Arial', 'font_size': 9, 'bold': True,
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })

    # ── строка 1: заголовок ───────────────────────────────────────────
    worksheet.merge_range("A1:J1", "ОТЧЕТ ОБ ИСПОЛЬЗОВАНИИ ПРОИЗВЕДЕНИЙ", fmt_title)
    worksheet.set_row(0, 22.2)

    # ── строки 2–5: подзаголовки ──────────────────────────────────────
    subtitle_lines = [
        [fmt_subtitle_bold, 'ВГТРК/ГТРК: ', fmt_subtitle_normal, '"Лотос"'],
        [fmt_subtitle_bold, 'Наименование СМИ: ', fmt_subtitle_normal, '"Радио России - Астрахань"'],
        [fmt_subtitle_bold, 'Отчетный период: ', fmt_subtitle_normal, _get_quarter_period_string(quarter, year)],
        [fmt_subtitle_bold, 'Основной отчет ', fmt_subtitle_normal, '/ отчет об анонсах (нужное выделить / подчеркнуть)']
    ]
    for i, rich_line in enumerate(subtitle_lines, start=1):
        worksheet.merge_range(i, 0, i, 9, '', fmt_subtitle_normal)
        worksheet.write_rich_string(i, 0, *rich_line, fmt_subtitle_normal)
        worksheet.set_row(i, 12.7)

    # ── строки 6–7: пустые строки ────────────────────────────────────
    worksheet.set_row(5, 16.0)
    worksheet.set_row(6, 16.0)

    # ── строка 8: заголовки таблицы ───────────────────────────────────
    for col, title in enumerate(table_headers):
        worksheet.write(7, col, title, fmt_header)
    worksheet.set_row(7, 60.0)

    # ── строки данных ────────────────────────────────────────────────
    for row_idx, row in enumerate(data, start=8):
        worksheet.set_row(row_idx, 21.0)
        for col_idx, val in enumerate(row):
            # Пропуск None
            if val is None:
                worksheet.write(row_idx, col_idx, '', formats[col_idx])
                continue

            # Специальная обработка
            if col_idx == 0:
                # Столбец с кавычками
                escaped = str(val).replace('"', '""')
                val_str = f'"{escaped}"'
                worksheet.write(row_idx, col_idx, val_str, formats[col_idx])
            elif col_idx == 1 and isinstance(val, (datetime.datetime, datetime.date)):
                dt = val if isinstance(val,
                                       datetime.datetime) else datetime.datetime.combine(
                    val, datetime.time())
                worksheet.write_datetime(row_idx, col_idx, dt, formats[col_idx])
            elif col_idx in (5, 7):
                if isinstance(val, datetime.timedelta):
                    t = val
                elif isinstance(val, datetime.time):
                    t = datetime.timedelta(minutes=val.minute, seconds=val.second)
                elif isinstance(val, (int, float)):
                    t = datetime.timedelta(seconds=int(val))
                elif isinstance(val, str) and val.strip().isdigit():
                    t = datetime.timedelta(seconds=int(val.strip()))
                else:
                    worksheet.write(row_idx, col_idx, str(val), formats[col_idx])
                    continue
                worksheet.write_datetime(row_idx, col_idx, t, formats[col_idx])
            else:
                worksheet.write(row_idx, col_idx, val, formats[col_idx])

    # ── Итог в конец ───────────────────────────────────────────────
    final_row = 8 + len(data)

    # 2 пустые строки
    worksheet.set_row(final_row, 14.25)
    worksheet.set_row(final_row + 1, 14.25)

    # "Итого общий хронометраж ..."
    fmt_footer_text = workbook.add_format({
        'font_name': 'Arial', 'font_size': 10,
        'valign': 'top'
    })

    total_play_time = _calculate_total_play_time(data)
    worksheet.write(
        final_row + 2, 0,
        f"Итого общий хронометраж Произведений за Отчетный период: {total_play_time}",
        fmt_footer_text
    )

    # Пустая строка
    worksheet.set_row(final_row + 3, 14.25)

    # "______ / ______ / __________ г."
    worksheet.write(final_row + 4, 0, "______ / ______ / __________ г.", fmt_footer_text)

    workbook.close()
