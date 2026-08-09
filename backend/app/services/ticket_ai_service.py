def analyze_ticket(ticket):
    title = ticket.title.lower()
    description = ticket.description.lower()

    text = f"{title} {description}"

    # CATEGORY
    if any(word in text for word in [
        "laptop", "computer", "pc", "boot",
        "keyboard", "mouse", "screen", "printer"
    ]):
        category = "hardware"

    elif any(word in text for word in [
        "wifi", "internet", "network",
        "connection", "router", "ethernet"
    ]):
        category = "network"

    elif any(word in text for word in [
        "password", "login", "account",
        "access", "locked"
    ]):
        category = "account_access"

    elif any(word in text for word in [
        "software", "application", "app",
        "program", "error", "install"
    ]):
        category = "software"

    else:
        category = "general"

    # PRIORITY
    if any(word in text for word in [
        "urgent", "critical",
        "server down", "system down",
        "completely down"
    ]):
        suggested_priority = "urgent"

    elif any(word in text for word in [
        "not working", "unable",
        "cannot", "failed", "failure"
    ]):
        suggested_priority = "high"

    else:
        suggested_priority = ticket.priority

    # SOLUTION
    if category == "network":
        solution = [
            "Check whether Wi-Fi is enabled on the device.",
            "Restart the Wi-Fi router and wait for 1-2 minutes.",
            "Disconnect and reconnect to the Wi-Fi network.",
            "Check whether other devices can access the internet.",
            "Restart the computer.",
            "If the issue continues, check the network adapter and DNS settings."
        ]

    elif category == "hardware":
        solution = [
            "Restart the computer and check whether the issue persists.",
            "Check all power and peripheral connections.",
            "Check whether the affected hardware is detected by the system.",
            "Update the required device driver.",
            "If the problem continues, perform a hardware diagnostic."
        ]

    elif category == "account_access":
        solution = [
            "Verify that the username or email address is correct.",
            "Check whether Caps Lock is enabled.",
            "Try resetting the password.",
            "Verify that the account is not locked.",
            "If access is still unavailable, contact the administrator."
        ]

    elif category == "software":
        solution = [
            "Restart the affected application.",
            "Restart the computer.",
            "Check whether the application has pending updates.",
            "Verify that the required software dependencies are installed.",
            "Reinstall the application if the issue continues."
        ]

    else:
        solution = [
            "Restart the affected device or application.",
            "Check the error message carefully.",
            "Verify the relevant system settings.",
            "Check whether the issue can be reproduced.",
            "Contact the support team if the problem continues."
        ]

    return {
        "ticket_id": ticket.id,
        "title": ticket.title,
        "category": category,
        "current_priority": ticket.priority,
        "suggested_priority": suggested_priority,
        "status": ticket.status,
        "analysis": f"Ticket classified as {category} issue.",
        "solution": solution
    }
