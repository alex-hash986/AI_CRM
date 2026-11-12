"""Generate the portfolio technical specification with python-docx."""

import argparse
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
INK = "20243A"
ACCENT = "49328C"


def fill(cell, color):
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shading)


def table(document, headers, rows, widths):
    grid = document.add_table(rows=1, cols=len(headers))
    grid.autofit = False
    for column, width in zip(grid.columns, widths):
        column.width = Inches(width)
    header = OxmlElement("w:tblHeader")
    grid.rows[0]._tr.get_or_add_trPr().append(header)
    for index, values in enumerate([headers, *rows]):
        row = grid.rows[0] if index == 0 else grid.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell, text, width in zip(row.cells, values, widths):
            cell.width = Inches(width)
            fill(cell, ACCENT if index == 0 else ("F0EDF8" if index % 2 else "F8F7FB"))
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_before = Pt(5)
            paragraph.paragraph_format.space_after = Pt(5)
            run = paragraph.add_run(text)
            run.font.size = Pt(10)
            if index == 0:
                run.bold = True
                run.font.color.rgb = RGBColor.from_string("FFFFFF")
    document.add_paragraph().paragraph_format.space_after = Pt(0)


def callout(document, label, message):
    cell = document.add_table(rows=1, cols=1).cell(0, 0)
    fill(cell, "EEE9FA")
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph.add_run(label + "\n").bold = True
    paragraph.add_run(message)


def configure(document):
    section = document.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = section.right_margin = Inches(0.8)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.75)

    for name, size, color in (
        ("Normal", 11, INK), ("Title", 32, "000000"),
        ("Subtitle", 15, ACCENT), ("Heading 1", 18, ACCENT),
        ("Heading 2", 12, INK), ("List Bullet", 11, INK),
    ):
        style = document.styles[name]
        style.font.name = "Liberation Sans"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
    normal = document.styles["Normal"].paragraph_format
    normal.space_after = Pt(7)
    normal.line_spacing = 1.12

    title_properties = document.styles["Title"].element.get_or_add_pPr()
    for border in title_properties.findall(qn("w:pBdr")):
        title_properties.remove(border)

    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run("AI Sales CRM   /   ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    document.core_properties.title = "Техническое задание AI Sales CRM"
    document.core_properties.author = "AI Sales CRM"


def build_document():
    doc = Document()
    configure(doc)
    doc.add_paragraph("Техническое задание", "Title")
    doc.add_paragraph("AI Sales CRM", "Subtitle")
    doc.add_paragraph("Версия 1.0  ·  12 ноября 2026 г.")

    doc.add_heading("1  Название и резюме проекта", 1)
    doc.add_paragraph(
        "AI Sales CRM — интеллектуальная система управления продажами и предиктивной "
        "аналитики воронки. Она объединяет сделки, историю контактов и прогноз выручки. "
        "Менеджер видит риски и следующее действие, руководитель — состояние воронки "
        "и ожидаемую выручку по стадиям."
    )
    doc.add_heading("2  Целевая аудитория и задачи бизнеса", 1)
    doc.add_paragraph(
        "B2B-компании, IT-интеграторы, онлайн-школы и отделы продаж со средним или "
        "длинным циклом сделки. Основные пользователи — менеджеры и руководители продаж."
    )
    for bullet in (
        "Менеджеры оценивают похожие сделки по-разному, поэтому приоритеты трудно сравнивать.",
        "Входящие лиды и договорённости теряются между каналами и этапами работы.",
        "Подготовка повторных писем и коммерческих предложений отнимает время.",
        "Прогноз по номинальным бюджетам не учитывает вероятность закрытия.",
    ):
        doc.add_paragraph(bullet, "List Bullet")

    doc.add_heading("3  Экономический эффект и целевые показатели", 1)
    table(doc, ("Показатель", "Цель пилота и способ измерения"), [
        ("Время подготовки письма", "До 70% экономии. Сравнить медианное время от начала подготовки до готового письма для одинаковых сценариев до и после внедрения."),
        ("Точность прогноза", "Снизить абсолютную ошибку прогноза относительно факта. Сравнить взвешенную и базовую модели на одинаковых периодах и в одной валюте."),
        ("Переговоры → оплата", "Увеличить долю оплат в когорте сделок, дошедших до переговоров. Подтверждение оплаты брать из учётной системы."),
    ], (1.75, 4.92))
    callout(doc, "Оценка окупаемости",
            "ROI = (денежная выгода − затраты) / затраты × 100%. В выгоду включают "
            "экономию рабочего времени и дополнительную маржу без двойного счёта. "
            "Целевые значения проверяются на пилоте.")

    doc.add_page_break()
    doc.add_heading("4  Функциональные требования", 1)
    modules = [
        ("FR 01  Воронка продаж", "Kanban группирует сделки по стадиям. Перенос карточки отображается сразу и откатывается при ошибке API. Переход на открытую стадию запускает фоновый скоринг. Финальная стадия устанавливает дату закрытия. Возврат в открытую стадию очищает эту дату."),
        ("FR 02  Клиенты и коммуникации", "Карточка клиента показывает контакты и связанные сделки. API отдаёт историю по клиенту и по сделке, интерфейс показывает таймлайн в карточке сделки. Журнал поддерживает email, Telegram, звонки и заметки. Заметка или входящее сообщение, привязанные к сделке, запускают пересчёт."),
        ("FR 03  Оценка сделок", "Celery собирает контекст сделки, клиента и недавних коммуникаций. OpenAI Structured Outputs возвращает скоринг 0–100, Win Probability 0–1, оценку рисков и Next Best Action. После валидации результат сохраняется в PostgreSQL. Интерфейс показывает статус задачи и позволяет запустить расчёт вручную."),
        ("FR 04  Генерация писем", "Сценарии: продолжение общения, первый контакт, коммерческое предложение и возобновление общения. Тональности: дружелюбная, формальная и прямая. Результат содержит тему, текст и тезисы. Менеджер проверяет черновик и отдельно запускает отправку."),
        ("FR 05  Аналитика", "Дашборд показывает активный бюджет, взвешенный прогноз, бюджет выигранных сделок, конверсию и средний AI-скоринг. Для прогноза бюджет каждой открытой сделки умножается на вероятность закрытия. При её отсутствии используется 0,2. Суммы отображаются отдельно по валютам."),
        ("FR 06  Интеграции", "SMTP отправляет письмо и сохраняет его в журнале после принятия сервером. Демо-режим имитирует отправку. Telegram связывает чат с клиентом и активной сделкой или создаёт их. Повтор update_id не дублирует запись. При достижении 80 баллов настроенный менеджер получает уведомление."),
    ]
    for heading, body in modules:
        doc.add_heading(heading, 2)
        doc.add_paragraph(body)
    callout(doc, "Приёмочный сценарий",
            "Создать сделку, сменить стадию и дождаться результата AI. Добавить заметку, "
            "сгенерировать и проверить письмо, выполнить демо-отправку. Обработать Telegram Update "
            "дважды и убедиться, что запись одна. Сверить KPI дашборда с данными воронки.")

    doc.add_page_break()
    doc.add_heading("5  Архитектура и технологический стек", 1)
    table(doc, ("Компонент", "Назначение"), [
        ("FastAPI и Pydantic v2", "HTTP API, OpenAPI, валидация запросов, ответов и результатов AI."),
        ("SQLAlchemy 2.0 Async и Alembic", "Асинхронные транзакции и версионирование схемы."),
        ("PostgreSQL 16", "Сделки, стадии, клиенты, коммуникации и показатели скоринга."),
        ("Celery и Redis", "Фоновые задачи скоринга и генерации, очередь и статусы задач."),
        ("OpenAI Structured Outputs", "Структурированный результат скоринга и черновики писем."),
        ("React 18, TypeScript и Tailwind CSS", "Воронка, карточки, отчёты и симулятор Telegram."),
        ("Docker Compose", "Локальный запуск API, воркера, миграций, базы, Redis и фронтенда."),
    ], (2.17, 4.5))
    doc.add_paragraph(
        "Фронтенд обращается к FastAPI через прокси. FastAPI пишет бизнес-данные в PostgreSQL "
        "и ставит AI-задачи в Redis. Воркер читает контекст из базы, обращается к OpenAI, "
        "сохраняет скоринг в PostgreSQL и публикует результат задачи в Redis."
    )

    doc.add_heading("6  Информационная безопасность и нормативные требования", 1)
    doc.add_heading("Демонстрационный контур", 2)
    doc.add_paragraph(
        "Для портфолио используют синтетические записи seed и отдельный стенд. Секреты "
        "хранятся в локальном backend/.env. В Git допускается только шаблон .env.example "
        "без действующих значений. Webhook сверяет заголовок Telegram со значением secret_token, заданным при регистрации. "
        "Порты UI и API в штатном Compose привязаны к loopback."
    )
    doc.add_heading("Требования перед промышленной эксплуатацией", 2)
    for bullet in (
        "Включить аутентификацию, разграничить права менеджеров и администраторов, выделить роли PostgreSQL для приложения и миграций, журналировать доступ и изменения.",
        "Защитить соединения TLS, шифровать тома PostgreSQL, Redis и резервные копии. Хранить ключи вне томов, ограничить доступ и проверять восстановление.",
        "Определить цели и основания обработки, сроки хранения и удаления, порядок исполнения запросов субъектов. Оценить применимость локализации и правила передачи данных провайдерам.",
        "Сократить контекст, отправляемый внешним сервисам, и убрать ненужные идентификаторы. Закрепить условия обработки у поставщиков и порядок реагирования на инциденты.",
    ):
        doc.add_paragraph(bullet, "List Bullet")
    doc.add_paragraph(
        "Ориентиры для проверки применимости: 152-ФЗ, ст. 5, 6, 12, 18, 18.1 и 19. "
        "GDPR, ст. 5, 6, 28, 32 и глава V. Указанные меры входят в требования к внедрению."
    )

    doc.add_page_break()
    doc.add_heading("7  Допущения и матрица рисков", 1)
    doc.add_paragraph(
        "Демонстрационный стенд рассчитан на локальный запуск. Для внешних вызовов нужны "
        "действующие настройки соответствующего провайдера. Прогноз зависит от полноты и "
        "актуальности данных. Статус «выиграно» отражает стадию CRM, оплату подтверждает учётная система."
    )
    table(doc, ("Риск", "Влияние", "Меры и проверка"), [
        ("Лимиты и задержки OpenAI", "Поздний или недоступный результат.", "Celery выполняет запросы в фоне, SDK ограничивает ожидание и повтор. Проверить статусы задач. Mock включается при пустом ключе или значении mock."),
        ("Выводы AI при слабом контексте", "Ошибочная оценка или неподходящее письмо.", "Structured Outputs и Pydantic проверяют формат и диапазоны. Промпт просит отмечать пробелы. Менеджер сверяет факты и редактирует письмо перед отправкой."),
        ("Сбой SMTP", "Письмо не принято провайдером.", "API возвращает ошибку, а запись об отправке не фиксируется. Сверить статус с провайдером перед повтором при неоднозначном сетевом сбое."),
        ("Сбой Telegram или повтор webhook", "Нет алерта или повтор входящего события.", "Уникальный update_id защищает стандартные Update. Сбой алерта журналируется. Проверить повтор входящего запроса и сценарий отказа уведомления."),
        ("Сбой очереди после записи", "Изменение сохранено, скоринг отложен.", "Сбой постановки в очередь журналируется. Менеджер может запустить пересчёт вручную после восстановления Redis."),
    ], (1.52, 1.35, 3.8))
    doc.add_heading("Критерии завершения приёмки", 2)
    for bullet in (
        "Интерфейс и API открываются через Docker Compose, миграции применяются, seed воспроизводит демонстрационную воронку.",
        "Дашборд воспроизводит сумму открытых сделок, взвешенный прогноз и конверсию по заданной выборке.",
        "Переход стадии, таймлайн, AI-задачи и коннекторы проходят проверку с синтетическими данными.",
    ):
        doc.add_paragraph(bullet, "List Bullet")
    doc.add_heading("Нормативные источники", 2)
    doc.add_paragraph("152-ФЗ · Минтруд России · https://mintrud.gov.ru/docs/laws/130")
    doc.add_paragraph("GDPR · EUR-Lex · https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/")
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "Technical_Specification.docx")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_document().save(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
