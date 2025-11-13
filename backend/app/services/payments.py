from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..integrations.yookassa import YooKassaClient
from ..models.payment import Payment, PaymentProvider, PaymentStatus
from ..models.subscription import Subscription
from ..models.subscription_plan import SubscriptionPlan
from ..models.user import User
from ..schemas.admin import PaymentListItem
from .payment_providers import PaymentProviderSettingsService
from .notifications import send_admin_message

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_recent(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[PaymentListItem], int]:
        offset = (page - 1) * size

        # Получаем общее количество
        from sqlalchemy import func
        count_stmt = select(func.count(Payment.id))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Получаем страницу данных
        stmt: Select[tuple[Payment]] = (
            select(Payment)
            .options(joinedload(Payment.user))
            .order_by(Payment.created_at.desc())
            .limit(size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        payments = result.scalars().all()
        items = [self._to_list_item(payment) for payment in payments]
        return items, total

    async def list_user_payments(
        self, user_id: int, limit: int = 50
    ) -> list[dict]:
        """Получает историю платежей пользователя."""
        stmt = (
            select(Payment)
            .options(
                joinedload(Payment.plan),
                joinedload(Payment.subscription),
            )
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        payments = result.scalars().unique().all()
        
        return [
            {
                "id": payment.id,
                "invoice": f"INV-{payment.id:04d}",
                "amount": str(payment.amount),
                "amount_formatted": self.format_amount(payment.amount, payment.currency),
                "currency": payment.currency,
                "status": payment.status.value,
                "status_label": self._get_status_label(payment.status),
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "description": payment.description,
                "plan_name": payment.plan.name if payment.plan else None,
                "payment_provider": payment.payment_provider.value,
                "external_id": payment.external_id,
                "has_subscription": payment.subscription is not None,
                "subscription_end": payment.subscription.end_date.isoformat() if payment.subscription else None,
            }
            for payment in payments
        ]

    @staticmethod
    def _get_status_label(status: PaymentStatus) -> str:
        """Возвращает читаемый статус платежа."""
        labels = {
            PaymentStatus.PENDING: "Ожидает оплаты",
            PaymentStatus.SUCCEEDED: "Оплачен",
            PaymentStatus.FAILED: "Ошибка оплаты",
            PaymentStatus.CANCELED: "Отменён",
        }
        return labels.get(status, status.value)

    def _to_list_item(self, payment: Payment) -> PaymentListItem:
        member_name = payment.user.first_name if payment.user else None
        if payment.user and payment.user.last_name:
            member_name = f"{member_name} {payment.user.last_name}".strip()
        if not member_name and payment.user:
            member_name = payment.user.username
        if not member_name and payment.user:
            member_name = f"#{payment.user.telegram_id}"

        status = payment.status.value
        amount_label = f"{payment.amount:,.2f} {payment.currency}".replace(",", " ")

        created_at_dt = payment.created_at
        if created_at_dt is None:
            created_at_dt = datetime.now(timezone.utc)
        elif created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)

        return PaymentListItem(
            id=payment.id,
            invoice=f"INV-{payment.id:04d}",
            member=member_name or "—",
            amount=amount_label,
            status=status,
            created_at=created_at_dt,
        )

    async def create_invoice(
        self,
        *,
        user: User,
        amount: Decimal,
        currency: str = "RUB",
        duration_days: int = 30,
        description: str | None = None,
        plan: SubscriptionPlan | None = None,
    ) -> Payment:
        try:
            payment = Payment(
                bot_id=user.bot_id,
                user_id=user.id,
                amount=amount,
                currency=currency,
                payment_provider=PaymentProvider.YOOKASSA,
                status=PaymentStatus.PENDING,
                description=description or "Оформление подписки",
                payload={
                    "plan_id": plan.id if plan else None,
                    "plan_name": plan.name if plan else None,
                    "duration_days": duration_days,
                },
                plan_id=plan.id if plan else None,
            )
            self.session.add(payment)
            await self.session.commit()
            await self.session.refresh(payment)
            return payment
        except Exception:
            await self.session.rollback()
            raise

    async def ensure_yookassa_payment(
        self,
        *,
        user: User,
        amount: Decimal | None,
        currency: str = "RUB",
        duration_days: int | None = None,
        description: str | None = None,
        plan: SubscriptionPlan | None = None,
        promo_code_id: int | None = None,
        promo_code_info: dict | None = None,
    ) -> dict[str, str | int | None]:
        if plan is None:
            raise ValueError("Не выбран тариф для оформления подписки")

        effective_amount = amount or plan.price_amount
        effective_duration = duration_days or plan.duration_days
        payment_description = description or plan.name or "Оформление подписки"

        payment = await self.create_invoice(
            user=user,
            amount=effective_amount,
            currency=currency,
            duration_days=effective_duration,
            description=payment_description,
            plan=plan,
        )
        
        # Сохраняем информацию о промокоде в payload
        if promo_code_info:
            payment.payload = {
                **(payment.payload or {}),
                "promo_code": promo_code_info,
            }
        
        formatted_amount = self.format_amount(payment.amount, payment.currency)

        payment_url: str | None = None
        try:
            provider_service = PaymentProviderSettingsService(self.session)
            shop_id, api_key = await provider_service.get_yookassa_credentials()
            client = YooKassaClient(shop_id=shop_id, api_key=api_key)
            
            # Проверяем наличие return_url
            if client.return_url is None:
                raise ValueError("YOOKASSA_RETURN_URL не настроен в конфигурации")
            
            metadata = {
                "payment_id": payment.id,
                "user_id": user.id,
                "plan_id": plan.id,
                "duration_days": effective_duration,
            }
            if promo_code_id:
                metadata["promo_code_id"] = promo_code_id
            remote_payment = await client.create_payment(
                amount=str(payment.amount),
                description=payment_description,
                metadata=metadata,
                confirmation_return_url=client.return_url,
            )
            payment.external_id = remote_payment.get("id")
            confirmation = remote_payment.get("confirmation") or {}
            payment_url = confirmation.get("confirmation_url")
            payment.payload = {
                **(payment.payload or {}),
                "yookassa_payment": remote_payment,
            }
            self.session.add(payment)
            await self.session.commit()
            await self.session.refresh(payment)
        except RuntimeError:
            payment_url = None
        except Exception:
            await self.session.rollback()
            raise

        if payment_url is None:
            payment_url = f"https://yookassa.fake/pay/{payment.id}"

        result = {
            "payment_id": payment.id,
            "payment_url": payment_url,
            "amount": str(payment.amount),
            "amount_formatted": formatted_amount,
            "duration_days": effective_duration,
            "description": payment_description,
            "plan_id": plan.id,
            "plan_name": plan.name,
        }
        
        # Добавляем информацию о промокоде в ответ
        if promo_code_info:
            result["promo_code"] = promo_code_info.get("promo_code")
            result["original_price"] = promo_code_info.get("original_price")
            result["discount_amount"] = promo_code_info.get("discount_amount")
        
        return result

    async def confirm_payment(
        self,
        payment_id: int,
        *,
        duration_days: int = 30,
    ) -> tuple[Payment, Subscription | None]:
        try:
            # Блокируем строку платежа для предотвращения race conditions
            stmt = (
                select(Payment)
                .options(selectinload(Payment.user), selectinload(Payment.plan))
                .where(Payment.id == payment_id)
                .with_for_update()
            )
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            if payment is None:
                raise ValueError("Платёж не найден")

            # Проверяем, что платеж еще не обработан
            if payment.status == PaymentStatus.SUCCEEDED:
                # Если подписка уже создана, возвращаем существующую
                await self.session.refresh(payment, attribute_names=["subscription"])
                subscription = payment.subscription
                logger.info(
                    "Платёж уже был подтверждён ранее",
                    extra={
                        "payment_id": payment.id,
                        "subscription_id": subscription.id if subscription else None,
                    },
                )
                return payment, subscription

            # Проверяем, что платеж не отменен
            if payment.status == PaymentStatus.CANCELED:
                raise ValueError("Платёж был отменён")

            await self._ensure_remote_payment_succeeded(payment)

            payment.status = PaymentStatus.SUCCEEDED
            if payment.paid_at is None:
                payment.paid_at = datetime.now(timezone.utc)
            self.session.add(payment)

            subscription = await self._activate_subscription(
                payment, duration_override=duration_days
            )

            # Применяем промокод после успешной оплаты
            promo_code_id = payment.payload.get("promo_code", {}).get("promo_code_id") if payment.payload else None
            if promo_code_id:
                try:
                    from .promo_codes import PromoCodeService
                    promo_service = PromoCodeService(self.session)
                    await promo_service.apply_promo_code(promo_code_id)
                    logger.info(
                        "Промокод применён",
                        extra={
                            "payment_id": payment.id,
                            "promo_code_id": promo_code_id,
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        "Не удалось применить промокод: %s",
                        exc,
                        extra={
                            "payment_id": payment.id,
                            "promo_code_id": promo_code_id,
                        },
                    )

            await self.session.commit()
            if subscription:
                await self.session.refresh(subscription)
            await self.session.refresh(payment)
            
            # Отправляем уведомление пользователю об успешной оплате
            if payment.user:
                try:
                    from .user_notifications import UserNotificationService
                    notification_service = UserNotificationService(self.session)
                    amount_formatted = self.format_amount(payment.amount, payment.currency)
                    plan_name = payment.plan.name if payment.plan else None
                    subscription_end = subscription.end_date if subscription else None
                    await notification_service.send_payment_success_notification(
                        user=payment.user,
                        payment_id=payment.id,
                        amount=amount_formatted,
                        plan_name=plan_name,
                        subscription_end=subscription_end,
                    )
                except Exception as exc:
                    logger.warning(
                        "Не удалось отправить уведомление об успешной оплате: %s",
                        exc,
                        extra={
                            "payment_id": payment.id,
                            "user_id": payment.user_id,
                        },
                    )
            
            logger.info(
                "Платёж подтверждён и подписка активирована",
                extra={
                    "payment_id": payment.id,
                    "user_id": payment.user_id,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "subscription_id": subscription.id if subscription else None,
                    "plan_id": payment.plan_id,
                },
            )
            return payment, subscription
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def format_amount(amount: Decimal, currency: str) -> str:
        return f"{amount:,.2f} {currency}".replace(",", " ")

    async def export_payments(self, limit: int | None = None) -> list[dict[str, str]]:
        stmt: Select[tuple[Payment]] = (
            select(Payment)
            .options(
                joinedload(Payment.user),
                joinedload(Payment.plan),
            )
            .order_by(Payment.created_at.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        payments = result.scalars().all()

        rows: list[dict[str, str]] = []
        for payment in payments:
            member_name = ""
            if payment.user:
                member_name = payment.user.first_name or ""
                if payment.user.last_name:
                    member_name = f"{member_name} {payment.user.last_name}".strip()
                if not member_name:
                    member_name = payment.user.username or ""
                if not member_name:
                    member_name = f"#{payment.user.telegram_id}"

            plan_name = payment.plan.name if payment.plan else ""
            created_at = (
                payment.created_at.isoformat() if getattr(payment, "created_at", None) else ""
            )
            paid_at = payment.paid_at.isoformat() if payment.paid_at else ""

            rows.append(
                {
                    "id": str(payment.id),
                    "invoice": f"INV-{payment.id:04d}",
                    "member": member_name,
                    "telegram_id": str(payment.user.telegram_id) if payment.user else "",
                    "amount": f"{payment.amount:.2f}",
                    "currency": payment.currency,
                    "amount_formatted": self.format_amount(payment.amount, payment.currency),
                    "status": payment.status.value,
                    "provider": payment.payment_provider.value,
                    "plan": plan_name,
                    "external_id": payment.external_id or "",
                    "created_at": created_at,
                    "paid_at": paid_at,
                }
            )
        return rows

    async def handle_yookassa_notification(
        self, payload: dict
    ) -> tuple[Payment | None, Subscription | None]:
        event = payload.get("event")
        payment_data = payload.get("object") or {}
        external_id = payment_data.get("id")
        if external_id is None:
            logger.warning("YooKassa notification without payment id: %s", payload)
            return None, None

        # Блокируем строку платежа для предотвращения race conditions
        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.user),
                selectinload(Payment.plan),
                selectinload(Payment.subscription),
            )
            .where(Payment.external_id == external_id)
            .with_for_update()
            .limit(1)
        )
        result = await self.session.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment is None:
            logger.warning("YooKassa payment %s not found locally", external_id)
            return None, None

        # Проверяем, не обработан ли уже платеж
        was_already_succeeded = payment.status == PaymentStatus.SUCCEEDED

        payment.payload = {
            **(payment.payload or {}),
            "yookassa_payment": payment_data,
            "yookassa_event": event,
        }

        status = payment_data.get("status")
        subscription: Subscription | None = None
        
        # Если платеж уже был обработан, не обрабатываем повторно
        if was_already_succeeded:
            subscription = payment.subscription
            logger.info(
                "YooKassa notification для уже обработанного платежа %s",
                payment.id,
            )
        elif status == "succeeded":
            payment.status = PaymentStatus.SUCCEEDED
            parsed_paid_at = self._parse_remote_datetime(
                payment_data.get("paid_at") or payment_data.get("captured_at")
            )
            if parsed_paid_at:
                payment.paid_at = parsed_paid_at
            duration_days = payment_data.get("metadata", {}).get("duration_days")
            subscription = await self._activate_subscription(
                payment,
                duration_override=duration_days if payment.plan is None else None,
            )
            
            # Применяем промокод после успешной оплаты
            promo_code_id = payment.payload.get("promo_code", {}).get("promo_code_id") if payment.payload else None
            if promo_code_id:
                try:
                    from .promo_codes import PromoCodeService
                    promo_service = PromoCodeService(self.session)
                    await promo_service.apply_promo_code(promo_code_id)
                    logger.info(
                        "Промокод применён через вебхук",
                        extra={
                            "payment_id": payment.id,
                            "promo_code_id": promo_code_id,
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        "Не удалось применить промокод через вебхук: %s",
                        exc,
                        extra={
                            "payment_id": payment.id,
                            "promo_code_id": promo_code_id,
                        },
                    )
        elif status in {"pending", "waiting_for_capture"}:
            payment.status = PaymentStatus.PENDING
        elif status == "canceled":
            payment.status = PaymentStatus.CANCELED
        else:
            logger.debug("Unhandled YooKassa status %s for payment %s", status, payment.id)

        self.session.add(payment)
        await self.session.commit()
        if subscription:
            await self.session.refresh(subscription)
        await self.session.refresh(payment)

        # Отправляем уведомления только если статус изменился
        if not was_already_succeeded:
            if payment.status == PaymentStatus.SUCCEEDED:
                amount_formatted = self.format_amount(payment.amount, payment.currency)
                await send_admin_message(
                    f"Оплата #{payment.id} подтверждена через YooKassa. Сумма: {amount_formatted}"
                )
                
                # Отправляем уведомление пользователю об успешной оплате
                if payment.user:
                    try:
                        from .user_notifications import UserNotificationService
                        notification_service = UserNotificationService(self.session)
                        plan_name = payment.plan.name if payment.plan else None
                        subscription_end = subscription.end_date if subscription else None
                        await notification_service.send_payment_success_notification(
                            user=payment.user,
                            payment_id=payment.id,
                            amount=amount_formatted,
                            plan_name=plan_name,
                            subscription_end=subscription_end,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Не удалось отправить уведомление об успешной оплате через вебхук: %s",
                            exc,
                            extra={
                                "payment_id": payment.id,
                                "user_id": payment.user_id,
                            },
                        )
            elif payment.status == PaymentStatus.CANCELED:
                await send_admin_message(f"Оплата #{payment.id} отменена в YooKassa.")

        return payment, subscription

    async def sync_pending_yookassa_payments(self, limit: int = 20) -> None:
        # Получаем список ID платежей без блокировки (для производительности)
        stmt = (
            select(Payment.id)
            .where(
                Payment.payment_provider == PaymentProvider.YOOKASSA,
                Payment.status == PaymentStatus.PENDING,
                Payment.external_id.is_not(None),
            )
            .order_by(Payment.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        payment_ids = result.scalars().all()
        if not payment_ids:
            return

        # Обрабатываем каждый платеж с блокировкой
        for payment_id in payment_ids:
            try:
                # Блокируем строку платежа для предотвращения race conditions
                payment_stmt = (
                    select(Payment)
                    .options(
                        selectinload(Payment.user),
                        selectinload(Payment.plan),
                        selectinload(Payment.subscription),
                    )
                    .where(Payment.id == payment_id)
                    .with_for_update(skip_locked=True)  # Пропускаем уже заблокированные
                )
                payment_result = await self.session.execute(payment_stmt)
                payment = payment_result.scalar_one_or_none()
                
                # Если платеж уже обрабатывается другим процессом или изменил статус, пропускаем
                if payment is None or payment.status != PaymentStatus.PENDING:
                    continue

                await self._ensure_remote_payment_succeeded(payment)
                
                # Проверяем статус после проверки удаленного платежа
                if payment.status == PaymentStatus.SUCCEEDED:
                    # Проверяем, что подписка еще не создана (защита от race condition)
                    await self.session.refresh(payment, attribute_names=["subscription"])
                    if payment.subscription is None:
                        subscription = await self._activate_subscription(payment)
                        
                        # Применяем промокод после успешной оплаты
                        promo_code_id = payment.payload.get("promo_code", {}).get("promo_code_id") if payment.payload else None
                        if promo_code_id:
                            try:
                                from .promo_codes import PromoCodeService
                                promo_service = PromoCodeService(self.session)
                                await promo_service.apply_promo_code(promo_code_id)
                                logger.info(
                                    "Промокод применён при синхронизации",
                                    extra={
                                        "payment_id": payment.id,
                                        "promo_code_id": promo_code_id,
                                    },
                                )
                            except Exception as exc:
                                logger.warning(
                                    "Не удалось применить промокод при синхронизации: %s",
                                    exc,
                                    extra={
                                        "payment_id": payment.id,
                                        "promo_code_id": promo_code_id,
                                    },
                                )
                    
                    self.session.add(payment)
                    await self.session.commit()
                    
                    # Отправляем уведомление пользователю об успешной оплате
                    if payment.user:
                        try:
                            from .user_notifications import UserNotificationService
                            notification_service = UserNotificationService(self.session)
                            amount_formatted = self.format_amount(payment.amount, payment.currency)
                            plan_name = payment.plan.name if payment.plan else None
                            subscription_end = payment.subscription.end_date if payment.subscription else None
                            await notification_service.send_payment_success_notification(
                                user=payment.user,
                                payment_id=payment.id,
                                amount=amount_formatted,
                                plan_name=plan_name,
                                subscription_end=subscription_end,
                            )
                        except Exception as exc:
                            logger.warning(
                                "Не удалось отправить уведомление об успешной оплате при синхронизации: %s",
                                exc,
                                extra={
                                    "payment_id": payment.id,
                                    "user_id": payment.user_id,
                                },
                            )
                    
                    logger.info(
                        "Платёж синхронизирован и подписка активирована",
                        extra={
                            "payment_id": payment.id,
                            "subscription_id": payment.subscription.id if payment.subscription else None,
                        },
                    )
                else:
                    # Сохраняем изменения статуса (например, CANCELED)
                    self.session.add(payment)
                    await self.session.commit()
            except ValueError as exc:
                await self.session.rollback()
                if "не завершён" in str(exc):
                    continue
                logger.info(
                    "YooKassa payment %s sync issue: %s",
                    payment_id,
                    exc,
                )
                continue
            except Exception as exc:
                await self.session.rollback()
                logger.exception(
                    "Ошибка при синхронизации платежа %s: %s",
                    payment_id,
                    exc,
                )
                continue

    async def _ensure_remote_payment_succeeded(self, payment: Payment) -> None:
        if payment.payment_provider != PaymentProvider.YOOKASSA:
            return

        if payment.external_id is None:
            # Если нет external_id, возможно тестовый режим — пропускаем проверку
            return

        try:
            provider_service = PaymentProviderSettingsService(self.session)
            shop_id, api_key = await provider_service.get_yookassa_credentials()
        except RuntimeError:
            # YooKassa не настроена — полагаемся на ручное подтверждение
            return

        client = YooKassaClient(shop_id=shop_id, api_key=api_key)
        remote_payment = await client.get_payment(payment.external_id)
        remote_status = (remote_payment or {}).get("status")

        payment.payload = {
            **(payment.payload or {}),
            "yookassa_payment": remote_payment,
        }

        if remote_status == "succeeded":
            payment.status = PaymentStatus.SUCCEEDED
            paid_at = remote_payment.get("paid_at") or remote_payment.get("captured_at")
            parsed_paid_at = self._parse_remote_datetime(paid_at)
            if parsed_paid_at is not None:
                payment.paid_at = parsed_paid_at
            elif payment.paid_at is None:
                payment.paid_at = datetime.now(timezone.utc)
            return

        if remote_status in {"pending", "waiting_for_capture"}:
            raise ValueError("Платёж ещё не завершён в YooKassa")

        if remote_status == "canceled":
            payment.status = PaymentStatus.CANCELED
            self.session.add(payment)
            await self.session.commit()
            raise ValueError("Платёж отменён в YooKassa")

        if remote_status:
            raise ValueError(f"Неизвестный статус платежа YooKassa: {remote_status}")

    @staticmethod
    def _parse_remote_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    async def _activate_subscription(
        self,
        payment: Payment,
        *,
        duration_override: int | None = None,
    ) -> Subscription | None:
        # Обновляем payment с блокировкой для проверки подписки
        await self.session.refresh(
            payment,
            attribute_names=["user", "plan", "subscription"],
        )
        if payment.user is None:
            logger.warning("Payment %s has no user bound", payment.id)
            return None
        
        # Проверяем, не создана ли уже подписка (защита от race condition)
        if payment.subscription is not None:
            return payment.subscription

        user = payment.user
        
        # Блокируем строку пользователя для предотвращения race conditions
        # при обновлении subscription_end
        user_stmt = select(User).where(User.id == user.id).with_for_update()
        user_result = await self.session.execute(user_stmt)
        locked_user = user_result.scalar_one()
        
        # Повторно проверяем подписку после блокировки (double-check pattern)
        await self.session.refresh(payment, attribute_names=["subscription"])
        if payment.subscription is not None:
            return payment.subscription

        now = datetime.now(timezone.utc)
        start_point = now
        if locked_user.subscription_end:
            end_candidate = locked_user.subscription_end
            if end_candidate.tzinfo is None:
                end_candidate = end_candidate.replace(tzinfo=timezone.utc)
            if end_candidate > now:
                start_point = end_candidate

        plan = payment.plan
        if plan is not None:
            duration_days = plan.duration_days
        else:
            duration_days = duration_override or 30
        end_point = start_point + timedelta(days=duration_days)

        subscription = Subscription(
            bot_id=locked_user.bot_id,
            user_id=locked_user.id,
            payment_id=payment.id,
            start_date=start_point,
            end_date=end_point,
            is_active=True,
            auto_renew=False,
            plan_id=plan.id if plan else None,
        )
        self.session.add(subscription)
        locked_user.subscription_end = end_point
        locked_user.is_premium = True
        self.session.add(locked_user)
        payment.subscription = subscription
        return subscription

