from Features.GmailOAuth import setup_status as gmail_status
from Features.CalendarOAuth import setup_status as calendar_status
from Features.PostgresStore import config_status as postgres_status
from Features.Integrations import status_text


def main():
    print(gmail_status())
    print(calendar_status())
    print(status_text("quickbooks"))
    print(postgres_status())


if __name__ == "__main__":
    main()
