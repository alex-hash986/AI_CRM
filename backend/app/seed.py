import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_engine, async_session_factory
from app.models import Client, CommunicationLog, Deal, Pipeline, PipelineStage

PIPELINE_NAME = "B2B Продажи"
SEED_LOCK_ID = 1357911359


async def seed(db: AsyncSession) -> bool:
    async with db.begin():
        # Serialize demo seed runs so a retry or concurrent invocation cannot duplicate data.
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": SEED_LOCK_ID}
        )
        existing = await db.scalar(
            select(Pipeline.id).where(Pipeline.name == PIPELINE_NAME).limit(1)
        )
        if existing is not None:
            return False

        stage_specs = [
            ("Первичный контакт", "#9CA3AF"),
            ("Квалификация", "#3B82F6"),
            ("КП отправлено", "#EAB308"),
            ("Переговоры", "#F97316"),
            ("Успешно", "#22C55E"),
            ("Отказ", "#EF4444"),
        ]
        stages = [
            PipelineStage(name=name, color=color, order=order)
            for order, (name, color) in enumerate(stage_specs)
        ]
        contact, qualification, proposal, negotiation, won, lost = stages
        won.is_won = True
        lost.is_lost = True
        pipeline = Pipeline(name=PIPELINE_NAME, stages=stages)

        cloud = Client(
            name="Анна Смирнова", company="Облако Софт",
            email="anna.cloud@example.com", phone="+7 383 555 01 01",
            custom_fields={"industry": "IT", "role": "Технический директор"},
        )
        retail = Client(
            name="Дмитрий Козлов", company="Север Маркет",
            email="dmitry.retail@example.com", phone="+7 495 555 01 02",
            custom_fields={"industry": "Ритейл", "role": "Руководитель продаж"},
        )
        factory = Client(
            name="Елена Воронова", company="СибПром Маш",
            email="elena.factory@example.com", phone="+7 383 555 01 03",
            custom_fields={"industry": "Производство", "role": "Коммерческий директор"},
        )
        logistics = Client(
            name="Михаил Белов", company="ТрансЛиния",
            email="mikhail.logistics@example.com", phone="+7 343 555 01 04",
            custom_fields={"industry": "Логистика", "role": "Операционный директор"},
        )
        security = Client(
            name="Ольга Лебедева", company="Контур Защиты",
            email="olga.security@example.com", phone="+7 812 555 01 05",
            custom_fields={"industry": "IT", "role": "Руководитель партнёрского отдела"},
        )

        closed_at = datetime.now(timezone.utc)
        cloud_demo = Deal(
            title="CRM для корпоративных продаж", budget=Decimal("1450000"), currency="RUB",
            stage=negotiation, client=cloud, ai_score=85, ai_win_probability=0.78,
            ai_next_step="Назначить демо техническому директору",
            ai_risk_assessment="ЛПР сомневается в сроках интеграции",
        )
        retail_rollout = Deal(
            title="Внедрение CRM в 24 магазинах", budget=Decimal("2100000"), currency="RUB",
            stage=proposal, client=retail, ai_score=68, ai_win_probability=0.60,
            ai_next_step="Согласовать перечень метрик для пилота",
            ai_risk_assessment="Бюджет зависит от результатов пилота",
        )
        factory_pilot = Deal(
            title="Пилот для отдела дистрибуции", budget=Decimal("720000"), currency="RUB",
            stage=qualification, client=factory, ai_score=47, ai_win_probability=0.39,
            ai_next_step="Запросить требования к обмену данными с 1С",
            ai_risk_assessment="Объём доработок в 1С пока неизвестен",
        )
        logistics_lead = Deal(
            title="Автоматизация входящих заявок", budget=Decimal("440000"), currency="RUB",
            stage=contact, client=logistics,
        )
        deals = [
            cloud_demo, retail_rollout, factory_pilot, logistics_lead,
            Deal(
                title="Портал для партнёров", budget=Decimal("960000"), currency="RUB",
                stage=contact, client=security,
            ),
            Deal(
                title="Миграция клиентской базы", budget=Decimal("380000"), currency="RUB",
                stage=won, client=retail, closed_at=closed_at, ai_score=94, ai_win_probability=0.92,
                ai_next_step="Передать план миграции команде внедрения",
                ai_risk_assessment="Потребуется дедупликация старых карточек",
            ),
            Deal(
                title="CRM для дилерской сети", budget=Decimal("1250000"), currency="RUB",
                stage=lost, client=factory, closed_at=closed_at, ai_score=23,
                ai_win_probability=0.12, ai_next_step="Вернуться к контакту в следующем квартале",
                ai_risk_assessment="Заказчик выбрал расширение текущей ERP",
            ),
            Deal(
                title="Интеграция заявок с ERP", budget=Decimal("580000"), currency="RUB",
                stage=proposal, client=logistics, ai_score=71, ai_win_probability=0.64,
                ai_next_step="Запросить доступ к тестовому контуру ERP",
                ai_risk_assessment="Доступ согласует служба безопасности",
            ),
            Deal(
                title="AI-скоринг партнёрских лидов", budget=Decimal("650000"), currency="RUB",
                stage=qualification, client=security,
            ),
        ]
        logs = [
            CommunicationLog(
                deal=cloud_demo, client=cloud, channel="call", direction="outbound",
                content="Анна попросила показать интеграцию с SSO и оценить сроки запуска.",
                ai_summary="На демо обсудить SSO и сроки интеграции.",
            ),
            CommunicationLog(
                deal=retail_rollout, client=retail, channel="email", direction="inbound",
                content="Готовы начать пилот в трёх магазинах. Пришлите варианты отчётности.",
            ),
            CommunicationLog(
                deal=factory_pilot, client=factory, channel="note", direction="outbound",
                content="На встрече подтвердили выгрузку заказов из 1С раз в сутки.",
            ),
            CommunicationLog(
                deal=logistics_lead, client=logistics, channel="email", direction="inbound",
                content="Подскажите, можно ли автоматически распределять заявки по филиалам?",
            ),
        ]
        db.add_all([pipeline, *deals, *logs])

    return True


async def main() -> None:
    try:
        async with async_session_factory() as db:
            created = await seed(db)
        print("Demo data created." if created else "Demo pipeline already exists.")
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
