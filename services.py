def subscription_status_text(status):

    if status == "active":
        return "🟢 Активна"

    elif status == "pending":
        return "🟡 Ожидает подтверждения"

    elif status == "rejected":
        return "🔴 Не оплачена"

    else:
        return "⚪ Неизвестно"
