def subscription_status_text(status: str) -> str:
    if status == "active":
        return "🟢 Активна"
    if status == "pending":
        return "🟡 Ожидает подтверждения"
    if status == "rejected":
        return "🔴 Не оплачена"
    return "⚪ Неизвестно"
